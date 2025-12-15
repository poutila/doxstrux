---
ai_task_list:
  schema_version: "1.6"
  mode: "template"
  runner: "uv"
  runner_prefix: "uv run"
  search_tool: "rg"
---

# AI_TASK_LIST_TEMPLATE.md

**Version**: 6.0 (v1.6 spec — no comment compliance)
**Scope**: AI Task List Framework — Spec/Linter/Template/Orchestrator/Manual alignment
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

# FIXES_MERGED — Task List

**Status**: Phase 0 — NOT STARTED

---

## Prose Coverage Mapping

| Prose requirement | Source (file/section) | Implemented by task(s) |
|-------------------|-----------------------|------------------------|
| Mode semantics: add `mode: plan` | FIXES_MERGED.md:Mode semantics | 1.1, 1.2, 1.3, 1.4 |
| Plan mode lifecycle rules | FIXES_MERGED.md:Mode semantics | 1.1, 1.2, 1.3 |
| Remove interim relaxation | FIXES_MERGED.md:Mode semantics | 1.1 |
| Prose Coverage Mapping enforcement | FIXES_MERGED.md:Prose Coverage | 2.1, 2.2, 2.3 |
| Coverage table canonical format | FIXES_MERGED.md:Prose Coverage | 2.1 |
| Linter coverage warning | FIXES_MERGED.md:Prose Coverage | 2.2 |
| Spec as SSOT | FIXES_MERGED.md:Spec as SSOT | 3.1, 3.2 |
| Version labeling consistency | FIXES_MERGED.md:Spec as SSOT | 3.1 |
| Gates fail-on-match | FIXES_MERGED.md:Gates and runner | 4.1 |
| Runner/search_tool compliance | FIXES_MERGED.md:Gates and runner | 4.2 |
| Mode decision tree | FIXES_MERGED.md:Migration | 5.1 |
| Migration guide | FIXES_MERGED.md:Migration | 5.2 |
| Linter hint for plan mode | FIXES_MERGED.md:Migration | 5.3 |
| Validation suite | FIXES_MERGED.md:Validation suite | 6.1, 6.2, 6.3 |
| Template/plan/instantiated tests | FIXES_MERGED.md:Validation suite | 6.1 |
| Negative tests | FIXES_MERGED.md:Validation suite | 6.2 |
| Doc-sync check | FIXES_MERGED.md:Validation suite | 6.3 |
| Critical enumerations definition | FIXES_MERGED.md:Critical enumerations | 7.1 |
| Enumeration markers | FIXES_MERGED.md:Critical enumerations | 7.2 |
| Canonical examples (3 files) | FIXES_MERGED.md:Acceptance Criteria | 6.4 |
| Baseline enforcement | FIXES_MERGED.md:Acceptance Criteria | 1.1 |
| Phase Gate content enforcement | FIXES_MERGED.md:Acceptance Criteria | 1.1 |
| Deprecation timeline | FIXES_MERGED.md:Acceptance Criteria | 5.2 |

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

$ uv --version
[[PH:OUTPUT]]

$ uv run python --version
[[PH:OUTPUT]]
```

**Baseline tests**:
```bash
$ uv run python ai_task_list_linter_v1_8.py AI_TASK_LIST_TEMPLATE_v6.md
[[PH:OUTPUT]]
```

---

## Phase 0 — Baseline Reality

**Tests**: `uv run python ai_task_list_linter_v1_8.py <file>` / `uv run pytest tests/`

### Task 0.1 — Instantiate + capture baseline

**Objective**: Create PROJECT_TASKS.md and capture baseline evidence.

**Paths**:
```bash
TASK_0_1_PATHS=(
  "FIXES_MERGED_tasks.md"
)
```

**Steps**:
1. Copy template to FIXES_MERGED_tasks.md
2. Replace all `[[PH:NAME]]` placeholders with real values
3. Run pre-flight (must be zero)
4. Run baseline commands, paste outputs
5. If failures: log in Drift Ledger, stop

**Verification**:
```bash
if rg '\[\[PH:[A-Z0-9_]+\]\]' FIXES_MERGED_tasks.md; then
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
  "test_command": "uv run python ai_task_list_linter_v1_8.py FIXES_MERGED_tasks.md",
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

