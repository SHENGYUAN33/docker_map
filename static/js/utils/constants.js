/**
 * 常數定義模組
 * 定義系統中使用的所有常數
 */

// API 端點配置
export const API_BASE = 'http://localhost:5000';
export const NODE_API_BASE = 'http://localhost:3000';

// LLM 模型資訊數據庫
export const LLM_MODELS = {
  'ollama-llama3.2:3b': {
    name: 'Llama 3.2 3B',
    provider: 'Ollama',
    size: '2.0 GB',
    speed: '快速',
    quality: '良好'
  },
  'ollama-mistral:7b': {
    name: 'Mistral 7B',
    provider: 'Ollama',
    size: '4.1 GB',
    speed: '中等',
    quality: '優秀'
  },
  'ollama-llama3:8b': {
    name: 'Llama 3 8B',
    provider: 'Ollama',
    size: '4.7 GB',
    speed: '中等',
    quality: '優秀'
  },
  'ollama-llama3.1:70b': {
    name: 'Llama 3.1 70B',
    provider: 'Ollama',
    size: '40 GB',
    speed: '較慢',
    quality: '極佳'
  }
};

// 模式名稱映射
export const MODE_NAMES = {
  'import_scenario': '兵棋場景匯入',
  'start_scenario': '兵棋模擬',
  'get_wta': '攻擊配對線繪製',
  'get_track': '軌跡繪製功能',
  'text_generation': '軍事行動準據文本生成',
  'military_qa': '軍事準則問答'
};

// 模式提示訊息
export const MODE_TIPS = {
  'import_scenario': '💡 支援智能參數提取，例如繪製1101的座標',
  'start_scenario': '💡 請輸入:兵棋模擬，\n將啟動 CMO 模擬，請等待約武器分派計算',
  'get_wta': '💡 請輸入:攻擊配對線繪製',
  'get_track': '💡 請輸入：顯示航跡、繪製軌跡等指令',
  'text_generation': '💡 軍事行動準據文本，例如:雄三飛彈射程?',
  'military_qa': '💡 提問任何軍事相關問題，例如：掩護種類有哪些？'
};

// 武器分派表格欄位
export const WTA_TABLE_COLUMNS = [
  { "attack_wave": "波次" },
  { "enemy_unit": "敵艦船型" },
  { "roc_unit": "我方單位" },
  { "weapon": "飛彈種類" },
  { "launched_number": "發射數量" },
  { "launched_time": "發射時間" }
];

// 分隔線設置
export const SPLITTER_MIN_MAP = 160;        // 地圖最小高度
export const SPLITTER_EXTRA_GAP = 30;       // 安全緩衝，避免壓到輸入列

// 輪詢間隔（毫秒）
export const POLLING_INTERVAL = 2000;       // 兵推模擬輪詢間隔
export const SIMULATION_STATUS_INTERVAL = 3000;  // 模擬狀態監聽間隔

// 通知顯示時間（毫秒）
export const NOTIFICATION_DURATION = 3000;

// Client ID 存儲鍵
export const CLIENT_ID_KEY = 'cmo_client_id';
