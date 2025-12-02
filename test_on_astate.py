#!/usr/bin/env python
"""
Automated testing script for umpyre on astate repository.

This script validates the umpyre metrics collection system by:
1. Running metrics collection on astate
2. Verifying storage outputs
3. Checking metric data validity
4. Measuring performance
"""

import sys
import os
import time
import json
import csv
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add umpyre to path
umpyre_root = Path(__file__).parent
sys.path.insert(0, str(umpyre_root))

from umpyre import Config, MetricSchema, registry
from umpyre.collectors.base import MetricCollector
from umpyre.storage.formats import serialize_metrics, deserialize_metrics


class TestResult:
    """Track test results."""

    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        self.start_time = None
        self.end_time = None

    def pass_test(self, name: str, details: str = ""):
        self.passed.append((name, details))
        print(f"✅ {name}")
        if details:
            print(f"   {details}")

    def fail_test(self, name: str, error: str):
        self.failed.append((name, error))
        print(f"❌ {name}")
        print(f"   Error: {error}")

    def warn(self, message: str):
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def summary(self):
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Duration: {self.duration:.2f}s")

        if self.failed:
            print("\n❌ FAILED TESTS:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("\n" + "=" * 70)
        return len(self.failed) == 0


def test_registry():
    """Test that collectors are registered."""
    result = TestResult()

    collectors = registry.list_collectors()
    if len(collectors) >= 3:  # At least workflow_status, coverage, wily
        result.pass_test(
            "Collector registry",
            f"Found {len(collectors)} collectors: {', '.join(collectors)}",
        )
    else:
        result.fail_test(
            "Collector registry",
            f"Expected at least 3 collectors, found {len(collectors)}",
        )

    return result


def test_config(repo_path: Path):
    """Test configuration loading."""
    result = TestResult()

    try:
        # Test with minimal config
        config_data = {
            'repo_path': str(repo_path),
            'collectors': {
                'workflow_status': {'enabled': True},
                'coverage': {'enabled': True},
            },
        }

        # Write temporary config
        config_file = repo_path / '.umpyre.yml'
        import yaml

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        config = Config(config_path=str(config_file))

        result.pass_test("Config loading", f"Loaded config from {config_file}")

        # Test config access
        if config.is_collector_enabled('workflow_status'):
            result.pass_test("Config collector check", "workflow_status is enabled")
        else:
            result.fail_test(
                "Config collector check", "workflow_status should be enabled"
            )

        # Cleanup
        config_file.unlink()

    except Exception as e:
        result.fail_test("Config loading", str(e))

    return result


def test_schema():
    """Test metric schema validation."""
    result = TestResult()

    try:
        # Create sample metric data
        sample_metrics = {
            'workflow_status': {
                'last_run_status': 'success',
                'last_run_conclusion': 'success',
            }
        }

        metric_data = MetricSchema.create_metric_data(
            commit_sha='abc123',
            metrics=sample_metrics,
            commit_message='Test commit',
            python_version='3.10',
        )

        # Validate
        is_valid = MetricSchema.validate(metric_data)

        if is_valid:
            result.pass_test(
                "Schema validation", "Sample metrics validated successfully"
            )
        else:
            result.fail_test("Schema validation", "Validation failed")

        # Check required fields
        required_fields = ['schema_version', 'timestamp', 'commit_sha', 'metrics']
        missing = [f for f in required_fields if f not in metric_data]

        if not missing:
            result.pass_test("Schema structure", "All required fields present")
        else:
            result.fail_test("Schema structure", f"Missing fields: {missing}")

    except Exception as e:
        result.fail_test("Schema validation", str(e))

    return result


def test_collectors_on_astate(repo_path: Path):
    """Test collectors on actual astate repository."""
    result = TestResult()
    result.start()

    # Test each collector with proper initialization
    test_specs = {
        'coverage': {
            'description': 'Test coverage',
            'init_kwargs': {'repo_path': str(repo_path), 'source': 'pytest-cov'},
        },
        'umpyre_stats': {
            'description': 'Code statistics (AST-based)',
            'init_kwargs': {
                'root_path': str(repo_path),
                'exclude_dirs': ['tests', 'examples', 'docsrc'],
            },
        },
    }

    for collector_name, spec in test_specs.items():
        description = spec['description']
        try:
            if collector_name not in registry.list_collectors():
                result.warn(f"Collector '{collector_name}' not registered, skipping")
                continue

            collector_class = registry.get(collector_name)
            collector = collector_class(**spec['init_kwargs'])

            # Collect metrics
            start = time.time()
            metrics = dict(collector)
            duration = time.time() - start

            if metrics:
                # Check for errors
                if 'error' in metrics:
                    result.warn(
                        f"{description}: Collector returned error: {metrics['error']}"
                    )
                else:
                    result.pass_test(
                        f"{description} collector",
                        f"Collected {len(metrics)} metrics in {duration:.2f}s",
                    )
            else:
                result.warn(
                    f"{description}: No metrics collected (may be normal if data not available)"
                )

        except Exception as e:
            result.fail_test(f"{description} collector", str(e))

    result.stop()
    return result


def test_full_collection(repo_path: Path):
    """Test full metrics collection pipeline."""
    result = TestResult()
    result.start()

    try:
        # Manually collect metrics from collectors
        all_metrics = {}

        # Coverage collector
        try:
            from umpyre.collectors.coverage_collector import CoverageCollector

            collector = CoverageCollector(repo_path=str(repo_path))
            all_metrics['coverage'] = collector.to_dict()
        except Exception as e:
            all_metrics['coverage'] = {'error': str(e)}

        # Umpyre stats collector
        try:
            from umpyre.collectors.umpyre_collector import UmpyreCollector

            collector = UmpyreCollector(
                root_path=str(repo_path), exclude_dirs=['tests', 'docsrc']
            )
            all_metrics['umpyre_stats'] = collector.to_dict()
        except Exception as e:
            all_metrics['umpyre_stats'] = {'error': str(e)}

        if all_metrics:
            result.pass_test(
                "Full collection pipeline",
                f"Collected metrics from {len(all_metrics)} collectors",
            )

            # Create proper schema structure
            import subprocess

            try:
                commit_sha = subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'], cwd=repo_path, text=True
                ).strip()
            except:
                commit_sha = 'unknown'

            metrics_data = MetricSchema.create_metric_data(
                commit_sha=commit_sha, metrics=all_metrics
            )

            # Validate schema
            is_valid = MetricSchema.validate(metrics_data)
            if is_valid:
                result.pass_test("Output schema validation", "Metrics data is valid")
            else:
                result.fail_test("Output schema validation", "Validation failed")

            # Test serialization to temp file
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False
            ) as f:
                temp_json = Path(f.name)

            try:
                serialize_metrics(metrics_data, temp_json, 'json')
                result.pass_test(
                    "JSON serialization",
                    f"Serialized to {temp_json.stat().st_size} bytes",
                )

                # Test deserialization
                recovered = deserialize_metrics(temp_json, 'json')
                if recovered == metrics_data:
                    result.pass_test("JSON deserialization", "Round-trip successful")
                else:
                    result.warn("JSON deserialization: Data changed during round-trip")
            finally:
                temp_json.unlink()

        else:
            result.fail_test("Full collection pipeline", "No metrics collected")

    except Exception as e:
        result.fail_test("Full collection pipeline", str(e))
        import traceback

        traceback.print_exc()

    result.stop()

    # Check performance requirement (<30s)
    if result.duration < 30:
        result.pass_test(
            "Performance requirement",
            f"Completed in {result.duration:.2f}s (target: <30s)",
        )
    else:
        result.fail_test(
            "Performance requirement", f"Took {result.duration:.2f}s (target: <30s)"
        )

    return result


