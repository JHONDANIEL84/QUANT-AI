"use client";

import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  Activity,
  Layers,
  Globe2,
  RefreshCw,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Database,
  BarChart2,
  Percent,
} from "lucide-react";
import {
  fetchTicker,
  fetchMarketBars,
  fetchOrderBook,
  fetchMacroIndicators,
} from "@/services/api";
import {
  TickerSnapshot,
  MarketBar,
  OrderBookDepth,
  MacroIndicator,
} from "@/types/market";
import { formatCOP, formatUSD } from "@/lib/utils";

const SAMPLE_ASSETS = [
  { symbol: "BTCUSDT", name: "Bitcoin", market: "crypto", provider: "Binance Public" },
  { symbol: "ETHUSDT", name: "Ethereum", market: "crypto", provider: "Binance Public" },
  { symbol: "AAPL", name: "Apple Inc.", market: "stock", provider: "Yahoo Finance" },
  { symbol: "NVDA", name: "NVIDIA Corp.", market: "stock", provider: "Yahoo Finance" },
  { symbol: "SPY", name: "S&P 500 ETF", market: "etf", provider: "Yahoo Finance" },
  { symbol: "ECOPETROL", name: "Ecopetrol S.A.", market: "bvc", provider: "BVC CSV" },
  { symbol: "PFBCOLO", name: "Bancolombia Pref.", market: "bvc", provider: "BVC CSV" },
];

