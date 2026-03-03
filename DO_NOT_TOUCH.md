# DO_NOT_TOUCH.md - 核心禁改清單

> 本文件列出系統中「絕對不可隨意修改」的核心區域。
> 這些區域已經過充分測試，任何變動都可能導致系統崩潰或功能異常。
> **修改前必須徵得用戶明確同意。**

---

## 一、會話隔離機制（絕對禁改）

### 1.1 前端 client_id 生成與注入
**檔案**：`static/js/modules/api-client.js`
**禁改區域**：第 1-80 行（完整的 `APIClient` class）

**關鍵程式碼**：
```javascript
// 禁改：client_id 生成邏輯
initClientId() {
    let clientId = sessionStorage.getItem('client_id');
    if (!clientId) {
        clientId = 'client-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('client_id', clientId);
    }
    this.clientId = clientId;
}

// 禁改：X-Client-ID Header 自動注入
setupFetchHook() {
    const originalFetch = window.fetch;
    const clientId = this.clientId;

    window.fetch = function(url, options = {}) {
        options.headers = options.headers || {};
        options.headers['X-Client-ID'] = clientId;
        return originalFetch(url, options);
    };
}
```

**為什麼不能改**：
- 整個系統依賴 `X-Client-ID` Header 來隔離會話
- 改變 client_id 格式會導致所有 API 請求失效
- `sessionStorage` 是唯一的會話識別來源

### 1.2 後端 client_id 提取與狀態管理
**檔案**：`utils/helpers.py`
**禁改區域**：`get_client_id()` 和 `get_map_state()` 函式

**關鍵程式碼**：
```python
# 禁改：全域狀態字典
_STATES = {}  # key=client_id, value=MapState 實例

# 禁改：client_id 提取邏輯
def get_client_id():
    client_id = request.headers.get('X-Client-ID')
    if not client_id:
        data = request.get_json(silent=True) or {}
        client_id = data.get('client_id')
    return client_id or 'default-session'

# 禁改：MapState 獲取邏輯
def get_map_state(client_id=None):
    if client_id is None:
        client_id = get_client_id()

    if client_id not in _STATES:
        if len(_STATES) >= MAX_CONCURRENT_SESSIONS:
            oldest_key = min(_STATES.keys(), key=lambda k: _STATES[k].last_access_time)
            del _STATES[oldest_key]

        _STATES[client_id] = MapState(client_id)

    _STATES[client_id].last_access_time = time.time()
    return _STATES[client_id]
```

**為什麼不能改**：
- `_STATES` 字典是唯一的會話隔離機制
- 改變提取邏輯會導致會話混亂
- 會話清理機制保護系統資源

---

## 二、API 契約（絕對禁改）

### 2.1 路由路徑
**禁止修改以下路由路徑**：

| 路由 | 用途 | 前端調用位置 |
|------|------|-------------|
| `/api/import_scenario` | 場景匯入 | `api-client.js` |
| `/api/star_scenario` | 啟動模擬 | `api-client.js` |
| `/api/clear_map` | 清除地圖 | `api-client.js` |
| `/api/get_wta` | 武器分派查詢 | `api-client.js` |
| `/api/get_track` | 航跡繪製 | `api-client.js` |
| `/api/get_answer` | RAG 問答 | `api-client.js` |
| `/api/stream_answer` | SSE 串流問答 | `api-client.js` |
| `/api/check_simulation_status` | 模擬狀態輪詢 | `simulation-manager.js` |
| `/api/save_cop` | 儲存 COP 截圖 | `cop-manager.js` |
| `/api/submit_feedback` | 提交反饋 | `feedback-manager.js` |
| `/api/layers` | 圖層管理 | `layer-manager.js` |
| `/api/save_scenario` | 儲存場景 | `scenario-save-manager.js` |
| `/api/load_scenario` | 載入場景 | `scenario-save-manager.js` |
| `/api/ships` | 船艦管理 | `ship-panel-manager.js` |
| `/maps/<filename>` | 地圖文件服務 | `map-manager.js` |

**改動後果**：前端所有 API 呼叫失效。

