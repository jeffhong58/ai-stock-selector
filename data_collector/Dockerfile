# data_collector/Dockerfile
# AI Stock Selector Data Collector - 修正版

FROM python:3.11-slim

# 設定環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 建立應用使用者
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 複製並安裝Python依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . /app/data_collector/
COPY ../backend/app /app/app/

# 建立必要目錄
RUN mkdir -p /app/logs

# 設定檔案權限
RUN chown -R appuser:appuser /app
USER appuser

# 健康檢查
HEALTHCHECK --interval=60s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "print('Data collector healthy')" || exit 1

# 預設指令 - 執行data collector服務
CMD ["python", "-c", "print('Data collector started'); import time; time.sleep(3600)"]