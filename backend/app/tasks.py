# backend/app/tasks.py
"""
Celery Background Tasks
Celery背景任務
"""

import logging
from datetime import datetime, timedelta
from typing import List
import asyncio
from celery import current_task

from backend.celery_app import celery_app
from app.config import settings
from app.database import db_manager
from data_collector.scrapers.yahoo_finance import YahooFinanceScraper
from data_collector.scrapers.twse_scraper import TWSEScraper
from app.utils.indicators import TechnicalIndicators

# Setup logging
logger = logging.getLogger(__name__)

# Initialize scrapers
yahoo_scraper = YahooFinanceScraper()
twse_scraper = TWSEScraper()
tech_indicators = TechnicalIndicators()


def run_async_task(coro):
    """Helper function to run async functions in Celery tasks"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, name='app.tasks.daily_data_update')
def daily_data_update(self):
    """
    Daily data update task
    每日資料更新任務
    """
    try:
        logger.info("Starting daily data update task")
        current_task.update_state(state='PROGRESS', meta={'status': 'Starting data update'})
        
        # Get list of active stocks
        stocks = run_async_task(db_manager.get_active_stocks())
        total_stocks = len(stocks)
        
        updated_count = 0
        failed_count = 0
        
        for i, stock in enumerate(stocks):
            try:
                symbol = stock['symbol']
                
                # Update task progress
                progress = int((i / total_stocks) * 100)
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Processing {symbol}',
                        'current': i + 1,
                        'total': total_stocks,
                        'progress': progress
                    }
                )
                
                # Fetch price data from Yahoo Finance
                price_data = yahoo_scraper.get_stock_data(symbol)
                if price_data:
                    run_async_task(db_manager.save_daily_prices(symbol, price_data))
                    updated_count += 1
                
                # Fetch institutional trading data from TWSE
                institutional_data = twse_scraper.get_institutional_trading(symbol)
                if institutional_data:
                    run_async_task(db_manager.save_institutional_trading(symbol, institutional_data))
                
                # Fetch margin trading data
                margin_data = twse_scraper.get_margin_trading(symbol)
                if margin_data:
                    run_async_task(db_manager.save_margin_trading(symbol, margin_data))
                
            except Exception as e:
                logger.error(f"Failed to update data for {symbol}: {str(e)}")
                failed_count += 1
                continue
        
        # Final status
        result = {
            'status': 'completed',
            'updated_stocks': updated_count,
            'failed_stocks': failed_count,
            'total_stocks': total_stocks,
            'completion_time': datetime.now().isoformat()
        }
        
        logger.info(f"Daily data update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Daily data update failed: {str(e)}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task(bind=True, name='app.tasks.calculate_technical_indicators')
def calculate_technical_indicators(self, symbol: str):
    """
    Calculate technical indicators for a specific stock
    計算特定股票的技術指標
    """
    try:
        logger.info(f"Calculating technical indicators for {symbol}")
        
        # Get historical price data
        price_data = run_async_task(db_manager.get_price_history(symbol, days=200))
        
        if not price_data:
            logger.warning(f"No price data found for {symbol}")
            return {'status': 'no_data', 'symbol': symbol}
        
        # Calculate indicators
        indicators = tech_indicators.calculate_all_indicators(price_data)
        
        # Save to database
        run_async_task(db_manager.save_technical_indicators(symbol, indicators))
        
        logger.info(f"Technical indicators calculated for {symbol}")
        return {
            'status': 'completed',
            'symbol': symbol,
            'indicators_count': len(indicators)
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate indicators for {symbol}: {str(e)}")
        raise


@celery_app.task(bind=True, name='app.tasks.calculate_all_indicators')
def calculate_all_indicators(self):
    """
    Calculate technical indicators for all active stocks
    計算所有活躍股票的技術指標
    """
    try:
        logger.info("Starting technical indicators calculation for all stocks")
        
        # Get list of active stocks
        stocks = run_async_task(db_manager.get_active_stocks())
        total_stocks = len(stocks)
        
        completed_count = 0
        failed_count = 0
        
        for i, stock in enumerate(stocks):
            try:
                symbol = stock['symbol']
                
                # Update progress
                progress = int((i / total_stocks) * 100)
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Calculating indicators for {symbol}',
                        'current': i + 1,
                        'total': total_stocks,
                        'progress': progress
                    }
                )
                
                # Calculate indicators for this stock
                result = calculate_technical_indicators.delay(symbol)
                result.get(timeout=60)  # Wait for completion
                completed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to calculate indicators for {symbol}: {str(e)}")
                failed_count += 1
                continue
        
        result = {
            'status': 'completed',
            'completed_stocks': completed_count,
            'failed_stocks': failed_count,
            'total_stocks': total_stocks
        }
        
        logger.info(f"Technical indicators calculation completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Technical indicators calculation failed: {str(e)}")
        raise


@celery_app.task(bind=True, name='app.tasks.update_ai_recommendations')
def update_ai_recommendations(self):
    """
    Update AI stock recommendations
    更新AI股票推薦
    """
    try:
        logger.info("Starting AI recommendations update")
        
        # This will be implemented in Phase 2
        # For now, return a placeholder
        
        result = {
            'status': 'placeholder',
            'message': 'AI recommendations will be implemented in Phase 2',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("AI recommendations update completed (placeholder)")
        return result
        
    except Exception as e:
        logger.error(f"AI recommendations update failed: {str(e)}")
        raise


@celery_app.task(bind=True, name='app.tasks.cleanup_old_data')
def cleanup_old_data(self, days_to_keep: int = 365):
    """
    Clean up old data from database
    清理資料庫中的舊資料
    """
    try:
        logger.info(f"Starting data cleanup, keeping {days_to_keep} days")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Clean up old price data
        deleted_prices = run_async_task(
            db_manager.cleanup_old_prices(cutoff_date)
        )
        
        # Clean up old indicators
        deleted_indicators = run_async_task(
            db_manager.cleanup_old_indicators(cutoff_date)
        )
        
        # Clean up old institutional data
        deleted_institutional = run_async_task(
            db_manager.cleanup_old_institutional(cutoff_date)
        )
        
        result = {
            'status': 'completed',
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_records': {
                'prices': deleted_prices,
                'indicators': deleted_indicators,
                'institutional': deleted_institutional
            }
        }
        
        logger.info(f"Data cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {str(e)}")
        raise


@celery_app.task(bind=True, name='app.tasks.weekly_maintenance')
def weekly_maintenance(self):
    """
    Weekly maintenance tasks
    每週維護任務
    """
    try:
        logger.info("Starting weekly maintenance")
        
        # Update stock list from TWSE
        new_stocks = twse_scraper.get_stock_list()
        if new_stocks:
            run_async_task(db_manager.update_stock_list(new_stocks))
        
        # Recalculate all technical indicators
        calculate_all_indicators.delay()
        
        # Database maintenance
        run_async_task(db_manager.vacuum_analyze_tables())
        
        result = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'new_stocks_added': len(new_stocks) if new_stocks else 0
        }
        
        logger.info(f"Weekly maintenance completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Weekly maintenance failed: {str(e)}")
        raise


@celery_app.task(bind=True, name='app.tasks.health_check')
def health_check(self):
    """
    Health check task for monitoring
    系統健康檢查任務
    """
    try:
        # Check database connection
        db_status = run_async_task(db_manager.health_check())
        
        # Check Redis connection
        redis_status = celery_app.backend.get('health_check_test') is not None
        
        # Check external APIs
        yahoo_status = yahoo_scraper.health_check()
        twse_status = twse_scraper.health_check()
        
        result = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': db_status,
                'redis': redis_status,
                'yahoo_finance': yahoo_status,
                'twse': twse_status
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }