# Graded voices and archetype compatibility

## Contents

- Separate language, signature speech and optional color
- Decide compatibility during the interview
- Three independent strength levels
- Blend fields and example
- Old blends, edits and evaluation

## Separate language, signature speech and optional color

Apply this in **any** language. Conduct the interview, warnings and examples in the user's language. The user's chosen reply language is authoritative; a referent, an archetype, a region or a historical style never selects it implicitly. English instructions in the SOUL are scaffolding, not a command to answer in English.

Before choosing accents, identify whether the selected character has **signature speech**: a recognizable literary register, historical manner, regional phrasing or form of address that contributes to its identity. A Shakespeare-inspired dramatic voice or a courtly medieval character may have strong signature rhetoric; an otherwise quiet or sarcastic character need not have an intrinsic dialect. Do not assign a national accent just from a name, appearance or birthplace.

For a referent, separate **what the user is borrowing**. Borrowing a well-known Argentine speaker's regional delivery suggests a Rioplatense base; borrowing only their argumentative energy does not require that base. Offer an informed default where the speech is part of the reference, record assumptions, and preserve the user's reply language independently. The figure remains construction material, not the agent's identity.

Signature speech is not an immutable rule. A Shakespeare-inspired character with Argentine Spanish can be a deliberate comic interpretation. The skill should explain that effect, then support it. A medieval character can keep readable modern speech while adding occasional historical or Asturian-inspired phrasing. Do not invent historical Asturian forms or claim reconstruction; ask for source examples when authenticity matters. Any other language/period can be handled by the same custom-entry path.

## Decide compatibility during the interview

1. Read the user's request and any original SOUL/blend. Preserve an existing signature unless the user changes it.
2. Record meaningful signature cues in `voice.signature` when present. Use observable speech features and provenance, not a stereotype inferred from nationality. No marked signature is a valid outcome; note it in the ledger rather than inventing one.
3. Compare the desired layers against that signature. Check grammar/address, historical register, cadence, lexical choices and expected emotional effect. The automated analyzer detects explicit removal/softening of a recorded strong signature; the author must assess semantic clashes it cannot infer.
4. If a choice would replace an important voice feature, give **one short warning in the same voice question**, followed by samples of the same situation. Explain what changes, not merely that it is "incompatible". Offer up to three meaningful options: preserve the signature with light secondary color; blend at medium strength; deliberately reinterpret the dominant voice.
5. Translate all choices and warnings into the user's language. For example, in Spanish: «Aviso: una base peninsular fuerte reemplazaría el voseo rioplatense que estamos tomando del referente. Podemos conservarlo y añadir giros suaves, o hacer esa reinterpretación a propósito». This is an example, not a mandatory phrase.
6. If the user already explicitly requested an intentional comic or contrasting reinterpretation, explain its effect briefly and record that request. Do not repeat a confirmation they already supplied. If intent is unclear, use the one compatibility question rather than silently discarding a decision.
7. If questions are forbidden, prefer preserving signature speech and add only compatible secondary color, marking assumptions. When a conflicting reinterpretation must be shown for review, set `compatibility.proposed: true`; render it as **pending user choice**, never invent acknowledgement or install it as accepted.

Compatibility warnings stay in the ledger/manifest and conversation, **outside SOUL**. The resulting SOUL should contain the chosen expressive voice, not the interview or an approval workflow. Technical tone, quotes, output formats and runtime authority remain separate.

## Three independent strength levels

| Level | Effect | Grammar and identity |
|---|---|---|
| `strong` | The recognizable dominant voice in its dimension | A compatible regional base can supply grammar/address. A literary base can supply dominant rhetoric. A foreign source remains an inspiration in the selected reply language. |
| `medium` | Restrained cadence, phrasing, rhetorical color or imagery when appropriate | The former subtle/low color belongs here. It should not compete with the dominant grammar or character. |
| `low` | Only occasional characteristic words or short turns of phrase across a conversation | No full dialect syntax, conjugation, phonetic spelling, new persona or required catchphrase. |

