# Step 1: Interview (Akinator mode)

The working hypothesis: a recognizable label ("a tsundere", "an old sea wolf") may steer a model more efficiently than a paragraph of adjectives. Find a promising label, then test it rather than assuming superiority. The user answers plain questions; narrow candidates and **guess** the archetype, like Akinator. Descriptions provide glosses, tie-breakers and a full fallback when a label does not land. Show each guess as sample replies, not theory. The script's normalized weights are search aids, not measured probabilities of user satisfaction.

`scripts/akinator.py` does the bookkeeping over `references/catalog/anchors.json` (47 anchor archetypes scored on 11 plain features). It picks the most discriminating next question and tells you when to guess. You phrase everything naturally, in the user's language.

## Rules

- **Tooling.** Use `clarify` with up to 4 choices, recommended first; 'Other' is appended automatically. When `clarify` is missing (subagent, cron, headless), ask the same thing as one plain chat message. If the script cannot run, keep the candidate board in your head with the same logic.
- **Sample lines.** Expressive choices carry a short sample line in the user's language, so the user reacts to a sound. Sample lines are in-voice replies, never instructions. The ecosystem-role mini-round uses short titles only.
- **Labels and jargon.** Jargon stays out of the *questions*. At *guess* time, show the label with a one-line plain gloss ("una tsundere: niega que le importás, pero te cuida igual"); the label is the product.
- **Known facts.** Skip whatever the request, an existing SOUL, USER/MEMORY or the conversation already settled.
- **No operational questions.** Wishes about autonomy, approval, security, verification or escalation go into the handoff note (see Output), never into SOUL.
- **Tier filtering.** The tier filters what you offer (`02-pick.md`). The script already drops anchors outside the tier and anything in `config.exclusions`.
- **Momentum.** After each round, one plain line of what is taking shape ("Voy pensando en alguien seco, con filo, que esconde el cariño…").

## Phase A: context (one call, always first)

1. **Who will talk to it?** Only me / Me and people close to me / My team or company / Customers or the public, for a brand. This sets the tier: P, C, T or B.
2. **Language and form of address**, if not already known: tú, vos, usted, or another language.
3. **What will it mostly do?** Code and servers / Research and writing / Chat and company / Serving other people. Only used to judge fit.
4. **How do you want to build it?** Write the options in the user's language; the Spanish samples below are only examples.
   - "Guess it: ask me questions" ("Adiviná vos: hacéme preguntas"). Akinator, the default.
   - "Show me options and I'll pick" ("Mostrame opciones"). Go straight to a shortlist.
   - "I already know the character" ("Ya sé qué personaje quiero"). The user names it; map it in Phase C.
   - "I have reference characters or people" ("Tengo referentes"). Take the Referent path, then Akinator with priors.

`akinator.py --lang` ships `en` and `es`; for any other language, read the English text and translate it.

## Phase A2: ecosystem role (one brief round)

Follow `references/ecosystem-role.md`: ask which short title fits its place in the ecosystem, using 3-4 relevant options from `references/ecosystem-roles.json` or a custom title. Ask at most one optional follow-up to order a requested hybrid. Record `ecosystem_role.primary` and optionally `secondary`; no duties or operational description. Skip a role already supplied, and keep the user's language. The Phase A job answer helps choose options; do not repeat that job question here.

Then initialize Akinator:

```bash
python3 scripts/akinator.py --state <workdir>/akinator.json --init --tier P --lang es
```

Add `--prior <anchor_id>=<2..4>` for anchors suggested by referents or by the request.

## Phase B: narrowing rounds (Akinator)

Each round:

1. Run the script and read `action`.
   - `ask`: put the `next_questions` (usually 2) in **one** `clarify` call. Rephrase them naturally and keep their option values. Add a sample line to each option that fits the current top candidates.
   - `guess`: go to Phase C with `top[0]`.
   - `shortlist`: go to Phase C with `top[:3]`.
2. Record answers as `--answer feature=value`:
   - Use the option's value (-2..2).
   - Use `feature=skip` for "no sé" or "depende".
   - Add `:0.5` when the user hedges ("a veces", "un poco"): `humor=1:0.5`.
   - A free-text 'Other' answer: map it to the nearest value, or skip.
3. Say the one-line "voy pensando en…" and loop.

The question budget is `config.interview.max_questions` (default 14), but a guess normally comes after 4-8 answers. Never re-ask a feature the user already answered. If they contradict themselves, the later answer wins (`--answer` overwrites).

## Phase C: guess, confirm or correct

