---
speksi:
  spec_id: AI_TASK_LIST_SPEC
  version: 1.9.0
  status: DRAFT
  tier: STANDARD
  layers:
    META: "§M"
    ARCHITECTURE: "§A"
    DEFINITIONS: "§D"
    RULES: "§R"
    VALIDATION: "§V"
    CHANGELOG: "§C"
    GLOSSARY: "§G"
---

# AI Task List Specification (SPEKSI Format)

## §M META

### §M.1 Purpose and Scope

This document is a SPEKSI-formatted specification for an “AI Task List” Markdown artifact. It defines the structure and linter-enforceable rules for producing task lists that are (a) reality-grounded, (b) minimally ambiguous for execution, and (c) mechanically verifiable.

Scope:

- Applies to: a single Markdown file (either a template, a plan, or an instantiated task list).
- Primary validator: a deterministic linter implementing this spec.
- Out of scope: feasibility, correctness of product requirements, and human judgment of semantics beyond what rules can capture.

### §M.2 Design Goals (Informative)

The framework is designed to support the following outcomes, summarized from the project goal definition:

- No drift between input prose and produced task list.
- Reality-first grounding in the actual repository state.
- Deterministic validation against a specification via a linter.
- Governance baked in (TDD, no weak tests, uv enforcement, clean table, import hygiene, rg discipline).
- Reduced iteration loops and minimized AI guessing via explicit constraints and evidence requirements.

### §M.3 Normativity and SSOT Policy

R-ATL-000: Spec–Linter Divergence Resolution
Rule: If this spec and the linter diverge, the linter is updated to match the spec.
Rationale: Preserves SSOT and prevents "implementation drift" from silently redefining the contract.

## §A ARCHITECTURE

### §A.1 Artifact Lifecycle

The task list artifact progresses through three modes:

- template: scaffolding mode; placeholders are allowed.
- plan: execution-ready mode; commands are real, evidence may be placeholder.
- instantiated: execution-complete mode; placeholders are forbidden; evidence is non-empty where required.

### §A.2 Enforcement Model

The linter enforces:

- Structural anchors (required headings and required blocks).
- Rule-driven invariants (IDs, unique tasks, canonical path arrays).
- Execution hygiene (runner prefix, uv constraints, $-prefixed command detection).
- Evidence presence constraints in instantiated mode.
- Optional evidence header capture requirements when invoked with a strict flag.

## §D DEFINITIONS

### §D.1 Terms

Mode
A front-matter field controlling placeholder tolerance: template, plan, or instantiated.

Task ID
A string in the form N.M where N is the phase number and M is the task number.

Canonical path array
A bash array in the form TASK_<N>_<M>_PATHS=(<quoted paths>) attached to Task N.M.

Runner
The declared toolchain context for command execution (e.g., uv).

Runner prefix
The mandatory prefix for tool invocations managed by the runner (e.g., “uv run”).

Search tool
A front-matter field declaring the permitted text search command in code blocks: rg or grep.

Placeholder
The only recognized placeholder token format: [[PH:NAME]] where NAME matches [A-Z0-9_]+.

### §D.2 Conventions

- “Command lines” are lines that start with “$” inside fenced code blocks in the task list artifact. The linter uses this to distinguish commands from pasted output.
- “Evidence blocks” are fenced code blocks in which command lines and captured output (or placeholders in permitted modes) appear.

Note: The SPEKSI Kernel disallows Markdown fences inside specifications. This document contains no fenced blocks; when describing fenced blocks as part of the target artifact, this spec describes their required content and semantics without embedding fences.

## §R RULES

### §R.1 Front Matter and Modes

R-ATL-001: Front matter required
Rule: The task list artifact starts with YAML front matter containing:

    ai_task_list:
      schema_version: "<VERSION.yaml version>"
      mode: "template" | "plan" | "instantiated"
      runner: "<string>"
      runner_prefix: "<string>"
      search_tool: "rg" | "grep"

R-ATL-002: Mode semantics
Rule: Placeholder behavior by mode:

- template: [[PH:...]] placeholders may appear.
- plan: commands must be real; evidence/output placeholders may appear; runner/search_tool/import-hygiene rules apply.
- instantiated: [[PH:...]] placeholders must not appear anywhere.

