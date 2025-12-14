# DOXSTRUX_NEXT_STEPS_1

Parser/Warehouse/Collector/Registry Refactor Execution

**Status:** Phase -1.0 – 📋 PLANNED  
**Version:** 0.3 (grounded to current repo layout, extractor-count neutral)  
**Last Updated:** 2025-12-13 04:30 UTC  

**Related Documents:**
- `DOXSTRUX_SPEC.md` – Target architecture (scaffolding)
- `DOXSTRUX_SOLID_ANALYSIS.md` – Pre-refactor diagnosis (archived)

---

## 0. Reality vs Spec – Alignment

### Current Codebase Layout (authoritative)

```
doxstrux/
├── markdown_parser_core.py        # ~2000 lines, monolithic parser
└── markdown/
    ├── extractors/                # N modules (currently 11)
    │   ├── sections.py
    │   ├── tables.py
    │   └── ...
    ├── security/
    ├── utils/
    ├── budgets.py
    ├── config.py
    └── ir.py
```

### Target Architecture (from DOXSTRUX_SPEC)

```
Parser:       doxstrux/markdown_parser_core.py::MarkdownParserCore
Registry:     doxstrux/markdown/collector_registry.py      (NEW)
Warehouse:    doxstrux/markdown/utils/token_warehouse.py   (NEW)
Collectors:   doxstrux/markdown/collectors_phase8/*.py     (NEW)
Interfaces:   doxstrux/markdown/interfaces.py              (NEW)
```

### Terminology Mapping

| Spec Term | Current Code | This Plan Introduces |
|-----------|--------------|----------------------|
| Parser | `markdown_parser_core.MarkdownParserCore` | Same class, refactored wiring |
| Warehouse | (none) | NEW `markdown/utils/token_warehouse.py` |
| Collector | `markdown/extractors/*.py` (N modules) | NEW `collectors_phase8/*.py` wrapping extractors |
| Registry | (none) | NEW `markdown/collector_registry.py` |

**This document is an execution checklist.** All normative behavior comes from `DOXSTRUX_SPEC.md`.

---

## Current Status

### Quick Status Dashboard

| Phase | Status | Tests | Files Changed | Clean Table |
|-------|--------|-------|---------------|-------------|
| -1.0 – Align Spec & Layout | 📋 PLANNED | 0/N | 0 | - |
| 0.0 – Baseline Golden Tests (SPEC §8 Step 0) | 📋 PLANNED | 0/N | 0 | - |
| 1.0 – Infrastructure (interfaces, registry, warehouse) | 📋 PLANNED | 0/N | 0 | - |
| 2.0 – Parser Wiring (MarkdownParserCore) | 📋 PLANNED | 0/N | 0 | - |
| 3.0 – Collector Conformance (wrappers) | 📋 PLANNED | 0/N | 0 | - |

---

## Prerequisites

**ALL must be verified before starting Phase -1.0:**

- [ ] Working virtual environment + uv:
  ```bash
  uv run python -c "import sys; print(sys.version)"
  ```

- [ ] Package importable:
  ```bash
  uv run python -c "import doxstrux; print(getattr(doxstrux, '__version__', 'no-version'))"
  ```

- [ ] Existing tests pass:
  ```bash
  uv run pytest
  ```

**Quick Verification:**
```bash
uv run pytest
# Expected: all existing tests pass with zero failures/errors
```

---

## Phase -1.0 – Align Spec & Layout

**Goal:** Remove fantasy paths and names. Make DOXSTRUX_SPEC + this plan match actual `src/doxstrux` layout.  
**Estimated Time:** 0.5–1.0 hours  
**Clean Table Required:** Yes

### Task -1.0.1 – Add explicit mapping to DOXSTRUX_SPEC

- [ ] Add a "Terminology & Paths" subsection to DOXSTRUX_SPEC §2:
  - State explicitly:
    - Parser = `doxstrux/markdown_parser_core.py::MarkdownParserCore`
    - Warehouse = `doxstrux/markdown/utils/token_warehouse.py::TokenWarehouse`
    - Extractors (current) = `doxstrux/markdown/extractors/*.py`
    - Collectors (target) = `doxstrux/markdown/collectors_phase8/*.py` (wrappers around extractors)
  - Clarify that `collectors_phase8` is NEW and wraps existing extractors

