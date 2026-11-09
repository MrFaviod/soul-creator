#!/usr/bin/env python3
"""soul_test.py - send SOUL candidates + one verbose request to one or more
OpenAI-compatible chat endpoints and write a Markdown report.

Stdlib only. The API key is read from an environment variable (or a .env
file); it is never printed. Sampling parameters are sent ONLY when given, so
by default every model runs with its provider defaults (thinking, temperature,
max tokens).

Examples
  python soul_test.py --check  --endpoint https://api.deepseek.com --models deepseek-chat --key-env DEEPSEEK_API_KEY
  python soul_test.py --endpoint https://openrouter.ai/api/v1 --key-env OPENROUTER_API_KEY \
      --models a/model-1,b/model-2 --soul A=souls/a.md --soul B=souls/b.md --control \
      --lang es --out-dir soul-test-out
"""
import argparse, concurrent.futures as cf, datetime as dt, hashlib, json, os, re
import socket, ssl, sys, time, urllib.error, urllib.request
from pathlib import Path
from decision_preview import single_preview, terminal_preview
from test_config import (manifest_soul_args, warn_lang, positive_int, parse_models, parse_extra, validate_souls,
                         context_messages, strip_reasoning, read_expectations, sha, slot_audit)

HERE = Path(__file__).resolve().parent
DEFAULT_PROMPTS = HERE.parent / "references" / "verbose-request.md"

# ---------------------------------------------------------------- labels
L = {
 "es": dict(title="Reporte de prueba de SOUL", setup="Configuración", endpoint="Endpoint",
   models="Modelos", params="Parámetros", defaults="ninguno enviado (defaults del proveedor)",
   date="Fecha", souls="Candidatos", control="control (sin SOUL)", prompt="Solicitud enviada",
   summary="Resumen", status="estado", latency="latencia", tok_in="tokens in", tok_out="tokens out",
   tok_reason="tokens razonamiento", chars="caracteres", name="menciones del nombre",
   emoji="emojis", kaomoji="kaomojis aprox.", caps="palabras en MAYÚSCULAS", errors="Errores y soluciones",
   outputs="Salidas", reasoning="Razonamiento", answer="Respuesta", empty="(vacío)",
   repeats="Frases repetidas entre corridas", none="ninguna", notes="Notas",
   note1="Las métricas son conteos mecánicos; no juzgan calidad ni fidelidad de voz.",
   note2="Una corrida por celda es anecdótica: repite (--runs) antes de decidir.",
   lines="líneas", ok="ok", runs="corridas"),
 "en": dict(title="SOUL test report", setup="Setup", endpoint="Endpoint", models="Models",
   params="Parameters", defaults="none sent (provider defaults)", date="Date", souls="Candidates",
   control="control (no SOUL)", prompt="Request sent", summary="Summary", status="status",
   latency="latency", tok_in="tokens in", tok_out="tokens out", tok_reason="reasoning tokens",
   chars="chars", name="name mentions", emoji="emojis", kaomoji="kaomojis approx.",
   caps="ALL-CAPS words", errors="Errors and fixes", outputs="Outputs", reasoning="Reasoning",
   answer="Answer", empty="(empty)", repeats="Phrases repeated across runs", none="none",
   notes="Notes", note1="Metrics are mechanical counts; they do not judge quality or voice fidelity.",
   note2="One run per cell is anecdotal: repeat (--runs) before deciding.", lines="lines",
   ok="ok", runs="runs"),
}

