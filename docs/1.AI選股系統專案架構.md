# AI選股系統專案架構

## 專案概述
基於免費數據源的台灣股市AI選股系統，支援短中長期投資分析，具備未來升級TEJ付費數據的擴展性。

## 技術棧
- **後端**: Python 3.9+, FastAPI, SQLAlchemy
- **資料庫**: PostgreSQL (主資料), InfluxDB (時序數據)
- **快取**: Redis
- **前端**: React 18, TypeScript, TradingView圖表
- **AI/ML**: scikit-learn, XGBoost, TA-Lib
- **部署**: Docker, Docker Compose

## 專案結構
```
ai-stock-selector/
├── backend/                    # 後端API服務
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI主程式
│   │   ├── config.py          # 配置設定
│   │   ├── database.py        # 資料庫連接
│   │   ├── models/            # 資料庫模型
│   │   │   ├── __init__.py
│   │   │   ├── stock.py       # 股票基本資料
│   │   │   ├── price.py       # 價格數據
│   │   │   └── analysis.py    # 分析結果
│   │   ├── api/               # API端點
│   │   │   ├── __init__.py
│   │   │   ├── stocks.py      # 股票相關API
│   │   │   ├── analysis.py    # 分析API
│   │   │   └── recommendations.py # 推薦API
│   │   ├── services/          # 業務邏輯
│   │   │   ├── __init__.py
│   │   │   ├── data_collector.py  # 數據收集
│   │   │   ├── technical_analysis.py # 技術分析
│   │   │   ├── fundamental_analysis.py # 基本面分析
│   │   │   └── ai_engine.py   # AI選股引擎
│   │   └── utils/             # 工具函數
│   │       ├── __init__.py
│   │       ├── indicators.py  # 技術指標計算
│   │       └── helpers.py     # 輔助函數
│   ├── requirements.txt       # Python依賴
│   └── Dockerfile            # 後端Docker配置
├── frontend/                  # 前端React應用
│   ├── public/
│   ├── src/
│   │   ├── components/        # React組件
│   │   │   ├── charts/        # 圖表組件
│   │   │   ├── stocks/        # 股票相關組件
│   │   │   └── layout/        # 佈局組件
│   │   ├── pages/             # 頁面組件
│   │   ├── services/          # API服務
│   │   ├── utils/             # 工具函數
│   │   └── types/             # TypeScript類型定義
│   ├── package.json
│   └── Dockerfile            # 前端Docker配置
├── data_collector/            # 資料收集系統
│   ├── scrapers/              # 爬蟲模組
│   │   ├── __init__.py
│   │   ├── yahoo_finance.py   # Yahoo Finance爬蟲
│   │   ├── twse_scraper.py    # 證交所資料爬蟲
│   │   └── mops_scraper.py    # 公開觀測站爬蟲
│   ├── schedulers/            # 排程器
│   │   ├── __init__.py
│   │   └── daily_update.py    # 每日更新排程
│   ├── processors/            # 資料處理
│   │   ├── __init__.py
│   │   ├── data_cleaner.py    # 資料清理
│   │   └── data_validator.py  # 資料驗證
│   └── requirements.txt
├── ml_models/                 # 機器學習模型
│   ├── training/              # 模型訓練
│   │   ├── __init__.py
│   │   ├── feature_engineering.py # 特徵工程
│   │   ├── model_training.py  # 模型訓練
│   │   └── backtesting.py     # 回測
│   ├── models/                # 儲存的模型檔案
│   └── requirements.txt
├── database/                  # 資料庫相關
│   ├── migrations/            # 資料庫遷移檔案
│   ├── seeds/                 # 初始資料
│   └── init.sql              # 初始化SQL
├── deployment/                # 部署相關
│   ├── docker-compose.yml     # Docker Compose配置
│   ├── nginx.conf             # Nginx配置
│   └── .env.example          # 環境變數範例
├── docs/                      # 文件
│   ├── API.md                # API文件
│   ├── DEPLOYMENT.md         # 部署指南
│   └── DEVELOPMENT.md        # 開發指南
├── tests/                     # 測試檔案
│   ├── backend/
│   ├── frontend/
│   └── integration/
├── .gitignore
├── README.md
└── setup.py                  # 安裝腳本
```

## 核心功能模組

### 1. 資料收集模組
- **Yahoo Finance**: 基本K線、成交量數據
- **證交所**: 三大法人買賣、融資融券
- **公開觀測站**: 財報、基本資料

### 2. 技術分析模組
- 移動平均線 (MA, EMA)
- 技術指標 (RSI, MACD, KD, 布林帶)
- 支撐壓力位計算
- 成交量分析

### 3. AI選股引擎
- 多因子選股模型
- 機器學習預測模型
- 產業輪動分析
- 風險評估

### 4. 可擴展設計
- 資料庫schema預留TEJ欄位
- 模組化資料源配置
- 統一的資料處理介面

## 資料庫設計

### 核心資料表
1. **stocks** - 股票基本資料
2. **daily_prices** - 日線數據
3. **technical_indicators** - 技術指標
4. **fundamental_data** - 基本面數據
5. **ai_recommendations** - AI推薦結果
6. **market_data** - 大盤數據

### 擴展設計
- 預留TEJ資料欄位
- 支援多時間週期數據
- 版本化的推薦結果

## API設計

### 主要端點
- `/api/stocks/` - 股票清單和基本資料
- `/api/stocks/{symbol}/analysis` - 個股分析
- `/api/recommendations/sector` - 產業推薦
- `/api/recommendations/timeframe` - 期間推薦
- `/api/charts/{symbol}` - 圖表數據

## 部署架構
- **前端**: Nginx + React靜態檔案
- **後端**: FastAPI + Gunicorn
- **資料庫**: PostgreSQL + InfluxDB
- **快取**: Redis
- **排程**: Celery + Redis

## 開發階段規劃

### 第一階段：基礎架構 (本階段)
- [x] 專案結構設計
- [ ] 資料庫schema設計
- [ ] 基本的資料收集系統
- [ ] FastAPI基礎框架

### 第二階段：AI模型開發
- [ ] 技術指標計算引擎
- [ ] 機器學習模型訓練
- [ ] 選股演算法實現

### 第三階段：前端界面
- [ ] React前端開發
- [ ] TradingView圖表整合
- [ ] 響應式設計

### 第四階段：整合測試
- [ ] 系統整合測試
- [ ] 效能優化
- [ ] 部署和上線

## 下一步行動
1. 建立資料庫schema
2. 實現Yahoo Finance資料收集器
3. 建立FastAPI基礎框架
4. 設定Docker開發環境