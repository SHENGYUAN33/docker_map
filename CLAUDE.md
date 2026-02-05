# CLAUDE.md - 軍事兵推 AI 系統開發規範

> 本文件約束 Claude 在修改、新增、debug 或重構本專案時的行為準則。
> 目的：保護現有功能、避免不必要的架構變動、確保最小侵入式修改。

---

## 一、最高原則

### 1.1 預設不可更動原則
- **已能執行、邏輯正確、正在使用中的功能 → 預設不動**
- 除非用戶明確要求，否則禁止：
  - 重構資料夾結構
  - 拆檔 / 合檔
  - 改路由路徑或 API I/O JSON 格式
  - 改前端互動流程或地圖呈現方式
  - 改 CSS 主題色或 UI 佈局
  - 改 LLM Function Calling 的 tool schema

### 1.2 非改不可時的處理流程
若判斷「非改不可」，必須先向用戶說明：
1. **原因**：為什麼現有寫法無法滿足需求
2. **影響範圍**：會動到哪些檔案、哪些函式
3. **替代方案**：是否有更小侵入的做法
4. **回滾方式**：如何還原到修改前狀態

---

## 二、既有系統邏輯（如實記錄）

### 2.1 完整資料流
```
前端用戶輸入
    ↓
API 客戶端（自動注入 X-Client-ID Header）
    ↓
Flask 路由層（routes/*.py）
    ↓
配置服務（讀取 prompts_config.json）
    ↓
LLM 服務層（services/llm_service.py）
    ├─ Ollama Function Calling
    └─ 失敗時 → FallbackHandler 規則解析
    ↓
參數解析與修正（utils/parser.py）
    ↓
智能清理層（陣營判斷、去重、空值處理）
    ↓
Node.js API / 本地 JSON 讀取
    ↓
地圖服務層（services/map_service.py）
    ↓
MapState 更新（models/map_state.py）
    ↓
Folium 生成 HTML + 軍事符號注入
    ↓
保存至 maps/ 目錄
    ↓
返回 JSON 響應（map_url, answer, table_html 等）
    ↓
前端渲染（iframe 載入地圖、顯示訊息）
```

### 2.2 分層責任（Separation of Concerns）— 嚴格遵守

| 層級 | 只負責 | 絕對不做 |
|------|--------|---------|
| **LLM** | 意圖理解 + 參數提取（Function Calling） | 商業邏輯、資料驗證、地圖繪製、資料正規化 |
| **Backend** | 驗證/正規化/重試/串接 API/生成地圖 | 前端互動、UI 邏輯 |
| **Frontend** | UI、事件綁定、顯示、互動（Leaflet 層） | 資料正規化、商業邏輯 |

**禁止違反分層原則：**
- ❌ 不得把 Backend 的資料正規化丟到前端做
- ❌ 不得把前端互動塞回 LLM prompt 亂做
- ❌ 不得讓 LLM 處理本應由 Backend 負責的邏輯

**細部責任對照：**

