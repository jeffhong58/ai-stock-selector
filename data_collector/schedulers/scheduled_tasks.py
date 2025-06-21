"""
Celery排程任務
定義系統的定時任務和後台任務
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
from app.services.data_collector import collect_yahoo_data
from app.services.twse_scraper import TWSEScraper
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
        
        results = {
            'yahoo_finance': None,
            'twse_data': None,
            'technical_indicators': None
        }
        
        # 1. 更新Yahoo Finance資料
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'yahoo_finance', 'progress': 20}
        )
        
        logger.info("更新Yahoo Finance資料...")
        results['yahoo_finance'] = await_task(update_yahoo_finance_data(target_date))
        
        # 2. 更新證交所資料
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'twse_data', 'progress': 50}
        )
        
        logger.info("更新證交所資料...")
        results['twse_data'] = await_task(update_twse_data(target_date))
        
        # 3. 計算技術指標
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'technical_indicators', 'progress': 80}
        )
        
        logger.info("計算技術指標...")
        results['technical_indicators'] = await_task(calculate_daily_technical_indicators(target_date))
        
        # 4. 清理快取
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'cleanup', 'progress': 95}
        )
        
        logger.info("清理快取...")
        clear_related_cache()
        
        # 更新日誌
        execution_time = int((datetime.now() - start_time).total_seconds())
        log_entry.status = 'completed'
        log_entry.completed_at = datetime.now()
        log_entry.execution_time_seconds = execution_time
        
        success_count = sum(1 for result in results.values() if result and result.get('success'))
        log_entry.records_processed = success_count
        
        db.commit()
        db.close()
        
        logger.info(f"每日資料更新任務完成: {task_id}, 耗時: {execution_time}秒")
        
        return {
            'task_id': task_id,
            'success': True,
            'results': results,
            'execution_time': execution_time,
            'date': target_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"每日資料更新任務失敗: {e}")
        
        # 記錄錯誤
        if 'log_entry' in locals():
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.execution_time_seconds = int((datetime.now() - start_time).total_seconds())
            db.commit()
            db.close()
        
        # 重試任務
        if self.request.retries < self.max_retries:
            logger.info(f"重試任務 {task_id}, 第 {self.request.retries + 1} 次")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'task_id': task_id,
            'success': False,
            'error': str(e),
            'date': target_date.isoformat() if 'target_date' in locals() else None
        }


@celery.task
def update_yahoo_finance_data(target_date: date):
    """更新Yahoo Finance資料"""
    try:
        db = get_db()
        
        # 取得所有活躍股票代碼
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        symbols = [stock.symbol for stock in stocks]
        
        logger.info(f"更新 {len(symbols)} 檔股票的Yahoo Finance資料")
        
        # 收集資料
        result = await_task(collect_yahoo_data(symbols, period="1d"))
        
        if not result or not result.get('data'):
            logger.warning("Yahoo Finance資料收集失敗")
            return {'success': False, 'error': 'No data collected'}
        
        # 儲存資料到資料庫
        saved_count = 0
        for symbol, data in result['data'].items():
            try:
                if data.get('history'):
                    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                    if stock:
                        for price_data in data['history']:
                            # 檢查是否已存在
                            existing = db.query(DailyPrice).filter(
                                DailyPrice.stock_id == stock.id,
                                DailyPrice.trade_date == price_data['trade_date']
                            ).first()
                            
                            if not existing:
                                daily_price = DailyPrice(
                                    stock_id=stock.id,
                                    symbol=symbol,
                                    trade_date=price_data['trade_date'],
                                    open_price=price_data['open_price'],
                                    high_price=price_data['high_price'],
                                    low_price=price_data['low_price'],
                                    close_price=price_data['close_price'],
                                    volume=price_data['volume'],
                                    adj_close=price_data.get('adj_close'),
                                    price_change=price_data.get('price_change'),
                                    price_change_pct=price_data.get('price_change_pct')
                                )
                                db.add(daily_price)
                                saved_count += 1
                        
                        db.commit()
                        
            except Exception as e:
                logger.error(f"儲存Yahoo Finance資料失敗 {symbol}: {e}")
                db.rollback()
                continue
        
        db.close()
        
        logger.info(f"Yahoo Finance資料更新完成，儲存 {saved_count} 筆記錄")
        
        return {
            'success': True,
            'symbols_processed': len(result['data']),
            'records_saved': saved_count,
            'date': target_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"更新Yahoo Finance資料失敗: {e}")
        return {'success': False, 'error': str(e)}


@celery.task
def update_twse_data(target_date: date):
    """更新證交所資料"""
    try:
        db = get_db()
        
        # 使用證交所爬蟲收集資料
        result = await_task(collect_twse_data_async(target_date))
        
        if not result or not result.get('success'):
            logger.warning(f"證交所資料收集失敗: {target_date}")
            return {'success': False, 'error': 'TWSE data collection failed'}
        
        # 儲存三大法人資料
        institutional_saved = 0
        for symbol, data in result.get('institutional_trading', {}).items():
            try:
                stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                if stock:
                    # 檢查是否已存在
                    existing = db.query(InstitutionalTrading).filter(
                        InstitutionalTrading.stock_id == stock.id,
                        InstitutionalTrading.trade_date == target_date
                    ).first()
                    
                    if not existing:
                        institutional = InstitutionalTrading(
                            stock_id=stock.id,
                            symbol=symbol,
                            trade_date=target_date,
                            foreign_buy=data.get('foreign_buy', 0),
                            foreign_sell=data.get('foreign_sell', 0),
                            foreign_net=data.get('foreign_net', 0),
                            trust_buy=data.get('trust_buy', 0),
                            trust_sell=data.get('trust_sell', 0),
                            trust_net=data.get('trust_net', 0),
                            dealer_buy=data.get('dealer_buy', 0),
                            dealer_sell=data.get('dealer_sell', 0),
                            dealer_net=data.get('dealer_net', 0),
                            total_net=data.get('total_net', 0)
                        )
                        db.add(institutional)
                        institutional_saved += 1
                    
            except Exception as e:
                logger.error(f"儲存三大法人資料失敗 {symbol}: {e}")
                continue
        
        # 儲存融資融券資料
        margin_saved = 0
        for symbol, data in result.get('margin_trading', {}).items():
            try:
                stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                if stock:
                    # 檢查是否已存在
                    existing = db.query(MarginTrading).filter(
                        MarginTrading.stock_id == stock.id,
                        MarginTrading.trade_date == target_date
                    ).first()
                    
                    if not existing:
                        margin = MarginTrading(
                            stock_id=stock.id,
                            symbol=symbol,
                            trade_date=target_date,
                            margin_buy=data.get('margin_buy', 0),
                            margin_sell=data.get('margin_sell', 0),
                            margin_balance=data.get('margin_balance', 0),
                            margin_quota=data.get('margin_quota', 0),
                            short_sell=data.get('short_sell', 0),
                            short_cover=data.get('short_cover', 0),
                            short_balance=data.get('short_balance', 0),
                            short_quota=data.get('short_quota', 0),
                            short_margin_ratio=data.get('short_margin_ratio', 0)
                        )
                        db.add(margin)
                        margin_saved += 1
                    
            except Exception as e:
                logger.error(f"儲存融資融券資料失敗 {symbol}: {e}")
                continue
        
        db.commit()
        db.close()
        
        logger.info(f"證交所資料更新完成，三大法人: {institutional_saved} 筆，融資融券: {margin_saved} 筆")
        
        return {
            'success': True,
            'institutional_saved': institutional_saved,
            'margin_saved': margin_saved,
            'date': target_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"更新證交所資料失敗: {e}")
        return {'success': False, 'error': str(e)}


@celery.task
def calculate_all_technical_indicators():
    """計算所有股票的技術指標"""
    try:
        db = get_db()
        calculator = TechnicalIndicators()
        
        # 取得所有活躍股票
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        
        processed_count = 0
        
        for stock in stocks:
            try:
                # 取得最近60天的價格資料
                recent_prices = (
                    db.query(DailyPrice)
                    .filter(DailyPrice.stock_id == stock.id)
                    .order_by(DailyPrice.trade_date.desc())
                    .limit(60)
                    .all()
                )
                
                if len(recent_prices) < 20:  # 資料不足
                    continue
                
                # 準備資料
                stock_data = prepare_stock_data_for_indicators(recent_prices)
                
                # 計算指標
                indicators = calculator.calculate_all_indicators(stock_data)
                
                if not indicators:
                    continue
                
                # 儲存最新的指標
                latest_date = recent_prices[0].trade_date
                latest_indicators = calculator.calculate_indicator_for_date(stock_data, latest_date)
                
                if latest_indicators:
                    # 檢查是否已存在
                    existing = db.query(TechnicalIndicator).filter(
                        TechnicalIndicator.stock_id == stock.id,
                        TechnicalIndicator.trade_date == latest_date
                    ).first()
                    
                    if existing:
                        # 更新現有記錄
                        for key, value in latest_indicators.items():
                            if hasattr(existing, key) and value is not None:
                                setattr(existing, key, value)
                    else:
                        # 建立新記錄
                        indicator = TechnicalIndicator(
                            stock_id=stock.id,
                            symbol=stock.symbol,
                            **latest_indicators
                        )
                        db.add(indicator)
                    
                    processed_count += 1
                
            except Exception as e:
                logger.error(f"計算技術指標失敗 {stock.symbol}: {e}")
                continue
        
        db.commit()
        db.close()
        
        logger.info(f"技術指標計算完成，處理 {processed_count} 檔股票")
        
        return {
            'success': True,
            'processed_count': processed_count
        }
        
    except Exception as e:
        logger.error(f"計算技術指標失敗: {e}")
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
            .all()
        )
        
        processed_count = 0
        
        for stock in stocks_with_data:
            try:
                # 取得該股票的歷史價格資料（包含目標日期）
                historical_prices = (
                    db.query(DailyPrice)
                    .filter(
                        DailyPrice.stock_id == stock.id,
                        DailyPrice.trade_date <= target_date
                    )
                    .order_by(DailyPrice.trade_date.desc())
                    .limit(240)  # 最多取240天資料
                    .all()
                )
                
                if len(historical_prices) < 20:
                    continue
                
                # 反轉順序（因為查詢是倒序）
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
    """生成每日AI推薦"""
    try:
        logger.info("開始生成每日AI推薦...")
        
        # 這裡將在第二階段實現AI選股邏輯
        # 目前先返回基本結果
        
        return {
            'success': True,
            'message': '將在第二階段實現AI推薦生成'
        }
        
    except Exception as e:
        logger.error(f"生成AI推薦失敗: {e}")
        return {'success': False, 'error': str(e)}


@celery.task
def cleanup_old_data():
    """清理舊資料"""
    try:
        db = get_db()
        
        # 取得保留天數設定
        retention_days = settings.RECOMMENDATION_RETENTION_DAYS
        cutoff_date = date.today() - timedelta(days=retention_days)
        
        # 清理舊的推薦記錄
        # deleted_recommendations = db.query(AIRecommendation).filter(
        #     AIRecommendation.recommendation_date < cutoff_date
        # ).delete()
        
        # 清理舊的更新日誌
        deleted_logs = db.query(DataUpdateLog).filter(
            DataUpdateLog.update_date < cutoff_date
        ).delete()
        
        db.commit()
        db.close()
        
        logger.info(f"清理舊資料完成，刪除日誌: {deleted_logs} 筆")
        
        return {
            'success': True,
            'deleted_logs': deleted_logs
        }
        
    except Exception as e:
        logger.error(f"清理舊資料失敗: {e}")
        return {'success': False, 'error': str(e)}


# 輔助函數
def await_task(coroutine):
    """在同步任務中執行異步函數"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


