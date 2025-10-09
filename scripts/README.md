# 📜 Scripts Directory

This directory contains utility scripts for the Docpipe project.

## 🔧 Documentation Compliance Scripts

### 📝 check_session_summary.py
Validates that session summaries exist and are recent.

```bash
python scripts/check_session_summary.py

# Check for summary within last 48 hours
python scripts/check_session_summary.py 48
```

**Checks:**
- Session summary exists within time threshold (default 24 hours)
- Required sections are present
- Proper naming convention followed

---

### 📋 check_task_completions.py
Ensures ALL completed tasks have completion summaries (NO EXCEPTIONS).

```bash
python scripts/check_task_completions.py
```

**Checks:**
- All tasks marked "✅ Completed" have summaries
- Summaries exist in `planning/completions/`
- Required sections present in summaries

**Philosophy:** "Knowledge is cheap, disc space is cheaper, lost context is expensive."

---

## 🔧 Testing & Coverage Scripts

### test_coverage_tool.py

**Purpose**: Comprehensive test coverage analysis tool that consolidates functionality from multiple legacy scripts.

**Features**:
- ✅ Verifies every source file has a corresponding test file
- 🔍 Identifies stale test files (tests without source files)
- 📊 Calculates test coverage percentage
- 🎯 Enforces 90% minimum coverage requirement (per CLAUDE.md)
- 📝 Multiple output formats (console, markdown, JSON)
- 🤖 CI/CD integration with proper exit codes
- 🗑️ Optional stale test cleanup

**Usage**:
```bash
# Basic analysis
python scripts/test_coverage_tool.py

# Custom directories
python scripts/test_coverage_tool.py --src src/myproject --test tests/unit

# Generate markdown report
python scripts/test_coverage_tool.py --format markdown --output coverage_report.md

# Delete stale tests (interactive confirmation)
python scripts/test_coverage_tool.py --delete

# Dry run to see what would be deleted
python scripts/test_coverage_tool.py --delete --dry-run

# CI/CD mode (exits with 1 if coverage < 90%)
python scripts/test_coverage_tool.py --ci

# Custom minimum coverage
python scripts/test_coverage_tool.py --ci --min-coverage 95
```

**Output Example**:
```
======================================================================
📊 TEST COVERAGE ANALYSIS REPORT
======================================================================
Generated: 2025-07-10T15:30:00
Source Directory: src
Test Directory: tests

📈 SUMMARY
--------------------------------------------------
Total Source Files: 42
Files with Tests: 38 ✅
Files Missing Tests: 4 ❌
Stale Test Files: 2 🗑️
Coverage: 90.5%

✅ Coverage meets 90% requirement!
```

### Legacy Scripts (Deprecated)

The following scripts have been consolidated into `test_coverage_tool.py`:
- `analyze_test_coverage.py` - Basic coverage analysis
- `check_test_coverage.py` - Coverage checking with CLI options
- `detailed_coverage_check.py` - Verbose coverage reporting
- `test_coverage_analysis.py` - Simple package-specific analysis

These scripts are retained for backwards compatibility but should not be used for new development.

## 🚀 Integration

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: test-coverage
      name: Check test coverage
      entry: python scripts/test_coverage_tool.py --ci
      language: system
      pass_filenames: false
      always_run: true
```

### GitHub Actions

Add to `.github/workflows/tests.yml`:
```yaml
- name: Check test coverage
  run: |
    python scripts/test_coverage_tool.py --ci --format markdown --output coverage.md
    
- name: Upload coverage report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: coverage-report
    path: coverage.md
```

### Makefile Target

Add to `Makefile`:
```makefile
.PHONY: coverage
coverage:
	@python scripts/test_coverage_tool.py

.PHONY: coverage-report
coverage-report:
	@python scripts/test_coverage_tool.py --format markdown --output docs/coverage_report.md

.PHONY: clean-stale-tests
clean-stale-tests:
	@python scripts/test_coverage_tool.py --delete
```

## 📋 Requirements

- Python 3.8+
- No external dependencies (uses standard library only)
- Follows CLAUDE.md guidelines:
  - Test files must be named `test_<module_name>.py`
  - Test files must mirror source directory structure
  - Excludes `__init__.py` and `__version__.py` files
  - Minimum 90% coverage requirement

## 🔒 Security Notes

- The tool only reads files and optionally deletes test files
- No external network calls or data transmission
- Follows principle of least privilege
- Deletion requires explicit confirmation (unless in CI mode)