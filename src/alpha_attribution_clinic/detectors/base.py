"""
Base class for anti-pattern detectors.
反模式检测器基类。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import pandas as pd


@dataclass
class DetectionResult:
    """Result of running a detector."""
    detected: bool
    confidence: float  # 0.0 to 1.0
    evidence: dict[str, Any]
    description: str
    recommendation: str


class BaseDetector(ABC):
    """
    Base class for all detectors.

    Each detector implements heuristics to identify a specific
    anti-pattern in data or code.
    """

    name: str = "base"
    description: str = "Base detector"

    @abstractmethod
    def detect(self, data: pd.DataFrame, **kwargs) -> DetectionResult:
        """
        Run detection on the provided data.

        Parameters
        ----------
        data : pd.DataFrame
            Data to analyze for anti-patterns

        Returns
        -------
        DetectionResult
            Detection result with confidence and evidence
        """
        pass
