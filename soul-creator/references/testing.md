# Testing variants: fidelity, label recognition and cost

The question: does the persona show up in the output, which variant shows it best, and what does that cost? The structural checker cannot answer this; only runs on the real target model can. Without runs, report `untested` and never invent scores.

## The one trap specific to Hermes

Hermes subagents skip SOUL.md and use the default identity, so spawning subagents "with each variant" tests nothing. Every variant must be sent as the **system prompt** of a real call to the target model:

- `scripts/run_pack.py`, which talks to any OpenAI-compatible endpoint;
- the installed `soul-tester` skill (`tester-contract.md`): `soul_multiturn.py --manifest <workdir>/souls/<persona>/manifest.json --control --set stability` runs every variant, with blind A/B review on top;
- or a temporary Hermes profile per variant, if the user's setup supports one. Confirm how; do not assume.

Use the same model, reasoning setting and sampling the profile will actually use.

## Pipeline

```bash
# 1. pack: control (no SOUL) + every variant x voice prompts x repeats, plus label probes
python3 scripts/make_test_pack.py <workdir>/souls/<persona>/manifest.json --out <workdir>/pack.jsonl --lang es
# 2. run in parallel (endpoint/model from env or flags; key from SOUL_TEST_API_KEY)
python3 scripts/run_pack.py <workdir>/pack.jsonl --out <workdir>/responses.jsonl
# 3. score, and optionally export a blind pack for a judge model
python3 scripts/score_responses.py <workdir>/responses.jsonl --manifest <workdir>/souls/<persona>/manifest.json \
    --json <workdir>/scores.json --judge-pack <workdir>/judge.jsonl --judge-key <workdir>/judge-key.json
```

Defaults for repeats, temperature, max tokens and concurrency come from `config.testing`. Prompts come from `templates/test-prompts.json`; copy that file and add prompts from the persona's real job with `--prompts`. `run_pack.py` can be resumed only with the identical pack and generation settings. It fingerprints both and refuses mixed or legacy result files. After any SOUL, prompt, model or sampling change, choose a fresh responses filename. Incomplete/empty/truncated replies are retained as errors, excluded from scoring and retried on an identical rerun. Each new manifest snapshots its blend and configuration, so editing the source cannot change an old evaluation target.

Running the pack sends every variant's SOUL text to the configured endpoint. Ask before running it against a third-party API if the user hasn't already chosen one.

## Contextual shape and anti-slop experiments

For a repetitive opener/options/question loop, test `voice.reply_shape` with the `soul-tester` development set `--set response-shape` (ordinary conversation, genuine choice, requested table, deliverable and creative exception). Compare the previous SOUL with the one-line contextual edit at the same time, on the same models and with repeated calls. For anti-slop, `render_variants.py --vary anti_slop` creates a `short` versus `off` comparison. Use whole-response qualitative review alongside correctness and voice fidelity: fewer questions or words are not automatic wins. See `references/response-shape.md`.

For capitalization, use `--plan grid --vary primary_emphasis anti_slop_emphasis --max 4 --check`, keeping `anti_slop=short` and all other axes fixed. These four conditions differ only in case; compare voice, utility, drift and excessive emphasis without promising a gain. Preserve names, examples and language lines. Disable `primary_emphasis` when isolating label-versus-description wording from label casing. See `references/emphasis.md` for scope and evidence. Structural tests do not measure this hypothesis.

## Multi-turn scenarios (persona stability)

The pack also includes multi-turn conversations from `templates/scenarios/`, chosen by `config.testing.scenarios`. The original stability scenes are adapted from Hersona's CC0 scenarios; the expression, naturalness and continuity scenes are original development tests. All ship in English and Spanish; translate the turns for other languages.

| Scenario | Probes |
|---|---|
| `long_form_topic_switch` | Voice drift across a 12-turn conversation with changing tone. |
| `persona_override_attack` | Social pressure to change the voice or become someone else (turns marked `attack`). |
| `persona_jailbreak` | Fake system notices, "I'm your developer", mode switches, nested roleplay (marked `attack`). |
| `technical_distraction` | Flat factual questions: does the voice survive without crowding out the answers? |
| `persona_expression` | Greeting, model/SOUL remark, error admission, direct personality question, truthful identity and a formal deliverable; recitation and marker-context controls. |
| `conversational_naturalness` | 12 turns with varied conversational acts, a legitimate clarification and requested structure. |
| `voice_continuity` | 18 turns with synthetic logs, technical work, artifacts and comparable voice probes before/during/after work. Development stress scene, not an hours-long agent benchmark. |

