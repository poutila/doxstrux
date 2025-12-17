# STRICT_SPECS.md — Plan for SPEKSI-Compliant Spec Governance

> **Purpose**: Step-by-step plan to adopt SPEKSI format and create linter specs for internal drift prevention.
> **Status**: PLAN (Updated)
> **Created**: 2025-12-16
> **Updated**: 2025-12-16

---

## Rationale

AI_TASK_LIST_GOAL_SPEKSI.md §A.1 states the framework targets output that:
- Remains faithful to input prose
- Reflects repository reality
- Can be checked deterministically via linter against spec
- Embeds governance expectations

This goal applies to the **framework itself**. SPEKSI provides structural governance. Adopting it prevents framework self-drift.

---

## Architecture Decision

**Extension Pattern**: Protocol with Composition

```
KERNEL_LINTER_SPEC.md (trimmed to our needs)
        ↓
kernel_linter.py (Protocol-based, composable)
        ↓
   ┌────┴────┐
   │         │
AI_TASK_LIST_LINTER_SPEC.md    PROSE_INPUT_LINTER_SPEC.md
   ↓                            ↓
ai_task_list_linter.py         prose_input_linter.py
(composes kernel)              (composes kernel)
```

**Why Protocol**:
- Composition over inheritance
- Structural typing (no tight coupling)
- Type-safe (mypy verifiable)
- Easy to test each layer independently

---

## Phase 0: Prerequisites (DONE)

### Task 0.1 — Verify Local Tooling

**Status**: COMPLETE

- kernel_linter.py exists at `tools/kernel_linter.py`
- Runs successfully: `uv run python tools/kernel_linter.py <spec.md>`

### Task 0.2 — Document Current State

**Status**: COMPLETE

- Original specs archived (if needed)
- SPEKSI proposals created and validated

---

## Phase 1: Reformat Document Specs (DONE)

### Task 1.1 — AI_TASK_LIST_SPEC SPEKSI Format

**Status**: COMPLETE

- File: `AI_TASK_LIST_SPEC_SPEKSI_proposal.md`
- Passes kernel_linter: YES
- Structure: §M META, §A ARCHITECTURE, §D DEFINITIONS, §R RULES, §V VALIDATION, §C CHANGELOG, §G GLOSSARY

### Task 1.2 — PROSE_INPUT_SPEC SPEKSI Format

**Status**: COMPLETE

- File: `PROSE_INPUT_SPEC_SPEKSI_proposal.md`
- Passes kernel_linter: YES
- Structure: Same as above

---

## Phase 2: Kernel Layer

### Task 2.1 — Trim KERNEL_LINTER_SPEC.md

**Objective**: Remove unused SPEKSI features, keep what we need.

**Remove**:
- §2.1 Mandatory Section Checks (§5 FACTS-ONLY requirement)
- §2.2 Facts-Only Enforcement
- §2.5 Fence-Free Constraint

**Keep**:
- §2.6 Input Processing Rules (R-LINT-IN-*)
- §2.7 Parsing Rules (R-LINT-PARSE-*)
- §2.8 Rule Enforcement (R-LINT-STR/REF/CON/PAT-*)
- §2.9 Exemption Rules (R-LINT-EX-*)
- §2.10 Definition Detection Rules (R-LINT-DEF-*)
- §2.11 Output Rules (R-LINT-OUT-*)

**Success Criteria**:
- [ ] Trimmed spec passes kernel_linter
- [ ] Spec reflects actual kernel_linter.py behavior

### Task 2.2 — Refactor kernel_linter.py to Protocol Pattern

**Objective**: Make kernel linter composable for domain linters.

**Structure**:
```python
from typing import Protocol

class LintError:
    line: int
    code: str
    message: str
    def format(self, path: Path) -> str: ...

class Section:
    token: str
    title: str
    level: int
    start_line: int
    end_line: int
    parent_idx: int | None
    layer_type: str | None

class KernelLinter(Protocol):
    def collect_sections(self, text: str) -> list[Section]: ...
    def check_tier_declared(self, text: str) -> list[LintError]: ...
    def check_rule_and_invariant_ids(self, text: str, sections: list[Section]) -> tuple[list[LintError], dict, dict]: ...
    def check_reference_integrity(self, text: str, sections: list[Section], rule_defs: dict, inv_defs: dict, is_framework: bool) -> list[LintError]: ...
    def check_anchored_constraints(self, text: str, sections: list[Section]) -> list[LintError]: ...
    def strip_code_blocks(self, text: str) -> tuple[str, list]: ...

class DefaultKernelLinter:
    """Default implementation of KernelLinter protocol."""
    # Existing logic refactored into methods
```

