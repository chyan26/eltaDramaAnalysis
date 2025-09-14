FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製requirements文件
COPY requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用文件
COPY . .

# 暴露端口
EXPOSE 8501
EXPOSE 5000

# 健康檢查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 啟動Streamlit應用
ENTRYPOINT ["streamlit", "run", "recommend.py", "--server.port=8501", "--server.address=0.0.0.0"]
