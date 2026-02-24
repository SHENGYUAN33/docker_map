"""
主應用程式入口 - Flask API v6.0
用途：啟動 Flask 應用程式，註冊所有路由藍圖，初始化系統配置

重構說明：
- 原始檔案: flask_v6.py (3356 行)
- 重構後: 模組化設計，主程式只負責應用初始化和啟動
- 所有業務邏輯已拆分到 models/, services/, handlers/, utils/, routes/ 模組

作者：軍事兵推 AI 系統團隊
版本：v6.0 Refactored
日期：2026-01
"""

import sys
import os

# 修正 Windows 終端 emoji 編碼問題（cp950 不支援 emoji）
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask import Flask
from flask_cors import CORS
from routes import register_blueprints
from config import ensure_directories, FLASK_HOST, FLASK_PORT, FLASK_DEBUG, CONFIG_DEFAULTS
from services import save_config

# ==================== 創建 Flask 應用程式 ====================
# 用途：初始化 Flask app 並配置靜態文件目錄
app = Flask(
    __name__,
    static_folder='static',      # 靜態文件目錄（JavaScript、CSS、圖片等）
    static_url_path='/static'    # 靜態文件 URL 前綴
)

# ==================== 配置 CORS ====================
# 用途：允許跨域請求（前端可能部署在不同域名/端口）
# 這對於前後端分離的應用程式是必要的
CORS(app)

# ==================== 初始化系統配置 ====================
# 用途：確保所有必要的目錄存在
# - maps/      : 儲存生成的地圖 HTML 檔案
# - feedbacks/ : 儲存使用者反饋資料
# - cops/      : 儲存 COP 截圖
print("🔧 正在初始化系統目錄...")
ensure_directories()

# 重置 config.json 為預設值（確保每次啟動回到初始狀態）
# 保留不應被重置的持久設定（如 cesium_ion_token）
from services import load_config as _load_existing
_existing = _load_existing()
_reset_config = dict(CONFIG_DEFAULTS)
_persistent_keys = ["cesium_ion_token", "custom_layers"]
for _key in _persistent_keys:
    if _key in _existing and _existing[_key]:
        _reset_config[_key] = _existing[_key]
save_config(_reset_config)

# ==================== 註冊所有路由藍圖 ====================
# 用途：將所有功能模組的路由註冊到 Flask app
# 藍圖包括：
# - scenario_bp  : 場景管理（匯入、啟動、清除）
# - data_bp      : 數據查詢（武器分派、航跡、狀態檢查）
# - answer_bp    : RAG 問答
# - feedback_bp  : 反饋管理
# - cop_bp       : COP 管理
# - prompt_bp    : Prompt 配置管理
# - admin_bp     : 系統管理
# - static_bp    : 靜態文件服務
print("🔗 正在註冊路由藍圖...")
register_blueprints(app)

# ==================== 啟動應用程式 ====================
if __name__ == '__main__':
    print("""
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
║  核心功能：                                                   ║
║  ✅ 功能一: 兵棋場景匯入 (POST /api/import_scenario)         ║
║  ✅ 功能二: 兵棋模擬啟動 (POST /api/start_scenario)          ║
║  ✅ 功能三: 武器分派查詢 (POST /api/get_wta)                 ║
║  ✅ 功能四: 航跡繪製     (POST /api/get_track)               ║
║  ✅ 功能五: 軍事問答     (POST /api/get_answer)              ║
║  ✅ 功能六: 反饋管理     (POST /api/submit_feedback)         ║
║  ✅ 功能七: COP 管理     (POST /api/save_cop)                ║
║  ✅ 功能八: Prompt 管理  (GET/POST /api/prompts/*)           ║
╠═══════════════════════════════════════════════════════════════╣
║  輔助功能：                                                   ║
║  🔍 健康檢查: GET  /health                                   ║
║  🗑️  清除地圖: POST /api/clear_map                          ║
║  ⚙️  系統設置: GET/POST /api/admin/settings                  ║
╠═══════════════════════════════════════════════════════════════╣
║  🌐 服務地址: http://localhost:5000                          ║
║  📖 API 文檔: 請參閱 API_ENDPOINTS.md                        ║
║  📝 使用指南: 請參閱 USAGE_GUIDE.md                          ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # 啟動 Flask 開發伺服器
    # host='0.0.0.0' : 允許外部訪問（不僅限於 localhost）
    # port=5000      : 監聽端口 5000
    # debug=True     : 開啟調試模式（自動重載、詳細錯誤信息）
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
