# Work with an existing SOUL

## Entry point: choose intent before interviewing

Classify the user's first message. If it already says *create*, *edit/refine/fix*, or *upgrade/migrate/bring up to the current scheme*, proceed without asking. If the intent is not clear, ask **one short question before the archetype interview**: "¿Querés crear un SOUL nuevo, modificar uno existente o actualizar uno al esquema actual sin cambiar su personalidad?" Translate to the user's language. An existing file by itself does **not** imply permission to migrate or replace it. If both edit and upgrade are requested, do both, using two separately reviewable diffs.

- **Create:** run the full discovery flow as needed.
- **Edit:** change one or more *chosen expressive behaviors* in an existing identity, and preserve other decisions. Ask what the user wants different only when not supplied.
- **Upgrade:** adapt an existing identity to the latest supported SOUL scheme while *preserving meaning* as much as possible; do not silently change its humor, intensity, register, language, anchor, name, limits or style decisions. New generic cues can conflict; have the user review them.

## Inspect and preserve

1. Locate the input SOUL file or the associated `blend.json` and manifest. Read them **before** any interview. If a prior blend exists, it is the preferred source of truth; compare it against the actual SOUL because a manually edited file can diverge.
2. Preserve an untouched copy in the project workspace, and record source path/hash and current scheme versus target. Do not write into an active profile by default.
3. List *what is already decided*, *what is unclear*, and *what is explicitly changing*. Capture explicit user choices separately from inferred traits; don't promote an example into an instruction.
4. Keep identity/persona distinct from policies, workflow, tools, biography and memory. Do not transfer accidental operational content from a legacy file into the new SOUL; record it in a separate handoff for explicit review, never discard it silently.

## Edit mode: targeted refinements

- Prefer editing `blend.json`, followed by `render_variants.py --plan baseline --check`. If absent, reconstruct a blend **manually and cautiously** from the original text and confirmed user choices. Use `templates/blend.example.json` and `references/variants.md`; don't invent a cultural archetype merely to fill `anchor.label`. Ask only about genuinely ambiguous identity-defining content, or clearly mark a proposed interpretation for confirmation.
- Show a plain-language before/after summary and a focused diff of the changed voice and reactions. Avoid running the Akinator anew unless the user wants to replace the core archetype.
- Test original versus edited on the **same** model and natural situations. Preserve the baseline as a named candidate. A stylistic choice belongs to the user; no automated score can replace that choice.

## Upgrade mode: bring existing SOUL to current scheme

**With a trustworthy blend:** render the blend under the current renderer; compare the result with the previously deployed file. Restore explicit manual customizations in the blend before accepting the candidate. Never assume a rendered file is equivalent solely because it validates.

**With only a Markdown SOUL:** for a standard file with `## Voice` or `## Voz`, use the conservative additive migrator:

```bash
python3 scripts/upgrade_soul.py original/SOUL.md --out workdir/SOUL-upgraded.md --diff --check
```

It stages a candidate, adds the default contextual reply-form cue and short anti-slop section only if apparently absent, preserves all existing lines and refuses in-place changes or existing destinations. `--no-reply-shape` and `--no-anti-slop` let the user decline either. This is **not** a semantic conversion into `blend.json`. If the original lacks a recognizable Voice heading, rewrite manually with evidence from the original instead of guessing. If the source has conflicting style cues, negotiate those changes explicitly rather than stacking more rules. Check idempotence, content changes and all scope warnings before approval.

For a full migration to an editable canonical `blend.json`, reconstruct and review its fields from the source; render only after distinguishing supported content from gaps. Compare the original and output in short, natural examples and identify any unavoidable wording/behavior changes. Do not auto-replace the old SOUL.

## Acceptance and deployment

For voice continuity or conversational-template problems, compare `voice_lock` and `humanize` independently (`references/voice-lock-humanize.md`). New renders default both to on, including when rerendering old blends: show the new blocks and identity-lock separation in the diff. Preserve `voice.continuity` if present; never infer it from a few dialect words.

For Markdown-only input, opt in with `--voice-lock --humanize`. The migrator adds only missing sections, preserves existing custom sections/cues and all source lines, and suppresses adding the old generic shape fallback when naturalness is present/requested. Existing overlapping or contradictory guidance needs manual review, not automatic deletion. No flag installs a precall hook or changes an active profile.

Present **source → proposed candidate → differences → sample replies / tested or untested**. Ask the user to choose or revise the candidate. When approval names an actual destination profile, back up the installed SOUL and write it explicitly; do not silently install. A new conversation may be needed before the updated prompt takes effect.


## Regional voice during edit or upgrade

Editing can change only the dialect dimension, without restarting the archetype interview. Ask whether to keep the existing regional voice, remove it, choose one variety or add a dominant/secondary mix; use `references/dialects.md`. Treat an unmentioned dialect as "preserve", not as permission to add a default national voice. On upgrade, do **not** auto-identify a region from hints like "che" or "mate" in an old SOUL; that is weak evidence and might be a personality quirk. If a previous blend has no `voice.dialect`, it remains unchanged. When adding a dialect, stage a diff and compare the original against the revised candidate before replacement.

The same preserve-by-default policy applies to `voice.stylization`. Offer fantasy, mythology, historical, character-inspired or no literary voice only when the user requests a voice change; don't infer a style from isolated metaphors in an old SOUL. When editing, preserve the existing archetype, phrasing and dialect; add only the selected optional literary influence and compare the diff. See `references/stylized-voices.md`.

On edit/upgrade, preserve `output_language` and `language_policy` even if the user requests a cross-language accent. Old blends without `voice.dialect.application` default to `auto`. Do not infer a new reply language from the source accent; review a fixed-language example before deployment.

## Graded voices in v2.4

Preserve existing speech before converting legacy voice objects into `voice.layers`. Map former subtle color to medium; low is a new lexical-only option and must not silently replace it. Carry forward a recognizable signature with provenance and compare dialect/register changes using `references/voice-compatibility.md`. Do not infer a reply language from the referent or an old accent. Static/dynamic rendering now keeps the same facet ingredients in both branches; old blends with facets need a visible before/after diff because their former static branch omitted them.

## Roles and emphasis in v2.5

Preserve an existing `ecosystem_role` or its absence. A new optional field does not justify a fresh role interview during an unrelated edit/upgrade. If the user requests a role, use the brief title-only round in `references/ecosystem-role.md`.

The renderer defaults to selective primary capitalization and an uppercase anti-slop verb. An old blend will pick up those defaults unless `baseline.primary_emphasis=off` and `baseline.anti_slop_emphasis=off` are explicit. Show the casing diff and keep the original deployed text intact. For an unrelated targeted edit, use those overrides if needed to preserve the original casing. The standalone Markdown upgrader does not rewrite existing capitalization or infer which old cues are primary.

## Expression and graphic markers in v2.6

Rerendering a blend adds the new `persona_expression` block: mid by default, or explicit soft/hard. Compare those levels separately with `--vary persona_expression --max 3`; all preserve normal first person and truthful identity/capability answers. For a standalone Markdown source, the upgrader only adds this block when passed `--persona-expression soft|mid|hard`. Existing expression sections remain intact for manual comparison. To stage three candidates, use three fresh output paths. Keep the original source untouched.

Preserve legacy `voice.markers` on unrelated edits. Convert to `voice.graphic_markers` only for a requested marker change, carrying forward the actual families and frequency independently of personality intensity; remove the active legacy object and review base/situational cues and examples for contradictions. The Markdown upgrader does not infer marker families or rewrite example dialogue. See `references/persona-expression.md` and `references/graphic-markers.md`.
