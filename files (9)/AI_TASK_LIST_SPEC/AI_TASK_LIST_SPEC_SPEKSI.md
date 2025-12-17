<!--
SPEC_KIND: linting_domain
SPEC_ID: AI_TASK_LIST_SPEC
SPEC_VERSION: 2.0.0
STATUS: active
-->

# AI TASK LIST SPECIFICATION

## §0 META

- **Purpose**: Define structure and linter-enforceable rules for AI Task List Markdown artifacts
- **Scope**: Task list validation, mode semantics, TDD enforcement, evidence requirements
- **Tier**: Framework
- **Drift Budget**: 0 — Any violation MUST fail the linter

---

## §1 DEFINITIONS

### §1.1 Mode Variables

| Term | Definition |
|------|------------|
| `template` | Scaffolding mode; placeholders are allowed |
| `plan` | Execution-ready mode; commands real, evidence may be placeholder |
| `instantiated` | Execution-complete mode; placeholders forbidden, evidence required |

### §1.2 Structural Terms

| Term | Definition |
|------|------------|
| `Task ID` | String in form N.M where N is phase number, M is task number |
| `Canonical path array` | Bash array `TASK_<N>_<M>_PATHS=(<quoted paths>)` attached to Task N.M |
| `Runner` | Declared toolchain context for command execution (e.g., uv) |
| `Runner prefix` | Mandatory prefix for tool invocations managed by runner (e.g., "uv run") |
| `Search tool` | Front-matter field declaring permitted text search command: rg or grep |
| `Placeholder` | Token format `[[PH:NAME]]` where NAME matches `[A-Z0-9_]+` |
| `Command line` | Line starting with `$` inside fenced code block |
| `Evidence block` | Fenced code block containing command lines and captured output |

### §1.3 Required Headings

| Heading | Purpose |
|---------|---------|
| `## Non-negotiable Invariants` | Framework invariants |
| `## Placeholder Protocol` | Placeholder usage rules |
| `## Source of Truth Hierarchy` | SSOT definition |
| `## Baseline Snapshot (capture before any work)` | Reality grounding |
| `## Phase 0 — Baseline Reality` | Initial phase |
| `## Drift Ledger (append-only)` | Drift tracking |
| `## Phase Unlock Artifact` | Phase completion artifact |
| `## Global Clean Table Scan` | Final validation |
| `## STOP — Phase Gate` | Phase gate checklist |

---

## §2 RULES

