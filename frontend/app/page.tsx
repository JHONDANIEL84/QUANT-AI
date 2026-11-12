import React from "react";
import { SystemTelemetry } from "@/components/SystemTelemetry";
import { PhaseTracker } from "@/components/PhaseTracker";
import { MarketDataExplorer } from "@/components/MarketDataExplorer";
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
            Plataforma profesional de análisis cuantitativo con datos trazables, cálculos reproducibles, Smart Money Concepts (SMC), Liquidity Intelligence, asistente contextual, visión de pantalla y voz en tiempo real.
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
              <span>Mercados: <strong className="text-white">Acciones US • ETFs • Criptomonedas • BVC • Macro</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Market Data Explorer (Phase 2 Delivery) */}
      <MarketDataExplorer />

      {/* Backend & Systems Telemetry */}
      <SystemTelemetry />

      {/* 14 Phases Implementation Roadmap */}
      <PhaseTracker />

      {/* Phase 2 Acceptance Criteria Verification Box */}
      <div className="rounded-xl border border-border bg-surface p-6 shadow-xl">
        <h3 className="font-mono text-sm font-semibold text-white flex items-center space-x-2 mb-3">
          <ShieldCheck className="h-4 w-4 text-quant-green" />
          <span>VERIFICACIÓN FORMAL — CRITERIOS DE ACEPTACIÓN FASE 2 (PROVEEDORES DE MERCADO)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Yahoo Finance (Acciones & ETFs):</strong>
              <p className="text-gray-400 mt-0.5">Adaptador yfinance con mapeo de temporalidades, caché en memoria TTL, clasificación de ETFs, información empresarial y manejo de límites.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Binance REST & WebSockets (Cripto):</strong>
              <p className="text-gray-400 mt-0.5">Endpoints públicos Vision (Klines, Ticker 24h, Trades, Order Book depth) y cálculo de ratio de desequilibrio bid/ask sin requerir API key.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Bolsa de Valores de Colombia (BVC CSV):</strong>
              <p className="text-gray-400 mt-0.5">Importador y normalizador CSV para acciones colombianas en COP (Ecopetrol, Bancolombia, ISA, GEB) con validación de precios y duplicados.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Fuentes Macroeconómicas Oficiales:</strong>
              <p className="text-gray-400 mt-0.5">Adaptadores para Banco de la República (tasa política, TRM USD/COP), DANE (inflación IPC, desempleo, PIB) y FRED (tasas e inflación de EE. UU.).</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
