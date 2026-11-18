#!/usr/bin/env python3
"""Static checks on a PaperOrchestra LaTeX draft.

Usage: python3 check_paper.py paper.tex citation_map.json [figures/info.json] [--log experimental_log.md]

ERRORs (must fix): unknown \\cite keys, mismatched figure/table environments, 'cleverref' typo,
figures/tables placed after the Conclusion (outside an appendix), missing \\includegraphics files,
de-anonymizing strings.
WARNINGs: citation coverage < 90% of the library, unused provided figures, numbers in tables
that do not appear in the experimental log.
"""
import argparse
import json
import os
import re
import sys


def strip_comments(tex):
    return re.sub(r"(?<!\\)%.*", "", tex)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tex")
    ap.add_argument("citation_map")
    ap.add_argument("figures_info", nargs="?")
    ap.add_argument("--log", help="experimental_log.md for number cross-checking")
    a = ap.parse_args()

    raw = open(a.tex, encoding="utf-8").read()
    tex = strip_comments(raw)
    cmap = json.load(open(a.citation_map, encoding="utf-8"))
    errors, warnings = [], []

    cited = set()
    for m in re.finditer(r"\\cite[tp]?\*?(?:\[[^\]]*\])*\{([^}]*)\}", tex):
        cited.update(k.strip() for k in m.group(1).split(",") if k.strip())
    unknown = sorted(cited - set(cmap))
    if unknown:
        errors.append(f"unknown cite keys (not in citation_map): {unknown}")
    if cmap:
        cov = len(cited & set(cmap)) / len(cmap)
        msg = f"citation coverage {len(cited & set(cmap))}/{len(cmap)} = {cov:.0%}"
        (warnings if cov < 0.9 else []).append(msg + " (< 90%)")
        print(msg)

    for env in ("figure", "figure*", "table", "table*"):
        e = re.escape(env)
        b = len(re.findall(r"\\begin\{" + e + r"\}", tex))
        en = len(re.findall(r"\\end\{" + e + r"\}", tex))
        if b != en:
            errors.append(f"\\begin{{{env}}} x{b} vs \\end{{{env}}} x{en}")
    for m in re.finditer(r"\\begin\{(figure\*?|table\*?)\}(.*?)\\end\{(figure\*?|table\*?)\}", tex, re.S):
        if m.group(1) != m.group(3):
            errors.append(f"\\begin{{{m.group(1)}}} closed by \\end{{{m.group(3)}}}")

    if "cleverref" in tex:
        errors.append("'cleverref' typo — the package is 'cleveref'")

    concl = re.search(r"\\section\*?\{[^}]*Conclusion[^}]*\}", tex, re.I)
    appendix = re.search(r"\\appendix\b", tex)
    if concl:
        tail = tex[concl.end(): appendix.start() if appendix else len(tex)]
        if re.search(r"\\begin\{(figure|table)\*?\}", tail):
            errors.append("figure/table environment appears after the Conclusion (outside the appendix)")
    bib = re.search(r"\\bibliography\{", tex)
    if appendix and bib and appendix.start() < bib.start():
        warnings.append("\\appendix appears before \\bibliography — appendix should follow References on a new page")

    tex_dir = os.path.dirname(os.path.abspath(a.tex))
    used = set()
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex):
        path = m.group(1)
        used.add(os.path.basename(path))
        if not os.path.exists(os.path.join(tex_dir, path)):
            errors.append(f"\\includegraphics file not found: {path}")
    if a.figures_info and os.path.exists(a.figures_info):
        info = json.load(open(a.figures_info, encoding="utf-8"))
        for f in info:
            if f["name"] not in used:
                warnings.append(f"provided figure not used: {f['name']}")
    for cap in re.findall(r"\\caption\{(Figure|Fig\.|Table)\s*\d", tex):
        warnings.append("caption text starts with a manual 'Figure/Table N' prefix")

    body = tex.split("\\begin{document}", 1)[-1]
    for pat in (r"[\w.+-]+@[\w-]+\.[\w.]+", r"corresponding author", r"github\.com/(?!anonymous)[\w-]+"):
        for m in re.finditer(pat, body, re.I):
            errors.append(f"possible de-anonymizing text: '{m.group(0)}'")

    if a.log and os.path.exists(a.log):
        log = open(a.log, encoding="utf-8").read()
        log_nums = set(re.findall(r"\d+(?:\.\d+)?", log))
        for t in re.finditer(r"\\begin\{tabular[x*]?\}(.*?)\\end\{tabular[x*]?\}", tex, re.S):
            for n in re.findall(r"(?<![\w.])\d+\.\d+(?![\w.])", t.group(1)):
                if n not in log_nums:
                    warnings.append(f"table number {n} not found verbatim in experimental log")

    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
