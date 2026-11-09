#!/usr/bin/env python3
"""Render several SOUL.md variants from one blend spec, changing one axis at a time.

  render_variants.py BLEND.json --out DIR [--plan ofat|grid|baseline]
                     [--vary anchor intensity ...] [--variants LIST.json]
                     [--max N] [--config FILE] [--check]

BLEND.json is the interview ledger in machine form (schema: references/variants.md).
Axes and their values come from config (variants.axes); nothing is hard-coded here.

Plans
  ofat      baseline + one variant per non-baseline value of each varied axis (default)
  grid      full product of the varied axes (capped by --max)
  baseline  only the baseline
  --variants LIST.json  explicit list of {"id": ..., "axes": {...}} overrides

Writes DIR/<persona>/<variant-id>.md plus manifest.json. Metadata never goes
inside the SOUL file, because Hermes injects SOUL.md verbatim.
"""
import argparse
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_layers
import check_blend
import ecosystem_roles
import emphasis
import graphic_markers
import conversational_voice
from _evaluation import fingerprint
from dialect_voice import render_dialect
from stylized_voice import render_stylization
from _common import find_excluded, load_config, slug  # noqa: E402


class SkipVariant(Exception):
    pass


def article(word):
    return "an" if word[:1].lower() in "aeiou" else "a"


def label_terms(blend):
    terms = list(blend.get("label_terms") or [])
    for key in ("anchor", "secondary"):
        part = blend.get(key) or {}
        if part.get("label"):
            terms.append(part["label"])
    return [t for t in terms if t]


def identity_line(blend, axes):
    name, anc, sec = blend["name"], blend["anchor"], blend.get("secondary")
    mode = axes["anchor"]
    if mode == "description":
        line = f"You are {name}, {anc['description'].rstrip('.')}"
    else:
        line = f"You are {name}, {article(anc['label'])} {emphasis.role_or_label(anc['label'], axes)}"
        if mode == "label" and sec:
            line += f" with a {sec['label']} streak"
        if mode == "label+gloss":
            line += f": {anc['gloss'].rstrip('.')}"
    ref = blend.get("referent")
    if axes["referent_name"] == "include":
        if not ref or not ref.get("phrase"):
            raise SkipVariant("referent_name=include but blend has no referent.phrase")
        if ref.get("kind") == "living":
            raise SkipVariant("living or controversial referents are never named in a SOUL")
        if blend.get("tier") not in ("P", "C"):
            raise SkipVariant("named referents only in personal or close-circle tiers")
        line += f", {ref['phrase'].rstrip('.')}"
    return (emphasis.directive(line) if emphasis.primary(axes) else line) + "."


def archetype_section(blend, axes):
    lines = ["## Archetype"]
    intensity = (blend.get("intensity") or {}).get(axes["intensity"])
    sec = blend.get("secondary")
    facets = blend.get("dynamic") or []
    dynamic = axes["blend_mode"] == "dynamic"
    if dynamic and not facets:
        raise SkipVariant("blend_mode=dynamic but blend has no dynamic facets")
    for i, behavior in enumerate(blend["archetype"]):
        if i == 0 and emphasis.primary(axes):
            behavior = emphasis.directive(behavior)
        lines.append(f"- {'Always: ' if dynamic and i == 0 else ''}{behavior}")
    if sec:
        mode = axes["anchor"]
        if mode == "label+gloss":
            lines.append(f"- A {sec['label']} streak: {(sec.get('adds') or sec['gloss']).rstrip('.') }.")
        elif mode == "description":
            desc = sec.get("description") or sec.get("adds") or ""
            lines.append(f"- {desc[:1].upper()}{desc[1:].rstrip('.')}.")
    for facet in facets:
        then = facet["then"].strip()
        if dynamic:
            lines.append(f"- When {facet['when'].rstrip('.')} — {then[:1].lower()}{then[1:]}")
        else:
            lines.append(f"- Throughout the conversation, this facet colors your expression: {then}")
    if intensity:
        lines.append(f"- {intensity}")
    if facets:
        lines.append(f"- Across all facets you remain {blend['name']}; only the emphasis of your voice changes.")
    return lines


