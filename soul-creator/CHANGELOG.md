# v2.6.0 — implicit personality and selected graphic markers

- Add soft/mid/hard `persona_expression` conditions; mid is the default, hard uses selective imperative emphasis. Preserve direct personality questions, ordinary first person and truthful identity/capability answers.
- Add independent emoji, ASCII and kaomoji blocks via `voice.graphic_markers`, with one shared rare/recurrent/frequent frequency independent of personality intensity. Preserve legacy palettes and reject active conflicting formats.
- Detect common ASCII faces previously missed; separate selected families, eligible/ineligible contexts and cross-prompt marker repetition. Exclude code/JSON decoration counts; retain explicit heuristic limits.
- Add single- and multi-turn expression controls and per-turn context metadata. Extend blind judging to semantic personality recitation and marker fit; do not infer absence of paraphrased recitation from lexical counts.
- Allow an explicit expression level in conservative Markdown upgrades, preserving existing sections and all source lines.
- Add focused render, scorer, migration, multilingual and end-to-end regressions. Behavioral superiority still requires target-model evaluation.

# v2.5.0 — brief ecosystem roles and selective emphasis

- Add a short role-selection round, 39 curated role titles, custom multilingual labels and one optional secondary focus; keep operational descriptions in the handoff.
- Keep ecosystem purpose separate from the personality archetype and preserve old blends without an inferred role.
- Enable selective case-only emphasis for main identity, role, archetype and voice cues; emphasize the initial anti-slop verb independently.
- Add two configurable comparison axes and a four-condition experiment, with examples, names and output-language lines unchanged.
- Allow selective uppercase in structural checks while retaining sustained-shouting warnings and operational errors. Include role choices in the judge's canonical target.
- Add role/format validation and render regressions; no claim of behavioral improvement without target-model runs.

# v2.4.0 — graded voices and evaluation repairs

- Add per-layer strong/medium/low voices, signature-speech analysis, informed reinterpretation and pending drafts; preserve user-selected language across all layers.
- Map former subtle color to medium when migrating; low is lexical only. Retain legacy formats.
- Fix stale result reuse with immutable execution fingerprints and manifest snapshots. Reject mixed evaluations and incomplete/empty/truncated answers.
- Correct prefer/always/match-user expectations, finite language-check coverage, canonical blind-judge targets/history and cross-prompt tic measurement.
- Preserve custom secondary dialect cues, validate blends before writes and match facet ingredients across static/dynamic conditions.
- Refresh conflicting voice examples and add focused regressions.

## 2.3.2 — output language independent of foreign accent

- Allow any catalog or custom voice as an accent influence while preserving the requested reply language (including fixed Spanish with a Cantonese influence).
- `voice.dialect.application=auto|accent` differentiates native regional writing from a non-native accent suggestion; no code-switching required.
- Keep foreign grammar/particles out of unrelated reply languages and avoid faked phonetic/learner errors; `match_user` adapts per turn.
- Expanded regression tests across single/blend, multiple scripts, and render integration.

## 2.3.1 — literary accents in Voice

- Added 56 optional written inflections across fantasy, mythology, historic registers and recognizable character inspirations, independently of the 67 real-world dialects.
- Interview offers none/single/mix with the personality always dominant, and handles a regional base plus literary color without changing language or inventing identity.
- Added `voice.stylization` validation and render variants `stylized_voice` (configured/single/off), with safeguards against excessive stacked marked/blended accents.
- Added unit tests for combinations and unchanged original SOUL migrations.

## 2.3.0

- Added a regional-voice question to the Voice interview: none, single variety, or dominant + up to two secondary influences; optional expression strength and explicit cross-language code switching.
- Added a 67-entry multilingual written-dialect catalog with contact-language/variety distinctions, sources and cautions (Jopará, Chinese varieties, Russian dialects, etc.).
- Render `blend.voice.dialect` as one subordinate Voice cue, and compare `regional_voice` configured / dominant-only / off without changing the persona or output language.
- Added validation and regression tests; upgrades of old SOULs preserve their dialect or lack thereof unless the user requests a change.

# Changelog

## 2.1.0: contextual reply form and compact anti-slop

- `anti_slop` is a controlled `short|off` variant axis; the default adds one impersonal `Substance and expression` line. No word blacklist, rewriting workflow, or private user data.
- `voice.reply_shape` supports a one-line personality-specific alternative to repetitive opening/menu/question habits; omitted blends get a compact fallback.
- New scenario-driven guidance in `references/response-shape.md` and voice sheet; validator remains focused on identity/operational scope.
- `akinator.py` persists language, accepts repeated `--answer` groups without losing input, and creates parent directories.
- Explicit custom variant axis values now validated before output.
- Offline regression tests added. No claim of improved model behavior without target-model experiments.

## 2.0.0: archetype-first interview and variant testing

### Thesis made testable
- The interview now **finds a label** instead of collecting a description. Phases:
  - A: context.
  - B: Akinator narrowing, driven by `scripts/akinator.py` over `references/catalog/anchors.json`.
  - C: guess, confirm or correct.
  - D: layers.
  - A referent path with priors and soft answers.
- `references/catalog/anchors.json`: 47 anchor archetypes, each with:
  - a label and a gloss;
  - a label-free description;
  - a recognition tier (A/B/C);
  - the allowed tiers;
  - 11 plain features with bilingual questions.
