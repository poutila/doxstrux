# Aggregator Agent Template

**Purpose**: Standard pattern for agents that aggregate multiple simple agents into comprehensive dashboards.

**Version**: 1.0.0
**Date**: 2025-12-23
**Applies To**: 2 of 23 agents

---

## 📋 Overview

**Aggregator Agents** are dashboard-generating agents that:
- Call 5-10 simple query agents in sequence
- Aggregate results into comprehensive compliance reports
- Compute overall scores and pass/fail status
- Generate executive summaries with top violations
- Verify TOCTOU protection across all sub-agent calls

**Philosophy**: Aggregators provide "one command" comprehensive analysis for pre-commit hooks, CI/CD, and release gates.

---

## 🏗️ Standard Implementation Pattern

### Structure (4 Phases)

1. **Phase 1: Prerequisites** - Verify FACTS, capture baseline
2. **Phase 2: Data Collection** - Call all sub-agents with TOCTOU verification
3. **Phase 3: Aggregation** - Combine results, compute summary metrics
4. **Phase 4: Scoring** - Calculate compliance scores, determine pass/fail

### Bash Script Template (Lines 1-150+)

```bash
#!/bin/bash
set -Eeuo pipefail

# =============================================================================
# <AGENT-NAME>
# Purpose: <One-line description>
# Template: AGGREGATOR_AGENT.md
# =============================================================================

# Error trap (MANDATORY)
trap 'echo "⛔ Error in $(basename "$0"): line $LINENO" >&2; exit 1' ERR

# ============================================================================
# PHASE 1: PREREQUISITES
# ============================================================================

# Verify FACTS.parquet exists
FACTS="${FACTS_FILE:-src/golden_validator_hybrid/FACTS.parquet}"
[[ -f "$FACTS" ]] || {
    echo "⛔ FACTS.parquet not found: $FACTS" >&2
    echo "   Run: uv run fact-file-query-tool generate" >&2
    exit 1
}

# Capture FACTS baseline for TOCTOU protection
BASELINE_FACTS=$(basename "$(readlink -f "$FACTS")")

# ============================================================================
# PHASE 2: DATA COLLECTION (Call All Sub-Agents)
# ============================================================================

echo "📊 Collecting data from sub-agents..." >&2

# Sub-agent 1: Complexity
COMPLEXITY=$(uv run fact-file-query-tool complexity --format json 2>&1)
COMPLEXITY_FACTS=$(echo "$COMPLEXITY" | jq -r '.metadata.facts_file')
[[ "$BASELINE_FACTS" == "$COMPLEXITY_FACTS" ]] || {
    echo "⚠️ STALE: Complexity used $COMPLEXITY_FACTS" >&2
    exit 1
}

# Sub-agent 2: Documentation
DOCUMENTATION=$(uv run fact-file-query-tool doc-quality --format json 2>&1)
DOC_FACTS=$(echo "$DOCUMENTATION" | jq -r '.metadata.facts_file')
[[ "$BASELINE_FACTS" == "$DOC_FACTS" ]] || {
    echo "⚠️ STALE: Documentation used $DOC_FACTS" >&2
    exit 1
}

# Sub-agent 3: Error Handling
ERROR_HANDLING=$(uv run fact-file-query-tool error-patterns --format json 2>&1)
ERROR_FACTS=$(echo "$ERROR_HANDLING" | jq -r '.metadata.facts_file')
[[ "$BASELINE_FACTS" == "$ERROR_FACTS" ]] || {
    echo "⚠️ STALE: Error handling used $ERROR_FACTS" >&2
    exit 1
}

# ... Continue for all sub-agents ...

# ============================================================================
# PHASE 3: AGGREGATION (Combine Results)
# ============================================================================

python3 <<EOF
import json, sys

# Load all sub-agent outputs
complexity = json.loads('''$COMPLEXITY''')
documentation = json.loads('''$DOCUMENTATION''')
error_handling = json.loads('''$ERROR_HANDLING''')
# ... load all other sub-agents ...

# Aggregate violations
all_violations = (
    complexity.get("violations", []) +
    documentation.get("violations", []) +
    error_handling.get("violations", [])
    # ... add all other violations ...
)

# Compute summary metrics
summary = {
    "total_violations": len(all_violations),
    "by_category": {
        "complexity": len(complexity.get("violations", [])),
        "documentation": len(documentation.get("violations", [])),
        "error_handling": len(error_handling.get("violations", []))
        # ... count all categories ...
    },
    "by_severity": {
        "ERROR": sum(1 for v in all_violations if v.get("severity") == "ERROR"),
        "WARNING": sum(1 for v in all_violations if v.get("severity") == "WARNING")
    }
}

# ============================================================================
# PHASE 4: SCORING (Calculate Compliance)
# ============================================================================

# Compliance score (0-100)
# Example: 100 - (ERROR_count * 2) - (WARNING_count * 1)
error_count = summary["by_severity"]["ERROR"]
warning_count = summary["by_severity"]["WARNING"]
compliance_score = max(0, 100 - (error_count * 2) - (warning_count * 1))

# Pass/fail determination
passed = error_count == 0 and warning_count < 10

# Generate final output
result = {
    "summary": summary,
    "compliance_score": compliance_score,
    "passed": passed,
    "categories": {
        "complexity": complexity,
        "documentation": documentation,
        "error_handling": error_handling
        # ... include all sub-agent outputs ...
    },
    "metadata": complexity["metadata"]  # Use metadata from first sub-agent
}

print(json.dumps(result, indent=2))
EOF
```

