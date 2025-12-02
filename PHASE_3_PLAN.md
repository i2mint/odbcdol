# Phase 3: Advanced Features & Production Hardening

## Overview

Add production-ready features including threshold validation, additional collectors, data management, and schema migrations.

**Estimated Duration**: 15-18 hours  
**Dependencies**: Phase 2 complete

---

## 3.1 Threshold Validation System (3 hours)

### Goal
Enforce quality standards by validating metrics against configurable thresholds.

### Features

**Threshold Types**:
- Minimum thresholds (e.g., coverage >= 80%)
- Maximum thresholds (e.g., complexity <= 10)
- Delta thresholds (e.g., coverage drop <= 5%)
- Custom validators (Python functions)

**Actions**:
- `warn`: Log warning, continue (exit code 0)
- `fail`: Exit with code 1, fail CI
- `notify`: Send notification (Slack/email)
- `comment`: Comment on PR

**Implementation**:
```python
# umpyre/validation/thresholds.py

@dataclass
class Threshold:
    """Threshold definition."""
    metric_path: str  # e.g., "metrics.coverage.line_coverage"
    operator: str     # ">=", "<=", "==", "!=", ">", "<"
    value: float
    action: str       # "warn", "fail", "notify", "comment"
    message: Optional[str] = None

class ThresholdValidator:
    """Validate metrics against thresholds."""
    
    def __init__(self, thresholds: list[Threshold]):
        self.thresholds = thresholds
    
    def validate(self, metrics: dict) -> list[ThresholdViolation]:
        """
        Validate metrics against all thresholds.
        
        Returns:
            List of violations
        """
        violations = []
        
        for threshold in self.thresholds:
            value = self._extract_metric(metrics, threshold.metric_path)
            if not self._check_threshold(value, threshold):
                violations.append(
                    ThresholdViolation(
                        threshold=threshold,
                        actual_value=value,
                        expected_value=threshold.value,
                    )
                )
        
        return violations
    
    def _check_threshold(self, value: float, threshold: Threshold) -> bool:
        """Check if value passes threshold."""
        ops = {
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
        }
        return ops[threshold.operator](value, threshold.value)
```

**Config**:
```yaml
thresholds:
  enabled: true
  rules:
    # Minimum coverage
    - metric: metrics.coverage.line_coverage
      operator: ">="
      value: 80.0
      action: fail
      message: "Test coverage must be at least 80%"
    
    # Maximum complexity
    - metric: metrics.wily.cyclomatic_avg
      operator: "<="
      value: 10.0
      action: warn
      message: "Average complexity should be below 10"
    
    # Delta threshold (vs previous commit)
    - metric: metrics.coverage.line_coverage
      operator: ">="
      value: -5.0  # Max 5% drop
      delta: true
      action: fail
      message: "Coverage dropped by more than 5%"
    
    # Custom validator
    - metric: custom
      validator: "umpyre.validators.check_docstring_ratio"
      action: warn
```

**Custom Validators**:
```python
# umpyre/validators.py

def check_docstring_ratio(metrics: dict) -> tuple[bool, str]:
    """
    Custom validator: check if docstring ratio is acceptable.
    
    Returns:
        (passed, message)
    """
    docs = metrics["metrics"]["umpyre_stats"]["docs_lines"]
    total = metrics["metrics"]["umpyre_stats"]["total_lines"]
    ratio = docs / total if total > 0 else 0
    
    if ratio < 0.1:
        return False, f"Docstring ratio {ratio:.1%} is below 10%"
    return True, "Docstring ratio acceptable"
```

**CLI Integration**:
```bash
# Validate metrics against thresholds
python -m umpyre.cli validate

# Validate and collect
python -m umpyre.cli collect --validate

# Show violations only
python -m umpyre.cli validate --violations-only
```

---

## 3.2 Additional Collectors (8 hours)

### 3.2.1 BanditCollector (2 hours)

**Purpose**: Security vulnerability scanning

```python
# umpyre/collectors/bandit_collector.py

class BanditCollector(MetricCollector):
    """Collect security metrics using Bandit."""
    
    def collect(self) -> dict:
        """
        Run bandit security scan.
        
        Returns:
            {
                "total_issues": 12,
                "high_severity": 2,
                "medium_severity": 5,
                "low_severity": 5,
                "confidence_high": 3,
                "confidence_medium": 6,
                "confidence_low": 3,
                "files_scanned": 25,
                "top_issues": [
                    {"test_id": "B101", "count": 4, "severity": "medium"},
                    ...
                ]
            }
        """
        # Run: bandit -r . -f json
        # Parse JSON output
        # Aggregate by severity/confidence
        pass
```

