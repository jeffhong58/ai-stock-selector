-- AI選股系統資料庫初始化腳本
-- 支援免費資料源，預留TEJ擴展欄位

-- 建立資料庫擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 股票基本資料表
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,              -- 股票代號 (如: 2330)
    name VARCHAR(100) NOT NULL,                      -- 股票名稱
    market VARCHAR(20) NOT NULL,                     -- 市場 (TSE, OTC)
    industry VARCHAR(50),                            -- 產業別
    sector VARCHAR(50),                              -- 類股
    listing_date DATE,                               -- 上市日期
    capital BIGINT,                                  -- 實收資本額
    shares_outstanding BIGINT,                       -- 流通股數
    par_value DECIMAL(10,2),                         -- 面額
    
    -- 基本面資料 (來自公開觀測站)
    market_cap BIGINT,                               -- 市值
    pe_ratio DECIMAL(10,2),                          -- 本益比
    pb_ratio DECIMAL(10,2),                          -- 股價淨值比
    dividend_yield DECIMAL(5,2),                     -- 殖利率
    
    -- TEJ擴展欄位 (預留)
    tej_industry_code VARCHAR(20),                   -- TEJ產業代碼
    tej_financial_data JSONB,                        -- TEJ財務資料
    tej_ratings JSONB,                               -- TEJ評等資料
    
    is_active BOOLEAN DEFAULT TRUE,                  -- 是否有效
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引
CREATE INDEX idx_stocks_symbol ON stocks(symbol);
CREATE INDEX idx_stocks_market ON stocks(market);
CREATE INDEX idx_stocks_industry ON stocks(industry);
CREATE INDEX idx_stocks_sector ON stocks(sector);

-- 日線價格資料表
CREATE TABLE daily_prices (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,                     -- 冗餘欄位，加速查詢
    trade_date DATE NOT NULL,                        -- 交易日期
    
    -- OHLCV資料 (來自Yahoo Finance)
    open_price DECIMAL(10,2) NOT NULL,               -- 開盤價
    high_price DECIMAL(10,2) NOT NULL,               -- 最高價
    low_price DECIMAL(10,2) NOT NULL,                -- 最低價
    close_price DECIMAL(10,2) NOT NULL,              -- 收盤價
    adj_close DECIMAL(10,2),                         -- 調整收盤價
    volume BIGINT NOT NULL,                          -- 成交量
    turnover BIGINT,                                 -- 成交值
    
    -- 計算欄位
    price_change DECIMAL(10,2),                      -- 漲跌
    price_change_pct DECIMAL(5,2),                   -- 漲跌幅
    
    -- TEJ擴展欄位 (預留)
    tej_adjusted_price DECIMAL(10,2),                -- TEJ調整價格
    tej_volume_data JSONB,                           -- TEJ成交量細節
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, trade_date)
);

-- 建立索引
CREATE INDEX idx_daily_prices_symbol_date ON daily_prices(symbol, trade_date DESC);
CREATE INDEX idx_daily_prices_trade_date ON daily_prices(trade_date DESC);
CREATE INDEX idx_daily_prices_stock_id ON daily_prices(stock_id);

-- 技術指標資料表
CREATE TABLE technical_indicators (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    
    -- 移動平均線
    ma_5 DECIMAL(10,2),                              -- 5日均線
    ma_10 DECIMAL(10,2),                             -- 10日均線
    ma_20 DECIMAL(10,2),                             -- 20日均線
    ma_60 DECIMAL(10,2),                             -- 60日均線
    ma_120 DECIMAL(10,2),                            -- 120日均線
    ma_240 DECIMAL(10,2),                            -- 240日均線
    
    -- 指數移動平均線
    ema_12 DECIMAL(10,2),                            -- 12日EMA
    ema_26 DECIMAL(10,2),                            -- 26日EMA
    
    -- 技術指標
    rsi_14 DECIMAL(5,2),                             -- 14日RSI
    macd DECIMAL(10,4),                              -- MACD
    macd_signal DECIMAL(10,4),                       -- MACD信號線
    macd_histogram DECIMAL(10,4),                    -- MACD柱狀圖
    
    -- KD指標
    k_value DECIMAL(5,2),                            -- K值
    d_value DECIMAL(5,2),                            -- D值
    
    -- 布林帶
    bb_upper DECIMAL(10,2),                          -- 布林帶上軌
    bb_middle DECIMAL(10,2),                         -- 布林帶中軌
    bb_lower DECIMAL(10,2),                          -- 布林帶下軌
    
    -- 成交量指標
    volume_ma_5 BIGINT,                              -- 5日量均
    volume_ma_20 BIGINT,                             -- 20日量均
    
    -- 支撐壓力位
    support_level DECIMAL(10,2),                     -- 支撐位
    resistance_level DECIMAL(10,2),                  -- 壓力位
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, trade_date)
);