**Key Elements**:
1. **Lines 27-28**: Capture FACTS baseline before ANY sub-agent calls
2. **Lines 35-62**: Call each sub-agent with TOCTOU verification
3. **Lines 70-93**: Aggregate violations and compute summary metrics (Python)
4. **Lines 98-102**: Calculate compliance score with custom formula
5. **Lines 105**: Determine pass/fail based on thresholds

---

## 📐 Frontmatter Schema

### Required Fields (Extended from Orchestrator)

```yaml
---
# Core identification (REQUIRED)
name: <agent-name>
description: Comprehensive <domain> compliance dashboard

# Execution (NO 'command:' field - aggregators have custom logic)
cost: high                # Aggregators are expensive (5-10 sub-agents)
runtime: >5s              # Usually >5s due to multiple sub-agent calls

# Dependencies (CRITICAL - aggregators depend on simple agents)
requires: []              # Usually empty (FACTS.parquet is enough)
after: []                 # Usually empty (can run standalone)

# Schema (COMPREHENSIVE dashboard structure)
returns:
  summary:
    total_violations: integer
    by_category: {category_name: count}
    by_severity: {ERROR: int, WARNING: int}
  compliance_score: integer (0-100)
  passed: boolean
  categories:
    <category1>: {violations, summary, metadata}
    <category2>: {violations, summary, metadata}
    ...
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1

# Inherited (KEEP)
tools: Bash, Read         # Aggregators need Read for Python scripts
model: sonnet             # Use sonnet for analysis (NOT haiku)
color: orange
permissionMode: bypassPermissions
---
```

---

## 🎯 2 Agents Using This Pattern

### 1. governance-report

**Purpose**: Comprehensive governance compliance dashboard

**Sub-Agents Called** (8 total):
1. `complexity` - Cyclomatic complexity, LOC, nesting, params
2. `doc-quality` - Docstring quality (Args, Returns, Raises)
3. `error-patterns` - Error handling anti-patterns
4. `logging-audit` - Logging anti-patterns
5. `type-coverage` - Type annotation coverage
6. `solid-srp` - Single Responsibility Principle violations
7. `solid-lsp` - Liskov Substitution Principle violations
8. `naming` - Naming convention violations

**Aggregation Logic**:
- Combine all violations (8 sources)
- Group by category (complexity, documentation, error_handling, types, SOLID)
- Count by severity (ERROR, WARNING)
- Calculate compliance score: `100 - (ERROR * 2) - (WARNING * 1)`

**Pass/Fail Criteria**:
- Passed: `ERROR_count == 0 AND WARNING_count < threshold`
- Failed: Any ERROR violations

**Output Schema**:
```yaml
returns:
  summary:
    total_violations: integer
    total_warnings: integer
    by_category:
      complexity: integer
      documentation: integer
      error_handling: integer
      types: integer
      solid: integer
    by_severity:
      ERROR: integer
      WARNING: integer
  compliance_score: integer (0-100)
  passed: boolean
  categories:
    complexity: {violations: [], summary: {}, metadata: {}}
    documentation: {violations: [], summary: {}, metadata: {}}
    error_handling: {violations: [], summary: {}, metadata: {}}
    types: {violations: [], summary: {}, metadata: {}}
    solid: {violations: [], summary: {}, metadata: {}}
  metadata: {6 standard fields}
```

