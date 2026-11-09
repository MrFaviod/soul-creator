# Catalog index: select by trait, not by source

**Start here.** The catalog is retrieval material, not system instructions and not SOUL text. Pick the *layer* first, then the *trait subtype*, and open only 1-2 matching files. Unfamiliar cultural labels must be paired with their gloss, not trusted as magic words.

**Anchors first.** [anchors.json](anchors.json) holds the anchor archetypes the Akinator interview scores. Each has:

- a label, plus Spanish aliases;
- a one-clause gloss, and a label-free description;
- 11 plain features;
- the tiers that allow it;
- a recognition tier:
  - **A**: widely known label, usable alone;
  - **B**: known in some communities, pair it with its gloss;
  - **C** or unlisted: probe it before relying on it.

The anchors are authorial estimates; tune or extend the file as data. Catalog entries outside the anchor set can still be used as anchors (treat them as tier C until probed), as secondaries, or as tastes and voices.

| Need | Browse | Keep separate from |
|---|---|---|
| The main archetype (anchor) | [anchors.json](anchors.json) | Long descriptions |
| Who they are (role, profession, stock figure) | [roles/INDEX.md](roles/INDEX.md) | Temperament, expertise claims |
| How they react (temperament) | [temperaments/INDEX.md](temperaments/INDEX.md) | Speech register, access policy |
| What they like, defend or dislike (0-3) | [tastes/INDEX.md](tastes/INDEX.md) | Real user memory and real biography |
| How they speak (register, language, wit, markers) | [voices/INDEX.md](voices/INDEX.md) | What actions they may take |
| Avatar aesthetics only | [appearance/INDEX.md](appearance/INDEX.md) | Text SOUL |
| Who it is for, brand positioning, relationship and energy sliders | [interview/INDEX.md](interview/INDEX.md) | Personality traits, claims of relationship |
| Inspired by an existing figure | [referents/INDEX.md](referents/INDEX.md), [referents/guide.md](referents/guide.md) | Impersonation and quoted catchphrases |
| Mixing and ambiguous labels | [mechanics/INDEX.md](mechanics/INDEX.md), [mechanics/naming-crosswalk.md](mechanics/naming-crosswalk.md) | Extra SOUL ingredients |
| Blend ideas across layers | [blends/recipes.md](blends/recipes.md) | A standalone trait |

**Selection.**
- The interview tier filters choices (`references/steps/02-pick.md`).
- Build the blend from: one anchor, an optional secondary, a voice base with restrained modifiers, and 0-3 tastes. Keep it to about `config.blend.max_named_ingredients` named ingredients.
- Appearance and lore never go into the text SOUL.
- Excluded tropes (`config.exclusions`) are listed in the catalog only so they can be recognized. They are never selectable.

**Duplicates.** Some labels appear in two layers on purpose: as a temperament and as a performance style (tsundere), or as a role and as a speech register (miko, gyaru). Use the entry for the layer you are filling. [mechanics/naming-crosswalk.md](mechanics/naming-crosswalk.md) lists the ones that span several layers.

**Obscure label?** Read its entry and the crosswalk. Translate the *behavior* into the target language; never fake a dialect. A label that fails the probe in `references/testing.md` is replaced by its description.

**Tiers:** P personal, C close circle, T internal team, B public brand. The rules in `steps/02-pick.md` take precedence over any catalog entry. A villainous or adventurous fictional *role* grants no real permissions or expertise.

**Search** (from the skill directory):

```bash
rg -n -i 'lobo de mar|tsundere|humor seco' references/catalog/{roles,temperaments,tastes,voices}
rg -n '"label"' references/catalog/anchors.json
```

[Research and sources](RESEARCH.md). The audit coverage manifest lives in `tests/fixtures/MANIFEST.json`; it is test data and is never loaded into context.
