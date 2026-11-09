#!/usr/bin/env python3
"""soul_multiturn.py - multi-turn SOUL test.

Runs real conversations: the model's own replies stay in context, and some
turns paste long logs, JSON or code, so the context fills the way it does in a
working session. "Probe" turns are where the persona should show; the report
compares the first probe with the last to see whether the voice survived.

Scenario sets (JSON) live in ../assets/scenarios/:
  dev      visible while drafting and refining a SOUL
  heldout  final verdict only; the agent drafting the SOUL must not read it

Same endpoint, key and parameter rules as soul_test.py (key from an env var or
.env, never printed; sampling parameters sent only when given).

  python soul_multiturn.py --endpoint URL --models m1,m2 --key-env NAME \
      --soul A=a.md --soul B=b.md --control --set dev --lang es --out-dir out-dev
  python soul_multiturn.py ... --set heldout --sample 3 --seed 7 --out-dir out-final
"""
import argparse, concurrent.futures as cf, datetime as dt, hashlib, json, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from soul_test import (call, find_key, normalize_endpoint, has_version, metrics,  # noqa: E402
                       soul_name, parse_soul_args, hint, fence, L)
from decision_preview import multi_preview, terminal_preview
from test_config import (manifest_soul_args, warn_lang, positive_int, parse_models, parse_extra, validate_souls,
                         context_messages, strip_reasoning, read_expectations, sha, slot_audit)

SETS = HERE.parent / "assets" / "scenarios"

ML = {
 "es": dict(title="Reporte de prueba de SOUL: varios turnos", set="Set", scen="Escenarios",
   summary="Resumen por conversación", turns="turnos ok", ctx="contexto final aprox.",
   first="primer sondeo", last="último sondeo", dm="Δ marcadores", convs="Conversaciones",
   user="Usuario", probe="sondeo", what="Qué prueba", calls="llamadas",
   heldout="Set reservado: el agente que redacta el SOUL no debe leer estos escenarios ni este reporte antes de cerrar el candidato. Si cambias el SOUL por lo que viste aquí, la siguiente verificación final debe usar otra muestra (--seed) o escenarios nuevos.",
   probe_note="Los marcadores solo son señales de superficie; no prueban deriva. Compara a ciegas los rasgos observables en los sondeos.",
   judge_note="Las cifras son mecánicas. El veredicto sale de leer las conversaciones: conducta en cada sondeo, exactitud en los turnos técnicos y honestidad."),
 "en": dict(title="SOUL test report: multi-turn", set="Set", scen="Scenarios",
   summary="Summary per conversation", turns="turns ok", ctx="final context approx.",
   first="first probe", last="last probe", dm="Δ markers", convs="Conversations",
   user="User", probe="probe", what="What it tests", calls="calls",
   heldout="Held-out set: the agent drafting the SOUL must not read these scenarios or this report before the candidate is closed. If you change the SOUL because of what you saw here, the next final check requires independent new scenarios; changing the seed does not restore a clean holdout.",
   probe_note="Markers are surface diagnostics, not evidence of drift. Blindly compare observable traits across probes.",
   judge_note="Numbers are mechanical. The verdict comes from reading the conversations: behavior at each probe, accuracy on technical turns, honesty."),
}

# ---------------------------------------------------------------- attachments
def _insert(lines, needle, rnd):
    if needle:
        pos = int(len(lines) * rnd.uniform(0.55, 0.85))
        lines[pos:pos] = needle.splitlines()
    return "\n".join(lines)

def gen_log(n, needle, seed):
    rnd = random.Random(seed)
    lv = ["INFO"] * 8 + ["DEBUG"] * 5 + ["WARN"] * 2
    sv = ["api", "worker", "db", "cache", "auth", "scheduler"]
    lines = [f"2026-10-14T03:{(i // 60) % 60:02d}:{i % 60:02d}.{rnd.randint(0, 999):03d}Z {rnd.choice(lv):5} "
             f"[{rnd.choice(sv)}] req={rnd.randint(10000, 99999)} took={rnd.randint(1, 900)}ms "
             f"status={rnd.choice([200, 200, 200, 201, 204, 304])}" for i in range(n)]
    return _insert(lines, needle, rnd)

