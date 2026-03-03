# ARCHITECTURE.md - 軍事兵推 AI 系統架構文件

> 本文件描述系統的完整架構、資料流、分層責任與技術實作細節。
> 基於實際程式碼分析生成，確保與現有實作完全一致。

---

## 一、系統總覽

### 1.1 技術堆疊
- **後端框架**：Flask (Python 3.10+)
- **前端**：原生 JavaScript (ES6 Modules)
- **地圖引擎**：
  - Folium (2D 地圖，基於 Leaflet)
  - Cesium (3D 地球儀)
- **LLM 支援**：
  - Ollama (本地部署)
  - OpenAI API
  - Anthropic Claude API
- **軍事符號**：milsymbol.js (NATO APP-6 標準)
- **API 通訊**：RESTful API + Server-Sent Events (SSE)

### 1.2 專案結構
```
map - 20260302_v3/
├── app.py                      # Flask 應用入口 (93 行)
├── config.py                   # 全域配置 (368 行)
├── config.json                 # 執行時配置
├── system_config.json          # 系統層級配置 (API 模式)
├── prompts_config.json         # LLM Prompt 配置
├── models/                     # 資料模型層
│   └── map_state.py            # 地圖狀態管理 (1519 行)
├── services/                   # 業務邏輯層
│   ├── llm_service.py          # LLM 呼叫封裝
│   ├── api_mode_service.py     # API 模式切換 (179 行)
│   ├── map_service.py          # 地圖繪製邏輯
│   └── config_loader.py        # 配置載入服務
├── routes/                     # 路由層 (12 個 Blueprints)
│   ├── __init__.py             # 藍圖註冊 (72 行)
│   ├── scenario_routes.py      # 場景管理 (425 行)
│   ├── data_routes.py          # 資料查詢
│   ├── answer_routes.py        # RAG 問答
│   ├── feedback_routes.py      # 反饋管理
│   ├── cop_routes.py           # COP 管理
│   ├── prompt_routes.py        # Prompt 管理
│   ├── admin_routes.py         # 系統管理
│   ├── stream_routes.py        # SSE 串流
│   ├── layer_routes.py         # 圖層管理
│   ├── scenario_save_routes.py # 場景儲存/載入
│   ├── ship_routes.py          # 船艦管理
│   └── static_routes.py        # 靜態檔案服務
├── handlers/                   # 處理器層
│   └── fallback_handler.py     # LLM 失敗處理
├── utils/                      # 工具層
│   ├── helpers.py              # 會話管理
│   ├── parser.py               # 參數解析修正
│   └── logger.py               # 日誌系統
├── templates/                  # HTML 模板
│   └── index.html              # 主頁面 (424 行)
└── static/                     # 靜態資源
    ├── js/
    │   ├── main.js             # 前端入口 (482 行)
    │   ├── milsymbol.js        # 軍事符號庫
    │   └── modules/            # 15 個前端模組
    │       ├── api-client.js           # API 客戶端
    │       ├── map-manager.js          # 地圖管理
    │       ├── ui-manager.js           # UI 操作
    │       ├── message-manager.js      # 訊息顯示
    │       ├── file-manager.js         # 檔案上傳
    │       ├── prompt-manager.js       # Prompt 管理
    │       ├── feedback-manager.js     # 反饋管理
    │       ├── cop-manager.js          # COP 管理
    │       ├── settings-manager.js     # 設定管理
    │       ├── simulation-manager.js   # 模擬狀態輪詢
    │       ├── cesium-manager.js       # Cesium 3D 地球儀
    │       ├── layer-manager.js        # 圖層管理
    │       ├── search-manager.js       # 搜尋功能
    │       ├── scenario-save-manager.js # 場景儲存
    │       └── ship-panel-manager.js   # 船艦面板
    └── css/
        └── style.css           # 樣式表
```

---

## 二、完整資料流

