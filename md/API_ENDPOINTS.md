# API 端點清單

## 快速參考

本文檔列出所有可用的 API 端點及其用途。

---

## 🎮 場景管理 (scenario_bp)

### POST /api/import_scenario
**場景匯入**
- 根據用戶指令在地圖上標示船艦位置
- 請求體: `{ user_input, llm_model, prompt_config }`
- 回應: `{ success, answer, map_url, ship_data, parameters, llm_model_used }`

### POST /api/start_scenario
**啟動兵棋模擬**
- 通知中科院 API 開始執行武器分派演算
- 請求體: `{ user_input, llm_model, prompt_config }`
- 回應: `{ success, answer, status, note }`

### POST /api/clear_map
**清除地圖**
- 清除當前會話的所有地圖元素
- 回應: `{ success, message }`

---

## 📊 數據查詢 (data_bp)

### POST /api/get_wta
**武器目標分派查詢**
- 查詢並繪製武器分派結果（攻擊配對線）
- 請求體: `{ user_input, llm_model, prompt_config }`
- 回應: `{ success, answer, map_url, wta_table_html, wta_data }`

### POST /api/wta_completed
**WTA 完成回調**
- 接收中科院系統的完成通知（內部 API）
- 請求體: `{ message }`
- 回應: `{ success, received, message }`

### POST /api/get_track
**航跡繪製**
- 繪製所有船艦的航行軌跡
- 請求體: `{ user_input, llm_model, prompt_config }`
- 回應: `{ success, answer, map_url, track_data, ship_count, llm_model_used }`

### GET /api/check_simulation_status/:simulation_id
**檢查模擬狀態**
- 檢查特定模擬的執行狀態（預留功能）
- 路徑參數: `simulation_id`
- 回應: `{ status, progress, message }`

---

## 💬 RAG 問答 (answer_bp)

### POST /api/get_answer
**軍事問答/文本生成**
- 調用 RAG 系統回答軍事相關問題
- 請求體: `{ user_input, mode, model, system_prompt }`
- 回應: `{ success, answer, question, sources, rag_id, datetime, finish_reason, show_rag_buttons }`

---

## 📝 反饋管理 (feedback_bp)

### POST /api/submit_feedback
**提交用戶反饋**
- 保存用戶對 AI 回答的反饋
- 請求體: `{ question, answer, feedback_type, feedback_text, sources, rag_id, datetime }`
- 回應: `{ success, message, feedback_id, saved_feedback_text_length }`

### GET /api/get_feedbacks
**獲取反饋列表**
- 查詢最近的用戶反饋記錄
- 查詢參數: `limit` (default: 20), `type` (positive/negative/error/all)
- 回應: `{ success, feedbacks, count, stats }`

---

## 📸 COP 管理 (cop_bp)

### POST /api/save_cop
**保存 COP 截圖**
- 使用 Selenium 截取當前地圖
- 回應: `{ success, message, filename, image_base64, cop_path, metadata }`

### GET /cops/:filename
**服務 COP 文件**
- 提供 COP 截圖文件下載
- 路徑參數: `filename`
- 回應: 文件內容

---

## ⚙️ Prompt 管理 (prompt_bp)

### GET /api/prompts/list
**獲取配置列表**
- 返回所有可用的 Prompt 配置
- 回應: `{ success, configs, default_config }`

### GET /api/prompts/get
**獲取配置詳情**
- 返回特定配置的完整內容
- 查詢參數: `config_name`
- 回應: `{ success, config }`

### POST /api/prompts/save
**保存配置**
- 保存或更新 Prompt 配置
- 請求體: `{ config_name, prompts }`
- 回應: `{ success, message }`

### POST /api/prompts/create
**創建新配置**
- 創建新的 Prompt 配置（複製預設）
- 請求體: `{ config_name }`
- 回應: `{ success, message }`

### DELETE /api/prompts/delete
**刪除配置**
- 刪除指定的 Prompt 配置
- 查詢參數: `config_name`
- 回應: `{ success, message }`

### POST /api/prompts/rename
**重命名配置**
- 重命名 Prompt 配置
- 請求體: `{ old_name, new_name }`
- 回應: `{ success, message }`

---

## 🔧 系統管理 (admin_bp)

### GET /health
**健康檢查**
- 檢查系統運行狀態
- 回應: `{ status, message, client_id, map_markers, map_lines, active_states }`

### GET /api/admin/settings
**獲取系統設置**
- 返回當前系統配置
- 回應: `{ success, settings }`

### POST /api/admin/settings
**保存系統設置**
- 保存系統配置
- 請求體: `{ show_source_btn, enable_animation, ... }`
- 回應: `{ success, settings }`

---

## 📁 靜態文件 (static_bp)

### GET /maps/:filename
**服務地圖文件**
- 提供地圖 HTML 文件訪問
- 路徑參數: `filename`
- 回應: 文件內容

### GET /
**首頁**
- 返回前端應用入口頁面
- 回應: index_v6.html

---

## 📋 請求格式示例

### 場景匯入示例
```json
POST /api/import_scenario
{
  "user_input": "繪製052D和055的座標",
  "llm_model": "llama3.2:3b",
  "prompt_config": "預設配置"
}
```

### RAG 問答示例
```json
POST /api/get_answer
{
  "user_input": "雄三飛彈的射程是多少？",
  "mode": "military_qa",
  "model": "TAIDE8B",
  "system_prompt": "請回答軍事問題"
}
```

### 提交反饋示例
```json
POST /api/submit_feedback
{
  "question": "雄三飛彈的射程是多少？",
  "answer": "雄三飛彈的射程約為 300 公里...",
  "feedback_type": "positive",
  "feedback_text": "回答很詳細",
  "sources": [...],
  "rag_id": "abc123",
  "datetime": "2026-01-30T10:00:00"
}
```

---

## 🔐 認證與授權

目前系統使用基於 `X-Client-ID` 標頭的會話隔離機制：
- 每個瀏覽器分頁自動生成唯一的 client_id
- 不同會話的地圖狀態完全隔離
- 無需額外的用戶認證

---

## ⚠️ 錯誤碼

所有 API 遵循統一的錯誤格式：

```json
{
  "success": false,
  "error": "錯誤訊息描述"
}
```

常見 HTTP 狀態碼：
- `200 OK` - 請求成功
- `400 Bad Request` - 請求參數錯誤
- `404 Not Found` - 資源不存在
- `500 Internal Server Error` - 服務器內部錯誤

---

**最後更新**: 2026-01-30
**API 版本**: v2
**總端點數**: 22
