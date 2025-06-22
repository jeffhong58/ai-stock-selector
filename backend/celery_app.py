# backend/celery_app.py
"""
統一的Celery應用配置
所有Celery相關設定都在這裡
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

# 建立Celery實例
celery_app = Celery(
    "ai_stock_selector",
    broker=settings.REDIS_URL.replace('/0', '/1'),  # 使用Redis DB 1
    backend=settings.REDIS_URL.replace('/0', '/1'),
)

# Celery配置
celery_app.conf.update(
    # 基本設定
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,
    
    # 任務設定
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分鐘超時
    task_soft_time_limit=25 * 60,  # 25分鐘軟超時
    task_acks_late=True,
    
    # Worker設定
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    
    # 結果設定
    result_expires=3600,  # 1小時
    result_persistent=True,
    
    # 任務路由
    task_routes={
        'app.tasks.scheduled_tasks.daily_data_update': {'queue': 'data_update'},
        'app.tasks.scheduled_tasks.calculate_daily_technical_indicators': {'queue': 'calculations'},
        'app.tasks.scheduled_tasks.generate_daily_recommendations': {'queue': 'ai_processing'},
        'app.tasks.scheduled_tasks.cleanup_old_data': {'queue': 'maintenance'},
        'app.tasks.scheduled_tasks.manual_update_stock': {'queue': 'data_update'},
    },
    
    # 自動發現任務
    include=[
        'app.tasks.scheduled_tasks',
    ],
    
    # Beat排程設定
    beat_schedule={
        # 每日資料更新 - 平日17:30
        'daily-data-update': {
            'task': 'app.tasks.scheduled_tasks.daily_data_update',
            'schedule': crontab(hour=17, minute=30, day_of_week='1-5'),
            'options': {'queue': 'data_update'}
        },
        
        # 計算技術指標 - 平日18:30
        'calculate-indicators': {
            'task': 'app.tasks.scheduled_tasks.calculate_daily_technical_indicators',
            'schedule': crontab(hour=18, minute=30, day_of_week='1-5'),
            'options': {'queue': 'calculations'}
        },
        
        # 生成AI推薦 - 平日19:00
        'generate-recommendations': {
            'task': 'app.tasks.scheduled_tasks.generate_daily_recommendations',
            'schedule': crontab(hour=19, minute=0, day_of_week='1-5'),
            'options': {'queue': 'ai_processing'}
        },
        
        # 清理舊資料 - 每日02:00
        'cleanup-old-data': {
            'task': 'app.tasks.scheduled_tasks.cleanup_old_data',
            'schedule': crontab(hour=2, minute=0),
            'options': {'queue': 'maintenance'}
        },
    },
)

# 自動發現任務
celery_app.autodiscover_tasks()

if __name__ == '__main__':
    celery_app.start()