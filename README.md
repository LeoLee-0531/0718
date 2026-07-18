# LLM 推論服務 MVP

一個小型的帳號與 API 金鑰服務，提供與 OpenAI 相容的模擬聊天補全端點。

## 環境需求

- Python 3.11 或更新版本
- [uv](https://docs.astral.sh/uv/)

## 安裝

```sh
uv sync
```

## 啟動

```sh
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

服務會監聽 `http://127.0.0.1:8000`。開啟 `/` 以建立帳號，並可由導覽列前往
`/manual` 查看公開 API 手冊。開發模式會在原始碼變更後自動重新載入，確保
Python 路由與瀏覽器控制台使用同一版程式。註冊成功後會回到登入頁面，必須
再次送出密碼登入，不會直接進入控制台。登入後，導覽列右側會顯示帳號 Avatar，
頁面會切換至 API 控制台；點選 Avatar 可查看目前的登入身分並登出。

設定：

| 變數 | 預設值 | 用途 |
| --- | --- | --- |
| `DATABASE_PATH` | `data/app.db` | SQLite 資料庫路徑 |
| `SESSION_TTL_MS` | `86400000` | 工作階段有效時間（毫秒） |
| `ENVIRONMENT` | `development` | 設為 `production` 時啟用安全 Cookie |

## 測試

```sh
uv run pytest
```

整合測試套件使用暫存 SQLite 資料庫，涵蓋帳號註冊、登入工作階段、API 金鑰的
建立與移除、推論驗證、API 金鑰命名、各金鑰的請求與 Token 計數器、回聲回應、
用量一致性、驗證錯誤、導覽列帳號選單，以及公開手冊。

提交前請執行靜態檢查：

```sh
uv run ruff check .
uv run ruff format --check .
```

## 問題排查

如果登入 API 回傳成功，但頁面沒有切換至 API 控制台，請依照
[Troubleshooting](docs/troubleshooting.md) 檢查 `/api/me`、瀏覽器 Console、
前端 DOM id，以及開發伺服器是否載入最新程式。

## API 快速入門

註冊並儲存登入 Cookie：

```sh
curl -i -X POST http://127.0.0.1:8000/api/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"correct-horse-battery-staple"}'

curl -i -c cookies.txt -X POST http://127.0.0.1:8000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"correct-horse-battery-staple"}'
```

使用已儲存的工作階段建立金鑰：

```sh
curl -X POST http://127.0.0.1:8000/api/keys \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{"name":"Production"}'
```

稍後重新命名金鑰：

```sh
curl -X PATCH http://127.0.0.1:8000/api/keys/1 \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{"name":"Staging"}'
```

使用 `GET /api/me` 回傳的 `id` 移除金鑰：

```sh
curl -X DELETE http://127.0.0.1:8000/api/keys/1 -b cookies.txt
```

使用回傳的金鑰呼叫模擬推論端點：

```sh
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer llm_live_REPLACE_ME' \
  -d '{"model":"mock-echo-1","messages":[{"role":"user","content":"Hello"}]}'
```

加入 `"stream":true` 並使用 `--no-buffer` 接收 OpenAI 相容 SSE 串流：

```sh
curl --no-buffer -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer llm_live_REPLACE_ME' \
  -d '{"model":"mock-echo-1","messages":[{"role":"user","content":"Hello"}],"stream":true}'
```

完整合約請參閱 [docs/api.md](docs/api.md)，瀏覽器版手冊則請前往 `/manual`。
