---
name: error-pattern-audit
description: Detect error handling anti-patterns

# Execution
command: error-patterns
cost: low
runtime: <1s

# Dependencies
requires: []
after: []

# Schema
returns:
  violations: [{file, entity, pattern_type, severity, message}]
  summary: {total_violations, by_pattern}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1

# Inherited
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

This agent uses the simple query pattern with command: `error-patterns`

**Detects**:
- Bare `except:` (catches everything including KeyboardInterrupt)
- Silent exceptions (`except: pass` with no logging)
- Swallowed errors (catching without re-raising or logging)

**Uses**: `exception_types`, `caught_exceptions` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml error_handling rules

```bash
#!/bin/bash
set -Eeuo pipefail
trap 'echo "⛔ Error in $(basename "$0"): line $LINENO" >&2; exit 1' ERR

FACTS="${FACTS_FILE:-src/golden_validator_hybrid/FACTS.parquet}"
[[ -f "$FACTS" ]] || {
    echo "⛔ FACTS.parquet not found: $FACTS" >&2
    echo "   Run: uv run fact-file-query-tool generate" >&2
    exit 1
}

uv run fact-file-query-tool error-patterns --format json | \
   
```
