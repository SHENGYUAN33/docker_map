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

# 複製資料檔案
COPY config.json system_config.json db_v2.json track_data.json ./

EXPOSE 5000

CMD ["python", "app.py"]
