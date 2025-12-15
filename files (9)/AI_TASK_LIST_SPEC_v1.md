# AI Task List Spec v1.7 (plan mode introduction)
<!-- See COMMON.md §Version Metadata -->

**Spec ID**: `AI_TASK_LIST_SPEC_V1_7`  
**Schema version**: `1.6`  
**Applies to**: A single Markdown file (the instantiated task list or the template)
**SSOT**: The spec is the authoritative contract; the linter implements the spec. If spec and linter diverge, fix the linter.

**Primary goals**:
1. No drift
2. Reality-first
3. Lintable against a spec
4. TDD + No Weak Tests + runner enforcement (incl. uv) + Clean Table baked in
5. Non-empty evidence in instantiated mode (v1.1)
6. Verifiable evidence provenance via captured headers (v1.3, opt-in)
7. Closed-loop enforcement (no bypass via formatting) (v1.4)
8. All governance rules baked in (import hygiene, Clean Table checklist)
9. **NEW v1.6**: No comment compliance — $ command lines required, not prose/comments

> This document is the normative contract for task lists. It is **not** a task
> list and is **not** intended to be linted by `ai_task_list_linter_v1_8.py`.
> If this spec and the linter diverge, fix the linter to match the spec.

---

## 0. Definitions

| Term | Definition |
|------|------------|
| **Mode** | Controls placeholder tolerance: `template` (placeholders allowed), `plan` (real commands, evidence placeholders), or `instantiated` (placeholders forbidden) | <!-- See COMMON.md §Mode Definitions -->
| **Task ID** | Format `N.M` where N = phase number, M = task number |
| **Canonical path array** | Bash array `TASK_N_M_PATHS=(...)` associated with Task N.M |
| **Runner** | Declared tool for command execution (e.g., `uv`), with `runner_prefix` (e.g., `uv run`) |

---

## Plan mode (additive)

This spec supports an intermediate `mode: "plan"`:
- Preconditions/Global/Phase unlock MUST use real `$ {search_tool} …` commands (no command placeholders). Runner/search_tool/import-hygiene rules apply.
- Evidence/output placeholders are allowed; placeholders are forbidden in YAML/paths/status/naming rule.
- Template mode continues to allow command/evidence placeholders; instantiated forbids placeholders entirely.
- Intended lifecycle: template → plan → instantiated.

### R-ATL-PROSE: Prose Coverage Mapping (plan/instantiated)
- If `mode: plan` or `mode: instantiated`, the document MUST include a `## Prose Coverage Mapping` section containing a markdown table with at least a header row and one data row.
- Purpose: tie prose requirements to tasks to reduce omission drift.
- Template mode: Coverage Mapping recommended, not required.

## 1. Required Document Header

### R-ATL-001: Front matter required — UPDATED in v1.6

The document MUST start with YAML front matter containing:

```yaml
ai_task_list:
  schema_version: "1.6"  # Must be exactly "1.6"
  mode: "template" | "plan" | "instantiated"
  runner: "<string>"
  runner_prefix: "<string>"
  search_tool: "rg" | "grep"  # Required (not optional)
```

**v1.6 changes**:
- `schema_version` must be exactly `"1.6"` (linter enforces this)
- Comment compliance loophole closed — $ command lines required

### R-ATL-002: Mode semantics

| Mode | Placeholder behavior |
|------|---------------------|
| `template` | `[[PH:...]]` placeholders MAY appear |
| `plan` | Commands MUST be real; evidence/output placeholders MAY appear; runner/search_tool/import-hygiene rules apply |
| `instantiated` | `[[PH:...]]` placeholders MUST NOT appear anywhere |

### R-ATL-003: Placeholder syntax

The only recognized placeholder format is:

```
[[PH:NAME]]
```

Where `NAME` matches `[A-Z0-9_]+`.

---

## 2. Required Top-Level Sections

### R-ATL-010: Required headings

The file MUST contain these headings (exact text, case-sensitive):

