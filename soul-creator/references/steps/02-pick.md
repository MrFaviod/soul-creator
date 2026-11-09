# Step 2: Pick the parts

Compose from layers. Each layer takes one primary ingredient and may take one secondary that colors it; the primary decides when they pull apart. Blends are expected ('tsundere with a deadpan streak', 'mentor who talks like a sea wolf'). Too many named ingredients read as a checklist (inference: nothing measures how many a model holds), so keep the total under about 6 across all layers.

| Layer | Pick | Browse |
|---|---|---|
| Character role / archetype | 1 primary + 0–1 secondary | `catalog/roles/INDEX.md` → subtype |
| Temperament | 1 primary + 0–1 secondary | `catalog/temperaments/INDEX.md` → subtype |
| Speech | 1 base register + 0–2 restrained flavors | `catalog/voices/INDEX.md` → register, delivery, language, character style |
| Tastes | 0–3 interests, values, aversions, quirks | `catalog/tastes/INDEX.md` → subtype |
| Appearance | avatars/cards only | `catalog/appearance/INDEX.md` (NEVER textual SOUL) |

The character-role bank describes a persona's social or theatrical archetype. `blend.ecosystem_role` is the separate short agent-purpose title chosen in Phase A2 (`references/ecosystem-role.md`); it neither replaces the archetype nor adds operational duties.

Combination rules:
- The primary is `blend.anchor`; the secondary is `blend.secondary`, and its `adds` field says in one clause what it brings ('with a deadpan streak: delivers the jab flat').
- Check every pair, inside a layer and across layers, in `03-compat.md`. If a pair clashes: use the clash as the gap, swap the secondary, or lower its intensity. Never keep both at full strength.
- A flavor must not fight the base register (a courtly register and a streamer voice cancel each other).
- Intensity can differ per ingredient: primary moderate, secondary mild.

If the interview ran (`01-interview.md`), `blend.json` and its ledger of decided and rejected items are the starting point: complete and check it here, do not restart it, and never reintroduce a rejected item. Otherwise start from the stereotype the user named (Inputs). If the user names a real or fictional figure ("like Socrates", "based on a public-domain detective", a living or controversial person), follow `catalog/referents/guide.md` first. Find candidates through `catalog/INDEX.md` (by trait layer and subtype), then read 1–2 concrete subcategory files only. Speech order: base register, delivery, language/region only when requested, then optional character flavor. Any source variety may inspire any user-selected reply language. Native grammar applies only when compatible; otherwise use restrained cross-language color. For a marked archetype voice, follow `references/voice-compatibility.md` before adding or replacing a dominant dialect. Tastes (0-3) are what make the character singular; take them from `catalog/tastes/`.

## Context tier (apply first)
The purpose question of the interview sets the tier. The tier removes options before any fit judgment; the agent does not offer what the tier excludes. A brand or style guide outranks everything below. For public tiers, the 12 brand positioning frames are under `catalog/interview/brand-archetypes.md`, not in the role bank; they can guide which role and voice to select.

| Tier | Who talks to it | Allowed | Excluded | Intensity, markers |
|---|---|---|---|---|
| Personal | only the user | the whole catalog, including dere types, anime voices, first-person registers | `config.exclusions` plus the user's own (`blend.exclude`) | any; user's choice |
| Close circle | family, friends, a group | warm, playful, character voices, light dere (tsundere, kuudere, deredere) | sexualized, bratty or condescending (sadodere, seductive), dark roles, crude humor | moderate at most; markers fine |
| Internal | a team or company | sober to warm professionals: Sage, Caregiver, Creator, Everyman, Mentor, Detective, Competent Man, Only Sane Man, Gentleman and a Scholar; temperaments pragmatist, serious, stoic, intellectual, diligent, sociable, optimist, kuudere, deadpan (mild) | dere types except a mild kuudere, anime and historical voices, bite at people, chaotic or grandiose temperaments | mild; emojis occasional, no kaomojis |
| Public | customers, users, the public, for a brand | brand archetypes that fit service (Caregiver, Sage, Everyman, Creator, Ruler for authority, Innocent for simple products), occupational roles (concierge, specialist, guide); temperaments sociable, diligent, optimist, serious, pragmatist | all dere types, anime, historical, fantasy and dialect voices, first-person theatrical registers, sarcasm, bite, persona quirks that are not brand values, Japanese speech catalog | mild; no markers unless the guide allows emojis |

For public/company agents: the SOUL is a **brand identity and voice**, not an operational handbook. Rules about AI disclosure, refunds, promises, data handling and human escalation must be set in the relevant runtime/organizational instructions outside SOUL. If the user requests them, record a separate configuration handoff note; do not copy those requirements into personality prose.

## Excluded
Excluded tropes come from `config/defaults.json` → `exclusions.terms` (by default yandere, menhera and mesugaki: possessive, self-harm-adjacent or minor-coded sexualized tropes) plus any user config or `blend.exclude`. The Akinator never offers them, the renderer refuses them and the checker flags them. Do not reintroduce an excluded trope; if a user explicitly asks to un-exclude one, that is their config change, not a silent edit.

## Fit for tool-using agents (judgment, no study measures it)
- Often suitable in expressive style: calm, dry or warm. Roles: mentor, engineer, scientist, doctor, bartender, big sister, senpai, detective. Temperaments: kuudere, deadpan, pragmatist, stoic, serious, tsundere, sociable, hinedere.
- With care: loud or chaotic (genki, hot_blooded, drama_queen, klutz, airhead, playful, chuunibyou), grandiose ones (kamidere, himedere, isekai-cheat hero), villainess, hikikomori (avoids interaction), burikko or extreme kawaii (loses clarity), imouto (infantilizes), braggart, fool, trickster, mad scientist, flatterer.
- For agents using tools or handling consequential work, dark or scheming *style* may create confusion with real authorization. Filter or soften it for clarity, but leave authority and security policy outside SOUL; no trope grants permission.

## Intensity
Each attribute exists at three strengths: mild, moderate, strong. The user's pick (Phase D) is the baseline; `config.blend.default_intensity` applies when nobody chose. Strong raises voice fidelity but costs tokens and crowds out plain answers; test neighbouring levels with the `intensity` variant axis instead of guessing.

Output: an updated `blend.json` (anchor, secondary, voice base, tastes, intensity). Pass it to step 3.
