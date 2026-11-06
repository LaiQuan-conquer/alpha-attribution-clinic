"""
Survivorship bias detector.
幸存者偏差检测器。

Heuristics to detect if analysis excludes delisted assets.
检测分析是否排除了退市资产。
"""

import pandas as pd
import numpy as np
from .base import BaseDetector, DetectionResult


class SurvivorshipDetector(BaseDetector):
    """
    Detect survivorship bias through universe analysis.

    Detection methods:
    1. Check for missing assets in historical periods
    2. Look for suspiciously consistent universe over time
    3. Compare against known delist records
    """

    name = "survivorship"
    description = "Detects if delisted assets have been improperly excluded"

    def detect(
        self,
        data: pd.DataFrame,
        delist_info: pd.DataFrame | None = None,
        **kwargs
    ) -> DetectionResult:
        """
        Detect potential survivorship bias.

        Parameters
        ----------
        data : pd.DataFrame
            Price data to analyze
        delist_info : pd.DataFrame, optional
            DataFrame with known delistings (asset_id, delist_date)
        """
        df = data.copy()
        df = df.reset_index()

        assets_per_date = df.groupby("date")["asset_id"].nunique()
        universe_stability = assets_per_date.std() / (assets_per_date.mean() + 1e-8)

        if delist_info is not None and not delist_info.empty:
            delisted_assets = set(delist_info["asset_id"])
            current_assets = set(df["asset_id"].unique())
            missing_delisted = delisted_assets - current_assets

            if missing_delisted:
                detected = True
                confidence = len(missing_delisted) / len(delisted_assets)
                evidence = {
                    "missing_delisted_assets": list(missing_delisted),
                    "n_missing": len(missing_delisted),
                    "n_total_delisted": len(delisted_assets),
                    "universe_stability": float(universe_stability),
                }
                description = (
                    f"DETECTED: {len(missing_delisted)} delisted assets are missing "
                    f"from the dataset entirely. This indicates survivorship bias."
                )
                recommendation = (
                    "Include delisted assets in historical analysis. "
                    "Use point-in-time universe composition."
                )
            else:
                detected = False
                confidence = 1.0
                evidence = {
                    "delisted_assets_present": True,
                    "universe_stability": float(universe_stability),
                }
                description = "All known delisted assets are present in the data."
                recommendation = "Data appears to handle delistings correctly."
        else:
            too_stable = universe_stability < 0.01 and len(assets_per_date) > 20
            detected = too_stable

            evidence = {
                "universe_stability": float(universe_stability),
                "n_dates": len(assets_per_date),
                "assets_range": (int(assets_per_date.min()), int(assets_per_date.max())),
            }

            if detected:
                confidence = 0.5
                description = (
                    f"WARNING: Universe is suspiciously stable (std/mean = {universe_stability:.4f}). "
                    "Real markets typically have some asset turnover."
                )
                recommendation = (
                    "Verify that delisted assets are included. "
                    "Provide delist_info for more accurate detection."
                )
            else:
                confidence = 0.0
                description = "Universe shows some variation over time."
                recommendation = "Provide delist_info for more thorough analysis."

        return DetectionResult(
            detected=detected,
            confidence=confidence,
            evidence=evidence,
            description=description,
            recommendation=recommendation,
        )