**Success Criteria**:
- [ ] Protocol defined
- [ ] DefaultKernelLinter implements protocol
- [ ] Existing CLI behavior unchanged
- [ ] All current tests pass (if any)

---

## Phase 3: Domain Linter Specs

### Task 3.1 — Create AI_TASK_LIST_LINTER_SPEC.md

**Objective**: Spec defining ai_task_list_linter.py behavior.

**Structure**:
```
## §M META
## §D DEFINITIONS
- Domain-specific patterns (task ID, phase heading, etc.)
## §R RULES
- §R.1 Kernel Integration (composes KernelLinter)
- §R.2 R-ATL-* Rule Enforcement
  - Table: R-ATL-* Rule ID | Check Function | Test Case
- §R.3 Mode Semantics (template/plan/instantiated)
## §V VALIDATION
## §C CHANGELOG
## §G GLOSSARY
```

**Key Content**:
- Every R-ATL-* rule from AI_TASK_LIST_SPEC maps to a check function
- Test matrix: rule → test case

**Success Criteria**:
- [ ] Passes kernel_linter
- [ ] Every R-ATL-* rule has implementation mapping
- [ ] Every R-ATL-* rule has test case mapping

### Task 3.2 — Create PROSE_INPUT_LINTER_SPEC.md

**Objective**: Spec defining prose_input_linter.py behavior.

**Structure**: Same as Task 3.1, adapted for PIN-* rules.

**Success Criteria**:
- [ ] Passes kernel_linter
- [ ] Every PIN-* rule has implementation mapping
- [ ] Every PIN-* rule has test case mapping

---

## Phase 4: Domain Linter Implementation

### Task 4.1 — Implement ai_task_list_linter.py

**Objective**: New linter extending kernel via composition.

**Structure**:
```python
from kernel_linter import DefaultKernelLinter, KernelLinter, LintError, Section

class AITaskListLinter:
    def __init__(self, kernel: KernelLinter | None = None):
        self.kernel = kernel or DefaultKernelLinter()

    def lint(self, path: Path, mode: str = "plan") -> int:
        text = path.read_text()
        errors: list[LintError] = []

        # Kernel checks
        stripped, _ = self.kernel.strip_code_blocks(text)
        sections = self.kernel.collect_sections(stripped)
        errors.extend(self.kernel.check_tier_declared(stripped))
        # ... more kernel checks

        # Domain checks (R-ATL-*)
        errors.extend(self.check_phase_headings(stripped, sections))
        errors.extend(self.check_task_ids(stripped, sections))
        errors.extend(self.check_tdd_steps(stripped, sections, mode))
        # ... more domain checks

        return 0 if not errors else 1

    # R-ATL-* check methods
    def check_phase_headings(self, text: str, sections: list[Section]) -> list[LintError]: ...
    def check_task_ids(self, text: str, sections: list[Section]) -> list[LintError]: ...
    def check_tdd_steps(self, text: str, sections: list[Section], mode: str) -> list[LintError]: ...
```

**Success Criteria**:
- [ ] Composes kernel linter
- [ ] Implements all R-ATL-* checks
- [ ] CLI: `uv run python ai_task_list_linter.py [--mode MODE] <file.md>`
- [ ] Exit codes: 0=pass, 1=fail, 2=usage error

### Task 4.2 — Implement prose_input_linter.py

**Objective**: New linter extending kernel via composition.

**Structure**: Same pattern as Task 4.1, with PIN-* checks.

**Success Criteria**:
- [ ] Composes kernel linter
- [ ] Implements all PIN-* checks
- [ ] CLI: `uv run python prose_input_linter.py <file.md>`
- [ ] Exit codes: 0=pass, 1=fail, 2=usage error

### Task 4.3 — Delete Old Linters

**Objective**: Remove superseded implementations.

