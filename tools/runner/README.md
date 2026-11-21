# 醫學論文評析工作台 — 本機 runner

> 完整的使用說明在 [`docs/使用說明.md`](../../docs/使用說明.md)，伺服器跑起來後也可以在
> 「使用說明」分頁直接讀。這份 README 只講 runner 本身。

在自己的電腦上跑的小伺服器，把 `medical-manuscript-review` skill 的四項服務做成可點擊的流程：
按「開始執行」就 spawn 一個 `claude -p`，把輸出即時串到瀏覽器，同時寫成 run log。

**流程由伺服器持有，不是瀏覽器。** 關掉分頁流程照跑；關掉啟動伺服器的終端機會一併結束。

```
tools/runner/
├─ server.mjs          伺服器（Node 標準函式庫，零相依）
├─ public/index.html   介面
└─ .runner-data/       執行時自動建立
   ├─ projects.json    論文清單
   └─ runs/            run-<時間>-<服務>.jsonl ＋ .meta.json
```

## 需要什麼

- **Node 18 以上**（裝了 Claude Code 就有）
- **`claude` 指令在 PATH 裡**：終端機打 `claude --version` 要有回應
- 四項服務會用到的工具，伺服器啟動後會在左下角實際檢查：
  `python-docx`、`python-pptx`、`openpyxl`、LibreOffice、pdftoppm

缺的話：

```bash
pip install python-docx python-pptx openpyxl
```

```bash
brew install --cask libreoffice && brew install poppler
```

## 啟動

```bash
node tools/runner/server.mjs --open
```

預設 `http://localhost:4178`。改連接埠或資料位置：

```bash
node tools/runner/server.mjs --port 5000 --data ~/.journal-runner
```

只綁 `127.0.0.1`，不會對外開放。

## 怎麼用

1. 按「＋ 新論文」，填**放著稿件的資料夾絕對路徑**。這個資料夾就是 Claude Code 的工作目錄，本文、supplementary 與圖檔 pptx 都放在裡面。
2. 到「材料與設定」填目標期刊（Service 2 需要）、模型、權限模式。
3. 選一個服務分頁，指令可以直接在框裡改，按「開始執行」。
4. 跳到「執行紀錄」看串流輸出。

建議順序 **③ 嚴格評析 → ④ 三位 reviewer → ① 語言編修 → ② 期刊格式**：沒必要去潤飾一段評析說要重寫的文字，而格式取決於最終字數與文獻清單。

同一篇論文一次只能跑一個流程，避免兩個 Claude 同時改同一批檔案。

### 指令裡的 `[STEP]`

預設指令都要求 Claude 每進一個步驟先印一行 `[STEP] …`。執行紀錄會把這種行變成藍色標題帶，上方橫幅也會顯示目前步驟。自己改指令時保留這個慣例，追蹤會好看很多。

## 權限模式

headless 的 `claude -p` **不會跳出權限視窗**，所以權限模式決定了流程遇到未授權動作時會怎樣。在「材料與設定」裡選：

| 模式 | 行為 |
|---|---|
| `acceptEdits`（預設） | 自動接受檔案編輯，其餘動作仍需授權——未授權的會停住 |
| `dontAsk` | 不詢問，未授權的動作直接略過（流程會繼續，但可能少做事） |
| `bypassPermissions` | 略過所有權限檢查 |
| `plan` | 只規劃不執行，適合先看它打算做什麼 |

`bypassPermissions` 會讓流程能刪檔案、對外連線、執行任意指令而不問你。只在你信任那個資料夾內容時使用——稿件本身是你自己的，但如果資料夾裡有別人給的檔案，它們的內容會進到 Claude 的 context。介面在選了這個模式時會顯示警告。

多數情況 `acceptEdits` 夠用。如果流程常常卡住，先看執行紀錄裡它想做什麼，再決定是放寬模式還是在專案的 `.claude/settings.json` 裡針對特定指令授權。

## 資料放哪

- 論文清單：`.runner-data/projects.json`
- 執行紀錄：`.runner-data/runs/run-<時間>-<服務>.jsonl`，原始的 stream-json，一行一個事件
- 每個 run 另有 `.meta.json`：狀態、exit code、花費、session id

伺服器重開後舊紀錄還在，可以從下拉選單回看。想看原始內容直接 `cat` 那個 `.jsonl`。

**產出的檔案在你的論文資料夾裡**，不在 `.runner-data`。

## 這個 runner 不做的事

- 不會自己決定要跑哪個服務，也不會串起整條流程——每一步都是你按的
- 不會驗證 Claude 的產出，報告內容要自己讀
- 沒有帳號與多人協作，就是本機單人工具
- 不會重跑失敗的流程

## 遇到問題

**按了沒反應、紀錄是空的**
看啟動伺服器那個終端機的輸出。`claude` 不在 PATH 時會出現 `spawn claude ENOENT`。

**流程卡住不動**
多半是權限。到執行紀錄看最後一個工具呼叫是什麼，再調整權限模式。

**想中止**
按橫幅上的「停止」。送 SIGTERM，8 秒後沒結束就 SIGKILL。

**關掉終端機之後流程就斷了**
這是設計如此，和原本的 Paper Orchestra 一樣。要長時間跑就讓終端機開著，或用 `tmux` / `screen`。

## 和雲端那頁的關係

`review_v30/web/` 那個 Artifact 是**唯讀的成果頁**：這次評析的報告、49 條意見、檢查清單，可以分享給共同作者看。
這個 runner 是**執行工具**，跑在你自己的電腦上，能讀寫你的檔案。兩者不互通。
