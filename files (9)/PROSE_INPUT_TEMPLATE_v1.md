---
prose_input:
  schema_version: "1.0"
  project_name: "[[PROJECT_NAME]]"
  runner: "uv"                    # uv | npm | cargo | go | poetry
  runner_prefix: "uv run"         # Command prefix for runner (empty string allowed for go/cargo)
  search_tool: "rg"               # rg | grep
  python_version: "3.12"          # Optional: for Python projects
---

<!--
PROSE INPUT TEMPLATE v1.0

This is a STRICT input format for the AI Task List Framework.
The structure here maps 1:1 to task list output - conversion is deterministic.

RULES:
1. All sections are REQUIRED unless marked (optional)
2. No free-form prose - only structured fields
3. No TBD/TODO/TBC markers - resolve before submission
4. No questions - all decisions must be made
5. No conditional language (if/maybe/might/could)
6. No time estimates - only completion criteria

Validate with: uv run python tools/prose_input_linter.py YOUR_FILE.md
-->

# [[PROJECT_NAME]] — Implementation Specification

## SSOT Declaration

<!-- What is this document authoritative for? Be specific. -->

| Scope | Authoritative Source |
|-------|---------------------|
| Implementation plan | This document |
| Schema shape | `[[PATH_TO_SCHEMA_FILE]]` |
| Test fixtures | `[[PATH_TO_FIXTURES]]` |

**Supersedes**: [[LIST_OF_DEPRECATED_DOCS_OR_NONE]]

---

## Scope

### In Scope

<!-- Explicit list of what WILL be implemented. One item per line. -->

- [ ] [[FEATURE_1]]
- [ ] [[FEATURE_2]]
- [ ] [[FEATURE_3]]

### Out of Scope

<!-- Explicit list of what will NOT be implemented. Required even if empty. -->

- [[EXCLUDED_1]] — Reason: [[WHY_EXCLUDED]]
- [[EXCLUDED_2]] — Deferred to: [[FUTURE_PHASE_OR_VERSION]]

### Constraints

<!-- Non-functional requirements, limitations, must-not-do items -->

| Constraint | Description | Enforcement |
|------------|-------------|-------------|
| No breaking changes | Public API must remain compatible | CI schema diff check |
| Python 3.12+ only | No backports | pyproject.toml requires-python |
| [[CONSTRAINT_N]] | [[DESCRIPTION]] | [[HOW_ENFORCED]] |

---

## Decisions (Binding)

<!--
All decisions must be FINAL. No "pending" or "to be decided".
Each decision must have a rationale.
-->

| ID | Decision | Rationale | Alternatives Rejected |
|----|----------|-----------|----------------------|
| D1 | [[DECISION_1]] | [[WHY]] | [[WHAT_ELSE_CONSIDERED]] |
| D2 | [[DECISION_2]] | [[WHY]] | [[WHAT_ELSE_CONSIDERED]] |

---

## External Dependencies

<!--
Pre-existing resources that MUST exist before work begins.
These are NOT created by this spec - they are PREREQUISITES.
Enables precondition validation and environment setup.
-->

### Required Files/Modules

<!-- Existing source files this work depends on -->

| Path | Required Symbol(s) | Purpose |
|------|-------------------|---------|
| `src/[[MODULE]]/__init__.py` | `[[CLASS_OR_FUNC]]` | [[WHY_NEEDED]] |
| `[[PATH_TO_CONFIG]]` | — | Configuration file |

### Required Directories

<!-- Folder structure that must exist -->

| Path | Contents | Notes |
|------|----------|-------|
| `src/[[MODULE]]/` | Package root | Must be importable |
| `tests/` | Test directory | pytest discovers here |

### Required Libraries

<!-- Python packages from pyproject.toml / requirements -->

| Package | Version | Purpose |
|---------|---------|---------|
| `[[PACKAGE_1]]` | `[[VERSION]]` | [[PURPOSE]] |
| `[[PACKAGE_2]]` | `[[VERSION]]` | [[PURPOSE]] |

### Required Tools

<!-- CLI tools that must be installed -->

| Tool | Version | Verification Command |
|------|---------|---------------------|
| `[[TOOL_1]]` | `[[VERSION]]` | `[[VERIFY_COMMAND]]` |
| `[[TOOL_2]]` | `[[VERSION]]` | `[[VERIFY_COMMAND]]` |

### External Services (optional)

<!-- APIs, databases, external systems - if applicable -->

| Service | Purpose | Local Alternative |
|---------|---------|-------------------|
| — | — | — |

---

## Sample Artifacts

<!--
PASTE actual outputs here - not descriptions. These are FACTS from your codebase.
Run PROSE_INPUT_DISCOVERY_PROMPT_v1.md to gather these.

