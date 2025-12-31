---
name: naming-validator
description: Validate naming conventions
command: naming
cost: low
runtime: <1s
requires: []
after: []
returns:
  violations: [{file, entity, current_name, expected_convention, severity, message}]
  summary: {total_violations, by_convention}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

**Validates**:
- SCREAMING_SNAKE_CASE for constants
- snake_case for functions/methods
- PascalCase for classes

**Uses**: `name`, `qualname` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml naming_conventions rule

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

uv run fact-file-query-tool naming --format json | \
   
```
