# Step 6: Refine (Round B and later: open questions with examples)

Round A asked specific questions to find a blend. The user now sees candidate comparison results from `soul-tester` (or an explicit `untested` notice), then chooses a draft to refine. From here the questions are about how it feels, not about operational parameters. Repeat until the user is satisfied. The agent's own satisfaction never ends the loop.

## 1. Show something to react to
- Show the draft, or only the changed lines after the first round, plus three sample exchanges in the voice: a greeting, thanks or praise, and an error or disagreement. Add a sample result presentation when relevant, to show how expressive flourishes shrink around technical content; do not invent tool runs.
- Samples are for reacting. They go into `blend.examples` only if the user asks, and then 2-3 that differ from each other.
- Do not explain design choices at length.

## 2. Ask how it feels (one `clarify` call)
After presenting the tester report and candidate choices (see `references/tester-contract.md`), ask which candidate to refine, then ask: 'How does it sound to you?' with an example inside each choice:
- It is what I imagined.
- Too much (show a line with the loudest feature of the draft: markers, tease, length).
- Too little, it sounds like a normal assistant (show a line without the persona).
- Right voice, but its expression feels off (jokes at the wrong time, chatty during technical explanations, awkward disagreement tone).
'Other' covers a different direction. If the user chooses it, ask one open question: 'What were you picturing: a character, a person, a moment?' If the direction is entirely different, return to Phase B/C (archetype) or Phase D (voice, layers) of `01-interview.md`.

## 3. Narrow the complaint (second call, only if needed)
Answer with before/after lines, so the user picks by sound:
- Too much: which part? markers / attitude / length / quirks. Offer the same reply with that part turned down.
- Too little: what is missing? sharper jokes / more concrete tastes / more markers / more attitude. Offer the same reply with that part added.
- Works strangely: which moment? errors / while working / disagreeing / endings. Offer the reply in the corrected behavior.

## 4. Apply the change
One or two changes per round, in `blend.json`, only in the fields that cause the complaint, so cause and effect stay readable. Re-render (`render_variants.py --plan baseline` for a single file, or vary the axis you're unsure about) instead of hand-editing one SOUL file.

| Complaint | Lever |
|---|---|
| Too many markers, too loud | Lower the intensity one level; marker frequency 'rarely'; keep the category palette |
| Sounds like the default assistant | Check the label probe: if the model doesn't know the label, switch to label+gloss or description. Otherwise add situations to Voice, sharpen a taste, firm up the directive; no caps |
| Barbs hurt | Aim them at the situation (Archetype); soften the temperament layer |
| Jokes at the wrong moment | Voice: reduce expression around serious or technical content |
| Repeats the same phrase | Remove fixed examples and closed lists; keep 'vary the form' |
| Too long | Shorter prose rule; cut sections the draft does not need |
| Repetitive opener → menu → closing question | Compare `humanize` and the custom shape cue on whole `conversational_naturalness` sequences; inspect examples/full-prompt conflicts |
| Voice fades during work | Compare `voice_lock` and a character-specific `voice.continuity` cue on before/during/after probes; preserve artifact format and flexible mood (`references/voice-lock-humanize.md`) |
| Generic filler or canned compliments | Compare `baseline.anti_slop` short vs off; check that character and creative imagery survive |
| Wrong archetype | Back to Phase B/C of the interview: `--reject` the anchor and continue narrowing |

Never insert, change or relax operational rules, approval policy or secret handling in SOUL to fix a style complaint. Check the ledger from the interview before every edit: a fix must not undo something the user decided, and must not reintroduce something rejected. Add new decisions and rejections to the ledger.

## 5. Loop and stop
- Repeat show, ask, apply. After the first round, ask only about what changed.
- After three rounds without convergence say so and offer two options: start again from another candidate, or live with the current draft for a few sessions, since taste is easier to judge in use.
- After meaningful changes, rerun the relevant `soul-tester` checks if available; otherwise label the updated draft `untested` for those dimensions. When the user says it is right, run final validation in `SKILL.md`. Report what was tested and what was not.
- Writing the result into a profile's SOUL.md needs the user's approval and a profile they named. Otherwise deliver the text in chat.
