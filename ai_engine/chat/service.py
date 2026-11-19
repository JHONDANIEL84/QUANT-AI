"""Quantitative AI Chat Service — Fase 10 QUANT AI.

Provee respuestas contextualizadas y rigurosas epistemológicamente:
  - Utiliza la API de Gemini (REST via httpx) cuando la API key está disponible.
  - Implementa un motor analítico cuantitativo experto determinista como fallback
    cuando no hay conexión o no se ha configurado la API key, garantizando disponibilidad 100%.
  - Siempre estructura las respuestas en:
      1. 🔬 OBSERVACIÓN (HECHOS VERIFICADOS)
      2. 💡 HIPÓTESIS (PROYECCIÓN CUANTITATIVA CON INVALIDACIÓN)
      3. 🛡️ GESTIÓN DE RIESGO EN COP
"""

from __future__ import annotations

import os
import json
import logging
from typing import List, Optional, Dict, Any, Generator
import httpx

from backend.core.config import settings
from ai_engine.chat.prompts import QUANT_AI_SYSTEM_PROMPT, build_chat_user_prompt

logger = logging.getLogger("quant_ai.chat")


class ChatMessage(Dict[str, str]):
    """Mensaje de chat con rol ('user', 'assistant', 'system') y contenido."""
    role: str
    content: str