-- 建立索引
CREATE INDEX idx_technical_indicators_symbol_date ON technical_indicators(symbol, trade_date DESC);

-- 三大法人買賣資料表 (來自證交所)
CREATE TABLE institutional_trading (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    
    -- 外資
    foreign_buy BIGINT DEFAULT 0,                    -- 外資買進
    foreign_sell BIGINT DEFAULT 0,                   -- 外資賣出
    foreign_net BIGINT DEFAULT 0,                    -- 外資淨買賣
    
    -- 投信
    trust_buy BIGINT DEFAULT 0,                      -- 投信買進
    trust_sell BIGINT DEFAULT 0,                     -- 投信賣出
    trust_net BIGINT DEFAULT 0,                      -- 投信淨買賣
    
    -- 自營商
    dealer_buy BIGINT DEFAULT 0,                     -- 自營商買進
    dealer_sell BIGINT DEFAULT 0,                    -- 自營商賣出
    dealer_net BIGINT DEFAULT 0,                     -- 自營商淨買賣
    
    -- 總計
    total_net BIGINT DEFAULT 0,                      -- 三大法人淨買賣
    
    -- TEJ擴展欄位 (預留)
    tej_qfii_data JSONB,                            -- TEJ外資細分資料
    tej_dealer_detail JSONB,                        -- TEJ自營商細節
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, trade_date)
);

-- 建立索引
CREATE INDEX idx_institutional_trading_symbol_date ON institutional_trading(symbol, trade_date DESC);

-- 融資融券資料表 (來自證交所)
CREATE TABLE margin_trading (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    
    -- 融資
    margin_buy BIGINT DEFAULT 0,                     -- 融資買進
    margin_sell BIGINT DEFAULT 0,                    -- 融資賣出
    margin_balance BIGINT DEFAULT 0,                 -- 融資餘額
    margin_quota BIGINT DEFAULT 0,                   -- 融資限額
    
    -- 融券
    short_sell BIGINT DEFAULT 0,                     -- 融券賣出
    short_cover BIGINT DEFAULT 0,                    -- 融券買進
    short_balance BIGINT DEFAULT 0,                  -- 融券餘額
    short_quota BIGINT DEFAULT 0,                    -- 融券限額
    
    -- 券資比
    short_margin_ratio DECIMAL(5,2),                 -- 券資比
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, trade_date)
);

-- 建立索引
CREATE INDEX idx_margin_trading_symbol_date ON margin_trading(symbol, trade_date DESC);

-- 財務報表資料表 (來自公開觀測站)
CREATE TABLE financial_statements (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL,                           -- 年度
    quarter INTEGER NOT NULL,                        -- 季度 (1-4)
    report_type VARCHAR(20) NOT NULL,                -- 報表類型 (Q1, Q2, Q3, Q4, Y)
    
    -- 損益表
    revenue BIGINT,                                  -- 營收
    gross_profit BIGINT,                             -- 毛利
    operating_income BIGINT,                         -- 營業利益
    net_income BIGINT,                               -- 淨利
    eps DECIMAL(10,2),                               -- 每股盈餘
    
    -- 資產負債表
    total_assets BIGINT,                             -- 總資產
    total_liabilities BIGINT,                        -- 總負債
    shareholders_equity BIGINT,                      -- 股東權益
    book_value_per_share DECIMAL(10,2),              -- 每股淨值
    
    -- 現金流量表
    operating_cash_flow BIGINT,                      -- 營業現金流
    investing_cash_flow BIGINT,                      -- 投資現金流
    financing_cash_flow BIGINT,                      -- 融資現金流
    free_cash_flow BIGINT,                           -- 自由現金流
    
    -- 財務比率
    roe DECIMAL(5,2),                                -- ROE
    roa DECIMAL(5,2),                                -- ROA
    debt_ratio DECIMAL(5,2),                         -- 負債比率
    current_ratio DECIMAL(5,2),                      -- 流動比率
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, year, quarter)
);

