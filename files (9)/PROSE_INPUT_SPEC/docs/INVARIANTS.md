# PROSE_INPUT Invariants Reference

**Spec:** PROSE_INPUT_SPEC
**Version:** 2.0.0
**Generated:** 2025-12-17 02:47:44

---

## Overview

This document contains 5 invariants defined in the prose_input specification.

Invariants are non-negotiable constraints that must always hold.

---

## Invariants

### INV-SSOT-A

**Description:** Spec is authoritative; linter implements spec

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_ssot_a`

---

### INV-COMPLETE-A

**Description:** All placeholders MUST be replaced before conversion

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_complete_a`

---

### INV-DECISION-A

**Description:** All decisions MUST be final before conversion

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_decision_a`

---

### INV-FACTS-A

**Description:** Facts are provided in input, not discovered during conversion

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_facts_a`

---

### INV-DETERMINISM-A

**Description:** Validation is deterministic and repeatable

**Section:** §3 INVARIANTS

**Enforcement:** `enforce_inv_determinism_a`

---

