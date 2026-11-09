---
name: soul-tester
description: "Run real-model tests on Hermes SOUL.md persona candidates: single-turn and multi-turn comparisons against a no-SOUL control, persona-stability and drift scenarios, blind A/B review. Use whenever the user wants to test, compare, validate or benchmark SOUL personas or the variants produced by soul-creator, check if a persona holds up, or pick between candidates, even if they just say 'probá estas variantes' or 'which soul works better'."
version: 1.4.0
metadata:
  hermes:
    tags: [soul, persona, testing, evaluation]
    related_skills: [soul-creator, skill-creator, agent-context-authoring]
---

# Soul Tester — controlled persona evaluation

Evaluate **whether a proposed SOUL changes observable interaction style while preserving utility**. This skill tests *identity*, not an agent's permissions, tools or authorization rules. Keep the source SOUL separate from operational configuration. The outputs are experimental observations, not proof of an agent's real-world reliability.

## When to use
Use with a SOUL candidate or multiple candidates that need comparison, regression testing, or refinement. The tester can compare one SOUL with a no-SOUL control, or several SOULs side-by-side. For authoring new identities use `soul-creator`. To benchmark skill *instructions* rather than SOULs, use `skill-creator`.

## 1. Set up a controlled experiment
1. Establish purpose (`personal`, `corporate`, `sales`, `support`, `roleplay`, `general` or custom); ask via `clarify` only for missing choices. Keep the same endpoint, model, sampling settings, prompts and available context across candidates; **vary only the SOUL**.
2. Use `--soul A=path.md --soul B=other.md`, or `--manifest <dir>/manifest.json` to load every variant rendered by `soul-creator` (labels = variant ids); add `--control` to quantify how much the SOUL changes baseline behavior. For one candidate, pair it with the control. The label `control` is reserved.
3. Obtain `--endpoint`, `--models`, `--key-env` or `--no-key`; never solicit or write key values. Default to provider sampling parameters, and `--runs 1` for smoke, >=3 for a comparison. `--dry-run` checks configuration offline and prints hashes, not persona content.
4. To grade **specific** personalities, prepare `--expectations targets.json` (schema under `assets/test-packs/expectations-example.json`) with `target_signals`, `forbidden_tics`, `situational_adjustments`, `task_invariants`. Use actual blend-spec expectations from `soul-creator` when provided. Expectation fields guide HUMAN/JUDGE review; no automatic semantic score is claimed.
5. Scripts live at `scripts/` relative to this skill root; when invoked from another cwd, use the installed absolute skill directory resolved at runtime. Do not use a fixed profile path.

## 2. Run a smoke check (single turn)
`python scripts/soul_test.py --check --endpoint URL --models MODEL --key-env ENV_NAME`

Then run (minimal example):

```bash
python scripts/soul_test.py --endpoint URL --models MODEL \
  --key-env ENV_NAME --soul A=/path/a.md --soul B=/path/b.md \
  --control --runs 3 --out-dir results/smoke
```

Default prompt in `references/verbose-request.md` exercises multiple reactions in one turn, but it **explicitly asks for personality** and must be labeled *smoke/demo*, not a naturalness benchmark. `--prompt-file` replaces it with an ordinary, purpose-specific task prompt.

Outputs: **`choice-guide.md`** (short, actual response excerpts for choosing a voice, also printed to terminal), `report.md` (full technical evidence), `results.json` (machine-readable, no reasoning by default) and `summary.json` (planned, successes, failures, completeness). A partially failed matrix exits **3**, a wholly failed one exits **1**; success requires all planned calls to succeed (exit **0**). Fix failures before judging winners.

## 3. Test actual conversations (multi-turn)

```bash
python scripts/soul_multiturn.py --endpoint URL --models MODEL \
  --key-env ENV_NAME --soul A=/path/a.md --soul B=/path/b.md \
  --control --set personal --runs 3 --out-dir results/personal
```

`--set` accepts `general`, `personal`, `corporate`, `sales`, `support`, `roleplay`, `dev`, `stability`, `response-shape`, `heldout`, or an external JSON file. A single-scenario file (such as `soul-creator/templates/scenarios/*.json`) is accepted as a one-scenario set. `stability` holds persona-override, jailbreak-style and long-form scenarios adapted from Hersona (CC0); turns marked `attack` are reported as probes. Use it to compare soul-creator's `identity_lock` variants (off / anchor / lock). It measures whether the *voice* held, not whether the runtime is secure against injection. Existing `dev` stresses technical context; purpose-specific sets test normal conversation and expected domain situations. Scenario JSON contains `id`, `what`, `turns` with `es` or `en`, `probe` and optional synthetic `attach`. Each run preserves the model's visible previous replies. Metrics of emoji/kaomoji, all-caps and name mentions are *surface diagnostics*, **never** a direct measure of personality fidelity or drift.

To approximate complex context, you may pass `--context-file nonsecret-system-context.txt` to **both candidate and control**. This is an augmented-context experiment, **not verified reproduction of the live Hermes system prompt, tools or runtime**. Production fidelity needs a real Hermes harness/trace.

## Languages
`--lang` takes any language code. Reports, the default prompt and bundled scenarios are localized in `es` and `en`; other codes fall back to English with a warning. For another language, copy a scenario file and add turns under that code (e.g. `"pt"`), then pass it with `--set`. Keep candidate, control and prompts in the same language so differences come from the SOUL. If a persona replies in the wrong language (a Japanese-origin archetype drifting into Japanese), classify it as `persona`.

## 4. Show the user a short choice view first

