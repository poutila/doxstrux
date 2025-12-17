# Strict Specs Governance Plan (SPEKSI Format)

**Version**: 2.0.0
**Status**: PLAN
**Created**: 2025-12-16
**Kernel-Version**: 1.0.1

> This plan governs how the framework’s specifications and linters are kept drift-free via SPEKSI rules, explicit binding decisions, and mechanical coverage checks.

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

SSOT-PLN-3: Rule coverage is evaluated against the spec rule IDs as written. Adding “implicit rules” in code is forbidden; every enforceable behavior must have a rule ID in a spec.

### §0.3 Kernel Constraint Acknowledgement

K-PLN-1: Specifications and plans must not contain Markdown fences (triple backticks). Use prose and inline code formatting instead.

### §0.4 Inputs and Target Artifacts

Inputs (current state):

- AI Task List output specification (R-ATL-* rule namespace).
- Prose input specification (PIN-* rule namespace).
- SPEKSI Kernel document (grammar constraints).

Target artifacts (end state):

- AI_TASK_LIST_LINTER_SPEC.md (normative, SPEKSI-compliant; includes rule→function→test coverage table).
- PROSE_INPUT_LINTER_SPEC.md (normative, SPEKSI-compliant; includes rule→function→test coverage table).
- Refactored, extendable kernel_linter implementation (composition-based rule registry).
- A single validation command (script) that verifies: specs lint clean + mapping coverage is 100% + templates pass.

---

## §1 DECISIONS (BINDING)

These decisions resolve prior ambiguity. They are treated as binding until superseded by a new decision entry in §C CHANGELOG.

### §1.1 Decision Register

| ID | Decision | Rationale | Consequences |
|----|----------|-----------|--------------|
| D-SSP-001 | **kernel_linter.py extension pattern = composition + rule registry + explicit plugin module list** (no inheritance-based extension). | Inheritance pushes behavior into implicit overriding and weakens coverage checks. A registry makes “what rules exist” mechanically enumerable. Explicit module lists keep loading deterministic. | Rules live in separate modules; new rules require registration; coverage tooling becomes straightforward. |
| D-SSP-002 | **Kernel trim scope = no trimming.** Project may not remove sections from KERNEL_LINTER_SPEC.md; instead, project-specific constraints live in framework-level specs. | Trimming Kernel docs creates an untrackable fork and breaks “Kernel as immutable grammar.” | Eliminates the need to guess “what to remove.” Any perceived excess becomes a “non-applicable” note at framework level, not a deletion. |
| D-SSP-003 | **Rule→function mapping SSOT = code annotations; spec tables are generated.** Each enforcement function declares implemented rule IDs; tooling generates the mapping table and enforces 100% coverage. | Handwritten tables drift. Code is the only place that truly knows enforcement boundaries; generation prevents divergence. | Requires a decorator (or structured metadata) in code and a tool that emits the mapping. Specs embed the generated table output. |

### §1.2 Deferred Decisions (Explicit)

None. Any future decision must be added to §1.1 with a new ID and recorded in §C CHANGELOG.

---

## §2 ARCHITECTURE

### §2.1 Governance Architecture Overview

The governance loop has four layers of verification:

1) Kernel grammar compliance (kernel_linter): structural validity for SPEKSI documents.
2) Framework policy compliance (framework_linter spec mode): project-level rules about spec hygiene, references, and layering.
3) Domain linter specs: AI Task List linter spec + Prose Input linter spec define behavioral contracts for domain linters.
4) Alignment verification: rule coverage checks (spec rule IDs ↔ code annotations ↔ tests).

### §2.2 Extensibility Architecture for kernel_linter.py (per D-SSP-001)

Architecture constraints:

- kernel_linter core only orchestrates: parse → apply rule registry → emit diagnostics.
- Rule checks are pure functions (or callable objects) with a stable signature.
- Rule registration is explicit and enumerable.

Required elements:

- A Rule metadata record: rule_id, description, severity, and the callable reference name.
- A registry that can be queried to list all checks and their rule IDs.
- An optional “plugin modules” list loaded deterministically from a config file (or constant list in code), not via implicit discovery.

### §2.3 Rule Coverage Architecture (per D-SSP-003)

Coverage check compares three sets:

- Spec set: rule IDs extracted from specifications (R-ATL-* and PIN-*).
- Code set: rule IDs declared in code annotations (e.g., decorator metadata).
- Test set: rule IDs referenced by test markers (or derived from parametrized tests).

Outputs:

- Orphan spec rules: in spec, not in code (BLOCKER).
- Phantom code rules: in code, not in spec (BLOCKER).
- Untested rules: in code/spec, missing tests (BLOCKER unless explicitly exempted by a rule in linter spec).

---

## §3 PLAN

### §3.1 Phase 0 — Baseline Inventory

**Objective**: Establish the baseline SSOT and avoid inventing structure.

Steps:

1) Produce the inventory of rule IDs:
   - Extract all R-ATL-* IDs from the AI Task List spec.
   - Extract all PIN-* IDs from the Prose Input spec.
2) Inventory current linter entry points and enforcement functions for:
   - ai_task_list_linter
   - prose_input_linter
   - kernel_linter
   - framework_linter
3) Capture “current rule coverage” as a table (even if incomplete).

Success Criteria:

