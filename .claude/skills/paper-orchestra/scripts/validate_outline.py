#!/usr/bin/env python3
"""Validate outline.json against the PaperOrchestra Outline Agent schema.

Usage: python3 validate_outline.py outline.json
Exit code 0 = OK (warnings may still be printed), 1 = errors found.
"""
import json
import re
import sys

ASPECT = {"1:1", "1:4", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
PLOT_TYPES = {"plot", "diagram"}
DATA_SOURCES = {"idea.md", "experimental_log.md", "both"}
AUTHOR_TITLE = re.compile(r"^.+\(.+\)$")
GENERIC_HINT = re.compile(r"research paper or technical report introducing '.+'", re.I)


def main(path):
    errors, warnings = [], []
    with open(path, encoding="utf-8") as f:
        o = json.load(f)

    for key in ("plotting_plan", "intro_related_work_plan", "section_plan"):
        if key not in o:
            errors.append(f"missing top-level key '{key}'")

    seen_ids = set()
    for i, fig in enumerate(o.get("plotting_plan", [])):
        tag = f"plotting_plan[{i}]"
        fid = fig.get("figure_id", "")
        if not fid:
            errors.append(f"{tag}: missing figure_id")
        elif "figure" in fid.lower().replace("fig_", "", 1):
            errors.append(f"{tag}: figure_id '{fid}' must not contain the word 'Figure'")
        if fid in seen_ids:
            errors.append(f"{tag}: duplicate figure_id '{fid}'")
        seen_ids.add(fid)
        if fig.get("plot_type") not in PLOT_TYPES:
            errors.append(f"{tag}: plot_type must be one of {sorted(PLOT_TYPES)}")
        if fig.get("data_source") not in DATA_SOURCES:
            errors.append(f"{tag}: data_source must be one of {sorted(DATA_SOURCES)}")
        if fig.get("aspect_ratio") not in ASPECT:
            errors.append(f"{tag}: aspect_ratio '{fig.get('aspect_ratio')}' not allowed")
        for k in ("title", "objective"):
            if not fig.get(k):
                errors.append(f"{tag}: missing {k}")

    plan = o.get("intro_related_work_plan", {})
    intro = plan.get("introduction_strategy", {})
    for k in ("hook_hypothesis", "problem_gap_hypothesis", "search_directions"):
        if not intro.get(k):
            errors.append(f"introduction_strategy: missing {k}")
    n_dirs = len(intro.get("search_directions", []))
    if intro and not 3 <= n_dirs <= 5:
        warnings.append(f"introduction_strategy: {n_dirs} search_directions (spec: 3-5)")
    rw = plan.get("related_work_strategy", {})
    subs = rw.get("subsections", [])
    if not 2 <= len(subs) <= 4:
        warnings.append(f"related_work_strategy: {len(subs)} clusters (spec: 2-4)")
    for j, s in enumerate(subs):
        for k in ("subsection_title", "methodology_cluster", "sota_investigation_mission",
                  "limitation_hypothesis", "bridge_to_our_method"):
            if not s.get(k):
                errors.append(f"related_work_strategy.subsections[{j}]: missing {k}")
        if not s.get("limitation_search_queries"):
            warnings.append(f"related_work_strategy.subsections[{j}]: no limitation_search_queries "
                            "(falls back to title + cluster as the query)")

    n_hints = 0
    for i, sec in enumerate(o.get("section_plan", [])):
        stitle = sec.get("section_title", f"#{i}")
        subs = sec.get("subsections", [])
        # Orphan rule: a section that is divided must have at least two numbered subsections.
        numbered = [s for s in subs if re.match(r"^\d+\.\d+", s.get("subsection_title", ""))]
        if len(numbered) == 1:
            errors.append(f"section '{stitle}': orphaned subsection (X.1 without X.2)")
        for s in subs:
            if not s.get("content_bullets"):
                warnings.append(f"section '{stitle}' / '{s.get('subsection_title')}': no content_bullets")
            for h in s.get("citation_hints", []):
                n_hints += 1
                if not (AUTHOR_TITLE.match(h) or GENERIC_HINT.search(h)):
                    warnings.append(f"citation hint not in an allowed format: '{h}'")

    print(f"figures={len(o.get('plotting_plan', []))} related_work_clusters={len(rw.get('subsections', []))} "
          f"citation_hints={n_hints}")
    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
