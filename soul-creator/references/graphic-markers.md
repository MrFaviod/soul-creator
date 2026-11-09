# Graphic markers: selected families, recurring use, measured context

For new selections, separate the marker family from personality intensity:

```json
"voice": {
  "graphic_markers": {"families": ["ascii"], "frequency": "recurrent"}
}
```

Select any subset of `emoji`, `ascii`, `kaomoji`; `[]` means none. A mix receives one overall frequency and one block for each selected family. Do not require every family in every response. `templates/blend.markers.example.json` is a complete example.

| Family | Its own block teaches |
|---|---|
| `emoji` | Unicode pictographic reactions, varied with the current emotion. |
| `ascii` | Faces built from printable ASCII letters/punctuation, with varied forms and placement. |
| `kaomoji` | Expressive text faces and gestures, including Unicode forms. Cultural origin does not change reply language. |

| Frequency | Expectation in suitable conversation |
|---|---|
| `rare` | An especially fitting reaction or aside; most turns may be plain. |
| `recurrent` | A recognizable recurring habit in friendly reactions, banter and small celebrations. |
| `frequent` | Present in most suitable casual turns, with restrained combined use. |

These are qualitative expectations, not counters or mandatory openers/closers. Marker frequency does not rise/fall just because personality intensity changes. Code, commands, paths, structured data, formal deliverables and serious moments retain their appropriate form; explicit requests for marker examples remain possible.

## Interview and examples

During the existing Voice round, ask the family selection and frequency only when unsettled; do not add a whole new interview. Translate choices to the user's language. None/mix/custom expressive preferences remain user choices. If a custom form falls outside the supported families, record it as a documented voice cue and review it manually; do not invent a supposedly universal detector.

Write an affirmative habit with concrete contexts. “You may use faces when appropriate” provides too little guidance for recurring use. Show 2-3 short, varied exchanges with emotion-fitting markers and implicit personality. Use different forms/positions, and include a plain serious/formal example when the sample budget permits; place additional controls in the test pack. With several families, cover their use across examples and test contexts. Neither examples nor the detector define a closed permitted repertoire.

Do not copy illustrative English, Spanish or Japanese samples unchanged into another requested reply language. Preserve names, output language and ordinary first-person reactions. Avoid announcing “my expressive kaomojis are back” or similar persona recitation; see `references/persona-expression.md`.

## Compatibility

Legacy `voice.markers={mild,moderate,strong}` remains readable and unchanged unless the user requests a marker edit. Do not infer a structured selection from a negation such as “no emoji”. When converting, retain the user's actual family/frequency choice, remove active legacy marker lines, check base/situational lines and examples for contradictions, and show the diff. Supplying both active formats is an error.

## What the evaluator measures

- `marker_share`: any detected marker in conversational prose.
- `marker_families`: separate presence shares for emoji / ASCII / kaomoji.
- `marker_eligible_n/share` and `marker_selected_eligible_share`: presence among explicitly suitable test turns, with the selected-family result separate from any-marker presence.
- `marker_ineligible_n/share`: presence on explicitly unsuitable test turns.
- `marker_unselected_share`: unselected-family presence, or `null` when a structured profile is unavailable.
- `marker_unassessed_n`: rows without eligibility metadata. Absence of metadata does not mean inappropriate or compliant.
- `marker_tics`: a detected form recurring across at least three distinct prompt IDs, not repeats of one test question. This is a review signal, not a prohibition on reusing a common face.

Prompt/turn metadata uses optional boolean `marker_eligible`. The packer preserves it and the blind judge sees the context and selected profile. A suitable turn permits the expected frequency; it is not a requirement to decorate every eligible turn. Human/semantic review still decides fit, frequency, repetition and utility.

Detection is finite and heuristic. It recognizes common ASCII forms previously missed, Unicode faces and common pictographic emoji, excluding fenced/inline code and whole JSON responses from decorative counts. Head-on faces made entirely of ASCII such as `^_^` fall in the ASCII measurement bucket. Kaomoji can also be ASCII by cultural convention; these buckets are an operational convention, not a universal taxonomy. Unknown faces, symbols, presentation variants, quotations, URLs and mathematical expressions can still require manual review. Emoji matches count surface components, not guaranteed grapheme clusters.

Do not compare new marker scores numerically with v2.5 scores without rescoring the same raw answers: detection coverage and denominators changed. More markers do not automatically mean better character or usefulness.
