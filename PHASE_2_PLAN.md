# Phase 2: Visualization & Aggregation

## Overview

Build visualization and cross-repository aggregation capabilities to make metrics actionable and provide organization-wide insights.

**Estimated Duration**: 10-13 hours  
**Dependencies**: Phase 1 complete ✅

---

## 2.1 Time-Series Plot Generation (3 hours)

### Goal
Generate visual charts showing metric trends over time.

### Features

**Core Plots**:
- Maintainability index trend
- Test coverage trend (line & branch)
- Lines of code growth
- Cyclomatic complexity over time
- Function/class count evolution

**Implementation**:
```python
# umpyre/visualization/plots.py

class PlotGenerator:
    """Generate time-series plots from metrics history."""
    
    def __init__(self, metrics_branch: str = "code-metrics"):
        self.branch = metrics_branch
    
    def generate_coverage_plot(self) -> Path:
        """Generate coverage trend plot."""
        # Parse history/*.json files
        # Extract coverage metrics over time
        # Plot with matplotlib/plotly
        # Save as PNG/SVG
        pass
    
    def generate_maintainability_plot(self) -> Path:
        """Generate maintainability trend plot."""
        pass
    
    def generate_all_plots(self) -> dict[str, Path]:
        """Generate all standard plots."""
        pass
```

**Technical Approach**:
1. Read all `history/*.json` files
2. Parse timestamps from filenames (`YYYY_MM_DD_HH_MM_SS__sha__version.json`)
3. Extract target metrics
4. Sort by timestamp
5. Generate matplotlib/plotly charts
6. Save to `plots/` directory in code-metrics branch

**Output Location**:
```
code-metrics branch:
├── plots/
│   ├── coverage_trend.png
│   ├── maintainability_trend.png
│   ├── loc_growth.png
│   └── complexity_trend.png
```

**Config Options**:
```yaml
visualization:
  enabled: true
  generate_plots: true
  plot_metrics:
    - coverage
    - maintainability
    - loc
    - complexity
  plot_format: png  # or svg
  lookback_days: 90  # Only plot last 90 days
```

---

## 2.2 README Auto-Generation (2 hours)

### Goal
Automatically generate `METRICS.md` in code-metrics branch with summary tables and embedded plots.

### Features

**Content Sections**:
1. **Latest Metrics Summary** (table)
2. **Trend Charts** (embedded images)
3. **Historical Comparison** (table: current vs 1 week ago vs 1 month ago)
4. **Badge Generation** (shields.io format for GitHub README)

**Example Output**:
```markdown
# Code Metrics Report

Generated: 2025-11-14 22:45:00 UTC  
Commit: 700e012  
Version: 0.1.0

## Latest Metrics

| Metric | Value | Change (7d) |
|--------|-------|-------------|
| Test Coverage | 85.2% | +2.1% ↑ |
| Maintainability | 72.5 | -1.2 ↓ |
| Lines of Code | 2,750 | +45 ↑ |
| Cyclomatic Complexity | 3.2 | 0.0 → |

## Trends

### Coverage Over Time
![Coverage Trend](plots/coverage_trend.png)

### Maintainability Index
![Maintainability](plots/maintainability_trend.png)

## Badges

![Coverage](https://img.shields.io/badge/coverage-85.2%25-brightgreen)
![Maintainability](https://img.shields.io/badge/maintainability-72.5-yellow)
```

**Implementation**:
```python
# umpyre/visualization/readme_generator.py

class ReadmeGenerator:
    """Generate METRICS.md from metrics history."""
    
    def generate_summary_table(self) -> str:
        """Create latest metrics table."""
        pass
    
    def generate_trend_section(self) -> str:
        """Embed plot images."""
        pass
    
    def generate_badges(self) -> str:
        """Create shields.io badges."""
        pass
    
    def generate_full_readme(self) -> str:
        """Generate complete METRICS.md."""
        pass
```

**Badge Format**:
```
https://img.shields.io/badge/coverage-85.2%25-brightgreen
https://img.shields.io/badge/maintainability-72.5-yellow
https://img.shields.io/badge/complexity-3.2-green
```

---

## 2.3 Cross-Repository Aggregation (4 hours)

### Goal
Aggregate metrics across multiple repositories to provide organization-wide insights.

### Features

**Aggregation Metrics**:
- Average coverage across all repos
- Total lines of code (organization-wide)
- Repos below threshold counts
- Trend analysis (improving vs declining repos)
- Top/bottom performers

**Implementation**:
```python
# umpyre/collectors/aggregation_collector.py

class AggregationCollector(MetricCollector):
    """Aggregate metrics across multiple repositories."""
    
    def __init__(
        self,
        org: str,
        repos: list[str],
        github_token: Optional[str] = None
    ):
        """
        Initialize aggregator.
        
        Args:
            org: GitHub organization name
            repos: List of repository names
            github_token: GitHub API token
        """
        self.org = org
        self.repos = repos
        self.token = github_token
    
    def collect(self) -> dict:
        """
        Aggregate metrics from multiple repos.
        
        Returns:
            Aggregated metrics dictionary
        """
        # For each repo:
        #   1. Clone code-metrics branch
        #   2. Read latest metrics.json
        #   3. Aggregate
        
        return {
            "total_repos": len(self.repos),
            "avg_coverage": 82.5,
            "total_loc": 125000,
            "repos_below_threshold": 3,
            "trending_up": 8,
            "trending_down": 2,
            "per_repo_summary": [...],
        }
```

