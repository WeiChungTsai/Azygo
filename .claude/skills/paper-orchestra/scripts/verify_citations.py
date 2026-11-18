#!/usr/bin/env python3
"""Verify candidate papers against Semantic Scholar (fallback: OpenAlex) and build the citation library.

Mirrors PaperOrchestra's HybridLiteratureAgent Phase 1b + 2 (s2_title_search, _is_paper_allowed,
_generate_key, _generate_bibtex, _generate_citation_map). Standard library only.

Usage:
  python3 verify_citations.py literature/candidates.json --cutoff 2024-11 --out literature/
  python3 verify_citations.py candidates.json --cutoff 2024-11 --out lit/ --offline cache.json   # no network

candidates.json: [{"title": str, "year": int|null, "section": str, "reason": str, "search_type": str}, ...]

Outputs in --out: citation_map.json, references.bib, section_keys.json, rejected.json, s2_cache.json
Env: SEMANTIC_SCHOLAR_API_KEY (optional, raises rate limit).
"""
import argparse
import difflib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

S2_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_FIELDS = "title,year,authors,venue,abstract,citationCount,publicationDate,journal,externalIds"
OA_URL = "https://api.openalex.org/works"
MATCH_THRESHOLD = 70
ABSTRACT_MAX = 1500
STOPWORDS = {"the", "a", "an", "in", "on", "at", "for", "to", "of", "and", "is", "are", "with", "by", "study"}


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def ratio(a, b):
    return int(round(100 * difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()))


def http_json(url, headers=None, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-orchestra-skill/1.0", **(headers or {})})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise
    return None


def s2_search(title):
    headers = {}
    if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        headers["x-api-key"] = os.environ["SEMANTIC_SCHOLAR_API_KEY"]
    q = urllib.parse.urlencode({"query": title, "fields": S2_FIELDS, "limit": 5})
    data = http_json(f"{S2_URL}?{q}", headers)
    return (data or {}).get("data", []) or []


def openalex_search(title):
    q = urllib.parse.urlencode({"search": title, "per-page": 5})
    data = http_json(f"{OA_URL}?{q}")
    out = []
    for w in (data or {}).get("results", []):
        inv = w.get("abstract_inverted_index") or {}
        words = sorted(((p, wd) for wd, ps in inv.items() for p in ps))
        loc = (w.get("primary_location") or {}).get("source") or {}
        biblio = w.get("biblio") or {}
        pages = "--".join(x for x in (biblio.get("first_page"), biblio.get("last_page")) if x) or None
        is_journal = loc.get("type") == "journal"
        out.append({
            "title": w.get("title") or w.get("display_name") or "",
            "year": w.get("publication_year"),
            "publicationDate": w.get("publication_date"),
            "authors": [{"name": a["author"]["display_name"]} for a in w.get("authorships", []) if a.get("author")],
            "venue": loc.get("display_name") or "",
            "journal": {"name": loc.get("display_name"), "volume": biblio.get("volume"), "pages": pages}
            if is_journal else None,
            "abstract": " ".join(wd for _, wd in words),
            "citationCount": w.get("cited_by_count", 0),
        })
    return out


def best_match(query_title, year_hint, results):
    best, best_score = None, 0
    for r in results:
        if not r.get("title"):
            continue
        s = ratio(query_title, r["title"])
        if year_hint and r.get("year") and int(r["year"]) == int(year_hint):
            s += 10
        if s > best_score:
            best, best_score = r, s
    return (best, best_score) if best_score > MATCH_THRESHOLD else (None, best_score)


def allowed_by_cutoff(rec, cutoff):
    """True if the paper was published on/before the cutoff (YYYY-MM or YYYY-MM-DD)."""
    if not cutoff:
        return True
    c = [int(x) for x in cutoff.split("-")]
    c_y, c_m, c_d = c[0], (c[1] if len(c) > 1 else 12), (c[2] if len(c) > 2 else 31)
    p = None
    if rec.get("publicationDate"):
        try:
            p = [int(x) for x in str(rec["publicationDate"]).split("-")]
        except ValueError:
            p = None
    if not p and rec.get("year"):
        p = [int(rec["year"])]
    if not p:
        return True
    for pv, cv in zip(p, (c_y, c_m, c_d)):
        if pv != cv:
            return pv < cv
    return True


def make_key(authors, year, title):
    first = authors[0]["name"].split()[-1] if authors else "Unknown"
    first = re.sub(r"[^a-zA-Z]", "", first).capitalize() or "Unknown"
    words = re.sub(r"[^a-zA-Z0-9\s]", "", title.lower()).split()
    meaningful = [w.capitalize() for w in words if w not in STOPWORDS]
    return f"{first}{year or 'nd'}{''.join(meaningful[:2]) or 'Paper'}"


def bib_escape(s):
    return (s or "").replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")


def to_bibtex(p):
    authors = " and ".join(p["authors"]) or "Unknown"
    if p.get("journal"):
        lines = [f"@article{{{p['citation_key']},", f"  title={{{{{bib_escape(p['title'])}}}}},",
                 f"  author={{{bib_escape(authors)}}},", f"  journal={{{bib_escape(p['journal'])}}},"]
    else:
        lines = [f"@inproceedings{{{p['citation_key']},", f"  title={{{{{bib_escape(p['title'])}}}}},",
                 f"  author={{{bib_escape(authors)}}},", f"  booktitle={{{bib_escape(p['venue'] or 'arXiv')}}},"]
    lines.append(f"  year={{{p['year']}}}")
    if p.get("volume"):
        lines[-1] += ","
        lines.append(f"  volume={{{p['volume']}}}")
    if p.get("pages"):
        lines[-1] += ","
        lines.append(f"  pages={{{p['pages']}}}")
    return "\n".join(lines) + "\n}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidates")
    ap.add_argument("--cutoff", required=True, help="YYYY-MM")
    ap.add_argument("--out", required=True)
    ap.add_argument("--offline", help="JSON cache {title: [records]} to use instead of the network")
    ap.add_argument("--sleep", type=float, default=None, help="seconds between queries (default 1.0, 0.2 with API key)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sleep = a.sleep if a.sleep is not None else (0.2 if os.environ.get("SEMANTIC_SCHOLAR_API_KEY") else 1.0)

    with open(a.candidates, encoding="utf-8") as f:
        cands = json.load(f)
    cache_path = os.path.join(a.out, "s2_cache.json")
    cache = {}
    if a.offline:
        with open(a.offline, encoding="utf-8") as f:
            cache = json.load(f)
    elif os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)

    registry, rejected = {}, []
    network_failures = 0
    for c in cands:
        title = (c.get("title") or "").strip()
        if not title:
            continue
        if norm_title(title) in registry:
            continue
        results = cache.get(title)
        source = "cache"
        if results is None:
            if a.offline:
                rejected.append({**c, "why": "not in offline cache"})
                continue
            results, source = [], "s2"
            try:
                results = s2_search(title)
                time.sleep(sleep)
            except Exception as e:  # noqa: BLE001
                print(f"  S2 failed for '{title[:60]}': {e}", file=sys.stderr)
            if not best_match(title, c.get("year"), results)[0]:
                try:
                    results = results + openalex_search(title)
                    source = "s2+openalex"
                except Exception as e:  # noqa: BLE001
                    network_failures += 1
                    print(f"  OpenAlex failed for '{title[:60]}': {e}", file=sys.stderr)
            cache[title] = results
        rec, score = best_match(title, c.get("year"), results)
        if not rec:
            rejected.append({**c, "why": f"no match above {MATCH_THRESHOLD} (best={score}, via {source})"})
            continue
        if not allowed_by_cutoff(rec, a.cutoff):
            rejected.append({**c, "why": f"published after cutoff ({rec.get('publicationDate') or rec.get('year')})"})
            continue
        abstract = (rec.get("abstract") or "").strip()
        if not abstract:
            rejected.append({**c, "why": "no abstract available"})
            continue
        if len(abstract) > ABSTRACT_MAX:
            abstract = abstract[:ABSTRACT_MAX] + "... [Truncated]"
        nt = norm_title(rec["title"])
        if nt in registry:
            continue
        j = rec.get("journal") or {}
        registry[nt] = {
            "citation_key": make_key(rec.get("authors") or [], rec.get("year") or c.get("year"), rec["title"]),
            "title": rec["title"],
            "authors": [x["name"] for x in rec.get("authors") or []],
            "venue": rec.get("venue") or "arXiv",
            "year": rec.get("year") or c.get("year"),
            "abstract": abstract,
            "citation_count": rec.get("citationCount") or 0,
            "found_in_section": c.get("section", "Unknown"),
            "reason": c.get("reason", ""),
            "journal": j.get("name"),
            "volume": j.get("volume"),
            "pages": j.get("pages"),
            "publication_date": rec.get("publicationDate"),
        }
        print(f"  + {registry[nt]['citation_key']}: {rec['title'][:70]}", file=sys.stderr)

    if not a.offline:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

    # unique keys
    seen = set()
    for p in registry.values():
        base, key, suf = p["citation_key"], p["citation_key"], "a"
        while key in seen:
            key = base + suf
            suf = chr(ord(suf) + 1)
        p["citation_key"] = key
        seen.add(key)

    papers = list(registry.values())
    citation_map = {p["citation_key"]: {k: p[k] for k in ("citation_key", "title", "authors", "venue", "year", "abstract")}
                    for p in papers}
    section_keys = {}
    for p in papers:
        section_keys.setdefault(p["found_in_section"], []).append(p["citation_key"])

    def dump(name, obj):
        with open(os.path.join(a.out, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    dump("citation_map.json", citation_map)
    dump("section_keys.json", section_keys)
    dump("rejected.json", rejected)
    with open(os.path.join(a.out, "references.bib"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(to_bibtex(p) for p in papers) + "\n")

    why = {}
    for r in rejected:
        why[r["why"].split(" (")[0]] = why.get(r["why"].split(" (")[0], 0) + 1
    print(f"candidates={len(cands)} verified={len(papers)} rejected={len(rejected)} {why}")
    missing_targeted = [r["title"] for r in rejected if r.get("search_type") == "targeted"]
    if missing_targeted:
        print("REJECTED MUST-HAVE (targeted) candidates — consider re-searching:")
        for t in missing_targeted:
            print("  -", t)
    if network_failures and not papers:
        print("ERROR: scholarly APIs unreachable from this environment; nothing verified.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
