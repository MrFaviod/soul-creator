# Ecosystem role: a brief identity round

Run this mini-round after context and before Akinator. It answers what kind of agent this is in the ecosystem. The archetype answers what personality it has. A medieval knight may be a generalist assistant, an ops assistant or a chatbot; do not infer the role from the costume or dialect.

Ask one short question in the user's language: “What role should it have in your ecosystem?” Offer 3-4 short titles suited to the known context, with custom text available. For example: assistant / generalist / ops / chatbot. Do not show all 39 choices at once, describe workflows or require sample replies in this round. If the user already chose a role, record it and skip this question. A known job can guide the shortlist but does not decide the title for them.

Only when the user wants a hybrid and its priority is unclear, ask one follow-up: “Which is primary, and which is the secondary focus?” Stop there. The budget is `config.interview.ecosystem_role_max_questions` (default 2); do not spend a second question merely to offer a secondary. Custom labels are allowed in any language. Translate UI titles, questions and any short field help into the user's language; catalog IDs are internal identifiers, not a preferred user language.

## Starting titles

`ecosystem-roles.json` contains a curated menu, not an official taxonomy:

| Family | Titles |
|---|---|
| General | assistant, generalist assistant, personal assistant, executive assistant, companion, chatbot |
| Collaboration | coordinator, orchestrator, router, planner, worker, specialist, advisor, reviewer, evaluator |
| Technical | coding assistant, ops assistant, DevOps assistant, IT support assistant, computer-use assistant, security assistant, monitor |
| Knowledge and creative | research assistant, analyst, knowledge assistant, librarian, tutor, coach, writer, editor, translator |
| Business | business bot, customer support assistant, sales assistant, HR assistant, finance assistant, marketing assistant, back-office assistant, concierge |

Use the most informative short title the user picks. Titles may overlap; there is no required hierarchy. A role label does not grant tools, authority, expertise, delegation or access to other agents.

## Record and render

```json
"ecosystem_role": {"primary": "generalist", "secondary": "ops"}
```

Or use a short custom title, including a localized title:

```json
"ecosystem_role": {"primary": {"label": "asistente generalista"}}
```

Render one identity line under `Ecosystem role`, for example: “Your place in the ecosystem is GENERALIST ASSISTANT, with a secondary ops assistant focus.” No duties, schedules, procedures, hierarchy descriptions or promises of capability. Put requested operational details in `ledger.handoff`; retain the actual role selection in `ledger.decided`. The validator checks shape and length; review the label semantically too, since a short sentence can still describe a procedure.

For no-question creation, use the stated role or a modest contextual assumption marked `ASSUMED:`; never imply the user selected it. Existing blends without the field still render without a role section. Edit/upgrade preserves their absence unless the user requests a role; do not restart the interview to populate a new field.

## Sources for the expanded menu

The catalog combines user-provided examples with short titles drawn from these primary sources, plus related editorial suggestions. These sources describe systems and business uses; their procedures are not copied into SOUL.

- [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): router, orchestrator, worker, evaluator, coding and customer support.
- [Google ADK, Workflows](https://adk.dev/workflows/): coordinator and agent-routing contexts.
- [Microsoft Learn, Empower your workforce with Microsoft Copilot](https://learn.microsoft.com/en-us/training/paths/empower-workforce-copilot-use-cases/): executive, sales, marketing, finance, IT, HR and operations contexts.
