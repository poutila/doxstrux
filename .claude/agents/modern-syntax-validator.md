---
name: modern-syntax-validator
description: Enforce modern type syntax (PEP 604, PEP 585)

# Execution
command: modern-syntax
cost: low
runtime: <1s

# Dependencies
requires: []
after: []

# Schema
returns:
  violations: [{file, entity, old_syntax, new_syntax, severity, message}]
  summary: {total_violations, by_type}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1

# Inherited
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

This agent uses the simple query pattern with command: `modern-syntax`

Enforces modern Python type syntax by detecting legacy patterns and suggesting modern alternatives.

**What it checks**:
- `list[T]` vs `List[T]` (PEP 585 - use lowercase)
- `dict[K, V]` vs `Dict[K, V]` (PEP 585)
- `tuple[T, ...]` vs `Tuple[T, ...]` (PEP 585)
- `X | None` vs `Optional[X]` (PEP 604 - use union syntax)
- `X | Y` vs `Union[X, Y]` (PEP 604)

**Severity levels**:
- WARNING: Legacy syntax detected (not an error, but should modernize)

**Uses**: `return_type` and `arg_types` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml modern_syntax rule

```bash
#!/bin/bash
set -Eeuo pipefail

# =============================================================================
# modern-syntax-validator
# Purpose: Enforce modern type syntax (PEP 604, PEP 585)
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
uv run fact-file-query-tool modern-syntax --format json | \
   
```
