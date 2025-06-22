#backend/tasks.py 
from celery import Celery
from app.config import settings

celery = Celery(
    'ai_stock_selector',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

@celery.task
def daily_data_update():
    # 呼叫資料收集器
    pass