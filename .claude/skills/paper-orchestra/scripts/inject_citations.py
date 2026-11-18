#!/usr/bin/env python3
"""Inject verified citation keys into outline.json (mirrors _inject_citations_into_outline).

Usage: python3 inject_citations.py outline.json literature/section_keys.json [--out outline.json]
Writes in place unless --out is given. Removes `citation_hints` from section_plan subsections.
"""
import argparse
import json


def inject(outline, section_keys):
    plan = outline.get("intro_related_work_plan", {})
    intro = plan.get("introduction_strategy", {})
    intro["citation_candidates"] = sorted(set(section_keys.get("Introduction", [])))
    for sub in plan.get("related_work_strategy", {}).get("subsections", []):
        sub["citation_candidates"] = section_keys.get(
            f"Related Work: {sub.get('subsection_title', 'General')}", [])
    for section in outline.get("section_plan", []):
        stitle = section.get("section_title", "Unknown Section")
        for sub in section.get("subsections", []):
            key = f"{stitle} - {sub.get('subsection_title', 'General')}"
            sub["citation_candidates"] = section_keys.get(key, [])
            sub.pop("citation_hints", None)
    return outline


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("outline")
    ap.add_argument("section_keys")
    ap.add_argument("--out")
    a = ap.parse_args()
    with open(a.outline, encoding="utf-8") as f:
        outline = json.load(f)
    with open(a.section_keys, encoding="utf-8") as f:
        keys = json.load(f)
    outline = inject(outline, keys)
    with open(a.out or a.outline, "w", encoding="utf-8") as f:
        json.dump(outline, f, indent=4, ensure_ascii=False)
    print(f"injected {sum(len(v) for v in keys.values())} keys across {len(keys)} sections")
