---
name: doc-quality-validator
description: Check docstring quality (Args, Returns, Raises sections)

# Execution
command: doc-quality
cost: low
runtime: <1s

# Dependencies
requires: []
after: []

# Schema
returns:
  violations: [{file, entity, missing_sections, severity, message}]
  summary: {total_violations, by_severity}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1

# Inherited
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

This agent uses the simple query pattern with command: `doc-quality`

Checks docstring quality by verifying presence of required sections (Args, Returns, Raises) based on function signatures and behavior.

**What it checks**:
- Args section present for functions with parameters
- Returns section present for functions with return values
- Raises section present for functions that raise exceptions

**Severity levels**:
- ERROR: Public function missing required section
- WARNING: Private function missing recommended section

**Uses**: `doc` and `doc_sections` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml documentation rule

```bash
#!/bin/bash
set -Eeuo pipefail

# =============================================================================
# doc-quality-validator
# Purpose: Check docstring quality (Args, Returns, Raises)
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
uv run fact-file-query-tool doc-quality --format json | \
   
```
