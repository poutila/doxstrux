<!--
SPEC_KIND: prose_input
SPEC_ID: PROSE_INPUT_SPEC_VALID_FIXTURE
SPEC_VERSION: 2.0.0
STATUS: active
-->

# Full Valid Document for prose_input

This document satisfies ALL rules and invariants.

## §1 META

- **Purpose**: Valid test fixture for prose_input
- **Scope**: Testing
- **Layer**: kernel

## §2 RULES

| Rule ID | Description | Enforcement |
|---------|-------------|-------------|
| PIN-SSOT-001 | This specification is the auth... | enforce_pin_ssot_001 |
| PIN-SSOT-002 | If spec and linter diverge, li... | enforce_pin_ssot_002 |
| PIN-YML-001 | Document MUST start with YAML ... | enforce_pin_yml_001 |
| PIN-YML-002 | YAML front matter MUST contain... | enforce_pin_yml_002 |
| PIN-YML-003 | prose_input block MUST contain... | enforce_pin_yml_003 |

## §3 INVARIANTS

| Invariant ID | Description | Enforcement |
|--------------|-------------|-------------|
| INV-SSOT-A | Spec is authoritative; linter ... | enforce_inv_ssot_a |
| INV-COMPLETE-A | All placeholders MUST be repla... | enforce_inv_complete_a |
| INV-DECISION-A | All decisions MUST be final be... | enforce_inv_decision_a |

## §4 PHASES

### Phase 1: Validation

Rules: [PIN-SSOT-001, PIN-SSOT-002, PIN-YML-001]
Invariants: [INV-SSOT-A, INV-COMPLETE-A]

---

This fixture is auto-generated. All sections are properly formatted.
