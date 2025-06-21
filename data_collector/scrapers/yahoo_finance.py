# data_collector/scrapers/yahoo_finance.py
"""
Yahoo Finance 資料收集器
負責收集台股的基本價量資料
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import json
from urllib.parse import quote

from app.config import settings, DATA_SOURCES_CONFIG

logger = logging.getLogger(__name__)


class YahooFinanceScraper:
    """Yahoo Finance 資料收集器"""
    
    def __init__(self):
        self.base_url = DATA_SOURCES_CONFIG["yahoo_finance"]["base_url"]
        self.rate_limit = DATA_SOURCES_CONFIG["yahoo_finance"]["rate_limit"]
        self.session = None
        self.request_count = 0
        self.last_request_time = None
    
    async def __aenter__(self):
        """異步上下文管理器進入"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.TIMEOUT_SECONDS),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit_wait(self):
        """速率限制等待"""
        current_time = datetime.now()
        
        if self.last_request_time:
            time_diff = (current_time - self.last_request_time).total_seconds()
            min_interval = 60 / self.rate_limit  # 每分鐘限制轉換為秒間隔
            
            if time_diff < min_interval:
                wait_time = min_interval - time_diff
                await asyncio.sleep(wait_time)
        
        self.last_request_time = current_time
        self.request_count += 1
    
    async def _make_request(self, url: str, params: dict = None) -> Optional[dict]:
        """發送HTTP請求"""
        await self._rate_limit_wait()
        
        retries = 0
        while retries < settings.MAX_RETRIES:
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Too Many Requests
                        wait_time = 2 ** retries
                        logger.warning(f"達到速率限制，等待 {wait_time} 秒")
                        await asyncio.sleep(wait_time)
                        retries += 1
                    else:
                        logger.error(f"HTTP錯誤 {response.status}: {url}")
                        return None
                        
            except Exception as e:
                logger.error(f"請求失敗 ({retries + 1}/{settings.MAX_RETRIES}): {e}")
                retries += 1
                if retries < settings.MAX_RETRIES:
                    await asyncio.sleep(settings.REQUEST_DELAY_SECONDS * retries)
        
        return None
    
    def _format_symbol(self, symbol: str) -> str:
        """格式化股票代號"""
        # 移除.TW後綴（如果存在）
        symbol = symbol.replace('.TW', '')
        # 確保是4位數字
        if symbol.isdigit() and len(symbol) <= 4:
            symbol = symbol.zfill(4)
        return f"{symbol}.TW"
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """取得股票基本資訊"""
        formatted_symbol = self._format_symbol(symbol)
        url = f"{self.base_url}/v8/finance/chart/{formatted_symbol}"
        
        params = {
            'interval': '1d',
            'range': '1d',
            'includePrePost': 'false'
        }
        
        try:
            data = await self._make_request(url, params)
            if not data or 'chart' not in data:
                return None
            
            chart_data = data['chart']['result'][0]
            meta = chart_data.get('meta', {})
            
            return {
                'symbol': symbol,
                'name': meta.get('longName', ''),
                'currency': meta.get('currency', 'TWD'),
                'exchange': meta.get('exchangeName', 'TPE'),
                'market_cap': meta.get('marketCap'),
                'shares_outstanding': meta.get('sharesOutstanding'),
                'regular_market_price': meta.get('regularMarketPrice'),
                'previous_close': meta.get('previousClose'),
                'timezone': meta.get('timezone', 'Asia/Taipei'),
                'updated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"取得股票資訊失敗 {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[List[Dict]]:
        """取得歷史價格資料"""
        formatted_symbol = self._format_symbol(symbol)
        url = f"{self.base_url}/v8/finance/chart/{formatted_symbol}"
        
        # 計算時間範圍
        end_time = int(datetime.now().timestamp())
        if period == "1d":
            start_time = end_time - 86400
        elif period == "1w":
            start_time = end_time - 604800
        elif period == "1mo":
            start_time = end_time - 2592000
        elif period == "3mo":
            start_time = end_time - 7776000
        elif period == "1y":
            start_time = end_time - 31536000
        else:
            start_time = end_time - 2592000  # 預設1個月
        
        params = {
            'interval': '1d',
            'period1': start_time,
            'period2': end_time,
            'includePrePost': 'false'
        }
        
        try:
            data = await self._make_request(url, params)
            if not data or 'chart' not in data:
                return None
            
            chart_data = data['chart']['result'][0]
            timestamps = chart_data.get('timestamp', [])
            indicators = chart_data.get('indicators', {})
            
            if not indicators or 'quote' not in indicators:
                return None
            
            quote = indicators['quote'][0]
            adj_close = indicators.get('adjclose', [{}])[0].get('adjclose', [])
            
            historical_data = []
            for i, timestamp in enumerate(timestamps):
                try:
                    trade_date = datetime.fromtimestamp(timestamp).date()
                    
                    # 檢查資料完整性
                    if (i >= len(quote.get('open', [])) or 
                        quote['open'][i] is None or
                        quote['close'][i] is None):
                        continue
                    
                    record = {
                        'symbol': symbol,
                        'trade_date': trade_date,
                        'open_price': float(quote['open'][i]),
                        'high_price': float(quote['high'][i]),
                        'low_price': float(quote['low'][i]),
                        'close_price': float(quote['close'][i]),
                        'volume': int(quote['volume'][i]) if quote['volume'][i] else 0,
                        'adj_close': float(adj_close[i]) if i < len(adj_close) and adj_close[i] else None
                    }
                    
                    # 計算漲跌
                    if i > 0 and quote['close'][i-1]:
                        prev_close = float(quote['close'][i-1])
                        record['price_change'] = record['close_price'] - prev_close
                        record['price_change_pct'] = (record['price_change'] / prev_close) * 100
                    
                    historical_data.append(record)
                    
                except (ValueError, TypeError, IndexError) as e:
                    logger.warning(f"處理歷史資料時跳過無效記錄 {symbol} {timestamp}: {e}")
                    continue
            
            return historical_data
            
        except Exception as e:
            logger.error(f"取得歷史資料失敗 {symbol}: {e}")
            return None
    
    async def get_realtime_quote(self, symbol: str) -> Optional[Dict]:
        """取得即時報價"""
        formatted_symbol = self._format_symbol(symbol)
        url = f"{self.base_url}/v8/finance/chart/{formatted_symbol}"
        
        params = {
            'interval': '1m',
            'range': '1d'
        }
        
        try:
            data = await self._make_request(url, params)
            if not data or 'chart' not in data:
                return None
            
            chart_data = data['chart']['result'][0]
            meta = chart_data.get('meta', {})
            
            return {
                'symbol': symbol,
                'current_price': meta.get('regularMarketPrice'),
                'previous_close': meta.get('previousClose'),
                'change': meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0),
                'change_percent': ((meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0)) / meta.get('previousClose', 1)) * 100,
                'volume': meta.get('regularMarketVolume'),
                'high': meta.get('regularMarketDayHigh'),
                'low': meta.get('regularMarketDayLow'),
                'open': meta.get('regularMarketOpen'),
                'market_time': meta.get('regularMarketTime'),
                'updated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"取得即時報價失敗 {symbol}: {e}")
            return None
    
    async def search_stocks(self, query: str) -> List[Dict]:
        """搜尋股票"""
        url = f"{self.base_url}/v1/finance/search"
        
        params = {
            'q': query,
            'quotesCount': 10,
            'newsCount': 0
        }
        
        try:
            data = await self._make_request(url, params)
            if not data or 'quotes' not in data:
                return []
            
            results = []
            for quote in data['quotes']:
                if quote.get('exchange') in ['TPE', 'TWO']:  # 台股交易所
                    results.append({
                        'symbol': quote.get('symbol', '').replace('.TW', ''),
                        'name': quote.get('shortname', ''),
                        'exchange': quote.get('exchange'),
                        'quote_type': quote.get('quoteType'),
                        'market_cap': quote.get('marketCap')
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"搜尋股票失敗 {query}: {e}")
            return []
    
    async def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量取得多檔股票資料"""
        results = {}
        
        # 使用信號量限制並發請求數
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        
        async def fetch_single_stock(symbol):
            async with semaphore:
                try:
                    # 取得基本資訊和歷史資料
                    info_task = self.get_stock_info(symbol)
                    history_task = self.get_historical_data(symbol, "1mo")
                    
                    info, history = await asyncio.gather(info_task, history_task)
                    
                    if info or history:
                        results[symbol] = {
                            'info': info,
                            'history': history,
                            'updated_at': datetime.now()
                        }
                    
                except Exception as e:
                    logger.error(f"批量取得股票資料失敗 {symbol}: {e}")
        
        # 並發執行所有任務
        tasks = [fetch_single_stock(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    def get_statistics(self) -> Dict:
        """取得收集器統計資訊"""
        return {
            'request_count': self.request_count,
            'last_request_time': self.last_request_time,
            'rate_limit': self.rate_limit,
            'base_url': self.base_url
        }


# 異步幫助函數
async def collect_yahoo_data(symbols: List[str], period: str = "1mo") -> Dict:
    """收集Yahoo Finance資料的主要函數"""
    async with YahooFinanceScraper() as scraper:
        logger.info(f"開始收集 {len(symbols)} 檔股票的Yahoo Finance資料")
        
        start_time = datetime.now()
        results = await scraper.get_multiple_stocks(symbols)
        end_time = datetime.now()
        
        logger.info(f"Yahoo Finance資料收集完成，耗時: {end_time - start_time}")
        logger.info(f"成功收集: {len(results)} 檔股票")
        
        return {
            'data': results,
            'statistics': scraper.get_statistics(),
            'collection_time': end_time - start_time,
            'success_count': len(results),
            'total_count': len(symbols)
        }


# 測試函數
async def test_yahoo_finance():
    """測試Yahoo Finance資料收集器"""
    test_symbols = ['2330', '2317', '2454']  # 台積電、鴻海、聯發科
    
    async with YahooFinanceScraper() as scraper:
        print("=== 測試Yahoo Finance資料收集器 ===")
        
        # 測試單一股票資訊
        print(f"取得2330股票資訊...")
        info = await scraper.get_stock_info('2330')
        print(f"結果: {info}")
        
        # 測試歷史資料
        print(f"取得2330歷史資料...")
        history = await scraper.get_historical_data('2330', '1w')
        print(f"歷史資料筆數: {len(history) if history else 0}")
        
        # 測試即時報價
        print(f"取得2330即時報價...")
        quote = await scraper.get_realtime_quote('2330')
        print(f"即時報價: {quote}")
        
        # 測試批量收集
        print(f"批量收集測試股票...")
        results = await scraper.get_multiple_stocks(test_symbols)
        print(f"批量收集結果: {len(results)} 檔股票")
        
        # 顯示統計
        stats = scraper.get_statistics()
        print(f"統計資訊: {stats}")


if __name__ == "__main__":
    asyncio.run(test_yahoo_finance())