Why: AI would otherwise have to run commands/search to discover this.
Pasting facts eliminates guessing and reduces iteration loops.
-->

### Current Output Shape (if implementing schema/validation)

<!-- Paste actual JSON/output from running your code on sample input -->

```json
[[PASTE_ACTUAL_OUTPUT_OR_REMOVE_SECTION]]
```

### Existing Files in Target Directory

<!-- Output of: ls -la [[TARGET_DIR]]/ -->

```
[[PASTE_LS_OUTPUT]]
```

### Existing Test Files

<!-- Output of: ls tests/test_*.py or similar -->

```
[[PASTE_TEST_FILE_LIST]]
```

### Current Config/Dependencies Section

<!-- Paste relevant section from pyproject.toml, package.json, etc. -->

```toml
[[PASTE_DEPENDENCIES_SECTION]]
```

---

## File Manifest

<!--
All files that will be CREATED or MODIFIED by this spec.
This becomes the source for TASK_N_M_PATHS arrays.
-->

| Path | Action | Phase | Description |
|------|--------|-------|-------------|
| `src/[[MODULE]]/[[FILE]].py` | CREATE | 1 | [[PURPOSE]] |
| `tests/test_[[FILE]].py` | CREATE | 1 | [[TEST_PURPOSE]] |
| `tools/[[TOOL]].py` | CREATE | 0 | [[TOOL_PURPOSE]] |

---

## Test Strategy

<!--
How will correctness be verified? Required for TDD structure.
-->

| Layer | Tool | Location | Trigger |
|-------|------|----------|---------|
| Unit tests | pytest | `tests/unit/` | Pre-commit, CI |
| Integration tests | pytest | `tests/integration/` | CI only |
| Type checking | mypy | `src/` | Pre-commit, CI |
| Linting | ruff | `src/`, `tests/` | Pre-commit |
| Schema validation | [[TOOL]] | [[LOCATION]] | [[TRIGGER]] |

---

## Phase 0 — [[PHASE_0_NAME]]

### Goal

<!-- One sentence. What is the exit condition for this phase? -->

[[SINGLE_SENTENCE_GOAL]]

### Phase 0 Success Criteria

<!-- All must be true to unlock Phase 1 -->

- [ ] [[CRITERION_1]]
- [ ] [[CRITERION_2]]
- [ ] [[CRITERION_3]]

### Tasks

#### Task 0.1 — [[TASK_NAME]]

| Field | Value |
|-------|-------|
| **Objective** | [[ONE_SENTENCE_OBJECTIVE]] |
| **Type** | Bootstrap / Discovery / Setup |
| **Paths** | `[[PATH_1]]`, `[[PATH_2]]` |

**Outputs** (artifacts this task produces):

- `[[OUTPUT_FILE_1]]` — [[DESCRIPTION]]
- `[[OUTPUT_FILE_2]]` — [[DESCRIPTION]]

**Success Criteria**:

- [ ] [[MEASURABLE_CRITERION_1]]
- [ ] [[MEASURABLE_CRITERION_2]]

**Commands**:

```bash
# Setup/Discovery command
$ [[ACTUAL_COMMAND]]
```

---

#### Task 0.2 — [[TASK_NAME]]

| Field | Value |
|-------|-------|
| **Objective** | [[ONE_SENTENCE_OBJECTIVE]] |
| **Type** | Bootstrap / Discovery / Setup |
| **Paths** | `[[PATH_1]]` |

**Outputs**:

- `[[OUTPUT_FILE]]` — [[DESCRIPTION]]

**Success Criteria**:

- [ ] [[CRITERION]]

**Commands**:

```bash
$ [[COMMAND]]
```

---

## Phase 1 — [[PHASE_1_NAME]]

### Goal

[[SINGLE_SENTENCE_GOAL]]

### Dependencies

<!-- What must be complete before this phase can start? -->

| Dependency | Type | Verification |
|------------|------|--------------|
| Phase 0 complete | Phase gate | `.phase-0.complete.json` exists |
| [[DEPENDENCY]] | [[TYPE]] | [[HOW_TO_CHECK]] |

### Phase 1 Success Criteria

- [ ] [[CRITERION_1]]
- [ ] [[CRITERION_2]]
- [ ] All Phase 1 tasks ✅ COMPLETE
- [ ] Full test suite passes
- [ ] No regressions in existing functionality

### Tasks

#### Task 1.1 — [[TASK_NAME]]

| Field | Value |
|-------|-------|
| **Objective** | [[ONE_SENTENCE_OBJECTIVE]] |
| **Type** | Implementation / Refactor / Test |
| **Paths** | `[[PATH_1]]`, `[[PATH_2]]` |

