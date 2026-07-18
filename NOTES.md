# 我如何領導 Agent 完成 LLM 推論服務

## 紀錄範圍

這份筆記不是只根據 Git commit 反推，而是讀取 Agent 在 `/Users/leo/Projects/0718` 下的全部 session 紀錄後整理。我用 session 內的需求、操作、測試、HTTP／Playwright 結果及 Git 歷史互相核對，再依實際事件時間排序。

本次納入 11 份使用者工作 session 和 3 份受管命令的 Guardian 審核 session。嘗試後撤回、環境阻擋、臨時 commit 重整等不會出現在最終 Git 歷史的步驟也一併保留；Session Cookie、完整 API Key 等憑證不寫入本文件。

## 我的領導方式

這個專案不是把一句模糊需求交給 Agent 後直接接受結果。我持續負責產品方向、工程標準、優先順序、錯誤判斷與完成定義，Agent 則負責依指令盤點、實作、測試並回報證據。我的主要做法是：

1. 我先定義可驗收的 MVP：使用者流程、API 路由、錯誤格式、Echo 規則、Tokens 一致性、公開手冊與 README 都有明確條件。
2. 我要求文件先行，並把「每次行為、設定或 UI 變更都要同步更新文件」寫成永久工程規則。
3. Agent 最初提出 Node.js 方案時，我立即指定 Python、uv、FastAPI，讓技術路線在大量程式碼提交前完成修正。
4. 我固定服務位址與開發方式，避免 Agent 用不同 port 或隱含環境完成一個無法一致重現的版本。
5. 我把 API Key 功能分階段加深：先撤銷，再 Usage，再命名，之後才調整 dialogs、icons、table 與 Avatar，讓每一步都能獨立驗證。
6. 我不只接受「測試通過」的回報，還要求實際 HTTP、SSE curl 與 Playwright E2E；SSE 測試也要求重新執行，不引用舊結果。
7. Playwright 驗證被帶往 GPT plugin 時，我主動質疑必要性，促使 Agent 改回標準 Playwright CLI，排除不必要的工具依賴。
8. 發生登入問題時，我提供 login 成功但控制台不顯示的具體證據，要求沿 `/api/login`、`/api/me`、前端 render 與程序版本逐層排查。
9. Agent 為通過測試想補回「操作」表頭時，我明確指出空白是刻意設計，要求測試配合產品意圖，而不是反過來改產品迎合過時測試。
10. 我要求 commits 依功能拆分、保留最新版內容、排除 `cookies.txt`，並把混合 commit 拆回重整，讓 Git 歷史可以審查。
11. 錯誤修好後，我再要求建立 troubleshooting 文件，把一次性排查結果轉成後續可重用的診斷流程。

因此，這份文件的主線是「我如何決策、糾偏與驗收」，而不是單純羅列 Agent 產生了哪些檔案。

## Session 對照表

| 開始時間 | 類型 | 主要內容 |
| --- | --- | --- |
| 21:45 | 我主導 | 從空倉庫建立 MVP；之後追加 SSE、手冊與 SSE 測試。 |
| 21:58 | 我主導 | 安裝 Microsoft Playwright MCP。 |
| 22:00 | 我主導 | Playwright 驗證、Chrome 安裝、改用獨立 Playwright CLI。 |
| 22:06 | 我主導 | API Key 刪除、用量、命名、dialogs、icons、table 與響應式調整。 |
| 22:08 | 系統審核 | 審核 Chrome 安裝等受管操作。 |
| 22:17 | 我主導 | 兩次登入後無法顯示控制台的診斷、修正與排查文件。 |
| 22:18 | 我主導 | README 翻譯成繁體中文並提交、推送。 |
| 22:30 | 我主導 | Navbar Avatar、帳號 popper、移動登出及移除重複手冊入口。 |
| 22:42 | 我主導 | 查詢 `<code>` 標籤樣式的修改位置。 |
| 22:46 | 我主導 | 將目前工作樹依 API Key 後端、控制台、SSE 拆成 commits。 |
| 22:50 | 我主導 | 查詢 Codex CLI 的 session 歷史指令。 |
| 22:52 | 系統審核 | 審核分批 `git add`、`git commit` 操作。 |
| 22:57 | 我主導 | 建立本 `NOTES.md`，並改為讀取所有 session 後撰寫。 |
| 23:04 | 系統審核 | 審核第二次登入修正後的 pytest 操作。 |

## 一、提出原始 MVP 需求

我一開始要求開發一個銷售 LLM inference 服務的 MVP，讓客戶可以在網站註冊、登入、取得 API Key，再用 API Key 呼叫 OpenAI 相容端點。原始需求包括：

