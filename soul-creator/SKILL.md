---
name: soul-creator
description: "Create a Hermes SOUL.md, modify an existing personality or migrate an old SOUL to the latest expressive scheme, then test and refine it from recognizable archetypes (tsundere, old sea wolf, Socratic mentor...) via an Akinator-style interview, then render and test several variants at once. Use whenever the user wants to create, change, compare or fix an agent's personality, character, voice or SOUL.md, wants a persona 'based on' a fictional, historical or real figure, or says things like 'quiero que mi agente sea más X', 'crear personalidad', 'arquetipo', 'personaje', 'soul', even without naming SOUL.md."
metadata:
  version: "2.7.0"
  hermes:
    tags: [soul, persona, identity, voice, archetype, personality]
    related_skills: [skill-creator, soul-tester]
---

# SOUL creator: create, edit or upgrade personas

**Working hypothesis.** Models may follow personality instructions better when they are anchored on a recognizable stereotype or archetype ("you are a tsundere") than on a paragraph of adjectives ("sometimes sweet, sometimes aggressive"). This skill finds the right label through an Akinator-style interview, adds 0-3 extra traits, renders several variants, and tests whether the label actually lands on the user's model. A label only works if the model knows it, so the variants measure it instead of assuming it.

SOUL.md is injected verbatim at the top of Hermes' system prompt. It holds **identity and expressive style only**. Persona text is a voice lever, not a capability lever: it does not reliably raise accuracy and can lower it (`references/evidence.md`).

## Scope

**In SOUL:**
- a name and an identity anchor;
- a short ecosystem-role label, with at most one secondary focus;
- the archetype (label, plus a gloss or description depending on the variant);
- temperament shown as reactions;
- voice and register;
- 0-3 tastes or quirks;
- how *expression* changes by situation;
- optional varied example exchanges.

**Out of SOUL:**
- user relationship or history (memory);
- biography or lore;
- autonomy, approvals, permissions, secrets and safety policy;
- task workflow, verification duties, commands and paths;
- expertise claims.

Operational wishes that come up in the interview go to `ledger.handoff` (a configuration note) and are never rendered. A persona may *sound* terser while working; it never decides *whether* an action is allowed.

## Entry: identify the operation before the interview

Choose one of **create**, **edit**, or **upgrade** (`references/edit-and-upgrade.md`). If the user's message does not make that choice clear, ask a **single short question at the beginning**: "¿Querés crear un SOUL nuevo, modificar uno existente o actualizarlo al esquema actual sin cambiar su personalidad?" Translate as needed. Do not ask again if the user already said what they want. If the user requests both edits and migration, stage and compare each change separately.

- **Create:** discover a new identity using the flow below.
- **Edit:** read the original SOUL and any blend first, preserve unchanged decisions, and alter only the requested expressive traits. Do not restart Akinator by default.
- **Upgrade:** carry forward an existing persona under the current scheme while retaining its name, traits, intensity and voice. Prefer rerendering an existing blend; for plain SOUL markdown, stage with `scripts/upgrade_soul.py` and review the diff. Never automatically overwrite the active SOUL.

Both existing-file paths skip completed interview phases. `references/edit-and-upgrade.md` describes source precedence, conservative migration and acceptance.

## Create flow

1. **Interview, Akinator mode** (`references/steps/01-interview.md`).
   - Phase A, context: tier, language, job, and how the user wants to build it.
   - Phase A2, ecosystem role: one short selection question, with one optional clarification for a hybrid role (`references/ecosystem-role.md`). Record a primary title and at most one secondary focus; no operational description. Skip choices already stated.
   - Phase B: narrow with `scripts/akinator.py` over `references/catalog/anchors.json`.
   - Phase C: guess the archetype and confirm or correct it.
   - Phase D: layers (secondary, intensity, voice **including optional regional/dialect and fantasy, mythology, historical or character-inspired inflections and controlled blends**, 0-3 traits, name). If not specified, ask once during Voice whether the user prefers none, regional, literary/fantasy, or a blend; do not add an entire separate interview (`references/dialects.md`, `references/stylized-voices.md`).
   - Figures the user names go through the referent path.
   - Output: `blend.json` with the ledger.
