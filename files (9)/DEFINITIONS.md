# DEFINITIONS.md

> Canonical definitions for the AI Task List Framework.

---

## Specification

A **specification** is a document that:

1. **Defines rules** for a specific domain
2. **MUST be validatable** - a linter MUST exist
3. **Is the SSOT** (Single Source of Truth) for that domain

If a linter does not exist, it is not a specification.

---

## SSOT Principle

Each specification is the **Single Source of Truth** for its domain.

| Specification | Domain | SSOT For |
|---------------|--------|----------|
| INPUT_SPEC | Prose input format | PIN-* rules |
| OUTPUT_SPEC | Task list format | R-ATL-* rules |

**Consequence**: When a rule changes, it changes in exactly one place - the specification.

---

## Derivation Chain

Everything propagates **from** specifications:

```
SPECIFICATION (SSOT)
       │
       ├──► Validator (linter)
       │    - Generated from spec rules
       │    - Enforces spec compliance
       │
       └──► Template
            - Derived from spec structure
            - Pre-filled skeleton that satisfies spec
```

**Invariant**: Validators and templates are never authoritative. They are derived artifacts. If they contradict the specification, the specification wins.

---

## Single Responsibility Principle (SRP)

Each specification has **one responsibility**:

- **INPUT_SPEC**: Defines valid input document structure
- **OUTPUT_SPEC**: Defines valid output document structure

Specifications do not share rules. If two specs need the same rule, the rule belongs to a different domain and requires its own spec - or the specs are incorrectly partitioned.

---

## What Is NOT a Specification

| Document | Why Not a Spec |
|----------|----------------|
| COMMON.md | Shared content resource, not validatable structure |
| Templates | Derived from spec, not authoritative |
| README, guides | Documentation, no rules to validate |

These are **resources** or **derived artifacts**, not specifications.

---

## Validation

A document is **valid** if it passes all applicable linters:

```bash
# Input document validation
input_linter.py DOCUMENT.md

# Output document validation
output_linter.py DOCUMENT.md
```

A specification is **correct** if:
1. Its rules are internally consistent
2. Its generated linter correctly enforces those rules
3. Valid documents satisfy the intended semantics

---

## Summary

```
Specification = Rules + Validatable + SSOT

Spec ──► Linter (enforces rules)
    ──► Template (satisfies rules)

One spec = One domain = One responsibility
```
