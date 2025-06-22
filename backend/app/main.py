# backend/app/main.py
"""
AI選股系統後端主程式
FastAPI主應用 - 移除重複Celery定義
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 本地模組
from app.config import settings
from app.database import engine, Base, check_database_health
from app.api import stocks, analysis, recommendations
from app.utils.logging import setup_logging

# 設定日誌
setup_logging()
logger = logging.getLogger(__name__)


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
    
    # 檢查資料庫連接狀態
    health_status = check_database_health()
    if not all([v for k, v in health_status.items() if k != 'errors']):
        logger.warning(f"部分資料庫連接異常: {health_status}")
    
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
        health_status = check_database_health()
        
        all_healthy = all([
            health_status.get("postgresql", False),
            health_status.get("redis", False)
        ])
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": health_status,
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
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
            "yahoo_finance": settings.YAHOO_FINANCE_ENABLED,
            "twse": settings.TWSE_ENABLED,
            "tej": getattr(settings, 'TEJ_ENABLED', False)
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
    try:
        # 導入Celery應用
        from celery_app import celery_app
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id, app=celery_app)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "info": result.info,
            "traceback": result.traceback if result.failed() else None
        }
    except Exception as e:
        logger.error(f"查詢任務狀態失敗: {e}")
        return {"task_id": task_id, "status": "unknown", "error": str(e)}


# 手動觸發資料更新
@app.post("/api/admin/update-data")
async def trigger_data_update():
    """手動觸發資料更新（管理員功能）"""
    try:
        from celery_app import celery_app
        
        # 發送任務到Celery
        task = celery_app.send_task(
            'app.tasks.scheduled_tasks.daily_data_update',
            queue='data_update'
        )
        
        return {
            "message": "資料更新任務已啟動",
            "task_id": task.id,
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"觸發資料更新失敗: {e}")
        raise HTTPException(status_code=500, detail=f"觸發資料更新失敗: {str(e)}")


# 手動觸發技術指標計算
@app.post("/api/admin/calculate-indicators")
async def trigger_calculate_indicators():
    """手動觸發技術指標計算"""
    try:
        from celery_app import celery_app
        from datetime import date, timedelta
        
        target_date = date.today() - timedelta(days=1)  # 昨天
        
        task = celery_app.send_task(
            'app.tasks.scheduled_tasks.calculate_daily_technical_indicators',
            args=[target_date],
            queue='calculations'
        )
        
        return {
            "message": "技術指標計算任務已啟動",
            "task_id": task.id,
            "target_date": target_date.isoformat(),
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"觸發技術指標計算失敗: {e}")
        raise HTTPException(status_code=500, detail=f"觸發技術指標計算失敗: {str(e)}")


# 手動觸發AI分析
@app.post("/api/admin/generate-recommendations")
async def trigger_ai_analysis():
    """手動觸發AI推薦生成（管理員功能）"""
    try:
        from celery_app import celery_app
        
        task = celery_app.send_task(
            'app.tasks.scheduled_tasks.generate_daily_recommendations',
            queue='ai_processing'
        )
        
        return {
            "message": "AI推薦生成任務已啟動",
            "task_id": task.id,
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"觸發AI分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"觸發AI分析失敗: {str(e)}")


# 查看任務佇列狀態
@app.get("/api/admin/celery-status")
async def get_celery_status():
    """查看Celery任務佇列狀態"""
    try:
        from celery_app import celery_app
        
        # 檢查Celery連接
        inspect = celery_app.control.inspect()
        
        # 獲取活躍任務
        active_tasks = inspect.active()
        
        # 獲取排程任務
        scheduled_tasks = inspect.scheduled()
        
        # 獲取Worker統計
        stats = inspect.stats()
        
        return {
            "celery_status": "connected" if active_tasks is not None else "disconnected",
            "active_tasks": active_tasks or {},
            "scheduled_tasks": scheduled_tasks or {},
            "worker_stats": stats or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"查詢Celery狀態失敗: {e}")
        return {
            "celery_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )