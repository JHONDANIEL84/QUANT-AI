"""Live Copilot Multimodal Orchestrator — Fase 13 QUANT AI.

Orquesta la integración en tiempo real de:
  - Voz (Speech-to-Text y Text-to-Speech)
  - Visión Multimodal (detección de figuras y zonas)
  - Datos Cuantitativos (Indicadores, Estructura, SMC, Liquidez, Scanner, Riesgo)
  - Sistema de Alertas Proactivas (Invalidaciones, mitigaciones de OB, barridos)
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from data_providers.base.models import MarketBar
from ai_engine.orchestration.models import (
    CopilotMode,
    CopilotAlert,
    AlertType,
    AlertSeverity,
    MultimodalTurnRequest,
    MultimodalTurnResponse,
)
from ai_engine.speech_to_text.models import TranscriptionRequest
from ai_engine.speech_to_text.transcriber import speech_transcriber
from ai_engine.text_to_speech.models import TTSRequest
from ai_engine.text_to_speech.synthesizer import tts_synthesizer
from ai_engine.vision.models import VisionAnalysisRequest
from ai_engine.vision.analyzer import vision_analyzer
from ai_engine.context.builder import build_chart_quantitative_context
from ai_engine.chat.service import chat_service
from quantitative_engine.smc.analyzer import run_smc_analysis
from quantitative_engine.smc.models import MitigationStatus
from quantitative_engine.liquidity.analyzer import run_liquidity_analysis
from quantitative_engine.scanner.evaluator import evaluate_asset_opportunity

logger = logging.getLogger("quant_ai.orchestration.copilot")


class LiveCopilotOrchestrator:
    """Orquestador central del Asistente Copiloto Integrado en Vivo."""

    def check_proactive_alerts(
        self,
        symbol: str,
        interval: str,
        bars: List[MarketBar],
        market: str = "crypto",
    ) -> List[CopilotAlert]:
        """Evalúa condiciones de alerta proactiva en el gráfico actual."""
        alerts: List[CopilotAlert] = []
        if len(bars) < 20:
            return alerts

        curr_bar = bars[-1]
        price = curr_bar.close

        # 1. Alerta de Oportunidad y Proximidad de Invalidación
        opp = evaluate_asset_opportunity(symbol, market, interval, bars)
        if opp and opp.invalidation_level:
            inv = opp.invalidation_level
            dist_pct = abs(price - inv) / price * 100.0

            if opp.direction.value == "BULLISH" and price <= inv:
                alerts.append(
                    CopilotAlert(
                        alert_type=AlertType.INVALIDATION_TRIGGERED,
                        severity=AlertSeverity.CRITICAL,
                        symbol=symbol,
                        interval=interval,
                        message=f"¡INVALIDACIÓN ALCISTA ALCANZADA! El precio ({price:,.2f}) cerró por debajo de {inv:,.2f}.",
                        price_level=inv,
                    )
                )
            elif opp.direction.value == "BEARISH" and price >= inv:
                alerts.append(
                    CopilotAlert(
                        alert_type=AlertType.INVALIDATION_TRIGGERED,
                        severity=AlertSeverity.CRITICAL,
                        symbol=symbol,
                        interval=interval,
                        message=f"¡INVALIDACIÓN BAJISTA ALCANZADA! El precio ({price:,.2f}) cerró por encima de {inv:,.2f}.",
                        price_level=inv,
                    )
                )
            elif dist_pct <= 1.2:
                alerts.append(
                    CopilotAlert(
                        alert_type=AlertType.INVALIDATION_NEAR,
                        severity=AlertSeverity.WARNING,
                        symbol=symbol,
                        interval=interval,
                        message=f"ALERTA DE RIESGO: Precio ({price:,.2f}) a solo {dist_pct:.1f}% del nivel de invalidación ({inv:,.2f}).",
                        price_level=inv,
                    )
                )

        # 2. Alerta de mitigación de Order Block activo
        smc = run_smc_analysis(symbol, interval, bars)
        for ob in smc.order_blocks:
            if ob.status == MitigationStatus.UNMITIGATED:
                if ob.bottom_price <= price <= ob.top_price:
                    alerts.append(
                        CopilotAlert(
                            alert_type=AlertType.OB_TESTED,
                            severity=AlertSeverity.INFO,
                            symbol=symbol,
                            interval=interval,
                            message=f"MITIGACIÓN EN CURSO: El precio ha ingresado al Order Block {ob.direction.value} [{ob.bottom_price:,.2f} - {ob.top_price:,.2f}].",
                            price_level=(ob.bottom_price + ob.top_price) / 2.0,
                        )
                    )
                    break

        # 3. Alerta de barrido de liquidez reciente
        liq = run_liquidity_analysis(symbol, interval, bars)
        if liq.sweeps:
            last_sw = liq.sweeps[-1]
            if len(bars) - 1 - last_sw.sweep_bar_index <= 2:
                alerts.append(
                    CopilotAlert(
                        alert_type=AlertType.LIQUIDITY_SWEPT,
                        severity=AlertSeverity.WARNING,
                        symbol=symbol,
                        interval=interval,
                        message=f"BARRIDO DE LIQUIDEZ RECIENTE: {last_sw.pool_type.value} en {last_sw.sweep_price:,.2f} con rechazo confirmado.",
                        price_level=last_sw.sweep_price,
                    )
                )

        return alerts

    def execute_multimodal_turn(
        self,
        req: MultimodalTurnRequest,
        bars: List[MarketBar],
    ) -> MultimodalTurnResponse:
        """Ejecuta un ciclo multimodal completo (Voz + Visión + Datos -> Respuesta y Audio)."""
        sym = req.symbol.upper()
        tf = req.interval

        # 1. Transcribir audio si está presente
        user_transcript: Optional[str] = None
        if req.audio_base64 and len(req.audio_base64.strip()) > 50:
            stt_req = TranscriptionRequest(
                audio_base64=req.audio_base64,
                format="webm",
                language="es-CO",
                prompt_hint=f"{sym} {tf} swing trading",
            )
            stt_res = speech_transcriber.transcribe(stt_req)
            user_transcript = stt_res.text

        # 2. Análisis visual si hay imagen
        visual_patterns_count = 0
        visual_bias_str: Optional[str] = None
        visual_findings_text = ""
        if req.image_base64 and len(req.image_base64.strip()) > 50:
            vis_req = VisionAnalysisRequest(
                image_base64=req.image_base64,
                symbol=sym,
                interval=tf,
                custom_prompt=req.text_prompt or user_transcript,
            )
            vis_res = vision_analyzer.analyze_frame(vis_req)
            visual_patterns_count = len(vis_res.patterns_detected)
            visual_bias_str = vis_res.dominant_bias.value
            visual_findings_text = (
                f"\n\n[HALLAZGOS VISUALES MULTIMODALES]:\n"
                f"- Sesgo visual dominante: {vis_res.dominant_bias.value.upper()}.\n"
                f"- Patrones detectados: {visual_patterns_count}.\n"
                f"- Observación visual: {vis_res.observation[:200]}..."
            )

        # 3. Determinar mensaje efectivo del operador
        effective_query = (
            user_transcript
            or req.text_prompt
            or f"Evalúa la confluencia institucional, estructura y niveles de invalidación para {sym} ({tf})."
        )

        # 4. Contexto cuantitativo del gráfico
        context_data = build_chart_quantitative_context(
            symbol=sym,
            interval=tf,
            bars=bars,
            market=req.market,
        )

        if visual_findings_text and "prompt_text" in context_data:
            context_data["prompt_text"] += visual_findings_text

        # 5. Evaluar alertas proactivas
        alerts = self.check_proactive_alerts(sym, tf, bars, req.market)

        # 6. Generar respuesta analítica
        chat_res = chat_service.generate_response(
            user_message=effective_query,
            context_data=context_data,
            history=req.history,
        )
        assistant_text = chat_res["response"]

        # Si hay alertas críticas, anteponerlas a la respuesta
        if alerts:
            critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
            if critical_alerts:
                prefix = "\n\n".join([f"🚨 **{a.message}**" for a in critical_alerts])
                assistant_text = f"{prefix}\n\n{assistant_text}"

        # 7. Síntesis de voz (TTS) de la respuesta
        tts_req = TTSRequest(text=assistant_text, voice_locale="es-CO", speed=1.0)
        tts_res = tts_synthesizer.synthesize(tts_req)

        # Determinar modo del copiloto
        mode = CopilotMode.ALERT if any(a.severity == AlertSeverity.CRITICAL for a in alerts) else CopilotMode.INTERACTING

        curr_p = bars[-1].close if bars else 0.0

        return MultimodalTurnResponse(
            symbol=sym,
            interval=tf,
            mode=mode,
            user_transcript=user_transcript,
            visual_patterns_detected_count=visual_patterns_count,
            visual_dominant_bias=visual_bias_str,
            assistant_response_text=assistant_text,
            assistant_audio_base64=tts_res.audio_base64,
            audio_duration_seconds=tts_res.duration_estimated_seconds,
            active_alerts=alerts,
            current_price=curr_p,
            trend=context_data.get("trend", "CONSOLIDATION"),
            dealing_zone=context_data.get("dealing_zone", "UNKNOWN"),
            scanner_score=context_data.get("scanner_score"),
        )


# Singleton
live_copilot = LiveCopilotOrchestrator()
