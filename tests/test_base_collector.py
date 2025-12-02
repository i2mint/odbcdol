"""Tests for base collector."""

import pytest
from umpyre.collectors.base import MetricCollector, CollectorRegistry


class SimpleCollector(MetricCollector):
    """Test collector implementation."""

    def collect(self) -> dict:
        return {
            "lines": 100,
            "functions": 10,
            "classes": 5,
        }


class ErrorCollector(MetricCollector):
    """Collector that raises an error."""

    def collect(self) -> dict:
        raise RuntimeError("Collection failed")


def test_collector_mapping_interface():
    """Should provide Mapping interface."""
    collector = SimpleCollector()

    # __getitem__
    assert collector["lines"] == 100
    assert collector["functions"] == 10

    # __iter__
    keys = list(collector)
    assert "lines" in keys
    assert "functions" in keys

    # __len__
    assert len(collector) == 3

    # dict methods
    assert "lines" in collector
    assert collector.get("lines") == 100
    assert collector.get("missing", "default") == "default"


def test_collector_lazy_collection():
    """Should lazily collect metrics on first access."""
    collector = SimpleCollector()

    # Not collected yet
    assert collector._cached_metrics is None

    # Access triggers collection
    _ = collector["lines"]
    assert collector._cached_metrics is not None

    # Subsequent accesses use cache
    assert collector["functions"] == 10


def test_collector_to_dict():
    """Should export metrics as dictionary."""
    collector = SimpleCollector()
    data = collector.to_dict()

    assert isinstance(data, dict)
    assert data == {"lines": 100, "functions": 10, "classes": 5}


def test_collector_refresh():
    """Should force re-collection of metrics."""
    collector = SimpleCollector()

    # Collect once
    _ = collector["lines"]
    cached = collector._cached_metrics

    # Refresh
    collector.refresh()
    assert collector._cached_metrics is None

    # Access again - should re-collect
    _ = collector["lines"]
    assert collector._cached_metrics is not None
    assert collector._cached_metrics is not cached  # New object


def test_collector_error_handling():
    """Should propagate collection errors."""
    collector = ErrorCollector()

    with pytest.raises(RuntimeError, match="Collection failed"):
        _ = collector["any_key"]


def test_collector_registry():
    """Should register and retrieve collectors."""
    registry = CollectorRegistry()

    # Register
    registry.register("simple", SimpleCollector)

    # Retrieve
    CollectorClass = registry.get("simple")
    assert CollectorClass is SimpleCollector

    # List
    assert "simple" in registry.list_collectors()


def test_registry_unknown_collector():
    """Should raise error for unknown collector."""
    registry = CollectorRegistry()

    with pytest.raises(KeyError, match="Unknown collector"):
        registry.get("nonexistent")


def test_registry_invalid_type():
    """Should reject non-collector classes."""
    registry = CollectorRegistry()

    class NotACollector:
        pass

    with pytest.raises(TypeError, match="must be a MetricCollector subclass"):
        registry.register("invalid", NotACollector)
