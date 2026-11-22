"use client";

/**
 * LiveAssistantHUD.tsx — Fase 13 QUANT AI
 *
 * Copiloto Integrado en Vivo (Heads-Up Display).
 * Fusión síncrona en un solo panel de:
 *   - Voz (STT en español de Colombia + TTS sintetizado)
 *   - Visión multimodal (detección de patrones y zonas en tiempo real)
 *   - Datos cuantitativos (indicadores, SMC, liquidez, scanner y riesgo)
 *   - Sistema de alertas proactivas (invalidaciones inminentes, mitigación de Order Blocks)
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Sparkles,
  Radio,
  Eye,
  Mic,
  Activity,
  AlertTriangle,
  Play,
  Volume2,
  VolumeX,
  RefreshCw,
  Shield,
  Layers,
  ChevronDown,
  ChevronUp,
  Cpu,
} from "lucide-react";

interface CopilotAlert {
  alert_type: string;
  severity: "info" | "warning" | "critical";
  symbol: string;
  interval: string;
  message: string;
  price_level?: number;
}

interface MultimodalTurnResponse {
  symbol: string;
  interval: string;
  mode: string;
  user_transcript?: string;
  visual_patterns_detected_count: number;
  visual_dominant_bias?: string;
  assistant_response_text: string;
  assistant_audio_base64?: string;
  audio_duration_seconds: number;
  active_alerts: CopilotAlert[];
  current_price: number;
  trend: string;
  dealing_zone: string;
  scanner_score?: number;
  timestamp: string;
}

interface LiveAssistantHUDProps {
  currentSymbol?: string;
  currentInterval?: string;
}

export default function LiveAssistantHUD({
  currentSymbol = "BTCUSDT",
  currentInterval = "1d",
}: LiveAssistantHUDProps) {
  const [expanded, setExpanded] = useState(true);
  const [isCopilotActive, setIsCopilotActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState<CopilotAlert[]>([]);
  const [turnResult, setTurnResult] = useState<MultimodalTurnResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoSpeak, setAutoSpeak] = useState(true);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 1. Monitoreo periódico de alertas proactivas
  const checkAlerts = useCallback(async () => {
    try {
      const res = await fetch(
        `/api/v1/copilot/alerts?symbol=${encodeURIComponent(currentSymbol)}&interval=${encodeURIComponent(currentInterval)}`
      );
      if (res.ok) {
        const data: CopilotAlert[] = await res.json();
        setAlerts(data);
      }
    } catch {
      // Monitoreo silencioso
    }
  }, [currentSymbol, currentInterval]);

  useEffect(() => {
    checkAlerts();
    const intervalId = setInterval(checkAlerts, 15000); // Cada 15 segundos
    return () => clearInterval(intervalId);
  }, [checkAlerts]);

  // 2. Ejecutar auditoría multimodal unificada
  const runMultimodalAudit = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Intentar capturar canvas de gráfico si está disponible
      let canvasImageB64: string | undefined = undefined;
      const chartCanvas = document.querySelector("canvas");
      if (chartCanvas) {
        try {
          canvasImageB64 = chartCanvas.toDataURL("image/png");
        } catch {
          // Cross-origin fallback
        }
      }

      const res = await fetch("/api/v1/copilot/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: currentSymbol,
          interval: currentInterval,
          market: currentSymbol.endsWith("USDT") ? "crypto" : "stock",
          image_base64: canvasImageB64,
          text_prompt: `Auditoría integral del copiloto: evalúa confluencia técnica, SMC, liquidez e invalidación para ${currentSymbol}.`,
        }),
      });

      if (!res.ok) {
        throw new Error(`Error ${res.status}: ${res.statusText}`);
      }

      const data: MultimodalTurnResponse = await res.json();
      setTurnResult(data);
      setAlerts(data.active_alerts);

      // Reproducir audio si está habilitado
      if (autoSpeak && data.assistant_audio_base64 && audioRef.current) {
        audioRef.current.src = `data:audio/wav;base64,${data.assistant_audio_base64}`;
        audioRef.current.play().catch(() => {});
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al ejecutar copiloto");
    } finally {
      setLoading(false);
    }
  }, [currentSymbol, currentInterval, autoSpeak]);

  return (
    <div className="border border-cyan-500/40 rounded-xl bg-zinc-950/95 overflow-hidden shadow-2xl backdrop-blur-md">
      {/* Header HUD */}
      <div className="flex items-center justify-between p-3 bg-zinc-900/90 border-b border-zinc-800">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-white tracking-wide uppercase">
                Copiloto QUANT AI en Vivo
              </span>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                {currentSymbol} • {currentInterval}
              </span>
            </div>
            <span className="text-[10px] text-zinc-400">
              Fusión Multimodal: Voz (es-CO) + Visión + Datos Cuantitativos
            </span>
          </div>
        </div>

        {/* Telemetry Dots */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-3 text-[10px] text-zinc-400 font-mono">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
              DATOS
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-violet-500" />
              VISIÓN
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
              VOZ
            </span>
          </div>

          <button
            onClick={() => setExpanded((p) => !p)}
            className="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="p-3.5 space-y-3">
          {/* Proactive Alerts Banner */}
          {alerts.length > 0 && (
            <div className="space-y-1.5">
              {alerts.map((a, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2 p-2.5 rounded-lg text-xs font-medium border ${
                    a.severity === "critical"
                      ? "bg-red-500/15 border-red-500/40 text-red-300 animate-pulse"
                      : a.severity === "warning"
                      ? "bg-amber-500/15 border-amber-500/40 text-amber-300"
                      : "bg-blue-500/15 border-blue-500/40 text-blue-300"
                  }`}
                >
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                  <span className="flex-1">{a.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* Action Row */}
          <div className="flex flex-wrap items-center justify-between gap-2 bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800">
            <button
              onClick={runMultimodalAudit}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg transition-all shadow-lg"
            >
              {loading ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              <span>Auditar Gráfico Completo Ahora</span>
            </button>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setAutoSpeak((p) => !p)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors border ${
                  autoSpeak
                    ? "bg-cyan-500/15 border-cyan-500/30 text-cyan-300"
                    : "bg-zinc-800 border-zinc-700 text-zinc-500"
                }`}
              >
                {autoSpeak ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">Audio Copiloto</span>
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Multimodal Turn Result */}
          {turnResult && (
            <div className="space-y-3 pt-1">
              {/* Telemetry Metrics Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                <div className="bg-zinc-900/80 p-2 rounded-lg border border-zinc-800">
                  <span className="text-[10px] text-zinc-500 block">Precio Actual</span>
                  <span className="font-mono font-bold text-white">
                    {turnResult.current_price.toLocaleString("es-CO", { maximumFractionDigits: 4 })}
                  </span>
                </div>
                <div className="bg-zinc-900/80 p-2 rounded-lg border border-zinc-800">
                  <span className="text-[10px] text-zinc-500 block">Estructura</span>
                  <span className="font-mono font-bold text-cyan-400">{turnResult.trend}</span>
                </div>
                <div className="bg-zinc-900/80 p-2 rounded-lg border border-zinc-800">
                  <span className="text-[10px] text-zinc-500 block">Zona SMC</span>
                  <span className="font-mono font-bold text-purple-400">{turnResult.dealing_zone}</span>
                </div>
                <div className="bg-zinc-900/80 p-2 rounded-lg border border-zinc-800">
                  <span className="text-[10px] text-zinc-500 block">Score Scanner</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {turnResult.scanner_score ? `${turnResult.scanner_score.toFixed(0)}/100` : "N/A"}
                  </span>
                </div>
              </div>

              {/* Epistemic Response Feed */}
              <div className="bg-zinc-900/90 p-3.5 rounded-lg border border-zinc-800 space-y-2">
                <div className="flex items-center justify-between pb-1.5 border-b border-zinc-800 text-xs">
                  <div className="flex items-center gap-1.5 text-cyan-400 font-bold">
                    <Activity className="w-3.5 h-3.5" />
                    <span>Dictamen Unificado del Copiloto</span>
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono">
                    {new Date(turnResult.timestamp).toLocaleTimeString("es-CO")}
                  </span>
                </div>

                <div className="text-xs text-zinc-200 leading-relaxed whitespace-pre-line max-h-72 overflow-y-auto">
                  {turnResult.assistant_response_text}
                </div>
              </div>
            </div>
          )}

          <audio ref={audioRef} className="hidden" />
        </div>
      )}
    </div>
  );
}