**Use Cases**:
- Pre-commit hooks (quality gate)
- CI/CD pipelines (release gate)
- Periodic code health checks

**Complexity**: HIGH (8 sub-agents, complex scoring)

---

### 2. security-audit

**Purpose**: Comprehensive security scan

**Sub-Agents Called** (5 total):
1. `hardcoding` - Hardcoded secrets, paths, URLs
2. `dangerous-calls` - eval(), exec(), subprocess with shell=True
3. `sql-injection` - SQL injection risks
4. `import-audit` - Wildcard imports (security risk)
5. `module-purity` - Import-time side effects (security concern)

**Aggregation Logic**:
- Combine all security violations (5 sources)
- Classify by severity (CRITICAL, HIGH, MEDIUM, LOW)
- Group by category (secrets, dangerous_ops, injection, imports)
- Calculate risk score: `CRITICAL * 10 + HIGH * 5 + MEDIUM * 2 + LOW * 1`

**Pass/Fail Criteria**:
- Passed: `CRITICAL == 0 AND HIGH == 0`
- Failed: Any CRITICAL or HIGH severity violations

**Output Schema**:
```yaml
returns:
  summary:
    total_issues: integer
    by_severity:
      CRITICAL: integer
      HIGH: integer
      MEDIUM: integer
      LOW: integer
    by_category:
      secrets: integer
      dangerous_ops: integer
      injection: integer
      imports: integer
  risk_score: integer (0-100+)
  passed: boolean
  categories:
    secrets: {violations: [], summary: {}, metadata: {}}
    dangerous_ops: {violations: [], summary: {}, metadata: {}}
    injection: {violations: [], summary: {}, metadata: {}}
    imports: {violations: [], summary: {}, metadata: {}}
  metadata: {6 standard fields}
```

**Use Cases**:
- Pre-release security audit
- Before deploying to production
- Compliance checks (SOC2, ISO27001)

**Complexity**: MEDIUM (5 sub-agents, simpler scoring than governance)

---

## 🔧 TOCTOU Protection (MANDATORY)

### Why Aggregators Need TOCTOU More Than Anyone

**Scenario**:
- Aggregator calls 8 sub-agents sequentially
- Total runtime: ~8 seconds
- Probability code changes during execution: **HIGH**
- Impact if TOCTOU not checked: **Dashboard shows inconsistent data**

### Implementation Pattern (For Each Sub-Agent)

```bash
# Capture baseline ONCE at start
BASELINE_FACTS=$(basename "$(readlink -f FACTS.parquet)")

# For EACH sub-agent:
OUTPUT=$(uv run fact-file-query-tool <command> --format json 2>&1)
OUTPUT_FACTS=$(echo "$OUTPUT" | jq -r '.metadata.facts_file')

if [[ "$BASELINE_FACTS" != "$OUTPUT_FACTS" ]]; then
    echo "⚠️ STALE: <agent> used $OUTPUT_FACTS, baseline is $BASELINE_FACTS" >&2
    echo "   Code changed during aggregation - aborting" >&2
    exit 1
fi

# Safe to proceed to next sub-agent
```

**Critical**: Check TOCTOU after EVERY sub-agent, not just at the end.

**Reference**: [USING_SUB_AGENTS.yaml](../rules/USING_SUB_AGENTS.yaml) § TOCTOU Protection

---

## 📊 Scoring Formulas

### Governance Compliance Score

```python
# Inputs
error_count = violations with severity="ERROR"
warning_count = violations with severity="WARNING"

# Formula
compliance_score = max(0, 100 - (error_count * 2) - (warning_count * 1))

# Pass/Fail
passed = (error_count == 0) and (warning_count < 10)
```

**Rationale**:
- ERROR violations: -2 points each (serious issues)
- WARNING violations: -1 point each (minor issues)
- Threshold: 0 errors, <10 warnings for pass

---

### Security Risk Score

```python
# Inputs
critical = violations with severity="CRITICAL"
high = violations with severity="HIGH"
medium = violations with severity="MEDIUM"
low = violations with severity="LOW"

# Formula
risk_score = (critical * 10) + (high * 5) + (medium * 2) + (low * 1)

# Pass/Fail
passed = (critical == 0) and (high == 0)
```

