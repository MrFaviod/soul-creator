# Regional voice: optional layer inside the voice interview

Use with `references/steps/01-interview.md` Phase D, then `references/steps/04-voice.md`. The searchable options live in `references/catalog/voices/dialects.json`; this document explains how to choose and apply them. It does **not** assign a nationality, ethnicity, lived experience or biography to the persona. The archetype/temperament and user's requested content remain primary.

## Ask the user by sound, not by a country checklist

After language, form of address, archetype and intensity have been settled, ask in one compact question **unless already specified**:

> "¿Preferís una voz sin acento marcado, una variedad regional (por ejemplo, rioplatense), un estilo de fantasía/mitología/historia/personaje, o una mezcla?"

Translate naturally into the interview language. That same voice question includes fictional, historical, mythological or character-inspired style or a mixed regional + literary voice. Those are **not real-world dialects**; handle them with `references/stylized-voices.md` and `voice.stylization`, not by smuggling fantasy categories into `dialects.json`.

If the user chooses a **regional** voice, ask single or blend and show a **small, relevant shortlist**, not all ~67 entries. Start by fixing the **reply language independently**. Offer varieties from that language first, but accept an influence from any other language (e.g. Spanish replies with a Cantonese-inspired accent). Ask whether the user wants native regional usage or cross-language accent color only if their intent is unclear. In cross-language use, target-language grammar and forms of address always win. For a blend, select the dominant voice influence and lighter secondary nuances. Ask about code-switching **separately**; selecting a foreign accent never authorizes switching languages. Finally ask for **strong / medium / low per influence**, with the same neutral content illustrated in each degree. Skippable; no regional voice is an ordinary, valid choice.

Don't repeat known answers. Show 2-3 short samples of **the same situation** in the user's selected voice (informal chat, empathy or an ordinary technical explanation), not stereotype parodies. A choice like "English" must not silently mean US or UK; "Chinese" must not silently mean Mandarin vs Cantonese. If the model cannot generate a variety reliably, say that and request authentic examples instead of making them up. Regional dialects are not intrinsically rude, funny, servile or charming. Those behaviors belong to the personality and context.

## Legacy model and render fields

For new multi-layer compositions use `voice.layers` in `references/voice-compatibility.md`. The older object below is still readable for existing blends; its old subtle/natural/marked vocabulary is not the new interview scale.

`blend.voice.dialect` is an optional object:

```json
{"mode":"blend","primary":"es-ar-rioplatense","secondary":["es-mx-urbano"],"strength":"natural","code_switch":"off"}
```

