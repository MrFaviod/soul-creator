# Changes from the supplied soul-tester 1.0.0

## 1.3.0: contextual shape, control integrity

- Added `response-shape` development scenarios: casual closure, genuine decision, requested table, legitimate question, emotional support, artifact-only output, creative language.
- Reject reserved candidate label `control` unless the control is truly SOUL-free via `--control`.
- Place SOUL in the first client-side system slot, including augmented-context runs; emit privacy-safe `slot-audit.json` (roles and hashes), with scope caveat.
- Expanded rubric to judge completed responses, not `?` counts; separate task correctness from naturalness.
- Added regression tests. No live model improvement asserted.

## Critical bugs
- Single and multi-turn now exit 0 only when **all** planned calls succeeded; 3 on partial success, 1 on total failure.
- `--extra` must be a JSON object and cannot overwrite `model`, `messages`, `stream`, tool wiring or parameters explicitly set by flags.
- Input validation for model lists, duplicate/invalid candidate labels, positive runs/timeout/parallel/sample and valid scenario sets.

## Reproducibility and privacy
- Added `summary.json` for each run with planned calls and completeness.
- Default artifacts omit provider-exposed reasoning; `--include-reasoning` is opt-in.
- Multi-turn `results.json` retains exact per-turn prompt SHA-256 hashes as well as scenario hash and seed-controlled fixture content description.
- Optional `--context-file` supplies a common system layer to all candidates AND control, explicitly labeled **augmented**, not true Hermes production replay.
- Heldout exposure ledger prevents silent reuse of any exposed scenario ID from the same set hash. Different seeds are not new independent examples. Default ledger at `~/.cache/soul-tester/heldout-ledger.json`.

## Persona testing
- Added purpose-specific development scenarios: `general`, `personal`, `corporate`, `sales`, `support`, `roleplay`; preserved original `dev` and `heldout`.
- Added `--expectations` JSON with observable target signals, forbidden tics, situational adjustments and task invariants; these are for **human review**, not automatic semantic grades.
- Added `scripts/prepare_blind.py` to generate unlabeled A/B output files and a separate reveal map, compatible with `skill-creator`'s offline HTML review utility.
- Replaced legacy advice to put policy, permissions or task procedures inside SOUL with clear classification: persona, capability, policy, harness or unknown.
- Updated smoke test documentation and anti-drift guidance: surface marker counts are not personality scores.
- Removed hardcoded profile paths and made test commands relative to installed skill root.

## Automated verification
- `tests/test_tester.py` contains 11 HTTP-mock + offline regression tests.
- The independent `skill-creator` paired audit had 11 cases, 10 observed repairs, zero observed regressions (mock only).
- No real LLM or live Hermes context was exercised.


# 1.2.0
- `--manifest` loads every variant rendered by soul-creator (labels = variant ids); works in both CLIs.
- Language-agnostic: `--lang` accepts any code; reports and bundled content fall back to English with a warning. Fixed label lookup so non-es/en languages no longer crash.
- New `stability` scenario set (persona-override, jailbreak-style and long-form, adapted from Hersona CC0 benchmarks, en + es). Turns marked `attack` count as probes. Single-scenario JSON files are accepted by `--set`.
- `soul_name` recognizes more identity forms (Tú eres, Você é, Tu es, Du bist) and non-ASCII names.
- `--heldout-ledger` help now matches the real default (`~/.cache/soul-tester/heldout-ledger.json`).
- Stronger trigger description.

## 1.4.0
- Added `scripts/decision_preview.py` for representative, aligned answer excerpts with no automatic winner.
- Both single-turn and multi-turn runners now print a digestible choice view and save `choice-guide.md`; `report.md` remains detailed and unchanged.
- Updated `SKILL.md` to require the assistant's chat output to show actual answer snippets and a readable choice, not only technical metrics and links.
