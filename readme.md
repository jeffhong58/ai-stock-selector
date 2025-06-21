# AI選股系統 🚀

基於人工智慧的台灣股市選股系統，支援短中長期投資分析，提供產業輪動建議和技術分析圖表。

## ✨ 主要功能

### 🎯 AI選股推薦
- **產業輪動分析**: 根據市場趨勢推薦下一波主流產業股票
- **多時間週期**: 支援短期(7天)、中期(30天)、長期(90天)投資建議
- **智能排序**: AI評分系統，可自定義推薦股票數量(前10、20、30名)

### 📊 技術分析
- **完整技術指標**: RSI、MACD、KD、布林帶、移動平均線
- **買賣點提醒**: 精準的進場和出場時機建議
- **支撐壓力位**: 自動計算關鍵價格區間
- **互動式圖表**: 基於TradingView的專業技術分析圖表

### 🔍 個股分析
- **即時查詢**: 輸入股票代號或名稱，獲得完整分析報告
- **投資建議**: AI評估投資價值和風險等級
- **詳細原因**: 提供投資建議的具體分析理由

### 📈 數據來源
- **免費版本**: Yahoo Finance、證交所公開資訊、公開觀測站
- **付費擴展**: 預留TEJ台灣經濟新報整合 (賺錢後升級)

## 🛠 技術架構

### 後端技術
- **API框架**: FastAPI + Python 3.11
- **資料庫**: PostgreSQL (主要) + InfluxDB (時序資料)
- **快取**: Redis
- **任務佇列**: Celery
- **機器學習**: scikit-learn, XGBoost, TA-Lib

### 前端技術
- **框架**: React 18 + TypeScript
- **UI庫**: Ant Design
- **圖表**: TradingView Charting Library
- **狀態管理**: React Query

### 部署方案
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **監控**: Prometheus + Grafana (可選)

## 🚀 快速開始

### 前置需求
- Docker 和 Docker Compose
- Git
- 至少 8GB RAM 的主機

### 1. 克隆專案
```bash
git clone https://github.com/jeffhong58/ai-stock-selector.git
cd ai-stock-selector
```

### 2. 設定環境變數
```bash
cp deployment/.env.example .env
# 編輯 .env 檔案，設定密碼和金鑰
```

### 3. 啟動服務
```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f backend
```

### 4. 初始化資料庫
```bash
# 建立資料表
docker-compose exec backend python -c "
from app.database import db_manager
import asyncio
asyncio.run(db_manager.create_tables())
"

# 執行初始資料收集
docker-compose exec backend python -c "
from app.main import celery
celery.send_task('app.tasks.daily_data_update')
"
```

### 5. 訪問應用
- **前端界面**: http://localhost:3000
- **API文檔**: http://localhost:8000/docs
- **系統監控**: http://localhost:8000/health

## 📱 使用指南

### 產業輪動分析
1. 訪問首頁，查看「產業輪動」區塊
2. 系統會根據資金流向和價格動能推薦下一波主流產業
3. 點擊產業可查看該產業推薦股票清單

### 選股功能
1. 在「智能選股」頁面選擇投資期間：
   - 短期：適合波段操作 (7-14天)
   - 中期：適合趨勢跟隨 (1-3個月)
   - 長期：適合價值投資 (3個月以上)

2. 設定推薦數量 (10、20、30家)

3. 查看推薦結果，包含：
   - AI評分
   - 買點建議
   - 目標價位
   - 停損位置
   - 推薦原因

### 個股分析
1. 在搜尋框輸入股票代號 (如: 2330) 或名稱
2. 查看完整分析報告：
   - 技術分析圖表
   - 基本面資料
   - 法人進出狀況
   - AI投資建議

## 🔧 維護和監控

### 每日自動更新
系統會在每日17:00自動更新股票資料：
- 價格和成交量
- 法人買賣
- 技術指標計算
- AI推薦更新

