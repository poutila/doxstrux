# Agent Dependencies Documentation

**Version**: 1.0.0
**Date**: 2025-12-23
**Last Updated**: 2025-12-23
**Status**: ✅ Complete (Phase 4 of Agent Refactoring)

## Overview

This document maps all dependencies in the golden-docs agent system:
- 23 total agents (17 simple, 4 orchestrator, 2 aggregator)
- 3 templates (SIMPLE_QUERY_AGENT.md, ORCHESTRATOR_AGENT.md, AGGREGATOR_AGENT.md)
- Self-documenting via `--help` (zero static SSOT dependencies)

## Agent Classification

### Simple Query Agents (17)

Execute single fact-file-query-tool command, return JSON. Inherit from SIMPLE_QUERY_AGENT.md template.

| Agent | Command | Tools | Purpose |
|-------|---------|-------|---------|
| doc-quality-validator.md | `doc-quality` | Bash | Check docstring quality (Args, Returns, Raises) |
| drift-detector.md | `drift` | Bash | Detect FACTS drift between snapshots |
| error-pattern-audit.md | `error-patterns` | Bash | Detect error handling anti-patterns |
| governance-check.md | `governance` | Bash | Check GOVERNANCE_RULES.yaml compliance |
| hardcoding-detector.md | `hardcoding` | Bash | Detect hardcoded paths, URLs, credentials |
| import-audit.md | `imports` | Bash | Check import style violations |
| logging-audit.md | `logging` | Bash | Detect logging anti-patterns (print() in production) |
| magic-number-detector.md | `magic-numbers` | Bash | Detect magic numbers needing named constants |
| modern-syntax-validator.md | `modern-syntax` | Bash | Enforce modern type syntax (PEP 604, PEP 585) |
| module-purity-check.md | `module-purity` | Bash | Detect import-time side effects |
| mutable-defaults-detector.md | `mutable-defaults` | Bash | Detect mutable default arguments |
| naming-validator.md | `naming` | Bash | Validate naming conventions |
| security-audit.md | `security` | Bash | Comprehensive security audit |
| solid-lsp-validator.md | `solid-lsp` | Bash | Detect SOLID LSP violations |
| solid-srp-validator.md | `solid-srp` | Bash | Detect SOLID SRP violations (god classes) |
| type-coverage-enforcer.md | `type-coverage` | Bash | Enforce type coverage requirements |
| weak-test-detector.md | `weak-tests` | Bash | Detect weak tests (no assertions) |

### Orchestrator Agents (4)

Perform complex analysis or aggregation. Inherit from ORCHESTRATOR_AGENT.md template.

| Agent | Command | Tools | Purpose |
|-------|---------|-------|---------|
| architecture-map.md | `architecture` | Bash, Read | Generate architecture overview (clusters, layers, coupling) |
| blast-radius.md | `blast-radius` | Bash, Read | Analyze blast radius for incident response |
| performance-hotspots.md | `performance` | Bash, Read | Find performance hotspots via static analysis |
| test-gap-analysis.md | `test-gaps` | Bash, Read | Identify where tests are most needed (risk-based) |

### Aggregator Agents (2)

Bundle multiple queries or provide workflow automation. Inherit from AGGREGATOR_AGENT.md template.

| Agent | Command(s) | Tools | Purpose |
|-------|------------|-------|---------|
| query-pack.md | `query-pack`, `entities`, `query` | Bash, Read | Execute pre-built query packs for common workflows |
| governance-report.md | `governance` + formatting | Bash, Read | Generate comprehensive governance dashboard |

## Template Dependencies

### SIMPLE_QUERY_AGENT.md (17 agents)

**Template location**: `.claude/templates/SIMPLE_QUERY_AGENT.md`

**Inheriting agents**:
- doc-quality-validator.md
- drift-detector.md
- error-pattern-audit.md
- governance-check.md
- hardcoding-detector.md
- import-audit.md
- logging-audit.md
- magic-number-detector.md
- modern-syntax-validator.md
- module-purity-check.md
- mutable-defaults-detector.md
- naming-validator.md
- security-audit.md
- solid-lsp-validator.md
- solid-srp-validator.md
- type-coverage-enforcer.md
- weak-test-detector.md

**Template provides**:
- Self-documenting pattern via `--help`
- Standard command execution pattern with error handling
- JSON output formatting via agent_formatter.py
- Hard stop trap (set -Eeuo pipefail)

### ORCHESTRATOR_AGENT.md (4 agents)

**Template location**: `.claude/templates/ORCHESTRATOR_AGENT.md`

**Inheriting agents**:
- architecture-map.md
- blast-radius.md
- performance-hotspots.md
- test-gap-analysis.md

**Template provides**:
- Multi-step workflow guidance
- Output interpretation sections
- Risk scoring methodologies
- Self-documenting pattern via `--help`

### AGGREGATOR_AGENT.md (2 agents)

**Template location**: `.claude/templates/AGGREGATOR_AGENT.md`

**Inheriting agents**:
- query-pack.md
- governance-report.md