export function MarketDataExplorer() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>("BTCUSDT");
  const [ticker, setTicker] = useState<TickerSnapshot | null>(null);
  const [bars, setBars] = useState<MarketBar[]>([]);
  const [orderBook, setOrderBook] = useState<OrderBookDepth | null>(null);
  const [macroIndicators, setMacroIndicators] = useState<MacroIndicator[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadMarketData = async (symbol: string) => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Fetch Ticker
      const tickerData = await fetchTicker(symbol).catch(() => null);
      setTicker(tickerData);

      // 2. Fetch Bars
      const barsData = await fetchMarketBars(symbol, "1d", 10).catch(() => []);
      setBars(barsData);

      // 3. Fetch Order Book if Crypto
      if (symbol.endsWith("USDT")) {
        const obData = await fetchOrderBook(symbol, 8).catch(() => null);
        setOrderBook(obData);
      } else {
        setOrderBook(null);
      }

      // 4. Fetch Macro Indicators
      const macroData = await fetchMacroIndicators("CO").catch(() => []);
      setMacroIndicators(macroData);
    } catch (err: any) {
      setError(err?.message || "Error al consultar los proveedores de mercado.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMarketData(selectedSymbol);
  }, [selectedSymbol]);

  const formatPrice = (val: number, currency: string) => {
    if (currency === "COP") return formatCOP(val);
    return formatUSD(val);
  };

  return (
    <div className="space-y-6">
      {/* Asset Selector Tabs */}
      <div className="rounded-xl border border-border bg-surface p-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div className="flex items-center space-x-2">
            <Activity className="h-4 w-4 text-quant-cyan" />
            <h3 className="font-mono text-sm font-semibold text-white tracking-wide uppercase">
              EXPLORADOR DE MERCADOS MULTIPROVEEDOR (FASE 2)
            </h3>
          </div>
          <button
            onClick={() => loadMarketData(selectedSymbol)}
            disabled={isLoading}
            className="flex items-center space-x-1.5 self-start sm:self-auto rounded-lg border border-border-light bg-surface-card px-3 py-1.5 text-xs font-mono text-white hover:bg-surface-hover transition-all"
          >
            <RefreshCw className={`h-3.5 w-3.5 text-quant-cyan ${isLoading ? "animate-spin" : ""}`} />
            <span>Refrescar</span>
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {SAMPLE_ASSETS.map((asset) => {
            const isSelected = selectedSymbol === asset.symbol;
            return (
              <button
                key={asset.symbol}
                onClick={() => setSelectedSymbol(asset.symbol)}
                className={`flex items-center space-x-2 rounded-lg border px-3 py-2 text-xs font-mono transition-all ${
                  isSelected
                    ? "border-quant-cyan bg-quant-cyan/10 text-white shadow-lg shadow-quant-cyan/10"
                    : "border-border bg-surface-card text-gray-400 hover:border-border-light hover:text-gray-200"
                }`}
              >
                <span className="font-bold">{asset.symbol}</span>
                <span className="text-[10px] text-gray-500">• {asset.provider}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Ticker Overview + Order Book or Macro */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Ticker Summary & OHLCV Bars */}
        <div className="lg:col-span-2 space-y-4">
          {/* Ticker Snapshot Card */}
          <div className="rounded-xl border border-border bg-surface p-5 shadow-xl">
            {ticker ? (
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h2 className="font-mono text-2xl font-extrabold text-white">
                        {ticker.symbol}
                      </h2>
                      <span className="rounded bg-surface-card border border-border px-2 py-0.5 font-mono text-[11px] text-quant-cyan uppercase">
                        {ticker.source.toUpperCase()}
                      </span>
                      <span
                        className={`rounded px-2 py-0.5 font-mono text-[10px] font-semibold uppercase ${
                          ticker.data_status === "realtime"
                            ? "bg-quant-green/20 text-quant-green border border-quant-green/40"
                            : "bg-quant-amber/20 text-quant-amber border border-quant-amber/40"
                        }`}
                      >
                        {ticker.data_status}
                      </span>
                    </div>
                    <div className="mt-2 flex items-baseline space-x-3">
                      <span className="font-mono text-3xl font-black text-white">
                        {formatPrice(ticker.price, ticker.currency)}
                      </span>
                      <span
                        className={`flex items-center font-mono text-sm font-semibold ${
                          ticker.change_24h >= 0 ? "text-quant-green" : "text-quant-red"
                        }`}
                      >
                        {ticker.change_24h >= 0 ? (
                          <ArrowUpRight className="h-4 w-4 mr-0.5" />
                        ) : (
                          <ArrowDownRight className="h-4 w-4 mr-0.5" />
                        )}
                        {ticker.change_24h_percent.toFixed(2)}% ({ticker.change_24h >= 0 ? "+" : ""}
                        {ticker.change_24h.toFixed(2)} {ticker.currency})
                      </span>
                    </div>
                  </div>

                  <div className="text-right text-xs text-gray-400 font-mono">
                    <div>Mercado: <span className="text-white uppercase">{ticker.market}</span></div>
                    <div>Moneda: <span className="text-quant-amber">{ticker.currency}</span></div>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-3 border-t border-border pt-3 text-xs font-mono text-gray-400">
                  <div>
                    <span className="text-gray-500">Máx 24h:</span>{" "}
                    <span className="text-white font-medium">
                      {ticker.high_24h ? formatPrice(ticker.high_24h, ticker.currency) : "N/D"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Mín 24h:</span>{" "}
                    <span className="text-white font-medium">
                      {ticker.low_24h ? formatPrice(ticker.low_24h, ticker.currency) : "N/D"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Volumen 24h:</span>{" "}
                    <span className="text-white font-medium">
                      {ticker.volume_24h ? ticker.volume_24h.toLocaleString("es-CO") : "N/D"}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-xs font-mono text-gray-500">
                Cargando datos del activo...
              </div>
            )}
          </div>

          {/* Historical Normalized Bars Table */}
          <div className="rounded-xl border border-border bg-surface p-5 shadow-xl">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-border">
              <h4 className="font-mono text-xs font-semibold text-gray-300 uppercase flex items-center space-x-1.5">
                <BarChart2 className="h-4 w-4 text-quant-cyan" />
                <span>ÚLTIMAS VELAS NORMALIZADAS (OHLCV)</span>
              </h4>
              <span className="text-[11px] font-mono text-gray-500">
                Intervalo: 1D • Fuente: {ticker?.source.toUpperCase() || "N/D"}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-border text-gray-500">
                    <th className="py-2">Fecha (UTC)</th>
                    <th className="py-2">Apertura</th>
                    <th className="py-2">Máximo</th>
                    <th className="py-2">Mínimo</th>
                    <th className="py-2">Cierre</th>
                    <th className="py-2 text-right">Volumen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50 text-gray-300">
                  {bars.slice(-6).map((b, idx) => (
                    <tr key={idx} className="hover:bg-surface-hover/50">
                      <td className="py-2 text-gray-400">
                        {new Date(b.timestamp).toLocaleDateString("es-CO")}
                      </td>
                      <td className="py-2">{b.open.toFixed(2)}</td>
                      <td className="py-2 text-quant-green">{b.high.toFixed(2)}</td>
                      <td className="py-2 text-quant-red">{b.low.toFixed(2)}</td>
                      <td className={`py-2 font-bold ${b.close >= b.open ? "text-quant-green" : "text-quant-red"}`}>
                        {b.close.toFixed(2)}
                      </td>
                      <td className="py-2 text-right text-gray-400">
                        {b.volume.toLocaleString("es-CO")}
                      </td>
                    </tr>
                  ))}
                  {bars.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-4 text-center text-gray-500">
                        No hay velas disponibles para mostrar.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Order Book Depth or Macro Panel */}
        <div className="space-y-4">
          {/* Order Book Depth (Crypto only) */}
          {orderBook ? (
            <div className="rounded-xl border border-border bg-surface p-5 shadow-xl">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-border">
                <div className="flex items-center space-x-1.5">
                  <Layers className="h-4 w-4 text-quant-purple" />
                  <h4 className="font-mono text-xs font-semibold text-gray-300 uppercase">
                    LIBRO DE ÓRDENES & DESEQUILIBRIO
                  </h4>
                </div>
                <span className="font-mono text-[10px] text-quant-green">EN VIVO</span>
              </div>

              {/* Imbalance Ratio Meter */}
              <div className="mb-4 rounded-lg border border-border bg-surface-card p-3">
                <div className="flex justify-between text-[11px] font-mono mb-1">
                  <span className="text-gray-400">Desequilibrio Bid/Ask:</span>
                  <span
                    className={`font-bold ${
                      orderBook.imbalance_ratio >= 0 ? "text-quant-green" : "text-quant-red"
                    }`}
                  >
                    {(orderBook.imbalance_ratio * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-border overflow-hidden flex">
                  <div
                    className="h-full bg-quant-green transition-all"
                    style={{
                      width: `${Math.max(10, Math.min(90, (orderBook.imbalance_ratio + 1) * 50))}%`,
                    }}
                  />
                  <div
                    className="h-full bg-quant-red transition-all"
                    style={{
                      width: `${Math.max(10, Math.min(90, (1 - orderBook.imbalance_ratio) * 50))}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-gray-500 mt-1">
                  <span>Bids: {orderBook.total_bid_volume}</span>
                  <span>Asks: {orderBook.total_ask_volume}</span>
                </div>
              </div>

              {/* Order Book Tables */}
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                {/* Bids */}
                <div>
                  <div className="text-[10px] font-bold text-quant-green mb-1 border-b border-quant-green/30 pb-0.5">
                    BIDS (COMPRA)
                  </div>
                  {orderBook.bids.slice(0, 5).map((b, i) => (
                    <div key={i} className="flex justify-between py-0.5 text-gray-300">
                      <span className="text-quant-green">{b.price.toFixed(1)}</span>
                      <span className="text-gray-400">{b.quantity.toFixed(3)}</span>
                    </div>
                  ))}
                </div>

                {/* Asks */}
                <div>
                  <div className="text-[10px] font-bold text-quant-red mb-1 border-b border-quant-red/30 pb-0.5">
                    ASKS (VENTA)
                  </div>
                  {orderBook.asks.slice(0, 5).map((a, i) => (
                    <div key={i} className="flex justify-between py-0.5 text-gray-300">
                      <span className="text-quant-red">{a.price.toFixed(1)}</span>
                      <span className="text-gray-400">{a.quantity.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-surface p-5 shadow-xl">
              <div className="flex items-center space-x-1.5 mb-3 pb-2 border-b border-border">
                <Globe2 className="h-4 w-4 text-quant-amber" />
                <h4 className="font-mono text-xs font-semibold text-gray-300 uppercase">
                  INDICADORES MACROECONÓMICOS OFICIALES
                </h4>
              </div>

              <div className="space-y-3">
                {macroIndicators.map((ind, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-border bg-surface-card p-2.5 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-mono text-[11px] font-medium text-white">
                        {ind.name}
                      </div>
                      <div className="text-[10px] font-mono text-gray-500">
                        {ind.source.toUpperCase()} • Período: {ind.period}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-sm font-bold text-quant-cyan">
                        {ind.value.toLocaleString("es-CO")}
                      </span>
                      <span className="ml-1 text-[10px] font-mono text-gray-400">
                        {ind.unit}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
