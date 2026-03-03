# CLAUDE.md - 軍事兵推 AI 系統開發規範

> 本文件約束 Claude 在修改、新增、debug 或重構本專案時的行為準則。
> 目的：保護現有功能、避免不必要的架構變動、確保最小侵入式修改。

# Claude 行為規則

在任何修改前：
必須閱讀：
- CLAUDE.md
- ARCHITECTURE.md
- DO_NOT_TOUCH.md


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
  - 改會話隔離機制（client_id、X-Client-ID Header）

### 1.2 非改不可時的處理流程
若判斷「非改不可」，必須先向用戶說明：
1. **原因**：為什麼現有寫法無法滿足需求
2. **影響範圍**：會動到哪些檔案、哪些函式
3. **替代方案**：是否有更小侵入的做法
4. **回滾方式**：如何還原到修改前狀態

---

## 二、修改前必須遵守的流程

### 2.1 修改前輸出
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

### 2.2 修改後提供
1. **可直接執行的版本**
   - 不要留 placeholder 或 TODO
   - 確保語法正確、import 完整

2. **測試與驗證方式**
   - API 測試：curl 指令或 Postman 步驟
   - UI 測試：操作步驟說明
   - 回歸確認：如何確認舊功能沒壞

---

## 三、禁止事項

除非用戶明確說「可以」，否則禁止以下行為：

### 3.1 禁止為了「更好」而改
- ❌ 「這樣寫比較乾淨」
- ❌ 「這樣架構比較好」
- ❌ 「這樣比較符合最佳實務」
- ❌ 「這樣比較容易維護」

### 3.2 禁止改既有使用者流程
- ❌ 改變操作順序（先選模式再輸入）
- ❌ 改變 UI 佈局（側邊欄位置、分隔線行為）
- ❌ 改變地圖顯示效果（顏色、符號、線條樣式）
- ❌ 改變訊息格式（成功/失敗的文字模板）

### 3.3 禁止未經說明就動核心流程
以下區塊屬於「核心流程」，修改前必須詳細說明：
- `services/llm_service.py` 的 Function Calling payload 結構
- `models/map_state.py` 的 `create_map()` 方法
- `routes/scenario_routes.py` 的參數清理邏輯（101-220 行）
- `static/js/modules/api-client.js` 的 X-Client-ID Header 注入機制
- `config.py` 的顏色/關鍵字配置
- `services/api_mode_service.py` 的模式切換邏輯
- `utils/helpers.py` 的會話管理（get_client_id、get_map_state）

### 3.4 禁止改 API 契約
- ❌ 改路由路徑（詳見 DO_NOT_TOUCH.md）
- ❌ 改請求參數名稱（`user_input` → `input`）
- ❌ 改回應欄位名稱（`map_url` → `mapUrl`）
- ❌ 改錯誤回應格式
- ❌ 改 X-Client-ID Header 名稱或格式

---

## 四、擴充與新增功能的標準方式

### 4.1 原則
- **新增 > 修改**：優先以新增模組/handler/layer 實現，而非侵入核心
- **可開關**：新功能預設需有開關機制（config.json 或參數）
- **可停用**：停用後不影響既有功能
- **可回滾**：能快速還原到修改前狀態

### 4.2 新增後端功能
```
1. 新增路由 → routes/ 下新建 xxx_routes.py
2. 在 routes/__init__.py 註冊藍圖
3. 新增服務 → services/ 下新建 xxx_service.py
4. 新增處理器 → handlers/ 下新建 xxx_handler.py
5. 若需要新的配置項 → 在 config.py 新增常數
```

**範例：新增路由藍圖**
```python
# routes/new_feature_routes.py
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)
new_feature_bp = Blueprint('new_feature', __name__)

@new_feature_bp.route('/api/new_feature', methods=['POST'])
def handle_new_feature():
    client_id = request.headers.get('X-Client-ID')
    # 實作邏輯
    return jsonify({"status": "success"})
```

```python
# routes/__init__.py
from .new_feature_routes import new_feature_bp

def register_blueprints(app: Flask):
    # ... 現有藍圖 ...
    app.register_blueprint(new_feature_bp)
    logger.info("所有路由藍圖註冊完成（共 13 個藍圖）")  # 更新數字
```

### 4.3 新增前端功能
```
1. 新增模組 → static/js/modules/ 下新建 xxx-manager.js
2. 在 main.js 的 Application class 初始化
3. 必要時在 index.html 新增 UI 元素
```

**範例：新增前端模組**
```javascript
// static/js/modules/new-feature-manager.js
export class NewFeatureManager {
    constructor(apiClient, messageManager) {
        this.apiClient = apiClient;
        this.messageManager = messageManager;
        this.initEventListeners();
    }

    initEventListeners() {
        // 綁定事件
    }
}
```

```javascript
// static/js/main.js
import { NewFeatureManager } from './modules/new-feature-manager.js';

class Application {
    constructor() {
        // ... 現有初始化 ...
        this.newFeatureManager = new NewFeatureManager(
            this.apiClient,
            this.messageManager
        );
    }
}
```

