# Orchestrator Agent Template

**Purpose**: Standard pattern for agents that call multiple sub-agents or queries and combine results.

**Version**: 1.0.0
**Date**: 2025-12-23
**Applies To**: 4 of 23 agents

---

## 📋 Overview

**Orchestrator Agents** are complex agents that:
- Call multiple sub-agents or `fact-file-query-tool` queries
- Combine results with custom logic (scoring, ranking, filtering)
- Verify TOCTOU protection when combining results from different sources
- Have sophisticated output schemas with derived metrics
- Require more computational resources (medium to high cost)

**Philosophy**: Orchestrators coordinate multiple data sources and apply domain-specific interpretation.

---

## 🏗️ Standard Implementation Pattern

### Structure (3 Phases)

1. **Phase 1: Prerequisites** - Verify FACTS exists, set up error handling
2. **Phase 2: Data Collection** - Execute queries/sub-agents, verify freshness
3. **Phase 3: Analysis** - Combine results, compute scores, generate output

### Bash Script Template (Lines 1-80+)

```bash
#!/bin/bash
set -Eeuo pipefail

# =============================================================================
# <AGENT-NAME>
# Purpose: <One-line description>
# Template: ORCHESTRATOR_AGENT.md
# =============================================================================

# Error trap (MANDATORY)
trap 'echo "⛔ Error in $(basename "$0"): line $LINENO" >&2; exit 1' ERR

# ============================================================================
# PHASE 1: PREREQUISITES
# ============================================================================

# Verify FACTS.parquet exists
FACTS="${FACTS_FILE:-src/golden_validator_hybrid/FACTS.parquet}"
[[ -f "$FACTS" ]] || {
    echo "⛔ FACTS.parquet not found: $FACTS" >&2
    echo "   Run: uv run fact-file-query-tool generate" >&2
    exit 1
}

# Capture FACTS baseline for TOCTOU protection
BASELINE_FACTS=$(basename "$(readlink -f "$FACTS")")

# ============================================================================
# PHASE 2: DATA COLLECTION
# ============================================================================

# Call sub-agent 1 (or direct query)
SUB1_OUTPUT=$(uv run fact-file-query-tool <command1> --format json 2>&1)
SUB1_FACTS=$(echo "$SUB1_OUTPUT" | jq -r '.metadata.facts_file')

# Verify freshness (TOCTOU protection)
if [[ "$BASELINE_FACTS" != "$SUB1_FACTS" ]]; then
    echo "⚠️ STALE: Sub-agent used $SUB1_FACTS, current is $BASELINE_FACTS" >&2
    exit 1
fi

# Call sub-agent 2 (if needed)
SUB2_OUTPUT=$(uv run fact-file-query-tool <command2> --format json 2>&1)
SUB2_FACTS=$(echo "$SUB2_OUTPUT" | jq -r '.metadata.facts_file')

# Verify freshness again
if [[ "$BASELINE_FACTS" != "$SUB2_FACTS" ]]; then
    echo "⚠️ STALE: Sub-agent used $SUB2_FACTS, current is $BASELINE_FACTS" >&2
    exit 1
fi

# ============================================================================
# PHASE 3: ANALYSIS & OUTPUT
# ============================================================================

# Combine results with custom logic
# (This is where orchestrator-specific logic goes)

# Option A: Use Python script for complex analysis
python3 <<EOF
import json, sys

# Load sub-agent outputs
sub1 = json.loads('''$SUB1_OUTPUT''')
sub2 = json.loads('''$SUB2_OUTPUT''')

# Custom logic (scoring, ranking, filtering)
# ...

# Generate combined output
result = {
    "analysis": { ... },
    "metadata": sub1["metadata"]  # Use metadata from sub-agent
}

print(json.dumps(result, indent=2))
EOF

# Option B: Use jq for simple combination
# echo "$SUB1_OUTPUT" | jq --argjson sub2 "$SUB2_OUTPUT" \
#     '{combined: .violations + $sub2.violations, metadata: .metadata}'
```

**Key Elements**:
1. **Lines 18-24**: FACTS verification with remediation
2. **Line 27**: Capture baseline for TOCTOU protection
3. **Lines 33-42**: Sub-agent execution with freshness verification
4. **Lines 56-74**: Custom analysis logic (Python or jq)

---

## 📐 Frontmatter Schema

### Required Fields (Extended from Simple Agents)