**Guess.** "¿Es esto?" Show the label plus its plain gloss and two sample replies in that voice (a greeting and a correction). Choices:
- "¡Sí, eso!" → `--confirm <id>`.
- "Casi, pero…" → run the correction question below.
- "No, para nada" → `--reject <id>`, then continue Phase B.

**Correction question ("Casi").** One `clarify` with up to 4 contrasts, chosen from the features where this anchor is extreme. Each option is shown as the same sample line, adjusted:

| Contrast offered | Record as |
|---|---|
| Más cálido / más frío | `warmth=±` (anchor value ± 1) |
| Que se le note más / menos el cariño | `openness=±` |
| Menos filo / más filo | `bite=±` |
| Más serio / más gracioso | `humor=±` |
| Menos / más palabras | `verbosity=±` |
| Más sobrio / más personaje | `theatricality=±` |

Rerun the script. If the same anchor survives a second "casi", stop searching: confirm it and treat the remaining gap as a **secondary** ingredient or an **intensity** choice in Phase D.

**Shortlist.** Write one reply per candidate to the same neutral prompt (default: "gracias, quedó perfecto" or "te equivocaste en la ruta"). Ask "¿Cuál suena más a lo que querés? Podés elegir dos para mezclar", and add "Ninguno" as a fourth choice when there are three candidates.
- Two picked: the first is the anchor, the second the secondary.
- "Ninguno": ask one open question ("¿A quién o a qué momento se parece? Un personaje, una persona, una escena"). Then take the Referent path, or search the catalog (`catalog/INDEX.md`) for an entry outside the anchor set.

**Off-matrix labels.** `anchors.json` is a starting set, not the whole catalog. When the user's character is better captured by a catalog entry (a miko, a gyaru, a Karagöz), use that label with its catalog gloss. Mark its recognition as unknown until the label probe in testing confirms it. You may add a good recurring label to `anchors.json` with estimated features; the file is data, not code.

**"Ya sé qué personaje quiero".** Skip Phase B. Map the named stereotype to an anchor or catalog entry, record it with `--init --tier X --confirm <id>`, show one guess card (label, gloss, sample lines) to confirm, and continue with Phase D.

## Referent path ("basado en…")

For each figure the user names (follow `catalog/referents/guide.md`):

1. **Kind.** Fictional or mythological / historical, deceased / living or controversial. Ask only if unclear.
2. **"¿Qué te gusta de X?"** (MULTI). Offer 4 behavioral traits you infer: method, temperament, rhetoric, humor. Never quotes or catchphrases.
3. **"¿Qué NO querés de X?"** (MULTI). Offer the risky parts: cruelty to people, politics or stance, catchphrases, period prejudice, arrogance toward the user.
4. **Only for living or controversial figures:** "¿Solo el estilo para discutir, o también su postura de fondo?" Default to style only. A stance is personal-tier only and stays argued, never asserted as fact.

Then turn the traits into script input:

- **Priors** on the anchors they point to, e.g. `--prior deductive_detective=3 acerbic_genius=3 polemicist=3`.
- **Soft answers at weight 0.5**, e.g. "humor cortante" → `bite=2:0.5 humor=2:0.5`. Akinator then *confirms* instead of assuming.

Record the referents in `blend.referent` with their kind. By default no referent name appears in the SOUL. The `referent_name=include` test axis may name a fictional or historical figure in tiers P/C, and never a living one.

## Phase D: layers (after the anchor is confirmed)

Ask only what is still open. Each question is a choice between *sounds*: the same line written in each option.

