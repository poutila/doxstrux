---
name: drift-detector
description: Detect drift between FACTS snapshots for CI/CD gating and release management

# Execution
command: drift
cost: low
runtime: <1s

# Dependencies
requires: []
after: []

# Schema
returns:
  violations: [{file, entity, change_type, severity, baseline_value, current_value, message}]
  summary: {total_changes, by_type, breaking_changes}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1

# Inherited
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

This agent uses the simple query pattern with command: `drift`

Detects semantic drift between FACTS snapshots by comparing baseline vs current state to identify breaking changes, contract violations, and behavioral changes.

**What it detects**:
- Signature changes (parameters added/removed/reordered)
- Behavioral changes (exceptions raised, side effects)
- Contract violations (return types changed, complexity increases)
- Breaking changes vs non-breaking changes

**Use cases**:
- CI/CD gating (fail build on breaking changes)
- Release management (identify what changed between versions)
- Documentation drift detection (docstring changes)

**Severity levels**:
- ERROR: Breaking changes (signature changes, new exceptions)
- WARNING: Non-breaking changes (complexity increase, doc changes)

**Uses**: All fact families from FACTS.parquet (compares baseline snapshot vs current)
**Enforces**: GOVERNANCE_RULES.yaml drift detection rules

```bash
#!/bin/bash
set -Eeuo pipefail

# =============================================================================
# drift-detector
# Purpose: Detect drift between FACTS snapshots
# Template: SIMPLE_QUERY_AGENT.md
# =============================================================================

# Error trap (MANDATORY)
trap 'echo "⛔ Error in $(basename "$0"): line $LINENO" >&2; exit 1' ERR

# Prerequisite check (MANDATORY)
FACTS="${FACTS_FILE:-src/golden_validator_hybrid/FACTS.parquet}"
[[ -f "$FACTS" ]] || {
    echo "⛔ FACTS.parquet not found: $FACTS" >&2
    echo "   Run: uv run fact-file-query-tool generate" >&2
    exit 1
}

# Main execution
uv run fact-file-query-tool drift --format json | \
   
```
