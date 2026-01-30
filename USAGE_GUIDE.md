# 重構後模組使用指南

本文檔說明如何在 `flask_v6.py` 或其他 Flask 路由中使用重構後的模組。

---

## 導入方式

### 1. 導入 MapState 類別

```python
# 方式 1：直接導入
from models.map_state import MapState

# 方式 2：從模組導入
from models import MapState

# 使用範例
map_state = MapState()
map_state.add_marker([25.0, 121.5], "台北", "blue")
folium_map = map_state.create_map()
```

---

### 2. 導入配置服務

```python
# 方式 1：直接導入
from services.config_service import (
    load_prompts_config,
    save_prompts_config,
    get_system_prompt,
    load_config,
    save_config
)

# 方式 2：從模組導入
from services import (
    load_prompts_config,
    get_system_prompt,
    load_config
)

# 使用範例
config = load_prompts_config()
system_prompt = get_system_prompt("預設配置", "import_scenario")
app_config = load_config()
```

---

### 3. 導入 LLM 服務

```python
# 方式 1：直接導入
from services.llm_service import LLMService

# 方式 2：從模組導入
from services import LLMService

# 使用範例
llm_service = LLMService()
result = llm_service.call_import_scenario(
    user_prompt="繪製052D和055",
    model="llama3.2:3b",
    custom_prompt=system_prompt
)
```

---

### 4. 導入地圖服務

```python
# 方式 1：直接導入
from services.map_service import MapService

# 方式 2：從模組導入
from services import MapService

# 使用範例
map_service = MapService()

# 獲取武器顏色
color = MapService.get_weapon_color("雄三飛彈")  # 返回 "#FF0000"

# 添加船艦到地圖
ship_data = {
    "enemy": [{"052D": {"location": [25.0, 121.5]}}],
    "roc": [{"1101": {"location": [25.1, 121.6]}}]
}
MapService.add_ships_to_map(ship_data, map_state)

# 生成武器分派表格
wta_data = {...}
html_table = MapService.generate_wta_table_html(wta_data)
```

---

### 5. 導入 Fallback 處理器

```python
# 方式 1：直接導入
from handlers.fallback_handler import FallbackHandler

# 方式 2：從模組導入
from handlers import FallbackHandler

# 使用範例
handler = FallbackHandler()

# 場景匯入 fallback
result = FallbackHandler.fallback_import_scenario("繪製052D")
# 返回: {'tool': 'import_scenario', 'parameters': {'enemy': ['052D']}}

# 啟動模擬 fallback
result = FallbackHandler.fallback_star_scenario("開始模擬")
# 返回: {'tool': 'star_scenario', 'parameters': {}}
```

---

### 6. 導入解析工具

```python
# 方式 1：直接導入
from utils.parser import parse_function_arguments

# 方式 2：從模組導入
from utils import parse_function_arguments

# 使用範例
# 處理 LLM 返回的參數
arguments = '{"enemy": ["052D", "055"]}'
parsed = parse_function_arguments(arguments)
# 返回: {'enemy': ['052D', '055']}

# 自動修正空陣列字符串
arguments = '{"enemy": "[]"}'
parsed = parse_function_arguments(arguments)
# 返回: {'enemy': []}
```

---

### 7. 導入輔助工具

```python
# 方式 1：直接導入
from utils.helpers import (
    get_client_id,
    get_map_state,
    cleanup_old_files
)

# 方式 2：從模組導入
from utils import get_client_id, get_map_state, cleanup_old_files

# 使用範例
# 獲取客戶端 ID
client_id = get_client_id()  # 從 request header 或 body 獲取

# 獲取當前會話的地圖狀態（多分頁隔離）
map_state = get_map_state()

# 清理舊文件
cleanup_old_files("maps", days=30)  # 清理 30 天前的地圖文件
```

---

## 完整使用範例

### 場景 1: 在 Flask 路由中處理場景匯入

```python
from flask import Flask, request, jsonify
from services import LLMService, MapService, get_system_prompt
from handlers import FallbackHandler
from utils import get_map_state

app = Flask(__name__)

@app.route('/api/import_scenario', methods=['POST'])
def import_scenario():
    """場景匯入 API"""
    try:
        data = request.json
        user_input = data.get('user_input', '')
        llm_model = data.get('llm_model', 'llama3.2:3b')
        prompt_config = data.get('prompt_config', '預設配置')

        # 1. 獲取 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'import_scenario')

        # 2. 使用 LLM 提取參數
        llm_service = LLMService()
        decision = llm_service.call_import_scenario(
            user_input,
            model=llm_model,
            custom_prompt=custom_prompt
        )

        # 3. Fallback: 如果 LLM 失敗，使用規則匹配
        if not decision or not decision.get('parameters'):
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = FallbackHandler.fallback_import_scenario(user_input)

        if not decision or not decision.get('parameters'):
            return jsonify({
                'success': False,
                'error': '無法解析指令，請檢查輸入格式。'
            })

        # 4. 獲取當前會話的地圖狀態
        map_state = get_map_state()

        # 5. 添加船艦到地圖（這裡需要從 Node.js API 獲取座標，省略...）
        # ship_data = {...}  # 從 Node.js API 獲取
        # MapService.add_ships_to_map(ship_data, map_state)

        # 6. 創建地圖
        folium_map = map_state.create_map()

        # 7. 保存地圖
        map_path = f"maps/map_{client_id}.html"
        folium_map.save(map_path)

        return jsonify({
            'success': True,
            'map_url': f'/maps/map_{client_id}.html'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
```

