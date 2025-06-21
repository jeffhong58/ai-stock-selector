# backend/app/models/stock.py
"""
股票相關資料庫模型
SQLAlchemy ORM 模型定義
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Decimal, BigInteger, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date

from app.database import Base


class Stock(Base):
    """股票基本資料表"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    market = Column(String(20), nullable=False)  # TSE, OTC
    industry = Column(String(50), index=True)
    sector = Column(String(50), index=True)
    listing_date = Column(Date)
    capital = Column(BigInteger)
    shares_outstanding = Column(BigInteger)
    par_value = Column(Decimal(10, 2))
    
    # 基本面資料
    market_cap = Column(BigInteger)
    pe_ratio = Column(Decimal(10, 2))
    pb_ratio = Column(Decimal(10, 2))
    dividend_yield = Column(Decimal(5, 2))
    
    # TEJ擴展欄位
    tej_industry_code = Column(String(20))
    tej_financial_data = Column(JSON)
    tej_ratings = Column(JSON)
    
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 關聯
    daily_prices = relationship("DailyPrice", back_populates="stock", cascade="all, delete-orphan")
    technical_indicators = relationship("TechnicalIndicator", back_populates="stock", cascade="all, delete-orphan")
    institutional_trading = relationship("InstitutionalTrading", back_populates="stock", cascade="all, delete-orphan")
    margin_trading = relationship("MarginTrading", back_populates="stock", cascade="all, delete-orphan")
    financial_statements = relationship("FinancialStatement", back_populates="stock", cascade="all, delete-orphan")
    ai_recommendations = relationship("AIRecommendation", back_populates="stock", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock(symbol={self.symbol}, name={self.name})>"


class DailyPrice(Base):
    """日線價格資料表"""
    __tablename__ = "daily_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    
    # OHLCV資料
    open_price = Column(Decimal(10, 2), nullable=False)
    high_price = Column(Decimal(10, 2), nullable=False)
    low_price = Column(Decimal(10, 2), nullable=False)
    close_price = Column(Decimal(10, 2), nullable=False)
    adj_close = Column(Decimal(10, 2))
    volume = Column(BigInteger, nullable=False)
    turnover = Column(BigInteger)
    
    # 計算欄位
    price_change = Column(Decimal(10, 2))
    price_change_pct = Column(Decimal(5, 2))
    
    # TEJ擴展欄位
    tej_adjusted_price = Column(Decimal(10, 2))
    tej_volume_data = Column(JSON)
    
    created_at = Column(DateTime, default=func.now())
    
    # 關聯
    stock = relationship("Stock", back_populates="daily_prices")
    
    # 複合索引
    __table_args__ = (
        {"schema": None}  # 可以指定schema
    )
    
    def __repr__(self):
        return f"<DailyPrice(symbol={self.symbol}, date={self.trade_date}, close={self.close_price})>"


class TechnicalIndicator(Base):
    """技術指標資料表"""
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    
    # 移動平均線
    ma_5 = Column(Decimal(10, 2))
    ma_10 = Column(Decimal(10, 2))
    ma_20 = Column(Decimal(10, 2))
    ma_60 = Column(Decimal(10, 2))
    ma_120 = Column(Decimal(10, 2))
    ma_240 = Column(Decimal(10, 2))
    
    # 指數移動平均線
    ema_12 = Column(Decimal(10, 2))
    ema_26 = Column(Decimal(10, 2))
    
    # 技術指標
    rsi_14 = Column(Decimal(5, 2))
    macd = Column(Decimal(10, 4))
    macd_signal = Column(Decimal(10, 4))
    macd_histogram = Column(Decimal(10, 4))
    
    # KD指標
    k_value = Column(Decimal(5, 2))
    d_value = Column(Decimal(5, 2))
    
    # 布林帶
    bb_upper = Column(Decimal(10, 2))
    bb_middle = Column(Decimal(10, 2))
    bb_lower = Column(Decimal(10, 2))
    
    # 成交量指標
    volume_ma_5 = Column(BigInteger)
    volume_ma_20 = Column(BigInteger)
    
    # 支撐壓力位
    support_level = Column(Decimal(10, 2))
    resistance_level = Column(Decimal(10, 2))
    
    created_at = Column(DateTime, default=func.now())
    
    # 關聯
    stock = relationship("Stock", back_populates="technical_indicators")
    
    def __repr__(self):
        return f"<TechnicalIndicator(symbol={self.symbol}, date={self.trade_date})>"


class InstitutionalTrading(Base):
    """三大法人買賣資料表"""
    __tablename__ = "institutional_trading"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    
    # 外資
    foreign_buy = Column(BigInteger, default=0)
    foreign_sell = Column(BigInteger, default=0)
    foreign_net = Column(BigInteger, default=0)
    
    # 投信
    trust_buy = Column(BigInteger, default=0)
    trust_sell = Column(BigInteger, default=0)
    trust_net = Column(BigInteger, default=0)
    
    # 自營商
    dealer_buy = Column(BigInteger, default=0)
    dealer_sell = Column(BigInteger, default=0)
    dealer_net = Column(BigInteger, default=0)
    
    # 總計
    total_net = Column(BigInteger, default=0)
    
    # TEJ擴展欄位
    tej_qfii_data = Column(JSON)
    tej_dealer_detail = Column(JSON)
    
    created_at = Column(DateTime, default=func.now())
    
    # 關聯
    stock = relationship("Stock", back_populates="institutional_trading")
    
    def __repr__(self):
        return f"<InstitutionalTrading(symbol={self.symbol}, date={self.trade_date})>"


class MarginTrading(Base):
    """融資融券資料表"""
    __tablename__ = "margin_trading"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    
    # 融資
    margin_buy = Column(BigInteger, default=0)
    margin_sell = Column(BigInteger, default=0)
    margin_balance = Column(BigInteger, default=0)
    margin_quota = Column(BigInteger, default=0)
    
    # 融券
    short_sell = Column(BigInteger, default=0)
    short_cover = Column(BigInteger, default=0)
    short_balance = Column(BigInteger, default=0)
    short_quota = Column(BigInteger, default=0)
    
    # 券資比
    short_margin_ratio = Column(Decimal(5, 2))
    
    created_at = Column(DateTime, default=func.now())
    
    # 關聯
    stock = relationship("Stock", back_populates="margin_trading")
    
    def __repr__(self):
        return f"<MarginTrading(symbol={self.symbol}, date={self.trade_date})>"


class FinancialStatement(Base):
    """財務報表資料表"""
    __tablename__ = "financial_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    report_type = Column(String(20), nullable=False)
    
    # 損益表
    revenue = Column(BigInteger)
    gross_profit = Column(BigInteger)
    operating_income = Column(BigInteger)
    net_income = Column(BigInteger)
    eps = Column(Decimal(10, 2))
    
    # 資產負債表
    total_assets = Column(BigInteger)
    total_liabilities = Column(BigInteger)
    shareholders_equity = Column(BigInteger)
    book_value_per_share = Column(Decimal(10, 2))
    
    # 現金流量表
    operating_cash_flow = Column(BigInteger)
    investing_cash_flow = Column(BigInteger)
    financing_cash_flow = Column(BigInteger)
    free_cash_flow = Column(BigInteger)
    
    # 財務比率
    roe = Column(Decimal(5, 2))
    roa = Column(Decimal(5, 2))
    debt_ratio = Column(Decimal(5, 2))
    current_ratio = Column(Decimal(5, 2))
    
    created_at = Column(DateTime, default=func.now())
    
    # 關聯
    stock = relationship("Stock", back_populates="financial_statements")
    
    def __repr__(self):
        return f"<FinancialStatement(symbol={self.symbol}, year={self.year}, quarter={self.quarter})>"


class AIRecommendation(Base):
    """AI推薦結果表"""
    __tablename__ = "ai_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    recommendation_date = Column(Date, nullable=False, index=True)
    recommendation_type = Column(String(20), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    
    # 推薦資訊
    score = Column(Decimal(5, 2), nullable=False, index=True)
    rank = Column(Integer, index=True)
    confidence = Column(Decimal(5, 2))
    
    # 買賣建議
    buy_signal = Column(Boolean, default=False)
    sell_signal = Column(Boolean, default=False)
    target_price = Column(Decimal(10, 2))
    stop_loss = Column(Decimal(10, 2))
    
    # 支撐壓力位
    support_price = Column(Decimal(10, 2))
    resistance_price = Column(Decimal(10, 2))
    
    # 分析原因
    reasons = Column(JSON)
    technical_signals = Column(JSON)
    fundamental_signals = Column(JSON)
    
    # 時間範圍
    timeframe = Column(String(20))
    expected_holding_days = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())
    
    # 關聯
    stock = relationship("Stock", back_populates="ai_recommendations")
    
    def __repr__(self):
        return f"<AIRecommendation(symbol={self.symbol}, type={self.recommendation_type}, score={self.score})>"


class MarketData(Base):
    """市場總體資料表"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_date = Column(Date, nullable=False, unique=True, index=True)
    
    # 大盤指數
    taiex_index = Column(Decimal(10, 2))
    taiex_change = Column(Decimal(10, 2))
    taiex_change_pct = Column(Decimal(5, 2))
    
    # 市場統計
    total_volume = Column(BigInteger)
    total_turnover = Column(BigInteger)
    up_stocks = Column(Integer)
    down_stocks = Column(Integer)
    unchanged_stocks = Column(Integer)
    
    # 法人總計
    foreign_net_total = Column(BigInteger)
    trust_net_total = Column(BigInteger)
    dealer_net_total = Column(BigInteger)
    
    # 產業輪動指標
    electronics_index = Column(Decimal(10, 2))
    financials_index = Column(Decimal(10, 2))
    plastics_index = Column(Decimal(10, 2))
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<MarketData(date={self.trade_date}, taiex={self.taiex_index})>"


class Industry(Base):
    """產業分類表"""
    __tablename__ = "industries"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), index=True)
    description = Column(Text)
    
    # 產業統計
    stock_count = Column(Integer, default=0)
    market_cap = Column(BigInteger, default=0)
    avg_pe_ratio = Column(Decimal(10, 2))
    avg_pb_ratio = Column(Decimal(10, 2))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 關聯
    performance = relationship("IndustryPerformance", back_populates="industry", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Industry(code={self.code}, name={self.name})>"


class IndustryPerformance(Base):
    """產業每日表現表"""
    __tablename__ = "industry_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    industry_id = Column(Integer, ForeignKey("industries.id"), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    
    # 產業表現
    price_change_pct = Column(Decimal(5, 2))
    volume_change_pct = Column(Decimal(5, 2))
    up_stocks = Column(Integer)
    down_stocks = Column(Integer)
    
    # 法人進出
    foreign_net = Column(BigInteger)
    trust_net = Column(BigInteger)
    dealer_net = Column(BigInteger)
    
    # 輪動指標
    momentum_score = Column(Decimal(5, 2))
    strength_rank = Column(Integer, index=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # 關聯
    industry = relationship("Industry", back_populates="performance")
    
    def __repr__(self):
        return f"<IndustryPerformance(industry_id={self.industry_id}, date={self.trade_date})>"


class SystemSetting(Base):
    """系統設定表"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), nullable=False, unique=True, index=True)
    setting_value = Column(Text)
    description = Column(Text)
    category = Column(String(50), index=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemSetting(key={self.setting_key}, value={self.setting_value})>"


class DataUpdateLog(Base):
    """資料更新日誌表"""
    __tablename__ = "data_update_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    update_date = Column(Date, nullable=False, index=True)
    data_source = Column(String(50), nullable=False, index=True)
    table_name = Column(String(100), nullable=False)
    
    # 統計資訊
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    status = Column(String(20), default='processing', index=True)
    error_message = Column(Text)
    execution_time_seconds = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<DataUpdateLog(date={self.update_date}, source={self.data_source}, status={self.status})>"


# 工具函數
def get_or_create_stock(db, symbol: str, **kwargs):
    """取得或建立股票記錄"""
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        stock = Stock(symbol=symbol, **kwargs)
        db.add(stock)
        db.commit()
        db.refresh(stock)
    return stock


def get_latest_price(db, symbol: str):
    """取得最新價格"""
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        return None
    
    latest_price = (
        db.query(DailyPrice)
        .filter(DailyPrice.stock_id == stock.id)
        .order_by(DailyPrice.trade_date.desc())
        .first()
    )
    return latest_price


def get_stock_with_latest_data(db, symbol: str):
    """取得股票及最新相關資料"""
    from sqlalchemy.orm import joinedload
    
    stock = (
        db.query(Stock)
        .options(
            joinedload(Stock.daily_prices),
            joinedload(Stock.technical_indicators),
            joinedload(Stock.ai_recommendations)
        )
        .filter(Stock.symbol == symbol)
        .first()
    )
    
    return stock


def bulk_insert_prices(db, prices_data: list):
    """批量插入價格資料"""
    db.bulk_insert_mappings(DailyPrice, prices_data)
    db.commit()


def bulk_insert_indicators(db, indicators_data: list):
    """批量插入技術指標資料"""
    db.bulk_insert_mappings(TechnicalIndicator, indicators_data)
    db.commit()


# 資料驗證函數
def validate_stock_data(stock_data: dict) -> bool:
    """驗證股票資料完整性"""
    required_fields = ['symbol', 'name', 'market']
    return all(field in stock_data and stock_data[field] for field in required_fields)


def validate_price_data(price_data: dict) -> bool:
    """驗證價格資料完整性"""
    required_fields = ['symbol', 'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
    return all(field in price_data and price_data[field] is not None for field in required_fields)