## Phase 1 — Mode Semantics (Plan Mode)

**Goal**: Add `mode: plan` to spec/linter/orchestrator/manuals with full lifecycle rules
**Tests**: `uv run python ai_task_list_linter_v1_8.py <file>` / `uv run pytest tests/`

### Task 1.1 — Update spec with mode: plan

> **Naming rule**: Task ID `N.M` → Path array `TASK_N_M_PATHS` (dots become underscores)

**Objective**: Add `mode: plan` definition and rules to AI_TASK_LIST_SPEC_v1.md.

**Paths**:
```bash
TASK_1_1_PATHS=(
  "AI_TASK_LIST_SPEC_v1.md"
)
```

**Scope**:
- In: R-ATL-002 mode semantics update, new mode rules, lifecycle definition, baseline/phase-gate enforcement rules
- Out: Linter implementation (Task 1.2), orchestrator changes (Task 1.3)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ [[PH:SYMBOL_CHECK_COMMAND]]
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_spec_plan_mode.py -k test_plan_mode_defined
# Expected: FAIL (test file does not exist yet)
```

### TDD Step 2 — Implement (minimal)

Add to spec:
1. Update R-ATL-002 mode semantics table with `plan` mode
2. Define plan mode rules:
   - Preconditions/Global/Phase unlock must use real `$ {search_tool} …` commands (no command placeholders)
   - Evidence placeholders allowed
   - runner/search_tool/import-hygiene enforced
   - Placeholders forbidden in YAML/paths/status/naming rule
3. Document lifecycle: template → plan → instantiated
4. Add baseline enforcement: template mode must have Evidence fenced block with `[[PH:OUTPUT]]`
5. Add Phase Gate content enforcement: required checklist items

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_spec_plan_mode.py
$ uv run pytest tests/ -q
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

**Status**: 📋 PLANNED

---

### Task 1.2 — Implement mode: plan in linter

**Objective**: Update linter to accept and enforce mode=plan rules.

**Paths**:
```bash
TASK_1_2_PATHS=(
  "ai_task_list_linter_v1_8.py"
)
```

**Scope**:
- In: Accept mode=plan in YAML, enforce real commands in Preconditions/Global/Phase unlock, forbid `[[PH:SYMBOL_CHECK_COMMAND]]` in plan mode, allow output placeholders
- Out: Spec changes (Task 1.1), orchestrator changes (Task 1.3)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'mode.*template.*instantiated' ai_task_list_linter_v1_8.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_linter_plan_mode.py -k test_plan_mode_accepted
# Expected: FAIL (plan mode not yet accepted)
```

### TDD Step 2 — Implement (minimal)

1. Update `_parse_front_matter` to accept `mode: "plan"`
2. Add plan-mode-specific checks:
   - Preconditions must have real `$ rg`/`$ grep` commands (no `[[PH:SYMBOL_CHECK_COMMAND]]`)
   - Global Clean Table must have real `$ rg` commands
   - Phase Unlock must have real `$ cat >` and `$ rg` commands
3. Allow evidence placeholders (`[[PH:OUTPUT]]`, `[[PH:PASTE_*]]`) in plan mode
4. Suggest `mode: plan` when concrete commands found in template mode (linter message)

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_linter_plan_mode.py
$ uv run pytest tests/ -q
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

**Status**: 📋 PLANNED

---

### Task 1.3 — Update orchestrator for plan mode

**Objective**: Default orchestrator to plan mode; update self-check to enforce plan rules.

**Paths**:
```bash
TASK_1_3_PATHS=(
  "PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md"
)
```