R-ATL-003: Placeholder syntax
Rule: Only [[PH:NAME]] placeholders are recognized, NAME matching [A-Z0-9_]+.

### §R.2 Required Top-Level Structure Anchors

R-ATL-010: Required headings
Rule: The task list artifact contains these headings with exact text and case:

    ## Non-negotiable Invariants
    ## Placeholder Protocol
    ## Source of Truth Hierarchy
    ## Baseline Snapshot (capture before any work)
    ## Phase 0 — Baseline Reality
    ## Drift Ledger (append-only)
    ## Phase Unlock Artifact
    ## Global Clean Table Scan
    ## STOP — Phase Gate

R-ATL-NEW-02: Prose Coverage Mapping (plan/instantiated)
Rule: If mode is plan or instantiated, include a "## Prose Coverage Mapping" section containing a Markdown table with at least a header row and one data row.

### §R.3 Baseline Snapshot (Reality-First)

R-ATL-020: Baseline Snapshot table required
Rule: Under “## Baseline Snapshot (capture before any work)”, include a Markdown table containing these rows:
- Date
- Repo
- Branch
- Commit
- Runner
- Runtime

R-ATL-021: Baseline Evidence block required
Rule: Baseline Snapshot includes an Evidence block with commands and output placeholders (template/plan) or real pasted output (instantiated).

R-ATL-021B: Baseline tests evidence required (all modes; stricter in instantiated)
Rule: Baseline Snapshot includes a “Baseline tests” evidence block in all modes.
- In instantiated mode:
  - At least one “$” command is present.
  - Each “$” command has at least one non-empty output line following it.
  - The block is non-empty overall.
- In template/plan mode: placeholders may be used, but the fenced block exists and is non-empty.

R-ATL-022: Instantiated mode forbids placeholders
Rule: If mode is instantiated, the linter fails if any literal [[PH:...]] tokens remain anywhere in the file.

R-ATL-023: Non-empty evidence required (instantiated mode)
Rule: In instantiated mode, required evidence slots contain real output lines (metadata-only headers do not count). This applies to:
1) Baseline Snapshot evidence.
2) Per-task STOP evidence (non-Phase-0): includes both labeled sections:
   - “# Test run output:” with real output lines.
   - “# Symbol/precondition check output:” with real output lines.
3) Global Clean Table evidence.

R-ATL-024: Captured evidence headers (opt-in)
Rule: When invoked with “--require-captured-evidence”, evidence blocks include:
- “# cmd: <exact command executed>”
- “# exit: <exit code as integer>”

Additional enforcement under the flag:
- STOP evidence sections and Global Clean Table evidence require exit code 0.
- Baseline evidence records exit code, which may be non-zero.

### §R.4 Phase and Task Syntax

R-ATL-030: Phase heading format
Rule: Phase headings match the regex:
- ^## Phase (\d+) — (.+)$
and Phase 0 exists exactly as:
- ## Phase 0 — Baseline Reality

R-ATL-NEW-01: Task heading format and uniqueness
Rule: Task headings match:
- ^### Task (\d+)\.(\d+) — (.+)$
and Task IDs are unique across the document.

R-ATL-032: Task → Paths canonical array required
Rule: Every task contains a “**Paths**:” block including a bash array named:
- TASK_<N>_<M>_PATHS=(<quoted paths>)
with at least one quoted path.

R-ATL-033: Naming rule stated once
Rule: The document includes the explicit naming rule linking Task ID N.M to array TASK_N_M_PATHS exactly once.

R-ATL-090: Task status value is singular and constrained
Rule: Each task contains:
- **Status**: <status>
where <status> is exactly one of:
- 📋 PLANNED
- ⏳ IN PROGRESS
- ✅ COMPLETE
- ❌ BLOCKED

R-ATL-091: Completed tasks require checked checklists (instantiated mode)
Rule: If a task is ✅ COMPLETE and mode is instantiated, all No Weak Tests and Clean Table checklist items in its STOP block are checked ([x]).

### §R.5 TDD and Task Gates

