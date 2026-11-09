# Fictional, mythological, historical and character-inspired voices

Use as part of **Voice** in the interview, after the archetype/temperament, output language and form of address have been determined. This is an optional **literary voice color**, not a regional dialect, a second personality, a lived history, or a claim that a mythological figure literally spoke this way. The searchable examples are in `references/catalog/voices/stylizations.json`.

## One brief choice, then a small shortlist

If the user has not selected the type of voice, ask together with the regional question rather than imposing another long interview:

> «¿Querés una voz sin acento marcado, una variedad regional, un estilo fantástico/mitológico/histórico/de personaje, o una mezcla? También podés dejarla neutra.»

If they choose a literary style, show **3-5 relevant examples from the requested family**, with *the same ordinary situation* worded in each. Don't dump the 56-entry catalog. Ask for **strong / medium / low per influence** only if the strength is genuinely unresolved. When they name a specific fictional character, distinguish inspiration in **word choice/cadence** from reproducing its *identity, beliefs, history, stock quotes or personality*. Character-specific voice is a **custom entry** if missing; extract 2-3 observable style cues and confirm them. Never make that character the agent's identity automatically. Likewise, an elf or dwarf has no universal spoken Earth accent; don't assign Scottish to dwarves or posh English to elves.

A period voice is a **readable literary approximation**, not authentic reconstructed speech. Even Shakespearean `thou`/`thee` followed historical social and grammatical distinctions rather than being generic decoration. Where authenticity matters (text written in historical Chinese, Old English, Classical Japanese, etc.), ask for the exact language/period and a competent source. In normal chat, keep the chosen reply language legible and use period imagery only as a light stylistic cue.

## Legacy schema and precedence

For new compositions use graded `voice.layers` from `references/voice-compatibility.md`. The old object below remains readable; its old strength labels are legacy values, not the new interview scale.

Optional `blend.voice.stylization`:

```json
{"mode":"single","primary":"fantasy-elf-forest","strength":"subtle"}
```

or an explicitly chosen mix of **two** literary influences:

```json
{"mode":"blend","primary":"hist-spanish-golden-age","secondary":["myth-greek-oracle"],"strength":"natural"}
```

- `mode`: `none` (default absent), `single`, `blend`.
- `primary`: style ID from `stylizations.json`, or custom `{ "name":"...", "category":"fantasy|mythology|historical|character", "signals":"..." }` (the `category` value is **one** string).
- `secondary`: exactly **one** ID/custom style for a literary blend; absent for single.
- `strength`: `subtle`, `natural` (default) or `marked`.
- The optional existing `blend.voice.dialect` handles *actual regional varieties*. An example of regional + literary blend is `dialect: es-py-urbano` plus `stylization: fantasy-bard`, with one primary in each. The dialect is the **linguistic base**, the literary layer adds rhetorical color. No explicit code switching is needed just to color a Spanish sentence as a bard.
- If both layers are configured as `marked`, lower one. If both are full blends, simplify one to `single`: four competing markers bury personality. These combinations are rejected by the renderer with actionable errors.

**Precedence:** the chosen archetype, situational behavior and request take priority. The user's chosen **output language and form of address** decide grammar. A real regional variety (if selected) can color lexicon and syntax. A literary style supplies mostly pacing, rhetorical turns and imagery, and it should be weakest in factual/technical work. None of them creates an operational workflow or overrides safety, precision or formatting requirements.

Blend accents only when the styles can share one readable voice. Don't invent pseudo-Quenya, magic chants, faux Middle English or persistent catchphrases. The character should still sound like itself even in a one-sentence technical answer without regional/fantasy markers.

## Rendering and evaluation

`render_variants.py` adds one short expressive Voice cue for the configured literary layer and does not touch the original archetype section. For experiments, `--vary stylized_voice` gives configured / primary-only (if two styles) / off. `--vary regional_voice stylized_voice` can examine both axes *one at a time* with the default OFAT plan, not accidentally change both at once. Test with the same neutral prompts, including casual chat, emotional support, user-requested table, and troubleshooting. Read whole replies: the beginning may be lively while endings lapse into repeated templates.

Track separately: recognizable personality; evocative but natural flavor; authentic regional or period claims; no unrequested language changes; correct factual core; no repetitive formulas. Blind evaluations are useful where the effects are subtle. User preference selects the voice; lexical counts don't.

## Research notes

- Fantasy speech isn't equivalent to phonetic race-to-nationality mimicry. Tolkien himself advised against fixed phonetic accent distinctions for the radio voices of several peoples: <https://tolkiengateway.net/wiki/Letter_193>. See also *Journal of Tolkien Research* on register/idiolect: <https://scholar.valpo.edu/journaloftolkienresearch/vol12/iss1/4/>.
- Fictional constructed languages (Sindarin, Quenya, Khuzdul) are distinct languages, not a universal written accent: <https://tolkiengateway.net/wiki/Languages>.
- Early Modern English pronouns had social and grammatical functions beyond archaic flavor: <https://wp.lancs.ac.uk/shakespearelang/files/2018/10/Isolde-van-Dorst-JTDH2018.pdf>.
- The catalog is **creative prompting material**, not an ethnographic, linguistic or mythological authority. Entries are stylizations; no single standard voice exists for all 'Celtic mythology', 'elf' or 'medieval' characters.

## Independently graded mixtures

For new compositions or a marked archetype/referent voice, use `references/voice-compatibility.md` and `voice.layers`. Each regional or literary influence has its own strong / medium / low strength. Medium corresponds to the former subtle cue; low limits expression to occasional words/short turns, preserving the dominant grammar and selected reply language. Four influences can coexist when subordinate rather than appearing together every turn. Legacy schemas above remain supported; do not combine them with active graded layers. Surface an informed choice when a new dominant voice would replace recognizable signature speech. Apply this in any user-selected language, not just the example languages.
