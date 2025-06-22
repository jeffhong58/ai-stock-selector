# backend/app/tasks/scheduled_tasks.py
"""
統一的Celery排程任務定義
整合所有後台任務到統一位置
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from celery import current_task
from sqlalchemy.orm import Session

from app.main import celery
from app.database import SessionLocal, redis_manager
from app.models.stock import Stock, DailyPrice, TechnicalIndicator, InstitutionalTrading, MarginTrading, DataUpdateLog
from app.utils.indicators import TechnicalIndicators, prepare_stock_data_for_indicators
from app.config import settings

logger = logging.getLogger(__name__)


def get_db():
    """取得資料庫會話"""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def await_task(coroutine):
    """在同步任務中執行異步函數"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


@celery.task(bind=True, max_retries=3)
def daily_data_update(self):
    """每日資料更新任務"""
    task_id = self.request.id
    start_time = datetime.now()
    
    try:
        logger.info(f"開始每日資料更新任務: {task_id}")
        
        # 更新任務狀態
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'starting', 'progress': 0}
        )
        
        db = get_db()
        target_date = date.today() - timedelta(days=1)  # 昨天的資料
        
        # 記錄任務開始
        log_entry = DataUpdateLog(
            update_date=target_date,
            data_source='daily_update',
            table_name='multiple',
            status='processing'
        )
        db.add(log_entry)
        db.commit()
        
        # 1. 更新Yahoo Finance資料
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'yahoo_finance', 'progress': 20}
        )
        
        logger.info("更新Yahoo Finance資料...")
        yahoo_result = await_task(update_yahoo_finance_data(target_date))
        
        # 2. 更新證交所資料
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'twse_data', 'progress': 50}
        )
        
        logger.info("更新證交所資料...")
        twse_result = await_task(update_twse_data(target_date))
        
        # 3. 計算技術指標
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'technical_indicators', 'progress': 80}
        )
        
        logger.info("計算技術指標...")
        indicators_result = calculate_daily_technical_indicators(target_date)
        
        # 更新日誌
        execution_time = int((datetime.now() - start_time).total_seconds())
        log_entry.status = 'completed'
        log_entry.completed_at = datetime.now()
        log_entry.execution_time_seconds = execution_time
        log_entry.records_processed = 1  # 簡化統計
        
        db.commit()
        db.close()
        
        logger.info(f"每日資料更新任務完成: {task_id}, 耗時: {execution_time}秒")
        
        return {
            'task_id': task_id,
            'success': True,
            'yahoo_result': yahoo_result,
            'twse_result': twse_result,
            'indicators_result': indicators_result,
            'execution_time': execution_time,
            'date': target_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"每日資料更新任務失敗: {e}")
        
        if 'log_entry' in locals():
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.execution_time_seconds = int((datetime.now() - start_time).total_seconds())
            db.commit()
            db.close()
        
        if self.request.retries < self.max_retries:
            logger.info(f"重試任務 {task_id}, 第 {self.request.retries + 1} 次")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'task_id': task_id,
            'success': False,
            'error': str(e),
            'date': target_date.isoformat() if 'target_date' in locals() else None
        }


async def update_yahoo_finance_data(target_date: date):
    """更新Yahoo Finance資料"""
    try:
        # 這裡需要實際的Yahoo Finance API調用
        # 目前先返回模擬結果
        from app.services.data_collector import collect_yahoo_data
        
        db = get_db()
        stocks = db.query(Stock).filter(Stock.is_active == True).limit(10).all()
        symbols = [stock.symbol for stock in stocks]
        
        result = await collect_yahoo_data(symbols, period="1d")
        
        db.close()
        return {'success': True, 'records': len(result.get('data', {}))}
        
    except Exception as e:
        logger.error(f"更新Yahoo Finance資料失敗: {e}")
        return {'success': False, 'error': str(e)}


async def update_twse_data(target_date: date):
    """更新證交所資料"""
    try:
        # 這裡需要實際的證交所API調用
        # 目前先返回模擬結果
        logger.info(f"更新證交所資料: {target_date}")
        return {'success': True, 'records': 100}
        
    except Exception as e:
        logger.error(f"更新證交所資料失敗: {e}")
        return {'success': False, 'error': str(e)}


