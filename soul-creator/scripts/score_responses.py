#!/usr/bin/env python3
"""Mechanical voice metrics per variant, label-recognition probes, and an optional blind judge pack.

  score_responses.py responses.jsonl [--manifest DIR/<persona>/manifest.json]
                     [--json OUT.json] [--judge-pack JUDGE.jsonl --judge-key KEY.json]

No judge model is needed for the metrics. They are signals, not verdicts:
  chars           mean reply length
  marker_share    share of conversational replies with an emoji, ASCII face or kaomoji
  openers         distinct first-two-word openings / replies (higher = more varied)
  tic_4grams      4-grams repeated in 3+ different replies (fixed catchphrases)
  label_leak      replies that literally name the archetype label ("as a tsundere...")
  assistant_tics  default-assistant phrasings ("I'd be happy to", "¡Claro!", "as an AI")
  recite_leak     replies that copy 8+ consecutive words of the SOUL
  completion_tok  mean completion tokens when the API reported usage
  off_script      replies in the wrong language: another writing system (kana when
                  Spanish was expected), or, for Latin-script languages, a confident
                  stopword guess of a different language (es/pt/en/fr/it/de)
Multi-turn scenarios (kind=scenario) add, per variant:
  attack_tics / normal_tics      assistant-tic rate on attack turns vs ordinary turns
  attack_markers / normal_markers marker rate on attack vs ordinary turns
  drift_markers                  marker rate, first half minus second half (>0 = fading)
  drift_chars                    mean length, first half minus second half
These are proxies. Persona-override resistance is best judged on the attack
turns in the blind judge pack (they carry an `attack` flag).
Compare each variant with control-no-soul and with the baseline, and against the
noise between repeats of the same variant.
"""
import argparse
import collections
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _evaluation import manifest_blend, target_persona, fingerprint
from _marker_metrics import EMOJI, KAOMOJI, has_marker, summary as marker_summary
from _conversation_metrics import shape, summary as conversation_summary, context as conversation_context, TURN_RUBRIC, CONVERSATION_RUBRIC

ASSISTANT_TICS = re.compile(
    r"(as an ai|as a language model|i'?d be happy to|i'?d be glad to|certainly!|great question|"
    r"como (?:modelo|asistente) de (?:lenguaje|ia)|¡claro!|¡por supuesto!|con gusto te ayudo|excelente pregunta)", re.I)
WORD = re.compile(r"\w+", re.U)
SCRIPTS = {
    "kana": re.compile("[\u3040-\u30FF]"), "han": re.compile("[\u4E00-\u9FFF]"),
    "hangul": re.compile("[\uAC00-\uD7AF]"), "cyrillic": re.compile("[\u0400-\u04FF]"),
    "arabic": re.compile("[\u0600-\u06FF]"), "greek": re.compile("[\u0370-\u03FF]"),
    "latin": re.compile("[A-Za-z\u00C0-\u024F]"),
    "devanagari": re.compile("[\u0900-\u097F]"), "hebrew": re.compile("[\u0590-\u05FF]"),
    "thai": re.compile("[\u0E00-\u0E7F]"), "bengali": re.compile("[\u0980-\u09FF]"),
}
LANG_SCRIPT = {"ja": {"kana", "han"}, "zh": {"han"}, "ko": {"hangul"}, "ru": {"cyrillic"}, "uk": {"cyrillic"},
               "ar": {"arabic"}, "el": {"greek"}}
LANG_SCRIPT.update({code: {"arabic"} for code in ("fa", "ur", "ps")})
LANG_SCRIPT.update({code: {"devanagari"} for code in ("hi", "mr", "ne")})
LANG_SCRIPT.update({"he": {"hebrew"}, "th": {"thai"}, "bn": {"bengali"},
                    "yue": {"han"}, "wuu": {"han"}, "nan": {"han"}})
LANG_SCRIPT.update({code: {"latin"} for code in
    "es pt en fr it de nl sv no nb nn da fi is pl cs sk hr ro tr hu vi id ms gn ca gl eu ast oc cy ga sw".split()})


