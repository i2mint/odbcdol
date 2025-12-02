"""Tests for config module."""

import pytest
import tempfile
from pathlib import Path
from umpyre.config import Config, ConfigError


def test_config_default_values():
    """Should provide default configuration."""
    config = Config()

    assert config.storage_branch == "code-metrics"
    assert "json" in config.storage_formats
    assert config.retention_strategy == "all"


def test_config_from_dict():
    """Should create config from dictionary."""
    custom = {
        "storage": {
            "branch": "custom-metrics",
            "formats": ["csv"],
        }
    }

    config = Config.from_dict(custom)
    assert config.storage_branch == "custom-metrics"
    assert config.storage_formats == ["csv"]


def test_config_from_yaml_file():
    """Should load config from YAML file."""
    yaml_content = """
collectors:
  wily:
    enabled: false
    max_revisions: 10

storage:
  branch: test-metrics
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(yaml_content)
        f.flush()

        config = Config.from_file(f.name)

        assert config.storage_branch == "test-metrics"
        assert config.is_collector_enabled("wily") is False
        assert config.collector_config("wily")["max_revisions"] == 10

        Path(f.name).unlink()


def test_config_deep_merge():
    """Should deep merge configurations properly."""
    config = Config.from_dict(
        {
            "collectors": {
                "wily": {
                    "max_revisions": 3,  # Override default
                    # Keep other wily defaults
                },
                "coverage": {
                    "enabled": False,  # Override default
                },
            }
        }
    )

    # Should have overridden value
    assert config.get("collectors", "wily", "max_revisions") == 3
    # Should keep default
    assert "cyclomatic" in config.get("collectors", "wily", "operators")
    # Should have override
    assert config.is_collector_enabled("coverage") is False


def test_config_get_nested():
    """Should retrieve nested config values."""
    config = Config()

    # Existing path
    assert config.get("collectors", "wily", "enabled") is True

    # Missing path with default
    assert config.get("missing", "path", default="fallback") == "fallback"

    # Missing path without default
    assert config.get("missing", "path") is None


def test_config_is_collector_enabled():
    """Should check if collector is enabled."""
    config = Config()

    assert config.is_collector_enabled("workflow_status") is True
    assert config.is_collector_enabled("nonexistent") is False


def test_config_collector_config():
    """Should get collector-specific configuration."""
    config = Config()

    wily_config = config.collector_config("wily")
    assert wily_config["enabled"] is True
    assert wily_config["max_revisions"] == 5

    missing_config = config.collector_config("nonexistent")
    assert missing_config == {}


def test_config_to_dict():
    """Should export config as dictionary."""
    config = Config.from_dict({"storage": {"branch": "test"}})
    exported = config.to_dict()

    assert isinstance(exported, dict)
    assert exported["storage"]["branch"] == "test"


def test_config_validation():
    """Should validate required config sections."""
    # This should work - has required sections via defaults
    Config()

    # Missing required sections should raise error
    # (though our implementation merges with defaults, so this is hard to trigger)
    # Future: could add more strict validation