**Rationale**:
- CRITICAL: 10 points each (hardcoded secrets, SQL injection)
- HIGH: 5 points each (dangerous calls, eval/exec)
- MEDIUM: 2 points each (wildcard imports)
- LOW: 1 point each (minor concerns)
- Threshold: 0 critical, 0 high for pass

---

## 🐍 Python Aggregation Pattern

### Standard Template

```python
#!/usr/bin/env python3
import json, sys

# ============================================================================
# LOAD SUB-AGENT OUTPUTS
# ============================================================================

# Load from bash variables (passed via heredoc)
sub1 = json.loads('''$SUB1_OUTPUT''')
sub2 = json.loads('''$SUB2_OUTPUT''')
# ... load all sub-agents ...

# ============================================================================
# AGGREGATE VIOLATIONS
# ============================================================================

all_violations = []
for sub in [sub1, sub2, ...]:
    all_violations.extend(sub.get("violations", []))

# ============================================================================
# COMPUTE SUMMARY METRICS
# ============================================================================

summary = {
    "total_violations": len(all_violations),
    "by_category": {
        "cat1": len(sub1.get("violations", [])),
        "cat2": len(sub2.get("violations", []))
    },
    "by_severity": {
        "ERROR": sum(1 for v in all_violations if v.get("severity") == "ERROR"),
        "WARNING": sum(1 for v in all_violations if v.get("severity") == "WARNING")
    }
}

# ============================================================================
# CALCULATE SCORES
# ============================================================================

error_count = summary["by_severity"]["ERROR"]
warning_count = summary["by_severity"]["WARNING"]

compliance_score = max(0, 100 - (error_count * 2) - (warning_count * 1))
passed = (error_count == 0) and (warning_count < 10)

# ============================================================================
# GENERATE OUTPUT
# ============================================================================

result = {
    "summary": summary,
    "compliance_score": compliance_score,
    "passed": passed,
    "categories": {
        "cat1": sub1,
        "cat2": sub2
    },
    "metadata": sub1["metadata"]  # Use metadata from first sub-agent
}

print(json.dumps(result, indent=2))
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ Mistake 1: Only Checking TOCTOU at End

**Bad**:
```bash
# Call all sub-agents
SUB1=$(uv run fact-file-query-tool complexity --format json)
SUB2=$(uv run fact-file-query-tool doc-quality --format json)
SUB3=$(uv run fact-file-query-tool security --format json)

# Check TOCTOU only once at end
CURRENT=$(basename "$(readlink -f FACTS.parquet)")
if [[ "$BASELINE" != "$CURRENT" ]]; then
    exit 1  # Too late! Already combined stale data
fi
```

**Good**:
```bash
# Check TOCTOU after EACH sub-agent
SUB1=$(uv run fact-file-query-tool complexity --format json)
[[ "$BASELINE" == "$(echo "$SUB1" | jq -r '.metadata.facts_file')" ]] || exit 1

SUB2=$(uv run fact-file-query-tool doc-quality --format json)
[[ "$BASELINE" == "$(echo "$SUB2" | jq -r '.metadata.facts_file')" ]] || exit 1

SUB3=$(uv run fact-file-query-tool security --format json)
[[ "$BASELINE" == "$(echo "$SUB3" | jq -r '.metadata.facts_file')" ]] || exit 1
```

---

### ❌ Mistake 2: Not Handling Sub-Agent Failures

**Bad**:
```bash
SUB1=$(uv run fact-file-query-tool complexity --format json 2>&1)
# If complexity fails with exit 1, $SUB1 contains error message, not JSON
# Python script will crash when trying to parse it
```

**Good**:
```bash
SUB1=$(uv run fact-file-query-tool complexity --format json 2>&1)
if ! echo "$SUB1" | jq empty 2>/dev/null; then
    echo "⛔ Sub-agent 'complexity' returned invalid JSON" >&2
    echo "$SUB1" >&2
    exit 1
fi
```

---

### ❌ Mistake 3: Hardcoding Sub-Agent Count in Summary

**Bad**:
```python
summary = {
    "total_agents": 8  # Hardcoded - will break if we add/remove agents
}
```

**Good**:
```python
sub_agents = [sub1, sub2, sub3, sub4, sub5, sub6, sub7, sub8]