@celery.task
def calculate_daily_technical_indicators(target_date: date):
    """計算指定日期的技術指標"""
    try:
        db = get_db()
        calculator = TechnicalIndicators()
        
        # 取得所有有價格資料的股票
        stocks_with_data = (
            db.query(Stock)
            .join(DailyPrice)
            .filter(
                Stock.is_active == True,
                DailyPrice.trade_date == target_date
            )
            .distinct()
            .limit(10)  # 限制數量以避免處理時間過長
            .all()
        )
        
        processed_count = 0
        
        for stock in stocks_with_data:
            try:
                # 取得該股票的歷史價格資料
                historical_prices = (
                    db.query(DailyPrice)
                    .filter(
                        DailyPrice.stock_id == stock.id,
                        DailyPrice.trade_date <= target_date
                    )
                    .order_by(DailyPrice.trade_date.desc())
                    .limit(60)  # 取60天資料
                    .all()
                )
                
                if len(historical_prices) < 20:
                    continue
                
                # 反轉順序
                historical_prices.reverse()
                
                # 準備資料
                stock_data = prepare_stock_data_for_indicators(historical_prices)
                
                # 計算該日期的指標
                indicators = calculator.calculate_indicator_for_date(stock_data, target_date)
                
                if not indicators:
                    continue
                
                # 檢查是否已存在
                existing = db.query(TechnicalIndicator).filter(
                    TechnicalIndicator.stock_id == stock.id,
                    TechnicalIndicator.trade_date == target_date
                ).first()
                
                if existing:
                    # 更新現有記錄
                    for key, value in indicators.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                else:
                    # 建立新記錄
                    indicator = TechnicalIndicator(
                        stock_id=stock.id,
                        symbol=stock.symbol,
                        **indicators
                    )
                    db.add(indicator)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"計算 {stock.symbol} 的技術指標失敗: {e}")
                continue
        
        db.commit()
        db.close()
        
        logger.info(f"日期 {target_date} 技術指標計算完成，處理 {processed_count} 檔股票")
        
        return {
            'success': True,
            'processed_count': processed_count,
            'date': target_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"計算日期技術指標失敗: {e}")
        return {'success': False, 'error': str(e)}


@celery.task
def generate_daily_recommendations():
    """生成每日AI推薦（第二階段實現）"""
    try:
        logger.info("開始生成每日AI推薦（第二階段功能）...")
        
        return {
            'success': True,
            'message': '將在第二階段實現AI推薦生成',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"生成AI推薦失敗: {e}")
        return {'success': False, 'error': str(e)}


@celery.task
def cleanup_old_data():
    """清理舊資料"""
    try:
        db = get_db()
        
        retention_days = settings.RECOMMENDATION_RETENTION_DAYS
        cutoff_date = date.today() - timedelta(days=retention_days)
        
        # 清理舊的更新日誌
        deleted_logs = db.query(DataUpdateLog).filter(
            DataUpdateLog.update_date < cutoff_date
        ).delete()
        
        db.commit()
        db.close()
        
        logger.info(f"清理舊資料完成，刪除日誌: {deleted_logs} 筆")
        
        return {
            'success': True,
            'deleted_logs': deleted_logs,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理舊資料失敗: {e}")
        return {'success': False, 'error': str(e)}


@celery.task
def manual_update_stock(symbol: str):
    """手動更新單一股票資料"""
    try:
        logger.info(f"手動更新股票資料: {symbol}")
        
        # 這裡會呼叫實際的資料收集邏輯
        result = await_task(update_single_stock(symbol))
        
        return {'success': True, 'symbol': symbol, 'result': result}
        
    except Exception as e:
        logger.error(f"手動更新股票失敗 {symbol}: {e}")
        return {'success': False, 'error': str(e), 'symbol': symbol}


async def update_single_stock(symbol: str):
    """更新單一股票的資料"""
    try:
        from app.services.data_collector import collect_yahoo_data
        
        result = await collect_yahoo_data([symbol], period="1w")
        
        if result and result.get('data') and symbol in result['data']:
            return result['data'][symbol]
        
        return None
        
    except Exception as e:
        logger.error(f"收集股票資料失敗 {symbol}: {e}")
        return None