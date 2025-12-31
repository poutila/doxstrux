---
name: test-gap-analysis
description: Identify where tests are most needed based on risk factors. Use when planning test improvements or prioritizing test coverage. Combines complexity, coupling, security concerns, and side effects to prioritize test writing efforts for maximum ROI.
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

Executes `fact-file-query-tool test-gaps` to identify high-risk untested code.

```bash
set -Eeuo pipefail

# Helper functions
require_cmd() { command -v "$1" >/dev/null || { echo "❌ Missing required command: $1" >&2; exit 2; }; }

# Canonical hard stop trap
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

# Run test gap analysis
echo "🔍 Running Test Gap Analysis..."
uv run fact-file-query-tool test-gaps --format json
echo "✅ Test gap analysis complete"
```

**Format options**:
- `json`: Machine-readable JSON for further processing (default for agents)
- `summary`: Human-readable formatted output

## Output

Return raw JSON only. Caller will analyze.

**Output includes**:
- **Risk score**: Composite risk from multiple factors
- **Complexity**: Cyclomatic complexity metrics
- **Coupling**: Fan-in/fan-out statistics
- **Security concerns**: Handles sensitive data, dangerous operations
- **Side effects**: I/O, mutations, external dependencies
- **Current test coverage**: Existing test presence

## Example Usage

```
User: Where should I write tests first?

Agent: uv run fact-file-query-tool test-gaps --format json
```
