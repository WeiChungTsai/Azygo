#!/usr/bin/env python3
"""Turn outline.json into the literature search task list (mirrors HybridLiteratureAgent._collect_search_tasks).

Usage: python3 collect_search_tasks.py outline.json > literature/search_tasks.json
"""
import json
import sys


def collect(outline):
    tasks = []
    plan = outline.get("intro_related_work_plan", {})

    intro = plan.get("introduction_strategy", {})
    for direction in intro.get("search_directions", []):
        tasks.append({
            "section": "Introduction",
            "focus": direction,
            "context": f"Hook: {intro.get('hook_hypothesis', '')}. Gap: {intro.get('problem_gap_hypothesis', '')}",
            "search_type": "exploration",
        })

    for sub in plan.get("related_work_strategy", {}).get("subsections", []):
        queries = sub.get("limitation_search_queries") or [
            f"{sub.get('subsection_title', '')} {sub.get('methodology_cluster', '')}"
        ]
        for q in queries:
            tasks.append({
                "section": f"Related Work: {sub.get('subsection_title', 'General')}",
                "focus": q,
                "context": f"Mission: {sub.get('sota_investigation_mission', '')}. "
                           f"Hypothesis: {sub.get('limitation_hypothesis', '')}",
                "search_type": "exploration",
            })

    for section in outline.get("section_plan", []):
        stitle = section.get("section_title", "Unknown Section")
        for sub in section.get("subsections", []):
            sub_title = sub.get("subsection_title", "General")
            context = " ".join(sub.get("content_bullets", []))
            for hint in sub.get("citation_hints", []):
                tasks.append({
                    "section": f"{stitle} - {sub_title}",
                    "focus": hint,
                    "context": f"Must-have citation for section covering: {context}",
                    "search_type": "targeted",
                })

    # de-duplicate identical (section, focus) pairs
    seen, unique = set(), []
    for t in tasks:
        k = (t["section"], t["focus"])
        if k not in seen:
            seen.add(k)
            unique.append(t)
    return unique


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        tasks = collect(json.load(f))
    print(json.dumps(tasks, indent=2, ensure_ascii=False))
    n_t = sum(t["search_type"] == "targeted" for t in tasks)
    print(f"{len(tasks)} tasks ({n_t} targeted, {len(tasks) - n_t} exploration)", file=sys.stderr)
