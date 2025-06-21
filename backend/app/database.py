# backend/app/database.py
"""
資料庫連接和會話管理
SQLAlchemy + PostgreSQL + InfluxDB
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import redis

from app.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy 設定
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # 自動檢測斷線
    pool_recycle=3600,   # 1小時回收連接
    echo=settings.DEBUG  # 在debug模式顯示SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立Base類別
Base = declarative_base()

# 自訂metadata，支援schema
metadata = MetaData()


# 資料庫會話依賴注入
def get_db() -> Generator[Session, None, None]:
    """取得資料庫會話"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"資料庫會話錯誤: {e}")
        raise
    finally:
        db.close()


# InfluxDB 客戶端
class InfluxDBManager:
    """InfluxDB管理器"""
    
    def __init__(self):
        self.client = None
        self.write_api = None
        self.query_api = None
        self._connect()
    
    def _connect(self):
        """連接InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=settings.INFLUXDB_ORG
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            # 測試連接
            self.client.ping()
            logger.info("InfluxDB連接成功")
            
        except Exception as e:
            logger.error(f"InfluxDB連接失敗: {e}")
            self.client = None
    
    def write_stock_data(self, symbol: str, timestamp, price_data: dict):
        """寫入股票價格數據到InfluxDB"""
        if not self.client:
            return False
        
        try:
            point = (
                Point("stock_prices")
                .tag("symbol", symbol)
                .field("open", price_data.get("open"))
                .field("high", price_data.get("high"))
                .field("low", price_data.get("low"))
                .field("close", price_data.get("close"))
                .field("volume", price_data.get("volume"))
                .time(timestamp, WritePrecision.S)
            )
            
            self.write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                org=settings.INFLUXDB_ORG,
                record=point
            )
            return True
            
        except Exception as e:
            logger.error(f"寫入InfluxDB失敗: {e}")
            return False
    
    def query_stock_data(self, symbol: str, days: int = 30) -> list:
        """查詢股票歷史數據"""
        if not self.client:
            return []
        
        try:
            query = f'''
            from(bucket:"{settings.INFLUXDB_BUCKET}")
                |> range(start: -{days}d)
                |> filter(fn: (r) => r["_measurement"] == "stock_prices")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"])
            '''
            
            result = self.query_api.query(org=settings.INFLUXDB_ORG, query=query)
            
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        "time": record.get_time(),
                        "symbol": record.values.get("symbol"),
                        "open": record.values.get("open"),
                        "high": record.values.get("high"),
                        "low": record.values.get("low"),
                        "close": record.values.get("close"),
                        "volume": record.values.get("volume")
                    })
            
            return data
            
        except Exception as e:
            logger.error(f"查詢InfluxDB失敗: {e}")
            return []
    
    def close(self):
        """關閉連接"""
        if self.client:
            self.client.close()


# Redis 管理器
class RedisManager:
    """Redis快取管理器"""
    
    def __init__(self):
        self.client = None
        self._connect()
    
    def _connect(self):
        """連接Redis"""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 測試連接
            self.client.ping()
            logger.info("Redis連接成功")
            
        except Exception as e:
            logger.error(f"Redis連接失敗: {e}")
            self.client = None
    
    def get(self, key: str):
        """取得快取值"""
        if not self.client:
            return None
        
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET失敗: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = None):
        """設定快取值"""
        if not self.client:
            return False
        
        try:
            return self.client.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Redis SET失敗: {e}")
            return False
    
    def delete(self, key: str):
        """刪除快取"""
        if not self.client:
            return False
        
        try:
            return self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE失敗: {e}")
            return False
    
    def exists(self, key: str):
        """檢查key是否存在"""
        if not self.client:
            return False
        
        try:
            return self.client.exists(key)
        except Exception as e:
            logger.error(f"Redis EXISTS失敗: {e}")
            return False
    
    def hget(self, name: str, key: str):
        """取得hash值"""
        if not self.client:
            return None
        
        try:
            return self.client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET失敗: {e}")
            return None
    
    def hset(self, name: str, key: str, value: str):
        """設定hash值"""
        if not self.client:
            return False
        
        try:
            return self.client.hset(name, key, value)
        except Exception as e:
            logger.error(f"Redis HSET失敗: {e}")
            return False
    
    def hgetall(self, name: str):
        """取得所有hash值"""
        if not self.client:
            return {}
        
        try:
            return self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis HGETALL失敗: {e}")
            return {}


# 全域實例
influxdb_manager = InfluxDBManager()
redis_manager = RedisManager()


# 資料庫事件監聽器
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """資料庫連接時設定"""
    if 'postgresql' in settings.DATABASE_URL:
        # PostgreSQL特定設定
        cursor = dbapi_connection.cursor()
        cursor.execute("SET timezone='Asia/Taipei'")
        cursor.close()


@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """SQL執行前記錄（debug模式）"""
    if settings.DEBUG:
        logger.debug(f"SQL執行: {statement[:100]}...")


# 資料庫健康檢查
def check_database_health() -> dict:
    """檢查資料庫連接狀態"""
    health_status = {
        "postgresql": False,
        "influxdb": False,
        "redis": False,
        "errors": []
    }
    
    # 檢查PostgreSQL
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["postgresql"] = True
    except Exception as e:
        health_status["errors"].append(f"PostgreSQL: {str(e)}")
    
    # 檢查InfluxDB
    try:
        if influxdb_manager.client:
            influxdb_manager.client.ping()
            health_status["influxdb"] = True
        else:
            health_status["errors"].append("InfluxDB: 未連接")
    except Exception as e:
        health_status["errors"].append(f"InfluxDB: {str(e)}")
    
    # 檢查Redis
    try:
        if redis_manager.client:
            redis_manager.client.ping()
            health_status["redis"] = True
        else:
            health_status["errors"].append("Redis: 未連接")
    except Exception as e:
        health_status["errors"].append(f"Redis: {str(e)}")
    
    return health_status


# 快取裝飾器
def cache_result(key_prefix: str, ttl: int = 300):
    """快取結果的裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成快取鍵
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            
            # 嘗試從快取取得結果
            cached_result = redis_manager.get(cache_key)
            if cached_result:
                import json
                return json.loads(cached_result)
            
            # 執行函數並快取結果
            result = func(*args, **kwargs)
            if result is not None:
                import json
                redis_manager.set(cache_key, json.dumps(result, default=str), ttl)
            
            return result
        return wrapper
    return decorator


# 清理資源
def cleanup_connections():
    """清理所有資料庫連接"""
    try:
        engine.dispose()
        influxdb_manager.close()
        if redis_manager.client:
            redis_manager.client.close()
        logger.info("資料庫連接已清理")
    except Exception as e:
        logger.error(f"清理連接時發生錯誤: {e}")