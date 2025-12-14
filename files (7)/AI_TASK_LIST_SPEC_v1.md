# AI Task List Spec v1.3

**Spec ID**: `AI_TASK_LIST_SPEC_V1_3`  
**Schema version**: `1.2`  
**Applies to**: A single Markdown file (the instantiated task list or the template)

**Primary goals**:
1. No drift
2. Reality-first
3. Lintable against a spec
4. TDD + No Weak Tests + runner enforcement (incl. uv) + Clean Table baked in
5. Non-empty evidence in instantiated mode (v1.1)
6. Verifiable evidence provenance via captured headers (v1.3, opt-in)

---

## 0. Definitions

| Term | Definition |
|------|------------|
| **Mode** | Controls placeholder tolerance: `template` (placeholders allowed) or `instantiated` (placeholders forbidden) |
| **Task ID** | Format `N.M` where N = phase number, M = task number |
| **Canonical path array** | Bash array `TASK_N_M_PATHS=(...)` associated with Task N.M |
| **Runner** | Declared tool for command execution (e.g., `uv`), with `runner_prefix` (e.g., `uv run`) |

---

## 1. Required Document Header

### R-ATL-001: Front matter required

The document MUST start with YAML front matter containing:

```yaml
ai_task_list:
  schema_version: "1.3"
  mode: "template" | "instantiated"
  runner: "<string>"
  runner_prefix: "<string>"
```

### R-ATL-002: Mode semantics

| Mode | Placeholder behavior |
|------|---------------------|
| `template` | `[[PH:...]]` placeholders MAY appear |
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

### R-ATL-021: Baseline Evidence blocks required

The Baseline Snapshot section MUST include an "Evidence" block with commands and `[[PH:OUTPUT]]` placeholders (template mode) or real pasted output (instantiated mode).

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

### R-ATL-D2: Preconditions symbol-check required for non-Phase-0 tasks

Non-Phase-0 tasks MUST include a **Preconditions** block with a fenced code block containing:

- **Template mode**: `[[PH:SYMBOL_CHECK_COMMAND]]` placeholder
- **Instantiated mode**: A `grep` or `rg` command (comment lines excluded from check)

**Rationale**: Prevents "non-existent API" errors by requiring symbol verification before implementation.

---

## 6. Phase Unlock Artifacts and Phase Gate

### R-ATL-050: Phase unlock artifact section required — ENFORCED in v1.3

The document MUST include a `## Phase Unlock Artifact` section that:

1. Shows `.phase-N.complete.json` generation using real substitutions for timestamp and commit
2. Includes a scan command that rejects `[[PH:` or common placeholder tokens in the artifact

**Linter enforcement**:
- Template mode: Section must include a fenced code block with artifact file pattern (e.g., `.phase-N.complete.json`)
- Instantiated mode: 
  - Section MUST include specific artifact file (e.g., `.phase-0.complete.json`, `.phase-1.complete.json`)
  - Section MUST include a fenced code block with artifact generation commands
  - Prose-only mentions are NOT sufficient

**Rationale**: The Phase Unlock Artifact is the gate between phases. Without explicit artifact commands in code blocks, the phase gating contract becomes ceremonial and unenforceable.

### R-ATL-051: Phase gate required and must reference unlock artifacts

The `## STOP — Phase Gate` section MUST include checklist items requiring:

- [ ] `.phase-N.complete.json` exists
- [ ] Global Clean Table scan passes
- [ ] Phase tests pass
- [ ] Drift ledger current

---

## 7. Global Clean Table Scan (Repo-Wide Gate)

### R-ATL-060: Global scan hook required

Under `## Global Clean Table Scan`, the file MUST include:

1. A command placeholder `[[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]]` (template mode) or actual command (instantiated)
2. An evidence paste slot `[[PH:PASTE_CLEAN_TABLE_OUTPUT]]`

### R-ATL-061: Instantiated scan evidence required

If `mode: instantiated`, the linter MUST fail if `[[PH:PASTE_CLEAN_TABLE_OUTPUT]]` remains.

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

**Required patterns** (at least one occurrence each, somewhere in file):

```
uv sync
uv run
```

**Rationale**: Prevents environment bypass while allowing truthful evidence pasting.

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

### R-ATL-D4: search_tool enforcement (ripgrep preferred) — CLARIFIED in v1.1

The YAML front matter MAY include an optional `search_tool` field:

```yaml
ai_task_list:
  search_tool: "rg"  # or "grep"
```

When `search_tool: rg`:
- All text searches in the document MUST use `rg` (ripgrep)
- The `grep` command is FORBIDDEN **inside fenced code blocks only**
- D2 Preconditions MUST use `rg` (not `grep`)
- Prose mentions of "grep" (e.g., "we use rg instead of grep") are NOT flagged

When `search_tool: grep` or not specified:
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
  "schema_version": "1.2"
}
```

---

## Minimal Compliance Summary

A document is **Spec v1.3 compliant** if:

1. ✅ Has required YAML metadata (schema_version: "1.3") and required headings (9 total)
2. ✅ Naming rule stated exactly once (R-ATL-033)
3. ✅ Tasks are parseable, unique, and each has a canonical path array
4. ✅ Non-Phase-0 tasks contain TDD blocks + STOP gates + No Weak Tests checklist + evidence slots
5. ✅ Non-Phase-0 tasks have Preconditions with symbol-check command (R-ATL-D2)
6. ✅ Instantiated mode has zero placeholders anywhere (R-ATL-022)
7. ✅ **STRENGTHENED**: STOP evidence has BOTH labels with real output (R-ATL-023)
   - `# Test run output:` required with real output below
   - `# Symbol/precondition check output:` required with real output below
   - Captured headers (`# cmd:`, `# exit:`) do NOT count as output
8. ✅ **STRENGTHENED**: Phase Unlock Artifact has code block with specific artifact file (R-ATL-050)
9. ✅ Drift Ledger Evidence contains path:line witness in instantiated mode (R-ATL-D3)
10. ✅ search_tool=rg forbids grep in code blocks only (R-ATL-D4)
11. ✅ Runner prefix enforced on $ command lines only (R-ATL-071)
12. ✅ **FIXED**: UV forbidden patterns only on $ command lines, not output (R-ATL-072)

**Optional (with --require-captured-evidence)**:

13. ⚡ Captured evidence headers (`# cmd:`, `# exit:`) in all evidence blocks (R-ATL-024)
14. ⚡ Exit code 0 required for STOP and Global Clean Table evidence

---

**End of Spec**