```yaml
---
# Core identification (REQUIRED)
name: <agent-name>
description: <One-line description>

# Execution (DIFFERENT from simple agents)
# NO 'command:' field - orchestrators have custom logic
cost: medium|high         # Usually medium or high
runtime: 1-5s|>5s        # Usually longer than simple agents

# Dependencies (MORE COMPLEX than simple agents)
requires: []              # May require specific fact families
after: []                 # May depend on other agents running first

# Schema (MORE COMPLEX output structure)
returns:
  <orchestrator-specific-fields>
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1

# Inherited (KEEP)
tools: Bash, Read         # Orchestrators may need Read for Python scripts
model: sonnet             # Use sonnet for complex analysis (NOT haiku)
color: orange
permissionMode: bypassPermissions
---
```

### Key Differences from Simple Agents

| Field | Simple Agent | Orchestrator Agent |
|-------|--------------|-------------------|
| `command` | Required | N/A (custom logic) |
| `cost` | Usually `low` | Usually `medium` or `high` |
| `runtime` | Usually `<1s` | Usually `1-5s` or `>5s` |
| `tools` | `Bash` only | `Bash, Read` (for scripts) |
| `model` | `haiku` | `sonnet` (needs reasoning) |
| Output schema | Simple violations | Complex analysis with derived metrics |

---

## 🎯 4 Agents Using This Pattern

### 1. blast-radius

**Purpose**: Analyze blast radius of function/class changes for incident response

**Queries**:
- Direct query for entity metadata
- Call graph analysis (who calls it, what it calls)
- Error contract analysis
- Side effect detection
- Resource usage patterns

**Custom Logic**:
- Risk score calculation (weighted sum of factors)
- Risk level classification (LOW/MEDIUM/HIGH/CRITICAL)
- Prioritized recommendations

**Output Schema**:
```yaml
returns:
  entity: string
  file: string
  blast_radius:
    callers: [array of caller entities]
    dependencies: [array of called entities]
    exceptions_raised: [array of exception types]
    side_effects: [array of side effect descriptions]
    io_operations: [array of I/O types]
    security_concerns: [array of security issues]
  risk_score: integer (0-100)
  risk_level: string (LOW|MEDIUM|HIGH|CRITICAL)
  recommendations: [array of action items]
  metadata: {6 standard fields}
```

**Complexity**: HIGH (multiple queries, weighted scoring, prioritization)

---

### 2. performance-hotspots

**Purpose**: Find performance issues using static analysis without profiling

**Queries**:
- Nested loop detection
- I/O in loops detection
- Blocking calls in async functions
- Regex/string operations in loops
- High complexity functions
- High coupling classes

**Custom Logic**:
- Hotspot ranking by severity (nested loops > I/O in loops > complexity)
- Aggregation by file and entity
- Deduplication of overlapping issues

**Output Schema**:
```yaml
returns:
  hotspots: [
    {
      file: string,
      entity: string,
      issue_type: string,
      severity: ERROR|WARNING,
      description: string,
      line: integer (optional)
    }
  ]
  summary:
    total_hotspots: integer
    by_severity: {ERROR: int, WARNING: int}
    by_type: {nested_loops: int, io_in_loops: int, ...}
  metadata: {6 standard fields}
```

**Complexity**: MEDIUM (multiple queries, ranking, deduplication)

---

### 3. test-gap-analysis

**Purpose**: Identify where tests are most needed based on risk factors

**Queries**:
- Complexity metrics (cyclomatic, LOC, nesting)
- Coupling metrics (fan-in, fan-out)
- Security concerns (dangerous calls, hardcoded secrets)
- Side effects (I/O, network, state mutations)
- Existing test coverage (assertion counts)

**Custom Logic**:
- Risk score per entity (weighted combination of factors)
- Priority ranking (highest risk, lowest coverage first)
- ROI calculation (risk × (1 - coverage))

**Output Schema**:
```yaml
returns:
  gaps: [
    {
      file: string,
      entity: string,
      risk_score: integer (0-100),
      priority: HIGH|MEDIUM|LOW,
      reasons: [array of risk factors],
      current_coverage: float (0.0-1.0),
      recommended_tests: [array of test types]
    }
  ]
  summary:
    total_gaps: integer
    high_priority: integer
    medium_priority: integer
    low_priority: integer
  metadata: {6 standard fields}
```

**Complexity**: HIGH (multiple queries, weighted scoring, ROI calculation)

---

### 4. architecture-map

**Purpose**: Generate architecture overview from FACTS without reading code

**Queries**:
- Module structure (imports, exports)
- Call graph (function calls across modules)
- Class hierarchy (inheritance relationships)
- Coupling metrics (dependencies between modules)

**Custom Logic**:
- Cluster detection (modules that call each other frequently)
- Layer detection (bottom-up from imports)
- Dependency analysis (identify circular dependencies)
- Coupling calculation (afferent/efferent coupling)

