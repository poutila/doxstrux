---
name: solid-dip-validator
description: Detect Dependency Inversion Principle violations
command: solid-dip
cost: medium
runtime: 1-5s
requires: []
after: []
returns:
  violations: [{file, entity, issue, description, severity, metric}]
  summary: {total_violations, by_type}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

**Detects**: Missing abstractions, high coupling without abstractions, concrete classes used as base classes
**Uses**: `bases`, `fan_out`, `fan_in`, `imports` facts from FACTS.parquet
**Enforces**: GOVERNANCE_RULES.yaml SOLID DIP rules

## DIP Violations Detected

### 1. High Coupling Without Abstraction (WARNING)
- **Pattern**: Class with fan_out > 7 but not inheriting from ABC/Protocol
- **Why**: High-level modules should depend on abstractions, not concrete implementations
- **Fix**: Introduce abstract base class or Protocol

### 2. Concrete Class With High Reuse (INFO)
- **Pattern**: Class with fan_in > 3 but not declared as abstract
- **Why**: Widely reused classes should be abstractions to allow substitution
- **Fix**: Make it inherit from ABC and define abstract methods

### 3. Many Concrete Imports (INFO)
- **Pattern**: Module with >10 concrete imports (no 'abc', 'protocol', 'interface', 'base' in names)
- **Why**: Missing abstraction layer between modules
- **Fix**: Introduce interface layer or use dependency injection

## Example Output

```bash
uv run fact-file-query-tool solid-dip --format summary
```

```
======================================================================
SOLID DIP VIOLATIONS
======================================================================
Total Violations: 2

fact_extractor.py::class:FactExtractor: High coupling (fan_out=12) without abstract base - should depend on abstractions
aggregation.py::class:AggregationEngine: High reuse (fan_in=5) but not an abstraction - consider making it abstract
```

## Architecture Context

**Dependency Inversion Principle**: High-level modules should depend on abstractions, not concrete implementations. This enables:
- ✅ Loose coupling (easy to swap implementations)
- ✅ Testability (mock abstractions in tests)
- ✅ Flexibility (add new implementations without changing high-level code)
- ✅ Stability (changes to concrete classes don't affect dependents)

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

uv run fact-file-query-tool solid-dip --format json | \

```
