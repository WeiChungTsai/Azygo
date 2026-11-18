# Step 2a — Literature Review Agent（Hybrid：網路搜尋發現 + 學術資料庫驗證）

**職責**：依 outline 搜尋並**驗證**真實文獻，建立唯一可引用的文獻庫，並撰寫 Introduction 與 Related Work。

**輸入**：`outline.json`、idea、log、`latex/template.tex`、cutoff
**輸出**：`literature/citation_map.json`、`literature/references.bib`（同時複製到 `latex/`）、已填好 Intro/Related Work 的 `latex/template.tex`、注入 `citation_candidates` 的 `outline.json`

## Phase 1 — 收集搜尋任務

`python3 scripts/collect_search_tasks.py outline.json > literature/search_tasks.json`

任務來源（與原版 `_collect_search_tasks` 相同）：

| 來源 | section 標籤 | 類型 |
|---|---|---|
| `introduction_strategy.search_directions[]` | `Introduction` | exploration |
| `related_work_strategy.subsections[].limitation_search_queries[]`（若空則用 `subsection_title + methodology_cluster`） | `Related Work: <subsection_title>` | exploration |
| `section_plan[].subsections[].citation_hints[]` | `<section_title> - <subsection_title>` | targeted |

## Phase 1a — 發現候選（WebSearch）

對每個任務用 WebSearch（任務彼此獨立，可在同一則訊息平行發出多個搜尋；任務多時可分給 2–3 個 subagent）。依任務類型套用原版提示詞的要求：

**targeted（必引）**
```text
Identify the SPECIFIC academic paper described by this hint: "<focus>".
CONTEXT: <context>
CUTOFF DATE: Published BEFORE <cutoff>
1. Find the EXACT title and year of this paper.
2. If the hint refers to a dataset, model architecture, or baseline ("research paper introducing..."),
   you MUST find the primary, original paper that introduced it.
3. Return EXACTLY 1 candidate paper that matches best.
```

**exploration（探索）**
```text
Find 10-15 highly relevant, influential academic papers matching the search task.
Do not force results; only return strictly relevant papers.
SEARCH TASK: <focus>
CONTEXT FOR TASK: <context>
BROADER PROJECT PROBLEM: <outline.intro_related_work_plan.introduction_strategy.problem_gap_hypothesis>
CUTOFF DATE: Published BEFORE <cutoff>
1. Find REAL papers (arXiv, CVPR, NeurIPS, ICML, ICLR, ...).
2. Only return papers published in top-tier conferences or journals, or highly-cited works,
   or the exact state-of-the-art relevant to the task.
```

把所有候選寫成 `literature/candidates.json`：

```json
[
  {"title": "Attention Is All You Need", "year": 2017, "section": "Methodology - 3.1 Temporal-Aware Attention", "reason": "Transformer backbone", "search_type": "targeted"}
]
```

> 只記錄你在搜尋結果中**實際看到**的標題，不要憑記憶補論文。

## Phase 1b — 驗證與建庫（Semantic Scholar，失敗退 OpenAlex）

`python3 scripts/verify_citations.py literature/candidates.json --cutoff <YYYY-MM> --out literature/`

腳本行為（對應原版 `_enrich_and_register_paper` + `s2_title_search`）：
- 依標題查詢；以模糊比對分數（0–100，年份相符 +10）> 70 才算命中。
- 剔除：查無結果、**無摘要**、發表日期晚於 cutoff、正規化標題重複（先到先得，保留首個 section 標籤）。
- 摘要截斷 1500 字元。
- key 規則：`{第一作者姓(去非字母, 首字大寫)}{年}{標題前兩個非停用詞(首字大寫)}`，例如 `Vaswani2017AttentionAll`；重複則加 `a`, `b`…
- BibTeX：有 journal → `@article{journal=}`，否則 `@inproceedings{booktitle=venue 或 arXiv}`。
- 輸出 `citation_map.json`（key → title/authors/venue/year/abstract）、`references.bib`、`section_keys.json`（section 標籤 → keys）、`rejected.json`（被丟掉的與原因）。
- 設定 `SEMANTIC_SCHOLAR_API_KEY` 可提高速率限制；未設時每次查詢間隔 1 秒。

驗證完向使用者回報：候選數、通過數、被拒原因統計。被拒的**必引** hint（targeted）要列出來——可能要換關鍵字重搜一次。

## Phase 2 — 把引用注入大綱

`python3 scripts/inject_citations.py outline.json literature/section_keys.json`
→ `introduction_strategy.citation_candidates`、各 related-work 子節與 section_plan 子節的 `citation_candidates`；刪除 `citation_hints`。

## Phase 3 — 撰寫 Introduction 與 Related Work

準備 context：`template.tex`、`intro_related_work_plan`、`project_idea`、`project_experimental_log`、`citation_checklist`（全部 keys）、`collected_papers`（citation_map 內容）。
`{paper_count}` = citation_map 篇數；`{min_cite_paper_count}` = `int(0.9 * paper_count)`；`{cutoff_date}` = cutoff。

只改這兩節，其餘內容與 preamble 一字不動；寫完把 `literature/references.bib` 複製到 `latex/references.bib`。
然後 `python3 scripts/check_paper.py latex/template.tex literature/citation_map.json` 確認無未知 key、引用覆蓋率 ≥ 90%。

### 系統提示詞（原文）

~~~~text
Role: Senior AI Researcher.
Task: Write the introduction and related work section of a paper.

You will be given a 'template.tex', this is the initial skeleton we outlined for you. 
Your job is to fill in two sections: Introduction and Related Work. Leave all the other sections untouched.

INPUTS:
* 'intro_related_work_plan': This is your PRIMARY guide for structure and arguments.
* 'project_idea' and 'project_experimental_log': Use them to ensure the Intro accurately frames the technical contribution and results.
* 'citation_checklist': This includes the citation keys that you should use when citing relevant papers.
* 'collected_papers': These are all the relevant papers we collect for you for citation purpose.

YOU MUST ONLY CITE THE GIVEN 'collected_papers', DO NOT cite new papers other than the given papers.

CITATION REQUIREMENTS:
- You have access to the abstract of {paper_count} collected papers.
- You MUST cite at least {min_cite_paper_count} of them across the introduction and related work sections.
- Introduction: Cite key statistics, foundational models (CLIP, etc.), and broad problem statements.
- Related Work: Do deep comparative citations. Group distinct works (e.g., "Several methods [A, B, C]...").
- Ensure every \cite{key} corresponds exactly to a key in 'citation_checklist'.
- CRITICAL TIMELINE RULE: Do not treat any papers published after {cutoff_date} as prior baselines to beat. Treat them strictly as concurrent work.
- CRITICAL EVALUATION RULE: Do not claim our method beats or achieves State-of-the-Art over a specific cited paper UNLESS that paper is explicitly evaluated against in 'project_experimental_log'. Frame other recent papers strictly as concurrent, orthogonal, or conceptual work.
- You need to return the full code for the new 'template.tex', where the two empty sections (Introduction and Related Work) are now fille in, 
  while all the other code (packages, styles, and other sections) are identical to the original 'template.tex'.

IMPORTANT NOTE:
- DO NOT change '\usepackage[capitalize]{cleveref}' into '\usepackage[capitalize]{cleverref}', as there's no 'cleverref.sty'.

OUTPUT Format:
You must return the code for the updated 'template.tex', Make sure to wrap the code with ```latex content```.
~~~~