| 層級 | 負責內容 | 不負責內容 |
|------|---------|-----------|
| **FallbackHandler** | LLM 失敗時的規則匹配 | 複雜邏輯判斷 |
| **routes/*.py** | 請求驗證、流程控制、回應組裝 | 地圖繪製細節 |
| **services/map_service.py** | 船艦標記、攻擊線、航跡的繪製邏輯 | 狀態儲存 |
| **models/map_state.py** | 會話級狀態管理、圖層管理、Folium HTML 生成 | API 呼叫 |
| **前端 JS modules** | UI 操作、API 呼叫封裝、地圖 iframe 管理 | 地圖內容生成 |

### 2.3 API 模式切換（必須保留）

系統存在 `local / mock / real` 或類似 `api_mode` 的切換概念：
- **local**：使用本地 JSON 檔案（如 `track_data.json`、`db_v2.json`）
- **mock**：使用模擬 API 回應
- **real**：連接真實的 Node.js API / 中科院系統

**新增功能時必須：**
1. 支援同樣的模式切換機制
2. 避免把某一種模式寫死
3. 在 `config.py` 或環境變數中可配置切換

```python
# 範例：正確的模式切換寫法
if api_mode == 'local':
    data = load_local_json('track_data.json')
elif api_mode == 'mock':
    data = get_mock_response()
else:  # real
    data = call_real_api(params)
```

### 2.4 三層圖層架構
```python
LAYER_SCENARIO = 'scenario'   # 場景層：敵我船艦標記
LAYER_WTA = 'wta'             # 武器分派層：攻擊線 + 動畫
LAYER_TRACKS = 'tracks'       # 航跡層：軌跡線段
```

- 各層獨立管理，可單獨清除
- Leaflet LayerControl 動態切換顯示
- 標記形狀：敵方紅色菱形、我方藍色圓形

### 2.5 會話隔離機制
- 前端：每個分頁生成唯一 `client_id`，存於 `sessionStorage`
- 後端：依 `X-Client-ID` Header 隔離 `MapState` 實例
- 清理：超過 `MAX_CONCURRENT_SESSIONS` 時自動淘汰最久未使用

### 2.6 動畫系統
- 開關：`config.json` 的 `enable_animation`
- 控制器：嵌入 Folium HTML 的 JavaScript
- 功能：播放/暫停/重播、速度控制（1x/2x/3x）、進度條拖曳
- 資料：`wta_animation_data` 持久化於 `MapState`

---

## 三、修改前必須遵守的流程

### 3.1 修改前輸出
在動手改 code 之前，必須先輸出以下內容：

1. **需求理解**
   - 用戶要什麼？
   - 是 bug 修復、功能新增、還是行為調整？

2. **修改範圍**
   - 會動到哪些檔案？
   - 會動到哪些函式/區塊？
   - 預估行數變動量

3. **不會動的功能**
   - 明確列出「這次修改不會影響」的現有功能
   - 例：「不會動場景匯入邏輯」「不會改 WTA 表格樣式」

### 3.2 修改後提供
1. **可直接執行的版本**
   - 不要留 placeholder 或 TODO
   - 確保語法正確、import 完整

2. **測試與驗證方式**
   - API 測試：curl 指令或 Postman 步驟
   - UI 測試：操作步驟說明
   - 回歸確認：如何確認舊功能沒壞

---

## 四、禁止事項

除非用戶明確說「可以」，否則禁止以下行為：

### 4.1 禁止為了「更好」而改
- ❌ 「這樣寫比較乾淨」
- ❌ 「這樣架構比較好」
- ❌ 「這樣比較符合最佳實務」
- ❌ 「這樣比較容易維護」

### 4.2 禁止改既有使用者流程
- ❌ 改變操作順序（先選模式再輸入）
- ❌ 改變 UI 佈局（側邊欄位置、分隔線行為）
- ❌ 改變地圖顯示效果（顏色、符號、線條樣式）
- ❌ 改變訊息格式（成功/失敗的文字模板）

### 4.3 禁止未經說明就動核心流程
以下區塊屬於「核心流程」，修改前必須詳細說明：
- `llm_service.py` 的 Function Calling payload 結構
- `map_state.py` 的 `create_map()` 方法
- `scenario_routes.py` 的參數清理邏輯
- `api-client.js` 的 Header 注入機制
- `config.py` 的顏色/關鍵字配置

### 4.4 禁止改 API 契約
- ❌ 改路由路徑（`/api/import_scenario` → `/api/scenario/import`）
- ❌ 改請求參數名稱（`user_input` → `input`）
- ❌ 改回應欄位名稱（`map_url` → `mapUrl`）
- ❌ 改錯誤回應格式

---

## 五、擴充與新增功能的標準方式

### 5.1 原則
- **新增 > 修改**：優先以新增模組/handler/layer 實現，而非侵入核心
- **可開關**：新功能預設需有開關機制（config.json 或參數）
- **可停用**：停用後不影響既有功能
- **可回滾**：能快速還原到修改前狀態

### 5.2 新增後端功能
```
1. 新增路由 → routes/ 下新建 xxx_routes.py
2. 在 routes/__init__.py 註冊藍圖
3. 新增服務 → services/ 下新建 xxx_service.py
4. 新增處理器 → handlers/ 下新建 xxx_handler.py
```

### 5.3 新增前端功能
```
1. 新增模組 → static/js/modules/ 下新建 xxx-manager.js
2. 在 main.js 的 Application class 初始化
3. 必要時在 index.html 新增 UI 元素
```

### 5.4 新增地圖圖層
```python
# 1. 在 config.py 定義常數
LAYER_NEW_FEATURE = 'new_feature'

# 2. 在 map_state.py 的 __init__ 新增儲存結構
self.new_feature_data = []

# 3. 在 create_map() 新增繪製邏輯（作為獨立區塊）
if self.new_feature_data:
    new_feature_layer = folium.FeatureGroup(name='新功能')
    # 繪製邏輯
    new_feature_layer.add_to(m)
```

### 5.5 新增 LLM 功能
```python
# 1. 在 prompts_config.json 新增對應的 prompt
# 2. 在 llm_service.py 新增 call_xxx() 方法
# 3. 在 routes/ 新增對應的 API 端點
# 4. 在 handlers/fallback_handler.py 新增對應的 fallback 方法
```

---

## 六、關鍵檔案路徑速查

### 後端核心
| 檔案 | 用途 |
|------|------|
| `app.py` | Flask 應用入口 |
| `config.py` | 全域配置（260+ 項） |
| `models/map_state.py` | 地圖狀態管理（1200+ 行） |
| `services/llm_service.py` | LLM 呼叫封裝 |
| `services/map_service.py` | 地圖繪製邏輯 |
| `routes/scenario_routes.py` | 場景相關 API |
| `routes/data_routes.py` | 資料查詢 API（最大 16KB） |
| `handlers/fallback_handler.py` | LLM 失敗處理 |
| `utils/parser.py` | 參數解析修正 |
| `utils/helpers.py` | 會話管理、檔案清理 |

### 前端核心
| 檔案 | 用途 |
|------|------|
| `templates/index.html` | 主 HTML（30KB） |
| `static/js/main.js` | 應用入口 |
| `static/js/milsymbol.js` | 軍事符號庫 |
| `static/js/modules/api-client.js` | API 封裝 |
| `static/js/modules/map-manager.js` | 地圖管理 |
| `static/js/modules/ui-manager.js` | UI 操作 |
| `static/js/modules/message-manager.js` | 訊息顯示 |
| `static/js/modules/simulation-manager.js` | 模擬狀態輪詢 |

### 資料檔案
| 檔案 | 用途 |
|------|------|
| `config.json` | 系統開關（動畫、來源按鈕） |
| `prompts_config.json` | LLM System Prompt 配置 |
| `db_v2.json` | 系統資料庫 |
| `track_data.json` | 航跡資料 |

---

## 七、常見修改場景指引

### 7.1 新增一種飛彈顏色
```python
# config.py
WEAPON_COLORS = {
    ...,
    "新飛彈名稱": "#HEX色碼"
}
```
不需動其他檔案，`map_service.py` 會自動讀取。

### 7.2 新增陣營識別關鍵字
```python
# config.py
ENEMY_KEYWORDS = [..., "新關鍵字"]
ROC_KEYWORDS = [..., "新關鍵字"]
```
影響：LLM Fallback 和參數清理邏輯。

### 7.3 調整地圖預設中心/縮放
```python
# config.py
MAP_DEFAULT_CENTER = [新緯度, 新經度]
MAP_DEFAULT_ZOOM = 新縮放級別
```

### 7.4 新增 API 端點
1. 在對應的 `routes/xxx_routes.py` 新增 route
2. 若需要 LLM → 在 `llm_service.py` 新增方法
3. 若需要 Fallback → 在 `fallback_handler.py` 新增方法
4. 在前端 `api-client.js` 新增對應方法

---

## 八、輸出規範

- **語言**：繁體中文
- **風格**：工程導向、具體、可執行
- **避免**：空泛描述、教科書式說明
- **程式碼**：完整、可直接執行、註解簡潔