### 2.1 場景匯入流程（/api/import_scenario）
```
1. 前端（api-client.js）
   ↓ 用戶輸入「匯入場景」指令
   ↓ API 客戶端自動注入 X-Client-ID Header
   ↓
2. Flask 路由層（routes/scenario_routes.py）
   ↓ @scenario_bp.route('/api/import_scenario', methods=['POST'])
   ↓ 提取 client_id = request.headers.get('X-Client-ID')
   ↓ 獲取 map_state = get_map_state(client_id)
   ↓
3. LLM 服務層（services/llm_service.py）
   ↓ call_import_scenario(user_input)
   ↓ 載入 prompts_config.json 的 system_prompt
   ↓ _call_with_provider() 依據 provider 呼叫對應 API
   │   ├─ Ollama：POST http://localhost:11434/api/chat
   │   ├─ OpenAI：openai.ChatCompletion.create()
   │   └─ Anthropic：anthropic.messages.create()
   ↓ 返回 {"tool": "import_scenario", "parameters": {...}}
   ↓ 若 LLM 失敗 → FallbackHandler.handle_import_scenario_fallback()
   ↓
4. 參數清理層（routes/scenario_routes.py: 101-220 行）
   ↓ 使用 ENEMY_KEYWORDS 和 ROC_KEYWORDS 判斷陣營
   ↓ 自動修正 LLM 誤分類的船艦
   ↓ 去重、移除空值、正規化經緯度格式
   ↓
5. API 模式切換層（services/api_mode_service.py）
   ↓ APIModeService.call_api('import_scenario', json_data)
   │   ├─ real: 呼叫中科院真實 API
   │   ├─ local: 呼叫本地 Node.js server
   │   └─ mock: 從 mock_responses/ 讀取 JSON
   ↓
6. 地圖服務層（services/map_service.py）
   ↓ mark_ships_from_scenario(map_state, enemy_ships, roc_ships)
   ↓ 使用 milsymbol.js 生成軍事符號圖示
   ↓ 敵方：紅色菱形 (LAYER_SCENARIO)
   ↓ 我方：藍色圓形 (LAYER_SCENARIO)
   ↓
7. MapState 更新（models/map_state.py）
   ↓ map_state.markers[LAYER_SCENARIO] 新增標記資料
   ↓ map_state.scenario_data 儲存原始資料
   ↓ map_state.create_map() 生成 Folium HTML
   ↓ 儲存至 maps/{client_id}.html
   ↓
8. 返回 JSON 響應
   ↓ {"status": "success", "map_url": "/maps/{client_id}.html", "answer": "..."}
   ↓
9. 前端渲染（map-manager.js）
   ↓ iframe.src = map_url
   ↓ message-manager.js 顯示成功訊息
```

### 2.2 武器分派查詢流程（/api/get_wta）
```
1. 前端 API 客戶端（注入 X-Client-ID）
   ↓
2. routes/data_routes.py: @data_bp.route('/api/get_wta')
   ↓ 提取 client_id 和 user_input
   ↓
3. LLM 服務層
   ↓ call_get_wta(user_input)
   ↓ Function Calling 提取 scenario_id
   ↓ 失敗時 → FallbackHandler.handle_get_wta_fallback()
   ↓
4. API 模式切換
   ↓ APIModeService.call_api('get_wta', {"scenario_id": ...})
   │   ├─ real: POST {real_api_url}/get_wta
   │   ├─ local: POST http://localhost:3000/api/v1/get_wta
   │   └─ mock: 讀取 mock_responses/get_wta_response.json
   ↓
5. 地圖服務層
   ↓ draw_wta_arrows(map_state, wta_data)
   ↓ 依據飛彈類型從 WEAPON_COLORS 取得顏色
   ↓ 繪製攻擊線段 (LAYER_WTA)
   ↓ 若 enable_animation=true → 生成動畫資料
   ↓
6. MapState 更新
   ↓ map_state.lines[LAYER_WTA] 新增線段
   ↓ map_state.wta_animation_data 儲存動畫資料
   ↓ create_map() 嵌入動畫控制器 JavaScript
   ↓
7. 返回 JSON
   ↓ {"status": "success", "map_url": "...", "table_html": "...", "answer": "..."}
   ↓
8. 前端渲染
   ↓ 更新地圖 iframe
   ↓ 顯示 WTA 表格
   ↓ 若有動畫 → 控制器顯示播放/暫停按鈕
```

