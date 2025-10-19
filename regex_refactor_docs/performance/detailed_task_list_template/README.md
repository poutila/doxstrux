# DETAILED_TASK_LIST Template - Usage Guide

**Version**: 2.0
**Date**: 2025-10-18
**Status**: Production-Ready (Multi-Format + Automation)

---

## Quick Start

```bash
# 1. Choose your format
ls -la
# DETAILED_TASK_LIST_template.md    # Human-readable Markdown
# DETAILED_TASK_LIST_template.yaml  # Machine-readable YAML
# DETAILED_TASK_LIST_template.json  # Machine-readable JSON

# 2. List all placeholders
python tools/render_template.py -t DETAILED_TASK_LIST_template.md --list-placeholders

# 3. Create your values file
cat > config/my_project_values.yml <<EOF
PROJECT_NAME: "Database Migration"
PROJECT_FULL_NAME: "PostgreSQL 12 → 15 Migration"
DATE: "2025-10-18"
VERSION: "1.0"
EOF

# 4. Render the template
python tools/render_template.py \
    -t DETAILED_TASK_LIST_template.md \
    -r config/my_project_values.yml \
    -o MY_PROJECT_TASK_LIST.md

# 5. Use --strict in CI to enforce all placeholders filled
python tools/render_template.py -t DETAILED_TASK_LIST_template.md -r config/values.yml --strict
```

---

## Overview

This template package provides a **comprehensive, automation-ready** structure for multi-phase project task lists extracted from the Regex-to-Token refactoring project. It includes built-in governance, testing, completion tracking, and **three formats** (Markdown, YAML, JSON) for both human and machine use.

### What's Included

| File | Format | Purpose |
|------|--------|---------|
| `DETAILED_TASK_LIST_template.md` | Markdown + YAML front matter | Human-readable with {{PLACEHOLDER}} tokens |
| `DETAILED_TASK_LIST_template.yaml` | YAML | Machine-readable for automation |
| `DETAILED_TASK_LIST_template.json` | JSON | Machine-readable for CI/CD pipelines |
| `tools/render_template.py` | Python script | Automated placeholder replacement |
| `README.md` | Documentation | This file |

### Why Multiple Formats?

- **Markdown**: Best for human editing, reading, and version control
- **YAML**: Best for automation tools, config management, CI/CD
- **JSON**: Best for programmatic access, APIs, strict validation

All three formats contain **identical structure and placeholders** - choose the format that fits your workflow.

## Template Features

### 1. **Phase Unlock Mechanism**
- JSON schema for phase completion artifacts
- Validation scripts for enforcing sequential phase progression
- Prevents starting Phase N+1 until Phase N is complete

### 2. **Global Utilities**
- Subprocess timeout helper (prevents CI hangs)
- Atomic file write utility (prevents partial writes)
- Schema version validator
- Evidence block creation with portalocker locking

### 3. **Testing Infrastructure**
- Fast iteration loop (§TEST_FAST)
- Full validation (§TEST_FULL)
- Performance testing (§TEST_PERF)
- CI gate sequence (§CI_ALL)

### 4. **Rollback Procedures**
- Single test failure (targeted revert)
- Multiple test failures (full revert)
- Performance regression handling
- CI gate failure diagnosis
- Emergency recovery from lost changes

### 5. **Phase Completion Template**
- Standardized completion checklist
- Automated artifact generation script
- Completion report markdown template
- Evidence block creation pattern

## Placeholder Reference

### Project Metadata
| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{PROJECT_NAME}}` | Short project name | Regex to Token Refactoring |
| `{{PROJECT_FULL_NAME}}` | Full project name | Docpipe Markdown Parser Zero-Regex Refactoring |
| `{{DATE}}` | Creation date | 2025-10-11 |
| `{{VERSION}}` | Document version | 1.0 |
| `{{STATUS}}` | Current status | Phase 0 ready to start |
| `{{PROJECT_GOAL}}` | Primary objective | Eliminate all regex usage from parser |

### Time & Metrics
| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{TOTAL_TIME_ESTIMATE}}` | Total estimated time | 60-82 hours |
| `{{NUM_PHASES}}` | Number of phases | 7 |
| `{{FINAL_PHASE_NUM}}` | Last phase number | 6 |
| `{{FAST_TEST_TIME}}` | Fast test duration | 100ms |
| `{{FULL_TEST_TIME}}` | Full test duration | 500ms |