- New variant axes:
  - `anchor`: label, label+gloss or description. This is the thesis test.
  - `intensity`, `blend_mode`, `examples`, `identity_lock`.
  - `referent_name`: off by default; never names a living person.
- Label probes in the test pack check whether the model actually knows each label.

### Several variants at once
- `blend.json` is the machine form of the interview ledger; `templates/blend.example.json` is a full example.
- `scripts/render_variants.py` renders one-factor-at-a-time (or grid) variants plus a `manifest.json`. It refuses excluded tropes and skips variants it cannot build cleanly.
- `scripts/make_test_pack.py`, `scripts/run_pack.py` and `scripts/score_responses.py` form the test pipeline:
  - a harness-agnostic JSONL pack;
  - a parallel runner for any OpenAI-compatible endpoint (env-configured);
  - mechanical voice metrics, a probe report and a blind judge pack.
- The skill states that Hermes subagents skip SOUL.md, so variants must be tested as real system prompts.

### Hersona learnings
- `identity_lock` has three levels: `off`, `anchor` and `lock`. `lock` is modeled on Hersona's `persona_lock` and is tested, not assumed. Hersona's own run found it helps long-form maintenance but not attack resistance.
- Multi-turn scenarios adapted from Hersona's CC0 benchmarks (English plus Spanish): long-form topic switch, persona-override attack, jailbreak and technical distraction. They are played as real conversations and scored for drift, attack-turn behavior and language, and the judge pack carries an `attack` flag.
- Language-agnostic output:
  - `blend.output_language` (`match_user` or a code);
  - a rendered origin note, so Japanese-origin labels don't switch the reply language;
  - an `off_script` metric.
- `README.md` with acknowledgments: Hersona code is MIT, its templates and scenarios are CC0.

### Validator fixes (`check_soul.py`)
- Identity lines in several languages and persons: voseo "Sos", "Tú eres", Portuguese, French, German, Italian, "I am", "Soy".
- Operational detection:
  - headings: Boundaries, Rules, Reglas, Constraints and others;
  - more instruction patterns;
  - lines inside example exchanges are now scanned too.
- In `--final`, these are errors:
  - HTML comments, because Hermes injects them verbatim;
  - excluded tropes;
  - two identity names.
- False positives fixed: markdown links are no longer placeholders, and non-dialogue `Label:` lines in examples are no longer speakers.
- New: `--json` output for batches, and `--config`.

### No hard-coding
- `config/defaults.json` holds exclusions, blend limits, interview thresholds, variant axes and baseline, and testing defaults. Overrides come from `--config` or `SOUL_CREATOR_CONFIG`.
- Exclusions are a config list (yandere, menhera, mesugaki by default, with the reason). They are no longer a personal preference written into the steps.
- Model-specific anecdotes were generalized into an "anecdotal field observations" section, and product names were removed from the checker.
- Section names are unified in English (Archetype, Voice, Example Exchanges); outputs can still be in any language.

### Catalog
- Same-layer duplicate labels were merged into one canonical entry. Legacy names are kept in the test manifest as `original_name`.
- Excluded tropes are marked EXCLUDED and are not selectable.
- The empty `mechanics/INDEX.md` table was fixed.
- The 136 KB `MANIFEST.json` moved to `tests/fixtures/`, so it is never loaded into context.
- The referent guide defaults to **no names in the SOUL**, and includes a worked detective + fictional doctor + living commentator example.

### Fixes from the first eval round (6 independent agent runs, v2 against v1)
- `blend.exclude` is checked only against identity fields, so "no kaomoji" in Voice no longer blocks a render.
- The baseline is now config + `tier_baseline` (tiers T and B default to mild) + `blend.baseline`.
- The dynamic variant keeps every archetype bullet; facet lines no longer produce a double colon.
- Unicode persona names get clean folder names (Fermín becomes `fermin`).
- `language_policy: always` gives a strict output language; `prefer` keeps the user's override.
- New language-pressure test prompts: a foreign-language message and a switch request. Latin-script languages are told apart with a stopword guess. `--scenario-dir` is added, and the pack warns when it falls back to English.
- A no-questions / unattended mode: assumptions are recorded as `ASSUMED:` in the ledger, and the run ends with a recommendation framed as judgment.
- Examples must never invent facts or system state.
- `ledger.notes` added; `check_soul.py --help` works.

### Known limits
- About 300 older catalog entries still have very short glosses, under 30 characters. They work as search labels. When one becomes an anchor or a secondary, write a fuller gloss in `blend.json` and probe it.
- The catalog's descriptive text is still a mix of Spanish and English. Skill instructions are English.
- Anchor features are authorial estimates; tune them as data.

## 1.1.0: semantic catalog
The catalog was reorganized by trait type and subtype (roles, temperaments, tastes, voices, interview, appearance, referents, mechanics) instead of by source. All legacy atlas and Hersona identifiers were kept as searchable labels. Provenance lives in `references/catalog/RESEARCH.md`.

## 2.2.0
- Added an explicit entry choice: create, edit an existing SOUL, or upgrade to the latest expressive scheme, with a single opening question only when the intent is unspecified.
- Added `references/edit-and-upgrade.md` with identity-preserving workflows and source-first diffs.
- Added `scripts/upgrade_soul.py` for conservative, staged Markdown migration; no in-place overwrites or semantic guesses.
- Updated handoff to prefer short answer-based SOUL comparisons in chat, with full technical reports as supporting evidence.