### 2.3 航跡繪製流程（/api/get_track）
```
1. 前端 API 客戶端
   ↓
2. routes/data_routes.py: @data_bp.route('/api/get_track')
   ↓
3. LLM 服務層
   ↓ call_get_track(user_input)
   ↓ 提取 {"ship_name": "...", "track_type": "..."}
   ↓
4. API 模式切換
   ↓ APIModeService.call_api('get_track', params)
   │   ├─ local: 從 track_data.json 讀取
   │   ├─ real: 呼叫真實 API
   │   └─ mock: 讀取 mock 回應
   ↓
5. 地圖服務層
   ↓ draw_track_line(map_state, track_points)
   ↓ 繪製航跡線段 (LAYER_TRACKS)
   ↓ 顏色：藍色（我方）或紅色（敵方）
   ↓
6. MapState 更新
   ↓ map_state.tracks[LAYER_TRACKS] 新增航跡
   ↓
7. 返回 JSON + 前端渲染
```

### 2.4 RAG 問答流程（/api/get_answer）
```
1. 前端 API 客戶端
   ↓
2. routes/answer_routes.py: @answer_bp.route('/api/get_answer')
   ↓
3. LLM 服務層
   ↓ call_get_answer(user_input)
   ↓ 使用 RAG 的 system_prompt（不使用 Function Calling）
   ↓ 直接返回文字回應
   ↓
4. 若是串流模式（/api/stream_answer）
   ↓ routes/stream_routes.py: @stream_bp.route('/api/stream_answer')
   ↓ APIModeService.call_api_stream('get_answer', ...)
   ↓ yield data: {text} (SSE 格式)
   ↓
5. 返回純文字或 SSE 串流
```

---

## 三、分層責任（Separation of Concerns）

### 3.1 嚴格分層原則

| 層級 | 只負責 | 絕對不做 |
|------|--------|---------|
| **LLM 層** | 意圖理解 + 參數提取（Function Calling） | 商業邏輯、資料驗證、地圖繪製、資料正規化 |
| **Backend 層** | 驗證/正規化/重試/串接 API/生成地圖 | 前端互動、UI 邏輯 |
| **Frontend 層** | UI、事件綁定、顯示、互動（Leaflet 層） | 資料正規化、商業邏輯 |

**禁止違反分層原則：**
- ❌ 不得把 Backend 的資料正規化丟到前端做
- ❌ 不得把前端互動塞回 LLM prompt 亂做
- ❌ 不得讓 LLM 處理本應由 Backend 負責的邏輯

### 3.2 細部責任對照