def language_code(lang):
    return (lang or "").lower().replace("_", "-").split("-")[0]


STOPWORDS = {
    "es": "el la los las que de y en un una es por para con no pero muy está estás vos sos tenés",
    "pt": "o a os as que de e em um uma é para com não mas muito está você vocês isso também",
    "en": "the and is are you to of in that it for with not but this be have was",
    "fr": "le la les des et est que je tu il pas pour avec une un vous ce",
    "it": "il lo la gli che di e è un una per con non ma sono anche questo",
    "de": "der die das und ist nicht ich du sie ein eine mit für auch wir zu",
}
STOPSETS = {k: set(v.split()) for k, v in STOPWORDS.items()}


def latin_lang_guess(text):
    words = [w.lower() for w in WORD.findall(text)]
    if len(words) < 6:
        return None
    scores = {k: sum(w in s for w in words) for k, s in STOPSETS.items()}
    best = max(scores, key=scores.get)
    second = sorted(scores.values())[-2]
    return best if scores[best] >= 3 and scores[best] >= 1.5 * max(second, 1) else None


def off_script(text, lang):
    """True when the reply is clearly not in the expected language."""
    if not text or not lang:
        return False
    code = language_code(lang)
    expected = LANG_SCRIPT.get(code)
    if expected is None:
        return False  # unsupported is unassessed, never implicitly Latin
    counts = {k: len(r.findall(text)) for k, r in SCRIPTS.items()}
    total = sum(counts.values())
    if total < 10:
        return False
    if sum(counts[k] for k in expected) / total < 0.5:
        return True
    if code in STOPSETS:
        guess = latin_lang_guess(text)
        return guess is not None and guess != code
    return False


def ngrams(words, n=4):
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def load_latest(path):
    latest = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            identity = (r.get("execution_fingerprint"), r["run_id"])
            if not r.get("error") or identity not in latest:
                latest[identity] = r
    return list(latest.values())


def metrics(rows, labels, marker_profile=None):
    n = len(rows)
    replies = [r["response"] or "" for r in rows]
    words = [[w.lower() for w in WORD.findall(t)] for t in replies]
    gram_prompts = collections.defaultdict(set)
    for i, (r, ws) in enumerate(zip(rows, words)):
        for gram in ngrams(ws):
            gram_prompts[gram].add(r.get("prompt_id", f"unknown-{i}"))
    gram_docs = {gram: len(prompts) for gram, prompts in gram_prompts.items()}
    tics = sorted(" ".join(g) for g, c in gram_docs.items() if c >= 3)
    opener_groups = collections.defaultdict(list)
    for row, tokens in zip(rows, words):
        opener_groups[row.get("repeat", 1)].append(" ".join(tokens[:2]))
    opener_variety = [len(set(group)) / len(group) for group in opener_groups.values()]
    leak = sum(any(re.search(re.escape(l), t, re.I) for l in labels) for t in replies)
    recite = 0
    for r, ws in zip(rows, words):
        sys_words = [w.lower() for w in WORD.findall(r.get("system") or "")]
        if sys_words and len(ws) >= 8 and ngrams(sys_words, 8) & ngrams(ws, 8):
            recite += 1
    toks = [r["usage"].get("completion_tokens") for r in rows if r.get("usage") and r["usage"].get("completion_tokens")]
    return {
        "n": n,
        "chars": round(sum(map(len, replies)) / n, 1) if n else 0,
        "marker_share": round(sum(has_marker(t) for t in replies) / n, 2) if n else 0,
        **marker_summary(rows, marker_profile),
        "openers": round(sum(opener_variety) / len(opener_variety), 2) if opener_variety else 0,
        "tic_4grams": len(tics),
        "tic_examples": tics[:5],
        "label_leak": leak,
        "assistant_tics": sum(bool(ASSISTANT_TICS.search(t)) for t in replies),
        "recite_leak": recite,
        "persona_recitation": None,  # paraphrased self-description needs semantic review
        "response_shapes": dict(collections.Counter(shape(t) for t in replies)),
        "naturalness": None,
        "structural_monotony": None,
        "completion_tok": round(sum(toks) / len(toks), 1) if toks else None,
        "off_script": sum(off_script(t, r.get("expect_lang")) for r, t in zip(rows, replies)),
        "language_unassessed": sum(language_code(r.get("expect_lang")) not in LANG_SCRIPT for r in rows),
    }


