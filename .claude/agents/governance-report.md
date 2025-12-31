---
name: governance-report
description: Generate comprehensive governance compliance report from GOVERNANCE_RULES.yaml. Use when requesting complete code quality dashboard or comprehensive compliance overview. Provides dashboard view of code quality across entire codebase - complexity metrics, SOLID principles, documentation coverage, error handling patterns, type annotation coverage, security concerns, and overall compliance score.
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

Executes `fact-file-query-tool governance-report` to generate compliance dashboard.

```bash
set -Eeuo pipefail

# Helper functions
require_cmd() { command -v "$1" >/dev/null || { echo "❌ Missing required command: $1" >&2; exit 2; }; }
require_file() { [ -f "$1" ] || { echo "❌ Missing required file: $1" >&2; echo "💡 Run: uv run fact-file-query-tool generate --source src/" >&2; exit 2; }; }

# Canonical hard stop trap
trap 'rc=$?;
  echo "❌ HARD STOP (rc=$rc)" >&2;
  echo "   file: ${BASH_SOURCE[0]}" >&2;
  echo "   line: $LINENO" >&2;
  echo "   func: ${FUNCNAME[1]:-MAIN}" >&2;
  echo "   cmd : $BASH_COMMAND" >&2;
  echo "" >&2;
  echo "💡 If fact-file-query-tool failed, check that FACTS.parquet exists" >&2;
  echo "💡 Run: uv run fact-file-query-tool generate --source src/" >&2;
  exit "$rc"' ERR

# Validate prerequisites
echo "🔍 Validating prerequisites..."
require_cmd uv

# Find FACTS.parquet (may be symlink to timestamped version)
FACTS_FILE=$(find src/ -maxdepth 2 -name "FACTS.parquet" -type f -o -name "FACTS.parquet" -type l | head -1)
if [ -z "$FACTS_FILE" ]; then
  echo "❌ FACTS.parquet not found in src/" >&2
  echo "💡 Generate it with: uv run fact-file-query-tool generate --source src/" >&2
  exit 2
fi

echo "✅ Found FACTS.parquet: $FACTS_FILE"
echo "✅ Prerequisites validated"

# Run governance report (uses fact-file-query-tool ONLY - NO file reading)
echo "🔍 Running Governance Compliance Report via fact-file-query-tool..."
uv run fact-file-query-tool governance-report --format json

echo "✅ Governance report complete"
```

Returns governance compliance report as JSON.
