# backend/app/api/analysis.py
"""
技術分析相關API路由
提供技術指標計算、圖表數據等功能
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db, redis_manager
from app.models.stock import Stock, DailyPrice, TechnicalIndicator
from app.utils.logging import get_logger, log_api_call
from app.utils.indicators import TechnicalIndicators, prepare_stock_data_for_indicators
import json

router = APIRouter()
logger = get_logger(__name__)

@router.get("/{symbol}/technical")
@log_api_call
async def get_technical_analysis(
    symbol: str,
    period: str = Query("1mo", description="時間範圍 (1w/1mo/3mo/6mo/1y)"),
    indicators: Optional[str] = Query(None, description="指標類型，逗號分隔"),
    db: Session = Depends(get_db)
):
    """
    取得股票技術分析
    """
    try:
        # 建立快取鍵
        cache_key = f"technical_analysis:{symbol}:{period}:{indicators}"
        
        # 嘗試從快取取得
        cached_data = redis_manager.get(cache_key)
        if cached_data:
            logger.info(f"從快取取得技術分析 {symbol}")
            return json.loads(cached_data)
        
        # 檢查股票是否存在
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票代碼不存在")
        
        # 計算日期範圍
        end_date = date.today()
        if period == "1w":
            start_date = end_date - timedelta(days=7)
        elif period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # 取得價格資料
        price_records = (
            db.query(DailyPrice)
            .filter(
                DailyPrice.stock_id == stock.id,
                DailyPrice.trade_date >= start_date,
                DailyPrice.trade_date <= end_date
            )
            .order_by(DailyPrice.trade_date)
            .all()
        )
        
        if not price_records:
            raise HTTPException(status_code=404, detail="無價格資料")
        
        # 準備資料並計算指標
        stock_data = prepare_stock_data_for_indicators(price_records)
        calculator = TechnicalIndicators()
        
        # 計算所有指標
        all_indicators = calculator.calculate_all_indicators(stock_data)
        
        # 取得最新信號
        signals = calculator.get_latest_signals(all_indicators)
        
        result = {
            "symbol": symbol,
            "name": stock.name,
            "period": period,
            "data_points": len(price_records),
            "latest_price": float(price_records[-1].close_price),
            "indicators": all_indicators,
            "signals": signals,
            "updated_at": datetime.now()
        }
        
        # 儲存到快取（10分鐘）
        redis_manager.set(cache_key, json.dumps(result, default=str), ttl=600)
        
        logger.info(f"技術分析完成: {symbol}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"技術分析失敗 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="技術分析失敗")


@router.get("/{symbol}/signals")
@log_api_call
async def get_trading_signals(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    取得股票交易信號
    """
    try:
        # 檢查股票是否存在
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票代碼不存在")
        
        # 取得最新技術指標
        latest_indicator = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.stock_id == stock.id)
            .order_by(TechnicalIndicator.trade_date.desc())
            .first()
        )
        
        if not latest_indicator:
            raise HTTPException(status_code=404, detail="無技術指標資料")
        
        # 分析交易信號
        signals = {
            "symbol": symbol,
            "name": stock.name,
            "trade_date": latest_indicator.trade_date,
            "buy_signals": [],
            "sell_signals": [],
            "hold_signals": []
        }
        
        # RSI 信號
        if latest_indicator.rsi_14:
            if latest_indicator.rsi_14 < 30:
                signals["buy_signals"].append({
                    "indicator": "RSI",
                    "value": float(latest_indicator.rsi_14),
                    "signal": "超賣區",
                    "strength": "strong"
                })
            elif latest_indicator.rsi_14 > 70:
                signals["sell_signals"].append({
                    "indicator": "RSI",
                    "value": float(latest_indicator.rsi_14),
                    "signal": "超買區",
                    "strength": "strong"
                })
        
        # MACD 信號
        if latest_indicator.macd and latest_indicator.macd_signal:
            if latest_indicator.macd > latest_indicator.macd_signal:
                signals["buy_signals"].append({
                    "indicator": "MACD",
                    "signal": "黃金交叉",
                    "strength": "medium"
                })
            else:
                signals["sell_signals"].append({
                    "indicator": "MACD",
                    "signal": "死亡交叉",
                    "strength": "medium"
                })
        
        # KD 信號
        if latest_indicator.k_value and latest_indicator.d_value:
            if latest_indicator.k_value < 20 and latest_indicator.d_value < 20:
                signals["buy_signals"].append({
                    "indicator": "KD",
                    "k": float(latest_indicator.k_value),
                    "d": float(latest_indicator.d_value),
                    "signal": "超賣區",
                    "strength": "strong"
                })
            elif latest_indicator.k_value > 80 and latest_indicator.d_value > 80:
                signals["sell_signals"].append({
                    "indicator": "KD",
                    "k": float(latest_indicator.k_value),
                    "d": float(latest_indicator.d_value),
                    "signal": "超買區",
                    "strength": "strong"
                })
        
        # 計算綜合建議
        buy_count = len(signals["buy_signals"])
        sell_count = len(signals["sell_signals"])
        
        if buy_count > sell_count:
            signals["recommendation"] = "買進"
            signals["confidence"] = (buy_count / (buy_count + sell_count)) * 100
        elif sell_count > buy_count:
            signals["recommendation"] = "賣出"
            signals["confidence"] = (sell_count / (buy_count + sell_count)) * 100
        else:
            signals["recommendation"] = "觀望"
            signals["confidence"] = 50
        
        return signals
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得交易信號失敗 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得交易信號失敗")