### Test Configuration
| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{FAST_TEST_COMMAND}}` | Quick test command | ./tools/run_tests_fast.sh 01_edge_cases |
| `{{FULL_TEST_COMMAND}}` | Full test command | python3 tools/baseline_test_runner.py |
| `{{PERF_TEST_COMMAND}}` | Performance test | python3 tools/ci/ci_gate_performance.py |
| `{{CORPUS_DIR}}` | Test corpus directory | tools/test_mds |
| `{{CORPUS_PATTERN}}` | File pattern | *.md |
| `{{ORIGINAL_CORPUS_COUNT}}` | Initial file count | 542 |

### CI/CD
| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{NUM_GATES}}` | Number of CI gates | 5 |
| `{{CI_GATE_1}}` | First CI gate command | python3 tools/ci/ci_gate_no_hybrids.py |
| `{{CI_GATE_2}}` | Second CI gate | python3 tools/ci/ci_gate_canonical_pairs.py |
| `{{GATE_1_NAME}}` | Gate 1 description | No Hybrids |
| `{{GATE_1_FIX}}` | Gate 1 fix hint | Remove USE_TOKEN_* patterns |

### Utilities & Scripts
| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{TIMEOUT_HELPER_SCRIPT}}` | Timeout helper filename | subprocess_timeout |
| `{{EVIDENCE_SCRIPT}}` | Evidence creation script | create_evidence_block |
| `{{SNIPPET_MAX_CHARS}}` | Max snippet length | 1000 |
| `{{BASE64_MIN_LENGTH}}` | Min base64 length to redact | 40 |
| `{{TOKEN_MIN_LENGTH}}` | Min token length to redact | 20 |
| `{{LOCK_TIMEOUT}}` | File lock timeout (seconds) | 10 |

### Metrics & Performance
| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{METRIC_NAME}}` | Primary metric name | REGEX |
| `{{METRIC_1}}` | Metric field name | regex_count |
| `{{PERF_THRESHOLD_SPEC}}` | Performance threshold | Δmedian ≤5%, Δp95 ≤10% |
| `{{PERF_POLICY_DOC}}` | Policy document | POLICY_GATES.md |
| `{{PERF_SECTION}}` | Policy section number | 5 |

### Phase-Specific
| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{PHASE_NUM}}` | Current phase number | 1 |
| `{{PREV_PHASE}}` | Previous phase number | 0 |
| `{{NEXT_PHASE}}` | Next phase number | 2 |
| `{{PHASE_NAME}}` | Phase descriptive name | Fences & Indented Code |
| `{{PHASE_GOAL}}` | Phase objective | Replace regex fence detection with tokens |
| `{{PHASE_TIME}}` | Phase time estimate | 4-6 hours |

### Evidence & Documentation
| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{EVIDENCE_ID}}` | Evidence block ID | phase1-fence-token-impl |
| `{{FILE_PATH}}` | Source file path | src/docpipe/markdown_parser_core.py |
| `{{LINE_RANGE}}` | Line range | 450-475 |
| `{{DESCRIPTION}}` | Change description | Added token-based fence detection |
| `{{ISSUES_FILE}}` | Issues tracking file | steps_taken/ISSUES.md |
| `{{PROGRESS_FILE}}` | Progress tracking file | PROGRESS.md |

---

## Automation with render_template.py

The `tools/render_template.py` script automates placeholder replacement for all three template formats.

### Features

- **Multi-format support**: Works with Markdown, YAML, JSON, or any text file
- **Value sources**: Reads from YAML/JSON config files + environment variables
- **Strict mode**: Fails CI if any placeholders remain unresolved
- **Placeholder discovery**: List all placeholders in a template
- **No dependencies**: Pure Python (PyYAML optional for YAML configs)

### Basic Usage

```bash
# Render Markdown template
python tools/render_template.py \
    -t DETAILED_TASK_LIST_template.md \
    -r config/my_values.yml \
    -o MY_TASK_LIST.md

# Render YAML template
python tools/render_template.py \
    -t DETAILED_TASK_LIST_template.yaml \
    -r config/my_values.json \
    -o my_task_list.yaml

# List all placeholders (useful for creating config file)
python tools/render_template.py \
    -t DETAILED_TASK_LIST_template.md \
    --list-placeholders > placeholders.txt
```

### Environment Variable Override

Environment variables take precedence over config file values:

```bash
# Use environment variables
export PROJECT_NAME="Database Migration"
export VERSION="2.0"

python tools/render_template.py \
    -t DETAILED_TASK_LIST_template.md \
    -r config/base_values.yml \
    -o output.md

# PROJECT_NAME and VERSION from env override config file
```

### Strict Mode (CI/CD)

Use `--strict` to fail if any placeholders remain unresolved:

```bash
# In CI pipeline
python tools/render_template.py \
    -t DETAILED_TASK_LIST_template.yaml \
    -r config/phase1_values.yml \
    --strict \
    -o phase1_task_list.yaml || exit 1

# Exits with non-zero code if placeholders like {{MISSING_VALUE}} remain
```

### Nested Value Lookup

Support for dot notation in placeholders:

