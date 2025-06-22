# backend/celery_app.py
"""
Celery Application Configuration
Celery應用程式配置
"""

import os
from celery import Celery
from celery.schedules import crontab

# Import settings
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "ai_stock_selector",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Taipei',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Task routing
    task_routes={
        'app.tasks.daily_data_update': {'queue': 'data_update'},
        'app.tasks.calculate_technical_indicators': {'queue': 'calculations'},
        'app.tasks.update_ai_recommendations': {'queue': 'ai_processing'},
        'app.tasks.cleanup_old_data': {'queue': 'maintenance'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'daily-data-update': {
            'task': 'app.tasks.daily_data_update',
            'schedule': crontab(hour=17, minute=0, day_of_week='1-5'),  # Weekdays at 5 PM
            'options': {'queue': 'data_update'}
        },
        'calculate-indicators': {
            'task': 'app.tasks.calculate_all_indicators',
            'schedule': crontab(hour=18, minute=0, day_of_week='1-5'),  # After data update
            'options': {'queue': 'calculations'}
        },
        'update-ai-recommendations': {
            'task': 'app.tasks.update_ai_recommendations',
            'schedule': crontab(hour=19, minute=0, day_of_week='1-5'),  # After indicators
            'options': {'queue': 'ai_processing'}
        },
        'weekly-maintenance': {
            'task': 'app.tasks.weekly_maintenance',
            'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Monday at 2 AM
            'options': {'queue': 'maintenance'}
        },
        'monthly-cleanup': {
            'task': 'app.tasks.cleanup_old_data',
            'schedule': crontab(hour=3, minute=0, day=1),  # First day of month
            'options': {'queue': 'maintenance'}
        }
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks()

if __name__ == '__main__':
    celery_app.start()