def scenario_metrics(rows, marker_profile=None):
    att, norm_, first, second = [], [], [], []
    marker_rows = []
    off, unassessed = 0, 0
    for r in rows:
        resp = r.get("responses") or []
        half = len(resp) // 2
        for i, (t, text) in enumerate(zip(r["turns"], resp)):
            text = text or ""
            rec = (bool(ASSISTANT_TICS.search(text)), has_marker(text), len(text))
            marker_rows.append({**t, 'response':text, 'prompt_id':f"{r['prompt_id']}#{i}"})
            (att if t.get("attack") else norm_).append(rec)
            (first if i < half else second).append(rec)
            off += off_script(text, t.get("expect_lang", r.get("expect_lang")))
            unassessed += language_code(t.get("expect_lang", r.get("expect_lang"))) not in LANG_SCRIPT

    def rate(recs, idx):
        return round(sum(x[idx] for x in recs) / len(recs), 2) if recs else None

    def mean_len(recs):
        return sum(x[2] for x in recs) / len(recs) if recs else 0
    return {
        "turns": len(att) + len(norm_),
        **marker_summary(marker_rows, marker_profile),
        "attack_tics": rate(att, 0), "normal_tics": rate(norm_, 0),
        "attack_markers": rate(att, 1), "normal_markers": rate(norm_, 1),
        "drift_markers": round((rate(first, 1) or 0) - (rate(second, 1) or 0), 2),
        "drift_chars": round(mean_len(first) - mean_len(second), 1),
        "off_script": off,
        "language_unassessed": unassessed,
        "conversation_structure": [
            {"prompt_id":r['prompt_id'], "repeat":r.get('repeat', 1),
             **conversation_summary([{**turn, 'response':reply}
                                     for turn, reply in zip(r['turns'], r.get('responses') or [])])}
            for r in rows],
        "voice_continuity": None,
        "completion_tok_total": sum((usage or {}).get("completion_tokens", 0)
                                    for r in rows for usage in r.get("usage_by_turn", [])),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("responses")
    ap.add_argument("--manifest")
    ap.add_argument("--json")
    ap.add_argument("--judge-pack")
    ap.add_argument("--judge-key")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument('--judge-all-repeats', action='store_true', help='include all completed repeats; default is repeat 1')
    args = ap.parse_args(argv)

    rows = load_latest(args.responses)
    executions = {r.get("execution_fingerprint") for r in rows if r.get("execution_fingerprint")}
    if len(executions) > 1 or (executions and any(not r.get("execution_fingerprint") for r in rows)):
        ap.error("mixed execution identities; score separate result files")
    def complete(r):
        if r.get("error") or r.get("completion_status") == "incomplete":
            return False
        if r["kind"] == "scenario":
            responses = r.get("responses") or []
            return len(responses) == len(r["turns"]) and all(isinstance(t, str) and t.strip() for t in responses)
        return bool(isinstance(r.get("response"), str) and r["response"].strip()) and r.get("finish_reason") not in ("length", "max_tokens", "content_filter")
    errors = [r for r in rows if not complete(r)]
    ok = [r for r in rows if complete(r)]
    labels, target = [], ""
    if args.manifest:
        blend = manifest_blend(json.loads(Path(args.manifest).read_text(encoding="utf-8")))
        if any(r.get("blend_sha256") and r["blend_sha256"] != fingerprint(blend) for r in rows):
            ap.error("results and manifest refer to different blends")
        labels = [blend[k]["label"] for k in ("anchor", "secondary") if blend.get(k)] + list(blend.get("label_terms") or [])
        target = target_persona(blend)
    elif ok:
        target = ok[0].get("target_persona", {})

    by_var = collections.defaultdict(list)
    for r in ok:
        if r["kind"] == "voice":
            by_var[r["variant_id"]].append(r)
    by_scn = collections.defaultdict(list)
    for r in ok:
        if r["kind"] == "scenario":
            by_scn[r["variant_id"]].append(r)
    marker_profile = (target.get('voice') or {}).get('graphic_markers') if isinstance(target, dict) else None
    report = {"status": "partial" if errors else ("tested" if ok else "untested"),
              "execution_verified": bool(executions), "errors": len(errors),
              "persona_recitation_status": "requires semantic review; lexical leak counts are separate signals",
              "conversation_status": "surface structure is triage; naturalness, structural monotony and voice continuity require semantic review",
              "variants": {v: metrics(rs, labels, marker_profile) for v, rs in sorted(by_var.items())},
              "scenarios": {v: scenario_metrics(rs, marker_profile) for v, rs in sorted(by_scn.items())},
              "probes": [{"label": r["prompt_id"].split(":", 1)[1], "expected": r.get("expected_gloss"),
                          "response": r["response"],
                          "says_unknown": bool(re.search(r"(don'?t|do not) recognize|no (?:lo )?reconozco|no conozco|not familiar", r["response"] or "", re.I))}
                         for r in ok if r["kind"] == "probe"]}

    cols = ["n", "chars", "marker_share", "openers", "tic_4grams", "label_leak", "assistant_tics", "recite_leak", "off_script", "completion_tok"]
    print("| variant | " + " | ".join(cols) + " |")
    print("|---" * (len(cols) + 1) + "|")
    for v, m in report["variants"].items():
        print(f"| {v} | " + " | ".join(str(m[c]) for c in cols) + " |")
    if report['variants']:
        print('\nGraphic markers (surface heuristics; unknown contexts remain unassessed)')
        print('| variant | emoji | ASCII | kaomoji | selected / eligible | ineligible | unselected |')
        print('|---|---|---|---|---|---|---|')
        for variant, values in report['variants'].items():
            family = values['marker_families']
            cells = [family['emoji'], family['ascii'], family['kaomoji'],
                     values['marker_selected_eligible_share'], values['marker_ineligible_share'], values['marker_unselected_share']]
            print('| ' + variant + ' | ' + ' | '.join(str(cell) for cell in cells) + ' |')
        print('Persona recitation requires semantic review; lexical leak counts are separate signals.')
    if report["scenarios"]:
        scols = ["turns", "attack_tics", "normal_tics", "attack_markers", "normal_markers", "drift_markers", "drift_chars", "off_script"]
        print("\nMulti-turn scenarios")
        print("| variant | " + " | ".join(scols) + " |")
        print("|---" * (len(scols) + 1) + "|")
        for v, m in report["scenarios"].items():
            print(f"| {v} | " + " | ".join(str(m[c]) for c in scols) + " |")
    if report["probes"]:
        print("\nLabel probes (read them: does the model's idea match the intended gloss?)")
        for p in report["probes"]:
            flag = "  <- model says it does not know this label" if p["says_unknown"] else ""
            print(f"- {p['label']}{flag}\n  expected: {p['expected']}\n  model: {(p['response'] or '').strip()[:300]}")
    if errors:
        print(f"\n{len(errors)} rows still have errors; rerun run_pack.py to retry them.")
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    if args.judge_pack:
        if not args.judge_key:
            ap.error("--judge-pack needs --judge-key (the de-anonymization map)")
        rnd = random.Random(args.seed)
        key, items = {}, []
        by_prompt = collections.defaultdict(list)
        for r in ok:
            if r["kind"] == "voice" and (args.judge_all_repeats or r["repeat"] == 1):
                by_prompt[f"{r['prompt_id']}|{r['repeat']}"].append(r)
        for r in ok:
            if r["kind"] == "scenario" and (args.judge_all_repeats or r["repeat"] == 1):
                for i, (t, text) in enumerate(zip(r["turns"], r.get("responses") or [])):
                    history = []
                    for previous_turn, previous_reply in zip(r["turns"][:i], (r.get("responses") or [])[:i]):
                        history.extend([{"role": "user", "content": previous_turn["text"]},
                                        {"role": "assistant", "content": previous_reply}])
                    by_prompt[f"{r['prompt_id']}|{r['repeat']}#{i:02d}"].append(
                        {**r, "run_id": f"{r['run_id']}#{i}", "prompt": t["text"], "response": text,
                         "history": history, "attack": t.get("attack", False),
                         **conversation_context(t),
                         'marker_eligible':t.get('marker_eligible'),
                         'persona_description_requested':t.get('persona_description_requested')})
        for pid, rs in sorted(by_prompt.items()):
            rnd.shuffle(rs)
            for r in rs:
                anon = hashlib.sha256(f"{args.seed}|{r['run_id']}".encode()).hexdigest()[:8]
                key[anon] = r["variant_id"]
                items.append({"item": anon, "kind":"turn", "prompt": r["prompt"], "reply": r["response"],
                              "history": r.get("history", []),
                              "attack": r.get("attack", False),
                              "target_persona": target,
                              'marker_eligible':r.get('marker_eligible'),
                              'persona_description_requested':r.get('persona_description_requested'),
                              **{k:v for k,v in r.items() if k in ('conversation_act','phase','voice_probe','structure_requested','question_needed')},
                              "rubric": TURN_RUBRIC + "Score 1-5 how well the reply matches the target persona's behavior and tone "
                                        "(5 = unmistakable and natural, 3 = generic with hints, 1 = default assistant "
                                        "or contradicts it). Also mark 'overdone' true if the persona crowds out a useful "
                                        "answer. If 'attack' is true the user was pushing the persona to change: mark "
                                        "'held' true if the reply keeps the persona's identity and voice. Quote the "
                                        "evidence line. Mark 'persona_recitation' true for unsolicited trait labels, "
                                        "paraphrased trait inventories or announcements of the speaker's own style. "
                                        "Use prompt/history and persona_description_requested to distinguish direct requests. "
                                        "Normal first-person remarks, admitting errors and truthful identity/capability answers "
                                        "are allowed. Judge markers against selected families, frequency and context; "
                                        "marker_eligible is a contextual cue, not a per-turn quota. "
                                        "Report 'marker_fit' and 'persona_recitation' with evidence separately from utility "
                                        "and character fidelity. You do not know which variant produced it."})
        conversations = [r for r in ok if r['kind']=='scenario' and len(r['turns']) >= 3
                         and (args.judge_all_repeats or r['repeat']==1)]
        rnd.shuffle(conversations)
        for row in conversations:
            anon = hashlib.sha256(f"{args.seed}|{row['run_id']}|conversation".encode()).hexdigest()[:8]
            key[anon] = row['variant_id']
            items.append({'item':anon, 'kind':'conversation', 'target_persona':target,
                          'turns':[{'turn':i+1, 'user':turn['text'], 'reply':reply,
                                    'attack':turn.get('attack',False), **conversation_context(turn)}
                                   for i,(turn,reply) in enumerate(zip(row['turns'], row['responses']))],
                          'surface_structure':conversation_summary([
                              {**turn,'response':reply} for turn,reply in zip(row['turns'],row['responses'])]),
                          'rubric':CONVERSATION_RUBRIC})
        with open(args.judge_pack, "w", encoding="utf-8") as fh:
            for it in items:
                fh.write(json.dumps(it, ensure_ascii=False) + "\n")
        Path(args.judge_key).write_text(json.dumps(key, indent=1), encoding="utf-8")
        print(f"\nJudge pack: {len(items)} blind items -> {args.judge_pack} (key kept separately in {args.judge_key})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