HINTS = {  # error kind -> (es, en)
 "no_key": ("No encontré la API key. Crea la variable de entorno {env} donde corre el script, o añade una línea {env}=... a un .env (./.env, el --env-file, o $HERMES_HOME/.env). El agente no debe escribir la key: hazlo tú.",
            "API key not found. Set the environment variable {env} where the script runs, or add {env}=... to a .env (./.env, --env-file, or $HERMES_HOME/.env). Do it yourself; the agent must not type the key."),
 "401": ("401/403: la key no es válida para este endpoint o no tiene permiso para el modelo. Revisa que la variable apunte a la key de ESTE proveedor.",
         "401/403: the key is invalid for this endpoint or lacks access to the model. Check the variable holds the key for THIS provider."),
 "404": ("404: la ruta no existe. Usa la URL base de la API (p. ej. https://api.proveedor.com/v1); el script añade /chat/completions. Prueba --check.",
         "404: path not found. Use the API base URL (e.g. https://api.provider.com/v1); the script appends /chat/completions. Try --check."),
 "model": ("El modelo no existe o no está disponible en este endpoint. Usa --check para listar los modelos que expone.",
           "The model does not exist or is not available here. Use --check to list the models it exposes."),
 "400": ("400: el proveedor rechazó la solicitud. Si pasaste parámetros custom, quítalos o usa los nombres que acepta ese proveedor (--extra). Mensaje: {msg}",
         "400: the provider rejected the request. If you passed custom parameters, drop them or use the names this provider accepts (--extra). Message: {msg}"),
 "429": ("429: límite de uso o sin saldo. Baja --parallel, espera, o revisa el saldo de la cuenta.",
         "429: rate limit or no credit. Lower --parallel, wait, or check the account balance."),
 "5xx": ("Error del servidor ({code}). Reintenté; si persiste es del proveedor, prueba más tarde u otro modelo.",
         "Server error ({code}). Retried; if it persists it is the provider's side, try later or another model."),
 "html": ("El endpoint devolvió HTML, no JSON: apunta a una página web, no a la API. Busca la URL base de la API en la documentación del proveedor.",
          "The endpoint returned HTML, not JSON: it points to a web page, not the API. Find the API base URL in the provider docs."),
 "dns": ("No se resuelve el host. Revisa que la URL esté bien escrita y que haya red desde donde corre el script (un sandbox o contenedor puede no tener salida).",
         "Host does not resolve. Check the URL spelling and that the place running the script has network (a sandbox or container may have no egress)."),
 "refused": ("Conexión rechazada. Si es un servidor local (Ollama, LM Studio, vLLM) comprueba que esté encendido y el puerto. Desde Docker, localhost es el contenedor: usa host.docker.internal.",
             "Connection refused. For a local server (Ollama, LM Studio, vLLM) check it is running and the port. Inside Docker, localhost is the container: use host.docker.internal."),
 "ssl": ("Error SSL. Si es un servidor local sin certificado usa http://; si es un proxy corporativo, faltan sus certificados.",
         "SSL error. For a local server without a certificate use http://; behind a corporate proxy its certificates are missing."),
 "timeout": ("Tiempo de espera agotado. Los modelos con razonamiento tardan: sube --timeout (p. ej. 600).",
             "Timed out. Reasoning models are slow: raise --timeout (e.g. 600)."),
 "shape": ("La respuesta no tiene el formato OpenAI (choices[0].message). Este endpoint quizá no es compatible con OpenAI; busca su ruta compatible o un proxy (OpenRouter, LiteLLM).",
           "The response is not OpenAI-shaped (choices[0].message). The endpoint may not be OpenAI-compatible; find its compatible route or use a proxy (OpenRouter, LiteLLM)."),
 "other": ("Error inesperado: {msg}", "Unexpected error: {msg}"),
}

def hint(kind, lang, **kw):
    es, en = HINTS[kind]
    return (es if lang == "es" else en).format(**kw)

# ---------------------------------------------------------------- env / key
def parse_env_file(p):
    out = {}
    try:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.replace("export ", "").strip()
            out[k] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out

def find_key(env_name, env_file):
    """Return (key, source). Never returns the key in logs."""
    if os.environ.get(env_name):
        return os.environ[env_name], "environment"
    candidates = [env_file] if env_file else []
    candidates.append(".env")
    if os.environ.get("HERMES_HOME"):
        candidates.append(os.path.join(os.environ["HERMES_HOME"], ".env"))
    candidates.append(os.path.expanduser("~/.hermes/.env"))
    for c in candidates:
        if c and os.path.isfile(c):
            v = parse_env_file(c).get(env_name)
            if v:
                return v, c
    return None, None