summary = {
    "total_agents": len(sub_agents),  # Dynamic count
    "total_violations": sum(len(s.get("violations", [])) for s in sub_agents)
}
```

---

### ❌ Mistake 4: Using First Metadata Without Verification

**Bad**:
```python
# What if sub1 failed and has no metadata?
result = {
    "metadata": sub1["metadata"]  # KeyError if sub1 invalid
}
```

**Good**:
```python
# Use metadata from first valid sub-agent
metadata = None
for sub in [sub1, sub2, sub3, ...]:
    if "metadata" in sub:
        metadata = sub["metadata"]
        break

if metadata is None:
    print('{"error": "No valid sub-agent outputs"}', file=sys.stderr)
    sys.exit(1)

result = {
    "metadata": metadata
}
```

---

## 📚 Related Documentation

| Document | Purpose | Key Sections |
|----------|---------|--------------|
| [AGENT_CONTRACT.md](../rules/AGENT_CONTRACT.md) | Agent standards | Exit codes, Metadata schema |
| [USING_SUB_AGENTS.yaml](../rules/USING_SUB_AGENTS.yaml) | Orchestration | TOCTOU protection (CRITICAL), Retry logic |
| [HARD_STOP_CONDITIONS.md](../rules/HARD_STOP_CONDITIONS.md) | Error handling | HS-201 (TOCTOU), HS-101 (Invalid JSON) |
| [JSON_PROCESSING_RULES.yaml](../rules/JSON_PROCESSING_RULES.yaml) | JSON standards | jq vs python |
| [SIMPLE_QUERY_AGENT.md](./SIMPLE_QUERY_AGENT.md) | Sub-agent pattern | What aggregators call |

---

## ✅ Compliance Checklist

**Before marking agent as "aggregator agent"**:

- [ ] Agent calls 5+ simple query agents
- [ ] Has error trap: `trap 'echo "⛔..." >&2' ERR`
- [ ] Checks FACTS.parquet exists before execution
- [ ] Captures FACTS baseline BEFORE first sub-agent call
- [ ] Verifies TOCTOU AFTER EACH sub-agent call (not just at end)
- [ ] Validates JSON from EACH sub-agent before using
- [ ] Aggregates violations from all sub-agents
- [ ] Computes summary metrics (total, by_category, by_severity)
- [ ] Calculates compliance/risk score with documented formula
- [ ] Determines pass/fail with documented thresholds
- [ ] Propagates metadata from first valid sub-agent
- [ ] Frontmatter uses `model: sonnet` (NOT haiku)
- [ ] Frontmatter uses `cost: high` (aggregators are expensive)
- [ ] Frontmatter uses `runtime: >5s` (multiple sub-agent calls)
- [ ] No `command:` field (aggregators have custom logic)
- [ ] References this template: `See: [AGGREGATOR_AGENT.md]`

---

## 🎓 Design Rationale

### Why Aggregators Exist

**Problem**: Running 8 agents manually is tedious
```bash
uv run fact-file-query-tool complexity --format json > complexity.json
uv run fact-file-query-tool doc-quality --format json > doc.json
uv run fact-file-query-tool error-patterns --format json > errors.json
# ... 5 more commands ...
# Then manually combine and score
```

**Solution**: One command for comprehensive analysis
```bash
uv run fact-file-query-tool governance-report --format json
# Returns combined dashboard with compliance score
```

### Why Aggregators Use High Cost

**Resource Usage**:
- 8 sub-agents × ~200ms each = ~1.6 seconds
- Python aggregation: ~200ms
- Total runtime: ~2 seconds
- Token usage: 8 agents × context = significant

**Justification**: "One command comprehensive audit" worth the cost.

### Why TOCTOU Is More Critical for Aggregators

**Simple Agent**: 1 query, <1s runtime → Low TOCTOU risk
**Orchestrator**: 2-3 queries, ~2s runtime → Medium TOCTOU risk
**Aggregator**: 8 queries, ~8s runtime → **HIGH TOCTOU risk**

**Impact**: Aggregator dashboard with inconsistent data → Wrong decisions

**Mitigation**: Check TOCTOU after EVERY sub-agent (not just at end)

---

## 📊 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-23 | Initial template - 2 aggregator agents covered |

---

**Status**: ✅ Active
**Applies To**: 2 of 23 agents (governance-report, security-audit)
**Last Updated**: 2025-12-23

---

**End of AGGREGATOR_AGENT.md**
