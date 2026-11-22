"""Financial Spanish Text Normalizer for Speech — Fase 12 QUANT AI.

Normaliza texto cuantitativo con notación financiera y Markdown a español fonético natural (Colombia)
para que la síntesis de voz (TTS) suene clara, fluida y profesional.
"""

from __future__ import annotations

import re


def normalize_text_for_speech(text: str) -> str:
    """Convierte texto cuantitativo/Markdown a texto limpio y fonético en español.

    Ejemplos:
      - 'COP $50,000,000' -> 'cincuenta millones de pesos colombianos'
      - 'R:R 1:2.5' -> 'ratio riesgo beneficio uno a dos punto cinco'
      - 'EMA 20' -> 'media móvil exponencial 20'
      - 'BOS' -> 'ruptura de estructura'
    """
    if not text:
        return ""

    t = text

    # 1. Eliminar Emojis y símbolos decorativos
    t = re.sub(r"[🔬💡🛡️📈📉🎯🟣✓✗⚠•\*\#\`_~]", " ", t)

    # 2. Expandir acrónimos institucionales a lenguaje hablado en español
    replacements = [
        (r"\bEMA\b", "media móvil exponencial"),
        (r"\bRSI\b", "índice de fuerza relativa"),
        (r"\bMACD\b", "convergencia divergencia de medias"),
        (r"\bATR\b", "rango verdadero promedio"),
        (r"\bBOS\b", "ruptura de estructura"),
        (r"\bCHOCH\b", "cambio de carácter"),
        (r"\bFVG\b", "desequilibrio o fair value gap"),
        (r"\bOrder Blocks?\b", "bloque de órdenes"),
        (r"\bOrder block\b", "bloque de órdenes"),
        (r"\bSSL\b", "liquidez de venta"),
        (r"\bBSL\b", "liquidez de compra"),
        (r"\bPDH\b", "máximo del día anterior"),
        (r"\bPDL\b", "mínimo del día anterior"),
        (r"\bPWH\b", "máximo de la semana anterior"),
        (r"\bPWL\b", "mínimo de la semana anterior"),
        (r"\bEQH\b", "máximos iguales"),
        (r"\bEQL\b", "mínimos iguales"),
        (r"\bHH\b", "máximo más alto"),
        (r"\bHL\b", "mínimo más alto"),
        (r"\bLH\b", "máximo más bajo"),
        (r"\bLL\b", "mínimo más bajo"),
        (r"\bMTF\b", "multi temporalidad"),
        (r"\bR:R\s*([0-9\.]+)", r"ratio riesgo beneficio \1"),
        (r"\b1:([0-9\.]+)", r"uno a \1"),
        (r"COP\s*\$?\s*([0-9\.\,]+)", r"\1 pesos colombianos"),
        (r"USD\s*\$?\s*([0-9\.\,]+)", r"\1 dólares"),
        (r"\$([0-9\.\,]+)\s*COP", r"\1 pesos colombianos"),
    ]

    for pattern, replacement in replacements:
        t = re.sub(pattern, replacement, t, flags=re.IGNORECASE)

    # 3. Limpiar espacios múltiples y saltos de línea
    t = re.sub(r"\n+", ". ", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\.\s*\.", ".", t)

    return t.strip()