R-ATL-040: TDD steps required per task
Rule: Each non-Phase-0 task includes the headings:
- ### TDD Step 1 — Write test (RED)
- ### TDD Step 2 — Implement (minimal)
- ### TDD Step 3 — Verify (GREEN)

R-ATL-041: STOP block required per non-Phase-0 task
Rule: Each non-Phase-0 task includes:
- ### STOP — Clean Table
and within that STOP section:
- Evidence slots (template/plan) or fenced evidence with real output (instantiated), including both:
  - [[PH:PASTE_TEST_OUTPUT]]
  - [[PH:PASTE_PRECONDITION_OUTPUT]]
- No Weak Tests checklist containing exactly these four items (whitespace-insensitive semantic match):
  - Stub/no-op would FAIL this test?
  - Asserts semantics, not just presence?
  - Has negative case for critical behavior?
  - Is NOT import-only/smoke/existence-only/exit-code-only?
- Clean Table checklist containing at minimum these five items (whitespace-insensitive semantic match):
  - Tests pass (not skipped)
  - Full suite passes
  - No placeholders remain
  - Paths exist
  - Drift ledger updated (if needed)

R-ATL-042: Clean Table checklist enforcement
Rule: The linter verifies presence of the five Clean Table checklist items listed in R-ATL-041.

R-ATL-D2: Preconditions symbol-check required for non-Phase-0 tasks
Rule: Non-Phase-0 tasks include a Preconditions block containing a fenced code block with:
- template mode: [[PH:SYMBOL_CHECK_COMMAND]]
- instantiated mode: an rg or grep command (comment lines excluded from check)

### §R.6 Phase Unlock Artifact and Phase Gate

R-ATL-050: Phase Unlock Artifact section required
Rule: The task list artifact includes a “## Phase Unlock Artifact” section that:
- shows generation of a .phase-N.complete.json artifact (template: pattern; instantiated: actual “$ cat > .phase-N.complete.json” command line)
- includes a placeholder rejection scan (instantiated: actual “$ rg” command line)
- rejects “comment compliance” (command lines must be real, not comments; trivial echo is insufficient)

R-ATL-051: Phase gate required and references unlock artifacts
Rule: The "## STOP — Phase Gate" section includes checklist items requiring:
- .phase-N.complete.json exists
- Global Clean Table scan passes
- Phase tests pass
- Drift ledger current

### §R.7 Global Clean Table Scan

R-ATL-060: Global scan hook required
Rule: Under “## Global Clean Table Scan” include:
- a command placeholder in template mode, or an actual command in instantiated mode
- an evidence paste slot [[PH:PASTE_CLEAN_TABLE_OUTPUT]]

R-ATL-061: Instantiated scan evidence required
Rule: In instantiated mode, [[PH:PASTE_CLEAN_TABLE_OUTPUT]] must not remain.

R-ATL-062: Recommended Clean Table patterns (informative)
Guideline: Typical checks include scanning for TODO/FIXME/XXX and scanning for [[PH:...]] tokens.

R-ATL-063: Import hygiene enforcement (Python; runner=uv; instantiated mode)
Rule: When runner is uv and mode is instantiated, Global Clean Table Scan contains actual "$" command lines (not comments) for:
- multi-dot relative import check (pattern: from ..)
- wildcard import check (pattern: import *)

### §R.8 Runner and $ Discipline

R-ATL-070: Runner metadata required
Rule: runner and runner_prefix are non-empty strings (or runner_prefix explicitly empty where intended).

R-ATL-071: Runner consistency (instantiated mode)
Rule: When runner_prefix is non-empty in instantiated mode, tool invocations inside fenced code blocks that require runner management include the runner_prefix.
Covered tools: pytest, python, mypy, ruff, black, isort.
Exempt system tools: git, rg, grep, cd, ls, cat, echo, test, mkdir, cp, mv, rm, touch.

R-ATL-072: UV-specific enforcement (instantiated mode; runner=uv)
Rule: Forbidden patterns in “$” command lines inside fenced code blocks:
- .venv/bin/python
- python -m
- pip install
Required patterns include:
- $ uv sync
- $ uv run <command>

