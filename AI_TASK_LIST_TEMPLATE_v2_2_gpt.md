# AI_TASK_LIST_TEMPLATE.md (Refactored)

**Version**: 2.2  
**Objective**: Produce an AI task list that (1) does not drift and (2) stays close to reality.

**Derived governance (inputs)**:
- `CLEAN_TABLE_PRINCIPLE.md`
- `NO_WEAK_TESTS.md`
- `UV_AS_PACKAGE_MANAGER.md`
- `CHAIN_OF_THOUGHT_GOLDEN_ALL_IN_ONE.json`
- `CODE_QUALITY.json`

---

## 0) Non‑negotiable invariants

1. **Clean Table is a delivery gate**  
   Do not ship or mark “complete” unless fully correct, verified, and stable. No deferrals.

2. **No silent errors**  
   Errors raise unconditionally. No “strict mode” flags or environment switches.

3. **No weak tests**  
   Tests must assert meaningful behavior (semantics), not existence/import/smoke/line-count.

4. **uv is the only runner**  
   All commands are `uv ...` / `uv run ...`. Any `.venv/bin/python` usage in committed docs/scripts/tests is drift.

5. **Evidence anchors are required for claims**  
   If you claim “X exists”, “X passes”, “X is wired”, attach command output or file evidence.

6. **No synthetic reality**  
   Do not invent outputs, file lists, test results, timings, or tool versions.

---

## 1) Placeholder protocol (drift control)

**Only** this placeholder form is allowed in an executable project task list:

- `[[PH:NAME]]` where NAME is `[A-Z0-9_]+`

**Pre-flight (must be zero before execution):**
```bash
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && { echo "Placeholders remain"; exit 1; } || true
```

**Allowed exceptions:** none.

---

## 2) Source of truth hierarchy (anti‑drift)

Highest → lowest:

1. Executed tests + captured tool output
2. Current repository state (working tree + commit hash)
3. Runtime code
4. This task list (once instantiated)
5. Design docs / plans (historical once execution begins)

**Drift rule:** if a lower source contradicts a higher source, update the lower source and log it in the Drift Ledger.

---

## 3) Required “Reality Anchors” (must exist in every instantiated task list)

Create these at the top of `PROJECT_TASKS.md` and keep them updated.

### 3.1 Baseline snapshot (captured, not narrated)

- Date (local): [[PH:DATE_YYYY_MM_DD]]
- Repo: [[PH:REPO_NAME]]
- Branch: [[PH:GIT_BRANCH]]
- Commit: [[PH:GIT_COMMIT]]
- OS: [[PH:OS]]
- Python: [[PH:PYTHON_VERSION]]
- uv: [[PH:UV_VERSION]]

Evidence anchors (paste exact output blocks):

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
uv --version
uv run python --version
```

### 3.2 Baseline test status (captured output)

Define the canonical commands:

- Fast: `[[PH:FAST_TEST_COMMAND]]`
- Full: `[[PH:FULL_TEST_COMMAND]]`

Then execute and paste the output (summary + failures, if any):

```bash
[[PH:FAST_TEST_COMMAND]]
[[PH:FULL_TEST_COMMAND]]
```

### 3.3 Baseline repo scan (Clean Table)

These are defaults. If your repo policy differs, change them explicitly and keep them executable.

```bash
# Placeholders must be zero
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' . && { echo "PLACEHOLDERS FOUND"; exit 1; } || true

# TODO policy: default forbids TODO/FIXME/XXX in src/tests (customize if you allow TODOs)
grep -RInE '(TODO|FIXME|XXX)' src tests && { echo "TODOs found"; exit 1; } || true
```

---

## 4) Global gates (phase + task)

### 4.1 Phase gate (Phase N+1 cannot start until Phase N is green)

- [ ] All Phase N tasks are ✅ COMPLETE
- [ ] Phase N tests pass (exact commands declared in Phase header)
- [ ] Clean Table checks pass
- [ ] Phase unlock artifact exists: `.phase-N.complete.json`
- [ ] File manifest checks pass (no missing files)
- [ ] Drift Ledger updated for any mismatch

### 4.2 Task STOP gate (cannot mark ✅ COMPLETE unless all apply)

- [ ] Task tests are GREEN and meaningful (No Weak Tests)
- [ ] Full suite is GREEN
- [ ] No TODO/FIXME/XXX introduced (per repo policy)
- [ ] No placeholders remain
- [ ] All task files exist
- [ ] Any SSOT mismatch logged

---

## 5) Canonical file list rule (anti‑drift)

Every task must define exactly one canonical file list and reuse it for verification.

Format (bash array):

```bash
TASK_0_1_FILES=(
  "src/..."
  "tests/..."
)
```

Existence verification:

```bash
for f in "${TASK_0_1_FILES[@]}"; do
  test -e "$f" || { echo "Missing path: $f"; exit 1; }
