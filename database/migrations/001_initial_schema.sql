-- =====================================================================
-- QUANT AI — SUPABASE POSTGRESQL INITIAL SCHEMA MIGRATION (001)
-- Multi-market Quantitative Swing Trading & AI Analysis Platform
-- Includes 22 Core Tables with Row Level Security (RLS)
-- Timezone default: America/Bogota | Currency: COP
-- =====================================================================

-- 1. Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------
-- 1. PROFILES (Extends auth.users)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    preferred_currency TEXT DEFAULT 'COP',
    timezone TEXT DEFAULT 'America/Bogota',
    theme TEXT DEFAULT 'dark',
    risk_tolerance TEXT DEFAULT 'moderate',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 2. USER PERMISSIONS & ROLES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'trader', -- 'viewer', 'trader', 'quant_researcher', 'admin'
    can_backtest BOOLEAN DEFAULT TRUE,
    can_use_ai_assistant BOOLEAN DEFAULT TRUE,
    can_use_live_vision BOOLEAN DEFAULT TRUE,
    can_use_live_voice BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 3. USER VOICE PREFERENCES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_voice_preferences (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    voice_name TEXT DEFAULT 'es-CO-Standard-A',
    voice_gender TEXT DEFAULT 'female',
    speaking_rate NUMERIC(3, 2) DEFAULT 1.0,
    pitch NUMERIC(3, 2) DEFAULT 1.0,
    volume NUMERIC(3, 2) DEFAULT 1.0,
    auto_speak BOOLEAN DEFAULT FALSE,
    continuous_listening BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 4. DATA SOURCES TELEMETRY
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.data_sources (
    id TEXT PRIMARY KEY, -- 'yahoo', 'binance', 'bvc', 'banrep', 'fred'
    name TEXT NOT NULL,
    market_types TEXT[] NOT NULL, -- ARRAY['stock', 'etf', 'crypto', 'macro']
    is_active BOOLEAN DEFAULT TRUE,
    is_realtime BOOLEAN DEFAULT FALSE,
    rate_limit_per_minute INT DEFAULT 60,
    latency_ms INT DEFAULT 0,
    last_ping TIMESTAMPTZ,
    notes TEXT
);

-- ---------------------------------------------------------------------
-- 5. INSTRUMENTS (Stocks, ETFs, Crypto, FX, Indices)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.instruments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT UNIQUE NOT NULL, -- 'AAPL', 'BTCUSDT', 'ECOPETROL'
    name TEXT NOT NULL,
    market TEXT NOT NULL, -- 'stock', 'etf', 'crypto', 'index', 'macro'
    exchange TEXT, -- 'NASDAQ', 'NYSE', 'BINANCE', 'BVC'
    base_currency TEXT NOT NULL DEFAULT 'USD',
    quote_currency TEXT NOT NULL DEFAULT 'USD',
    primary_source TEXT NOT NULL REFERENCES public.data_sources(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 6. OHLCV BARS (Normalized Bar History)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ohlcv_bars (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL, -- '1m', '5m', '15m', '1h', '4h', '1d', '1w'
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(18, 8) NOT NULL,
    high NUMERIC(18, 8) NOT NULL,
    low NUMERIC(18, 8) NOT NULL,
    close NUMERIC(18, 8) NOT NULL,
    volume NUMERIC(24, 8) NOT NULL,
    quote_volume NUMERIC(24, 8),
    trades_count INT,
    source TEXT NOT NULL,
    data_status TEXT DEFAULT 'historical', -- 'realtime', 'delayed', 'historical', 'provisional'
    downloaded_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    CONSTRAINT uq_symbol_interval_timestamp UNIQUE (symbol, interval, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_interval_time ON public.ohlcv_bars (symbol, interval, timestamp DESC);

-- ---------------------------------------------------------------------
-- 7. INDICATOR VALUES (Precomputed / Cached indicators)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.indicator_values (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    indicator_name TEXT NOT NULL, -- 'EMA_20', 'RSI_14', 'MACD', 'ATR_14'
    timestamp TIMESTAMPTZ NOT NULL,
    values JSONB NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    CONSTRAINT uq_indicator_point UNIQUE (symbol, interval, indicator_name, timestamp)
);

-- ---------------------------------------------------------------------
-- 8. MARKET STRUCTURES (HH, HL, LH, LL, Swings, Breakouts)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.market_structures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    structure_type TEXT NOT NULL, -- 'HH', 'HL', 'LH', 'LL', 'SWING_HIGH', 'SWING_LOW', 'RANGE'
    price_level NUMERIC(18, 8) NOT NULL,
    confirmed_at TIMESTAMPTZ NOT NULL,
    is_broken BOOLEAN DEFAULT FALSE,
    broken_at TIMESTAMPTZ,
    details JSONB
);

-- ---------------------------------------------------------------------
-- 9. SMART MONEY CONCEPTS (SMC ZONES: BOS, CHOCH, OB, FVG)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.smc_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    zone_type TEXT NOT NULL, -- 'BOS', 'CHOCH', 'ORDER_BLOCK', 'FVG', 'BREAKER', 'IND_EQUILIBRIUM'
    direction TEXT NOT NULL, -- 'bullish', 'bearish'
    top_price NUMERIC(18, 8) NOT NULL,
    bottom_price NUMERIC(18, 8) NOT NULL,
    formed_at TIMESTAMPTZ NOT NULL,
    is_mitigated BOOLEAN DEFAULT FALSE,
    mitigated_at TIMESTAMPTZ,
    quality_score NUMERIC(5, 2),
    metadata JSONB
);

-- ---------------------------------------------------------------------
-- 10. LIQUIDITY ZONES (BSL, SSL, Equal Highs/Lows, Sweeps)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.liquidity_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    liquidity_type TEXT NOT NULL, -- 'BSL', 'SSL', 'EQH', 'EQL', 'PREV_DAY_HIGH', 'PREV_DAY_LOW'
    price_level NUMERIC(18, 8) NOT NULL,
    price_upper NUMERIC(18, 8),
    price_lower NUMERIC(18, 8),
    touches INT DEFAULT 2,
    liquidity_score NUMERIC(5, 2) NOT NULL,
    is_swept BOOLEAN DEFAULT FALSE,
    swept_at TIMESTAMPTZ,
    sweep_type TEXT, -- 'provisional', 'confirmed_close', 'sustained_break'
    detected_at TIMESTAMPTZ NOT NULL,
    metadata JSONB
);

-- ---------------------------------------------------------------------
-- 11. ORDER BOOK SNAPSHOTS (Depth and Imbalance)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.order_book_snapshots (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    source TEXT NOT NULL,
    best_bid NUMERIC(18, 8) NOT NULL,
    best_ask NUMERIC(18, 8) NOT NULL,
    spread NUMERIC(18, 8) NOT NULL,
    imbalance_ratio NUMERIC(6, 4) NOT NULL,
    bids_depth JSONB NOT NULL,
    asks_depth JSONB NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL
);

-- ---------------------------------------------------------------------
-- 12. WATCHLISTS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    symbols TEXT[] NOT NULL DEFAULT '{}',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 13. SCANNER RESULTS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.scanner_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    matched_criteria TEXT[] NOT NULL,
    unmatched_criteria TEXT[] NOT NULL,
    score NUMERIC(5, 2),
    scanned_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    evidence JSONB
);

