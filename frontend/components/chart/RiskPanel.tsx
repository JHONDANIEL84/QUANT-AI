"use client";

/**
 * RiskPanel.tsx — Fase 8 QUANT AI
 *
 * Panel de Gestión del Riesgo y Portafolio Simulado.
 * Incluye:
 *   - Calculadora de Tamaño de Posición (4 métodos)
 *   - Display de R:R con semáforo visual
 *   - Estado del portafolio simulado en COP
 *   - Curva de equity mini-sparkline
 *
 * Principio epistémico: observación (cálculo verificado) separada de
 * hipótesis (proyección con invalidación explícita en precio).
 */

import React, { useState, useCallback } from "react";
import {
  Shield,
  Calculator,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Eye,
  Lightbulb,
  Target,
  DollarSign,
  BarChart2,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type TradeDirection = "long" | "short";
type SizingMethod = "fixed_percent" | "kelly" | "atr_based" | "fixed_cop";
type RiskRating = "muy_bajo" | "bajo" | "moderado" | "alto" | "excesivo";

interface PositionSizeResult {
  method: SizingMethod;
  direction: TradeDirection;
  units: number;
  position_value_cop: number;
  position_value_usd: number | null;
  risk_amount_cop: number;
  risk_percent_actual: number;
  entry_price: number;
  stop_loss_price: number;
  target_price: number | null;
  risk_reward_ratio: number | null;
  risk_rating: RiskRating;
  observation: string;
  hypothesis: string;
  calculated_at: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCOP(value: number): string {
  return value.toLocaleString("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

function RRBadge({ rr }: { rr: number | null }) {
  if (rr === null)
    return <span className="text-zinc-500 text-xs">Sin objetivo</span>;

  const cfg =
    rr >= 4
      ? { color: "text-emerald-400", label: `R:R ${rr.toFixed(2)} ✓✓✓` }
      : rr >= 3
        ? { color: "text-green-400", label: `R:R ${rr.toFixed(2)} ✓✓` }
        : rr >= 2
          ? { color: "text-yellow-400", label: `R:R ${rr.toFixed(2)} ✓` }
          : rr >= 1
            ? { color: "text-orange-400", label: `R:R ${rr.toFixed(2)} ⚠` }
            : { color: "text-red-400", label: `R:R ${rr.toFixed(2)} ✗` };

  return (
    <span className={`font-mono font-bold text-sm ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}

function RiskMeter({ pct }: { pct: number }) {
  const color =
    pct <= 1 ? "bg-emerald-500" : pct <= 2 ? "bg-yellow-500" : pct <= 3 ? "bg-orange-500" : "bg-red-500";
  const width = Math.min(100, (pct / 5) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-zinc-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${width}%` }} />
      </div>
      <span className={`font-mono text-xs font-bold ${color.replace("bg-", "text-")}`}>
        {pct.toFixed(2)}%
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface RiskPanelProps {
  defaultSymbol?: string;
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function RiskPanel({ defaultSymbol }: RiskPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PositionSizeResult | null>(null);

  // Form state
  const [capital, setCapital] = useState("50000000");
  const [entry, setEntry] = useState("");
  const [stop, setStop] = useState("");
  const [target, setTarget] = useState("");
  const [riskPct, setRiskPct] = useState("1.0");
  const [direction, setDirection] = useState<TradeDirection>("long");
  const [method, setMethod] = useState<SizingMethod>("fixed_percent");
  const [winRate, setWinRate] = useState("0.55");
  const [avgRatio, setAvgRatio] = useState("1.5");
  const [atrValue, setAtrValue] = useState("");
  const [usdCop, setUsdCop] = useState("");

  const calculate = useCallback(async () => {
    if (!entry || !stop) return;
    setLoading(true);
    setError(null);
    try {
      const body: Record<string, unknown> = {
        capital_cop: parseFloat(capital),
        entry_price: parseFloat(entry),
        stop_loss_price: parseFloat(stop),
        risk_percent: parseFloat(riskPct),
        method,
        direction,
      };
      if (target) body.target_price = parseFloat(target);
      if (usdCop) body.usd_cop_rate = parseFloat(usdCop);
      if (method === "kelly") {
        body.win_rate = parseFloat(winRate);
        body.avg_win_loss_ratio = parseFloat(avgRatio);
      }
      if (method === "atr_based" && atrValue) body.atr_value = parseFloat(atrValue);

      const res = await fetch("/api/v1/risk/position-size", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Error ${res.status}`);
      }
      const data: PositionSizeResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }, [capital, entry, stop, target, riskPct, direction, method, winRate, avgRatio, atrValue, usdCop]);

  return (
    <div className="border border-zinc-700/60 rounded-xl bg-zinc-900/80 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between p-3 hover:bg-zinc-800/60 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-orange-400" />
          <span className="text-sm font-semibold text-orange-400">
            Gestión del Riesgo — Calculadora de Posición en COP
          </span>
          {result && (
            <span className="ml-2 px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded text-xs">
              {result.units.toFixed(4)} unidades
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
          {/* Form */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {/* Capital */}
            <div className="col-span-2 sm:col-span-1">
              <label className="text-xs text-zinc-500 mb-1 block">Capital disponible (COP)</label>
              <div className="flex items-center bg-zinc-700 border border-zinc-600 rounded overflow-hidden">
                <DollarSign className="w-3.5 h-3.5 text-zinc-400 ml-2 flex-shrink-0" />
                <input
                  type="number"
                  value={capital}
                  onChange={(e) => setCapital(e.target.value)}
                  className="flex-1 bg-transparent px-2 py-1.5 text-xs text-white focus:outline-none"
                  placeholder="50000000"
                />
              </div>
            </div>

            {/* Direction */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Dirección</label>
              <select
                value={direction}
                onChange={(e) => setDirection(e.target.value as TradeDirection)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-orange-500"
              >
                <option value="long">LONG (Compra)</option>
                <option value="short">SHORT (Venta)</option>
              </select>
            </div>

            {/* Method */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Método de sizing</label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as SizingMethod)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-orange-500"
              >
                <option value="fixed_percent">% Fijo del Capital</option>
                <option value="kelly">Criterio de Kelly</option>
                <option value="atr_based">Basado en ATR</option>
                <option value="fixed_cop">Monto Fijo COP</option>
              </select>
            </div>

            {/* Risk % */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Riesgo % por operación</label>
              <input
                type="number"
                value={riskPct}
                onChange={(e) => setRiskPct(e.target.value)}
                step="0.5"
                min="0.1"
                max="5"
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
              />
            </div>

            {/* Entry */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Precio de entrada</label>
              <input
                type="number"
                value={entry}
                onChange={(e) => setEntry(e.target.value)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
                placeholder="ej. 300000000"
              />
            </div>

            {/* Stop Loss */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Stop Loss (invalidación)</label>
              <input
                type="number"
                value={stop}
                onChange={(e) => setStop(e.target.value)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
                placeholder="ej. 285000000"
              />
            </div>

            {/* Target */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Objetivo (take profit)</label>
              <input
                type="number"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
                placeholder="opcional"
              />
            </div>

            {/* TRM USD/COP */}
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">TRM USD→COP (si aplica)</label>
              <input
                type="number"
                value={usdCop}
                onChange={(e) => setUsdCop(e.target.value)}
                className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
                placeholder="ej. 4150"
              />
            </div>

            {/* Kelly extras */}
            {method === "kelly" && (
              <>
                <div>
                  <label className="text-xs text-zinc-500 mb-1 block">Win Rate (0-1)</label>
                  <input
                    type="number"
                    value={winRate}
                    onChange={(e) => setWinRate(e.target.value)}
                    step="0.01"
                    min="0"
                    max="1"
                    className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-500 mb-1 block">Ratio Win/Loss prom.</label>
                  <input
                    type="number"
                    value={avgRatio}
                    onChange={(e) => setAvgRatio(e.target.value)}
                    step="0.1"
                    min="0.1"
                    className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
                  />
                </div>
              </>
            )}

            {/* ATR value */}
            {method === "atr_based" && (
              <div>
                <label className="text-xs text-zinc-500 mb-1 block">ATR actual</label>
                <input
                  type="number"
                  value={atrValue}
                  onChange={(e) => setAtrValue(e.target.value)}
                  className="w-full bg-zinc-700 border border-zinc-600 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500"
                  placeholder="ej. 1500"
                />
              </div>
            )}
          </div>

          {/* Calculate button */}
          <button
            onClick={calculate}
            disabled={loading || !entry || !stop}
            className="w-full flex items-center justify-center gap-2 py-2 bg-orange-600 hover:bg-orange-500 disabled:opacity-50 rounded-lg text-sm text-white font-semibold transition-colors"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Calculator className="w-4 h-4" />
            )}
            Calcular Posición Óptima
          </button>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-3">
              {/* Key metrics grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-1">Unidades</p>
                  <p className="font-mono font-bold text-white text-sm">
                    {result.units.toLocaleString("es-CO", { maximumFractionDigits: 6 })}
                  </p>
                </div>
                <div className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-1">Valor posición</p>
                  <p className="font-mono font-bold text-cyan-400 text-sm">
                    {formatCOP(result.position_value_cop)}
                  </p>
                </div>
                <div className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-1">En riesgo</p>
                  <p className="font-mono font-bold text-red-400 text-sm">
                    {formatCOP(result.risk_amount_cop)}
                  </p>
                </div>
                <div className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-1">R:R</p>
                  <RRBadge rr={result.risk_reward_ratio} />
                </div>
              </div>

              {/* Risk meter */}
              <div>
                <p className="text-xs text-zinc-500 mb-1 flex items-center gap-1">
                  <BarChart2 className="w-3 h-3" />
                  Riesgo real del capital
                </p>
                <RiskMeter pct={result.risk_percent_actual} />
              </div>

              {/* Observation */}
              <div className="p-2.5 bg-blue-500/5 border border-blue-500/20 rounded-md">
                <div className="flex items-center gap-1.5 mb-1">
                  <Eye className="w-3 h-3 text-blue-400" />
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wide">
                    Observación
                  </span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed">{result.observation}</p>
              </div>

              {/* Hypothesis */}
              <div className="p-2.5 bg-amber-500/5 border border-amber-500/20 rounded-md">
                <div className="flex items-center gap-1.5 mb-1">
                  <Lightbulb className="w-3 h-3 text-amber-400" />
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">
                    Hipótesis
                  </span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed">{result.hypothesis}</p>
                <div className="mt-1.5 flex items-center gap-1.5">
                  <Target className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400 font-mono">
                    Stop: {result.stop_loss_price.toLocaleString("es-CO", { maximumFractionDigits: 4 })}
                    {result.target_price !== null && (
                      <>
                        {" | "}
                        Objetivo:{" "}
                        {result.target_price.toLocaleString("es-CO", { maximumFractionDigits: 4 })}
                      </>
                    )}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
