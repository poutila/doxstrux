# PROSE_INPUT Rules Reference

**Spec:** PROSE_INPUT_SPEC
**Version:** 2.0.0
**Generated:** 2025-12-17 02:47:44

---

## Overview

This document contains 45 rules defined in the prose_input specification.

---

## Rules

### PIN-SSOT-001

**Description:** This specification is the authoritative contract for prose input documents

**Section:** §2 RULES

**Enforcement:** `enforce_pin_ssot_001`

---

### PIN-SSOT-002

**Description:** If spec and linter diverge, linter MUST be updated to match spec

**Section:** §2 RULES

**Enforcement:** `enforce_pin_ssot_002`

---

### PIN-YML-001

**Description:** Document MUST start with YAML front matter delimited by `---`

**Section:** §2 RULES

**Enforcement:** `enforce_pin_yml_001`

---

### PIN-YML-002

**Description:** YAML front matter MUST contain `prose_input:` block

**Section:** §2 RULES

**Enforcement:** `enforce_pin_yml_002`

---

### PIN-YML-003

**Description:** prose_input block MUST contain: schema_version, project_name, runner, runner_prefix, search_tool

**Section:** §2 RULES

**Enforcement:** `enforce_pin_yml_003`

---

### PIN-YML-004

**Description:** All required YAML fields MUST be strings

**Section:** §2 RULES

**Enforcement:** `enforce_pin_yml_004`

---

### PIN-YML-005

**Description:** schema_version MUST exactly match VERSION.yaml

**Section:** §2 RULES

**Enforcement:** `enforce_pin_yml_005`

---

### PIN-YML-006

**Description:** runner MUST be one of: uv, npm, cargo, go, poetry, pipenv

**Section:** §2 RULES

**Enforcement:** `enforce_pin_yml_006`

---

### PIN-YML-007

**Description:** search_tool MUST be one of: rg, grep

**Section:** §2 RULES

**Enforcement:** `enforce_pin_yml_007`

---

### PIN-YML-008

**Description:** YAML field values MUST NOT contain `[[` or `]]` placeholder tokens

**Section:** §2 RULES

**Enforcement:** `enforce_pin_yml_008`

---

### PIN-SEC-001

**Description:** Document MUST contain `## SSOT Declaration` section

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_001`

---

### PIN-SEC-002

**Description:** Document MUST contain `## Scope` section

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_002`

---

### PIN-SEC-003

**Description:** Document MUST contain `### In Scope` subsection

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_003`

---

### PIN-SEC-004

**Description:** Document MUST contain `### Out of Scope` subsection

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_004`

---

### PIN-SEC-005

**Description:** Document MUST contain `## Decisions (Binding)` section

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_005`

---

### PIN-SEC-006

**Description:** Document MUST contain `## External Dependencies` section

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_006`

---

### PIN-SEC-007

**Description:** Document MUST contain `## File Manifest` section

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_007`

---

### PIN-SEC-008

**Description:** Document MUST contain `## Test Strategy` section

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_008`

---

### PIN-SEC-009

**Description:** Document MUST contain `## Phase 0` section

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_009`

---

### PIN-SEC-010

**Description:** External Dependencies MUST contain `### Required Files/Modules`

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_010`

---

### PIN-SEC-011

**Description:** External Dependencies MUST contain `### Required Libraries`

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_011`

---

### PIN-SEC-012

**Description:** External Dependencies MUST contain `### Required Tools`

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sec_012`

---

### PIN-ORD-001

**Description:** Sections MUST appear in order PIN-SEC-001 to PIN-SEC-009; preceding section before succeeding

**Section:** §2 RULES

**Enforcement:** `enforce_pin_ord_001`

---

### PIN-FBN-001

**Description:** Document MUST NOT contain: TBD, TODO, TBC, FIXME, XXX (case-insensitive)

**Section:** §2 RULES

**Enforcement:** `enforce_pin_fbn_001`

---

### PIN-FBN-002

**Description:** Document MUST NOT contain `[[PLACEHOLDER]]` tokens (except `[[PH:...]]` reserved format)

**Section:** §2 RULES

**Enforcement:** `enforce_pin_fbn_002`

---

### PIN-FBN-003

**Description:** Lines MUST NOT end with single `?` (except `??` in code)

**Section:** §2 RULES

**Enforcement:** `enforce_pin_fbn_003`

---

### PIN-FBN-004

**Description:** Document MUST NOT contain tentative phrases: maybe, might, could, possibly, potentially, consider

**Section:** §2 RULES

**Enforcement:** `enforce_pin_fbn_004`

---

### PIN-FBN-005

**Description:** Document MUST NOT contain conditional statements: if we... then, if you... then

**Section:** §2 RULES

**Enforcement:** `enforce_pin_fbn_005`

---

### PIN-FBN-006

**Description:** Document MUST NOT contain time estimates: 2-3 hours, 1-2 days, etc.

**Section:** §2 RULES

**Enforcement:** `enforce_pin_fbn_006`

---

### PIN-FBN-007

**Description:** Document MUST NOT contain pending decision phrases: pending, to be decided, TBD by

**Section:** §2 RULES

**Enforcement:** `enforce_pin_fbn_007`

---

### PIN-CTX-001

**Description:** Success Criteria MUST NOT contain subjective terms: good, nice, clean, proper, appropriate, reasonable, adequate

**Section:** §2 RULES

**Enforcement:** `enforce_pin_ctx_001`

---

### PIN-TSK-001

**Description:** Document MUST contain at least one task matching `#### Task N.M — Name`

