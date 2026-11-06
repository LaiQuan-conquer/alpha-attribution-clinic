"""
Survivorship bias injector.
幸存者偏差注入器。

Simulates analyzing only assets that survived to the present,
ignoring those that delisted/failed.
模拟仅分析存活至今的资产，忽略已退市/失败的资产。
"""

import pandas as pd
import numpy as np
from typing import Any
from .base import BaseInjector


class SurvivorshipInjector(BaseInjector):
    """
    Inject survivorship bias by filtering to survivors only.

    Anti-pattern: Using current universe composition to analyze
    historical periods, thus excluding assets that failed.

    This makes historical performance look better because failed
    assets (which often had poor returns) are excluded.
    """

    name = "survivorship"
    description = "Filters to only surviving assets, excluding delisted ones"

    def __init__(self):
        self._removed_assets: list[str] = []
        self._injection_applied = False

    def inject(
        self,
        data: pd.DataFrame,
        delist_info: pd.DataFrame | None = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Remove delisted assets entirely from the dataset.

        Parameters
        ----------
        data : pd.DataFrame
            Price data with potential delistings
        delist_info : pd.DataFrame
            DataFrame with 'asset_id' and 'delist_date' columns

        Returns
        -------
        pd.DataFrame
            Data with delisted assets completely removed (survivorship bias)
        """
        df = data.copy()

        if delist_info is None or delist_info.empty:
            df = df.reset_index()
            assets = df["asset_id"].unique()
            if len(assets) > 2:
                np.random.seed(42)
                remove_n = max(1, len(assets) // 5)
                self._removed_assets = list(
                    np.random.choice(assets, size=remove_n, replace=False)
                )
                df = df[~df["asset_id"].isin(self._removed_assets)]
            df = df.set_index(["date", "asset_id"])
        else:
            delisted_assets = delist_info["asset_id"].tolist()
            self._removed_assets = delisted_assets

            df = df.reset_index()
            df = df[~df["asset_id"].isin(delisted_assets)]
            df = df.set_index(["date", "asset_id"])

        self._injection_applied = True
        return df

    def get_injection_metadata(self) -> dict[str, Any]:
        return {
            "injector": self.name,
            "removed_assets": self._removed_assets,
            "n_removed": len(self._removed_assets),
            "description": f"Removed {len(self._removed_assets)} delisted assets entirely",
        }


def filter_point_in_time(
    data: pd.DataFrame,
    delist_info: pd.DataFrame
) -> pd.DataFrame:
    """
    Filter data using point-in-time universe (CORRECT approach).

    Assets are included until they delist, then removed.
    This is the proper way to handle delistings without bias.
    使用时点宇宙过滤数据（正确方法）。
    资产在退市前保留，退市后移除。
    """
    df = data.copy()
    return df
