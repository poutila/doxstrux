# AI_TASK_LIST_TEMPLATE — General Only

**Purpose**: Provide a project-agnostic, drift-resistant task list format for AI-assisted delivery.  
**Scope**: This document contains **no project names, no repo paths, and no repo-specific environment variables**.  
**Core goals**:
1. **No drift**: one SSOT per fact; mechanical enforcement for placeholders and file lists.
2. **Close to reality**: claims require evidence anchors; no invented outputs or unverifiable assertions.

---

## 0. Non‑negotiable invariants

1. **Clean Table delivery gate**  
   Do not mark tasks/phases complete unless verified end-to-end and stable.

2. **No silent errors**  
   Errors raise unconditionally; no “strict mode” flags to suppress failures.

3. **No weak tests**  
   Tests must assert semantics (behavior), not existence/import/smoke/line-count.

4. **Single runner principle**  
   The project must declare one canonical runner (e.g., `uv run`, `poetry run`, `python -m`, etc.).  
   The task list must use that runner consistently for all commands.

5. **Evidence anchors required**  
   Any claim of “exists / passes / wired / safe” must be backed by concrete evidence (command output, file excerpt, or test output).

6. **No synthetic reality**  
   Do not invent file lists, test results, timings, tool versions, or outputs.

---

## 1. Placeholder protocol (drift control)

**Only** this placeholder form is allowed:

- `[[PH:NAME]]` where `NAME` matches `[A-Z0-9_]+`

**Pre-flight rule**: placeholder scan must return **zero** before execution:

```bash
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && { echo "Placeholders remain"; exit 1; } || true
```

**Allowed exceptions:** none.

---

## 2. Source of truth hierarchy (anti‑drift)

Highest → lowest:

1. **Executed tests + captured tool output**
2. **Current repository state** (working tree + commit hash)
3. **Runtime code**
4. **This task list** (once instantiated)
5. **Design docs / plans** (historical once execution begins)

**Drift rule**: if a lower source contradicts a higher source, update the lower source and log it in the Drift Ledger.

---

## 3. Required “Reality Anchors” (must exist in every instantiated task list)

These anchors convert narrative into evidence.

### 3.1 Baseline snapshot (captured, not narrated)

- Date (local): [[PH:DATE_YYYY_MM_DD]]
- Repo name: [[PH:REPO_NAME]]
- Branch: [[PH:GIT_BRANCH]]
- Commit: [[PH:GIT_COMMIT]]
- OS: [[PH:OS]]
- Language/runtime version(s): [[PH:RUNTIME_VERSION]]
- Canonical runner: [[PH:RUNNER_NAME_AND_VERSION]]

**Evidence anchors (paste exact outputs):**
```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
[[PH:RUNNER_VERSION_COMMAND]]
[[PH:RUNTIME_VERSION_COMMAND]]
```

### 3.2 Baseline test status (captured output)

Declare canonical commands:

- Fast tests: `[[PH:FAST_TEST_COMMAND]]`
- Full tests: `[[PH:FULL_TEST_COMMAND]]`

Execute and paste output (summary + failures if any):
```bash
[[PH:FAST_TEST_COMMAND]]
[[PH:FULL_TEST_COMMAND]]
```

### 3.3 Baseline Clean Table scan (project policy)

Declare and execute the project’s Clean Table checks. Defaults below; replace as required.

```bash
# Placeholders must be zero
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' . && { echo "PLACEHOLDERS FOUND"; exit 1; } || true

# TODO policy example (customize; do NOT copy if your repo allows TODOs)
grep -RInE '(TODO|FIXME|XXX)' . && { echo "TODOs found"; exit 1; } || true
```

---

## 4. Global gates (phase + task)

### 4.1 Phase gate (Phase N+1 cannot start until Phase N is green)

- [ ] All Phase N tasks are ✅ COMPLETE
- [ ] Phase N tests pass (exact commands declared in Phase header)
- [ ] Clean Table checks pass (declared in phase)
- [ ] Phase unlock artifact exists: `.phase-N.complete.json`
- [ ] File manifest checks pass (no missing paths)
- [ ] Drift Ledger updated for any mismatch

### 4.2 Task STOP gate (cannot mark ✅ COMPLETE unless all apply)

- [ ] Task tests are GREEN and meaningful (No Weak Tests)
- [ ] Full suite is GREEN
- [ ] No placeholders remain
- [ ] Clean Table checks pass per policy
- [ ] All task paths exist
- [ ] Drift ledger updated (if needed)

---

## 5. Canonical file list rule (anti‑drift)

Every task must define exactly one canonical file list and reuse it for verification.

Format (bash array):

```bash
TASK_0_1_PATHS=(
  "path/to/file_or_dir"
  "path/to/another"
)
```

Existence verification:

