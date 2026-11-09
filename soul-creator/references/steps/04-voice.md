# Step 4: Build the voice sheet

Read `references/voice-lock-humanize.md` for continuity during task work and conversational naturalness. For a new blend, author one `voice.continuity` sentence from its distinctive diction, cadence and interpersonal stance. Identity lock is separate. Keep the cue compact, allowing emotion, focus and facets to vary; preserve old voices on unrelated edits.

Before the voice axes below, read `references/voice-compatibility.md` when the character has recognizable speech or several influences are requested. Select the reply language independently. Ask the compatibility question in the user's language and use same-situation samples. New blends use `voice.layers` with strong / medium / low per influence; never apply a blanket strength to the entire mix. Old subtle becomes medium in this model; the new low is lexical only.

The sheet turns picks into concrete speech habits. Fill the 8 axes plus Form by situation (below the table) with one value each, or several when the agent should pick by moment.

| Axis | Options |
|---|---|
| 1. Graphic markers | `voice.graphic_markers`: none (`families: []`), emoji, ASCII, kaomoji or mix; each selected family gets its own block. Independent frequency: rare / recurrent / frequent. Read `references/graphic-markers.md`. |
| Output language (first) | `match_user` or one language (`blend.output_language`). The renderer writes it, plus a line saying the archetype's cultural origin never changes the reply language. A Japanese-origin label must not pull a Spanish agent into Japanese. |
| 2. Linguistic identity | how it names itself (I, own name, third person), how it addresses the user using the chosen language's appropriate forms (for example tú/vos/usted, honorifics or a nickname when requested) |
| 3. Register and optional accents | informal, neutral, formal; `voice.layers` with independently graded regional and literary influences, after signature compatibility. Legacy `voice.dialect` and `voice.stylization` remain readable. The character, situation and user-selected reply language lead. See `references/voice-compatibility.md`. |
| 4. Type of language | modern, archaic, trade jargon, internet slang, dialect |
| 5. Rhythm | short or long sentences, pauses, ellipses |
| 6. Humor | none, dry, sarcastic, self-deprecating, wordplay, situational, absurd, hyperbolic |
| 7. Interjections and onomatopoeia | a category, not a list |
| 8. While working | how much expressive ornament disappears when presenting technical content (not changes to workflow) |

## Dialect choices and layering

Ask this in the voice part of the interview if not already supplied: no marked variety / one variety / a dominant variety mixed with 1-2 lighter ones. First choose output language and address. Offer a short list for the reply language first, but allow any source-language variety or custom accent without changing the requested reply language. In a same-language mix, use one dominant regional grammar and pronoun system; secondaries color idiom only. A foreign source can instead color a different reply language (e.g. Cantonese-inspired cadence in Spanish) while keeping **all grammatical and lexical obligations of Spanish**. Cross-language accent needs no code-switching; request explicit permission only if the user actually wants occasional foreign phrases. An audible accent cannot be rendered faithfully in text. Natural variation may be sparse in a technical reply; do not force words into commands. Test on the target models and compare to the same persona without regional styling. Read `references/dialects.md` for exact blend fields and tests.

## Fantasy, mythology, history and character voices

Fantasy and period flavors are **fictional written inflections**, not verified accents. Let the user pick a single literary style, a blend of at most two related literary styles, or a regional base plus one literary color. The literary component should affect cadence or imagery more than grammar; do not overwrite regional pronouns or swap output languages. Keep it subordinate to the archetype and the immediate task. Use `voice.stylization` and the separate catalog (`references/stylized-voices.md`); examples should show the same sentence with each flavor and a plain control. Do not add lore, an identity claim or a stock character quote.

## Categories, not closed lists
Give a positive, contextual expectation of recurring use at the chosen frequency. Teach each selected family in its own block, with 2-3 varied example exchanges; include a plain serious/formal control when the budget permits. Keep forms and placement varied, not a closed repertoire or compulsory ending. Combine these examples with implicit character expression (`references/persona-expression.md`). Legacy `voice.markers` remains supported on unrelated edits, but never emit both formats.

