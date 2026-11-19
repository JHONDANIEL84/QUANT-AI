"use client";

/**
 * PriceActionPanel — Phase 4 Frontend Component
 * Displays candle patterns, market structure pivots, and S/R zones
 * fetched from the backend price action analysis endpoint.
 *
 * Data is always labeled with its status (observation vs hypothesis).
 * No financial calculations are performed in the frontend.
 */

import React, { useState, useEffect } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CandlePattern {
  pattern_type: string;
  direction: string;
  timestamp: string;
  bar_index: number;
  price: number;
  confirmed_at: string;
  confidence: number;
  rule_applied: string;
  invalidation_level: number;
}

interface StructurePivot {
  bar_index: number;
  timestamp: string;
  confirmed_at: string;
  price: number;
  is_high: boolean;
  structure_type: string;
  rule_applied: string;
}

interface ConsolidationRange {
  top: number;
  bottom: number;
  mean: number;
  duration_bars: number;
}

interface MarketStructure {
  trend: string;
  last_swing_high: number | null;
  last_swing_low: number | null;
  summary: string;
  pivot_count: number;
  pivots: StructurePivot[];
  consolidation: ConsolidationRange | null;
}

interface PriceZone {
  zone_type: string;
  price_level: number;
  top_price: number;
  bottom_price: number;
  touches: number;
  strength: number;
  status: string;
  invalidation_level: number;
  evidence: string;
}

interface PAEvent {
  event_type: string;
  timestamp: string;
  price: number;
  description: string;
  rule_applied: string;
  invalidation_criteria: string;
  is_confirmed: boolean;
}

interface PriceActionData {
  zones: PriceZone[];
  events: PAEvent[];
  is_compressed: boolean;
  observation: string;
  hypothesis: string;
}

interface PriceActionResponse {
  symbol: string;
  interval: string;
  bars_analyzed: number;
  candle_patterns: CandlePattern[];
  market_structure: MarketStructure;
  price_action: PriceActionData;
  data_status: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchPriceAction(
  symbol: string,
  interval: string
): Promise<PriceActionResponse> {
  const url = `${API_BASE}/api/v1/price-action/analysis?symbol=${encodeURIComponent(symbol)}&interval=${interval}&limit=200`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Error al obtener análisis de Price Action");
  }
  return res.json();
}