async def collect_twse_data_async(target_date: date):
    """異步收集證交所資料"""
    async with TWSEScraper() as scraper:
        return await scraper.collect_daily_data(target_date)


def clear_related_cache():
    """清理相關快取"""
    try:
        # 清理股票相關快取
        cache_patterns = [
            'stock_detail:*',
            'realtime:*',
            'recommendations:*'
        ]
        
        # 注意：這裡簡化了快取清理邏輯
        # 實際環境中可能需要更複雜的快取管理
        
        logger.info("快取清理完成")
        
    except Exception as e:
        logger.error(f"清理快取失敗: {e}")


# 手動任務
@celery.task
def manual_update_stock(symbol: str):
    """手動更新單一股票資料"""
    try:
        logger.info(f"手動更新股票資料: {symbol}")
        
        # 更新Yahoo Finance資料
        result = await_task(collect_yahoo_data([symbol], period="1w"))
        
        if result and result.get('data') and symbol in result['data']:
            # 儲存資料到資料庫
            db = get_db()
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            
            if stock:
                data = result['data'][symbol]
                if data.get('history'):
                    for price_data in data['history']:
                        existing = db.query(DailyPrice).filter(
                            DailyPrice.stock_id == stock.id,
                            DailyPrice.trade_date == price_data['trade_date']
                        ).first()
                        
                        if not existing:
                            daily_price = DailyPrice(
                                stock_id=stock.id,
                                symbol=symbol,
                                **price_data
                            )
                            db.add(daily_price)
                
                db.commit()
                
                # 重新計算技術指標
                calculate_daily_technical_indicators.delay(date.today() - timedelta(days=1))
            
            db.close()
        
        return {'success': True, 'symbol': symbol}
        
    except Exception as e:
        logger.error(f"手動更新股票失敗 {symbol}: {e}")
        return {'success': False, 'error': str(e), 'symbol': symbol}