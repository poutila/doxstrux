---
name: blast-radius
description: Analyze the blast radius of a function or class for incident response. Shows who calls it, what it calls, error contract, side effects, and resource usage - everything needed for fast triage. Use proactively when investigating incidents, planning changes, or assessing impact.
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

Executes `fact-file-query-tool blast-radius` to analyze impact of a function or class.

```bash
set -Eeuo pipefail

# Helper functions
require_cmd() { command -v "$1" >/dev/null || { echo "❌ Missing required command: $1" >&2; exit 2; }; }
require_file() { [[ -f "$1" ]] || { echo "❌ Missing required file: $1" >&2; exit 2; }; }

# Canonical hard stop trap (HARD_STOP_CONDITIONS.md)
trap 'rc=$?; 
  echo "❌ HARD STOP (rc=$rc)" >&2;
  echo "   file: ${BASH_SOURCE[0]}" >&2;
  echo "   line: $LINENO" >&2;
  echo "   func: ${FUNCNAME[1]:-MAIN}" >&2;
  echo "   cmd : $BASH_COMMAND" >&2;
  exit "$rc"' ERR

# Validate prerequisites
echo "🔍 Validating prerequisites..."
require_cmd uv
echo "✅ Prerequisites validated"

# Run validation
echo "🔍 Running Blast Radius..."
uv run fact-file-query-tool blast-radius \
echo "✅ Blast Radius passed"

uv run fact-file-query-tool blast-radius \
```

Returns raw JSON with blast radius analysis.

## Metadata (TOCTOU Protection)

**All blast radius outputs include metadata for result freshness verification.**

This protects against TOCTOU (Time-Of-Check-Time-Of-Use) vulnerabilities where agent results become stale between generation and use by the orchestrator.

### Metadata Fields

Every output includes these 6 fields:

- **`facts_file`**: Timestamped filename (e.g., `"FACTS-20251222-163851.parquet"`)
- **`facts_mtime`**: File modification time (ISO 8601 format)
- **`commit_sha`**: Git commit SHA (7-char short hash, if in repo)
- **`generator_version`**: Package version (e.g., `"0.1.0"`)
- **`file_count`**: Number of files analyzed (sanity check)
- **`query_timestamp`**: When the query was executed (ISO 8601 format)

### Example with Metadata

```json
{
  "entity": "function.process_payment",
  "file": "payments.py",
  "blast_radius": {
    "callers": ["function.checkout", "function.refund"],
    "dependencies": ["function.validate_card", "function.log_transaction"],
    "exceptions_raised": ["PaymentError", "NetworkError"],
    "side_effects": ["database write", "external API call"],
    "io_operations": ["database", "network"],
    "security_concerns": ["handles credit card data"]
  },
  "risk_score": 65,
  "risk_level": "HIGH",
  "metadata": {
    "facts_file": "FACTS-20251222-163851.parquet",
    "facts_mtime": "2025-12-22T18:38:56.507106",
    "commit_sha": "67c6db1",
    "generator_version": "0.1.0",
    "file_count": 43,
    "query_timestamp": "2025-12-22T18:39:08.857397"
  }
}
```

### Orchestrator Verification (MANDATORY)

**When using this agent as a sub-agent, orchestrators MUST verify result freshness:**

```bash
# Extract metadata from agent output
agent_facts=$(echo "$agent_output" | uv run python -c "import json, sys; print(json.load(sys.stdin)['metadata']['facts_file'])")
current_facts=$(readlink FACTS.parquet)

# Verify freshness
if [ "$current_facts" != "$agent_facts" ]; then
    echo "⚠️ STALE: Agent results are from old FACTS - DISCARD" >&2
    exit 1
fi

# Safe to use results
echo "✅ Results are fresh - proceeding"
```

**Rationale**: Code may change between agent execution (T1) and result usage (T3). Without verification, stale results can cause incorrect decisions.

**See**: [USING_SUB_AGENTS.yaml](../.claude/rules/USING_SUB_AGENTS.yaml) for complete orchestration protocol, metadata requirements, and TOCTOU protection guidance.