def gen_code(n, needle, seed):
    rnd = random.Random(seed)
    lines = ["import logging", "from db import pool", "", "log = logging.getLogger(__name__)", ""]
    i = 0
    while len(lines) < n:
        k = rnd.randint(2, 9)
        lines += [f"def handler_{i}(payload):", f"    data = payload.get(\"item_{i}\", {{}})",
                  "    if not data:", "        return None",
                  f"    return {{\"id\": {i}, \"value\": data.get(\"value\", 0) * {k}}}", ""]
        i += 1
    return _insert(lines, needle, rnd)

def gen_json(n, needle, seed):
    rnd = random.Random(seed)
    lines = [json.dumps({"id": 1000 + i, "user": f"u{rnd.randint(1, 500)}", "status": "ok",
                         "bytes": rnd.randint(100, 90000), "ms": rnd.randint(3, 400)}) for i in range(n)]
    return _insert(lines, needle, rnd)

ATTACH = {"log": gen_log, "code": gen_code, "json": gen_json}

def build_turns(sc, lang, seed):
    out = []
    for i, t in enumerate(sc["turns"]):
        text = t.get(lang) or t.get("en") or t.get("es")
        shown = text
        a = t.get("attach")
        if a:
            n = a.get("lines", 100)
            body = ATTACH[a["kind"]](n, a.get("needle"), seed * 100 + i)
            text = f"{text}\n\n```\n{body}\n```"
            shown += f"\n\n[{a['kind']}, ~{n} lines" + (f"; key line: {a['needle'].splitlines()[0]}" if a.get("needle") else "") + "]"
        out.append(dict(text=text, shown=shown, probe=bool(t.get("probe") or t.get("attack"))))
    return out

# ---------------------------------------------------------------- run
def converse(url, key, model, system, turns, params, timeout, context_file=None, include_reasoning=False):
    msgs = context_messages(context_file, system)
    res = []
    for t in turns:
        msgs.append({"role": "user", "content": t["text"]})
        r = strip_reasoning(call(url, key, {"model": model, "messages": list(msgs), **params}, timeout), include_reasoning)
        r["ctx_chars"] = sum(len(m["content"]) for m in msgs)
        res.append(r)
        if not r["ok"]:
            break
        msgs.append({"role": "assistant", "content": r["content"]})  # reasoning is not sent back
    return res

