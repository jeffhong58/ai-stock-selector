"""
股票相關API端點
提供股票基本資料、價格查詢等功能
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.database import get_db, redis_manager
from app.models.stock import Stock, DailyPrice, TechnicalIndicator
from app.schemas.stock import (
    StockInfo, StockPrice, StockSearch,
    StockListResponse, StockDetailResponse
)
from app.services.data_collector import YahooFinanceScraper

router = APIRouter()


@router.get("/", response_model=StockListResponse)
async def get_stocks(
    market: Optional[str] = Query(None, description="市場類型 (TSE/OTC)"),
    industry: Optional[str] = Query(None, description="產業代碼"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """取得股票清單"""
    try:
        # 建立查詢
        query = db.query(Stock).filter(Stock.is_active == True)
        
        # 篩選條件
        if market:
            query = query.filter(Stock.market == market.upper())
        if industry:
            query = query.filter(Stock.industry == industry)
        
        # 總數量
        total = query.count()
        
        # 分頁查詢
        stocks = query.offset(offset).limit(limit).all()
        
        return StockListResponse(
            stocks=[StockInfo.from_orm(stock) for stock in stocks],
            total=total,
            page=offset // limit + 1,
            page_size=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢股票清單失敗: {str(e)}")


@router.get("/{symbol}", response_model=StockDetailResponse)
async def get_stock_detail(
    symbol: str,
    include_history: bool = Query(True, description="是否包含歷史價格"),
    days: int = Query(30, ge=1, le=365, description="歷史資料天數"),
    db: Session = Depends(get_db)
):
    """取得股票詳細資訊"""
    try:
        # 檢查快取
        cache_key = f"stock_detail:{symbol}:{days}"
        cached_data = redis_manager.get(cache_key)
        if cached_data:
            import json
            return json.loads(cached_data)
        
        # 查詢股票基本資料
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票代碼不存在")
        
        result = StockDetailResponse(
            stock=StockInfo.from_orm(stock),
            history=[],
            technical_indicators=None,
            last_updated=datetime.now()
        )
        
        # 查詢歷史價格
        if include_history:
            start_date = date.today() - timedelta(days=days)
            
            history_query = (
                db.query(DailyPrice)
                .filter(
                    and_(
                        DailyPrice.stock_id == stock.id,
                        DailyPrice.trade_date >= start_date
                    )
                )
                .order_by(desc(DailyPrice.trade_date))
                .limit(days)
            )
            
            history = history_query.all()
            result.history = [StockPrice.from_orm(price) for price in history]
            
            # 查詢最新技術指標
            latest_indicator = (
                db.query(TechnicalIndicator)
                .filter(TechnicalIndicator.stock_id == stock.id)
                .order_by(desc(TechnicalIndicator.trade_date))
                .first()
            )
            
            if latest_indicator:
                result.technical_indicators = {
                    "rsi_14": latest_indicator.rsi_14,
                    "macd": latest_indicator.macd,
                    "ma_20": latest_indicator.ma_20,
                    "ma_60": latest_indicator.ma_60,
                    "bb_upper": latest_indicator.bb_upper,
                    "bb_lower": latest_indicator.bb_lower,
                    "support_level": latest_indicator.support_level,
                    "resistance_level": latest_indicator.resistance_level,
                    "trade_date": latest_indicator.trade_date
                }
        
        # 快取結果
        import json
        redis_manager.set(
            cache_key, 
            json.dumps(result.dict(), default=str), 
            ttl=300  # 5分鐘快取
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢股票詳情失敗: {str(e)}")


@router.get("/{symbol}/price")
async def get_stock_price(
    symbol: str,
    period: str = Query("1mo", description="時間範圍 (1d/1w/1mo/3mo/1y)"),
    db: Session = Depends(get_db)
):
    """取得股票價格資料"""
    try:
        # 檢查股票是否存在
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票代碼不存在")
        
        # 計算日期範圍
        end_date = date.today()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "1w":
            start_date = end_date - timedelta(days=7)
        elif period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # 查詢價格資料
        prices = (
            db.query(DailyPrice)
            .filter(
                and_(
                    DailyPrice.stock_id == stock.id,
                    DailyPrice.trade_date >= start_date,
                    DailyPrice.trade_date <= end_date
                )
            )
            .order_by(DailyPrice.trade_date)
            .all()
        )
        
        return {
            "symbol": symbol,
            "period": period,
            "data": [StockPrice.from_orm(price) for price in prices],
            "count": len(prices)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢價格資料失敗: {str(e)}")


@router.get("/{symbol}/realtime")
async def get_realtime_quote(symbol: str):
    """取得即時報價"""
    try:
        # 檢查快取
        cache_key = f"realtime:{symbol}"
        cached_quote = redis_manager.get(cache_key)
        if cached_quote:
            import json
            return json.loads(cached_quote)
        
        # 使用Yahoo Finance API取得即時報價
        async with YahooFinanceScraper() as scraper:
            quote = await scraper.get_realtime_quote(symbol)
            
            if not quote:
                raise HTTPException(status_code=404, detail="無法取得即時報價")
            
            # 快取1分鐘
            import json
            redis_manager.set(
                cache_key,
                json.dumps(quote, default=str),
                ttl=60
            )
            
            return quote
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得即時報價失敗: {str(e)}")


@router.get("/search/{query}")
async def search_stocks(
    query: str,
    limit: int = Query(10, ge=1, le=50, description="限制數量"),
    db: Session = Depends(get_db)
):
    """搜尋股票"""
    try:
        # 檢查是否為股票代碼
        if query.isdigit():
            # 精確匹配股票代碼
            stocks = (
                db.query(Stock)
                .filter(
                    and_(
                        Stock.symbol.like(f"%{query}%"),
                        Stock.is_active == True
                    )
                )
                .limit(limit)
                .all()
            )
        else:
            # 模糊搜尋股票名稱
            stocks = (
                db.query(Stock)
                .filter(
                    and_(
                        Stock.name.contains(query),
                        Stock.is_active == True
                    )
                )
                .limit(limit)
                .all()
            )
        
        return {
            "query": query,
            "results": [
                StockSearch(
                    symbol=stock.symbol,
                    name=stock.name,
                    market=stock.market,
                    industry=stock.industry
                ) for stock in stocks
            ],
            "count": len(stocks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜尋股票失敗: {str(e)}")


@router.get("/{symbol}/indicators")
async def get_technical_indicators(
    symbol: str,
    days: int = Query(30, ge=1, le=90, description="查詢天數"),
    db: Session = Depends(get_db)
):
    """取得技術指標"""
    try:
        # 檢查股票是否存在
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票代碼不存在")
        
        # 查詢技術指標
        start_date = date.today() - timedelta(days=days)
        
        indicators = (
            db.query(TechnicalIndicator)
            .filter(
                and_(
                    TechnicalIndicator.stock_id == stock.id,
                    TechnicalIndicator.trade_date >= start_date
                )
            )
            .order_by(desc(TechnicalIndicator.trade_date))
            .all()
        )
        
        return {
            "symbol": symbol,
            "indicators": [
                {
                    "trade_date": indicator.trade_date,
                    "rsi_14": indicator.rsi_14,
                    "macd": indicator.macd,
                    "macd_signal": indicator.macd_signal,
                    "macd_histogram": indicator.macd_histogram,
                    "ma_5": indicator.ma_5,
                    "ma_20": indicator.ma_20,
                    "ma_60": indicator.ma_60,
                    "bb_upper": indicator.bb_upper,
                    "bb_middle": indicator.bb_middle,
                    "bb_lower": indicator.bb_lower,
                    "k_value": indicator.k_value,
                    "d_value": indicator.d_value,
                    "support_level": indicator.support_level,
                    "resistance_level": indicator.resistance_level
                } for indicator in indicators
            ],
            "count": len(indicators)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢技術指標失敗: {str(e)}")


@router.post("/{symbol}/refresh")
async def refresh_stock_data(symbol: str):
    """手動更新股票資料"""
    try:
        # 使用Yahoo Finance更新資料
        async with YahooFinanceScraper() as scraper:
            # 取得股票基本資訊
            info = await scraper.get_stock_info(symbol)
            # 取得歷史資料
            history = await scraper.get_historical_data(symbol, "1w")
            
            if not info and not history:
                raise HTTPException(status_code=404, detail="無法取得股票資料")
            
            # 清除相關快取
            cache_keys = [
                f"stock_detail:{symbol}:*",
                f"realtime:{symbol}"
            ]
            for key in cache_keys:
                redis_manager.delete(key)
            
            return {
                "symbol": symbol,
                "message": "股票資料更新成功",
                "info_updated": info is not None,
                "history_updated": history is not None,
                "updated_at": datetime.now()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新股票資料失敗: {str(e)}")