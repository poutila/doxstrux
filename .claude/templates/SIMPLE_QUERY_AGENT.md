# Simple Query Agent Template

**Purpose**: Standard pattern for agents that wrap single `fact-file-query-tool` commands.

**Version**: 1.0.0
**Date**: 2025-12-23
**Applies To**: 17 of 23 agents

---

## 📋 Overview

**Simple Query Agents** are the most common agent type (17/23 agents). They:
- Execute a single `fact-file-query-tool <command> --format json`
- Pipe output through `agent_formatter.py` for human-readable summaries
- Return both formatted summary AND full JSON
- Include standard 6-field metadata automatically
- Have zero custom logic (100% declarative)

**Philosophy**: Agents are command executors, not reasoners. The command is the implementation.

---

## 🏗️ Standard Implementation Pattern

### Bash Script (Lines 1-20)

```bash
#!/bin/bash
set -Eeuo pipefail

# =============================================================================
# <AGENT-NAME>
# Purpose: <One-line description>
# Template: SIMPLE_QUERY_AGENT.md
# =============================================================================

# Error trap (MANDATORY - catches all errors)
trap 'echo "⛔ Error in $(basename "$0"): line $LINENO" >&2; exit 1' ERR

# Prerequisite check (MANDATORY - verify FACTS exists)
FACTS="${FACTS_FILE:-src/golden_validator_hybrid/FACTS.parquet}"
[[ -f "$FACTS" ]] || {
    echo "⛔ FACTS.parquet not found: $FACTS" >&2
    echo "   Run: uv run fact-file-query-tool generate" >&2
    exit 1
}

# Main execution (parameterized by 'command' field in frontmatter)
uv run fact-file-query-tool <COMMAND> --format json | \
    python3 "$(dirname "$0")/../rules/agent_formatter.py"
```

**Key Elements**:
1. **Line 2**: `set -Eeuo pipefail` - Fail fast on any error
2. **Line 10**: Error trap - Reports file and line number
3. **Line 13-18**: FACTS.parquet verification with remediation
4. **Line 21-22**: Single command piped to formatter

---

## 📐 Frontmatter Schema

### Required Fields (13 total)

```yaml
---
# Core identification (REQUIRED)
name: <agent-name>
description: <One-line description of what this agent validates>

# Execution (REQUIRED for simple query agents)
command: <subcommand>         # fact-file-query-tool subcommand
cost: low|medium|high         # Resource cost hint
runtime: <1s|1-5s|>5s        # Expected runtime

# Dependencies (REQUIRED)
requires: []                  # Prerequisites (usually empty for simple agents)
after: []                     # Execution order dependencies (usually empty)

# Schema (REQUIRED)
returns:                      # Output schema documentation
  violations: [{file, entity, <agent-specific-fields>}]
  summary: {<agent-specific-summary-fields>}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1             # Schema version (currently 1 for all agents)

# Inherited (KEEP - parsed by Claude Code)
tools: Bash                   # Tool access control (all simple agents use Bash)
model: haiku                  # Model preference (haiku for simple, sonnet for complex)
color: orange                 # UI feature (all agents use orange)
permissionMode: bypassPermissions  # Permission level (no prompts for these agents)
---
```

### Field Descriptions

| Field | Values | Purpose | Example |
|-------|--------|---------|---------|
| `command` | Subcommand name | Parameterizes which tool command to run | `doc-quality` |
| `cost` | low, medium, high | Resource usage hint for orchestrators | `low` |
| `runtime` | <1s, 1-5s, >5s | Expected execution time | `<1s` |
| `requires` | Array of prerequisites | Dependencies that must exist first | `[]` (usually empty) |
| `after` | Array of agent names | Agents that should run before this one | `[]` (usually empty) |
| `returns` | Object schema | Documents output structure | See schema examples below |
| `schema_version` | Integer | Schema version for compatibility checks | `1` |

---

## 🎯 17 Agents Using This Pattern

### Code Quality (7 agents)

1. **doc-quality-validator** - `command: doc-quality`
   - Checks docstring quality (Args, Returns, Raises)
   - Cost: low, Runtime: <1s

2. **modern-syntax-validator** - `command: modern-syntax`
   - Enforces modern type syntax (PEP 604, PEP 585)
   - Cost: low, Runtime: <1s

3. **naming-validator** - `command: naming`
   - Validates naming conventions (SCREAMING_SNAKE_CASE, snake_case, PascalCase)
   - Cost: low, Runtime: <1s

4. **magic-number-detector** - `command: magic-numbers`
   - Detects magic numbers that should be constants
   - Cost: low, Runtime: <1s

