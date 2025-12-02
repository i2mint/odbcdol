"""Git branch-based storage operations."""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from umpyre.storage.formats import serialize_metrics


class GitBranchStorage:
    """
    Store metrics in a separate git branch.

    This provides versioned, branch-based storage without polluting
    the main branch or requiring external artifacts.

    Example:
        >>> storage = GitBranchStorage(repo_path="/path/to/repo")  # doctest: +SKIP
        >>> metrics = {"lines": 100, "functions": 10}  # doctest: +SKIP
        >>> storage.store_metrics(metrics, "abc123", branch="code-metrics")  # doctest: +SKIP
    """

    def __init__(self, repo_path: str, remote: str = "origin"):
        """
        Initialize storage.

        Args:
            repo_path: Path to git repository
            remote: Git remote name
        """
        self.repo_path = Path(repo_path)
        self.remote = remote

        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

    def store_metrics(
        self,
        metrics: dict,
        commit_sha: str,
        branch: str = "code-metrics",
        formats: Optional[list[str]] = None,
    ):
        """
        Store metrics to git branch.

        Args:
            metrics: Metric dictionary to store
            commit_sha: Git commit SHA
            branch: Target branch name
            formats: List of formats ('json', 'csv')
        """
        formats = formats or ["json", "csv"]

        # Create temporary directory for branch checkout
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Fetch and checkout metrics branch
            self._fetch_branch(branch)
            self._checkout_branch(branch, tmpdir)

            # Create history directory (flat structure)
            history_dir = tmpdir / "history"
            history_dir.mkdir(exist_ok=True)

            # Build filename: YYYY_MM_DD_HH_MM_SS__shahash__version.json
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            commit_short = commit_sha[:7]

            # Extract pypi_version if available (use 'none' if not found)
            pypi_version = (
                metrics.get('metrics', {}).get('umpyre_stats', {}).get('pypi_version')
                or 'none'
            )

            # Filename format: timestamp__sha__version (parseable, chronological)
            filename_base = f"{timestamp}__{commit_short}__{pypi_version}"

            for fmt in formats:
                if fmt == "json":
                    # Latest snapshot
                    serialize_metrics(metrics, tmpdir / "metrics.json", format="json")

                    # Historical record (flat structure, parseable filename)
                    history_file = history_dir / f"{filename_base}.json"
                    serialize_metrics(metrics, history_file, format="json")

                elif fmt == "csv":
                    serialize_metrics(metrics, tmpdir / "metrics.csv", format="csv")

            # Commit and push
            self._commit_and_push(tmpdir, branch, commit_sha)

    def _fetch_branch(self, branch: str):
        """Fetch metrics branch from remote."""
        try:
            subprocess.run(
                ["git", "fetch", self.remote, f"{branch}:{branch}"],
                cwd=self.repo_path,
                capture_output=True,
                check=False,  # May not exist yet
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            pass

    def _checkout_branch(self, branch: str, target_dir: Path):
        """Checkout metrics branch to temporary directory."""
        # Check if branch exists locally
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            cwd=self.repo_path,
            capture_output=True,
            check=False,
        )

        if result.returncode == 0:
            # Branch exists - clone it
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--branch",
                    branch,
                    "--depth",
                    "1",
                    str(self.repo_path),
                    str(target_dir),
                ],
                capture_output=True,
                check=True,
                timeout=60,
            )
        else:
            # Branch doesn't exist - create new
            subprocess.run(
                ["git", "clone", "--depth", "1", str(self.repo_path), str(target_dir)],
                capture_output=True,
                check=True,
                timeout=60,
            )
            subprocess.run(
                ["git", "checkout", "--orphan", branch],
                cwd=target_dir,
                capture_output=True,
                check=True,
            )
            # Remove all files from new orphan branch
            subprocess.run(
                ["git", "rm", "-rf", "."],
                cwd=target_dir,
                capture_output=True,
                check=False,
            )

    def _commit_and_push(self, work_dir: Path, branch: str, commit_sha: str):
        """Commit changes and push to remote."""
        # Configure git
        subprocess.run(
            ["git", "config", "user.name", "umpyre-bot"],
            cwd=work_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "umpyre@automated"],
            cwd=work_dir,
            capture_output=True,
            check=True,
        )

        # Add all files
        subprocess.run(
            ["git", "add", "."],
            cwd=work_dir,
            capture_output=True,
            check=True,
        )

        # Check if there are changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=work_dir,
            capture_output=True,
            check=False,
        )

        if result.returncode != 0:
            # There are changes - commit them
            commit_message = f"Update metrics for {commit_sha[:7]}"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=work_dir,
                capture_output=True,
                check=True,
            )

            # Push with retries
            for attempt in range(3):
                try:
                    subprocess.run(
                        ["git", "push", self.remote, branch],
                        cwd=work_dir,
                        capture_output=True,
                        check=True,
                        timeout=60,
                    )
                    break
                except subprocess.CalledProcessError:
                    if attempt < 2:
                        # Pull and try again
                        subprocess.run(
                            ["git", "pull", "--rebase", self.remote, branch],
                            cwd=work_dir,
                            capture_output=True,
                            check=False,
                        )
                    else:
                        raise


class GitBranchStorageError(Exception):
    """Raised when git branch storage operations fail."""
