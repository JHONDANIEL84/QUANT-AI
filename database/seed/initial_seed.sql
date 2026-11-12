-- =====================================================================
-- QUANT AI — INITIAL SEED DATA (Instruments & Data Sources)
-- =====================================================================

-- 1. Insert Data Sources
INSERT INTO public.data_sources (id, name, market_types, is_active, is_realtime, notes)
VALUES
    ('yahoo', 'Yahoo Finance API Adapter', ARRAY['stock', 'etf', 'index'], TRUE, FALSE, 'Free OHLCV, delayed by 15 mins for stocks, historical data.'),
    ('binance', 'Binance Public Market Data & Streams', ARRAY['crypto'], TRUE, TRUE, 'Free real-time tickers, OHLCV, Order Book depth via WebSocket and Vision API.'),
    ('bvc', 'Bolsa de Valores de Colombia CSV Adapter', ARRAY['stock', 'index'], TRUE, FALSE, 'Historical EOD data from Colombian equity market.'),
    ('banrep', 'Banco de la República de Colombia', ARRAY['macro'], TRUE, FALSE, 'Inflation, policy interest rates, TRM USD/COP.'),
    ('fred', 'Federal Reserve Economic Data (FRED)', ARRAY['macro'], TRUE, FALSE, 'US Fed funds, CPI, GDP, unemployment.')
ON CONFLICT (id) DO UPDATE SET is_active = EXCLUDED.is_active;

-- 2. Insert Core Instruments (Stocks, ETFs, Crypto, BVC)
INSERT INTO public.instruments (symbol, name, market, exchange, base_currency, quote_currency, primary_source)
VALUES
    -- US Equities (Yahoo)
    ('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'USD', 'USD', 'yahoo'),
    ('MSFT', 'Microsoft Corporation', 'stock', 'NASDAQ', 'USD', 'USD', 'yahoo'),
    ('NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', 'USD', 'USD', 'yahoo'),
    ('TSLA', 'Tesla Inc.', 'stock', 'NASDAQ', 'USD', 'USD', 'yahoo'),
    ('AMZN', 'Amazon.com Inc.', 'stock', 'NASDAQ', 'USD', 'USD', 'yahoo'),
    ('GOOGL', 'Alphabet Inc. (Class A)', 'stock', 'NASDAQ', 'USD', 'USD', 'yahoo'),
    ('META', 'Meta Platforms Inc.', 'stock', 'NASDAQ', 'USD', 'USD', 'yahoo'),

    -- US ETFs (Yahoo)
    ('SPY', 'SPDR S&P 500 ETF Trust', 'etf', 'NYSE Arca', 'USD', 'USD', 'yahoo'),
    ('QQQ', 'Invesco QQQ Trust (Nasdaq-100)', 'etf', 'NASDAQ', 'USD', 'USD', 'yahoo'),
    ('DIA', 'SPDR Dow Jones Industrial Average ETF', 'etf', 'NYSE Arca', 'USD', 'USD', 'yahoo'),
    ('IWM', 'iShares Russell 2000 ETF', 'etf', 'NYSE Arca', 'USD', 'USD', 'yahoo'),

    -- Cryptocurrencies (Binance)
    ('BTCUSDT', 'Bitcoin / Tether USD', 'crypto', 'BINANCE', 'BTC', 'USDT', 'binance'),
    ('ETHUSDT', 'Ethereum / Tether USD', 'crypto', 'BINANCE', 'ETH', 'USDT', 'binance'),
    ('BNBUSDT', 'BNB / Tether USD', 'crypto', 'BINANCE', 'BNB', 'USDT', 'binance'),
    ('SOLUSDT', 'Solana / Tether USD', 'crypto', 'BINANCE', 'SOL', 'USDT', 'binance'),
    ('XRPUSDT', 'Ripple / Tether USD', 'crypto', 'BINANCE', 'XRP', 'USDT', 'binance'),

    -- Colombian Equities (BVC)
    ('ECOPETROL', 'Ecopetrol S.A.', 'stock', 'BVC', 'COP', 'COP', 'bvc'),
    ('PFBCOLO', 'Bancolombia S.A. Preferencial', 'stock', 'BVC', 'COP', 'COP', 'bvc'),
    ('ISA', 'Interconexión Eléctrica S.A.', 'stock', 'BVC', 'COP', 'COP', 'bvc'),
    ('GEB', 'Grupo Energía Bogotá', 'stock', 'BVC', 'COP', 'COP', 'bvc')
ON CONFLICT (symbol) DO NOTHING;