**Config**:
```yaml
collectors:
  bandit:
    enabled: true
    config_file: .bandit  # Optional
    exclude_dirs: [tests, examples]
    severity_threshold: medium  # low, medium, high
```

---

### 3.2.2 InterrogateCollector (2 hours)

**Purpose**: Docstring coverage analysis

```python
# umpyre/collectors/interrogate_collector.py

class InterrogateCollector(MetricCollector):
    """Collect docstring coverage using interrogate."""
    
    def collect(self) -> dict:
        """
        Run interrogate to check docstring coverage.
        
        Returns:
            {
                "coverage": 78.5,
                "functions_with_docs": 45,
                "functions_without_docs": 12,
                "classes_with_docs": 8,
                "classes_without_docs": 2,
                "files_analyzed": 15,
            }
        """
        # Run: interrogate . -vv --generate-badge . --quiet
        # Parse output
        pass
```

---

### 3.2.3 MyPyCollector (2 hours)

**Purpose**: Type hint coverage and type checking

```python
# umpyre/collectors/mypy_collector.py

class MyPyCollector(MetricCollector):
    """Collect type checking results using mypy."""
    
    def collect(self) -> dict:
        """
        Run mypy type checker.
        
        Returns:
            {
                "total_errors": 15,
                "error_types": {
                    "type-error": 8,
                    "attr-defined": 4,
                    "arg-type": 3,
                },
                "files_checked": 25,
                "functions_typed": 45,
                "functions_untyped": 12,
                "type_coverage": 78.9,
            }
        """
        # Run: mypy . --show-error-codes --no-error-summary
        # Parse output
        # Calculate type coverage
        pass
```

---

### 3.2.4 PylintCollector (2 hours)

**Purpose**: Code quality scoring

```python
# umpyre/collectors/pylint_collector.py

class PylintCollector(MetricCollector):
    """Collect code quality score using Pylint."""
    
    def collect(self) -> dict:
        """
        Run pylint code analysis.
        
        Returns:
            {
                "score": 8.5,  # Out of 10
                "total_statements": 1250,
                "convention": 12,
                "refactor": 5,
                "warning": 8,
                "error": 2,
                "files_analyzed": 15,
            }
        """
        # Run: pylint --output-format=json .
        # Parse JSON
        # Extract score and violations
        pass
```

---

## 3.3 Data Management (3 hours)

### Goal
Manage metrics history efficiently (pruning, compression, rotation).

### 3.3.1 Pruning Strategy

**Keep**:
- All metrics from last 30 days
- One metric per week for 30-90 days ago
- One metric per month for 90+ days ago

```python
# umpyre/storage/pruning.py

class MetricsPruner:
    """Prune old metrics to save space."""
    
    def prune(self, branch: str = "code-metrics"):
        """
        Prune metrics history based on retention policy.
        
        Strategy:
        - Keep all metrics < 30 days old
        - Keep weekly snapshots for 30-90 days
        - Keep monthly snapshots for 90+ days
        """
        # Parse all history/*.json filenames
        # Extract timestamps
        # Apply retention policy
        # Delete old files
        pass
```

**Config**:
```yaml
storage:
  retention:
    strategy: tiered  # all, tiered, custom
    keep_days: 30
    weekly_after_days: 30
    monthly_after_days: 90
    prune_on_collect: false  # Prune automatically after each collection
```

---

### 3.3.2 Compression

**Goal**: gzip old metrics to save space

```python
# umpyre/storage/compression.py

class MetricsCompressor:
    """Compress old metrics files."""
    
    def compress_old_files(
        self,
        branch: str = "code-metrics",
        older_than_days: int = 90
    ):
        """
        Compress metrics older than N days.
        
        Changes:
        - 2024_01_15_10_30_00__abc1234__0.1.0.json
        → 2024_01_15_10_30_00__abc1234__0.1.0.json.gz
        """
        # Find files older than N days
        # gzip compress
        # Delete original
        pass
```

---

### 3.3.3 Rotation

**Goal**: Auto-delete very old metrics

```python
# umpyre/storage/rotation.py

class MetricsRotator:
    """Rotate out very old metrics."""
    
    def rotate(
        self,
        branch: str = "code-metrics",
        max_age_days: int = 365
    ):
        """Delete metrics older than max_age_days."""
        # Parse timestamps
        # Delete files older than threshold
        pass
```