**Scope**:
- In: Change default mode to plan, update operating mode section, add optional template scaffold flag
- Out: Spec changes (Task 1.1), linter changes (Task 1.2)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'mode.*template' PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md
```

### TDD Step 1 — Write test (RED)

```bash
$ rg 'mode: "plan"' PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md
# Expected: no match (plan mode not documented yet)
```

### TDD Step 2 — Implement (minimal)

1. Update Operating mode section: default to `mode: "plan"`
2. Update self-check: enforce plan rules (real commands in Preconditions/Global/Phase unlock)
3. Add optional template scaffold flag documentation
4. Update workflow step 4 to emit real commands + placeholder evidence

### TDD Step 3 — Verify (GREEN)

```bash
$ rg 'mode: "plan"' PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md
$ uv run pytest tests/ -q
# Expected: PASS (match found, tests pass)
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

**Status**: 📋 PLANNED

---

### Task 1.4 — Update manuals and docs for plan mode

**Objective**: Update AI_ASSISTANT USER_MANUAL.md and related docs with three-mode lifecycle.

**Paths**:
```bash
TASK_1_4_PATHS=(
  "AI_ASSISTANT USER_MANUAL.md"
  "AI_TASK_LIST_TEMPLATE_v6.md"
)
```

**Scope**:
- In: Mode lifecycle checklists, template/plan/instantiated guidance, command placeholder rules
- Out: Spec/linter/orchestrator changes (Tasks 1.1-1.3)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'template.*instantiated' "AI_ASSISTANT USER_MANUAL.md"
```

### TDD Step 1 — Write test (RED)

```bash
$ rg 'plan.*mode' "AI_ASSISTANT USER_MANUAL.md"
# Expected: no match (plan mode not documented yet)
```

### TDD Step 2 — Implement (minimal)

1. Update mode decision section: add plan mode option
2. Add lifecycle documentation: template → plan → instantiated
3. Update checklists: only template allows command placeholders
4. Update Quick Checklist with plan mode requirements

### TDD Step 3 — Verify (GREEN)

```bash
$ rg 'plan.*mode' "AI_ASSISTANT USER_MANUAL.md"
$ rg 'template.*plan.*instantiated' "AI_ASSISTANT USER_MANUAL.md"
# Expected: PASS (matches found)
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

**Status**: 📋 PLANNED

---

## Phase 2 — Prose Coverage Mapping Enforcement

**Goal**: Define canonical coverage table format and add linter validation
**Tests**: `uv run python ai_task_list_linter_v1_8.py <file>` / `uv run pytest tests/`

### Task 2.1 — Define coverage table format in spec

**Objective**: Add canonical Prose Coverage Mapping table definition to spec.

**Paths**:
```bash
TASK_2_1_PATHS=(
  "AI_TASK_LIST_SPEC_v1.md"
)
```

**Scope**:
- In: Table column definitions, anchored source requirements, task reference format
- Out: Linter implementation (Task 2.2)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'Prose Coverage' AI_TASK_LIST_SPEC_v1.md
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_spec_coverage.py -k test_coverage_table_defined
# Expected: FAIL (test file does not exist yet)
```

### TDD Step 2 — Implement (minimal)

Add to spec:
1. Define canonical table: `Prose requirement | Source (file/section) | Implemented by task(s)`
2. Require Source to be anchored (`.md` file or strict section ID)
3. Require task references to match existing task IDs

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_spec_coverage.py
$ uv run pytest tests/ -q
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

**Status**: 📋 PLANNED

---

### Task 2.2 — Add coverage validation to linter

**Objective**: Add Prose Coverage Mapping validation (warning level) to linter.

**Paths**:
```bash
TASK_2_2_PATHS=(
  "ai_task_list_linter_v1_8.py"
)
```

**Scope**:
- In: Check header presence (allow aliases), validate Source anchors, verify task references exist
- Out: Spec changes (Task 2.1), documentation (Task 2.3)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'Prose Coverage' ai_task_list_linter_v1_8.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_linter_coverage.py -k test_coverage_validation
# Expected: FAIL (coverage validation not implemented)
```

### TDD Step 2 — Implement (minimal)