# ---------------------------------------------------------------- endpoint
def normalize_endpoint(ep):
    """Return (chat_url, base_url, warnings)."""
    w = []
    ep = ep.strip()
    if not re.match(r"^https?://", ep):
        local = re.match(r"^(localhost|127\.|0\.0\.0\.0|host\.docker\.internal)", ep)
        ep = ("http://" if local else "https://") + ep
        w.append(f"scheme added: {ep}")
    ep = ep.rstrip("/")
    for suffix in ("/chat/completions", "/models", "/completions", "/responses", "/messages"):
        if ep.endswith(suffix):
            if suffix != "/chat/completions":
                w.append(f"'{suffix}' replaced by /chat/completions")
            ep = ep[: -len(suffix)]
            break
    return ep + "/chat/completions", ep, w

def has_version(base):
    return bool(re.search(r"/v\d+[a-z0-9]*$", base) or re.search(r"/api/v\d", base))

# ---------------------------------------------------------------- http
def http(method, url, key, body=None, timeout=180):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
        return r.status, raw, r.headers.get("Content-Type", ""), time.time() - t0

def classify(exc):
    """Map an exception to (kind, code, message)."""
    if isinstance(exc, urllib.error.HTTPError):
        code = exc.code
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        msg = body[:400]
        try:
            j = json.loads(body)
            e = j.get("error", j)
            msg = (e.get("message") if isinstance(e, dict) else str(e)) or msg
        except Exception:
            pass
        low = msg.lower()
        if code in (401, 403):
            return "401", code, msg
        if code == 404 and ("model" in low and ("not" in low or "exist" in low or "found" in low)):
            return "model", code, msg
        if code == 404:
            return "404", code, msg
        if code in (400, 422) and "model" in low and ("not" in low or "invalid" in low or "exist" in low):
            return "model", code, msg
        if code in (400, 422):
            return "400", code, msg
        if code == 429:
            return "429", code, msg
        if code >= 500:
            return "5xx", code, msg
        return "other", code, msg
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "timeout", None, str(exc)
    if isinstance(exc, urllib.error.URLError):
        r = exc.reason
        if isinstance(r, ssl.SSLError):
            return "ssl", None, str(r)
        if isinstance(r, (socket.timeout, TimeoutError)):
            return "timeout", None, str(r)
        if isinstance(r, ConnectionRefusedError):
            return "refused", None, str(r)
        if isinstance(r, socket.gaierror):
            return "dns", None, str(r)
        return "other", None, str(r)
    return "other", None, f"{type(exc).__name__}: {exc}"

def extract(raw, ctype):
    """Return dict with content, reasoning, usage, or raise ValueError(kind)."""
    s = raw.lstrip()
    if "html" in ctype.lower() or s.startswith("<"):
        raise ValueError("html")
    try:
        j = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("shape")
    try:
        msg = j["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        raise ValueError("shape")
    content = msg.get("content")
    if isinstance(content, list):  # some proxies return content parts
        content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict))
    reasoning = msg.get("reasoning_content") or msg.get("reasoning") or msg.get("thinking") or ""
    if isinstance(reasoning, (list, dict)):
        reasoning = json.dumps(reasoning, ensure_ascii=False)
    u = j.get("usage") or {}
    det = u.get("completion_tokens_details") or {}
    return dict(content=content or "", reasoning=reasoning or "",
                tok_in=u.get("prompt_tokens"), tok_out=u.get("completion_tokens"),
                tok_reason=det.get("reasoning_tokens"),
                finish=j["choices"][0].get("finish_reason"), model_echo=j.get("model"))

def call(chat_url, key, payload, timeout, retries=2):
    last = None
    for attempt in range(retries + 1):
        try:
            status, raw, ctype, lat = http("POST", chat_url, key, payload, timeout)
            out = extract(raw, ctype)
            out.update(ok=True, latency=round(lat, 1))
            return out
        except ValueError as e:
            return dict(ok=False, kind=str(e), code=None, msg="")
        except Exception as e:  # noqa: BLE001
            kind, code, msg = classify(e)
            last = dict(ok=False, kind=kind, code=code, msg=msg)
            if kind in ("429", "5xx", "timeout") and attempt < retries:
                time.sleep(2 * (attempt + 1) * (3 if kind == "429" else 1))
                continue
            return last
    return last

