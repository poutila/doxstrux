# Project Rules

This directory contains modular rule definitions for the project. Claude Code automatically loads all `.yaml` files in this directory.

## Overview

The project uses multiple rule systems for AI assistants and development workflows:

### Core Development Rules:
1. **[GOVERNANCE_RULES.yaml](./GOVERNANCE_RULES.yaml)** - Code quality standards + FDP-LITE principles
2. **[FDP_LITE.yaml](./FDP_LITE.yaml)** - Lightweight evidence-based development philosophy
3. **[USING_SUB_AGENTS.yaml](./USING_SUB_AGENTS.yaml)** - Sub-agent orchestration and TOCTOU protection
4. **[USING_FACT_FILE_QUERY_TOOL.yml](./USING_FACT_FILE_QUERY_TOOL.yml)** - How to use `fact-file-query-tool`

### Tool Usage & Environment Rules:
4. **[USING_TOOLS.yaml](./USING_TOOLS.yaml)** - Mandatory workflows for fact-query skill and agents
5. **[CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml](./CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml)** - UV/Python environment safety rules

### AI Assistant Discovery Protocol:
6. **[AI_PACKAGE_DOCUMENTATION.yaml](./AI_PACKAGE_DOCUMENTATION.yaml)** - Auto-discover bundled AI docs in installed packages

### External Reference:
7. **fact-file-query-tool documentation** - fact-file-query-tool reference (if using fact-file-query-tool package)

## Rule Files

### [GOVERNANCE_RULES.yaml](./GOVERNANCE_RULES.yaml)

**Purpose**: Define code quality standards and architectural constraints + FDP-LITE principles

**Scope**: Python code in `src/your_project/` + evidence-based development practices

**Version**: 1.1.0 (Added FDP-LITE principles integration)

**Key Sections**:

1. **Code Quality Rules**:
   - Complexity limits (cyclomatic complexity ≤ 10, lines per function ≤ 50)
   - Documentation requirements (public APIs must have docstrings with Args/Returns/Raises)
   - Type annotation coverage (100% for public APIs)
   - Security constraints (no hardcoded secrets, dangerous calls, shell injection)
   - SOLID principles (SRP, LSP validation)
   - Error handling patterns (no bare except, no silent exceptions)
   - Naming conventions (SCREAMING_SNAKE_CASE for constants, snake_case for functions, PascalCase for classes)

2. **FDP-LITE Principles** (lines 329-821):
   - **Query before claim**: No unverified statements about code
   - **Evidence over intuition**: Trust measurement over memory
   - **Precision over approximation**: Exact counts when trivial to obtain
   - **No probabilistic language**: "verified" not "probably"
   - **Verifiable decisions**: Evidence → Alternatives → Trade-offs → Verification
   - **Copy-paste executable**: Commands work without modification
   - **Assumption vs fact**: Clear labeling (ASSUMPTION: vs VERIFIED:)
   - **Freshness awareness**: Know when evidence is stale

3. **FDP Adoption Path** (3 levels):
   - **Level 1 (Aware)**: 10% overhead, 50% bug reduction
   - **Level 2 (Systematic)**: 25% overhead, 80% bug reduction
   - **Level 3 (Full FDP)**: 50% overhead, 95% bug reduction

4. **Facts Before Files** (decision tree):
   - When to query facts vs read files directly
   - Structural info → facts query
   - Implementation logic → file reading

**Enforcement Tools**:
- `fact-file-query-tool governance` - Check code quality compliance
- `fact-file-query-tool governance-report` - Generate dashboard
- Specialized agents (security-audit, performance-hotspots, solid-srp-validator, etc.)
- Pre-commit hooks (grep for probabilistic language)

**Integration with Other Principles**:
- **YAGNI**: Verify the need before building (grep shows 0 call sites → YAGNI)
- **KISS**: Measure complexity, don't guess (cyclomatic complexity: 24 → refactor)
- **SOLID**: Measure coupling before generalizing (fan_in=15 → tightly coupled)
- **Clean Table**: No unverified claims in delivery (ASSUMPTION → VERIFIED)

**When Applied**:
- Code quality: Before commits, during code review, in CI/CD pipelines
- FDP principles: During planning, architectural decisions, refactoring

### [FDP_LITE.yaml](./FDP_LITE.yaml)

**Purpose**: Lightweight evidence-based development philosophy without full protocol machinery

**Scope**: Architectural decisions, refactoring, planning, design reviews

**Version**: 1.0.0

**Philosophy**: "Query before claim, verify before assume, measure before estimate"

