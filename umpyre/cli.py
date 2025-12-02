"""Command-line interface for umpyre."""

import argparse
import sys
import os
import time
from pathlib import Path
from typing import Optional

from umpyre.config import Config
from umpyre.schema import MetricSchema
from umpyre.collectors import registry
from umpyre.storage import GitBranchStorage


def _collect_metrics(config: Config, repo_path: str) -> dict:
    """Collect metrics from enabled collectors."""
    all_metrics = {}

    for collector_name in registry.list_collectors():
        if not config.is_collector_enabled(collector_name):
            continue

        try:
            collector_config = config.collector_config(collector_name)
            CollectorClass = registry.get(collector_name)

            # Initialize collector with config
            if collector_name == "workflow_status":
                # Requires repo and token
                repo = os.getenv("GITHUB_REPOSITORY") or collector_config.get("repo")
                if not repo:
                    print(f"Skipping {collector_name}: no repository specified")
                    continue
                collector = CollectorClass(
                    repo=repo, lookback_runs=collector_config.get("lookback_runs", 10)
                )
            elif collector_name == "wily":
                collector = CollectorClass(
                    repo_path=repo_path,
                    max_revisions=collector_config.get("max_revisions", 5),
                    operators=collector_config.get(
                        "operators", ["cyclomatic", "maintainability"]
                    ),
                )
            elif collector_name == "coverage":
                collector = CollectorClass(
                    repo_path=repo_path,
                    source=collector_config.get("source", "pytest-cov"),
                )
            elif collector_name == "umpyre_stats":
                collector = CollectorClass(
                    root_path=repo_path,
                    exclude_dirs=collector_config.get(
                        "exclude_dirs", ["tests", "examples"]
                    ),
                )
            else:
                collector = CollectorClass()

            # Collect metrics
            metrics = collector.to_dict()
            all_metrics[collector_name] = metrics

        except Exception as e:
            print(f"Error collecting {collector_name}: {e}")
            all_metrics[collector_name] = {"error": str(e)}

    return all_metrics


def cmd_collect(args):
    """Collect and store metrics."""
    start_time = time.time()

    try:
        # Load config
        config = Config(config_path=args.config if args.config else None)

        # Get repo info
        repo_path = args.repo_path or os.getcwd()
        commit_sha = (
            args.commit or os.getenv("GITHUB_SHA") or _get_current_commit(repo_path)
        )
        commit_message = args.message or _get_commit_message(repo_path, commit_sha)

        print(f"Collecting metrics for {commit_sha[:7]}...")

        # Collect metrics
        metrics = _collect_metrics(config, repo_path)

        # Create standardized metric data
        duration = time.time() - start_time
        metric_data = MetricSchema.create_metric_data(
            commit_sha=commit_sha,
            metrics=metrics,
            commit_message=commit_message,
            python_version=_get_python_version(),
            collection_duration=duration,
        )

        # Store metrics
        if args.no_store:
            print("Metrics collected (not stored):")
            import json

            print(json.dumps(metric_data, indent=2))
        else:
            storage = GitBranchStorage(repo_path)
            storage.store_metrics(
                metric_data,
                commit_sha,
                branch=config.storage_branch,
                formats=config.storage_formats,
            )
            print(f"Metrics stored to branch '{config.storage_branch}'")

        print(f"Collection completed in {duration:.2f}s")
        return 0

    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Error during metrics collection: {e}", file=sys.stderr)
        print(f"Collection failed after {duration:.2f}s", file=sys.stderr)

        # In CI mode, log but don't fail
        if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
            print("⚠️  Running in CI - treating as non-fatal", file=sys.stderr)
            return 0

        return 1


def cmd_validate(args):
    """Validate metrics against thresholds."""
    # Load config
    config = Config(config_path=args.config if args.config else None)

    # Collect metrics
    repo_path = args.repo_path or os.getcwd()
    metrics = _collect_metrics(config, repo_path)

    # TODO: Implement threshold validation
    print("Threshold validation not yet implemented")
    return 0


def _get_current_commit(repo_path: str) -> str:
    """Get current git commit SHA."""
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _get_commit_message(repo_path: str, commit_sha: str) -> str:
    """Get commit message."""
    import subprocess

    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%B", commit_sha],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _get_python_version() -> str:
    """Get Python version string."""
    import sys

    return f"{sys.version_info.major}.{sys.version_info.minor}"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Umpyre - Code metrics collection and tracking"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # collect command
    collect_parser = subparsers.add_parser("collect", help="Collect and store metrics")
    collect_parser.add_argument(
        "--config", help="Path to config file (.github/umpyre-config.yml)"
    )
    collect_parser.add_argument(
        "--repo-path", help="Path to repository (default: current directory)"
    )
    collect_parser.add_argument(
        "--commit", help="Commit SHA (default: current HEAD or GITHUB_SHA)"
    )
    collect_parser.add_argument(
        "--message", help="Commit message (default: auto-detect from git)"
    )
    collect_parser.add_argument(
        "--no-store", action="store_true", help="Collect but don't store (dry-run)"
    )
    collect_parser.set_defaults(func=cmd_collect)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate metrics against thresholds"
    )
    validate_parser.add_argument("--config", help="Path to config file")
    validate_parser.add_argument("--repo-path", help="Path to repository")
    validate_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

        # In CI mode, be more forgiving
        if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
            print("⚠️  Running in CI - treating error as non-fatal", file=sys.stderr)
            return 0

        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
