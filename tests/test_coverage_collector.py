"""Tests for CoverageCollector."""

import tempfile
import json
from pathlib import Path
import pytest

from umpyre.collectors.coverage_collector import CoverageCollector
from umpyre.collectors import registry


def test_coverage_collector_json_report():
    """Should parse coverage.py JSON report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock coverage.json file
        coverage_file = Path(tmpdir) / "coverage.json"
        coverage_data = {
            "totals": {
                "num_statements": 100,
                "covered_lines": 85,
                "num_branches": 20,
                "covered_branches": 16,
            }
        }
        coverage_file.write_text(json.dumps(coverage_data))

        collector = CoverageCollector(
            repo_path=tmpdir, coverage_file=str(coverage_file)
        )
        metrics = collector.collect()

        assert metrics["line_coverage"] == 85.0
        assert metrics["branch_coverage"] == 80.0
        assert metrics["statements_covered"] == 85
        assert metrics["statements_total"] == 100
        assert "error" not in metrics


def test_coverage_collector_xml_report():
    """Should parse Cobertura XML report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock coverage.xml file
        coverage_file = Path(tmpdir) / "coverage.xml"
        xml_content = '''<?xml version="1.0" ?>
<coverage line-rate="0.875" branch-rate="0.80" lines-covered="87" lines-valid="100">
</coverage>
'''
        coverage_file.write_text(xml_content)

        collector = CoverageCollector(
            repo_path=tmpdir, coverage_file=str(coverage_file)
        )
        metrics = collector.collect()

        assert metrics["line_coverage"] == 87.5
        assert metrics["branch_coverage"] == 80.0
        assert metrics["statements_covered"] == 87
        assert metrics["statements_total"] == 100


def test_coverage_collector_no_file():
    """Should handle missing coverage file gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collector = CoverageCollector(repo_path=tmpdir)
        metrics = collector.collect()

        # Should return empty metrics with error
        assert metrics["line_coverage"] == 0.0
        assert "error" in metrics
        assert "No coverage file found" in metrics["error"]


def test_coverage_collector_auto_detect():
    """Should auto-detect coverage file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Place coverage.json in standard location
        coverage_file = Path(tmpdir) / "coverage.json"
        coverage_data = {
            "totals": {
                "num_statements": 50,
                "covered_lines": 40,
                "num_branches": 0,
                "covered_branches": 0,
            }
        }
        coverage_file.write_text(json.dumps(coverage_data))

        collector = CoverageCollector(repo_path=tmpdir)
        metrics = collector.collect()

        assert metrics["line_coverage"] == 80.0
        assert "error" not in metrics


def test_coverage_collector_registered():
    """Should be registered in global registry."""
    from umpyre.collectors import registry as global_registry

    assert "coverage" in global_registry.list_collectors()
    CollectorClass = global_registry.get("coverage")
    assert CollectorClass.__name__ == "CoverageCollector"


def test_coverage_collector_zero_statements():
    """Should handle zero statements gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        coverage_file = Path(tmpdir) / "coverage.json"
        coverage_data = {
            "totals": {
                "num_statements": 0,
                "covered_lines": 0,
                "num_branches": 0,
                "covered_branches": 0,
            }
        }
        coverage_file.write_text(json.dumps(coverage_data))

        collector = CoverageCollector(
            repo_path=tmpdir, coverage_file=str(coverage_file)
        )
        metrics = collector.collect()

        # Should not divide by zero
        assert metrics["line_coverage"] == 0.0
        assert metrics["branch_coverage"] == 0.0