```
## Non-negotiable Invariants
## Placeholder Protocol
## Source of Truth Hierarchy
## Baseline Snapshot (capture before any work)
## Phase 0 — Baseline Reality
## Drift Ledger (append-only)
## Phase Unlock Artifact
## Global Clean Table Scan
## STOP — Phase Gate
```

**Rationale**: These headings are minimal "lint anchors" that enforce drift killers and gates without requiring the linter to understand prose.

---

## 3. Baseline Snapshot Requirements (Reality-First)

### R-ATL-020: Baseline Snapshot table required

Under `## Baseline Snapshot (capture before any work)`, a Markdown table MUST contain these rows:

| Required Row |
|--------------|
| Date |
| Repo |
| Branch |
| Commit |
| Runner |
| Runtime |

Values may be placeholders only in `template` mode.

### Plan mode (v1.7)

`mode: "plan"` is allowed as an intermediate state:
- Commands in Preconditions/Global/Phase unlock MUST be real (no command placeholders); runner/search_tool/import-hygiene rules apply.
- Evidence/output placeholders are allowed; placeholders are forbidden in YAML/paths/status/naming rule.
- Template mode continues to allow command/evidence placeholders; instantiated forbids placeholders entirely.
- Lifecycle: template → plan → instantiated.

### R-ATL-021: Baseline Evidence blocks required

The Baseline Snapshot section MUST include an "Evidence" block with commands and `[[PH:OUTPUT]]` placeholders (template/plan mode) or real pasted output (instantiated mode). In template/plan, the Evidence block must be fenced and contain the canonical placeholder.

### R-ATL-021B: Baseline tests evidence required (instantiated mode)

The Baseline Snapshot section MUST include a **Baseline tests** fenced code block in all modes. In instantiated mode:
- It MUST contain at least one `$` command.
- Each `$` command MUST have non-empty output lines (captured headers alone do not count).
- The block must be non-empty overall.
In template/plan mode, the Baseline tests block may contain placeholders, but it must exist and be fenced.

**$ discipline**: In instantiated mode, command lines in Baseline evidence/tests MUST start with `$`.

### R-ATL-022: Instantiated mode forbids placeholders

If `mode: instantiated`, the linter MUST fail if any literal `[[PH:OUTPUT]]` or `[[PH:PASTE_*]]` tokens remain anywhere in the file.

### R-ATL-023: Non-empty evidence required (instantiated mode) — STRENGTHENED in v1.3

If `mode: instantiated`, every required evidence slot MUST contain real output lines (not just metadata headers).

**v1.3 changes**:
- STOP evidence labels are now ALWAYS required (not just when `--require-captured-evidence` is used)
- Captured header lines (`# cmd:`, `# exit:`, `# ts_utc:`, `# cwd:`) do NOT count as "evidence content"
- Each labeled section must contain at least one real output line

This applies to:

1. **Baseline Snapshot evidence**: Each `$ command` line must have at least one non-empty output line following it.

2. **Per-task STOP evidence** (non-Phase-0): The evidence block MUST include BOTH labeled sections:
   - `# Test run output:` — with real output lines below
   - `# Symbol/precondition check output:` — with real output lines below
   
   **Note**: Captured header metadata (`# cmd:`, `# exit:`) does not satisfy the "real output" requirement.

3. **Global Clean Table evidence**: The evidence block must contain at least one real output line (not just headers).

**Rationale**: Closes the "blank evidence" and "headers-only evidence" loopholes where structurally valid documents pass lint while containing no actual proof of execution.

### R-ATL-024: Captured evidence headers (opt-in) — NEW in v1.3

When the linter is invoked with `--require-captured-evidence`, evidence blocks MUST include captured headers:

```
# cmd: <exact command executed>
# exit: <exit code as integer>
```

**Enforcement rules**:

1. **Baseline Snapshot evidence**: Must have `# cmd:` and `# exit:` headers. Exit code may be non-zero (recording initial state).

