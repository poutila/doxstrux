---
name: magic-number-detector
description: Detect magic numbers that should be named constants
command: magic-numbers
cost: low
runtime: <1s
requires: []
after: []
returns:
  violations: [{file, entity, magic_number, context, severity, message}]
  summary: {total_violations, allowed_literals}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

**Detects**: Unexplained numeric literals that should be named constants
**Allowed**: 0, 1, -1, 2 (common literals)
**Uses**: `magic_numbers` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml no_magic_numbers rule

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

uv run fact-file-query-tool magic-numbers --format json | \
   
```
