"""Collector for test coverage metrics."""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from umpyre.collectors.base import MetricCollector, registry


class CoverageCollector(MetricCollector):
    """
    Collect test coverage metrics from coverage reports.

    Supports:
    - coverage.py JSON reports
    - coverage.py XML reports (Cobertura format)

    Tracks:
    - Line coverage percentage
    - Branch coverage percentage (if available)
    - Statements covered/total

    Example:
        >>> # This requires coverage report files
        >>> # Skip in doctest as it requires actual test runs
        >>> True  # doctest: +SKIP
    """

    def __init__(
        self,
        repo_path: Optional[str] = None,
        source: str = "pytest-cov",
        coverage_file: Optional[str] = None,
    ):
        """
        Initialize collector.

        Args:
            repo_path: Path to repository (defaults to current directory)
            source: Coverage source ('pytest-cov' or 'coverage')
            coverage_file: Explicit path to coverage report (auto-detect if None)
        """
        super().__init__()
        self.repo_path = repo_path or os.getcwd()
        self.source = source
        self.coverage_file = coverage_file

    def collect(self) -> dict:
        """
        Collect coverage metrics from report files.

        Returns:
            Dictionary with:
            - line_coverage: Line coverage percentage
            - branch_coverage: Branch coverage percentage (may be 0 if not tracked)
            - statements_covered: Number of statements covered
            - statements_total: Total number of statements
        """
        try:
            # Try to find coverage file
            coverage_file = self._find_coverage_file()

            if not coverage_file:
                return self._empty_metrics(error="No coverage file found")

            # Parse based on file type
            if coverage_file.suffix == ".json":
                return self._parse_json_report(coverage_file)
            elif coverage_file.suffix == ".xml":
                return self._parse_xml_report(coverage_file)
            else:
                return self._empty_metrics(
                    error=f"Unsupported coverage file format: {coverage_file.suffix}"
                )

        except Exception as e:
            return self._empty_metrics(error=str(e))

    def _find_coverage_file(self) -> Optional[Path]:
        """Auto-detect coverage report file."""
        if self.coverage_file:
            path = Path(self.coverage_file)
            return path if path.exists() else None

        # Common coverage file locations
        repo = Path(self.repo_path)
        candidates = [
            repo / "coverage.json",
            repo / ".coverage.json",
            repo / "coverage.xml",
            repo / "htmlcov" / "coverage.json",
            repo / ".pytest_cache" / "coverage.json",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None

    def _parse_json_report(self, file_path: Path) -> dict:
        """Parse coverage.py JSON report."""
        with open(file_path) as f:
            data = json.load(f)

        # Extract totals
        totals = data.get("totals", {})

        # Calculate coverage percentages
        num_statements = totals.get("num_statements", 0)
        covered_lines = totals.get("covered_lines", 0)
        num_branches = totals.get("num_branches", 0)
        covered_branches = totals.get("covered_branches", 0)

        line_coverage = (
            (covered_lines / num_statements * 100) if num_statements > 0 else 0
        )
        branch_coverage = (
            (covered_branches / num_branches * 100) if num_branches > 0 else 0
        )

        return {
            "line_coverage": round(line_coverage, 2),
            "branch_coverage": round(branch_coverage, 2),
            "statements_covered": covered_lines,
            "statements_total": num_statements,
        }

    def _parse_xml_report(self, file_path: Path) -> dict:
        """Parse Cobertura XML report."""
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Cobertura format has coverage attributes at root level
        line_rate = float(root.get("line-rate", 0))
        branch_rate = float(root.get("branch-rate", 0))

        # Convert rates (0-1) to percentages
        line_coverage = line_rate * 100
        branch_coverage = branch_rate * 100

        # Try to get statement counts
        lines_covered = int(root.get("lines-covered", 0))
        lines_valid = int(root.get("lines-valid", 0))

        return {
            "line_coverage": round(line_coverage, 2),
            "branch_coverage": round(branch_coverage, 2),
            "statements_covered": lines_covered,
            "statements_total": lines_valid,
        }

    @staticmethod
    def _empty_metrics(error: Optional[str] = None) -> dict:
        """Return empty metrics."""
        metrics = {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "statements_covered": 0,
            "statements_total": 0,
        }
        if error:
            metrics["error"] = error
        return metrics


# Register collector
registry.register("coverage", CoverageCollector)