2. **Per-task STOP evidence**: Each labeled section (`# Test run output:` and `# Symbol/precondition check output:`) must have `# cmd:` and `# exit:` headers with `exit: 0` (gates must pass).

3. **Global Clean Table evidence**: Must have `# cmd:` and `# exit:` headers with `exit: 0` (clean table must pass).

**Rationale**: Raises the cost of evidence fabrication by requiring explicit claims about command and exit status. While not cryptographically verifiable, this creates a structured contract that is much harder to fake than arbitrary prose.

**Example**:
```bash
# cmd: uv run pytest tests/
# exit: 0
===== test session starts =====
collected 5 items
tests/test_main.py::test_something PASSED
===== 1 passed in 0.03s =====
```

---

## 4. Phase and Task Syntax

### R-ATL-030: Phase heading format

A phase heading MUST match:

```regex
^## Phase (\d+) — (.+)$
```

Phase 0 MUST exist and match exactly:

```
## Phase 0 — Baseline Reality
```

### R-ATL-031: Task heading format and uniqueness

A task heading MUST match:

```regex
^### Task (\d+)\.(\d+) — (.+)$
```

Task IDs MUST be unique across the document.

### R-ATL-032: Task → Paths canonical array required

Every task MUST contain a `**Paths**:` block with a bash array named:

```bash
TASK_<N>_<M>_PATHS=(...)
```

The array MUST include at least 1 quoted path string.

### R-ATL-033: Naming rule must be stated once

The document MUST include the explicit naming rule linking Task ID `N.M` to path array `TASK_N_M_PATHS`.

---

## 5. TDD and Verification Blocks (Task-Level)

### R-ATL-040: TDD steps required per task

Each task MUST include all three headings:

```
### TDD Step 1 — Write test (RED)
### TDD Step 2 — Implement (minimal)
### TDD Step 3 — Verify (GREEN)
```

**Exception**: Phase 0 tasks (bootstrap tasks like "Instantiate + capture baseline") are exempt from TDD requirements.

### R-ATL-041: STOP block required per task

Each task MUST include a STOP section matching:

```
### STOP — Clean Table
```

**Exception**: Phase 0 tasks (bootstrap tasks) are exempt from STOP block requirements.

For non-Phase-0 tasks, inside that STOP section, it MUST include:

**Evidence subsection** containing:
- `[[PH:PASTE_TEST_OUTPUT]]`
- `[[PH:PASTE_PRECONDITION_OUTPUT]]`

In instantiated mode, the STOP section MUST contain a fenced evidence block even if the "Evidence/paste" label is renamed or removed.

**No Weak Tests checklist** with exactly these four items (semantic match, whitespace-insensitive):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table checklist** containing (at minimum):
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

### R-ATL-090: Task status must be a single allowed value

Each task MUST contain a status line in the form:

```
**Status**: <status>
```

Where `<status>` is exactly one of:

```
📋 PLANNED | ⏳ IN PROGRESS | ✅ COMPLETE | ❌ BLOCKED
```

No slash-separated menu; a single selection is required.

### R-ATL-091: Completed tasks must have checked checklists (instantiated mode)

If a task's status is `✅ COMPLETE` and `mode: instantiated`, all No Weak Tests and Clean Table checklist items in its STOP block MUST be checked (`[x]`).

### R-ATL-042: Clean Table checklist enforcement

The linter MUST verify that the STOP section contains all five Clean Table checklist items (semantic match, whitespace-insensitive):

1. `Tests pass (not skipped)`
2. `Full suite passes`
3. `No placeholders remain`
4. `Paths exist`
5. `Drift ledger updated`

**Rationale**: The Clean Table checklist was previously in template only but not linter-enforced. This allowed documents to pass lint without the checklist, reducing the "delivery gate" effect.

### R-ATL-D2: Preconditions symbol-check required for non-Phase-0 tasks

Non-Phase-0 tasks MUST include a **Preconditions** block with a fenced code block containing:

