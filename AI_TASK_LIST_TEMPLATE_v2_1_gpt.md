# AI_TASK_LIST_TEMPLATE.md (Refactored)

**Purpose**: Executable task list template for AI-assisted implementation that is (a) drift-resistant and (b) reality-anchored.
**Version**: 2.1 (refactor of v2.0)
**Core goals**:
- **No drift**: avoid duplicated SSOTs, ambiguous placeholders, and “planned but not verified” completion.
- **Close to reality**: prefer observed facts (command outputs, file trees, tests) over narrative.

---

## 0. Non-negotiable invariants

1. **Evidence over prose**: any claim that “X works / exists / passes” must have a concrete evidence anchor.
2. **SSOT is explicit**: if two sources disagree, the hierarchy below decides, and the drift is logged.
3. **No progress on red**: failing tests, missing files, or unverified prerequisites are hard stops.
4. **No synthetic reality**: do not invent outputs, file lists, test results, or timings.

---

## 1. Placeholder protocol (drift control)

This template uses a single, machine-detectable placeholder format:

- Allowed placeholder form: `[[PH:NAME]]` (uppercase NAME, underscores allowed)
- Disallowed: `[NAME]`, `<NAME>`, `YYYY-MM-DD`, “TBD”, or any ambiguous freeform placeholder.

**Pre-flight rule** (mandatory before executing a project task list):
- Grep must return **zero** placeholders:
  ```bash
  grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && { echo "Placeholders remain"; exit 1; } || true
  ```

**Allowed exceptions**: none in the executable project task list.

---

## 2. Source of truth hierarchy (anti-drift)

**Highest → lowest**:

1. **Executed tests + tool output** (captured in this task list)
2. **Current repository state** (files in the working tree; commit hash)
3. **Runtime code** (actual implementation)
4. **Task list** (this document, once instantiated for a project)
5. **Design/spec docs** (historical once implementation begins)

**Drift rule**: if a lower source contradicts a higher source, update the lower source and log the mismatch.

---

## 3. Required “Reality Anchors” (must exist in every instantiated task list)

Create these at the top of `PROJECT_TASKS.md` and keep them updated:

### 3.1 Baseline snapshot (captured, not narrated)

- **Date (local)**: [[PH:DATE_YYYY_MM_DD]]
- **Repo**: [[PH:REPO_NAME]]
- **Branch**: [[PH:GIT_BRANCH]]
- **Commit**: [[PH:GIT_COMMIT]]
- **OS**: [[PH:OS]]
- **Python**: [[PH:PYTHON_VERSION]]
- **uv**: [[PH:UV_VERSION]]

Evidence anchors (paste exact output blocks):

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
uv --version
uv run python --version
```

### 3.2 Baseline test status

```bash
[[PH:FAST_TEST_COMMAND]]
[[PH:FULL_TEST_COMMAND]]
```

Paste the full output (or at minimum: summary lines + failure tracebacks).

---

## 4. Global phase gate rules

Phase N+1 cannot start until Phase N is fully green:

- [ ] All Phase N tasks are ✅ COMPLETE
- [ ] Phase N tests pass (the phase declares exact commands)
- [ ] Clean Table checks pass (declared below)
- [ ] Phase unlock artifact exists: `.phase-N.complete.json`
- [ ] File manifest checks pass for Phase N (no missing files)
- [ ] Drift log updated for any SSOT mismatch detected during Phase N

---

## 5. Clean Table definition (project-wide)

A phase is “clean” only if all apply:

- [ ] Full test suite passes
- [ ] No new TODO/FIXME/XXX in changed files
- [ ] No placeholder tokens remain in generated artifacts
- [ ] No swallowed exceptions / silent failure paths introduced
- [ ] Lint/type checks (if applicable) pass under the same runner as CI

**Default checks (customize, but keep them executable):**
```bash
# Placeholder scan (must be zero)
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' . && { echo "PLACEHOLDERS FOUND"; exit 1; } || true

# TODO scan (define repo policy; this is a typical baseline)
grep -RInE '(TODO|FIXME|XXX)' src tests && { echo "TODOs found"; exit 1; } || true
```

---

## 6. Canonical file list rule (anti-drift)

Every task must define one canonical file list, used for:
- the task header
- existence verification

Format (bash array; copy-paste friendly):
```bash
TASK_0_1_FILES=(
  "src/..."
  "tests/..."
)
```

Existence check (must pass before task completion):
```bash
for f in "${TASK_0_1_FILES[@]}"; do
  test -f "$f" || { echo "Missing file: $f"; exit 1; }
