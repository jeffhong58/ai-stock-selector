# AI選股系統 - 部署安裝指南

## 📋 系統需求

### 硬體需求
- **CPU**: 4核心以上
- **記憶體**: 8GB以上 (推薦16GB)
- **硬碟**: 50GB以上可用空間
- **網路**: 穩定的網際網路連接

### 軟體需求
- **作業系統**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **Git**: 2.30+

## 🚀 快速開始

### 1. 克隆專案

```bash
git clone https://github.com/jeffhong58/ai-stock-selector.git
cd ai-stock-selector
```

### 2. 環境設定

複製環境變數範例檔案：
```bash
cp deployment/.env.example .env
```

編輯 `.env` 檔案，設定必要的環境變數：
```bash
# 資料庫設定
POSTGRES_PASSWORD=your_secure_password_here
DB_PASSWORD=your_secure_password_here

# InfluxDB設定
INFLUXDB_PASSWORD=your_influxdb_password
INFLUXDB_TOKEN=your_influxdb_token_here

# Redis設定 (可選)
REDIS_PASSWORD=your_redis_password

# 應用設定
SECRET_KEY=your_secret_key_change_in_production
ENVIRONMENT=production
DEBUG=false
```

### 3. 一鍵部署

```bash
# 啟動所有服務
docker-compose up -d

# 檢查服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

### 4. 驗證部署

等待所有服務啟動後（約2-3分鐘），開啟瀏覽器訪問：

- **API文件**: http://localhost:8000/docs
- **系統健康檢查**: http://localhost:8000/health
- **前端界面**: http://localhost:3000 (待前端開發完成)

## 📊 服務說明

### 核心服務

| 服務名稱 | 端口 | 說明 |
|---------|------|------|
| PostgreSQL | 5432 | 主要資料庫 |
| InfluxDB | 8086 | 時序資料庫 |
| Redis | 6379 | 快取和任務佇列 |
| Backend API | 8000 | 後端API服務 |
| Data Collector | - | 資料收集服務 |
| Celery Worker | - | 後台任務處理 |
| Celery Beat | - | 定時任務排程 |

### 資料流程

```
Yahoo Finance API → Data Collector → PostgreSQL/InfluxDB
證交所公開資料 → Data Collector → PostgreSQL/InfluxDB
公開觀測站 → Data Collector → PostgreSQL/InfluxDB
                ↓
           AI Engine → 生成推薦
                ↓
           FastAPI → 前端界面
```

## 🔧 詳細配置

### 資料庫初始化

系統首次啟動時會自動建立資料庫表格。如需手動初始化：

```bash
# 進入後端容器
docker-compose exec backend bash

# 執行資料庫遷移
alembic upgrade head

# 載入初始資料
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### 資料收集設定

系統預設每日17:30自動收集資料。可手動觸發：

```bash
# 手動觸發資料更新
curl -X POST http://localhost:8000/api/admin/update-data

# 手動觸發AI分析
curl -X POST http://localhost:8000/api/admin/generate-recommendations
```

### 監控和日誌

```bash
# 查看即時日誌
docker-compose logs -f backend

# 查看特定服務日誌
docker-compose logs -f data_collector

# 監控資源使用
docker stats
```

## 🛠️ 進階設定

### 效能調優

#### 1. 資料庫調優
編輯 `postgresql.conf` (在postgres容器內)：
```sql
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
```

#### 2. 應用程式調優
編輯 `.env` 檔案：
```bash
# 增加工作進程數
MAX_WORKERS=8

# 調整快取TTL
CACHE_TTL_SECONDS=600

# 調整並發請求數
MAX_CONCURRENT_REQUESTS=10
```

### 安全設定

#### 1. 更新預設密碼
```bash
# 生成安全密碼
openssl rand -base64 32

# 更新 .env 檔案中的所有密碼
```