- **Template mode**: `[[PH:SYMBOL_CHECK_COMMAND]]` placeholder
- **Instantiated mode**: A `grep` or `rg` command (comment lines excluded from check)

**Rationale**: Prevents "non-existent API" errors by requiring symbol verification before implementation.

---

## 6. Phase Unlock Artifacts and Phase Gate

### R-ATL-050: Phase unlock artifact section required — UPDATED in v1.6

The document MUST include a `## Phase Unlock Artifact` section that:

1. Shows `.phase-N.complete.json` generation using real substitutions for timestamp and commit
2. Includes a scan command that rejects `[[PH:` or common placeholder tokens in the artifact

**Linter enforcement**:
- Template mode: Section must include a fenced code block with artifact file pattern (e.g., `.phase-N.complete.json`)
- Instantiated mode: 
  - Section MUST have `$ cat > .phase-N.complete.json` as an actual command line (not comment; `.json` suffix required)
  - Section MUST have `$ rg` command for placeholder rejection scan (not comment)
  - Trivial commands like `echo .phase-0.complete.json` do NOT satisfy this requirement
  - **v1.6**: Comments containing these patterns do NOT satisfy the requirement

**Rationale**: The Phase Unlock Artifact is the gate between phases. Without explicit `$ cat >` artifact creation and `$ rg` placeholder verification as command lines, the phase gating contract becomes ceremonial and unenforceable.

### R-ATL-051: Phase gate required and must reference unlock artifacts

The `## STOP — Phase Gate` section MUST include checklist items requiring:

- [ ] `.phase-N.complete.json` exists
- [ ] Global Clean Table scan passes
- [ ] Phase tests pass
- [ ] Drift ledger current

Linter note: checklist presence is enforced; shell exit semantics of referenced gates are process-level (linter enforces command presence, not control flow).

---

## 7. Global Clean Table Scan (Repo-Wide Gate)

### R-ATL-060: Global scan hook required

Under `## Global Clean Table Scan`, the file MUST include:

1. A command placeholder `[[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]]` (template mode) or actual command (instantiated)
2. An evidence paste slot `[[PH:PASTE_CLEAN_TABLE_OUTPUT]]`

### R-ATL-061: Instantiated scan evidence required

If `mode: instantiated`, the linter MUST fail if `[[PH:PASTE_CLEAN_TABLE_OUTPUT]]` remains.

### R-ATL-062: Recommended Clean Table patterns

The Global Clean Table Scan SHOULD include project-appropriate checks using `rg` patterns. Recommended patterns include:

**Standard patterns (all projects)**:
```bash
$ rg 'TODO|FIXME|XXX' src/                    # No unfinished work markers
$ rg '\[\[PH:' .                              # No placeholders in any file
```

### R-ATL-063: Import hygiene enforcement (Python projects) — UPDATED in v1.6

When `runner: "uv"` (Python project) and `mode: instantiated`, the linter MUST verify that the Global Clean Table Scan section contains **actual `$` command lines** (not comments):

1. Multi-dot relative import check: `$ rg 'from \.\.'` command line
2. Wildcard import check: `$ rg 'import \*'` command line

**Required patterns for Python (runner=uv)** (gates must fail on matches):
```bash
$ if rg 'from \.\.' src/; then
>   echo "ERROR: multi-dot relative import found"
>   exit 1
> fi
$ if rg 'import \*' src/; then
>   echo "ERROR: wildcard import found"
>   exit 1
> fi
```

**v1.6 change**: Comments containing these patterns do NOT satisfy the requirement. The linter checks only lines starting with `$` inside fenced code blocks.

**Rationale**: Import hygiene rules (absolute imports preferred, no multi-dot relative, no wildcards) are critical for Python projects. Comment compliance (putting patterns in comments to pass lint) undermines the enforcement.

**Scope**: Only enforced when `runner: "uv"`. Other runners (npm, cargo, go) do not trigger this check.

---

## 8. Runner Enforcement (Including uv)