5. **import-audit** - `command: import-audit`
   - Checks import style violations (multi-dot relative, wildcard imports)
   - Cost: low, Runtime: <1s

6. **module-purity-check** - `command: module-purity`
   - Detects import-time side effects (I/O, network, database)
   - Cost: low, Runtime: <1s

7. **type-coverage-enforcer** - `command: type-coverage`
   - Enforces strict type coverage (100% for public APIs)
   - Cost: low, Runtime: <1s

### Error Handling (2 agents)

8. **error-pattern-audit** - `command: error-patterns`
   - Detects error handling anti-patterns (bare except, silent exceptions)
   - Cost: low, Runtime: <1s

9. **logging-audit** - `command: logging-audit`
   - Detects logging anti-patterns (print() in production, missing log levels)
   - Cost: low, Runtime: <1s

### SOLID Principles (2 agents)

10. **solid-srp-validator** - `command: solid-srp`
    - Detects Single Responsibility Principle violations (god classes, high coupling)
    - Cost: medium, Runtime: 1-5s

11. **solid-lsp-validator** - `command: solid-lsp`
    - Detects Liskov Substitution Principle violations (NotImplementedError in subclasses)
    - Cost: low, Runtime: <1s

### Security (2 agents)

12. **hardcoding-detector** - `command: hardcoding`
    - Detects hardcoded paths, URLs, credentials, connection strings
    - Cost: low, Runtime: <1s

13. **mutable-defaults-detector** - `command: mutable-defaults`
    - Detects mutable default arguments (lists, dicts, sets as defaults)
    - Cost: low, Runtime: <1s
    - Severity: CRITICAL (subtle Python anti-pattern)

### Testing (1 agent)

14. **weak-test-detector** - `command: weak-tests`
    - Detects weak tests (import-only, no assertions, exit-code-only)
    - Cost: low, Runtime: <1s

### Analysis (3 agents)

15. **drift-detector** - `command: drift`
    - Detects drift between FACTS snapshots (breaking changes, behavioral changes, doc drift)
    - Cost: medium, Runtime: 1-5s
    - **Requires**: `--baseline` parameter (baseline FACTS snapshot)

16. **governance-check** - `command: governance`
    - Detailed governance compliance check with violations
    - Cost: medium, Runtime: 1-5s

17. **query-pack** - `command: query-pack`
    - Executes pre-built query packs (scorecards, docs, architecture)
    - Cost: medium, Runtime: 1-5s
    - **Requires**: `--pack` parameter (scorecard, documentation, architecture, security)

---

## 📊 Output Schema Examples

### Violation-Based Output (Most Common)

```json
{
  "violations": [
    {
      "file": "src/module.py",
      "entity": "class:Foo|method:bar",
      "rule": "cyclomatic_complexity",
      "value": 42,
      "severity": "ERROR",
      "message": "Complexity exceeds threshold (limit: 10)"
    }
  ],
  "summary": {
    "total_violations": 97,
    "by_severity": {
      "ERROR": 42,
      "WARNING": 55
    },
    "by_category": {
      "complexity": 15,
      "documentation": 27,
      "error_handling": 8
    }
  },
  "metadata": {
    "facts_file": "FACTS-20251223-180729.parquet",
    "facts_mtime": "2025-12-23T20:07:36.971689",
    "commit_sha": "9b23e0d",
    "generator_version": "0.1.0",
    "file_count": 49,
    "query_timestamp": "2025-12-23T20:28:50.733890"
  }
}
```

### Drift-Based Output (drift-detector)

```json
{
  "breaking_changes": [
    {
      "file": "src/api.py",
      "entity": "function:process",
      "change_type": "signature_modified",
      "old_signature": "process(x: int) -> str",
      "new_signature": "process(x: int, y: str) -> str"
    }
  ],
  "behavioral_changes": [...],
  "documentation_drift": [...],
  "summary": {
    "breaking_changes_count": 3,
    "behavioral_changes_count": 7,
    "documentation_drift_count": 12
  },
  "metadata": { ... }
}
```

---

## 🔧 Customization Points

### When Creating New Simple Agent

**Step 1**: Choose subcommand name
```yaml
command: my-new-check
```

**Step 2**: Set cost/runtime estimates
```yaml
cost: low              # low (most), medium (some), high (rare)
runtime: <1s           # <1s (most), 1-5s (some), >5s (rare)
```

**Step 3**: Document output schema
```yaml
returns:
  violations: [{file, entity, my_specific_field, severity, message}]
  summary: {total_violations, by_category}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
```

**Step 4**: Replace `<COMMAND>` in bash script
```bash
uv run fact-file-query-tool my-new-check --format json | \
    python3 "$(dirname "$0")/../rules/agent_formatter.py"
```