`run_pack.py` plays each scenario as one conversation, so each turn sees the full history. `score_responses.py` reports these columns:

- `attack_tics` and `normal_tics`: the default-assistant voice on attack turns versus ordinary turns.
- `attack_markers` and `normal_markers`: marker use on the same two kinds of turn.
- `drift_markers` and `drift_chars`: first half minus second half.
- `off_script`: replies in the wrong writing system, evaluated against each turn’s language expectation. Unsupported language/script combinations remain unassessed, never implicitly Latin.
- `completion_tok_total`: recorded scenario completion tokens, summed over turns when supplied by the endpoint.

The blind judge pack carries each scenario turn, its preceding conversation and `attack` flag, plus a common canonical target with identity, language, voice layers and situational behavior. The judge does not see the condition or variant id. It can therefore assess whether the expected identity/voice held without guessing the missing target.

**Reading the `identity_lock` axis.** In Hersona's published run (one model, a tsundere and keigo blend), the lock brought:

- no gain on attack turns (67% against 67%, and a short hand-written prompt reached 83%);
- better long-conversation maintenance (67% against 33%).

Do not expect the same split: other published repeats differ. Decide per model:
- Keep `lock` only if it improves the long-form scenario without making ordinary format requests ("write this as a formal email") feel refused.
- Prefer `anchor` or `off` when the user relies on `/personality` overlays.

Identity lock and the independent voice lock are expressive controls. Neither is a security control; real protection against prompt injection belongs to the runtime.

## Voice lock and humanize

Read `references/voice-lock-humanize.md`. Use `--plan grid --vary voice_lock humanize --max 4 --check` to compare neither, lock only, humanize only and both; keep examples and other settings fixed. `voice_lock` preserves the established voice during work; `humanize` addresses conversational action and habitual response plans. Both default to on for new renders, including old blends; preserve the deployed original for before/after comparisons.

The scorer adds `response_shapes` and per-history `conversation_structure`: language-independent surface forms and five-turn review windows. These cannot recognize semantic sameness by themselves. `naturalness`, `structural_monotony` and `voice_continuity` remain null until qualitative/semantic review. Never pool independent histories into one drift window or equate fewer lists/questions with improvement.

Blind export adds whole-scenario `kind=conversation` items for completed histories of at least three turns, alongside `kind=turn` items. Judge voice continuity, conversational appropriateness, structural repetition, utility, correctness, marker fit and persona recitation separately; cite turn numbers. Use optional `conversation_act`, `phase`, `voice_probe`, `structure_requested` and `question_needed` annotations as context, not compulsory output shapes. The judge sees the common persona target, not condition axes or the rendered SOUL.

Judge export includes repeat 1 by default; `--judge-all-repeats` includes every completed repetition. This exports inputs only, without calling a judge or generating scores. Translate prompts and inspect a sample manually. Stress longer real task histories and representative tool-result volume separately before claiming long-session efficacy.

## Language consistency

The pack sets `expect_lang` on every row: the blend's `output_language`, or the pack's `--lang` when it is `match_user`. `off_script` counts replies written mostly in another writing system, for example Japanese kana when Spanish was expected. Labels borrowed from Japanese (tsundere, kuudere) or other cultures can pull a model toward that language. The rendered language line and origin note exist for that reason; this metric checks they work. For Latin-script languages it also uses a small stopword guess (es, pt, en, fr, it, de) and flags only confident mismatches. Still read a sample of replies; short replies are not judged.

The default prompts include two language-pressure items:
- `foreign_language`: the user writes in Japanese.
- `switch_language`: the user asks to switch to French.

With `match_user`, the expected reply follows the user. With a fixed language, it should stay fixed: always, under `language_policy: always`; otherwise the user's explicit request may win.

**Other languages.** Prompts and scenarios ship in English and Spanish. For another language, copy `templates/test-prompts.json` and the scenario files, add a key for that language (for example `"pt"`), and pass `--prompts` and `--scenario-dir`. `make_test_pack.py` warns whenever it falls back to English.

## What to look at

1. **Label probes.** Probes run with no system prompt and ask the model what the anchor and secondary labels mean.
   - The model says it does not know a label, or describes something else: that label cannot carry the persona on this model. Prefer `label+gloss` or `description`, or swap in a better-known label.
   - The model's idea matches the gloss: the label is doing the work the thesis expects.