### 2.2 請求參數名稱
**禁止修改以下參數名稱**：

```python
# /api/import_scenario
{
    "user_input": str,        # 禁改
    "scenario_id": str,       # 禁改
    "enemy_ships": list,      # 禁改
    "roc_ships": list         # 禁改
}

# /api/get_wta
{
    "user_input": str,        # 禁改
    "scenario_id": str        # 禁改
}

# /api/get_track
{
    "user_input": str,        # 禁改
    "ship_name": str,         # 禁改
    "track_type": str         # 禁改
}

# /api/get_answer
{
    "user_input": str,        # 禁改
    "scenario_id": str        # 禁改（可選）
}
```

### 2.3 回應欄位名稱
**禁止修改以下回應欄位**：

```python
# 成功回應格式
{
    "status": "success",      # 禁改
    "map_url": str,           # 禁改
    "answer": str,            # 禁改
    "table_html": str,        # 禁改（可選）
    "data": dict              # 禁改（可選）
}

# 錯誤回應格式
{
    "status": "error",        # 禁改
    "message": str            # 禁改
}
```

**為什麼不能改**：
- 前端依賴這些欄位名稱解析回應
- 改動會導致所有功能失效

---

## 三、MapState 結構（絕對禁改）

### 3.1 核心屬性
**檔案**：`models/map_state.py`
**禁改區域**：`__init__` 方法的屬性初始化

**關鍵屬性**：
```python
class MapState:
    def __init__(self, client_id):
        # 禁改：會話識別
        self.client_id = client_id
        self.last_access_time = time.time()

        # 禁改：三層資料結構
        self.markers = {
            LAYER_SCENARIO: [],
            LAYER_WTA: [],
            LAYER_TRACKS: []
        }
        self.lines = {
            LAYER_SCENARIO: [],
            LAYER_WTA: [],
            LAYER_TRACKS: []
        }
        self.tracks = {
            LAYER_TRACKS: []
        }

        # 禁改：動畫資料
        self.wta_animation_data = []

        # 禁改：原始資料儲存
        self.scenario_data = None
        self.wta_data = None
```

**為什麼不能改**：
- 整個地圖繪製系統依賴這些屬性
- 改變結構會導致所有地圖功能失效
- 清除地圖邏輯依賴這些屬性的初始化方式

### 3.2 圖層常數
**檔案**：`config.py`
**禁改區域**：
```python
LAYER_SCENARIO = 'scenario'   # 禁改
LAYER_WTA = 'wta'             # 禁改
LAYER_TRACKS = 'tracks'       # 禁改
```

**為什麼不能改**：
- 所有地圖繪製邏輯依賴這些常數
- 前端 Leaflet LayerControl 依賴這些名稱

---

## 四、參數清理邏輯（謹慎修改）

### 4.1 陣營判斷邏輯
**檔案**：`routes/scenario_routes.py`
**謹慎區域**：101-220 行

**關鍵邏輯**：
```python
# 101-220 行：參數清理與陣營判斷
# 此區域已經過充分測試，修改前必須理解完整邏輯

# 1. LLM 可能誤分類船艦到錯誤陣營
# 2. 使用 ENEMY_KEYWORDS 和 ROC_KEYWORDS 判斷真實陣營
# 3. 自動移動到正確陣營並記錄

# 範例：
if ship in ROC_KEYWORDS:
    moved_to_roc.append(ship)
    roc_ships_corrected.append(ship)
elif ship in ENEMY_KEYWORDS:
    moved_to_enemy.append(ship)
    enemy_ships_corrected.append(ship)
```

**為什麼要謹慎**：
- 這是 LLM 誤分類的主要修正邏輯
- 測試過數百個場景的分類準確性
- 改動可能導致陣營錯亂

### 4.2 陣營關鍵字配置
**檔案**：`config.py`
**可擴充但不可刪減**：
```python
ENEMY_KEYWORDS = [
    "共軍", "解放軍", "中共", "紅軍", "敵方",
    "PLA", "PLAN", "055", "052D", "山東號"
    # 可新增，但不可刪除現有關鍵字
]

ROC_KEYWORDS = [
    "國軍", "海軍", "空軍", "我方", "友軍",
    "成功級", "康定級", "基德級", "濟陽級"
    # 可新增，但不可刪除現有關鍵字
]
```

**為什麼**：
- 刪除關鍵字會導致已知船艦無法識別
- 新增關鍵字是安全的

---

## 五、LLM Function Calling Schema（絕對禁改）

### 5.1 Tool Schema 結構
**檔案**：`prompts_config.json`
**禁改區域**：所有 `tools` 陣列的結構

**範例（import_scenario）**：
```json
{
  "import_scenario": {
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "import_scenario",              // 禁改
          "description": "匯入場景",
          "parameters": {
            "type": "object",
            "properties": {
              "scenario_id": {                    // 禁改
                "type": "string",
                "description": "場景編號"
              },
              "enemy_ships": {                    // 禁改
                "type": "array",
                "items": {"type": "string"}
              },
              "roc_ships": {                      // 禁改
                "type": "array",
                "items": {"type": "string"}
              }
            },
            "required": ["scenario_id"]           // 禁改
          }
        }
      }
    ]
  }
}
```

**為什麼不能改**：
- 後端解析邏輯依賴這些參數名稱
- 改動會導致 LLM 無法正確提取參數
- 所有功能失效

### 5.2 返回格式
**禁改格式**：
```python
# LLM Service 必須返回此格式
{
    "tool": str,           # 工具名稱（如 "import_scenario"）
    "parameters": dict     # 參數字典
}
```

---

## 六、API 模式切換機制（絕對禁改）

### 6.1 模式切換邏輯
**檔案**：`services/api_mode_service.py`
**禁改區域**：`call_api()` 方法的主邏輯

**關鍵邏輯**：
```python
@staticmethod
def call_api(endpoint_key, json_data=None, method='POST'):
    api_mode = get_api_mode()  # 從 system_config.json 讀取

    # 禁改：三種模式的分支邏輯
    if api_mode == 'real':
        return APIModeService._call_http_api(get_real_api_config(), ...)
    elif api_mode == 'local':
        return APIModeService._call_http_api(get_local_api_config(), ...)
    elif api_mode == 'mock':
        return APIModeService._get_mock_response(endpoint_key, json_data)
    else:
        # 禁改：預設回退到 local
        return APIModeService._call_http_api(get_local_api_config(), ...)
```

### 6.2 配置檔案結構
**檔案**：`system_config.json`
**禁改欄位**：
```json
{
  "api_mode": "local",           // 禁改欄位名稱（值可改為 "real"/"local"/"mock"）
  "real_api": {                  // 禁改欄位名稱
    "base_url": "...",
    "endpoints": {
      "import_scenario": "...",  // 禁改欄位名稱
      "star_scenario": "...",
      "get_wta": "...",
      "get_answer": "...",
      "get_track": "..."
    }
  },
  "local_api": {...},            // 禁改欄位名稱
  "local_data": {...}            // 禁改欄位名稱
}
```

---

## 七、配置重置機制（絕對禁改）

### 7.1 啟動時重置邏輯
**檔案**：`app.py`
**禁改區域**：59-68 行

**關鍵邏輯**：
```python
# 禁改：重置 config.json 為預設值
_existing = _load_existing()
_reset_config = dict(CONFIG_DEFAULTS)

# 禁改：保留持久化設定的清單
_persistent_keys = ["cesium_ion_token", "cesium_offline_mode", "custom_layers"]
for _key in _persistent_keys:
    if _key in _existing and _existing[_key]:
        _reset_config[_key] = _existing[_key]

save_config(_reset_config)
```

**為什麼不能改**：
- 確保每次啟動回到已知狀態
- 避免配置污染導致功能異常
- 持久化設定（如 token、圖層）需要保留