done
```

---

# [[PH:PROJECT_NAME]] — Task List

**Status**: Phase 0 — NOT STARTED

## Phase 0 — Reality, Tooling, and Baseline

### Task 0.1 — Baseline snapshot + test reality

**Objective**: Capture the baseline snapshot and baseline test status as evidence anchors.
**Canonical files**:
```bash
TASK_0_1_FILES=(
  "PROJECT_TASKS.md"
  ".phase-0.complete.json"
)
```

**Steps**
1. Populate §3.1 and §3.2 using executed commands; paste outputs.
2. Run the declared test commands; paste outputs.
3. If failures exist:
   - log them in §9 Drift + Issues Ledger
   - do not proceed to Phase 1 until resolved or explicitly scoped out.

**Verification**
- [ ] Snapshot fields filled from real outputs
- [ ] Test outputs captured
- [ ] File existence check passes for `TASK_0_1_FILES`

**Status**: 📋 PLANNED

---

## Phase [[PH:PHASE_N]] — [[PH:PHASE_NAME]]

**Goal**: [[PH:PHASE_GOAL]]
**Phase tests**:
- Fast: `[[PH:FAST_TEST_COMMAND]]`
- Full: `[[PH:FULL_TEST_COMMAND]]`

### Task [[PH:TASK_ID]] — [[PH:TASK_NAME]]

**Objective**: [[PH:ONE_SENTENCE_OBJECTIVE]]

**Canonical files**
```bash
TASK_[[PH:TASK_ID_SANITIZED]]_FILES=(
  [[PH:FILES_ONE_PER_LINE_QUOTED]]
)
```

### Scope

**In scope**
- [[PH:IN_SCOPE_1]]

**Out of scope**
- [[PH:OUT_SCOPE_1]]

### Preconditions (must be evidenced)

- [ ] Current tests are green (or failures are explicitly accepted and logged)
- [ ] Symbols referenced exist in code (grep evidence included)

Evidence anchors:
```bash
# Symbol existence
rg -n "^[[:space:]]*def [[PH:SYMBOL]]\b|class [[PH:SYMBOL]]\b" -S src

# Current tests
[[PH:FAST_TEST_COMMAND]]
```

### TDD Step 1 — Write the test first (RED)

- Create/modify test files from `TASK_..._FILES`
- Run:
  ```bash
  uv run pytest [[PH:TEST_PATH_OR_EXPR]] -v
  ```
- Expected: FAIL for a reason that is directly tied to the missing behavior.

**Test strength check**
- [ ] Would the test pass with a stub (`return None`, empty list, no-op)? If yes, strengthen it.
- [ ] Does the test assert semantics (content/structure), not just existence or exit code?

### TDD Step 2 — Implement

- Implement minimal behavior to satisfy the test.
- Avoid speculative generalization unless there is a second real consumer in-scope.

### TDD Step 3 — Verify (GREEN)

```bash
uv run pytest [[PH:TEST_PATH_OR_EXPR]] -v
uv run pytest -q
```

### STOP — Clean Table check (task-level)

- [ ] Task test is GREEN and strong
- [ ] Full suite GREEN
- [ ] No TODO/FIXME introduced
- [ ] File existence checks pass for `TASK_..._FILES`
- [ ] Any SSOT mismatch logged in Drift ledger

**Status**: 📋 PLANNED / ⏳ IN PROGRESS / ✅ COMPLETE / ❌ BLOCKED

---

## 9. Drift + Issues Ledger (required)

Maintain as an append-only table.

| Date | Higher SSOT | Lower SSOT | Mismatch | Resolution | Evidence |
|------|------------|------------|----------|------------|----------|
| [[PH:DATE]] | tests | task list | Example mismatch | Example fix | command output / file path |

---

## 10. Phase unlock artifacts

For each completed phase N, create `.phase-N.complete.json` with:

- phase number
- timestamp (real)
- commit hash
- test commands executed
- pass/fail summary

Example:
```json
{
  "phase": 0,
  "completed_at": "2025-12-14T00:00:00+02:00",
  "commit": "abc123...",
  "fast_test_command": "uv run pytest -q",
  "full_test_command": "uv run pytest -v",
  "result": "PASS"
}
```

End of template.
