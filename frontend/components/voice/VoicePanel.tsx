"use client";

/**
 * VoicePanel.tsx — Fase 12 QUANT AI
 *
 * Módulo de Voz Bidireccional en Vivo (STT / TTS).
 * Permite al operador conversar verbalmente con el Asistente Cuantitativo
 * en español con acento local (Colombia), conectado en tiempo real al gráfico.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  RefreshCw,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Radio,
  StopCircle,
} from "lucide-react";

interface VoicePanelProps {
  currentSymbol?: string;
  currentInterval?: string;
}

interface VoiceTurn {
  userText: string;
  assistantText: string;
  timestamp: string;
}

export default function VoicePanel({
  currentSymbol = "BTCUSDT",
  currentInterval = "1d",
}: VoicePanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [lastTurn, setLastTurn] = useState<VoiceTurn | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Inicializar Web Speech Recognition
  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "es-CO"; // Español de Colombia

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        let currentText = "";
        for (let i = 0; i < event.results.length; i++) {
          currentText += event.results[i][0].transcript;
        }
        setTranscript(currentText);
      };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onerror = (event: any) => {
        if (event.error !== "no-speech") {
          setError(`Error de micrófono: ${event.error}`);
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  // Función para reproducir texto por voz (TTS del navegador con voz es-CO o backend)
  const speakText = useCallback(
    (textToSpeak: string) => {
      if (!autoSpeak) return;

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();

        // Limpiar markdown básico para fonética
        const clean = textToSpeak
          .replace(/[#*`_~🔬💡🛡️]/g, "")
          .replace(/BOS/g, "ruptura de estructura")
          .replace(/EMA/g, "media móvil")
          .replace(/RSI/g, "índice de fuerza relativa")
          .replace(/R:R/g, "ratio riesgo beneficio")
          .replace(/COP/g, "pesos colombianos");

        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.lang = "es-CO";
        utterance.rate = 1.05;

        // Intentar seleccionar voz en español
        const voices = window.speechSynthesis.getVoices();
        const spanishVoice =
          voices.find((v) => v.lang.startsWith("es-CO")) ||
          voices.find((v) => v.lang.startsWith("es-419")) ||
          voices.find((v) => v.lang.startsWith("es"));
        if (spanishVoice) {
          utterance.voice = spanishVoice;
        }

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);

        window.speechSynthesis.speak(utterance);
      }
    },
    [autoSpeak]
  );

  const stopSpeaking = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  // Enviar pregunta transcrita al backend
  const sendVoiceQuery = useCallback(
    async (queryText: string) => {
      if (!queryText.trim()) return;
      setLoading(true);
      setError(null);

      try {
        const res = await fetch("/api/v1/chat/message", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: queryText,
            symbol: currentSymbol,
            interval: currentInterval,
            market: currentSymbol.endsWith("USDT") ? "crypto" : "stock",
          }),
        });

        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        const turn: VoiceTurn = {
          userText: queryText,
          assistantText: data.response,
          timestamp: new Date().toLocaleTimeString("es-CO"),
        };
        setLastTurn(turn);
        speakText(data.response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al procesar consulta de voz");
      } finally {
        setLoading(false);
      }
    },
    [currentSymbol, currentInterval, speakText]
  );

  const toggleListening = () => {
    setError(null);
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      if (transcript.trim()) {
        sendVoiceQuery(transcript);
      }
    } else {
      setTranscript("");
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch {
        setError("No se pudo iniciar el micrófono. Verifica los permisos del navegador.");
      }
    }
  };

  return (
    <div className="border border-rose-500/30 rounded-xl bg-zinc-900/90 overflow-hidden shadow-2xl">
      {/* Header */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between p-3 bg-zinc-800/80 hover:bg-zinc-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-rose-500/20 text-rose-400">
            <Mic className="w-4 h-4" />
          </div>
          <span className="text-sm font-semibold text-rose-300">
            Live Voice — Conversación Bidireccional por Voz (es-CO)
          </span>
          {isListening && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-red-500/20 text-red-400 font-mono animate-pulse">
              <Radio className="w-2.5 h-2.5" /> ESCUCHANDO...
            </span>
          )}
          {isSpeaking && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 font-mono animate-pulse">
              <Volume2 className="w-2.5 h-2.5" /> HABLANDO...
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
        <div className="p-4 space-y-4 border-t border-zinc-700/60">
          {/* Controls Bar */}
          <div className="flex items-center justify-between bg-zinc-800/60 p-3 rounded-lg border border-zinc-700/60">
            <div className="flex items-center gap-3">
              {/* Mic Toggle Button */}
              <button
                onClick={toggleListening}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-lg ${
                  isListening
                    ? "bg-red-600 hover:bg-red-500 text-white animate-pulse"
                    : "bg-rose-600 hover:bg-rose-500 text-white"
                }`}
              >
                {isListening ? (
                  <>
                    <StopCircle className="w-4 h-4" />
                    <span>Detener y Enviar</span>
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4" />
                    <span>Hablar con QUANT AI</span>
                  </>
                )}
              </button>

              {/* Stop Speaking Button */}
              {isSpeaking && (
                <button
                  onClick={stopSpeaking}
                  className="flex items-center gap-1 px-2.5 py-1.5 bg-zinc-700 hover:bg-zinc-600 text-zinc-300 text-xs rounded-lg transition-colors"
                >
                  <VolumeX className="w-3.5 h-3.5" />
                  <span>Silenciar</span>
                </button>
              )}
            </div>

            {/* Auto-speak Toggle */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoSpeak((p) => !p)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-colors ${
                  autoSpeak ? "bg-rose-500/20 text-rose-300" : "bg-zinc-800 text-zinc-500"
                }`}
              >
                {autoSpeak ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                <span>Lectura Automática</span>
              </button>
            </div>
          </div>

          {/* Transcript in Progress */}
          {transcript && (
            <div className="bg-zinc-800/80 p-3 rounded-lg border border-zinc-700 space-y-1">
              <div className="flex items-center justify-between text-[11px] text-zinc-400">
                <span className="font-semibold text-rose-400">Transcripción en Vivo (es-CO):</span>
                <span>{currentSymbol} • {currentInterval}</span>
              </div>
              <p className="text-xs text-white font-medium italic">&quot;{transcript}&quot;</p>
            </div>
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex items-center gap-2 p-3 bg-zinc-800/40 rounded-lg text-xs text-zinc-400 border border-zinc-700/40">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-rose-400" />
              <span>Procesando audio y consultando motores cuantitativos...</span>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Last Turn Result */}
          {lastTurn && (
            <div className="space-y-3 pt-1">
              <div className="bg-zinc-800/40 p-2.5 rounded-lg border border-zinc-700/60 text-xs">
                <span className="text-zinc-500 block text-[10px]">Tú dijiste:</span>
                <span className="text-zinc-200 font-medium">&quot;{lastTurn.userText}&quot;</span>
              </div>

              <div className="bg-zinc-800/90 p-3.5 rounded-lg border border-zinc-700 space-y-2">
                <div className="flex items-center justify-between pb-1.5 border-b border-zinc-700/60">
                  <div className="flex items-center gap-1.5 text-rose-400 text-xs font-bold">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Respuesta Cuantitativa</span>
                  </div>
                  <span className="text-[10px] text-zinc-500">{lastTurn.timestamp}</span>
                </div>

                <div className="text-xs text-zinc-200 leading-relaxed whitespace-pre-line max-h-60 overflow-y-auto">
                  {lastTurn.assistantText}
                </div>
              </div>
            </div>
          )}

          <audio ref={audioPlayerRef} className="hidden" />
        </div>
      )}
    </div>
  );
}
