FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴（curl 用於 healthcheck）
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY app.py config.py ./
COPY prompts_config.json default_prompts.json ship_registry.json ./
COPY .env.example .env
COPY models/ models/
COPY services/ services/
COPY routes/ routes/
COPY handlers/ handlers/
COPY utils/ utils/
COPY templates/ templates/
COPY static/js/ static/js/
COPY static/css/ static/css/
COPY static/cesium/ static/cesium/
COPY tiles/ tiles/

# 複製資料檔案
COPY config.json db_v2.json track_data.json ./

# 生成 Docker 用的 system_config.json（api_mode=local，指向容器內服務名稱）
RUN echo '{\
  "api_settings": {\
    "api_mode": "local",\
    "real_api": { "base_url": "https://your-real-api-server.com", "timeout": 300, "endpoints": { "import_scenario": "/import_scenario", "star_scenario": "/start_scenario", "get_wta": "/get_wta", "get_answer": "/get_answer", "get_track": "/get_track" } },\
    "local_api": { "base_url": "http://node-api:3000/api/v1", "timeout": 300, "endpoints": { "import_scenario": "/import_scenario", "star_scenario": "/start_scenario", "get_wta": "/get_wta", "get_answer": "/get_answer", "get_track": "/get_track" } },\
    "local_data": { "db_file": "db_v2.json", "track_file": "track_data.json", "mock_responses_dir": "mock_responses" }\
  },\
  "llm_settings": {\
    "active_provider": "ollama",\
    "providers": {\
      "ollama": { "name": "Ollama", "base_url": "http://ollama:11434", "chat_endpoint": "/api/chat", "timeout": 300, "default_model": "llama3.2:3b", "models": [{ "id": "llama3.2:3b", "name": "Llama 3.2 3B", "size": "2.0 GB", "speed": "快速", "quality": "良好" }] },\
      "openai": { "name": "OpenAI", "base_url": "https://api.openai.com", "chat_endpoint": "/v1/chat/completions", "timeout": 120, "api_key_env": "OPENAI_API_KEY", "default_model": "gpt-4", "models": [{ "id": "gpt-4", "name": "GPT-4" }] },\
      "anthropic": { "name": "Anthropic", "base_url": "https://api.anthropic.com", "chat_endpoint": "/v1/messages", "timeout": 120, "api_key_env": "ANTHROPIC_API_KEY", "default_model": "claude-sonnet-4-5-20250929", "models": [{ "id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5" }] }\
    }\
  },\
  "rag_settings": { "default_mode": "military_qa", "default_model": "TAIDE8B", "stream": 0, "max_sources": 5 }\
}' > system_config.json

EXPOSE 5000

CMD ["python", "app.py"]
