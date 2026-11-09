# Troubleshooting (environment, endpoint, key)

Run `--check` first. It prints the resolved URL, whether the key was found and where, whether `/models` lists each model, and a one-word "ping" per model. It never prints the key.

The script already reports the fix for each error in the user's language (in the terminal and in the report). This page is for the agent, to diagnose before running and to explain options.

## No key / no .env
The script looks, in order: the environment variable named by `--key-env`, then `--env-file`, `./.env`, `$HERMES_HOME/.env`, `~/.hermes/.env`. Lines may be `NAME=value`, `export NAME=value`, quoted or not.

Offer the user, in this order:
1. Use a key that already exists: ask which variable name holds it (common: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`) and pass it with `--key-env`.
2. Create a `.env` next to where the script runs with `NAME=...`; the user types the value, not the agent. Remind them to keep `.env` out of git.
3. Export it in their shell for this session.
4. Local servers without auth (Ollama, LM Studio, vLLM, llama.cpp): `--no-key`.

Never ask for the key in chat, never write it into a file yourself, never echo it. If the agent runs in a sandbox that cannot see the user's environment, give the user the exact command to run on their machine instead.

## Endpoint mistakes the script fixes or detects
| Given | What happens |
|---|---|
| `api.x.com/v1` (no scheme) | `https://` added (`http://` for localhost and host.docker.internal) |
| `.../v1/chat/completions` | accepted, used as is |
| `.../v1/models`, `/completions`, `/responses`, `/messages` | replaced by `/chat/completions`, with a warning |
| base without `/vN` that 404s | retried once with `/v1` |
| URL of the provider's website | detected as HTML; points to the docs |
| non-OpenAI shape (no `choices[0].message`) | "shape" error; suggest the provider's OpenAI-compatible route or a proxy (OpenRouter, LiteLLM) |

Known OpenAI-compatible bases (check the provider docs, they change): OpenAI `https://api.openai.com/v1`, OpenRouter `https://openrouter.ai/api/v1`, DeepSeek `https://api.deepseek.com` (also `/v1`), Groq `https://api.groq.com/openai/v1`, Ollama `http://localhost:11434/v1`, LM Studio `http://localhost:1234/v1`. Anthropic's native API is not OpenAI-shaped; use a compatible proxy or its OpenAI-compatibility route if the account has it.

## Other errors
| Kind | Likely cause | Offer |
|---|---|---|
| 401/403 | wrong key for this provider, or no access to the model | check the variable, try another model |
| model | wrong id | `--check` lists ids; copy one exactly |
| 400 | a custom parameter this provider rejects | drop it, or pass the provider's own name with `--extra` |
| 429 | rate limit or no credit | `--parallel 1`, wait, check balance |
| 5xx | provider side | the script retries twice; try later |
| timeout | reasoning models are slow | `--timeout 600` |
| dns / refused | wrong host, no network, server down | check spelling; in Docker use `host.docker.internal`; a sandbox may have no egress |
| ssl | local server on https, or a corporate proxy | use `http://` locally |

## Parameters
Default: nothing is sent except `model` and `messages`, so thinking, temperature and max tokens are the provider's defaults. Custom values only when the user asks:
- `--temperature`, `--max-tokens`, `--reasoning-effort` map to the standard OpenAI names.
- Anything provider-specific goes through `--extra` as JSON, e.g. a thinking switch. Names differ by provider; read their docs rather than guessing. Some reasoning models ignore temperature.
- Reasoning text is read from `reasoning_content`, `reasoning` or `thinking` when the provider returns it; many do not.