**Config**:
```yaml
storage:
  rotation:
    enabled: true
    max_age_days: 365
    warn_before_delete: true
```

---

## 3.4 Schema Migrations (4 hours)

### Goal
Handle schema version changes gracefully with automatic migrations.

### Implementation

```python
# umpyre/schema.py (enhanced)

class MetricSchema:
    """Versioned schema with migration support."""
    
    version: str = "1.1"  # Bump version
    
    @classmethod
    def migrate(cls, data: dict, from_version: str) -> dict:
        """
        Migrate data from old schema to current.
        
        Migration chain:
        1.0 → 1.1 → 1.2 → ...
        """
        if from_version == cls.current_version():
            return data
        
        # Migration registry
        migrations = {
            "1.0": cls._migrate_1_0_to_1_1,
            "1.1": cls._migrate_1_1_to_1_2,
        }
        
        # Apply migrations in sequence
        current_version = from_version
        current_data = data
        
        while current_version != cls.current_version():
            if current_version not in migrations:
                raise ValueError(f"No migration path from {current_version}")
            
            migrator = migrations[current_version]
            current_data = migrator(current_data)
            current_version = cls._next_version(current_version)
        
        return current_data
    
    @classmethod
    def _migrate_1_0_to_1_1(cls, data: dict) -> dict:
        """
        Migrate from schema 1.0 to 1.1.
        
        Changes in 1.1:
        - Added pypi_version field
        - Added collection_duration_seconds
        """
        # Add new fields with defaults
        if "metrics" in data:
            for collector_name, metrics in data["metrics"].items():
                if "pypi_version" not in metrics:
                    metrics["pypi_version"] = None
        
        data["schema_version"] = "1.1"
        return data
    
    @classmethod
    def _migrate_1_1_to_1_2(cls, data: dict) -> dict:
        """Future migration example."""
        # Apply changes for 1.2
        data["schema_version"] = "1.2"
        return data
```

**Auto-Migration on Load**:
```python
# umpyre/storage/formats.py (enhanced)

def load_metrics(filepath: Path) -> dict:
    """
    Load metrics with automatic schema migration.
    
    If old schema detected, automatically migrates to current.
    """
    with open(filepath) as f:
        data = json.load(f)
    
    schema_version = data.get("schema_version", "1.0")
    current_version = MetricSchema.current_version()
    
    if schema_version != current_version:
        print(f"Migrating from schema {schema_version} to {current_version}")
        data = MetricSchema.migrate(data, from_version=schema_version)
    
    return data
```

**Migration Tool**:
```bash
# Migrate all metrics in branch
python -m umpyre.cli migrate --branch code-metrics

# Dry run (show what would change)
python -m umpyre.cli migrate --dry-run
```

---

## CLI Integration

New commands for Phase 3:

```bash
# Validate against thresholds
python -m umpyre.cli validate

# Prune old metrics
python -m umpyre.cli prune --older-than 90

# Compress old metrics
python -m umpyre.cli compress

# Migrate schema
python -m umpyre.cli migrate

# Run all collectors (including new ones)
python -m umpyre.cli collect --all
```

---

## Testing Strategy

1. **Threshold Tests**:
   - Test all operators (>=, <=, ==, !=, >, <)
   - Test delta thresholds
   - Test custom validators
   - Test actions (warn, fail, notify)

2. **Collector Tests**:
   - Test each new collector with sample repos
   - Test error handling
   - Test config options

3. **Data Management Tests**:
   - Test pruning logic
   - Test compression/decompression
   - Test rotation

4. **Migration Tests**:
   - Create sample data in old schema
   - Verify migration to new schema
   - Test migration chains (1.0 → 1.1 → 1.2)

---

## Dependencies

**New Python Packages**:
```toml
[project.optional-dependencies]
security = [
    "bandit>=1.7.0",
]
quality = [
    "interrogate>=1.5.0",
    "mypy>=1.0.0",
    "pylint>=2.15.0",
]
```

---

## Success Criteria

- [ ] Threshold validation working with all operators
- [ ] 4 new collectors implemented (bandit, interrogate, mypy, pylint)
- [ ] Pruning/compression/rotation working
- [ ] Schema migration system working
- [ ] CLI commands functional
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Phase 3 complete and production-ready

---

## Future Enhancements (Beyond Phase 3)

- Machine learning predictions (predict when coverage will drop)
- Anomaly detection (unusual metric changes)
- Automated PR comments with metrics
- Slack/Discord bot integration
- Web API for querying metrics
- Export to data warehouses (BigQuery, Snowflake)