| 層級/模組 | 負責內容 | 不負責內容 |
|----------|---------|-----------|
| **LLM Service** | Function Calling 參數提取、Provider 切換 | 參數驗證、資料清理 |
| **FallbackHandler** | LLM 失敗時的規則匹配 | 複雜邏輯判斷 |
| **routes/*.py** | 請求驗證、參數清理、流程控制、回應組裝 | 地圖繪製細節 |
| **services/map_service.py** | 船艦標記、攻擊線、航跡的繪製邏輯 | 狀態儲存 |
| **models/map_state.py** | 會話級狀態管理、圖層管理、Folium HTML 生成 | API 呼叫 |
| **services/api_mode_service.py** | API 模式切換（real/local/mock） | 資料解析 |
| **handlers/fallback_handler.py** | 規則匹配、關鍵字提取 | API 呼叫 |
| **utils/helpers.py** | 會話管理（get_client_id、get_map_state） | 業務邏輯 |
| **前端 JS modules** | UI 操作、API 呼叫封裝、地圖 iframe 管理 | 地圖內容生成 |

---

## 四、核心機制

### 4.1 會話隔離機制
**實作位置**：
- 前端：`static/js/modules/api-client.js`
- 後端：`utils/helpers.py`

**流程**：
```javascript
// 前端：生成 client_id
export class APIClient {
    constructor() {
        this.initClientId();
        this.setupFetchHook();
    }

    initClientId() {
        let clientId = sessionStorage.getItem('client_id');
        if (!clientId) {
            clientId = 'client-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('client_id', clientId);
        }
        this.clientId = clientId;
    }

    setupFetchHook() {
        const originalFetch = window.fetch;
        const clientId = this.clientId;

        window.fetch = function(url, options = {}) {
            options.headers = options.headers || {};
            options.headers['X-Client-ID'] = clientId;  // 注入 Header
            return originalFetch(url, options);
        };
    }
}
```

```python
# 後端：提取 client_id 並隔離狀態
# utils/helpers.py
_STATES = {}  # 全域字典，key=client_id, value=MapState 實例

def get_client_id():
    """從 X-Client-ID Header 或 request body 提取 client_id"""
    client_id = request.headers.get('X-Client-ID')
    if not client_id:
        data = request.get_json(silent=True) or {}
        client_id = data.get('client_id')
    return client_id or 'default-session'

def get_map_state(client_id=None):
    """根據 client_id 獲取或創建 MapState 實例"""
    if client_id is None:
        client_id = get_client_id()

    if client_id not in _STATES:
        # 超過上限時清理最久未使用的會話
        if len(_STATES) >= MAX_CONCURRENT_SESSIONS:
            oldest_key = min(_STATES.keys(), key=lambda k: _STATES[k].last_access_time)
            del _STATES[oldest_key]

        _STATES[client_id] = MapState(client_id)

    _STATES[client_id].last_access_time = time.time()
    return _STATES[client_id]
```

**關鍵特性**：
- 每個瀏覽器分頁擁有唯一的 `client_id`（存於 `sessionStorage`）
- 所有 API 請求自動注入 `X-Client-ID` Header
- 後端依據 `client_id` 隔離 `MapState` 實例
- 超過 `MAX_CONCURRENT_SESSIONS` (200) 時自動淘汰最久未使用

### 4.2 API 模式切換機制
**實作位置**：`services/api_mode_service.py`

**配置檔**：`system_config.json`
```json
{
  "api_mode": "local",  // "real" | "local" | "mock"
  "real_api": {
    "base_url": "https://real-api.example.com",
    "timeout": 300,
    "endpoints": {
      "import_scenario": "/import_scenario",
      "star_scenario": "/star_scenario",
      "get_wta": "/get_wta",
      "get_answer": "/get_answer",
      "get_track": "/get_track"
    }
  },
  "local_api": {
    "base_url": "http://localhost:3000/api/v1",
    "timeout": 300,
    "endpoints": {...}
  },
  "local_data": {
    "track_data_file": "track_data.json",
    "db_file": "db_v2.json",
    "mock_responses_dir": "mock_responses"
  }
}
```

**實作邏輯**：
```python
# services/api_mode_service.py
class APIModeService:
    @staticmethod
    def call_api(endpoint_key, json_data=None, method='POST'):
        api_mode = get_api_mode()  # 從 system_config.json 讀取

        if api_mode == 'real':
            return APIModeService._call_http_api(get_real_api_config(), ...)
        elif api_mode == 'local':
            return APIModeService._call_http_api(get_local_api_config(), ...)
        elif api_mode == 'mock':
            return APIModeService._get_mock_response(endpoint_key, json_data)
        else:
            # 預設回退到 local
            return APIModeService._call_http_api(get_local_api_config(), ...)

    @staticmethod
    def _call_http_api(api_config, endpoint_key, json_data, method):
        base_url = api_config['base_url']
        endpoint_path = api_config['endpoints'][endpoint_key]
        url = f"{base_url}{endpoint_path}"

        if method == 'POST':
            response = requests.post(url, json=json_data, timeout=timeout)
        elif method == 'GET':
            response = requests.get(url, params=json_data, timeout=timeout)

        return response

    @staticmethod
    def _get_mock_response(endpoint_key, json_data):
        mock_path = f"mock_responses/{endpoint_key}_response.json"
        with open(mock_path, 'r', encoding='utf-8') as f:
            mock_data = json.load(f)
        return _LocalResponse(200, mock_data)  # 模擬 requests.Response

class _LocalResponse:
    """模擬 requests.Response 的物件，讓 mock 模式的回應格式一致"""
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data
        self.text = json.dumps(data, ensure_ascii=False)

    def json(self):
        return self._data
```

### 4.3 三層地圖架構
**實作位置**：`models/map_state.py`

**圖層定義**：
```python
# config.py
LAYER_SCENARIO = 'scenario'   # 場景層：敵我船艦標記
LAYER_WTA = 'wta'             # 武器分派層：攻擊線 + 動畫
LAYER_TRACKS = 'tracks'       # 航跡層：軌跡線段
```

**MapState 結構**：
```python
# models/map_state.py
class MapState:
    def __init__(self, client_id):
        self.client_id = client_id
        self.last_access_time = time.time()

        # 三層資料儲存
        self.markers = {
            LAYER_SCENARIO: [],  # 船艦標記
            LAYER_WTA: [],
            LAYER_TRACKS: []
        }
        self.lines = {
            LAYER_SCENARIO: [],
            LAYER_WTA: [],       # 武器分派攻擊線
            LAYER_TRACKS: []     # 航跡線段
        }
        self.tracks = {
            LAYER_TRACKS: []     # 完整航跡資料
        }

        # 動畫資料
        self.wta_animation_data = []

        # 原始資料
        self.scenario_data = None
        self.wta_data = None

    def create_map(self):
        """生成 Folium HTML 地圖"""
        m = folium.Map(
            location=MAP_DEFAULT_CENTER,  # [23.5, 120.5]
            zoom_start=MAP_DEFAULT_ZOOM,  # 7
            tiles=None  # 使用自訂圖層
        )

        # 繪製場景層標記
        if self.markers[LAYER_SCENARIO]:
            scenario_layer = folium.FeatureGroup(name='場景')
            for marker in self.markers[LAYER_SCENARIO]:
                folium.Marker(...).add_to(scenario_layer)
            scenario_layer.add_to(m)

        # 繪製 WTA 層線段
        if self.lines[LAYER_WTA]:
            wta_layer = folium.FeatureGroup(name='武器分派')
            for line in self.lines[LAYER_WTA]:
                folium.PolyLine(...).add_to(wta_layer)
            wta_layer.add_to(m)

        # 繪製航跡層
        if self.tracks[LAYER_TRACKS]:
            track_layer = folium.FeatureGroup(name='航跡')
            for track in self.tracks[LAYER_TRACKS]:
                folium.PolyLine(...).add_to(track_layer)
            track_layer.add_to(m)

        # 嵌入動畫控制器（若有動畫資料）
        if self.wta_animation_data:
            animation_js = self._generate_animation_script()
            m.get_root().html.add_child(folium.Element(animation_js))

        # 儲存 HTML
        map_path = os.path.join(MAP_DIR, f'{self.client_id}.html')
        m.save(map_path)
        return map_path
```

**圖層控制**：
- Leaflet LayerControl 自動生成圖層開關
- 可單獨清除某一層（如 `clear_wta_layer()`）
- 互不影響，獨立管理

### 4.4 LLM Provider 抽象層
**實作位置**：`services/llm_service.py`

**支援的 Providers**：
- Ollama (本地部署)
- OpenAI API
- Anthropic Claude API

**配置檔**：`system_config.json`
```json
{
  "llm_provider": "ollama",  // "ollama" | "openai" | "anthropic"
  "ollama_config": {
    "base_url": "http://localhost:11434",
    "model": "llama3.1:70b"
  },
  "openai_config": {
    "api_key": "sk-...",
    "model": "gpt-4"
  },
  "anthropic_config": {
    "api_key": "sk-ant-...",
    "model": "claude-3-opus-20240229"
  }
}
```

**實作邏輯**：
```python
# services/llm_service.py
def _call_with_provider(system_prompt, user_input, tools=None):
    provider = get_llm_provider()  # 從 system_config.json 讀取

    if provider == 'ollama':
        response = requests.post(
            f"{ollama_base_url}/api/chat",
            json={
                "model": ollama_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "tools": tools,
                "stream": False
            }
        )
        return parse_ollama_response(response)

    elif provider == 'openai':
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            tools=tools if tools else None
        )
        return parse_openai_response(response)

    elif provider == 'anthropic':
        client = anthropic.Anthropic(api_key=anthropic_api_key)
        response = client.messages.create(
            model=anthropic_model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_input}],
            tools=tools if tools else None
        )
        return parse_anthropic_response(response)
```

**Function Calling 格式**：
```python
# prompts_config.json
{
  "import_scenario": {
    "system_prompt": "你是軍事兵推專家...",
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "import_scenario",
          "description": "匯入場景",
          "parameters": {
            "type": "object",
            "properties": {
              "scenario_id": {"type": "string"},
              "enemy_ships": {"type": "array"},
              "roc_ships": {"type": "array"}
            },
            "required": ["scenario_id"]
          }
        }
      }
    ]
  }
}
```

---

## 五、關鍵檔案速查

### 5.1 後端核心檔案

| 檔案 | 行數 | 用途 | 關鍵函式/類別 |
|------|------|------|--------------|
| `app.py` | 93 | Flask 應用入口 | `register_blueprints()`, `app.run()` |
| `config.py` | 368 | 全域配置 | 260+ 常數定義 |
| `models/map_state.py` | 1519 | 地圖狀態管理 | `MapState`, `create_map()` |
| `services/llm_service.py` | ~300 | LLM 呼叫封裝 | `call_import_scenario()`, `_call_with_provider()` |
| `services/api_mode_service.py` | 179 | API 模式切換 | `APIModeService.call_api()` |
| `services/map_service.py` | ~800 | 地圖繪製邏輯 | `mark_ships_from_scenario()`, `draw_wta_arrows()` |
| `routes/scenario_routes.py` | 425 | 場景相關 API | `/api/import_scenario`, 參數清理邏輯 (101-220 行) |
| `routes/data_routes.py` | ~500 | 資料查詢 API | `/api/get_wta`, `/api/get_track` |
| `routes/__init__.py` | 72 | 藍圖註冊 | `register_blueprints()` (註冊 12 個藍圖) |
| `handlers/fallback_handler.py` | ~400 | LLM 失敗處理 | `FallbackHandler.handle_xxx_fallback()` |
| `utils/helpers.py` | ~200 | 會話管理 | `get_client_id()`, `get_map_state()` |
| `utils/parser.py` | ~150 | 參數解析修正 | 經緯度正規化、陣營判斷 |

### 5.2 前端核心檔案

| 檔案 | 行數 | 用途 | 關鍵類別/函式 |
|------|------|------|--------------|
| `templates/index.html` | 424 | 主 HTML | UI 佈局、側邊欄、地圖容器 |
| `static/js/main.js` | 482 | 前端入口 | `Application` class, 初始化 15 個 managers |
| `static/js/milsymbol.js` | ~8000 | 軍事符號庫 | NATO APP-6 標準符號 |
| `static/js/modules/api-client.js` | ~200 | API 客戶端 | `APIClient`, `initClientId()`, `setupFetchHook()` |
| `static/js/modules/map-manager.js` | ~300 | 地圖管理 | `MapManager`, `loadMap()`, 地圖 iframe 管理 |
| `static/js/modules/ui-manager.js` | ~400 | UI 操作 | `UIManager`, 按鈕綁定、分隔線拖曳 |
| `static/js/modules/message-manager.js` | ~150 | 訊息顯示 | `MessageManager`, `showSuccess()`, `showError()` |
| `static/js/modules/simulation-manager.js` | ~200 | 模擬狀態輪詢 | `SimulationManager`, 輪詢 `/api/check_simulation_status` |
| `static/js/modules/cesium-manager.js` | ~500 | Cesium 3D 地球儀 | `CesiumManager`, `enable3DMode()`, `disable3DMode()` |
| `static/js/modules/layer-manager.js` | ~300 | 圖層管理 | `LayerManager`, 圖層 CRUD |
| `static/js/modules/search-manager.js` | ~200 | 搜尋功能 | `SearchManager`, 船艦搜尋定位 |
| `static/js/modules/scenario-save-manager.js` | ~250 | 場景儲存 | `ScenarioSaveManager`, 場景儲存/載入 |
| `static/js/modules/ship-panel-manager.js` | ~300 | 船艦面板 | `ShipPanelManager`, 船艦清單顯示 |

### 5.3 配置檔案

| 檔案 | 用途 | 關鍵欄位 |
|------|------|---------|
| `config.json` | 執行時配置 | `enable_animation`, `enable_3d_globe`, `cesium_offline_mode`, `custom_layers` |
| `system_config.json` | 系統層級配置 | `api_mode`, `llm_provider`, `real_api`, `local_api` |
| `prompts_config.json` | LLM Prompt 配置 | 各功能的 `system_prompt` 和 `tools` |
| `db_v2.json` | 系統資料庫 | 船艦、武器、場景資料 |
| `track_data.json` | 航跡資料 | 各船艦的軌跡座標 |

---

## 六、12 個 Flask Blueprints

| Blueprint 名稱 | 檔案 | 主要路由 | 用途 |
|---------------|------|---------|------|
| `scenario_bp` | `routes/scenario_routes.py` | `/api/import_scenario`, `/api/star_scenario`, `/api/clear_map` | 場景管理 |
| `data_bp` | `routes/data_routes.py` | `/api/get_wta`, `/api/get_track`, `/api/check_simulation_status` | 資料查詢 |
| `answer_bp` | `routes/answer_routes.py` | `/api/get_answer` | RAG 問答 |
| `feedback_bp` | `routes/feedback_routes.py` | `/api/submit_feedback`, `/api/get_feedback_list` | 反饋管理 |
| `cop_bp` | `routes/cop_routes.py` | `/api/save_cop`, `/cops/<filename>` | COP 管理 |
| `prompt_bp` | `routes/prompt_routes.py` | `/api/get_prompts_config`, `/api/save_prompts_config` | Prompt 管理 |
| `admin_bp` | `routes/admin_routes.py` | `/api/get_system_config`, `/api/save_system_config` | 系統管理 |
| `stream_bp` | `routes/stream_routes.py` | `/api/stream_answer` | SSE 串流 |
| `layer_bp` | `routes/layer_routes.py` | `/api/layers`, `/api/layers/<layer_id>` | 圖層管理 |
| `scenario_save_bp` | `routes/scenario_save_routes.py` | `/api/save_scenario`, `/api/load_scenario` | 場景儲存/載入 |
| `ship_bp` | `routes/ship_routes.py` | `/api/ships`, `/api/ships/<ship_name>` | 船艦管理 |
| `static_bp` | `routes/static_routes.py` | `/maps/<filename>`, `/` | 靜態檔案 |

---

## 七、15 個前端模組

| 模組名稱 | 檔案 | 用途 |
|---------|------|------|
| `APIClient` | `api-client.js` | API 客戶端，X-Client-ID 注入 |
| `MapManager` | `map-manager.js` | 地圖 iframe 管理 |
| `UIManager` | `ui-manager.js` | UI 操作、按鈕綁定 |
| `MessageManager` | `message-manager.js` | 訊息顯示（成功/錯誤） |
| `FileManager` | `file-manager.js` | 檔案上傳處理 |
| `PromptManager` | `prompt-manager.js` | Prompt 配置管理 |
| `FeedbackManager` | `feedback-manager.js` | 反饋提交與顯示 |
| `COPManager` | `cop-manager.js` | COP 截圖管理 |
| `SettingsManager` | `settings-manager.js` | 設定管理 |
| `SimulationManager` | `simulation-manager.js` | 模擬狀態輪詢 |
| `CesiumManager` | `cesium-manager.js` | Cesium 3D 地球儀 |
| `LayerManager` | `layer-manager.js` | 圖層 CRUD |
| `SearchManager` | `search-manager.js` | 船艦搜尋定位 |
| `ScenarioSaveManager` | `scenario-save-manager.js` | 場景儲存/載入 |
| `ShipPanelManager` | `ship-panel-manager.js` | 船艦面板顯示 |

---

## 八、動畫系統

### 8.1 配置
- **開關**：`config.json` 的 `enable_animation`
- **資料儲存**：`MapState.wta_animation_data`

### 8.2 實作邏輯
```python
# services/map_service.py
def draw_wta_arrows(map_state, wta_data):
    if load_config().get('enable_animation', False):
        animation_data = []
        for wta_item in wta_data:
            animation_data.append({
                'from': [wta_item['from_lat'], wta_item['from_lon']],
                'to': [wta_item['to_lat'], wta_item['to_lon']],
                'weapon': wta_item['weapon'],
                'color': WEAPON_COLORS.get(wta_item['weapon'], '#FF0000')
            })
        map_state.wta_animation_data = animation_data
```

### 8.3 前端控制器
嵌入 Folium HTML 的 JavaScript：
```javascript
// 動畫控制器（由 map_state.py 生成）
<script>
let animationPlaying = false;
let animationSpeed = 1;
let currentFrame = 0;
const animationData = [...];  // 從 Python 注入

function playAnimation() {
    animationPlaying = true;
    // 繪製飛彈飛行動畫
}

function pauseAnimation() {
    animationPlaying = false;
}

function setSpeed(speed) {
    animationSpeed = speed;
}
</script>
```

---

## 九、Cesium 3D 地球儀支援

### 9.1 配置
- **開關**：`config.json` 的 `enable_3d_globe`
- **離線模式**：`config.json` 的 `cesium_offline_mode`
- **Token**：`config.json` 的 `cesium_ion_token`（若使用線上模式）

### 9.2 實作位置
- 前端：`static/js/modules/cesium-manager.js`
- 後端：無需特殊處理（Cesium 完全在前端運作）

### 9.3 功能
- 2D/3D 模式切換
- 離線模式支援（本地 Cesium 資源）
- 標記同步（從 Folium 地圖提取座標）

---

## 十、自訂圖層管理

### 10.1 配置結構
```json
// config.json
{
  "custom_layers": [
    {
      "id": "layer_1772009340196",
      "name": "暗",
      "url_template": "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
      "attribution": "",
      "max_zoom": 18,
      "opacity": 1,
      "enabled": false
    },
    {
      "id": "layer_1772084352836",
      "type": "geojson",
      "name": "櫻花",
      "filename": "layer_1772084352836.geojson",
      "original_filename": "map.geojson",
      "style": {
        "color": "#ff3333",
        "weight": 2,
        "fill_color": "#ff3333",
        "fill_opacity": 0.2
      },
      "opacity": 1.0,
      "enabled": false
    }
  ]
}
```

### 10.2 API 路由
- `GET /api/layers`：取得圖層清單
- `POST /api/layers`：新增圖層
- `PUT /api/layers/<layer_id>`：更新圖層
- `DELETE /api/layers/<layer_id>`：刪除圖層

### 10.3 前端管理
- `LayerManager` 負責圖層 CRUD 操作
- 支援 Tile Layer 和 GeoJSON Layer

---

## 十一、配置重置機制

### 11.1 啟動時重置
```python
# app.py (59-68 行)
from services import load_config as _load_existing
_existing = _load_existing()
_reset_config = dict(CONFIG_DEFAULTS)

# 保留持久化設定
_persistent_keys = ["cesium_ion_token", "cesium_offline_mode", "custom_layers"]
for _key in _persistent_keys:
    if _key in _existing and _existing[_key]:
        _reset_config[_key] = _existing[_key]

save_config(_reset_config)
```

### 11.2 預設配置
```python
# config.py
CONFIG_DEFAULTS = {
    "show_source_btn": False,
    "enable_animation": True,
    "enable_3d_globe": True,
    "enable_measurement": True,
    "cesium_offline_mode": True,
    "cesium_ion_token": "",
    "google_maps_api_key": "",
    "custom_layers": []
}
```

---

**版本**：v6.0 (基於實際程式碼分析)
**更新日期**：2026-03-02
**維護團隊**：軍事兵推 AI 系統團隊
