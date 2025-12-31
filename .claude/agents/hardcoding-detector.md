---
name: hardcoding-detector
description: Detect hardcoded paths, URLs, credentials, connection strings
command: hardcoding
cost: low
runtime: <1s
requires: []
after: []
returns:
  violations: [{file, entity, hardcoded_value, type, severity, message}]
  summary: {total_violations, by_type}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

**Detects**: Hardcoded paths, URLs, credentials, connection strings - prevents credential leaks
**Uses**: `hardcoded_paths`, `hardcoded_secrets`, `security_hardcoded_secrets` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml no_hardcoding rule

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

uv run fact-file-query-tool hardcoding --format json | \
   
```