### 7.2 預設配置
**檔案**：`config.py`
**禁改欄位名稱**：
```python
CONFIG_DEFAULTS = {
    "show_source_btn": False,           # 禁改欄位名稱（值可改）
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

## 八、地圖繪製核心方法（謹慎修改）

### 8.1 create_map() 方法
**檔案**：`models/map_state.py`
**謹慎區域**：`create_map()` 方法（約 200-500 行）

**為什麼要謹慎**：
- 這是地圖生成的唯一入口
- 涉及三層圖層的繪製邏輯
- 涉及動畫控制器的嵌入
- 涉及 Leaflet LayerControl 的生成

**安全修改方式**：
- 新增圖層繪製邏輯（作為獨立區塊）
- 不要改變現有圖層的繪製順序
- 不要改變 Folium 地圖的初始化參數

### 8.2 軍事符號生成邏輯
**檔案**：`services/map_service.py`
**謹慎區域**：`mark_ships_from_scenario()` 方法

**關鍵邏輯**：
```python
# 禁改：軍事符號的 SIDC 碼生成
if faction == 'enemy':
    sidc = "SFGPEWNH---E---"  # 敵方水面艦艇
    color = "#FF0000"
elif faction == 'roc':
    sidc = "SFGPUFNH---F---"  # 我方水面艦艇
    color = "#0000FF"
```

**為什麼要謹慎**：
- SIDC 碼必須符合 NATO APP-6 標準
- 改動會導致符號顯示錯誤

---

## 九、前端模組初始化順序（禁改）

### 9.1 Application 類別初始化
**檔案**：`static/js/main.js`
**禁改區域**：`Application` class 的 `constructor`

**關鍵順序**：
```javascript
class Application {
    constructor() {
        // 1. API 客戶端（必須最先初始化）
        this.apiClient = new APIClient();

        // 2. 訊息管理器（其他模組依賴）
        this.messageManager = new MessageManager();

        // 3. 地圖管理器
        this.mapManager = new MapManager(this.apiClient, this.messageManager);

        // 4. UI 管理器
        this.uiManager = new UIManager(this.apiClient, this.messageManager, this.mapManager);

        // 5. 其他管理器（順序可調整）
        this.fileManager = new FileManager(...);
        this.promptManager = new PromptManager(...);
        // ...
    }
}
```

**為什麼不能改**：
- `APIClient` 必須最先初始化（注入 X-Client-ID）
- `MessageManager` 被其他模組依賴
- 改變順序會導致 undefined 錯誤

---

## 十、可安全擴充的區域

以下區域可以安全新增內容，不會破壞現有功能：

### 10.1 新增路由藍圖
- 在 `routes/` 新增 `xxx_routes.py`
- 在 `routes/__init__.py` 註冊新藍圖

### 10.2 新增前端模組
- 在 `static/js/modules/` 新增 `xxx-manager.js`
- 在 `main.js` 的 `Application` class 初始化

### 10.3 新增配置項目
- 在 `config.py` 新增常數
- 在 `CONFIG_DEFAULTS` 新增預設值

### 10.4 新增地圖圖層
- 在 `config.py` 新增圖層常數
- 在 `map_state.py` 新增資料儲存結構
- 在 `create_map()` 新增繪製邏輯（作為獨立區塊）

### 10.5 新增 LLM Provider
- 在 `services/llm_service.py` 的 `_call_with_provider()` 新增分支
- 在 `system_config.json` 新增對應配置

### 10.6 新增陣營關鍵字
- 在 `config.py` 的 `ENEMY_KEYWORDS` 或 `ROC_KEYWORDS` 新增

### 10.7 新增飛彈顏色
- 在 `config.py` 的 `WEAPON_COLORS` 新增

---

## 十一、修改前的檢查清單

在修改任何核心區域前，必須確認：

- [ ] 已閱讀 `CLAUDE.md` 的修改流程
- [ ] 已確認修改範圍不在本文件的「禁改區域」
- [ ] 已向用戶說明修改原因、影響範圍、替代方案
- [ ] 已獲得用戶明確同意
- [ ] 已準備回滾方案（Git commit 或備份）

---

**版本**：v6.0 (基於實際程式碼分析)
**更新日期**：2026-03-02
**維護團隊**：軍事兵推 AI 系統團隊
