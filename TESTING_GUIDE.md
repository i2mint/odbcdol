# Testing Guide for Umpyre on astate and ps Repositories

## Test Repositories

1. **https://github.com/thorwhalen/astate** - Small, stable repo (recommended first test)
2. **https://github.com/thorwhalen/ps** - Larger repo for scale testing

---

## Pre-Test Setup

```bash
# Install umpyre in development mode
cd /path/to/umpyre
pip install -e .

# Verify installation
umpyre --help
python -m pytest tests/ -v  # Should pass 32 tests
```

---

## Test 1: astate Repository

### Step 1: Clone and Setup

```bash
cd ~/test_metrics  # Or wherever you want to test
git clone https://github.com/thorwhalen/astate
cd astate

# Check if it has tests and coverage
pytest --cov=astate --cov-report=json  # Generate coverage data
ls -la coverage.json  # Should exist
```

### Step 2: Create Config

```bash
mkdir -p .github
cat > .github/umpyre-config.yml << 'EOF'
schema_version: "1.0"

collectors:
  coverage:
    enabled: true
    source: pytest-cov
  
  umpyre_stats:
    enabled: true
    exclude_dirs: [tests, examples, scrap]
  
  workflow_status:
    enabled: false  # Requires GitHub token

storage:
  branch: code-metrics-test
  formats: [json, csv]
EOF
```

### Step 3: Dry Run

```bash
# Test without storing
umpyre collect --no-store

# Expected output:
# - Collecting metrics for <commit_sha>...
# - Metrics collected (not stored):
# - {JSON output}
# - Collection completed in X.XXs

# Check for errors
echo $?  # Should be 0
```

### Step 4: Store Metrics

```bash
# Create metrics branch
umpyre collect --config .github/umpyre-config.yml

# Verify branch was created
git branch -a | grep code-metrics-test
# Should see: code-metrics-test

# Check branch contents
git checkout code-metrics-test
ls -la
# Expected files:
# - metrics.json
# - metrics.csv  
# - history/YYYY-MM/*.json
```

### Step 5: Verify Metrics

```bash
# Check JSON structure
cat metrics.json | python -m json.tool | head -20

# Check CSV
cat metrics.csv | head -10

# Verify historical record
ls history/$(date +%Y-%m)/
```

### Step 6: Test Multiple Collections

```bash
# Switch back to main branch
git checkout main

# Make a small change
echo "# Test comment" >> README.md
git add README.md
git commit -m "Test: trigger new metrics collection"

# Collect again
umpyre collect

# Verify new entry in history
git checkout code-metrics-test
ls history/$(date +%Y-%m)/
# Should have 2 files now
```

---

## Test 2: ps Repository

### Step 1: Clone and Setup

```bash
cd ~/test_metrics
git clone https://github.com/thorwhalen/ps
cd ps

# Run tests if available
pytest --cov=ps --cov-report=json
```

### Step 2: Create Config (Same as astate)

```bash
mkdir -p .github
# Copy same config from astate test
```

### Step 3: Performance Test

```bash
# Time the collection
time umpyre collect --no-store

# Expected: < 30 seconds
# If slower, check which collector is taking time
```

### Step 4: Test with Wily (Optional)

```bash
# Install wily
pip install wily

# Update config to enable wily
cat >> .github/umpyre-config.yml << 'EOF'
collectors:
  wily:
    enabled: true
    max_revisions: 3  # Keep it small for testing
EOF

# Build wily cache (first time is slow)
wily build . --max-revisions 3

# Collect with wily
umpyre collect
```

---

## Test 3: GitHub Actions Integration (Optional)

If you have write access to a fork:

### Create Test Workflow

```yaml
# .github/workflows/test-metrics.yml
name: Test Metrics Collection

on:
  push:
    branches: [test-metrics]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest --cov=astate --cov-report=json
      
      - name: Track Metrics
        if: success()
        uses: i2mint/umpyre/actions/track-metrics@master
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Push and Test

```bash
git checkout -b test-metrics
git add .github/workflows/test-metrics.yml
git commit -m "Add metrics tracking workflow"
git push origin test-metrics

# Check Actions tab in GitHub UI
# Verify code-metrics-test branch is created/updated
```

---

## Verification Checklist

### For Each Repository:

- [ ] `umpyre collect --no-store` runs without errors
- [ ] Collection completes in < 30 seconds
- [ ] `code-metrics-test` branch is created
- [ ] `metrics.json` exists and is valid JSON
- [ ] `metrics.csv` exists and is valid CSV
- [ ] `history/` directory has monthly subdirectories
- [ ] Multiple collections create separate history files
- [ ] Coverage metrics are present (if tests exist)
- [ ] Code stats metrics are present
- [ ] No sensitive data in metrics files
- [ ] Branch can be pushed to remote

### Expected Metrics Structure:

```json
{
  "schema_version": "1.0",
  "timestamp": "2025-11-14T...",
  "commit_sha": "...",
  "metrics": {
    "coverage": {
      "line_coverage": <number>,
      "branch_coverage": <number>
    },
    "umpyre_stats": {
      "num_functions": <number>,
      "num_classes": <number>,
      "total_lines": <number>
    }
  }
}
```

---

## Common Issues and Solutions

### Issue: "No coverage file found"

**Solution:**
```bash
# Generate coverage data first
pytest --cov=<package> --cov-report=json
# Then collect
umpyre collect
```

### Issue: "Not a git repository"

**Solution:**
```bash
git init
git add .
git commit -m "Initial commit"
```

### Issue: UmpyreCollector returns 0 functions

**Solution:** This is a known issue. Disable in config:
```yaml
collectors:
  umpyre_stats:
    enabled: false
```

### Issue: Collection is slow (>30s)

**Check:**
- Disable wily if not needed
- Reduce `max_revisions` for wily
- Check if repository is very large

### Issue: Branch push fails

**Solution:**
```bash
# Pull first
git checkout code-metrics-test
git pull origin code-metrics-test
# Then try collect again
```

---

## Success Criteria

✅ Both repositories successfully collect metrics  
✅ Collection time < 30 seconds each  
✅ Metrics stored correctly in git branches  
✅ JSON and CSV formats both valid  
✅ Historical tracking works across multiple runs  
✅ No errors in dry-run mode  
✅ No sensitive data exposed in metrics  

---

## Reporting Results

After testing, document:

1. **Performance:**
   - Collection time for each repo
   - Any timeouts or slow operations

2. **Metrics Quality:**
   - Which collectors worked
   - Which had issues
   - Accuracy of metrics

3. **Usability:**
   - Ease of setup
   - Clarity of output
   - Any confusing errors

4. **Issues Found:**
   - Error messages
   - Unexpected behavior
   - Suggestions for improvement

---

## Next Steps After Testing

If tests pass:
1. Document any issues found
2. Consider enabling on production repos
3. Plan Phase 2 (visualization) based on needs

If tests fail:
1. Check error messages
2. Verify environment setup
3. Review logs in `IMPLEMENTATION_SUMMARY.md`
4. Open issues with details
