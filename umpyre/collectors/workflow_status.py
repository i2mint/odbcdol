"""Collector for GitHub workflow status using GitHub API."""

import os
from datetime import datetime, timezone
from typing import Optional

import requests

from umpyre.collectors.base import MetricCollector, registry


class WorkflowStatusCollector(MetricCollector):
    """
    Collect GitHub workflow status using GitHub API.

    Tracks:
    - Last workflow run status (success/failure)
    - Last successful run timestamp
    - Recent failure count
    - Workflow run URL

    Example:
        >>> # Mock test (requires actual GitHub API)
        >>> import os
        >>> if os.getenv('GITHUB_TOKEN'):  # doctest: +SKIP
        ...     collector = WorkflowStatusCollector(
        ...         repo="thorwhalen/astate",
        ...         token=os.getenv('GITHUB_TOKEN')
        ...     )
        ...     metrics = collector.collect()
        ...     'last_run_status' in metrics
        ... else:
        ...     True  # Skip if no token
        True
    """

    def __init__(
        self,
        repo: str,
        token: Optional[str] = None,
        lookback_runs: int = 10,
        workflow_name: Optional[str] = None,
    ):
        """
        Initialize collector.

        Args:
            repo: Repository in format "owner/repo"
            token: GitHub token (defaults to GITHUB_TOKEN env var)
            lookback_runs: Number of recent runs to analyze
            workflow_name: Specific workflow name to track (None = all workflows)
        """
        super().__init__()
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.lookback_runs = lookback_runs
        self.workflow_name = workflow_name

        if not self.token:
            raise ValueError("GitHub token required (set GITHUB_TOKEN env var)")

    def collect(self) -> dict:
        """
        Collect workflow status from GitHub API.

        Returns:
            Dictionary with:
            - last_run_status: 'success', 'failure', or 'other'
            - last_success_timestamp: ISO timestamp or None
            - recent_failure_count: Number of failures in lookback window
            - run_url: URL of last run
            - total_runs_analyzed: Number of runs examined
        """
        try:
            runs = self._fetch_workflow_runs()

            if not runs:
                return self._empty_metrics()

            # Analyze runs
            last_run = runs[0]
            last_run_status = self._map_conclusion(last_run.get("conclusion"))

            # Find last successful run
            last_success = None
            for run in runs:
                if run.get("conclusion") == "success":
                    last_success = run.get("updated_at")
                    break

            # Count recent failures
            failure_count = sum(
                1
                for run in runs
                if run.get("conclusion") in ["failure", "cancelled", "timed_out"]
            )

            return {
                "last_run_status": last_run_status,
                "last_success_timestamp": last_success,
                "recent_failure_count": failure_count,
                "run_url": last_run.get("html_url"),
                "total_runs_analyzed": len(runs),
            }

        except Exception as e:
            return {
                "last_run_status": "error",
                "last_success_timestamp": None,
                "recent_failure_count": 0,
                "run_url": None,
                "total_runs_analyzed": 0,
                "error": str(e),
            }

    def _fetch_workflow_runs(self) -> list[dict]:
        """Fetch recent workflow runs from GitHub API."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Fetch workflow runs
        url = f"https://api.github.com/repos/{self.repo}/actions/runs"
        params = {
            "per_page": self.lookback_runs,
            "status": "completed",  # Only completed runs
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        runs = data.get("workflow_runs", [])

        # Filter by workflow name if specified
        if self.workflow_name:
            runs = [run for run in runs if run.get("name") == self.workflow_name]

        return runs[: self.lookback_runs]

    @staticmethod
    def _map_conclusion(conclusion: Optional[str]) -> str:
        """Map GitHub conclusion to simplified status."""
        if conclusion == "success":
            return "success"
        elif conclusion in ["failure", "cancelled", "timed_out"]:
            return "failure"
        else:
            return "other"

    @staticmethod
    def _empty_metrics() -> dict:
        """Return empty metrics when no data available."""
        return {
            "last_run_status": "unknown",
            "last_success_timestamp": None,
            "recent_failure_count": 0,
            "run_url": None,
            "total_runs_analyzed": 0,
        }


# Register collector
registry.register("workflow_status", WorkflowStatusCollector)
