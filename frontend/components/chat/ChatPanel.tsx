"use client";

/**
 * ChatPanel.tsx — Fase 10 QUANT AI
 *
 * Asistente Cuantitativo Contextual en Tiempo Real.
 * Conectado dinámicamente al activo y temporalidad del gráfico activo.
 *
 * Características:
 *   - Inyección en tiempo real del snapshot cuantitativo (indicadores, SMC, liquidez, scanner).
 *   - Estricta separación epistémica: Observación (hechos) vs Hipótesis con invalidación explícita.
 *   - Botones de acción rápida para análisis instantáneo.
 *   - Renderizado limpio de respuestas estructuradas.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  MessageSquare,
  Send,
  Sparkles,
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Trash2,
  TrendingUp,
  Shield,
  Layers,
  Target,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  source?: string;
  model?: string;
  timestamp: string;
}

interface ChatPanelProps {
  currentSymbol?: string;
  currentInterval?: string;
}

// ---------------------------------------------------------------------------
// Quick Prompts
// ---------------------------------------------------------------------------

const QUICK_PROMPTS = [
  {
    label: "Estructura y Confluencia",
    prompt: "Analiza la estructura de mercado actual y la confluencia general del activo.",
    icon: <TrendingUp className="w-3 h-3 text-cyan-400" />,
  },
  {
    label: "Order Blocks & Liquidez",
    prompt: "¿Dónde se encuentran los Order Blocks activos y las piscinas de liquidez más relevantes?",
    icon: <Layers className="w-3 h-3 text-purple-400" />,
  },
  {
    label: "Hipótesis de Swing (R:R)",
    prompt: "Formula una hipótesis cuantitativa de swing trade con nivel de invalidación exacto y ratio R:R.",
    icon: <Target className="w-3 h-3 text-amber-400" />,
  },
  {
    label: "Gestión de Riesgo en COP",
    prompt: "¿Cómo debería gestionar el tamaño de posición para este activo con capital en pesos colombianos?",
    icon: <Shield className="w-3 h-3 text-emerald-400" />,
  },
];

// ---------------------------------------------------------------------------
// Markdown Parser & Formatter Component
// ---------------------------------------------------------------------------

function FormattedContent({ text }: { text: string }) {
  // Simple markdown renderer for headers, bold, and lists
  const lines = text.split("\n");

  return (
    <div className="space-y-1 text-xs leading-relaxed text-zinc-200">
      {lines.map((line, i) => {
        // Headers
        if (line.startsWith("### 🔬 OBSERVACIÓN")) {
          return (
            <div key={i} className="pt-2 pb-1 border-b border-blue-500/30 flex items-center gap-1.5 text-blue-400 font-bold">
              <span>🔬 OBSERVACIÓN (HECHOS VERIFICADOS)</span>
            </div>
          );
        }
        if (line.startsWith("### 💡 HIPÓTESIS")) {
          return (
            <div key={i} className="pt-2 pb-1 border-b border-amber-500/30 flex items-center gap-1.5 text-amber-400 font-bold">
              <span>💡 HIPÓTESIS (PROYECCIÓN CUANTITATIVA)</span>
            </div>
          );
        }
        if (line.startsWith("### 🛡️ GESTIÓN DE RIESGO")) {
          return (
            <div key={i} className="pt-2 pb-1 border-b border-emerald-500/30 flex items-center gap-1.5 text-emerald-400 font-bold">
              <span>🛡️ GESTIÓN DE RIESGO EN COP</span>
            </div>
          );
        }
        if (line.startsWith("### ")) {
          return (
            <h4 key={i} className="font-bold text-white pt-1">
              {line.replace("### ", "")}
            </h4>
          );
        }
        if (line.startsWith("#### ")) {
          return (
            <h5 key={i} className="font-semibold text-zinc-300 pt-0.5">
              {line.replace("#### ", "")}
            </h5>
          );
        }

        // List items
        if (line.startsWith("- ") || line.startsWith("* ")) {
          const raw = line.slice(2);
          // Highlight bold text
          const parts = raw.split(/(\*\*.*?\*\*|`.*?`)/g);
          return (
            <div key={i} className="flex items-start gap-1.5 pl-1">
              <span className="text-zinc-500 mt-0.5">•</span>
              <span className="flex-1">
                {parts.map((p, j) => {
                  if (p.startsWith("**") && p.endsWith("**")) {
                    return <strong key={j} className="text-white font-semibold">{p.slice(2, -2)}</strong>;
                  }
                  if (p.startsWith("`") && p.endsWith("`")) {
                    return <code key={j} className="bg-zinc-800 text-cyan-300 px-1 py-0.2 rounded font-mono text-[11px]">{p.slice(1, -1)}</code>;
                  }
                  return p;
                })}
              </span>
            </div>
          );
        }

        // Empty lines
        if (!line.trim()) {
          return <div key={i} className="h-1" />;
        }

        // Normal paragraph
        const parts = line.split(/(\*\*.*?\*\*|`.*?`)/g);
        return (
          <p key={i}>
            {parts.map((p, j) => {
              if (p.startsWith("**") && p.endsWith("**")) {
                return <strong key={j} className="text-white font-semibold">{p.slice(2, -2)}</strong>;
              }
              if (p.startsWith("`") && p.endsWith("`")) {
                return <code key={j} className="bg-zinc-800 text-cyan-300 px-1 py-0.2 rounded font-mono text-[11px]">{p.slice(1, -1)}</code>;
              }
              return p;
            })}
          </p>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main ChatPanel
// ---------------------------------------------------------------------------

export default function ChatPanel({
  currentSymbol = "BTCUSDT",
  currentInterval = "1d",
}: ChatPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial",
      role: "assistant",
      content:
        `Hola, soy tu Asistente Cuantitativo QUANT AI. ` +
        `Estoy conectado en tiempo real al activo **${currentSymbol}** (${currentInterval}).\n\n` +
        `Puedo analizar estructura de mercado, zonas SMC (Order Blocks, FVG), barridos de liquidez, ` +
        `confluencia técnica y formular hipótesis con niveles exactos de invalidación y cálculo de riesgo en COP.\n\n` +
        `Usa los botones de acción rápida o escribe tu consulta a continuación.`,
      source: "quantitative_expert_system",
      model: "quant-expert-system-v1",
      timestamp: new Date().toLocaleTimeString("es-CO"),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (expanded) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, expanded]);

  const handleSendMessage = useCallback(
    async (textToSend?: string) => {
      const query = textToSend || input;
      if (!query.trim() || loading) return;

      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: query.trim(),
        timestamp: new Date().toLocaleTimeString("es-CO"),
      };

      setMessages((prev) => [...prev, userMsg]);
      if (!textToSend) setInput("");
      setLoading(true);

      try {
        const historyPayload = messages.map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const res = await fetch("/api/v1/chat/message", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: query.trim(),
            symbol: currentSymbol,
            interval: currentInterval,
            market: currentSymbol.endsWith("USDT") ? "crypto" : "stock",
            history: historyPayload.slice(-6),
          }),
        });

        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        const assistantMsg: Message = {
          id: `asst-${Date.now()}`,
          role: "assistant",
          content: data.response,
          source: data.source,
          model: data.model,
          timestamp: new Date().toLocaleTimeString("es-CO"),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        const errorMsg: Message = {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `⚠️ Error al comunicarse con el asistente: ${err instanceof Error ? err.message : "Error desconocido"}`,
          source: "system",
          timestamp: new Date().toLocaleTimeString("es-CO"),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [input, loading, messages, currentSymbol, currentInterval]
  );

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="border border-indigo-500/30 rounded-xl bg-zinc-900/90 overflow-hidden shadow-2xl">
      {/* Header */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between p-3 bg-zinc-800/80 hover:bg-zinc-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-indigo-500/20 text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="text-sm font-semibold text-indigo-300">
            Asistente QUANT AI — Contexto en Vivo ({currentSymbol} • {currentInterval})
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 font-mono">
            ACTIVO
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-zinc-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-zinc-400" />
        )}
      </button>

      {expanded && (
        <div className="flex flex-col h-[520px]">
          {/* Quick Action Pills */}
          <div className="p-2.5 bg-zinc-800/50 border-b border-zinc-700/60 flex items-center gap-1.5 overflow-x-auto">
            {QUICK_PROMPTS.map((qp, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(qp.prompt)}
                disabled={loading}
                className="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-700/70 hover:bg-zinc-700 disabled:opacity-50 text-[11px] text-zinc-200 rounded-full whitespace-nowrap transition-colors border border-zinc-600/50"
              >
                {qp.icon}
                <span>{qp.label}</span>
              </button>
            ))}
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-2.5 ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {m.role === "assistant" && (
                  <div className="w-6 h-6 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5 text-indigo-400" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-lg p-3 ${
                    m.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-none"
                      : "bg-zinc-800/90 border border-zinc-700/70 rounded-bl-none"
                  }`}
                >
                  {m.role === "assistant" && m.source && (
                    <div className="flex items-center justify-between text-[10px] text-zinc-500 mb-1 pb-1 border-b border-zinc-700/40">
                      <span>{m.model || "QUANT AI"}</span>
                      <span>{m.timestamp}</span>
                    </div>
                  )}

                  {m.role === "assistant" ? (
                    <FormattedContent text={m.content} />
                  ) : (
                    <p className="text-xs leading-relaxed">{m.content}</p>
                  )}
                </div>

                {m.role === "user" && (
                  <div className="w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <User className="w-3.5 h-3.5 text-zinc-300" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 p-3 bg-zinc-800/40 rounded-lg text-xs text-zinc-400 border border-zinc-700/40">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                <span>Analizando contexto cuantitativo de {currentSymbol} y generando respuesta...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input & Footer */}
          <div className="p-2.5 bg-zinc-800/70 border-t border-zinc-700/60">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={`Pregunta a QUANT AI sobre ${currentSymbol} (${currentInterval})...`}
                disabled={loading}
                className="flex-1 bg-zinc-700/80 border border-zinc-600 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-400 focus:outline-none focus:border-indigo-500"
              />

              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg transition-colors flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={clearChat}
                title="Limpiar chat"
                className="p-2 bg-zinc-700 hover:bg-zinc-600 text-zinc-400 hover:text-white rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