- [ ] Remove/adjust any claim that TokenWarehouse "already exists":
  - Mark it as "to be created in `markdown/utils/token_warehouse.py`"

**Clean Table Check:**
- [ ] DOXSTRUX_SPEC has no misleading path assumptions about existing files
- [ ] Collector ↔ Extractor mapping documented once (and only once)
- [ ] No references to `doxstrux/markdown/parser.py` remain; all say `markdown_parser_core.py`

### Task -1.0.2 – Update this document to match final mapping

- [ ] Verify all paths match:
  - `doxstrux/markdown_parser_core.py`
  - `doxstrux/markdown/interfaces.py`
  - `doxstrux/markdown/collector_registry.py`
  - `doxstrux/markdown/collectors_phase8/*.py`
  - `doxstrux/markdown/utils/token_warehouse.py`

- [ ] Commit updated DOXSTRUX_NEXT_STEPS_1.md together with spec edits so docs are in sync

**Clean Table Check:**
- [ ] No reference in this file to non-existent legacy paths
- [ ] This document and DOXSTRUX_SPEC use the same names and paths

### Phase -1.0 Final Validation

**Success Criteria:**
- [ ] DOXSTRUX_SPEC explicitly documents Parser/Warehouse/Extractors/Collectors/Registry paths
- [ ] This plan references only those documented paths
- [ ] No contradictions between DOXSTRUX_SPEC and DOXSTRUX_NEXT_STEPS_1

**Test:**
```bash
# No code changes yet; just re-run tests to ensure no accidental breakage
uv run pytest
```

**Clean Table Check for Phase -1.0:**
- [ ] All success criteria met
- [ ] No TODO markers left in spec or this plan regarding path/term mapping

---

## Phase 0.0 – Baseline Golden Tests (SPEC §8 Step 0)

**Goal:** Freeze current observable behavior of parser + extractors so regressions are caught.  
**Estimated Time:** 2–4 hours  
**Clean Table Required:** Yes  
**Spec Reference:** DOXSTRUX_SPEC.md §8 "Execution Steps — Step 0"

### Task 0.0.1 – Per-extractor golden tests (future collectors)

- [ ] Enumerate current extractors:
  - List all modules in `doxstrux/markdown/extractors/` that the parser uses (N modules, currently 11)

- [ ] Design per-extractor fixtures:
  - For each extractor module, create at least one small markdown document
  - Must meaningfully exercise that extractor's behavior (structure, not just "non-empty")

- [ ] Add tests (e.g. `tests/test_extractors_baseline.py` or per-extractor files):
  - Use `MarkdownParserCore.parse()` from `markdown_parser_core.py` as it exists today
  - Assert specific structure:
    - Headings → exact (level, text, line) tuples
    - Tables → row/column counts, header structure
    - Lists → nesting structure
    - etc.

**Test:**
```bash
uv run pytest -q
# Expected:
# - New tests pass under CURRENT implementation
# - No existing tests regress
```

**Clean Table Check:**
- [ ] Each extractor module has at least one anchored golden test with structural assertions
- [ ] Tests are clearly labelled as "pre-refactor baseline"
- [ ] No "TODO" or "fill later" assertions
- [ ] Full suite green (`uv run pytest`)

### Task 0.0.2 – Security golden test

- [ ] Choose a security-sensitive markdown fixture:
  - One input that triggers whatever security flags/metadata are currently produced

- [ ] Add dedicated test (`tests/test_security_baseline.py`):
  - Call `MarkdownParserCore.parse(content)` as implemented today
  - Assert both:
    - Keys present in security metadata
    - Critical values (e.g. `blocked == True`, at least one issue code)

**Test:**
```bash
uv run pytest -q -k "security_baseline"
# Expected: new security test passes with current behaviour
```

**Clean Table Check:**
- [ ] Security metadata keys and critical values pinned for at least one adversarial document
- [ ] Test clearly documents it is a "baseline" against current implementation
- [ ] Full test suite still green (`uv run pytest`)

### Phase 0.0 Final Validation

**Success Criteria:**
- [ ] All extractor modules used by the parser have at least one golden test with structural assertions
- [ ] One dedicated security baseline test exists and passes
- [ ] Entire test suite passes in pre-refactor state