**Precondition** (symbol check before implementation):

```bash
# Verify required symbols/APIs exist
$ rg -n '[[SYMBOL_TO_CHECK]]' [[FILE_TO_CHECK]]
```

**TDD Specification**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| RED | Write test `test_[[NAME]]` in `[[TEST_FILE]]` | Test fails (feature not implemented) |
| GREEN | Implement `[[FUNCTION/CLASS]]` in `[[SOURCE_FILE]]` | Test passes |
| VERIFY | Run full suite | All tests pass, no regressions |

**Test Cases** (concrete test names and assertions):

```python
# In [[TEST_FILE]]

def test_[[NAME]]_[[SCENARIO_1]]():
    """[[WHAT_IT_TESTS]]."""
    # Arrange
    [[SETUP]]
    # Act
    result = [[ACTION]]
    # Assert
    assert [[ASSERTION]]

def test_[[NAME]]_[[SCENARIO_2]]_[[NEGATIVE_CASE]]():
    """[[NEGATIVE_CASE_DESCRIPTION]]."""
    # Arrange
    [[SETUP]]
    # Act & Assert
    with pytest.raises([[EXCEPTION]]):
        [[ACTION]]
```

**Success Criteria**:

- [ ] `[[SOURCE_FILE]]` exists with `[[SYMBOL]]`
- [ ] `[[TEST_FILE]]` exists with passing tests
- [ ] `rg -n '[[SYMBOL]]' [[SOURCE_FILE]]` returns matches
- [ ] `uv run pytest [[TEST_FILE]] -v` passes
- [ ] `uv run mypy [[SOURCE_FILE]]` passes

**Clean Table Verification**:

```bash
# Run after implementation
$ uv run pytest [[TEST_FILE]] -v
$ uv run mypy [[SOURCE_FILE]]
$ rg 'TODO|FIXME' [[SOURCE_FILE]] [[TEST_FILE]]  # Must return empty
```

---

#### Task 1.2 — [[TASK_NAME]]

<!-- Same structure as Task 1.1 -->

| Field | Value |
|-------|-------|
| **Objective** | [[ONE_SENTENCE_OBJECTIVE]] |
| **Type** | Implementation / Refactor / Test |
| **Paths** | `[[PATH_1]]` |

**Precondition**:

```bash
$ rg -n '[[SYMBOL]]' [[FILE]]
```

**TDD Specification**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| RED | [[ACTION]] | [[EXPECTED]] |
| GREEN | [[ACTION]] | [[EXPECTED]] |
| VERIFY | [[ACTION]] | [[EXPECTED]] |

**Test Cases**:

```python
def test_[[NAME]]():
    """[[DESCRIPTION]]."""
    assert [[ASSERTION]]
```

**Success Criteria**:

- [ ] [[CRITERION_1]]
- [ ] [[CRITERION_2]]

**Clean Table Verification**:

```bash
$ [[VERIFICATION_COMMAND]]
```

---

## Phase N — [[PHASE_N_NAME]]

<!-- Repeat Phase structure as needed -->

### Goal

[[GOAL]]

### Dependencies

| Dependency | Type | Verification |
|------------|------|--------------|
| Phase N-1 complete | Phase gate | `.phase-N-1.complete.json` exists |

### Tasks

#### Task N.1 — [[NAME]]

<!-- Same task structure -->

---

## Drift Provisions

<!--
Pre-identified risks and how they'll be handled.
Becomes seed content for Drift Ledger.
-->

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [[RISK_1]] | [[LIKELIHOOD]] | [[IMPACT]] | [[MITIGATION]] |
| [[RISK_2]] | [[LIKELIHOOD]] | [[IMPACT]] | [[MITIGATION]] |

---

## Glossary

<!-- Define project-specific terms to prevent ambiguity -->

| Term | Definition |
|------|------------|
| [[TERM_1]] | [[DEFINITION_1]] |
| [[TERM_2]] | [[DEFINITION_2]] |

---

## Checklist Before Submission

<!--
Author must check all boxes before submitting for conversion.
Linter enforces this.
-->

- [ ] All `[[PLACEHOLDER]]` tokens replaced with real values
- [ ] No TBD/TODO/TBC markers remain
- [ ] No questions (lines ending with `?`) remain
- [ ] All decisions in Decisions table are final
- [ ] External Dependencies section lists all prerequisites
- [ ] Required libraries match pyproject.toml / requirements
- [ ] Required tools have verification commands
- [ ] All paths in File Manifest exist or will be created
- [ ] All test cases have concrete assertions
- [ ] All success criteria are measurable (not subjective)
- [ ] Dependencies between phases are explicit
- [ ] Glossary defines all project-specific terms

---

**End of Specification**
