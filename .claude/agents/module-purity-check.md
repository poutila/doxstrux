---
name: module-purity-check
description: Detect import-time side effects (I/O, network, database)

# Execution
command: module-purity
cost: low
runtime: <1s

# Dependencies
requires: []
after: []

# Schema
returns:
  violations: [{file, entity, side_effect_type, severity, message}]
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

This agent uses the simple query pattern with command: `module-purity`

**Detects**: Side effects at module import time that cause test flakiness and slow imports
- I/O operations during import
- Network calls during import
- Database connections during import

**Uses**: `calls` and side-effect facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml module_import_purity rules

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

uv run fact-file-query-tool module-purity --format json | \
   
```