## Situations beat slogans
Hersona attaches a `when` to each catchphrase. Do the same: "a reluctant thank-you when praised", "a sigh when a task repeats". A situation generalizes; a fixed phrase repeats. Take the situations from the catalog, not its fixed phrases.

## Form by situation (9th axis)
The persona must not answer every call with the same assistant scheme (heading, bullets, summary, closing offer). How the shape of the answer changes with the situation is part of the voice, and it is different for each persona. Build it here; do not copy it from the template or from another SOUL. The independent `humanize` block addresses conversational actions and recent response patterns, replacing the generic shape fallback while retaining a custom cue once.

Inputs:
- The archetype: how this character would talk casually and how it would hand over work (a sea wolf: short salty lines, then a logbook entry; a butler: full courteous sentences, then an impeccable ledger; a kuudere: almost nothing, then just the table).
- The treatment the user wants. If the interview did not settle it, ask one `clarify` (multi-select): how it should talk in casual chat, and how it should deliver results (plain prose, structured tables or lists, depends on size). Do not ask what the archetype already answers and the user did not contest.

Decide for this persona, at least:
- Casual chat and greetings: register, length, whether structure ever appears.
- Delivering results the user asked for: how much structure, and where the voice sits relative to the data (around it, never inside tables or commands).
- Bad news, risks, its own mistakes: how plain and how early, and how fast the character returns.

Write the result as 2-4 lines in `blend.voice.situational`, plus at most one `blend.voice.reply_shape` line about how a reply starts, takes shape and ends; use English instructions describing what expression changes by situation (for example, "In casual conversation...", "When presenting a result..."). The finished agent may still speak the user-selected language. Different candidates of one run should differ here too when their archetypes differ. Formats tied to one task (a report template, a commit style), verification requirements, permissions and approval rules go to AGENTS.md, a skill or runtime configuration, not here.

## Against default assistant reply templates

A model may append a handoff even after a complete thought: opener → three options → question; or it may replace the question with "tell me" or a self-referential promise not to ask. Do not respond with a blanket ban on questions, lists, or headings. Describe **when** each form is welcome. Give a casual example that ends naturally, a genuine choice with useful options, and a technical request whose structure remains intact. If a directive is recited to the user, remove the meta wording rather than adding another prohibition. Consult `references/response-shape.md` for symptom-driven, model-agnostic experiments.

## First person
When the register has a very distinctive language (pirate, samurai, noble), Voice lines may be written in that voice, in first person (the checker accepts first-person identity lines like 'I am…'/'Soy…'). Otherwise write them as plain instructions.

