#!/usr/bin/env python3
"""Accept/revert decision for one content-refinement round (mirrors ContentRefinementAgent.run).

Usage: python3 refine_gate.py review_prev.json review_new.json [--worklog refinement/worklog.json]
                              [--round N] [--plan agent_worklog.json]
Prints one of: ACCEPTED_SCORE_INCREASE | ACCEPTED_NEUTRAL_IMPROVEMENT |
               REJECTED_SCORE_DECREASE | REJECTED_DEGRADATION
Exit code 0 = accept (continue), 1 = reject (revert to previous version and stop).
"""
import argparse
import json
import os
import sys

AXES = ["Originality", "Quality", "Clarity", "Significance", "Soundness",
        "Presentation", "Contribution", "Overall", "Confidence"]
EXCLUDED = {"Overall", "Confidence"}


def scores(review):
    out = {}
    for k in AXES:
        try:
            out[k] = float(review.get(k, 0))
        except (TypeError, ValueError):
            out[k] = 0.0
    return out


def decide(old, new):
    deltas = {k: new[k] - old[k] for k in AXES if k not in EXCLUDED}
    gain = sum(d for d in deltas.values() if d > 0)
    drop = sum(-d for d in deltas.values() if d < 0)
    if new["Overall"] > old["Overall"]:
        outcome = "ACCEPTED_SCORE_INCREASE"
    elif new["Overall"] < old["Overall"]:
        outcome = "REJECTED_SCORE_DECREASE"
    elif drop > gain:
        outcome = "REJECTED_DEGRADATION"
    else:
        outcome = "ACCEPTED_NEUTRAL_IMPROVEMENT"
    return outcome, deltas, gain, drop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prev")
    ap.add_argument("new")
    ap.add_argument("--worklog")
    ap.add_argument("--round", type=int)
    ap.add_argument("--plan", help="the refiner's JSON worklog for this round")
    a = ap.parse_args()
    old = scores(json.load(open(a.prev, encoding="utf-8")))
    new = scores(json.load(open(a.new, encoding="utf-8")))
    outcome, deltas, gain, drop = decide(old, new)
    print(f"Overall: {old['Overall']} -> {new['Overall']} | sub-axes gain +{gain} drop -{drop}")
    print(f"deltas: {deltas}")
    print(outcome)
    if a.worklog:
        log = {}
        if os.path.exists(a.worklog):
            log = json.load(open(a.worklog, encoding="utf-8"))
        r = a.round or len(log) + 1
        log[f"v{r}"] = {
            "round": r,
            "agent_plan": json.load(open(a.plan, encoding="utf-8")) if a.plan else None,
            "scores_before": old, "scores_after": new, "deltas": deltas,
            "total_gain": gain, "total_drop": drop, "outcome": outcome,
        }
        with open(a.worklog, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=4, ensure_ascii=False)
    return 0 if outcome.startswith("ACCEPTED") else 1


if __name__ == "__main__":
    sys.exit(main())
