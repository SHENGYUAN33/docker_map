# Sequence Diagrams - 軍事兵推 AI 系統

## 1. 整體系統架構互動總覽

```mermaid
sequenceDiagram
    participant User as 使用者 (Browser)
    participant Flask as Flask App (app.py)
    participant Routes as Routes Layer
    participant LLM as LLMService
    participant Fallback as FallbackHandler
    participant MapSvc as MapService
    participant MapState as MapState
    participant ConfigSvc as ConfigService
    participant NodeAPI as Node.js CMO API
    participant Ollama as Ollama LLM
    participant FS as File System

    User->>Flask: HTTP Request
    Flask->>Routes: Route dispatch
    Routes->>ConfigSvc: get_system_prompt()
    ConfigSvc->>FS: load prompts_config.json
    FS-->>ConfigSvc: prompt config
    ConfigSvc-->>Routes: system_prompt
    Routes->>LLM: call_xxx(user_input, model, prompt)
    LLM->>Ollama: POST /api/chat (Function Calling)
    alt LLM 成功
        Ollama-->>LLM: tool_calls response
        LLM-->>Routes: {tool, parameters}
    else LLM 失敗/逾時
        Ollama-->>LLM: error/timeout
        LLM-->>Routes: None
        Routes->>Fallback: fallback_xxx(user_input)
        Fallback-->>Routes: {tool, parameters}
    end
    Routes->>NodeAPI: POST /api/xxx (parameters)
    NodeAPI-->>Routes: response data
    Routes->>MapSvc: add_xxx_to_map(data, map_state)
    MapSvc->>MapState: add_marker() / add_line()
    Routes->>MapState: create_map()
    MapState->>FS: save HTML to /maps/
    MapState-->>Routes: map HTML
    Routes-->>Flask: JSON response
    Flask-->>User: {success, answer, map_url, data}
```

---

## 2. 匯入想定 (Import Scenario) - 繪製艦船座標

```mermaid
sequenceDiagram
    participant User as 使用者
    participant SR as scenario_routes.py
    participant CS as ConfigService
    participant LLM as LLMService
    participant Ollama as Ollama
    participant Parser as parser.py
    participant FB as FallbackHandler
    participant NodeAPI as Node.js API
    participant MS as MapService
    participant State as MapState
    participant FS as /maps/

    User->>SR: POST /api/import_scenario<br/>{user_input, llm_model, prompt_config}

    Note over SR: Step 1: 取得系統提示詞
    SR->>CS: get_system_prompt(config_name, "import_scenario")
    CS-->>SR: system_prompt

    Note over SR: Step 2: LLM 解析使用者意圖
    SR->>LLM: call_import_scenario(user_input, model, prompt)
    LLM->>Ollama: POST /api/chat<br/>tools: [{import_scenario: {enemy[], roc[]}}]

    alt LLM 回應成功
        Ollama-->>LLM: tool_calls: [{function: "import_scenario",<br/>arguments: '{"enemy":["052D"]}'}]
        LLM->>Parser: parse_function_arguments(arguments)
        Parser-->>LLM: {"enemy": ["052D"]}
        LLM-->>SR: {"tool": "import_scenario",<br/>"parameters": {"enemy": ["052D"]}}
    else LLM 逾時或失敗
        Ollama-->>LLM: timeout / error
        LLM-->>SR: None
        SR->>FB: fallback_import_scenario(user_input)
        Note over FB: 關鍵字比對：ENEMY_KEYWORDS,<br/>ENEMY_SHIP_NAMES
        FB-->>SR: {"tool": "import_scenario",<br/>"parameters": {"enemy": ["052D"]}}
    end

    Note over SR: Step 3: 參數校正
    SR->>SR: 檢查艦船是否被誤分類<br/>(ROC船出現在enemy → 移到roc)<br/>(敵船出現在roc → 移到enemy)
    SR->>SR: 移除使用者未提及的空陣列

    Note over SR: Step 4: 呼叫 Node.js API 取得座標
    SR->>NodeAPI: POST /import_scenario<br/>{enemy: ["052D"]}
    NodeAPI-->>SR: {enemy: [{name, lat, lon}],<br/>roc: [{name, lat, lon}]}

    Note over SR: Step 5: 繪製地圖
    SR->>MS: add_ships_to_map(ship_data, map_state)
    MS->>State: add_marker(location, popup,<br/>color, icon, shape)
    Note over State: 敵軍=紅色菱形, 國軍=藍色圓形

    SR->>State: create_map()
    Note over State: 建立 Folium Map<br/>注入 milsymbol.js (MIL-STD-2525)
    State->>FS: save scenario_map_{timestamp}.html
    State-->>SR: map object

    SR-->>User: {success: true,<br/>answer: "已繪製052D...",<br/>map_url: "/maps/scenario_map_xxx.html",<br/>ship_data: {...},<br/>parameters: {...}}
```

