---
name: logging-audit
description: Detect logging anti-patterns (print() in production, missing log levels)

# Execution
command: logging-audit
cost: low
runtime: <1s

# Dependencies
requires: []
after: []

# Schema
returns:
  violations: [{file, entity, issue_type, severity, message}]
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

This agent uses the simple query pattern with command: `logging-audit`

**Detects**:
- `print()` statements in production code
- Missing log levels (should use logger.info/warning/error, not print)

**Uses**: `calls` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml logging rules

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

uv run fact-file-query-tool logging-audit --format json
   
```