-- 建立索引
CREATE INDEX idx_financial_statements_symbol_year ON financial_statements(symbol, year DESC, quarter DESC);

-- AI推薦結果表
CREATE TABLE ai_recommendations (
    id SERIAL PRIMARY KEY,
    recommendation_date DATE NOT NULL,               -- 推薦日期
    recommendation_type VARCHAR(20) NOT NULL,        -- 推薦類型 (sector, short_term, mid_term, long_term)
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    
    -- 推薦資訊
    score DECIMAL(5,2) NOT NULL,                     -- 推薦分數 (0-100)
    rank INTEGER,                                    -- 排名
    confidence DECIMAL(5,2),                         -- 信心度
    
    -- 買賣建議
    buy_signal BOOLEAN DEFAULT FALSE,                -- 買進信號
    sell_signal BOOLEAN DEFAULT FALSE,               -- 賣出信號
    target_price DECIMAL(10,2),                      -- 目標價
    stop_loss DECIMAL(10,2),                         -- 停損價
    
    -- 支撐壓力位
    support_price DECIMAL(10,2),                     -- 支撐價
    resistance_price DECIMAL(10,2),                  -- 壓力價
    
    -- 分析原因
    reasons JSONB,                                   -- 推薦原因 (JSON格式)
    technical_signals JSONB,                         -- 技術信號
    fundamental_signals JSONB,                       -- 基本面信號
    
    -- 時間範圍
    timeframe VARCHAR(20),                           -- 投資時間框架 (short/mid/long)
    expected_holding_days INTEGER,                   -- 預期持有天數
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(recommendation_date, recommendation_type, stock_id)
);

-- 建立索引
CREATE INDEX idx_ai_recommendations_date_type ON ai_recommendations(recommendation_date DESC, recommendation_type);
CREATE INDEX idx_ai_recommendations_symbol ON ai_recommendations(symbol);
CREATE INDEX idx_ai_recommendations_score ON ai_recommendations(score DESC);

-- 市場總體資料表
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,                 -- 交易日期
    
    -- 大盤指數
    taiex_index DECIMAL(10,2),                       -- 台股指數
    taiex_change DECIMAL(10,2),                      -- 指數漲跌
    taiex_change_pct DECIMAL(5,2),                   -- 指數漲跌幅
    
    -- 市場統計
    total_volume BIGINT,                             -- 總成交量
    total_turnover BIGINT,                           -- 總成交值
    up_stocks INTEGER,                               -- 上漲股票數
    down_stocks INTEGER,                             -- 下跌股票數
    unchanged_stocks INTEGER,                        -- 平盤股票數
    
    -- 法人總計
    foreign_net_total BIGINT,                        -- 外資淨買賣總額
    trust_net_total BIGINT,                          -- 投信淨買賣總額
    dealer_net_total BIGINT,                         -- 自營商淨買賣總額
    
    -- 產業輪動指標
    electronics_index DECIMAL(10,2),                 -- 電子類股指數
    financials_index DECIMAL(10,2),                  -- 金融類股指數
    plastics_index DECIMAL(10,2),                    -- 塑膠類股指數
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引
CREATE INDEX idx_market_data_trade_date ON market_data(trade_date DESC);