R-ATL-075: $ prefix mandatory for commands (plan/instantiated)
Rule: In mode plan or instantiated, command lines in these sections start with "$":
- Baseline Snapshot (including Baseline tests)
- Preconditions (non-Phase-0 tasks)
- TDD Step 3 — Verify (GREEN)
- Phase Unlock Artifact
- Global Clean Table Scan

### §R.9 Drift Ledger and Search Tool Enforcement

R-ATL-080: Drift Ledger present and structured
Rule: “## Drift Ledger (append-only)” contains a Markdown table with columns:
- Date | Higher | Lower | Mismatch | Resolution | Evidence

R-ATL-D3: Drift Ledger Evidence witness (instantiated mode)
Rule: In instantiated mode, any non-empty Drift Ledger row has an Evidence cell containing a path:line witness (e.g., src/module.py:123). Fully empty rows are allowed.

R-ATL-D4: search_tool enforcement
Rule: YAML front matter includes search_tool.
- If search_tool is rg: text searches in code blocks use rg; grep is forbidden inside fenced code blocks.
- If search_tool is grep: both rg and grep are allowed.
Scope: code blocks only; prose mentions are not flagged.

### §R.10 Linter Behavior Contract

R-LNT-001: Exit codes
Rule: The linter uses:
- 0: pass
- 1: lint violations found
- 2: usage or file read error

R-LNT-002: Diagnostics format
Rule: Default human-readable diagnostics:
- path:line:rule_id:message

R-LNT-003: JSON output
Rule: With a "--json" flag, emit a JSON object containing:
- passed (bool)
- error_count (int)
- errors (array of {line, rule_id, message})
- mode, runner, schema_version

## §V VALIDATION

### §V.1 Compliance Checklist (Rule-anchored)

- [ ] Front matter present and complete (R-ATL-001)
- [ ] Mode semantics observed (R-ATL-002, R-ATL-022, R-ATL-023)
- [ ] Placeholder syntax only (R-ATL-003)
- [ ] Required headings present (R-ATL-010)
- [ ] Prose Coverage Mapping present when required (R-ATL-NEW-02)
- [ ] Baseline Snapshot table present (R-ATL-020)
- [ ] Baseline evidence and baseline tests present (R-ATL-021, R-ATL-021B)
- [ ] Phase and task heading formats correct; task IDs unique (R-ATL-030, R-ATL-NEW-01)
- [ ] Each task has canonical path array; naming rule stated once (R-ATL-032, R-ATL-033)
- [ ] Each task has a single allowed status (R-ATL-090)
- [ ] Non-Phase-0 tasks have TDD steps + STOP gate + Preconditions (R-ATL-040, R-ATL-041, R-ATL-D2)
- [ ] Clean Table checklist presence enforced (R-ATL-042)
- [ ] Phase unlock artifact requirements satisfied (R-ATL-050)
- [ ] Phase gate checklist present (R-ATL-051)
- [ ] Global Clean Table scan section includes required hooks (R-ATL-060, R-ATL-061)
- [ ] Runner and uv constraints enforced (R-ATL-070, R-ATL-071, R-ATL-072, R-ATL-075)
- [ ] Drift ledger structured; evidence witness in instantiated mode (R-ATL-080, R-ATL-D3)
- [ ] search_tool discipline satisfied (R-ATL-D4)
- [ ] Linter behavior contract implemented (R-LNT-001, R-LNT-002, R-LNT-003)

## §C CHANGELOG

- 1.9.0 (2025-12-16): Converted the AI Task List spec into SPEKSI layer structure (META/ARCHITECTURE/DEFINITIONS/RULES/VALIDATION/CHANGELOG/GLOSSARY) without intended semantic changes to the rule set.

## §G GLOSSARY

AI Task List
A Markdown artifact that enumerates phased tasks with TDD steps, gates, and evidence requirements, intended for execution with minimal ambiguity and enforced by a deterministic linter.

Evidence
Captured command output (or permitted placeholders, depending on mode) used to demonstrate that required checks and tests were executed.

Clean Table
A governance gate asserting that the repo and the task list artifact contain no unfinished markers, no placeholders in forbidden modes, and that tests/verification pass as required by the task gates.

Runner
The declared tooling context used to run verification commands consistently (e.g., uv).

End of Document