---

## 3. 開始兵推 → WTA 完成 → 查看武器分派

```mermaid
sequenceDiagram
    participant User as 使用者
    participant SR as scenario_routes.py
    participant DR as data_routes.py
    participant LLM as LLMService
    participant FB as FallbackHandler
    participant NodeAPI as Node.js CMO API
    participant MS as MapService
    participant State as MapState
    participant Config as config.json
    participant FS as /maps/

    Note over User,FS: === Phase 1: 開始兵推 ===
    User->>SR: POST /api/start_scenario<br/>{user_input: "開始進行兵推"}
    SR->>LLM: call_star_scenario(user_input)
    LLM-->>SR: {tool: "star_scenario"}
    SR->>NodeAPI: POST /star_scenario
    NodeAPI-->>SR: {success: true}
    SR-->>User: {answer: "模擬進行中，請稍候..."}

    Note over NodeAPI: Node.js 背景執行 WTA 模擬...

    Note over User,FS: === Phase 2: 模擬完成回呼 ===
    NodeAPI->>DR: POST /api/wta_completed<br/>{message: "模擬已完成"}
    DR->>DR: 更新所有 _STATES[*]<br/>simulation_completed = True<br/>completion_message = "模擬已完成"
    DR-->>NodeAPI: {received: true}

    Note over User,FS: === Phase 3: 查看武器分派結果 ===
    User->>DR: POST /api/get_wta<br/>{user_input: "查看武器分派結果"}
    DR->>LLM: call_get_wta(user_input)

    alt LLM 成功
        LLM-->>DR: {tool: "get_wta",<br/>parameters: {enemy: []}}
    else LLM 失敗
        LLM-->>DR: None
        DR->>FB: fallback_get_wta(user_input)
        FB-->>DR: {tool: "get_wta",<br/>parameters: {enemy: []}}
    end

    DR->>NodeAPI: POST /get_wta<br/>{enemy: []}
    NodeAPI-->>DR: [wta_results]<br/>{attack_wave, weapon, launched_number,<br/>launched_time, roc_location,<br/>enemy_location, roc_unit, enemy_unit}

    DR->>MS: add_wta_to_map(wta_results, map_state)
    MS->>MS: get_weapon_color(weapon_name)
    MS->>State: add_line(roc→enemy, color, popup)

    Note over DR: 檢查動畫設定
    DR->>Config: load config.json
    Config-->>DR: {enable_animation: true/false}

    alt 動畫啟用
        DR->>DR: 準備 wta_animation_data<br/>{wta_results, weapon_colors}
        DR->>State: create_map(wta_animation_data)
        Note over State: 注入 JavaScript 動畫控制器<br/>(播放/暫停/重置/速度調整)
    else 動畫關閉
        DR->>State: create_map()
        Note over State: 僅顯示靜態攻擊線
    end

    DR->>MS: generate_wta_table_html(wta_data)
    MS-->>DR: HTML table string

    State->>FS: save wta_map_{timestamp}.html
    DR-->>User: {success: true,<br/>answer: "武器分派結果...",<br/>map_url: "/maps/wta_map_xxx.html",<br/>wta_table_html: "<table>...",<br/>wta_data: [...]}
```

---

## 4. 顯示航跡 (Get Track)

```mermaid
sequenceDiagram
    participant User as 使用者
    participant DR as data_routes.py
    participant LLM as LLMService
    participant FB as FallbackHandler
    participant MS as MapService
    participant State as MapState
    participant FS as File System

    User->>DR: POST /api/get_track<br/>{user_input: "顯示航跡"}

    DR->>LLM: call_get_track(user_input)
    alt LLM 成功
        LLM-->>DR: {tool: "get_track"}
    else LLM 失敗
        LLM-->>DR: None
        DR->>FB: fallback_get_track(user_input)
        FB-->>DR: {tool: "get_track"}
    end

    DR->>FS: read track_data.json
    FS-->>DR: {ship: {enemy: {...}, roc: {...}}}

    Note over DR: 清除舊航跡
    DR->>State: tracks = []

    DR->>MS: add_tracks_to_map(track_data, map_state)

    loop 每艘艦船 (敵軍+國軍)
        MS->>State: add_line(polyline segments,<br/>color=紅/藍)
        MS->>State: add_marker(last_position,<br/>popup=ship_name)
    end

    DR->>State: create_map()
    Note over State: 智慧 Tooltip 方向判斷<br/>(根據航跡方向決定標籤位置)
    State->>FS: save track_map_{timestamp}.html

    DR-->>User: {success: true,<br/>answer: "已顯示航跡...",<br/>map_url: "/maps/track_map_xxx.html",<br/>track_data: {...},<br/>ship_count: N}
```