```yaml
# config/values.yml
metadata:
  project:
    name: "Database Migration"
    version: "2.0"
```

```markdown
# Template
Project: {{metadata.project.name}} v{{metadata.project.version}}
```

```bash
python tools/render_template.py -t template.md -r config/values.yml
# Output: Project: Database Migration v2.0
```

### CI/CD Integration Example

```yaml
# .github/workflows/render_task_list.yml
name: Render Task List

on:
  push:
    paths:
      - 'config/project_values.yml'

jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install PyYAML
        run: pip install pyyaml

      - name: Render task list
        env:
          DATE: ${{ github.event.head_commit.timestamp }}
          GIT_COMMIT: ${{ github.sha }}
        run: |
          python tools/render_template.py \
            -t DETAILED_TASK_LIST_template.md \
            -r config/project_values.yml \
            --strict \
            -o TASK_LIST.md

      - name: Commit rendered file
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add TASK_LIST.md
          git commit -m "Auto-render task list from template"
          git push
```

---

## How to Use This Template

### Step 1: Search and Replace

Use your editor's search-and-replace feature to fill in placeholders:

```bash
# Example using sed (bulk replacement)
sed -i 's/{{PROJECT_NAME}}/MyProject/g' task_list.md
sed -i 's/{{TOTAL_TIME_ESTIMATE}}/40-50 hours/g' task_list.md

# Or use interactive replacement in your editor
# VSCode: Ctrl+H (Find and Replace)
# Vim: :%s/{{PLACEHOLDER}}/value/g
```

### Step 2: Customize Phases

1. **Define your phases** (Phase 0 through N)
2. **Break down each phase** into tasks (Task 0.0, 0.1, 1.0, 1.1, etc.)
3. **Specify acceptance criteria** for each task
4. **Estimate time** for each task

### Step 3: Adapt Utilities

Customize the utility scripts for your project:

- **Timeout helper**: Adjust timeout values for your CI
- **Evidence script**: Modify redaction patterns for your codebase
- **Atomic write**: Keep as-is (generic utility)
- **Phase validator**: Add project-specific validation rules

### Step 4: Configure CI Gates

Define your CI gate sequence:

1. **G1**: First validation (e.g., no hybrid code)
2. **G2**: Second validation (e.g., canonical pairs)
3. **G3**: Third validation (e.g., parity tests)
4. **G4**: Performance validation
5. **G5**: Evidence integrity

### Step 5: Add Project-Specific Sections

Extend the template with:

- **Domain-specific utilities**
- **Custom rollback procedures**
- **Project-specific schemas**
- **Additional appendices**

## Example: Quick Start

Here's a minimal example to get started:

```markdown
# Detailed Task List - Database Migration

**Project**: PostgreSQL 12 → 15 Migration
**Date**: 2025-10-18
**Version**: 1.0
**Status**: Phase 0 ready to start

## Overview

**Goal**: Migrate production database from PostgreSQL 12 to 15 with zero downtime

**Success Criteria**:
- All tables migrated with schema parity
- Performance maintained (Δmedian ≤5%)
- Zero data loss (verified via checksums)

**Total Estimated Time**: 20-30 hours

**Phases**: 4 phases (Phase 0 through Phase 3)

---

## Phase 0: Pre-Migration Setup

**Goal**: Establish migration infrastructure
**Time**: 4-6 hours
**Status**: ⏳ Not started

### Task 0.0: Schema Snapshot

**Time**: 1 hour
**Files**: `tools/snapshot_schema.py`
**Test**: Schema validation

**Steps**:
- [ ] Create schema snapshot tool
- [ ] Generate baseline schema from PG12
- [ ] Validate snapshot integrity
- [ ] Store in `baselines/schema_pg12.sql`

**Acceptance Criteria**:
- [ ] Tool runs in <30 seconds
- [ ] Schema file < 10MB
- [ ] All 150 tables captured

**Status**: ⏳ Not started
```

## Advanced Features

### Dynamic Corpus Counting

The template includes cross-platform corpus counting:

```python
from pathlib import Path

def get_corpus_count() -> int:
    """Get current corpus count (dynamic, cross-platform)."""
    return len(list(Path("tools/test_mds").rglob("*.md")))
```

**Why this matters**:
- Works on Windows, Linux, macOS
- Handles spaces in filenames
- No shell command dependencies

### Evidence Block Redaction

Built-in secret redaction before storage:

```python
def _redact_secrets(snippet: str) -> str:
    """Remove probable secrets before truncation."""
    import re

    # Remove long base64 strings
    snippet = re.sub(r'[A-Za-z0-9+/]{40,}={0,2}', '<REDACTED_BASE64>', snippet)

    # Remove token/key patterns
    snippet = re.sub(
        r'\b(token|key|secret|password)\s*[=:]\s*["\']?[\w\-_+/]{20,}["\']?',
        r'\1=<REDACTED>',
        snippet,
        flags=re.IGNORECASE
    )

    return snippet
```

