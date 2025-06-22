# backend/app/schemas/stock.py
"""
股票相關的Pydantic模型
用於API請求和回應的資料驗證
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class StockBase(BaseModel):
    """股票基本資訊"""
    symbol: str = Field(..., description="股票代號")
    name: str = Field(..., description="股票名稱")
    market: str = Field(..., description="市場別")
    industry: Optional[str] = Field(None, description="產業別")


class StockInfo(StockBase):
    """股票詳細資訊"""
    id: int
    listing_date: Optional[date]
    capital: Optional[int]
    shares_outstanding: Optional[int]
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    dividend_yield: Optional[float]
    is_active: bool
    
    class Config:
        orm_mode = True


class StockPrice(BaseModel):
    """股票價格資料"""
    trade_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    turnover: Optional[int]
    price_change: Optional[float]
    price_change_pct: Optional[float]
    
    class Config:
        orm_mode = True


class StockSearch(BaseModel):
    """股票搜尋結果"""
    symbol: str
    name: str
    market: str
    industry: Optional[str]


class StockListResponse(BaseModel):
    """股票清單回應"""
    stocks: List[StockInfo]
    total: int
    page: int
    page_size: int


class StockDetailResponse(BaseModel):
    """股票詳情回應"""
    stock: StockInfo
    history: List[StockPrice]
    technical_indicators: Optional[Dict[str, Any]]
    last_updated: datetime


class RealtimeQuote(BaseModel):
    """即時報價"""
    symbol: str
    current_price: float
    previous_close: float
    change: float
    change_percent: float
    volume: int
    high: float
    low: float
    open: float
    market_time: Optional[datetime]
    updated_at: datetime