Runner enforcement is conditional and derived from metadata, keeping the spec general while enabling strict uv rules.

### R-ATL-070: Runner metadata required

`runner` and `runner_prefix` MUST be non-empty strings.

Exception: Ecosystems where prefix is intentionally empty MUST declare `runner_prefix: ""` explicitly.

### R-ATL-071: Runner consistency — STRENGTHENED in v1.1

If `mode: instantiated` and `runner_prefix` is non-empty, the linter MUST verify that all command lines **inside fenced code blocks** that invoke runner-managed tools include the `runner_prefix`.

**Commands requiring runner_prefix**:
- `pytest`
- `python`
- `mypy`
- `ruff`
- `black`
- `isort`

**Commands exempt from runner_prefix** (system tools):
- `git`, `rg`, `grep`, `cd`, `ls`, `cat`, `echo`, `test`, `mkdir`, `cp`, `mv`, `rm`, `touch`

**Scope**: Only lines beginning with `$` inside fenced code blocks are checked. Output lines (without `$`) are NOT checked, preventing false positives on pasted command output.

**Rationale**: Catches common mistakes like bare `pytest` instead of `uv run pytest`, which causes environment mismatches. The `$` prefix requirement ensures output mentioning these tools (e.g., "python version ok") doesn't trigger false positives.

### R-ATL-072: UV-specific enforcement — FIXED in v1.3 (no false positives)

If `runner: "uv"` and `mode: instantiated`:

**Forbidden patterns** (linter MUST fail if present in `$` command lines):

```
.venv/bin/python
python -m
pip install
```

**Scope**: Only `$` command lines inside fenced code blocks are checked. Pasted output (e.g., error messages, CI logs, hints like "Run 'pip install foo'") does NOT trigger this rule.

**Required patterns** (must appear as `$` command lines inside fenced code blocks):

```
$ uv sync
$ uv run ...
```

**Rationale**: Prevents environment bypass while allowing truthful evidence pasting.

### R-ATL-075: $ prefix mandatory for commands — NEW in v1.4

If `mode: plan` or `mode: instantiated`, command lines in key sections MUST start with `$` prefix.

**Sections requiring $ prefix**:
- Baseline Snapshot (including Baseline tests)
- Preconditions (non-Phase-0 tasks)
- TDD Step 3 — Verify (GREEN)
- Phase Unlock Artifact
- Global Clean Table Scan

**Command indicators** (lines matching these patterns must have `$`):
- `rg `, `grep `, `cat `, `echo `, `pytest`, `python`, `mypy`, `ruff`, `black`, `isort`
- `uv `, `git `, `cd `, `ls `, `mkdir `, `touch `, `rm `, `cp `, `mv `, `test `, `exit `

**Rationale**: Without `$` prefix, the linter cannot distinguish command lines from output lines. This allowed bypassing R-ATL-071/072 by simply omitting `$`. Making `$` mandatory closes this escape hatch.

---

## 9. Drift Ledger Rules

### R-ATL-080: Drift ledger present and structured

The `## Drift Ledger (append-only)` section MUST contain a Markdown table with columns:

```
| Date | Higher | Lower | Mismatch | Resolution | Evidence |
```

Note: "Append-only" is a process property; the linter only enforces structure.

### R-ATL-D3: Drift Ledger Evidence must be a witness (instantiated mode)

In **instantiated mode**, any non-empty Drift Ledger row MUST have an Evidence cell containing a `path:line` witness pattern (e.g., `src/module.py:123` or `tests/test_foo.py:45`).

Fully empty rows are allowed (for template structure preservation).

**Rationale**: Prevents prose-only drift resolution ("looks good") by requiring a concrete code reference.

### R-ATL-D4: search_tool enforcement — UPDATED in v1.6

The YAML front matter MUST include the `search_tool` field (required since v1.4):

```yaml
ai_task_list:
  search_tool: "rg"  # or "grep" — REQUIRED
```

