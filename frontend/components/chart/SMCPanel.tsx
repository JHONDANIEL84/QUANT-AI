"use client";

/**
 * SMCPanel — Phase 5 Frontend Component (Smart Money Concepts)
 * Visualizes institutional Order Blocks, Fair Value Gaps (FVG),
 * BOS (Break of Structure), CHOCH (Change of Character),
 * and Premium vs. Discount Dealing Range.
 *
 * Strictly causal data labeled with observation vs hypothesis.
 */

import React, { useState, useEffect } from "react";
import {
  Layers,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Zap,
  Target,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Compass,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StructureBreak {
  break_type: string;
  direction: string;
  broken_pivot_price: number;
  breaking_bar_index: number;
  breaking_bar_timestamp: string;
  breaking_price: number;
  invalidation_level: number;
  rule_applied: string;
}

interface OrderBlock {
  direction: string;
  bar_index: number;
  timestamp: string;
  top_price: number;
  bottom_price: number;
  body_top: number;
  body_bottom: number;
  status: string;
  mitigated_at: string | null;
  mitigated_bar_index: number | null;
  is_breaker: boolean;
  quality_score: number;
  volume: number;
  rule_applied: string;
}

interface FairValueGap {
  direction: string;
  bar_index: number;
  timestamp: string;
  top_price: number;
  bottom_price: number;
  gap_size: number;
  consequent_encroachment: number;
  status: string;
  mitigated_pct: number;
  mitigated_at: string | null;
  rule_applied: string;
}

interface PremiumDiscount {
  swing_high: number;
  swing_low: number;
  equilibrium: number;
  current_price: number;
  current_position_pct: number;
  zone: string;
  observation: string;
}

interface SMCResponse {
  symbol: string;
  interval: string;
  bars_analyzed: number;
  structure_breaks: StructureBreak[];
  order_blocks: OrderBlock[];
  fair_value_gaps: FairValueGap[];
  premium_discount: PremiumDiscount | null;
  observation: string;
  hypothesis: string;
  data_status: string;
}

export interface SMCPanelProps {
  symbol?: string;
  interval?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchSMCAnalysis(symbol: string, interval: string): Promise<SMCResponse> {
  const url = `${API_BASE}/api/v1/smc/analysis?symbol=${encodeURIComponent(symbol)}&interval=${interval}&limit=200`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Error al obtener análisis SMC");
  }
  return res.json();
}

function formatPrice(price: number): string {
  return price.toLocaleString("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

const TABS = ["Order Blocks & Breakers", "Fair Value Gaps (FVG)", "BOS & CHOCH", "Premium / Discount"] as const;

export default function SMCPanel({
  symbol = "BTCUSDT",
  interval = "1d",
}: SMCPanelProps) {
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>(TABS[0]);
  const [data, setData] = useState<SMCResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchSMCAnalysis(symbol, interval)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol, interval]);

  return (
    <section className="bg-surface border border-border rounded-xl overflow-hidden shadow-xl mt-4">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-border bg-surface-card/60">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-quant-purple animate-pulse" />
          <h2 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <span>SMART MONEY CONCEPTS (SMC)</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-quant-purple/20 text-quant-purple border border-quant-purple/40">
              FASE 5
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
                  ? "bg-quant-purple text-white font-semibold shadow-md shadow-quant-purple/20"
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
          <div className="flex items-center justify-center py-12 text-xs font-mono text-quant-purple space-x-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Calculando zonas institucionales (OB, FVG, BOS, CHOCH)...</span>
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
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>HECHOS OBSERVADOS (DATOS VERIFICADOS)</span>
                </div>
                <p className="text-gray-300 leading-relaxed font-sans text-xs">
                  {data.observation}
                </p>
              </div>

              <div className="rounded-lg border border-quant-purple/30 bg-quant-purple/5 p-3">
                <div className="flex items-center gap-1.5 text-quant-purple font-bold mb-1">
                  <Target className="h-3.5 w-3.5" />
                  <span>HIPÓTESIS CUANTITATIVA (SUJETA A INVALIDACIÓN)</span>
                </div>
                <p className="text-gray-300 leading-relaxed font-sans text-xs">
                  {data.hypothesis}
                </p>
              </div>
            </div>

            {/* 2. Tab Contents */}
            {activeTab === "Order Blocks & Breakers" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Total identificados: {data.order_blocks.length}</span>
                  <div className="flex gap-2">
                    <span className="flex items-center gap-1 text-[11px] text-quant-green">
                      <span className="w-2 h-2 rounded-full bg-quant-green" /> Bullish (Demand)
                    </span>
                    <span className="flex items-center gap-1 text-[11px] text-quant-red">
                      <span className="w-2 h-2 rounded-full bg-quant-red" /> Bearish (Supply)
                    </span>
                    <span className="flex items-center gap-1 text-[11px] text-quant-amber">
                      <span className="w-2 h-2 rounded-full bg-quant-amber" /> Breaker Block
                    </span>
                  </div>
                </div>

                {data.order_blocks.length === 0 ? (
                  <p className="text-xs text-gray-500 py-6 text-center">No se detectaron Order Blocks en el rango actual.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead>
                        <tr className="border-b border-border text-gray-500 font-mono">
                          <th className="py-2 px-3">TIPO</th>
                          <th className="py-2 px-3">DIRECCIÓN</th>
                          <th className="py-2 px-3">RANGO DE PRECIO</th>
                          <th className="py-2 px-3">CUERPO</th>
                          <th className="py-2 px-3">ESTADO</th>
                          <th className="py-2 px-3 text-right">SCORE</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50">
                        {data.order_blocks.slice(-15).reverse().map((ob, idx) => {
                          const isBull = ob.direction === "BULLISH";
                          return (
                            <tr key={idx} className="hover:bg-surface-card/40 transition-colors">
                              <td className="py-2.5 px-3 font-mono">
                                {ob.is_breaker ? (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-quant-amber/20 text-quant-amber border border-quant-amber/40">
                                    BREAKER
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-surface text-gray-300 border border-border">
                                    ORDER BLOCK
                                  </span>
                                )}
                              </td>
                              <td className="py-2.5 px-3 font-mono">
                                <span className={`inline-flex items-center gap-1 font-semibold ${isBull ? "text-quant-green" : "text-quant-red"}`}>
                                  {isBull ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                  {ob.direction}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 font-mono text-white">
                                [{formatPrice(ob.bottom_price)} — {formatPrice(ob.top_price)}]
                              </td>
                              <td className="py-2.5 px-3 font-mono text-gray-400 text-[11px]">
                                [{formatPrice(ob.body_bottom)} — {formatPrice(ob.body_top)}]
                              </td>
                              <td className="py-2.5 px-3 font-mono">
                                <span className={`px-2 py-0.5 rounded text-[10px] ${
                                  ob.status === "UNMITIGATED"
                                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                    : ob.status === "MITIGATED"
                                    ? "bg-gray-500/10 text-gray-400 border border-gray-500/30"
                                    : "bg-red-500/10 text-red-400 border border-red-500/30"
                                }`}>
                                  {ob.status}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 font-mono text-right font-bold text-quant-cyan">
                                {ob.quality_score.toFixed(0)} pts
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

            {activeTab === "Fair Value Gaps (FVG)" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>FVGs detectados: {data.fair_value_gaps.length}</span>
                  <span className="text-[11px] font-mono text-gray-500">Consequent Encroachment = 50% del Gap</span>
                </div>

                {data.fair_value_gaps.length === 0 ? (
                  <p className="text-xs text-gray-500 py-6 text-center">No se detectaron Fair Value Gaps en el rango actual.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead>
                        <tr className="border-b border-border text-gray-500 font-mono">
                          <th className="py-2 px-3">DIRECCIÓN</th>
                          <th className="py-2 px-3">RANGO GAP</th>
                          <th className="py-2 px-3">CE (50%)</th>
                          <th className="py-2 px-3">TAMAÑO</th>
                          <th className="py-2 px-3">MITIGACIÓN</th>
                          <th className="py-2 px-3">ESTADO</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50">
                        {data.fair_value_gaps.slice(-15).reverse().map((fvg, idx) => {
                          const isBull = fvg.direction === "BULLISH";
                          return (
                            <tr key={idx} className="hover:bg-surface-card/40 transition-colors">
                              <td className="py-2.5 px-3 font-mono">
                                <span className={`inline-flex items-center gap-1 font-semibold ${isBull ? "text-quant-green" : "text-quant-red"}`}>
                                  {isBull ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                  {fvg.direction}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 font-mono text-white">
                                [{formatPrice(fvg.bottom_price)} — {formatPrice(fvg.top_price)}]
                              </td>
                              <td className="py-2.5 px-3 font-mono text-quant-amber font-semibold">
                                {formatPrice(fvg.consequent_encroachment)}
                              </td>
                              <td className="py-2.5 px-3 font-mono text-gray-400">
                                {formatPrice(fvg.gap_size)}
                              </td>
                              <td className="py-2.5 px-3 font-mono">
                                <div className="w-24 bg-surface rounded-full h-1.5 overflow-hidden border border-border">
                                  <div
                                    className={`h-full ${fvg.mitigated_pct >= 100 ? "bg-gray-500" : isBull ? "bg-quant-green" : "bg-quant-red"}`}
                                    style={{ width: `${Math.min(100, fvg.mitigated_pct)}%` }}
                                  />
                                </div>
                                <span className="text-[10px] text-gray-400 mt-0.5 block">
                                  {fvg.mitigated_pct.toFixed(0)}% llenado
                                </span>
                              </td>
                              <td className="py-2.5 px-3 font-mono">
                                <span className={`px-2 py-0.5 rounded text-[10px] ${
                                  fvg.status === "UNMITIGATED"
                                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                    : fvg.status === "PARTIAL"
                                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                    : "bg-gray-500/10 text-gray-400 border border-gray-500/30"
                                }`}>
                                  {fvg.status}
                                </span>
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

            {activeTab === "BOS & CHOCH" && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Rupturas estructurales: {data.structure_breaks.length}</span>
                  <div className="flex gap-2">
                    <span className="flex items-center gap-1 text-[11px] text-quant-purple">
                      <span className="w-2 h-2 rounded-full bg-quant-purple" /> CHOCH (Cambio de Carácter)
                    </span>
                    <span className="flex items-center gap-1 text-[11px] text-quant-cyan">
                      <span className="w-2 h-2 rounded-full bg-quant-cyan" /> BOS (Continuación)
                    </span>
                  </div>
                </div>

                {data.structure_breaks.length === 0 ? (
                  <p className="text-xs text-gray-500 py-6 text-center">No se han registrado rupturas BOS o CHOCH en la serie analizada.</p>
                ) : (
                  <div className="space-y-2">
                    {data.structure_breaks.slice(-10).reverse().map((brk, idx) => {
                      const isChoch = brk.break_type === "CHOCH";
                      const isBull = brk.direction === "BULLISH";
                      return (
                        <div
                          key={idx}
                          className={`rounded-lg border p-3 text-xs font-mono transition-all ${
                            isChoch
                              ? "border-quant-purple/40 bg-quant-purple/5"
                              : "border-quant-cyan/30 bg-quant-cyan/5"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                isChoch
                                  ? "bg-quant-purple/20 text-quant-purple border border-quant-purple/40"
                                  : "bg-quant-cyan/20 text-quant-cyan border border-quant-cyan/40"
                              }`}>
                                {brk.break_type}
                              </span>
                              <span className={`font-semibold ${isBull ? "text-quant-green" : "text-quant-red"}`}>
                                {brk.direction}
                              </span>
                            </div>
                            <span className="text-gray-400 text-[11px]">
                              {new Date(brk.breaking_bar_timestamp).toLocaleDateString("es-CO")}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2 pt-2 border-t border-border/50 text-[11px]">
                            <div>
                              <span className="text-gray-500">Pivote Roto:</span>{" "}
                              <strong className="text-white">{formatPrice(brk.broken_pivot_price)}</strong>
                            </div>
                            <div>
                              <span className="text-gray-500">Cierre de Ruptura:</span>{" "}
                              <strong className="text-quant-cyan">{formatPrice(brk.breaking_price)}</strong>
                            </div>
                            <div>
                              <span className="text-gray-500">Nivel de Invalidación:</span>{" "}
                              <strong className="text-quant-amber">{formatPrice(brk.invalidation_level)}</strong>
                            </div>
                          </div>

                          <p className="text-[11px] text-gray-400 mt-1 font-sans">
                            {brk.rule_applied}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {activeTab === "Premium / Discount" && (
              <div className="space-y-4">
                {data.premium_discount ? (
                  <div className="rounded-xl border border-border bg-surface-card p-4 space-y-4 font-mono text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Compass className="h-4 w-4 text-quant-purple" />
                        <span className="font-semibold text-white">RANGO DE NEGOCIACIÓN INSTITUCIONAL</span>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                        data.premium_discount.zone === "PREMIUM"
                          ? "bg-red-500/20 text-red-400 border-red-500/40"
                          : data.premium_discount.zone === "DISCOUNT"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                          : "bg-amber-500/20 text-amber-400 border-amber-500/40"
                      }`}>
                        ZONA {data.premium_discount.zone}
                      </span>
                    </div>

                    {/* Progress Gauge */}
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-[11px] text-gray-400">
                        <span>DISCOUNT (0%) — Min: {formatPrice(data.premium_discount.swing_low)}</span>
                        <span className="text-quant-amber font-semibold">50% EQUILIBRIUM: {formatPrice(data.premium_discount.equilibrium)}</span>
                        <span>PREMIUM (100%) — Max: {formatPrice(data.premium_discount.swing_high)}</span>
                      </div>

                      <div className="relative w-full h-4 bg-gradient-to-r from-emerald-500/30 via-amber-500/30 to-red-500/30 rounded-full border border-border overflow-hidden">
                        {/* Equilibrium Divider line */}
                        <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-quant-amber" />
                        {/* Price marker pin */}
                        <div
                          className="absolute top-0 bottom-0 w-2.5 bg-white border border-black shadow-lg rounded-full -ml-1 transition-all duration-300"
                          style={{ left: `${Math.min(100, Math.max(0, data.premium_discount.current_position_pct))}%` }}
                        />
                      </div>

                      <div className="text-center text-xs text-white pt-1">
                        Precio Actual: <strong className="text-quant-cyan">{formatPrice(data.premium_discount.current_price)}</strong>{" "}
                        ({data.premium_discount.current_position_pct.toFixed(1)}% del rango)
                      </div>
                    </div>

                    <p className="text-xs text-gray-300 font-sans leading-relaxed pt-2 border-t border-border/50">
                      {data.premium_discount.observation}
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 py-6 text-center">Rango de dealing insuficiente para calcular Premium / Discount.</p>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
