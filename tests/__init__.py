# tests/__init__.py
"""
Test Package for AI Stock Selector
AI選股系統測試套件
"""

# tests/conftest.py
# 測試配置檔案 - 設定測試環境和共用的測試工具

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# 設定測試環境變數
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app
from backend.app.database import db_manager

# 測試客戶端
@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """建立測試用的FastAPI客戶端"""
    with TestClient(app) as test_client:
        yield test_client

# 測試資料庫
@pytest.fixture(scope="session")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """建立測試用的資料庫連線"""
    # 建立測試資料庫
    await db_manager.create_tables()
    
    # 提供資料庫連線
    async with db_manager.get_session() as session:
        yield session
    
    # 清理測試資料庫
    await db_manager.drop_tables()

# 測試資料
@pytest.fixture
def sample_stock_data():
    """提供測試用的股票資料"""
    return {
        "symbol": "2330",
        "name": "台積電",
        "price": 580.0,
        "change": 5.0,
        "volume": 25000000,
        "industry": "半導體"
    }

# tests/test_api.py
# API端點測試檔案

import pytest
from fastapi.testclient import TestClient

def test_read_root(client: TestClient):
    """測試根路徑是否正常回應"""
    response = client.get("/")
    assert response.status_code == 200

def test_health_check(client: TestClient):
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_get_stocks(client: TestClient):
    """測試獲取股票清單API"""
    response = client.get("/api/stocks/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_stock_detail(client: TestClient):
    """測試獲取單一股票詳情API"""
    response = client.get("/api/stocks/2330")
    # 如果股票不存在，應該回傳404或空資料
    assert response.status_code in [200, 404]

def test_search_stocks(client: TestClient):
    """測試股票搜尋API"""
    response = client.get("/api/stocks/search/台積電")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# tests/test_indicators.py
# 技術指標計算測試檔案

import pytest
from backend.app.utils.indicators import TechnicalIndicators

class TestTechnicalIndicators:
    """技術指標計算測試類別"""
    
    def setup_method(self):
        """在每個測試前執行的設定"""
        self.indicators = TechnicalIndicators()
        
        # 準備測試用的價格資料
        self.sample_prices = [
            {"date": "2025-06-01", "close": 570, "high": 575, "low": 565, "volume": 1000000},
            {"date": "2025-06-02", "close": 575, "high": 580, "low": 570, "volume": 1200000},
            {"date": "2025-06-03", "close": 580, "high": 585, "low": 575, "volume": 1100000},
            {"date": "2025-06-04", "close": 585, "high": 590, "low": 580, "volume": 1300000},
            {"date": "2025-06-05", "close": 590, "high": 595, "low": 585, "volume": 1400000},
        ]
    
    def test_calculate_rsi(self):
        """測試RSI計算是否正確"""
        rsi = self.indicators.calculate_rsi(self.sample_prices)
        
        # RSI值應該在0-100之間
        assert 0 <= rsi <= 100
        
        # 上漲趨勢的RSI應該偏高
        assert rsi > 50
    
    def test_calculate_ma(self):
        """測試移動平均線計算"""
        ma5 = self.indicators.calculate_ma(self.sample_prices, period=5)
        
        # 移動平均應該是數字
        assert isinstance(ma5, (int, float))
        
        # 5日均線應該接近最近5天的平均價格
        expected_ma = sum([price["close"] for price in self.sample_prices]) / len(self.sample_prices)
        assert abs(ma5 - expected_ma) < 1  # 允許1元的誤差
    
    def test_calculate_macd(self):
        """測試MACD計算"""
        macd_data = self.indicators.calculate_macd(self.sample_prices)
        
        # MACD應該包含必要的欄位
        assert "macd" in macd_data
        assert "signal" in macd_data
        assert "histogram" in macd_data
        
        # 所有值都應該是數字
        assert isinstance(macd_data["macd"], (int, float))
        assert isinstance(macd_data["signal"], (int, float))
        assert isinstance(macd_data["histogram"], (int, float))

# tests/test_database.py
# 資料庫測試檔案

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import db_manager

@pytest.mark.asyncio
async def test_database_connection(test_db: AsyncSession):
    """測試資料庫連線是否正常"""
    # 嘗試執行簡單查詢
    result = await test_db.execute("SELECT 1")
    assert result.scalar() == 1

@pytest.mark.asyncio
async def test_create_stock(test_db: AsyncSession, sample_stock_data):
    """測試建立股票資料"""
    # 這裡會測試資料庫的CRUD操作
    # 實際實作需要配合資料庫模型
    pass

@pytest.mark.asyncio
async def test_get_stocks(test_db: AsyncSession):
    """測試獲取股票清單"""
    # 測試從資料庫獲取股票清單
    stocks = await db_manager.get_stocks()
    assert isinstance(stocks, list)

# tests/test_scrapers.py
# 資料收集器測試檔案

import pytest
from unittest.mock import Mock, patch
from data_collector.scrapers.yahoo_finance import YahooFinanceScraper
from data_collector.scrapers.twse_scraper import TWSEScraper

class TestYahooFinanceScraper:
    """Yahoo Finance爬蟲測試"""
    
    def setup_method(self):
        self.scraper = YahooFinanceScraper()
    
    @patch('requests.get')
    def test_get_stock_data(self, mock_get):
        """測試獲取股票資料"""
        # 模擬API回應
        mock_response = Mock()
        mock_response.json.return_value = {
            "chart": {
                "result": [{
                    "meta": {"regularMarketPrice": 580.0},
                    "timestamp": [1640995200],
                    "indicators": {
                        "quote": [{
                            "close": [580.0],
                            "high": [585.0],
                            "low": [575.0],
                            "volume": [25000000]
                        }]
                    }
                }]
            }
        }
        mock_get.return_value = mock_response
        
        # 執行測試
        data = self.scraper.get_stock_data("2330")
        
        # 驗證結果
        assert data is not None
        assert "price" in data
        assert data["price"] == 580.0

class TestTWSEScraper:
    """證交所爬蟲測試"""
    
    def setup_method(self):
        self.scraper = TWSEScraper()
    
    def test_health_check(self):
        """測試爬蟲健康檢查"""
        result = self.scraper.health_check()
        assert isinstance(result, bool)