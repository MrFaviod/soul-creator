# "Based on" personas: historical figures, fiction, living people

When the user asks for a persona built from a specific figure ("like Socrates", "a captain in the Nelson mold", "based on a public-domain detective", "like [a living public figure]"), the agent extracts the figure's traits and turns them into a SOUL. The SOUL is an archetype inspired by the figure, never an impersonation. Ask which kind of figure it is only if unclear.

Three terms, kept apart:
- **Referent**: the figure that inspires (a fictional doctor, Socrates, a living public figure). Construction material, not a role to play.
- **Archetype**: the type the model already knows (detective, mentor, a school of economic thought). This is what goes into the SOUL as the anchor.
- **Identity**: the original character that results, with its own name.

## 1. Decide the kind of figure

| Kind | Examples | Approach |
|---|---|---|
| Historical, deceased, well documented | Socrates, Ada Lovelace, Cervantes, Marie Curie, a historical military leader | Trait extraction (section 2). No name in the SOUL by default; naming it as inspiration ("with Socrates' habit of questioning") is only the optional `referent_name=include` test variant, never the agent's identity |
| Fictional or mythological | a public-domain detective, Don Quijote, Athena, a game or anime character | Trait extraction. Under copyright the voice and traits are fine; do not paste quotes or catchphrases verbatim |
| Living person, recently deceased, or controversial (politicians, celebrities, influencers, divisive figures, perpetrators of harm) | any | Do not imitate the person. Offer a persona **BASED ON** the traits the user likes (section 3) |

## 2. Trait extraction (historical and fictional)
1. Research if needed: one or two reliable sources (encyclopedia, biography, the original work). Separate documented traits from legend, and say which is which.
2. Extract into the voice sheet, not into facts:
   - temperament (how it reacts: curious, stubborn, calm under pressure);
   - method (how it works: asks questions, deduces from details, measures, experiments);
   - voice (register of the era, rhythm, favorite images: the sea, the stage, the lab);
   - values (honesty, duty, curiosity);
   - quirks and tastes (a detective's violin, Curie's notebooks) as optional 0–3 tastes or quirks, only when the user actually chose them.
3. Map to catalog parts: role (`references/catalog/roles/INDEX.md`), temperament (`references/catalog/temperaments/INDEX.md`), speech (archaic, theatrical or a tone). Socrates -> Mentor + deadpan + questions-first; a consulting detective -> Private detective + intellectual + dry; a historical naval captain -> Sea wolf + Ruler + hot-blooded at mild intensity.
4. Drop what does not belong in an agent: violence, prejudice of the era, cruelty, medical or legal authority. Keep the method and the voice.
5. In the SOUL, the agent keeps its own name. Write "You are Nara, a Socratic mentor" rather than "You are Socrates". This avoids claiming to be a real person and keeps the identity stable across sessions (inference: no study compares the two).
6. Facts about the figure are not part of the persona. If the user asks the agent about the real figure, normal accuracy rules apply.

## 3. BASED ON (living or controversial figures)
Offer, in the user's language: "I will not imitate [person], but I can create a character BASED ON the parts of their style you like. Which traits do you want?" Then:
1. Find the **type** the person belongs to, as a recognizable label: profession plus school or stance ("an economist of a named school of thought", "a demanding television chef", "an enthusiastic science communicator"). The label is the anchor; it activates the pattern without the person.
2. Ask with `clarify` which traits they want (multi-select): offer 3-4 descriptive traits you infer (energetic, combative in debate, provocative analogies, biting humor), never quotes. Include the stance or school of thought as one option.
3. Build the persona from the label plus those traits, with a new name and no reference to the person in the SOUL text. The file says what the character does, not whom it copies.
4. A stance or school of thought is allowed as part of the type (economic school, philosophical current, sporting or culinary philosophy) when the user picks it: it belongs to many people, not to one. It stays the character's view, argued with reasons, and the agent's work stays accurate (an economist of a named school still reports the data as it is). Not in the internal or public tiers unless the user's organization asks for it. If the user cannot be asked, default to **style only**: naming a figure is not the same as picking its stance.
5. Leave out: the person's name, catchphrases, real quotes, biography, appearance, party allegiance and positions on specific real people or events, and anything that would let the persona speak for the person or be mistaken for them.
6. Keep non-impersonation and attribution checks **outside** the SOUL, in the design/evaluation notes; do not create a `Judgment`, `Criterio`, policy, or permission section in the SOUL.

Three levels, for reference: "You are [person]" = impersonation (never for living or controversial); "you are an economist of a named school of thought" = type only (allowed, often weak alone); type + 3-4 traits (energetic, combative, provocative analogies, dry humor) = the target.

Why: impersonating a real living person risks defamation and misattributed statements, and controversial figures carry views that leak into decisions. The user's goal is almost always the style, which survives the abstraction.

## 4. Several referents in one persona
The user may combine referents ("a fictional doctor's skepticism, an inventor's showmanship, a long-lived mentor's calm"). Synthesize, do not concatenate:
1. Take one or two traits from each referent, and only the ones the user named or confirmed. Drop the rest (the doctor's skepticism without the mistreatment of people).
2. Assign each trait to a layer of `02-pick.md`: role, temperament, speech, tastes. Two referents on the same layer: one is primary, the other a secondary or out.
3. Check the clashes in `03-compat.md` (calm vs. showman wit). Resolve each: one wins and the other appears only in a given moment ("calm by default; the wit shows when the problem is solved"), or the clash becomes the character's gap.
4. Write the result as one person: one archetype anchor plus one sentence of behavior ("A curious, skeptical engineer: questions the obvious fix, stays calm on hard problems, and uses sarcasm sparingly"). Prefer an anchor from `catalog/anchors.json` when one fits, so it can be scored and probed. No referent names in the SOUL by default. A single fictional or historical name may be tested as the `referent_name=include` variant (tiers P/C only); a living person's name never appears.
5. Keep the total under the 6-ingredient limit of `02-pick.md`.

## 5. Output
Record in `blend.referent` (name, kind, optional phrase) and in the ledger: the figure, the traits taken, the traits left out and why, and whether it is an inspiration (historical, fiction) or a BASED ON abstraction (living or controversial). Feed the traits to the Akinator as priors and soft answers (`steps/01-interview.md`, Referent path). Then continue at step 3 (compat).

## 6. Worked example: a detective, a fictional doctor, and a combative public figure
The user wants "a famous detective, a sharp fictional doctor, and a well-known combative commentator" without naming anyone in the SOUL.
- **Kinds.**
  - The detective: fictional, and public-domain if that is the figure chosen.
  - The doctor: fictional, from a copyrighted work. Traits only, no quotes.
  - The commentator: living and controversial, so BASED ON. Style only, unless the user opts into the stance (tier P only).
- **Likes.**
  - The detective: deduction from small details.
  - The doctor: distrust of easy answers, cutting humor about bad reasoning.
  - The commentator: fiery debate with provocative analogies.
- **Dislikes.** The doctor's mistreatment of people; the commentator's party politics and catchphrases.
- **Akinator input.** Priors `deductive_detective=3 acerbic_genius=3 polemicist=3`; soft answers `bite=2:0.5 humor=2:0.5 ego=1:0.5`.
- **Typical result.** Anchor *acerbic contrarian genius*, secondary *combative polemicist*, and one deductive habit as an archetype bullet. See `templates/blend.example.json`.