1. 網頁註冊與登入，密碼必須加密。
2. 登入後可產生並查看自己的 API Key。
3. 提供 `POST /api/register`、`POST /api/login`、`POST /api/keys`。
4. 提供 Bearer Auth 的 `POST /v1/chat/completions`。
5. MVP 不打真實模型，回應需包含最後一則 user message 的 Echo 內容。
6. 回應需有自洽的 Prompt、Completion 與 Total Tokens。
7. 金鑰缺少或錯誤時回 JSON 401，不可回 HTML 或 stack trace。
8. 未登入也能查看 `/manual`，內容需有完整流程與 curl 範例。
9. 建立含安裝、啟動、測試方式的 README。
10. 一般 API 統一使用 `{ success, message }`。
11. 先寫 `AGENTS.md` 與 `docs/`，再寫功能。
12. 經常依 `[type]: [description]` 格式 commit。

## 二、從空倉庫開始，先寫規格

### 21:45 - 盤點與規劃

我先要求 Agent 盤點現況並逐條對照 MVP。Agent 確認工作目錄是一個沒有既有程式與提交的新倉庫後，依我的完成條件建立開發計畫，列出文件、後端、前端、測試、驗證與完成度稽核。

### 21:46 - 先採用 Node 草案

在我尚未指定技術棧時，Agent 先提出 Node.js、Express、SQLite 與 bcrypt 方案，並依我「先寫文件」的要求建立：

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/security.md`

這一階段先定義了產品範圍、一般 JSON response wrapper、OpenAI 相容推論欄位、Session、API Key 只顯示一次及只儲存雜湊等規則，然後建立第一個文件 commit。

Agent 曾開始建立 `package.json` 與 `src/*.js` 的 Node 後端草案。我在它提交前指定新技術棧，讓這批草案直接被替換，避免錯誤路線進入正式歷史。

### 21:48 - 我指定 Python、uv、FastAPI

我輸入 `Skill Stack: python, uv, fastapi`，明確收斂技術方向，並要求保留既有 API 契約。Agent 立即停止 Node 實作，改成：

- Python 3.11+
- FastAPI
- Uvicorn
- uv
- Python 標準函式庫 SQLite
- Pydantic
- pwdlib + Argon2
- pytest、httpx、Ruff

文件也先從 Express／bcrypt 改成 FastAPI／Argon2，並獨立提交技術棧變更。

## 三、建立 FastAPI MVP

### 21:49 - 建立專案骨架與相依套件

我要求 Agent 依文件契約建立可測試的 FastAPI 骨架，Agent 建立：

- `pyproject.toml` 與 `uv.lock`
- `app/__init__.py`
- `app/database.py`
- `app/security.py`
- `app/schemas.py`
- `app/main.py`
- `public/index.html`
- `public/app.js`
- `public/styles.css`
- `public/manual.html`

後端用 FastAPI 同時提供 HTML、靜態檔案與 JSON API。SQLite 層建立 users、sessions、api_keys 表，啟用 Foreign Key 與 WAL，並用 Lock 保護共用連線。

安全層完成 Argon2 密碼雜湊、32-byte 隨機 Session Token、`llm_live_` API Key、SHA-256 digest 與 Cookie 解析。資料庫只保存 Session 與 API Key 的 digest，不保存明文。

Schema 限制 username、password、model、messages、role 等欄位，FastAPI validation error、未知 API route 與未處理例外都統一轉成 JSON。

### 21:51 - 完成帳號、Key 與推論路由

我用原始規格逐項指定必要路由，Agent 實作：

- `POST /api/register`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`
- `POST /api/keys`
- `POST /v1/chat/completions`

登入建立 server-side Session Cookie，使用 `HttpOnly`、`SameSite=Lax`，production 時加上 `Secure`。推論端點解析 Bearer Key，找最後一筆 user message，回傳 `Echo: ...`，用 UTF-8 byte 長度產生固定近似 Token 數，並保留 OpenAI 相容的頂層欄位。

前端建立登入／註冊 tab、登入後控制台、API Key 一次性顯示與複製、遮罩後 Key 清單。公開 `/manual` 提供帳號、Key 與推論 curl 範例。

### 21:53 - 我固定服務位址並提高文件要求

我要求服務統一跑在 `http://127.0.0.1:8000`，並要求 `AGENTS.md` 明定後續所有程式、行為、設定與 UI 變更都要同步更新文件。

Agent 依我的決策同步修正 README、架構文件、公開手冊、curl 範例與 production 環境變數，並把固定 port 設成 8000。

### 21:54 - 安裝、鎖版與靜態檢查

我要求在整合測試前先鎖定相依並清除靜態問題。Agent 執行 `uv sync`；第一次 Ruff 檢查發現格式與 FastAPI dependency injection 寫法問題，於是：

- 改用 `Annotated[..., Depends(...)]`。
- 整理長行與格式。
- 在 README 加入 Ruff lint 與 format check 指令。
- 執行格式化、lint 與 app import smoke test。

### 21:55 - 建立第一批整合測試

我要求測試直接證明安全與 API 契約，而不只測 happy path。Agent 建立 pytest fixtures 與帳號、推論、頁面測試，驗證：

- 密碼與 API Key 不以明文儲存。
- username 大小寫不敏感且不可重複。
- Cookie 安全屬性與 Session digest。
- 未登入與無效 Key 回 JSON 401。
- Echo 使用最後一筆 user message。
- Token 三欄加總一致。
- `/manual` 公開可讀。
- 未知 API route 回 JSON 404。

第一次 pytest collection 因 Python import path 失敗。我要求 Agent 區分「測試環境問題」與「API 行為失敗」，不要誤判功能。Agent 在 `pyproject.toml` 加入專案根目錄，並在架構文件補上 `app/`、`public/`、`tests/` 的責任邊界。修正後 10 個整合測試全部通過；唯一訊息是 Starlette 對未來 httpx2 的棄用警告。

### 21:56 - 提交 MVP 並做實際 HTTP 驗證

在自動測試通過後，我仍要求 Agent 驗證實際程序。Agent 建立 FastAPI MVP 功能 commit，啟動 `127.0.0.1:8000`。由於 in-app Browser 沒有可用 instance，這一輪無法做截圖；我接受以實際 HTTP smoke test 作為當下替代證據，驗證註冊 201、登入 200、Set-Cookie、建立 Key 200、推論 200、Echo 內容與 usage 加總。

完成度稽核確認文件、路由、測試、lock、Ruff、format 與 HTTP 流程都通過，初版 MVP 完成。

## 四、建立 Playwright 驗證環境

### 21:58 - 安裝 Microsoft Playwright MCP

為補上瀏覽器實機證據，我要求 Agent 安裝 `https://github.com/microsoft/playwright-mcp`。Agent 先查官方說明、本機 `codex mcp` 指令、Node 版本與既有 MCP 清單，確認沒有同名設定後，把 Playwright MCP 加到全域 Codex 設定。

安裝結果：

- 設定檔：`~/.codex/config.toml`
- 套件：`@playwright/mcp`
- 當時解析版本：`0.0.78`
- 狀態：enabled
- CLI 啟動及 MCP `initialize` handshake 通過

這次只修改 Codex 全域環境，沒有修改專案檔案。

### 22:00 - 第一次要求 Playwright 驗證

我要求 Agent 用 Playwright 驗證專案，且測試資料不能污染正式開發資料。Agent 以獨立暫存 SQLite 啟動測試服務，但 in-app Browser 沒有任何可用 browser instance，所以停止該測試服務，沒有改檔案。

### 22:03 - 安裝 Chrome 與誤走的外掛路徑

為排除缺少瀏覽器的阻礙，我允許 Agent 安裝 Chrome instance。Agent 使用 Homebrew 安裝 Google Chrome `150.0.7871.129`，再安裝並啟用 Codex 的 `chrome@openai-bundled` plugin。

後續為了讓 Codex 控制現有 Chrome，又依序：

1. 啟動 Chrome 建立預設 profile。
2. 開啟 Chrome Web Store。
3. 由我確認安裝 ChatGPT Chrome Extension。
4. 發現 native messaging 連線元件仍缺少，要求重裝 Chrome plugin。

我沒有直接接受這條工具鏈，而是追問「為什麼 Playwright 驗證需要 GPT plugin」。Agent 才釐清：一般 Playwright 完全不需要 GPT plugin；前面的需求只源於 Codex in-app `tab.playwright` 控制既有 Chrome 的特殊路徑。我因此終止這條不必要的繞路，改用標準 Playwright CLI。

### 22:28 - 改用獨立 Playwright CLI

我要求 Agent 回到目標本身並繼續驗證。Agent 不再使用 GPT plugin，而是在 `/tmp/playwright-0718` 建立暫存的 `@playwright/test` 環境，使用系統 Chrome 和獨立 SQLite，不修改專案依賴。

我把驗收範圍擴大到完整生命週期與響應式畫面，Agent 建立暫存 E2E 測試，涵蓋：

- 註冊與登入。
- 建立、命名、改名、移除 API Key。
- 實際呼叫推論 API。
- 用量更新。
- Key 撤銷後拒絕請求。
- 登出與錯誤密碼。
- 桌面與 390px 手機版。
- `/manual` 公開頁。
- console error、page error 與截圖。

前幾輪失敗來自暫存測試 selector 太寬、登入按鈕文字重複、手冊 H1 預期錯誤，以及專案同步把 `.key-row` 改成 table 後 selector 過時。我要求 Agent 先用 DOM snapshot 與截圖分辨「測試寫錯」或「產品真的壞了」，再修正暫存 selector，沒有把測試問題誤判成產品錯誤。

最後功能流程以 `1 passed (3.1s)` 通過，桌面與手機控制台沒有重疊或溢出。Playwright 真正找到的問題是 390px 手機手冊被長 SSE JSON 撐到 2056px 寬；診斷為 `.manual-grid` 的 intrinsic width，建議使用 `minmax(0, 1fr)` 並讓 `.manual-content` 設 `min-width: 0`。這個 Playwright session 只回報問題，沒有直接修改專案檔案。

## 五、擴充 API Key 完整生命週期

我同時推進 Playwright、README、登入診斷與 API Key 工作線，因此工作樹會接收其他 session 的更新。我明確要求 Agent 保留既有變更、以現況為準，並繼續遵守文件優先規則，避免並行工作互相覆蓋。

### 22:06 - 加入移除與立即撤銷

我先把 API Key 管理從「只能建立」推進到完整撤銷，要求控制台能移除 Key，且刪除後必須立即失效。原架構文件當時把 revocation 列為 scope 外，因此我要求 Agent 先修改契約，再更新 API、架構、安全文件與實作：

- `DELETE /api/keys/{key_id}`。
- 只允許登入者刪除自己的 Key。
- 不存在和屬於他人的 Key 都回 404 `api_key_not_found`，避免洩漏所有權。
- 控制台刪除後重新載入列表。
- 刪除 digest 後，新推論請求立即回 401 `invalid_api_key`。

測試涵蓋未登入、跨帳號、重複刪除、只刪指定 Key、其他 Key 保留及刪除後拒絕推論。完成這一段時測試由 10 增加到 11 個。

### 22:10 - 加入每把 Key 的 Usage 監控

完成撤銷後，我再要求每把 Key 都能獨立查看用量，並守住不保存 prompt 或 response 內容的隱私邊界。Agent 先把這個資料邊界寫進文件，接著加入：

- `request_count`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`，由前兩者相加
- `last_used_at`

成功推論時，用同一個 SQL update 原子累加該 Key 的次數與 Tokens；驗證失敗不計數。`GET /api/me` 回傳各 Key 的獨立 usage。

我要求功能不能迫使既有使用者刪除資料庫重建。Agent 因此在啟動時讀取 `PRAGMA table_info(api_keys)`，缺欄位就用 `ALTER TABLE` 加入零值欄位，並新增舊 schema migration 測試。

### 22:12 - 加入 Key 命名與改名

接著我補齊可管理性，要求建立時命名、後續可編輯，同時不能破壞省略 payload 的舊 client。Agent 先更新契約，再實作：

- `ApiKeyName` schema。
- 名稱 trim 後需 1-64 字元。
- 省略建立 payload 時使用 `Untitled key`，維持舊 client 相容。
- `PATCH /api/keys/{key_id}`。
- 更新時同樣做 owner scope 與一致的 404。
- 舊資料遷移後自動取得預設名稱。
- 建立與編輯共用同一個命名 dialog。

完成命名、Usage、刪除及 migration 後，我要求 Agent 先跑完整測試，再做真實服務驗證，共 14 個測試通過。因 port 8000 已被另一個服務占用，Agent 用獨立資料庫在 8001 啟動最新版服務，避免干擾既有程序。

第一次真實 HTTP 腳本因包含暫存檔清理命令被執行環境拒絕，並未碰到服務；移除清理步驟後重新執行，驗證建立命名 Key 時 usage 為 0、推論後變 1、改名立即反映、刪除後原 Key 回 `invalid_api_key`，並通過前端 JavaScript 語法檢查。

我另外追問「移除是否等於 revoke」，要求 Agent 把 UI 文案背後的安全語意說清楚。確認結果是刪除資料庫 digest 就會立即撤銷後續請求；已經完成授權的進行中請求仍可能完成。

## 六、改善 API Key 控制台介面

### 22:25 - Icon 按鈕與自訂 Dialog

我要求：

- 編輯、移除按鈕改成 icon。
- 移除 border。
- 不使用原生 `window.confirm`。
- 改成站內 dialog。
- 建立 Key 後在另一個 dialog 顯示完整 Key。

我要求先同步文件與安全說明，再改介面。Agent 加入內嵌 icon symbols、36x36 無邊框 icon buttons、hover tooltip、`aria-label`、移除確認 dialog 與新 Key 一次性 dialog。新 Key dialog 關閉時會清空 DOM 內的完整 API Key。

這一輪 14 個測試、Ruff、JavaScript 語法及 diff check 通過；in-app Browser 仍沒有 instance，所以當時沒有截圖式 QA。

### 22:30 - Navbar Avatar 與帳號 Popper

我重新整理登入後的資訊架構，要求在 navbar 最右側加入 Avatar，點擊顯示 popper，並把登出移進 popper。Agent 沿用原生 HTML/CSS/JS 與既有 icon sprite，完成：

- 只有登入後顯示 Avatar。
- 顯示 username 與登出按鈕。
- 點擊外部、focus 離開或 Escape 關閉。
- Escape 關閉後恢復 Avatar focus。
- `aria-expanded` 與可存取 label。
- 登出按鈕在 DOM 只保留一個。

我隨後辨識出重複入口，要求移除 API 控制台標題區的「查看手冊」按鈕，只保留 navbar 的 `/manual`。我再要求用測試證明連結和登出按鈕各只剩一個；完成後 17 tests、Ruff 與 JavaScript 語法檢查通過，服務另開在 8002 供檢查。

### 22:34 - Key List 改成 Table

為提升掃描與比較效率，我要求 API Key List 改成分欄 table。Agent 把原本 CSS Grid list 改成語意化 `<table>`，包含：

- 名稱
- API Key 遮罩值
- 建立時間
- 最近使用
- 用量
- 操作

`#key-list` 改成 `<tbody>`；空狀態使用跨六欄的 row，並保留 caption、thead、th 和 td 語意。

### 22:38 - 解決 Table Row 寬度溢出

第一版 table 依賴 900px 最小寬度，我沒有接受把水平捲動當成完成，而是要求重新整理 row，窄螢幕不能溢出。Agent 移除固定最小寬度，桌面使用 `table-layout: fixed`，名稱、日期與 Key 可在 cell 內換行；700px 以下把每一列轉成標籤／值排列，以 `data-label` 顯示欄名，六個欄位都保留且頁面不產生水平溢出。

後續獨立 Playwright 截圖也確認桌面和手機控制台沒有溢出或重疊。

## 七、診斷兩次登入後無法進入控制台

### 22:17 - 第一次：新前端搭配舊後端

我沒有只說「登入壞了」，而是提供可定位的證據：正確帳密登入成功，`/api/login` 回 `{"success":true,"message":{"username":"Leo"}}`，但畫面沒有切換到 API Key 列表，後續看似沒有回覆。這讓 Agent 能先排除帳密驗證，把調查焦點放在 login 後的狀態載入。

我要求 Agent 沿著登入後的資料流與實際程序查證，而不是先改帳號 API。Agent 確認前端不會換 URL，而是再呼叫 `GET /api/me`，成功後才切換畫面。當時 8000 與 8001 同時有 Uvicorn 程序；8000 是修改前啟動的舊程式，回傳的 Key 缺少新版前端會讀取的 `name` 與 `usage`，8001 才是最新版。

新版前端執行 `key.usage.total_tokens` 時發生 JavaScript 例外，而外層 catch 把所有錯誤都當成未登入，所以畫面無聲回到登入頁。當時的處理是：

1. README 啟動指令加入 `--reload`。
2. 架構文件記錄開發時前後端資源必須保持同一 revision。
3. 重啟 8000，載入最新版後端。
4. 用既有 Session 驗證 `/api/me` 回完整結構。
5. 執行 14 tests、Ruff 與 diff check。

修正驗證後，我要求只 commit 與 push 這次 reload 問題相關內容，不把並行中的 API Key 功能或 `cookies.txt` 混入。README 的 reload 修改已隨繁體中文翻譯 commit 推上去；架構文件的 reload 說明另以 `df02b02` 提交並推送。

### 23:02 - 第二次：失效 DOM 引用

功能 commits 完成後，我再次實際操作並回報同樣症狀。我沒有接受「已加 reload，所以不會再發生」的舊結論，而是要求重新診斷。這次 reload worker 已換新 PID，後端 `/api/me` 也正常，因此我與 Agent 排除第一次的舊程序假設。

在我要求檢查新增 Avatar/menu 的 DOM 初始化後，Agent 發現 `9bbd6c2` 的新版 HTML 已移除 `#current-user`，但 `public/app.js` 的 `loadAccount()` 仍執行：

```js
document.querySelector('#current-user').textContent = username;
```

`querySelector` 回傳 null，登入後雖然 `/api/me` 成功，前端仍因 `null.textContent` 例外而進入 catch；catch 又把任何錯誤都視為 401，畫面因此回到登入表單。

修正步驟：

1. 先更新 README 與架構文件，補充登入後會載入 `/api/me` 再切換控制台。
2. 移除失效的 `#current-user` 引用。
3. 讓 `request()` 把 HTTP status 放進 Error。
4. 只有真正的 401 才切回未登入畫面。
5. 其他錯誤寫入 console 並在表單顯示「無法載入 API 控制台」。
6. 新增 DOM contract test，確認 `app.js` 用 `querySelector('#...')` 引用的 id 都存在於首頁。

測試一度仍因「操作」表頭的舊斷言失敗。Agent 先嘗試補回可見表頭，但我說明操作欄位是刻意留白，要求撤回這個為測試而改產品的做法，改掉過時斷言並保留真正能防止登入回歸的 DOM contract test。最終完整套件為 `18 passed`，我也親自確認登入成功，再追問根因以確認不是帳密或 `/api/me` 後端問題。

### 23:12 - 建立快速排查文件

我沒有讓排查知識只留在對話裡；確認修復後，我要求把問題寫進文件，讓後續發生相同症狀時可以快速診斷。Agent 新增 `docs/troubleshooting.md`，並從 README 加入入口。文件記錄：

- login 200 但控制台不顯示的症狀。
- `/api/me` 200 與 401 的判斷差異。
- 這次失效 DOM id 的根因。
- 如何從 Network 與 Console 判斷前端渲染例外。
- DOM contract 單一回歸測試。
- 完整 pytest／Ruff 指令。
- Uvicorn reload 短暫換 worker 與新舊版本混用的注意事項。
- `cookies.txt` 含有效 Session，不得提交或分享。

這份排查文件與 README 連結通過 `git diff --check`，最後連同登入修正、錯誤邊界與 DOM contract test 建立 `48a7186 fix: restore API console after login`。

### 我用來領導錯誤排查的方法

兩次相同登入症狀的根因不同，這讓我確立一套不依賴猜測的排查方式：

1. 先提供可觀察事實：哪一個 request 成功、status/body 是什麼、畫面停在哪裡。
2. 要求 Agent 畫出完整事件鏈：submit、login、Set-Cookie、`/api/me`、render、view switch。
3. 分層排除：帳密驗證、Session、HTTP response、後端版本、前端 DOM、error boundary。
4. 檢查實際執行程序與 port，不只讀工作樹；舊 worker 可能讓正確程式碼看起來沒有生效。
5. 相同症狀再次發生時重新蒐證，不能沿用第一次根因。第一次是新舊版本混用，第二次是 stale DOM reference。
6. 修正根因之外也要修正可觀測性。本次把所有錯誤都吞成「未登入」的 catch 拆開，讓非 401 錯誤能顯示並寫入 console。
7. 回歸測試要守住真正的契約。本次新增 DOM id 一致性測試，而不是用錯誤的可見表頭斷言逼迫 UI 改版。
8. 最後由我實際重現成功、要求完整測試，再把症狀、判斷分支、指令與安全注意事項寫入 troubleshooting 文件。

## 八、README、手冊與樣式查詢

### 22:18 - README 翻譯成繁體中文

我要求把 README 翻譯成繁體中文，並指定不得改動 shell 指令、路徑與 JSON 範例。Agent 保留當時已存在的工作樹內容，只翻譯說明文字，統一使用「推論」、「API 金鑰」、「工作階段」等術語。

我接著要求 commit 與 push，並維持單一功能邊界。Agent 只暫存 README，不納入其他程式、文件、測試及 `cookies.txt`，建立 `9abd272 docs: translate README to Traditional Chinese` 並推到 `origin/main`。

### 22:36 - 擴充公開 API 手冊

我認為原本簡短的 SSE 說明不足以讓使用者真正串接，因此要求更新 API 手冊。Agent 把 SSE 升級為 `/manual` 的獨立章節，新增：

- 導覽連結。
- `stream: true` request。
- `curl --no-buffer`。
- `text/event-stream`。
- role、content、stop、`[DONE]` 事件順序表。
- 完整 wire frames。
- `delta.content` 重組。
- final usage。
- 驗證錯誤仍為 JSON 400／401。

當時手冊修改曾建立臨時 commit `30ec967 docs: 擴充 SSE API 公開手冊`，之後為符合我「依功能切分」的要求，被重新整理進最終功能 commits，因此不在現在的最終歷史中。

### 22:42 - 查詢 `<code>` 樣式位置

我詢問 code 標籤在哪裡修改。Agent 回覆主要位置都在 `public/styles.css`：

- 一般 inline code：`code { ... }`
- 手冊 code block：`.manual-content pre` 與 `.manual-content pre code`
- API Key table：`.key-table code`

這個 session 只查詢程式位置，沒有修改檔案。

## 九、加入 SSE Streaming

### 22:28 - 先定義契約

我在基本 MVP 穩定後主導加入 `/v1/chat/completions` SSE streaming，並要求仍然遵守「契約先於程式」。Agent 先執行既有 14 個測試建立基準，再新增 `docs/streaming.md`，並把它加入 `AGENTS.md` 必讀清單。

契約定義：

- request 用 `"stream": true`。
- response 為 `text/event-stream`。
- 先送 assistant role chunk。
- 再送一到多個 content chunks。
- 最後送含 usage 的 stop chunk。
- 結尾送 `data: [DONE]`。
- 所有 JSON chunks 共用 completion ID、created、model、success 與 message。
- 驗證失敗在開 stream 前回原本 JSON 400／401。
- stream 成功到 stop event 才記一次用量，中斷不計。

SSE 契約先以 `c7dca50 docs: 定義 SSE 串流回應契約` 獨立提交。

### 22:31 - 實作 StreamingResponse

契約確認後，我才讓 Agent 更新 `ChatCompletionRequest`，加入 `stream: bool = False`；在 endpoint 加入：

- `encode_sse()`。
- 固定字元數的 `split_content()`，不切斷 Unicode code point。
- 非同步 event generator。
- FastAPI `StreamingResponse`。
- `Cache-Control: no-cache`。
- `X-Accel-Buffering: no`。
- `request.is_disconnected()`。
- 一般與串流共用 usage 計算及記錄函式。

非串流 response 保持不變。新增測試會解析 SSE frames，驗證事件順序、共用 metadata、中文字串重組、final usage、`[DONE]`、錯誤 JSON 與 `stream: false` 相容性。

### 22:32 - 測試與實際 curl

完整 17 tests 通過後，我仍要求用真實 curl 證明事件是逐 frame 送出。Agent 重啟固定 8000 服務時發現 port 很快被另一個程序占用，因此先辨識占用者，再安全載入此專案新版。

實際 curl 驗證結果：HTTP 200、Content-Type 為 `text/event-stream`、收到 4 個事件、中文內容可重組、stop usage 為 `5 + 6 = 11`、最後收到 `[DONE]`。

我稍後特別追問 SSE 測試是否通過，要求提供當下證據。Agent 重新只跑 SSE 專屬案例，結果為 `3 passed, 4 deselected`，沒有只引用前一次結果。

### Cookie 安全補強

SSE 實際 curl 過程使用了 `cookies.txt`。Agent 回報它含有效 Session 後，我同意把這個測試產物納入安全收尾：加入 `.gitignore`，並在安全文件註明不得提交或分享，建立 `c8d9022 chore: 忽略本機 Session cookie 檔案`。

## 十、重新整理 Git 歷史

我兩次要求「依照功能分次 commit」，沒有接受依檔案或依當下暫存狀態直接提交。Agent 依我的要求檢查 staged／unstaged hunks、文件與測試後，規劃切成：

1. API Key 生命週期與 Usage 後端。
2. API Key 控制台、dialogs、table 與帳號選單。
3. SSE 串流功能與手冊。

過程中發現臨時 commit `f36a5c2` 同時混入 API Key 與 SSE，不符合我的功能邊界；後面又有 cookie 安全與 SSE 手冊 commits。我要求在尚未推送時整理歷史，Agent 將 `c7dca50` 之後的本機變更拆回工作區重新分組，保留檔案內容，不動既有 SSE 契約 commit。

第一批先完成 `22fa1f5 feat: add API key management and usage tracking`。第二批部分暫存 README、手冊與頁面測試的 UI hunks，把 SSE 專屬內容留給第三批。

我要求每個 commit 的暫存快照本身也要可驗證。測試第二批時，舊斷言期待「操作」文字、HTML 卻刻意留白。Agent 曾補上一行以修切片，但我要求完全依目前最新版 commit，因此那行被撤回，保留我的空白表頭設計。當時我接受如實記錄 16 passed、1 failed，而不是偷偷改 UI；後續再以正確測試意圖收斂到 18 passed。

最終三個功能 commits 為：

| Commit | 功能 |
| --- | --- |
| `22fa1f5` | API Key 命名、改名、撤銷、用量、migration 與後端測試。 |
| `9bbd6c2` | API Key 管理控制台、dialogs、icons、table、Avatar 與帳號選單。 |
| `f9089af` | SSE schema、endpoint、文件、公開手冊與測試。 |
| `48a7186` | 登入後控制台修正、錯誤邊界、DOM contract test 與 troubleshooting。 |

上述功能與修正 commits 都已出現在 `origin/main`。本 NOTES 保持為獨立文件變更，沒有混入既有功能 commits。

## 十一、其他開發工具步驟

為了能回顧與稽核 Agent 的完整工作過程，我另外查詢如何用 Codex 指令叫出 session 歷史。確認後的用法為：

```sh
codex resume
codex resume --all
codex resume --last
codex resume <SESSION_ID>
```

在 Codex 互動介面可使用 `/resume`。當時沒有 `codex history` 子指令。

## 十二、最終功能範圍

開發完成後，專案具備：

- FastAPI + uv + SQLite。
- Argon2 密碼雜湊。
- Server-side Session 與安全 Cookie。
- API Key 只儲存 SHA-256 digest。
- 註冊、登入、登出及 `/api/me`。
- Key 建立、一次性顯示、遮罩、命名、改名、刪除與撤銷。
- 每把 Key 獨立的請求數、Prompt、Completion、Total Tokens 與最近使用時間。
- 舊 SQLite schema 自動 migration。
- OpenAI 相容非串流 Echo Chat Completion。
- OpenAI 相容 SSE Chat Completion。
- 響應式 Key table、icon actions、自訂 dialogs、Avatar popper。
- 公開 API 手冊、SSE 手冊與 curl 範例。
- 帳號、資料庫、Key、推論、SSE、頁面與 DOM contract 自動測試。
- 獨立 Playwright E2E 驗證流程。

## 十三、如何驗證功能完成

### 1. 安裝並執行自動化檢查

```sh
uv sync
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

完成標準：

- uv lock 沒有漂移。
- Ruff 沒有 lint error。
- Python 格式檢查通過。
- pytest 全部通過；本紀錄完成前的最新版結果為 `18 passed`。
- 可以接受目前 Starlette/httpx 的 upstream deprecation warning，但不得有 test failure。

### 2. 啟動最新版服務

```sh
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

確認：

- `http://127.0.0.1:8000/` 回 200。
- `http://127.0.0.1:8000/manual` 未登入也回 200。
- 修改 Python 或 public 資源後 reload worker 會載入最新版，避免新舊前後端混用。

### 3. 驗證註冊、登入與 Session

```sh
curl -i -X POST http://127.0.0.1:8000/api/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"correct-horse-battery-staple"}'

curl -i -c cookies.txt -X POST http://127.0.0.1:8000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"correct-horse-battery-staple"}'

curl -b cookies.txt http://127.0.0.1:8000/api/me
```

完成標準：註冊回 201；登入回 200 並包含 `Set-Cookie`；Cookie 有 HttpOnly、SameSite=Lax；`/api/me` 在短時間內回 200 並包含 username 和 keys。瀏覽器登入後必須切到 API 控制台，而不是停留或無聲回到登入表單。

### 4. 驗證 API Key 管理

```sh
curl -X POST http://127.0.0.1:8000/api/keys \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{"name":"Production"}'
```

保存這次 response 的完整 Key，然後檢查 `/api/me`：

- 名稱為 Production。
- 列表只出現遮罩值，不能再次取得完整 Key。
- 初始 requests 與 tokens 都是 0。
- 可以用 `PATCH /api/keys/{id}` 改名。
- 未登入、他人 Key、純空白名稱都按契約被拒絕。

### 5. 驗證非串流推論與 Usage

```sh
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer llm_live_REPLACE_ME' \
  -d '{"model":"mock-echo-1","messages":[{"role":"user","content":"Hello"}]}'
```

完成標準：HTTP 200；`object` 為 `chat.completion`；`choices[0].message.content` 包含 Hello；`total_tokens` 等於 Prompt 加 Completion；再次查 `/api/me` 時只有使用的那把 Key 增加 1 次請求與對應 Tokens。

### 6. 驗證 SSE

```sh
curl --no-buffer -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer llm_live_REPLACE_ME' \
  -d '{"model":"mock-echo-1","messages":[{"role":"user","content":"Hello"}],"stream":true}'
```

完成標準：Content-Type 為 `text/event-stream`；順序為 role chunk、content chunks、含 usage 的 stop chunk、`data: [DONE]`；所有 chunks 共用 id/model/created；串接 `delta.content` 後得到完整 Echo；usage 只增加一次。

專屬測試可執行：

```sh
uv run pytest tests/test_inference.py -k 'stream'
```

歷史實跑結果為 `3 passed, 4 deselected`。

### 7. 驗證撤銷與錯誤格式

```sh
curl -X DELETE http://127.0.0.1:8000/api/keys/KEY_ID -b cookies.txt
```

刪除後再用原 Key 呼叫推論，必須回 401 `invalid_api_key`。同帳號其他 Key 仍要可用。缺少 Bearer、錯誤 payload、未知 `/api/*` 或 `/v1/*` 路由都必須回 JSON，且包含 `success: false` 與穩定的 `message.code`，不可回 HTML 或 stack trace。

### 8. 驗證瀏覽器操作與響應式畫面

用 Playwright 或人工在 desktop 與 390px mobile viewport 驗證：

1. 註冊後自動登入並顯示控制台。
2. 建立 Key 前先輸入名稱。
3. 完整 Key 只出現在第二個 dialog，關閉後 DOM 被清空。
4. 複製按鈕、改名 dialog、刪除確認 dialog 可操作。
5. 刪除不使用 `window.confirm`。
6. Avatar popper 可用滑鼠、鍵盤 Escape、focusout 與點擊外部關閉。
7. Navbar 只有一個手冊入口，登出按鈕只存在 popper。
8. Key table 在 desktop 分六欄，在 mobile 轉為標籤／值排列。
9. 頁面沒有水平溢出、文字裁切、元素重疊或 JavaScript page error。
10. `/manual` 的長 SSE 範例在手機版不應把整頁撐寬。

### 9. 完成度最後檢查

在宣告完成前逐項確認：

- 文件契約、程式行為與公開手冊一致。
- 每個行為變更都有測試。
- `git diff --check` 通過。
- `git status` 沒有誤納 `cookies.txt`、資料庫或憑證。
- commit 依功能切分且符合 `[type]: [description]`。
- 實際 HTTP 與瀏覽器流程都通過，不只依賴單元測試。
- 已知問題有明確記錄；不能把未驗證項目寫成已完成。

### 10. 本次實際驗證結論

建立本筆記時重新執行的結果：

- `uv lock --check`：通過。
- `uv run ruff check .`：通過。
- `uv run ruff format --check .`：通過，10 個 Python 檔案格式正確。
- `uv run pytest -q`：`18 passed`，另有 1 個 Starlette/httpx upstream deprecation warning。
- `git diff --check`：通過。

核心 Playwright E2E 歷史結果已通過註冊、登入、Key 管理、推論、Usage、撤銷、登出，以及桌面／手機控制台。當時 390px 手機手冊曾量到 2056px 文件寬度；這是已記錄但尚需用最新版重新驗證的視覺項目。在它通過前，不應宣稱所有響應式畫面已完全驗收。
