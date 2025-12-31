---
name: governance-check
description: Check code governance rules from GOVERNANCE_RULES.yaml using FACTS.parquet

# Execution
command: governance
cost: medium
runtime: 1-5s

# Dependencies
requires: []
after: []

# Schema
returns:
  violations: [{file, entity, rule_id, category, severity, threshold, actual_value, message}]
  summary: {total_violations, by_category, by_severity, compliance_score}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1

# Inherited
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

This agent uses the simple query pattern with command: `governance`

Comprehensive governance compliance check that verifies code against all rules in GOVERNANCE_RULES.yaml - complexity limits, documentation requirements, error handling, types, security, and SOLID principles.

**What it checks**:
- Complexity limits (cyclomatic, cognitive, max_params, max_loc)
- Documentation requirements (docstring presence, quality)
- Error handling patterns (no silent exceptions, no bare except)
- Type annotation coverage (typed_param_ratio, return_typed)
- Security concerns (dangerous calls, hardcoded secrets)
- SOLID principles (SRP, LSP violations)

**Use cases**:
- Pre-commit validation (verify compliance before committing)
- CI/CD quality gate (fail build on governance violations)
- Code review preparation (identify issues before review)

**Severity levels**:
- ERROR: Critical violations (complexity over limit, missing docs on public APIs)
- WARNING: Non-critical violations (complexity approaching limit, missing private docs)

**Uses**: All fact families from FACTS.parquet (complexity, documentation, errors, types, security, etc.)
**Enforces**: All rules from GOVERNANCE_RULES.yaml

```bash
#!/bin/bash
set -Eeuo pipefail

# =============================================================================
# governance-check
# Purpose: Check code governance rules compliance
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
uv run fact-file-query-tool governance --format json | \
   
```
