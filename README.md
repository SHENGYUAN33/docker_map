# 軍事兵推 AI 系統 v6.0

> 基於 Flask + Folium + Ollama + Node.js 的軍事兵推輔助決策系統，支援完全離線運行。

## 1. 專案簡介

本系統是一套**軍事兵棋推演輔助決策平台**，核心功能包括：

- **2D 戰術地圖**（Folium / Leaflet）：在瀏覽器中渲染敵我態勢、武器分派攻擊線、船艦航跡，支援離線圖磚
- **3D 地球儀**（Cesium）：可選的 3D 視角，支援離線 Cesium 資源
- **LLM 意圖理解**（Ollama）：使用本地部署的大語言模型（預設 `llama3.2:3b`），透過 Function Calling 解析使用者自然語言指令（如「匯入場景一」「查詢武器分派」），自動提取參數
- **Local Node.js API**（模擬 CMO API）：在本機以 Node.js 提供船艦資料庫、WTA 武器分派、航跡等 RESTful API，替代中科院真實 API

四個元件的關係：**瀏覽器 → Flask(:5000) → Ollama(:11434) 解析意圖 → Node.js(:3000) 取得資料 → Flask 生成地圖 → 瀏覽器渲染**。

---

## 2. 架構總覽

```
┌────────────────────┐
│     瀏覽器          │
│  Leaflet 2D 地圖    │  http://localhost:5000
│  Cesium 3D 地球儀   │
│  15 個 JS 模組      │
└────────┬───────────┘
         │ HTTP (X-Client-ID Header)
         ▼
┌────────────────────┐     ┌─────────────────────┐
│  Flask 後端         │────▶│  Ollama LLM          │
│  :5000              │◀────│  :11434              │
│                     │     │  llama3.2:3b         │
│  - 12 個 Blueprints │     │  Function Calling    │
│  - Folium 地圖生成  │     └─────────────────────┘
│  - 會話隔離         │
│  - 參數清理/修正    │
└────────┬───────────┘
         │ HTTP (api_mode: local)
         ▼
┌────────────────────┐
│  Node.js API       │
│  :3000             │
│  server_v2_fixed.js│
│                    │
│  - db_v2.json      │
│  - track_data.json │
│  - 模擬 CMO API    │
└────────────────────┘
```

**三個服務必須同時運行**（Local mode）：

| 服務 | Port | 用途 |
|------|------|------|
| Flask 後端 | `5000` | 主應用程式、API 伺服器、Folium 地圖生成 |
| Node.js API | `3000` | 模擬中科院 CMO API（船艦資料、WTA、航跡） |
| Ollama | `11434` | 本地 LLM 推理（意圖理解 + Function Calling） |

---

## 3. 先決條件

### 方法 A：純本機部署