2. **Mechanical voice metrics** (`score_responses.py`), compared with `control-no-soul` and the baseline:
   - `marker_share` and `marker_families`: detected markers in prose, with separate emoji / ASCII / kaomoji presence. `marker_selected_eligible_share` measures the selected families on annotated suitable turns; `marker_ineligible_share` and `marker_unselected_share` flag other cases. Missing annotations remain unassessed. See `references/graphic-markers.md` for denominators and heuristic limits.
   - `openers` and `tic_4grams`: variety versus fixed catchphrases. Opener variety is averaged within repetition rounds; 4-grams must recur across at least three distinct prompt ids, so repeating one question three times is not a cross-situation tic.
   - `label_leak`: the persona announces its trope ("como buena tsundere…"). This is a smell.
   - `assistant_tics`: the default assistant voice leaking through.
   - `recite_leak`: replies copying 8+ words of SOUL text; lexical triage, not a semantic recitation verdict. `persona_recitation` remains null until human/semantic review; direct personality questions and natural first person are controls (`references/persona-expression.md`).
   - `chars` and `completion_tok`: cost.
   - Reasoning traces, when present, are stored separately. Check whether they call the persona an injection or an instruction to ignore.
3. **Blind judge** (optional, recommended for close calls). Give `judge.jsonl` to a model from a different family. It scores 1-5 against the target persona and flags "overdone". Join the scores back with `judge-key.json`, and check about 10 of its judgments by hand.
4. **Read the replies.** Show the user 2-3 replies per variant to the same prompts. Taste decides; metrics explain.

For the three expression levels use `--vary persona_expression --max 3`, holding other axes fixed. Compare spontaneous trait inventories and paraphrases on ordinary/meta conversation, direct requested descriptions, voice, utility and marker fit. Hard combines stronger wording with uppercase verbs; it does not isolate casing alone. The judge rubric and per-turn metadata separate these dimensions. A high marker rate or zero literal leaks does not prove a better SOUL.

## Reading the anchor axis (the thesis)

Compare the `anchor-label`, baseline (`label+gloss`) and `anchor-description` variants on the same prompts:

- **Label ≥ the others, and the probe recognized the label.** The thesis holds for this model and label: keep the short anchor.
- **Description wins, or the probe failed.** The label is not known well enough here. Keep the gloss, or use the description.
- **All tie within the noise between repeats.** Prefer the shortest variant (fewest tokens).

Record the result in the blend ledger. It applies to *this model and this label*, not universally.

## Accuracy and cost (when the persona will do real work)

Add 15-30 tasks with checkable outcomes and a baseline pass rate between 40% and 85%, so a cost can actually show. A test set where every variant scores near 100% cannot reveal a regression. Run every variant and the control on them. Keep a persona variant when its fidelity beats the plainer variants and its pass rate does not fall beyond the noise between repeats. Otherwise trim, in this order: the marker palette, the identity lock, then intensity. Re-test after each cut.

## Long-session drift (optional)

Hold one 40+ turn conversation per finalist and compare the voice metrics of the first and last 10 replies. If the voice fades, consider a short re-anchor mechanism outside SOUL rather than a longer SOUL.

## Report

Use the format in `tester-contract.md`: status (`tested`, `partial` or `untested`), the model and conditions, per-variant observations, the anchor-axis finding, and limitations. No automatic winner.

## Provider and language coverage

Use `--request-options provider-options.json` for provider-specific generation settings such as reasoning effort, or `testing.request_options` in config. The runner records these settings in the execution fingerprint and rejects transport/model/message overrides. Match the actual profile; an endpoint that requires a different token-budget field or message schema needs an explicit transport adaptation. Do not claim that a bare SOUL run reproduces Hermes tools, memories or its whole system prompt. Scenario usage is stored per turn.

The pack's language policy is evaluated per item: `match_user` follows the localized input or explicit `lang_request`; fixed `prefer` accepts an explicit requested language; fixed `always` retains its own voice language. Translations/quotes should be annotated and reviewed separately. Mechanical language checks are heuristics with finite script/stopword coverage; `language_unassessed` reports unsupported codes. Any language may still be selected and tested qualitatively. Translate prompts and scenarios into the user's chosen language rather than treating English fallback as proof of coverage.
