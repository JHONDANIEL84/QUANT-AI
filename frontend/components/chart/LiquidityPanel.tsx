"use client";

/**
 * LiquidityPanel — Phase 6 Frontend Component (Liquidity Intelligence & Sweeps)
 * Visualizes Equal Highs (EQH), Equal Lows (EQL), Buy-side/Sell-side pools,
 * confirmed Liquidity Sweeps (Stop Hunts), and Session Benchmarks (PDH, PDL, PWH, PWL).
 *
 * Strictly causal data with separation between facts and hypotheses.
 */

import React, { useState, useEffect } from "react";
import {
  Droplets,
  Target,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Crosshair,
  TrendingUp,
  TrendingDown,
  Layers,
  Clock,
  Compass,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface LiquidityPool {
  pool_type: string;
  price_level: number;
  top_price: number;
  bottom_price: number;
  touch_count: number;
  first_touch_at: string;
  last_touch_at: string;
  liquidity_score: number;
  status: string;
  swept_at: string | null;
  swept_bar_index: number | null;
  sweep_penetration_pct: number;
  rule_applied: string;
}

interface LiquiditySweepEvent {
  pool_type: string;
  price_level: number;
  sweep_bar_index: number;
  sweep_timestamp: string;
  penetration_price: number;
  rejection_close: number;
  penetration_pct: number;
  invalidation_level: number;
  rule_applied: string;
}

interface SessionLevels {
  pdh: number | null;
  pdl: number | null;
  pwh: number | null;
  pwl: number | null;
}

interface LiquidityResponse {
  symbol: string;
  interval: string;
  bars_analyzed: number;
  pools: LiquidityPool[];
  sweeps: LiquiditySweepEvent[];
  session_levels: SessionLevels;
  observation: string;
  hypothesis: string;
  data_status: string;
}

export interface LiquidityPanelProps {
  symbol?: string;
  interval?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchLiquidityAnalysis(symbol: string, interval: string): Promise<LiquidityResponse> {
  const url = `${API_BASE}/api/v1/liquidity/analysis?symbol=${encodeURIComponent(symbol)}&interval=${interval}&limit=200`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Error al obtener análisis de Liquidez");
  }
  return res.json();
}

function formatPrice(price: number): string {
  return price.toLocaleString("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

const TABS = ["Pools de Liquidez (EQH/EQL)", "Barridos Confirmados (Sweeps)", "Niveles de Sesión"] as const;

export default function LiquidityPanel({
  symbol = "BTCUSDT",
  interval = "1d",
}: LiquidityPanelProps) {
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>(TABS[0]);
  const [data, setData] = useState<LiquidityResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchLiquidityAnalysis(symbol, interval)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol, interval]);

  return (
    <section className="bg-surface border border-border rounded-xl overflow-hidden shadow-xl mt-4">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-border bg-surface-card/60">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-quant-cyan animate-pulse" />
          <h2 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <span>LIQUIDITY INTELLIGENCE & SWEEPS</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-quant-cyan/20 text-quant-cyan border border-quant-cyan/40">
              FASE 6
            </span>
          </h2>
          {data && (
            <span className="text-xs font-mono text-gray-500">
              • {data.symbol} ({data.interval}) • {data.bars_analyzed} barras
            </span>
          )}
        </div>

        {/* Tab Buttons */}
        <div className="flex flex-wrap gap-1">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 text-xs rounded-lg font-mono transition-all duration-150 ${
                activeTab === tab
                  ? "bg-quant-cyan text-black font-bold shadow-md shadow-quant-cyan/20"
                  : "bg-surface hover:bg-surface-card text-gray-400 hover:text-gray-200 border border-border"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="p-4 space-y-4">
        {loading && (
          <div className="flex items-center justify-center py-12 text-xs font-mono text-quant-cyan space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Mapeando pools institucionales y detectando barridos (Sweeps)...</span>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-xs font-mono text-red-400 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && data && (
          <>
            {/* 1. Facts vs Hypotheses Dual Banner */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
              <div className="rounded-lg border border-quant-cyan/30 bg-quant-cyan/5 p-3">
                <div className="flex items-center gap-1.5 text-quant-cyan font-bold mb-1">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>HECHOS OBSERVADOS (LIQUIDEZ VERIFICADA)</span>
                </div>
                <p className="text-gray-300 leading-relaxed font-sans text-xs">
                  {data.observation}
                </p>
              </div>

              <div className="rounded-lg border border-quant-purple/30 bg-quant-purple/5 p-3">
                <div className="flex items-center gap-1.5 text-quant-purple font-bold mb-1">
                  <Target className="h-3.5 w-3.5" />
                  <span>HIPÓTESIS DE ROTACIÓN & BARRIDO (SUJETA A INVALIDACIÓN)</span>
                </div>
                <p className="text-gray-300 leading-relaxed font-sans text-xs">
                  {data.hypothesis}
                </p>
              </div>
            </div>

            {/* 2. Tab Contents */}
            {activeTab === "Pools de Liquidez (EQH/EQL)" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Pools mapeados: {data.pools.length}</span>
                  <div className="flex gap-2 text-[11px] font-mono">
                    <span className="text-quant-green">EQH / BSL = Buy-side</span>
                    <span>•</span>
                    <span className="text-quant-red">EQL / SSL = Sell-side</span>
                  </div>
                </div>

                {data.pools.length === 0 ? (
                  <p className="text-xs text-gray-500 py-6 text-center">No se detectaron pools de liquidez concentrada.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead>
                        <tr className="border-b border-border text-gray-500 font-mono">
                          <th className="py-2 px-3">TIPO</th>
                          <th className="py-2 px-3">NIVEL ANCLA</th>
                          <th className="py-2 px-3">BANDA DE TOLERANCIA</th>
                          <th className="py-2 px-3">TOQUES</th>
                          <th className="py-2 px-3">ESTADO</th>
                          <th className="py-2 px-3 text-right">SCORE LIQUIDEZ</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50">
                        {data.pools.map((p, idx) => {
                          const isBuySide = ["EQH", "BSL", "PDH", "PWH"].includes(p.pool_type);
                          return (
                            <tr key={idx} className="hover:bg-surface-card/40 transition-colors">
                              <td className="py-2.5 px-3 font-mono">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                                  p.pool_type === "EQH" || p.pool_type === "EQL"
                                    ? "bg-quant-cyan/20 text-quant-cyan border-quant-cyan/40"
                                    : "bg-surface text-gray-300 border-border"
                                }`}>
                                  {p.pool_type}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 font-mono font-semibold text-white">
                                {formatPrice(p.price_level)}
                              </td>
                              <td className="py-2.5 px-3 font-mono text-gray-400 text-[11px]">
                                [{formatPrice(p.bottom_price)} — {formatPrice(p.top_price)}]
                              </td>
                              <td className="py-2.5 px-3 font-mono text-gray-300">
                                {p.touch_count} {p.touch_count > 1 ? "toques" : "pivote"}
                              </td>
                              <td className="py-2.5 px-3 font-mono">
                                <span className={`px-2 py-0.5 rounded text-[10px] ${
                                  p.status === "ACTIVE"
                                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold"
                                    : p.status === "SWEPT"
                                    ? "bg-quant-amber/10 text-quant-amber border border-quant-amber/30"
                                    : "bg-gray-500/10 text-gray-400 border border-gray-500/30"
                                }`}>
                                  {p.status}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 font-mono text-right font-bold text-quant-cyan">
                                {p.liquidity_score.toFixed(0)} / 100
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {activeTab === "Barridos Confirmados (Sweeps)" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Barridos con rechazo confirmados: {data.sweeps.length}</span>
                  <span className="text-[11px] font-mono text-gray-500">Stop Hunt = Mecha penetra + Cierre por dentro</span>
                </div>

                {data.sweeps.length === 0 ? (
                  <p className="text-xs text-gray-500 py-6 text-center">No se han registrado barridos de liquidez con rechazo en las barras analizadas.</p>
                ) : (
                  <div className="space-y-2">
                    {data.sweeps.slice(-10).reverse().map((sw, idx) => {
                      const isBuySide = ["EQH", "BSL", "PDH", "PWH"].includes(sw.pool_type);
                      return (
                        <div
                          key={idx}
                          className="rounded-lg border border-quant-cyan/30 bg-quant-cyan/5 p-3 text-xs font-mono transition-all"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-quant-cyan/20 text-quant-cyan border border-quant-cyan/40">
                                LIQUIDITY SWEEP
                              </span>
                              <span className="font-semibold text-white">
                                {sw.pool_type} @ {formatPrice(sw.price_level)}
                              </span>
                            </div>
                            <span className="text-gray-400 text-[11px]">
                              {new Date(sw.sweep_timestamp).toLocaleDateString("es-CO")}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2 pt-2 border-t border-border/50 text-[11px]">
                            <div>
                              <span className="text-gray-500">Extremo Mecha:</span>{" "}
                              <strong className={isBuySide ? "text-quant-green" : "text-quant-red"}>
                                {formatPrice(sw.penetration_price)}
                              </strong>
                            </div>
                            <div>
                              <span className="text-gray-500">Cierre Rechazo:</span>{" "}
                              <strong className="text-white">{formatPrice(sw.rejection_close)}</strong>
                            </div>
                            <div>
                              <span className="text-gray-500">Penetración:</span>{" "}
                              <strong className="text-quant-amber">+{sw.penetration_pct}%</strong>
                            </div>
                            <div>
                              <span className="text-gray-500">Nivel Invalidación:</span>{" "}
                              <strong className="text-quant-cyan">{formatPrice(sw.invalidation_level)}</strong>
                            </div>
                          </div>

                          <p className="text-[11px] text-gray-300 mt-1 font-sans">
                            {sw.rule_applied}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {activeTab === "Niveles de Sesión" && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                  <div className="rounded-lg border border-border bg-surface-card p-3">
                    <span className="text-gray-500 text-[11px] block">PREVIOUS DAY HIGH (PDH)</span>
                    <strong className="text-base text-quant-green block mt-1">
                      {data.session_levels.pdh ? formatPrice(data.session_levels.pdh) : "N/D"}
                    </strong>
                    <span className="text-[10px] text-gray-500 mt-0.5 block">Máximo de sesión anterior</span>
                  </div>

                  <div className="rounded-lg border border-border bg-surface-card p-3">
                    <span className="text-gray-500 text-[11px] block">PREVIOUS DAY LOW (PDL)</span>
                    <strong className="text-base text-quant-red block mt-1">
                      {data.session_levels.pdl ? formatPrice(data.session_levels.pdl) : "N/D"}
                    </strong>
                    <span className="text-[10px] text-gray-500 mt-0.5 block">Mínimo de sesión anterior</span>
                  </div>

                  <div className="rounded-lg border border-border bg-surface-card p-3">
                    <span className="text-gray-500 text-[11px] block">PREVIOUS WEEK HIGH (PWH)</span>
                    <strong className="text-base text-quant-cyan block mt-1">
                      {data.session_levels.pwh ? formatPrice(data.session_levels.pwh) : "N/D"}
                    </strong>
                    <span className="text-[10px] text-gray-500 mt-0.5 block">Máximo semanal anterior</span>
                  </div>

                  <div className="rounded-lg border border-border bg-surface-card p-3">
                    <span className="text-gray-500 text-[11px] block">PREVIOUS WEEK LOW (PWL)</span>
                    <strong className="text-base text-quant-purple block mt-1">
                      {data.session_levels.pwl ? formatPrice(data.session_levels.pwl) : "N/D"}
                    </strong>
                    <span className="text-[10px] text-gray-500 mt-0.5 block">Mínimo semanal anterior</span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