When `search_tool: rg`:
- All text searches in the document MUST use `rg` (ripgrep)
- The `grep` command is FORBIDDEN **inside fenced code blocks only**
- D2 Preconditions MUST use `rg` (not `grep`)
- Prose mentions of "grep" (e.g., "we use rg instead of grep") are NOT flagged

When `search_tool: grep`:
- Both `rg` and `grep` are allowed

**Rationale**: ripgrep (`rg`) is faster, has better defaults (ignores .gitignore, binary files), and provides consistent behavior across platforms. Code-block-only enforcement prevents false positives on documentation prose.

---

## 10. Linter Behavior Contract

### R-LNT-001: Exit codes

| Code | Meaning |
|------|---------|
| 0 | Pass |
| 1 | Lint violations found |
| 2 | Usage / file read error |

### R-LNT-002: Diagnostics format

Default output (human-readable):

```
path:line:rule_id:message
```

### R-LNT-003: JSON output

`--json` flag emits:

```json
{
  "passed": true,
  "error_count": 0,
  "errors": [
    {"line": 42, "rule_id": "R-ATL-031", "message": "..."}
  ],
  "mode": "instantiated",
  "runner": "uv",
  "schema_version": "1.6"
}
```

---

## Minimal Compliance Summary

A document is **Spec v1.7 compliant** if:

1. ✅ schema_version must be exactly "1.6" (R-ATL-001)
2. ✅ search_tool is required (not optional) (R-ATL-001, R-ATL-D4)
3. ✅ Has required YAML metadata and required headings (9 total)
4. ✅ Naming rule stated exactly once (R-ATL-033)
5. ✅ Tasks are parseable, unique, and each has a canonical path array
6. ✅ Non-Phase-0 tasks contain TDD blocks + STOP gates + evidence slots
7. ✅ Non-Phase-0 tasks have Preconditions with symbol-check command (R-ATL-D2)
8. ✅ Instantiated mode has zero placeholders anywhere (R-ATL-022)
9. ✅ Baseline tests block present with real output (instantiated) (R-ATL-021B)
10. ✅ STOP evidence has BOTH labels with real output (R-ATL-023)
11. ✅ No Weak Tests checklist: 4 required prompts (R-ATL-041)
12. ✅ Clean Table checklist: 5 required prompts (R-ATL-042)
13. ✅ **UPDATED**: Phase Unlock requires `$ cat > .phase-N.complete.json` and `$ rg` command lines (R-ATL-050)
14. ✅ $ prefix mandatory for command lines in key sections (R-ATL-075)
15. ✅ Drift Ledger Evidence contains path:line witness in instantiated mode (R-ATL-D3)
16. ✅ search_tool=rg forbids grep in code blocks only (R-ATL-D4)
17. ✅ Runner prefix enforced on $ command lines (R-ATL-071)
18. ✅ UV forbidden patterns only on $ command lines (R-ATL-072)

**Optional (with --require-captured-evidence)**:

19. ⚡ Captured evidence headers (`# cmd:`, `# exit:`) in all evidence blocks (R-ATL-024)
20. ⚡ Exit code 0 required for STOP and Global Clean Table evidence

**Recommended (project-specific Clean Table patterns)**:

21. 📋 No unfinished markers: `$ rg 'TODO|FIXME|XXX' src/` (R-ATL-062)

**Python-specific (runner=uv) — LINTER ENFORCED**:

22. ✅ **UPDATED**: Import hygiene: `$ rg 'from \.\.'` command line required (R-ATL-063)
23. ✅ **UPDATED**: Import hygiene: `$ rg 'import \*'` command line required (R-ATL-063)
24. ✅ Single status value required per task (R-ATL-090)
25. ✅ Completed tasks must have checked No Weak Tests + Clean Table boxes (instantiated) (R-ATL-091)
26. ✅ runner=uv requires `$ uv sync` and `$ uv run ...` command lines in code blocks (R-ATL-072)

**v1.6 key change**: Comments containing required patterns do NOT satisfy requirements. Actual `$` command lines are required.
