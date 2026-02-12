# 系統與中科院 API 整合指南

> 本文件說明本系統與中科院 CMO API 之間的關係、資料流、POST/GET 使用原則，以及如何配合中科院進行對接。

---

## 一、系統角色：既是 Server 也是 Client

本系統的 Flask 後端同時扮演兩種角色：

| 角色 | 說明 | 對象 |
|------|------|------|
| **Server**（被動接收） | 前端瀏覽器呼叫你、中科院回調通知你 | 前端 JS、中科院 |
| **Client**（主動發出） | 你去呼叫中科院 API 取資料 | 中科院 CMO 系統 |

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│   前端瀏覽器  │──────→│   Flask 後端     │──────→│  中科院 API   │
│  (Client)    │←──────│ (Server+Client) │←──────│  (Server)    │
└─────────────┘       └─────────────────┘       └─────────────┘
                              ↑
                              │ 回調 (wta_completed)
                              │
                       ┌─────────────┐
                       │  中科院 CMO   │
                       │  (Client)    │
                       └─────────────┘
```

---

## 二、所有 API 端點分類與 POST/GET 對照

### A. Flask → 中科院（主動發出請求）

透過 `APIModeService.call_api()` 發出，端點定義於 `system_config.json`：

| # | 端點 | HTTP 方法 | 你送出的資料 | 中科院回傳的資料 | 為何用此方法 |
|---|------|----------|-------------|-----------------|-------------|
| 1 | `/import_scenario` | **POST** | `{ enemy: ["052D"], roc: ["成功級"] }` | 船艦座標 JSON | 送出 JSON body 查詢條件 |
| 2 | `/start_scenario` | **POST** | `{}` (空 body) | 確認訊息 | 觸發伺服端動作（啟動模擬） |
| 3 | `/get_wta` | **POST** | `{ enemy: ["052D"] }` | 武器分派結果 | 送出 JSON body 查詢條件 |
| 4 | `/get_track` | **POST** | 無特定參數 | 航跡數據 | 中科院端決定，目前用 POST |
| 5 | `/get_answer` | **POST** | `{ stream:0, model:"TAIDE8B", messages:[...] }` | RAG 回答 | 送出複雜 JSON body |

### B. 中科院 → Flask（被動接收回調）

| # | 你的端點 | HTTP 方法 | 中科院送來的資料 | 你回傳的資料 |
|---|---------|----------|-----------------|-------------|
| 6 | `/api/wta_completed` | **POST** | `{ message: "武器分派演算已完成" }` | `{ success: true, received: true }` |

> **這是唯一一個中科院會主動呼叫你的端點。** 中科院模擬跑完後，會 POST 通知你。

### C. 前端 → Flask（內部端點）

| # | 端點 | 方法 | 說明 | 會轉發到中科院？ |
|---|------|------|------|-----------------|
| 7 | `/api/import_scenario` | POST | 前端送指令 | **會** → 轉發到中科院 |
| 8 | `/api/start_scenario` | POST | 前端啟動模擬 | **會** → 通知中科院 |
| 9 | `/api/get_wta` | POST | 前端查 WTA | **會** → 向中科院取結果 |
| 10 | `/api/get_track` | POST | 前端查航跡 | **會** → 向中科院取資料 |
| 11 | `/api/get_answer` | POST | 前端問問題 | **會** → 向中科院 RAG 發問 |
| 12 | `/api/get_simulation_status` | **GET** | 前端輪詢模擬狀態 | **不會** — 讀本地狀態 |
| 13 | `/api/clear_map` | POST | 清除地圖 | **不會** — 純本地操作 |
| 14 | `/api/save_cop` | POST | 截圖 | **不會** |
| 15 | `/api/submit_feedback` | POST | 提交回饋 | **不會** |
| 16 | `/api/get_feedbacks` | **GET** | 讀取回饋 | **不會** |
| 17 | `/api/prompts/*` | GET/POST/DELETE | Prompt 管理 | **不會** |
| 18 | `/api/admin/settings` | GET/POST | 系統設定 | **不會** |
| 19 | `/health` | **GET** | 健康檢查 | **不會** |
| 20 | `/maps/<filename>` | **GET** | 取得地圖 HTML | **不會** |

---

## 三、POST vs GET 使用原則

### 通用原則

| 用 **GET** | 用 **POST** |
|-----------|------------|
| 純粹「讀取」資料 | 「送出資料」讓伺服器處理 |
| 參數簡單，可放在 URL query string | 參數複雜，需要 JSON body |
| 不會改變伺服器狀態 | 會觸發伺服器動作（啟動模擬、寫入資料等） |
| 可以被瀏覽器快取 | 不會被快取 |
| 有長度限制（URL 約 2048 字元） | 無長度限制 |

### 套用到本系統

```
GET 適用場景：
  ✅ 查狀態     → GET /api/get_simulation_status     （無參數，純讀取）
  ✅ 拿設定     → GET /api/admin/settings             （純讀取）
  ✅ 拿回饋清單 → GET /api/get_feedbacks              （純讀取）
  ✅ 拿靜態檔   → GET /maps/xxx.html                  （純讀取）
  ✅ 健康檢查   → GET /health                         （純讀取）

POST 適用場景：
  ✅ 匯入場景   → POST /import_scenario  （帶 JSON body: 船艦參數）
  ✅ 啟動模擬   → POST /start_scenario   （觸發伺服器動作）
  ✅ 查 WTA     → POST /get_wta          （帶 JSON body: 查詢條件）
  ✅ 查航跡     → POST /get_track        （可能帶參數）
  ✅ RAG 問答   → POST /get_answer       （帶 JSON body: messages）
  ✅ 回調通知   → POST /wta_completed    （帶 JSON body: 完成訊息）
  ✅ 清除地圖   → POST /clear_map        （改變伺服器狀態）
```

> **注意**：即使 `get_wta` 和 `get_track` 名字有 "get"，但因為需要送出 JSON body 作為查詢條件，所以用 **POST** 是正確的。HTTP 規範中 GET 不該帶 request body。

---

## 四、完整資料流時序圖

### 步驟 1：匯入場景

```
瀏覽器 ──POST /api/import_scenario──→ Flask ──POST /import_scenario──→ 中科院
瀏覽器 ←── 船艦座標 + 地圖 URL ────── Flask ←── 船艦座標 JSON ──────── 中科院
```

### 步驟 2：啟動模擬

```
瀏覽器 ──POST /api/start_scenario──→ Flask ──POST /start_scenario──→ 中科院
瀏覽器 ←── "模擬已啟動" ────────── Flask ←── 確認 ──────────────── 中科院
```

### 步驟 3：等待模擬完成（非同步）

```
瀏覽器 ──GET /api/get_simulation_status──→ Flask（前端輪詢，每隔數秒）
                                                  ↑
中科院 ──POST /api/wta_completed─────────────────→ Flask（模擬完成時回調）
```

### 步驟 4：查看 WTA 結果

```
瀏覽器 ──POST /api/get_wta──→ Flask ──POST /get_wta──→ 中科院
瀏覽器 ←── WTA 表格 + 地圖 ── Flask ←── WTA 結果 ───── 中科院
```

### 步驟 5：查看航跡

```
瀏覽器 ──POST /api/get_track──→ Flask ──POST /get_track──→ 中科院
瀏覽器 ←── 航跡地圖 ─────── Flask ←── 航跡數據 ──────── 中科院
```

### 步驟 6：RAG 問答

```
瀏覽器 ──POST /api/get_answer──→ Flask ──POST /get_answer──→ 中科院 RAG
瀏覽器 ←── AI 回答 + 來源 ──── Flask ←── RAG 回應 ──────── 中科院 RAG
```

### 完整流程串接

```
用戶操作順序：
  1. 匯入場景（POST import_scenario）  → 地圖出現船艦標記
  2. 啟動模擬（POST start_scenario）   → 中科院背景執行演算
  3. 等待完成（中科院 POST wta_completed 回調）
  4. 查看 WTA（POST get_wta）          → 地圖出現攻擊配對線
  5. 查看航跡（POST get_track）        → 地圖出現航行軌跡
  6. RAG 問答（POST get_answer）       → 軍事知識問答
```

---

## 五、配合中科院 Real API 的修改指南

### 5.1 最小改動（只改配置檔）

**只需修改 `system_config.json`：**

```json
{
  "api_settings": {
    "api_mode": "real",
    "real_api": {
      "base_url": "https://中科院的實際URL",
      "timeout": 300,
      "endpoints": {
        "import_scenario": "/中科院的實際路徑",
        "star_scenario": "/中科院的實際路徑",
        "get_wta": "/中科院的實際路徑",
        "get_answer": "/中科院的實際路徑",
        "get_track": "/中科院的實際路徑"
      }
    }
  }
}
```

### 5.2 需要跟中科院確認的事項

| # | 問題 | 為什麼要問 | 影響檔案 |
|---|------|-----------|---------|
| 1 | **各端點的確切路徑是什麼？** | 路徑可能不是 `/import_scenario` 而是 `/api/v1/scenario/import` | `system_config.json` |
| 2 | **各端點用 POST 還是 GET？** | 如果某些端點用 GET，需改 `call_api()` 的 method 參數 | `routes/*.py` |
| 3 | **Request Body 的 JSON 欄位名稱？** | 中科院可能要的不是 `{ enemy: [...] }` 而是 `{ target_ships: [...] }` | `routes/*.py` 參數組裝 |
| 4 | **Response Body 的 JSON 格式？** | 中科院回傳的可能不是 `{ wta_results: [...] }` 而是其他結構 | `routes/*.py` 回應解析 |
| 5 | **回調 URL 怎麼設定？** | 中科院怎麼知道要 POST 到你的 `/api/wta_completed`？ | 可能需在 start_scenario 時傳 callback URL |
| 6 | **是否需要認證？** | API Key、Token、或其他認證方式 | `services/api_mode_service.py` headers |
| 7 | **get_answer 的 RAG 請求格式？** | 目前送 `{ stream:0, model:"TAIDE8B", messages:[...] }` 是否正確 | `routes/answer_routes.py` |
| 8 | **你的伺服器 IP/Port？** | 中科院要能存取你的 `/api/wta_completed` 回調端點 | 網路/防火牆設定 |

### 5.3 情境：中科院端點改用 GET

如果中科院的 `get_track` 端點用 GET，只需改 route 裡的呼叫：

```python
# 原本（POST）：
res = APIModeService.call_api("get_track", method='POST')

# 改為 GET：
res = APIModeService.call_api("get_track", method='GET')
```

`APIModeService._call_http_api()` 已支援 GET，會自動將參數放到 query string：

```python
# services/api_mode_service.py 第 85-86 行
if method.upper() == 'GET':
    response = requests.get(url, params=json_data, ...)  # 參數變成 ?key=value
```

### 5.4 情境：中科院需要認證 Header

修改 `services/api_mode_service.py` 的 `_call_http_api()` 方法：

```python
headers = {'Content-Type': 'application/json'}

# 若中科院需要 API Key：
if 'mock.pstmn.io' not in base_url:  # 非 Mock 環境才加
    headers['Authorization'] = f'Bearer {API_KEY}'
    # 或
    headers['X-API-Key'] = API_KEY
```

### 5.5 情境：中科院的 Request/Response 格式不同

如果中科院的欄位名稱不同，需要在 route 層做**轉換層**：

```python
# 範例：import_scenario 的參數轉換
# 你的系統用 { enemy: [...], roc: [...] }
# 中科院要   { red_force: [...], blue_force: [...] }

api_params = {
    'red_force': params.get('enemy', []),
    'blue_force': params.get('roc', [])
}
res = APIModeService.call_api("import_scenario", api_params)

# 範例：回應轉換
# 中科院回傳 { red_ships: [...], blue_ships: [...] }
# 你的系統要 { enemy: [...], roc: [...] }

raw_data = res.json()
api_data = {
    'enemy': raw_data.get('red_ships', []),
    'roc': raw_data.get('blue_ships', [])
}
```

---

## 六、API 模式切換機制

### 切換方式

修改 `system_config.json` 的 `api_mode` 欄位：

| 模式 | 值 | 資料來源 | 用途 |
|------|---|---------|------|
| 真實 API | `"real"` | 中科院 CMO 系統（目前指向 Postman Mock） | 正式環境 / API 測試 |
| 本地 Node.js | `"local"` | `http://localhost:3000/api/v1` | 開發環境 |
| 離線 Mock | `"mock"` | `mock_responses/` 目錄的 JSON 檔案 | 純前端測試 |

### 切換流程

```
system_config.json
    ↓ 讀取 api_mode
APIModeService.call_api()
    ├─ "real"  → _call_http_api(real_api 配置)  → 中科院
    ├─ "local" → _call_http_api(local_api 配置) → Node.js
    └─ "mock"  → _get_mock_response()           → 本地 JSON
```

---

## 七、關鍵檔案速查

| 檔案 | 用途 | 何時需要改 |
|------|------|-----------|
| `system_config.json` | API 模式 + 端點 URL 配置 | 切換中科院 URL 時 |
| `services/api_mode_service.py` | 統一 API 呼叫入口 | 加認證 Header、改 HTTP 方法時 |
| `services/config_loader.py` | 讀取 system_config.json | 新增配置欄位時 |
| `routes/scenario_routes.py` | 匯入場景 + 啟動模擬 | Request/Response 格式不同時 |
| `routes/data_routes.py` | WTA 查詢 + 航跡 + 回調 | Request/Response 格式不同時 |
| `routes/answer_routes.py` | RAG 問答 | RAG API 格式不同時 |
| `static/js/modules/api-client.js` | 前端 API 封裝 | 一般不需改（格式轉換在後端做） |

---

## 八、給中科院的 API 規格說明（可直接提供）

### 你需要中科院提供的 API

| 端點 | 方法 | 你會送的 Request Body | 你期望收到的 Response |
|------|------|---------------------|---------------------|
| 匯入場景 | POST | `{ "enemy": ["052D", "遼寧號"], "roc": ["成功級"] }` | `{ "enemy": [{name, lat, lon, ...}], "roc": [{...}] }` |
| 啟動模擬 | POST | `{}` | `{ "success": true }` |
| 查詢 WTA | POST | `{ "enemy": ["052D"] }` | `{ "wta_results": [{attack_wave, weapon, roc_location, enemy_location, ...}] }` |
| 查詢航跡 | POST | `{}` | `{ "ship": { "enemy": {...}, "roc": {...} } }` |
| RAG 問答 | POST | `{ "stream": 0, "model": "TAIDE8B", "messages": [{role, content}] }` | `{ "messages": [{role, content}], "sources": [{chunk, score, path}] }` |

### 中科院需要呼叫你的 API

| 端點 | 方法 | 中科院送的 Request Body | 你會回傳的 Response |
|------|------|----------------------|---------------------|
| `/api/wta_completed` | POST | `{ "message": "武器分派演算已完成" }` | `{ "success": true, "received": true, "message": "已接收完成通知" }` |

> **重要**：中科院必須能存取你的伺服器 IP 和 Port 才能發送回調。
