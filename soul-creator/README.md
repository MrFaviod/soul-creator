# soul-creator

A Hermes Agent skill for creating, refining or migrating a `SOUL.md` persona, with archetype-based discovery and testable variants.

**Hypothesis.** Models may follow a personality better when it is anchored on a stereotype they already know ("a tsundere", "an old sea wolf", "a Socratic mentor") than on a list of adjectives. Measure this per model rather than assuming it. For new personas the skill:

1. finds that label with an Akinator-style interview;
2. adds 0-3 extra traits;
3. renders variants that differ in one thing at a time: label only, label plus gloss, description only, intensity, static or dynamic blend, identity lock, and more;
4. tests them on the user's real model, including whether the model recognizes the label at all.

It works in any language. Personas can be *inspired by* fictional, historical or living figures without naming or imitating them.

## Layout

| Path | What |
|---|---|
| `SKILL.md` | Entry point and workflow |
| `references/steps/` | Interview, pick, compatibility, voice, dynamic blend, refine |
| `references/variants.md`, `references/testing.md` | Variant axes, blend schema, test pipeline |
| `references/edit-and-upgrade.md` | Existing SOUL: targeted edits and conservative migration |
| `references/catalog/` | Trait bank by layer, plus `anchors.json` for the Akinator |
| `config/defaults.json` | Exclusions, limits, axes, render scaffolding, testing defaults |
| `templates/` | Example blend, SOUL template, test prompts, multi-turn scenarios |
| `scripts/` | `akinator.py`, `upgrade_soul.py`, `render_variants.py`, `check_soul.py`, `make_test_pack.py`, `run_pack.py`, `score_responses.py` (Python standard library only) |
| `tests/` | `python3 -m unittest discover -s tests` |

## Quick start (from the skill directory)

```bash
python3 scripts/render_variants.py templates/blend.example.json --out /tmp/souls --check
python3 scripts/make_test_pack.py /tmp/souls/ciro/manifest.json --out /tmp/pack.jsonl --lang es
SOUL_TEST_BASE_URL=... SOUL_TEST_MODEL=... SOUL_TEST_API_KEY=... \
  python3 scripts/run_pack.py /tmp/pack.jsonl --out /tmp/responses.jsonl
python3 scripts/score_responses.py /tmp/responses.jsonl --manifest /tmp/souls/ciro/manifest.json
```

## Acknowledgments