2. **Pick and complete** (`references/steps/02-pick.md`). Check the tier filters and fill only what the interview left open, taking it from the catalog.
3. **Compatibility** (`references/steps/03-compat.md`, `references/voice-compatibility.md`). Check personality and signature speech separately. Preserve a marked archetype/referent voice by default; warn once in the voice question when a requested dominant dialect would replace it. Offer lighter coloring or an intentional reinterpretation. Record explicit choices; do not infer the reply language from the referent.
4. **Voice sheet** (`references/steps/04-voice.md`). Write palettes and situational expression into the blend. New compositions use `voice.layers`: up to four independently graded dialect/literary influences, `strong`, `medium`, `low`. Strong owns its compatible base, medium supplies restrained cadence/rhetoric, low supplies only occasional words/short turns. The former subtle influence corresponds to medium. Legacy formats remain readable.
5. **Render variants** (`references/variants.md`).
   - `scripts/render_variants.py blend.json --out <workdir>/souls --check` writes the baseline plus one variant per changed axis, by default `anchor` (label, label+gloss, description) and `intensity`.
   - Add `blend_mode`, `examples`, `identity_lock` or `referent_name` when they matter. For 3-4-ingredient personal blends, include `blend_mode` (`references/steps/05-dynamic-blend.md`). Selective capitalization is enabled by default; compare `primary_emphasis` and `anti_slop_emphasis` separately when testing it (`references/emphasis.md`).
   - For unsolicited personality descriptions, compare `--vary persona_expression`: exactly three conditions, soft / mid / hard. Mid is the starting baseline; hard emphasizes its control verbs. Keep all other axes fixed (`references/persona-expression.md`).
   - For fading voice or default-assistant conversational templates, use independent `voice_lock` and `humanize` axes (both start `on`). Compare the four combinations with `--plan grid --vary voice_lock humanize --max 4`; read `references/voice-lock-humanize.md`.
6. **Test** (`references/testing.md`).
   - `make_test_pack.py` → `run_pack.py` (or `soul-tester`) → `score_responses.py`.
   - The pack holds single prompts, label probes, and multi-turn scenarios: long-form drift, persona-override and jailbreak-style pressure, and technical distraction.
   - Read the label probes first: they say whether the thesis holds for this label on this model.
   - Hermes subagents skip SOUL.md, so test through real system-prompt calls.
   - Without a runner, mark the comparison `untested`.
7. **Compare and choose.** Show sample replies per variant with the report (`references/tester-contract.md`). The user chooses; metrics never auto-select.
8. **Refine** (`references/steps/06-refine.md`). Change one or two expressive levers per round in `blend.json`, then re-render and retest the affected variants.
9. **Deliver.**
   - Run `scripts/check_soul.py --final` on the chosen file. Then read it against the ledger yourself: the checker validates form, not choices.
   - State the test coverage, or `untested`.
   - Write a profile's SOUL.md only with explicit authorization and a named profile; otherwise deliver the text. A new session may be needed for the change to apply.

If the user says "don't ask me", or nobody is there to answer, run the same flow on assumptions recorded as `ASSUMED:` in the ledger (`01-interview.md`). End with a recommended starting variant, framed as judgment, not a measured winner.

Skip whatever is already settled. If the user arrives with a complete character for a new persona, map it to `blend.json` when appropriate; still resolve an unstated ecosystem role briefly in Phase A2, and ask Phase D questions only for genuine gaps. Then render, test and refine. For existing files, follow the **edit/upgrade** path instead of silently treating them as a fresh persona.

## Drafting rules (the renderer applies most of them)

1. **Identity.** "You are <Name>, <a/an> <label>…" in English scaffolding. Never "act as" or "pretend to be". `identity_lock` sets how strongly the identity holds:
   - `off`: nothing added;
   - `anchor`: adds "You are <Name> and no one else";
   - `lock`: a short Hersona-style Identity section that declines persona swaps but still adapts one output's format.

   Test the lock; don't assume it.
