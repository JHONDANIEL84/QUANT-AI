"use client";

import React from "react";
import { CheckCircle2, Circle, Clock, ArrowRight } from "lucide-react";

interface Phase {
  id: number;
  title: string;
  desc: string;
  status: "completed" | "in_progress" | "pending";
}

const PHASES: Phase[] = [
  { id: 1, title: "Fase 1: Arquitectura y Configuración", desc: "Monorepo, Next.js, FastAPI, Supabase, Normalización Base, Tests", status: "completed" },
  { id: 2, title: "Fase 2: Proveedores de Datos", desc: "Yahoo Finance (Acciones/ETFs), Binance WS (Crypto), BVC CSV, Macro", status: "completed" },
  { id: 3, title: "Fase 3: Gráficos e Indicadores", desc: "Lightweight Charts, OHLCV, EMA 20/50/100/200, RSI, MACD, ATR, VWAP", status: "completed" },
  { id: 4, title: "Fase 4: Price Action y Estructura", desc: "Velas japonesas, HH/HL/LH/LL, Swings, S/R, Rupturas, Retesteos", status: "pending" },
  { id: 5, title: "Fase 5: Smart Money Concepts", desc: "BOS, CHOCH, Order Blocks, Mitigation, Breakers, FVG, Premium/Discount", status: "pending" },
  { id: 6, title: "Fase 6: Liquidity Intelligence", desc: "Equal Highs/Lows, Sweeps confirmados, Order Book Depth & Imbalance", status: "pending" },
  { id: 7, title: "Fase 7: Scanner y Análisis Multitemporal", desc: "Screener multiactivo, filtros técnicos y confluencia 1H/4H/1D/1W", status: "pending" },
  { id: 8, title: "Fase 8: Gestión del Riesgo y Portafolio", desc: "Simulación de capital en COP, cálculo de posición, Drawdown, R:R", status: "pending" },
  { id: 9, title: "Fase 9: Backtesting Lab", desc: "Motor cuantitativo reproducible, walk-forward, sin look-ahead bias", status: "pending" },
  { id: 10, title: "Fase 10: Chat Inteligente Contextual", desc: "Asistente QUANT AI conectado en tiempo real al estado del gráfico", status: "pending" },
  { id: 11, title: "Fase 11: Análisis Visual (Live Vision)", desc: "Compartir pantalla con el asistente, detección de patrones en vivo", status: "pending" },
  { id: 12, title: "Fase 12: Voz (Live Voice STT / TTS)", desc: "Conversación bidireccional por voz en español con acento local", status: "pending" },
  { id: 13, title: "Fase 13: Asistente Integrado en Vivo", desc: "Voz + Visión + Datos Cuantitativos en tiempo real en un solo panel", status: "pending" },
  { id: 14, title: "Fase 14: Seguridad, Pruebas y Despliegue", desc: "RLS exhaustivo, CI/CD GitHub Actions, Vercel & servidor Python", status: "pending" },
];

export function PhaseTracker() {
  return (
    <div className="rounded-xl border border-border bg-surface p-5 shadow-2xl">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
        <div>
          <h3 className="font-mono text-sm font-semibold tracking-wide text-white flex items-center space-x-2">
            <span>PLAN MAESTRO DE IMPLEMENTACIÓN (14 FASES)</span>
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">
            Metodología incremental rigurosa: cada fase es verificada matemáticamente y subida a GitHub.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="flex items-center space-x-1 text-quant-green">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Fases 1, 2 y 3 Listas</span>
          </span>
          <span className="text-gray-500">•</span>
          <span className="text-gray-400">11 Fases Restantes</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {PHASES.map((p) => {
          const isDone = p.status === "completed";

          return (
            <div
              key={p.id}
              className={`rounded-lg border p-3 transition-all ${
                isDone
                  ? "border-quant-green/40 bg-quant-green/5"
                  : "border-border bg-surface-card opacity-60"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  {isDone ? (
                    <CheckCircle2 className="h-4 w-4 text-quant-green shrink-0" />
                  ) : (
                    <Circle className="h-4 w-4 text-gray-600 shrink-0" />
                  )}
                  <h5 className="font-mono text-xs font-semibold text-white">
                    {p.title}
                  </h5>
                </div>
                {isDone && (
                  <span className="rounded bg-quant-green/20 px-1.5 py-0.5 font-mono text-[9px] font-bold text-quant-green uppercase tracking-wider">
                    Listo
                  </span>
                )}
              </div>
              <p className="mt-1.5 text-[11px] text-gray-400 pl-6 leading-tight">
                {p.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
