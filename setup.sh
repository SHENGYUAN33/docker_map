#!/bin/bash
# ================================================================
# 軍事兵推 AI 系統 — 部署腳本
# 用途：檢查環境、安裝依賴、生成配置檔案
# 用法：bash setup.sh
# ================================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 計數器
WARN_COUNT=0
ERR_COUNT=0

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_ok() {
    echo -e "  ${GREEN}[OK]${NC} $1"
}

print_warn() {
    echo -e "  ${YELLOW}[WARN]${NC} $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

print_err() {
    echo -e "  ${RED}[ERR]${NC} $1"
    ERR_COUNT=$((ERR_COUNT + 1))
}

# ==================== 1. 檢查執行環境 ====================
print_header "1. 檢查執行環境"

# Python
if command -v python3 &> /dev/null; then
    PY_CMD="python3"
elif command -v python &> /dev/null; then
    PY_CMD="python"
else
    print_err "Python 未安裝。請安裝 Python 3.10+：https://www.python.org/downloads/"
    PY_CMD=""
fi

if [ -n "$PY_CMD" ]; then
    PY_VER=$($PY_CMD --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        print_ok "Python $PY_VER（命令: $PY_CMD）"
    else
        print_warn "Python $PY_VER 版本較低，建議 3.10+（命令: $PY_CMD）"
    fi
fi

# Node.js
if command -v node &> /dev/null; then
    NODE_VER=$(node --version 2>&1)
    NODE_MAJOR=$(echo "$NODE_VER" | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        print_ok "Node.js $NODE_VER"
    else
        print_warn "Node.js $NODE_VER 版本較低，建議 v18+"
    fi
else
    print_err "Node.js 未安裝。請安裝 Node.js 18+：https://nodejs.org/"
fi

# Ollama
if command -v ollama &> /dev/null; then
    print_ok "Ollama 已安裝"
else
    print_err "Ollama 未安裝。請安裝：https://ollama.com/download"
fi

# ==================== 2. 安裝 Python 依賴 ====================
print_header "2. 安裝 Python 依賴"

if [ -n "$PY_CMD" ] && [ -f "requirements.txt" ]; then
    echo "  執行: pip install -r requirements.txt"
    $PY_CMD -m pip install -r requirements.txt --quiet 2>&1 | while read line; do echo "    $line"; done
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_ok "Python 依賴安裝完成"
    else
        print_err "Python 依賴安裝失敗，請手動執行: pip install -r requirements.txt"
    fi
else
    print_warn "跳過 Python 依賴安裝（Python 未安裝或 requirements.txt 不存在）"
fi

# ==================== 3. 建立 .env ====================
print_header "3. 建立環境變數檔"

if [ -f ".env" ]; then
    print_ok ".env 已存在，跳過"
elif [ -f ".env.example" ]; then
    cp .env.example .env
    print_ok "已從 .env.example 建立 .env"
else
    print_warn ".env.example 不存在，跳過"
fi

# ==================== 4. 建立 system_config.json ====================
print_header "4. 建立系統配置"

if [ -f "system_config.json" ]; then
    print_ok "system_config.json 已存在，跳過"
else
    cat > system_config.json << 'SYSCONFIG_EOF'
{
  "api_settings": {
    "api_mode": "local",
    "real_api": {
      "base_url": "https://your-real-api-server.com",
      "timeout": 300,
      "endpoints": {
        "import_scenario": "/import_scenario",
        "star_scenario": "/start_scenario",
        "get_wta": "/get_wta",
        "get_answer": "/get_answer",
        "get_track": "/get_track"
      }
    },
    "local_api": {
      "base_url": "http://localhost:3000/api/v1",
      "timeout": 300,
      "endpoints": {
        "import_scenario": "/import_scenario",
        "star_scenario": "/star_scenario",
        "get_wta": "/get_wta",
        "get_answer": "/get_answer",
        "get_track": "/get_track"
      }
    },
    "local_data": {
      "db_file": "db_v2.json",
      "track_file": "track_data.json",
      "mock_responses_dir": "mock_responses"
    }
  },
  "llm_settings": {
    "active_provider": "ollama",
    "providers": {
      "ollama": {
        "name": "Ollama",
        "base_url": "http://localhost:11434",
        "chat_endpoint": "/api/chat",
        "timeout": 300,
        "default_model": "llama3.2:3b",
        "models": [
          {
            "id": "llama3.2:3b",
            "name": "Llama 3.2 3B",
            "size": "2.0 GB",
            "speed": "快速",
            "quality": "良好"
          },
          {
            "id": "qwen2.5:7b",
            "name": "Qwen 2.5 7B（支援tools，中文強）",
            "size": "4.7 GB",
            "speed": "中等",
            "quality": "優秀",
            "supports_tools": true
          },
          {
            "id": "llama3.1:8b",
            "name": "Llama 3.1 8B（支援tools）",
            "size": "4.7 GB",
            "speed": "中等",
            "quality": "優秀",
            "supports_tools": true
          },
          {
            "id": "mistral:7b",
            "name": "Mistral 7B",
            "size": "4.1 GB",
            "speed": "中等",
            "quality": "優秀"
          },
          {
            "id": "llama3.1:70b",
            "name": "Llama 3.1 70B",
            "size": "40 GB",
            "speed": "較慢",
            "quality": "極佳",
            "supports_tools": true
          }
        ]
      },
      "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com",
        "chat_endpoint": "/v1/chat/completions",
        "timeout": 120,
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4",
        "models": [
          { "id": "gpt-4", "name": "GPT-4", "speed": "中等", "quality": "極佳" },
          { "id": "gpt-4o", "name": "GPT-4o", "speed": "快速", "quality": "極佳" }
        ]
      },
      "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "chat_endpoint": "/v1/messages",
        "timeout": 120,
        "api_key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-5-20250929",
        "models": [
          { "id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5", "speed": "快速", "quality": "極佳" },
          { "id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5", "speed": "極快", "quality": "良好" }
        ]
      }
    }
  },
  "rag_settings": {
    "default_mode": "military_qa",
    "default_model": "TAIDE8B",
    "stream": 0,
    "max_sources": 5
  }
}
SYSCONFIG_EOF
    print_ok "已生成 system_config.json（local mode + ollama）"
fi

# ==================== 5. 檢查 Ollama 模型 ====================
print_header "5. 檢查 Ollama 模型"

if command -v ollama &> /dev/null; then
    # 嘗試連接 Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null)
        if echo "$MODELS" | grep -q "llama3.2:3b"; then
            print_ok "llama3.2:3b 模型已下載"
        else
            print_warn "llama3.2:3b 模型未下載，請執行: ollama pull llama3.2:3b"
        fi
    else
        print_warn "Ollama 服務未運行。請先執行 'ollama serve'，然後下載模型: ollama pull llama3.2:3b"
    fi
else
    print_warn "跳過模型檢查（Ollama 未安裝）"
fi

# ==================== 6. 檢查離線資源 ====================
print_header "6. 檢查離線資源"

# 離線地圖圖磚
if [ -d "tiles/osm" ]; then
    TILE_COUNT=$(find tiles/ -name "*.png" 2>/dev/null | wc -l)
    print_ok "離線地圖圖磚存在（${TILE_COUNT} 個圖磚檔案）"
else
    print_warn "tiles/ 目錄不存在 — 離線地圖底圖將為空白（連網時自動使用線上圖磚）"
    echo "        取得方式：從現有部署環境複製 tiles/ 目錄"
fi

# Cesium 3D
if [ -d "static/cesium/Cesium" ]; then
    print_ok "Cesium 3D 離線資源存在"
else
    print_warn "static/cesium/ 不存在 — 3D 地球儀功能不可用（2D 地圖不受影響）"
    echo "        取得方式：從現有環境複製，或從 https://cesium.com/downloads/ 下載 CesiumJS 1.124"
fi

# 資料檔案
if [ -f "db_v2.json" ]; then
    print_ok "db_v2.json 船艦資料庫存在"
else
    print_err "db_v2.json 不存在 — Node.js API 將無法提供船艦資料"
fi

if [ -f "track_data.json" ]; then
    print_ok "track_data.json 航跡資料存在"
else
    print_err "track_data.json 不存在 — 航跡功能將無法使用"
fi

if [ -f "prompts_config.json" ]; then
    print_ok "prompts_config.json LLM Prompt 配置存在"
else
    print_err "prompts_config.json 不存在 — LLM Function Calling 將無法運作"
fi

# ==================== 7. 摘要 ====================
print_header "部署摘要"

if [ $ERR_COUNT -gt 0 ]; then
    echo -e "  ${RED}錯誤: ${ERR_COUNT} 個${NC}（必須修復才能運行）"
fi
if [ $WARN_COUNT -gt 0 ]; then
    echo -e "  ${YELLOW}警告: ${WARN_COUNT} 個${NC}（非必要，但部分功能可能受限）"
fi
if [ $ERR_COUNT -eq 0 ] && [ $WARN_COUNT -eq 0 ]; then
    echo -e "  ${GREEN}所有檢查通過！${NC}"
fi

echo ""
echo -e "${BLUE}啟動指令（請開 3 個終端分別執行）：${NC}"
echo ""
echo "  終端 1 (Ollama):    ollama serve"
echo "  終端 2 (Node API):  node server_v2_fixed.js"
echo "  終端 3 (Flask):     ${PY_CMD:-python} app.py"
echo ""
echo "  瀏覽器開啟:         http://localhost:5000"
echo ""
echo -e "${BLUE}健康檢查：${NC}"
echo ""
echo "  curl http://localhost:11434/api/tags    # Ollama"
echo "  curl http://localhost:3000/health       # Node API"
echo "  curl http://localhost:5000/             # Flask"
echo ""
