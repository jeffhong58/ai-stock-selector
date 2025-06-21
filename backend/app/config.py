# backend/app/config.py
"""
AI選股系統配置檔案
使用Pydantic進行配置管理
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """系統設定"""
    
    # 基本設定
    APP_NAME: str = "AI選股系統"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # 伺服器設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 資料庫設定
    DATABASE_URL: str = "postgresql://stock_user:your_password_here@localhost:5432/ai_stock_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis設定
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # InfluxDB設定
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "your_token_here"
    INFLUXDB_ORG: str = "stock_org"
    INFLUXDB_BUCKET: str = "stock_data"
    
    # CORS設定
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # 資料源設定
    YAHOO_FINANCE_ENABLED: bool = True
    TWSE_ENABLED: bool = True
    MOPS_ENABLED: bool = True
    TEJ_ENABLED: bool = False
    
    # TEJ設定（付費升級時使用）
    TEJ_API_KEY: Optional[str] = None
    TEJ_API_URL: Optional[str] = None
    
    # 資料收集設定
    DATA_UPDATE_TIME: str = "17:30"
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_DELAY_SECONDS: float = 1.0
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 30
    
    # AI模型設定
    AI_MODEL_VERSION: str = "1.0.0"
    MODEL_RETRAIN_DAYS: int = 30
    FEATURE_LOOKBACK_DAYS: int = 60
    MIN_TRADING_DAYS: int = 60
    
    # 推薦設定
    MAX_RECOMMENDATIONS_PER_TYPE: int = 50
    RECOMMENDATION_CONFIDENCE_THRESHOLD: float = 0.6
    SECTOR_ROTATION_LOOKBACK_DAYS: int = 20
    
    # 技術分析設定
    RSI_PERIOD: int = 14
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD: float = 2.0
    
    # 資料清理設定
    RECOMMENDATION_RETENTION_DAYS: int = 90
    LOG_RETENTION_DAYS: int = 180
    PRICE_DATA_RETENTION_YEARS: int = 5
    
    # 快取設定
    CACHE_TTL_SECONDS: int = 300  # 5分鐘
    CACHE_RECOMMENDATIONS_TTL: int = 3600  # 1小時
    CACHE_STOCK_INFO_TTL: int = 1800  # 30分鐘
    
    # 日誌設定
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/ai_stock_system.log"
    LOG_MAX_SIZE: str = "10MB"
    LOG_BACKUP_COUNT: int = 5
    
    # 安全設定
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 效能設定
    MAX_WORKERS: int = 4
    WORKER_TIMEOUT: int = 30
    KEEP_ALIVE: int = 2
    
    # 監控設定
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001
    
    # Yahoo Finance API設定
    YAHOO_BASE_URL: str = "https://query1.finance.yahoo.com"
    YAHOO_RATE_LIMIT: int = 100  # 每分鐘請求數
    
    # 證交所API設定
    TWSE_BASE_URL: str = "https://www.twse.com.tw"
    TWSE_RATE_LIMIT: int = 60  # 每分鐘請求數
    
    # 公開觀測站API設定
    MOPS_BASE_URL: str = "https://mops.twse.com.tw"
    MOPS_RATE_LIMIT: int = 30  # 每分鐘請求數
    
    @validator('ALLOWED_ORIGINS', pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator('DATABASE_URL', pre=True)
    def assemble_db_connection(cls, v):
        if v and not v.startswith('postgresql'):
            # 支援環境變數組合
            user = os.getenv('DB_USER', 'stock_user')
            password = os.getenv('DB_PASSWORD', 'your_password_here')
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME', 'ai_stock_db')
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return v
    
    @validator('TEJ_ENABLED')
    def check_tej_requirements(cls, v, values):
        if v and not values.get('TEJ_API_KEY'):
            raise ValueError('TEJ_API_KEY is required when TEJ_ENABLED is True')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """開發環境設定"""
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    
    # 開發時使用較短的快取時間
    CACHE_TTL_SECONDS: int = 60
    CACHE_RECOMMENDATIONS_TTL: int = 300
    
    # 開發時較少的資料保留
    RECOMMENDATION_RETENTION_DAYS: int = 30
    
    # 開發時較寬鬆的限制
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_DELAY_SECONDS: float = 0.5


class ProductionSettings(Settings):
    """正式環境設定"""
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # 正式環境更嚴格的安全設定
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # 正式環境更保守的請求限制
    MAX_CONCURRENT_REQUESTS: int = 3
    REQUEST_DELAY_SECONDS: float = 2.0
    
    # 正式環境更長的資料保留
    RECOMMENDATION_RETENTION_DAYS: int = 180
    LOG_RETENTION_DAYS: int = 365


class TestingSettings(Settings):
    """測試環境設定"""
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    
    # 測試用資料庫
    DATABASE_URL: str = "postgresql://test_user:test_password@localhost:5432/test_ai_stock_db"
    
    # 測試時禁用外部API調用
    YAHOO_FINANCE_ENABLED: bool = False
    TWSE_ENABLED: bool = False
    MOPS_ENABLED: bool = False
    
    # 測試時使用記憶體快取
    REDIS_URL: str = "redis://localhost:6379/1"
    
    # 測試時較短的保留期間
    RECOMMENDATION_RETENTION_DAYS: int = 7


def get_settings() -> Settings:
    """根據環境變數取得對應的設定"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# 全域設定實例
settings = get_settings()


# 資料源設定
DATA_SOURCES_CONFIG = {
    "yahoo_finance": {
        "enabled": settings.YAHOO_FINANCE_ENABLED,
        "base_url": settings.YAHOO_BASE_URL,
        "rate_limit": settings.YAHOO_RATE_LIMIT,
        "endpoints": {
            "quote": "/v8/finance/chart/{symbol}.TW",
            "history": "/v7/finance/download/{symbol}.TW"
        }
    },
    "twse": {
        "enabled": settings.TWSE_ENABLED,
        "base_url": settings.TWSE_BASE_URL,
        "rate_limit": settings.TWSE_RATE_LIMIT,
        "endpoints": {
            "daily_trading": "/exchangeReport/STOCK_DAY",
            "institutional": "/fund/T86",
            "margin": "/exchangeReport/MI_MARGN"
        }
    },
    "mops": {
        "enabled": settings.MOPS_ENABLED,
        "base_url": settings.MOPS_BASE_URL,
        "rate_limit": settings.MOPS_RATE_LIMIT,
        "endpoints": {
            "financial": "/server-java/ApiProxy",
            "company_info": "/server-java/ApiProxy"
        }
    },
    "tej": {
        "enabled": settings.TEJ_ENABLED,
        "api_key": settings.TEJ_API_KEY,
        "api_url": settings.TEJ_API_URL,
        "rate_limit": 1000  # TEJ通常有較高的限制
    }
}


# AI模型設定
AI_MODEL_CONFIG = {
    "feature_engineering": {
        "technical_indicators": [
            "rsi", "macd", "bollinger", "ma", "ema", "kd"
        ],
        "fundamental_features": [
            "pe_ratio", "pb_ratio", "roe", "debt_ratio"
        ],
        "market_features": [
            "volume_ratio", "price_momentum", "sector_strength"
        ]
    },
    "models": {
        "classification": {
            "algorithm": "xgboost",
            "parameters": {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1
            }
        },
        "regression": {
            "algorithm": "random_forest",
            "parameters": {
                "n_estimators": 200,
                "max_depth": 10
            }
        }
    },
    "training": {
        "train_test_split": 0.8,
        "validation_split": 0.2,
        "cross_validation_folds": 5
    }
}