2. **Label + behavior.** One recognizable label as the anchor. Archetype bullets show observable reactions without repeating the label, so the anchor axis can be compared cleanly. A referent is construction material: abstract its traits; never impersonate.
3. **Voice as categories.** First identify whether the archetype already has signature speech. Then choose register, rhythm, a palette of kinds of markers with a frequency, and situational expression. Under Voice offer no marked accent, one real-world variety, one literary/fictional accent (fantasy, mythology, history or character), or a controlled blend. Preserve the selected output language even with a foreign accent (for example, Cantonese-inspired Spanish), keep native regional grammar coherent and literary elements subordinate to personality and situation (`references/dialects.md`, `references/stylized-voices.md`). Never silently infer a nationality or invent local expressions. No fixed catchphrases or closed emoji lists.
4. **Reply form and substance.** Ground one optional `voice.reply_shape` cue in the character. Use `humanize` to respond to the actual conversational move and recent context, allowing complete contributions to end. It replaces the generic shape fallback, retains custom cues once and preserves real choices, useful structure and necessary questions. Keep `anti_slop=short` separate for concrete substance (`references/voice-lock-humanize.md`, `references/response-shape.md`).
5. **Quirks.** 0-3, concrete and observable, or none.
6. **Examples.** 2-3 character-specific exchanges or none. Vary conversational acts, length and endings; include task expression or return from work when continuity matters. Show implicit reactions, never trait inventories, fixed catchphrases or procedures. Never invent facts or system state ("tests pass"); use conceptual explanations or supplied fictional data. Respect the user's reply language and no-examples choice.
7. **Length.** Around 20-50 useful lines. One identity name. No HTML comments: Hermes injects the file verbatim.
8. **No operational sections.** Nothing like Rules, Boundaries, Permissions, Workflow, Criterio or Límites. The checker rejects them in `--final`.
9. **Selective capitalization.** Emphasize the main archetype label, primary ecosystem role, leading identity/behavior/voice directive and strong voice-layer directive. The anti-slop cue emphasizes its initial verb only. Keep secondary and medium/low cues, names, language instructions, examples and ordinary reply text unchanged. Casing never changes instruction authority or guarantees fidelity. The two emphasis axes can disable it independently (`references/emphasis.md`).
10. **Implicit personality.** Express traits through observable reactions and language. Use `persona_expression=soft|mid|hard` for graded resistance to unsolicited trait inventories and announcements of one's own style. Allow direct personality questions, ordinary first person, error admissions and truthful identity/capability answers. This is expressive control, not system-prompt secrecy or a security mechanism (`references/persona-expression.md`).
11. **Graphic-marker families.** For new choices, use `voice.graphic_markers` with selected `emoji`, `ascii`, `kaomoji` families and independent `rare|recurrent|frequent` frequency; `[]` means none. Render a distinct block per selected family. Teach recurring use with concrete contexts and 2-3 varied examples, not a closed repertoire or mandatory closing. Keep examples in the user's chosen language and include a plain serious/formal control when space permits. Preserve legacy `voice.markers` on unrelated edits; never emit both formats (`references/graphic-markers.md`).
12. **Voice continuity.** Use `voice_lock` independently of identity lock. For new blends, author one `voice.continuity` sentence preserving distinctive diction, cadence and interpersonal stance during work while allowing mood, focus and dynamic facets to vary. Keep requested artifact register intact and return to the usual conversational voice around it. Preserve old blends without inventing a cue. Review full-prompt conflicts through the handoff; no runtime hooks or hierarchy overrides (`references/voice-lock-humanize.md`).

## Language-agnostic by design

- The interview runs in the user's language. Akinator questions ship in English and Spanish; translate them for any other language.
- The SOUL scaffolding uses English as an instruction format. The persona replies in `blend.output_language`: `match_user` by default, or a fixed language selected by the user. Do not claim English is universally better for persona fidelity.
- The renderer always adds a line saying the archetype's cultural origin never changes the reply language. When the accent source and reply language match, apply native regional usage; otherwise treat the source as a restrained accent inspiration without foreign-language grammar or compulsory words. Neither foreign-accent selection nor blending requires code-switching, which remains an explicit opt-in. Literary voices do not change the output language or claim phonetic accuracy. A label borrowed from Japanese (tsundere, kuudere) must not turn a Spanish agent Japanese.
- Tests flag replies written in the wrong writing system (`off_script`).
- Never privilege Spanish, English, Japanese or any other language. Interview questions, warnings and illustrative replies follow the user’s chosen language; the English SOUL scaffolding is only the instruction format. Every layer is independently projected into the selected reply language. Unknown varieties remain available as documented custom entries.
- Regional dialects are style targets only when the user asks and the model can really produce them; never fake idioms. Fantasy/historical styles are literary approximation, not a regional dialect or second identity.

## Configuration (nothing user-specific is hard-coded)

`config/defaults.json` holds:

- exclusions (tropes that are never selectable);
- blend limits;
- interview thresholds;
- variant axes, baseline and plan;
- the renderer's scaffolding lines (language, origin note, identity anchor and lock);
- testing defaults and scenarios.

User overrides go in a separate JSON passed with `--config` or `SOUL_CREATOR_CONFIG`, and are deep-merged. Scripts that consume configurable workflow/render/test settings load the shared config; standalone scoring consumes the recorded execution and manifest snapshots. Respect a user's own exclusions (from memory, USER.md or the interview) by adding them to `blend.exclude` or their config.

## Catalog and references