def language_lines(blend, rcfg):
    lang = blend.get("output_language", "match_user")
    if lang == "match_user":
        first = rcfg["language_match_user"]
    else:
        key = "language_always" if blend.get("language_policy") == "always" else "language_fixed"
        first = rcfg[key].format(language=blend.get("language") or lang)
    if lang != "match_user":
        first += f" The selected reply-language code is {lang}; it takes precedence over source accent or style names."
    return [first, rcfg["origin_note"]]


def render(blend, axes, rcfg):
    lock_voice = conversational_voice.enabled(axes, 'voice_lock')
    humanize = conversational_voice.enabled(axes, 'humanize')
    name = blend["name"]
    out = ["# Soul", "", identity_line(blend, axes), ""]
    out += ecosystem_roles.render(blend.get("ecosystem_role"), emphasis.primary(axes))
    if axes["identity_lock"] in ("anchor", "lock"):
        out += [rcfg["identity_anchor"].format(name=name), ""]
    out += archetype_section(blend, axes) + [""]
    expression = axes.get('persona_expression', 'mid')
    if expression not in rcfg['persona_expression']:
        raise ValueError('persona_expression must be soft, mid or hard')
    out += ['## Personality expression', '- ' + rcfg['persona_expression'][expression], '']
    voice = blend["voice"]
    out.append("## Voice")
    out += [f"- {v}" for v in language_lines(blend, rcfg)]
    if "layers" in voice or "signature" in voice:
        cues, skipped = voice_layers.render(voice, blend.get("output_language", "match_user"),
            axes.get("regional_voice", "configured"), axes.get("stylized_voice", "configured"))
        if skipped:
            raise SkipVariant(skipped)
        out += [f"- {emphasis.voice_line(v) if emphasis.primary(axes) else v}" for v in cues]
    else:
        regional = axes.get("regional_voice", "configured")
        dialect = voice.get("dialect")
        if regional == "off":
            if not dialect or dialect.get("mode", "none") == "none":
                raise SkipVariant("no regional voice is configured to disable")
            dialect = None
        elif regional == "single":
            if not dialect or dialect.get("mode", "none") != "blend":
                raise SkipVariant("no configured regional blend to reduce to one dominant variety")
            dialect = {**dialect, "mode": "single", "secondary": []}
        regional_lines = render_dialect(dialect, blend.get("output_language", "match_user"))
        out += [f"- {emphasis.directive(v) if emphasis.primary(axes) else v}" for v in regional_lines]
        stylized = axes.get("stylized_voice", "configured")
        style = voice.get("stylization")
        if stylized == "off":
            if not style or style.get("mode", "none") == "none":
                raise SkipVariant("no stylized voice is configured to disable")
            style = None
        elif stylized == "single":
            if not style or style.get("mode", "none") != "blend":
                raise SkipVariant("no configured stylized blend to reduce to primary-only")
            style = {**style, "mode": "single", "secondary": []}
        if regional_lines and style and style.get("mode") != "none":
            # Avoid multiple heavy layers obscuring personality or the grammatical base.
            if dialect.get("strength") in ("marked", "strong") and style.get("strength") in ("marked", "strong"):
                raise ValueError("regional and stylized voices cannot both be marked; lower one to natural/subtle")
            if dialect.get("mode") == "blend" and style.get("mode") == "blend":
                raise ValueError("do not combine two full voice blends; reduce one layer to single")
        out += [f"- {emphasis.directive(v) if emphasis.primary(axes) and (style or {}).get('strength') in ('marked', 'strong') else v}"
                for v in render_stylization(style, regional_enabled=bool(regional_lines))]
    out += [f"- {emphasis.directive(v) if i == 0 and emphasis.primary(axes) else v}"
            for i, v in enumerate(voice.get("base", []))]
    marker = (voice.get("markers") or {}).get(axes["intensity"])
    if marker:
        out.append(f"- {marker}")
    out += [f"- {v}" for v in voice.get("situational", [])]
    # A per-persona line wins. The fallback prevents omitted blend fields from
    # silently restoring the same opener/options/question structure everywhere.
    reply_shape = voice.get("reply_shape", rcfg["reply_shape_default"])
    if reply_shape:
        if not isinstance(reply_shape, str):
            raise ValueError("voice.reply_shape must be a short string, or empty to omit")
        if not humanize or 'reply_shape' in voice:
            out.append(f"- {reply_shape}")
    out.append("")
    out += graphic_markers.render(voice.get('graphic_markers'), rcfg, emphasis.primary(axes))
    if lock_voice:
        out += conversational_voice.lock(voice, rcfg, emphasis.primary(axes))
    if humanize:
        out += conversational_voice.naturalness(voice, rcfg)
    if axes.get("anti_slop", "short") == "short":
        cue = rcfg['anti_slop_short']
        if axes.get('anti_slop_emphasis', 'off') == 'verb':
            cue = emphasis.directive(cue)
        out += ["## Substance and expression", f"- {cue}", ""]
    if blend.get("quirks"):
        out.append("## Distinctive Quirks")
        out += [f"- {q}" for q in blend["quirks"]]
        out.append("")
    if axes["identity_lock"] == "lock":
        out.append("## Identity")
        out += [f"- {l.format(name=name)}" for l in rcfg["identity_lock"]]
        out.append("")
    if axes["examples"] == "on" and blend.get("examples"):
        out.append("## Example Exchanges")
        for ex in blend["examples"]:
            out += [f"User: {ex['user']}", f"{blend['name']}: {ex['reply']}", ""]
    text = "\n".join(out).rstrip() + "\n"
    if axes["anchor"] == "description":
        leaked = [t for t in label_terms(blend) if re.search(re.escape(t), text, re.I)]
        if leaked:
            raise SkipVariant(f"description variant still names the label(s) {leaked}; "
                              "rewrite archetype/voice bullets without labels so the comparison is clean")
    return text


