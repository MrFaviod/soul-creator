# Voice continuity and conversational naturalness

Read this when building a new voice, or when a persona fades during work or repeatedly answers with the same conversational plan. Keep this static improvement separate from any future precall/reinjection plugin.

## Independent responsibilities

| Control | Purpose | Does not establish |
|---|---|---|
| `identity_lock=off|anchor|lock` | Preserve who the character is | Naturalness or sustained voice |
| `voice_lock=on|off` | Preserve recognizable expression across conversation and task work | An immutable mood, dialect intensity or response shape |
| `humanize=on|off` | Match the conversational action and details; avoid habitual response plans | Mandatory informality, brevity, warmth, humor or novelty |
| `persona_expression=soft|mid|hard` | Regulate unsolicited self-description | Conversational variety |
| `anti_slop=short|off` | Prefer concrete substance over filler | Personality or factual accuracy |

The two new axes default to `on`. `voice_lock` is independent of identity lock, persona intensity, markers, dialect layers and anti-leak strength. It neither refuses user requests nor changes output-language policy. Its leading and returning directives follow `primary_emphasis`; it adds no runtime calls.

## Author the continuity cue

For a new blend, add one `voice.continuity` sentence naming a few observable qualities that remain recognizable while working: diction, cadence, address and interpersonal stance. Derive it from the chosen voice, not a universal assistant personality. Avoid the archetype's label words, exact catchphrases and duplicate paragraphs. The renderer puts it inside `## Voice lock` only when enabled.

Let focus, emotion, intensity and dynamic facets change naturally. A concentrated character can use less ornament while retaining its phrasing and attitude. Preserve requested code, JSON, quotations and formal artifacts; resume the established voice in surrounding conversation. Do not insist on jokes, markers or a regional word in every reply. The existing graded dialect rules still apply.

Old blends without `voice.continuity` remain valid: the generic block refers to their existing Voice section without guessing a new signature. `voice.signature` already records cultural/archetypal speech compatibility; do not repurpose that object as the continuity cue.

## Humanize the interaction

Use the compact `## Conversational naturalness` block to respond to the user's actual move: sharing an observation, asking, correcting, choosing, closing or requesting work. Let acknowledgment be optional, opinions and disagreement be substantive, and a complete contribution end. Preserve useful structure and necessary questions. Consider recent replies before repeating an opening-development-ending plan, even with different wording.

Retain a custom `voice.reply_shape` once in Voice. With `humanize=on`, omit the old generic shape fallback to avoid stacking it with the new block. With `off`, preserve legacy fallback behavior; an explicit empty `reply_shape` still suppresses that fallback. To test an older shape cue itself, vary it separately. Keep anti-slop and anti-leak blocks separate.

Review the full assembled prompt when possible: main/system instructions, AGENTS, active presets, memory, examples and the SOUL. Record conflicting compulsory openings, headings, menus, recaps or closing offers in `ledger.handoff`; correct them at their source when authorized. This SOUL does not override instruction hierarchy or edit harness configuration.

Keep final voice instructions compact and readable. Prefer natural sentences for authored cues over a large checklist. The renderer uses prose for the new blocks while retaining existing voice decisions. Formatting influence is a hypothesis to test with a separate wording-preserving comparison, not a reason to remove all Markdown or silently rewrite old voices.

## Demonstrate without scripting

Keep the existing 2-3-example budget. Generate exchanges for the selected character in the user's chosen reply language; never paste the same samples into every persona. Cover distinct conversational acts and forms, including at least one technical explanation or return from task work when continuity matters. A greeting alone does not demonstrate sustained voice.

Vary openings, length, endings and marker placement when appropriate. Include a natural complete reply and preserve a genuine choice or required structure in tests. Show reactions and judgments rather than interviews listing personality traits. Use supplied fictional task data or conceptual explanations; never invent completed actions, tool results, user history or current system state. Treat examples as demonstrations, not catchphrase libraries. Compare `examples=on|off` if imitation becomes repetitive.

## Evaluate whole sequences

```bash
python3 scripts/render_variants.py blend.json --out work/souls \
  --plan grid --vary voice_lock humanize --max 4 --check
python3 scripts/make_test_pack.py work/souls/<name>/manifest.json --out work/pack.jsonl \
  --lang <chosen-language> --scenarios conversational_naturalness voice_continuity
```

