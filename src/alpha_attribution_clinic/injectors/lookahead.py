"""
Lookahead bias injector.
前视偏差注入器。

This injector uses future information in feature computation,
which would be impossible in live trading.
此注入器在特征计算中使用未来信息，这在实盘交易中是不可能的。
"""

import pandas as pd
import numpy as np
from typing import Any
from .base import BaseInjector


class LookaheadInjector(BaseInjector):
    """
    Inject lookahead bias by using future returns in features.

    Anti-pattern: Computing features using data that wouldn't be
    available at decision time.

    Example of what this simulates:
    - Using close price at time t to make decision at time t
      (should use t-1)
    - Using future returns as part of feature computation
    - Peeking at next-day volatility
    """

    name = "lookahead"
    description = "Uses future information in feature computation"

    def __init__(self, lookahead_days: int = 1):
        """
        Parameters
        ----------
        lookahead_days : int
            How many days of future data to "peek" at
        """
        self.lookahead_days = lookahead_days
        self._injection_applied = False

    def inject(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Add features that use future information.

        This creates a "magic" feature that perfectly predicts returns
        because it literally uses future data.
        """
        df = data.copy()

        if "close" not in df.columns:
            raise ValueError("Data must have 'close' column")

        df = df.reset_index()
        df = df.sort_values(["asset_id", "date"])

        future_returns = (
            df.groupby("asset_id")["close"]
            .pct_change(periods=self.lookahead_days)
            .shift(-self.lookahead_days)
        )
        df["signal_lookahead"] = future_returns

        noise = np.random.normal(0, 0.001, len(df))
        df["signal_lookahead"] = df["signal_lookahead"] + noise

        df = df.set_index(["date", "asset_id"])
        self._injection_applied = True

        return df

    def get_injection_metadata(self) -> dict[str, Any]:
        return {
            "injector": self.name,
            "lookahead_days": self.lookahead_days,
            "affected_columns": ["signal_lookahead"],
            "description": f"Feature uses {self.lookahead_days}-day future returns",
        }


def compute_clean_momentum(data: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """
    Compute momentum the CORRECT way: using only past data.

    This is the clean baseline for comparison.
    使用正确方式计算动量：仅使用过去数据。
    """
    df = data.copy()
    df = df.reset_index()
    df = df.sort_values(["asset_id", "date"])

    df["signal_clean"] = (
        df.groupby("asset_id")["close"]
        .pct_change(periods=lookback)
    )

    df = df.set_index(["date", "asset_id"])
    return df
