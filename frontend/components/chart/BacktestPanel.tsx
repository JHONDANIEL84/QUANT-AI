"use client";

/**
 * BacktestPanel.tsx — Fase 9 QUANT AI
 *
 * Laboratorio de Backtesting Cuantitativo Causal (Walk-Forward).
 * Características:
 *   - Ejecución sin sesgo de anticipación (no look-ahead bias).
 *   - Simulación con capital inicial en Pesos Colombianos (COP).
 *   - Fricciones de mercado modeladas (comisión y slippage).
 *   - Selección de estrategias: SMC + Liquidity, EMA + RSI Trend.
 *   - Métricas de desempeño completas: Win Rate, Profit Factor, Max Drawdown, Sharpe, Expectancy.
 *   - Visualización de curva de equity y registro histórico de trades.
 *   - Separación epistémica: Observación (hechos) vs Hipótesis de robustez.
 */

import React, { useState, useCallback } from "react";
import {
  FlaskConical,
  Play,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Eye,
  Lightbulb,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  BarChart2,
  List,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type StrategyName = "smc_liquidity" | "ema_rsi_trend";
type ExitReason = "stop_loss" | "take_profit" | "signal_reversal" | "trailing_stop" | "timeout" | "end_of_data";

interface BacktestTrade {
  trade_id: number;
  symbol: string;
  direction: string;
  entry_bar_idx: number;
  exit_bar_idx: number;
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  units: number;
  commission_cop: number;
  slippage_cop: number;
  gross_pnl_cop: number;
  net_pnl_cop: number;
  pnl_percent: number;
  r_multiple: number | null;
  is_winner: boolean;
  exit_reason: ExitReason;
  holding_bars: number;
}

interface BacktestConfig {
  symbol: string;
  interval: string;
  initial_capital_cop: number;
  risk_per_trade_pct: number;
  max_holding_bars: number;
  commission_pct: number;
  slippage_pct: number;
  strategy_name: StrategyName;
  strategy_params: Record<string, unknown>;
  usd_cop_rate?: number;
}

interface BacktestResult {
  config: BacktestConfig;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  initial_capital_cop: number;
  final_equity_cop: number;
  gross_profit_cop: number;
  gross_loss_cop: number;
  net_profit_cop: number;
  net_profit_percent: number;
  profit_factor: number;
  expectancy_cop: number;
  cagr_percent: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown_pct: number;
  max_drawdown_cop: number;
  avg_trade_duration_bars: number;
  equity_curve: number[];
  trades: BacktestTrade[];
  observation: string;
  hypothesis: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCOP(val: number): string {
  return val.toLocaleString("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

function ExitBadge({ reason }: { reason: ExitReason }) {
  const map: Record<ExitReason, { label: string; cls: string }> = {
    stop_loss: { label: "Stop Loss", cls: "bg-red-500/20 text-red-400 border-red-500/30" },
    take_profit: { label: "Take Profit", cls: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
    signal_reversal: { label: "Reversa", cls: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
    trailing_stop: { label: "Trailing", cls: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
    timeout: { label: "Timeout", cls: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30" },
    end_of_data: { label: "Fin Datos", cls: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
  };
  const cfg = map[reason] || { label: reason, cls: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30" };
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Mini Equity Sparkline
// ---------------------------------------------------------------------------

function MiniEquityChart({ points }: { points: number[] }) {
  if (points.length < 2) return null;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const w = 400;
  const h = 50;

  const path = points
    .map((p, i) => {
      const x = (i / (points.length - 1)) * w;
      const y = h - ((p - min) / range) * (h - 8) - 4;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");

  const isProfitable = points[points.length - 1] >= points[0];
  const strokeColor = isProfitable ? "#10b981" : "#ef4444";

  return (
    <div className="bg-zinc-800/80 p-2 rounded-lg border border-zinc-700/60">
      <div className="flex justify-between items-center text-xs text-zinc-400 mb-1">
        <span>Curva de Equity (COP)</span>
        <span className={isProfitable ? "text-emerald-400 font-mono" : "text-red-400 font-mono"}>
          {formatCOP(points[points.length - 1])}
        </span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-12 overflow-visible">
        <path d={path} fill="none" stroke={strokeColor} strokeWidth="1.5" />
      </svg>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface BacktestPanelProps {
  defaultSymbol?: string;
  defaultInterval?: string;
}

export default function BacktestPanel({ defaultSymbol = "BTCUSDT", defaultInterval = "1d" }: BacktestPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BacktestResult | null>(null);

  // Form State
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [interval, setInterval] = useState(defaultInterval);
  const [strategy, setStrategy] = useState<StrategyName>("smc_liquidity");
  const [capital, setCapital] = useState("50000000");
  const [riskPct, setRiskPct] = useState("1.5");
  const [maxHolding, setMaxHolding] = useState("60");
  const [commissionPct, setCommissionPct] = useState("0.1");
  const [slippagePct, setSlippagePct] = useState("0.05");
  const [limitBars, setLimitBars] = useState("300");

  const runBacktest = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        config: {
          symbol: symbol.trim().toUpperCase(),
          interval,
          initial_capital_cop: parseFloat(capital),
          risk_per_trade_pct: parseFloat(riskPct),
          max_holding_bars: parseInt(maxHolding, 10),
          commission_pct: parseFloat(commissionPct) / 100.0,
          slippage_pct: parseFloat(slippagePct) / 100.0,
          strategy_name: strategy,
          strategy_params: strategy === "ema_rsi_trend" ? { fast_ema: 20, slow_ema: 50, rsi_period: 14 } : { rr_multiplier: 3.0, k_fractal: 3 },
        },
        limit_bars: parseInt(limitBars, 10),
      };

      const res = await fetch("/api/v1/backtest/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Error ${res.status}`);
      }

      const data: BacktestResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido al ejecutar backtest");
    } finally {
      setLoading(false);
    }
  }, [symbol, interval, strategy, capital, riskPct, maxHolding, commissionPct, slippagePct, limitBars]);

  return (
    <div className="border border-zinc-700/60 rounded-xl bg-zinc-900/80 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between p-3 hover:bg-zinc-800/60 transition-colors"
      >
        <div className="flex items-center gap-2">
          <FlaskConical className="w-4 h-4 text-emerald-400" />
          <span className="text-sm font-semibold text-emerald-400">
            Laboratorio de Backtesting Cuantitativo (Walk-Forward)
          </span>
          {result && (
            <span
              className={`ml-2 px-1.5 py-0.5 rounded text-xs font-mono font-bold ${
                result.net_profit_cop >= 0
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "bg-red-500/20 text-red-400"
              }`}
            >
              {result.net_profit_percent >= 0 ? "+" : ""}
              {result.net_profit_percent.toFixed(2)}% | {result.total_trades} trades
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-zinc-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-zinc-500" />
        )}
      </button>

      {expanded && (
        <div className="p-3 space-y-4 border-t border-zinc-700/60">
          {/* Simulation Settings */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {/* Symbol */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Símbolo</label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            {/* Interval */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Temporalidad</label>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-emerald-500"
              >
                <option value="1d">1 Día (1D)</option>
                <option value="4h">4 Horas (4H)</option>
                <option value="1h">1 Hora (1H)</option>
              </select>
            </div>

            {/* Strategy */}
            <div className="col-span-2">
              <label className="text-xs text-zinc-500 mb-1 block">Estrategia Cuantitativa</label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value as StrategyName)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-emerald-500 font-medium"
              >
                <option value="smc_liquidity">SMC + Barridos de Liquidez (Order Blocks & Sweeps)</option>
                <option value="ema_rsi_trend">Tendencial EMA 20/50 + Momentum RSI</option>
              </select>
            </div>

            {/* Capital */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Capital Inicial (COP)</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(e.target.value)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            {/* Risk % */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Riesgo / Trade %</label>
              <input
                type="number"
                value={riskPct}
                onChange={(e) => setRiskPct(e.target.value)}
                step="0.5"
                min="0.5"
                max="5"
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            {/* Commission % */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Comisión %</label>
              <input
                type="number"
                value={commissionPct}
                onChange={(e) => setCommissionPct(e.target.value)}
                step="0.01"
                min="0"
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            {/* Slippage % */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Slippage %</label>
              <input
                type="number"
                value={slippagePct}
                onChange={(e) => setSlippagePct(e.target.value)}
                step="0.01"
                min="0"
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>
          </div>

          {/* Action Button */}
          <button
            onClick={runBacktest}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-sm text-white font-semibold transition-colors"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-current" />
            )}
            Ejecutar Simulación Causal Walk-Forward
          </button>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-4 pt-2">
              {/* Performance Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-0.5">Retorno Neto (COP)</p>
                  <p
                    className={`font-mono font-bold text-sm ${
                      result.net_profit_cop >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {formatCOP(result.net_profit_cop)}
                  </p>
                  <p className="text-[10px] text-zinc-400">
                    {result.net_profit_percent >= 0 ? "+" : ""}
                    {result.net_profit_percent.toFixed(2)}%
                  </p>
                </div>

                <div className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-0.5">Win Rate</p>
                  <p className="font-mono font-bold text-white text-sm">
                    {(result.win_rate * 100).toFixed(1)}%
                  </p>
                  <p className="text-[10px] text-zinc-400">
                    {result.winning_trades}W / {result.losing_trades}L ({result.total_trades} total)
                  </p>
                </div>

                <div className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-0.5">Profit Factor</p>
                  <p
                    className={`font-mono font-bold text-sm ${
                      result.profit_factor >= 1.5
                        ? "text-emerald-400"
                        : result.profit_factor >= 1.0
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {result.profit_factor.toFixed(2)}
                  </p>
                  <p className="text-[10px] text-zinc-400">
                    E: {formatCOP(result.expectancy_cop)} / trade
                  </p>
                </div>

                <div className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-0.5">Max Drawdown</p>
                  <p className="font-mono font-bold text-red-400 text-sm">
                    -{result.max_drawdown_pct.toFixed(2)}%
                  </p>
                  <p className="text-[10px] text-zinc-400">
                    {formatCOP(result.max_drawdown_cop)}
                  </p>
                </div>
              </div>

              {/* Secondary Ratios */}
              <div className="grid grid-cols-3 gap-2 text-center bg-zinc-800/40 p-2 rounded-lg border border-zinc-700/60">
                <div>
                  <span className="text-[10px] text-zinc-500 block">Sharpe Ratio</span>
                  <span className="font-mono text-xs font-semibold text-zinc-200">
                    {result.sharpe_ratio.toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-500 block">Sortino Ratio</span>
                  <span className="font-mono text-xs font-semibold text-zinc-200">
                    {result.sortino_ratio.toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-500 block">Calmar Ratio</span>
                  <span className="font-mono text-xs font-semibold text-zinc-200">
                    {result.calmar_ratio.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Equity Curve Mini-Chart */}
              <MiniEquityChart points={result.equity_curve} />

              {/* Epistemic: Observation (Facts) */}
              <div className="p-2.5 bg-blue-500/5 border border-blue-500/20 rounded-md">
                <div className="flex items-center gap-1.5 mb-1">
                  <Eye className="w-3 h-3 text-blue-400" />
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wide">
                    Observación (Hechos Verificados)
                  </span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed">{result.observation}</p>
              </div>

              {/* Epistemic: Hypothesis (Robustness & Invalidation) */}
              <div className="p-2.5 bg-amber-500/5 border border-amber-500/20 rounded-md">
                <div className="flex items-center gap-1.5 mb-1">
                  <Lightbulb className="w-3 h-3 text-amber-400" />
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">
                    Hipótesis de Robustez Cuantitativa
                  </span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed">{result.hypothesis}</p>
              </div>

              {/* Trades Log */}
              {result.trades.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2 text-xs font-semibold text-zinc-400">
                    <List className="w-3.5 h-3.5 text-zinc-400" />
                    <span>Registro de Operaciones ({result.trades.length})</span>
                  </div>
                  <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                    {result.trades.map((t) => (
                      <div
                        key={t.trade_id}
                        className="flex items-center justify-between text-xs p-2 rounded bg-zinc-800/70 border border-zinc-700/50"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-mono font-bold uppercase text-[10px] px-1 rounded ${
                              t.direction === "long" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                            }`}
                          >
                            {t.direction}
                          </span>
                          <span className="text-zinc-400 text-[11px] font-mono">
                            {t.entry_price.toFixed(2)} → {t.exit_price.toFixed(2)}
                          </span>
                          <ExitBadge reason={t.exit_reason} />
                        </div>
                        <div className="flex items-center gap-3">
                          {t.r_multiple !== null && (
                            <span className="font-mono text-zinc-400 text-[10px]">
                              {t.r_multiple > 0 ? "+" : ""}{t.r_multiple.toFixed(1)}R
                            </span>
                          )}
                          <span
                            className={`font-mono font-bold text-xs ${
                              t.net_pnl_cop >= 0 ? "text-emerald-400" : "text-red-400"
                            }`}
                          >
                            {t.net_pnl_cop >= 0 ? "+" : ""}{formatCOP(t.net_pnl_cop)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