| Rule ID | Description | Enforcement |
|---------|-------------|-------------|
| R-ATL-000 | If spec and linter diverge, linter MUST be updated to match spec | enforce_r_atl_000 |
| R-ATL-001 | Task list MUST start with YAML front matter containing ai_task_list block with schema_version, mode, runner, runner_prefix, search_tool | enforce_r_atl_001 |
| R-ATL-002 | Mode semantics: template allows placeholders; plan requires real commands; instantiated forbids all placeholders | enforce_r_atl_002 |
| R-ATL-003 | Only `[[PH:NAME]]` placeholders recognized, NAME matching `[A-Z0-9_]+` | enforce_r_atl_003 |
| R-ATL-010 | Task list MUST contain all required headings with exact text and case | enforce_r_atl_010 |
| R-ATL-011 | If mode is plan or instantiated, MUST include `## Prose Coverage Mapping` section with table | enforce_r_atl_011 |
| R-ATL-020 | Baseline Snapshot MUST include table with Date, Repo, Branch, Commit, Runner, Runtime rows | enforce_r_atl_020 |
| R-ATL-021 | Baseline Snapshot MUST include Evidence block with commands and output | enforce_r_atl_021 |
| R-ATL-021B | Baseline Snapshot MUST include "Baseline tests" evidence block in all modes | enforce_r_atl_021b |
| R-ATL-022 | In instantiated mode, linter MUST fail if any `[[PH:...]]` tokens remain | enforce_r_atl_022 |
| R-ATL-023 | In instantiated mode, required evidence slots MUST contain real output lines | enforce_r_atl_023 |
| R-ATL-024 | With `--require-captured-evidence`, evidence blocks MUST include cmd and exit headers | enforce_r_atl_024 |
| R-ATL-030 | Phase headings MUST match `^## Phase (\d+) — (.+)$`; Phase 0 MUST exist | enforce_r_atl_030 |
| R-ATL-031 | Task headings MUST match `^### Task (\d+)\.(\d+) — (.+)$`; Task IDs MUST be unique | enforce_r_atl_031 |
| R-ATL-032 | Every task MUST contain `**Paths**:` block with `TASK_<N>_<M>_PATHS=(<quoted paths>)` | enforce_r_atl_032 |
| R-ATL-033 | Document MUST include naming rule linking Task ID N.M to array exactly once | enforce_r_atl_033 |
| R-ATL-040 | Each non-Phase-0 task MUST include TDD Step 1, 2, 3 headings | enforce_r_atl_040 |
| R-ATL-041 | Each non-Phase-0 task MUST include `### STOP — Clean Table` with evidence slots and checklists | enforce_r_atl_041 |
| R-ATL-042 | Linter MUST verify presence of five Clean Table checklist items | enforce_r_atl_042 |
| R-ATL-050 | Task list MUST include `## Phase Unlock Artifact` section with .phase-N.complete.json generation | enforce_r_atl_050 |
| R-ATL-051 | `## STOP — Phase Gate` MUST include checklist referencing unlock artifacts | enforce_r_atl_051 |
| R-ATL-060 | `## Global Clean Table Scan` MUST include command and evidence paste slot | enforce_r_atl_060 |
| R-ATL-061 | In instantiated mode, `[[PH:PASTE_CLEAN_TABLE_OUTPUT]]` MUST NOT remain | enforce_r_atl_061 |
| R-ATL-063 | When runner=uv and instantiated, Global Clean Table MUST include import hygiene checks | enforce_r_atl_063 |
| R-ATL-070 | runner and runner_prefix MUST be non-empty strings (or runner_prefix explicitly empty) | enforce_r_atl_070 |
| R-ATL-071 | In instantiated mode with non-empty runner_prefix, tool invocations MUST include prefix | enforce_r_atl_071 |
| R-ATL-072 | When runner=uv and instantiated, forbidden: .venv/bin/python, python -m, pip install | enforce_r_atl_072 |
| R-ATL-075 | In plan/instantiated mode, command lines in gated sections MUST start with `$` | enforce_r_atl_075 |
| R-ATL-080 | Drift Ledger MUST contain table with Date, Higher, Lower, Mismatch, Resolution, Evidence columns | enforce_r_atl_080 |
| R-ATL-090 | Each task MUST contain `**Status**:` with exactly one of: PLANNED, IN PROGRESS, COMPLETE, BLOCKED | enforce_r_atl_090 |
| R-ATL-091 | If task is COMPLETE and instantiated, all checklist items in STOP block MUST be checked | enforce_r_atl_091 |
| R-ATL-D2 | Non-Phase-0 tasks MUST include Preconditions block with symbol-check command | enforce_r_atl_d2 |
| R-ATL-D3 | In instantiated mode, non-empty Drift Ledger rows MUST have path:line witness | enforce_r_atl_d3 |
| R-ATL-D4 | search_tool MUST be in YAML; if rg, grep forbidden in code blocks | enforce_r_atl_d4 |
| R-LNT-001 | Linter exit codes: 0=pass, 1=violations, 2=usage error | enforce_r_lnt_001 |
| R-LNT-002 | Default diagnostics format: path:line:rule_id:message | enforce_r_lnt_002 |
| R-LNT-003 | With --json flag, emit JSON object with passed, error_count, errors, mode, runner, schema_version | enforce_r_lnt_003 |

---

## §3 INVARIANTS

| Invariant ID | Description | Enforcement |
|--------------|-------------|-------------|
| INV-MODE-A | Mode determines placeholder tolerance; no exceptions | enforce_inv_mode_a |
| INV-SSOT-A | Spec is authoritative; linter implements spec | enforce_inv_ssot_a |
| INV-EVIDENCE-A | Evidence in instantiated mode MUST be real output, not fabricated | enforce_inv_evidence_a |
| INV-TDD-A | Non-Phase-0 tasks MUST follow RED-GREEN-REFACTOR structure | enforce_inv_tdd_a |
| INV-CLEAN-A | Clean Table gate MUST pass before phase completion | enforce_inv_clean_a |