**Files to delete**:
- `tools/ai_task_list_linter.py` (1236 lines)
- `tools/prose_input_linter.py` (815 lines)

**Success Criteria**:
- [ ] Old files removed
- [ ] No references to old linters remain

---

## Phase 5: Alignment Verification

### Task 5.1 — Verify Spec↔Linter Alignment

**Objective**: Confirm linters implement all spec rules.

**Steps**:
1. Extract all R-ATL-* rule IDs from AI_TASK_LIST_SPEC_SPEKSI_proposal.md
2. Verify each has check function in ai_task_list_linter.py
3. Verify each has test case
4. Repeat for PIN-* rules

**Success Criteria**:
- [ ] 100% rule coverage
- [ ] No orphan rules (spec but not linter)
- [ ] No phantom rules (linter but not spec)

### Task 5.2 — Verify Template Compliance

**Objective**: Templates pass their linters.

**Steps**:
1. Run ai_task_list_linter.py on AI_TASK_LIST_TEMPLATE.md (mode=template)
2. Run prose_input_linter.py on PROSE_INPUT_TEMPLATE.md
3. Fix any violations

**Success Criteria**:
- [ ] Templates pass in appropriate mode

### Task 5.3 — Update COMMON.md

**Objective**: File table reflects new architecture.

**Add**:
- AI_TASK_LIST_LINTER_SPEC.md
- PROSE_INPUT_LINTER_SPEC.md

**Update descriptions** for linter files.

---

## Phase 6: CI Integration (Optional)

### Task 6.1 — Create validate_framework.py

**Objective**: Single command validates entire framework.

**Checks**:
1. All specs pass kernel_linter
2. All linter specs pass kernel_linter
3. Templates pass domain linters
4. Rule coverage is 100%

**Success Criteria**:
- [ ] Exit 0 = framework consistent
- [ ] Exit 1 = drift detected

---

## Dependency Graph

```
Phase 0 (Prerequisites) ................ DONE
    │
    ▼
Phase 1 (Reformat Document Specs) ...... DONE
    │
    ▼
Phase 2 (Kernel Layer)
    ├── Task 2.1: Trim KERNEL_LINTER_SPEC.md
    └── Task 2.2: Refactor kernel_linter.py (Protocol)
    │
    ▼
Phase 3 (Domain Linter Specs)
    ├── Task 3.1: AI_TASK_LIST_LINTER_SPEC.md
    └── Task 3.2: PROSE_INPUT_LINTER_SPEC.md
    │
    ▼
Phase 4 (Domain Linter Implementation)
    ├── Task 4.1: ai_task_list_linter.py (new)
    ├── Task 4.2: prose_input_linter.py (new)
    └── Task 4.3: Delete old linters
    │
    ▼
Phase 5 (Alignment Verification)
    ├── Task 5.1: Spec↔Linter alignment
    ├── Task 5.2: Template compliance
    └── Task 5.3: Update COMMON.md
    │
    ▼
Phase 6 (CI Integration) [Optional]
    └── Task 6.1: validate_framework.py
```

---

## Deliverables Summary

| Phase | Deliverable | Type | Status |
|-------|-------------|------|--------|
| 1 | AI_TASK_LIST_SPEC_SPEKSI_proposal.md | Spec | DONE |
| 1 | PROSE_INPUT_SPEC_SPEKSI_proposal.md | Spec | DONE |
| 2 | KERNEL_LINTER_SPEC.md (trimmed) | Update | TODO |
| 2 | kernel_linter.py (Protocol) | Update | TODO |
| 3 | AI_TASK_LIST_LINTER_SPEC.md | **New** | TODO |
| 3 | PROSE_INPUT_LINTER_SPEC.md | **New** | TODO |
| 4 | ai_task_list_linter.py | **New** | TODO |
| 4 | prose_input_linter.py | **New** | TODO |
| 5 | Updated COMMON.md | Update | TODO |
| 6 | validate_framework.py | **New** | Optional |

---

## Success Metrics

When complete:
1. All specs pass kernel_linter (exit 0)
2. Protocol pattern enables composition without inheritance
3. Every rule ID has: spec definition → linter function → test case
4. Templates pass their domain linters
5. Old linters deleted, no duplication

---

**End of Plan**
