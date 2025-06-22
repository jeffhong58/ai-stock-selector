# backend/app/api/recommendations.py
"""
AI推薦相關API路由
提供智能選股、產業輪動、投資建議等功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db, get_redis
from app.utils.logging import get_logger, log_api_call
import json
import redis

router = APIRouter()
logger = get_logger(__name__)

# Pydantic模型
from pydantic import BaseModel

class StockRecommendation(BaseModel):
    """股票推薦"""
    symbol: str
    name: str
    recommendation_type: str  # buy, sell, hold
    confidence_score: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    investment_period: str  # short, medium, long
    reasons: List[str]
    risk_level: str  # low, medium, high
    ai_score: float
    created_at: datetime

class SectorRotation(BaseModel):
    """產業輪動分析"""
    sector: str
    sector_name: str
    momentum_score: float
    fund_flow_score: float
    technical_score: float
    overall_score: float
    trend: str  # rising, falling, stable
    recommended_stocks: List[str]
    analysis_date: datetime

class InvestmentStrategy(BaseModel):
    """投資策略"""
    strategy_name: str
    description: str
    time_horizon: str
    risk_level: str
    expected_return: float
    max_drawdown: float
    recommended_allocation: Dict[str, float]
    stocks: List[StockRecommendation]

class AIInsight(BaseModel):
    """AI洞察分析"""
    insight_type: str
    title: str
    description: str
    confidence: float
    impact_level: str  # high, medium, low
    related_stocks: List[str]
    created_at: datetime


@router.get("/stocks", response_model=List[StockRecommendation])
@log_api_call
async def get_stock_recommendations(
    recommendation_type: Optional[str] = Query(None, description="推薦類型 (buy/sell/hold)"),
    investment_period: Optional[str] = Query(None, description="投資期間 (short/medium/long)"),
    risk_level: Optional[str] = Query(None, description="風險等級 (low/medium/high)"),
    limit: int = Query(20, ge=1, le=100, description="回傳筆數"),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0, description="最低信心分數"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    取得AI股票推薦清單
    """
    try:
        # 建立快取鍵
        cache_key = f"recommendations:{recommendation_type}:{investment_period}:{risk_level}:{limit}:{min_confidence}"
        
        # 嘗試從快取取得
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"從快取取得股票推薦")
                return json.loads(cached_data)
        
        # 模擬AI推薦資料（實際應用中應該從資料庫或AI模型取得）
        from app.models.stock import Stock
        
        # 取得股票清單
        query = db.query(Stock)
        
        if recommendation_type == "buy":
            # 篩選適合買入的股票
            stocks = query.limit(limit * 2).all()  # 取多一些進行篩選
        else:
            stocks = query.limit(limit).all()
        
        # 模擬AI分析結果
        recommendations = []
        for stock in stocks[:limit]:
            # 這裡應該是實際的AI推薦邏輯
            confidence = _calculate_ai_confidence(stock.symbol, db)
            
            if confidence >= min_confidence:
                recommendation = StockRecommendation(
                    symbol=stock.symbol,
                    name=stock.name,
                    recommendation_type=recommendation_type or "buy",
                    confidence_score=confidence,
                    target_price=_calculate_target_price(stock.symbol, db),
                    stop_loss=_calculate_stop_loss(stock.symbol, db),
                    investment_period=investment_period or "medium",
                    reasons=_generate_recommendation_reasons(stock.symbol, db),
                    risk_level=_assess_risk_level(stock.symbol, db),
                    ai_score=confidence * 100,
                    created_at=datetime.now()
                )
                recommendations.append(recommendation)
        
        # 按信心分數排序
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # 儲存到快取（1小時）
        if redis_client:
            redis_client.setex(cache_key, 3600, json.dumps([r.dict() for r in recommendations], default=str))
        
        logger.info(f"取得股票推薦: {len(recommendations)} 筆")
        return recommendations
        
    except Exception as e:
        logger.error(f"取得股票推薦失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得股票推薦失敗")


