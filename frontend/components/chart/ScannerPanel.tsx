"use client";

/**
 * ScannerPanel.tsx — Fase 7 QUANT AI
 *
 * Panel de Escáner de Mercado y Confluencia Multi-Temporalidad (MTF).
 * Muestra oportunidades de swing trading cuantificadas con:
 *   - Dirección (BULLISH / BEARISH / NEUTRAL)
 *   - Nivel de convicción (HIGH / MODERATE / LOW)
 *   - Score compuesto (0-100)
 *   - Criterios técnicos + SMC + Liquidez verificados
 *   - Hipótesis con nivel de invalidación explícito
 *   - Alineación MTF entre marco temporal mayor y menor
 *
 * Principio epistémico: observación (hechos verificados) separada de
 * hipótesis (predicción con criterio de falsabilidad explícito).
 */

import React, { useState, useCallback } from "react";
import {
  Search,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Layers,
  Target,
  Eye,
  Lightbulb,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type SetupDirection = "BULLISH" | "BEARISH" | "NEUTRAL";
type ConvictionLevel = "HIGH" | "MODERATE" | "LOW";
type MarketFilter = "all" | "crypto" | "stock" | "bvc";
type Timeframe = "1d" | "4h" | "1h" | "15m";

interface ScanOpportunity {
  symbol: string;
  market: string;
  interval: string;
  direction: SetupDirection;
  conviction: ConvictionLevel;
  score: number;
  current_price: number;
  invalidation_level: number | null;
  matched_criteria: string[];
  unmatched_criteria: string[];
  evidence: Record<string, number | string>;
  observation: string;
  hypothesis: string;
  scanned_at: string;
}

interface MarketScanResponse {
  opportunities: ScanOpportunity[];
  total_assets_scanned: number;
  opportunities_found: number;
  scan_duration_ms: number;
  interval: string;
  scanned_at: string;
}

interface MTFConfluenceResult {
  symbol: string;
  htf_interval: string;
  ltf_interval: string;
  htf_direction: SetupDirection;
  ltf_direction: SetupDirection;
  confluence_score: number;
  is_aligned: boolean;
  summary: string;
  analyzed_at: string;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ScannerPanelProps {
  defaultSymbol?: string;
  defaultInterval?: Timeframe;
}

// ---------------------------------------------------------------------------
// Sub-components: Direction & Conviction Badges
// ---------------------------------------------------------------------------

function DirectionBadge({ direction }: { direction: SetupDirection }) {
  const cfg = {
    BULLISH: {
      icon: <TrendingUp className="w-3 h-3" />,
      label: "ALCISTA",
      cls: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
    },
    BEARISH: {
      icon: <TrendingDown className="w-3 h-3" />,
      label: "BAJISTA",
      cls: "bg-red-500/20 text-red-400 border border-red-500/30",
    },
    NEUTRAL: {
      icon: <Minus className="w-3 h-3" />,
      label: "NEUTRAL",
      cls: "bg-zinc-500/20 text-zinc-400 border border-zinc-500/30",
    },
  }[direction];

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${cfg.cls}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function ConvictionBadge({ conviction }: { conviction: ConvictionLevel }) {
  const cfg = {
    HIGH: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
    MODERATE: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
    LOW: "bg-zinc-500/20 text-zinc-500 border border-zinc-600/30",
  }[conviction];

  const label = { HIGH: "ALTA", MODERATE: "MEDIA", LOW: "BAJA" }[conviction];

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cfg}`}
    >
      {label}
    </span>
  );
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct >= 75
      ? "bg-emerald-500"
      : pct >= 55
        ? "bg-yellow-500"
        : pct >= 40
          ? "bg-blue-500"
          : "bg-zinc-600";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-zinc-300 w-8 text-right">
        {score.toFixed(0)}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Opportunity Card (expanded detail)
// ---------------------------------------------------------------------------

function OpportunityCard({
  opp,
  expanded,
  onToggle,
}: {
  opp: ScanOpportunity;
  expanded: boolean;
  onToggle: () => void;
}) {
  const isUp = opp.direction === "BULLISH";
  const isDown = opp.direction === "BEARISH";
  const borderColor = isUp
    ? "border-emerald-500/30"
    : isDown
      ? "border-red-500/30"
      : "border-zinc-700";

  return (
    <div
      className={`border rounded-lg bg-zinc-800/60 overflow-hidden transition-all duration-200 ${borderColor}`}
    >
      {/* Header row */}
      <button
        onClick={onToggle}
        className="w-full text-left p-3 hover:bg-zinc-700/40 transition-colors"
      >
        <div className="flex items-center gap-3">
          {/* Symbol */}
          <span className="font-mono font-bold text-white text-sm w-24 truncate">
            {opp.symbol}
          </span>
          {/* Direction & Conviction */}
          <DirectionBadge direction={opp.direction} />
          <ConvictionBadge conviction={opp.conviction} />
          {/* Score bar */}
          <div className="flex-1 min-w-0">
            <ScoreBar score={opp.score} />
          </div>
          {/* Price */}
          <span className="font-mono text-xs text-zinc-300 w-24 text-right hidden sm:block">
            {opp.current_price.toLocaleString("es-CO", {
              maximumFractionDigits: 4,
            })}
          </span>
          {/* Criteria count */}
          <span className="text-xs text-zinc-500 w-6 text-right">
            {opp.matched_criteria.length}✓
          </span>
          {/* Expand icon */}
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-zinc-500 flex-shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-zinc-500 flex-shrink-0" />
          )}
        </div>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-3 pb-3 space-y-3 border-t border-zinc-700/60">
          {/* Observation (hechos verificados) */}
          <div className="mt-3 p-2.5 bg-blue-500/5 border border-blue-500/20 rounded-md">
            <div className="flex items-center gap-1.5 mb-1">
              <Eye className="w-3 h-3 text-blue-400" />
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wide">
                Observación (Hechos)
              </span>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed">
              {opp.observation}
            </p>
          </div>

          {/* Hypothesis (predicción + invalidación) */}
          <div className="p-2.5 bg-amber-500/5 border border-amber-500/20 rounded-md">
            <div className="flex items-center gap-1.5 mb-1">
              <Lightbulb className="w-3 h-3 text-amber-400" />
              <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">
                Hipótesis (Predicción)
              </span>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed">
              {opp.hypothesis}
            </p>
            {opp.invalidation_level !== null && (
              <div className="mt-1.5 flex items-center gap-1.5">
                <Target className="w-3 h-3 text-red-400" />
                <span className="text-xs text-red-400 font-mono">
                  Invalidación:{" "}
                  {opp.invalidation_level.toLocaleString("es-CO", {
                    maximumFractionDigits: 4,
                  })}
                </span>
              </div>
            )}
          </div>

          {/* Criterios coincidentes */}
          {opp.matched_criteria.length > 0 && (
            <div>
              <p className="text-xs text-zinc-500 font-semibold mb-1 uppercase tracking-wide">
                Confluencias activas
              </p>
              <ul className="space-y-0.5">
                {opp.matched_criteria.map((c, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-zinc-300">
                    <CheckCircle className="w-3 h-3 text-emerald-500 mt-0.5 flex-shrink-0" />
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Criterios no coincidentes */}
          {opp.unmatched_criteria.length > 0 && (
            <div>
              <p className="text-xs text-zinc-500 font-semibold mb-1 uppercase tracking-wide">
                Factores ausentes
              </p>
              <ul className="space-y-0.5">
                {opp.unmatched_criteria.map((c, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-zinc-500">
                    <XCircle className="w-3 h-3 text-zinc-600 mt-0.5 flex-shrink-0" />
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Evidence metrics */}
          <div>
            <p className="text-xs text-zinc-500 font-semibold mb-1 uppercase tracking-wide">
              Métricas cuantitativas
            </p>
            <div className="grid grid-cols-3 gap-1.5">
              {Object.entries(opp.evidence).map(([k, v]) => (
                <div key={k} className="bg-zinc-700/40 rounded px-2 py-1">
                  <p className="text-xs text-zinc-500 capitalize">{k.replace(/_/g, " ")}</p>
                  <p className="text-xs font-mono text-zinc-200">
                    {typeof v === "number" ? v.toFixed(2) : String(v)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// MTF Confluence Widget
// ---------------------------------------------------------------------------

function MTFWidget({ defaultSymbol }: { defaultSymbol?: string }) {
  const [symbol, setSymbol] = useState(defaultSymbol ?? "BTCUSDT");
  const [htf, setHtf] = useState<Timeframe>("1d");
  const [ltf, setLtf] = useState<Timeframe>("4h");
  const [result, setResult] = useState<MTFConfluenceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async () => {
    if (!symbol.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const url = `/api/v1/scanner/mtf?symbol=${encodeURIComponent(symbol.trim())}&htf_interval=${htf}&ltf_interval=${ltf}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const data: MTFConfluenceResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }, [symbol, htf, ltf]);

  const alignedColor = result?.is_aligned
    ? "border-emerald-500/30 bg-emerald-500/5"
    : result
      ? "border-red-500/30 bg-red-500/5"
      : "border-zinc-700 bg-zinc-800/40";

  return (
    <div className="border border-zinc-700 rounded-lg bg-zinc-800/40 p-3 space-y-3">
      <div className="flex items-center gap-2">
        <Layers className="w-4 h-4 text-purple-400" />
        <h3 className="text-sm font-semibold text-purple-400">
          Confluencia Multi-Temporalidad (MTF)
        </h3>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Símbolo"
          className="flex-1 min-w-20 bg-zinc-700 border border-zinc-600 rounded px-2 py-1 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-purple-500"
        />
        <select
          value={htf}
          onChange={(e) => setHtf(e.target.value as Timeframe)}
          className="bg-zinc-700 border border-zinc-600 rounded px-2 py-1 text-xs text-zinc-300 focus:outline-none focus:border-purple-500"
        >
          <option value="1d">Marco Mayor: 1D</option>
          <option value="4h">Marco Mayor: 4H</option>
          <option value="1h">Marco Mayor: 1H</option>
        </select>
        <select
          value={ltf}
          onChange={(e) => setLtf(e.target.value as Timeframe)}
          className="bg-zinc-700 border border-zinc-600 rounded px-2 py-1 text-xs text-zinc-300 focus:outline-none focus:border-purple-500"
        >
          <option value="4h">Marco Menor: 4H</option>
          <option value="1h">Marco Menor: 1H</option>
          <option value="15m">Marco Menor: 15M</option>
        </select>
        <button
          onClick={analyze}
          disabled={loading}
          className="flex items-center gap-1 px-3 py-1 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded text-xs text-white font-medium transition-colors"
        >
          {loading ? (
            <RefreshCw className="w-3 h-3 animate-spin" />
          ) : (
            <Search className="w-3 h-3" />
          )}
          Analizar
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-400">
          <AlertTriangle className="w-3 h-3 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className={`p-3 border rounded-lg space-y-2 transition-all ${alignedColor}`}>
          <div className="flex items-center justify-between">
            <span className="font-mono font-bold text-white text-sm">
              {result.symbol}
            </span>
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded ${
                result.is_aligned
                  ? "bg-emerald-500/20 text-emerald-400"
                  : "bg-red-500/20 text-red-400"
              }`}
            >
              {result.is_aligned ? "ALINEADO" : "DIVERGENTE"}
            </span>
          </div>
          <div className="flex gap-3">
            <div className="text-center">
              <p className="text-xs text-zinc-500">{result.htf_interval}</p>
              <DirectionBadge direction={result.htf_direction} />
            </div>
            <div className="flex items-center text-zinc-600 text-xs">→</div>
            <div className="text-center">
              <p className="text-xs text-zinc-500">{result.ltf_interval}</p>
              <DirectionBadge direction={result.ltf_direction} />
            </div>
            <div className="ml-auto text-right">
              <p className="text-xs text-zinc-500">Score MTF</p>
              <p className="font-mono font-bold text-white">
                {result.confluence_score.toFixed(0)}/100
              </p>
            </div>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">{result.summary}</p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main ScannerPanel
// ---------------------------------------------------------------------------

export default function ScannerPanel({ defaultSymbol, defaultInterval = "1d" }: ScannerPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<MarketScanResponse | null>(null);
  const [marketFilter, setMarketFilter] = useState<MarketFilter>("all");
  const [interval, setInterval] = useState<Timeframe>(defaultInterval);
  const [minScore, setMinScore] = useState(40);
  const [expandedOpp, setExpandedOpp] = useState<string | null>(null);

  const runScan = useCallback(async () => {
    setScanLoading(true);
    setScanError(null);
    try {
      const url = `/api/v1/scanner/scan?market_filter=${marketFilter}&interval=${interval}&min_score=${minScore}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const data: MarketScanResponse = await res.json();
      setScanResult(data);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : "Error desconocido al ejecutar escáner");
    } finally {
      setScanLoading(false);
    }
  }, [marketFilter, interval, minScore]);

  const toggleOpp = (symbol: string) => {
    setExpandedOpp((prev) => (prev === symbol ? null : symbol));
  };

  return (
    <div className="border border-zinc-700/60 rounded-xl bg-zinc-900/80 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between p-3 hover:bg-zinc-800/60 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-cyan-400" />
          <span className="text-sm font-semibold text-cyan-400">
            Escáner de Mercado — Oportunidades Cuantitativas
          </span>
          {scanResult && (
            <span className="ml-2 px-1.5 py-0.5 bg-cyan-500/20 text-cyan-400 rounded text-xs">
              {scanResult.opportunities_found} oportunidades
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
          {/* Scanner controls */}
          <div className="flex flex-wrap gap-2 items-end">
            {/* Market filter */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-zinc-500">Mercado</label>
              <select
                value={marketFilter}
                onChange={(e) => setMarketFilter(e.target.value as MarketFilter)}
                className="bg-zinc-700 border border-zinc-600 rounded px-2 py-1 text-xs text-zinc-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="all">Todos</option>
                <option value="crypto">Criptomonedas</option>
                <option value="stock">Acciones (US)</option>
                <option value="bvc">BVC Colombia</option>
              </select>
            </div>

            {/* Timeframe */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-zinc-500">Temporalidad</label>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value as Timeframe)}
                className="bg-zinc-700 border border-zinc-600 rounded px-2 py-1 text-xs text-zinc-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="1d">Diario (1D)</option>
                <option value="4h">4 Horas</option>
                <option value="1h">1 Hora</option>
                <option value="15m">15 Minutos</option>
              </select>
            </div>

            {/* Min Score */}
            <div className="flex flex-col gap-1 flex-1 min-w-32">
              <label className="text-xs text-zinc-500">
                Score mínimo: <span className="text-cyan-400 font-mono">{minScore}</span>
              </label>
              <input
                type="range"
                min={20}
                max={80}
                step={5}
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>

            {/* Scan button */}
            <button
              onClick={runScan}
              disabled={scanLoading}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded text-xs text-white font-semibold transition-colors"
            >
              {scanLoading ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Search className="w-3.5 h-3.5" />
              )}
              Escanear Mercado
            </button>
          </div>

          {/* Error */}
          {scanError && (
            <div className="flex items-center gap-2 p-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {scanError}
            </div>
          )}

          {/* Results */}
          {scanResult && (
            <div className="space-y-2">
              {/* Stats row */}
              <div className="flex items-center gap-4 text-xs text-zinc-500 pb-1 border-b border-zinc-700/60">
                <span>
                  Escaneados:{" "}
                  <span className="text-zinc-300 font-mono">
                    {scanResult.total_assets_scanned}
                  </span>
                </span>
                <span>
                  Oportunidades:{" "}
                  <span className="text-cyan-400 font-mono">
                    {scanResult.opportunities_found}
                  </span>
                </span>
                <span>
                  Duración:{" "}
                  <span className="text-zinc-300 font-mono">
                    {scanResult.scan_duration_ms}ms
                  </span>
                </span>
                <span className="ml-auto">
                  {new Date(scanResult.scanned_at).toLocaleTimeString("es-CO")}
                </span>
              </div>

              {/* Column headers */}
              {scanResult.opportunities.length > 0 && (
                <div className="flex items-center gap-3 px-3 text-xs text-zinc-600 uppercase tracking-wide">
                  <span className="w-24">Símbolo</span>
                  <span className="w-20">Dirección</span>
                  <span className="w-16">Convicción</span>
                  <span className="flex-1">Score</span>
                  <span className="w-24 text-right hidden sm:block">Precio</span>
                  <span className="w-6 text-right">✓</span>
                  <span className="w-4" />
                </div>
              )}

              {/* Opportunity cards */}
              {scanResult.opportunities.length === 0 ? (
                <div className="text-center py-8 text-zinc-600 text-sm">
                  <Search className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p>Sin oportunidades con score ≥ {minScore} en este universo.</p>
                  <p className="text-xs mt-1">Ajusta los filtros o ejecuta el escáner nuevamente.</p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {scanResult.opportunities.map((opp) => (
                    <OpportunityCard
                      key={opp.symbol}
                      opp={opp}
                      expanded={expandedOpp === opp.symbol}
                      onToggle={() => toggleOpp(opp.symbol)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* MTF Confluence Widget */}
          <MTFWidget defaultSymbol={defaultSymbol} />
        </div>
      )}
    </div>
  );
}
