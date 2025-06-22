# backend/app/tasks/__init__.py
"""
任務模組
所有Celery任務的統一入口
"""

from .scheduled_tasks import (
    daily_data_update,
    calculate_daily_technical_indicators,
    generate_daily_recommendations,
    cleanup_old_data,
    manual_update_stock
)

__all__ = [
    'daily_data_update',
    'calculate_daily_technical_indicators', 
    'generate_daily_recommendations',
    'cleanup_old_data',
    'manual_update_stock'
]