---

### 場景 2: 處理武器分派查詢

```python
from flask import Flask, request, jsonify
from services import LLMService, MapService, get_system_prompt
from utils import get_map_state

@app.route('/api/get_wta', methods=['POST'])
def get_wta():
    """武器分派查詢 API"""
    try:
        data = request.json
        user_input = data.get('user_input', '')
        llm_model = data.get('llm_model', 'llama3.2:3b')
        prompt_config = data.get('prompt_config', '預設配置')

        # 1. 獲取 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'get_wta')

        # 2. 使用 LLM 提取參數
        llm_service = LLMService()
        decision = llm_service.call_get_wta(
            user_input,
            model=llm_model,
            custom_prompt=custom_prompt
        )

        # 3. 獲取武器分派結果（從 Node.js API，省略...）
        # wta_results = [...]

        # 4. 獲取當前會話的地圖狀態
        map_state = get_map_state()

        # 5. 添加武器分派線條到地圖
        MapService.add_wta_to_map(wta_results, map_state)

        # 6. 生成武器分派表格 HTML
        wta_data = {
            'wta_table_columns': [...],
            'wta_results': wta_results
        }
        table_html = MapService.generate_wta_table_html(wta_data)

        # 7. 創建地圖
        folium_map = map_state.create_map()

        return jsonify({
            'success': True,
            'table_html': table_html
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
```

---

### 場景 3: 定期清理舊文件

```python
import threading
from utils import cleanup_old_files

def cleanup_thread():
    """定期清理舊文件的背景線程"""
    import time
    while True:
        # 每天執行一次清理
        cleanup_old_files("maps", days=30)
        cleanup_old_files("feedbacks", days=90)
        cleanup_old_files("cops", days=60)

        # 等待 24 小時
        time.sleep(24 * 60 * 60)

# 啟動清理線程
cleanup_thread = threading.Thread(target=cleanup_thread, daemon=True)
cleanup_thread.start()
```

---

## 目錄結構

重構後的目錄結構如下：

```
c:\Users\User\Desktop\20260126\重構\
├── models/
│   ├── __init__.py
│   └── map_state.py          # MapState 類別
├── services/
│   ├── __init__.py
│   ├── config_service.py     # 配置管理
│   ├── llm_service.py        # LLM 服務
│   └── map_service.py        # 地圖服務
├── handlers/
│   ├── __init__.py
│   └── fallback_handler.py   # Fallback 處理器
├── utils/
│   ├── __init__.py
│   ├── parser.py             # 解析工具
│   └── helpers.py            # 輔助工具
├── config.py                 # 配置常數
├── flask_v6.py              # Flask 主程式（需更新 import）
└── USAGE_GUIDE.md           # 本文檔
```

---

## 注意事項

1. **導入順序**: 確保 Python 能找到這些模組，可能需要將項目根目錄添加到 `PYTHONPATH`

2. **循環依賴**: 目前的設計已避免循環依賴：
   - `models/` 不依賴其他模組
   - `utils/` 只依賴 `models/`
   - `services/` 依賴 `models/`, `utils/`, `config`
   - `handlers/` 不依賴其他模組

3. **Flask Context**: 在 `models/map_state.py` 的 `create_map()` 方法中使用了 `current_app`，需要確保在 Flask 應用上下文中調用

4. **線程安全**: `utils/helpers.py` 中的 `_STATES` 字典使用了 `threading.Lock()` 確保線程安全

---

## 遷移建議

將 `flask_v6.py` 遷移到使用這些模組的步驟：

1. **備份原文件**
   ```bash
   cp flask_v6.py flask_v6_backup.py
   ```

2. **添加 import 語句**
   ```python
   from models import MapState
   from services import LLMService, MapService, get_system_prompt, load_config
   from handlers import FallbackHandler
   from utils import get_client_id, get_map_state, parse_function_arguments
   ```

3. **移除已重構的代碼**
   - 刪除 MapState 類定義（第143-1066行）
   - 刪除 load_prompts_config(), save_prompts_config(), get_system_prompt()
   - 刪除所有 call_llama_* 函數
   - 刪除所有 fallback_* 函數
   - 刪除 parse_function_arguments()
   - 刪除 get_weapon_color(), add_ships_to_map() 等函數
   - 刪除 _sanitize_client_id(), get_client_id(), get_map_state()
   - 刪除 cleanup_old_files()

4. **更新函數調用**
   - 將 `call_llama_import_scenario()` 改為 `llm_service.call_import_scenario()`
   - 將 `add_ships_to_map()` 改為 `MapService.add_ships_to_map()`
   - 將 `get_map_state()` 保持不變（從 utils 導入）

5. **測試驗證**
   - 運行 Flask 應用
   - 測試所有 API 端點
   - 確認地圖生成正常

---

## 完成時間
2026-01-30
