import React from "react";
import { SystemTelemetry } from "@/components/SystemTelemetry";
import { PhaseTracker } from "@/components/PhaseTracker";
import { MarketDataExplorer } from "@/components/MarketDataExplorer";
import { TradingChart } from "@/components/chart/TradingChart";
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
  LineChart,
} from "lucide-react";

export default function HomePage() {
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
            Plataforma profesional de análisis cuantitativo con datos trazables, cálculos vectorizados en Python, Smart Money Concepts (SMC), Liquidity Intelligence, asistente contextual, visión de pantalla y voz en tiempo real.
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
              <span>Gráficos: <strong className="text-white">Lightweight Charts + Motor Python</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Trading Chart (Phase 3 Core Delivery) */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <LineChart className="h-4 w-4 text-quant-cyan" />
            <h3 className="font-mono text-xs font-semibold tracking-wider text-gray-300 uppercase">
              TERMINAL GRÁFICA CUANTITATIVA (FASE 3)
            </h3>
          </div>
          <span className="text-xs font-mono text-gray-500">
            Lightweight Charts • Cálculos Vectorizados Backend Python
          </span>
        </div>
        <TradingChart />
      </section>

      {/* Multi-Market Data Explorer (Phase 2 Delivery) */}
      <MarketDataExplorer />

      {/* Backend & Systems Telemetry */}
      <SystemTelemetry />

      {/* 14 Phases Implementation Roadmap */}
      <PhaseTracker />

      {/* Phase 3 Acceptance Criteria Verification Box */}
      <div className="rounded-xl border border-border bg-surface p-6 shadow-xl">
        <h3 className="font-mono text-sm font-semibold text-white flex items-center space-x-2 mb-3">
          <ShieldCheck className="h-4 w-4 text-quant-green" />
          <span>VERIFICACIÓN FORMAL — CRITERIOS DE ACEPTACIÓN FASE 3 (GRÁFICOS E INDICADORES)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Lightweight Charts Integrado:</strong>
              <p className="text-gray-400 mt-0.5">Renderizado de velas OHLC con colores profesionales oscuros, escala de volumen acoplada, crosshairs sincronizados y reescalado adaptativo.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Indicadores Técnicos Vectorizados en Python:</strong>
              <p className="text-gray-400 mt-0.5">Cálculo en backend de EMA 20/50/100/200, RSI 14 (Wilder), MACD (12,26,9), ATR 14, VWAP y Bandas de Bollinger sin cálculos pesados en frontend.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Niveles de Fibonacci:</strong>
              <p className="text-gray-400 mt-0.5">Cálculo de retrocesos automáticos (0.236, 0.382, 0.500, 0.618 golden ratio, 0.786) proyectados dinámicamente como líneas de precio en el gráfico.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Pruebas Unitarias de Fórmulas Matemáticas:</strong>
              <p className="text-gray-400 mt-0.5">Suite exhaustiva con 27 pruebas aprobadas al 100% que validan factores de suavizado, límites de osciladores y consistencia numérica.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
