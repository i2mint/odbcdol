"""Versioned schema for metrics storage and migration support."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class MetricSchema:
    """Versioned schema for metrics storage with migration support."""

    version: str = "1.0"

    @classmethod
    def current_version(cls) -> str:
        """Return the current schema version."""
        return "1.0"

    @classmethod
    def migrate(cls, data: dict, from_version: str) -> dict:
        """
        Migrate data from old schema version to current version.

        Args:
            data: Metric data in old format
            from_version: Version of the input data

        Returns:
            Migrated data in current schema format
        """
        if from_version == cls.current_version():
            return data

        # Future: implement migration chains
        # e.g., 1.0 -> 1.1 -> 1.2
        migrations = {
            # "1.0": cls._migrate_1_0_to_1_1,
        }

        if from_version not in migrations:
            raise ValueError(f"No migration path from version {from_version}")

        return migrations[from_version](data)

    @classmethod
    def validate(cls, data: dict) -> bool:
        """
        Validate that data conforms to schema.

        Args:
            data: Metric data to validate

        Returns:
            True if valid, raises ValueError otherwise
        """
        required_fields = {"schema_version", "timestamp", "commit_sha", "metrics"}

        if not all(field in data for field in required_fields):
            missing = required_fields - set(data.keys())
            raise ValueError(f"Missing required fields: {missing}")

        return True

    @classmethod
    def create_metric_data(
        cls,
        commit_sha: str,
        metrics: dict,
        commit_message: Optional[str] = None,
        python_version: Optional[str] = None,
        workflow_status: Optional[dict] = None,
        collection_duration: Optional[float] = None,
    ) -> dict:
        """
        Create a standardized metric data structure.

        Args:
            commit_sha: Git commit SHA
            metrics: Dictionary of collected metrics
            commit_message: Optional commit message
            python_version: Optional Python version string
            workflow_status: Optional workflow status dict
            collection_duration: Optional collection time in seconds

        Returns:
            Standardized metric dictionary
        """
        return {
            "schema_version": cls.current_version(),
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "commit_sha": commit_sha,
            "commit_message": commit_message,
            "python_version": python_version,
            "workflow_status": workflow_status or {},
            "metrics": metrics,
            "collection_duration_seconds": collection_duration,
        }