**Core Principles**:
1. **Query Before Claim**: No unverified statements about code ("grep shows 47" not "around 20")
2. **Evidence Over Intuition**: Trust measurement over memory
3. **Precision Over Approximation**: Exact counts when trivial to obtain
4. **No Probabilistic Language**: "verified" not "probably"
5. **Verifiable Decisions**: Evidence → Alternatives → Trade-offs → Verification
6. **Copy-Paste Executable**: Commands work without modification
7. **Assumption vs Fact**: Clear labeling (ASSUMPTION: vs VERIFIED:)
8. **Freshness Awareness**: Know when evidence is stale

**ROI**: Prevents 60-80% of assumption-based bugs with 10-25% overhead

**Relationship to GOVERNANCE_RULES.yaml**: FDP-LITE is embedded in GOVERNANCE_RULES.yaml (lines 329-821). This standalone file provides the philosophical foundation.

**When Applied**: During architectural decisions, refactoring planning, design reviews

### [USING_SUB_AGENTS.yaml](./USING_SUB_AGENTS.yaml)

**Purpose**: Define sub-agent orchestration protocol and TOCTOU protection

**Scope**: Sub-agent usage, metadata validation, freshness verification

**Key Enforcement**:
- All sub-agent outputs MUST include 6 metadata fields (facts_file, facts_mtime, commit_sha, generator_version, file_count, query_timestamp)
- Orchestrators MUST compare metadata.facts_file across results (prevent TOCTOU vulnerabilities)
- Hard stops on stale results (agent_facts != current_facts)
- Complete registry of all 23 agents with purposes and commands

**Cross-References**:
- Enforces metadata documented in all 23 agents in `.claude/agents/`

**When Applied**: Before using any sub-agent results, during evidence block creation, in orchestrator code

### [USING_TOOLS.yaml](./USING_TOOLS.yaml)

**Purpose**: Define WHEN and HOW Claude should use fact-query skill, specialized agents, and governance rules

**Scope**: Mandatory workflows for AI assistants working on this project

**Status**: MANDATORY

**Problem Addressed**: Tools are useless if not used - Claude must proactively use available capabilities

**Key Workflows**:

1. **Query Facts Before Reading Files**:
   - Trigger: Any question about code in `src/your_project/`
   - Decision: Is this in FACTS.parquet? → Use fact-query skill
   - Coverage: 230 fact keys, 99% of analysis needs

2. **Use Specialized Agents Proactively**:
   - 28 specialized agents available (governance, security, performance, SOLID, types)
   - Check agent registry before manual analysis
   - Run governance-report before commits

3. **Read GOVERNANCE_RULES.yaml First**:
   - Don't guess thresholds, read them
   - 831 lines of defined standards
   - Use for compliance checks

**Cross-References**:
- References agents in [USING_SUB_AGENTS.yaml](./USING_SUB_AGENTS.yaml)
- Enforces rules from [GOVERNANCE_RULES.yaml](./GOVERNANCE_RULES.yaml)

**When Applied**: Every time Claude analyzes code, makes decisions, or performs quality checks

### [CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml](./CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml)

**Purpose**: AI assistant safety rules for Python projects using uv

**Scope**: Environment management, dependency installation, Python execution

**Status**: CRITICAL - Never violate these rules

**Key Safety Rules**:

1. **NEVER use system Python - ALWAYS use 'uv run'**:
   - ❌ Forbidden: `python3 script.py`, `python script.py`, `.venv/bin/python`
   - ✅ Required: `uv run python script.py` or `uv run script.py`
   - Why: Prevents version mismatches, missing dependencies, non-reproducible environments

2. **ALWAYS install with uv, NEVER with pip**:
   - ❌ Forbidden: `pip install`, `.venv/bin/pip install`
   - ✅ Required: `uv add <package>` or `uv pip install`
   - Why: Maintains lockfile consistency, ensures reproducibility

3. **ALWAYS verify before assuming**:
   - Check `pyproject.toml` for dependencies
   - Use `uv tree` to verify package installation
   - Never assume system packages are available

**Benefits**:
- Reproducible environments across machines
- Locked dependencies (no version drift)
- Isolated from system Python pollution

**When Applied**: Every Python command execution, dependency installation, environment check


**Purpose**: Complete reference for `fact-file-query-tool` (bundled with package)

**Status**: ✅ **Active** - Replaced TOOL_REFERENCE.yaml (deprecated 2025-12-23)

**Scope**: CLI syntax, parameters, workflows, troubleshooting, JSON processing

**Contains**:
- 33 command definitions (syntax, category, purpose, parameters, time, examples)
- Quick start paths (4 common scenarios: orientation, refactoring, security, evidence)
- Complete workflows (entities → manifest → query)
- Troubleshooting decision trees (error recovery)
- JSON processing rules (jq vs python, forbidden patterns)
- Metadata (tool version, facts schema, TOCTOU protection)

