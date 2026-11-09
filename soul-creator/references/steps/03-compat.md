# Step 3: Check compatibility

The source lists are hand-written and partial. Read them as hints.

## Procedure
1. In the catalog entries of your picks, read Pairs with and Clashes with. Check both directions (A lists B, or B lists A).
2. An empty list means undeclared, not safe. Judge by the descriptions. Example: tsundere lists no clashes in its YAML, but the Hersona README warns against mixing it with playful.
3. If a clash appears, choose one:
   - **Swap** a layer (cheapest).
   - **Use the clash as the gap.** Contrast is the point of many stereotypes: tsundere is cold words over warm behavior, hinedere is a bitter surface over a kind core. Write the contrast as a behavior in `blend.archetype` (without the label word).
   - **Lower the intensity** of one layer.
4. Check speech against temperament by hand; the catalog has no table for it.

## Hersona matrix (temperament: combines with / clashes with)
| Temperament | Combines with | Clashes with |
|---|---|---|
| tsundere | rival, childhood_friend | (empty in the YAML) |
| kuudere | mentor, rival, heroine | genki, playful |
| deredere | heroine, idol, childhood_friend | kuudere, stoic |
| dandere | childhood_friend, heroine | genki, playful |
| genki | childhood_friend, gamer_otaku | kuudere, pessimist, stoic |
| himedere | idol, heroine, rival | dandere, stoic |
| hinedere | mentor, rival | genki, optimist |
| kamidere | rival, mentor | genki, dandere, optimist |
| sadodere | rival, childhood_friend | protective, dandere |
| deadpan | mentor, rival | genki, hot_blooded |
| intellectual | mentor, heroine, rival | airhead, genki, playful |
| serious, stoic | mentor, rival | playful, genki |
| pragmatist | mentor, rival, heroine | hot_blooded, genki, airhead |
| laid_back | mentor, gamer_otaku | hot_blooded, serious |
| protective | mentor, heroine, rival | pragmatist, tsundere |
| sassy | rival, heroine, idol | socially_anxious, dandere |
| playful | gamer_otaku, rival | stoic, pessimist, kuudere |

Speech clashes worth knowing: keigo vs kansai_ben, ore_boy, boku_girl, genki; blunt vs theatrical, princess_speech, gyaru; formal_en vs casual_en, blunt_en. A strict identity lock can clash with playful overlays and dynamic facets; test it as the `identity_lock` variant axis.

The anchor features in `catalog/anchors.json` give a quick numeric check: a secondary that differs from the anchor by 4 points on the same feature (e.g. warmth -2 vs 2) is a clash to resolve, not a blend.

## Own affinities (inference, not from the source)
Good: sage + jester (hard truths as jokes), caregiver + ruler (protects with clear rules), deadpan snarker + only sane man, hinedere + mentor (complains and teaches), genki + sidekick, creator + explorer, tsundere + code reviewer, kuudere + detective, big sister + mentor, rebel + mentor (questions the established order without crossing limits), sociable + teacher (steady; the safest in long sessions).
Clashes: kuudere + genki, deredere + kuudere, tsundere + protective, himedere + dandere, serious + playful, jester humor during serious errors.

Ready-made combinations are in `references/examples.md`.

Compatibility checks affect expressive coherence only. Never resolve a clash by adding runtime policy or operational permissions to SOUL.

Output: `blend.json` with clashes resolved, and a ledger note on each resolution. Pass to step 4.

## Signature speech and dialects

Personality compatibility does not settle speech compatibility. Follow `references/voice-compatibility.md` for an archetype with strong literary/regional speech or when a referent supplies recognizable vocal habits. Keep the user-selected reply language independent. Use a strong compatible base with medium/low secondary colors, or record a deliberate reinterpretation after explaining what changes. The mechanism is language-agnostic.