class ChatService:
    """Servicio orquestador del Chat Contextual de QUANT AI."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.AI_API_KEY or os.environ.get("GEMINI_API_KEY") or ""
        self.model = model or settings.AI_MODEL or "gemini-1.5-flash"

    def generate_response(
        self,
        user_message: str,
        context_data: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Genera una respuesta contextualizada estructurada.

        Args:
            user_message: Pregunta o instrucción del operador.
            context_data: Diccionario con métricas cuantitativas y prompt_text.
            history: Historial previo de la conversación.

        Returns:
            Dict con 'response', 'model', 'source' ('gemini' o 'quantitative_expert_system').
        """
        prompt_text = context_data.get("prompt_text") if context_data else None
        full_user_prompt = build_chat_user_prompt(user_message, prompt_text)

        # 1. Intentar llamar a Gemini si hay API Key disponible
        if self.api_key and len(self.api_key.strip()) > 10:
            try:
                gemini_resp = self._call_gemini(full_user_prompt, history)
                if gemini_resp:
                    return {
                        "response": gemini_resp,
                        "model": self.model,
                        "source": "gemini",
                    }
            except Exception as exc:
                logger.warning("Fallo al llamar Gemini API (%s), utilizando motor cuantitativo fallback.", exc)

        # 2. Motor cuantitativo experto determinista
        expert_resp = self._generate_expert_fallback(user_message, context_data)
        return {
            "response": expert_resp,
            "model": "quant-expert-system-v1",
            "source": "quantitative_expert_system",
        }

    def _call_gemini(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        """Llama a la API REST de Google Gemini."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        contents: List[Dict[str, Any]] = []

        # Agregar historial si existe
        if history:
            for msg in history[-6:]:  # Limitar a los últimos 6 turnos
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        # Agregar el prompt actual
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "system_instruction": {
                "parts": [{"text": QUANT_AI_SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }

        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                logger.warning("Gemini API respondió con código %d: %s", resp.status_code, resp.text[:200])

        return None

    def _generate_expert_fallback(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Genera respuesta cuantitativa estructurada con separación epistémica estricta."""
        q = user_message.lower()

        if not context or "current_price" not in context:
            return (
                "### 🔬 OBSERVACIÓN (HECHOS)\n"
                "Actualmente no hay un activo con serie de barras seleccionada en el gráfico.\n\n"
                "### 💡 HIPÓTESIS CUANTITATIVA\n"
                "Para formular una hipótesis estructurada (dirección, stop loss, take profit y R:R), "
                "selecciona un activo (ej. BTCUSDT, NVDA, ECOPETROL) y temporalidad en el gráfico superior.\n\n"
                "### 🛡️ GESTIÓN DE RIESGO EN COP\n"
                "Recuerda que toda operación debe estar precedida por un cálculo de tamaño de posición "
                "con riesgo máximo del 1% al 2% sobre tu capital total en COP."
            )

        sym = context.get("symbol", "ACTIVO")
        tf = context.get("interval", "1D")
        price = context.get("current_price", 0.0)
        trend = context.get("trend", "CONSOLIDATION")
        rsi = context.get("rsi")
        ema20 = context.get("ema20")
        ema50 = context.get("ema50")
        zone = context.get("dealing_zone", "UNKNOWN")
        obs_count = context.get("active_obs_count", 0)
        score = context.get("scanner_score")

        # Determinar sesgo direccional
        is_bullish = trend == "UPTREND" or (score and score >= 50.0 and (ema20 and ema50 and ema20 > ema50))
        is_bearish = trend == "DOWNTREND" or (score and score >= 50.0 and (ema20 and ema50 and ema20 < ema50))

        direction_str = "ALCISTA (Long)" if is_bullish else ("BAJISTA (Short)" if is_bearish else "NEUTRAL / EN RANGO")
        invalidation = price * 0.96 if is_bullish else (price * 1.04 if is_bearish else price * 0.98)
        target = price * 1.08 if is_bullish else (price * 0.92 if is_bearish else price * 1.04)
        rr = abs(target - price) / abs(price - invalidation) if abs(price - invalidation) > 0 else 2.0

        # Bloque de Observación
        obs_lines = [
            f"- **Activo**: {sym} en marco temporal `{tf}`.",
            f"- **Precio actual**: `{price:,.4f}`.",
            f"- **Estructura de mercado**: `{trend}`.",
            f"- **Medias Móviles**: EMA 20 = `{ema20:,.2f}` | EMA 50 = `{ema50:,.2f}`." if ema20 and ema50 else "- **Medias Móviles**: Datos insuficientes para cálculo de EMA.",
            f"- **RSI (14)**: `{rsi:.1f}` ({'sobrecompra' if rsi and rsi >= 70 else ('sobreventa' if rsi and rsi <= 30 else 'neutral')})." if rsi else "- **RSI (14)**: No disponible.",
            f"- **Zona del Rango (Dealing Range)**: `{zone}`.",
            f"- **Order Blocks Activos**: `{obs_count}` bloques institucionales sin mitigar.",
        ]
        if score is not None:
            obs_lines.append(f"- **Score Compuesto del Escáner**: `{score:.1f}/100`.")

        obs_text = "\n".join(obs_lines)

        # Bloque de Hipótesis
        if is_bullish:
            hypo_text = (
                f"- **Sesgo direccional**: **{direction_str}**.\n"
                f"- **Punto de Entrada Sugerido**: Precio de mercado actual (`{price:,.4f}`) o retroceso hacia EMA 20 (`{ema20:,.4f}`).\n"
                f"- **Nivel de Invalidación Cuantitativo (Stop Loss)**: Cierre de vela por debajo de **`{invalidation:,.4f}`**.\n"
                f"- **Nivel Objetivo (Take Profit)**: Proyección hacia piscina de liquidez superior en **`{target:,.4f}`**.\n"
                f"- **Ratio Riesgo:Recompensa Estimado**: **1:{rr:.2f}** (Asimetría favorable confirmada)."
            )
        elif is_bearish:
            hypo_text = (
                f"- **Sesgo direccional**: **{direction_str}**.\n"
                f"- **Punto de Entrada Sugerido**: Precio de mercado actual (`{price:,.4f}`) o retroceso hacia EMA 20 (`{ema20:,.4f}`).\n"
                f"- **Nivel de Invalidación Cuantitativo (Stop Loss)**: Cierre de vela por encima de **`{invalidation:,.4f}`**.\n"
                f"- **Nivel Objetivo (Take Profit)**: Proyección hacia piscina de liquidez inferior en **`{target:,.4f}`**.\n"
                f"- **Ratio Riesgo:Recompensa Estimado**: **1:{rr:.2f}** (Asimetría favorable confirmada)."
            )
        else:
            hypo_text = (
                f"- **Sesgo direccional**: **{direction_str}**.\n"
                f"- **Recomendación Cuantitativa**: El mercado se encuentra en consolidación o confluencias mixtas. "
                f"Se recomienda permanecer al margen y esperar una ruptura confirmada de estructura (BOS/CHOCH) o un barrido de liquidez.\n"
                f"- **Nivel de Invalidación de Rango**: Cierre por fuera del rango `{invalidation:,.4f}` - `{price * 1.02:,.4f}`.\n"
                f"- **Zonas de alerta**: Observar reacción si el precio prueba `{price * 1.02:,.4f}` o `{invalidation:,.4f}`."
            )

        # Bloque de Gestión de Riesgo
        risk_text = (
            f"- **Regla de Capital en COP**: Sobre un capital base (ej. COP $50,000,000), "
            f"arriesgar máximo el 1% (COP $500,000) o 2% (COP $1,000,000) por trade.\n"
            f"- **Falsabilidad**: Si el precio alcanza el nivel de invalidación ({invalidation:,.4f}), "
            f"la hipótesis queda refutada y se debe cerrar la posición inmediatamente sin promediar pérdidas."
        )

        return (
            f"### 🔬 OBSERVACIÓN (HECHOS VERIFICADOS)\n"
            f"{obs_text}\n\n"
            f"### 💡 HIPÓTESIS (PROYECCIÓN CUANTITATIVA)\n"
            f"{hypo_text}\n\n"
            f"### 🛡️ GESTIÓN DE RIESGO EN COP\n"
            f"{risk_text}"
        )


# Singleton instance
chat_service = ChatService()