**Benefits**:
- Bundled with tool (distributed with package)
- Version-controlled with code (impossible to get out of sync)
- Accessible at runtime (enables CLI features)
- Single source of truth (no duplication)

**Used By**:
- All 23 agents (via templates or direct reference)
- Future CLI features (--help-full, docs command)

**When Applied**: Command validation, tool usage, documentation generation, runtime help

## Relationships

```
GOVERNANCE_RULES.yaml (./GOVERNANCE_RULES.yaml) [v1.1.0]
  ├─→ defines quality thresholds (code quality section)
  ├─→ embeds FDP-LITE principles (lines 329-821)
  ├─→ provides 3-level adoption path (10% → 25% → 50% overhead)
  ├─→ integrates with YAGNI, KISS, SOLID, Clean Table
  ├─→ includes Facts Before Files decision tree
  └─→ enforced by 23 agents (listed in USING_SUB_AGENTS.yaml)

FDP_LITE.yaml (./FDP_LITE.yaml) [v1.0.0]
  ├─→ provides philosophical foundation for evidence-based development
  ├─→ embedded in GOVERNANCE_RULES.yaml (lines 329-821)
  ├─→ standalone reference for core principles
  └─→ guides architectural decisions and refactoring

USING_SUB_AGENTS.yaml (./USING_SUB_AGENTS.yaml)
  ├─→ defines metadata schema (6 required fields)
  ├─→ lists all 23 agents + purposes
  ├─→ specifies TOCTOU protection (3 hard stops)
  ├─→ uses fact-file-query-tool documentation JSON processing rules (jq for metadata extraction)
  └─→ enforces orchestrator verification protocol

USING_TOOLS.yaml (./USING_TOOLS.yaml)
  ├─→ defines mandatory workflows for AI assistants
  ├─→ enforces fact-query skill usage (before reading files)
  ├─→ requires proactive agent usage (28 specialized agents)
  └─→ references GOVERNANCE_RULES.yaml and USING_SUB_AGENTS.yaml

CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml (./CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml)
  ├─→ critical safety rules for uv/Python environments
  ├─→ forbids system Python usage (requires 'uv run')
  ├─→ forbids pip usage (requires 'uv add')
  └─→ ensures reproducible environments

  ├─→ defines 33 commands + workflows + troubleshooting
  ├─→ referenced by USING_SUB_AGENTS.yaml (agent commands)
  ├─→ referenced by USING_TOOLS.yaml (fact-query skill)
  ├─→ includes JSON processing rules (§1148-1228)
  ├─→ bundled with tool package
  └─→ used by all 23 agents (via templates)
```

## Validation Feedback Loops

### GOVERNANCE ↔ fact-file-query-tool documentation
- **Enforcement**: Agents use fact-file-query-tool documentation to determine valid query syntax (33 commands)
- **Stop Condition**: If agent needs command not in SSOT → extend tool or use Polars fallback

### USING_SUB_AGENTS ↔ Agents
- **Loop**: [USING_SUB_AGENTS.yaml](./USING_SUB_AGENTS.yaml) defines metadata schema → all 23 agents must comply
- **Enforcement**: Every agent output includes 6 metadata fields + orchestrator verification section in docs
- **Stop Condition**: If agent output lacks metadata → ERROR (cannot verify freshness, unsafe to use)

### USING_TOOLS ↔ Workflow Enforcement
- **Loop**: [USING_TOOLS.yaml](./USING_TOOLS.yaml) defines workflows → Claude must follow before file operations
- **Enforcement**: Query facts before reading files, use agents before manual analysis
- **Stop Condition**: If Claude skips fact-query when info is available → inefficient workflow

### UV_RULES ↔ Environment Safety
- **Loop**: [CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml](./CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml) defines safety rules → all Python execution must comply
- **Enforcement**: Never use system Python or pip directly
- **Stop Condition**: If system Python used → non-reproducible environment, version mismatches

## Usage for AI Assistants

When working with this codebase, Claude Code should:

1. **Before ANY work** ([CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml](./CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml) - CRITICAL):
   - **NEVER use system Python**: Always use `uv run python` (not `python3` or `python`)
   - **NEVER use pip**: Always use `uv add` or `uv pip install`
   - **ALWAYS verify**: Check `pyproject.toml` before assuming packages exist
   - **Reproducibility first**: Prevent version drift, maintain lockfile

2. **During development** ([GOVERNANCE_RULES.yaml](./GOVERNANCE_RULES.yaml) + [FDP_LITE.yaml](./FDP_LITE.yaml)):
   - **Query before claim**: No unverified statements ("around 20" → "grep shows 47")
   - **No probabilistic language**: Replace "probably" with measurements
   - **Precision over approximation**: Use exact counts when trivial
   - **Verifiable decisions**: Evidence → Alternatives → Trade-offs → Verification
   - **Facts before files**: Query FACTS.parquet for structural info, read files for implementation details

