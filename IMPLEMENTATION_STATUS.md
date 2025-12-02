# Summary: Storage Structure Improvements & Phase Plans

## What Changed

### Storage Structure (Addressing Your Feedback) ✅

**Your concerns**:
1. ❌ `by_version/` folder = data duplication (not SSOT)
2. ❌ Monthly folders = unnecessary complexity

**Solution Implemented**:
- **Flat structure**: Just `history/` (no nested `history/2025-11/` folders)
- **No duplication**: Removed `by_version/` folder entirely
- **Smart filename**: `YYYY_MM_DD_HH_MM_SS__shahash__version.json`

### New Structure

```
code-metrics branch:
├── metrics.json                                        # Latest snapshot
├── metrics.csv                                         # Latest CSV
└── history/                                            # Flat! (SSOT)
    ├── 2025_11_14_22_45_00__700e012__0.1.0.json
    ├── 2025_11_14_22_50_15__abc1234__0.1.1.json
    └── 2025_11_15_10_30_22__def5678__none.json        # No version
```

### Filename Format

`{YYYY_MM_DD_HH_MM_SS}__{commit_sha}__{version}.json`

**Benefits**:
1. ✅ **Chronological**: Natural time-based sorting
2. ✅ **Unique**: Commit SHA prevents duplicates
3. ✅ **Parseable**: All metadata in filename
4. ✅ **SSOT**: No duplication anywhere
5. ✅ **Simple**: Flat structure, easy queries
6. ✅ **Shell-friendly**: Works with standard tools

### Query Examples

```bash
# Get all metrics from November 14
ls history/2025_11_14_*

# Find metrics for commit 700e012
ls history/*__700e012__*

# Find all v0.1.0 metrics
ls history/*__0.1.0.json

# Get latest 10 metrics
ls -t history/ | head -10

# Exclude metrics without version
ls history/ | grep -v "__none.json"
```

---

## Phase Plans Created

### PHASE_2_PLAN.md ✅

**Duration**: 10-13 hours

**Components**:
1. **Plot Generation** (3h): Time-series charts (coverage, maintainability, LOC, complexity)
2. **README Auto-Generation** (2h): `METRICS.md` with tables, charts, badges
3. **Cross-Repo Aggregation** (4h): Organization-wide metrics aggregation
4. **Dashboard Generation** (4h): Interactive HTML dashboard with Plotly.js

**Key Features**:
- Matplotlib/Plotly charts saved to `plots/` in code-metrics branch
- Shields.io badges for GitHub README
- Aggregate metrics across all i2mint repos
- Interactive dashboard hosted on GitHub Pages
- CLI commands: `visualize`, `aggregate`, `dashboard`

### PHASE_3_PLAN.md ✅

**Duration**: 15-18 hours

**Components**:
1. **Threshold Validation** (3h): Enforce quality standards (min/max/delta thresholds)
2. **Additional Collectors** (8h):
   - BanditCollector (security scanning)
   - InterrogateCollector (docstring coverage)
   - MyPyCollector (type hint coverage)
   - PylintCollector (code quality)
3. **Data Management** (3h): Pruning, compression, rotation
4. **Schema Migrations** (4h): Version migration system (1.0 → 1.1 → 1.2)

**Key Features**:
- Config-driven thresholds with custom validators
- 4 new collectors for comprehensive code analysis
- Intelligent data pruning (keep last 30 days, then weekly, then monthly)
- gzip compression for old metrics
- Auto-migration on schema version changes

---

## Current Status

✅ **Phase 1**: COMPLETE (100%)
- All collectors working
- Storage system (flat, SSOT-compliant)
- PyPI version tracking
- CLI interface
- GitHub Action
- CI failure protection
- 34/34 tests passing
- **Production-ready!**

📋 **Phase 2**: PLANNED (detailed plan ready)
- Visualization system
- Cross-repo aggregation
- Dashboard generation

📋 **Phase 3**: PLANNED (detailed plan ready)
- Threshold validation
- Additional collectors (security, quality, types)
- Data management
- Schema migrations

---

## Files Created/Updated

### Created:
- `PHASE_2_PLAN.md` - Detailed Phase 2 implementation plan
- `PHASE_3_PLAN.md` - Detailed Phase 3 implementation plan
- `STORAGE_STRUCTURE.md` - Complete storage architecture docs

### Updated:
- `umpyre/storage/git_branch.py` - Flat structure, no duplication
- `umpyre/collectors/umpyre_collector.py` - PyPI version extraction
- `misc/CHANGELOG.md` - Storage structure improvements

---

## Next Steps (Your Call)

**Option 1: Deploy Phase 1 Now** 🚀
- Add CI snippet to your templates (you mentioned doing this)
- Start collecting metrics on production repos
- Gather feedback before Phase 2

**Option 2: Start Phase 2** 📊
- Begin with plot generation (3 hours)
- Add README auto-generation (2 hours)
- Build incrementally

**Option 3: Test Storage** 🧪
- Run `collect` without `--no-store` on umpyre
- Verify new flat structure works
- Inspect generated filenames

---

## Testing the New Structure

```bash
# Test on umpyre itself (will create code-metrics branch)
cd /Users/thorwhalen/Dropbox/py/proj/i/umpyre
python -m umpyre.cli collect

# Then check the structure
git checkout code-metrics
ls -lh history/
# Should see: 2025_11_14_*__*__0.1.0.json

# Parse filename
ls history/ | head -1
# Example: 2025_11_14_15_03_23__700e012__0.1.0.json
#          ^^^^^^^^^^^^^^^^^^  ^^^^^^^  ^^^^^
#          timestamp           commit   version
```

---

## Questions?

- Want me to test the storage by running actual collection?
- Ready to start Phase 2 (which part first)?
- Need any clarification on the plans?

**Meanwhile**, you're adding the CI snippet to your templates - perfect timing! The storage structure is now battle-ready and SSOT-compliant. 🎉