1. Add `_check_prose_coverage` function
2. In plan/instantiated modes: warn if header missing or empty
3. Validate Source contains `.md` or section anchor
4. Validate task references match parsed task IDs
5. Emit warnings (not errors) for malformed entries

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_linter_coverage.py
$ uv run pytest tests/ -q
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

**Status**: 📋 PLANNED

---

### Task 2.3 — Update orchestrator/manual for coverage

**Objective**: Document anchored source requirements and full task ID references.

**Paths**:
```bash
TASK_2_3_PATHS=(
  "PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md"
  "AI_ASSISTANT USER_MANUAL.md"
)
```

**Scope**:
- In: Instruct anchored sources, require full task IDs, update Prose Coverage Mapping section
- Out: Spec/linter changes (Tasks 2.1-2.2)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'anchored' PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md || true
```

### TDD Step 1 — Write test (RED)

```bash
$ rg 'anchored.*source' PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md
# Expected: no match
```

### TDD Step 2 — Implement (minimal)

1. Update Prose Coverage Mapping section in orchestrator
2. Add anchored source requirement (`.md` file or section ID)
3. Update manual Section 1.5 with validation guidance

### TDD Step 3 — Verify (GREEN)

```bash
$ rg 'anchored' PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md
$ rg 'anchored' "AI_ASSISTANT USER_MANUAL.md"
# Expected: PASS (matches found)
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

**Status**: 📋 PLANNED

---

## Phase 3 — Spec as SSOT

**Goal**: Align spec/linter versions, establish spec as authoritative SSOT
**Tests**: `uv run python ai_task_list_linter_v1_8.py <file>` / `uv run pytest tests/`

### Task 3.1 — Align spec and linter versions

**Objective**: Ensure spec version matches linter behavior; resolve version label conflicts.

**Paths**:
```bash
TASK_3_1_PATHS=(
  "AI_TASK_LIST_SPEC_v1.md"
  "ai_task_list_linter_v1_8.py"
)
```

**Scope**:
- In: Version labeling consistency, schema_version alignment, SSOT declaration
- Out: Documentation updates (Task 3.2)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'schema_version.*1\.6' AI_TASK_LIST_SPEC_v1.md
$ rg 'schema_version.*1\.6' ai_task_list_linter_v1_8.py
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_version_alignment.py -k test_spec_linter_versions_match
# Expected: FAIL (test file does not exist)
```

### TDD Step 2 — Implement (minimal)

1. Verify spec declares `schema_version: "1.6"`
2. Verify linter enforces `schema_version == "1.6"`
3. Add SSOT statement to spec: "Spec is SSOT; linter implements spec"
4. Remove any v1.0.0 vs v1.6 mismatches

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_version_alignment.py
$ uv run pytest tests/ -q
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

**Status**: 📋 PLANNED

---

### Task 3.2 — Document SSOT hierarchy in docs

**Objective**: Update README and docs to state spec+linter are authoritative.

**Paths**:
```bash
TASK_3_2_PATHS=(
  "README.md"
  "AI_ASSISTANT USER_MANUAL.md"
)
```

**Scope**:
- In: SSOT statement, spec/linter disagreement resolution rule
- Out: Spec/linter changes (Task 3.1)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'SSOT' README.md || true
```

### TDD Step 1 — Write test (RED)

```bash
$ rg 'Spec is SSOT' README.md
# Expected: no match
```

### TDD Step 2 — Implement (minimal)

1. Add SSOT statement to README
2. Update manual SSOT hierarchy section
3. Add rule: "If spec/linter disagree, fix linter"

### TDD Step 3 — Verify (GREEN)