---

## 5. RAG 軍事問答 (Get Answer)

```mermaid
sequenceDiagram
    participant User as 使用者
    participant AR as answer_routes.py
    participant NodeAPI as Node.js RAG API

    User->>AR: POST /api/get_answer<br/>{user_input: "雄三飛彈的射程?",<br/>mode: "military_qa",<br/>model: "TAIDE8B"}

    AR->>AR: 組建 RAG 請求<br/>{stream: 0, model, messages:<br/>[{system, content}, {user, content}]}

    AR->>NodeAPI: POST /get_answer<br/>{stream: 0, model: "TAIDE8B",<br/>messages: [...]}
    NodeAPI-->>AR: {messages: [{role: "assistant",<br/>content: "雄三飛彈射程約150公里..."}],<br/>sources: [{content, score, path}],<br/>rag_id: "xxx"}

    AR->>AR: 擷取回答內容
    AR->>AR: 格式化前5筆來源<br/>(index, content_preview, score, path)

    AR-->>User: {success: true,<br/>answer: "雄三飛彈射程約150公里...",<br/>question: "雄三飛彈的射程?",<br/>sources: [...],<br/>rag_id: "xxx",<br/>show_rag_buttons: true}
```

---

## 6. 使用者回饋 (Feedback)

```mermaid
sequenceDiagram
    participant User as 使用者
    participant FR as feedback_routes.py
    participant FS as /feedbacks/

    Note over User,FS: === 提交回饋 ===
    User->>FR: POST /api/submit_feedback<br/>{question, answer,<br/>feedback_type: "negative",<br/>feedback_text: "答案不完整",<br/>sources, rag_id, datetime}

    FR->>FR: 驗證必填欄位<br/>(question, answer, feedback_type)
    FR->>FR: 產生 feedback_id (timestamp)
    FR->>FR: 附加 metadata<br/>(user_agent, ip_address)
    FR->>FS: save feedback_{id}.json
    FR-->>User: {success: true,<br/>feedback_id: "xxx"}

    Note over User,FS: === 查詢回饋 ===
    User->>FR: GET /api/get_feedbacks<br/>?limit=20&type=negative
    FR->>FS: read all feedback_*.json
    FR->>FR: 按時間排序 (新→舊)
    FR->>FR: 依 type 篩選
    FR->>FR: 計算統計<br/>(total, positive, negative, error)
    FR-->>User: {feedbacks: [...],<br/>count: N,<br/>stats: {total, positive, negative, error}}
```

---

## 7. COP 截圖 (Save COP)

```mermaid
sequenceDiagram
    participant User as 使用者
    participant CR as cop_routes.py
    participant FS as File System
    participant Selenium as Selenium Chrome
    participant MapFile as /maps/*.html

    User->>CR: POST /api/save_cop

    CR->>FS: 掃描 /maps/ 目錄<br/>找最新的 map HTML
    FS-->>CR: latest_map_file

    CR->>Selenium: 啟動 Chrome (headless)<br/>1920x1080
    CR->>Selenium: driver.get(file://map.html)
    CR->>Selenium: wait(COP_PAGE_LOAD_WAIT)

    alt 找到 .folium-map 元素
        CR->>Selenium: element.screenshot()
    else 找不到元素
        CR->>Selenium: driver.get_screenshot()
    end
    Selenium-->>CR: screenshot PNG bytes

    CR->>FS: save cops/cop_{timestamp}.png
    CR->>FS: save cops/cop_{timestamp}_meta.json<br/>(timestamp, map_file, markers, lines)

    Note over CR: 清理過期檔案<br/>(> FILE_RETENTION_DAYS)
    CR->>CR: base64 encode image

    CR-->>User: {filename: "cop_xxx.png",<br/>image_base64: "...",<br/>cop_path: "/cops/cop_xxx.png",<br/>metadata: {...}}
```

---

## 8. Session 管理 & 狀態隔離

```mermaid
sequenceDiagram
    participant Req as HTTP Request
    participant Helpers as helpers.py
    participant Config as config.py (_STATES)
    participant State as MapState

    Req->>Helpers: get_client_id()
    Helpers->>Helpers: 讀取 X-Client-ID header<br/>或 request body client_id
    Helpers->>Helpers: _sanitize_client_id(raw)<br/>(限80字元, 僅允許英數-_.)
    Helpers-->>Req: client_id

    Req->>Helpers: get_map_state()
    Helpers->>Config: acquire _STATE_LOCK

    alt client_id 已存在
        Config-->>Helpers: _STATES[client_id]
        Helpers->>Config: 更新 last_access 時間
    else client_id 不存在
        Note over Helpers: 檢查是否超過<br/>MAX_CONCURRENT_SESSIONS
        alt 超過上限
            Helpers->>Config: 找出最舊的<br/>SESSION_CLEANUP_BATCH 個 state
            Helpers->>Config: 刪除舊 states
        end
        Helpers->>State: new MapState()
        Helpers->>Config: _STATES[client_id] = {<br/>state: MapState(),<br/>last_access: now,<br/>simulation_completed: False}
    end

    Config-->>Helpers: release _STATE_LOCK
    Helpers-->>Req: MapState instance
```