**Storage**:
- Store aggregated metrics in special "metrics-dashboard" repository
- Or in `.github` repository with organization-wide metrics

**Config**:
```yaml
aggregation:
  enabled: true
  org: i2mint
  repos:
    - umpyre
    - py2store
    - creek
    - dol
    # ... or use "all" to auto-discover
  schedule: daily  # Run aggregation daily
```

---

## 2.4 Dashboard Generation (4 hours)

### Goal
Create interactive HTML dashboard with organization-wide metrics.

### Features

**Dashboard Sections**:
1. **Overview Cards**: Total repos, avg coverage, total LOC
2. **Interactive Charts**: Plotly.js for zoom/pan
3. **Repository Table**: Sortable, filterable list of all repos
4. **Trend Indicators**: Up/down arrows, color coding
5. **Drill-Down**: Click repo → see detailed metrics

**Tech Stack**:
- Static HTML/CSS/JS (no server needed)
- Plotly.js for interactive charts
- GitHub Pages hosting
- Data embedded as JSON

**Implementation**:
```python
# umpyre/visualization/dashboard.py

class DashboardGenerator:
    """Generate interactive HTML dashboard."""
    
    def generate_html(self, aggregated_metrics: dict) -> str:
        """
        Generate dashboard HTML.
        
        Args:
            aggregated_metrics: Output from AggregationCollector
            
        Returns:
            HTML string
        """
        # Use Jinja2 template
        # Embed metrics as JSON
        # Include Plotly.js CDN
        # Generate interactive charts
        pass
```

**Example Dashboard**:
```
https://i2mint.github.io/metrics-dashboard/

┌─────────────────────────────────────────┐
│  i2mint Metrics Dashboard               │
├─────────────────────────────────────────┤
│  📊 Total Repos: 25                     │
│  ✅ Avg Coverage: 82.5%                 │
│  📝 Total LOC: 125,000                  │
└─────────────────────────────────────────┘

[Interactive Chart: Coverage by Repo]
[Interactive Chart: LOC Distribution]

┌───────────┬──────────┬────────┬──────────┐
│ Repo      │ Coverage │ LOC    │ Status   │
├───────────┼──────────┼────────┼──────────┤
│ umpyre    │ 85%      │ 2,750  │ ✓ Good   │
│ py2store  │ 78%      │ 8,200  │ ⚠ Fair   │
│ creek     │ 92%      │ 1,500  │ ✓ Great  │
└───────────┴──────────┴────────┴──────────┘
```

---

## CLI Integration

Add new commands to `umpyre.cli`:

```bash
# Generate plots for current repo
python -m umpyre.cli visualize

# Generate plots + README
python -m umpyre.cli visualize --with-readme

# Aggregate metrics across org
python -m umpyre.cli aggregate --org i2mint

# Generate dashboard
python -m umpyre.cli dashboard --org i2mint --output-dir ./dashboard
```

---

## GitHub Action Integration

```yaml
# .github/workflows/metrics-visualization.yml

name: Generate Metrics Visualizations

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  visualize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: code-metrics
          
      - name: Generate Plots
        uses: i2mint/umpyre/actions/visualize@master
        with:
          generate-plots: true
          generate-readme: true
          
      - name: Commit Visualizations
        run: |
          git config user.name "umpyre-bot"
          git config user.email "umpyre@automated"
          git add plots/ METRICS.md
          git commit -m "Update visualizations [skip ci]"
          git push
```

---

## Testing Strategy

1. **Unit Tests**:
   - Test plot generation with mock data
   - Test README generation
   - Test aggregation logic

2. **Integration Tests**:
   - Test on real umpyre repository
   - Verify plots are created
   - Verify README is valid markdown

3. **Visual Tests**:
   - Manual inspection of generated plots
   - Check dashboard rendering

---

## Dependencies

**New Python Packages**:
- `matplotlib` or `plotly` (for plotting)
- `jinja2` (for templating)
- `pygithub` (for GitHub API in aggregation)

**Update pyproject.toml**:
```toml
[project.optional-dependencies]
visualization = [
    "matplotlib>=3.5.0",
    "plotly>=5.0.0",
    "jinja2>=3.0.0",
]
aggregation = [
    "pygithub>=2.0.0",
]
```

---

## Success Criteria

- [ ] Time-series plots generated for all key metrics
- [ ] METRICS.md auto-generated with tables and charts
- [ ] Cross-repo aggregation working for 5+ repos
- [ ] Interactive dashboard deployed to GitHub Pages
- [ ] CLI commands functional
- [ ] GitHub Action workflow working
- [ ] Documentation updated
- [ ] Tests passing

---

## Future Enhancements (Beyond Phase 2)

- Real-time dashboard updates (webhook-triggered)
- Slack/Discord notifications for threshold violations
- Comparison views (repo A vs repo B)
- Custom metric definitions
- Export to CSV/Excel for analysis
