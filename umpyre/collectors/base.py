"""Base collector class with Mapping interface."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class MetricCollector(Mapping, ABC):
    """
    Abstract base for metric collectors using Mapping interface.

    Collectors implement the Mapping protocol to provide dict-like access
    to collected metrics, enabling flexible composition and iteration.

    Example:
        >>> class SimpleCollector(MetricCollector):
        ...     def collect(self) -> dict:
        ...         return {'lines': 100, 'functions': 10}
        >>> collector = SimpleCollector()
        >>> collector['lines']
        100
        >>> list(collector)
        ['lines', 'functions']
    """

    def __init__(self):
        """Initialize collector."""
        self._cached_metrics = None

    @abstractmethod
    def collect(self) -> dict:
        """
        Collect metrics and return as dictionary.

        Returns:
            Dictionary of metric names to values
        """
        raise NotImplementedError("Subclasses must implement collect()")

    def _ensure_collected(self):
        """Lazily collect metrics on first access."""
        if self._cached_metrics is None:
            self._cached_metrics = self.collect()

    def __getitem__(self, key: str) -> Any:
        """Get specific metric value."""
        self._ensure_collected()
        return self._cached_metrics[key]

    def __iter__(self):
        """Iterate over metric names."""
        self._ensure_collected()
        return iter(self._cached_metrics)

    def __len__(self) -> int:
        """Return number of metrics."""
        self._ensure_collected()
        return len(self._cached_metrics)

    def to_dict(self) -> dict:
        """Export all metrics as dictionary."""
        self._ensure_collected()
        return self._cached_metrics.copy()

    def refresh(self):
        """Force re-collection of metrics."""
        self._cached_metrics = None


class CollectorRegistry:
    """Registry for managing available collectors."""

    def __init__(self):
        """Initialize empty registry."""
        self._collectors = {}

    def register(self, name: str, collector_class: type[MetricCollector]):
        """
        Register a collector class.

        Args:
            name: Collector identifier
            collector_class: MetricCollector subclass
        """
        if not issubclass(collector_class, MetricCollector):
            raise TypeError(f"{collector_class} must be a MetricCollector subclass")
        self._collectors[name] = collector_class

    def get(self, name: str) -> type[MetricCollector]:
        """Get collector class by name."""
        if name not in self._collectors:
            raise KeyError(f"Unknown collector: {name}")
        return self._collectors[name]

    def list_collectors(self) -> list[str]:
        """List all registered collector names."""
        return list(self._collectors.keys())


# Global collector registry
registry = CollectorRegistry()
