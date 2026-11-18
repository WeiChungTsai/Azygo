---
name: paper-orchestra
description: Turn raw research materials (an idea/method note plus an experimental log, optionally figures) into a submission-ready, anonymized LaTeX conference paper using the PaperOrchestra multi-agent pipeline — Outline → (Literature Review ∥ Plotting) → Section Writing → Reviewer-gated Content Refinement. Use when the user wants to "write a paper from my experiment notes/logs", "draft a CVPR/ICLR/NeurIPS paper", "turn my idea and results into LaTeX", "auto-write intro and related work with real citations", or mentions PaperOrchestra. Not for editing an existing finished manuscript line-by-line, and not for non-empirical humanities writing.
---

# PaperOrchestra（論文交響樂團）— Claude 原生版

改寫自 Google Cloud AI Research 的 [google-research/paper-orchestra](https://github.com/google-research/paper-orchestra)
（Song et al., 2026, arXiv:2604.05018，Apache-2.0）。原版以 Gemini API + Python 驅動 5 個專職 agent；
本 skill 把每個 agent 的**角色、輸入輸出契約、提示詞與決策規則**拆解出來，由 Claude 自己（必要時配合 subagent）扮演，
不需要 Gemini / OpenAI 金鑰。

## 0. 何時使用 / 先確認什麼

開始前向使用者確認（已提供就不要再問）：

1. **原始材料**：`idea.md`（方法、貢獻、理論）與 `experimental_log.md`（所有數字、消融、設定）。格式見 `references/inputs.md`。若使用者只給零散筆記，先幫他整理成這兩份檔並請他確認——**實驗數字一律以使用者提供的為準，絕不補造**。
2. **目標會議模板**：內建 `templates/cvpr2025`、`templates/iclr2025`；其他會議依 `references/inputs.md` 的「自訂模板」規則建一個資料夾（`template.tex` + `guidelines.md` + 樣式檔）。
3. **研究截止日 `cutoff`**（YYYY-MM）：晚於此日期的論文只能當「同期工作」，不能當要打敗的 baseline。預設為今天的年月。
4. **是否產生圖表**（plotting，預設開）與是否已有現成圖（放在 `raw_materials/` 並附 caption）。

## 1. 工作區配置

```
<paper_dir>/
├── raw_materials/            # 使用者輸入（唯讀）
│   ├── idea.md
│   ├── experimental_log.md
│   └── *.png + figures.json  # 選用：現成圖與 caption
├── outline.json              # Step 1 產出；Step 2 會注入 citation_candidates
├── literature/
│   ├── candidates.json       # 搜尋得到的候選論文（未驗證）
│   ├── citation_map.json     # 驗證過的文獻庫（唯一可引用來源）
│   └── references.bib
├── latex/                    # 模板複本，最終稿在這
│   ├── template.tex  guidelines.md  references.bib  *.sty *.bst
│   ├── figures/  + figures/info.json
│   └── paper.tex
├── refinement/               # v0, v1, ... 草稿、審稿 JSON、worklog
└── final_paper.pdf / final_paper.tex
```

建立：`cp -r <skill_dir>/templates/<venue> <paper_dir>/latex`。

下文的 `scripts/`、`references/`、`templates/` 都指本 skill 目錄（此 SKILL.md 所在處）；其餘相對路徑都以 `<paper_dir>` 為準。腳本只用 Python 標準函式庫。

## 2. 管線總覽

| 步驟 | Agent | 輸入 | 輸出 | 詳細規格 |
|---|---|---|---|---|
| 1 | Outline Agent | idea, log, template.tex, guidelines | `outline.json`（plotting_plan / intro_related_work_plan / section_plan） | `references/01-outline-agent.md` |
| 2a | Literature Review Agent | outline, idea, log, template | `citation_map.json`、`references.bib`、寫好 Intro + Related Work 的 `template.tex`、注入候選引用的 outline | `references/02-literature-agent.md` |
| 2b | Plotting Agent（與 2a **平行**） | outline.plotting_plan, raw_materials | `latex/figures/*.png` + `info.json`（含 caption） | `references/03-plotting-agent.md` |
| 3 | Section Writing Agent | 以上全部 | `latex/paper.tex`（完整初稿） | `references/04-section-writing-agent.md` |
| 4 | Content Refinement Agent | 初稿 PDF/TeX、log、citation_map、guidelines | 經審稿分數把關的迭代修訂稿（最多 3 輪）+ 版面修正 | `references/05-refinement-agent.md` |
| 評分 | Reviewer（AgentReview persona） | 編譯後論文文字 | 結構化審稿 JSON（Overall 1–10 等） | `references/06-reviewer.md` |

執行方式：

- **Step 2a 與 2b 互相獨立**：用 Agent tool 在**同一則訊息**發出兩個 subagent（或自己依序做也可）。給 subagent 的 prompt 要附上對應 reference 檔的路徑、`paper_dir`、cutoff 與輸出路徑。
- 每一步都把產出寫到檔案再進下一步；下一步只讀檔案，不靠記憶。
- 每步結束用一行回報進度（例如「Outline 完成：4 張圖、3 個 related-work 群組、27 個 citation hints」）。

## 3. 全域硬性規則（覆蓋其他所有指示）

1. **知識隔離與匿名（Strict Knowledge Isolation）**：論文只能由本次提供的材料 + 由其推導的邏輯構成。不得憑訓練資料回想或重建任何已發表論文；不得推測或寫入作者姓名、單位、email、致謝、"corresponding author"。作者欄一律 `Anonymous Author(s)`。（原文提示詞見 `references/00-shared-rules.md`）
2. **數據真值**：所有數字（表格、內文、圖）必須逐字對應 `experimental_log.md`。log 沒有的實驗、baseline、延遲、成本——不寫、不承諾「未來會補」。
3. **引用封閉性**：`\cite{}` 只能用 `citation_map.json` 裡的 key。citation_map 只收錄**經學術資料庫驗證**（標題模糊比對 + 有摘要 + 早於 cutoff）的論文；網路搜尋得到但驗證不過的候選一律丟棄。絕不自行編 BibTeX。
4. **時間線**：cutoff 之後的論文只能當 concurrent / orthogonal work。
5. **SOTA 宣稱**：只有在 log 中真的比較過的方法，才能宣稱「優於」它。
6. **LaTeX 可編譯**：`\begin{figure*}` 對 `\end{figure*}`；不要把 `cleveref` 寫成 `cleverref`；保留 `\documentclass` 與 preamble；不亂加套件。
7. **圖表位置**：所有圖表出現在 Conclusion 之前（附錄除外）；附錄放在 References 之後的新頁。

## 4. 逐步執行

### Step 1 — Outline
讀 `references/01-outline-agent.md`，以其中的系統提示詞為角色，一次產出符合 schema 的 `outline.json`，再用
`python3 scripts/validate_outline.py <paper_dir>/outline.json` 檢查（列舉值、aspect_ratio、子節不可孤兒等）。不通過就修到通過。

### Step 2a — Literature Review（可交給 subagent）
依 `references/02-literature-agent.md`：
1. `python3 scripts/collect_search_tasks.py outline.json > literature/search_tasks.json`（Intro 探索、Related-work 限制查詢、section_plan 的必引 hints）。
2. 每個任務用 **WebSearch** 找候選（探索型 10–15 篇、目標型恰 1 篇；只收 cutoff 前、頂會/高引/確切 SOTA）。寫進 `literature/candidates.json`。
3. `python3 scripts/verify_citations.py literature/candidates.json --cutoff YYYY-MM --out literature/`
   → 用 Semantic Scholar（失敗時改 OpenAlex）驗證、去重、產生 key（`{第一作者姓}{年}{前兩個實詞}`）、`references.bib`、`citation_map.json`、`section_keys.json`。若此環境網路擋住學術 API，告訴使用者並請他在可連網處執行，**不要**改用未驗證的書目。
4. `python3 scripts/inject_citations.py outline.json literature/section_keys.json` → 把 `citation_candidates` 注入 outline、移除 `citation_hints`。
5. 以「Intro/Related Work 寫手」提示詞改寫 `latex/template.tex` 的這兩節，至少引用 citation_map 中 90% 的論文；複製 `references.bib` 到 `latex/`。

### Step 2b — Plotting（可交給 subagent，與 2a 平行）
依 `references/03-plotting-agent.md`，對 `plotting_plan` 每張圖：Planner（含所有數據點的詳細描述）→ Stylist（美化不改內容）→ Visualizer（plot 用 matplotlib 程式；diagram 用 TikZ/Graphviz/matplotlib 繪製，或沿用使用者提供的圖）→ Critic（最多 3 輪，回覆 `No changes needed.` 即停）→ Caption。產出 `latex/figures/<figure_id>.png` 與 `latex/figures/info.json`。

### Step 3 — Section Writing
依 `references/04-section-writing-agent.md`，填寫其餘所有章節（Abstract、Method、Experiments、Conclusion、選用 Appendix），保留已寫好的 Intro/Related Work，使用全部圖、booktabs 表格、log 中的確切數字。存成 `latex/paper.tex`。
接著跑 `python3 scripts/check_paper.py latex/paper.tex literature/citation_map.json latex/figures/info.json --log raw_materials/experimental_log.md`（未知 cite key、表格數字對不上 log、未使用的圖、figure 環境不匹配、Conclusion 後的圖表、cleverref 拼字）。

### Step 4 — Content Refinement（審稿把關迴圈）
依 `references/05-refinement-agent.md` 與 `references/06-reviewer.md`：
1. `bash scripts/compile.sh latex paper` 編譯 v0（無 TeX 環境時見該檔說明：改用 tectonic 或請使用者上傳 Overleaf；此時以 .tex 文字審稿）。
2. 以**獨立的 reviewer subagent**（看不到你的寫作推理，只拿到論文文字）產生 3 份審稿 → meta-review → 各分數取平均。
3. 依審稿修訂（只改呈現，不加新實驗）→ 編譯 → 再審 → `python3 scripts/refine_gate.py refinement/review_v{i-1}.json refinement/review_v{i}.json --worklog refinement/worklog.json --round {i}` 決定 ACCEPT（exit 0）/ REVERT（exit 1）：
   - Overall 上升 → 接受、繼續；Overall 下降 → 回退、停止；
   - Overall 持平 → 子軸（Originality…Contribution）總增益 ≥ 總損失則接受、繼續，否則回退、停止。
   最多 3 輪。
4. **版面檢查**：`pdftoppm -r 60 -png` 轉頁圖，自己看（Read 圖片）頁數上限、溢出邊界、表格重疊、孤立標題、空白頁，用 Format Agent 規則修到合規。
5. 輸出 `final_paper.tex`（+ `final_paper.pdf`），並在回覆中報告：頁數、引用數、圖表數、各輪分數與接受/回退紀錄、任何仍需使用者補的東西（例如 log 中缺少的設定）。

## 5. 選用：評估（autoraters）
原 repo 另有 citation F1、文獻回顧品質、side-by-side 論文比較等自動評分；若使用者要比較兩版稿件，見 `references/07-autoraters.md`。

## 6. 誠實回報
- 本 skill 產出的是**草稿**；要提醒使用者逐一核對數字、引用與論述，並遵守投稿會議對 AI 輔助寫作的揭露政策。
- 任何步驟被環境擋住（無 LaTeX、學術 API 被擋、無 matplotlib），照實說哪一步沒跑、替代做法是什麼。