-- 產業分類表
CREATE TABLE industries (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,                -- 產業代碼
    name VARCHAR(100) NOT NULL,                      -- 產業名稱
    category VARCHAR(50),                            -- 大分類 (電子、傳產、金融等)
    description TEXT,                                -- 產業描述
    
    -- 產業統計 (每日更新)
    stock_count INTEGER DEFAULT 0,                   -- 該產業股票數量
    market_cap BIGINT DEFAULT 0,                     -- 產業總市值
    avg_pe_ratio DECIMAL(10,2),                      -- 平均本益比
    avg_pb_ratio DECIMAL(10,2),                      -- 平均股價淨值比
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引
CREATE INDEX idx_industries_category ON industries(category);

-- 產業每日表現表
CREATE TABLE industry_performance (
    id SERIAL PRIMARY KEY,
    industry_id INTEGER REFERENCES industries(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    
    -- 產業表現
    price_change_pct DECIMAL(5,2),                   -- 產業漲跌幅
    volume_change_pct DECIMAL(5,2),                  -- 成交量變化
    up_stocks INTEGER,                               -- 上漲股票數
    down_stocks INTEGER,                             -- 下跌股票數
    
    -- 法人進出
    foreign_net BIGINT,                              -- 外資淨買賣
    trust_net BIGINT,                                -- 投信淨買賣
    dealer_net BIGINT,                               -- 自營商淨買賣
    
    -- 輪動指標
    momentum_score DECIMAL(5,2),                     -- 動能分數
    strength_rank INTEGER,                           -- 強勢排名
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(industry_id, trade_date)
);

-- 建立索引
CREATE INDEX idx_industry_performance_date ON industry_performance(trade_date DESC);
CREATE INDEX idx_industry_performance_momentum ON industry_performance(momentum_score DESC);

-- 使用者自選股表 (未來功能)
CREATE TABLE user_watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,                                 -- 使用者ID (未來實現)
    name VARCHAR(100) NOT NULL,                      -- 自選股名稱
    description TEXT,                                -- 描述
    is_default BOOLEAN DEFAULT FALSE,                -- 是否為預設
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 自選股股票關聯表
CREATE TABLE watchlist_stocks (
    id SERIAL PRIMARY KEY,
    watchlist_id INTEGER REFERENCES user_watchlists(id) ON DELETE CASCADE,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    added_date DATE DEFAULT CURRENT_DATE,
    notes TEXT,                                      -- 備註
    
    UNIQUE(watchlist_id, stock_id)
);

-- 系統設定表
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,       -- 設定鍵
    setting_value TEXT,                              -- 設定值
    description TEXT,                                -- 描述
    category VARCHAR(50),                            -- 分類
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入預設系統設定
INSERT INTO system_settings (setting_key, setting_value, description, category) VALUES
('data_update_time', '17:30', '資料更新時間', 'schedule'),
('ai_model_version', '1.0.0', 'AI模型版本', 'ai'),
('tej_enabled', 'false', '是否啟用TEJ數據源', 'data_source'),
('yahoo_finance_enabled', 'true', '是否啟用Yahoo Finance', 'data_source'),
('twse_enabled', 'true', '是否啟用證交所數據', 'data_source'),
('mops_enabled', 'true', '是否啟用公開觀測站數據', 'data_source'),
('recommendation_retention_days', '90', '推薦結果保留天數', 'cleanup'),
('min_trading_days', '60', '最少交易天數要求', 'filter'),
('max_recommendations_per_type', '50', '每類型最大推薦數量', 'ai');

-- 資料更新日誌表
CREATE TABLE data_update_logs (
    id SERIAL PRIMARY KEY,
    update_date DATE NOT NULL,                       -- 更新日期
    data_source VARCHAR(50) NOT NULL,                -- 資料源
    table_name VARCHAR(100) NOT NULL,                -- 更新的表名
    records_processed INTEGER DEFAULT 0,             -- 處理的記錄數
    records_inserted INTEGER DEFAULT 0,              -- 新增的記錄數
    records_updated INTEGER DEFAULT 0,               -- 更新的記錄數
    records_failed INTEGER DEFAULT 0,                -- 失敗的記錄數
    status VARCHAR(20) DEFAULT 'processing',         -- 狀態 (processing, completed, failed)
    error_message TEXT,                              -- 錯誤訊息
    execution_time_seconds INTEGER,                  -- 執行時間(秒)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 建立索引
CREATE INDEX idx_data_update_logs_date_source ON data_update_logs(update_date DESC, data_source);
CREATE INDEX idx_data_update_logs_status ON data_update_logs(status);

-- 建立觸發器函數：自動更新 updated_at 欄位
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ language 'plpgsql';

-- 建立觸發器
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON stocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_industries_updated_at BEFORE UPDATE ON industries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_watchlists_updated_at BEFORE UPDATE ON user_watchlists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 建立視圖：股票完整資訊
CREATE VIEW stock_full_info AS
SELECT 
    s.*,
    i.name as industry_name,
    i.category as industry_category,
    dp.close_price as latest_price,
    dp.price_change,
    dp.price_change_pct,
    dp.volume as latest_volume,
    dp.trade_date as latest_trade_date,
    ti.rsi_14,
    ti.ma_20,
    ti.ma_60,
    it.foreign_net as latest_foreign_net,
    it.trust_net as latest_trust_net,
    ar.score as ai_score,
    ar.rank as ai_rank
FROM stocks s
LEFT JOIN industries i ON s.industry = i.code
LEFT JOIN LATERAL (
    SELECT * FROM daily_prices dp2 
    WHERE dp2.stock_id = s.id 
    ORDER BY dp2.trade_date DESC 
    LIMIT 1
) dp ON true
LEFT JOIN LATERAL (
    SELECT * FROM technical_indicators ti2 
    WHERE ti2.stock_id = s.id 
    ORDER BY ti2.trade_date DESC 
    LIMIT 1
) ti ON true
LEFT JOIN LATERAL (
    SELECT * FROM institutional_trading it2 
    WHERE it2.stock_id = s.id 
    ORDER BY it2.trade_date DESC 
    LIMIT 1
) it ON true
LEFT JOIN LATERAL (
    SELECT * FROM ai_recommendations ar2 
    WHERE ar2.stock_id = s.id 
    ORDER BY ar2.recommendation_date DESC 
    LIMIT 1
) ar ON true
WHERE s.is_active = true;

-- 建立視圖：每日推薦摘要
CREATE VIEW daily_recommendations_summary AS
SELECT 
    recommendation_date,
    recommendation_type,
    COUNT(*) as total_recommendations,
    AVG(score) as avg_score,
    MAX(score) as max_score,
    MIN(score) as min_score,
    SUM(CASE WHEN buy_signal THEN 1 ELSE 0 END) as buy_signals,
    SUM(CASE WHEN sell_signal THEN 1 ELSE 0 END) as sell_signals
FROM ai_recommendations
GROUP BY recommendation_date, recommendation_type
ORDER BY recommendation_date DESC, recommendation_type;

-- 建立分區表：提升大量歷史資料查詢效能
-- 將 daily_prices 依年份分區
ALTER TABLE daily_prices RENAME TO daily_prices_old;

CREATE TABLE daily_prices (
    LIKE daily_prices_old INCLUDING ALL
) PARTITION BY RANGE (trade_date);

-- 建立年度分區 (可根據需要調整)
CREATE TABLE daily_prices_2023 PARTITION OF daily_prices
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE daily_prices_2024 PARTITION OF daily_prices
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE daily_prices_2025 PARTITION OF daily_prices
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- 將舊資料遷移到新分區表 (如果有的話)
-- INSERT INTO daily_prices SELECT * FROM daily_prices_old;

-- 刪除舊表
DROP TABLE daily_prices_old;

-- 建立函數：計算技術指標
CREATE OR REPLACE FUNCTION calculate_technical_indicators(
    p_stock_id INTEGER,
    p_trade_date DATE
) RETURNS VOID AS $
DECLARE
    v_prices DECIMAL(10,2)[];
    v_volumes BIGINT[];
    v_count INTEGER;
BEGIN
    -- 取得最近60天的價格和成交量數據
    SELECT 
        array_agg(close_price ORDER BY trade_date),
        array_agg(volume ORDER BY trade_date),
        COUNT(*)
    INTO v_prices, v_volumes, v_count
    FROM daily_prices 
    WHERE stock_id = p_stock_id 
      AND trade_date <= p_trade_date
      AND trade_date >= p_trade_date - INTERVAL '60 days'
    ORDER BY trade_date;
    
    -- 如果資料不足，則不計算
    IF v_count < 20 THEN
        RETURN;
    END IF;
    
    -- 插入或更新技術指標
    INSERT INTO technical_indicators (
        stock_id, 
        trade_date,
        ma_5,
        ma_20,
        volume_ma_5,
        volume_ma_20
    ) VALUES (
        p_stock_id,
        p_trade_date,
        -- 計算5日均線 (簡化版本，實際應使用更複雜的演算法)
        (SELECT AVG(unnest) FROM unnest(v_prices[greatest(1, v_count-4):v_count])),
        -- 計算20日均線
        (SELECT AVG(unnest) FROM unnest(v_prices[greatest(1, v_count-19):v_count])),
        -- 計算5日量均
        (SELECT AVG(unnest) FROM unnest(v_volumes[greatest(1, v_count-4):v_count])),
        -- 計算20日量均
        (SELECT AVG(unnest) FROM unnest(v_volumes[greatest(1, v_count-19):v_count]))
    )
    ON CONFLICT (stock_id, trade_date) 
    DO UPDATE SET
        ma_5 = EXCLUDED.ma_5,
        ma_20 = EXCLUDED.ma_20,
        volume_ma_5 = EXCLUDED.volume_ma_5,
        volume_ma_20 = EXCLUDED.volume_ma_20;
END;
$ LANGUAGE plpgsql;

-- 建立函數：清理舊資料
CREATE OR REPLACE FUNCTION cleanup_old_data() RETURNS VOID AS $
DECLARE
    retention_days INTEGER;
BEGIN
    -- 取得保留天數設定
    SELECT setting_value::INTEGER INTO retention_days
    FROM system_settings 
    WHERE setting_key = 'recommendation_retention_days';
    
    IF retention_days IS NULL THEN
        retention_days := 90; -- 預設保留90天
    END IF;
    
    -- 清理舊的推薦記錄
    DELETE FROM ai_recommendations 
    WHERE recommendation_date < CURRENT_DATE - INTERVAL '1 day' * retention_days;
    
    -- 清理舊的更新日誌
    DELETE FROM data_update_logs 
    WHERE update_date < CURRENT_DATE - INTERVAL '1 day' * (retention_days * 2);
    
    -- 更新統計資訊
    ANALYZE ai_recommendations;
    ANALYZE data_update_logs;
END;
$ LANGUAGE plpgsql;

-- 初始化台股主要產業資料
INSERT INTO industries (code, name, category) VALUES
('01', '水泥工業', '傳統產業'),
('02', '食品工業', '傳統產業'),
('03', '塑膠工業', '傳統產業'),
('04', '紡織纖維', '傳統產業'),
('05', '電機機械', '傳統產業'),
('06', '電器電纜', '傳統產業'),
('08', '玻璃陶瓷', '傳統產業'),
('09', '造紙工業', '傳統產業'),
('10', '鋼鐵工業', '傳統產業'),
('11', '橡膠工業', '傳統產業'),
('12', '汽車工業', '傳統產業'),
('14', '建材營造', '傳統產業'),
('15', '航運業', '傳統產業'),
('16', '觀光事業', '傳統產業'),
('17', '金融保險', '金融業'),
('18', '貿易百貨', '傳統產業'),
('19', '綜合', '其他'),
('20', '其他', '其他'),
('21', '化學工業', '傳統產業'),
('22', '生技醫療', '生技醫療'),
('23', '油電燃氣', '傳統產業'),
('24', '半導體', '電子業'),
('25', '電腦及週邊設備', '電子業'),
('26', '光電業', '電子業'),
('27', '通信網路', '電子業'),
('28', '電子零組件', '電子業'),
('29', '電子通路', '電子業'),
('30', '資訊服務', '電子業'),
('31', '其他電子', '電子業');

COMMENT ON TABLE stocks IS '股票基本資料表，支援TEJ擴展';
COMMENT ON TABLE daily_prices IS '日線價格資料表，按年份分區';
COMMENT ON TABLE technical_indicators IS '技術指標計算結果表';
COMMENT ON TABLE institutional_trading IS '三大法人買賣資料表';
COMMENT ON TABLE margin_trading IS '融資融券資料表';
COMMENT ON TABLE financial_statements IS '財務報表資料表';
COMMENT ON TABLE ai_recommendations IS 'AI推薦結果表';
COMMENT ON TABLE market_data IS '市場總體資料表';
COMMENT ON TABLE industries IS '產業分類表';
COMMENT ON TABLE industry_performance IS '產業每日表現表';

-- 資料庫初始化完成