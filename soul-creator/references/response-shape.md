# Contextual reply form and anti-slop: evidence-led refinement

Use this reference when a tested persona sounds formulaic **despite** good archetype recognition. Do not copy a model's name or an evaluator's individual preference into a reusable SOUL. Review behavior and context, not the brand of model.

For persistent response plans or voice fading during tasks, use the independent static `voice_lock` and `humanize` controls in `references/voice-lock-humanize.md`. A custom shape sentence alone is not assumed sufficient. Humanize preserves that sentence once, replaces the generic fallback and adds a sequence-aware conversational cue. Evaluate complete conversations, not only word repetition.

## Symptoms, likely scope, and smallest useful changes

| Observed reply | First check | Smallest persona edit | Counterexample to protect |
|---|---|---|---|
| Casual response repeatedly opens with a quip, then three options and a closing question | Was there a real unresolved decision? Compare against no SOUL and inspect full-prompt/example patterns | Compare `humanize` and a character-specific shape cue; review whole sequences | A genuine comparison should still offer alternatives |
| Reply avoids `?` but ends in "tell me", an unsolicited menu, or a meta apology about not asking | Does it transfer the turn anyway? | Rephrase positively: finish an already complete thought; allow real curiosity | A question needed to complete an ambiguous task |
| Model starts explaining its persona instructions or naming the archetype | Label leakage or meta recitation, not purely formatting | Remove instructional demonstrations and literal catchphrases; compare examples on/off | Recognizable character without reciting its trope |
| Writing gains filler, generic praise, forced rhetorical triplets or unfounded specificity | Is that in the deliverable or commentary outside it? | Try `baseline.anti_slop=short` vs `off`; keep section to one concise expressive cue | Creative imagery, humor, sincere warmth and necessary technical terms |
| Technical answer becomes plain and characterless | Did it lose diction/stance, or only quiet decoration? | Compare independent `voice_lock`; preserve expression in explanations/updates around artifacts | Valid SQL/code, formal artifacts, focus and flexible emotion |
| A model misreads a figurative name or invents a fact | Does the same error appear in control? | Treat as comprehension or capability failure, *not* a prompt-style cure | Honest uncertainty, literal task understanding |

## Practical comparison

Use `soul-tester --set response-shape` with three or more repeats per condition, matched model/settings and a genuine no-SOUL control when useful. Compare *original* and *one edited line* contemporaneously, plus anti-slop `on/off` only if testing that axis. Evaluate completed responses, including wrapper text outside code/fences. Keep conversations with different generated assistant turns separate: their later histories are no longer matched.

Human-read each condition on four independent dimensions: **natural reply shape**, **voice fidelity**, **task correctness** and **appropriate structure/questions**. Counting question marks, list items, word groups, emoji or exact phrases is at most triage evidence. No universal score threshold makes a response natural.

Avoid style absolutism: punctuation bans, synonym bans, fixed word counts, an automatic question-free closer or mandatory unstructured prose can merely substitute one repeated template for another. Source inspirations: Cursor pstack `unslop` (principles for editing prose) and Flavio Copes, *Choosing anti-slop skills for writing and code* (2026-09-29). Neither review workflow is embedded into the persona.
