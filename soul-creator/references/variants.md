# Variants: one blend, several SOULs, one change at a time

A persona is chosen by comparing sounds, and a prompt hypothesis is checked by comparing variants. This step turns the interview's `blend.json` into several SOUL files. Each differs from a baseline along a declared **axis**, so any difference in the test results can be traced to one cause.

Axes, their values, the baseline and the default plan all live in `config/defaults.json` → `variants`, and a user config can override them. The renderer and tests read them from there; nothing below is fixed in code.

## Axes

| Axis | Values | What it tests |
|---|---|---|
| `anchor` | `label`, `label+gloss`, `description` | **The core thesis.** Does the bare label ("an acerbic contrarian genius") steer as well as or better than label plus a one-clause gloss, or than a label-free description? The answer is per model, so measure it. |
| `intensity` | `mild`, `moderate`, `strong` | Fidelity versus noise and length. The interview fixes the user's preferred level as the baseline. |
| `blend_mode` | `static`, `dynamic` | Whether the blend's facets show all the time, or only on triggers (`steps/05-dynamic-blend.md`). |
| `examples` | `on`, `off` | Whether example exchanges get copied as tics or help. |
| `voice_lock` | `on`, `off` | Static continuity of the established voice during work, independently of identity lock. Default `on`; optional authored `voice.continuity` cue. No runtime reinjection. |
| `humanize` | `on`, `off` | Contextual conversational action and reduced habitual response plans. Default `on`; generic old shape fallback is used only when off. Keep custom `voice.reply_shape` fixed. See `references/voice-lock-humanize.md`. |
| `identity_lock` | `off`, `anchor`, `lock` | Identity stability. `anchor` adds "You are X and no one else". `lock` adds a short Identity section modeled on Hersona's `persona_lock`: decline persona swaps briefly, still adapt one output's format, and only a new SOUL changes who it is. Hersona's own run found the lock helped long-conversation voice maintenance but not attack resistance, so measure it with the multi-turn scenarios (`references/testing.md`). If the user relies on `/personality` overlays, test `off` against `anchor` and expect `lock` to fight them. |
| `regional_voice` | `configured`, `single`, `off` | Compare the chosen dialect/blend to dominant-only and no regional styling. `single` is applicable when a blend exists; duplicates are skipped. Keep personality and other axes unchanged. |
| `stylized_voice` | `configured`, `single`, `off` | Compare literary/fantasy/myth/history/character voice to its single primary and no fictional inflection. `single` only applies to a literary blend. |
| `anti_slop` | `short`, `off` | One compact expressive-bias section versus none; baseline defaults to `short`. Keep it distinct from task-specific editing checklists. Test separately on real target models. |
| `primary_emphasis` | `off`, `selective` | Case-only emphasis on main identity, role, archetype and voice cues; default `selective`. Medium/low voice layers and examples stay unchanged. |
| `anti_slop_emphasis` | `off`, `verb` | Case-only emphasis on the initial anti-slop verb; default `verb`. Keep `anti_slop=short` when testing this axis. See `references/emphasis.md`. |
| `persona_expression` | `soft`, `mid`, `hard` | Graded control of unsolicited trait recitation. Mid defaults; hard has explicit, selectively uppercase imperatives. This bundles wording/strength/casing, not a case-only contrast. See `references/persona-expression.md`. |
| `referent_name` | `omit`, `include` | Whether naming the fictional or historical inspiration is a stronger anchor than describing it. Only fictional or historical referents, only in tiers P/C, never living people. Off by default. |

Plans:

- **`ofat`** (default). One factor at a time: the baseline, plus one variant per non-baseline value of each axis in `default_axes_to_vary` (or `--vary`). With the default `anchor intensity` this gives 5 files.
- **`grid`**. The full product of the chosen axes, capped by `max_count`. Use it only with 2 small axes; it explodes quickly.
- **`--variants list.json`**. An explicit list of `{"id": "...", "axes": {...}}` when the user wants specific pairs.

Keep a run to about 4-6 variants: each one multiplies the test cost by prompts × repeats.

## Commands

From the skill directory:

```bash
python3 scripts/render_variants.py <workdir>/blend.json --out <workdir>/souls --check
python3 scripts/render_variants.py <workdir>/blend.json --out <workdir>/souls --vary anchor blend_mode examples
python3 scripts/render_variants.py <workdir>/blend.json --out <workdir>/regional-comparison --vary regional_voice --check
python3 scripts/render_variants.py <workdir>/blend.json --out <workdir>/literary-comparison --vary stylized_voice --check
python3 scripts/render_variants.py <workdir>/blend.json --out <workdir>/emphasis-comparison --plan grid --vary primary_emphasis anti_slop_emphasis --max 4 --check
python3 scripts/render_variants.py <workdir>/blend.json --out <workdir>/expression-comparison --vary persona_expression --max 3 --check
python3 scripts/check_soul.py --final --json <workdir>/souls/<persona>/*.md
```