- `mode`: `none` (no regional cue), `single` (one variety only), or `blend` (dominant + one or two secondaries).
- `primary`: ID from `dialects.json` or an explicitly researched `{ "name":"...", "language":"es", "signals":"..." }`. Don't alter the catalog to encode one user's preferences.
- `secondary`: array of 1-2 IDs or custom objects; only for `blend`. No duplicate variants.
- `strength`: `subtle`, `natural` (default), `marked`. These are presentation degrees, **not percentages** and never stronger than the core identity.
- `code_switch`: `off` (default), `contextual` (opt-in for occasional meaningful code switching, independent of the variety's source language). A cross-language accent works with `off`. Jopará is a documented contact variety and may mix languages naturally in its own context, but is not a license to abandon a separately requested output language.
- `application`: `auto` (default: authentic written variety if compatible with the reply language, otherwise a limited accent influence) or `accent` (even if the source language matches, emphasize only transferable delivery cues; useful when the user says “accent”, not full dialect).

Set `blend.output_language` independently and give it precedence over every dialect or stylization. With `match_user`, follow the language requested in the current turn; when that language matches the source variety, render its native patterns, and otherwise translate the **voice impression**, not its language or grammar. With a fixed `output_language`, source varieties from other languages are **accepted as accent inspirations**, not rejected or interpreted as permission to change language. The separate `blend.language` label names the *reply language* (“Spanish”), never the source accent (“Cantonese”). Explicitly requested translations and quotations keep their intended language per `language_policy`.

```json
{"mode":"single","primary":"es-py-jopara","strength":"subtle"}
```

Jopará deserves a separate contact-language entry: it is not simply Paraguayan Spanish with an obligatory Guaraní greeting, nor necessarily one standardized language. The model may use insertions or code-switching when authentic and appropriate; when unsure, use the base language cleanly rather than inventing words. <https://cvc.cervantes.es/lengua/anuario/anuario_20/alcaraz/p01.htm> and <https://www.degruyterbrill.com/document/doi/10.1515/9783110334845-023/html>.

## Render and test without imposing quotas

The renderer adds **one** regional Voice line. When source and target languages match, the chosen primary may supply grammar/address/cadence and same-language secondaries may color idioms. When they differ, the **requested language owns grammar, spelling, pronouns and vocabulary**; the source only suggests carefully grounded cadence or pragmatic delivery, if textual expression makes sense. The cross-language case must not quote the source dialect's native grammar instructions as if they applied to Spanish, English, etc. The personality determines which moments invite expressive markers. Do not make a list of catchphrases, percentages, regional words per answer, invented phonetic misspellings or stereotypes. Keep dialect out of code, paths, citations, quoted sources and technical literals.

Use `--vary regional_voice` to compare baseline (configured mix or single), dominant-only (if a blend exists) and regional voice off, **without altering other axes**. The renderer skips unavailable/duplicate conditions. If the user also wants to compare different dominant regions, prepare two named blends or explicit scenarios and compare contemporaneously on the same prompts. Choose per conversation, not by counting buzzwords in each reply. `soul-tester` should sample a chat reaction, empathetic exchange and technical answer, ideally across multiple turns.

Qualitative checks: personality remains recognizable, target-language grammar and address remain correct, regional accents remain subordinate, no unrequested foreign language or invented “learner errors”, secondary markers show up only when natural **across the conversation**, no stacked stereotypes or invented biography, and technical artifacts remain untouched. Do not claim native authenticity without speaker review. Cross-model comparisons are not evidence of a universal winner.

## Linguistic boundaries and references

This is a **text** feature: many Russian and Japanese regional distinctions are phonetic, and written dialect markers may be sparse. Treat Japanese Ryukyuan languages and several Sinitic varieties as distinct languages or groups, not amusing substitutes for standard Japanese or Mandarin. Cantonese, Wu and Min are not interchangeable Mandarin accents. <https://www.britannica.com/topic/Chinese-languages> and <https://pmc.ncbi.nlm.nih.gov/articles/PMC6561542/>.

Grounding for sampling and refinement (the entries remain prompts, not a linguistic corpus):
- RAE/ASALE on voseo and its regional forms: <https://www.rae.es/dpd/vos>.
- Instituto Cervantes on Spanish–Guaraní contact: <https://cvc.cervantes.es/lengua/anuario/anuario_20/alcaraz/p01.htm>.
- British Council on diverse World Englishes: <https://www.britishcouncil.org/english-language-day>.
- University of Iowa on Russian north/central/south distinctions: <https://pressbooks.uiowa.edu/russiancareer/chapter/recognizing-some-dialects-of-the-russian-language/>.
- Chinese language groups: <https://www.britannica.com/topic/Chinese-languages>.
- Portuguese European/Brazilian/Angolan: <https://academic.oup.com/edited-volume/63048/chapter-abstract/566523091>.
- Arabic Egyptian/Levantine/Gulf/Iraqi/Maghrebi grouping: <https://direct.mit.edu/coli/article/40/1/171/1458/Arabic-Dialect-Identification>.
- Japanese vs Ryukyuan classification: <https://pmc.ncbi.nlm.nih.gov/articles/PMC6561542/>.

## Cross-language accent example

```json
{"output_language":"es", "language":"Spanish", "voice":{"dialect":{"mode":"single", "primary":"zh-yue-cantonese", "application":"auto", "strength":"subtle", "code_switch":"off"}}}
```

This means *respond in natural Spanish*, with at most a faint, non-caricatured trace of Cantonese-inspired conversational cadence where it can actually be expressed in text. It does **not** mean write in Cantonese, use Cantonese grammar/particles, transcribe a phonetic accent, translate loanwords into gibberish or portray a Cantonese person. Text cannot reproduce a spoken accent faithfully. If the user wants an audible accent, that is a separate voice/audio production task; request speaker examples for authenticity if needed.

A multi-language accent blend also works without code-switching. Leave `code_switch=off` unless the user specifically wants occasional foreign phrases, and keep those rare enough for the reply language to remain unambiguous.

## Independently graded mixtures

For new compositions or a marked archetype/referent voice, use `references/voice-compatibility.md` and `voice.layers`. Each regional or literary influence has its own strong / medium / low strength. Medium corresponds to the former subtle cue; low limits expression to occasional words/short turns, preserving the dominant grammar and selected reply language. Four influences can coexist when subordinate rather than appearing together every turn. Legacy schemas above remain supported; do not combine them with active graded layers. Surface an informed choice when a new dominant voice would replace recognizable signature speech. Apply this in any user-selected language, not just the example languages.
