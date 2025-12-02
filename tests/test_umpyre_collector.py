"""Tests for UmpyreCollector."""

import tempfile
from pathlib import Path
import pytest

from umpyre.collectors.umpyre_collector import UmpyreCollector


def test_umpyre_collector_basic():
    """Should collect basic code statistics using AST parsing."""
    # Test with real umpyre package itself
    import umpyre
    import os

    umpyre_path = os.path.dirname(umpyre.__file__)
    collector = UmpyreCollector(root_path=umpyre_path)
    metrics = collector.collect()

    # Should have collected metrics from umpyre package itself
    assert metrics["num_functions"] > 0
    assert metrics["total_lines"] > 0
    assert metrics["files_analyzed"] > 0
    # Should not have errors (AST parsing is safe)
    assert "error" not in metrics


def test_umpyre_collector_exclude_dirs():
    """Should exclude specified directories using AST parsing."""
    import umpyre
    import os

    # Test with real umpyre package, excluding tests directory
    umpyre_root = os.path.dirname(os.path.dirname(umpyre.__file__))

    # Collect without exclusions
    collector1 = UmpyreCollector(root_path=umpyre_root, exclude_dirs=[])
    metrics1 = collector1.collect()

    # Collect with tests excluded
    collector2 = UmpyreCollector(root_path=umpyre_root, exclude_dirs=["tests"])
    metrics2 = collector2.collect()

    # With tests excluded, should have fewer or equal functions and files
    assert metrics2["num_functions"] <= metrics1["num_functions"]
    assert metrics2["files_analyzed"] < metrics1["files_analyzed"]


def test_umpyre_collector_empty_directory():
    """Should handle empty directory gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collector = UmpyreCollector(root_path=tmpdir)
        metrics = collector.collect()

        # Should return zeros
        assert metrics["num_functions"] == 0
        assert metrics["total_lines"] == 0


def test_umpyre_collector_mapping_interface():
    """Should work as Mapping."""
    import umpyre
    import os

    umpyre_path = os.path.dirname(umpyre.__file__)
    collector = UmpyreCollector(root_path=umpyre_path)

    # Access via mapping
    assert collector["num_functions"] >= 0
    assert "total_lines" in collector
    assert len(collector) > 0


def test_umpyre_collector_registered():
    """Should be registered in global registry."""
    from umpyre.collectors import registry as global_registry

    assert "umpyre_stats" in global_registry.list_collectors()
    CollectorClass = global_registry.get("umpyre_stats")
    assert CollectorClass.__name__ == "UmpyreCollector"