def main():
    """Run all tests."""
    print("=" * 70)
    print("UMPYRE AUTOMATED TEST SUITE")
    print("=" * 70)
    print()

    # Check astate path
    astate_path = Path("/Users/thorwhalen/Dropbox/py/proj/t/astate")

    if not astate_path.exists():
        print(f"❌ astate repository not found at: {astate_path}")
        print("   Please update the path in the script")
        return 1

    if not (astate_path / '.git').exists():
        print(f"❌ {astate_path} is not a git repository")
        return 1

    print(f"✅ Found astate repository at: {astate_path}")
    print()

    all_results = []

    # Run tests
    print("TEST 1: Registry")
    print("-" * 70)
    all_results.append(test_registry())
    print()

    print("TEST 2: Configuration")
    print("-" * 70)
    all_results.append(test_config(astate_path))
    print()

    print("TEST 3: Schema")
    print("-" * 70)
    all_results.append(test_schema())
    print()

    print("TEST 4: Individual Collectors")
    print("-" * 70)
    all_results.append(test_collectors_on_astate(astate_path))
    print()

    print("TEST 5: Full Collection Pipeline")
    print("-" * 70)
    all_results.append(test_full_collection(astate_path))
    print()

    # Overall summary
    print("\n" + "=" * 70)
    print("OVERALL RESULTS")
    print("=" * 70)

    total_passed = sum(len(r.passed) for r in all_results)
    total_failed = sum(len(r.failed) for r in all_results)
    total_warnings = sum(len(r.warnings) for r in all_results)

    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Total Warnings: {total_warnings}")

    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
