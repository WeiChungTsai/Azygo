#!/usr/bin/env python3
"""Pull a manuscript's reference list into a structured worklist for verification.

    python extract_references.py WORKDIR/main.md [WORKDIR/supp.md] \
        --out WORKDIR/references.json

Reads the markdown `extract_manuscript.py` produced and emits one record per
reference — the raw string plus whatever first author, year, journal, volume,
first page and DOI can be parsed off it — together with which in-text citation
numbers actually appear. That is the input Stage B verifies one entry at a time
against PubMed.

Parsing is deliberately tolerant: every record keeps its `raw` string, and
fields that could not be parsed are left null rather than guessed. A wrong
guess here would be verified against the wrong paper, which is worse than a
blank. Whatever the parser could not read, the verifier reads itself.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# "12.<tab>Author A, Author B. Title. Journal 2018;71:688-697."
ENTRY = re.compile(r"^\[P\d+\]\s*(\d{1,3})[.)]\s*\t?\s*(.+)$")
DOI = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")
YEAR = re.compile(r"\b((?:19|20)\d{2})\b")
# "... Journal name 2018;71:688-697"  /  "... Journal name. 2018;71(4):284-7."
TAIL = re.compile(
    r"(?P<journal>[A-Z][^.;]{2,90}?)\.?\s*"
    r"(?P<year>(?:19|20)\d{2})\s*[;,]\s*"
    r"(?P<volume>\d+)?\s*(?:\(\d+\))?\s*[:]\s*(?P<page>[A-Za-z]?\d+)")


def strip_pid(line):
    return re.sub(r"^\[P\d+\]\s*", "", line)


def parse_entry(n, raw):
    rec = {"n": n, "raw": raw.strip(), "first_author": None, "year": None,
           "journal": None, "volume": None, "first_page": None, "doi": None,
           "title_guess": None, "parse_note": None}

    m = DOI.search(raw)
    if m:
        rec["doi"] = m.group(1).rstrip(".,;")

    # first author surname: the leading "Surname XY," / "Surname XY."
    m = re.match(r"\s*([A-ZÀ-Ý][A-Za-zÀ-ÿ'’\-]+)\s+[A-ZÀ-Ý]{1,3}\b", raw)
    if m:
        rec["first_author"] = m.group(1)

    m = TAIL.search(raw)
    if m:
        rec["journal"] = m.group("journal").strip(" .,")
        rec["year"] = int(m.group("year"))
        rec["volume"] = m.group("volume")
        rec["first_page"] = m.group("page")
    else:
        ys = YEAR.findall(raw)
        if ys:
            rec["year"] = int(ys[-1])
        rec["parse_note"] = "卷期頁碼解析不出來，需人工或由驗證步驟補"

    # title: between the author block's first "." and the journal, roughly
    parts = [p.strip() for p in re.split(r"(?<=[a-z0-9\)])\.\s+", raw) if p.strip()]
    if len(parts) >= 2:
        rec["title_guess"] = parts[1][:300]

    return rec


def collect(paths):
    refs, seen_section = [], False
    cited = set()
    for p in paths:
        text = Path(p).read_text(encoding="utf8")
        lines = text.split("\n")
        in_refs = False
        for line in lines:
            if re.match(r"^##\s", line):
                in_refs = bool(re.search(r"references?", line, re.I))
                seen_section = seen_section or in_refs
                continue
            if not in_refs:
                continue
            m = ENTRY.match(line)
            if m:
                refs.append(parse_entry(int(m.group(1)), m.group(2)))

        # in-text citation numbers, outside the reference list
        body = text.split("## References")[0] if "## References" in text else text
        body = strip_pid(body)
        for pat in (r"p\s*[=<>≤≥]\s*0?\.\d+", r"\bN\s*=\s*\d+", r"\b0\.\d+\b",
                    r"\b(?:19|20)\d{2}\b", r"\d+\s*[-–]\s*\d+\s*(?:Hz|dB|ms|mg)",
                    r"\b\d+\s*(?:Hz|dB|ms|min|mg|kg|µL|mL|µV|mV|days?|weeks?)\b",
                    r"Figures?\s+S?\d+[A-Za-z]?", r"Tables?\s+S?\d+"):
            body = re.sub(pat, " ", body, flags=re.I)
        for m in re.finditer(r"(?<=[A-Za-z\)\.,;])\s?(\d{1,3}(?:\s*[,\-–]\s*\d{1,3})*)(?=[\s.,;)]|$)", body):
            for part in m.group(1).split(","):
                part = part.strip()
                rng = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", part)
                if rng:
                    cited.update(range(int(rng.group(1)), int(rng.group(2)) + 1))
                elif part.isdigit():
                    cited.add(int(part))
    return refs, cited, seen_section


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sources", nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()

    refs, cited, found_section = collect(a.sources)
    if not found_section:
        sys.exit("這些檔案裡找不到 References 章節——確認擷取的 .md 路徑對不對")

    numbers = [r["n"] for r in refs]
    hi = max(numbers) if numbers else 0
    cited = {c for c in cited if 1 <= c <= hi}
    dupes = sorted({n for n in numbers if numbers.count(n) > 1})

    # the same work listed twice under different numbers
    def sig(r):
        return (r["first_author"] or "", r["year"] or 0, r["first_page"] or "")
    bysig = {}
    for r in refs:
        if any(sig(r)):
            bysig.setdefault(sig(r), []).append(r["n"])
    repeated = {f"{k[0]} {k[1]} p{k[2]}": v for k, v in bysig.items() if len(v) > 1}

    out = {
        "count": len(refs),
        "numbers": {"listed": sorted(set(numbers)), "highest": hi},
        "never_cited": sorted(set(numbers) - cited),
        "cited_but_not_listed": sorted(cited - set(numbers)),
        "duplicate_numbers": dupes,
        "possible_duplicate_works": repeated,
        "unparsed": [r["n"] for r in refs if r["parse_note"]],
        "references": refs,
        "status": "unverified — Stage B 逐筆查證後寫入 citation_map.json",
    }
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf8")

    print(f"{len(refs)} 筆文獻 → {a.out}")
    if out["never_cited"]:
        print(f"  列了但內文從未引用：{out['never_cited']}")
    if out["cited_but_not_listed"]:
        print(f"  內文引用但文獻表沒有：{out['cited_but_not_listed']}")
    if dupes:
        print(f"  編號重複：{dupes}")
    for k, v in repeated.items():
        print(f"  疑似同一篇重複收錄：{k} → refs {v}")
    if out["unparsed"]:
        print(f"  書目解析不完整（驗證時要自己讀 raw）：{out['unparsed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