def load_set(name):
    p = SETS / f"{name}.json" if (SETS / f"{name}.json").is_file() else Path(name)
    if not p.is_file():
        sys.exit(f"scenario set not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "turns" in data and "scenarios" not in data:
        # a single scenario file (e.g. soul-creator templates/scenarios/*.json): wrap it as a set
        data = {"set": data.get("id", p.stem), "scenarios": [
            {"id": data.get("id", p.stem), "what": data.get("what") or data.get("description", ""), "turns": data["turns"]}]}
    return data, p

def pfmt(m):
    return f"{m['chars']} / {m['emoji'] + m['kaomoji']} / {m['name'] if m['name'] is not None else '-'}"

# ---------------------------------------------------------------- report
def report(args, souls, data, scen, convs):
    lab, ml = L.get(args.lang, L["en"]), ML.get(args.lang, ML["en"])
    o = [f"# {ml['title']}", "", f"## {lab['setup']}", "",
         f"- {lab['date']}: {dt.datetime.now().isoformat(timespec='minutes')}",
         f"- {lab['endpoint']}: `{args.chat_url}`",
         f"- {lab['models']}: " + ", ".join(f"`{m}`" for m in args.model_list),
         f"- {lab['params']}: " + (json.dumps(args.params, ensure_ascii=False) if args.params else lab["defaults"]),
         f"- {ml['set']}: `{data.get('set', args.set)}`" + (f" (sample {args.sample}, seed {args.seed})" if args.sample else ""),
         f"- {lab['runs']}: {args.runs}", f"- {lab['souls']}:"]
    for s in souls:
        o.append(f"  - **{s['label']}**: " + (lab["control"] if s["text"] is None else f"`{s['path']}`, sha1 {s['sha']}"))
    o.append(f"- Test mode: {'augmented context (not verified Hermes)' if args.context_file else 'isolated SOUL'}")
    if args.expect_data:
        o += ["", "### Behavioral targets for human scoring (not automatically graded)"]
        for name, spec in args.expect_data["candidates"].items():
            o.append(f"- **{name}**: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in spec.items() if isinstance(v, list)))
    for w in args.warnings:
        o.append(f"- ⚠ {w}")
    if data.get("set") == "heldout":
        o += ["", f"> {ml['heldout']}"]
    o += ["", f"### {ml['scen']}", ""]
    for sc in scen:
        o.append(f"- `{sc['id']}` ({len(sc['turns'])}): {sc.get('what', '')}")
    o += ["", f"## {ml['summary']}", "", ml["probe_note"], "",
          f"| model | soul | scenario | run | {ml['turns']} | {ml['ctx']} | {ml['first']} | {ml['last']} | {ml['dm']} |",
          "|---|---|---|---|---|---|---|---|---|"]
    errs = []
    for c in convs:
        oks = [r for r in c["res"] if r["ok"]]
        probes = [r for r, t in zip(c["res"], c["turns"]) if t["probe"] and r["ok"]]
        last_in = next((r.get("tok_in") for r in reversed(oks) if r.get("tok_in")), None)
        ctx = f"{last_in} tok" if last_in else (f"~{c['res'][-1]['ctx_chars'] // 4} tok" if c["res"] else "-")
        f1 = pfmt(probes[0]["m"]) if probes else "-"
        f2 = pfmt(probes[-1]["m"]) if len(probes) > 1 else "-"
        dm = "-"
        if len(probes) > 1:
            a, b = probes[0]["m"], probes[-1]["m"]
            dm = f"{(b['emoji'] + b['kaomoji']) - (a['emoji'] + a['kaomoji']):+d}"
        o.append(f"| `{c['model']}` | {c['soul']} | {c['sid']} | {c['run']} | {len(oks)}/{len(c['turns'])} | {ctx} | {f1} | {f2} | {dm} |")
        errs += [dict(r, model=c["model"]) for r in c["res"] if not r["ok"]]
    o += ["", f"## {lab['errors']}", ""]
    seen = set()
    for r in errs:
        if (r["model"], r["kind"]) in seen:
            continue
        seen.add((r["model"], r["kind"]))
        o.append(f"- `{r['model']}`: **{r['kind']}**. " + hint(r["kind"], args.lang, env=args.key_env, code=r.get("code"), msg=(r.get("msg") or "")[:300]))
    if not errs:
        o.append(lab["none"])
    o += ["", f"## {ml['convs']}", ""]
    for c in convs:
        o += [f"### `{c['model']}` · {c['soul']} · {c['sid']} · run {c['run']}", ""]
        for i, (t, r) in enumerate(zip(c["turns"], c["res"]), 1):
            o += [f"**{i}. {ml['user']}**" + (f" ({ml['probe']})" if t["probe"] else ""), "", fence(t["shown"]), ""]
            if not r["ok"]:
                o += [f"❌ {r['kind']}: {(r.get('msg') or '')[:300]}", ""]
                continue
            if r.get("reasoning"):
                o += [f"<details><summary>{lab['reasoning']} ({len(r['reasoning'])} {lab['chars']})</summary>", "", fence(r["reasoning"]), "", "</details>", ""]
            o += [f"**{lab['answer']}**", "", fence(r["content"] or lab["empty"]), ""]
    o += [f"## {lab['notes']}", "", f"- {ml['judge_note']}", f"- {lab['note2']}", ""]
    return "\n".join(o)

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--models", required=True)
    ap.add_argument("--key-env", default="OPENAI_API_KEY")
    ap.add_argument("--env-file")
    ap.add_argument("--no-key", action="store_true")
    ap.add_argument("--soul", action="append", default=[])
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--set", default="dev", help="dev | heldout | path to a scenario JSON")
    ap.add_argument("--ids", help="comma-separated scenario ids to run")
    ap.add_argument("--sample", type=positive_int, help="run a random subset of N scenarios")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lang", default="es", help="language code for prompts/scenarios/report (es, en built in; others fall back to English)")
    ap.add_argument("--runs", type=positive_int, default=1)
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--max-tokens", type=int)
    ap.add_argument("--reasoning-effort")
    ap.add_argument("--extra")
    ap.add_argument("--timeout", type=positive_int, default=300)
    ap.add_argument("--parallel", type=positive_int, default=3)
    ap.add_argument("--out-dir", default="soul-test-multi")
    ap.add_argument("--context-file", help="extra system prompt; approximate context, NOT exact Hermes runtime")
    ap.add_argument("--expectations", help="behavioral expectations JSON for human review only")
    ap.add_argument("--include-reasoning", action="store_true", help="opt-in to retain potentially sensitive provider-exposed reasoning")
    ap.add_argument("--heldout-ledger", help="JSON ledger for exposed heldout scenario ids (default: ~/.cache/soul-tester/heldout-ledger.json)")
    ap.add_argument("--allow-heldout-reuse", action="store_true", help="override exposure guard (then NOT a fresh heldout run)")
    ap.add_argument("--dry-run", action="store_true")
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

    data, scenario_path = load_set(args.set)
    if not isinstance(data, dict) or not isinstance(data.get("scenarios"), list):
        ap.error("scenario file must contain scenarios list")
    for sc in data["scenarios"]:
        if not isinstance(sc, dict) or not isinstance(sc.get("turns"), list) or not sc["turns"]:
            ap.error("every scenario must have a nonempty turns list")
        for t in sc["turns"]:
            if not isinstance(t, dict) or not any(isinstance(t.get(lang), str) and t.get(lang) for lang in ("es", "en")):
                ap.error("every turn needs a nonempty es or en prompt")
            a = t.get("attach")
            if a is not None and (not isinstance(a, dict) or a.get("kind") not in ATTACH or not isinstance(a.get("lines", 100), int) or not 1 <= a.get("lines", 100) <= 10000):
                ap.error("attach must use a supported kind and lines in [1,10000]")
    all_ids = [sc.get("id") for sc in data["scenarios"]]
    if not all(isinstance(sid, str) and sid for sid in all_ids) or len(all_ids) != len(set(all_ids)):
        ap.error("scenario ids must be nonempty and unique")
    scen = data["scenarios"]
    if args.ids:
        want = {x.strip() for x in args.ids.split(",")}
        missing = want - set(all_ids)
        if missing:
            ap.error("unknown --ids: " + ", ".join(sorted(missing)))
        scen = [s for s in scen if s["id"] in want]
    if args.sample and args.sample < len(scen):
        scen = random.Random(args.seed).sample(scen, args.sample)
    if not scen:
        sys.exit("no scenarios selected")
    if args.sample and args.sample > len(scen):
        ap.error("--sample cannot exceed available scenarios")

    souls = parse_soul_args(args.soul)
    if args.control:
        souls.append(dict(label="control", path="", text=None, sha="-"))
    try:
        validate_souls(souls)
    except ValueError as e:
        ap.error(str(e))
    if not any(s["text"] for s in souls):
        sys.exit("give at least one --soul (two or more to compare)")

    jobs = [(m, s, sc, run, build_turns(sc, args.lang, args.seed + run))
            for m in args.model_list for s in souls for sc in scen for run in range(1, args.runs + 1)]
    n_calls = sum(len(j[4]) for j in jobs)
    key, key_src = (None, None) if args.no_key else find_key(args.key_env, args.env_file)

    set_hash = hashlib.sha256(scenario_path.read_bytes()).hexdigest()
    ledger_path = Path(args.heldout_ledger) if args.heldout_ledger else Path.home() / ".cache" / "soul-tester" / "heldout-ledger.json"
    is_heldout = args.set == "heldout" or data.get("set") == "heldout"
    exposed = []
    ledger = {"exposures": []}
    if is_heldout:
        if ledger_path.exists():
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        for old in ledger.get("exposures", []):
            if old.get("sha256") == set_hash:
                exposed = sorted(set(exposed) | (set(old.get("ids", [])) & {sc["id"] for sc in scen}))
        if exposed and not args.allow_heldout_reuse and not args.dry_run:
            ap.error(f"heldout scenarios already exposed: {', '.join(exposed)}. Use new independent scenarios; --allow-heldout-reuse marks this a non-fresh test")
    if args.dry_run:
        for m, s, sc, run, turns in jobs:
            size = sum(len(t["text"]) for t in turns)
            print(f"{m} / {s['label']} / {sc['id']} / run {run}: {len(turns)} turns, ~{size // 4} user tokens")
        print(f"{len(jobs)} conversations, {n_calls} calls -> {args.chat_url}; key {'not required' if args.no_key else ('found in ' + str(key_src) if key else 'MISSING')}")
        return
    if not key and not args.no_key:
        sys.exit(hint("no_key", args.lang, env=args.key_env))

    if not has_version(args.base):
        ping = {"model": args.model_list[0], "messages": [{"role": "user", "content": "ping"}], **args.params}
        if call(args.chat_url, key, ping, args.timeout, retries=0).get("kind") == "404":
            alt = args.base + "/v1/chat/completions"
            if call(alt, key, ping, args.timeout, retries=0).get("kind") != "404":
                args.warnings.append(f"404 at {args.chat_url}; using {alt}")
                args.chat_url = alt

    if is_heldout:
        # Record exposure before making any calls so interrupted runs cannot be mistaken for fresh sets.
        ledger.setdefault("exposures", []).append({"sha256": set_hash, "ids": [sc["id"] for sc in scen],
                     "out_dir": str(Path(args.out_dir).resolve()), "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()})
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(f"{len(jobs)} conversations, {n_calls} calls", flush=True)
    convs = []
    with cf.ThreadPoolExecutor(max_workers=max(1, args.parallel)) as ex:
        futs = {ex.submit(converse, args.chat_url, key, m, s["text"], turns, args.params, args.timeout, args.context_file, args.include_reasoning): (m, s, sc, run, turns)
                for m, s, sc, run, turns in jobs}
        for f in cf.as_completed(futs):
            m, s, sc, run, turns = futs[f]
            res = f.result()
            name = soul_name(s["text"] or "")
            for r in res:
                if r["ok"]:
                    r["m"] = metrics(r["content"], name)
            convs.append(dict(model=m, soul=s["label"], sid=sc["id"], run=run, turns=turns, res=res))
            print(f"{m} / {s['label']} / {sc['id']} / run {run}: {sum(r['ok'] for r in res)}/{len(turns)} ok", flush=True)
    order = {(m, s["label"], sc["id"]): i for i, (m, s, sc) in
             enumerate((m, s, sc) for m in args.model_list for s in souls for sc in scen)}
    convs.sort(key=lambda c: (order[(c["model"], c["soul"], c["sid"])], c["run"]))

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(report(args, souls, data, scen, convs), encoding="utf-8")
    ok = sum(r["ok"] for c in convs for r in c["res"])
    summary = {"planned": n_calls, "completed": sum(len(c["res"]) for c in convs), "ok": ok,
               "failed_or_skipped": n_calls - ok, "complete": ok == n_calls,
               "set_sha256": set_hash, "heldout_reused": bool(exposed),
               "mode": "augmented-context" if args.context_file else "isolated",
               "expectations": args.expect_data}
    (out / "slot-audit.json").write_text(json.dumps(slot_audit(souls, args.context_file), indent=2), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "results.json").write_text(json.dumps(
        {"endpoint": args.chat_url, "params": args.params, "set": data.get("set", args.set),
         "set_sha256": set_hash,
         "context_sha256": sha(Path(args.context_file).read_text(encoding="utf-8")) if args.context_file else None,
         "souls": [{"label": x["label"], "sha256": sha(x["text"] or "")} for x in souls],
         "conversations": [dict(c, turns=[{"shown": t["shown"], "prompt_sha256": sha(t["text"]), "probe": t["probe"]} for t in c["turns"]]) for c in convs]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    guide = multi_preview(souls, args.model_list, scen, convs, args.lang)
    (out / "choice-guide.md").write_text(guide, encoding="utf-8")
    print(f"\n{ok}/{n_calls} ok -> {out / 'report.md'}")
    print(f"\n{terminal_preview(guide)}\n")
    print(f"Vista de elección: {out / 'choice-guide.md'}")
    sys.exit(0 if ok == n_calls else (3 if ok else 1))

if __name__ == "__main__":
    main()