- Baseline rule ID counts are recorded and reproducible.
- Baseline linter function inventory exists (names + file paths).
- No “guessing” remains about what rule sets exist.

### §3.2 Phase 1 — Ensure Specs are SPEKSI-Compliant (Kernel + Framework)

**Objective**: Convert and/or adjust all specs so they pass the Kernel and Framework linters.

Steps:

1) Ensure each spec:
   - uses §-numbered headings consistently,
   - separates layers cleanly,
   - avoids Markdown fences (see K-PLN-1),
   - contains CHANGELOG and GLOSSARY sections.
2) Run kernel_linter on:
   - AI Task List spec
   - Prose Input spec
   - This plan (STRICT_SPECS)
3) Run framework_linter in “spec” mode on the same set.

Success Criteria:

- All specs pass kernel_linter with exit 0.
- All specs pass framework_linter spec mode with exit 0.

### §3.3 Phase 2 — Refactor kernel_linter.py for Extension (per D-SSP-001)

**Objective**: Make kernel_linter extendable without inheritance and without implicit discovery.

Steps:

1) Extract rule checks into a dedicated rules package/module set (e.g., speksi.tools.kernel_rules.*).
2) Introduce:
   - a Rule registry,
   - structured rule metadata,
   - a deterministic plugin module list (optional, explicit).
3) Add a “list rules” output mode that prints all rule IDs and their implementing callable names.

Success Criteria:

- Adding a new rule requires:
  - creating a rule check in a rule module,
  - registering it in the registry,
  - writing at least one test.
- kernel_linter can list all rules and their implementing callables deterministically.

### §3.4 Phase 3 — Implement Rule→Function→Test Mapping Tooling (per D-SSP-003)

**Objective**: Eliminate handwritten mapping drift by generating mapping tables from code and tests.

Steps:

1) Add a code annotation mechanism (example: decorator) so each enforcement function declares which rule IDs it implements.
2) Add a test marker convention so tests can be linked to rule IDs deterministically (example: parametrized table keyed by rule_id).
3) Create a tooling script that emits a Markdown table with columns:
   - Rule ID | Linter Function | Test Case(s) | Notes/Exemptions
4) Enforce that:
   - every spec rule appears in the mapping output,
   - every mapped rule has at least one test unless exempted by a documented exemption rule.

Success Criteria:

- Mapping output is generated deterministically from the repo state.
- 100% rule coverage is enforced for R-ATL-* and PIN-* namespaces.
- Phantom/orphan rules fail CI.

### §3.5 Phase 4 — Create Linter Specs (AI Task List + Prose Input)

**Objective**: Author normative linter specifications that include the generated mapping tables and fully describe linter behavior.

Deliverables:

- AI_TASK_LIST_LINTER_SPEC.md
- PROSE_INPUT_LINTER_SPEC.md

Required contents (both):

- input/output schemas,
- exit codes,
- diagnostics format,
- JSON output format,
- exemptions contract (if any),
- generated mapping table embedded verbatim (as plain Markdown table text, no fences).

Success Criteria:

- Both linter specs pass kernel_linter and framework_linter.
- Generated mapping tables embedded in the specs match the current repo outputs (no manual edits).

### §3.6 Phase 5 — Single-Command Validation Script

**Objective**: Provide a single command that validates internal consistency.

Script responsibilities:

- Run kernel_linter across all SPEKSI docs.
- Run framework_linter spec mode across all specs.
- Run domain linters on their templates (template mode where applicable).
- Run rule coverage check (spec ↔ code ↔ tests).
- Fail fast on any mismatch.

Success Criteria:

- Exit 0 only when the framework is internally consistent.
- Exit 1 on any drift or missing coverage.

---

## §4 DELIVERABLES

| Deliverable | Type | Owner |
|------------|------|-------|
| Refactored kernel_linter (registry + annotations) | Code | Framework |
| Rule coverage generator script | Code | Framework |
| AI_TASK_LIST_LINTER_SPEC.md | Spec | Framework |
| PROSE_INPUT_LINTER_SPEC.md | Spec | Framework |
| Single validation script | Code | Framework |
| CI wiring to enforce “no drift” | CI | Framework |

---

## §5 RISKS

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Coverage tooling adds complexity | Medium | Medium | Keep SSOT in code and generate tables; avoid handwritten artifacts. |
| Plugin loading introduces nondeterminism | Low | High | Explicit module lists only; no auto-discovery. |
| Exemption creep (“temporarily skip”) | High | High | Require explicit exemption rules in linter specs with expiry/criteria. |
| Kernel constraints violated by examples | Medium | Medium | No fences anywhere; use inline code only (K-PLN-1). |

---

## §6 VALIDATION

### §6.1 Plan Completion Gates

A phase is complete only if:

- All artifacts listed in that phase exist.
- Kernel + framework linters pass for affected specs.
- Mapping coverage check passes for affected rule namespaces.
- CI runs the validation script and blocks regressions.

---

## §C CHANGELOG

- 2.0.0 (2025-12-16): Updated STRICT_SPECS plan to resolve missing binding decisions:
  - extension pattern (D-SSP-001),
  - kernel trim scope (D-SSP-002),
  - rule→function→test mapping SSOT (D-SSP-003).
  Also removed Markdown fences by policy (K-PLN-1).

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

Plugin module list
A deterministic list of modules that contribute rules, loaded explicitly (not via discovery).

End of Document