---

## §4 PHASES

### Phase 1: Front Matter Validation
Validate YAML front matter and mode declaration.
Run R-ATL-001, R-ATL-002, R-ATL-003, R-ATL-070, R-ATL-D4.

### Phase 2: Structure Validation
Validate required headings and sections exist.
Run R-ATL-010, R-ATL-011, R-ATL-020, R-ATL-030, R-ATL-050, R-ATL-051, R-ATL-060, R-ATL-080.

### Phase 3: Task Validation
Validate task structure, IDs, paths, TDD steps.
Run R-ATL-031, R-ATL-032, R-ATL-033, R-ATL-040, R-ATL-041, R-ATL-042, R-ATL-090, R-ATL-D2.

### Phase 4: Mode-Specific Validation
Apply mode-dependent rules.
Run R-ATL-021, R-ATL-021B, R-ATL-022, R-ATL-023, R-ATL-061, R-ATL-063, R-ATL-071, R-ATL-072, R-ATL-075, R-ATL-091, R-ATL-D3.

### Phase 5: Output Generation
Generate linter output.
Run R-LNT-001, R-LNT-002, R-LNT-003.

---

## §5 SCHEMAS

### §5.1 YAML Front Matter

```yaml
ai_task_list:
  schema_version: "<VERSION.yaml version>"
  mode: "template" | "plan" | "instantiated"
  runner: "<string>"
  runner_prefix: "<string>"
  search_tool: "rg" | "grep"
```

### §5.2 Task Structure

```markdown
### Task N.M — <Name>

**Status**: 📋 PLANNED | ⏳ IN PROGRESS | ✅ COMPLETE | ❌ BLOCKED

**Paths**:
TASK_N_M_PATHS=("path/to/file.py")

**Preconditions**:
$ rg "symbol" path/

### TDD Step 1 — Write test (RED)
### TDD Step 2 — Implement (minimal)
### TDD Step 3 — Verify (GREEN)

### STOP — Clean Table
```

### §5.3 Linter JSON Output

```json
{
  "passed": true,
  "error_count": 0,
  "errors": [],
  "mode": "plan",
  "runner": "uv",
  "schema_version": "1.0.0"
}
```

---

## §6 CLI COMMANDS

### §6.1 `ai_task_list_linter.py <file.md>`

**Purpose**: Validate AI Task List artifact against this specification.

**Flags**:
- `--mode MODE`: Override mode detection (template/plan/instantiated)
- `--json`: Output JSON instead of human-readable diagnostics
- `--require-captured-evidence`: Enforce evidence headers

**Exit codes**:
- 0: Pass
- 1: Lint violations found
- 2: Usage or file read error

---

## §7 APPENDICES

### A. Rule ID Namespaces

| Prefix | Domain |
|--------|--------|
| `R-ATL-0xx` | Front matter and mode rules |
| `R-ATL-01x` | Structure anchors |
| `R-ATL-02x` | Baseline snapshot |
| `R-ATL-03x` | Phase and task syntax |
| `R-ATL-04x` | TDD and task gates |
| `R-ATL-05x` | Phase unlock and gate |
| `R-ATL-06x` | Global clean table |
| `R-ATL-07x` | Runner and $ discipline |
| `R-ATL-08x` | Drift ledger |
| `R-ATL-09x` | Task status |
| `R-ATL-Dx` | Additional constraints |
| `R-LNT-xxx` | Linter behavior |
| `INV-xxx` | Invariants |

### B. Checklist Items (SSOT)

**No Weak Tests checklist**:
1. Stub/no-op would FAIL this test?
2. Asserts semantics, not just presence?
3. Has negative case for critical behavior?
4. Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table checklist**:
1. Tests pass (not skipped)
2. Full suite passes
3. No placeholders remain
4. Paths exist
5. Drift ledger updated (if needed)

---

**END OF SPEC**
