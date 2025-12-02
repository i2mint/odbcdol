"""Helper utilities for working with umpyre metrics storage."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional


def parse_metric_filename(filename: str) -> dict:
    """
    Parse metric filename into components.

    Args:
        filename: Filename like "2025_11_14_22_45_00__700e012__0.1.0.json"

    Returns:
        Dictionary with parsed components:
        {
            "timestamp": datetime object,
            "timestamp_str": "2025-11-14T22:45:00",
            "commit_sha": "700e012",
            "pypi_version": "0.1.0" or None,
            "has_version": bool,
        }

    Example:
        >>> info = parse_metric_filename("2025_11_14_22_45_00__700e012__0.1.0.json")
        >>> info['commit_sha']
        '700e012'
        >>> info['pypi_version']
        '0.1.0'
    """
    pattern = r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})__(\w{7})__(.+)\.json'
    match = re.match(pattern, filename)

    if not match:
        raise ValueError(f"Invalid filename format: {filename}")

    timestamp_str, sha, version = match.groups()

    # Parse timestamp
    dt = datetime.strptime(timestamp_str, "%Y_%m_%d_%H_%M_%S")
    timestamp_iso = dt.isoformat()

    # Parse version (None if 'none')
    pypi_version = None if version == "none" else version

    return {
        "timestamp": dt,
        "timestamp_str": timestamp_iso,
        "commit_sha": sha,
        "pypi_version": pypi_version,
        "has_version": pypi_version is not None,
    }


def find_metrics_by_commit(history_dir: Path, commit_sha: str) -> Optional[Path]:
    """
    Find metrics file for a specific commit.

    Args:
        history_dir: Path to history directory
        commit_sha: Commit SHA (7 chars or full)

    Returns:
        Path to metrics file or None

    Example:
        >>> metrics = find_metrics_by_commit(Path("history"), "700e012")  # doctest: +SKIP
        >>> print(metrics.name)  # doctest: +SKIP
        2025_11_14_22_45_00__700e012__0.1.0.json
    """
    short_sha = commit_sha[:7]
    matches = list(history_dir.glob(f"*__{short_sha}__*.json"))
    return matches[0] if matches else None


def find_metrics_by_version(history_dir: Path, version: str) -> list[Path]:
    """
    Find all metrics files for a specific PyPI version.

    Args:
        history_dir: Path to history directory
        version: PyPI version string (e.g., "0.1.0")

    Returns:
        List of paths (sorted by timestamp, latest first)

    Example:
        >>> metrics = find_metrics_by_version(Path("history"), "0.1.0")  # doctest: +SKIP
        >>> for m in metrics:  # doctest: +SKIP
        ...     print(m.name)
        2025_11_14_22_50_00__abc1234__0.1.0.json
        2025_11_14_22_45_00__700e012__0.1.0.json
    """
    matches = list(history_dir.glob(f"*__{version}.json"))
    # Sort by filename (chronological order), reverse for latest first
    return sorted(matches, reverse=True)


def get_latest_metric_for_version(history_dir: Path, version: str) -> Optional[Path]:
    """
    Get the most recent metrics file for a version.

    Args:
        history_dir: Path to history directory
        version: PyPI version string

    Returns:
        Path to latest metrics file or None

    Example:
        >>> latest = get_latest_metric_for_version(Path("history"), "0.1.0")  # doctest: +SKIP
        >>> info = parse_metric_filename(latest.name)  # doctest: +SKIP
        >>> print(f"Latest 0.1.0 metrics from {info['timestamp_str']}")  # doctest: +SKIP
    """
    matches = find_metrics_by_version(history_dir, version)
    return matches[0] if matches else None


def get_all_versions(history_dir: Path) -> list[str]:
    """
    Get all unique PyPI versions found in metrics.

    Args:
        history_dir: Path to history directory

    Returns:
        Sorted list of versions (excluding 'none')

    Example:
        >>> versions = get_all_versions(Path("history"))  # doctest: +SKIP
        >>> print(versions)  # doctest: +SKIP
        ['0.1.0', '0.1.1', '0.2.0']
    """
    versions = set()

    for filepath in history_dir.glob("*.json"):
        try:
            info = parse_metric_filename(filepath.name)
            if info['has_version']:
                versions.add(info['pypi_version'])
        except ValueError:
            continue

    # Sort semantically (simple lexicographic works for most cases)
    return sorted(versions)


def filter_by_date_range(
    history_dir: Path,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[Path]:
    """
    Get metrics files within a date range.

    Args:
        history_dir: Path to history directory
        start_date: Start datetime (inclusive)
        end_date: End datetime (inclusive)

    Returns:
        List of paths within date range (sorted chronologically)

    Example:
        >>> from datetime import datetime, timedelta  # doctest: +SKIP
        >>> end = datetime.now()  # doctest: +SKIP
        >>> start = end - timedelta(days=7)  # doctest: +SKIP
        >>> recent = filter_by_date_range(Path("history"), start, end)  # doctest: +SKIP
        >>> print(f"Found {len(recent)} metrics from last 7 days")  # doctest: +SKIP
    """
    matches = []

    for filepath in history_dir.glob("*.json"):
        try:
            info = parse_metric_filename(filepath.name)
            timestamp = info['timestamp']

            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue

            matches.append(filepath)
        except ValueError:
            continue

    return sorted(matches)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
