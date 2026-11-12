"""Volume Weighted Average Price (VWAP) and Anchored VWAP implementation.
Formulas:
    TypicalPrice = (High + Low + Close) / 3
    VWAP = Cumulative(TypicalPrice * Volume) / Cumulative(Volume)
"""

from typing import List, Optional
import pandas as pd
import numpy as np


def compute_vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Computes standard cumulative VWAP over entire series."""
    typical_price = (high + low + close) / 3.0
    price_volume = typical_price * volume

    cum_price_volume = price_volume.cumsum()
    cum_volume = volume.cumsum()

    # Avoid division by zero
    vwap = cum_price_volume / cum_volume.replace(0, np.nan)
    return vwap


def compute_anchored_vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    anchor_index: int = 0,
) -> pd.Series:
    """Computes Anchored VWAP starting from a specific bar index."""
    typical_price = (high + low + close) / 3.0
    price_volume = typical_price * volume

    # Slice from anchor
    pv_sliced = price_volume.iloc[anchor_index:].cumsum()
    v_sliced = volume.iloc[anchor_index:].cumsum()

    anchored = pv_sliced / v_sliced.replace(0, np.nan)

    # Pad prefix with NaNs
    prefix = pd.Series([np.nan] * anchor_index, index=high.index[:anchor_index])
    return pd.concat([prefix, anchored])


def compute_vwap_list(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> List[Optional[float]]:
    """Returns JSON-serializable list of VWAP floats."""
    vwap_series = compute_vwap(high, low, close, volume)
    return [None if np.isnan(v) else round(float(v), 4) for v in vwap_series]