@router.get("/sectors", response_model=List[SectorRotation])
@log_api_call
async def get_sector_rotation(
    date: Optional[str] = Query(None, description="分析日期 (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=20, description="回傳筆數"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    取得產業輪動分析
    """
    try:
        # 處理日期參數
        if not date:
            target_date = datetime.now().date()
        else:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # 建立快取鍵
        cache_key = f"sector_rotation:{target_date}:{limit}"
        
        # 嘗試從快取取得
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"從快取取得產業輪動分析")
                return json.loads(cached_data)
        
        # 取得產業清單
        from app.models.stock import Stock
        
        sectors = db.query(Stock.industry).distinct().all()
        sector_analysis = []
        
        for sector_tuple in sectors[:limit]:
            sector = sector_tuple[0]
            if sector:
                analysis = _analyze_sector_performance(sector, target_date, db)
                sector_analysis.append(analysis)
        
        # 按總分排序
        sector_analysis.sort(key=lambda x: x.overall_score, reverse=True)
        
        # 儲存到快取（2小時）
        if redis_client:
            redis_client.setex(cache_key, 7200, json.dumps([r.dict() for r in sector_analysis], default=str))
        
        logger.info(f"取得產業輪動分析: {len(sector_analysis)} 筆")
        return sector_analysis
        
    except Exception as e:
        logger.error(f"取得產業輪動分析失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得產業輪動分析失敗")


@router.get("/strategies", response_model=List[InvestmentStrategy])
@log_api_call
async def get_investment_strategies(
    risk_tolerance: Optional[str] = Query(None, description="風險承受度 (conservative/moderate/aggressive)"),
    time_horizon: Optional[str] = Query(None, description="投資期間 (short/medium/long)"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    取得投資策略建議
    """
    try:
        # 建立快取鍵
        cache_key = f"strategies:{risk_tolerance}:{time_horizon}"
        
        # 嘗試從快取取得
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"從快取取得投資策略")
                return json.loads(cached_data)
        
        strategies = []
        
        # 生成不同的投資策略
        if not risk_tolerance or risk_tolerance == "conservative":
            strategy = _generate_conservative_strategy(db)
            strategies.append(strategy)
        
        if not risk_tolerance or risk_tolerance == "moderate":
            strategy = _generate_moderate_strategy(db)
            strategies.append(strategy)
        
        if not risk_tolerance or risk_tolerance == "aggressive":
            strategy = _generate_aggressive_strategy(db)
            strategies.append(strategy)
        
        # 儲存到快取（4小時）
        if redis_client:
            redis_client.setex(cache_key, 14400, json.dumps([s.dict() for s in strategies], default=str))
        
        logger.info(f"取得投資策略: {len(strategies)} 個")
        return strategies
        
    except Exception as e:
        logger.error(f"取得投資策略失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得投資策略失敗")


@router.get("/insights", response_model=List[AIInsight])
@log_api_call
async def get_ai_insights(
    insight_type: Optional[str] = Query(None, description="洞察類型"),
    limit: int = Query(10, ge=1, le=50, description="回傳筆數"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    取得AI市場洞察
    """
    try:
        # 建立快取鍵
        cache_key = f"insights:{insight_type}:{limit}"
        
        # 嘗試從快取取得
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"從快取取得AI洞察")
                return json.loads(cached_data)
        
        # 生成AI洞察
        insights = _generate_ai_insights(limit, db)
        
        # 儲存到快取（30分鐘）
        if redis_client:
            redis_client.setex(cache_key, 1800, json.dumps([i.dict() for i in insights], default=str))
        
        logger.info(f"取得AI洞察: {len(insights)} 筆")
        return insights
        
    except Exception as e:
        logger.error(f"取得AI洞察失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得AI洞察失敗")


# 輔助函數
def _calculate_ai_confidence(symbol: str, db: Session) -> float:
    """計算AI信心分數"""
    # 這裡應該是實際的AI模型計算
    # 暫時使用模擬資料
    import random
    return round(random.uniform(0.5, 0.95), 2)


def _calculate_target_price(symbol: str, db: Session) -> Optional[float]:
    """計算目標價"""
    from app.models.stock import DailyPrice
    
    latest_price = db.query(DailyPrice).filter(
        DailyPrice.symbol == symbol
    ).order_by(DailyPrice.trade_date.desc()).first()
    
    if latest_price:
        # 簡單的目標價計算（實際應該使用複雜的AI模型）
        return round(latest_price.close_price * 1.15, 2)
    return None


def _calculate_stop_loss(symbol: str, db: Session) -> Optional[float]:
    """計算停損價"""
    from app.models.stock import DailyPrice
    
    latest_price = db.query(DailyPrice).filter(
        DailyPrice.symbol == symbol
    ).order_by(DailyPrice.trade_date.desc()).first()
    
    if latest_price:
        # 簡單的停損價計算
        return round(latest_price.close_price * 0.9, 2)
    return None


def _generate_recommendation_reasons(symbol: str, db: Session) -> List[str]:
    """生成推薦理由"""
    reasons = [
        "技術指標呈現多頭排列",
        "基本面表現優異",
        "產業前景看好",
        "法人持續買超",
        "營收成長穩定",
        "AI模型預測上漲機率高"
    ]
    
    import random
    return random.sample(reasons, 3)


def _assess_risk_level(symbol: str, db: Session) -> str:
    """評估風險等級"""
    import random
    return random.choice(["low", "medium", "high"])


def _analyze_sector_performance(sector: str, date: datetime, db: Session) -> SectorRotation:
    """分析產業表現"""
    import random
    
    # 模擬產業分析（實際應該使用複雜的計算）
    momentum_score = round(random.uniform(0, 100), 1)
    fund_flow_score = round(random.uniform(0, 100), 1)
    technical_score = round(random.uniform(0, 100), 1)
    overall_score = round((momentum_score + fund_flow_score + technical_score) / 3, 1)
    
    # 取得該產業的股票
    from app.models.stock import Stock
    stocks = db.query(Stock.symbol).filter(Stock.industry == sector).limit(5).all()
    recommended_stocks = [s[0] for s in stocks]
    
    trend = "rising" if overall_score > 60 else "falling" if overall_score < 40 else "stable"
    
    return SectorRotation(
        sector=sector,
        sector_name=sector,
        momentum_score=momentum_score,
        fund_flow_score=fund_flow_score,
        technical_score=technical_score,
        overall_score=overall_score,
        trend=trend,
        recommended_stocks=recommended_stocks,
        analysis_date=date
    )


def _generate_conservative_strategy(db: Session) -> InvestmentStrategy:
    """生成保守型投資策略"""
    # 取得一些穩健的股票推薦
    recommendations = []
    
    return InvestmentStrategy(
        strategy_name="穩健成長策略",
        description="適合風險承受度較低的投資者，著重於穩定成長的優質股票",
        time_horizon="long",
        risk_level="low",
        expected_return=8.0,
        max_drawdown=15.0,
        recommended_allocation={
            "大型權值股": 60.0,
            "高股息股": 25.0,
            "債券ETF": 15.0
        },
        stocks=recommendations
    )


def _generate_moderate_strategy(db: Session) -> InvestmentStrategy:
    """生成穩健型投資策略"""
    return InvestmentStrategy(
        strategy_name="均衡成長策略",
        description="平衡風險與報酬，適合中等風險承受度的投資者",
        time_horizon="medium",
        risk_level="medium",
        expected_return=12.0,
        max_drawdown=25.0,
        recommended_allocation={
            "成長股": 40.0,
            "價值股": 30.0,
            "科技股": 20.0,
            "現金": 10.0
        },
        stocks=[]
    )


def _generate_aggressive_strategy(db: Session) -> InvestmentStrategy:
    """生成積極型投資策略"""
    return InvestmentStrategy(
        strategy_name="積極成長策略",
        description="追求高報酬，適合高風險承受度的投資者",
        time_horizon="short",
        risk_level="high",
        expected_return=20.0,
        max_drawdown=40.0,
        recommended_allocation={
            "成長股": 50.0,
            "小型股": 30.0,
            "新興產業": 20.0
        },
        stocks=[]
    )


def _generate_ai_insights(limit: int, db: Session) -> List[AIInsight]:
    """生成AI洞察"""
    insights = [
        AIInsight(
            insight_type="market_trend",
            title="AI偵測到半導體產業轉強訊號",
            description="基於資金流向和技術指標分析，半導體產業可能即將迎來反彈",
            confidence=0.78,
            impact_level="high",
            related_stocks=["2330", "2454", "3008"],
            created_at=datetime.now()
        ),
        AIInsight(
            insight_type="sector_rotation",
            title="金融股表現相對強勢",
            description="法人資金持續流入金融股，建議關注相關投資機會",
            confidence=0.65,
            impact_level="medium",
            related_stocks=["2891", "2892", "2884"],
            created_at=datetime.now()
        )
    ]
    
    return insights[:limit]