Both CLI runners print a compact, sample-first preview and save `choice-guide.md`; the detailed `report.md` remains intact. **In the assistant's final chat response, quote or briefly paraphrase representative replies from that choice view, grouped by the same model and situation.** Make the user able to choose *from the response itself*, without opening JSON or the full report. If more than a few candidates, show the most informative aligned samples and link the rest; never conceal options or silently crown a winner.

Suggested chat presentation (adapt to the actual outputs, not a rigid template):

- **Context:** which model, natural situation, how many runs and whether all returned.
- **What each option actually sounds like:** one short excerpt per candidate **for the same prompt**. Add a second contrasting situation when helpful, especially casual versus technical/support.
- **Differences in plain language:** up to one sentence per candidate about visible behaviors, not numeric scores masquerading as quality. Keep both personality and usefulness in view.
- **Decision:** ask which voice the user prefers or whether to revise/retest. The human can choose none. Do not recommend a winner on mechanical counts alone.

Do not turn the short view into another huge report. More details, methodological caveats, exact full answers and all repetitions remain in `report.md`/`results.json`; never invent representative replies or hide incomplete runs. The preview selects a *fixed comparable turn* for each multi-turn scenario, not the most flattering one per SOUL. History between variants may diverge in multi-turn, so quote it as an illustrative comparison only.

## 5. Read results using a rubric
- **Persona fidelity:** target archetype, temperament, voice, quirks visibly and naturally emerge.
- **Naturalness:** the character appears during an ordinary task, not only when asked to introduce itself.
- **Modulation:** humor, warmth, brevity and expression adapt to context without dropping identity.
- **Reply shape:** an ordinary remark can stand alone; real choices may merit alternatives; a required question is welcome; requested tables and deliverables stay structured. Distinguish obligatory handoff (even "tell me" without `?`) from a useful question. Use `--set response-shape` and qualitative review; don't use question-mark counts as verdicts.
- **Anti-slop:** check concrete meaning versus filler, vague praise and self-referential wrapper text in the **entire** reply while protecting humor, imagery, warmth and technical specificity. An anti-slop cleanup can hide persona failure if it flattens the voice.
- **Continuity:** relevant personality traits remain stable after lengthy/technical turns; absence of emoji is NOT sufficient to infer drift.
- **Task invariants:** no fabricated facts, broken code, bogus claims of completed actions, or impractical advice; classify the cause as `persona`, `capability`, `policy`, `harness` or `unknown` before suggesting edits.

Only `persona` failures justify SOUL revisions. For policies, tool permissions or operational procedure, fix the proper external configuration, not SOUL.md. Keep factual task errors distinct from voice preference. Use `references/improvements.md` to turn observations into targeted amendments; quote real outputs and state strength of evidence. A single run is anecdotal.

## 6. Blind comparison and feedback

```bash
python scripts/prepare_blind.py results/smoke/results.json \
  --left A --right B --out-dir results/blind
# Open `pairs.json` with the review utility bundled in `skill-creator` to build an offline HTML viewer.
```

The viewer contains unlabeled A/B responses and exports human ratings locally. `reveal-map.json` must be held back until reviews are locked. If the human prefers neither, do not force a winner. This viewer is **not** a grading model.

## 7. Final, reserved evaluation
`assets/scenarios/heldout.json` is nominally reserved. Do not inspect it when refining. Use `--set heldout --sample N --seed S` after closing the candidate; the CLI logs exposed scenario IDs in a persistent ledger (default: `~/.cache/soul-tester/heldout-ledger.json`). **Changing seed does not generate a fresh holdout**. Previously exposed IDs are refused unless `--allow-heldout-reuse` is explicit, in which case the result must be labeled non-fresh. A genuinely new final check requires **new independent scenarios**, ideally written by another person before seeing results.

## Privacy, failure handling and costs
- Provider-exposed reasoning is discarded before reports and JSON by default. `--include-reasoning` is an explicit opt-in; such data may be private and is not definitive causal evidence for model behavior.
- Keys stay in environment variables or local `.env`, not in prompts, traces or published reports. Treat SOULs, attached logs and responses as sensitive; sharing reports is the user's decision.
- `--extra` may contain only a JSON object of provider-specific additional parameters. It cannot override `model`, `messages`, tool wiring or explicitly selected parameters; invalid input stops before network calls.
- Total single-turn calls = models × (candidates + control) × runs. Multi-turn calls multiply by each scenario's turns; a failing conversation stops early and the global result is incomplete. Preview costs using `--dry-run`.
- Refer to `references/troubleshooting.md` for HTTP, model, proxy and auth errors.

## Verification
Run local test suite (`python -m unittest discover -s tests -v`) and compile scripts before packaging. A complete technical report includes planned vs successful calls, method (isolated/augmented/live harness), raw outputs, explicit expectations, prompt/scenario hashes, `slot-audit.json` (client role order and hashes, not the provider-internal prompt), and **which aspects remain untested**. Mock HTTP validates transport and output correctness, not persona quality.

## Pitfalls
- Do not edit the SOUL to fix permissions, tool errors or technical inaccuracies.
- Do not infer emotional continuity from emoji counts; grade observable behavior in context.
- Do not advertise mock-endpoint results as if they were from real language models.
- A candidate labeled `control` is rejected; the only control is genuinely SOUL-free via `--control`.
- Never cure a model's factual misinterpretation or a failing artifact by merely adding anti-slop adjectives to its SOUL; isolate ability from voice. Compare contemporaneous samples and preserve original failed runs.