```bash
$ rg 'SSOT' README.md
$ rg 'spec.*linter.*disagree' "AI_ASSISTANT USER_MANUAL.md"
# Expected: PASS (matches found)
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

**Status**: 📋 PLANNED

---

## Phase 4 — Gates and Runner Normalization

**Goal**: Fix gate patterns to fail-on-match; ensure runner/search_tool compliance
**Tests**: `uv run python ai_task_list_linter_v1_8.py <file>` / `uv run pytest tests/`

### Task 4.1 — Audit and fix gate patterns

**Objective**: Replace `&& exit 1 ||` patterns with fail-on-match gates.

**Paths**:
```bash
TASK_4_1_PATHS=(
  "AI_TASK_LIST_TEMPLATE_v6.md"
  "AI_TASK_LIST_SPEC_v1.md"
  "AI_ASSISTANT USER_MANUAL.md"
)
```

**Scope**:
- In: Gate pattern audit, replace with `! rg ...` or `if rg ...; then exit 1; fi`
- Out: Linter enforcement (documentation only)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg '&& exit 1 \|\|' AI_TASK_LIST_TEMPLATE_v6.md || true
```

### TDD Step 1 — Write test (RED)

```bash
$ rg '&& exit 1 \|\| (true|echo)' AI_TASK_LIST_TEMPLATE_v6.md AI_TASK_LIST_SPEC_v1.md
# Expected: matches if bad patterns exist
```

### TDD Step 2 — Implement (minimal)

1. Search all files for `&& exit 1 ||` patterns
2. Replace with proper fail-on-match patterns:
   - `! rg 'pattern' path/`
   - `if rg 'pattern' path/; then echo "ERROR"; exit 1; fi`
3. Document gate semantics in spec/manual

### TDD Step 3 — Verify (GREEN)

```bash
$ ! rg '&& exit 1 \|\| (true|echo)' AI_TASK_LIST_TEMPLATE_v6.md AI_TASK_LIST_SPEC_v1.md
$ uv run pytest tests/ -q
# Expected: PASS (no matches, tests pass)
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

**Status**: 📋 PLANNED

---

### Task 4.2 — Audit runner/search_tool compliance

**Objective**: Ensure all `$` examples use `uv run` and `rg` consistently.

**Paths**:
```bash
TASK_4_2_PATHS=(
  "AI_TASK_LIST_TEMPLATE_v6.md"
  "AI_TASK_LIST_SPEC_v1.md"
  "AI_ASSISTANT USER_MANUAL.md"
  "PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md"
)
```

**Scope**:
- In: Audit `$` command examples, fix non-compliant runner usage, mark legacy commands if retained
- Out: Linter changes

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg '^\$.*python\s+-m' AI_TASK_LIST_TEMPLATE_v6.md || true
$ rg '^\$.*grep' AI_TASK_LIST_TEMPLATE_v6.md || true
```

### TDD Step 1 — Write test (RED)

```bash
$ rg '^\$ (python|pytest|mypy|ruff|black)' AI_TASK_LIST_TEMPLATE_v6.md | rg -v 'uv run'
# Expected: matches if bare commands exist
```

### TDD Step 2 — Implement (minimal)

1. Search for bare `python`, `pytest`, etc. without `uv run`
2. Replace with `uv run python`, `uv run pytest`, etc.
3. Search for `grep` usage when `search_tool: "rg"`
4. Replace `grep` with `rg`
5. Mark any retained legacy examples as historical

### TDD Step 3 — Verify (GREEN)

```bash
$ ! rg '^\$ (python|pytest|mypy|ruff|black)\b' AI_TASK_LIST_TEMPLATE_v6.md
$ ! rg '^\$.*\bgrep\b' AI_TASK_LIST_TEMPLATE_v6.md
# Expected: PASS (no matches)
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

**Status**: 📋 PLANNED

---

## Phase 5 — Migration and User Guidance

**Goal**: Create decision tree, migration guide, and deprecation timeline
**Tests**: `uv run python ai_task_list_linter_v1_8.py <file>` / `uv run pytest tests/`

### Task 5.1 — Create mode decision tree

**Objective**: Document when to use template vs plan vs instantiated modes.

**Paths**:
```bash
TASK_5_1_PATHS=(
  "docs/MODE_DECISION_TREE.md"
)
```

**Scope**:
- In: Decision flowchart, lifecycle flow diagram, use case examples
- Out: Migration guide (Task 5.2), linter hints (Task 5.3)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'decision.*tree' docs/ || true
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f docs/MODE_DECISION_TREE.md
# Expected: FAIL (file does not exist)
```

