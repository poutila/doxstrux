# AI_TASK_LIST Invariants Reference

**Spec:** AI_TASK_LIST_SPEC
**Version:** 2.0.0
**Generated:** 2025-12-17 02:47:50

---

## Overview

This document contains 5 invariants defined in the ai_task_list specification.

Invariants are non-negotiable constraints that must always hold.

---

## Invariants

### INV-MODE-A

**Description:** Mode determines placeholder tolerance; no exceptions

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_mode_a`

---

### INV-SSOT-A

**Description:** Spec is authoritative; linter implements spec

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_ssot_a`

---

### INV-EVIDENCE-A

**Description:** Evidence in instantiated mode MUST be real output, not fabricated

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_evidence_a`

---

### INV-TDD-A

**Description:** Non-Phase-0 tasks MUST follow RED-GREEN-REFACTOR structure

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_tdd_a`

---

### INV-CLEAN-A

**Description:** Clean Table gate MUST pass before phase completion

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_clean_a`

---

