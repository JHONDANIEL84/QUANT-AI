"""Abstract Base Strategy — Fase 9 QUANT AI.

Todas las estrategias deben implementar `generate_signals` de forma estrictamente causal:
la señal en el índice `i` solo puede basarse en datos de barras `0` a `i`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from data_providers.base.models import MarketBar
from quantitative_engine.backtesting.models import BacktestSignal


class BaseStrategy(ABC):
    """Clase base para estrategias de trading cuantitativo."""

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        self.params: Dict[str, Any] = params or {}

    @abstractmethod
    def generate_signal(
        self,
        current_idx: int,
        bars: List[MarketBar],
        active_position: Optional[str] = None,  # 'long', 'short', o None
    ) -> Optional[BacktestSignal]:
        """Evalúa las barras hasta `current_idx` (inclusive) y emite una señal si aplica.

        Principio causal: la estrategia NUNCA debe acceder a barras con índice > current_idx.
        """
        pass