```bash
for p in "${TASK_0_1_PATHS[@]}"; do
  test -e "$p" || { echo "Missing path: $p"; exit 1; }
done
```

---

## 6. No Weak Tests rules (task-level)

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

## 7. Decision + evidence structure (lightweight, enforceable)

For each task, record a minimal decision chain and evidence anchors.

### 7.1 Decision chain

- What: [[PH:DECISION_WHAT]]
- Why: [[PH:DECISION_WHY]]
- Why not: [[PH:DECISION_WHY_NOT]]
- Impact: [[PH:DECISION_IMPACT]]

### 7.2 Evidence anchors (minimum viable)

Each non-trivial claim must cite one of:
- command output pasted inline, or
- file path + short excerpt, or
- test output excerpt.

---

# [[PH:PROJECT_NAME]] — Task List

**Status**: Phase 0 — NOT STARTED

---

## Phase 0 — Reality, Tooling, and Baseline

**Phase tests**
- Fast: `[[PH:FAST_TEST_COMMAND]]`
- Full: `[[PH:FULL_TEST_COMMAND]]`

### Task 0.1 — Instantiate task list + capture baseline reality

**Objective**: Create `PROJECT_TASKS.md` from this template and capture baseline evidence (snapshot + tests + scans).

**Canonical paths**
```bash
TASK_0_1_PATHS=(
  "PROJECT_TASKS.md"
  ".phase-0.complete.json"
)
```

**Steps**
1. Copy this template to `PROJECT_TASKS.md`.
2. Replace all placeholders (`[[PH:...]]`) with real values.
3. Run placeholder scan (must be zero).
4. Run baseline snapshot commands; paste outputs.
5. Run baseline tests; paste outputs.
6. Run baseline Clean Table scans; paste outputs.
7. If anything fails: log it in the Drift + Issues Ledger and stop. Do not proceed.

**Verification**
```bash
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && { echo "Placeholders remain"; exit 1; } || true
```

- [ ] Snapshot captured
- [ ] Tests captured
- [ ] Scans captured
- [ ] Paths exist (`TASK_0_1_PATHS`)

**Status**: 📋 PLANNED

---

## Phase [[PH:PHASE_N]] — [[PH:PHASE_NAME]]

**Goal**: [[PH:PHASE_GOAL]]

**Phase tests**
- Fast: `[[PH:FAST_TEST_COMMAND]]`
- Full: `[[PH:FULL_TEST_COMMAND]]`

### Task [[PH:TASK_ID]] — [[PH:TASK_NAME]]

**Objective**: [[PH:ONE_SENTENCE_OBJECTIVE]]

**Canonical paths**
```bash
TASK_[[PH:TASK_ID_SANITIZED]]_PATHS=(
  [[PH:PATHS_ONE_PER_LINE_QUOTED]]
)
```

### Scope
**In scope**
- [[PH:IN_SCOPE_1]]

**Out of scope**
- [[PH:OUT_SCOPE_1]]

### Preconditions (must be evidenced)

- [ ] Baseline tests are green OR failures are explicitly accepted and logged
- [ ] All referenced symbols/paths exist (evidence included)
- [ ] Canonical runner is available and used consistently

Evidence anchors (paste outputs):
```bash
[[PH:RUNNER_VERSION_COMMAND]]
[[PH:SYMBOL_EXISTENCE_COMMAND]]
[[PH:FAST_TEST_COMMAND]]
```

### TDD Step 1 — Write the test first (RED)

Run:
```bash
[[PH:RUNNER_PREFIX]] [[PH:TEST_COMMAND]]
```

Expected: FAIL for a reason tied to missing behavior.

### TDD Step 2 — Implement minimal change (KISS/YAGNI)

- Implement the smallest change that satisfies the test.
- Do not introduce new abstraction layers without ≥2 current consumers.

### TDD Step 3 — Verify (GREEN)

```bash
[[PH:RUNNER_PREFIX]] [[PH:TEST_COMMAND]]
[[PH:FULL_TEST_COMMAND]]
```

### STOP — Clean Table (task-level)

- [ ] Tests are meaningful (No Weak Tests)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Clean Table checks pass
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED / ⏳ IN PROGRESS / ✅ COMPLETE / ❌ BLOCKED

---

## 9. Drift + Issues Ledger (append-only)

| Date | Higher SSOT | Lower SSOT | Mismatch | Resolution | Evidence |
|------|------------|------------|----------|------------|----------|
| [[PH:DATE]] | tests | task list | Example mismatch | Example fix | pasted command output / file path |

---

## 10. Phase unlock artifacts

For each completed Phase N, create `.phase-N.complete.json` with real values:

```json
{
  "phase": 0,
  "completed_at": "2025-12-14T00:00:00+02:00",
  "commit": "abc123...",
  "fast_test_command": "…",
  "full_test_command": "…",
  "result": "PASS"
}
```

End of general-only template.
