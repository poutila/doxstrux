# PROSE_INPUT Execution Phases

**Spec:** PROSE_INPUT_SPEC
**Version:** 2.0.0
**Generated:** 2025-12-17 02:47:44

---

## Overview

Phases define the order in which rules and invariants are checked.
Rules within a phase are executed in declaration order.

---

## Phases

### Phase 1: META

---

### Phase 2: DEFINITIONS

---

### Phase 3: Document Terms

---

### Phase 4: Configuration Terms

---

### Phase 5: Required Sections

---

### Phase 6: RULES

---

### Phase 7: INVARIANTS

---

### Phase 8: PHASES

---

### Phase 9: 1: YAML Validation

**Rules:**
- PIN-YML-001
- PIN-YML-002
- PIN-YML-003
- PIN-YML-004
- PIN-YML-005
- PIN-YML-006
- PIN-YML-007
- PIN-YML-008

---

### Phase 10: 2: Section Validation

**Rules:**
- PIN-SEC-001
- PIN-SEC-002
- PIN-SEC-003
- PIN-SEC-004
- PIN-SEC-005
- PIN-SEC-006
- PIN-SEC-007
- PIN-SEC-008
- PIN-SEC-009
- PIN-SEC-010
- PIN-SEC-011
- PIN-SEC-012
- PIN-ORD-001

---

### Phase 11: 3: Forbidden Pattern Scan

**Rules:**
- PIN-FBN-001
- PIN-FBN-002
- PIN-FBN-003
- PIN-FBN-004
- PIN-FBN-005
- PIN-FBN-006
- PIN-FBN-007

---

### Phase 12: 4: Context-Specific Validation

**Rules:**
- PIN-CTX-001
- PIN-TSK-001
- PIN-TSK-002
- PIN-TSK-003
- PIN-TSK-004

---

### Phase 13: 5: Table Validation

**Rules:**
- PIN-DEC-001
- PIN-DEC-002
- PIN-MAN-001

---

### Phase 14: 6: Checklist Validation

**Rules:**
- PIN-CHK-001
- PIN-CHK-002

---

### Phase 15: 7: Output Generation

**Rules:**
- PIN-LNT-001
- PIN-LNT-002
- PIN-LNT-003
- PIN-LNT-004
- PIN-SEV-001

---

### Phase 16: SCHEMAS

---

### Phase 17: YAML Front Matter

---

### Phase 18: Task Structure

---

### Phase 19: Decisions Table

---

### Phase 20: Linter JSON Output

---

### Phase 21: CLI COMMANDS

---

### Phase 22: `prose_input_linter.py <file.md>`

---

### Phase 23: APPENDICES

---