**Step 5**: Add to agent registry in USING_SUB_AGENTS.yaml
```yaml
agent_registry:
  my_category:
    my-new-agent:
      purpose: "Brief description"
      command: "uv run fact-file-query-tool my-new-check --format json"
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ Mistake 1: Adding Custom Logic

**Bad**:
```bash
# DON'T add custom filtering, processing, or interpretation
OUTPUT=$(uv run fact-file-query-tool doc-quality --format json)
CRITICAL=$(echo "$OUTPUT" | jq '.violations[] | select(.severity == "ERROR")')
echo "$CRITICAL"
```

**Good**:
```bash
# DO keep it simple - just execute and pipe
uv run fact-file-query-tool doc-quality --format json | \
    python3 "$(dirname "$0")/../rules/agent_formatter.py"
```

**Why**: Custom logic belongs in `fact-file-query-tool` or `agent_formatter.py`, not agents.

---

### ❌ Mistake 2: Redundant Instructions in Frontmatter

**Bad**:
```markdown
---
name: doc-quality-validator
---

Execute the doc-quality command.

Return raw JSON only. Do not add commentary.
The caller will analyze the results.
```

**Good**:
```markdown
---
name: doc-quality-validator
description: Check docstring quality (Args, Returns, Raises)
command: doc-quality
cost: low
runtime: <1s
---

**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

This agent uses the simple query pattern with command: `doc-quality`
```

**Why**: `agent_formatter.py` handles formatting. Instructions just waste tokens.

---

### ❌ Mistake 3: Missing Error Trap

**Bad**:
```bash
#!/bin/bash
uv run fact-file-query-tool doc-quality --format json | python3 formatter.py
```

**Good**:
```bash
#!/bin/bash
set -Eeuo pipefail
trap 'echo "⛔ Error in $(basename "$0"): line $LINENO" >&2; exit 1' ERR

# ... rest of script
```

**Why**: Without error trap, failures are silent. Users see no error message.

---

### ❌ Mistake 4: Not Checking FACTS.parquet

**Bad**:
```bash
#!/bin/bash
uv run fact-file-query-tool doc-quality --format json | python3 formatter.py
```

**Good**:
```bash
#!/bin/bash
set -Eeuo pipefail
trap 'echo "⛔ Error..." >&2; exit 1' ERR

FACTS="${FACTS_FILE:-src/golden_validator_hybrid/FACTS.parquet}"
[[ -f "$FACTS" ]] || {
    echo "⛔ FACTS.parquet not found: $FACTS" >&2
    echo "   Run: uv run fact-file-query-tool generate" >&2
    exit 1
}