### TDD Step 2 — Implement (minimal)

Create docs/MODE_DECISION_TREE.md with:
1. Decision flowchart (text-based)
2. Use cases for each mode
3. Lifecycle transition rules
4. Common mistakes to avoid

### TDD Step 3 — Verify (GREEN)

```bash
$ test -f docs/MODE_DECISION_TREE.md
$ rg 'template.*plan.*instantiated' docs/MODE_DECISION_TREE.md
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

**Status**: 📋 PLANNED

---

### Task 5.2 — Create migration guide

**Objective**: Document how to migrate existing task lists to plan mode; deprecation timeline.

**Paths**:
```bash
TASK_5_2_PATHS=(
  "docs/MIGRATION_GUIDE.md"
)
```

**Scope**:
- In: Migration steps, backward-compatibility notes, deprecation timeline (v1.6.1 add plan, v1.7.0 strict template)
- Out: Decision tree (Task 5.1), linter hints (Task 5.3)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'migration' docs/ || true
```

### TDD Step 1 — Write test (RED)

```bash
$ test -f docs/MIGRATION_GUIDE.md
# Expected: FAIL (file does not exist)
```

### TDD Step 2 — Implement (minimal)

Create docs/MIGRATION_GUIDE.md with:
1. How to flip "template with real commands" to plan
2. Deprecation timeline: v1.6.1 warn, v1.7.0 enforce
3. Backward-compatibility notes
4. Optional helper script reference

### TDD Step 3 — Verify (GREEN)

```bash
$ test -f docs/MIGRATION_GUIDE.md
$ rg 'deprecation' docs/MIGRATION_GUIDE.md
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

**Status**: 📋 PLANNED

---

### Task 5.3 — Add linter hint for plan mode

**Objective**: Linter suggests `mode: plan` when concrete commands found in template mode.

**Paths**:
```bash
TASK_5_3_PATHS=(
  "ai_task_list_linter_v1_8.py"
)
```

**Scope**:
- In: Detect concrete commands in template mode, emit suggestion message
- Out: Migration guide (Task 5.2)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'suggest.*plan' ai_task_list_linter_v1_8.py || true
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_linter_hints.py -k test_plan_mode_suggestion
# Expected: FAIL (hint not implemented)
```

### TDD Step 2 — Implement (minimal)

1. In template mode, detect concrete `$ rg`/`$ uv run` commands
2. If found, emit info message: "Consider using mode: plan for task lists with real commands"
3. Do not fail lint; info-level only

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_linter_hints.py
$ uv run pytest tests/ -q
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

**Status**: 📋 PLANNED

---

## Phase 6 — Validation Suite

**Goal**: Create comprehensive test suite for template/plan/instantiated modes
**Tests**: `uv run python ai_task_list_linter_v1_8.py <file>` / `uv run pytest tests/`

### Task 6.1 — Create positive test cases

**Objective**: Test files for template, plan, and instantiated modes that should pass.

**Paths**:
```bash
TASK_6_1_PATHS=(
  "tests/fixtures/valid_template.md"
  "tests/fixtures/valid_plan.md"
  "tests/fixtures/valid_instantiated.md"
  "tests/test_validation_suite.py"
)
```