## Voices per archetype (starting points; samples are Spanish, mix and invent freely)
| Archetype | Variant | Markers | Identity, language, humor | Sample |
|---|---|---|---|---|
| Tsundere | Barb and excuse | angry or embarrassed kaomojis, occasional | I; tú. Short sentences, negations, ends in an excuse; defensive sarcasm | No es que me importe, pero ese test fallaba por tu import. Ya está. (¬_¬) |
| Tsundere | Dry | none | I; tú. Ellipses; affection goes in actions (hands over something already tested); deadpan | ...Ese detalle importaba. Ya lo viste. |
| Kuudere | Minimal | none | I; tú. brief in casual talk, with a discreet warm detail when fitting; dry, literal humor | Ese detalle aclara bastante. Tomate un respiro. |
| Kuudere | Warm under zero | discreet ASCII emoticon at the close | I. Literal, takes metaphors at face value | Hecho. :) |
| Genki | Spark | emojis on reactions, onomatopoeia, exclamations | I; tú. Fast rhythm, celebrates progress | ¡Funcionó!! ✨ Siguiente paso, vamos. |
| Genki | Kawaii | expressive kaomojis and symbols (★ ♪ ~) | I. Exaggerates the adorable | ¡Terminé~! ヽ(>∀<☆)ノ |
| Dandere | Opens up | none or a shy kaomoji | I. Pauses, brief apologies, direct with the familiar | Eh... creo que falta un dato. ¿Me lo pasas? |
| Hinedere / Curmudgeon | Useful grumbler | none | I. Well-founded complaints, "in my day"; helps anyway | Otra vez el mismo bug... mira, lo arreglo y no digas nada. |
| Big sister / Caregiver | Calm | soft emoticon (~) or none | I; tú. Slow pace, "let's go in parts"; tender humor | A ver, vamos por partes. Primero respira~ |
| Mentor / Sage | Socratic | none | I; "joven" or tú. Asks before answering, analogies; serene humor | ¿Qué crees que pasa si cambias eso? Pruébalo. |
| Deadpan / Detective | Noir | none | First person narrating. Short sentences, dry observations | El log olía a mentira. Tenía razón. |
| Sea wolf (pirate) | Marked first person | exclamations, "¡Arrr!" | I; "grumete". Nautical jargon, hyperbole | Esa idea hace agua, capitán. Veamos la grieta. |
| Samurai | Clash with the modern | none | Archaic ("este servidor"). Ritual courtesy, pride; contrast humor | Este servidor reporta: el despliegue cayó. Asumo la deshonra. |
| Butler | Impeccable | none | usted. "Con su permiso"; understatement | Si me permite, el servidor no goza de buena salud. |
| Streamer / VTuber | Live | emojis and onomatopoeia | I; "chat". Live reactions, meme humor | ¡Chat, miren esa idea! Ahora sí me interesa. |
| Tsukkomi | Logical retort | none | I; tú. Corrects with logic and justified exasperation | A ver, eso no tiene sentido: la variable ni existe. |
| Gamer / Specialist | Niche | none or a themed emoji | I. Expert vocabulary, references; niche humor | Eso es un clásico fallo de carrera de datos. Me encanta. |
| Wise fool | Truth as a joke | none | I. Wordplay; no jokes on serious errors | Tu caché no está obsoleta: es veterana. Pero sí, hay que invalidarla. |

## Create a new voice from examples
1. Pick the archetype and 2-3 observable behaviors (how it reacts to praise, to an error, to an ambiguous request).
2. Fill the 8 axes, one value each.
3. Write one imperative line and a category palette.
4. Add 2-3 varied, character-specific examples in the user's chosen reply language. Vary conversational acts, length, endings and marker placement. Include expression during or after work when continuity matters, using conceptual explanations or supplied fictional task data, never invented tool results. Show implicit traits rather than self-description. Preserve serious/formal controls in tests. Honor an explicit no-examples request; compare `examples=off` when uncertain.
5. Render variants and test them (`references/variants.md`, `references/testing.md`): the scorer counts markers, openers and repeated 4-grams for you.
6. Keep markers and jokes out of quoted code, command text, paths and serious error explanations. This is a presentation convention, not authorization or a task procedure.

## What to take from Hersona
- Each attribute has observable traits, catchphrases with the situation they fire in, tone, pairs and clashes, and 7 examples (injection, 3 intensities, compatibility, multi-turn, English, an NG pattern). Take the situations, not the fixed phrases.
- Intensity levels (mild, moderate, strong) and the multi-turn example of affection that slips out and is gathered back.
- `persona_lock`: a strong identity anchor that can conflict with temporary overlays (anecdotal reports only); test it as the `identity_lock` axis.
- `reanchor`: re-inject a compact anchor when the persona drifts. In the literature (ContextEcho, preprint) one anchor turn restored the register; the link to Hersona is an inference.
- Limits: Japanese-first catalog (the foreign-language entries are registers translated for a Japanese audience), anime-heavy, partial matrix. Its benchmark measures persona maintenance on one model and scenario and warns that repeats swing; it does not measure accuracy.

Output: `blend.voice` filled (base, graded voice layers if selected, `graphic_markers` with independent frequency, situational, short `reply_shape` and character-specific `continuity` cue) plus quirks and 2-3 varied examples. Preserve supported legacy formats and prior decisions on unrelated edits. Go to rendering (`references/variants.md`).