### 4.4 新增地圖圖層
```python
# 1. 在 config.py 定義常數
LAYER_NEW_FEATURE = 'new_feature'

# 2. 在 models/map_state.py 的 __init__ 新增儲存結構
class MapState:
    def __init__(self):
        # ... 現有初始化 ...
        self.new_feature_data = []

# 3. 在 create_map() 新增繪製邏輯（作為獨立區塊）
def create_map(self):
    # ... 現有地圖初始化 ...

    # 新增的圖層繪製邏輯
    if self.new_feature_data:
        new_feature_layer = folium.FeatureGroup(name='新功能')
        for item in self.new_feature_data:
            # 繪製標記/線段
            folium.Marker(
                location=[item['lat'], item['lon']],
                popup=item['name']
            ).add_to(new_feature_layer)
        new_feature_layer.add_to(m)

    # ... 後續程式碼 ...
```

### 4.5 新增 LLM 功能
```python
# 1. 在 prompts_config.json 新增對應的 prompt
{
  "new_feature": {
    "system_prompt": "你是...",
    "tools": [...]
  }
}

# 2. 在 services/llm_service.py 新增方法
def call_new_feature(user_input):
    return _call_with_provider(
        system_prompt=prompts['new_feature']['system_prompt'],
        user_input=user_input,
        tools=prompts['new_feature']['tools']
    )

# 3. 在 routes/ 新增對應的 API 端點（參考 4.2）

# 4. 在 handlers/fallback_handler.py 新增對應的 fallback 方法
@staticmethod
def handle_new_feature_fallback(user_input):
    # 規則匹配邏輯
    return {"tool": "new_feature", "parameters": {...}}
```

### 4.6 新增配置項目
```python
# 1. 在 config.py 新增常數
NEW_FEATURE_ENABLED = True
NEW_FEATURE_COLOR = "#FF5733"

# 2. 在 config.py 的 CONFIG_DEFAULTS 新增（若需持久化）
CONFIG_DEFAULTS = {
    # ... 現有配置 ...
    "enable_new_feature": True
}

# 3. 使用時從 config.json 讀取
from services import load_config
config = load_config()
if config.get('enable_new_feature', False):
    # 執行新功能邏輯
```

---

## 五、常見修改場景指引

### 5.1 新增一種飛彈顏色
```python
# config.py
WEAPON_COLORS = {
    # ... 現有顏色 ...
    "新飛彈名稱": "#HEX色碼"
}
```
不需動其他檔案，`services/map_service.py` 會自動讀取。

### 5.2 新增陣營識別關鍵字
```python
# config.py
ENEMY_KEYWORDS = [
    # ... 現有關鍵字 ...
    "新敵方關鍵字"
]

ROC_KEYWORDS = [
    # ... 現有關鍵字 ...
    "新我方關鍵字"
]
```
影響：`routes/scenario_routes.py` 的參數清理邏輯（101-220 行）。

### 5.3 調整地圖預設中心/縮放
```python
# config.py
MAP_DEFAULT_CENTER = [新緯度, 新經度]  # 目前: [23.5, 120.5]
MAP_DEFAULT_ZOOM = 新縮放級別           # 目前: 7
```

### 5.4 新增 LLM Provider
```python
# services/llm_service.py
def _call_with_provider(system_prompt, user_input, tools=None):
    if provider == 'new_provider':
        # 實作新 provider 的呼叫邏輯
        response = call_new_provider_api(...)
        return parse_response(response)
    # ... 現有邏輯 ...
```

### 5.5 調整會話數量上限
```python
# config.py
MAX_CONCURRENT_SESSIONS = 新數字  # 目前: 200
```

---

## 六、輸出規範

### 6.1 語言與風格
- **語言**：繁體中文
- **風格**：工程導向、具體、可執行
- **避免**：空泛描述、教科書式說明

### 6.2 程式碼規範
- **完整性**：可直接執行、不留 placeholder
- **註解**：簡潔、必要時才加
- **import**：完整列出所有相依模組
- **錯誤處理**：適當的 try-except 包裹

### 6.3 回應格式
修改完成後，必須提供：
1. **修改摘要**：列出異動檔案與主要變更
2. **測試指令**：API 測試的 curl 或 UI 操作步驟
3. **回歸檢查**：如何確認舊功能正常

**範例輸出格式：**
```
## 修改摘要
- 修改檔案：routes/scenario_routes.py (新增 50 行)
- 新增檔案：services/new_feature_service.py (120 行)
- 主要變更：新增 XXX 功能，支援 YYY 場景

## 測試指令
# 測試新功能
curl -X POST http://localhost:5000/api/new_feature \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: test-client-123" \
  -d '{"param": "value"}'

## 回歸檢查
1. 測試場景匯入功能（/api/import_scenario）
2. 確認 WTA 查詢正常（/api/get_wta）
3. 檢查地圖渲染無異常
```

---

## 七、參考文件

- **ARCHITECTURE.md**：完整的系統架構與資料流
- **DO_NOT_TOUCH.md**：核心禁改清單與 API 契約
- **prompts_config.json**：LLM System Prompt 配置
- **system_config.json**：系統層級配置（API 模式切換）
- **config.json**：執行時配置（功能開關）

---

**版本**：v6.0 (基於實際程式碼分析)
**更新日期**：2026-03-02
**維護團隊**：軍事兵推 AI 系統團隊
