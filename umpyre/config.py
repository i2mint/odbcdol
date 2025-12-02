"""Configuration loading and validation for umpyre."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid."""


class Config:
    """Configuration manager for umpyre metrics collection."""

    DEFAULT_CONFIG = {
        "schema_version": "1.0",
        "collectors": {
            "workflow_status": {
                "enabled": True,
                "lookback_runs": 10,
            },
            "wily": {
                "enabled": True,
                "max_revisions": 5,
                "operators": ["cyclomatic", "maintainability"],
            },
            "coverage": {
                "enabled": True,
                "source": "pytest-cov",
            },
            "umpyre_stats": {
                "enabled": True,
                "exclude_dirs": ["tests", "examples", "scrap"],
            },
        },
        "storage": {
            "branch": "code-metrics",
            "formats": ["json", "csv"],
            "retention": {
                "strategy": "all",  # or: last_n_days, last_n_commits
            },
        },
        "visualization": {
            "generate_plots": True,
            "generate_readme": True,
            "plot_metrics": ["maintainability", "coverage", "loc"],
        },
        "thresholds": {
            "enabled": False,
        },
        "aggregation": {
            "enabled": False,
        },
    }

    def __init__(
        self, config_path: Optional[str] = None, config_dict: Optional[dict] = None
    ):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML config file
            config_dict: Config as dictionary (overrides file)
        """
        self._config = self._load_config(config_path, config_dict)
        self._validate()

    def _load_config(
        self, config_path: Optional[str], config_dict: Optional[dict]
    ) -> dict:
        """Load configuration from file or dict, merging with defaults."""
        config = self.DEFAULT_CONFIG.copy()

        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                file_config = yaml.safe_load(f) or {}
            config = self._deep_merge(config, file_config)

        if config_dict:
            config = self._deep_merge(config, config_dict)

        return config

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _validate(self):
        """Validate configuration structure."""
        required_sections = ["collectors", "storage"]
        for section in required_sections:
            if section not in self._config:
                raise ConfigError(f"Missing required config section: {section}")

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get nested config value.

        Args:
            *keys: Nested keys (e.g., 'collectors', 'wily', 'enabled')
            default: Default value if key not found

        Returns:
            Config value or default

        >>> config = Config(config_dict={'collectors': {'wily': {'enabled': True}}})
        >>> config.get('collectors', 'wily', 'enabled')
        True
        >>> config.get('collectors', 'missing', default='default_value')
        'default_value'
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def is_collector_enabled(self, collector_name: str) -> bool:
        """Check if a collector is enabled."""
        return self.get("collectors", collector_name, "enabled", default=False)

    def collector_config(self, collector_name: str) -> dict:
        """Get configuration for a specific collector."""
        return self.get("collectors", collector_name, default={})

    @property
    def storage_branch(self) -> str:
        """Get the storage branch name."""
        return self.get("storage", "branch", default="code-metrics")

    @property
    def storage_formats(self) -> list[str]:
        """Get enabled storage formats."""
        return self.get("storage", "formats", default=["json"])

    @property
    def retention_strategy(self) -> str:
        """Get data retention strategy."""
        return self.get("storage", "retention", "strategy", default="all")

    def to_dict(self) -> dict:
        """Export config as dictionary."""
        return self._config.copy()

    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load config from YAML file."""
        return cls(config_path=path)

    @classmethod
    def from_dict(cls, config: dict) -> "Config":
        """Create config from dictionary."""
        return cls(config_dict=config)
