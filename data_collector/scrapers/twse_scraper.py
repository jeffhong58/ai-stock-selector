"""
證交所資料收集器
負責收集三大法人買賣、融資融券等資料
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import json
import time
from urllib.parse import urlencode

from app.config import settings, DATA_SOURCES_CONFIG

logger = logging.getLogger(__name__)


class TWSEScraper:
    """證交所資料收集器"""
    
    def __init__(self):
        self.base_url = DATA_SOURCES_CONFIG["twse"]["base_url"]
        self.rate_limit = DATA_SOURCES_CONFIG["twse"]["rate_limit"]
        self.session = None
        self.request_count = 0
        self.last_request_time = None
    
    async def __aenter__(self):
        """異步上下文管理器進入"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.TIMEOUT_SECONDS),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.twse.com.tw/'
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
            min_interval = 60 / self.rate_limit
            
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
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            text = await response.text()
                            # 證交所有時會回傳包含BOM的內容
                            if text.startswith('\ufeff'):
                                text = text[1:]
                            return json.loads(text)
                    elif response.status == 429:
                        wait_time = 2 ** retries * 2  # 證交所需要更長等待時間
                        logger.warning(f"證交所速率限制，等待 {wait_time} 秒")
                        await asyncio.sleep(wait_time)
                        retries += 1
                    else:
                        logger.error(f"證交所HTTP錯誤 {response.status}: {url}")
                        return None
                        
            except Exception as e:
                logger.error(f"證交所請求失敗 ({retries + 1}/{settings.MAX_RETRIES}): {e}")
                retries += 1
                if retries < settings.MAX_RETRIES:
                    await asyncio.sleep(settings.REQUEST_DELAY_SECONDS * retries * 2)
        
        return None
    
    def _format_date(self, target_date: date) -> str:
        """格式化日期為證交所格式 (YYYYMMDD)"""
        return target_date.strftime('%Y%m%d')
    
    def _parse_date_string(self, date_str: str) -> date:
        """解析證交所日期字串"""
        try:
            if '/' in date_str:
                # 民國年格式 111/12/31
                parts = date_str.split('/')
                year = int(parts[0]) + 1911  # 轉換為西元年
                month = int(parts[1])
                day = int(parts[2])
                return date(year, month, day)
            else:
                # YYYYMMDD格式
                return datetime.strptime(date_str, '%Y%m%d').date()
        except Exception as e:
            logger.error(f"日期解析失敗: {date_str}, {e}")
            return None
    
    async def get_institutional_trading(self, target_date: date) -> Dict:
        """取得三大法人買賣資料"""
        url = f"{self.base_url}/fund/T86"
        
        params = {
            'response': 'json',
            'date': self._format_date(target_date),
            'selectType': 'ALL'
        }
        
        try:
            data = await self._make_request(url, params)
            if not data or 'data' not in data:
                logger.warning(f"三大法人資料為空: {target_date}")
                return {}
            
            institutional_data = {}
            
            for row in data['data']:
                if len(row) < 15:  # 確保資料完整
                    continue
                
                try:
                    symbol = row[0].strip()
                    name = row[1].strip()
                    
                    # 跳過非股票資料（如總計、指數等）
                    if not symbol.isdigit() or len(symbol) != 4:
                        continue
                    
                    institutional_data[symbol] = {
                        'symbol': symbol,
                        'name': name,
                        'trade_date': target_date,
                        
                        # 外資 (包含外資自營)
                        'foreign_buy': self._parse_number(row[2]),
                        'foreign_sell': self._parse_number(row[3]),
                        'foreign_net': self._parse_number(row[4]),
                        
                        # 投信
                        'trust_buy': self._parse_number(row[5]),
                        'trust_sell': self._parse_number(row[6]),
                        'trust_net': self._parse_number(row[7]),
                        
                        # 自營商 (避險)
                        'dealer_hedge_buy': self._parse_number(row[8]),
                        'dealer_hedge_sell': self._parse_number(row[9]),
                        'dealer_hedge_net': self._parse_number(row[10]),
                        
                        # 自營商 (自行買賣)
                        'dealer_prop_buy': self._parse_number(row[11]),
                        'dealer_prop_sell': self._parse_number(row[12]),
                        'dealer_prop_net': self._parse_number(row[13]),
                        
                        # 三大法人合計
                        'total_net': self._parse_number(row[14])
                    }
                    
                    # 計算自營商總計
                    institutional_data[symbol]['dealer_buy'] = (
                        institutional_data[symbol]['dealer_hedge_buy'] + 
                        institutional_data[symbol]['dealer_prop_buy']
                    )
                    institutional_data[symbol]['dealer_sell'] = (
                        institutional_data[symbol]['dealer_hedge_sell'] + 
                        institutional_data[symbol]['dealer_prop_sell']
                    )
                    institutional_data[symbol]['dealer_net'] = (
                        institutional_data[symbol]['dealer_hedge_net'] + 
                        institutional_data[symbol]['dealer_prop_net']
                    )
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"解析三大法人資料失敗: {row}, {e}")
                    continue
            
            logger.info(f"取得三大法人資料: {target_date}, {len(institutional_data)} 檔股票")
            return institutional_data
            
        except Exception as e:
            logger.error(f"取得三大法人資料失敗 {target_date}: {e}")
            return {}
    
    async def get_margin_trading(self, target_date: date) -> Dict:
        """取得融資融券資料"""
        url = f"{self.base_url}/exchangeReport/MI_MARGN"
        
        params = {
            'response': 'json',
            'date': self._format_date(target_date),
            'selectType': 'ALL'
        }
        
        try:
            data = await self._make_request(url, params)
            if not data or 'data' not in data:
                logger.warning(f"融資融券資料為空: {target_date}")
                return {}
            
            margin_data = {}
            
            for row in data['data']:
                if len(row) < 12:  # 確保資料完整
                    continue
                
                try:
                    symbol = row[0].strip()
                    name = row[1].strip()
                    
                    # 跳過非股票資料
                    if not symbol.isdigit() or len(symbol) != 4:
                        continue
                    
                    margin_data[symbol] = {
                        'symbol': symbol,
                        'name': name,
                        'trade_date': target_date,
                        
                        # 融資
                        'margin_buy': self._parse_number(row[2]),
                        'margin_sell': self._parse_number(row[3]),
                        'margin_balance': self._parse_number(row[5]),
                        'margin_quota': self._parse_number(row[6]),
                        
                        # 融券
                        'short_sell': self._parse_number(row[7]),
                        'short_cover': self._parse_number(row[8]),
                        'short_balance': self._parse_number(row[10]),
                        'short_quota': self._parse_number(row[11])
                    }
                    
                    # 計算券資比
                    if margin_data[symbol]['margin_balance'] > 0:
                        margin_data[symbol]['short_margin_ratio'] = (
                            margin_data[symbol]['short_balance'] / 
                            margin_data[symbol]['margin_balance'] * 100
                        )
                    else:
                        margin_data[symbol]['short_margin_ratio'] = 0
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"解析融資融券資料失敗: {row}, {e}")
                    continue
            
            logger.info(f"取得融資融券資料: {target_date}, {len(margin_data)} 檔股票")
            return margin_data
            
        except Exception as e:
            logger.error(f"取得融資融券資料失敗 {target_date}: {e}")
            return {}
    
    async def get_daily_trading_summary(self, target_date: date) -> Dict:
        """取得每日成交資訊"""
        url = f"{self.base_url}/exchangeReport/FMTQIK"
        
        params = {
            'response': 'json',
            'date': self._format_date(target_date)
        }
        
        try:
            data = await self._make_request(url, params)
            if not data or 'data' not in data:
                return {}
            
            # 取得大盤資訊
            for row in data['data']:
                if len(row) > 2 and '發行量加權股價指數' in str(row[0]):
                    return {
                        'trade_date': target_date,
                        'taiex_index': self._parse_number(row[1]),
                        'taiex_change': self._parse_number(row[2]),
                        'total_volume': self._parse_number(row[3]) if len(row) > 3 else None,
                        'total_turnover': self._parse_number(row[4]) if len(row) > 4 else None
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"取得每日成交資訊失敗 {target_date}: {e}")
            return {}
    
    async def get_market_statistics(self, target_date: date) -> Dict:
        """取得市場統計資料"""
        url = f"{self.base_url}/exchangeReport/BFIAMU"
        
        params = {
            'response': 'json',
            'date': self._format_date(target_date)
        }
        
        try:
            data = await self._make_request(url, params)
            if not data or 'data' not in data:
                return {}
            
            stats = {
                'trade_date': target_date,
                'up_stocks': 0,
                'down_stocks': 0,
                'unchanged_stocks': 0,
                'total_stocks': 0
            }
            
            for row in data['data']:
                if len(row) >= 4 and '上漲' in str(row[0]):
                    stats['up_stocks'] = self._parse_number(row[1])
                elif len(row) >= 4 and '下跌' in str(row[0]):
                    stats['down_stocks'] = self._parse_number(row[1])
                elif len(row) >= 4 and '平盤' in str(row[0]):
                    stats['unchanged_stocks'] = self._parse_number(row[1])
            
            stats['total_stocks'] = (
                stats['up_stocks'] + 
                stats['down_stocks'] + 
                stats['unchanged_stocks']
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"取得市場統計失敗 {target_date}: {e}")
            return {}
    
    def _parse_number(self, value) -> int:
        """解析數字字串"""
        if not value or value == '--':
            return 0
        
        try:
            # 移除逗號和空格
            value = str(value).replace(',', '').replace(' ', '')
            if value == '' or value == 'N/A':
                return 0
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    async def collect_daily_data(self, target_date: date) -> Dict:
        """收集指定日期的所有證交所資料"""
        logger.info(f"開始收集證交所資料: {target_date}")
        
        tasks = [
            self.get_institutional_trading(target_date),
            self.get_margin_trading(target_date),
            self.get_daily_trading_summary(target_date),
            self.get_market_statistics(target_date)
        ]
        
        try:
            institutional, margin, trading_summary, market_stats = await asyncio.gather(
                *tasks, return_exceptions=True
            )
            
            # 處理異常結果
            if isinstance(institutional, Exception):
                logger.error(f"三大法人資料收集失敗: {institutional}")
                institutional = {}
            
            if isinstance(margin, Exception):
                logger.error(f"融資融券資料收集失敗: {margin}")
                margin = {}
            
            if isinstance(trading_summary, Exception):
                logger.error(f"成交資訊收集失敗: {trading_summary}")
                trading_summary = {}
            
            if isinstance(market_stats, Exception):
                logger.error(f"市場統計收集失敗: {market_stats}")
                market_stats = {}
            
            return {
                'date': target_date,
                'institutional_trading': institutional,
                'margin_trading': margin,
                'trading_summary': trading_summary,
                'market_statistics': market_stats,
                'collection_time': datetime.now(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"證交所資料收集失敗 {target_date}: {e}")
            return {
                'date': target_date,
                'success': False,
                'error': str(e)
            }
    
    async def collect_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """收集日期範圍內的資料"""
        results = []
        current_date = start_date
        
        while current_date <= end_date:
            # 跳過週末
            if current_date.weekday() < 5:  # 0-4 是週一到週五
                result = await self.collect_daily_data(current_date)
                results.append(result)
                
                # 避免過於頻繁的請求
                await asyncio.sleep(2)
            
            current_date += timedelta(days=1)
        
        return results
    
    def get_statistics(self) -> Dict:
        """取得收集器統計資訊"""
        return {
            'request_count': self.request_count,
            'last_request_time': self.last_request_time,
            'rate_limit': self.rate_limit,
            'base_url': self.base_url
        }


# 測試函數
async def test_twse_scraper():
    """測試證交所資料收集器"""
    test_date = date.today() - timedelta(days=1)  # 昨天
    
    async with TWSEScraper() as scraper:
        print("=== 測試證交所資料收集器 ===")
        
        # 測試三大法人資料
        print(f"取得三大法人資料: {test_date}")
        institutional = await scraper.get_institutional_trading(test_date)
        print(f"三大法人資料筆數: {len(institutional)}")
        
        # 測試融資融券資料
        print(f"取得融資融券資料: {test_date}")
        margin = await scraper.get_margin_trading(test_date)
        print(f"融資融券資料筆數: {len(margin)}")
        
        # 測試市場統計
        print(f"取得市場統計: {test_date}")
        stats = await scraper.get_market_statistics(test_date)
        print(f"市場統計: {stats}")
        
        # 測試完整資料收集
        print(f"完整資料收集: {test_date}")
        daily_data = await scraper.collect_daily_data(test_date)
        print(f"收集結果: {daily_data['success']}")
        
        # 顯示統計
        collector_stats = scraper.get_statistics()
        print(f"收集器統計: {collector_stats}")


if __name__ == "__main__":
    asyncio.run(test_twse_scraper())