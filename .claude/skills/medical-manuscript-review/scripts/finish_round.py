#!/usr/bin/env python3
"""Carry out what the gate decided: keep a revision round, or roll it back.

    python finish_round.py --round 1 --dir <paper_dir> --verdict ACCEPT|REVERT

A gate that only prints a verdict is easy to ignore. The round that scored
worse is the one most likely to be sitting in the folder with the newest
timestamp and the most confident-looking prose, so the rollback has to be a
step somebody actually takes. This moves the files and writes down what
happened, so that the version left in place is the one the reviewers scored
highest — not the one written last.

ACCEPT  the round's manuscript becomes `manuscript_current.docx`
REVERT  the round's files move to `reverted/round-N/` and
        `manuscript_current.docx` goes back to the previous round
"""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def round_files(d: Path, n: int):
    """Everything this round produced, by the pipeline's naming."""
    pats = [f"manuscript_r{n}.docx", f"change_log_r{n}.md", f"edits_r{n}.json",
            f"edits.json" if n == 1 else f"edits_r{n}.json",
            f"review_v{n}.json"]
    return [d / p for p in dict.fromkeys(pats) if (d / p).exists()]


def previous_manuscript(d: Path, n: int):
    for k in range(n - 1, 0, -1):
        p = d / f"manuscript_r{k}.docx"
        if p.exists():
            return p
    for name in ("manuscript_original.docx", "manuscript.docx"):
        if (d / name).exists():
            return d / name
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--verdict", required=True, choices=["ACCEPT", "REVERT"])
    ap.add_argument("--note", default="")
    a = ap.parse_args()

    d, n = a.dir, a.round
    cur = d / "manuscript_current.docx"
    this_round = d / f"manuscript_r{n}.docx"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    moved = []

    if a.verdict == "ACCEPT":
        if not this_round.exists():
            sys.exit(f"找不到 {this_round.name}")
        shutil.copyfile(this_round, cur)
        print(f"保留第 {n} 輪 → {cur.name}")
    else:
        dest = d / "reverted" / f"round-{n}"
        dest.mkdir(parents=True, exist_ok=True)
        for f in round_files(d, n):
            shutil.move(str(f), str(dest / f.name))
            moved.append(f.name)
        prev = previous_manuscript(d, n)
        if prev:
            shutil.copyfile(prev, cur)
            print(f"回退第 {n} 輪 → 移到 {dest.relative_to(d)}／，"
                  f"目前版本回到 {prev.name}")
        else:
            if cur.exists():
                cur.unlink()
            print(f"回退第 {n} 輪 → 移到 {dest.relative_to(d)}／；"
                  f"沒有更早的版本，請用原始稿件")
        if moved:
            print("  移走：" + "、".join(moved))

    rec = {"round": n, "at": stamp, "verdict": a.verdict,
           "moved": moved, "note": a.note,
           "current": cur.name if cur.exists() else None}
    log = d / "refinement" / "rounds.json"
    log.parent.mkdir(parents=True, exist_ok=True)
    hist = []
    if log.exists():
        try:
            hist = json.loads(log.read_text(encoding="utf8"))
        except Exception:
            hist = []
    hist = [h for h in hist if h.get("round") != n] + [rec]
    hist.sort(key=lambda h: h.get("round", 0))
    log.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf8")
    print(f"  紀錄 → {log.relative_to(d)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