Set strength **per layer**, not once for the whole mixture. Multiple medium/low colors can coexist without all appearing in every reply. Use one strong regional grammar/address base at most. A strong literary voice and a strong regional base can coexist intentionally; show their effect if the combination wasn't already requested. Keep blends to a few meaningful influences, default maximum four.

Low does not automatically authorize foreign words. `code_switch: off` preserves the selected language; use grounded turns already compatible with it or omit the trace. With explicit `contextual`, occasional meaningful foreign insertions are permitted while the reply language remains dominant. For a low Cantonese influence in a non-Cantonese reply, explain that there may be little identifiable lexical effect without such insertions. Never invent "Cantonese-sounding" errors to make the influence visible.

## Blend fields and example

`templates/blend.layers.example.json` is a complete runnable example. New mixtures use `voice.layers`; do not combine it with active legacy `voice.dialect`/`voice.stylization` objects. Each layer contains:

- `kind`: `dialect` or `stylization`.
- `primary`: an existing catalog ID or a documented custom entry, using the corresponding catalog schema.
- `strength`: `strong`, `medium`, `low`.
- For dialects, `application`: `auto` or `accent`, and `code_switch`: `off` or explicit `contextual`.

The following example is illustrative, not a user or language default:

```json
{
  "output_language": "es",
  "language": "Spanish",
  "language_policy": "always",
  "voice": {
    "base": ["Speak clearly, with dry wit and understated warmth."],
    "signature": {
      "description": "A regional delivery explicitly selected as part of the character.",
      "source": "user choice",
      "layers": [
        {"kind":"dialect", "primary":"es-ar-rioplatense", "strength":"strong"}
      ]
    },
    "layers": [
      {"kind":"dialect", "primary":"es-ar-rioplatense", "strength":"strong"},
      {"kind":"stylization", "primary":"char-noir-narrator", "strength":"medium"},
      {"kind":"dialect", "primary":"fr-fr-contemporary", "strength":"medium", "code_switch":"off"},
      {"kind":"dialect", "primary":"zh-yue-cantonese", "strength":"low", "code_switch":"off"}
    ]
  }
}
```

`voice.signature` is optional: `{description, source, layers}`. It records the voice associated with the archetype/referent/original SOUL **before** optional reinterpretation; it does not override the reply language. If signature is present and `voice.layers` is absent, those signature layers are preserved as the effective defaults.

`voice.compatibility` optionally records:

```json
{
  "conflicts": ["The requested dominant voice would replace an established form of address."],
  "acknowledged": true,
  "reason": "The user explicitly chose this reinterpretation after seeing the difference."
}
```

Only record acknowledgement supported by the request or conversation. Put unresolved drafts under `proposed: true`; their manifest keeps `needs_choice: true`. The renderer rejects unresolved changes unless explicitly staged as proposed. It does not install or accept anything.

Use `scripts/voice_layers.py blend.json --json` to inspect layers/changes and `scripts/check_blend.py blend.json` to validate before rendering. They cannot discover undocumented semantic clashes; the interview remains responsible for that judgment.

## Old blends, edits and evaluation

Legacy dialect/stylization objects continue to render. When migrating into graded layers, `subtle` corresponds to `medium`, not the new lexical `low`; `natural` is a medium presentation cue and `marked` corresponds to strong. Preserve explicit prior grammar/address in the dominant base rather than losing it during a mechanical rename. Show the resulting diff, especially when the old format applied one strength to several influences.

On edit or upgrade, do not add an accent or infer a new output language merely because the feature exists. Preserve unmentioned choices, including code-switching. The original SOUL and decisions outrank the example above.

For comparison, `--vary regional_voice stylized_voice` still changes one dimension at a time. `single` retains the strongest layer of that kind, ties resolved by order; `off` removes that kind. These are experiment conditions, not silent edits to the accepted signature. The manifest records the configuration and compatibility notes separately from the SOUL. Compare conversational, supportive and technical situations; grade voice fidelity and utility separately, without treating marker density as a winner.