| 軟體 | 最低版本 | 說明 |
|------|---------|------|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **Ollama** | 最新版 | [ollama.com](https://ollama.com/download) |
| **Git** | 任意 | [git-scm.com](https://git-scm.com/) |

**作業系統**：Windows 10/11、Ubuntu 20.04+、macOS 12+、WSL2 均可。

### 方法 B：Docker 部署

| 軟體 | 最低版本 |
|------|---------|
| **Docker Engine** | 24+ |
| **Docker Compose** | v2+ |
| **Docker Desktop**（Windows/Mac） | 最新版 |

> Windows 用戶建議啟用 WSL2 後端以獲得最佳效能。
> GPU 加速 Ollama 需安裝 NVIDIA Container Toolkit（可選）。

---

## 4. 快速開始（方法 A：純本機，最短路徑）

### 4.1 取得專案

```bash
git clone <repository-url>
cd "map - 20260302_v3"
```

### 4.2 安裝 Python 依賴

**Linux / macOS / WSL2：**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows PowerShell：**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4.3 建立環境變數檔

**Linux / macOS / WSL2：**
```bash
cp .env.example .env
```

**Windows PowerShell：**
```powershell
Copy-Item .env.example .env
```

> Local mode 不需修改任何值，所有預設值已適用。

### 4.4 啟動 Ollama 並下載模型

```bash
# 啟動 Ollama（Windows 安裝後通常已作為系統服務運行，可跳過）
ollama serve

# 下載預設模型（另開終端）
ollama pull llama3.2:3b

# 驗證模型已就緒
curl http://localhost:11434/api/tags
```

預期回應包含 `"llama3.2:3b"` 的模型資訊。

### 4.5 啟動 Node.js API（終端 2）

```bash
node server_v2_fixed.js
```

預期輸出：
```
╔══════════════════════════════════════════════════════════╗
║  📍 URL: http://localhost:3000                          ║
╚══════════════════════════════════════════════════════════╝
```

驗證：
```bash
curl http://localhost:3000/health
# 預期: {"status":"ok","timestamp":"..."}
```

### 4.6 啟動 Flask 後端（終端 3）

```bash
python app.py
```

預期輸出：
```
軍事兵推 AI 系統 v6.0 啟動中... 服務地址: http://0.0.0.0:5000
```

### 4.7 開啟系統

瀏覽器前往 **http://localhost:5000**

---

## 5. 環境設定

### 5.1 .env 檔案

從範本建立：`cp .env.example .env`

**Local mode 最小配置（不需修改，全部使用預設值）：**

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `FLASK_HOST` | `0.0.0.0` | Flask 綁定位址 |
| `FLASK_PORT` | `5000` | Flask 綁定端口 |
| `OLLAMA_URL` | `http://localhost:11434/api/chat` | Ollama chat API 端點 |
| `DEFAULT_LLM_MODEL` | `llama3.2:3b` | 預設 LLM 模型 |
| `NODE_API_BASE` | `http://localhost:3000/api/v1` | Node.js API 基礎 URL |
| `LLM_API_TIMEOUT` | `300` | LLM 請求超時（秒） |
| `TILES_DIR` | `tiles` | 離線地圖圖磚目錄 |
| `MAP_DIR` | `maps` | 生成地圖 HTML 儲存目錄 |

**使用 OpenAI / Anthropic 時需額外設定：**
```bash
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
```

### 5.2 system_config.json

此檔案控制 **API 模式**和 **LLM Provider**。執行 `bash setup.sh` 會自動生成，或手動建立。

**關鍵設定值：**

| JSON 路徑 | 值 | 說明 |
|-----------|------|------|
| `api_settings.api_mode` | `"local"` | API 模式：`local` / `mock` / `real` |
| `api_settings.local_api.base_url` | `"http://localhost:3000/api/v1"` | Node.js API 位址 |
| `api_settings.local_api.timeout` | `300` | API 請求超時（秒） |
| `llm_settings.active_provider` | `"ollama"` | LLM 供應商：`ollama` / `openai` / `anthropic` |
| `llm_settings.providers.ollama.base_url` | `"http://localhost:11434"` | Ollama 位址 |
| `llm_settings.providers.ollama.default_model` | `"llama3.2:3b"` | 預設模型 |

<details>
<summary>點擊展開完整 system_config.json 範本</summary>

```json
{
  "api_settings": {
    "api_mode": "local",
    "real_api": {
      "base_url": "https://your-real-api-server.com",
      "timeout": 300,
      "endpoints": {
        "import_scenario": "/import_scenario",
        "star_scenario": "/start_scenario",
        "get_wta": "/get_wta",
        "get_answer": "/get_answer",
        "get_track": "/get_track"
      }
    },
    "local_api": {
      "base_url": "http://localhost:3000/api/v1",
      "timeout": 300,
      "endpoints": {
        "import_scenario": "/import_scenario",
        "star_scenario": "/star_scenario",
        "get_wta": "/get_wta",
        "get_answer": "/get_answer",
        "get_track": "/get_track"
      }
    },
    "local_data": {
      "db_file": "db_v2.json",
      "track_file": "track_data.json",
      "mock_responses_dir": "mock_responses"
    }
  },
  "llm_settings": {
    "active_provider": "ollama",
    "providers": {
      "ollama": {
        "name": "Ollama",
        "base_url": "http://localhost:11434",
        "chat_endpoint": "/api/chat",
        "timeout": 300,
        "default_model": "llama3.2:3b",
        "models": [
          { "id": "llama3.2:3b", "name": "Llama 3.2 3B", "size": "2.0 GB", "speed": "快速", "quality": "良好" },
          { "id": "qwen2.5:7b", "name": "Qwen 2.5 7B", "size": "4.7 GB", "speed": "中等", "quality": "優秀", "supports_tools": true },
          { "id": "llama3.1:8b", "name": "Llama 3.1 8B", "size": "4.7 GB", "speed": "中等", "quality": "優秀", "supports_tools": true }
        ]
      },
      "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com",
        "chat_endpoint": "/v1/chat/completions",
        "timeout": 120,
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4",
        "models": [
          { "id": "gpt-4", "name": "GPT-4" },
          { "id": "gpt-4o", "name": "GPT-4o" }
        ]
      },
      "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "chat_endpoint": "/v1/messages",
        "timeout": 120,
        "api_key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-5-20250929",
        "models": [
          { "id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5" },
          { "id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5" }
        ]
      }
    }
  },
  "rag_settings": {
    "default_mode": "military_qa",
    "default_model": "TAIDE8B",
    "stream": 0,
    "max_sources": 5
  }
}
```

</details>

### 5.3 離線資源（可選）

| 資源 | 目錄 | 大小 | 缺少時的影響 |
|------|------|------|-------------|
| 離線地圖圖磚 | `tiles/` (含 `osm/`, `carto_dark/`, `esri_satellite/`) | ~101 MB | 離線模式地圖底圖空白，連網時正常 |
| Cesium 3D | `static/cesium/` | ~134 MB | 3D 地球儀功能不可用，2D 不受影響 |

取得方式：從現有部署環境複製對應目錄到專案根目錄。

---

## 6. 常用指令

### 開發環境

**Linux / macOS / WSL2：**
```bash
# 啟動所有服務（各開一個終端）
ollama serve                    # 終端 1（若已作為服務運行可跳過）
node server_v2_fixed.js         # 終端 2
python app.py                   # 終端 3

# 切換 LLM 模型
ollama pull qwen2.5:7b          # 下載新模型
# 然後在系統管理頁面切換，或修改 system_config.json

# 查看日誌
tail -f logs/app.log

# 清除生成的地圖檔案
rm -rf maps/*
```

**Windows PowerShell：**
```powershell
# 啟動所有服務（各開一個終端）
ollama serve                    # 終端 1（若已作為服務運行可跳過）
node server_v2_fixed.js         # 終端 2
python app.py                   # 終端 3

# 切換 LLM 模型
ollama pull qwen2.5:7b

# 查看日誌
Get-Content logs\app.log -Tail 50 -Wait

# 清除生成的地圖檔案
Remove-Item maps\* -Recurse -Force
```

### LLM 模型管理

```bash
ollama list                     # 列出已下載的模型
ollama pull llama3.2:3b         # 下載模型
ollama pull qwen2.5:7b          # 中文能力較強
ollama pull llama3.1:8b         # 支援 Function Calling
ollama rm <model-name>          # 刪除模型
```

| 模型 | 大小 | 速度 | 中文 | Function Calling |
|------|------|------|------|-----------------|
| `llama3.2:3b` | 2 GB | 快速 | 良好 | 支援 |
| `qwen2.5:7b` | 4.7 GB | 中等 | 優秀 | 支援 |
| `llama3.1:8b` | 4.7 GB | 中等 | 良好 | 支援 |
| `mistral:7b` | 4.1 GB | 中等 | 一般 | 支援 |
| `llama3.1:70b` | 40 GB | 較慢 | 良好 | 支援 |

---

## 7. Docker 部署（方法 B：Docker Compose）

### 7.1 前置準備

確保已安裝 Docker Desktop（Windows/Mac）或 Docker Engine + Docker Compose（Linux）。

### 7.2 啟動

**Linux / macOS / WSL2：**
```bash
# 首次啟動（建置 image + 啟動容器，約 3-5 分鐘）
docker compose up -d

# 下載 LLM 模型（首次必做，約 1-2 分鐘）
docker compose exec ollama ollama pull llama3.2:3b

# 查看日誌
docker compose logs -f

# 停止
docker compose down
```

**Windows PowerShell：**
```powershell
# 首次啟動
docker compose up -d

# 下載 LLM 模型
docker compose exec ollama ollama pull llama3.2:3b

# 查看日誌
docker compose logs -f

# 停止
docker compose down
```

啟動後瀏覽器前往 **http://localhost:5000**。

### 7.3 docker-compose.yml

檔案位於專案根目錄，包含三個服務：`flask-app`、`node-api`、`ollama`。

**Ports 映射：**

| 服務 | 容器內 Port | 主機 Port |
|------|-----------|----------|
| flask-app | 5000 | 5000 |
| node-api | 3000 | 3000 |
| ollama | 11434 | 11434 |

**Volumes 持久化：**

| Volume | 用途 |
|--------|------|
| `ollama_data` | Ollama 模型檔案（避免重複下載） |
| `./tiles` | 離線地圖圖磚 |
| `./logs` | 應用日誌 |
| `./scenarios` | 場景存檔 |
| `./geojson_layers` | 使用者自訂 GeoJSON 圖層 |

### 7.4 GPU 加速（可選）

若主機有 NVIDIA GPU 並安裝了 NVIDIA Container Toolkit，`docker-compose.yml` 的 `ollama` 服務已包含 GPU 設定（`deploy.resources.reservations.devices`）。若無 GPU，Ollama 會自動退回 CPU 模式，不需修改任何設定。

---

## 8. Troubleshooting

### 8.1 Ollama Function Calling / Tool Call 不穩定

**症狀**：LLM 有時回傳純文字而非 tool call，或 `arguments` 變成 JSON schema 而非實際參數值。

**解法**：
- 系統已內建 `FallbackHandler`，當 LLM 的 tool call 失敗時會自動退回規則匹配
- 切換到支援 tools 較穩定的模型：`qwen2.5:7b` 或 `llama3.1:8b`
- 在 `system_config.json` 修改 `llm_settings.providers.ollama.default_model`
- 重啟 Flask

### 8.2 LLM 回傳的 arguments 變成 schema 定義

**症狀**：Ollama 回傳的 `arguments` 內容是 `{"type":"object","properties":...}` 而非 `{"scenario_id":"1","enemy_ships":[...]}`。

**解法**：
- 這是某些 Ollama 模型的已知問題
- 後端 `FallbackHandler` 會自動攔截並改用規則匹配
- 建議模型：`llama3.2:3b`（此問題較少）或 `qwen2.5:7b`

### 8.3 roc_ships 為空陣列 `[]` 但全部船艦都被畫出

**症狀**：匯入場景時 `roc_ships: []` 但我方船艦全部出現在地圖上。

**解法**：
- 這是 Node.js API 的正確行為：當 `roc` 為空陣列時，回傳資料庫中所有我方船艦
- 若只想匯入指定船艦，需在自然語言中明確列出船艦名稱
- 例：「匯入場景一，我方包含成功級、康定級」

### 8.4 CORS 錯誤

**症狀**：瀏覽器 Console 出現 `Access-Control-Allow-Origin` 錯誤。

**解法**：
- Flask 已啟用 `flask-cors`，預設允許 `http://localhost:5000` 和 `http://127.0.0.1:5000`
- 若從其他 port 存取，在 `.env` 設定：
  ```bash
  CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000,http://localhost:8080
  ```
- Node.js API (`server_v2_fixed.js`) 已設定 `Access-Control-Allow-Origin: *`

### 8.5 Port 被佔用

**症狀**：`Address already in use: port 5000` 或 `EADDRINUSE: port 3000`。

**Windows PowerShell：**
```powershell
# 查看佔用 port 的程序
netstat -ano | findstr :5000
netstat -ano | findstr :3000

# 結束佔用程序（替換 <PID>）
taskkill /PID <PID> /F
```

**Linux / macOS：**
```bash
lsof -i :5000
lsof -i :3000
kill -9 <PID>
```

也可改用其他 port：
```bash
FLASK_PORT=8080 python app.py
```

### 8.6 Windows 終端亂碼 / cp950 編碼問題

**症狀**：終端出現 `UnicodeEncodeError: 'cp950' codec can't encode character`。

**解法**：
- `app.py` 已內建 UTF-8 編碼修正（第 19-24 行），正常情況不需處理
- 若仍有問題：
  ```powershell
  chcp 65001
  $env:PYTHONIOENCODING="utf-8"
  python app.py
  ```

### 8.7 Ollama 模型不存在

**症狀**：Flask 啟動後呼叫 LLM 回傳 `model "xxx" not found`。

**解法**：
```bash
# 確認模型已下載
ollama list

# 下載預設模型
ollama pull llama3.2:3b

# 確認 Ollama 正在運行
curl http://localhost:11434/api/tags
```

### 8.8 LLM 請求 Timeout

**症狀**：匯入場景或查詢時等很久後回傳 timeout 錯誤。

**解法**：
- 預設超時 300 秒（5 分鐘），可在 `.env` 調整：
  ```bash
  LLM_API_TIMEOUT=600
  ```
- 較大模型（如 `llama3.1:70b`）推理較慢，建議增加超時
- 確認 Ollama 未被其他程序佔用 GPU/記憶體
- 在 `system_config.json` 中 `providers.ollama.timeout` 也可調整

### 8.9 離線圖磚 (tiles/) 找不到 / 地圖底圖空白

**症狀**：地圖底圖顯示灰色空白區塊。

**解法**：
- 確認 `tiles/` 目錄存在且包含子目錄（`osm/`、`carto_dark/`、`esri_satellite/`）
- 圖磚格式：`tiles/{圖層名}/{z}/{x}/{y}.png`
- 若無離線圖磚，系統在**連網狀態**下會自動使用線上圖磚（OpenStreetMap 等）
- 取得離線圖磚：從現有部署環境複製整個 `tiles/` 目錄

### 8.10 Node.js API 無回應 / db_v2.json 找不到

**症狀**：Flask 呼叫 Node.js API 回傳 connection refused 或 500 錯誤。

**解法**：
```bash
# 確認 Node.js 正在運行
curl http://localhost:3000/health

# 確認 db_v2.json 和 track_data.json 存在於專案根目錄
ls db_v2.json track_data.json     # Linux
dir db_v2.json,track_data.json    # Windows

# 重新啟動 Node.js
node server_v2_fixed.js
```

### 8.11 Docker 中 Ollama 連線失敗

**症狀**：Docker 容器內 Flask 無法連接 Ollama。

**解法**：
- Docker Compose 中服務之間使用服務名稱通訊，不是 `localhost`
- `docker-compose.yml` 已正確設定環境變數：`OLLAMA_URL=http://ollama:11434/api/chat`
- 確認 Ollama 容器已啟動：`docker compose ps`
- 確認模型已下載：`docker compose exec ollama ollama list`

### 8.12 場景匯入後地圖未更新

**症狀**：API 回傳成功但 iframe 未刷新。

**解法**：
- 確認回應中 `map_url` 欄位有值且可存取
- 嘗試硬重整瀏覽器：`Ctrl + Shift + R`
- 檢查 `maps/` 目錄是否有對應的 HTML 檔案
- 查看 Flask 日誌是否有錯誤：`logs/app.log`

---

## 9. 驗證 Checklist

完成部署後，依序執行以下檢查。全部通過 = 部署成功。

### 9.1 服務健康檢查

```bash
# 1. Ollama 運行中（應回傳含模型列表的 JSON）
curl http://localhost:11434/api/tags

# 2. Node.js API 運行中（應回傳 {"status":"ok",...}）
curl http://localhost:3000/health

# 3. Flask 運行中（應回傳 HTML 頁面）
curl -s http://localhost:5000/ | head -5
```

### 9.2 核心功能測試

```bash
# 4. 場景匯入（應回傳 {"status":"success","map_url":"/maps/...","answer":"..."}）
curl -X POST http://localhost:5000/api/import_scenario \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: test-deploy" \
  -d '{"user_input": "匯入場景一"}'

# 5. 武器分派查詢（應回傳含 table_html 的 JSON）
curl -X POST http://localhost:5000/api/get_wta \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: test-deploy" \
  -d '{"user_input": "查詢武器分派"}'

# 6. 地圖檔案可存取（替換為步驟 4 回傳的 map_url）
curl -s http://localhost:5000/maps/test-deploy.html | head -5
```

**Windows PowerShell 版本：**
```powershell
# 1. Ollama
Invoke-RestMethod http://localhost:11434/api/tags

# 2. Node.js
Invoke-RestMethod http://localhost:3000/health

# 3. Flask
(Invoke-WebRequest http://localhost:5000/).Content.Substring(0, 200)

# 4. 場景匯入
$body = '{"user_input": "匯入場景一"}'
$headers = @{ "Content-Type" = "application/json"; "X-Client-ID" = "test-deploy" }
Invoke-RestMethod -Uri http://localhost:5000/api/import_scenario -Method Post -Body $body -Headers $headers

# 5. 武器分派
$body = '{"user_input": "查詢武器分派"}'
Invoke-RestMethod -Uri http://localhost:5000/api/get_wta -Method Post -Body $body -Headers $headers
```

### 9.3 預期畫面

在瀏覽器 http://localhost:5000 應看到：
- 左側：聊天側邊欄（含輸入框、設定按鈕）
- 右側：地圖區域（Leaflet 地圖，預設中心台灣海峽 `[23.5, 120.5]`）
- 輸入「匯入場景一」後，地圖上出現敵我船艦標記（紅色菱形 = 敵方、藍色圓形 = 我方）

---

## 10. 專案目錄結構

```
map - 20260302_v3/
├── app.py                      # Flask 應用入口
├── config.py                   # 全域配置（環境變數 + 預設值）
├── server_v2_fixed.js          # Node.js 本地 API 伺服器
├── setup.sh                    # 自動部署腳本
├── requirements.txt            # Python 依賴
├── .env.example                # 環境變數範本
├── .env                        # 實際環境變數（不進版控）
├── config.json                 # 執行時配置（啟動時重置為預設值）
├── system_config.json          # 系統配置：API 模式 + LLM Provider（不進版控）
├── prompts_config.json         # LLM System Prompt + Function Calling 定義
├── ship_registry.json          # 船艦資料庫（陣營關鍵字來源）
├── db_v2.json                  # 船艦 + 場景 + WTA 資料（Node.js API 使用）
├── track_data.json             # 船艦航跡座標資料
├── docker-compose.yml          # Docker Compose 部署配置
├── Dockerfile                  # Flask 應用 Docker 映像
│
├── models/                     # 資料模型
│   └── map_state.py            #   MapState：會話級地圖狀態管理、Folium HTML 生成
├── services/                   # 業務邏輯
│   ├── llm_service.py          #   LLM 呼叫封裝（Ollama / OpenAI / Anthropic）
│   ├── api_mode_service.py     #   API 模式切換（local / mock / real）
│   ├── map_service.py          #   地圖繪製邏輯（船艦標記、攻擊線、航跡）
│   └── config_loader.py        #   配置載入服務
├── routes/                     # Flask 路由藍圖（12 個）
│   ├── scenario_routes.py      #   /api/import_scenario, /api/star_scenario, /api/clear_map
│   ├── data_routes.py          #   /api/get_wta, /api/get_track, /api/check_simulation_status
│   ├── answer_routes.py        #   /api/get_answer
│   ├── cop_routes.py           #   /api/save_cop
│   ├── stream_routes.py        #   /api/stream_answer (SSE)
│   ├── layer_routes.py         #   /api/layers (CRUD)
│   ├── scenario_save_routes.py #   /api/save_scenario, /api/load_scenario
│   ├── ship_routes.py          #   /api/ships
│   └── ...                     #   feedback, prompt, admin, static
├── handlers/                   # 處理器
│   └── fallback_handler.py     #   LLM 失敗時的規則匹配
├── utils/                      # 工具
│   ├── helpers.py              #   會話管理（get_client_id, get_map_state）
│   ├── parser.py               #   參數解析修正（經緯度正規化、陣營判斷）
│   └── logger.py               #   日誌系統
│
├── templates/
│   └── index.html              # 前端主頁面（UI 佈局、側邊欄、地圖容器）
├── static/
│   ├── js/
│   │   ├── main.js             #   前端入口（Application class，初始化 15 個 managers）
│   │   ├── milsymbol.js        #   軍事符號庫（NATO APP-6 標準）
│   │   └── modules/            #   15 個前端模組（api-client, map-manager, ui-manager...）
│   ├── css/style.css           #   樣式表
│   └── cesium/                 #   Cesium 3D 資源（不進版控，~134 MB）
│
├── tiles/                      # 離線地圖圖磚（osm/, carto_dark/, esri_satellite/）
├── scenarios/                  # 場景存檔
├── geojson_layers/             # 使用者自訂 GeoJSON/KML 圖層
├── mock_responses/             # Mock 模式用的 JSON 回應檔案
├── maps/                       # 生成的地圖 HTML（自動建立，不進版控）
├── cops/                       # COP 截圖（自動建立，不進版控）
├── feedbacks/                  # 使用者反饋（自動建立，不進版控）
└── logs/                       # 應用日誌
```

---

## 11. 安全注意

- **`.env` 檔案不可上傳至版控**（已在 `.gitignore` 中排除），其中可能包含 API Keys
- **`system_config.json` 不可上傳至版控**（已在 `.gitignore` 中排除），其中可能包含 API 端點資訊
- 不要在程式碼中寫死 API Keys 或密碼，一律透過環境變數或 `system_config.json` 管理
- `config.json` 中的 `google_maps_api_key` 和 `cesium_ion_token` 僅在使用對應服務時才需要填入，不用時保持空字串
- 部署到公網時，建議：
  - 關閉 Flask debug 模式：`ENV=production` 或 `FLASK_DEBUG=False`
  - 限制 CORS 來源：設定 `CORS_ORIGINS` 為實際域名
  - 使用 reverse proxy（Nginx）而非直接暴露 Flask

---

## 12. License / Contact

**License**：<!-- 待定，請填入適用的授權條款 -->

**維護團隊**：軍事兵推 AI 系統團隊

**技術文件**：
- [ARCHITECTURE.md](ARCHITECTURE.md) — 完整系統架構與資料流
- [DO_NOT_TOUCH.md](DO_NOT_TOUCH.md) — 核心禁改清單
- [CLAUDE.md](CLAUDE.md) — AI 輔助開發規範

---

**版本**：v6.0 | **更新日期**：2026-03-04
