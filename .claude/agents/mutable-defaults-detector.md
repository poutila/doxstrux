---
name: mutable-defaults-detector
description: Detect mutable default arguments (CRITICAL bug preventer)
command: mutable-defaults
cost: low
runtime: <1s
requires: []
after: []
returns:
  violations: [{file, entity, param_name, default_type, severity, message}]
  summary: {total_violations, by_type}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

**Detects**: Mutable default arguments (lists, dicts, sets) - subtle Python anti-pattern that causes shared state bugs

**Severity**: CRITICAL - These bugs are hard to detect and cause unexpected behavior

**Uses**: `mutable_default_params` fact from FACTS.parquet

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

uv run fact-file-query-tool mutable-defaults --format json | \
   
```