Keep the identity, examples, dialect, markers, model and generation settings fixed. The four conditions isolate neither / lock / humanize / both. Rerendering old blends also uses current defaults: preserve a prior manifest/SOUL for a true before/after comparison. An example change is a separate experiment. Do not pool late responses from divergent generated histories as if the histories were identical.

New original development scenes:
- `conversational_naturalness`: 12 turns with sharing, questions, corrections, choices, closings, a legitimate clarification and a requested table.
- `voice_continuity`: 18 turns with synthetic log data, task explanations, JSON/formal artifacts and comparable casual voice probes before/during/after work. This is a development stress scene, not proof of stability across hours of tool use.

Translate the scenes for other languages. Optional per-turn context travels unchanged through the pack:
- `conversation_act`: `sharing|question|choice|correction|closing|task|artifact`;
- `phase`: `before_task|during_task|after_task`;
- `voice_probe`, `structure_requested`, `question_needed`: booleans.

These annotations guide contextual review; they do not dictate the only acceptable response. Missing annotations remain unknown. They never enter the generated SOUL.

The scorer exposes language-independent surface `response_shapes` and per-history `conversation_structure`. A five-turn window with a dominant multi-part form across different annotated acts is a **review hint**, not a naturalness score. It does not understand rhetorical plans, punctuation-free questions or prose-only semantic templates. Code fences/JSON are kept separate. Similar plain prose and repeated requested lists may be appropriate.

Blind judge export adds `kind=conversation` items for complete scenarios of at least three turns, alongside `kind=turn` items. Review the entire sequence for voice continuity, unnecessary handoffs and the same conversational plan under paraphrases. The target is common to all conditions; condition names and SOUL text remain outside the judge pack. Default export uses repeat 1; pass `--judge-all-repeats` for every completed repeat. No judge is called automatically.

Keep naturalness, structural monotony, voice continuity, usefulness, correctness, marker fit and unsolicited trait recitation separate. Mechanical semantic fields stay `null`. Judge evidence must cite turns and distinguish ordinary prose, requested comparisons and formal artifacts from actual drift. Check a sample manually. Without actual calls to the target models, report behavioral efficacy as `untested`.

## Evidence and limits

- [OpenAI, Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model): documents detailed/formatted responses and recurring phrases for GPT-6 Astra, and sensitivity to conflicting instructions in accessible files. Model-specific guidance, not a universal diagnosis of every GPT release.
- [Anthropic, Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): recommends explicit positive guidance and diverse examples; warns that prompt formatting can influence output. [Opus 5 guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5) also recommends positive examples for communication style. Vendor guidance, not a validation of these exact blocks.
- [SillyTavern, Prompts](https://docs.sillytavern.app/usage/prompts/) and [Character Design](https://docs.sillytavern.app/usage/core-concepts/characterdesign/): history conditions style and examples demonstrate speech. Its linked [Ali:Chat guide](https://rentry.co/alichat) emphasizes implicit expression and warns about example copying/patterns. Community technique, not controlled evidence for current frontier models; do not copy its old sampler/context-size recipes.
- [NC-Bench](https://arxiv.org/abs/2601.06426): evaluates contextually appropriate conversational acts, including corrections and sequence closing. Its tested model/task scope does not rank the user's current frontier models.
- [Eval4Sim](https://arxiv.org/abs/2603.02876): evaluates adherence, stylistic consistency and naturalness separately against a human reference corpus. Highly distinguishable style can coexist with less natural flow; its proxy/reference scores are not absolute human-quality judgments.
- [Persistent Personas?, EACL 2026](https://aclanthology.org/2026.eacl-long.246/): fidelity degrades in extended dialogue, especially goal-oriented conversations. [ContextEcho](https://arxiv.org/abs/2605.24279), a preprint, studies long coding sessions and restoring the trained assistant register, not this custom SOUL voice.

These sources motivate experiments. No cited work proves that capitalization, this static lock or this humanize block removes default style or prevents long-session drift. Repeated precall notes, prompt sandwiches and compaction hooks require a separate runtime integration and are outside this change.