# ---------------------------------------------------------------- metrics
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]")
KAOMOJI = re.compile(r"[(（][^()（）\n]{1,12}[)）]")
CAPS = re.compile(r"\b[A-ZÁÉÍÓÚÑ]{3,}\b")

def is_kaomoji(s):
    inner = s[1:-1]
    sym = sum(1 for ch in inner if not ch.isalnum() and not ch.isspace())
    return sym >= 2 and len(re.findall(r"[A-Za-z]{3,}", inner)) == 0

def soul_name(text):
    m = re.search(r"(?:Eres|Sos|Tú eres|You are|I am|Soy|Me llamo|Você é|Tu es|Du bist)\s+([^\W\d_a-z][\w'-]*)", text)
    return m.group(1) if m else None

def metrics(text, name):
    return dict(chars=len(text), emoji=len(EMOJI.findall(text)),
                kaomoji=sum(1 for k in KAOMOJI.findall(text) if is_kaomoji(k)),
                caps=len(CAPS.findall(text)),
                name=(len(re.findall(rf"\b{re.escape(name)}\b", text)) if name else None))

def repeated_phrases(texts, n=4, min_runs=2):
    seen = {}
    for i, t in enumerate(texts):
        words = re.findall(r"\w+", t.lower())
        grams = {" ".join(words[k:k + n]) for k in range(len(words) - n + 1)}
        for g in grams:
            seen.setdefault(g, set()).add(i)
    rep = sorted((g for g, s in seen.items() if len(s) >= min_runs), key=len, reverse=True)
    return rep[:8]

