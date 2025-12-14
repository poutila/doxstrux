# AI Task List Spec v1.0

**Spec ID**: `AI_TASK_LIST_SPEC_V1`  
**Applies to**: A single Markdown file (the instantiated task list or the template)

**Primary goals**:
1. No drift
2. Reality-first
3. Lintable against a spec
4. TDD + No Weak Tests + runner enforcement (incl. uv) + Clean Table baked in

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
  schema_version: "1.0"
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

### R-ATL-022: Instantiated evidence non-empty

If `mode: instantiated`, the linter MUST fail if any literal `[[PH:OUTPUT]]` or `[[PH:PASTE_*]]` tokens remain anywhere in the file.

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

### R-ATL-050: Phase unlock artifact section required

The document MUST include a `## Phase Unlock Artifact` section that:

1. Shows `.phase-N.complete.json` generation using real substitutions for timestamp and commit
2. Includes a scan command that rejects `[[PH:` or common placeholder tokens in the artifact

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

### R-ATL-071: Runner consistency

If `mode: instantiated`, the linter MUST verify that all command lines in:

- Baseline tests
- Task TDD Verify blocks
- Phase gate checks

contain the declared `runner_prefix` (unless `runner_prefix: ""`).

### R-ATL-072: UV-specific enforcement

If `runner: "uv"` and `mode: instantiated`:

**Forbidden patterns** (linter MUST fail if present anywhere):

```
.venv/bin/python
python -m
pip install
```

**Required patterns** (at least one occurrence each, somewhere in file):

```
uv sync
uv run
```

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

### R-ATL-D4: search_tool enforcement (ripgrep preferred)

The YAML front matter MAY include an optional `search_tool` field:

```yaml
ai_task_list:
  search_tool: "rg"  # or "grep"
```

When `search_tool: rg`:
- All text searches in the document MUST use `rg` (ripgrep)
- The `grep` command is FORBIDDEN in code blocks
- D2 Preconditions MUST use `rg` (not `grep`)

When `search_tool: grep` or not specified:
- Both `rg` and `grep` are allowed

**Rationale**: ripgrep (`rg`) is faster, has better defaults (ignores .gitignore, binary files), and provides consistent behavior across platforms. Projects that standardize on `rg` can enforce this via the linter.

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
  "schema_version": "1.0"
}
```

---

## Minimal Compliance Summary

A document is **Spec v1 compliant** if:

1. ✅ Has required YAML metadata and required headings (9 total)
2. ✅ Tasks are parseable, unique, and each has a canonical path array
3. ✅ Non-Phase-0 tasks contain TDD blocks + STOP gates + No Weak Tests checklist + evidence slots
4. ✅ Non-Phase-0 tasks have Preconditions with symbol-check command (R-ATL-D2)
5. ✅ Instantiated mode has zero placeholders anywhere (including paste slots)
6. ✅ Drift Ledger Evidence contains path:line witness in instantiated mode (R-ATL-D3)
7. ✅ search_tool=rg forbids grep usage (R-ATL-D4)
8. ✅ Clean Table scan and Phase Gate are present and require phase artifacts
9. ✅ Runner rules are enforced based on metadata (including uv forbiddens)

---

**End of Spec**
