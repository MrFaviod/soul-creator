#!/usr/bin/env python3
"""Create A/B review input and a SEPARATE reveal map from soul_test results.json.

Run `skill-creator/scripts/review.py` on the exported `pairs.json` to create a
fully offline viewer. Do NOT load reveal-map.json until choices are locked.
"""
import argparse
import json
import random
from pathlib import Path


def prepare(data, left, right, seed):
    if "results" not in data or "prompt" not in data:
        raise ValueError("prepare_blind currently expects single-turn results.json")
    results = data["results"]
    key = lambda x: (x["model"], x["run"])
    one = {key(x): x for x in results if x["soul"] == left and x["ok"]}
    two = {key(x): x for x in results if x["soul"] == right and x["ok"]}
    rnd = random.Random(seed)
    pairs, mapping = [], {}
    for m, run in sorted(one.keys() & two.keys()):
        candidates = [(left, one[(m, run)]["content"]), (right, two[(m, run)]["content"])]
        rnd.shuffle(candidates)
        ident = f"p{len(pairs) + 1}"
        pairs.append({"id": ident, "prompt": data["prompt"], "a": candidates[0][1], "b": candidates[1][1]})
        mapping[ident] = {"A": candidates[0][0], "B": candidates[1][0], "model": m, "run": run}
    if not pairs:
        raise ValueError("no complete pairs; failures must be addressed before blind review")
    return {"pairs": pairs}, {"mapping": mapping, "note": "Only reveal after recording blind ratings."}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results")
    ap.add_argument("--left", required=True)
    ap.add_argument("--right", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default="blind-review")
    args = ap.parse_args()
    data = json.loads(Path(args.results).read_text(encoding="utf-8"))
    try:
        review, mapping = prepare(data, args.left, args.right, args.seed)
    except ValueError as e:
        ap.error(str(e))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "pairs.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "reveal-map.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(review['pairs'])} blind pairs created; do not open reveal-map.json before human rating")


if __name__ == "__main__":
    main()
