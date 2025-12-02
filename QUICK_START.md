# Umpyre Quick Start Guide

## Installation

```bash
pip install umpyre
```

## Basic Usage (5 minutes)

### 1. Test Locally (Dry Run)

```bash
# In any Python repo with tests
cd /path/to/your/repo

# Collect metrics without storing
umpyre collect --no-store
```

You'll see output like:
```
Collecting metrics for abc1234...
Metrics collected (not stored):
{
  "schema_version": "1.0",
  "timestamp": "2025-11-14T12:00:00Z",
  ...
}
Collection completed in 3.45s
```

### 2. Store Metrics Locally

```bash
# This creates a 'code-metrics' branch
umpyre collect
```

Check the branch:
```bash
git fetch origin code-metrics  # If you pushed
git checkout code-metrics
ls -la  # See metrics.json, metrics.csv, history/
```

### 3. Customize Configuration

Create `.github/umpyre-config.yml`:

```yaml
schema_version: "1.0"

collectors:
  coverage:
    enabled: true
  umpyre_stats:
    enabled: true
    exclude_dirs: [tests, examples, scrap]

storage:
  branch: code-metrics
  formats: [json, csv]
```

Run again:
```bash
umpyre collect --config .github/umpyre-config.yml
```

### 4. Add to GitHub Actions

In `.github/workflows/ci.yml`, add after your tests:

```yaml
jobs:
  test-and-publish:
    runs-on: ubuntu-latest
    steps:
      # ... your existing steps ...
      
      - name: Track Code Metrics
        if: success()  # Only after successful tests
        uses: i2mint/umpyre/actions/track-metrics@master
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

Commit and push - metrics will be tracked automatically!

## What Gets Tracked?

By default (if tools are available):

- ✅ **Test Coverage** (from pytest-cov or coverage.py)
  - Line coverage %
  - Branch coverage %

- ✅ **Code Statistics** (built-in analyzer)
  - Number of functions and classes
  - Lines of code (total, empty, comments, docs)
  - Code ratios

- ✅ **CI Health** (from GitHub API, in Actions only)
  - Last run status
  - Recent failure count

- ⚠️ **Complexity** (requires `pip install wily`)
  - Cyclomatic complexity
  - Maintainability index

## Viewing Metrics

### In Git Branch

```bash
git checkout code-metrics
cat metrics.json  # Latest snapshot
cat metrics.csv   # Flat format for analysis
ls history/       # Historical records by month
```

### In Python

```python
from umpyre.storage import deserialize_metrics

metrics = deserialize_metrics("metrics.json", format="json")
print(metrics["metrics"]["coverage"]["line_coverage"])
# 87.5
```

### With Pandas

```python
import pandas as pd

# Load historical data
df = pd.read_csv("metrics.csv")
print(df.head())

# Or load multiple history files
import glob
import json

history = []
for file in glob.glob("history/*/*.json"):
    with open(file) as f:
        history.append(json.load(f))

df = pd.DataFrame(history)
```

## Common Use Cases

### Track Coverage Over Time

```bash
# Collect after each test run
pytest --cov=mypackage --cov-report=json
umpyre collect
```

### Only Track Specific Metrics

`.github/umpyre-config.yml`:
```yaml
collectors:
  coverage:
    enabled: true
  umpyre_stats:
    enabled: false  # Disable
  wily:
    enabled: false  # Disable
```

### Custom Branch Name

```yaml
storage:
  branch: my-metrics  # Instead of code-metrics
```

## Troubleshooting

### "No coverage file found"
- Run tests with `--cov-report=json` or `--cov-report=xml`
- Coverage file should be in repo root

### "wily not installed"
- Install: `pip install wily`
- Or disable in config: `wily: { enabled: false }`

### "Not a git repository"
- Umpyre requires git for storage
- Initialize: `git init`

### UmpyreCollector returns 0
- Known issue with some directory structures
- Disable in config if problematic: `umpyre_stats: { enabled: false }`

## Next Steps

- 📖 Read full docs: `README.md`
- 🔧 See all config options: `.github/umpyre-config.yml`
- 🧪 Test on repos: `astate`, `ps`
- 📊 Coming soon: Visualization and dashboards!

## Get Help

- Issues: https://github.com/i2mint/umpyre/issues
- Docs: See `README.md` and `IMPLEMENTATION_SUMMARY.md`
