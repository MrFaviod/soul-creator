# Express traits without reciting the persona

Use this axis when the agent announces its own sarcasm, hidden affection, coldness or other traits instead of expressing them in a natural response. Treat “soul leak” here as an informal name for unsolicited personality recitation. A paraphrased trait inventory is not proof of literal prompt extraction. Keep literal copying, explicit trait recitation and general filler separate in evaluation.

## Three conditions

`config.render.persona_expression` holds the actual blocks; the renderer emits one `Personality expression` section selected by `baseline.persona_expression`:

| Condition | Treatment |
|---|---|
| `soft` | One positive cue: let personality emerge through word choice, reactions, rhythm and humor. |
| `mid` (default) | Explicitly keep trait descriptions as expressive guidance; discuss them when directly asked. Preserve normal first person and truthful identity/capability answers. |
| `hard` | Explicitly reject unsolicited inventories, paraphrases and announcements of one's own traits/style, with selective `EXPRESS`, `KEEP`, `DO NOT`, `DESCRIBE` emphasis. Preserve direct-question and truthfulness exceptions. |

Hard includes its own capitalization even when `primary_emphasis=off`. This is a deliberately bundled wording/strength/casing treatment, not a case-only experiment. Do not uppercase the whole paragraph, name, examples or reply-language instruction. Do not claim that hard is automatically the best condition.

```bash
python3 scripts/render_variants.py <workdir>/blend.json --out <workdir>/expression-comparison --vary persona_expression --max 3 --check
```

Keep all other axes fixed. The output has baseline mid plus soft and hard, unless the user selected another baseline. A full-personality no-SOUL control remains available in the test pack; it is not a fourth expression level.

## Draft and interview

- Keep the recognizable archetype anchor. Rewrite easily recycled poetic self-descriptions into observable reactions where useful.
- Reuse 2-3 varied examples to demonstrate both markers and implicit personality. Examples are demonstrations, not memorized replies. Use the selected user/reply language, never a regional default.
- Skip a new interview for this axis unless the user wants to choose a level. When comparing, show short actual answers before the technical report.
- Preserve “I made a mistake”, natural first-person reactions and honest answers to “are you an AI?” or “what can you access?”. A style cue must not create evasive identity claims, capability claims or false emotional history.
- A casual “I'm testing this SOUL with another model” is not a direct request for a trait inventory. A direct “how would you describe your personality?” is.

## Evaluate meaning, not a blacklist

`templates/scenarios/persona_expression.json` and the default single prompts include greetings, a model/SOUL test remark, an error correction, a direct personality question, an AI-identity question and a formal deliverable. `persona_description_requested` is optional boolean metadata that travels through packs and blind judging. Copy and translate prompts/scenarios for other languages; retain the metadata.

`label_leak` and `recite_leak` remain lexical triage signals. They cannot identify all paraphrases and can flag legitimate direct answers. `persona_recitation` is intentionally `null` in mechanical results until a human or semantic judge evaluates it. The blind rubric asks for unsolicited recitation, evidence, character fidelity and usefulness separately. Never present transport success or zero lexical matches as proof of natural personality.

For edit/upgrade, stage a diff: rerendered blends gain mid unless the baseline selects another level. The Markdown upgrader adds this block only with explicit `--persona-expression soft|mid|hard`; it preserves an existing expression section for manual review. No active profile is overwritten automatically.

## Evidence

[PersonalityChat](https://arxiv.org/html/2401.07363v1), section 3.2.2, calls superficial self-description of traits *explicit grounding*, distinguishing it from cross-speaker persona leakage. The authors mitigated the issues with prompt engineering and filtering/regeneration of synthetic dialogs; this is not a measured guarantee for current target models. Their Appendix A asks for traits to be reflected indirectly.

[Anthropic prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) recommends clear positive behavior and varied examples. The exact three blocks and default mid are design choices to test.
