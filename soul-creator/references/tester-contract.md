# Handoff contract: soul-creator → any tester

This is a **logical report format**, not a claim about a particular tester's CLI. `scripts/make_test_pack.py` produces a pack any runner can execute. `soul-tester`, when installed, may use its own invocation; check it and adapt the field names. Never invent a command, a tool result, a model run or a score.

## When it runs

1. Render the variants from one `blend.json` (`references/variants.md`) and make them pass `check_soul.py --final`.
2. Test them **before** the user accepts a final candidate, with the same prompt set, model, reasoning level and sampling for every variant (`references/testing.md`).
3. Show a short answer-based choice view in chat first (same prompt, one excerpt per variant); keep the full `report.md` separately. The user chooses one to refine, or asks for another round.
4. After meaningful edits, re-render and rerun at least the affected checks. Do not claim a full retest unless one happened.
5. After acceptance, run final static validation and deliver. Write a profile file only with explicit approval.

If no runner is available, set `status: untested`. Candidates can still be compared by their sample exchanges; do not imply that they passed live tests.

## Minimum input

```yaml
manifest: <workdir>/souls/<persona>/manifest.json   # variant ids, files, axes
pack: <workdir>/pack.jsonl                          # optional, from make_test_pack.py
audience_tier: P   # P | C | T | B
identity_goal: "short description from the user's choices"
model: "the model the profile will actually use"
```

## Minimum report

```yaml
status: tested # tested | partial | untested
model: "actual model identifier, or unknown"
conditions: "prompt set, repeats, reasoning and sampling"
label_probes:
  "<label>": "recognized | partial | not recognized; one-line paraphrase of what the model said"
anchor_axis: "label vs label+gloss vs description: what differed, or 'within noise'"
variants:
  v01-baseline:
    voice_fidelity: "metrics and/or judge scores, or not measured"
    consistency: "multi-turn observations, or not measured"
    voice_continuity: "comparable before/during/after task observations, or not measured"
    conversational_naturalness: "appropriate conversational acts and unnecessary handoffs, or not measured"
    structural_monotony: "repeated conversational plans with cited turns, or not measured"
    task_regressions: "vs control, or not measured"
    costs: "chars/tokens, or not measured"
    problematic_behavior: "unsolicited trait recitation, literal copying, assistant tics, marker mismatch, or none observed; distinguish direct personality questions"
comparison: "what actually differed; no automatic selection"
limitations: "what could not be evaluated"
```

Do not infer accuracy, token savings or long-session consistency from sample dialogue alone.

For `persona_expression=soft|mid|hard`, report semantic recitation separately from lexical `label_leak`/`recite_leak`, voice fidelity and utility. Preserve the direct-question controls. For `voice.graphic_markers`, report the selected family, suitable/inappropriate contexts and repetition separately; raw marker presence is not compliance. Optional per-turn `marker_eligible` and `persona_description_requested` metadata travels through the pack and blind judge.

For `voice_lock` and `humanize`, use four matched conditions with other axes fixed and whole-conversation review. Judge export contains `kind=turn` and `kind=conversation`; adapters must preserve both or explicitly report missing sequence review. `response_shapes` and `conversation_structure.review_windows` are surface triage, not scored naturalness or drift. The semantic fields stay null without actual review. See `references/voice-lock-humanize.md` for context metadata, repeat coverage and language limits.

## Scope guardrail

Findings about authorization, secrets, tool workflow or accuracy are evidence about **runtime behavior**. They are not permission to write those controls into SOUL. Route them through `ledger.handoff` as a separate recommendation.

## User-facing choice view (before the diagnostic report)

When `soul-tester` is available, use its terminal preview / `choice-guide.md`. For each model and comparable situation, present short **actual answers**, organized by candidate and then one natural-language behavioral difference per candidate. Flag missing calls. Leave the verdict to the user. Avoid columns of latency, tokens and marker counts in the chat; those belong in the technical report. Never confuse transport success with better personality.
