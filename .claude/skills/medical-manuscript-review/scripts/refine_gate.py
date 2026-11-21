#!/usr/bin/env python3
"""Decide whether a revision round is kept or rolled back.

    python refine_gate.py review_v0.json review_v1.json --round 1 \
        --worklog refinement/worklog.json

Exit 0 = ACCEPT the round and continue. Exit 1 = REVERT it and stop.

This is the gate from PaperOrchestra (Song et al., 2026), applied to a clinical
manuscript: a revision is kept only when an independent re-review says it got
better. Without it a revision loop drifts — each round sounds more polished to
whoever wrote it while the reviewers' actual objections go unanswered, and
nothing ever says stop.

The rule:

  overall rises            -> ACCEPT, continue
  overall falls            -> REVERT, stop
  overall unchanged        -> ACCEPT and continue if the per-axis gains are at
                              least the losses, else REVERT and stop

`overall` is the panel's recommendation, which is what an editor acts on:
Reject 1, Major revision 2, Minor revision 3, Accept 4, averaged over the
reviewers. The axes are their 1-5 scores. A round that leaves the
recommendation where it was can still be worth keeping if the axes moved
forward on balance — that is the tie-break, not a second chance.

Review JSON (one per round; write `round` 0 for the first review):

{
  "round": 1,
  "reviewers": [
    {"id": "1", "role": "Clinical content expert",
     "recommendation": "Major revision",
     "scores": {"originality": 4, "rigour": 2, "importance": 3,
                "clarity": 2, "fit": 3}}
  ]
}
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REC_SCALE = {
    "reject": 1.0, "reject and resubmit": 1.5, "major revision": 2.0,
    "minor revision": 3.0, "accept": 4.0,
}
AXES = ["originality", "rigour", "importance", "clarity", "fit"]
AXIS_ZH = {"originality": "原創性", "rigour": "嚴謹度", "importance": "重要性",
           "clarity": "表達清晰", "fit": "期刊適配"}
EPS = 1e-9


def rec_score(text):
    t = str(text or "").strip().lower().rstrip(".")
    for k in sorted(REC_SCALE, key=len, reverse=True):
        if t.startswith(k) or k in t:
            return REC_SCALE[k]
    return None


def summarise(path):
    d = json.loads(Path(path).read_text(encoding="utf8"))
    revs = d.get("reviewers") or []
    if not revs:
        sys.exit(f"{path}：沒有 reviewers，無法評分")
    recs, unknown = [], []
    for r in revs:
        s = rec_score(r.get("recommendation"))
        (recs.append(s) if s is not None
         else unknown.append(r.get("id", "?")))
    if not recs:
        sys.exit(f"{path}：沒有一個 reviewer 的 recommendation 看得懂")
    axes = {}
    for a in AXES:
        vals = [r["scores"][a] for r in revs
                if isinstance(r.get("scores"), dict) and a in r["scores"]]
        if vals:
            axes[a] = sum(vals) / len(vals)
    return {
        "path": str(path), "n": len(revs),
        "overall": sum(recs) / len(recs), "axes": axes,
        "unknown_rec": unknown,
        "recommendations": [r.get("recommendation") for r in revs],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("previous", type=Path)
    ap.add_argument("current", type=Path)
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--worklog", type=Path)
    ap.add_argument("--max-rounds", type=int, default=3)
    a = ap.parse_args()

    prev, cur = summarise(a.previous), summarise(a.current)
    d_overall = cur["overall"] - prev["overall"]

    shared = [x for x in AXES if x in prev["axes"] and x in cur["axes"]]
    deltas = {x: cur["axes"][x] - prev["axes"][x] for x in shared}
    gains = sum(v for v in deltas.values() if v > 0)
    losses = -sum(v for v in deltas.values() if v < 0)

    if d_overall > EPS:
        verdict, why = "ACCEPT", "整體建議上升"
    elif d_overall < -EPS:
        verdict, why = "REVERT", "整體建議下降"
    elif not shared:
        verdict, why = "REVERT", "整體建議持平，且沒有可比較的子軸"
    elif gains + EPS >= losses:
        verdict, why = "ACCEPT", f"整體建議持平，子軸淨增益 {gains - losses:+.2f}"
    else:
        verdict, why = "REVERT", f"整體建議持平，子軸淨損失 {losses - gains:.2f}"

    last_round = a.round >= a.max_rounds
    cont = verdict == "ACCEPT" and not last_round

    print(f"第 {a.round} 輪 — {verdict}：{why}")
    print(f"  整體建議  {prev['overall']:.2f} → {cur['overall']:.2f}  ({d_overall:+.2f})")
    print(f"            {' / '.join(str(r) for r in prev['recommendations'])}")
    print(f"         →  {' / '.join(str(r) for r in cur['recommendations'])}")
    if shared:
        print("  子軸")
        for x in shared:
            print(f"    {AXIS_ZH[x]:<6} {prev['axes'][x]:.2f} → {cur['axes'][x]:.2f}"
                  f"  ({deltas[x]:+.2f})")
    for s in (prev, cur):
        if s["unknown_rec"]:
            print(f"  ! {Path(s['path']).name}：reviewer "
                  f"{', '.join(map(str, s['unknown_rec']))} 的 recommendation 無法判讀，已略過")
    if verdict == "ACCEPT":
        print("  → 保留這一輪的修改，" + ("已達最大輪數，停止。" if last_round else "繼續下一輪。"))
    else:
        print("  → 回退這一輪的修改並停止。上一版才是要送出的版本。")

    # A panel of three 1-5 scorers resolves about a third of a point. Changes
    # smaller than that are inside the noise: the same reviewer re-reading an
    # unchanged section will often move an axis by a whole point. Say so rather
    # than let a tie-break read as evidence of improvement.
    n_rev = max(prev["n"], cur["n"])
    resolution = 1.0 / n_rev
    small = abs(d_overall) < EPS and max((abs(v) for v in deltas.values()), default=0) <= resolution + EPS
    if small:
        print(f"  ⚠ 這一輪的所有變化都在 ±{resolution:.2f} 以內，也就是 {n_rev} 位評分者中"
              f"一位移動一分的幅度。以 {n_rev} 位評分者的解析度，這等於「測不出差別」，"
              f"不是「有進步」。要分辨這麼小的差異，得每輪多跑幾組 reviewer 取平均。")

    if a.worklog:
        entry = {
            "round": a.round, "at": datetime.now(timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ"),
            "verdict": verdict, "reason": why, "continue": cont,
            "overall": {"before": round(prev["overall"], 3),
                        "after": round(cur["overall"], 3),
                        "delta": round(d_overall, 3)},
            "axes": {x: {"before": round(prev["axes"][x], 3),
                         "after": round(cur["axes"][x], 3),
                         "delta": round(deltas[x], 3)} for x in shared},
            "reviews": {"previous": prev["path"], "current": cur["path"]},
        }
        log = []
        if a.worklog.exists():
            try:
                log = json.loads(a.worklog.read_text(encoding="utf8"))
            except Exception:
                log = []
        log = [e for e in log if e.get("round") != a.round] + [entry]
        log.sort(key=lambda e: e.get("round", 0))
        a.worklog.parent.mkdir(parents=True, exist_ok=True)
        a.worklog.write_text(json.dumps(log, ensure_ascii=False, indent=2),
                             encoding="utf8")
        print(f"  紀錄 → {a.worklog}")

    return 0 if cont else 1


if __name__ == "__main__":
    sys.exit(main())