### Atomic File Writes

Prevents partial writes and race conditions:

```python
from tools.atomic_write import atomic_write_text
from pathlib import Path
import json

# Phase unlock artifacts
atomic_write_text(
    Path(".phase-1.complete.json"),
    json.dumps(artifact, indent=2)
)
```

## Best Practices

### 1. **Always Work Sequentially**
- Complete Phase N before starting Phase N+1
- Use phase unlock artifacts to enforce this

### 2. **Test Continuously**
- Run §TEST_FAST after every small change
- Run §TEST_FULL before commits
- Run §CI_ALL before phase completion

### 3. **Git Checkpoints**
- Commit before and after each task
- Tag after each phase completion
- Use descriptive commit messages

### 4. **Document Issues**
- Track problems in {{ISSUES_FILE}}
- Include reproduction steps
- Note resolution approach

### 5. **Track Time**
- Record estimated vs. actual time
- Identify tasks that took longer than expected
- Adjust future estimates accordingly

## Rollback Strategy

The template includes 6 rollback procedures:

1. **A.1**: Single test failure → Targeted revert
2. **A.2**: Multiple failures → Full revert
3. **A.3**: Performance regression → Profile & decide
4. **A.4**: CI gate failure → Diagnose & fix
5. **A.5**: Custom failure type (adapt to your project)
6. **A.6**: Emergency recovery from lost changes

**Rule of thumb**: If you can't fix in 15-30 minutes, rollback and rethink.

## Phase Completion Checklist

Before marking any phase complete, verify:

- [ ] All tests pass (§CORPUS_COUNT/§CORPUS_COUNT)
- [ ] Performance within budget ({{PERF_THRESHOLD}})
- [ ] All CI gates pass (G1-G{{NUM_GATES}})
- [ ] Metrics improved or maintained
- [ ] Phase unlock artifact created and valid
- [ ] Completion report written
- [ ] Evidence blocks created
- [ ] Git checkpoint created
- [ ] Git tag created (`phase-N-complete`)

## Customization Examples

### Example 1: Adding a Custom CI Gate

```python
# tools/ci/ci_gate_security_scan.py
"""G6: Security vulnerability scan."""

import subprocess
import sys

def run_security_scan():
    """Run security scan with bandit."""
    result = subprocess.run(
        ["bandit", "-r", "src/", "-f", "json", "-o", "security_report.json"],
        timeout=300
    )

    if result.returncode != 0:
        print("❌ G6 FAIL: Security vulnerabilities detected")
        sys.exit(1)

    print("✅ G6 PASS: No security issues")
    sys.exit(0)

if __name__ == "__main__":
    run_security_scan()
```

### Example 2: Custom Rollback Procedure

```markdown
### A.7: Database Migration Rollback

bash
# 1. Stop application servers
kubectl scale deployment/app --replicas=0

# 2. Restore database snapshot
pg_restore --clean --if-exists -d production backups/pre_migration_snapshot.dump

# 3. Verify data integrity
python3 tools/verify_checksums.py

# 4. Restart application on old version
kubectl set image deployment/app app=app:v1.2.3
kubectl scale deployment/app --replicas=3

# 5. Monitor for 10 minutes
watch -n 10 'curl -s http://healthcheck/status'
```

## FAQ

### Q: Can I skip Phase 0?

**A**: No. Phase 0 establishes critical infrastructure (testing, CI gates, utilities). Skipping it will cause issues in later phases.

### Q: What if my project doesn't need evidence blocks?

**A**: Remove the evidence utility script and skip evidence creation in phase completion. Update the acceptance criteria accordingly.

### Q: Can I run phases in parallel?

**A**: No. The phase unlock mechanism enforces sequential execution. This prevents dependency issues and ensures each phase is stable before proceeding.

### Q: What if a phase takes longer than estimated?

**A**: Update the time tracking table with actual time. Use this data to improve future estimates. If variance is >50%, document why in the completion report.

### Q: How do I handle external dependencies (APIs, databases)?

**A**: Add a "Dependencies" section to each phase. Document required access, credentials (stored securely), and fallback plans if dependencies are unavailable.

## Support

For questions or issues with this template:

1. Review the original `DETAILED_TASK_LIST.md` in the regex refactoring project
2. Check the `REGEX_REFACTOR_EXECUTION_GUIDE.md` for context
3. Consult the `POLICY_GATES.md` for CI gate specifications

---

**Template Created**: 2025-10-18
**Based On**: Regex-to-Token Refactoring Project (Phase 0-7)
**Maintained By**: {{YOUR_TEAM}}
**Version**: 1.0
