# DOXSTRUX_SOLID_ANALYSIS

> **Status:** ARCHIVED — Pre-refactor diagnosis. Preserved as historical evidence.
> See **DOXSTRUX_SPEC.md** for the active specification.

---

## Executive Summary

**Pre-Refactor SOLID Compliance: 6/10**

Clear module-level separation, but `MarkdownParserCore` is a God Object.

---

## Quantitative Assessment

| Metric | Value | Historical Guideline |
|--------|-------|----------------------|
| `MarkdownParserCore` lines | 2075 | 300-500 |
| Methods | 49 | — |
| `_extract_*` methods | 17 | — |
| Concrete module imports | 11 | 0 (use abstractions) |
| Extractor callback params | 8 | 1 (context object) |

*These numbers are frozen as of 2025-12-12. They are a diagnostic snapshot, not targets to maintain.*

**⚠️ Guidelines superseded:** DOXSTRUX_SPEC explicitly allows the registry to import concrete collectors. Do not use "0 imports" as a design goal — that would lead to unnecessary abstraction.

---

## S — Single Responsibility Principle

**Status: VIOLATED**

Eight responsibilities in `MarkdownParserCore`:
1. Content normalization
2. Security validation
3. Plugin management
4. Token parsing
5. Extraction orchestration (17 methods)
6. Metadata generation
7. Caching
8. IR generation

---

## O — Open/Closed Principle

**Status: PARTIAL**

- Plugins: Open for extension ✓
- Extractors: Closed (hardcoded, no registry) ✗

---

## L — Liskov Substitution Principle

**Status: N/A** — Composition over inheritance. Good design.

---

## I — Interface Segregation Principle

**Status: VIOLATED**

Extractors take 8 callback parameters. Fat interface.

---

## D — Dependency Inversion Principle

**Status: VIOLATED**

Parser imports 11 concrete extractor modules directly.

---

## Summary

| Principle | Status | Fix |
|-----------|--------|-----|
| SRP | VIOLATED | Warehouse + collectors |
| OCP | PARTIAL | Registry pattern |
| LSP | N/A | — |
| ISP | VIOLATED | Warehouse context |
| DIP | VIOLATED | Registry indirection |

**Note:** The DIP guideline ("0 concrete imports") was intentionally relaxed in DOXSTRUX_SPEC. The registry is allowed to import concrete collectors — that coupling is moved to one place rather than eliminated.

---

*Captured: 2025-12-12. This analysis originally informed an earlier refactor plan; its role now is historical context for DOXSTRUX_SPEC.md.*
