# Metrics Storage Structure

## Overview

Metrics are stored in a separate `code-metrics` git branch with a **flat, chronologically-ordered structure** using parseable filenames: `YYYY_MM_DD_HH_MM_SS__shahash__version.json`

This design follows **SSOT principles** (no data duplication) while enabling efficient querying by time, commit, or version.

## Storage Location

**Without** `--no-store` flag: Metrics are pushed to the `code-metrics` branch in the same repository.

**With** `--no-store` flag: Metrics are collected and displayed but not stored.

## Branch Structure

```
code-metrics branch:
├── metrics.json                                        # Latest snapshot
├── metrics.csv                                         # Latest CSV
└── history/                                            # Flat history (SSOT!)
    ├── 2025_11_14_22_45_00__700e012__0.1.0.json
    ├── 2025_11_14_22_50_15__abc1234__0.1.1.json
    ├── 2025_11_15_10_30_22__def5678__0.1.1.json
    ├── 2025_11_15_14_20_00__9a8b7c6__none.json        # No version detected
    └── 2025_11_16_09_00_00__1234567__0.2.0.json
```

## Filename Format

**Pattern**: `{YYYY_MM_DD_HH_MM_SS}__{commit_sha[:7]}__{pypi_version}.json`

**Components**:
1. **Timestamp**: `YYYY_MM_DD_HH_MM_SS` - Chronological ordering
2. **Commit SHA**: 7-character short hash - Uniqueness guarantee
3. **PyPI Version**: Semantic version or `none` - Easy filtering

**Examples**:
- `2025_11_14_22_45_00__700e012__0.1.0.json`
- `2025_11_15_10_30_22__def5678__none.json` (no version found)

## Key Design Decisions

### 1. Flat Structure (No Nested Folders) ✅

**Why**: Simplicity and easy querying
- No need to know which month to look in
- Simple `ls` or glob patterns
- Easy to parse all metrics
- No directory traversal overhead

### 2. Chronological Ordering ✅

**Why**: Natural time-based queries
- Files are already sorted by time (filename sorting)
- Easy to find "latest N metrics"
- Easy to filter by date range
- Works with standard shell tools

### 3. Commit SHA for Uniqueness ✅

**Why**: One entry per commit
- Guarantees no duplicates (same commit = overwrite)
- Git-traceable (link to exact code state)
- Works even without version tags
- 7 chars enough for uniqueness in practice

### 4. PyPI Version for Filtering ✅

**Why**: Easy version-based queries without duplication
- No separate `by_version/` folder (SSOT!)
- Simple grep/filter to find version
- Supports repos without versions (`none`)
- Parseable from filename

### 5. No Data Duplication (SSOT) ✅

**Why**: Single source of truth
- One file = one commit's metrics
- No redundant storage in `by_version/`
- Easier to maintain consistency
- Smaller repository size

## Querying Patterns

### Query by Time Range

```bash
# Get all metrics from November 2025
git checkout code-metrics
ls history/2025_11_*

# Get metrics from specific date
ls history/2025_11_14_*

# Get latest 10 metrics
ls -t history/ | head -10
```

### Query by Commit SHA

```bash
# Find metrics for commit 700e012
git checkout code-metrics
ls history/*__700e012__*

# Or with grep
ls history/ | grep "700e012"
```

### Query by Version

```bash
# Find all metrics for version 0.1.0
git checkout code-metrics
ls history/*__0.1.0.json

# Find all metrics with a version (exclude 'none')
ls history/ | grep -v "__none.json"

# Get latest metric for version 0.1.0
ls -t history/*__0.1.0.json | head -1
```

### Parse Filename Components

```python
import re
from pathlib import Path

def parse_metric_filename(filename: str) -> dict:
    """
    Parse metric filename into components.
    
    Example: "2025_11_14_22_45_00__700e012__0.1.0.json"
    Returns: {
        "timestamp": "2025-11-14T22:45:00",
        "commit_sha": "700e012",
        "pypi_version": "0.1.0",
    }
    """
    pattern = r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})__(\w{7})__(.+)\.json'
    match = re.match(pattern, filename)
    
    if not match:
        raise ValueError(f"Invalid filename format: {filename}")
    
    timestamp_str, sha, version = match.groups()
    
    # Convert timestamp to ISO format
    timestamp = timestamp_str.replace('_', '-', 2).replace('_', ':', 2).replace('_', 'T', 1)
    
    return {
        "timestamp": timestamp,
        "commit_sha": sha,
        "pypi_version": None if version == "none" else version,
    }

# Usage
for file in Path("history").glob("*.json"):
    info = parse_metric_filename(file.name)
    print(f"Commit {info['commit_sha']} at {info['timestamp']} (v{info['pypi_version']})")
```

## Metrics Schema

```json
{
  "schema_version": "1.0",
  "timestamp": "2025-11-14T22:45:00Z",
  "commit_sha": "700e012d85d1393de95d0634eec8efa224ff0bc9",
  "commit_message": "Refactor collector...",
  "python_version": "3.12",
  "metrics": {
    "umpyre_stats": {
      "num_functions": 134,
      "num_classes": 13,
      "total_lines": 2750,
      "pypi_version": "0.1.0",        ← Used in filename!
      "files_analyzed": 16,
      ...
    },
    "coverage": { ... },
    "wily": { ... }
  },
  "collection_duration_seconds": 3.42
}
```

## Benefits of This Structure

1. **SSOT**: No data duplication (no `by_version/` folder)
2. **Chronological**: Files naturally sorted by time
3. **Parseable**: All info in filename (timestamp, commit, version)
4. **Unique**: One entry per commit (commit SHA)
5. **Queryable**: Easy to filter by time, commit, or version
6. **Simple**: Flat structure, no directory traversal
7. **Scalable**: Works with thousands of metrics files
8. **Shell-Friendly**: Standard tools (ls, grep, sort) work perfectly

## CI Workflow Integration

When running in CI (e.g., GitHub Actions):

```yaml
- name: Track Code Metrics
  uses: ./actions/track-metrics
  with:
    branch: code-metrics
  continue-on-error: true  # Never fails CI
```

On each CI run after PyPI publish:
1. Collects metrics (including pypi_version from pyproject.toml)
2. Stores as `history/{timestamp}__{commit_sha}__{version}.json`
3. Updates `metrics.json` (latest snapshot)
4. No duplication, no nested folders

## Migration from Old Structure

If you have old structure with monthly folders or `by_version/`:
1. Old metrics remain accessible
2. New metrics use flat structure
3. No breaking changes
4. Can run migration script to flatten old structure (optional)