**Output Schema**:
```yaml
returns:
  architecture:
    clusters: [
      {
        name: string,
        modules: [array of module names],
        cohesion: float (0.0-1.0)
      }
    ]
    layers: [
      {
        level: integer,
        modules: [array of module names],
        dependencies: [array of lower layers]
      }
    ]
    dependencies: [
      {
        from: string,
        to: string,
        type: import|call|inheritance
      }
    ]
    coupling:
      high_coupling: [array of module pairs],
      circular_deps: [array of module cycles]
  metadata: {6 standard fields}
```

**Complexity**: HIGH (graph algorithms, cluster detection, layer analysis)

---

## 🔧 TOCTOU Protection (MANDATORY)

### Why Orchestrators Need TOCTOU Protection

**Scenario**:
1. Orchestrator calls sub-agent A → gets results from FACTS snapshot T1
2. Code changes, FACTS regenerates → snapshot T2
3. Orchestrator calls sub-agent B → gets results from snapshot T2
4. Orchestrator combines A + B → **INCONSISTENT** (different code states)

**Solution**: Verify all sub-agents used same FACTS snapshot

### Implementation Pattern

```bash
# Step 1: Capture baseline before any sub-agent calls
BASELINE_FACTS=$(basename "$(readlink -f FACTS.parquet)")

# Step 2: After each sub-agent call, extract and verify metadata
SUB_OUTPUT=$(uv run fact-file-query-tool <command> --format json 2>&1)
SUB_FACTS=$(echo "$SUB_OUTPUT" | jq -r '.metadata.facts_file')

if [[ "$BASELINE_FACTS" != "$SUB_FACTS" ]]; then
    echo "⚠️ STALE: Sub-agent used $SUB_FACTS, current is $BASELINE_FACTS" >&2
    echo "   Code changed during execution - results discarded" >&2
    exit 1
fi

# Step 3: Safe to use results (verified fresh)
```

**Reference**: [USING_SUB_AGENTS.yaml](../rules/USING_SUB_AGENTS.yaml) § TOCTOU Protection

---

## 🐍 Python vs Bash for Analysis

### When to Use Python (Recommended for Complex Logic)

**Use Python when**:
- Need weighted scoring (multiply/divide/round)
- Need sorting/ranking with custom comparators
- Need complex data structures (nested dicts, lists)
- Need deduplication or aggregation

**Example**:
```bash
python3 <<EOF
import json, sys

# Load data
violations = json.loads('''$SUB_OUTPUT''')["violations"]

# Custom scoring
for v in violations:
    score = v["complexity"] * 2 + v["coupling"] * 3
    v["risk_score"] = min(100, score)

# Sort by score descending
violations.sort(key=lambda x: x["risk_score"], reverse=True)

# Take top 10
top10 = violations[:10]

print(json.dumps({"top_risks": top10}, indent=2))
EOF
```

---

### When to Use jq (For Simple Combination)

**Use jq when**:
- Just combining arrays (`violations1 + violations2`)
- Simple filtering (`.[] | select(.severity == "ERROR")`)
- Field extraction (`.violations | map({file, entity})`)

**Example**:
```bash
echo "$SUB1_OUTPUT" | jq --argjson sub2 "$SUB2_OUTPUT" \
    '{
        combined: .violations + $sub2.violations,
        total: (.violations | length) + ($sub2.violations | length),
        metadata: .metadata
    }'
```

**Reference**: [JSON_PROCESSING_RULES.yaml](../rules/JSON_PROCESSING_RULES.yaml)

---

## ⚠️ Common Mistakes to Avoid

### ❌ Mistake 1: Not Verifying TOCTOU

**Bad**:
```bash
SUB1=$(uv run fact-file-query-tool complexity --format json)
SUB2=$(uv run fact-file-query-tool security --format json)
# Combine without checking if both used same FACTS
```

**Good**:
```bash
BASELINE=$(basename "$(readlink -f FACTS.parquet)")

SUB1=$(uv run fact-file-query-tool complexity --format json)
SUB1_FACTS=$(echo "$SUB1" | jq -r '.metadata.facts_file')
[[ "$BASELINE" == "$SUB1_FACTS" ]] || exit 1

SUB2=$(uv run fact-file-query-tool security --format json)
SUB2_FACTS=$(echo "$SUB2" | jq -r '.metadata.facts_file')
[[ "$BASELINE" == "$SUB2_FACTS" ]] || exit 1

# Safe to combine
```

---

### ❌ Mistake 2: Using Bare python3 Instead of uv run

**Bad** (violates JSON_PROCESSING_RULES.yaml):
```bash
echo "$OUTPUT" | python3 -m json.tool
```

