# backend/app/services/data_collector.py
"""
資料收集服務
整合各種資料源的收集功能
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, date
import sys
import os

# 添加 data_collector 到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from data_collector.scrapers.yahoo_finance import YahooFinanceScraper, collect_yahoo_data
from data_collector.scrapers.twse_scraper import TWSEScraper

from app.utils.logging import get_logger

logger = get_logger(__name__)


async def collect_stock_data(symbols: List[str], period: str = "1mo") -> Dict:
    """
    收集股票資料的主要函數
    """
    logger.info(f"開始收集 {len(symbols)} 檔股票資料")
    
    # 使用 Yahoo Finance 收集資料
    result = await collect_yahoo_data(symbols, period)
    
    return result


async def collect_twse_daily_data(target_date: date) -> Dict:
    """
    收集證交所每日資料
    """
    logger.info(f"開始收集證交所資料: {target_date}")
    
    async with TWSEScraper() as scraper:
        result = await scraper.collect_daily_data(target_date)
    
    return result


async def test_data_sources():
    """
    測試資料源連接
    """
    logger.info("測試資料源連接...")
    
    # 測試 Yahoo Finance
    try:
        async with YahooFinanceScraper() as scraper:
            test_data = await scraper.get_stock_info("2330")
            if test_data:
                logger.info("✅ Yahoo Finance 連接正常")
            else:
                logger.warning("⚠️ Yahoo Finance 連接異常")
    except Exception as e:
        logger.error(f"❌ Yahoo Finance 連接失敗: {e}")
    
    # 測試證交所
    try:
        async with TWSEScraper() as scraper:
            test_date = date.today()
            test_data = await scraper.get_market_statistics(test_date)
            if test_data:
                logger.info("✅ 證交所連接正常")
            else:
                logger.warning("⚠️ 證交所連接異常")
    except Exception as e:
        logger.error(f"❌ 證交所連接失敗: {e}")