**Template provides**:
- Multi-command orchestration patterns
- Workflow automation guidance
- Result aggregation strategies

## Tool Dependencies

### Bash (23 agents - all)

**Purpose**: Execute fact-file-query-tool commands
**Usage pattern**:
```bash
uv run fact-file-query-tool <command> --format json | python3 agent_formatter.py
```

**Required for**:
- Command execution
- Output piping to formatter
- Error handling (set -Eeuo pipefail)
- Prerequisite validation

### Read (5 agents)

**Purpose**: Read documentation files for context
**Usage pattern**:
```markdown
See: [GOVERNANCE_RULES.yaml](...) for complete rules
```

**Agents using Read**:
- architecture-map.md
- blast-radius.md
- performance-hotspots.md
- test-gap-analysis.md
- query-pack.md

**Why needed**: These agents provide interpretation guidance that references external documentation.

## Data Dependencies

### FACTS.parquet (all 23 agents)

**Location**: `src/golden_validator_hybrid/FACTS.parquet`
**Purpose**: Primary fact database for all queries
**Format**: Parquet (columnar, compressed)

**Schema**: 230+ fact keys including:
- Entity metadata (name, qualname, file, line_start, line_end)
- Signatures (params, return_type, decorators)
- Complexity metrics (complexity, loc, params)
- Dependencies (calls, imports, fan_in, fan_out)
- Side effects (self_attrs_written, side_effect_kinds)
- Security (dangerous_calls, command_execution)

**Used by**: All agents query FACTS.parquet via fact-file-query-tool

### GOVERNANCE_RULES.yaml (20+ governance agents)

**Location**: `.claude/rules/GOVERNANCE_RULES.yaml`
**Purpose**: Quality thresholds and validation rules
**Size**: 831 lines

**Sections used by agents**:
- `complexity_limits`: Used by governance-check, solid-srp-validator
- `SOLID_principles`: Used by solid-srp-validator, solid-lsp-validator
- `error_handling`: Used by error-pattern-audit
- `logging`: Used by logging-audit
- `no_hardcoding`: Used by hardcoding-detector
- `no_magic_numbers`: Used by magic-number-detector
- `naming_conventions`: Used by naming-validator
- `modern_syntax`: Used by modern-syntax-validator
- `import_governance`: Used by import-audit
- `documentation`: Used by doc-quality-validator
- `no_weak_tests`: Used by weak-test-detector
- `type_checking`: Used by type-coverage-enforcer
- `module_import_purity`: Used by module-purity-check
- `security`: Used by security-audit

### agent_formatter.py (23 agents - all)

**Location**: `.claude/rules/agent_formatter.py`
**Purpose**: Transform raw JSON into caller-optimized summaries
**Size**: ~15KB

**Functionality**:
- Reads JSON from stdin
- Reads AGENT_SUMMARY_FORMAT.yaml for formatting rules
- Outputs formatted summaries with badges (✅ ⚠️ ❌)
- Provides risk scores and prioritized recommendations

**Used by**: All agents pipe JSON output to agent_formatter.py

## Command Dependencies

### fact-file-query-tool Commands

All agents depend on fact-file-query-tool binary being available via `uv run`.

**Command mapping** (agent → command):

```
architecture-map.md         → architecture
blast-radius.md             → blast-radius
doc-quality-validator.md    → doc-quality
drift-detector.md           → drift
error-pattern-audit.md      → error-patterns
governance-check.md         → governance
governance-report.md        → governance (+ formatting)
hardcoding-detector.md      → hardcoding
import-audit.md             → imports
logging-audit.md            → logging
magic-number-detector.md    → magic-numbers
modern-syntax-validator.md  → modern-syntax
module-purity-check.md      → module-purity
mutable-defaults-detector.md→ mutable-defaults
naming-validator.md         → naming
performance-hotspots.md     → performance
query-pack.md               → query-pack, entities, query, get-schema
security-audit.md           → security
solid-lsp-validator.md      → solid-lsp
solid-srp-validator.md      → solid-srp
test-gap-analysis.md        → test-gaps
type-coverage-enforcer.md   → type-coverage
weak-test-detector.md       → weak-tests
```

### Self-Documenting via --help

**All agents use runtime help discovery** instead of static documentation:

```bash
# Discover all commands
uv run fact-file-query-tool --help

# Get command-specific syntax
uv run fact-file-query-tool <command> --help
```

