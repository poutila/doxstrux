# DOXSTRUX_SOLID_ANALYSIS

> **Status:** ARCHIVED — Pre-refactor diagnosis. Preserved as historical evidence.
> See **DOXSTRUX_REFACTOR.md** for the active plan.

---

## Executive Summary

**Pre-Refactor SOLID Compliance: 6/10**

Clear module-level separation, but `MarkdownParserCore` is a God Object.

---

## Quantitative Assessment

| Metric | Value | Guideline |
|--------|-------|-----------|
| `MarkdownParserCore` lines | 2075 | 300-500 |
| Methods | 49 | — |
| `_extract_*` methods | 17 | — |
| Concrete module imports | 11 | 0 (use abstractions) |
| Extractor callback params | 8 | 1 (context object) |

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

---

*Captured: 2025-12-12. This analysis informed DOXSTRUX_REFACTOR.md.*