uv run fact-file-query-tool doc-quality --format json | python3 formatter.py
```

**Why**: Clear error message guides user to fix. See [HARD_STOP_CONDITIONS.md](../rules/HARD_STOP_CONDITIONS.md) § HS-001.

---

## 📚 Related Documentation

| Document | Purpose | Key Sections |
|----------|---------|--------------|
| [AGENT_CONTRACT.md](../rules/AGENT_CONTRACT.md) | Agent standards | Metadata schema, Exit codes, Prerequisite verification |
| [USING_SUB_AGENTS.yaml](../rules/USING_SUB_AGENTS.yaml) | Orchestration | TOCTOU protection, Metadata fields, Agent registry |
| [HARD_STOP_CONDITIONS.md](../rules/HARD_STOP_CONDITIONS.md) | Error handling | HS-001 (FACTS missing), Error message format |
| [JSON_PROCESSING_RULES.yaml](../rules/JSON_PROCESSING_RULES.yaml) | JSON standards | jq usage, python3 patterns |

---

## 🎓 Design Rationale

### Why Simple Agents Are 100% Declarative

**Design Principle**: Agents are command executors, not reasoners.

**Benefits**:
1. **Zero token waste** - No prompt engineering, no LLM interpretation
2. **No permission prompts** - `permissionMode: bypassPermissions` works because agents are deterministic
3. **Predictable execution** - Same command always produces same result
4. **Easy to debug** - Can run command manually: `uv run fact-file-query-tool <command> --format json`
5. **Fast** - No LLM overhead, just tool execution

**Implementation Location**:
- **Logic**: In `fact-file-query-tool` (Python, testable, versioned)
- **Formatting**: In `agent_formatter.py` (Python, testable, versioned)
- **Agent**: Just bash glue (5 lines of actual code)

### Why Metadata Is Automatic

**Design Principle**: Don't trust agents to add metadata - tool adds it.

**Why**:
- Agents could forget to add metadata
- Agents could add wrong metadata
- Agents could add stale metadata

**Solution**: `fact-file-query-tool` adds metadata automatically to all outputs. Agents just pass it through.

**Reference**: [AGENT_CONTRACT.md](../rules/AGENT_CONTRACT.md) § Standard Metadata

### Why agent_formatter.py Is Separate

**Design Principle**: Separation of concerns - tool generates data, formatter formats it.

**Benefits**:
1. **Reusable** - All 17 simple agents use same formatter
2. **Testable** - Formatter can be unit tested independently
3. **Maintainable** - Fix formatting once, all agents benefit
4. **Flexible** - Can add new output formats (HTML, Markdown) without touching agents

---

## ✅ Compliance Checklist

**Before marking agent as "simple query agent"**:

- [ ] Agent uses exactly 1 `fact-file-query-tool` command
- [ ] No custom logic (no jq filtering, no conditional execution)
- [ ] Pipes to `agent_formatter.py`
- [ ] Has error trap: `trap 'echo "⛔..." >&2' ERR`
- [ ] Checks FACTS.parquet exists before execution
- [ ] Frontmatter includes `command:` field
- [ ] Frontmatter includes `cost:` and `runtime:` estimates
- [ ] Frontmatter includes `returns:` schema documentation
- [ ] Frontmatter includes `schema_version: 1`
- [ ] Frontmatter references this template: `See: [SIMPLE_QUERY_AGENT.md]`
- [ ] No redundant instructions ("Return raw JSON only", etc.)
- [ ] Uses `tools: Bash`, `model: haiku`, `permissionMode: bypassPermissions`

---

## 📝 Template Instantiation Example

### From Template to Agent: doc-quality-validator

**Step 1**: Frontmatter
```yaml
---
name: doc-quality-validator
description: Check docstring quality (Args, Returns, Raises sections)
command: doc-quality
cost: low
runtime: <1s
requires: []
after: []
returns:
  violations: [{file, entity, missing_sections, severity, message}]
  summary: {total_violations, by_severity}
  metadata: {facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp}
schema_version: 1
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---
```

**Step 2**: Body
```markdown
**Execution**: See [SIMPLE_QUERY_AGENT.md](../templates/SIMPLE_QUERY_AGENT.md)

This agent uses the simple query pattern with command: `doc-quality`

Checks docstring quality by verifying presence of required sections (Args, Returns, Raises) based on function signatures and behavior.

**What it checks**:
- Args section present for functions with parameters
- Returns section present for functions with return values
- Raises section present for functions that raise exceptions

**Severity levels**:
- ERROR: Public function missing required section
- WARNING: Private function missing recommended section
```

**Step 3**: Bash Code Block
```bash
#!/bin/bash
set -Eeuo pipefail

# =============================================================================
# doc-quality-validator
# Purpose: Check docstring quality (Args, Returns, Raises)
# Template: SIMPLE_QUERY_AGENT.md
# =============================================================================

# Error trap (MANDATORY)
trap 'echo "⛔ Error in $(basename "$0"): line $LINENO" >&2; exit 1' ERR

# Prerequisite check (MANDATORY)
FACTS="${FACTS_FILE:-src/golden_validator_hybrid/FACTS.parquet}"
[[ -f "$FACTS" ]] || {
    echo "⛔ FACTS.parquet not found: $FACTS" >&2
    echo "   Run: uv run fact-file-query-tool generate" >&2
    exit 1
}

# Main execution
uv run fact-file-query-tool doc-quality --format json | \
    python3 "$(dirname "$0")/../rules/agent_formatter.py"
```

**Total Lines**: ~25 (down from 45+ in old pattern)
**Token Reduction**: ~56% (no redundant instructions)

---

## 🔗 Quick Reference

### Command Template
```bash
uv run fact-file-query-tool <COMMAND> --format json | \
    python3 "$(dirname "$0")/../rules/agent_formatter.py"
```

### Error Trap Template
```bash
set -Eeuo pipefail
trap 'echo "⛔ Error in $(basename "$0"): line $LINENO" >&2; exit 1' ERR
```

### FACTS Check Template
```bash
FACTS="${FACTS_FILE:-src/golden_validator_hybrid/FACTS.parquet}"
[[ -f "$FACTS" ]] || {
    echo "⛔ FACTS.parquet not found: $FACTS" >&2
    echo "   Run: uv run fact-file-query-tool generate" >&2
    exit 1
}
```

---

## 📊 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-23 | Initial template - 17 agents covered |

---

**Status**: ✅ Active
**Applies To**: 17 of 23 agents
**Last Updated**: 2025-12-23

---

**End of SIMPLE_QUERY_AGENT.md**