**Good**:
```bash
echo "$OUTPUT" | jq .
# OR
echo "$OUTPUT" | uv run python -m json.tool
```

---

### ❌ Mistake 3: Not Propagating Metadata

**Bad**:
```bash
python3 <<EOF
result = {
    "analysis": {...}
    # Missing metadata!
}
print(json.dumps(result))
EOF
```

**Good**:
```bash
python3 <<EOF
import json

sub_output = json.loads('''$SUB_OUTPUT''')

result = {
    "analysis": {...},
    "metadata": sub_output["metadata"]  # Propagate from sub-agent
}
print(json.dumps(result))
EOF
```

---

### ❌ Mistake 4: Using haiku Instead of sonnet

**Bad** (frontmatter):
```yaml
model: haiku  # Too simple for orchestrator logic
```

**Good**:
```yaml
model: sonnet  # Can handle complex analysis reasoning
```

**Why**: Orchestrators may need to explain analysis, interpret results, or debug issues. Sonnet has better reasoning.

---

## 📚 Related Documentation

| Document | Purpose | Key Sections |
|----------|---------|--------------|
| [AGENT_CONTRACT.md](../rules/AGENT_CONTRACT.md) | Agent standards | Exit codes, Metadata schema |
| [USING_SUB_AGENTS.yaml](../rules/USING_SUB_AGENTS.yaml) | Orchestration | TOCTOU protection (MANDATORY), Retry logic |
| [HARD_STOP_CONDITIONS.md](../rules/HARD_STOP_CONDITIONS.md) | Error handling | HS-201 (TOCTOU failure), HS-101 (Invalid JSON) |
| [JSON_PROCESSING_RULES.yaml](../rules/JSON_PROCESSING_RULES.yaml) | JSON standards | jq vs python, Bare python3 forbidden |

---

## ✅ Compliance Checklist

**Before marking agent as "orchestrator agent"**:

- [ ] Agent calls 2+ sub-agents OR performs custom analysis
- [ ] Has error trap: `trap 'echo "⛔..." >&2' ERR`
- [ ] Checks FACTS.parquet exists before execution
- [ ] Captures FACTS baseline before sub-agent calls
- [ ] Verifies TOCTOU after EACH sub-agent call
- [ ] Uses jq or `uv run python` (NOT bare `python3`)
- [ ] Propagates metadata from sub-agent to output
- [ ] Frontmatter uses `model: sonnet` (NOT haiku)
- [ ] Frontmatter uses `tools: Bash, Read` (if using Python scripts)
- [ ] Frontmatter includes `cost: medium` or `cost: high`
- [ ] Frontmatter includes `runtime: 1-5s` or `runtime: >5s`
- [ ] No `command:` field (orchestrators have custom logic)
- [ ] References this template: `See: [ORCHESTRATOR_AGENT.md]`

---

## 🎓 Design Rationale

### Why Orchestrators Need Custom Logic

**Simple agents** execute one command and return results.
**Orchestrators** must:
- Combine multiple data sources
- Apply domain-specific weights/scores
- Rank/prioritize results
- Generate actionable recommendations

**Example**: blast-radius risk score
- Simple agent: Return raw metrics (complexity=42, coupling=15)
- Orchestrator: Calculate `risk = (complexity * 2) + (coupling * 3) + (side_effects * 5)`

### Why Orchestrators Use sonnet, Not haiku

**Reasoning Requirements**:
- Explain scoring methodology
- Debug TOCTOU failures
- Interpret complex analysis results
- Generate human-readable recommendations

**Cost Tradeoff**:
- Haiku: $0.25/MTok → cheap, fast, limited reasoning
- Sonnet: $3.00/MTok → 12x cost, better reasoning

**For orchestrators**: Reasoning quality worth 12x cost.

### Why TOCTOU Protection Is MANDATORY

**Without TOCTOU protection**:
```
T0: baseline = FACTS-V1.parquet
T1: complexity query → uses FACTS-V1 (complexity=42)
T2: Code change, FACTS regenerate → FACTS-V2.parquet
T3: security query → uses FACTS-V2 (security=0)
T4: Combine: complexity from V1 + security from V2 → WRONG!
```

**Result**: Risk score calculated from inconsistent data.

**With TOCTOU protection**: Exit immediately if FACTS changed. User re-runs, gets consistent snapshot.

---

## 📊 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-23 | Initial template - 4 orchestrator agents covered |

---

**Status**: ✅ Active
**Applies To**: 4 of 23 agents (blast-radius, performance-hotspots, test-gap-analysis, architecture-map)
**Last Updated**: 2025-12-23

---

**End of ORCHESTRATOR_AGENT.md**
