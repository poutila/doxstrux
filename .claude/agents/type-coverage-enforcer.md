---
name: type-coverage-enforcer
description: Enforce strict type coverage (100% for public APIs)
command: type-coverage
cost: low
runtime: <1s
requires: []
after: []
returns:
  violations: [{file, entity, missing_annotations, coverage_pct, severity, message}]
  summary: {total_violations, avg_coverage}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

**Enforces**: 100% type coverage for public APIs
**Uses**: `typed_param_ratio`, `return_typed`, `type_complete` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml type_checking rules

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

uv run fact-file-query-tool type-coverage --format json | \
   
```
