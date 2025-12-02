# Failure Protection Strategy

Umpyre implements **three layers of failure protection** to ensure metrics collection never breaks your CI/CD pipeline.

## Why This Matters

Metrics collection is **informational**, not critical. Your CI should:
- ✅ Always publish to PyPI successfully
- ✅ Always commit version bumps
- ✅ Always tag releases
- ⚠️  Try to collect metrics, but don't fail if it doesn't work

## Three Layers of Protection

### Layer 1: GitHub Actions `continue-on-error`

In your CI workflow file, the metrics step has `continue-on-error: true`:

```yaml
- name: Track Code Metrics
  uses: i2mint/umpyre/actions/track-metrics@master
  continue-on-error: true  # Don't fail CI if metrics collection fails
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

**What it does**: If the entire action fails (Python crashes, dependency issues, etc.), GitHub Actions will log the error but continue with the next step.

### Layer 2: Action Error Handling

The GitHub Action itself catches errors and always exits with code 0:

```bash
set +e  # Don't exit on error

python -m umpyre.cli collect --config "${{ inputs.config-path }}"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Metrics collection completed successfully"
else
  echo "⚠️ Metrics collection failed with exit code $EXIT_CODE"
  echo "This is informational only - CI pipeline continues"
fi

exit 0  # Always succeed
```

**What it does**: Even if umpyre CLI fails, the action reports it as a warning and exits successfully.

### Layer 3: CLI Error Handling

The umpyre CLI detects CI environment and returns exit code 0 on errors:

```python
def cmd_collect(args):
    try:
        # ... collect metrics ...
        return 0
    except Exception as e:
        print(f"❌ Error during metrics collection: {e}")
        
        # In CI mode, log but don't fail
        if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
            print("⚠️  Running in CI - treating as non-fatal")
            return 0
        
        return 1  # Fail in local development
```

**What it does**: 
- **In CI**: Logs error, returns 0 (success)
- **Locally**: Returns 1 (failure) so developers know something's wrong

## Behavior Summary

| Scenario | Layer | CI Exit Code | Result |
|----------|-------|--------------|--------|
| Collection succeeds | - | 0 | ✅ Metrics stored |
| Collector error (missing coverage) | L3 | 0 | ⚠️ Partial metrics stored |
| CLI error (no git repo) | L3 | 0 | ⚠️ Error logged, CI continues |
| Action failure (Python crash) | L2 | 0 | ⚠️ Error logged, CI continues |
| Timeout or system error | L1 | 0 | ⚠️ Step marked as warning |

## Local Development

When running locally (not in CI), errors **will fail** with exit code 1:

```bash
$ python -m umpyre.cli collect
❌ Error during metrics collection: ...
Collection failed after 0.02s
$ echo $?
1
```

This helps you debug issues during development.

## Testing Failure Modes

### Test Layer 3 (CLI error handling):

```bash
# Normal mode - should fail
cd /tmp/not-a-repo
python -m umpyre.cli collect
echo $?  # Returns 1

# CI mode - should not fail
CI=true python -m umpyre.cli collect
echo $?  # Returns 0
```

### Test Layer 2 (Action error handling):

Create a workflow with invalid config and check GitHub Actions logs - step will show warning but not fail.

### Test Layer 1 (continue-on-error):

Trigger any catastrophic failure (kill Python process, etc.) - CI will continue.

## Best Practices

1. **Always use `continue-on-error: true`** in CI workflows
2. **Place metrics collection AFTER critical steps** (publish, tag, commit)
3. **Monitor but don't alert on metrics failures** - treat as informational
4. **Test locally first** - fix issues before they hit CI

## Collector-Level Error Handling

Individual collectors also handle errors gracefully:

```python
def collect(self) -> dict:
    try:
        # ... collect metrics ...
        return metrics
    except Exception as e:
        return {
            "num_functions": 0,
            "error": str(e)
        }
```

This ensures one broken collector doesn't fail the entire collection.

## Gradual Degradation

Umpyre fails gracefully at every level:
- Missing collector dependency? Skip that collector
- Coverage file not found? Return zero coverage
- Git command fails? Use environment variables
- Network error? Store partial metrics

The goal: **Always provide some value, never break CI.**
