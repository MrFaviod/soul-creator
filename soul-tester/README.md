# soul-tester

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill that tests `SOUL.md` personas against a real model. Version 1.4.0.

It answers one question: does this persona change how the model talks, without making it worse at the task? It compares candidates with each other and with a run that has no persona at all. It does not pick a winner.

## What you get

- **Single-turn smoke test.** One prompt, every candidate, plus an optional no-persona control.
- **Multi-turn conversations.** Purpose packs for personal, support, sales, roleplay, corporate, and general use, including drift and persona-override scenarios.
- **A choice guide.** `choice-guide.md` shows a short real excerpt from each candidate so you can compare voices. Full replies stay in `report.md`.
- **Blind review.** `prepare_blind.py` strips labels before a person or another model judges the replies.

## Run it

Python standard library only. The API key is read from an environment variable and never printed.

```bash
python3 scripts/soul_test.py \
  --endpoint https://your-endpoint.example/v1 \
  --models your-model \
  --key-env YOUR_API_KEY \
  --soul A=souls/a.md --soul B=souls/b.md \
  --control --runs 3 --out-dir results/smoke
```

`--manifest <dir>/manifest.json` loads every variant rendered by [`soul-creator`](../soul-creator/). `--check` verifies the endpoint without sending a persona. `--dry-run` prints configuration hashes and no persona text.

Exit codes: **0** every planned call succeeded, **3** some failed, **1** all failed. Fix failures before comparing voices.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Notes

- The default prompt asks the model to show its personality, so treat that run as a smoke test, not a naturalness benchmark. Use `--prompt-file` for an ordinary task.
- Sampling parameters are sent only when you set them. Otherwise each model runs with its provider defaults.
- Results are observations from one setup. They are not a measure of how the persona behaves in production.

See [`SKILL.md`](SKILL.md) for the workflow Hermes follows, and [`references/`](references/) for the prompt, the choice guide, and troubleshooting.