**Test:**
```bash
uv run pytest
```

**Clean Table Check for Phase 0.0:**
- [ ] All success criteria met
- [ ] No failing or flaky tests
- [ ] No placeholder assertions

---

## Phase 1.0 – Infrastructure (interfaces, registry, warehouse)

**Goal:** Introduce the new abstraction layer next to existing code, with zero behavior change.  
**Estimated Time:** 3–6 hours  
**Clean Table Required:** Yes  
**Spec Reference:** DOXSTRUX_SPEC.md §§3–5, §8 Step 1

### Task 1.0.1 – Create interfaces.py

- [ ] Create `doxstrux/markdown/interfaces.py`:
  - Implement `DispatchContext`, `CollectorInterest`, `Collector` as described in DOXSTRUX_SPEC
  - No extra types or behavior

**Test:**
```bash
uv run python -c "from doxstrux.markdown.interfaces import DispatchContext, CollectorInterest, Collector; print('OK')"
```

**Clean Table Check:**
- [ ] File exists and matches type/field/method signatures from DOXSTRUX_SPEC
- [ ] No additional responsibilities or ad hoc helpers
- [ ] `uv run pytest` still fully green

### Task 1.0.2 – Create collector_registry.py

- [ ] Create `doxstrux/markdown/collector_registry.py`:
  - Import `Collector` protocol from `interfaces.py`
  - Declare:
    ```python
    def default_collectors() -> tuple[Collector, ...]: ...
    def register_default_collectors(warehouse) -> None: ...
    ```
  - May return empty tuple for now (real wiring in Phase 3.0)

**Test:**
```bash
uv run python -c "from doxstrux.markdown.collector_registry import default_collectors, register_default_collectors; print('OK:', default_collectors())"
# Expected: "OK: ()" or similar placeholder
```

**Clean Table Check:**
- [ ] Functions exist with correct signatures
- [ ] No parser or other code calls `register_default_collectors` yet
- [ ] All tests still pass

### Task 1.0.3 – Create token_warehouse.py

- [ ] Create `doxstrux/markdown/utils/token_warehouse.py`:
  - `TokenWarehouse` class per DOXSTRUX_SPEC
  - Constructor accepting minimal data MarkdownParserCore will provide (tokens, content, etc.)
  - Read-only methods (`tokens`, `get_token_text`, `text_between`, `section_of`, etc.) — adapt logic from `markdown_parser_core.py`
  - Collector-related attributes and methods:
    ```python
    self._collectors: list[Collector] = []
    self._routing: dict[str, list[Collector]] = defaultdict(list)
    
    def register_collector(self, collector: Collector) -> None: ...
    def _get_collectors_for(self, token) -> list[Collector]: ...
    def dispatch_all(self) -> None: ...
    def finalize_all(self) -> dict[str, Any]: ...
    ```
  - This class is new; nothing in existing parser calls it yet

**Test:**
```bash
uv run python -c "from doxstrux.markdown.utils.token_warehouse import TokenWarehouse; print('OK')"
```

**Clean Table Check:**
- [ ] TokenWarehouse is defined and imports cleanly
- [ ] Signatures and attributes match DOXSTRUX_SPEC
- [ ] No changes yet to `markdown_parser_core.py`
- [ ] All tests still pass

### Phase 1.0 Final Validation

**Success Criteria:**
- [ ] `interfaces.py`, `collector_registry.py`, and `utils/token_warehouse.py` exist and match DOXSTRUX_SPEC APIs
- [ ] No existing code depends on these modules yet (pure addition)
- [ ] Entire test suite passes

**Test:**
```bash
uv run pytest
```

**Clean Table Check for Phase 1.0:**
- [ ] All success criteria met
- [ ] No TODOs in new modules
- [ ] No partial wiring in `markdown_parser_core.py`

---

## Phase 2.0 – Parser Wiring (markdown_parser_core.py)

**Goal:** Make MarkdownParserCore orchestrate via TokenWarehouse + collector_registry, leaving security/caching/metadata logic intact.  
**Estimated Time:** 2–4 hours  
**Clean Table Required:** Yes  
**Spec Reference:** DOXSTRUX_SPEC.md §2, §5–§6, §8 Step 2

### Task 2.0.1 – Integrate TokenWarehouse into MarkdownParserCore

- [ ] Locate in `doxstrux/markdown_parser_core.py`:
  - Where markdown-it is invoked
  - Where extractors are called directly
  - Where metadata is assembled and returned

- [ ] Introduce TokenWarehouse:
  - Instantiate with same tokens/content used today
  - Keep old extractor calls in place temporarily

**Clean Table Check:**
- [ ] New TokenWarehouse instantiation exists, but old behavior still active
- [ ] Tests still pass

### Task 2.0.2 – Switch from direct extractor calls to registry + warehouse

- [ ] Replace the block that imports/calls extractors directly with:
  ```python
  from doxstrux.markdown.collector_registry import register_default_collectors
  
  register_default_collectors(self._warehouse)  # or local var
  self._warehouse.dispatch_all()
  metadata_from_collectors = self._warehouse.finalize_all()
  ```

- [ ] Integrate `metadata_from_collectors` into existing metadata structure without changing:
  - Security checks
  - Config handling
  - Top-level return schema

- [ ] Remove direct extractor imports from `markdown_parser_core.py` (they move behind registry)

**Test:**
```bash
uv run pytest
# Expected:
# - All tests pass
# - Golden tests from Phase 0.0 show consistent structures
# - Security baseline still matches
```

**Clean Table Check:**
- [ ] No direct imports of extractor modules remain in `markdown_parser_core.py`
- [ ] All collector outputs flow via TokenWarehouse and collector_registry
- [ ] Golden tests and security baseline tests from Phase 0.0 still pass unmodified

### Phase 2.0 Final Validation

**Success Criteria:**
- [ ] MarkdownParserCore uses TokenWarehouse + `register_default_collectors` as orchestration path
- [ ] Direct extractor wiring fully removed from `markdown_parser_core.py`
- [ ] All tests (including golden and security) pass

**Test:**
```bash
uv run pytest
```

**Clean Table Check for Phase 2.0:**
- [ ] All success criteria met
- [ ] No TODOs in `markdown_parser_core.py` related to wiring

---

## Phase 3.0 – Collector Conformance (collectors_phase8 wrappers)

**Goal:** Implement Collector protocol for all feature areas by adding wrapper classes in `collectors_phase8/` that delegate to existing `extractors/`.  
**Estimated Time:** 4–8 hours  
**Clean Table Required:** Yes  
**Spec Reference:** DOXSTRUX_SPEC.md §§3–5, §8 Step 3

### Task 3.0.1 – Define Collector ↔ Extractor mapping

Before writing any wrappers, explicitly document the mapping between intended Collector classes and current extractor modules/entry points.

**This mapping MUST be completed and agreed before coding Phase 3.0.**  
Once filled, it becomes the ground truth for registry wiring and golden test coverage.

#### Collector–Extractor Mapping Table (to be filled based on actual code)

| Collector Class | Extractor Module | Entry Point / Notes |
|-----------------|------------------|---------------------|
| SectionsCollector | `markdown/extractors/sections.py` | e.g. `extract_sections(...)` |
| HeadingsCollector | `markdown/extractors/sections.py` | e.g. headings part of sections; confirm actual func |
| ParagraphsCollector | `markdown/extractors/sections.py` or other | Confirm module + function |
| ListsCollector | `markdown/extractors/lists.py` (if exists) | e.g. `extract_lists(...)` |
| TasklistsCollector | `markdown/extractors/lists.py` (if exists) | e.g. task-list subset; confirm |
| CodeblocksCollector | `markdown/extractors/codeblocks.py` (?) | Confirm module + function |
| TablesCollector | `markdown/extractors/tables.py` | e.g. `extract_tables(...)` |
| LinksCollector | `markdown/extractors/links.py` (?) | Confirm module + function |
| ImagesCollector | `markdown/extractors/media.py` (?) | Confirm module + function |
| FootnotesCollector | `markdown/extractors/footnotes.py` (?) | Confirm module + function |
| HtmlCollector | `markdown/extractors/html.py` (?) | Confirm module + function |
| MathCollector | `markdown/extractors/math.py` (?) | Confirm module + function |