#### 2. 設定防火牆
```bash
# 僅允許必要端口
ufw allow 80
ufw allow 443
ufw deny 5432  # 資料庫端口不對外開放
ufw deny 6379  # Redis端口不對外開放
```

#### 3. SSL憑證 (正式環境)
```bash
# 使用Let's Encrypt
certbot --nginx -d yourdomain.com

# 或放置自有憑證到 deployment/ssl/
```

### 備份策略

#### 1. 資料庫備份
```bash
# 建立備份腳本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U stock_user ai_stock_db > backup_${DATE}.sql
EOF

chmod +x backup.sh

# 設定定時備份
crontab -e
# 添加: 0 2 * * * /path/to/backup.sh
```

#### 2. 應用程式備份
```bash
# 備份重要檔案
tar -czf app_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

## 🔍 故障排除

### 常見問題

#### 1. 容器啟動失敗
```bash
# 檢查日誌
docker-compose logs [service_name]

# 重新建置映像
docker-compose build --no-cache

# 清理並重新啟動
docker-compose down -v
docker-compose up -d
```

#### 2. 資料庫連接失敗
```bash
# 檢查資料庫狀態
docker-compose exec postgres pg_isready -U stock_user

# 檢查網路連接
docker network ls
docker network inspect ai-stock-selector_stock_network
```

#### 3. 資料收集失敗
```bash
# 檢查資料收集器狀態
docker-compose logs data_collector

# 手動測試資料源
docker-compose exec backend python -c "
from app.services.data_collector import test_data_sources
import asyncio
asyncio.run(test_data_sources())
"
```

#### 4. API回應緩慢
```bash
# 檢查資源使用
docker stats

# 檢查快取狀態
docker-compose exec redis redis-cli info memory

# 增加工作進程
# 編輯 .env: MAX_WORKERS=8
```

### 日誌位置

```bash
# 應用程式日誌
docker-compose logs backend > backend.log

# 系統日誌
journalctl -u docker

# 自訂日誌目錄
mkdir logs
# 日誌會自動寫入 logs/ 目錄
```

## 📈 升級指南

### 1. 程式碼更新
```bash
# 拉取最新程式碼
git pull origin main

# 重新建置並部署
docker-compose down
docker-compose build
docker-compose up -d
```

### 2. 資料庫遷移
```bash
# 備份資料庫
./backup.sh

# 執行遷移
docker-compose exec backend alembic upgrade head
```

### 3. TEJ付費數據升級
```bash
# 編輯 .env 檔案
TEJ_ENABLED=true
TEJ_API_KEY=your_tej_api_key
TEJ_API_URL=your_tej_api_url

# 重新啟動服務
docker-compose restart backend data_collector
```

## 🌐 正式環境部署

### 1. 雲端平台部署

#### AWS EC2
```bash
# 啟動 t3.large 實例 (推薦)
# 安裝 Docker 和 Docker Compose
# 設定安全群組開放必要端口
```

#### Google Cloud Platform
```bash
# 建立 Compute Engine 實例
# 配置防火牆規則
# 設定負載平衡器
```

### 2. Nginx反向代理設定

編輯 `deployment/nginx.conf`：
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://frontend:3000;
    }
}
```

### 3. 監控和告警

安裝Prometheus和Grafana：
```yaml
# 添加到 docker-compose.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## 💡 最佳實踐

1. **定期備份**: 設定自動備份策略
2. **監控資源**: 持續監控CPU、記憶體使用率
3. **日誌管理**: 定期清理老舊日誌
4. **安全更新**: 定期更新Docker映像和依賴套件
5. **效能測試**: 定期進行負載測試

## 🆘 獲得幫助

如遇到問題，請：

1. 查看本文件的故障排除章節
2. 檢查GitHub Issues
3. 查看詳細日誌訊息
4. 提供完整的錯誤訊息和環境資訊

---

🎉 **恭喜！您已成功部署AI選股系統第一階段！**

下一步：開始收集股票資料並測試API功能。