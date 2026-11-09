#!/usr/bin/env python3
"""Build a harness-agnostic test pack (JSONL) from a variants manifest.

  make_test_pack.py DIR/<persona>/manifest.json --out pack.jsonl
                    [--lang es] [--prompts PROMPTS.json] [--repeats N]
                    [--no-control] [--no-probes] [--config FILE]

Each line: {run_id, kind, variant_id, system, prompt_id, prompt, repeat}
  kind=voice  the SOUL text as the system prompt + a user prompt
  kind=probe     no system prompt; asks the model what a label means
                 (checks whether the anchor label is actually recognized)
  kind=scenario  a multi-turn conversation (row has `turns`, some marked attack)
                 from templates/scenarios/ (long-form drift, persona-override
                 attacks, jailbreak-style pressure, technical distraction)
A 'control' variant with no SOUL is added unless --no-control.

Any runner works if it sends `system` as the system message: scripts/run_pack.py
(OpenAI-compatible API), soul-tester, or a custom harness. Do not test through
Hermes subagents: they skip SOUL.md and use the default identity.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import SKILL_DIR, load_config  # noqa: E402
from _evaluation import manifest_blend, target_persona, fingerprint
from _conversation_metrics import context as conversation_context


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--prompts", default=str(SKILL_DIR / "templates" / "test-prompts.json"))
    ap.add_argument("--repeats", type=int)
    ap.add_argument("--no-control", action="store_true")
    ap.add_argument("--no-probes", action="store_true")
    ap.add_argument("--scenarios", nargs="*", help="scenario ids or JSON paths; default config.testing.scenarios; pass none to skip")
    ap.add_argument("--no-scenarios", action="store_true")
    ap.add_argument("--scenario-dir", help="folder searched first for <id>.json (e.g. your translated copies)")
    ap.add_argument("--config")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    repeats = args.repeats or cfg["testing"]["repeats"]
    mpath = Path(args.manifest)
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    prompts = json.loads(Path(args.prompts).read_text(encoding="utf-8"))

    warnings = set()

    def context(item):
        try:
            return conversation_context(item)
        except ValueError as exc:
            ap.error(str(exc))

    def localized(item):
        if "any" in item:
            return item["any"]
        if args.lang not in item:
            warnings.add(f"no '{args.lang}' text for some prompts/scenarios; fell back to English. "
                         f"Add a '{args.lang}' key to a copy and pass --prompts / --scenario-dir.")
        return item.get(args.lang) or item["en"]

    def expected(item):
        actual_input = item.get("lang") if "any" in item else (args.lang if args.lang in item else "en")
        if out_lang == "match_user":
            return item.get("lang_request") or actual_input or expect_lang
        if blend.get("language_policy", "prefer") == "prefer" and item.get("lang_request"):
            return item["lang_request"]
        return expect_lang

    blend = manifest_blend(manifest)
    out_lang = blend.get("output_language", "match_user")
    expect_lang = args.lang if out_lang == "match_user" else out_lang
    variants = [(v["id"], (mpath.parent / v["file"]).read_text(encoding="utf-8")) for v in manifest["variants"]]
    if not args.no_control:
        variants.insert(0, ("control-no-soul", ""))

    rows = []
    for vid, system in variants:
        for p in prompts["voice"]:
            for r in range(1, repeats + 1):
                rows.append({"run_id": f"{vid}|{p['id']}|{r}", "kind": "voice", "variant_id": vid,
                             "system": system, "prompt_id": p["id"], "prompt": localized(p), "repeat": r,
                             "expect_lang": expected(p), **context(p)})

    if not args.no_scenarios:
        names = args.scenarios if args.scenarios is not None else cfg["testing"].get("scenarios", [])
        for name in names:
            if name.endswith(".json"):
                sp = Path(name)
            else:
                cands = ([Path(args.scenario_dir) / f"{name}.json"] if args.scenario_dir else []) + \
                        [SKILL_DIR / "templates" / "scenarios" / f"{name}.json"]
                sp = next(c for c in cands if c.exists())
            sc = json.loads(sp.read_text(encoding="utf-8"))
            turns = [{"text": localized(t), "attack": bool(t.get("attack")),
                      "expect_lang": expected(t), **context(t)} for t in sc["turns"]]
            for vid, system in variants:
                for r in range(1, cfg["testing"].get("scenario_repeats", 1) + 1):
                    rows.append({"run_id": f"{vid}|scenario:{sc['id']}|{r}", "kind": "scenario", "variant_id": vid,
                                 "system": system, "prompt_id": f"scenario:{sc['id']}", "turns": turns,
                                 "repeat": r, "expect_lang": expect_lang})

    if not args.no_probes:
        tmpl = localized(prompts["probe_template"])
        labels = [blend[k]["label"] for k in ("anchor", "secondary") if blend.get(k) and blend[k].get("label")]
        for lab in labels:
            rows.append({"run_id": f"probe|{lab}|1", "kind": "probe", "variant_id": "probe", "system": "",
                         "prompt_id": f"probe:{lab}", "prompt": tmpl.format(label=lab), "repeat": 1,
                         "expected_gloss": next(blend[k]["gloss"] for k in ("anchor", "secondary")
                                                if blend.get(k) and blend[k].get("label") == lab)})

    target = target_persona(blend)
    for row in rows:
        row["target_persona"] = target
        row["blend_sha256"] = fingerprint(blend)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"rows": len(rows), "variants": [v for v, _ in variants], "out": args.out,
                      "warnings": sorted(warnings)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