---

## 9. LLM Function Calling 詳細流程

```mermaid
sequenceDiagram
    participant Route as Routes
    participant LLM as LLMService
    participant Ollama as Ollama API
    participant Parser as parser.py

    Route->>LLM: call_import_scenario<br/>(user_input, model, custom_prompt)

    LLM->>LLM: 組建 messages<br/>[{role: system, content: prompt},<br/>{role: user, content: input}]

    LLM->>LLM: 定義 tools<br/>[{type: function,<br/>function: {name, parameters}}]

    LLM->>Ollama: POST /api/chat<br/>{model, messages, tools, stream: false}

    Note over Ollama: Ollama 執行 Function Calling<br/>辨識使用者意圖並提取參數

    alt 正常回應 (有 tool_calls)
        Ollama-->>LLM: {message: {tool_calls: [{<br/>function: {name, arguments}}]}}

        LLM->>LLM: 取出 function_name<br/>取出 arguments (string)

        LLM->>Parser: parse_function_arguments(args_str)
        Note over Parser: 1. JSON string → dict<br/>2. 修正空陣列: "[]" → []<br/>3. 解析 JSON 陣列字串<br/>4. 解包不正確的包裝
        Parser-->>LLM: parsed_dict

        LLM-->>Route: {tool: function_name,<br/>parameters: parsed_dict}

    else 無 tool_calls (純文字回應)
        Ollama-->>LLM: {message: {content: "..."}}
        LLM-->>Route: None

    else 逾時 (LLM_API_TIMEOUT)
        Ollama-->>LLM: Timeout Error
        LLM-->>Route: None

    else 連線錯誤
        Ollama-->>LLM: Connection Error
        LLM-->>Route: None
    end
```

---

## 10. 完整使用者操作流程 (End-to-End)

```mermaid
sequenceDiagram
    actor User as 使用者
    participant App as Flask Application
    participant LLM as LLM + Fallback
    participant API as Node.js CMO API
    participant Map as MapState + MapService

    Note over User,Map: ═══ Step 1: 匯入想定 ═══
    User->>App: "繪製052D和沱江艦座標"
    App->>LLM: 解析意圖
    LLM-->>App: {enemy: ["052D"], roc: ["沱江"]}
    App->>API: POST /import_scenario
    API-->>App: 艦船座標資料
    App->>Map: 繪製艦船標記
    Map-->>App: 地圖 HTML
    App-->>User: 顯示艦船位置地圖

    Note over User,Map: ═══ Step 2: 開始兵推 ═══
    User->>App: "開始進行兵推"
    App->>LLM: 確認為開始指令
    App->>API: POST /star_scenario
    App-->>User: "模擬進行中..."

    Note over API: 背景執行 WTA 模擬...
    API->>App: POST /wta_completed (回呼)

    Note over User,Map: ═══ Step 3: 查看武器分派 ═══
    User->>App: "查看武器分派結果"
    App->>LLM: 解析目標艦船
    App->>API: POST /get_wta
    API-->>App: WTA 結果 (攻擊波次、武器、座標)
    App->>Map: 繪製攻擊線 + 動畫
    Map-->>App: 地圖 HTML + 動畫控制器
    App-->>User: 顯示 WTA 地圖 + 結果表格

    Note over User,Map: ═══ Step 4: 顯示航跡 ═══
    User->>App: "顯示航跡"
    App->>LLM: 確認為航跡指令
    App->>Map: 讀取 track_data.json<br/>繪製軌跡折線 + 當前位置
    Map-->>App: 地圖 HTML
    App-->>User: 顯示航跡地圖

    Note over User,Map: ═══ Step 5: 軍事問答 ═══
    User->>App: "雄三飛彈射程多少?"
    App->>API: POST /get_answer (RAG)
    API-->>App: 回答 + 來源文件
    App-->>User: 顯示回答 + 參考來源

    Note over User,Map: ═══ Step 6: 提交回饋 ═══
    User->>App: 回饋: "答案不完整"
    App->>App: 儲存至 /feedbacks/
    App-->>User: 回饋已記錄

    Note over User,Map: ═══ Step 7: COP 截圖 ═══
    User->>App: "截取 COP"
    App->>App: Selenium 截圖最新地圖
    App-->>User: COP 截圖 (Base64 PNG)
```
