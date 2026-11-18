# PaperOrchestra 拆解 → Claude Code Skill

來源：<https://github.com/google-research/paper-orchestra>（Google Cloud AI Research，Apache-2.0，論文 arXiv:2604.05018）

## 一、原專案在做什麼

輸入「寫作前的原始材料」——`idea.md`（方法想法）＋ `experimental_log.md`（實驗紀錄）——輸出一篇符合會議模板、雙盲匿名、可直接投稿的 LaTeX 論文（含真實文獻回顧與自動生成的圖表）。

## 二、原始碼結構拆解

| 路徑 | 角色 |
|---|---|
| `paper_writing_cli.py/.sh` | CLI 入口（`--raw_materials_dir --latex_template_dir --use_plotting`） |
| `methods/paper_writer_with_plotting.py` | **總指揮**：依序呼叫 5 個 agent，失敗最多重試 3 次 |
| `methods/agents/outline_agent.py` + `prompts/outline_agent.py` | ① 大綱 agent：產出 `plotting_plan` / `intro_related_work_plan` / `section_plan` 三段 JSON |
| `methods/agents/literature_review_agent.py` | ② 文獻 agent：Gemini + Google Search 找候選 → Semantic Scholar 驗證（模糊比對 > 70、要有摘要、早於 cutoff）→ 產生 BibTeX / citation_map → 寫 Intro + Related Work（須引用 ≥ 90%） |
| `methods/agents/plotting_agent.py` + `utils/paper_banana_utils.py` | ③ 繪圖 agent（PaperBanana）：Retriever → Planner → Stylist → Visualizer（matplotlib 或影像模型）→ Critic ×3 → Caption；與 ② **平行** |
| `methods/agents/section_writing_agent.py` | ④ 章節 agent：補完 Abstract / Method / Experiments / Conclusion，表格數字只能取自 log |
| `methods/agents/content_refinement_agent.py` | ⑤ 修訂 agent：編譯 → AgentReview 審稿 → 依審稿修訂 → 再審；以分數決定接受或回退（最多 3 輪），另有 VLM 版面檢查 |
| `autoraters/agent_review.py` | 審稿人 persona（knowledgeable/responsible/benign）、3 份審稿 + meta-review + 分數平均 |
| `autoraters/*` 其他 | 研究評估：citation F1、文獻回顧品質、side-by-side 比較 |
| `utils/prompt_utils.py` | `UNIVERSAL_NO_LEAKAGE_PROMPT`：知識隔離 + 匿名，附加在所有寫作 prompt 後 |
| `templates/cvpr2025`, `templates/iclr2025` | `template.tex`（以 `%%%%` 標記各節）+ `guidelines.md`（頁數/匿名/格式規則）+ 樣式檔 |
| `frontend/` | Streamlit demo 與範例輸入（TSAM, CVPR 2025） |

### 資料流

```
idea.md + experimental_log.md + template.tex + guidelines.md
        │
        ▼
 ① Outline ──► outline.json
        │
        ├──────────────► ② Literature ──► citation_map.json, references.bib, template.tex(Intro+RW), outline(+citation_candidates)
        └──────────────► ③ Plotting  ──► figures/*.png + info.json(captions)
                                 │
                                 ▼
                      ④ Section Writing ──► paper.tex (完整初稿)
                                 │
                                 ▼
                      ⑤ Refinement loop:  compile → review → revise → compile → review → gate(accept/revert) ×≤3
                                 │
                                 ▼
                           final_paper.pdf
```

### 關鍵設計決策（skill 完整保留）

1. **知識隔離**：只准用提供的材料寫，不得重建既有論文、不得寫作者資訊。
2. **兩段式文獻檢索**：LLM 搜尋只負責「發現」，學術資料庫負責「驗證」；沒驗證過的論文不能被引用 → 消除幻覺引用。
3. **引用分層**：Intro = 宏觀（10–20 篇，基礎、綜述）；Related Work = 微觀（30–50 篇，2–4 個方法群組，每組有「限制假說」與「我們如何解決」的橋接）。
4. **必引窮舉**：每個 dataset / optimizer / metric / backbone / baseline 都要有 citation hint；不知道作者時用通用格式，不准猜。
5. **時間線與 SOTA 規則**：cutoff 後的論文只能是同期工作；只有 log 中比較過的方法才能宣稱勝過。
6. **以修訂代替反駁**：審稿問題直接改進論文，不寫回覆信；log 沒有的實驗一律忽略。
7. **分數把關**：Overall ↑ 接受；↓ 回退停止；持平時比較子軸增益與損失。

## 三、轉成 Skill 的對應

| 原版 | Skill 版 |
|---|---|
| Gemini API 呼叫各 agent | Claude 依 `references/0X-*.md` 中**逐字保留**的系統提示詞扮演各 agent |
| `ThreadPoolExecutor` 平行 ②③ | Agent tool 在同一則訊息啟動兩個 subagent |
| Gemini + Google Search 發現文獻 | WebSearch |
| `s2_title_search`（thefuzz） | `scripts/verify_citations.py`（difflib，S2 失敗退 OpenAlex，含離線快取） |
| `_collect_search_tasks` / `_inject_citations_into_outline` | `scripts/collect_search_tasks.py` / `scripts/inject_citations.py` |
| Pydantic schema | `scripts/validate_outline.py` |
| 影像模型畫 diagram | TikZ / Graphviz / matplotlib，或沿用使用者提供的圖 |
| PaperBanana 參考圖庫 + NeurIPS style guide（未隨 repo 釋出） | 跳過 retrieval；`03-plotting-agent.md` 內自訂風格指引 |
| VLM 看 PDF 截圖 | `pdftoppm` 轉 PNG 後由 Claude Read 圖片檢查 |
| `compile_latex` | `scripts/compile.sh`（latexmk → pdflatex+bibtex → tectonic） |
| 分數比較邏輯 | `scripts/refine_gate.py` |
| 自己審自己 | Reviewer 用**獨立 subagent**，看不到寫作 context |
| 無 | `scripts/check_paper.py`：未知 cite key、環境不配對、Conclusion 後的圖表、去匿名字串、表格數字對 log |

## 四、使用方式

在這個 repo 開 Claude Code，直接說：

> 用 paper-orchestra 幫我把 `my_paper/raw_materials/` 寫成 CVPR 論文，cutoff 2025-06

或 `/paper-orchestra`。想先試跑，可用內建範例 `examples/tsam_cvpr/raw_materials/`。

需要的環境：Python 3（腳本只用標準函式庫）、TeX Live 或 tectonic（編譯用）、matplotlib（畫圖用）、可連 `api.semanticscholar.org` 或 `api.openalex.org`（文獻驗證）。選用 `SEMANTIC_SCHOLAR_API_KEY`。

## 五、限制與提醒

- 產出是**草稿**：數字、引用、論述都要作者逐一確認；並依投稿會議規範揭露 AI 輔助寫作。
- 原提示詞要求「不明說限制」；若會議需要 Limitations 段落，以會議規定為準。
- 原專案的資料集（benchmark）尚未釋出，因此原論文中的評估數據無法在此重現。
