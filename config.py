"""
配置檔案 - 集中管理系統所有配置常數
用途：定義 API URL、目錄路徑、飛彈顏色映射等全域配置
"""
import os
import threading

# ==================== API 配置 ====================
# Ollama LLM API 端點 URL
OLLAMA_URL = "http://localhost:11434/api/generate"

# Node.js 後端 API 基礎 URL
NODE_API_BASE = "http://localhost:3000/api/v1"

# ==================== 目錄配置 ====================
# 地圖 HTML 檔案儲存目錄
MAP_DIR = "maps"

# 使用者反饋資料儲存目錄
FEEDBACK_DIR = "feedbacks"

# COP（Common Operational Picture，共同作戰圖像）截圖儲存目錄
COP_DIR = "cops"

# ==================== 配置檔案路徑 ====================
# SYSTEM PROMPT 配置檔案路徑（儲存各種 LLM prompt 模板）
PROMPTS_CONFIG_FILE = "prompts_config.json"

# 系統配置檔案路徑（儲存系統設定，如顯示選項等）
CONFIG_FILE = "config.json"

# ==================== 飛彈顏色映射 ====================
# 用途：在地圖上以不同顏色標示不同類型的飛彈攻擊線
# 格式：飛彈名稱 -> 顏色代碼（HEX）
WEAPON_COLORS = {
    "雄三飛彈": "#FF0000",      # 紅色
    "雄風三型": "#FF0000",
    "標準二型飛彈": "#0066FF",  # 藍色
    "標準二型": "#0066FF",
    "雄二飛彈": "#FF6600",      # 橙色
    "雄風二型": "#FF6600",
    "天劍飛彈": "#9900CC",      # 紫色
    "魚叉飛彈": "#00CC66",      # 綠色
}

# ==================== 會話狀態管理 ====================
# 用途：儲存每個客戶端的地圖狀態（多分頁/多會話隔離）
# 格式：client_id -> {"state": MapState 實例, "last_access": 時間戳}
_STATE_LOCK = threading.Lock()  # 執行緒安全鎖
_STATES = {}

# ==================== 初始化函數 ====================
def ensure_directories():
    """
    確保所有必要的目錄存在
    用途：在應用程式啟動時創建必要的目錄結構
    """
    os.makedirs(MAP_DIR, exist_ok=True)
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    os.makedirs(COP_DIR, exist_ok=True)
    print(f"✅ 目錄初始化完成: {MAP_DIR}, {FEEDBACK_DIR}, {COP_DIR}")
