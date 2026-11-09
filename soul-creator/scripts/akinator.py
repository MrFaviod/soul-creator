#!/usr/bin/env python3
"""Akinator-style narrowing over anchor archetypes (references/catalog/anchors.json).

Keeps a small JSON state file, scores every anchor against the answers so far,
and proposes the next most discriminating question, a guess, or a shortlist.

  # start (tier: P personal, C close circle, T internal team, B public brand)
  akinator.py --state S.json --init --tier P [--prior deductive_detective=3]
  # record answers: feature=value[:weight]; value in -2..2, or 'skip'
  akinator.py --state S.json --answer energy=1 humor=2 bite=skip
  # the user rejected or confirmed a guess
  akinator.py --state S.json --reject tsundere
  akinator.py --state S.json --confirm kuudere
  # print status only
  akinator.py --state S.json [--lang es]

Output is JSON: action (ask | guess | shortlist | done), top candidates with
normalized similarity weights (not calibrated preference probabilities), and
the next questions in the requested language. The script is
an aid: the agent still phrases questions naturally and adds sample lines.
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_excluded, load_anchors, load_config  # noqa: E402

SIGMA = 1.0


def candidates(state, data, cfg):
    tier = state["tier"]
    out = []
    for a in data["anchors"]:
        if tier not in a["tiers"] or a["id"] in state["rejected"]:
            continue
        if find_excluded(" ".join([a["id"], a["label"], *a["aliases"]]), cfg):
            continue
        out.append(a)
    return out


def posterior(state, cands):
    scores = {}
    for a in cands:
        logp = math.log(state["priors"].get(a["id"], 1.0))
        for feat, (val, w) in state["answers"].items():
            d = a["features"][feat] - val
            logp -= w * d * d / (2 * SIGMA * SIGMA)
        scores[a["id"]] = logp
    if not scores:
        return {}
    m = max(scores.values())
    exp = {k: math.exp(v - m) for k, v in scores.items()}
    z = sum(exp.values())
    return {k: v / z for k, v in exp.items()}


def next_questions(state, data, cands, post, k):
    asked = set(state["answers"]) | set(state["skipped"])
    ranked = []
    for q in data["questions"]:
        if q["feature"] in asked:
            continue
        mean = sum(post[a["id"]] * a["features"][q["feature"]] for a in cands)
        var = sum(post[a["id"]] * (a["features"][q["feature"]] - mean) ** 2 for a in cands)
        ranked.append((var, q))
    ranked.sort(key=lambda t: -t[0])
    return [(v, q) for v, q in ranked[:k] if v > 0.05]


def status(state, data, cfg, lang):
    icfg = cfg["interview"]
    cands = candidates(state, data, cfg)
    post = posterior(state, cands)
    by_id = {a["id"]: a for a in cands}
    top = sorted(post.items(), key=lambda t: -t[1])[: icfg["top_k"]]
    n_asked = len(state["answers"]) + len(state["skipped"])
    qs = next_questions(state, data, cands, post, icfg["questions_per_round"])

    if state.get("confirmed"):
        action = "done"
    elif not cands:
        action = "shortlist"  # everything rejected: fall back to open description
    elif n_asked < icfg["min_questions_before_guess"] and qs:
        action = "ask"
    elif top and top[0][1] >= icfg["guess_threshold"]:
        action = "guess"
    elif not qs or n_asked >= icfg["max_questions"] or sum(p for _, p in top[:3]) >= icfg["shortlist_mass"]:
        action = "shortlist"
    else:
        action = "ask"

    def show(aid, p):
        a = by_id[aid]
        return {"id": aid, "label": a["label"], "p": round(p, 3), "recognition": a["recognition"],
                "gloss": a["gloss"], "catalog_hint": a["catalog_hint"]}

    def q_out(q):
        lg = lang if lang in q["text"] else "en"
        return {"feature": q["feature"], "text": q["text"][lg],
                "options": [{"label": o.get(lg, o["en"]), "value": o["value"]} for o in q["options"]]}

    return {
        "action": action,
        "tier": state["tier"],
        "asked": n_asked,
        "confirmed": state.get("confirmed"),
        "rejected": state["rejected"],
        "top": [show(i, p) for i, p in top],
        "next_questions": [q_out(q) for _, q in qs] if action == "ask" else [],
        "hint": {
            "ask": "Ask these in plain words, each option with a short in-voice sample line.",
            "guess": "Present top[0] as a guess with one sample line; ask yes / close / no.",
            "shortlist": "Show top 3 as sample replies to the same prompt; let the user pick 1-2 or describe.",
            "done": "Anchor confirmed: move to layers (voice, secondary, quirks, name).",
        }[action],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", required=True)
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--tier", choices=list("PCTB"))
    ap.add_argument("--prior", nargs="*", default=[], help="id=multiplier, e.g. from referents")
    ap.add_argument("--answer", nargs="+", action="append", default=[], help="feature=value[:weight]; flag may repeat")
    ap.add_argument("--reject", nargs="*", default=[])
    ap.add_argument("--confirm")
    ap.add_argument("--lang", default=None, help="persist language in state; initial default en")
    ap.add_argument("--config")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    data = load_anchors()
    feats = set(data["features"])
    sp = Path(args.state)
    if args.init:
        if not args.tier:
            ap.error("--init needs --tier")
        state = {"tier": args.tier, "answers": {}, "skipped": [], "rejected": [], "priors": {},
                 "confirmed": None, "lang": args.lang or "en"}
    else:
        if not sp.exists():
            ap.error(f"state not found: {sp}. Initialize first with --init --tier P|C|T|B")
        state = json.loads(sp.read_text(encoding="utf-8"))
        if args.lang:
            state["lang"] = args.lang
        state.setdefault("lang", "en")
    ids = {a["id"] for a in data["anchors"]}

    for p in args.prior:
        aid, mult = p.split("=")
        if aid not in ids:
            ap.error(f"unknown anchor {aid}")
        state["priors"][aid] = float(mult)
    for ans in (item for group in args.answer for item in group):
        if "=" not in ans:
            ap.error(f"invalid --answer {ans!r}; expected feature=value[:weight]")
        feat, raw = ans.split("=", 1)
        if feat not in feats:
            ap.error(f"unknown feature {feat}; one of {sorted(feats)}")
        if raw == "skip":
            state["skipped"].append(feat)
            continue
        val, _, w = raw.partition(":")
        state["answers"][feat] = [max(-2.0, min(2.0, float(val))), float(w) if w else 1.0]
    for r in args.reject:
        if r not in ids:
            ap.error(f"unknown anchor {r}")
        state["rejected"].append(r)
    if args.confirm:
        if args.confirm not in ids:
            ap.error(f"unknown anchor {args.confirm}")
        state["confirmed"] = args.confirm

    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(json.dumps(status(state, data, cfg, state["lang"]), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
