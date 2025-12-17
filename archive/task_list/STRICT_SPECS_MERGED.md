# Strict Specs Governance Plan (SPEKSI Format)

**Version**: 3.0.0
**Status**: PLAN
**Created**: 2025-12-16
**Kernel-Version**: 1.0.1

> This plan governs how the framework's specifications and linters are kept drift-free via SPEKSI rules, explicit binding decisions, and mechanical coverage checks.

---

## §0 META

### §0.1 Purpose

Establish a deterministic, repeatable governance workflow so that:

- Specifications are SPEKSI-compliant and structurally lintable.
- Linters are provably aligned to specifications (rule coverage is measurable).
- Internal drift (spec ↔ linter ↔ templates) is detectable and blocks progress.

### §0.2 SSOT Hierarchy

SSOT-PLN-1: If a document-level spec and its linter disagree, update the linter to match the spec.

SSOT-PLN-2: If the SPEKSI Kernel and any project document disagree on Kernel grammar requirements, update the project document to match the Kernel.

SSOT-PLN-3: Rule coverage is evaluated against the spec rule IDs as written. Adding "implicit rules" in code is forbidden; every enforceable behavior must have a rule ID in a spec.

### §0.3 Kernel Constraint Acknowledgement

K-PLN-1: Specifications and plans must not contain Markdown fences (triple backticks). Use prose and inline code formatting instead.

### §0.4 Inputs and Target Artifacts

Inputs (current state):

- AI_TASK_LIST_SPEC_SPEKSI_proposal.md (R-ATL-* rule namespace) — DONE, passes kernel_linter
- PROSE_INPUT_SPEC_SPEKSI_proposal.md (PIN-* rule namespace) — DONE, passes kernel_linter
- KERNEL_LINTER_SPEC.md (grammar constraints)
- kernel_linter.py (current implementation)

Target artifacts (end state):

- AI_TASK_LIST_LINTER_SPEC.md (normative, SPEKSI-compliant; includes rule→function→test coverage table).
- PROSE_INPUT_LINTER_SPEC.md (normative, SPEKSI-compliant; includes rule→function→test coverage table).
- Refactored kernel_linter.py (Protocol-based, composition, rule registry).
- ai_task_list_linter.py (composes kernel, implements R-ATL-* checks).
- prose_input_linter.py (composes kernel, implements PIN-* checks).
- validate_framework.py (single validation command).

---

## §1 DECISIONS (BINDING)

These decisions resolve prior ambiguity. They are treated as binding until superseded by a new decision entry in §C CHANGELOG.

### §1.1 Decision Register

| ID | Decision | Rationale | Consequences |
|----|----------|-----------|--------------|
| D-SSP-001 | **Extension pattern = Protocol + composition + rule registry.** Domain linters compose kernel via Protocol interface. Rule checks are registered callables with metadata. No inheritance. | Protocol enables structural typing without tight coupling. Registry makes rules enumerable. Composition keeps layers testable independently. | Rules live in separate modules; coverage tooling straightforward; mypy verifiable. |
| D-SSP-002 | **Kernel spec = no trimming.** KERNEL_LINTER_SPEC.md is not modified. Project-specific constraints live in domain linter specs. | Trimming creates untrackable fork. Kernel is immutable grammar. | Unused Kernel features are "non-applicable" at domain level, not deleted. |
| D-SSP-003 | **Rule→function mapping SSOT = code annotations; spec tables are generated.** Each enforcement function declares implemented rule IDs via decorator; tooling generates mapping table. | Handwritten tables drift. Code is the only place that truly knows enforcement. | Requires decorator metadata and generation tool. Specs embed generated output. |
| D-SSP-004 | **Old linters are deleted after new linters pass regression tests.** tools/ai_task_list_linter.py (1236 lines) and tools/prose_input_linter.py (815 lines) are superseded. | Clean slate avoids dual maintenance. New architecture incompatible with old code. | Canonical examples used for regression testing before deletion. |

### §1.2 Deferred Decisions (Explicit)

None. Any future decision must be added to §1.1 with a new ID and recorded in §C CHANGELOG.

---

## §2 ARCHITECTURE

### §2.1 Governance Architecture Overview

The governance loop has three layers of verification:

1) Kernel grammar compliance (kernel_linter): structural validity for SPEKSI documents (§-sections, references, anchoring).
2) Domain linter specs: AI_TASK_LIST_LINTER_SPEC.md + PROSE_INPUT_LINTER_SPEC.md define behavioral contracts.
3) Alignment verification: rule coverage checks (spec rule IDs ↔ code annotations ↔ tests).

### §2.2 Extensibility Architecture (per D-SSP-001)

Architecture constraints:

- kernel_linter provides Protocol interface for composition.
- Domain linters instantiate kernel and add domain-specific checks.
- Rule checks are pure functions with stable signature, registered in a rule registry.
- Rule registration is explicit and enumerable via decorator metadata.

Required elements:

- KernelLinter Protocol: collect_sections, check_references, check_anchored_constraints, strip_code_blocks.
- DefaultKernelLinter: concrete implementation of Protocol.
- Rule decorator: marks function with rule_id, description, severity.
- Rule registry: queryable list of all checks and their metadata.

Domain linter structure (example for ai_task_list_linter.py):

    class AITaskListLinter:
        def __init__(self, kernel: KernelLinter | None = None):
            self.kernel = kernel or DefaultKernelLinter()

        def lint(self, path: Path, mode: str) -> int:
            # Kernel checks via composition
            # Domain checks (R-ATL-*) via registered rule functions
            ...

### §2.3 Rule Coverage Architecture (per D-SSP-003)

Coverage check compares three sets:

- Spec set: rule IDs extracted from specifications (R-ATL-* and PIN-*).
- Code set: rule IDs declared in code annotations (decorator metadata).
- Test set: rule IDs referenced by test markers or parametrized tests.

Outputs:

- Orphan spec rules: in spec, not in code (BLOCKER).
- Phantom code rules: in code, not in spec (BLOCKER).
- Untested rules: in code/spec, missing tests (BLOCKER unless explicitly exempted).

### §2.4 Regression Testing Architecture (per D-SSP-004)

Canonical examples directory provides regression fixtures:

- canonical_examples/example_template.md — PASS (template mode)
- canonical_examples/example_plan.md — PASS (plan mode)
- canonical_examples/example_instantiated.md — PASS (instantiated mode)
- canonical_examples/negatives/template_missing_clean_table_placeholder.md — FAIL
- canonical_examples/negatives/plan_preconditions_placeholder.md — FAIL
- canonical_examples/negatives/plan_missing_coverage_mapping.md — FAIL

Regression test procedure:

1) Run old linter on all fixtures, record exit codes.
2) Run new linter on all fixtures, compare exit codes.
3) Any mismatch blocks deletion of old linters.

---

## §3 PLAN

### §3.0 Phase 0 — Baseline Inventory (DONE)

**Status**: COMPLETE

Completed:

- kernel_linter.py exists and runs
- AI_TASK_LIST_SPEC_SPEKSI_proposal.md created and passes kernel_linter
- PROSE_INPUT_SPEC_SPEKSI_proposal.md created and passes kernel_linter

### §3.1 Phase 1 — Reformat Document Specs (DONE)

**Status**: COMPLETE

Completed:

- AI_TASK_LIST_SPEC_SPEKSI_proposal.md — SPEKSI format, passes kernel_linter
- PROSE_INPUT_SPEC_SPEKSI_proposal.md — SPEKSI format, passes kernel_linter
- Both use §M/§A/§D/§R/§V/§C/§G structure

### §3.2 Phase 2 — Refactor kernel_linter.py (per D-SSP-001)

**Objective**: Make kernel_linter Protocol-based and composable.

Steps:

1) Define KernelLinter Protocol with required methods.
2) Refactor existing functions into DefaultKernelLinter class implementing Protocol.
3) Add rule decorator for metadata annotation.
4) Add rule registry that collects decorated functions.
5) Add --list-rules output mode.
6) Verify CLI behavior unchanged.

Success Criteria:

- Protocol defined and documented.
- DefaultKernelLinter implements Protocol.
- Existing CLI produces same output on same inputs.
- --list-rules shows all kernel rule IDs and callables.

### §3.3 Phase 3 — Implement Rule Coverage Tooling (per D-SSP-003)

**Objective**: Generate rule→function→test mapping from code.

Steps:

1) Create @rule decorator that captures rule_id, description, severity.
2) Create test marker convention (pytest.mark.rule or parametrize by rule_id).
3) Create generate_rule_mapping.py script that:
   - Extracts rule IDs from specs (R-ATL-*, PIN-*)
   - Extracts rule IDs from decorated functions
   - Extracts rule IDs from test markers
   - Emits coverage table as Markdown
   - Reports orphan/phantom/untested rules
4) Integrate into CI as blocking check.

Success Criteria:

- Mapping generated deterministically from repo state.
- 100% coverage enforced for R-ATL-* and PIN-* namespaces.
- Orphan/phantom rules fail CI.

### §3.4 Phase 4 — Create Domain Linter Specs

**Objective**: Author normative linter specifications.

Deliverables:

- AI_TASK_LIST_LINTER_SPEC.md
- PROSE_INPUT_LINTER_SPEC.md

Required contents (both):

- Input/output schemas
- Exit codes (0=pass, 1=fail, 2=usage error)
- Diagnostics format
- JSON output format
- Exemptions contract (if any)
- Generated mapping table (embedded as plain Markdown table)

Success Criteria:

- Both linter specs pass kernel_linter.
- Generated mapping tables match repo state.

### §3.5 Phase 5 — Implement Domain Linters

**Objective**: Create new linters that compose kernel.

Deliverables:

- ai_task_list_linter.py (new, composes DefaultKernelLinter)
- prose_input_linter.py (new, composes DefaultKernelLinter)

Steps:

1) Implement AITaskListLinter class composing kernel.
2) Implement all R-ATL-* checks as decorated functions.
3) Implement CLI: uv run python ai_task_list_linter.py [--mode MODE] [--json] file.md
4) Repeat for ProseInputLinter with PIN-* checks.
5) Run regression tests against canonical_examples.
6) Delete old linters after regression tests pass.

Success Criteria:

- New linters compose kernel (not inherit).
- All R-ATL-* and PIN-* rules implemented.
- Regression tests pass (same results as old linters on canonical examples).
- Old linters deleted.

### §3.6 Phase 6 — Single-Command Validation Script

**Objective**: Provide validate_framework.py that checks everything.

Script responsibilities:

- Run kernel_linter on all SPEKSI specs.
- Run domain linters on templates (appropriate modes).
- Run rule coverage check.
- Fail fast on any mismatch.

Success Criteria:

- Exit 0 only when framework is internally consistent.
- Exit 1 on any drift or missing coverage.

---

## §4 DELIVERABLES

| Deliverable | Type | Phase | Status |
|-------------|------|-------|--------|
| AI_TASK_LIST_SPEC_SPEKSI_proposal.md | Spec | 1 | DONE |
| PROSE_INPUT_SPEC_SPEKSI_proposal.md | Spec | 1 | DONE |
| kernel_linter.py (Protocol refactor) | Code | 2 | TODO |
| Rule decorator + registry | Code | 2-3 | TODO |
| generate_rule_mapping.py | Code | 3 | TODO |
| AI_TASK_LIST_LINTER_SPEC.md | Spec | 4 | TODO |
| PROSE_INPUT_LINTER_SPEC.md | Spec | 4 | TODO |
| ai_task_list_linter.py (new) | Code | 5 | TODO |
| prose_input_linter.py (new) | Code | 5 | TODO |
| validate_framework.py | Code | 6 | TODO |

---

## §5 RISKS

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Coverage tooling adds complexity | Medium | Medium | Keep SSOT in code; generate tables; avoid handwritten artifacts. |
| Decorator/registry overhead | Low | Low | Simple implementation; decorator is metadata only. |
| Regression test misses edge case | Medium | High | Expand canonical_examples/negatives with more fixtures. |
| Exemption creep | High | High | Require explicit exemption rules in linter specs with criteria. |

---

## §6 VALIDATION

### §6.1 Phase Completion Gates

A phase is complete only if:

- All artifacts listed in that phase exist.
- kernel_linter passes for affected specs (exit 0).
- Rule coverage check passes for affected namespaces.
- Regression tests pass (where applicable).

### §6.2 Regression Test Gate (Phase 5)

Before deleting old linters:

- Run old ai_task_list_linter.py on all canonical_examples, record results.
- Run new ai_task_list_linter.py on same files, compare results.
- Any difference blocks deletion.
- Repeat for prose_input_linter.py.

---

## §C CHANGELOG

- 3.0.0 (2025-12-16): Merged STRICT_SPECS.md and STRICT_SPECS_SPEKSI_proposal.md:
  - Adopted D-SSP-001 (Protocol + composition + registry)
  - Adopted D-SSP-002 (no kernel trimming)
  - Adopted D-SSP-003 (code annotations → generated tables)
  - Added D-SSP-004 (delete old linters after regression)
  - Marked Phase 0-1 as DONE
  - Added regression testing architecture (§2.4)
  - Removed framework_linter references (not used)
  - Added deliverables status column

---

## §G GLOSSARY

Rule coverage
A mechanical guarantee that every normative rule ID in a spec is implemented by code and verified by tests.

Orphan rule
A rule ID that exists in a spec but has no implementing function in code.

Phantom rule
A rule ID that exists in code annotations but does not exist in the spec.

Rule registry
A deterministic list of rule checks and their metadata, used by a linter to apply enforcement consistently.

Protocol (Python typing)
A structural typing mechanism that defines an interface without requiring inheritance. Classes satisfy a Protocol if they have the required methods.

Composition
An architecture pattern where objects contain instances of other objects rather than inheriting from them.

Canonical examples
Purpose-built test fixtures that verify linter behavior; positive examples must pass, negative examples must fail.

End of Document
