# Evidence behind soul-creator (check scope before citing)

Many persona studies use open 7-70B models, factual/reasoning tasks or short chats. Newer work also studies extended role dialogue and long agentic coding, but does not validate this custom SOUL scheme or its exact blocks. Treat results as directions, not forecasts for your model; the variant tests (`references/testing.md`) are how you find out.

## Does persona text change accuracy
- Zheng et al., EMNLP Findings 2024 (arXiv 2311.10054): 162 roles, open-weight model families, 2,410 MMLU questions. No persona beat the no-persona control; the best persona per question could not be picked better than chance. Audience-framed prompts beat speaker-framed ones by a small margin.
- Luz de Araujo et al., Principled Personas, EMNLP 2025: expert personas usually helped or held; irrelevant attributes (names, colors) significantly changed performance on 14-59% of tasks depending on model; mitigations worked mainly on the largest models.
- PRISM (arXiv 2603.18507, six 7-8B open models): expert personas help alignment-type tasks (writing, roleplay, safety) and hurt knowledge retrieval (MMLU 68.0 vs 71.6); shorter personas hurt less; the damage grows with instruction tuning. Small models only.
- Jekyll & Hyde (arXiv 2408.08631): role-play prompts degraded reasoning on 7 of 12 datasets for Llama 3; LLM-generated personas were more stable than handwritten ones.
- Counter-evidence: Kong et al., NAACL 2024 (arXiv 2308.07702): role-play prompting raised ChatGPT on AQuA from 53.5% to 63.8% and acted as an implicit chain-of-thought trigger. Reasoning-heavy, older ChatGPT models; the positive effect is a role related to the task, which is not the taste persona SOUL.md carries.
- Reading: persona is a voice lever, not a capability lever. The sign of the effect depends on the model and the task; test it.

## What persona text installs
- Preprint (ideafields, 18 configs from 3B to 756B): a rich persona plus a reinforcing exchange stabilizes how the model presents itself across contexts (35 of 36 contrasts) but mostly does not install the matching behavior. A few-shot rung saturated and sometimes reduced the effect, which supports varied or no examples. Not peer reviewed.
- Reverse Role Prompting (GPT-3.5/4o, book chapter): stating what the persona is not raised trait fidelity. This conflicts with the "say what to do" advice. Resolution used here: express negations as concrete behavior and keep hard negatives for irreversible actions. Medium-low evidence.
- System prompt strength (arXiv 2601.06403): behaviors that conflict with the assistant prior need more steering force. Supports giving a tsundere or blunt archetype concrete behavior, and explains why overlays that clash with the SOUL lose.
- Role-slot wording in rankers (arXiv 2510.17535, 8B models): adverbs and adjectives carry the role signal; the modal or verb barely matters. No study compares "eres X" with "actúa como X". The recommendation to prefer "Eres" is the maintainer's hypothesis.

## Wording and format guidance from labs
- Anthropic prompting docs: a one-sentence role focuses behavior and tone; prompt style leaks into output style; Opus 4.5/4.6 respond more strongly to the system prompt, so dial back CRITICAL/MUST (stated for tool use, applied here by analogy).
- Anthropic, Effective context engineering (Sep 2025): right-altitude prompts, minimal high-signal tokens, canonical examples over edge-case lists.
- DeepSeek R1 paper (Nature, arXiv 2501.12948): few-shot prompting hurts R1; weaker than V3 at complex role-play. Applies to R1; not shown for later models.

## Hersona benchmark (persona maintenance, persona_lock)
- Hersona's `bench` scores surface speech adherence (sentence endings, catchphrase density) on real transcripts, with no LLM judge. One published run (one model, tsundere + keigo, moderate, Japanese scenarios, metric v2):
  - A hand-written 41-token prompt was competitive with the 482-token generated block.
  - `persona_lock` doubled long-form maintenance (67% against 33%) but gave no lift on persona-override attack turns (67% against 67%); the short hand-written prompt held best on attacks (83%).
  - No persona gave 0-8%.
- One model, one blend, surface metrics only, and the project's own documentation says so. Treat it as a hint: compact prompts can match long ones, and a lock is a maintenance aid, not an injection defense. The `identity_lock` axis and the multi-turn scenarios replicate this comparison on the user's own model.

## Drift and robustness
- Assistant Axis (Anthropic, arXiv 2601.10387; Gemma 2 27B, Qwen 3 32B, Llama 3.3 70B): drift appears in emotional and philosophical chats, not in coding and writing; drift correlates with harmful responses. Not frontier models.
- ContextEcho (arXiv 2605.24279, preprint, 23 frontier models, long real sessions): compaction did not reliably reset drift; an anchor restored the trained assistant register on measured probes. This does not demonstrate recovery of a custom SOUL voice or indefinite persistence.
- [Persistent Personas?, EACL 2026](https://aclanthology.org/2026.eacl-long.246/): seven models, dialogues over 100 rounds; fidelity declined especially during goal-oriented dialogue and responses approached no-persona baselines. Applies to its tested models/personas, not a proof that a static lock fixes drift.

## Naturalness and sustained voice

Read `references/voice-lock-humanize.md` for primary sources, design and limitations: current OpenAI/Anthropic prompting guidance, SillyTavern and Ali:Chat, NC-Bench conversational actions, and Eval4Sim's separate adherence/consistency/naturalness dimensions. This motivates independent `voice_lock` and `humanize` comparisons, varied implicit examples and whole-sequence review. It does not establish that more recognizable traits, fewer questions, more uppercase, higher temperature or this exact static prompt improve naturalness universally.
- Sycophancy under user personas (medRxiv preprint): rates varied from 2.4% to 15.3% across five frontier models.

## Hermes mechanics (official docs)
- SOUL.md is slot #1 of the system prompt, loaded only from HERMES_HOME, injected verbatim without wrapper text, injection-scanned (a hit warns, the file still loads), truncated if long, default identity if empty. Agent writes need user approval. Subagents skip it and use the default identity.
- `/personality` presets are session overlays listed after the stable identity; the docs do not say whether they are wrapped in delimiters. Built-in presets mix an identity line, a voice imperative and a token palette (kawaii: "cute expressions like (◕‿◕), ★, ♪"; catgirl: "add 'nya'"); pirate is written in first person and in voice. No evaluation of any preset found.
- GitHub issue 82801 (community report, unverified in code): an active preset replaces SOUL.md instead of composing with it, and stale preset names can reactivate after updates. Check `display.personality` first when a SOUL seems ignored.
- Recommended workflow in the docs: seeded default, trim, add 4-8 lines, iterate.

## Anecdotal field observations (single setups, not general evidence)
- In one setup, a reasoning model's trace treated a `/personality` overlay as a prompt injection because the SOUL had a strict "you are X and no one else" line; other models also ignored the overlay. This motivates testing `identity_lock` as a variant, not a rule.
- One small benchmark (12 exact-answer problems, 6 persona variants x 3 runs) sat at ~100% accuracy for every variant, with no reliable token effect. At ceiling it shows no *large* cost, not *no* cost; use tasks below the ceiling.
- Drafts that use two identity names (one in the identity line, another in examples) happen in practice; the checker rejects them.

## Gaps
- No study of Spanish identity phrasing, of "eres" vs "actúa como", or of kaomoji palettes versus closed lists.
- Little measurement of SOUL decay in long agentic sessions, or of reasoning-trace style versus prompt style.
- No evaluation of Hermes presets.
- No study directly compares a stereotype label against an equivalent description as a system-prompt anchor. That is this skill's working thesis; the `anchor` variant axis and the label probes test it per model and per label.