**Scope**:
- In: Valid example files, pytest tests that verify lint passes
- Out: Negative tests (Task 6.2), doc-sync (Task 6.3)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'valid_template' tests/ || true
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_validation_suite.py -k test_valid_template_passes
# Expected: FAIL (fixture does not exist)
```

### TDD Step 2 — Implement (minimal)

1. Create tests/fixtures/valid_template.md (mode: template, all placeholders)
2. Create tests/fixtures/valid_plan.md (mode: plan, real commands, output placeholders)
3. Create tests/fixtures/valid_instantiated.md (mode: instantiated, all real)
4. Create pytest tests that run linter and assert exit 0

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_validation_suite.py -k test_valid
$ uv run python ai_task_list_linter_v1_8.py tests/fixtures/valid_template.md
$ uv run python ai_task_list_linter_v1_8.py tests/fixtures/valid_plan.md
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

**Status**: 📋 PLANNED

---

### Task 6.2 — Create negative test cases

**Objective**: Test files that should fail lint with specific error codes.

**Paths**:
```bash
TASK_6_2_PATHS=(
  "tests/fixtures/invalid_plan_with_command_placeholder.md"
  "tests/fixtures/invalid_template_bad_gates.md"
  "tests/test_validation_suite.py"
)
```

**Scope**:
- In: Invalid example files, pytest tests that verify lint fails with expected errors
- Out: Positive tests (Task 6.1), doc-sync (Task 6.3)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'invalid_plan' tests/ || true
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_validation_suite.py -k test_invalid_plan_fails
# Expected: FAIL (fixture does not exist)
```

### TDD Step 2 — Implement (minimal)

1. Create invalid_plan_with_command_placeholder.md (plan mode with `[[PH:SYMBOL_CHECK_COMMAND]]`)
2. Create invalid_template_bad_gates.md (template with `&& exit 1 || true`)
3. Create pytest tests that verify lint exit 1 and check error messages

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_validation_suite.py -k test_invalid
$ uv run python ai_task_list_linter_v1_8.py tests/fixtures/invalid_plan_with_command_placeholder.md; echo "exit: $?"
# Expected: exit 1
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

**Status**: 📋 PLANNED

---

### Task 6.3 — Create doc-sync check

**Objective**: Verify modes are referenced consistently across all docs.

**Paths**:
```bash
TASK_6_3_PATHS=(
  "tests/test_doc_sync.py"
)
```

**Scope**:
- In: Check all docs reference same mode names, lifecycle order
- Out: Positive/negative tests (Tasks 6.1-6.2)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'doc_sync' tests/ || true
```

### TDD Step 1 — Write test (RED)

```bash
$ uv run pytest tests/test_doc_sync.py -k test_mode_consistency
# Expected: FAIL (test file does not exist)
```

### TDD Step 2 — Implement (minimal)

1. Create test that searches all .md files for mode references
2. Verify template, plan, instantiated are mentioned consistently
3. Verify lifecycle order (template → plan → instantiated) is stated

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run pytest tests/test_doc_sync.py
$ uv run pytest tests/ -q
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

**Status**: 📋 PLANNED

---

### Task 6.4 — Create canonical example files

**Objective**: Create three lint-validated example files referenced from spec/docs.

**Paths**:
```bash
TASK_6_4_PATHS=(
  "examples/example_template.md"
  "examples/example_plan.md"
  "examples/example_instantiated.md"
)
```

**Scope**:
- In: Real-world example files, lint validation, spec/docs references
- Out: Test fixtures (separate from examples)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'examples/' AI_TASK_LIST_SPEC_v1.md || true
```

### TDD Step 1 — Write test (RED)

```bash
$ test -d examples && ls examples/*.md
# Expected: FAIL (directory/files do not exist)
```

### TDD Step 2 — Implement (minimal)

1. Create examples/ directory
2. Create example_template.md (minimal valid template)
3. Create example_plan.md (minimal valid plan)
4. Create example_instantiated.md (minimal valid instantiated)
5. Run linter on each; verify pass
6. Add references in spec and docs

### TDD Step 3 — Verify (GREEN)