3. **When analyzing code** ([USING_TOOLS.yaml](./USING_TOOLS.yaml) - MANDATORY):
   - **Query facts FIRST**: Before reading Python files, check if info is in FACTS.parquet
   - **Use specialized agents**: Check 28 agent registry before manual analysis
   - **Read governance rules**: Don't guess thresholds, read GOVERNANCE_RULES.yaml
   - **Proactive tool usage**: Tools are useless if not used

4. **When using sub-agents** ([USING_SUB_AGENTS.yaml](./USING_SUB_AGENTS.yaml)):
   - Run agent to get JSON output with metadata
   - Extract `metadata.facts_file` from output
   - Verify `agent_facts == current_facts` (TOCTOU protection)
   - Only use results after successful verification
   - Include metadata in evidence blocks

5. **During code review** ([GOVERNANCE_RULES.yaml](./GOVERNANCE_RULES.yaml)):
   - Check complexity limits before writing functions
   - Ensure type annotations on all public APIs
   - Run `fact-file-query-tool governance` before commits

   - Use tool commands instead of manual file reading
   - Follow 3-step workflow: entities → manifest → query
   - Reference fact-file-query-tool documentation for correct syntax (33 commands)

7. **When processing JSON** (fact-file-query-tool documentation § JSON Processing):
   - ALWAYS use `jq` for JSON processing (preferred)
   - If `jq` unavailable, use `uv run python -m json.tool` (alternative)
   - NEVER use bare `python3` or `python` (blocked by hooks)
   - All commands MUST use `uv run` prefix for environment isolation

## File Locations

All rule files are in `.claude/rules/`:

```
.claude/rules/
├── RULES.md                                      # This file (overview and cross-references)
├── GOVERNANCE_RULES.yaml                         # Code quality + FDP-LITE (1296 lines) [v1.1.0]
├── FDP_LITE.yaml                                 # Evidence-based philosophy (v1.0.0)
├── USING_SUB_AGENTS.yaml                         # Sub-agent orchestration (750+ lines)
├── USING_TOOLS.yaml                              # Mandatory tool workflows
└── CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml         # UV/Python safety rules (CRITICAL)
```

**fact-file-query-tool documentation** (bundled with package):
  - 33 commands, workflows, troubleshooting, JSON processing rules

**Quick Links**:
- [GOVERNANCE_RULES.yaml](./GOVERNANCE_RULES.yaml) (code quality + FDP-LITE)
- [FDP_LITE.yaml](./FDP_LITE.yaml) (evidence-based philosophy)
- [USING_SUB_AGENTS.yaml](./USING_SUB_AGENTS.yaml) (orchestration)
- [USING_TOOLS.yaml](./USING_TOOLS.yaml) (mandatory workflows)
- [CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml](./CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml) (UV safety)

## Version Information

**Active Rules**:
- **[GOVERNANCE_RULES.yaml](./GOVERNANCE_RULES.yaml)**: v1.1.0 (Updated: 2025-12-24) - Code quality + FDP-LITE
- **[FDP_LITE.yaml](./FDP_LITE.yaml)**: v1.0.0 - Evidence-based development philosophy
- **[USING_SUB_AGENTS.yaml](./USING_SUB_AGENTS.yaml)**: v1.0.0 (Created: 2025-12-23) - Orchestration + TOCTOU
- **[USING_TOOLS.yaml](./USING_TOOLS.yaml)**: Active (Updated: 2025-12-21) - Mandatory tool workflows
- **[CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml](./CLAUDE_PROJECT_AGNOSTIC_UV_RULES.yaml)**: Active (Updated: 2025-12-26) - UV/Python safety (CRITICAL)

**Deprecated** (content migrated):
- ~~JSON_PROCESSING_RULES.yaml~~ → fact-file-query-tool documentation § JSON Processing (lines 1148-1228)
- ~~TOOL_REFERENCE.yaml~~ → fact-file-query-tool documentation (bundled with package)

**Changes in v1.1.0**:
- ✅ Embedded FDP-LITE principles into GOVERNANCE_RULES.yaml (465+ lines added)
- ✅ Added 3-level adoption path (10% → 25% → 50% overhead)
- ✅ Integrated with YAGNI, KISS, SOLID, Clean Table
- ✅ Added "Facts Before Files" decision tree
- ✅ Provided pre-commit hooks for probabilistic language detection

---

**Last Updated**: 2025-12-26
**Maintained By**: golden-docs project
**Status**: Production-ready, all rules enforced
**Total Rule Files**: 6 (5 in .claude/rules/ + 1 bundled with package)