def baseline_for(cfg, blend):
    vcfg = cfg["variants"]
    base = dict(vcfg["baseline"])
    base.update({k: v for k, v in vcfg.get("tier_baseline", {}).get(blend.get("tier"), {}).items() if not k.startswith("_")})
    base.update(blend.get("baseline") or {})
    return base


def plan_variants(cfg, args, blend):
    vcfg = cfg["variants"]
    base = baseline_for(cfg, blend)
    axes = vcfg["axes"]
    for k, v in base.items():
        if v not in axes.get(k, [v]):
            sys.exit(f"baseline {k}={v} is not a value of that axis (config, tier_baseline or blend.baseline)")
    if args.variants:
        items = json.loads(Path(args.variants).read_text(encoding="utf-8"))
        if not isinstance(items, list):
            sys.exit("--variants must contain a list")
        planned = []
        for it in items:
            if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,70}", it["id"]):
                sys.exit("each variant needs a safe id (letters, digits, _ or -)")
            overrides = it.get("axes", {})
            if not isinstance(overrides, dict) or any(k not in axes or v not in axes[k] for k, v in overrides.items()):
                sys.exit(f"variant {it['id']} has an unknown axis or invalid value")
            planned.append((it["id"], {**base, **overrides}))
        if len({vid for vid, _ in planned}) != len(planned):
            sys.exit("--variants contains duplicate ids")
        return planned
    vary = args.vary or vcfg["default_axes_to_vary"]
    unknown = [a for a in vary if a not in axes]
    if unknown:
        sys.exit(f"unknown axes {unknown}; configured: {sorted(axes)}")
    plan = args.plan or vcfg["plan"]
    result = [("baseline", base)]
    if plan == "ofat":
        for ax in vary:
            for val in axes[ax]:
                if val != base[ax]:
                    result.append((f"{ax}-{val}", {**base, ax: val}))
    elif plan == "grid":
        result = []
        for combo in itertools.product(*(axes[a] for a in vary)):
            ax = {**base, **dict(zip(vary, combo))}
            vid = "-".join(f"{a}-{v}" for a, v in zip(vary, combo) if v != base[a]) or "baseline"
            result.append((vid, ax))
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("blend")
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", choices=["ofat", "grid", "baseline"])
    ap.add_argument("--vary", nargs="*")
    ap.add_argument("--variants")
    ap.add_argument("--max", type=int)
    ap.add_argument("--config")
    ap.add_argument("--check", action="store_true", help="run check_soul --final on each output")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    blend_raw = Path(args.blend).read_text(encoding="utf-8")
    blend = json.loads(blend_raw)
    for req in ("name", "anchor", "archetype", "voice"):
        if req not in blend:
            sys.exit(f"blend is missing '{req}' (see references/variants.md)")
    try:
        voice_report = check_blend.validate(blend, cfg)
    except (ValueError, KeyError, TypeError) as exc:
        sys.exit(f"invalid blend: {exc}")
    # Exclusions are tropes: check the fields that define who the character is,
    # not voice lines that merely negate something ("no kaomoji").
    identity_text = json.dumps([blend.get("anchor"), blend.get("secondary"), blend.get("archetype"),
                                blend.get("dynamic"), blend.get("quirks")], ensure_ascii=False)
    extra_cfg = {"exclusions": {"terms": cfg["exclusions"]["terms"] + list(blend.get("exclude", []))}}
    bad = find_excluded(identity_text, extra_cfg)
    if bad:
        sys.exit(f"blend contains excluded trope(s): {sorted(set(bad))}")
    bcfg = cfg["blend"]
    if len(blend.get("quirks", [])) > bcfg["max_quirks"]:
        sys.exit(f"{len(blend['quirks'])} quirks; max is {bcfg['max_quirks']}")
    if len(blend.get("dynamic", [])) > bcfg["max_dynamic_facets"]:
        sys.exit(f"too many dynamic facets; max is {bcfg['max_dynamic_facets']}")
    named = 1 + bool(blend.get("secondary")) + len(blend.get("quirks", [])) + len(blend.get("dynamic", []))
    warnings = list(voice_report.get("notes", []))
    prefix = "Proposed voice change, pending user choice: " if voice_report.get("needs_choice") else "Acknowledged voice change: "
    warnings += [prefix + note for note in voice_report.get("conflicts", [])]
    if named > bcfg["max_named_ingredients"]:
        warnings.append(f"{named} named ingredients (> {bcfg['max_named_ingredients']}): may read as a checklist")

    limit = args.max or cfg["variants"]["max_count"]
    planned = plan_variants(cfg, args, blend)
    persona_dir = Path(args.out) / slug(blend["name"])
    persona_dir.mkdir(parents=True, exist_ok=True)
    produced, n = [], 0
    for vid, axes in planned:
        if n >= limit:
            warnings.append(f"stopped at --max {limit}; {len(planned) - n} planned variants not rendered")
            break
        try:
            text = render(blend, axes, cfg["render"])
        except ValueError as e:
            sys.exit(f"invalid voice or variant settings for {vid}: {e}")
        except SkipVariant as e:
            warnings.append(f"{vid}: skipped ({e})")
            continue
        n += 1
        fname = f"v{n:02d}-{vid}.md"
        (persona_dir / fname).write_text(text, encoding="utf-8")
        base = baseline_for(cfg, blend)
        produced.append({"id": f"v{n:02d}-{vid}", "file": fname, "axes": axes,
                         "differs_from_baseline": {k: v for k, v in axes.items() if base.get(k) != v},
                         "chars": len(text), "system_sha256": hashlib.sha256(text.encode()).hexdigest()})

    manifest = {"schema": "soul-creator/variants-v1", "persona": blend["name"], "baseline": baseline_for(cfg, blend),
                "blend_file": str(Path(args.blend).resolve()),
                "blend_sha256": fingerprint(blend), "blend_snapshot": blend, "config_snapshot": cfg,
                "voice_compatibility": voice_report,
                "variants": produced, "warnings": warnings}
    (persona_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    status = 0
    if args.check:
        import check_soul
        for v in produced:
            res = check_soul.check(persona_dir / v["file"], True, cfg)
            v["check"] = {"errors": [m for l, m in res if l == "ERROR"], "warnings": [m for l, m in res if l == "WARN"]}
            status |= bool(v["check"]["errors"])
        (persona_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"dir": str(persona_dir), "variants": [
        {"id": v["id"], "differs": v["differs_from_baseline"], **({"errors": v["check"]["errors"]} if "check" in v else {})}
        for v in produced], "warnings": warnings}, ensure_ascii=False, indent=1))
    return 1 if status else 0


if __name__ == "__main__":
    sys.exit(main())
