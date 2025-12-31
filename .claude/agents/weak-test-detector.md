---
name: weak-test-detector
description: Detect weak tests (import-only, no assertions, exit-code-only)
command: weak-tests
cost: low
runtime: <1s
requires: []
after: []
returns:
  violations: [{file, entity, weakness_type, severity, message}]
  summary: {total_violations, by_type}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

**Detects**: Tests that provide false confidence
- Import-only tests
- No assertions
- Exit-code-only tests

**Uses**: `assertions`, `assertion_triggers` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml no_weak_tests rule

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

uv run fact-file-query-tool weak-tests --format json | \
   
```
