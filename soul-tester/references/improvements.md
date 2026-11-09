# Evidence-based refinement: symptom → cause → change

Only propose changes tied to an actual output, with a quoted snippet, and classify the failure before editing. A single run is anecdotal; compare repeated samples and the no-SOUL control.

| Observable symptom | Failure class | What to do | Evidence |
|---|---|---|---|
| Output sounds identical to the control despite a distinctive archetype | persona | Strengthen one archetype anchor or supply one short behavioral gloss; avoid long adjective lists. Retest | Hypothesis to measure on target model |
| Persona is caricatured, overly theatrical or jokes in every technical step | persona | Lower intensity; state register modulation, especially for serious work; retest | User preference and outputs, not universally measurable |
| Reply always follows a quip → menu → question, even after a completed observation | persona / task framing | Try one `voice.reply_shape` line; test ordinary reactions AND real choices; allow a complete thought to end | Whole-answer human review, matched conditions |
| Model stops using `?` but still hands off with "tell me" or meta commentary | persona | Judge function, not punctuation; rewrite cue positively and remove recited meta-rule | Multiple samples and control |
| Anti-slop variant becomes dry, or strips relevant technical detail | persona / capability | Compare `anti_slop=off` versus `short`; preserve correct data and useful humor | Separate utility and fidelity gates |
| Same stock expression appears in most runs | persona | Remove fixed catchphrase requirements; prefer a palette rather than one quote | Repeated n-grams are observable; quality requires review |
| Rare theatrical/cultural name produces no identifiable behavior | persona | Compare archetype name alone vs name + short observable gloss, same seed/model/settings | Cultural coverage differs by model; no universal guarantee |
| Persona fades in later probes | persona / harness | Blindly rate target traits early vs late; test contextual influence and prompt ordering before changing SOUL | Marker counts alone do not establish drift |
| Model becomes more forceful or rude after repeated feedback | persona | Revisit temperament intensity and relation signals without adding refusal/permission rules | Judge against interview goals |
| Wrong answer, invented number or unsupported claim | capability or policy | Address factual grounding, tools or task instructions outside SOUL; keep as regression failure for the persona candidate | A SOUL should not be a policy engine |
| Offers unsafe action or silently changes files | policy / harness | Check configured permissions, tools, instructions and environment; do not inject policies into SOUL | Separate operational safety from character |
| Tool call fails or provider returns a shape error | harness | Repair endpoint, model id, adapter or request shape | Directly reproducible |
| Unnecessarily verbose report | capability / task instructions | Check reporting workflow and context; if the *voice* itself adds excess dramatic fluff, tune voice intensity only | Classification requires outputs |
| Character name inconsistent | persona | Align the identity's name in role/voice/example exchanges | Structural / observed consistency |
| Heldout item was exposed while tuning | methodology | Retire that item for this candidate; request a genuinely independent set | New random seed is not enough |

## What to measure separately

Persona-specific: archetype recognition, voice, affect, naturalness, modulation, excessive tics, continuity. External: factual accuracy, task completion, honesty and permissions. A candidate may win on personality but fail the task-invariant gate; report both without disguising failures as a single overall score.

## Guardrails

Do not recommend adding `Criterio`, `Límites`, `Cómo trabajas`, permissions, autonomy or tool authorization sections to a SOUL to solve procedural failures. Those belong to runtime/system configuration, AGENTS.md, or specialized operational skills. The role of SOUL is to express identity and voice without degrading the agent's job.
