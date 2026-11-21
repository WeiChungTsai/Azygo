# 審閱與修改管線（A–G）

改寫自 [google-research/paper-orchestra](https://github.com/google-research/paper-orchestra)
（Song et al., 2026, Apache-2.0）。原版是「從實驗紀錄寫出一篇新論文」；這裡是
**審閱並修改一份既有的醫學稿件**，文獻來源換成 PubMed，檔案格式換成 docx 與 pptx。

保留的核心是**審稿把關迴圈**：修訂之後重新審稿、比分，分數沒進步就回退。沒有這個
閘門，修訂迴圈會自己飄走——每一輪在寫的人眼裡都更通順，但審稿人真正的異議沒被處理，
而且沒有任何東西會說「停」。

| 階段 | 做什麼 | 產出 | 閘門 |
|---|---|---|---|
| **A 稿件剖析** | 擷取 docx/pptx、渲染圖、建 profile、把主張對應到證據 | `work/`、`01_manuscript_profile.md` | 使用者確認 |
| **B 文獻** | PubMed 逐筆查證引用、找漏引的關鍵文獻 | `citation_map.json`、`02_literature.md` | 使用者確認 |
| **C 圖檔稽核** | 實際看圖，對照期刊規範 | `03_figure_audit.md` | — |
| **D 評析** | 一致性交叉檢查 + Major/Minor concerns | `04_appraisal.md` | — |
| **E 三位 reviewer** | 三個獨立 subagent + 主編綜合 + 結構化評分 | `review_v0.json`、`05_panel.md` | — |
| **F 修改** | 依 concerns 改 docx（追蹤修訂）+ 回覆草稿 | `manuscript_rN.docx`、`change_log.md` | — |
| **G 把關** | 重審 → 比分 → 接受或回退 | `review_vN.json`、`worklog.json` | 自動 |

A→B→C→D→E 是一次性的；**F→E'→G 是迴圈**，最多 3 輪。

---

## 全域硬性規則

優先於其他任何指示。

1. **不捏造。** 數字、統計、文獻、DOI、PMID、倫理編號一律不得編造。缺的就說缺。
2. **數據真值。** 稿件裡的每個數字以作者的原始檔為準。你看得到的只有稿件印出來的值，
   看不到原始資料——不要宣稱驗證過沒看到的東西。
3. **引用封閉性。** 只有進了 `citation_map.json`（經 PubMed 查證）的文獻才算確認。
   查不到的標 `[VERIFY]` 留在原處，**絕不自行補上卷期頁碼或 DOI**。
4. **修改不改科學內容。** 語言層級的修訂不得改動任何數字、單位、P 值、CI、樣本數、
   劑量、時間點，也不得改變結論的方向或強度。要改變主張強度時，那是一條 concern，
   要經作者同意，不是語言編修。
5. **作者保有否決權。** 每一處修訂都以追蹤修訂寫入，作者逐項接受或拒絕。語意不清的
   地方用 Word 註解提問，不要自己猜。
6. **稿件不外流。** 未發表稿件只留在本機工作目錄。不要上傳、不要寫進版控、不要送到
   任務不需要的外部服務。查一筆文獻的書目是必要的；把摘要貼到第三方網站不是。

---

## Stage A — 稿件剖析

```bash
python3 scripts/extract_manuscript.py <本文.docx> <supplementary.docx> <圖檔.pptx> --out work
```

讀 `work/INVENTORY.md`（它會自動標出 placeholder、空段落、從未引用的文獻），然後
**實際開啟 `work/*_slides/*.png` 看每一張圖**。多數圖表問題只有看圖才看得出來。

產出 manuscript profile（見 `SKILL.md`），讓使用者確認推定的研究類型與設計再往下走。

---

## Stage B — 文獻（PubMed）

```bash
python3 scripts/extract_references.py work/main.md work/supp.md --out work/references.json
```

腳本把文獻表拆成結構化清單，並標出：從未被引用的編號、內文引用但表上沒有的編號、
編號重複、書目解析不完整的筆數。解析不出來的欄位留空而不是亂猜——猜錯會導致查證到
錯誤的論文，比留空更糟。

接著**逐筆查證**。用 PubMed 的 MCP 工具：

- `mcp__PubMed__lookup_article_by_citation` — 一次最多帶幾筆 `{author, journal, year, volume, first_page}`，
  回傳 PMID。這是主要路徑，批次查最有效率。
- `mcp__PubMed__get_article_metadata` — 拿到 PMID 後取完整書目核對標題、作者、卷期頁。
- `mcp__PubMed__search_articles` — 書目殘缺時用標題或關鍵詞搜。
- `mcp__PubMed__find_related_articles` — 找作者可能漏引的關鍵文獻。

每一筆判定為：

| 判定 | 意思 | 處理 |
|---|---|---|
| `verified` | PMID 找到且書目相符 | 寫入 citation_map |
| `corrected` | 找到了但稿件書目有誤 | 寫入正確書目，列進修正清單 |
| `duplicate` | 與另一筆是同一個 PMID | 合併、重新編號 |
| `retracted` | 有撤稿或 expression of concern | **立刻告訴使用者**，不要只記在報告裡 |
| `unverified` | 查不到 | 標 `[VERIFY]`，保留作者原文 |
| `not_indexed` | 書籍、網頁、會議論文等 PubMed 不收錄 | 標明來源類型，不算錯誤 |

重複收錄的判定要等查證完成後用 **PMID** 比對，不要用解析出來的書目字串比——書目殘缺
的那筆（正是常出問題的那筆）字串比對不到。

`citation_map.json`：

```json
{
  "verified_at": "2026-11-21",
  "source": "PubMed (MCP connector)",
  "entries": [
    {"n": 3, "status": "duplicate", "pmid": "14665815",
     "duplicate_of": 33, "raw": "Chang T-Y, ... 20031289-1296",
     "correct": "Chang T-Y, Jain R-M, Wang C-S, Chan C-C. Effects of occupational noise exposure on blood pressure. J Occup Environ Med. 2003;45(1289):1289-1296.",
     "note": "與 ref 33 同一篇；原文卷期頁碼格式殘缺"}
  ],
  "never_cited": [27, 28, 29],
  "missing_literature": [
    {"pmid": "...", "why": "本研究技術的人體對應文獻，Discussion 未引用"}
  ]
}
```

同時產出 `02_literature.md`：逐筆判定表、要修正的書目、建議補引的文獻與理由。

**查不到不等於文獻不存在。** PubMed 不收錄書籍、多數會議論文與部分期刊。判 `unverified`
之前先確認那筆是不是本來就不該在 PubMed 裡。

---

## Stage C — 圖檔稽核

開 `work/*_slides/*.png` 逐張看，依 `references/journal-formatting.md` 的圖檔規則檢查：
panel 標示、字級、解析度、誤差線定義、n、統計標記、色盲友善、scale bar、影像完整性。

不要替作者重畫圖。報告問題，只修安全的文字層項目（圖說、panel 標籤）。

---

## Stage D — 評析

依 `references/critical-appraisal.md`。務必先做 `SKILL.md` 的一致性交叉檢查——跨圖列出
每組 n、重算能重算的統計、檢查時間窗口是否符合物種生理、硬體設定與分析設定是否相容。

---

## Stage E — 三位 reviewer

依 `references/reviewer-panel.md`。除了給人看的報告，**另外產出 `review_v0.json`**
供把關迴圈使用：

```json
{
  "round": 0,
  "reviewers": [
    {"id": "1", "role": "Clinical content expert",
     "recommendation": "Major revision",
     "scores": {"originality": 4, "rigour": 2, "importance": 3,
                "clarity": 2, "fit": 3},
     "major": ["..."], "minor": ["..."]}
  ]
}
```

`recommendation` 用 Accept / Minor revision / Major revision / Reject and resubmit / Reject。
`scores` 五軸各 1–5。

---

## Stage F — 修改

把 concerns 轉成一份 `edits.json`，交給腳本寫成追蹤修訂：

```bash
python3 scripts/revise_docx.py 本文.docx edits.json \
    --out manuscript_r1.docx --log change_log_r1.md
```

`edits.json`：

```json
{"author": "Claude (medical-manuscript-review)",
 "edits": [
   {"para": "P48", "find": "may partially explain the mortality",
    "new": "", "reason": "PVC 不是致死性心律不整的已驗證替代指標", "ref": "M8"},
   {"para": "P40", "find": "a direct index",
    "query": "SCNA 是間接替代指標，而在小鼠身上的驗證正是本文自己要做的事——確認要保留 direct 嗎？"}
 ]}
```

`para` 是 Stage A 擷取出的 `[P..]` 編號，`find` 是該段落裡要改的文字。`new` 留空代表
刪除；`query` 代表加一則 Word 註解而不改內容。腳本會把對不上的修訂列在紀錄裡，不會
默默跳過——默默跳過的修訂就是改到一半出門的稿件。

**哪些改、哪些不改。** 這一階段只做「不需要新資料就能做完」的修訂：用詞過度宣稱、
未經檢定的主張、文獻錯誤、圖號與編號、格式問題。需要新實驗或重新分析的 concern
**不要在稿件上動手**——寫進回覆草稿，標明作者必須自己決定。

**改一處就要找出所有說同一件事的地方。** 這是局部修訂最容易出的錯，而且會製造出
**原本不存在的矛盾**。把 Abstract 的主張改軟，卻留著 Discussion 裡原來的說法，稿件
就自相矛盾了——獨立重審的人第一眼就會抓到，而且那會比原本單純的過度宣稱更難看。

所以 edits.json 寫完之後，對每一條語意性的修訂做一次反向搜尋：改掉的那個主張，在
Abstract、Results、Discussion、Conclusions、圖說裡還有沒有別的說法？有就一併列進
同一份 edits.json。腳本幫不了這個忙，它只負責把你指定的文字換掉。

---

## Stage G — 把關

改完之後，用**全新的 reviewer subagent**（看不到你的修改理由，只拿到改後的稿件）重審，
產出 `review_v1.json`，然後：

```bash
python3 scripts/refine_gate.py review_v0.json review_v1.json \
    --round 1 --worklog refinement/worklog.json
```

- **exit 0 = ACCEPT** — 保留這一輪，可以進下一輪
- **exit 1 = REVERT** — 回退這一輪並停止；上一版才是要送出的版本

規則：整體建議上升就接受；下降就回退；持平時看五軸的淨增減。最多 3 輪。

回退的時候要**真的回退**——把 `manuscript_rN.docx` 擱置，回到 `manuscript_r(N-1).docx`，
並在回報裡說明哪一輪被回退、為什麼。把分數下降的那一版當成成果交出去，比不修改更糟。

重審必須是獨立的 subagent。拿自己改過的稿件自己重審，分數幾乎一定會上升，那個閘門
就沒有意義了。

---

## 回報

每一輪結束報告：目前輪數、各輪分數與接受／回退、哪些 concern 已處理、哪些還等作者
決定、哪些步驟被環境擋住。

最後提醒使用者：這是草稿，數字、引用與論述要逐一自己核對；並依目標期刊的規定揭露
AI 輔助。