-- ---------------------------------------------------------------------
-- 14. STRATEGIES (Hypothetical & Quantitative)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    rules JSONB NOT NULL,
    risk_parameters JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 15. BACKTEST RUNS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.backtest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES public.strategies(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital NUMERIC(18, 2) NOT NULL,
    final_equity NUMERIC(18, 2) NOT NULL,
    total_trades INT NOT NULL,
    win_rate NUMERIC(5, 2) NOT NULL,
    profit_factor NUMERIC(6, 2),
    sharpe_ratio NUMERIC(6, 2),
    sortino_ratio NUMERIC(6, 2),
    max_drawdown NUMERIC(5, 2) NOT NULL,
    cagr NUMERIC(5, 2),
    slippage_modeled NUMERIC(6, 4) DEFAULT 0.0005,
    commission_modeled NUMERIC(6, 4) DEFAULT 0.001,
    executed_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 16. BACKTEST TRADES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.backtest_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_run_id UUID NOT NULL REFERENCES public.backtest_runs(id) ON DELETE CASCADE,
    trade_number INT NOT NULL,
    direction TEXT NOT NULL, -- 'long', 'short'
    entry_time TIMESTAMPTZ NOT NULL,
    entry_price NUMERIC(18, 8) NOT NULL,
    exit_time TIMESTAMPTZ NOT NULL,
    exit_price NUMERIC(18, 8) NOT NULL,
    stop_loss NUMERIC(18, 8) NOT NULL,
    take_profit NUMERIC(18, 8) NOT NULL,
    quantity NUMERIC(18, 8) NOT NULL,
    pnl NUMERIC(18, 2) NOT NULL,
    pnl_percentage NUMERIC(6, 2) NOT NULL,
    exit_reason TEXT NOT NULL -- 'take_profit', 'stop_loss', 'timeout', 'signal'
);

