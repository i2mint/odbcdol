"""Collector for complexity metrics using wily."""

import os
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Optional

from umpyre.collectors.base import MetricCollector, registry


class WilyCollector(MetricCollector):
    """
    Collect complexity metrics using wily.

    Tracks:
    - Cyclomatic complexity (average)
    - Maintainability index
    - Total lines of code
    - Files analyzed

    Note: Limited to recent commits (max_revisions) for performance.

    Example:
        >>> # This requires wily to be installed and a git repo
        >>> # Skip in doctest as it requires git setup
        >>> True  # doctest: +SKIP
    """

    def __init__(
        self,
        repo_path: Optional[str] = None,
        max_revisions: int = 5,
        operators: Optional[list[str]] = None,
    ):
        """
        Initialize collector.

        Args:
            repo_path: Path to git repository (defaults to current directory)
            max_revisions: Number of recent commits to analyze (for speed)
            operators: Wily operators to use (defaults to ['cyclomatic', 'maintainability'])
        """
        super().__init__()
        self.repo_path = repo_path or os.getcwd()
        self.max_revisions = max_revisions
        self.operators = operators or ["cyclomatic", "maintainability"]

    def collect(self) -> dict:
        """
        Collect complexity metrics using wily.

        Returns:
            Dictionary with:
            - cyclomatic_avg: Average cyclomatic complexity
            - maintainability_index: Maintainability index score
            - total_loc: Total lines of code
            - files_analyzed: Number of files analyzed
        """
        try:
            # Check if wily is available
            if not self._is_wily_available():
                return self._empty_metrics(error="wily not installed")

            # Check if repo is initialized
            wily_cache = Path(self.repo_path) / ".wily"
            if not wily_cache.exists():
                # Build wily cache (limited revisions for speed)
                self._build_wily_cache()

            # Get latest metrics
            metrics = self._get_latest_metrics()

            return metrics

        except Exception as e:
            return self._empty_metrics(error=str(e))

    def _is_wily_available(self) -> bool:
        """Check if wily is installed."""
        try:
            subprocess.run(
                ["wily", "--version"], capture_output=True, check=True, timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _build_wily_cache(self):
        """Build wily cache with limited revisions."""
        cmd = [
            "wily",
            "build",
            self.repo_path,
            "--max-revisions",
            str(self.max_revisions),
        ]

        # Add operators
        for operator in self.operators:
            cmd.extend(["--operators", operator])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.repo_path,
            timeout=60,
        )

        if result.returncode != 0:
            raise RuntimeError(f"wily build failed: {result.stderr}")

    def _get_latest_metrics(self) -> dict:
        """Extract metrics from wily report."""
        # Get report in JSON format
        result = subprocess.run(
            ["wily", "report", self.repo_path, "--format", "json"],
            capture_output=True,
            text=True,
            cwd=self.repo_path,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(f"wily report failed: {result.stderr}")

        # Parse JSON output
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Fallback: parse text output
            return self._parse_text_report()

        # Extract metrics from JSON
        return self._extract_metrics_from_json(report)

    def _parse_text_report(self) -> dict:
        """Parse text output as fallback (wily doesn't always output valid JSON)."""
        result = subprocess.run(
            ["wily", "report", self.repo_path],
            capture_output=True,
            text=True,
            cwd=self.repo_path,
            timeout=30,
        )

        # Simple parsing of key metrics from text
        output = result.stdout

        # This is a simplified parser - actual implementation would be more robust
        metrics = {
            "cyclomatic_avg": 0.0,
            "maintainability_index": 0.0,
            "total_loc": 0,
            "files_analyzed": 0,
        }

        # Count files
        metrics["files_analyzed"] = output.count(".py")

        return metrics

    def _extract_metrics_from_json(self, report: dict) -> dict:
        """Extract metrics from JSON report."""
        # Wily JSON structure varies, this is a best-effort extraction
        metrics = {
            "cyclomatic_avg": 0.0,
            "maintainability_index": 0.0,
            "total_loc": 0,
            "files_analyzed": 0,
        }

        # Navigate report structure (this varies by wily version)
        if isinstance(report, dict):
            metrics["files_analyzed"] = len(report)

            # Calculate averages
            cyclomatic_values = []
            maintainability_values = []
            loc_values = []

            for file_data in report.values():
                if isinstance(file_data, dict):
                    if "cyclomatic" in file_data:
                        cyclomatic_values.append(file_data["cyclomatic"])
                    if "maintainability" in file_data:
                        maintainability_values.append(file_data["maintainability"])
                    if "loc" in file_data:
                        loc_values.append(file_data["loc"])

            if cyclomatic_values:
                metrics["cyclomatic_avg"] = sum(cyclomatic_values) / len(
                    cyclomatic_values
                )
            if maintainability_values:
                metrics["maintainability_index"] = sum(maintainability_values) / len(
                    maintainability_values
                )
            if loc_values:
                metrics["total_loc"] = sum(loc_values)

        return metrics

    @staticmethod
    def _empty_metrics(error: Optional[str] = None) -> dict:
        """Return empty metrics."""
        metrics = {
            "cyclomatic_avg": 0.0,
            "maintainability_index": 0.0,
            "total_loc": 0,
            "files_analyzed": 0,
        }
        if error:
            metrics["error"] = error
        return metrics


# Register collector
registry.register("wily", WilyCollector)
