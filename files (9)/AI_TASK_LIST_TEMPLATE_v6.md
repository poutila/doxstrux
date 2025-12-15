---
ai_task_list:
  schema_version: "1.6"
  mode: "template"  # "template" = placeholders allowed, "instantiated" = placeholders forbidden
  runner: "[[PH:RUNNER]]"  # e.g., "uv", "poetry", "npm", "cargo", "go"
  runner_prefix: "[[PH:RUNNER_PREFIX]]"  # e.g., "uv run", "poetry run", "" (empty for go/cargo)
  search_tool: "rg"  # "rg" (ripgrep) or "grep" — REQUIRED
---

# AI_TASK_LIST_TEMPLATE.md

**Version**: 6.0 (v1.6 spec — no comment compliance)  
**Scope**: General-only — no project names, no repo paths, no project-specific env vars.
**Modes**: Template mode (placeholders allowed) → Instantiated mode (placeholders forbidden)

---

## Non-negotiable Invariants

1. **Clean Table is a delivery gate** — Do not mark complete unless verified and stable.
2. **No silent errors** — Errors raise unconditionally.
3. **No weak tests** — Tests assert semantics, not existence/import/smoke.
4. **Single runner principle** — One canonical runner everywhere.
5. **Evidence anchors required** — Claims require command output or file evidence.
6. **No synthetic reality** — Do not invent outputs, results, or versions.
7. **Import hygiene** — Absolute imports preferred; no multi-dot relative (`from ..`); no wildcards (`import *`).

---

## Placeholder Protocol

**Format**: `[[PH:NAME]]` where NAME is `[A-Z0-9_]+`

**Pre-flight** (must return zero — fails if placeholders found):
```bash
$ if rg '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md; then
>   echo "ERROR: Placeholders found"
>   exit 1
> fi
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
)
```

**Steps**:
1. Copy template to PROJECT_TASKS.md
2. Replace all `[[PH:NAME]]` placeholders with real values
3. Run pre-flight (must be zero)
4. Run baseline commands, paste outputs
5. If failures: log in Drift Ledger, stop

**Verification**:
```bash
if rg '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md; then
  echo "ERROR: Placeholders found"
  exit 1
fi
for p in "${TASK_0_1_PATHS[@]}"; do test -e "$p" || exit 1; done
```

- [ ] Placeholders zero
- [ ] Snapshot captured
- [ ] Tests captured
- [ ] Paths exist

**Status**: 📋 PLANNED

---

### Task 0.2 — Create phase unlock artifact

**Objective**: Generate `.phase-0.complete.json` with real values.

**Paths**:
```bash
TASK_0_2_PATHS=(
  ".phase-0.complete.json"
)
```

**Steps**:
```bash
cat > .phase-0.complete.json << EOF
{
  "phase": 0,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "test_command": "[[PH:FULL_TEST_COMMAND]]",
  "result": "PASS"
}
EOF

# Verify no placeholders in artifact
if rg '\[\[PH:|YYYY-MM-DD|TBD' .phase-0.complete.json; then
  echo "ERROR: Placeholder-like tokens found in artifact"
  exit 1
fi
```

- [ ] Artifact created with real timestamp
- [ ] Artifact has real commit hash
- [ ] No placeholders in artifact

**Status**: 📋 PLANNED

---

## Phase [[PH:N]] — [[PH:PHASE_NAME]]

**Goal**: [[PH:PHASE_GOAL]]  
**Tests**: `[[PH:FAST_TEST_COMMAND]]` / `[[PH:FULL_TEST_COMMAND]]`

### Task [[PH:TASK_ID]] — [[PH:TASK_NAME]]

> **Naming rule**: Task ID `N.M` → Path array `TASK_N_M_PATHS` (dots become underscores)

**Objective**: [[PH:ONE_SENTENCE]]

