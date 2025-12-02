"""Tests for schema module."""

import pytest
from datetime import datetime, timezone
from umpyre.schema import MetricSchema


def test_schema_current_version():
    """Schema should have a current version."""
    assert MetricSchema.current_version() == "1.0"


def test_schema_create_metric_data():
    """Should create standardized metric data structure."""
    metrics = {
        "complexity": {"cyclomatic_avg": 3.2},
        "coverage": {"line_coverage": 87.5},
    }

    data = MetricSchema.create_metric_data(
        commit_sha="abc123",
        metrics=metrics,
        commit_message="Test commit",
        python_version="3.10",
    )

    assert data["schema_version"] == "1.0"
    assert data["commit_sha"] == "abc123"
    assert data["commit_message"] == "Test commit"
    assert data["python_version"] == "3.10"
    assert data["metrics"] == metrics
    assert "timestamp" in data
    assert data["timestamp"].endswith("Z")


def test_schema_validate_valid_data():
    """Should validate correct metric data."""
    data = {
        "schema_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "commit_sha": "abc123",
        "metrics": {},
    }

    assert MetricSchema.validate(data) is True


def test_schema_validate_missing_fields():
    """Should raise error for missing required fields."""
    data = {
        "schema_version": "1.0",
        # Missing timestamp, commit_sha, metrics
    }

    with pytest.raises(ValueError, match="Missing required fields"):
        MetricSchema.validate(data)


def test_schema_migrate_same_version():
    """Should return data unchanged for same version."""
    data = {"schema_version": "1.0", "test": "value"}
    result = MetricSchema.migrate(data, "1.0")
    assert result == data


def test_schema_migrate_unknown_version():
    """Should raise error for unknown source version."""
    data = {"schema_version": "0.5"}

    with pytest.raises(ValueError, match="No migration path"):
        MetricSchema.migrate(data, "0.5")
