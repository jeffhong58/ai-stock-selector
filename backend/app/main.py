"""
AI選股系統後端主程式
FastAPI + SQLAlchemy + Celery
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from celery import Celery

# 本地模組
from app.config import settings
from app.database import engine, Base
from app.api import stocks, analysis, recommendations
from app.utils.logging import setup_logging

# 設定日誌
setup_logging()
logger = logging.getLogger(__name__)


# Celery配置
celery = Celery(
    "ai_stock_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.services.data_collector',
        'app.services.ai_engine',
        'app.tasks.scheduled_tasks'
    ]
)

# Celery配置
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分鐘超時
    task_soft_time_limit=25 * 60,  # 25分鐘軟超時
    worker_max_tasks_per_child=50,  # 每個worker最多處理50個任務後重啟
)

# 排程任務配置
celery.conf.beat_schedule = {
    'daily-data-update': {
        'task': 'app.tasks.scheduled_tasks.daily_data_update',
        'schedule': {
            'hour': 17,
            'minute': 30,
        },  # 每日17:30執行
    },
    'calculate-technical-indicators': {
        'task': 'app.tasks.scheduled_tasks.calculate_all_technical_indicators',
        'schedule': {
            'hour': 18,
            'minute': 30,
        },  # 每日18:30執行
    },
    'generate-ai-recommendations': {
        'task': 'app.tasks.scheduled_tasks.generate_daily_recommendations',
        'schedule': {
            'hour': 19,
            'minute': 0,
        },  # 每日19:00執行
    },
    'cleanup-old-data': {
        'task': 'app.tasks.scheduled_tasks.cleanup_old_data',
        'schedule': {
            'hour': 2,
            'minute': 0,
        },  # 每日02:00執行清理
    },
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時執行
    logger.info("啟動AI選股系統...")
    
    # 建立資料庫表格
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("資料庫表格初始化完成")
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {e}")
        raise
    
    # 檢查資料源連接
    from app.services.data_collector import test_data_sources
    await test_data_sources()
    
    yield
    
    # 關閉時執行
    logger.info("關閉AI選股系統...")


# 建立FastAPI應用
app = FastAPI(
    title="AI選股系統 API",
    description="基於人工智慧的台灣股市選股系統",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 中介軟體設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# 全域例外處理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"未處理的例外: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "內部伺服器錯誤",
            "status_code": 500
        }
    )


# 健康檢查端點
@app.get("/health")
async def health_check():
    """系統健康檢查"""
    try:
        # 檢查資料庫連接
        from app.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        
        # 檢查Redis連接
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# API路由註冊
app.include_router(
    stocks.router,
    prefix="/api/stocks",
    tags=["stocks"]
)

app.include_router(
    analysis.router,
    prefix="/api/analysis",
    tags=["analysis"]
)

app.include_router(
    recommendations.router,
    prefix="/api/recommendations",
    tags=["recommendations"]
)


# 根路徑
@app.get("/")
async def root():
    return {
        "message": "AI選股系統 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


# 系統資訊端點
@app.get("/api/system/info")
async def system_info():
    """取得系統資訊"""
    return {
        "system_name": "AI選股系統",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "data_sources": {
            "yahoo_finance": True,
            "twse": True,
            "mops": True,
            "tej": settings.TEJ_ENABLED
        },
        "features": {
            "sector_rotation": True,
            "technical_analysis": True,
            "ai_recommendations": True,
            "multi_timeframe": True
        }
    }


# Celery任務狀態查詢
@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查詢Celery任務狀態"""
    result = celery.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
        "info": result.info
    }


# 手動觸發資料更新
@app.post("/api/admin/update-data")
async def trigger_data_update():
    """手動觸發資料更新（管理員功能）"""
    try:
        from app.tasks.scheduled_tasks import daily_data_update
        task = daily_data_update.delay()
        
        return {
            "message": "資料更新任務已啟動",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"觸發資料更新失敗: {e}")
        raise HTTPException(status_code=500, detail="觸發資料更新失敗")


# 手動觸發AI分析
@app.post("/api/admin/generate-recommendations")
async def trigger_ai_analysis():
    """手動觸發AI推薦生成（管理員功能）"""
    try:
        from app.tasks.scheduled_tasks import generate_daily_recommendations
        task = generate_daily_recommendations.delay()
        
        return {
            "message": "AI推薦生成任務已啟動",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"觸發AI分析失敗: {e}")
        raise HTTPException(status_code=500, detail="觸發AI分析失敗")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )