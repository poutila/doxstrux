# STRICT_SPECS.md — Plan for SPEKSI-Compliant Spec Governance

> **Purpose**: Step-by-step plan to adopt SPEKSI format and create linter specs for internal drift prevention.
> **Status**: PLAN
> **Created**: 2025-12-16

---

## Rationale

GOAL.md §1 states: "Does not drift — Output remains faithful to input."

This goal applies to the **framework itself**, not just its outputs. Currently:
- Document specs exist but have no formal linter-spec alignment
- No automated way to verify linter implements all spec rules
- Cross-document references are not validated
- Internal drift is possible and undetected

SPEKSI provides battle-tested governance. Adopting it prevents framework self-drift.

---

## Phase 0: Prerequisites

### Task 0.1 — Verify SPEKSI Access

**Objective**: Confirm SPEKSI linters are accessible and working.

**Steps**:
1. Verify `kernel_linter.py` exists at `/home/lasse/Dropbox/python/omat/SPEKSI/src/speksi/tools/`
2. Verify `framework_linter.py` exists at same location
3. Run: `python kernel_linter.py --help` (confirm working)
4. Run: `python framework_linter.py --help` (confirm working)

**Success Criteria**:
- [ ] Both linters execute without error
- [ ] Help output shows expected modes (spec, plan, consistency)

### Task 0.2 — Document Current State

**Objective**: Snapshot current specs before modification.

**Steps**:
1. Copy current `AI_TASK_LIST_SPEC.md` to `archive/AI_TASK_LIST_SPEC_v1.md`
2. Copy current `PROSE_INPUT_SPEC.md` to `archive/PROSE_INPUT_SPEC_v1.md`
3. Record current rule counts:
   - AI_TASK_LIST_SPEC.md: Count R-ATL-* rules
   - PROSE_INPUT_SPEC.md: Count PIN-* rules

**Success Criteria**:
- [ ] Archives created
- [ ] Rule counts documented

---

## Phase 1: Reformat Document Specs to SPEKSI Structure

### Task 1.1 — Reformat AI_TASK_LIST_SPEC.md

**Objective**: Convert to SPEKSI-compliant structure.

**Reference**: Use SPEKSI_KERNEL.md and SPEKSI_FRAMEWORK.md as templates.

**Steps**:
1. Add SPEKSI header block:
   ```
   **Version**: 2.0.0
   **Status**: DRAFT
   **Tier**: FULL
   **Kernel-Version**: 1.0
   ```

2. Restructure sections with § prefixes:
   - `## §0 META` — Add Layer Mapping, Frozen Layers, Linter Integration
   - `## §1 DEFINITIONS` — Move definitions section
   - `## §2 RULES` — Consolidate all R-ATL-* rules
   - `## §3 IMPLEMENTATION` — Mode lifecycle, validation phases
   - `## §4 TESTS` — Add test matrix (rule → test case mapping)
   - `## §5 VALIDATION` — Compliance checklists
   - `## §C CHANGELOG` — Version history
   - `## §G GLOSSARY` — Term definitions

3. Preserve all existing R-ATL-* rule IDs (no renaming)

4. Add cross-references using SPEKSI format:
   - `→ §X.Y` for section references
   - `(per R-ATL-XXX)` for rule references

**Success Criteria**:
- [ ] Passes `kernel_linter.py` with exit 0
- [ ] All original R-ATL-* rules preserved
- [ ] Layer Mapping table present
- [ ] CHANGELOG section present
- [ ] GLOSSARY section present

### Task 1.2 — Reformat PROSE_INPUT_SPEC.md

**Objective**: Convert to SPEKSI-compliant structure.

**Steps**: Same as Task 1.1, adapted for PIN-* rule namespace.

**Success Criteria**:
- [ ] Passes `kernel_linter.py` with exit 0
- [ ] All original PIN-* rules preserved
- [ ] Layer Mapping table present
- [ ] CHANGELOG section present
- [ ] GLOSSARY section present

### Task 1.3 — Validate Reformatted Specs

**Objective**: Confirm SPEKSI compliance.

**Steps**:
1. Run: `kernel_linter.py AI_TASK_LIST_SPEC.md`
2. Run: `kernel_linter.py PROSE_INPUT_SPEC.md`
3. Fix any violations
4. Run: `framework_linter.py spec AI_TASK_LIST_SPEC.md`
5. Run: `framework_linter.py spec PROSE_INPUT_SPEC.md`
6. Fix any violations

**Success Criteria**:
- [ ] Both specs pass kernel_linter (exit 0)
- [ ] Both specs pass framework_linter spec mode (exit 0)

---

## Phase 2: Create Linter Specs

### Task 2.1 — Create AI_TASK_LIST_LINTER_SPEC.md

**Objective**: Spec defining `ai_task_list_linter.py` behavior.

**Reference**: Use KERNEL_LINTER_SPEC.md as template.

**Structure**:
```
## §0 META
- Layer Mapping, Frozen Layers, Linter Integration

## §1 DEFINITIONS
- Input schema (LintInput)
- Output schema (LintResult, LintError)
- Pattern constants (regexes used)

## §2 RULES
- §2.1 Input Processing Rules (R-LINT-IN-*)
- §2.2 Parsing Rules (R-LINT-PARSE-*)
- §2.3 Rule Enforcement (R-LINT-ENF-*)
  - Table: Rule ID | Linter Function | Implementation Status
- §2.4 Output Rules (R-LINT-OUT-*)
- §2.5 Exemption Rules (R-LINT-EX-*)

## §3 IMPLEMENTATION
- Validation phases
- Function responsibilities

## §4 TESTS
- Test matrix: Rule ID | Test Case | Expected Behavior
- Regression tests
- Property-based tests (optional)

## §5 VALIDATION
- Code-spec alignment checklist
- Test coverage checklist

## §C CHANGELOG
## §G GLOSSARY
```

**Key Content**:
1. Extract all R-ATL-* rules from AI_TASK_LIST_SPEC.md
2. For each rule, document:
   - Which linter function implements it
   - What test case verifies it
3. Document exit codes, error format, JSON output

**Success Criteria**:
- [ ] Passes `kernel_linter.py` (exit 0)
- [ ] Every R-ATL-* rule has implementation mapping
- [ ] Every R-ATL-* rule has test case mapping
- [ ] Test matrix is complete (no gaps)

### Task 2.2 — Create PROSE_INPUT_LINTER_SPEC.md

**Objective**: Spec defining `prose_input_linter.py` behavior.

**Steps**: Same as Task 2.1, adapted for PIN-* rules.

**Success Criteria**:
- [ ] Passes `kernel_linter.py` (exit 0)
- [ ] Every PIN-* rule has implementation mapping
- [ ] Every PIN-* rule has test case mapping
- [ ] Test matrix is complete (no gaps)

### Task 2.3 — Validate Linter Specs

**Objective**: Confirm linter specs are SPEKSI-compliant.

**Steps**:
1. Run `kernel_linter.py` on both linter specs
2. Run `framework_linter.py spec` on both linter specs
3. Fix any violations

**Success Criteria**:
- [ ] Both linter specs pass all SPEKSI linters

---

## Phase 3: Alignment Verification

### Task 3.1 — Verify Linter↔Spec Alignment

**Objective**: Confirm linters implement all spec rules.

**Steps**:
1. Extract all R-ATL-* rule IDs from AI_TASK_LIST_SPEC.md
2. For each rule, verify:
   - Listed in AI_TASK_LIST_LINTER_SPEC.md §2.3 table
   - Function exists in `ai_task_list_linter.py`
   - Test exists for the rule
3. Repeat for PIN-* rules and prose_input_linter.py

**Success Criteria**:
- [ ] 100% rule coverage in linter specs
- [ ] No orphan rules (in spec but not linter)
- [ ] No phantom rules (in linter but not spec)

### Task 3.2 — Verify Template↔Spec Alignment

**Objective**: Confirm templates pass their own linters.

**Steps**:
1. Run: `prose_input_linter.py PROSE_INPUT_TEMPLATE.md`
2. Run: `ai_task_list_linter.py AI_TASK_LIST_TEMPLATE.md --mode template`
3. Fix any violations in templates

**Success Criteria**:
- [ ] Templates pass linters in template mode

### Task 3.3 — Update COMMON.md

**Objective**: Add new files to framework file table.

**Steps**:
1. Add `AI_TASK_LIST_LINTER_SPEC.md` to file table
2. Add `PROSE_INPUT_LINTER_SPEC.md` to file table
3. Update any changed file descriptions

**Success Criteria**:
- [ ] COMMON.md file table is accurate

---

## Phase 4: CI Integration (Optional)

### Task 4.1 — Create Validation Script

**Objective**: Single script that validates entire framework.

**Script**: `tools/validate_framework.py`

**Checks**:
1. All specs pass kernel_linter
2. All specs pass framework_linter
3. All templates pass their linters
4. Rule coverage is 100%
5. VERSION.yaml is consistent across all docs

**Success Criteria**:
- [ ] Script exists and runs
- [ ] Exit 0 = framework is internally consistent
- [ ] Exit 1 = drift detected

---

## Dependency Graph

```
Phase 0 (Prerequisites)
    │
    ▼
Phase 1 (Reformat Document Specs)
    ├── Task 1.1: AI_TASK_LIST_SPEC.md
    ├── Task 1.2: PROSE_INPUT_SPEC.md
    └── Task 1.3: Validate
    │
    ▼
Phase 2 (Create Linter Specs)
    ├── Task 2.1: AI_TASK_LIST_LINTER_SPEC.md
    ├── Task 2.2: PROSE_INPUT_LINTER_SPEC.md
    └── Task 2.3: Validate
    │
    ▼
Phase 3 (Alignment Verification)
    ├── Task 3.1: Linter↔Spec alignment
    ├── Task 3.2: Template↔Spec alignment
    └── Task 3.3: Update COMMON.md
    │
    ▼
Phase 4 (CI Integration) [Optional]
    └── Task 4.1: Validation script
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SPEKSI linters reject our rule namespaces | Medium | High | Use project-level namespaces (ATL, PIN) per SPEKSI rules |
| Reformatting breaks existing linter logic | Low | High | Preserve all rule IDs exactly |
| Scope creep into framework improvements | Medium | Medium | Stay focused on structure, not content |
| Test matrix reveals missing linter coverage | High | Medium | Good — this is the point |

---

## Deliverables Summary

| Phase | Deliverable | Type |
|-------|-------------|------|
| 0 | Archived original specs | Backup |
| 1 | Reformatted AI_TASK_LIST_SPEC.md | Update |
| 1 | Reformatted PROSE_INPUT_SPEC.md | Update |
| 2 | AI_TASK_LIST_LINTER_SPEC.md | **New** |
| 2 | PROSE_INPUT_LINTER_SPEC.md | **New** |
| 3 | Updated COMMON.md | Update |
| 4 | tools/validate_framework.py | **New** (optional) |

---

## Success Metrics

When complete:
1. All 4 specs pass `kernel_linter.py` (exit 0)
2. All 4 specs pass `framework_linter.py spec` (exit 0)
3. Every rule ID has: spec definition → linter function → test case
4. Templates pass their own linters
5. Single command validates entire framework

---

**End of Plan**