done
```

---

## 6) No Weak Tests rules (task-level)

A task’s tests are invalid if they are any of the following:

- import-only tests
- “runs without crashing” smoke tests without semantic assertions
- existence-only assertions (“file exists”, “function exists”)
- line-count/length thresholds as primary proof
- exit-code-only checks without output/content assertions

Required properties:

- A stub/no-op implementation must **fail** the test.
- At least one negative case exists for critical behavior (errors/safety).
- Assertions prove semantics (structure/content), not just presence.

---

## 7) Decision + evidence structure (Golden discipline, lightweight)

For each task, record:

### 7.1 Decision Chain (why this task exists)
- What: [[PH:DECISION_WHAT]]
- Why: [[PH:DECISION_WHY]]
- Why not: [[PH:DECISION_WHY_NOT]]
- Impact: [[PH:DECISION_IMPACT]]

### 7.2 Evidence Anchors (minimum viable)
Each non-trivial claim must cite one of:
- command output pasted inline, or
- file path + exact excerpt (short), or
- test output excerpt.

Optional (recommended for high-risk changes): sha256 hash of quoted excerpt.

---

# [[PH:PROJECT_NAME]] — Task List

**Status**: Phase 0 — NOT STARTED

---

## Phase 0 — Reality, Tooling, and Baseline

**Phase tests**
- Fast: `[[PH:FAST_TEST_COMMAND]]`
- Full: `[[PH:FULL_TEST_COMMAND]]`

### Task 0.1 — Create PROJECT_TASKS.md + baseline reality capture

**Objective**: Instantiate this template into `PROJECT_TASKS.md` and capture baseline reality (snapshot + tests + scans).

**Canonical files**
```bash
TASK_0_1_FILES=(
  "PROJECT_TASKS.md"
  ".phase-0.complete.json"
)
```

**Steps**
1. Copy this template into `PROJECT_TASKS.md`.
2. Replace all placeholders (`[[PH:...]]`) with real values.
3. Run placeholder scan (must be zero).
4. Run baseline snapshot commands; paste outputs.
5. Run baseline tests; paste outputs.
6. Run baseline repo scans; paste outputs.
7. If anything fails: log in Drift + Issues Ledger and stop. Do not proceed.

**Verification**
```bash
# Must find zero placeholders
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && { echo "Placeholders remain"; exit 1; } || true
```

- [ ] Snapshot captured
- [ ] Tests captured
- [ ] Scans captured
- [ ] File existence check passes for `TASK_0_1_FILES`

**Status**: 📋 PLANNED

---

## Phase [[PH:PHASE_N]] — [[PH:PHASE_NAME]]

**Goal**: [[PH:PHASE_GOAL]]

**Phase tests**
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

- [ ] Baseline tests are green OR failures are explicitly accepted and logged
- [ ] All referenced symbols exist (grep evidence included)
- [ ] uv is available and used for all commands

Evidence anchors (paste outputs):
```bash
uv --version
rg -n "def [[PH:SYMBOL]]\b|class [[PH:SYMBOL]]\b" -S src || true
[[PH:FAST_TEST_COMMAND]]
```

### TDD Step 1 — Write the test first (RED)

Run:
```bash
uv run pytest [[PH:TEST_PATH_OR_EXPR]] -v
```

Expected: FAIL for a reason tied to missing behavior.

### TDD Step 2 — Implement minimal change (KISS/YAGNI)

- Implement minimal behavior to satisfy the test.
- Do not add extension points without ≥2 real consumers today.

### TDD Step 3 — Verify (GREEN)

```bash
uv run pytest [[PH:TEST_PATH_OR_EXPR]] -v
uv run pytest -q
```

### STOP — Clean Table (task-level)

- [ ] Tests are meaningful (No Weak Tests checklist)
- [ ] Full suite passes
- [ ] No TODO/FIXME/XXX introduced
- [ ] No placeholders remain
- [ ] Files exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED / ⏳ IN PROGRESS / ✅ COMPLETE / ❌ BLOCKED

---

## 9) Drift + Issues Ledger (append-only)

| Date | Higher SSOT | Lower SSOT | Mismatch | Resolution | Evidence |
|------|------------|------------|----------|------------|----------|
| [[PH:DATE]] | tests | task list | Example mismatch | Example fix | pasted command output / file path |

---

## 10) Phase unlock artifacts

For each completed Phase N, create `.phase-N.complete.json` with real values:

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
