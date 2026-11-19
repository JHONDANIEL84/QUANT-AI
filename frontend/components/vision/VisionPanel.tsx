"use client";

/**
 * VisionPanel.tsx — Fase 11 QUANT AI
 *
 * Módulo de Análisis Visual Multimodal (Live Vision).
 * Permite capturar la pantalla, el gráfico activo o subir una imagen para
 * detectar patrones chartistas, zonas de Order Blocks y mechas de barrido
 * mediante IA multimodal y visión artificial.
 */

import React, { useState, useRef, useCallback } from "react";
import {
  Eye,
  Camera,
  Upload,
  RefreshCw,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Layers,
  Target,
  Sparkles,
  Shield,
  Lightbulb,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type VisualBias = "alcista" | "bajista" | "neutral";

interface DetectedVisualPattern {
  name: string;
  category: string;
  bias: VisualBias;
  confidence: number;
  description: string;
}

interface VisionAnalysisResponse {
  symbol: string;
  interval: string;
  dominant_bias: VisualBias;
  patterns_detected: DetectedVisualPattern[];
  observation: string;
  hypothesis: string;
  risk_guidance: string;
  source: string;
  model: string;
  timestamp: string;
}

interface VisionPanelProps {
  currentSymbol?: string;
  currentInterval?: string;
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function VisionPanel({
  currentSymbol = "BTCUSDT",
  currentInterval = "1d",
}: VisionPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState("");
  const [result, setResult] = useState<VisionAnalysisResponse | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. Capturar pantalla mediante Screen Share API
  const handleCaptureScreen = useCallback(async () => {
    setError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
        throw new Error("La API de captura de pantalla no está disponible en este navegador.");
      }

      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { displaySurface: "browser" },
      });

      const video = document.createElement("video");
      video.srcObject = stream;
      video.play();

      await new Promise((resolve) => {
        video.onloadedmetadata = resolve;
      });

      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);

      const b64 = canvas.toDataURL("image/png");
      setPreviewImage(b64);

      // Detener los tracks del stream
      stream.getTracks().forEach((t) => t.stop());
    } catch (err) {
      if (err instanceof Error && err.name !== "NotAllowedError") {
        setError(err.message);
      }
    }
  }, []);

  // 2. Subir imagen manual
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setPreviewImage(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  // 3. Ejecutar análisis visual
  const analyzeVision = useCallback(async () => {
    if (!previewImage) {
      setError("Por favor captura o sube una imagen del gráfico primero.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/v1/vision/analyze-frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_base64: previewImage,
          symbol: currentSymbol,
          interval: currentInterval,
          custom_prompt: customPrompt.trim() || undefined,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Error ${res.status}`);
      }

      const data: VisionAnalysisResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al procesar análisis visual");
    } finally {
      setLoading(false);
    }
  }, [previewImage, currentSymbol, currentInterval, customPrompt]);

  return (
    <div className="border border-violet-500/30 rounded-xl bg-zinc-900/90 overflow-hidden shadow-2xl">
      {/* Header */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between p-3 bg-zinc-800/80 hover:bg-zinc-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-violet-500/20 text-violet-400">
            <Eye className="w-4 h-4" />
          </div>
          <span className="text-sm font-semibold text-violet-300">
            Live Vision — Análisis Visual Multimodal del Gráfico
          </span>
          {result && (
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                result.dominant_bias === "alcista"
                  ? "bg-emerald-500/20 text-emerald-400"
                  : result.dominant_bias === "bajista"
                  ? "bg-red-500/20 text-red-400"
                  : "bg-zinc-500/20 text-zinc-400"
              }`}
            >
              {result.dominant_bias.toUpperCase()}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-zinc-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-zinc-400" />
        )}
      </button>

      {expanded && (
        <div className="p-3 space-y-4 border-t border-zinc-700/60">
          {/* Controls & Capture buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleCaptureScreen}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold rounded-lg transition-colors"
            >
              <Camera className="w-3.5 h-3.5" />
              <span>Capturar Pantalla / Gráfico</span>
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 text-zinc-200 text-xs font-semibold rounded-lg transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Subir Captura</span>
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />

            {previewImage && (
              <button
                onClick={() => {
                  setPreviewImage(null);
                  setResult(null);
                }}
                className="text-xs text-zinc-400 hover:text-red-400 ml-auto transition-colors"
              >
                Limpiar captura
              </button>
            )}
          </div>

          {/* Image Preview */}
          {previewImage && (
            <div className="space-y-3">
              <div className="relative rounded-lg overflow-hidden border border-zinc-700 bg-black max-h-56 flex items-center justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewImage}
                  alt="Captura del gráfico"
                  className="max-h-56 object-contain"
                />
              </div>

              {/* Custom Prompt */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Pregunta visual específica (ej. ¿Detectas absorción en los mínimos?)..."
                  className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500"
                />
                <button
                  onClick={analyzeVision}
                  disabled={loading}
                  className="flex items-center gap-1.5 px-4 py-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg transition-colors"
                >
                  {loading ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5" />
                  )}
                  <span>Analizar</span>
                </button>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-3 pt-2">
              {/* Detected Patterns Grid */}
              {result.patterns_detected.length > 0 && (
                <div>
                  <p className="text-xs text-zinc-400 font-semibold mb-1.5 flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-violet-400" />
                    <span>Patrones y Zonas Visuales Detectadas</span>
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {result.patterns_detected.map((p, idx) => (
                      <div
                        key={idx}
                        className="bg-zinc-800/80 p-2.5 rounded-lg border border-zinc-700/60 space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white">{p.name}</span>
                          <span className="text-[10px] font-mono text-zinc-400">
                            {(p.confidence * 100).toFixed(0)}% conf.
                          </span>
                        </div>
                        <p className="text-[11px] text-zinc-300 leading-relaxed">
                          {p.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Epistemic: Observation */}
              <div className="p-2.5 bg-blue-500/5 border border-blue-500/20 rounded-md">
                <div className="flex items-center gap-1.5 mb-1">
                  <Eye className="w-3 h-3 text-blue-400" />
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wide">
                    Observación Visual (Hechos)
                  </span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed whitespace-pre-line">
                  {result.observation}
                </p>
              </div>

              {/* Epistemic: Hypothesis */}
              <div className="p-2.5 bg-amber-500/5 border border-amber-500/20 rounded-md">
                <div className="flex items-center gap-1.5 mb-1">
                  <Lightbulb className="w-3 h-3 text-amber-400" />
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">
                    Hipótesis Visual (Proyección e Invalidación)
                  </span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed whitespace-pre-line">
                  {result.hypothesis}
                </p>
              </div>

              {/* Epistemic: Risk Guidance */}
              <div className="p-2.5 bg-emerald-500/5 border border-emerald-500/20 rounded-md">
                <div className="flex items-center gap-1.5 mb-1">
                  <Shield className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">
                    Gestión de Riesgo en COP
                  </span>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed whitespace-pre-line">
                  {result.risk_guidance}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
