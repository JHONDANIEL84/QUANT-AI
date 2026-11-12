import React from "react";
import { SystemTelemetry } from "@/components/SystemTelemetry";
import { PhaseTracker } from "@/components/PhaseTracker";
import {
  TrendingUp,
  Cpu,
  ShieldCheck,
  Zap,
  Layers,
  Database,
  Terminal,
  Activity,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";

export default function HomePage() {
  const sampleTickers = [
    { symbol: "BTCUSDT", name: "Bitcoin / Tether USD", price: "$90,450.00", change: "+2.45%", isUp: true, market: "Crypto (Binance)" },
    { symbol: "NVDA", name: "NVIDIA Corporation", price: "$145.20", change: "+3.12%", isUp: true, market: "Stock (Yahoo)" },
    { symbol: "AAPL", name: "Apple Inc.", price: "$228.80", change: "+0.85%", isUp: true, market: "Stock (Yahoo)" },
    { symbol: "SPY", name: "S&P 500 ETF Trust", price: "$585.10", change: "+0.42%", isUp: true, market: "ETF (Yahoo)" },
    { symbol: "ECOPETROL", name: "Ecopetrol S.A.", price: "2,050 COP", change: "-0.48%", isUp: false, market: "Stock (BVC)" },
    { symbol: "PFBCOLO", name: "Bancolombia Pref.", price: "34,200 COP", change: "+1.18%", isUp: true, market: "Stock (BVC)" },
  ];

  return (
    <div className="space-y-8">
      {/* Hero / System Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-surface via-surface-card to-background p-6 sm:p-8 shadow-2xl">
        <div className="absolute right-0 top-0 -mt-10 -mr-10 h-72 w-72 rounded-full bg-quant-cyan/5 blur-3xl" />
        <div className="absolute left-1/3 bottom-0 -mb-10 h-64 w-64 rounded-full bg-quant-blue/5 blur-3xl" />

        <div className="relative z-10">
          <div className="inline-flex items-center space-x-2 rounded-full border border-quant-cyan/30 bg-quant-cyan/10 px-3 py-1 text-xs font-mono font-medium text-quant-cyan mb-4">
            <Sparkles className="h-3.5 w-3.5" />
            <span>PLATAFORMA CUANTITATIVA AVANZADA & ASISTENTE IA MULTIMODAL</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white max-w-3xl">
            QUANT <span className="text-quant-cyan">AI</span> — Intelligent Quantitative Swing Trading
          </h1>

          <p className="mt-3 text-sm sm:text-base text-gray-400 max-w-2xl leading-relaxed">
            Plataforma profesional de análisis de swing trading cuantitativo con trazabilidad matemática, Smart Money Concepts, detección de liquidez técnica y libro de órdenes, asistente contextual, visión de pantalla y voz en tiempo real.
          </p>

          <div className="mt-6 flex flex-wrap gap-4 text-xs font-mono text-gray-300">
            <div className="flex items-center space-x-2 rounded-lg border border-border bg-surface/80 px-3 py-2">
              <span className="h-2 w-2 rounded-full bg-quant-green" />
              <span>Zona Horaria: <strong className="text-white">America/Bogota</strong></span>
            </div>
            <div className="flex items-center space-x-2 rounded-lg border border-border bg-surface/80 px-3 py-2">
              <span className="h-2 w-2 rounded-full bg-quant-amber" />
              <span>Moneda Base: <strong className="text-white">COP / USD</strong></span>
            </div>
            <div className="flex items-center space-x-2 rounded-lg border border-border bg-surface/80 px-3 py-2">
              <span className="h-2 w-2 rounded-full bg-quant-cyan" />
              <span>Mercados: <strong className="text-white">Acciones • ETF • Criptomonedas • BVC</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Market Watchlist Snapshot */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-4 w-4 text-quant-cyan" />
            <h3 className="font-mono text-xs font-semibold tracking-wider text-gray-300 uppercase">
              UNIVERSO DE ACTIVOS CONFIGURADOS
            </h3>
          </div>
          <span className="text-xs font-mono text-gray-500">
            Proveedores Públicos Gratuitos (Yahoo / Binance / BVC)
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {sampleTickers.map((t, idx) => (
            <div
              key={idx}
              className="rounded-xl border border-border bg-surface p-3 hover:border-border-light transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">{t.symbol}</span>
                  <span
                    className={`font-mono text-[11px] font-semibold ${
                      t.isUp ? "text-quant-green" : "text-quant-red"
                    }`}
                  >
                    {t.change}
                  </span>
                </div>
                <div className="font-mono text-sm font-semibold text-gray-200 mt-1">
                  {t.price}
                </div>
              </div>
              <div className="mt-2 pt-2 border-t border-border text-[10px] font-mono text-gray-500 truncate">
                {t.market}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Backend & Systems Telemetry */}
      <SystemTelemetry />

      {/* 14 Phases Implementation Roadmap */}
      <PhaseTracker />

      {/* Phase 1 Verification Checklist Box */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="font-mono text-sm font-semibold text-white flex items-center space-x-2 mb-3">
          <ShieldCheck className="h-4 w-4 text-quant-green" />
          <span>VERIFICACIÓN FORMAL — CRITERIOS DE ACEPTACIÓN FASE 1</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Frontend Next.js App Router:</strong>
              <p className="text-gray-400 mt-0.5">Estructura TypeScript estricta, Tailwind CSS, Lucide icons, layouts responsivos y clientes de datos preparados.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Backend FastAPI Operativo:</strong>
              <p className="text-gray-400 mt-0.5">Endpoints modulares (<code className="text-quant-cyan">/api/v1/health</code> y <code className="text-quant-cyan">/api/v1/system/status</code>), CORS seguro y schemas tipados con Pydantic.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Modelo de Datos & Migración Supabase:</strong>
              <p className="text-gray-400 mt-0.5">Script SQL completo con 22 tablas normalizadas, políticas RLS para aislamiento de usuarios y seed de instrumentos.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Pruebas Unitarias Aprobadas:</strong>
              <p className="text-gray-400 mt-0.5">Suite de pruebas pytest ejecutada con 100% de éxito verificando endpoints, modelos MarketBar y configuraciones regionales.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