This skill stands on the shoulders of **[Hersona](https://github.com/shiro-0x/hersona)** by the hersona contributors, a wonderful project for composable, measurable personas.

From Hersona we took:
- **Identifiers and descriptions** of many temperaments, roles, hobbies, speech registers and visual attributes, now spread across `references/catalog/` as searchable labels.
- The **persona-pack ideas** in `references/examples.md`.
- The **intensity levels** (mild, moderate, strong).
- The **compatibility and clash hints**.
- The **`persona_lock`** concept, which became the `identity_lock=lock` variant.
- Its **benchmark scenarios** (long-form topic switch, persona-override attack, persona jailbreak, technical distraction), adapted in `templates/scenarios/` with Spanish translations added.
- Its honest, publish-the-bad-numbers comparison of persona prompts, summarized in `references/evidence.md`.

Hersona's templates (`attributes/`, `personas/`) and benchmark scenarios are released under **CC0 1.0**, and its code under the **MIT License**. CC0 requires no attribution; this credit is given gladly anyway. No Hersona code is copied here, and the scripts in this skill are an independent implementation. Hersona is Japanese-first. This skill keeps its ideas and makes the output language an explicit, tested choice, so a Japanese-origin archetype never pulls an agent into Japanese unless the user wants that.

Other sources for cultural labels (kabuki and Chinese opera role types, Karagöz, akyns, sainete types, Anansi, brand archetypes and character-card formats) are listed in `references/catalog/RESEARCH.md`.

Thank you to everyone who documents characters, tropes and voices in the open.

## Rework a SOUL already in use

This skill also supports refining an existing SOUL and upgrading a prior SOUL.md to the current expressive scheme. If your request does not specify **create**, **edit**, or **upgrade**, the skill asks one brief question first. For a standard old SOUL.md without a blend:

```bash
python3 scripts/upgrade_soul.py path/to/SOUL.md --out work/SOUL-upgraded.md --diff --check
```

The source file is left untouched. See `references/edit-and-upgrade.md` for preserving identity and comparing candidate behavior.

## Regional and literary voices (v2.3.2)

During the Voice phase, choose unmarked speech, one regional variety or a controlled blend (dominant grammar/address + up to two occasional lexical influences). The dialect catalog contains 67 starting points across world languages; a separate 56-entry literary-voice catalog includes fantasy, mythology, history and character-inspired inflections. Both allow user-supplied choices. Example in `templates/blend.example.json`; details in `references/dialects.md`. Compare with `--vary regional_voice` and/or `--vary stylized_voice` to isolate influences from the persona. See `references/stylized-voices.md` for regional-plus-literary blends that do not alter identity or the reply language.

Cross-language accents are supported independently of the reply language, e.g. Spanish output with a Cantonese voice influence. They do not trigger code-switching or forced learner mistakes; `voice.dialect.application=auto|accent` controls native written variety versus gentle accent color.

## v2.4: graded voices and reliable evaluations

New compositions use independently graded `voice.layers`: strong base, medium cadence/rhetoric and low lexical traces. Compatibility questions preserve or intentionally reinterpret an archetype’s signature speech, always in the user-selected reply language. See `references/voice-compatibility.md`. The evaluator now fingerprints executions, snapshots inputs, excludes incomplete replies, respects language policies, supplies the judge with its full behavioral target/history and measures tics across distinct situations.

## v2.5: ecosystem roles and selective capitalization

A brief role round chooses one primary title and optionally one secondary focus from 39 curated labels or a custom multilingual title: assistant, generalist, ops, chatbot, business bot, coordinator, reviewer, researcher and more. The SOUL receives a compact identity line; procedures and capabilities remain outside it. See `references/ecosystem-role.md`.

New renders emphasize main identity/archetype/role/voice cues and the initial anti-slop verb with selective uppercase. Two independent axes, `primary_emphasis` and `anti_slop_emphasis`, support a four-condition comparison. Examples and output-language choices stay unchanged. See `references/emphasis.md`; efficacy still needs real model tests. Rerendered old blends gain the casing defaults unless explicitly disabled, so review the diff before deployment.

## v2.6: implicit personality and graphic-marker families

Compare `--vary persona_expression --max 3` for soft/mid/hard control of unsolicited trait recitation. Mid is the starting baseline; hard emphasizes its control verbs. Normal first person, direct personality questions and truthful identity/capability answers remain allowed. See `references/persona-expression.md`.

Choose `voice.graphic_markers` for separate emoji, ASCII and kaomoji blocks with frequency independent of personality intensity. Detection now includes common ASCII faces, selected-family/context measures and repetition signals. Semantic recitation and marker appropriateness still require review. See `references/graphic-markers.md` and `templates/blend.markers.example.json`; old palettes remain supported.

## v2.7: independent voice lock and humanize

New renders default to independent `voice_lock=on` and `humanize=on`. A compact character-specific `voice.continuity` cue preserves expression during work while allowing mood and focus to vary. Humanize targets conversational actions and habitual opening/development/ending plans, retaining custom shape cues and useful structure. Identity lock, anti-slop, anti-leak, reply language and dialect strength remain separate. Compare the four combinations with `--plan grid --vary voice_lock humanize --max 4`.

The evaluator adds complete-conversation blind items and language-independent surface-structure hints; semantic quality fields stay unscored without review. New original development scenarios cover mixed conversational acts and before/during/after-task voice probes. Markdown upgrades opt in with `--voice-lock --humanize`, preserving old text. No runtime plugin or precall reinjection is installed. See `references/voice-lock-humanize.md`; efficacy on actual target models remains to be measured.
