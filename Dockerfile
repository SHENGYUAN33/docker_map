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

# 複製 Docker 專用的 system_config.json（localhost 改為容器名稱）
COPY system_config.docker.json system_config.json

EXPOSE 5000

CMD ["python", "app.py"]
