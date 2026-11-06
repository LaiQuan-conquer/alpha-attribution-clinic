"""
Base class for anti-pattern injectors.
反模式注入器基类。
"""

from abc import ABC, abstractmethod
from typing import Any
import pandas as pd


class BaseInjector(ABC):
    """
    Base class for all injectors.

    Each injector implements a specific anti-pattern that would make
    backtest results look artificially good.
    """

    name: str = "base"
    description: str = "Base injector"

    @abstractmethod
    def inject(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Apply the anti-pattern to the data.

        Parameters
        ----------
        data : pd.DataFrame
            Clean input data

        Returns
        -------
        pd.DataFrame
            Data with anti-pattern injected
        """
        pass

    @abstractmethod
    def get_injection_metadata(self) -> dict[str, Any]:
        """
        Return metadata about what was injected.

        This is used by detectors to verify they catch the right issues.
        """
        pass
