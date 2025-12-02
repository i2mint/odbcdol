# Changelog

All notable changes to the umpyre project are recorded here.

## 2025-11-14 - Simplified Storage Structure (SSOT Compliance)

### Changed
- **Storage structure**: Completely redesigned for SSOT principles and simplicity
  - **Flat structure**: Removed monthly folders (`history/2025-11/`) - now just `history/`
  - **Removed data duplication**: Eliminated `by_version/` folder (was redundant)
  - **New filename format**: `YYYY_MM_DD_HH_MM_SS__shahash__version.json`
    - Chronologically ordered (sorts naturally by time)
    - All info parseable from filename (timestamp, commit, version)
    - Example: `2025_11_14_22_45_00__700e012__0.1.0.json`
  - **Benefits**: Single source of truth, easier querying, simpler maintenance

### Rationale
- User feedback: "Is it a good idea to have a separate by_version folder? We'll be repeating data there no? That's not very SSOT."
- Flat structure is simpler than nested monthly directories
- Filename contains all indexing info (no need for duplicate folders)
- Shell-friendly: `ls`, `grep`, `sort` work perfectly

## 2025-11-14 - Added PyPI Version Tracking and Commit-Based Indexing

### Added
- **PyPI version extraction**: `UmpyreCollector` now automatically detects and includes `pypi_version` in metrics
  - Checks `pyproject.toml` (preferred), `setup.py` (fallback), or `__init__.py` (last resort)
  - Uses regex to extract version strings (e.g., "0.1.0", "1.2.3-beta")
  - Returns `null` if no version found
- **Commit-SHA indexing**: Storage now uses commit hash as primary index for uniqueness
  - Historical files named as `{commit_sha[:7]}.json` (e.g., `700e012.json`)
  - Guarantees one entry per commit (prevents duplicates)
  - Timestamp removed from filename for cleaner structure
- **By-version secondary index**: New `by_version/` directory for easy version-based queries
  - Files named as `{pypi_version}.json` (e.g., `0.1.0.json`)
  - Contains latest metrics for each published version
  - Enables comparison across releases

### Changed
- **Storage structure**: Now uses dual indexing system
  ```
  code-metrics/
  ├── history/2025-11/{commit_sha}.json  ← Primary index
  └── by_version/{version}.json           ← Secondary index
  ```
- **Root path handling**: Fixed `UmpyreCollector.__init__` to convert `root_path` to `Path` object (was causing type errors)

### Documentation
- Added `STORAGE_STRUCTURE.md` with comprehensive storage design documentation
- Explains uniqueness guarantees, querying patterns, and CI integration

# Changelog

All notable changes to the umpyre project are documented here.

## 2025-11-14 - Fixed UmpyreCollector with AST-based Parsing

### Changed
- **UmpyreCollector**: Completely reimplemented using Python's AST (Abstract Syntax Tree) module instead of dynamic imports
  - Previously used `py2store.sources.Attrs.module_from_path()` which dynamically imported files, causing setup.py and other files to execute
  - Now uses safe AST parsing that analyzes code structure without executing it
  - Works on all Python files including setup.py, conf.py, and scripts
  - Maintains same metrics output format for backward compatibility
  
### Added
- `_analyze_file()` method: AST-based analysis of individual Python files
- `_should_analyze()` method: Improved filtering logic for files to analyze
- `files_analyzed` metric: Now tracks how many files were successfully analyzed
- Error tracking: Records parsing errors per file without failing entire collection

### Fixed
- **Critical**: UmpyreCollector no longer crashes when encountering setup.py or other executable scripts
- All 5 umpyre_collector tests now pass (previously 2 were skipped)
- Total test suite: 34/34 tests passing

### Performance
- AST parsing is faster than dynamic imports
- No subprocess overhead
- No risk of code execution side effects

## 2025-11-14 - Phase 1 Implementation Complete

### Added

**Architecture & Configuration**
- Implemented config-driven architecture with YAML configuration support
- Created versioned schema system (`schema.py`) for metrics with migration support
- Built pluggable collector system with Mapping interface pattern
- Added comprehensive configuration loading with deep merge and validation

**Metric Collectors**
- `WorkflowStatusCollector`: Track GitHub CI/CD workflow status via API
  - Last run status (success/failure/other)
  - Recent failure counts with configurable lookback
  - Last successful run timestamp
- `WilyCollector`: Complexity metrics using wily
  - Cyclomatic complexity (configurable operators)
  - Maintainability index
  - Limited to recent commits for performance (default: 5 revisions)
- `CoverageCollector`: Test coverage from pytest-cov or coverage.py
  - Line and branch coverage percentages
  - Supports JSON and XML (Cobertura) report formats
  - Auto-detection of coverage files
- `UmpyreCollector`: Code statistics using existing `python_code_stats` module
  - Function/class counts
  - Line metrics (total, empty, comments, docs)
  - Code ratios and averages

**Storage System**
- Git branch-based storage (`GitBranchStorage`)
  - Stores metrics in separate branch (default: `code-metrics`)
  - Supports JSON and CSV formats
  - Monthly history organization
  - Handles concurrent commits with retry logic
- Serialization formats module with JSON/CSV support
- Flat CSV format for easy pandas integration

**CLI Interface**
- `umpyre collect`: Collect and store metrics
  - Config-driven collection
  - Auto-detects git commit info
  - Dry-run mode (`--no-store`)
  - Environment variable support (GITHUB_SHA, GITHUB_REPOSITORY)
- `umpyre validate`: Placeholder for threshold validation (Phase 3)

**GitHub Action**
- Reusable composite action at `actions/track-metrics/action.yml`
- Integrates with GitHub CI/CD workflows
- Auto-installs dependencies (umpyre, coverage, wily, bandit, interrogate)
- Configurable Python version and config path

**Testing**
- Comprehensive test suite for all core components
- Test coverage for config, schema, collectors, and storage
- 23+ passing tests with pytest

### Design Patterns Used

- **Facade Pattern**: Collectors provide clean Mapping interface
- **Registry Pattern**: Collector registry for extensibility
- **Open-Closed Principle**: Config-driven, easily extensible without code changes
- **Lazy Evaluation**: Collectors cache results on first access
- **Dependency Injection**: Collectors accept configuration as constructor args

### Configuration Example

```yaml
schema_version: "1.0"

collectors:
  workflow_status:
    enabled: true
    lookback_runs: 10
  wily:
    enabled: true
    max_revisions: 5
    operators: [cyclomatic, maintainability]
  coverage:
    enabled: true
    source: pytest-cov
  umpyre_stats:
    enabled: true
    exclude_dirs: [tests, examples, scrap]

storage:
  branch: code-metrics
  formats: [json, csv]
  retention:
    strategy: all

visualization:
  generate_plots: true
  generate_readme: true
  plot_metrics: [maintainability, coverage, loc]

thresholds:
  enabled: false

aggregation:
  enabled: false
```

### Usage Example

```bash
# Install umpyre
pip install umpyre

# Collect metrics (uses .github/umpyre-config.yml if present)
python -m umpyre.cli collect

# Collect with custom config
python -m umpyre.cli collect --config my-config.yml

# Dry run (don't store)
python -m umpyre.cli collect --no-store
```

### In GitHub Actions

```yaml
- name: Track Code Metrics
  if: success()  # Only after successful publish
  uses: i2mint/umpyre/actions/track-metrics@master
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    config-path: .github/umpyre-config.yml
```

### Known Limitations

- `UmpyreCollector` may have compatibility issues with some directory structures (inherits from `python_code_stats.py`)
- `WilyCollector` requires wily installation and git history
- GitHub API rate limiting applies to `WorkflowStatusCollector` (5000 req/hour with auth)

### Pending (Future Phases)

**Phase 2**: Visualization & Aggregation
- Plot generation (matplotlib/plotly)
- README auto-generation with embedded charts
- Cross-repository aggregation
- Dashboard generation for organizations

**Phase 3**: Advanced Features
- Additional collectors (bandit for security, interrogate for docstrings)
- Threshold validation system with custom validators
- Data pruning and compression
- Schema migration utilities

### Technical Details

- Python 3.10+ required
- Dependencies: py2store, pandas, pyyaml, requests
- Test framework: pytest
- Schema version: 1.0
