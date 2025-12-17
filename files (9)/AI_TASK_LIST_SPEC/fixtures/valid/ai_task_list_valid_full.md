<!--
SPEC_KIND: ai_task_list
SPEC_ID: AI_TASK_LIST_SPEC_VALID_FIXTURE
SPEC_VERSION: 2.0.0
STATUS: active
-->

# Full Valid Document for ai_task_list

This document satisfies ALL rules and invariants.

## §1 META

- **Purpose**: Valid test fixture for ai_task_list
- **Scope**: Testing
- **Layer**: kernel

## §2 RULES

| Rule ID | Description | Enforcement |
|---------|-------------|-------------|
| R-ATL-000 | If spec and linter diverge, li... | enforce_r_atl_000 |
| R-ATL-001 | Task list MUST start with YAML... | enforce_r_atl_001 |
| R-ATL-002 | Mode semantics: template allow... | enforce_r_atl_002 |
| R-ATL-003 | Only `[[PH:NAME]]` placeholder... | enforce_r_atl_003 |
| R-ATL-010 | Task list MUST contain all req... | enforce_r_atl_010 |

## §3 INVARIANTS

| Invariant ID | Description | Enforcement |
|--------------|-------------|-------------|
| INV-MODE-A | Mode determines placeholder to... | enforce_inv_mode_a |
| INV-SSOT-A | Spec is authoritative; linter ... | enforce_inv_ssot_a |
| INV-EVIDENCE-A | Evidence in instantiated mode ... | enforce_inv_evidence_a |

## §4 PHASES

### Phase 1: Validation

Rules: [R-ATL-000, R-ATL-001, R-ATL-002]
Invariants: [INV-MODE-A, INV-SSOT-A]

---

This fixture is auto-generated. All sections are properly formatted.