**Notes:**
- Replace `?` and "Confirm..." with real module paths and function names from actual codebase
- Multiple Collectors may delegate to same module (e.g., sections/headings share `sections.py`)
- If a Collector in the spec has no corresponding extractor, document explicitly

**Clean Table Check (for mapping table):**
- [ ] Every Collector listed in DOXSTRUX_SPEC has a corresponding row
- [ ] Each row has concrete module path and entry point (no `?`, no "confirm")
- [ ] Number of Collectors matches what `default_collectors()` will return

### Task 3.0.2 – Create collectors_phase8 package

- [ ] Create directory `doxstrux/markdown/collectors_phase8/` with `__init__.py`

- [ ] For each mapping row, create a Collector class that:
  - Implements `Collector` interface from `interfaces.py`
  - Delegates to existing extractor logic from mapping table

- [ ] Export Collector classes at package level from `collectors_phase8/__init__.py`

**Test:**
```bash
uv run python -c "from doxstrux.markdown.collector_registry import default_collectors; print([c.name for c in default_collectors()])"
# Expected: prints names of all Collector instances defined for current feature set
```

**Clean Table Check:**
- [ ] `collectors_phase8` package exists and is importable
- [ ] For each row in mapping table, a corresponding Collector class exists and is exported
- [ ] `default_collectors()` returns the Collector instances documented in mapping table

### Task 3.0.3 – Verify per-collector behavior against golden tests

- [ ] Run all golden tests from Phase 0.0:
  - They should pass with new Collector-based wiring

- [ ] If any golden test breaks:
  - Fix ONLY the adapter/wiring, not core extractor algorithms

**Test:**
```bash
uv run pytest -q
# Expected: all golden tests pass unchanged
```

**Clean Table Check:**
- [ ] Each feature's golden test passes with new Collector wrappers
- [ ] No algorithmic changes in extractors themselves (only adapters/wiring changed)

### Phase 3.0 Final Validation

**Success Criteria:**
- [ ] `collectors_phase8` package contains Collector implementations for all mapped features
- [ ] `collector_registry` imports from `collectors_phase8` only
- [ ] Collector–Extractor mapping table fully resolved (no placeholders) and matches actual code
- [ ] All tests (golden, security, existing) pass

**Test:**
```bash
uv run pytest
```

**Clean Table Check for Phase 3.0:**
- [ ] All success criteria met
- [ ] No TODOs or "temporary" notes left in wrappers, registry, or mapping table

---

## File Changes Summary

| File / Directory | Action | Phase |
|------------------|--------|-------|
| `doxstrux/markdown/interfaces.py` | CREATE | 1.0 |
| `doxstrux/markdown/collector_registry.py` | CREATE | 1.0 |
| `doxstrux/markdown/utils/token_warehouse.py` | CREATE | 1.0 |
| `doxstrux/markdown_parser_core.py` | UPDATE | 2.0 |
| `doxstrux/markdown/collectors_phase8/` | CREATE | 3.0 |
| `doxstrux/markdown/collectors_phase8/__init__.py` | CREATE | 3.0 |
| `doxstrux/markdown/collectors_phase8/*.py` | CREATE | 3.0 |
| `tests/test_extractors_baseline*.py` | CREATE/UPDATE | 0.0 |
| `tests/test_security_baseline.py` | CREATE | 0.0 |

---

## Overall Success Criteria

- [ ] DOXSTRUX_SPEC §§2–6 and §8 implemented in code (interfaces, registry, warehouse, parser wiring, collectors)
- [ ] All pre-refactor golden tests and security tests still passing
- [ ] Public API of MarkdownParserCore unchanged:
  ```python
  MarkdownParserCore(content: str, *, config: dict | None = None, security_profile: str | None = None)
  parse(self) -> dict
  ```
- [ ] All tests pass:
  ```bash
  uv run pytest
  ```
- [ ] Clean Table achieved: no TODOs, no speculative half-measures, no failing tests

---

## Clean Table Principle

A phase is **CLEAN** only if:

- ✅ No unresolved errors, warnings, or TODOs
- ✅ No unverified assumptions
- ✅ No duplicated or conflicting logic
- ✅ Code and tests are production-ready
- ✅ Documentation and plans match actual code structure

**Do not start the next phase until the current phase passes its Clean Table check.**

---

*End of DOXSTRUX_NEXT_STEPS_1.md*
