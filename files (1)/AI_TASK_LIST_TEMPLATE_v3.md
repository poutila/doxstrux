# AI_TASK_LIST_TEMPLATE.md

**Version**: 3.0 (minimal, enforceable-only)  
**Scope**: General-only — no project names, no repo paths, no project-specific env vars.

---

## Non-negotiable Invariants

1. **Clean Table is a delivery gate** — Do not mark complete unless verified and stable.
2. **No silent errors** — Errors raise unconditionally.
3. **No weak tests** — Tests assert semantics, not existence/import/smoke.
4. **Single runner principle** — One canonical runner everywhere.
5. **Evidence anchors required** — Claims require command output or file evidence.
6. **No synthetic reality** — Do not invent outputs, results, or versions.

---

## Placeholder Protocol

**Format**: `[[PH:NAME]]` where NAME is `[A-Z0-9_]+`

**Pre-flight** (must return zero):
```bash
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && exit 1 || true
```

---

## Source of Truth Hierarchy

1. Executed tests + tool output (highest)
2. Repository state (commit hash)
3. Runtime code
4. This task list
5. Design docs (lowest — historical once execution begins)

**Drift rule**: Higher wins. Update lower source and log in Drift Ledger.

---

# [[PH:PROJECT_NAME]] — Task List

**Status**: Phase 0 — NOT STARTED

---

## Baseline Snapshot (capture before any work)

| Field | Value |
|-------|-------|
| Date | [[PH:DATE_YYYY_MM_DD]] |
| Repo | [[PH:REPO_NAME]] |
| Branch | [[PH:GIT_BRANCH]] |
| Commit | [[PH:GIT_COMMIT]] |
| Runner | [[PH:RUNNER_NAME_VERSION]] |
| Runtime | [[PH:RUNTIME_VERSION]] |

**Evidence** (paste outputs):
```bash
$ git rev-parse --abbrev-ref HEAD
[[PH:OUTPUT]]

$ git rev-parse HEAD
[[PH:OUTPUT]]

$ [[PH:RUNNER_VERSION_COMMAND]]
[[PH:OUTPUT]]

$ [[PH:RUNTIME_VERSION_COMMAND]]
[[PH:OUTPUT]]
```

**Baseline tests**:
```bash
$ [[PH:FAST_TEST_COMMAND]]
[[PH:OUTPUT]]
```

---

## Phase 0 — Baseline Reality

**Tests**: `[[PH:FAST_TEST_COMMAND]]` / `[[PH:FULL_TEST_COMMAND]]`

### Task 0.1 — Instantiate + capture baseline

**Objective**: Create PROJECT_TASKS.md and capture baseline evidence.

**Paths**:
```bash
TASK_0_1_PATHS=(
  "PROJECT_TASKS.md"
  ".phase-0.complete.json"
)
```

**Steps**:
1. Copy template to PROJECT_TASKS.md
2. Replace all `[[PH:...]]` placeholders
3. Run pre-flight (must be zero)
4. Run baseline commands, paste outputs
5. If failures: log in Drift Ledger, stop

**Verification**:
```bash
grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && exit 1 || true
for p in "${TASK_0_1_PATHS[@]}"; do test -e "$p" || exit 1; done
```

- [ ] Placeholders zero
- [ ] Snapshot captured
- [ ] Tests captured
- [ ] Paths exist

**Status**: 📋 PLANNED

---

## Phase [[PH:N]] — [[PH:PHASE_NAME]]

**Goal**: [[PH:PHASE_GOAL]]  
**Tests**: `[[PH:FAST_TEST_COMMAND]]` / `[[PH:FULL_TEST_COMMAND]]`

### Task [[PH:TASK_ID]] — [[PH:TASK_NAME]]

**Objective**: [[PH:ONE_SENTENCE]]

**Paths**:
```bash
TASK_[[PH:ID]]_PATHS=(
  "[[PH:PATH_1]]"
  "[[PH:PATH_2]]"
)
```

**Scope**:
- In: [[PH:IN_SCOPE]]
- Out: [[PH:OUT_SCOPE]]

**Preconditions** (evidence required):
```bash
[[PH:FAST_TEST_COMMAND]]
[[PH:SYMBOL_CHECK_COMMAND]]
```

### TDD Step 1 — Write test (RED)

```bash
[[PH:RUNNER_PREFIX]] [[PH:TEST_COMMAND]]
# Expected: FAIL
```

### TDD Step 2 — Implement (minimal)

### TDD Step 3 — Verify (GREEN)

```bash
[[PH:RUNNER_PREFIX]] [[PH:TEST_COMMAND]]
[[PH:FULL_TEST_COMMAND]]
# Expected: PASS
```

### STOP — Clean Table

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED / ⏳ IN PROGRESS / ✅ COMPLETE / ❌ BLOCKED

---

## Drift Ledger (append-only)

| Date | Higher | Lower | Mismatch | Resolution | Evidence |
|------|--------|-------|----------|------------|----------|
| | | | | | |

---

## Phase Unlock Artifact

`.phase-N.complete.json`:
```json
{
  "phase": 0,
  "completed_at": "[[PH:ISO_TIMESTAMP]]",
  "commit": "[[PH:COMMIT]]",
  "test_command": "[[PH:FULL_TEST_COMMAND]]",
  "result": "PASS"
}
```

---

## Phase Gate (N+1 requires)

- [ ] All Phase N tasks ✅ COMPLETE
- [ ] Phase N tests pass
- [ ] Clean Table checks pass
- [ ] `.phase-N.complete.json` exists
- [ ] All paths exist
- [ ] Drift ledger current

---

**End of Template**