function formatPrice(price: number): string {
  return price.toLocaleString("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-CO", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TrendBadge({ trend }: { trend: string }) {
  const colors: Record<string, string> = {
    UPTREND: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
    DOWNTREND: "bg-red-500/20 text-red-400 border-red-500/40",
    CONSOLIDATION: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  };
  const labels: Record<string, string> = {
    UPTREND: "▲ Tendencia Alcista",
    DOWNTREND: "▼ Tendencia Bajista",
    CONSOLIDATION: "◆ Consolidación",
  };
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${colors[trend] ?? "bg-gray-700 text-gray-400"}`}
    >
      {labels[trend] ?? trend}
    </span>
  );
}

function DirectionBadge({ direction }: { direction: string }) {
  const map: Record<string, string> = {
    BULLISH: "text-emerald-400",
    BEARISH: "text-red-400",
    NEUTRAL: "text-gray-400",
  };
  const icons: Record<string, string> = {
    BULLISH: "▲",
    BEARISH: "▼",
    NEUTRAL: "◆",
  };
  return (
    <span className={`font-semibold text-xs ${map[direction] ?? "text-gray-400"}`}>
      {icons[direction] ?? "·"} {direction}
    </span>
  );
}

function StrengthBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    value >= 0.7
      ? "bg-emerald-500"
      : value >= 0.4
      ? "bg-amber-400"
      : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-400">{pct}%</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab Panels
// ---------------------------------------------------------------------------

function CandlePatternsTab({ patterns }: { patterns: CandlePattern[] }) {
  if (patterns.length === 0) {
    return (
      <p className="text-gray-500 text-sm py-4 text-center">
        No se detectaron patrones de velas para este símbolo / temporalidad.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-700/60">
            <th className="text-left py-2 px-3 text-gray-400 font-medium">Patrón</th>
            <th className="text-left py-2 px-3 text-gray-400 font-medium">Dirección</th>
            <th className="text-right py-2 px-3 text-gray-400 font-medium">Precio</th>
            <th className="text-left py-2 px-3 text-gray-400 font-medium">Confirmado</th>
            <th className="text-right py-2 px-3 text-gray-400 font-medium">Confianza</th>
          </tr>
        </thead>
        <tbody>
          {patterns.slice(-30).reverse().map((p, i) => (
            <tr
              key={i}
              className="border-b border-gray-800/40 hover:bg-gray-800/30 transition-colors"
              title={p.rule_applied}
            >
              <td className="py-2 px-3 text-gray-200 font-medium">
                {p.pattern_type.replace(/_/g, " ")}
              </td>
              <td className="py-2 px-3">
                <DirectionBadge direction={p.direction} />
              </td>
              <td className="py-2 px-3 text-right text-gray-300 font-mono">
                {formatPrice(p.price)}
              </td>
              <td className="py-2 px-3 text-gray-500">
                {formatDate(p.confirmed_at)}
              </td>
              <td className="py-2 px-3 text-right">
                <span
                  className={`font-mono text-xs ${
                    p.confidence >= 0.9
                      ? "text-emerald-400"
                      : p.confidence >= 0.8
                      ? "text-amber-400"
                      : "text-gray-400"
                  }`}
                >
                  {(p.confidence * 100).toFixed(0)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MarketStructureTab({ data }: { data: MarketStructure }) {
  return (
    <div className="space-y-4">
      {/* Trend badge + summary */}
      <div className="flex flex-col gap-2">
        <TrendBadge trend={data.trend} />
        <p className="text-xs text-gray-400 leading-relaxed">{data.summary}</p>
      </div>

      {/* Swing highs / lows */}
      {(data.last_swing_high || data.last_swing_low) && (
        <div className="grid grid-cols-2 gap-3">
          {data.last_swing_high && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
              <p className="text-xs text-gray-400">Último Swing High</p>
              <p className="text-sm text-red-400 font-mono font-semibold">
                {formatPrice(data.last_swing_high)}
              </p>
            </div>
          )}
          {data.last_swing_low && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3">
              <p className="text-xs text-gray-400">Último Swing Low</p>
              <p className="text-sm text-emerald-400 font-mono font-semibold">
                {formatPrice(data.last_swing_low)}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Consolidation range */}
      {data.consolidation && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs space-y-1">
          <p className="text-amber-400 font-semibold">Rango de Consolidación</p>
          <p className="text-gray-400">
            Tope: <span className="text-gray-200 font-mono">{formatPrice(data.consolidation.top)}</span>
            {" · "}
            Base: <span className="text-gray-200 font-mono">{formatPrice(data.consolidation.bottom)}</span>
            {" · "}
            Media: <span className="text-gray-200 font-mono">{formatPrice(data.consolidation.mean)}</span>
          </p>
        </div>
      )}

      {/* Pivot table */}
      {data.pivots.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">
            Últimos pivotes confirmados (sin sesgo de futuro)
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-700/60">
                  <th className="text-left py-1.5 px-2 text-gray-400">Tipo</th>
                  <th className="text-right py-1.5 px-2 text-gray-400">Precio</th>
                  <th className="text-left py-1.5 px-2 text-gray-400">Confirmado</th>
                </tr>
              </thead>
              <tbody>
                {data.pivots.slice(-15).reverse().map((p, i) => {
                  const isHigh = p.is_high;
                  const isBullish = ["HH", "HL"].includes(p.structure_type);
                  return (
                    <tr
                      key={i}
                      className="border-b border-gray-800/30 hover:bg-gray-800/20"
                      title={p.rule_applied}
                    >
                      <td className="py-1.5 px-2">
                        <span
                          className={`font-semibold ${
                            isBullish
                              ? "text-emerald-400"
                              : p.structure_type.includes("L")
                              ? "text-red-400"
                              : "text-gray-400"
                          }`}
                        >
                          {p.structure_type}
                        </span>
                      </td>
                      <td className="py-1.5 px-2 text-right font-mono text-gray-300">
                        {formatPrice(p.price)}
                      </td>
                      <td className="py-1.5 px-2 text-gray-500">
                        {formatDate(p.confirmed_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function SRZonesTab({ data }: { data: PriceActionData }) {
  return (
    <div className="space-y-4">
      {/* Observation vs Hypothesis */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
        <p className="text-xs text-blue-400 font-semibold mb-1">
          📊 Observación (Factual)
        </p>
        <p className="text-xs text-gray-300 leading-relaxed">{data.observation}</p>
      </div>
      <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
        <p className="text-xs text-purple-400 font-semibold mb-1">
          💡 Hipótesis (Interpretiva)
        </p>
        <p className="text-xs text-gray-300 leading-relaxed">{data.hypothesis}</p>
      </div>

      {/* Compression indicator */}
      {data.is_compressed && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2 flex items-center gap-2">
          <span className="text-amber-400 text-sm">⚡</span>
          <p className="text-xs text-amber-300">
            <strong>Compresión de ATR detectada</strong> — El rango promedio actual es
            inferior al 50% del rango histórico de referencia.
          </p>
        </div>
      )}

      {/* S/R Zones */}
      {data.zones.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-4">
          No se detectaron zonas con suficientes reacciones de precio.
        </p>
      ) : (
        <div className="space-y-2">
          {data.zones.map((z, i) => (
            <div
              key={i}
              className={`rounded-lg border p-3 ${
                z.zone_type === "RESISTANCE" || z.zone_type === "SUPPLY"
                  ? "bg-red-500/8 border-red-500/20"
                  : "bg-emerald-500/8 border-emerald-500/20"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-semibold ${
                      z.zone_type === "RESISTANCE" || z.zone_type === "SUPPLY"
                        ? "text-red-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {z.zone_type}
                  </span>
                  <span className="text-xs text-gray-500">
                    {z.touches} reacciones
                  </span>
                </div>
                <StrengthBar value={z.strength} />
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <div>
                  <span className="text-gray-500">Centro: </span>
                  <span className="text-gray-200">{formatPrice(z.price_level)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Rango: </span>
                  <span className="text-gray-400">
                    [{formatPrice(z.bottom_price)} – {formatPrice(z.top_price)}]
                  </span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed truncate" title={z.evidence}>
                {z.evidence}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* PA Events */}
      {data.events.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Eventos Recientes</p>
          <div className="space-y-1.5">
            {data.events.slice(-8).reverse().map((ev, i) => (
              <div
                key={i}
                className="bg-gray-800/40 rounded-lg px-3 py-2 border border-gray-700/30"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-300">
                    {ev.event_type}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">
                    {formatPrice(ev.price)}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">
                  {ev.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export interface PriceActionPanelProps {
  symbol?: string;
  interval?: string;
}

const TABS = ["Patrones de Velas", "Estructura de Mercado", "Zonas S/R"] as const;

export default function PriceActionPanel({
  symbol = "AAPL",
  interval = "1d",
}: PriceActionPanelProps) {
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>(TABS[0]);
  const [data, setData] = useState<PriceActionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchPriceAction(symbol, interval)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol, interval]);

  return (
    <section className="bg-gray-900 border border-gray-700/50 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
          <h2 className="text-sm font-semibold text-gray-200">
            Análisis de Price Action
          </h2>
          {data && (
            <span className="text-xs text-gray-500">
              {data.symbol} · {data.interval} · {data.bars_analyzed} barras
            </span>
          )}
        </div>
        <span className="text-xs text-gray-600 bg-gray-800 px-2 py-0.5 rounded">
          Observación causal · Sin sesgo de futuro
        </span>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700/50">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
              activeTab === tab
                ? "text-violet-400 border-b-2 border-violet-500 bg-violet-500/5"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Body */}
      <div className="p-4 max-h-[520px] overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="w-5 h-5 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
            <span className="ml-2 text-sm text-gray-400">Calculando análisis…</span>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-400">
            <strong>Error:</strong> {error}
          </div>
        )}

        {data && !loading && !error && (
          <>
            {activeTab === "Patrones de Velas" && (
              <CandlePatternsTab patterns={data.candle_patterns} />
            )}
            {activeTab === "Estructura de Mercado" && (
              <MarketStructureTab data={data.market_structure} />
            )}
            {activeTab === "Zonas S/R" && (
              <SRZonesTab data={data.price_action} />
            )}
          </>
        )}
      </div>
    </section>
  );
}