| Need | Where |
|---|---|
| Anchor archetypes the Akinator scores (label, gloss, description, recognition tier A/B/C, features) | `references/catalog/anchors.json` |
| The full trait bank by layer: roles, temperaments, tastes, voices, interview inputs, appearance (avatars only), referents, mechanics | `references/catalog/INDEX.md` |
| "Based on" a figure (fictional, historical, living or controversial) | `references/catalog/referents/guide.md` |
| Ambiguous cross-layer names | `references/catalog/mechanics/naming-crosswalk.md` |
| Blend ideas | `references/catalog/blends/recipes.md` |
| Finished example | `references/examples.md` |
| Blend schema, axes, rendering | `references/variants.md` |
| Brief ecosystem-role round and 39 starting labels | `references/ecosystem-role.md`, `references/ecosystem-roles.json` |
| Selective capitalization and the four-condition comparison | `references/emphasis.md` |
| Soft/mid/hard control of unsolicited personality recitation | `references/persona-expression.md` |
| Separate emoji / ASCII / kaomoji blocks and contextual measurement | `references/graphic-markers.md` |
| Graded layers, signature speech and informed compatibility choices | `references/voice-compatibility.md` |
| Contextual reply form, anti-slop and symptom-based tests | `references/response-shape.md` |
| Independent voice lock, humanize and whole-conversation evaluation | `references/voice-lock-humanize.md` |
| Modify a SOUL or upgrade its scheme without losing prior traits | `references/edit-and-upgrade.md` |
| Testing pipeline and reading the thesis | `references/testing.md` |
| Report format | `references/tester-contract.md` |

Open one or two catalog files at a time; the catalog is selection data, never SOUL text.

Recognition tiers:
- **A**: the label is widely known; usable alone.
- **B**: known in some communities; pair it with its gloss.
- **C**, or not listed: probe it first, or prefer the description.

A label that fails its probe is replaced by its gloss or description, not by louder prose.

## Scripts

Run them from the skill directory, or with an absolute path. Use `${SKILL_DIR}` only if the host actually provides it; otherwise resolve the installed skill folder, and never assume a particular user's profile path. The scripts need only the Python standard library. Keep working files (`blend.json`, `souls/`, packs) in a work directory the user agrees to, not inside the skill.

| Script | Purpose |
|---|---|
| `scripts/check_blend.py` | Validate blend types, choices and voice compatibility before writing |
| `scripts/voice_layers.py` | Inspect graded layers and signature-voice changes |
| `scripts/akinator.py` | Interview state: next question, guess or shortlist |
| `scripts/upgrade_soul.py` | Stage a conservative upgrade of an existing Markdown SOUL; no in-place overwrites |
| `scripts/render_variants.py` | `blend.json` → variant SOUL files + `manifest.json` |
| `scripts/check_soul.py [--final] [--json]` | Structural and scope validation; supports multilingual identity lines |
| `scripts/make_test_pack.py` | Harness-agnostic JSONL pack: control + variants, single prompts, multi-turn scenarios, label probes |
| `scripts/run_pack.py` | Parallel runner for any OpenAI-compatible endpoint (env-configured); plays scenarios as conversations |
| `scripts/score_responses.py` | Voice, drift, attack-turn and language metrics; probe report; blind judge pack |

`python3 -m unittest discover -s tests` checks the scripts and the catalog.

## Pitfalls

- "Expert" in a persona is not an accuracy strategy; configure real tools and instructions elsewhere.
- An obscure label without a gloss can steer the model toward the wrong behavior. Probe it.
- `/personality` overlays may replace or fight a SOUL. When a SOUL seems ignored, check which preset is active. A `lock` will fight overlays the user actually wants.
- Identity and voice locks are expressive maintenance aids, not injection defenses; real security lives in the runtime.
- Longer is not stronger: a compact, well-anchored SOUL can match a long one (`references/evidence.md`). Prefer trimming over adding.
- Voice drifts in long sessions on some models. Measure static `voice_lock` and humanize on full sequences; repeated re-anchors require a separate runtime integration.
- A test set at ceiling accuracy cannot reveal regressions. Report what was actually measured.
- A shorter/slop-free answer is not automatically a better personality. Check voice and utility separately; don't encode one session's tastes or model-specific quirks into the reusable skill.

## Done when

- Every rendered variant passes `--final`.
- The user picked a variant after seeing the test report, or an explicit `untested` limitation.
- The chosen SOUL contains only identity and expression, and matches the ledger.
- Handoff wishes and voice-compatibility warnings are documented separately. Any proposed reinterpretation is labeled pending; explicit selections are recorded without repeated confirmation.
- Any installed profile change was explicitly authorized; editing/migration outputs are staged separately from the source.
- For edits/upgrades, the original identity is preserved unless explicitly changed, and a before/after comparison was shown.

Credits and licenses: `README.md`.
