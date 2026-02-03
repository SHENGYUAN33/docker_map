## 專案目錄結構

```

project/
│
├─ flask_v6.py              # 主系統後端
├─ static/
│   └─ js/milsymbol.js      # 本地軍事符號庫
│
├─ maps/                    # 產生的地圖 HTML
├─ cops/                    # COP 截圖
├─ feedbacks/               # 回饋資料
│
├─ prompts_config.json      # SYSTEM PROMPT 管理
├─ config.json              # 系統開關設定
│
└─ requirements.txt

````

---

## 安裝與部署（Windows）

### 1. 建立 Conda 環境
```bash
conda create -n wargame python=3.10
conda activate wargame
````

### 2. 安裝套件

```bash
pip install -r requirements.txt
```

必要套件：

```
flask
flask-cors
requests
folium
branca
```

---

## 啟動服務

### 1. 啟動 Ollama

```bash
ollama run llama3.2:3b
```

### 2. 啟動 Node.js API（模擬或真實）

```bash
node server.js
```

### 3. 啟動 Flask

```bash
python flask_v6.py
```

### 開啟網頁：

```bash
index_v6.html
```

---
