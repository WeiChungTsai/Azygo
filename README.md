# Azygo

醫學論文評析工作台：一份在**自己電腦上**跑的論文審閱與修改助手。

- `.claude/skills/medical-manuscript-review/` — skill 本體。八個階段（A 剖析 → B 文獻 →
  C 圖檔 → D 評析 → E 審稿 → F 修改 ⇄ G 把關 → H 回覆信）加四項獨立服務，以及六支腳本：
  docx/pptx 擷取、文獻清單解析、追蹤修訂寫入、審稿比分閘門、輪次搬檔、回覆信範本。
- `tools/runner/` — 本機網頁介面。零相依的 Node 伺服器，把每個階段做成一顆按鈕。
- `docs/使用說明.md` — 使用說明（runner 的「使用說明」分頁讀的就是這份）。

```bash
node tools/runner/server.mjs --open
```

管線改寫自 [google-research/paper-orchestra](https://github.com/google-research/paper-orchestra)
（Song et al., 2026, Apache-2.0）：原版從實驗紀錄寫出新論文，這裡改成審閱並修改既有稿件，
文獻來源換成 PubMed，檔案格式換成 docx 與 pptx，並保留它最重要的設計——**審稿把關迴圈**。

稿件不進版控。`review_v30/` 在 `.gitignore` 裡。