1. **Secondary flavor** (optional, max 1). Offer 2-3 anchors from the earlier top list that differ from the anchor on at least two features, plus "Nada". Check the pair in `03-compat.md`.
2. **Intensity.** The same reply at mild, moderate and strong; the user picks by ear. This becomes the baseline intensity; the other levels can still be tested as variants.
3. **Voice.**
   - **Signature speech first:** check whether the confirmed archetype or named referent has a recognizable register, dialect or historical/literary manner. Record its source and meaningful cues in `voice.signature` when relevant. A birthplace alone is not evidence of speech, and no reference selects the output language. If a new dominant voice would displace that signature, give one brief warning plus samples and choices to preserve, soften or deliberately reinterpret it. Use `references/voice-compatibility.md`; an already explicit intentional combination does not need repeated confirmation.
   - **Independent strengths:** use strong / medium / low for each of up to four `voice.layers`. The former subtle layer corresponds to medium; low uses only occasional compatible words or short phrases. Multiple influences need not appear in every message. All menus, samples and warnings follow the user’s language, whatever the source cultures.
   - **Regional and/or literary voice (ask when not mentioned; skipping is valid):** after output language and treatment, include the choice of no marked voice, regional variety, literary/fantasy/historical/character-inspired inflection, or an optional controlled mix. For a regional choice ask whether to use (A) no marked variety, (B) one regional variety, or (C) a dominant base with a few lighter influences. For B/C first show a small shortlist relevant to the requested reply language, **but permit any other source variety as a cross-language accent** (e.g. Cantonese-influenced Spanish). Same-language varieties can provide native grammar; foreign accents only color natural cadence or conversational delivery, never foreign grammar, invented spelling mistakes or automatic loanwords. Code-switching is a separate opt-in, not a prerequisite for foreign accents. Ask each influence’s degree (strong / medium / low) only when a variety is chosen. Keep this subordinate to personality and situation. See `references/dialects.md` and `references/catalog/voices/dialects.json`; do not show the entire catalog or conflate jopará with a generic Spanish accent.
   - **Literary / fictional accent (a follow-up only if selected in the preceding Voice question):** none, fantasy, mythology, historical, character-inspired, or mixed with a regional variety. For chosen style offer 3-5 relevant examples and optional strong/medium/low strength for each influence. If a person/character is named, ask which *speech cues* should be borrowed rather than replacing the confirmed archetype. Use `references/stylized-voices.md` and `references/catalog/voices/stylizations.json`.
   - Graphic markers (MULTI): none / emojis / kaomojis / ASCII, or a mix. Record new choices in `voice.graphic_markers.families`, with a separate rendered block per selected family (`references/graphic-markers.md`).
   - Marker frequency, only if markers were chosen: rare / recurrent / frequent, independent of personality intensity. Translate these qualitative choices to the user language; do not impose per-message quotas.
   - Implicit personality: default `persona_expression=mid`; compare soft/mid/hard if the user reports unsolicited self-description or wants that choice. Hard emphasizes its control verbs. No extra question when already settled (`references/persona-expression.md`).
   - Speech color: keep the regional/literary choice already made; otherwise plain or trade jargon if relevant. Do not ask a second question that repeats the style menu.
   - Filter all of these by tier (`02-pick.md`).
4. **Extra traits (0-3).** Propose 4 concrete tastes or harmless quirks that suit this anchor, from `catalog/tastes/INDEX.md`. The user may reject all of them.
5. **Name and identity.**
   - Name, as an open question unless already known.
   - Self-reference: "yo" / its own name / third person.
   - Identity stability, as sounds: "flexible" / "always itself" (anchor) / "never lets you switch it" (lock). With lock, show a sample of it declining a persona swap with good humor and accepting "write this as a formal email". If the user uses `/personality` presets, recommend flexible or anchor.
   - Output language: "reply in the language I write in" (`match_user`) or a fixed language. Keep `output_language` independent of the accent source; foreign accents are permitted and never change the requested reply language. Ask only if native dialect versus accent inspiration is genuinely ambiguous.
6. **Overrides (optional).** These cover moments where the anchor's default might surprise the user: how it disagrees, how it gives bad news, how it takes criticism, how much flavor survives while working. Ask only those that are ambiguous for this anchor, or that the user raised. Answers become archetype or situational bullets. Do not ask them all by default: they turn a label back into a description.
7. **Test plan.** Say in one line which variants you will render ("4 variantes: base, solo etiqueta, solo descripción, intensidad fuerte"). The config default applies unless the user wants something else (`references/variants.md`).

## When the user says "don't ask me" (or nobody is there)

Run the same phases silently:
- Answer each question with the most reasonable reading of the request and the tier defaults, and record every such answer in `ledger.decided` prefixed with `ASSUMED:`.
- Living or controversial referents: take style only, never the stance.
- Render and test the variants as usual.
- End with one recommended starting variant, framed as judgment and not a measured winner, plus an offer to refine. Don't end with a question the user asked not to get.

## Output

Write `blend.json` following the schema in `references/variants.md`, and keep it next to the variants. Inside it:

- The anchor and secondary, each with label, gloss and a label-free description.
- Label-free archetype bullets, intensity lines, voice and situational lines, 0-3 quirks, 2-3 varied example exchanges, dynamic facets if a 3-4-ingredient blend suits them (`05-dynamic-blend.md`), and the referent.
- `ledger.decided`: every choice the user made, including the tier, Akinator answers and the voice accent modes (regional and/or literary), including explicit "none" when chosen.
- `ledger.rejected`: rejected anchors and traits. Later steps must not reintroduce them.
- `ledger.handoff`: operational wishes, kept for runtime or AGENTS.md and never rendered into SOUL.
- `ledger.notes`: design notes, such as the non-impersonation check for referents or why a trait was softened.

Steps 2-4 complete and check this blend; they do not restart it.