-- ---------------------------------------------------------------------
-- 17. SIMULATED PORTFOLIOS (Paper Trading / Educational Sandbox)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.simulated_portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    initial_balance NUMERIC(18, 2) DEFAULT 100000000.00, -- 100M COP
    current_cash NUMERIC(18, 2) DEFAULT 100000000.00,
    currency TEXT DEFAULT 'COP',
    positions JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 18. TRADING JOURNAL
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL, -- 'long', 'short'
    hypothesis TEXT NOT NULL,
    evidence TEXT NOT NULL,
    invalidation_criteria TEXT NOT NULL,
    risk_reward_ratio NUMERIC(4, 2),
    outcome_status TEXT DEFAULT 'pending', -- 'pending', 'win', 'loss', 'scratched'
    tags TEXT[] DEFAULT '{}',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 19. ALERTS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    condition_type TEXT NOT NULL, -- 'RSI', 'EMA_CROSS', 'BOS', 'SWEEP', 'PRICE_LEVEL'
    parameters JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMPTZ,
    trigger_message TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 20. CHAT SESSIONS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Nuevo Análisis Cuantitativo',
    active_symbol TEXT,
    active_interval TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 21. CHAT MESSAGES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    quantitative_context JSONB, -- Bound market data snapshot at query time
    tool_calls JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------
-- 22. AI REPORTS (Audit and Explainability)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ai_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    observation TEXT NOT NULL,
    evidence TEXT NOT NULL,
    hypotheses JSONB NOT NULL,
    limitations TEXT NOT NULL,
    market_data_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);

-- =====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Ensures user data isolation and multi-tenant security
-- =====================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_voice_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.backtest_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.simulated_portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_reports ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can read and update their own profile
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Watchlists: Users manage their own watchlists
CREATE POLICY "Users can manage own watchlists" ON public.watchlists FOR ALL USING (auth.uid() = user_id);

-- Portfolios: Users manage own simulated portfolios
CREATE POLICY "Users can manage own portfolios" ON public.simulated_portfolios FOR ALL USING (auth.uid() = user_id);

-- Journal: Users manage own journal entries
CREATE POLICY "Users can manage own journal" ON public.journal_entries FOR ALL USING (auth.uid() = user_id);

-- Chat: Users manage own sessions and messages
CREATE POLICY "Users can manage own chat sessions" ON public.chat_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view messages in own sessions" ON public.chat_messages FOR ALL
    USING (EXISTS (SELECT 1 FROM public.chat_sessions s WHERE s.id = session_id AND s.user_id = auth.uid()));

-- Public Market Data Tables (Read-only for all authenticated or public users)
ALTER TABLE public.instruments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read for instruments" ON public.instruments FOR SELECT USING (true);

ALTER TABLE public.ohlcv_bars ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read for ohlcv_bars" ON public.ohlcv_bars FOR SELECT USING (true);

ALTER TABLE public.data_sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read for data_sources" ON public.data_sources FOR SELECT USING (true);
