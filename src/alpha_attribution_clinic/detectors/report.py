"""
Detection report generation.
检测报告生成。
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any
import pandas as pd

from .base import DetectionResult


@dataclass
class DetectionReport:
    """Complete detection report across all checks."""

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    results: dict[str, DetectionResult] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)

    def add_result(self, detector_name: str, result: DetectionResult):
        """Add a detector result to the report."""
        self.results[detector_name] = result
        self._update_summary()

    def _update_summary(self):
        """Update summary statistics."""
        n_detected = sum(1 for r in self.results.values() if r.detected)
        n_total = len(self.results)

        self.summary = {
            "total_checks": n_total,
            "issues_detected": n_detected,
            "issues_clean": n_total - n_detected,
            "detectors_triggered": [
                name for name, r in self.results.items() if r.detected
            ],
        }

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "summary": self.summary,
            "results": {
                name: asdict(result) for name, result in self.results.items()
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_markdown(self) -> str:
        """Convert report to Markdown format."""
        lines = [
            "# Detection Report / 检测报告",
            "",
            f"**Generated**: {self.timestamp}",
            "",
            "## Summary / 摘要",
            "",
            f"- Total checks: {self.summary.get('total_checks', 0)}",
            f"- Issues detected: {self.summary.get('issues_detected', 0)}",
            f"- Clean: {self.summary.get('issues_clean', 0)}",
            "",
        ]

        if self.summary.get("detectors_triggered"):
            lines.append("**Issues found in:** " + ", ".join(self.summary["detectors_triggered"]))
            lines.append("")

        lines.extend(["## Details / 详情", ""])

        for name, result in self.results.items():
            status = "⚠️ DETECTED" if result.detected else "✅ CLEAN"
            lines.extend([
                f"### {name} - {status}",
                "",
                f"**Confidence**: {result.confidence:.1%}",
                "",
                f"**Description**: {result.description}",
                "",
                f"**Recommendation**: {result.recommendation}",
                "",
                "**Evidence**:",
                "```json",
                json.dumps(result.evidence, indent=2, default=str),
                "```",
                "",
            ])

        return "\n".join(lines)


def generate_report(
    data: pd.DataFrame,
    delist_info: pd.DataFrame | None = None,
    signal_cols: dict[str, str] | None = None,
) -> DetectionReport:
    """
    Run all detectors and generate a comprehensive report.

    Parameters
    ----------
    data : pd.DataFrame
        Data to analyze
    delist_info : pd.DataFrame, optional
        Delist information for survivorship detection
    signal_cols : dict, optional
        Mapping of detector name to signal column name

    Returns
    -------
    DetectionReport
        Complete detection report
    """
    from .lookahead_detector import LookaheadDetector
    from .leakage_detector import LeakageDetector
    from .survivorship_detector import SurvivorshipDetector
    from .cost_blind_detector import CostBlindDetector

    if signal_cols is None:
        signal_cols = {
            "lookahead": "signal_lookahead",
            "leakage": "signal_leaked",
        }

    report = DetectionReport()

    lookahead = LookaheadDetector()
    report.add_result(
        "lookahead",
        lookahead.detect(data, signal_col=signal_cols.get("lookahead", "signal_lookahead"))
    )

    leakage = LeakageDetector()
    report.add_result(
        "leakage",
        leakage.detect(data, signal_col=signal_cols.get("leakage", "signal_leaked"))
    )

    survivorship = SurvivorshipDetector()
    report.add_result(
        "survivorship",
        survivorship.detect(data, delist_info=delist_info)
    )

    cost_blind = CostBlindDetector()
    report.add_result(
        "cost_blind",
        cost_blind.detect(data)
    )

    return report