**Section:** §2 RULES

**Enforcement:** `enforce_pin_tsk_001`

---

### PIN-TSK-002

**Description:** Task IDs (N.M format) MUST be unique across document

**Section:** §2 RULES

**Enforcement:** `enforce_pin_tsk_002`

---

### PIN-TSK-003

**Description:** Phase 0 tasks MUST contain Objective, Paths; non-Phase-0 tasks MUST also contain Precondition, TDD Specification, Success Criteria

**Section:** §2 RULES

**Enforcement:** `enforce_pin_tsk_003`

---

### PIN-TSK-004

**Description:** Precondition commands MUST use search_tool declared in YAML; if rg, grep forbidden

**Section:** §2 RULES

**Enforcement:** `enforce_pin_tsk_004`

---

### PIN-DEC-001

**Description:** Decisions table MUST have at least one decision row (not just header/separator)

**Section:** §2 RULES

**Enforcement:** `enforce_pin_dec_001`

---

### PIN-DEC-002

**Description:** Decisions table MUST contain columns: ID, Decision, Rationale

**Section:** §2 RULES

**Enforcement:** `enforce_pin_dec_002`

---

### PIN-MAN-001

**Description:** File Manifest table MUST have at least one file entry

**Section:** §2 RULES

**Enforcement:** `enforce_pin_man_001`

---

### PIN-CHK-001

**Description:** Document MUST contain `## Checklist Before Submission` section

**Section:** §2 RULES

**Enforcement:** `enforce_pin_chk_001`

---

### PIN-CHK-002

**Description:** All checklist items MUST be checked `[x]` before document is valid

**Section:** §2 RULES

**Enforcement:** `enforce_pin_chk_002`

---

### PIN-LNT-001

**Description:** Linter exit codes: 0=valid, 1=validation errors, 2=schema/parse error, 3=usage/file error

**Section:** §2 RULES

**Enforcement:** `enforce_pin_lnt_001`

---

### PIN-LNT-002

**Description:** Default diagnostics format: `Line N: [RULE_ID] message`

**Section:** §2 RULES

**Enforcement:** `enforce_pin_lnt_002`

---

### PIN-LNT-003

**Description:** With --json, emit JSON with: file, valid, schema_version, error_count, warning_count, metadata, errors

**Section:** §2 RULES

**Enforcement:** `enforce_pin_lnt_003`

---

### PIN-LNT-004

**Description:** With --fix-hints, show suggested fixes for each error

**Section:** §2 RULES

**Enforcement:** `enforce_pin_lnt_004`

---

### PIN-SEV-001

**Description:** ERROR severity blocks conversion (exit 1); WARNING does not block but may cause poor output

**Section:** §2 RULES

**Enforcement:** `enforce_pin_sev_001`

---