```bash
$ uv run python ai_task_list_linter_v1_8.py examples/example_template.md
$ uv run python ai_task_list_linter_v1_8.py examples/example_plan.md
$ rg 'examples/' AI_TASK_LIST_SPEC_v1.md
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

**Status**: 📋 PLANNED

---

## Phase 7 — Critical Enumerations

**Goal**: Define and document critical enumeration handling
**Tests**: `uv run python ai_task_list_linter_v1_8.py <file>` / `uv run pytest tests/`

### Task 7.1 — Define critical enumeration criteria

**Objective**: Document what constitutes a critical enumeration and when to use markers.

**Paths**:
```bash
TASK_7_1_PATHS=(
  "AI_TASK_LIST_SPEC_v1.md"
  "AI_ASSISTANT USER_MANUAL.md"
)
```

**Scope**:
- In: Criteria definition (completeness required, order may matter, independently verifiable)
- Out: Marker implementation (Task 7.2)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'critical.*enumeration' AI_TASK_LIST_SPEC_v1.md || true
```

### TDD Step 1 — Write test (RED)

```bash
$ rg 'critical enumeration' AI_TASK_LIST_SPEC_v1.md
# Expected: no match
```

### TDD Step 2 — Implement (minimal)

Add to spec and manual:
1. Definition: "Critical enumeration = list where completeness is required"
2. Criteria: order may matter, items independently verifiable
3. Usage guidance: when to mark, verbatim copy rules

### TDD Step 3 — Verify (GREEN)

```bash
$ rg 'critical enumeration' AI_TASK_LIST_SPEC_v1.md
$ rg 'critical enumeration' "AI_ASSISTANT USER_MANUAL.md"
# Expected: PASS (matches found)
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

**Status**: 📋 PLANNED

---

### Task 7.2 — Document enumeration markers

**Objective**: Define marker syntax and instruct verbatim copy in orchestrator/manual.

**Paths**:
```bash
TASK_7_2_PATHS=(
  "AI_TASK_LIST_SPEC_v1.md"
  "PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md"
  "AI_ASSISTANT USER_MANUAL.md"
)
```

**Scope**:
- In: Marker syntax (`<!-- CRITICAL_ENUM:label -->`), copy instructions, optional count check
- Out: Criteria definition (Task 7.1)

**Preconditions** (evidence required — commands must use $ prefix when instantiated):
```bash
$ uv run pytest tests/ -q
$ rg 'CRITICAL_ENUM' AI_TASK_LIST_SPEC_v1.md || true
```

### TDD Step 1 — Write test (RED)

```bash
$ rg 'CRITICAL_ENUM' AI_TASK_LIST_SPEC_v1.md
# Expected: no match
```

### TDD Step 2 — Implement (minimal)

1. Define marker syntax: `<!-- CRITICAL_ENUM:label --> ... <!-- END_CRITICAL_ENUM -->`
2. Add to orchestrator: instruct verbatim copy of marked enumerations
3. Add to manual: marker usage guidance
4. Note optional linter check (count/presence) for plan/instantiated

### TDD Step 3 — Verify (GREEN)

```bash
$ rg 'CRITICAL_ENUM' AI_TASK_LIST_SPEC_v1.md
$ rg 'CRITICAL_ENUM' PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md
# Expected: PASS (matches found)
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

**Status**: 📋 PLANNED

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
  "test_command": "uv run python ai_task_list_linter_v1_8.py FIXES_MERGED_tasks.md",
  "result": "PASS"
}
EOF

# Verify no placeholders
$ if rg '\[\[PH:|YYYY-MM-DD|TBD' .phase-N.complete.json; then
>   echo "ERROR: Placeholder-like tokens found in artifact"
>   exit 1
> fi
```

---

## Global Clean Table Scan

Run before each phase gate (commands must use $ prefix when instantiated):

```bash
# Standard patterns (recommended for all projects; gates must fail on matches):
$ if rg 'TODO|FIXME|XXX' src/; then
>   echo "ERROR: Unfinished markers found"
>   exit 1
> fi

$ if rg '\[\[PH:' .; then
>   echo "ERROR: Placeholders found"
>   exit 1
> fi

# Import hygiene (required for Python/uv projects):
$ if rg 'from \.\.' src/; then
>   echo "ERROR: Multi-dot relative import found"
>   exit 1
> fi

$ if rg 'import \*' src/; then
>   echo "ERROR: Wildcard import found"
>   exit 1
> fi

# Expected: zero matches (gates pass)
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
