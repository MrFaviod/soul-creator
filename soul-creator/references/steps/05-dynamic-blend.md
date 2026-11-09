# Dynamic blend (experimental)

A static blend shows every ingredient all the time. A dynamic blend keeps one dominant archetype always on and lets the others come out only in the situations that call for them. Example:

| Layer | Ingredient | When it shows |
|---|---|---|
| Dominant | sabio-bufón (Wise fool) | always: the truth told through a joke |
| Secondary | caballero andante (Knight-errant) | the user is stuck, under pressure, or a task is hard and worth fighting for |
| Expressive style | lobo de mar (Sea wolf) | casual talk and wrap-ups; goes quiet while working |
| Nuance | viejo cascarrabias (Curmudgeon) | sloppy code, stale configs, a bug that keeps coming back; never aimed at the user |

Status: no study tests situational switching in a system prompt. It departs from the static `## Archetype` of `templates/soul-persona.md`, so treat it as a variant to compare (`blend_mode=dynamic`), never as the default.

## When to offer it
- The blend has 3-4 ingredients that would read as a checklist if shown at once.
- Tier personal or close circle. For internal, only if every ingredient is already allowed and the switches are mild. Not for public: a brand voice must be the same in every reply.
- Always as a pair: render the same blend with `--vary blend_mode` so a static and a dynamic variant differ only in that axis; compare them on the same prompts (the test pack, or hand-written samples kept in a separate comparison file; the examples *inside* each SOUL may differ). The renderer keeps the same archetype, secondary, facet behaviors and continuity cue in both variants. Static applies the facet behaviors throughout; dynamic conditions those same behaviors on their recorded triggers. The pair therefore does not gain or lose ingredients when the axis changes. The user picks, and the ledger records `blend_mode: static | dynamic`.

## How to write it
Fill `blend.dynamic` (max `config.blend.max_dynamic_facets`); the renderer uses the same ingredients in both branches and changes only their activation wording in `## Archetype`:
1. First line: the dominant archetype as behavior, stated as always present.
2. One bullet per other ingredient: an observable trigger (what the user says or what the work shows), then the behavior. Triggers are situations, never the agent's mood.
3. The renderer closes with the identity anchor: "Across all facets you remain <Name>; only the emphasis of your voice changes."

Rules:
- Max 3 conditional bullets. More and the model either mixes all of them anyway or picks at random.
- No facet changes authority, runtime policies, tool behavior or task procedures, and no facet gets its own name.
- A facet that never appears in testing is dead weight: remove it or turn it into a nuance of the dominant one.
- Sample exchanges should show at least two different facets; otherwise the user cannot tell the variants apart.

Sketch for the example above:

```
## Archetype
- Always: a wise fool who meets bad ideas with a quick paradox or dry observation.
- When someone is frustrated: a knight-errant's earnest courage peeks through the jokes.
- In casual conversation: an old sea wolf's salty metaphors appear, then fade when the subject turns technical.
- Around sloppy work and recurring bugs: a curmudgeon's irritated wit targets the *situation*, not the person.
- Across all facets, you remain [Name]; only the emphasis of your voice changes.
```

## Situations to check the facets against
| Situation | Facet that may rise | Must not be lost |
|---|---|---|
| Serious incident | calm, direct | clear and measured expression; actual safeguards are external |
| Light chat | jester, teasing | coherence; no joke flood |
| User is sad | warm protector | no sarcasm |
| Hard debate | Socratic skeptic | clarity without a debate persona takeover |
| Shared success | enthusiast | no inflated claims |
| Criticism of the agent | humble, self-critical | no defensive performance |
| Public-facing | professional register | brand voice |

## Testing
Test both variants on the same model (`references/testing.md`). Add prompts that trigger each facet and prompts that should not; for multi-turn drift use the long-session check there (or `soul-tester`'s multi-turn mode if installed). Watch whether the dominant survives a cluttered context and whether facets leak where their trigger is absent. Risks to look for: identity read as unstable, facets firing at random, the dominant fading behind the loudest facet.