**Benefits**:
- Zero static SSOT dependencies (was 44KB × 23 = 1,012 KB overhead)
- Agents stay synchronized with tool evolution
- No documentation drift
- Reduced agent file sizes (templates don't carry tool docs)

## External Dependencies (None)

**Historical note**: During Phase 3 refactoring (2025-12-23), we removed all static SSOT dependencies:
- ~~TOOL_REFERENCE.yaml~~ (deprecated, 991 lines) → agents use `--help` instead
- ~~JSON_PROCESSING_RULES.yaml~~ (deprecated, 305 lines) → JSON handling baked into tool
- ~~FACT_FILE_QUERY_TOOL_REFERENCE_ENRICHED.yaml~~ (44KB) → no longer referenced

All agents now achieve **zero external documentation dependencies** through self-discovery.

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│  Templates (3)                                               │
│  ┌────────────────────┐  ┌─────────────────┐  ┌───────────┐│
│  │ SIMPLE_QUERY_AGENT│  │ ORCHESTRATOR_   │  │ AGGREGATOR││
│  │     (17 agents)    │  │   (4 agents)    │  │ (2 agents)││
│  └────────────────────┘  └─────────────────┘  └───────────┘│
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  All Agents (23)                                             │
│  - Use Bash tool to execute commands                         │
│  - Query fact-file-query-tool with --help for syntax       │
│  - Pipe JSON to agent_formatter.py for pretty output        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  fact-file-query-tool (33 commands)                          │
│  - Queries FACTS.parquet (230+ fact keys)                   │
│  - Enforces GOVERNANCE_RULES.yaml thresholds                │
│  - Returns JSON or summary format                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Sources                                                │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │FACTS.parquet │  │GOVERNANCE_       │  │agent_         │ │
│  │ (all agents) │  │RULES.yaml        │  │formatter.py   │ │
│  │              │  │ (20+ agents)     │  │ (all agents)  │ │
│  └──────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Adding New Agents

### For Simple Query Agents

1. **Choose template**: SIMPLE_QUERY_AGENT.md
2. **Define command**: Pick from `uv run fact-file-query-tool --help`
3. **Set tools**: `Bash` (minimum)
4. **Add metadata**: Name, description, color, model
5. **Document usage**: When to use, example output

**Example**:
```yaml
---
name: my-new-validator
description: Detects my-specific-pattern violations
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---

Execute this command and return JSON to caller:

```bash
uv run fact-file-query-tool my-command --format json | python3 "$(dirname "$0")/../rules/agent_formatter.py"
```

**Output**: Return raw JSON only. Caller will analyze.
```

### For Orchestrator Agents

1. **Choose template**: ORCHESTRATOR_AGENT.md
2. **Define workflow**: Multi-step or complex analysis
3. **Set tools**: `Bash, Read`
4. **Add sections**:
   - When to Use
   - Command Guidelines (MANDATORY)
   - How to Analyze
   - Output Interpretation
   - Risk Scoring (if applicable)

See architecture-map.md, blast-radius.md, performance-hotspots.md, test-gap-analysis.md for examples.

### For Aggregator Agents

1. **Choose template**: AGGREGATOR_AGENT.md
2. **Define workflow**: Multiple command orchestration
3. **Set tools**: `Bash, Read`
4. **Document**:
   - Multi-command sequences
   - Result aggregation strategy
   - Workflow automation patterns

See query-pack.md, governance-report.md for examples.

## Maintenance

### When fact-file-query-tool Changes

**No agent updates required** - agents discover syntax via `--help`.

**Only update if**:
- Command is renamed (update agent's command string)
- Command is removed (deprecate agent or switch command)
- New command is added (create new agent if needed)

### When GOVERNANCE_RULES.yaml Changes

**No agent updates required** - governance rules are read by fact-file-query-tool at runtime.

**Agents affected automatically**:
- All governance agents (20+) immediately use new thresholds
- No template updates needed
- No agent file modifications needed

### When Templates Change

**Update propagates automatically** to all inheriting agents (template inheritance model).

**Affected agents**:
- SIMPLE_QUERY_AGENT.md changes → 17 agents inherit
- ORCHESTRATOR_AGENT.md changes → 4 agents inherit
- AGGREGATOR_AGENT.md changes → 2 agents inherit

## Verification Commands

```bash
# Count agents by type
grep -l "SIMPLE_QUERY_AGENT.md" *.md | wc -l        # Should be 17
grep -l "ORCHESTRATOR_AGENT.md" *.md | wc -l        # Should be 4
grep -l "AGGREGATOR_AGENT.md" *.md | wc -l          # Should be 2

# Verify all use --help pattern
grep -L "uv run fact-file-query-tool --help" *.md   # Should be empty

# Check for stale SSOT references
grep -r "FACT_FILE_QUERY_TOOL_REFERENCE_ENRICHED" . # Should be empty (except archive/)

# Verify tool usage
grep "^tools:" *.md | sort | uniq -c                # Should show Bash (23) and Bash, Read (5)
```

## Change Log

### 2025-12-23 (Phase 3 & 4 Refactoring)

- ✅ Removed all SSOT references (1,012 KB context savings)
- ✅ Refactored 4 orchestrator agents with comprehensive Command Guidelines
- ✅ Established self-documenting pattern via `--help`
- ✅ Created AGENT_DEPENDENCIES.md (this file)
- ✅ Deprecated TOOL_REFERENCE.yaml and JSON_PROCESSING_RULES.yaml

### 2025-12-22 (Phase 2 Refactoring)

- ✅ Refactored 17 simple agents to use SIMPLE_QUERY_AGENT.md template
- ✅ Standardized agent structure and naming conventions

---

**Status**: ✅ **Complete** - All dependencies documented, zero external SSOT dependencies, self-sufficient agent system.