### 手動觸發更新
```bash
# 手動更新資料
curl -X POST http://localhost:8000/admin/update-data

# 手動重訓練模型
curl -X POST http://localhost:8000/admin/train-models
```

### 查看系統狀態
```bash
# 查看所有服務狀態
docker-compose ps

# 查看特定服務日誌
docker-compose logs backend
docker-compose logs data_collector
docker-compose logs celery_worker

# 查看資料庫狀態
docker-compose exec postgres psql -U stock_user -d ai_stock_db -c "\dt"
```

## 📊 資料來源說明

### 免費資料源 (目前版本)
1. **Yahoo Finance**
   - K線資料 (開高低收、成交量)
   - 基本技術指標
   - 更新頻率: 每日

2. **證交所公開資訊**
   - 三大法人買賣
   - 融資融券餘額
   - 大股東持股變化
   - 更新頻率: 每日

3. **公開觀測站**
   - 財務報表
   - 公司基本資料
   - 重大訊息
   - 更新頻率: 季度/即時

### 付費資料源 (升級選項)
- **TEJ台灣經濟新報**: 提供更精細的籌碼分析和法人資料

## 🔄 升級路徑

### 從免費版升級到TEJ版本
1. 購買TEJ API服務
2. 更新 `.env` 檔案:
   ```
   TEJ_ENABLED=true
   TEJ_API_KEY=your_api_key_here
   ```
3. 重啟服務: `docker-compose restart`
4. 系統會自動切換到高精度模式

## 🐛 故障排除

### 常見問題

**1. 容器啟動失敗**
```bash
# 檢查端口是否被佔用
netstat -tlnp | grep :5432
netstat -tlnp | grep :6379
netstat -tlnp | grep :8000

# 清理舊容器
docker-compose down -v
docker system prune -f
```

**2. 資料庫連接錯誤**
```bash
# 檢查PostgreSQL狀態
docker-compose logs postgres

# 手動連接測試
docker-compose exec postgres psql -U stock_user -d ai_stock_db
```

**3. 資料更新失敗**
```bash
# 檢查資料收集器日誌
docker-compose logs data_collector

# 檢查網路連接
docker-compose exec backend ping -c 3 finance.yahoo.com
```

**4. 前端無法載入**
```bash
# 檢查前端建構狀態
docker-compose logs frontend

# 檢查Nginx配置
docker-compose exec nginx nginx -t
```

## 📈 效能優化

### 資料庫優化
```sql
-- 建立必要索引
CREATE INDEX CONCURRENTLY idx_daily_prices_symbol_date 
ON daily_prices(symbol, trade_date DESC);

-- 定期清理舊資料
SELECT cleanup_old_data(365); -- 保留1年資料
```

### 快取設定
```bash
# 調整Redis記憶體限制
echo "maxmemory 512mb" >> redis.conf
echo "maxmemory-policy allkeys-lru" >> redis.conf
```

## 🤝 貢獻指南

1. Fork 專案
2. 建立特性分支: `git checkout -b feature/amazing-feature`
3. 提交變更: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 開啟 Pull Request

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🆘 支援與聯絡

- **GitHub Issues**: [回報問題](https://github.com/jeffhong58/ai-stock-selector/issues)
- **討論區**: [GitHub Discussions](https://github.com/jeffhong58/ai-stock-selector/discussions)
- **Email**: support@example.com

## 🎯 發展路線圖

### v1.1 (下一版本)
- [ ] 支援更多技術指標
- [ ] 加入選擇權分析
- [ ] 港股、美股擴展

### v1.2
- [ ] 機器學習模型優化
- [ ] 即時資料支援
- [ ] 手機App開發

### v2.0
- [ ] 多帳戶投資組合管理
- [ ] 自動交易功能
- [ ] 社群分享功能

---

## 🙏 致謝

感謝以下開源專案和資料提供者：
- Yahoo Finance API
- 台灣證券交易所
- 公開觀測站
- FastAPI、React、PostgreSQL 等開源社群

**⭐ 如果這個專案對您有幫助，請給個星星支持！**