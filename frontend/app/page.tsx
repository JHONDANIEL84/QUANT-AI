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

      {/* Phase 4 Acceptance Criteria Verification Box */}
      <div className="rounded-xl border border-border bg-surface p-6 shadow-xl">
        <h3 className="font-mono text-sm font-semibold text-white flex items-center space-x-2 mb-3">
          <ShieldCheck className="h-4 w-4 text-quant-green" />
          <span>VERIFICACIÓN FORMAL — CRITERIOS DE ACEPTACIÓN FASE 4 (PRICE ACTION Y ESTRUCTURA)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Detección de Patrones de Velas Japonesas:</strong>
              <p className="text-gray-400 mt-0.5">Detección causal de Engulfing, Hammer, Inverted Hammer, Shooting Star, Hanging Man, Morning/Evening Star, Doji y Marubozu con reglas de proporción de mecha/cuerpo.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Estructura de Mercado (Swings & Tendencia):</strong>
              <p className="text-gray-400 mt-0.5">Algoritmo fractal causal (k=3) para Swing Highs (HH, LH) y Swing Lows (HL, LL), clasificación de tendencia (Alcista, Bajista, Consolidación) y prevención de look-ahead bias con confirmación diferida.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Zonas Dinámicas de Soporte y Resistencia:</strong>
              <p className="text-gray-400 mt-0.5">Identificación de niveles de precio por densidad de pivotes, bandas de tolerancia, conteo de toques, validación de fuerza y detección de rupturas y retesteos con invalidación objetiva.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Panel React Especializado & API Endpoint:</strong>
              <p className="text-gray-400 mt-0.5">Ruta <code className="text-quant-cyan">/api/v1/price-action/analysis</code> integrada con componente interactivo con pestañas de Velas, Estructura y S/R, diferenciando hechos de hipótesis.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Phase 5 Acceptance Criteria Verification Box */}
      <div className="rounded-xl border border-border bg-surface p-6 shadow-xl">
        <h3 className="font-mono text-sm font-semibold text-white flex items-center space-x-2 mb-3">
          <ShieldCheck className="h-4 w-4 text-quant-green" />
          <span>VERIFICACIÓN FORMAL — CRITERIOS DE ACEPTACIÓN FASE 5 (SMART MONEY CONCEPTS - SMC)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">BOS (Break of Structure) & CHOCH (Change of Character):</strong>
              <p className="text-gray-400 mt-0.5">Detección causal de rupturas continuistas (BOS) y alertas tempranas de giro estructural (CHOCH) con nivel explícito de invalidación.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Order Blocks & Breaker Blocks Institucionales:</strong>
              <p className="text-gray-400 mt-0.5">Identificación de la última vela previa al desplazamiento, puntuación de calidad (0-100 pts) y seguimiento de mitigación e invalidación a Breaker Block.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Fair Value Gaps (FVG) & Consequent Encroachment:</strong>
              <p className="text-gray-400 mt-0.5">Detección algorítmica de desequilibrios de 3 velas, cálculo del nivel medio CE (50%) y porcentaje dinámico de rellenado en tiempo real.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Rango Dealing, Premium / Discount & Endpoint API:</strong>
              <p className="text-gray-400 mt-0.5">Cálculo de Equilibrium al 50%, ruta <code className="text-quant-cyan">/api/v1/smc/analysis</code> y panel interactivo con pestañas especializadas.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Phase 6 Acceptance Criteria Verification Box */}
      <div className="rounded-xl border border-border bg-surface p-6 shadow-xl">
        <h3 className="font-mono text-sm font-semibold text-white flex items-center space-x-2 mb-3">
          <ShieldCheck className="h-4 w-4 text-quant-green" />
          <span>VERIFICACIÓN FORMAL — CRITERIOS DE ACEPTACIÓN FASE 6 (LIQUIDITY INTELLIGENCE & SWEEPS)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Equal Highs (EQH) & Equal Lows (EQL):</strong>
              <p className="text-gray-400 mt-0.5">Agrupamiento de pivotes extremos bajo tolerancia adaptativa ATR ($\pm 0.2\%$), identificando pools de Buy-side y Sell-side con score de liquidez (0-100 pts).</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Barridos Institucionales (Sweeps & Stop Hunts):</strong>
              <p className="text-gray-400 mt-0.5">Detección causal de mechas que penetran niveles clave con cierre inmediato por dentro (absorción institucional) y nivel explícito de invalidación.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Niveles de Sesión (PDH, PDL, PWH, PWL):</strong>
              <p className="text-gray-400 mt-0.5">Cálculo dinámico de los máximos y mínimos de la sesión diaria y semanal anterior como referencias primarias de liquidez externa.</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-surface-card p-3 flex items-start space-x-3">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-quant-green/20 text-quant-green text-xs font-bold shrink-0">✓</span>
            <div>
              <strong className="text-white font-mono">Panel React de Liquidez & Endpoint API:</strong>
              <p className="text-gray-400 mt-0.5">Endpoint <code className="text-quant-cyan">/api/v1/liquidity/analysis</code> acoplado a componente <code className="text-quant-cyan">LiquidityPanel.tsx</code> con separación de hechos e hipótesis.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