Output goes to `<workdir>/souls/<persona>/`:

- `vNN-<axis>-<value>.md` files, one per variant.
- `manifest.json`, which records each variant's axes and its difference from the baseline. Metadata never goes inside a SOUL, because Hermes injects SOUL.md verbatim. Manifests snapshot the canonical blend and configuration, hash the blend and each rendered system text, and retain compatibility notes. Pack/scorer reuse this snapshot rather than silently reading a changed source blend.

The renderer skips a variant and says why when it cannot be built cleanly:

- dynamic mode without facets;
- `referent_name=include` for a living figure or outside P/C;
- a `description` variant whose text still names the label.

It refuses a blend that contains an excluded trope, too many quirks or too many facets.

Choose `<workdir>` outside the skill directory, for example a scratch or project folder the user agrees to. Never default to someone's profile folder.

## `blend.json` schema

`templates/blend.example.json` is a complete example.

| Field | Required | Content |
|---|---|---|
| `name` | yes | The persona's own name; never a real person's name. |
| `tier` | yes | `P`, `C`, `T` or `B`. |
| `ecosystem_role` | no | `{primary: catalog-id or {label: short title}, secondary?: same}`. One compact identity line, never duties or permissions. See `references/ecosystem-role.md`. Old blends without it remain valid. |
| `output_language` | no | `match_user` (default: reply in the user's language) or a language code such as `es` or `ja`. The renderer writes the language line plus a note that the archetype's cultural origin never changes the reply language; both texts live in `config.render`. |
| `language` | no | Human name of the variety and register ("Rioplatense Spanish with voseo"), used in the fixed-language line. |
| `anchor` | yes | `{id, label, gloss, description}`. `label` is the recognizable stereotype. `gloss` is one clause with an optional "not X" contrast. `description` is the same character with no label words. |
| `secondary` | no | Same shape plus `adds`: what it adds to the anchor, in one clause. |
| `label_terms` | no | Extra words that count as "the label" when checking description variants for leaks. |
| `archetype` | yes | 2-4 observable behaviors **with no label words**, so they are valid in every anchor mode. |
| `intensity` | no | `{mild, moderate, strong}`, one line each. |
| `voice.layers` | no | Preferred for new compositions: up to four `{kind: dialect|stylization, primary: catalog-id|custom, strength: strong|medium|low, application?, code_switch?}` layers, each graded independently. Do not combine with active legacy voice objects. See `references/voice-compatibility.md`. |
| `voice.signature` | no | `{description, source, layers}` for recognizable speech associated with the archetype, referent or source SOUL. Never infers reply language. A replacement/softening needs an informed choice or an explicitly proposed draft. |
| `voice.compatibility` | no | `{conflicts: [explanations], acknowledged: true, reason: explicit choice}` or `{proposed: true}` for a pending draft. Interview metadata stays outside SOUL. |
| `voice.dialect` (legacy) | no | `{mode: none|single|blend, primary: catalog-id|custom, secondary: [1-2 catalog IDs|custom] for blend, strength: subtle|natural|marked, application: auto|accent, code_switch: off|contextual}`. A source variety from a different language becomes an accent influence in the requested reply language, not an output-language override; `code_switch` is separate opt-in. Use `references/dialects.md`. |
| `voice.stylization` (legacy) | no | `{mode: none|single|blend, primary: stylization-id|custom, secondary: [one stylization-id|custom] only for blend, strength: subtle|natural|marked}`. Literary fantasy/mythology/history/character inflection, not an authentic dialect. See `references/stylized-voices.md`. |
| `voice.base` | yes | Register, plus one decisive directive. |
| `voice.graphic_markers` | no | Preferred for new selections: `{families: [emoji|ascii|kaomoji], frequency: rare|recurrent|frequent}`. Any subset or `[]` for none; one block per family and one shared frequency independent of persona intensity. No closed repertoire. |
| `voice.markers` (legacy) | no | `{mild, moderate, strong}` palette lines; preserved on unrelated edits. Do not combine active legacy lines with `voice.graphic_markers`. |
| `voice.situational` | no | 2-4 lines on how expression changes by situation, never what is authorized. |
| `voice.continuity` | no | One character-specific sentence on recognizable diction, cadence and interpersonal stance during work. Rendered only by `voice_lock=on`; old blends need not supply it. Distinct from the cultural compatibility object `voice.signature`. |
| `voice.reply_shape` | no | One archetype-specific sentence on reply shape, rendered once in Voice. If omitted, `humanize=on` supplies the new conversational-naturalness block; `off` uses the legacy generic fallback. An empty string suppresses that fallback, not the independently selected humanize axis. |
| `dynamic` | no | Up to 3 `{when, then}` facets, used only in `blend_mode=dynamic`. |
| `quirks` | no | 0-3 concrete tastes or harmless quirks. |
| `examples` | no | 2-3 varied `{user, reply}` pairs in the persona's language. |
| `referent` | no | `{name, kind: fictional|historical|living, phrase}`. `phrase` is used only by `referent_name=include`. |
| `exclude` | no | Extra **tropes** this user rejected, added to the config exclusions. They are checked against the identity fields (anchor, secondary, archetype, facets, quirks), not against voice lines, so "no kaomoji" in Voice is fine. New marker choices belong in `voice.graphic_markers`, not here. |
| `anti_slop` | no | Controlled via `baseline.anti_slop` (`short` or `off`); its single line lives in `config.render.anti_slop_short`, not in user/session records. It does not instruct a writing-review workflow. |
| `baseline` | no | Axis values for this persona's baseline, for example `{"intensity": "mild"}` when the user picked mild. They are merged over `config.variants.baseline` and the tier defaults (`config.variants.tier_baseline`: T and B default to mild). |
| `language_policy` | no | `prefer` (default: the fixed language, unless the user explicitly asks for another) or `always` (stays fixed; translations and quotes are written as asked). Only used with a fixed `output_language`. |
| `ledger` | no | `{decided, rejected, handoff, notes}`. The renderer ignores it; it is the memory of the interview. Prefix assumed answers with `ASSUMED:`. |

## Writing a blend that renders well

- Archetype bullets describe **behavior**, not adjectives, and avoid the label words. The label lives only in `anchor.label`, so the anchor axis is a clean comparison.
- The gloss is one clause. If it needs a paragraph, the label is too obscure: probe it, or switch the baseline to `description`.
- Intensity lines change **how often and how loud**, not who the character is.
- Situational lines are about presentation. Approval, verification and tool rules go to `ledger.handoff`.
- Write `voice.reply_shape` for the *character*, not the model vendor. It should allow a reply to end naturally and allow requested lists/tables/questions when useful. Do not use rigid word counts or mandatory openers/closers.
- Write `voice.continuity` for a new voice, preserving recognizable expression while focus, mood and facets vary. Compare `voice_lock` and `humanize` independently on complete conversations, holding examples and other axes fixed (`references/voice-lock-humanize.md`).
- `anti_slop=short` adds exactly one general expressive preference. Avoid per-word blacklists, strict punctuation prohibitions, automatic sanitization of metaphors, and user-specific defaults. The independent review pass described by external anti-slop skills belongs in a separate editing workflow, not inside SOUL.
- Leave the language itself out of `voice.base`; `output_language` and `language` produce that line. `voice.base` holds register details (voseo, keigo, formality) and the directive.

## Existing SOUL sources

To **edit** a persona, reuse its `blend.json` and vary only the chosen traits. To **upgrade** an old file, prefer rerendering its blend with this renderer. If only a standalone SOUL.md is available, `scripts/upgrade_soul.py` can stage the new short sections without rewriting identity; see `references/edit-and-upgrade.md`. It does **not** infer a complete blend or claim behavioral equivalence.

## After rendering

Every variant must pass `check_soul.py --final`. Then build and run the test pack (`references/testing.md`), and show the user the comparison next to the sample exchanges. The user picks; metrics inform but never decide. The chosen variant becomes the candidate refined in `steps/06-refine.md`. Re-render from the edited `blend.json` rather than hand-editing a single file, so the variants stay comparable.

## Matched static/dynamic facets

Both conditions now include the same archetype, secondary and `dynamic[].then` behaviors, plus the same continuity cue. Static makes those facets broadly present; dynamic conditions them on `when`. This corrects the older comparison that could add ingredients only to dynamic. Rerendering an old blend with facets therefore changes its former static output: show the diff on upgrade and do not silently replace an installed SOUL.

Capitalization defaults also change old-blend renders. Show that diff, or retain ordinary case with both emphasis switches set to `off` in `baseline`. For a pure anchor-wording comparison, disable `primary_emphasis` so the label condition has no extra casing treatment.

Rerendered blends also receive the `persona_expression` block (mid unless explicitly selected otherwise). Review it separately from other edits. Existing legacy marker palettes are not automatically converted or assigned a new frequency.