# ---------------------------------------------------------------- prompts
def load_prompt(path, lang):
    """verbose-request.md holds fenced blocks tagged ```request-es / ```request-en."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    m = re.search(rf"```request-{lang}\n(.*?)```", text, re.S) or re.search(r"```request-en\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()

# ---------------------------------------------------------------- report
def fence(s):
    s = s or ""
    tick = "`" * max(3, 1 + max((len(x) for x in re.findall(r"`+", s)), default=0))
    return f"{tick}text\n{s}\n{tick}"

def report(args, lab, souls, prompt, results, warnings):
    out = [f"# {lab['title']}", "", f"## {lab['setup']}", "",
           f"- {lab['date']}: {dt.datetime.now().isoformat(timespec='minutes')}",
           f"- {lab['endpoint']}: `{args.chat_url}`",
           f"- {lab['models']}: " + ", ".join(f"`{m}`" for m in args.model_list),
           f"- {lab['params']}: " + (json.dumps(args.params, ensure_ascii=False) if args.params else lab["defaults"]),
           f"- {lab['runs']}: {args.runs}",
           f"- {lab['souls']}:"]
    for s in souls:
        if s["text"] is None:
            out.append(f"  - **{s['label']}**: {lab['control']}")
        else:
            out.append(f"  - **{s['label']}**: `{s['path']}`, {s['text'].count(chr(10)) + 1} {lab['lines']}, sha1 {s['sha']}")
    out.append(f"- Test mode: {'augmented context (not verified Hermes)' if args.context_file else 'isolated SOUL'}")
    if args.expect_data:
        out += ["", "### Human evaluation targets (not automatically scored)"]
        for name, spec in args.expect_data["candidates"].items():
            out.append(f"- **{name}**: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in spec.items() if isinstance(v, list)))
    for w in warnings:
        out.append(f"- ⚠ {w}")
    out += ["", f"### {lab['prompt']}", "", fence(prompt), "", f"## {lab['summary']}", "",
            f"| model | soul | run | {lab['status']} | {lab['latency']} | {lab['tok_in']} | {lab['tok_out']} | {lab['tok_reason']} | {lab['chars']} | {lab['name']} | {lab['emoji']} | {lab['kaomoji']} | {lab['caps']} |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    errs = []
    for r in results:
        if r["ok"]:
            m = r["m"]
            cells = [lab["ok"], f"{r['latency']}s", r.get("tok_in"), r.get("tok_out"), r.get("tok_reason"),
                     m["chars"], m["name"], m["emoji"], m["kaomoji"], m["caps"]]
        else:
            cells = [f"❌ {r['kind']}{' ' + str(r['code']) if r.get('code') else ''}"] + ["-"] * 9
            errs.append(r)
        out.append(f"| `{r['model']}` | {r['soul']} | {r['run']} | " + " | ".join("-" if c is None else str(c) for c in cells) + " |")
    out += ["", f"## {lab['errors']}", ""]
    if not errs:
        out.append(lab["none"])
    seen = set()
    for r in errs:
        key = (r["model"], r["kind"])
        if key in seen:
            continue
        seen.add(key)
        n = sum(1 for x in errs if x["model"] == r["model"] and x["kind"] == r["kind"])
        out.append(f"- `{r['model']}` ({n}x): **{r['kind']}**. " + hint(r["kind"], args.lang, env=args.key_env, code=r.get("code"), msg=(r.get("msg") or "")[:300]))
    out += ["", f"## {lab['repeats']}", ""]
    any_rep = False
    for model in args.model_list:
        for s in souls:
            texts = [r["content"] for r in results if r["ok"] and r["model"] == model and r["soul"] == s["label"]]
            if len(texts) >= 2:
                rep = repeated_phrases(texts)
                if rep:
                    any_rep = True
                    out.append(f"- `{model}` / {s['label']}: " + "; ".join(f"“{g}”" for g in rep))
    if not any_rep:
        out.append(lab["none"] + (f" ({lab['runs']} = 1)" if args.runs < 2 else ""))
    out += ["", f"## {lab['outputs']}", ""]
    for model in args.model_list:
        out += [f"### `{model}`", ""]
        for s in souls:
            for r in [x for x in results if x["model"] == model and x["soul"] == s["label"]]:
                out.append(f"#### {s['label']} · run {r['run']}")
                out.append("")
                if not r["ok"]:
                    out += [f"❌ {r['kind']}: {(r.get('msg') or '')[:300]}", ""]
                    continue
                if r.get("reasoning"):
                    out += [f"<details><summary>{lab['reasoning']} ({len(r['reasoning'])} {lab['chars']})</summary>", "", fence(r["reasoning"]), "", "</details>", ""]
                out += [f"**{lab['answer']}**", "", fence(r["content"] or lab["empty"]), ""]
    out += [f"## {lab['notes']}", "", f"- {lab['note1']}", f"- {lab['note2']}", ""]
    return "\n".join(out)

# ---------------------------------------------------------------- main
def parse_soul_args(items):
    souls = []
    for it in items:
        label, _, path = it.partition("=") if "=" in it else (Path(it).stem, "", it)
        p = Path(path).expanduser()
        if not p.is_file():
            sys.exit(f"SOUL file not found: {p}")
        text = p.read_text(encoding="utf-8")
        souls.append(dict(label=label, path=str(p), text=text, sha=hashlib.sha1(text.encode()).hexdigest()[:8]))
    validate_souls(souls)
    return souls

def check(args, key, key_src):
    lang = args.lang
    print(f"endpoint -> {args.chat_url}")
    for w in args.warnings:
        print(f"  warning: {w}")
    print(f"key {args.key_env}: " + (f"found ({key_src}, {len(key)} chars)" if key else ("not required (--no-key)" if args.no_key else "MISSING")))
    if not key and not args.no_key:
        print("  -> " + hint("no_key", lang, env=args.key_env))
        return 2
    try:
        _, raw, ctype, _ = http("GET", args.base + "/models", key, timeout=30)
        ids = [m.get("id") for m in json.loads(raw).get("data", [])]
        print(f"/models: {len(ids)} models")
        for m in args.model_list:
            print(f"  {m}: " + ("listed" if m in ids else "NOT listed (may still work through aliases)"))
    except Exception as e:  # noqa: BLE001
        kind, code, msg = classify(e)
        print(f"/models: not available ({kind} {code or ''}); not fatal")
    rc = 0
    for m in args.model_list:
        r = call(args.chat_url, key, {"model": m, "messages": [{"role": "user", "content": "ping"}], **args.params}, args.timeout, retries=0)
        if r["ok"]:
            print(f"chat {m}: ok ({r['latency']}s)")
        else:
            rc = 1
            print(f"chat {m}: {r['kind']} {r.get('code') or ''} -> " + hint(r["kind"], lang, env=args.key_env, code=r.get("code"), msg=(r.get("msg") or "")[:200]))
    return rc

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--endpoint", required=True, help="API base URL, e.g. https://api.x.com/v1")
    ap.add_argument("--models", required=True, help="comma-separated model ids")
    ap.add_argument("--key-env", default="OPENAI_API_KEY", help="name of the env var holding the key")
    ap.add_argument("--env-file", help="extra .env file to read the key from")
    ap.add_argument("--no-key", action="store_true", help="local servers without auth")
    ap.add_argument("--soul", action="append", default=[], help="LABEL=path/to/SOUL.md (repeat)")
    ap.add_argument("--control", action="store_true", help="also run with no SOUL")
    ap.add_argument("--prompt-file", help="verbose request (plain text, or md with ```request-xx blocks)")
    ap.add_argument("--lang", default="es", help="language code for prompts/scenarios/report (es, en built in; others fall back to English)")
    ap.add_argument("--runs", type=positive_int, default=1)
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--max-tokens", type=int)
    ap.add_argument("--reasoning-effort")
    ap.add_argument("--extra", help="JSON merged into every payload, e.g. '{\"thinking\":{\"type\":\"disabled\"}}'")
    ap.add_argument("--timeout", type=positive_int, default=300)
    ap.add_argument("--parallel", type=positive_int, default=3)
    ap.add_argument("--out-dir", default="soul-test-out")
    ap.add_argument("--context-file", help="extra system context (approximation, not a real Hermes session)")
    ap.add_argument("--expectations", help="optional candidate behavioral targets JSON; for human grading only")
    ap.add_argument("--include-reasoning", action="store_true", help="opt-in: save provider-exposed reasoning in reports (may be sensitive)")
    ap.add_argument("--check", action="store_true", help="diagnose key, endpoint and models, then exit")
    ap.add_argument("--dry-run", action="store_true", help="print payloads, no network")
    ap.add_argument("--manifest", help="soul-creator manifest.json: adds every rendered variant as a candidate")
    args = ap.parse_args()
    args.soul = list(args.soul) + manifest_soul_args(args.manifest)
    if warn_lang(args.lang):
        print("warning: " + warn_lang(args.lang), file=sys.stderr)

    try:
        args.model_list = parse_models(args.models)
    except ValueError as e:
        ap.error(str(e))
    args.chat_url, args.base, args.warnings = normalize_endpoint(args.endpoint)
    args.params = {}
    if args.temperature is not None:
        if not 0 <= args.temperature <= 2: ap.error("--temperature must be between 0 and 2")
        args.params["temperature"] = args.temperature
    if args.max_tokens is not None:
        if args.max_tokens < 1: ap.error("--max-tokens must be positive")
        args.params["max_tokens"] = args.max_tokens
    if args.reasoning_effort: args.params["reasoning_effort"] = args.reasoning_effort
    try:
        args.params = parse_extra(args.extra, args.params)
        args.expect_data = read_expectations(args.expectations)
        if args.context_file:
            context_messages(args.context_file, None)
    except (ValueError, OSError) as e:
        ap.error(str(e))

    # Check candidate integrity before optional endpoint probing; --check may
    # make live calls, so a mislabeled control must fail before any such call.
    try:
        souls = parse_soul_args(args.soul)
        if args.control:
            souls.append(dict(label="control", path="", text=None, sha="-"))
        validate_souls(souls)
    except ValueError as e:
        ap.error(str(e))
    key, key_src = (None, None) if args.no_key else find_key(args.key_env, args.env_file)
    if args.check:
        sys.exit(check(args, key, key_src))
    if len([s for s in souls if s["text"]]) < 1:
        sys.exit("give at least one --soul (two or more to compare)")
    prompt = load_prompt(args.prompt_file or DEFAULT_PROMPTS, args.lang)

    jobs = []
    for m in args.model_list:
        for s in souls:
            msgs = context_messages(args.context_file, s["text"]) + [{"role": "user", "content": prompt}]
            for run in range(1, args.runs + 1):
                jobs.append((m, s, run, {"model": m, "messages": msgs, **args.params}))

    if args.dry_run:
        for m, s, run, p in jobs:
            print(json.dumps({"model": m, "soul": s["label"], "run": run,
                              "message_count": len(p["messages"]),
                              "system_sha256": [sha(x["content"]) for x in p["messages"] if x["role"] == "system"],
                              "parameters": args.params}, ensure_ascii=False))
        print(f"{len(jobs)} calls -> {args.chat_url}; key {'not required' if args.no_key else ('found in ' + str(key_src) if key else 'MISSING')}")
        return

    if not key and not args.no_key:
        sys.exit(hint("no_key", args.lang, env=args.key_env))

    # 404 on a URL without /vN: retry once with /v1 before running everything
    if not has_version(args.base):
        probe = call(args.chat_url, key, jobs[0][3], args.timeout, retries=0)
        if not probe["ok"] and probe["kind"] == "404":
            alt = args.base + "/v1/chat/completions"
            if call(alt, key, jobs[0][3], args.timeout, retries=0).get("kind") != "404":
                args.warnings.append(f"404 at {args.chat_url}; using {alt}")
                args.chat_url = alt

    results = []
    with cf.ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
        futs = {ex.submit(call, args.chat_url, key, p, args.timeout): (m, s, run) for m, s, run, p in jobs}
        for f in cf.as_completed(futs):
            m, s, run = futs[f]
            r = strip_reasoning(f.result(), args.include_reasoning)
            r.update(model=m, soul=s["label"], run=run)
            if r["ok"]:
                r["m"] = metrics(r["content"], soul_name(s["text"] or ""))
            results.append(r)
            print(f"{m} / {s['label']} / run {run}: " + ("ok" if r["ok"] else f"{r['kind']} {r.get('code') or ''}"), flush=True)
    order = {(m, s["label"]): i for i, (m, s) in enumerate((m, s) for m in args.model_list for s in souls)}
    results.sort(key=lambda r: (order[(r["model"], r["soul"])], r["run"]))

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(report(args, L.get(args.lang, L["en"]), souls, prompt, results, args.warnings), encoding="utf-8")
    total = len(jobs)
    ok = sum(r["ok"] for r in results)
    summary = {"planned": total, "completed": len(results), "ok": ok, "failed": total - ok,
               "complete": (ok == total), "mode": "augmented-context" if args.context_file else "isolated",
               "prompt_sha256": sha(prompt), "expectations": args.expect_data}
    (out / "slot-audit.json").write_text(json.dumps(slot_audit(souls, args.context_file), indent=2), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "results.json").write_text(json.dumps(
        {"endpoint": args.chat_url, "params": args.params, "prompt": prompt,
         "context_sha256": sha(Path(args.context_file).read_text(encoding="utf-8")) if args.context_file else None,
         "souls": [{"label": x["label"], "sha256": sha(x["text"] or "")} for x in souls],
         "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    guide = single_preview(souls, args.model_list, prompt, results, args.lang)
    (out / "choice-guide.md").write_text(guide, encoding="utf-8")
    print(f"\n{ok}/{total} ok -> {out / 'report.md'}")
    print(f"\n{terminal_preview(guide)}\n")
    print(f"Vista de elección: {out / 'choice-guide.md'}")
    sys.exit(0 if ok == total else (3 if ok else 1))

if __name__ == "__main__":
    main()