@router.get("/{symbol}/support-resistance")
@log_api_call
async def get_support_resistance(
    symbol: str,
    period: int = Query(20, description="計算期間"),
    db: Session = Depends(get_db)
):
    """
    取得支撐壓力位
    """
    try:
        # 檢查股票是否存在
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail="股票代碼不存在")
        
        # 取得最新技術指標
        latest_indicator = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.stock_id == stock.id)
            .order_by(TechnicalIndicator.trade_date.desc())
            .first()
        )
        
        if not latest_indicator:
            raise HTTPException(status_code=404, detail="無技術指標資料")
        
        # 取得最新價格
        latest_price = (
            db.query(DailyPrice)
            .filter(DailyPrice.stock_id == stock.id)
            .order_by(DailyPrice.trade_date.desc())
            .first()
        )
        
        result = {
            "symbol": symbol,
            "name": stock.name,
            "current_price": float(latest_price.close_price) if latest_price else None,
            "support_levels": [],
            "resistance_levels": []
        }
        
        # 主要支撐位
        if latest_indicator.support_level:
            result["support_levels"].append({
                "level": float(latest_indicator.support_level),
                "type": "技術支撐",
                "strength": "strong"
            })
        
        # 移動平均線支撐
        if latest_indicator.ma_20:
            result["support_levels"].append({
                "level": float(latest_indicator.ma_20),
                "type": "MA20",
                "strength": "medium"
            })
        
        if latest_indicator.ma_60:
            result["support_levels"].append({
                "level": float(latest_indicator.ma_60),
                "type": "MA60",
                "strength": "strong"
            })
        
        # 主要壓力位
        if latest_indicator.resistance_level:
            result["resistance_levels"].append({
                "level": float(latest_indicator.resistance_level),
                "type": "技術壓力",
                "strength": "strong"
            })
        
        # 布林帶壓力
        if latest_indicator.bb_upper:
            result["resistance_levels"].append({
                "level": float(latest_indicator.bb_upper),
                "type": "布林上軌",
                "strength": "medium"
            })
        
        # 排序
        result["support_levels"].sort(key=lambda x: x["level"], reverse=True)
        result["resistance_levels"].sort(key=lambda x: x["level"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得支撐壓力位失敗 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得支撐壓力位失敗")