# Selective capitalization

Capitalization is an experimental salience cue, not an instruction-priority mechanism. New renders default to `primary_emphasis=selective` and `anti_slop_emphasis=verb`. These switches only change letter case, never add urgency words or rewrite content.

| Span | Selective rendering |
|---|---|
| Identity prefix and main archetype label | `YOU ARE Ciro, an ACERBIC CONTRARIAN GENIUS: …` |
| Primary ecosystem role | `GENERALIST ASSISTANT`; secondary focus stays ordinary case |
| First archetype behavior | Leading directive/prefix only, e.g. `YOU READ …` |
| First base-voice line | Leading directive/prefix only, e.g. `SPEAK briskly …` |
| Strong graded voice influence | Leading directive after `Strong influence:`; medium/low unchanged |
| Legacy regional primary / marked literary influence | Leading directive only |
| Anti-slop | `CHOOSE concrete words …`; the remainder stays unchanged |

The prefix helper handles English instruction scaffolding. Names, examples, selected output-language lines, palettes, situational cues, secondary archetypes and ordinary replies retain their original case. The role title can be custom and multilingual; scripts without a case distinction remain unchanged. This does not require users to speak English or the persona to answer in uppercase. Do not add mandatory uppercase catchphrases.

## Compare independently

```bash
python3 scripts/render_variants.py <workdir>/blend.json --out <workdir>/emphasis-comparison --plan grid --vary primary_emphasis anti_slop_emphasis --max 4 --check
```

This produces off/off, off/verb, selective/off and selective/verb conditions with all other axes fixed. Keep `anti_slop=short` to measure its verb casing. Use the same target model, prompts, temperature and repetitions, then compare voice, usefulness, drift and excessive emphasis. No live measurement means `untested`, not “uppercase works.” To isolate anchor wording without label-casing differences between label and description, set `baseline.primary_emphasis=off` for that experiment.

For edits/upgrades, preserve the deployed file and show the casing diff before applying anything. Old blends pick up the new default when rerendered; explicit `baseline` switches retain ordinary casing. The standalone Markdown upgrader remains conservative and does not guess which old words should be capitalized.

The checker allows selective uppercase cues and warns on sustained uppercase prose. It still checks identity and operational scope; intentional emphasis does not exempt those checks.

## Evidence and limits

- [Attention is Case-Sensitive](https://arxiv.org/abs/2608.03711) studies capitalization as an attention cue across models. It is not evidence that this exact persona scheme improves fidelity on every model.
- [OpenAI Realtime prompting guide](https://cdn.openai.com/API/docs/realtime-prompting-guide.pdf) includes uppercase emphasis among its prompting techniques; its scope is Realtime models.

Selective casing and the two independent comparison axes are design choices to test, not an established optimum. Keep instructions explicit and compact even when emphasis is off.

`persona_expression=hard` deliberately retains its own uppercase imperative verbs independently of the two casing axes. Hold its level fixed during a case-only comparison; compare soft/mid/hard as a bundled expression treatment (`references/persona-expression.md`). Selected graphic-marker blocks follow `primary_emphasis` for their leading directive; medium/low voice influences still remain unchanged.