**Paths**:
```bash
# Example: Task 1.2 → TASK_1_2_PATHS
TASK_[[PH:TASK_ID_UNDERSCORED]]_PATHS=(
  "[[PH:PATH_1]]"
  "[[PH:PATH_2]]"
)
```

**Scope**:
- In: [[PH:IN_SCOPE]]
- Out: [[PH:OUT_SCOPE]]

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ [[PH:FAST_TEST_COMMAND]]
$ [[PH:SYMBOL_CHECK_COMMAND]]
```

### TDD Step 1 — Write test (RED)

```bash
$ [[PH:TEST_COMMAND]]
# Expected: FAIL
```

### TDD Step 2 — Implement (minimal)

### TDD Step 3 — Verify (GREEN)

```bash
$ [[PH:TEST_COMMAND]]
$ [[PH:FULL_TEST_COMMAND]]
# Expected: PASS
```

### STOP — Clean Table

**Evidence** (paste actual output):
```
# Test run output:
[[PH:PASTE_TEST_OUTPUT]]

# Symbol/precondition check output:
[[PH:PASTE_PRECONDITION_OUTPUT]]
```

**No Weak Tests** (all YES):
- [ ] Stub/no-op would FAIL this test?
- [ ] Asserts semantics, not just presence?
- [ ] Has negative case for critical behavior?
- [ ] Is NOT import-only/smoke/existence-only/exit-code-only?

**Clean Table**:
- [ ] Tests pass (not skipped)
- [ ] Full suite passes
- [ ] No placeholders remain
- [ ] Paths exist
- [ ] Drift ledger updated (if needed)

**Status**: 📋 PLANNED  <!-- Choose one of: 📋 PLANNED | ⏳ IN PROGRESS | ✅ COMPLETE | ❌ BLOCKED -->

---

## Drift Ledger (append-only)

| Date | Higher | Lower | Mismatch | Resolution | Evidence |
|------|--------|-------|----------|------------|----------|
| | | | | | |

---

## Phase Unlock Artifact

Generate with real values (no placeholders — commands must use $ prefix when instantiated):
```bash
$ cat > .phase-N.complete.json << EOF
{
  "phase": N,
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse HEAD)",
  "test_command": "...",
  "result": "PASS"
}
EOF

# Verify no placeholders
if rg '\[\[PH:|YYYY-MM-DD|TBD' .phase-N.complete.json; then
  echo "ERROR: Placeholder-like tokens found in artifact"
  exit 1
fi
```

---

## Global Clean Table Scan

Run before each phase gate (commands must use $ prefix when instantiated):

```bash
# [[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]]
# 
# Standard patterns (recommended for all projects; gates must fail on matches):
# $ ! rg 'TODO|FIXME|XXX' src/                           # No unfinished markers
# $ ! rg '\[\[PH:' .                                     # No placeholders
#
# Python import hygiene (REQUIRED when runner=uv):
# $ rg 'from \.\.' src/ || exit 1                        # No multi-dot relative imports
# $ rg 'import \*' src/ || exit 1                        # No wildcard imports

$ [[PH:CLEAN_TABLE_GLOBAL_CHECK_COMMAND]]

# Import hygiene (required for Python/uv projects):
if rg 'from \.\.' [[PH:SOURCE_DIR]]; then
  echo "ERROR: Multi-dot relative import found"
  exit 1
fi
if rg 'import \*' [[PH:SOURCE_DIR]]; then
  echo "ERROR: Wildcard import found"
  exit 1
fi

# Expected: zero matches (or explicit allowlist)
```

**Evidence** (paste output):
```
[[PH:PASTE_CLEAN_TABLE_OUTPUT]]
```

---

## STOP — Phase Gate

Requirements for Phase N+1:

- [ ] All Phase N tasks ✅ COMPLETE
- [ ] Phase N tests pass
- [ ] Global Clean Table scan passes (output pasted above)
- [ ] `.phase-N.complete.json` exists
- [ ] All paths exist
- [ ] Drift ledger current

---

**End of Template**
