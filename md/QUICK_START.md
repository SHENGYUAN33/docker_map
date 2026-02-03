# 🚀 快速啟動指南 - 軍事兵推 AI 系統 v6.0 (重構版)

## 📋 目錄
1. [系統要求](#系統要求)
2. [啟動步驟](#啟動步驟)
3. [驗證測試](#驗證測試)
4. [常見問題](#常見問題)
5. [目錄結構](#目錄結構)

---

## 系統要求

### 必需軟體
- Python 3.8+
- Node.js 14+ (如果使用 Node 後端)
- 現代瀏覽器（Chrome 61+, Firefox 60+, Safari 11+, Edge 16+）

### Python 依賴套件
```bash
pip install flask flask-cors folium branca requests selenium
```

---

## 啟動步驟

### 方式 1：使用重構後的系統（推薦）

#### 步驟 1：啟動 Flask 後端
```bash
cd "c:\Users\User\Desktop\20260126\重構"
python app.py
```

**預期輸出：**
```
╔═══════════════════════════════════════════════════════════════╗
║           🚀 軍事兵推 AI 系統 v6.0 啟動中...                 ║
╠═══════════════════════════════════════════════════════════════╣
║  系統架構：模組化重構版本                                     ║
║  ├─ models/      : 數據模型層（MapState）                    ║
║  ├─ services/    : 業務邏輯層（LLM、地圖、配置服務）         ║
║  ├─ handlers/    : 處理器層（Fallback 處理器）              ║
║  ├─ utils/       : 工具函數層（解析器、輔助函數）            ║
║  └─ routes/      : 路由層（22 個 API 端點）                  ║
╠═══════════════════════════════════════════════════════════════╣
║  🌐 服務地址: http://localhost:5000                          ║
╚═══════════════════════════════════════════════════════════════╝
```

#### 步驟 2：訪問前端
打開瀏覽器訪問：
```
http://localhost:5000
```

### 方式 2：使用原始系統（備份方案）

如果重構版本有問題，可以使用原始版本：

```bash
cd "c:\Users\User\Desktop\20260126\重構"
python flask_v6.py
```

然後直接打開 `index_v6.html` 文件。

---

## 驗證測試

### 1. 健康檢查
訪問：`http://localhost:5000/health`

**預期響應：**
```json
{
  "status": "ok",
  "message": "Flask API v2 is running"
}
```

### 2. 前端界面檢查
訪問：`http://localhost:5000`

**檢查項目：**
- ✅ 頁面正常載入（沒有 404 錯誤）
- ✅ 左側功能列顯示正常
- ✅ 右上角管理按鈕顯示正常
- ✅ LLM 模型選擇器顯示正常
- ✅ 上下分隔線可以拖曳
- ✅ 控制台沒有 JavaScript 錯誤

### 3. 基本功能測試

#### 測試 1：清除地圖
1. 點擊「清除地圖」按鈕
2. 應該看到成功通知：「✅ 地圖已清除」

#### 測試 2：LLM 模型選擇
1. 點擊 LLM 模型選擇器
2. 應該看到 4 個選項：
   - llama3.2:3b (Ollama)
   - hermes3:8b (Ollama)
   - hermes-3-llama-3.1:8b (Ollama)
   - Phi-4 (Ollama)

#### 測試 3：Prompt 配置管理
1. 點擊側邊欄的「Prompt 配置」區塊
2. 應該看到配置選擇器
3. 點擊「管理 Prompt 配置」按鈕
4. 應該彈出 Prompt 管理面板

#### 測試 4：系統設置
1. 點擊右上角「系統設置」按鈕
2. 應該彈出系統設置面板
3. 檢查「顯示來源按鈕」和「啟用動畫」選項

### 4. 核心功能測試（需要後端 API）

#### 測試 5：場景匯入
1. 在輸入框輸入：`繪製解放軍054A和055`
2. 點擊「發送」按鈕
3. 應該看到 LLM 解析和 API 調用過程
4. 如果後端 API 正常，應該生成地圖

#### 測試 6：武器分派查詢
1. 在輸入框輸入：`查看所有敵軍的武器分派結果`
2. 點擊「發送」按鈕
3. 應該看到武器分派結果

---

## 常見問題

### Q1: 瀏覽器顯示 "Cannot import module 'routes'"
**原因：** Python 找不到 routes 模組

**解決方案：**
```bash
# 確認當前目錄
cd "c:\Users\User\Desktop\20260126\重構"

# 確認 routes 目錄存在
dir routes

# 重新啟動
python app.py
```

### Q2: 前端顯示 404 錯誤（JavaScript 文件）
**原因：** 靜態文件路徑錯誤

**解決方案：**
1. 確認 `static/js/` 目錄存在
2. 確認 `static/js/main.js` 文件存在
3. 檢查瀏覽器控制台的錯誤訊息
4. 確保使用 `http://localhost:5000` 訪問（不要直接打開 HTML 文件）

### Q3: 前端界面與原版不一致
**原因：** CSS 可能未正確載入

**解決方案：**
1. 清除瀏覽器緩存（Ctrl + F5）
2. 檢查 `templates/index.html` 文件是否完整
3. 檢查瀏覽器控制台是否有錯誤

### Q4: JavaScript 模組載入失敗
**原因：** ES6 模組需要通過 HTTP 服務器運行

**解決方案：**
- ❌ 不要直接打開 `templates/index.html` 文件
- ✅ 必須通過 Flask 服務器訪問：`http://localhost:5000`

### Q5: 地圖不顯示
**可能原因：**
1. 後端 Node.js API 未啟動
2. Ollama LLM 未啟動
3. 網絡連接問題

**解決方案：**
```bash
# 檢查 Node.js API（如果使用）
# 確認 http://localhost:3000 是否可訪問

# 檢查 Ollama API
# 確認 http://localhost:11434 是否可訪問

# 查看 Flask 後端日誌
# 檢查是否有錯誤訊息
```

---

## 目錄結構

### 重要文件和目錄

```
重構/
├── app.py                          # ⭐ 主應用程式入口（從這裡啟動）
├── config.py                       # 全域配置
│
├── backup/                         # 📦 原始文件備份
│   ├── flask_v6.py.backup_*
│   └── index_v6.html.backup_*
│
├── models/                         # 數據模型層
│   └── map_state.py
│
├── services/                       # 業務邏輯層
│   ├── config_service.py
│   ├── llm_service.py
│   └── map_service.py
│
├── handlers/                       # 處理器層
│   └── fallback_handler.py
│
├── utils/                          # 工具函數層
│   ├── parser.py
│   └── helpers.py
│
├── routes/                         # 路由層
│   ├── __init__.py                # ⭐ 路由註冊中心
│   ├── scenario_routes.py
│   ├── data_routes.py
│   ├── answer_routes.py
│   ├── feedback_routes.py
│   ├── cop_routes.py
│   ├── prompt_routes.py
│   ├── admin_routes.py
│   └── static_routes.py
│
├── templates/                      # HTML 模板
│   └── index.html                 # ⭐ 主頁面
│
├── static/js/                      # 前端 JavaScript
│   ├── main.js                    # ⭐ 主入口
│   ├── modules/                   # 功能模組
│   │   ├── api-client.js
│   │   ├── ui-manager.js
│   │   ├── map-manager.js
│   │   ├── message-manager.js
│   │   ├── prompt-manager.js
│   │   ├── feedback-manager.js
│   │   ├── cop-manager.js
│   │   ├── file-manager.js
│   │   ├── settings-manager.js
│   │   └── simulation-manager.js
│   └── utils/                     # 工具模組
│       ├── constants.js
│       └── helpers.js
│
├── maps/                           # 生成的地圖文件
├── feedbacks/                      # 反饋資料
├── cops/                           # COP 截圖
│
└── 📚 文檔文件
    ├── CODE_MAPPING.md            # ⭐ 新舊程式碼對照表
    ├── QUICK_START.md             # ⭐ 本文件
    ├── REFACTORING_SUMMARY.md     # 後端重構總結
    ├── USAGE_GUIDE.md             # 使用指南
    ├── ROUTES_README.md           # 路由藍圖說明
    ├── API_ENDPOINTS.md           # API 端點參考
    └── FRONTEND_REFACTORING.md    # 前端重構說明
```

---

## 📚 相關文檔

| 文檔 | 用途 |
|------|------|
| [CODE_MAPPING.md](./CODE_MAPPING.md) | ⭐ 新舊程式碼對照表（檢查遺漏） |
| [QUICK_START.md](./QUICK_START.md) | ⭐ 快速啟動指南（本文件） |
| [USAGE_GUIDE.md](./USAGE_GUIDE.md) | 詳細使用指南 |
| [API_ENDPOINTS.md](./API_ENDPOINTS.md) | API 端點參考 |
| [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) | 後端重構總結 |
| [ROUTES_README.md](./ROUTES_README.md) | 路由藍圖說明 |
| [FRONTEND_REFACTORING.md](./FRONTEND_REFACTORING.md) | 前端重構說明 |

---

## 🎉 恭喜！

如果您完成了以上所有步驟，您的軍事兵推 AI 系統 v6.0（重構版）已經成功啟動！

### 下一步：
1. 📖 閱讀 [CODE_MAPPING.md](./CODE_MAPPING.md) 了解詳細的代碼對照
2. 🧪 進行完整的功能測試
3. 📝 根據需要自定義配置
4. 🚀 開始使用系統

### 需要幫助？
- 檢查瀏覽器控制台（F12）的錯誤訊息
- 檢查 Flask 後端日誌
- 參閱相關文檔

---

**重構版本：** v6.0 Refactored
**重構日期：** 2026-01-30
**維護團隊：** 軍事兵推 AI 系統團隊

✨ 享受全新的模組化架構帶來的便利！
