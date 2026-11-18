# 輸入材料格式

原版只需要兩份 Markdown（`idea.md`、`experimental_log.md`），格式不限（"unconstrained pre-writing materials"）。
以下是建議結構——越完整，Outline 與寫作品質越好。範例見 `examples/tsam_cvpr/raw_materials/`（取自原 repo 的 demo，源自 CVPR 2025 論文 TSAM）。

## idea.md（方法與貢獻）
```markdown
## Problem Statement      — 要解決的問題、現有方法的缺陷
## Core Hypothesis        — 核心假設 / 洞見
## Proposed Methodology   — 架構、模組、公式（給出符號定義與方程式）、訓練目標、演算法步驟
## Key Contributions      — 3–4 點貢獻
## (選用) Theoretical Analysis / Design Rationale
```
原版有 `idea_dense.md`（詳細）與 `idea_sparse.md`（只有摘要式想法）兩種密度；兩種都能跑，dense 結果較好。

## experimental_log.md（唯一的數據真值）
```markdown
## Setup           — 資料集（含 split 與規模）、backbone、超參數、硬體、訓練時間、評估指標定義
## Baselines       — 比較了哪些方法（只有這些可以宣稱「優於」）
## Main Results    — 表格（Markdown 表格即可），保留原始精度
## Ablations       — 每個消融的設定與數字
## Qualitative Observations — 成功/失敗案例的文字描述
## (選用) Raw data for plots — 曲線、敏感度分析的逐點數據
```

## 現成圖（選用）
放在 `raw_materials/`，並建立 `raw_materials/figures.json`：
```json
[{"file": "fig_framework_overview.png", "caption": "Overview of ...", "kind": "diagram"}]
```

## 自訂會議模板
在 `templates/<venue>/` 放：
- `template.tex`：完整可編譯骨架，每節之間用 `%%%%%%%%% <SECTION> %%%%%%%%%` 標記包住佔位文字（參考內建模板）；`\bibliography{references}`。
- `guidelines.md`：頁數上限（主文是否含 references）、雙盲規則、欄數、字級、圖表規範。
- 會議官方 `.sty`、`.bst`、`references.bib`（可空）。
