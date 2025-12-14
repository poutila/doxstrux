# DOXSTRUX - AI Task List

**Project**: Parser/Warehouse/Collector/Registry Refactor
**Created**: 2025-12-13
**Status**: Phase -1 - NOT STARTED

**Related Documents**:
- `DOXSTRUX_SPEC.md` – Target architecture (normative)
- `DOXSTRUX_SOLID_ANALYSIS.md` – Pre-refactor diagnosis (archived)

---

## Quick Status Dashboard

| Phase | Name | Status | Tests | Clean Table |
|-------|------|--------|-------|-------------|
| -1 | Align Spec & Layout | ⏳ NOT STARTED | -/- | - |
| 0 | Baseline Golden Tests | 📋 PLANNED | -/- | - |
| 1 | Infrastructure | 📋 PLANNED | -/- | - |
| 2 | Parser Wiring | 📋 PLANNED | -/- | - |
| 3 | Collector Conformance | 📋 PLANNED | -/- | - |

**Status Key**: ✅ COMPLETE | ⏳ IN PROGRESS | 📋 PLANNED | ❌ BLOCKED

---

## Success Criteria (Project-Level)

The project is DONE when ALL of these are true:

- [ ] DOXSTRUX_SPEC §§2–6 and §8 implemented (interfaces, registry, warehouse, parser wiring, collectors)
- [ ] All pre-refactor golden tests and security tests still passing
- [ ] Public API unchanged: `MarkdownParserCore(content, *, config, security_profile).parse() -> dict`
- [ ] All tests pass: `uv run pytest`
- [ ] Clean Table: no TODOs, no speculative code, no failing tests

---

## ⛔ PHASE GATE RULES

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE N+1 CANNOT START UNTIL:                              │
│                                                             │
│  1. All Phase N tasks have ✅ status                        │
│  2. Phase N tests pass: uv run pytest → ALL PASS            │
│  3. Phase N Clean Table verified                            │
│  4. Phase unlock artifact exists: .phase-N.complete.json    │
│                                                             │
│  If ANY criterion fails → STOP. Fix or rollback.            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 TDD Protocol

Every implementation task follows this sequence:

```
1. WRITE TEST FIRST (or identify existing test)
   └── Test must fail initially or be new

2. IMPLEMENT minimum code to pass
   └── Match DOXSTRUX_SPEC signatures exactly

3. VERIFY no regressions
   └── Run: uv run pytest
   └── Expected: ALL PASS

4. CLEAN TABLE CHECK
   └── No TODOs, no placeholders, no warnings
```

**Test Commands Reference**:
```bash
# Fast iteration (single test file)
uv run pytest tests/test_specific.py -v

# Full validation (before commits)
uv run pytest

# Import check (new modules)
uv run python -c "from doxstrux.markdown.MODULE import CLASS; print('OK')"
```

---

## 🧹 Clean Table Definition

> A task is CLEAN only when ALL are true:

- ✅ No unresolved errors or warnings
- ✅ No TODOs, FIXMEs, or placeholders in changed code
- ✅ No unverified assumptions
- ✅ Signatures match DOXSTRUX_SPEC exactly
- ✅ Tests pass (not skipped, not mocked away)
- ✅ Documentation and code paths are consistent

**If any box is unchecked → task is NOT complete.**

---

## Architecture Reference

### Current Layout (authoritative)
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

### Target Architecture
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

---

## Prerequisites

**ALL must pass before Phase -1 begins:**

- [ ] **Working virtual environment + uv**:
  ```bash
  uv run python -c "import sys; print(sys.version)"
  # Expected: Python version string
  ```

- [ ] **Package importable**:
  ```bash
  uv run python -c "import doxstrux; print(getattr(doxstrux, '__version__', 'no-version'))"
  # Expected: version or 'no-version' (no ImportError)
  ```

- [ ] **Existing tests pass**:
  ```bash
  uv run pytest
  # Expected: ALL PASS, zero failures/errors
  ```

**Quick Verification**:
```bash
uv run pytest && echo "✅ Prerequisites met" || echo "❌ BLOCKED"
```

---

# Phase -1: Align Spec & Layout

**Goal**: Remove fantasy paths. Make DOXSTRUX_SPEC + this plan match actual `src/doxstrux` layout.
**Time Estimate**: 0.5–1.0 hours
**Status**: ⏳ NOT STARTED

---

## Task -1.1: Add explicit mapping to DOXSTRUX_SPEC

**Objective**: Document real paths in spec so all documents agree
**Files**: `DOXSTRUX_SPEC.md`

### Steps

- [ ] Add "Terminology & Paths" subsection to DOXSTRUX_SPEC §2:
  - Parser = `doxstrux/markdown_parser_core.py::MarkdownParserCore`
  - Warehouse = `doxstrux/markdown/utils/token_warehouse.py::TokenWarehouse`
  - Extractors (current) = `doxstrux/markdown/extractors/*.py`
  - Collectors (target) = `doxstrux/markdown/collectors_phase8/*.py`

- [ ] Remove/adjust any claim that TokenWarehouse "already exists"
  - Mark as "to be created in `markdown/utils/token_warehouse.py`"

### Verify

```bash
# No code changes; ensure tests still pass
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] DOXSTRUX_SPEC has no misleading path assumptions
- [ ] Collector ↔ Extractor mapping documented once (not duplicated)
- [ ] No references to `doxstrux/markdown/parser.py` remain
- [ ] Tests still pass

**Status**: ⏳ NOT STARTED

---

## Task -1.2: Update this document to match final mapping

**Objective**: Ensure this plan and spec use identical paths
**Files**: This document

### Steps

- [ ] Verify all paths in this document match:
  - `doxstrux/markdown_parser_core.py`
  - `doxstrux/markdown/interfaces.py`
  - `doxstrux/markdown/collector_registry.py`
  - `doxstrux/markdown/collectors_phase8/*.py`
  - `doxstrux/markdown/utils/token_warehouse.py`

- [ ] Commit updated docs together so they stay in sync

### Verify

```bash
uv run pytest
# Expected: ALL PASS (no code changes, just doc edits)
```

### ⛔ STOP: Clean Table Check

- [ ] No reference in this file to non-existent paths
- [ ] This document and DOXSTRUX_SPEC use same names/paths
- [ ] Docs committed together

**Status**: ⏳ NOT STARTED

---

## ⛔ STOP: Phase -1 Gate

**Before starting Phase 0, ALL must be true:**

```bash
# 1. Tests still pass (no accidental breakage)
uv run pytest
# Expected: ALL PASS

# 2. Spec and plan aligned (manual check)
grep -l "markdown_parser_core.py" DOXSTRUX_SPEC.md
# Expected: file found (path is documented)
```

### Phase -1 Completion Checklist

- [ ] DOXSTRUX_SPEC explicitly documents Parser/Warehouse/Extractors/Collectors/Registry paths
- [ ] This plan references only those documented paths
- [ ] No contradictions between DOXSTRUX_SPEC and this document
- [ ] No TODO markers left regarding path/term mapping
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
# Only run after ALL above criteria pass
cat > .phase--1.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": -1,
  "phase_name": "Align Spec & Layout",
  "tests_passed": "all",
  "clean_table": true,
  "git_commit": "$(git rev-parse HEAD)",
  "completion_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

git add .phase--1.complete.json DOXSTRUX_SPEC.md
git commit -m "Phase -1 complete: spec and plan aligned"
git tag phase--1-complete
```

**Phase -1 Status**: ⏳ NOT STARTED

---

# Phase 0: Baseline Golden Tests

**Goal**: Freeze current observable behavior so regressions are caught
**Time Estimate**: 2–4 hours
**Prerequisite**: `.phase--1.complete.json` must exist
**Spec Reference**: DOXSTRUX_SPEC.md §8 Step 0
**Status**: 📋 PLANNED

---

## ⛔ STOP: Verify Phase -1 Complete

```bash
test -f .phase--1.complete.json && echo "✅ Phase -1 complete" || echo "❌ BLOCKED"
```

---

## Task 0.1: Per-extractor golden tests

**Objective**: Create structural baseline tests for each extractor
**Files**: `tests/test_extractors_baseline.py` (or per-extractor files)

### TDD Step 1: Design Tests

- [ ] Enumerate current extractors in `doxstrux/markdown/extractors/`
  ```bash
  ls -1 doxstrux/markdown/extractors/*.py | grep -v __pycache__
  ```

- [ ] For each extractor module, design at least one fixture:
  - Small markdown document that exercises that extractor
  - Structural assertions (not just "non-empty")

### TDD Step 2: Implement Tests

```python
# tests/test_extractors_baseline.py
"""Pre-refactor baseline tests - DO NOT MODIFY after Phase 0"""

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore

class TestSectionsBaseline:
    """Baseline for sections extractor behavior."""
    
    def test_heading_extraction_structure(self):
        content = "# Title\n\nParagraph\n\n## Subtitle\n\nMore text"
        parser = MarkdownParserCore(content)
        result = parser.parse()
        
        # Structural assertions - exact values from current behavior
        headings = result.get("headings", [])
        assert len(headings) == 2
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "Title"
        assert headings[1]["level"] == 2
        assert headings[1]["text"] == "Subtitle"

# Similar classes for each extractor...
```

### TDD Step 3: Verify (GREEN)

```bash
# Run new baseline tests
uv run pytest tests/test_extractors_baseline.py -v
# Expected: ALL PASS (tests match current behavior)

# Full suite (no regressions)
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] Each extractor module has at least one anchored golden test
- [ ] Tests use structural assertions (not "assert result is not None")
- [ ] Tests clearly labelled as "pre-refactor baseline"
- [ ] No "TODO" or "fill later" assertions
- [ ] Full suite green

**Status**: 📋 PLANNED

---

## Task 0.2: Security golden test

**Objective**: Pin security metadata behavior for at least one adversarial document
**Files**: `tests/test_security_baseline.py`

### TDD Step 1: Design Test

- [ ] Choose security-sensitive markdown fixture
- [ ] Identify what security flags/metadata are currently produced

### TDD Step 2: Implement Test

```python
# tests/test_security_baseline.py
"""Pre-refactor security baseline - DO NOT MODIFY after Phase 0"""

from doxstrux.markdown_parser_core import MarkdownParserCore

def test_security_metadata_structure():
    """Baseline: security metadata keys and critical values."""
    # Adversarial content that triggers security flags
    content = """
    <script>alert('xss')</script>
    [link](javascript:void(0))
    """
    
    parser = MarkdownParserCore(content)
    result = parser.parse()
    
    security = result.get("security", {})
    # Assert specific keys exist
    assert "issues" in security or "blocked" in security
    # Assert specific values from current behavior
    # (fill in actual expected values after first run)
```

### TDD Step 3: Verify (GREEN)

```bash
uv run pytest tests/test_security_baseline.py -v
# Expected: PASS

uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] Security metadata keys and critical values pinned
- [ ] Test documents it is a "baseline" against current implementation
- [ ] Full test suite green

**Status**: 📋 PLANNED

---

## ⛔ STOP: Phase 0 Gate

**Before starting Phase 1, ALL must be true:**

```bash
# 1. All tests pass
uv run pytest
# Expected: ALL PASS

# 2. Baseline tests exist
ls tests/test_*baseline*.py
# Expected: at least 2 files

# 3. No placeholder assertions
grep -rn "TODO\|NotImplemented\|pass  #" tests/test_*baseline*.py
# Expected: no results
```

### Phase 0 Completion Checklist

- [ ] All extractor modules have at least one golden test with structural assertions
- [ ] One dedicated security baseline test exists and passes
- [ ] Entire test suite passes in pre-refactor state
- [ ] No placeholder assertions
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
cat > .phase-0.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 0,
  "phase_name": "Baseline Golden Tests",
  "tests_passed": "$(uv run pytest --collect-only -q | tail -1)",
  "baseline_tests_created": true,
  "clean_table": true,
  "git_commit": "$(git rev-parse HEAD)",
  "completion_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

git add .phase-0.complete.json tests/test_*baseline*.py
git commit -m "Phase 0 complete: baseline golden tests established"
git tag phase-0-complete
```

**Phase 0 Status**: 📋 PLANNED

---

# Phase 1: Infrastructure

**Goal**: Introduce new abstraction layer (interfaces, registry, warehouse) with zero behavior change
**Time Estimate**: 3–6 hours
**Prerequisite**: `.phase-0.complete.json` must exist
**Spec Reference**: DOXSTRUX_SPEC.md §§3–5, §8 Step 1
**Status**: 📋 PLANNED

---

## ⛔ STOP: Verify Phase 0 Complete

```bash
test -f .phase-0.complete.json && echo "✅ Phase 0 complete" || echo "❌ BLOCKED"
```

---

## Task 1.1: Create interfaces.py

**Objective**: Define `DispatchContext`, `CollectorInterest`, `Collector` protocols
**Files**: `doxstrux/markdown/interfaces.py`

### TDD Step 1: Write Test First

```python
# tests/test_interfaces.py
"""Test interface definitions match DOXSTRUX_SPEC."""

def test_interfaces_importable():
    from doxstrux.markdown.interfaces import (
        DispatchContext,
        CollectorInterest,
        Collector
    )
    # Verify they are protocols/classes
    assert DispatchContext is not None
    assert CollectorInterest is not None
    assert Collector is not None

def test_collector_protocol_methods():
    from doxstrux.markdown.interfaces import Collector
    # Verify expected methods exist on protocol
    assert hasattr(Collector, 'name')
    assert hasattr(Collector, 'interest')
    assert hasattr(Collector, 'dispatch')
    assert hasattr(Collector, 'finalize')
```

```bash
# Verify test fails (RED) - module doesn't exist yet
uv run pytest tests/test_interfaces.py -v
# Expected: ImportError (module not found)
```

### TDD Step 2: Implement

```python
# doxstrux/markdown/interfaces.py
"""Interface definitions per DOXSTRUX_SPEC §§3-4."""

from typing import Protocol, Any, runtime_checkable
from dataclasses import dataclass

@dataclass(frozen=True)
class DispatchContext:
    """Context passed to collectors during dispatch."""
    token: Any
    token_index: int
    warehouse: Any  # TokenWarehouse (forward ref)

@dataclass(frozen=True)
class CollectorInterest:
    """Declares what token types a collector wants."""
    token_types: frozenset[str]

@runtime_checkable
class Collector(Protocol):
    """Protocol for all collectors per DOXSTRUX_SPEC §4."""
    
    @property
    def name(self) -> str: ...
    
    def interest(self) -> CollectorInterest: ...
    
    def dispatch(self, ctx: DispatchContext) -> None: ...
    
    def finalize(self) -> dict[str, Any]: ...
```

### TDD Step 3: Verify (GREEN)

```bash
# Import check
uv run python -c "from doxstrux.markdown.interfaces import DispatchContext, CollectorInterest, Collector; print('OK')"
# Expected: OK

# Test passes
uv run pytest tests/test_interfaces.py -v
# Expected: PASS

# Full suite (no regressions)
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] File exists at `doxstrux/markdown/interfaces.py`
- [ ] Signatures match DOXSTRUX_SPEC exactly
- [ ] No additional responsibilities or ad hoc helpers
- [ ] Tests pass
- [ ] Full suite green

**Status**: 📋 PLANNED

---

## Task 1.2: Create collector_registry.py

**Objective**: Define registry functions (empty implementation for now)
**Files**: `doxstrux/markdown/collector_registry.py`

### TDD Step 1: Write Test First

```python
# tests/test_collector_registry.py
"""Test registry functions exist with correct signatures."""

def test_registry_importable():
    from doxstrux.markdown.collector_registry import (
        default_collectors,
        register_default_collectors
    )
    assert callable(default_collectors)
    assert callable(register_default_collectors)

def test_default_collectors_returns_tuple():
    from doxstrux.markdown.collector_registry import default_collectors
    result = default_collectors()
    assert isinstance(result, tuple)
```

```bash
# Verify test fails (RED)
uv run pytest tests/test_collector_registry.py -v
# Expected: ImportError
```

### TDD Step 2: Implement

```python
# doxstrux/markdown/collector_registry.py
"""Collector registry per DOXSTRUX_SPEC §5."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from doxstrux.markdown.interfaces import Collector
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse

def default_collectors() -> tuple:  # tuple[Collector, ...]
    """Return all default collectors. Empty until Phase 3."""
    return ()

def register_default_collectors(warehouse: "TokenWarehouse") -> None:
    """Register all default collectors with warehouse. Wired in Phase 3."""
    for collector in default_collectors():
        warehouse.register_collector(collector)
```

### TDD Step 3: Verify (GREEN)

```bash
# Import check
uv run python -c "from doxstrux.markdown.collector_registry import default_collectors, register_default_collectors; print('OK:', default_collectors())"
# Expected: OK: ()

# Tests pass
uv run pytest tests/test_collector_registry.py -v
# Expected: PASS

# Full suite
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] Functions exist with correct signatures
- [ ] Returns empty tuple (real wiring in Phase 3)
- [ ] No parser code calls these yet
- [ ] Tests pass

**Status**: 📋 PLANNED

---

## Task 1.3: Create token_warehouse.py

**Objective**: Implement TokenWarehouse class per DOXSTRUX_SPEC
**Files**: `doxstrux/markdown/utils/token_warehouse.py`

### TDD Step 1: Write Test First

```python
# tests/test_token_warehouse.py
"""Test TokenWarehouse implementation."""

def test_warehouse_importable():
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    assert TokenWarehouse is not None

def test_warehouse_instantiation():
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    # Minimal instantiation (adapt to actual constructor)
    wh = TokenWarehouse(tokens=[], content="")
    assert wh is not None

def test_warehouse_has_collector_methods():
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    wh = TokenWarehouse(tokens=[], content="")
    assert hasattr(wh, 'register_collector')
    assert hasattr(wh, 'dispatch_all')
    assert hasattr(wh, 'finalize_all')
```

```bash
# Verify test fails (RED)
uv run pytest tests/test_token_warehouse.py -v
# Expected: ImportError
```

### TDD Step 2: Implement

```python
# doxstrux/markdown/utils/token_warehouse.py
"""TokenWarehouse per DOXSTRUX_SPEC §3."""

from typing import Any, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from doxstrux.markdown.interfaces import Collector, DispatchContext

class TokenWarehouse:
    """Central token storage and collector orchestration."""
    
    def __init__(self, tokens: list, content: str, **kwargs):
        self._tokens = tokens
        self._content = content
        self._collectors: list["Collector"] = []
        self._routing: dict[str, list["Collector"]] = defaultdict(list)
    
    @property
    def tokens(self) -> list:
        return self._tokens
    
    @property
    def content(self) -> str:
        return self._content
    
    def register_collector(self, collector: "Collector") -> None:
        """Register a collector and build routing table."""
        self._collectors.append(collector)
        interest = collector.interest()
        for token_type in interest.token_types:
            self._routing[token_type].append(collector)
    
    def _get_collectors_for(self, token: Any) -> list["Collector"]:
        """Get collectors interested in this token type."""
        token_type = token.get("type", "") if isinstance(token, dict) else getattr(token, "type", "")
        return self._routing.get(token_type, [])
    
    def dispatch_all(self) -> None:
        """Dispatch all tokens to interested collectors."""
        from doxstrux.markdown.interfaces import DispatchContext
        
        for idx, token in enumerate(self._tokens):
            collectors = self._get_collectors_for(token)
            if collectors:
                ctx = DispatchContext(token=token, token_index=idx, warehouse=self)
                for collector in collectors:
                    collector.dispatch(ctx)
    
    def finalize_all(self) -> dict[str, Any]:
        """Finalize all collectors and merge results."""
        result = {}
        for collector in self._collectors:
            collector_result = collector.finalize()
            result[collector.name] = collector_result
        return result
```

### TDD Step 3: Verify (GREEN)

```bash
# Import check
uv run python -c "from doxstrux.markdown.utils.token_warehouse import TokenWarehouse; print('OK')"
# Expected: OK

# Tests pass
uv run pytest tests/test_token_warehouse.py -v
# Expected: PASS

# Full suite
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] TokenWarehouse defined and imports cleanly
- [ ] Signatures match DOXSTRUX_SPEC
- [ ] No changes to `markdown_parser_core.py` yet
- [ ] Tests pass

**Status**: 📋 PLANNED

---

## ⛔ STOP: Phase 1 Gate

**Before starting Phase 2, ALL must be true:**

```bash
# 1. All new modules importable
uv run python -c "
from doxstrux.markdown.interfaces import DispatchContext, CollectorInterest, Collector
from doxstrux.markdown.collector_registry import default_collectors, register_default_collectors
from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
print('✅ All infrastructure modules importable')
"

# 2. All tests pass
uv run pytest
# Expected: ALL PASS

# 3. No changes to parser yet
git diff doxstrux/markdown_parser_core.py
# Expected: no changes (or empty)
```

### Phase 1 Completion Checklist

- [ ] `interfaces.py` exists and matches DOXSTRUX_SPEC APIs
- [ ] `collector_registry.py` exists with correct signatures
- [ ] `token_warehouse.py` exists with correct signatures
- [ ] No existing code depends on these modules yet (pure addition)
- [ ] All tests pass
- [ ] No TODOs in new modules
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
cat > .phase-1.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 1,
  "phase_name": "Infrastructure",
  "modules_created": [
    "doxstrux/markdown/interfaces.py",
    "doxstrux/markdown/collector_registry.py",
    "doxstrux/markdown/utils/token_warehouse.py"
  ],
  "parser_modified": false,
  "clean_table": true,
  "git_commit": "$(git rev-parse HEAD)",
  "completion_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

git add .phase-1.complete.json doxstrux/markdown/interfaces.py doxstrux/markdown/collector_registry.py doxstrux/markdown/utils/token_warehouse.py tests/test_*.py
git commit -m "Phase 1 complete: infrastructure modules created"
git tag phase-1-complete
```

**Phase 1 Status**: 📋 PLANNED

---

# Phase 2: Parser Wiring

**Goal**: Make MarkdownParserCore orchestrate via TokenWarehouse + collector_registry
**Time Estimate**: 2–4 hours
**Prerequisite**: `.phase-1.complete.json` must exist
**Spec Reference**: DOXSTRUX_SPEC.md §2, §5–§6, §8 Step 2
**Status**: 📋 PLANNED

---

## ⛔ STOP: Verify Phase 1 Complete

```bash
test -f .phase-1.complete.json && echo "✅ Phase 1 complete" || echo "❌ BLOCKED"
```

---

## Task 2.1: Integrate TokenWarehouse into MarkdownParserCore

**Objective**: Add warehouse instantiation without changing behavior yet
**Files**: `doxstrux/markdown_parser_core.py`

### TDD Step 1: Identify Integration Points

```bash
# Find where markdown-it is invoked
grep -n "markdown-it\|MarkdownIt\|tokens" doxstrux/markdown_parser_core.py | head -20

# Find where extractors are called
grep -n "extract\|from.*extractors" doxstrux/markdown_parser_core.py | head -20
```

### TDD Step 2: Add Warehouse (No Behavior Change)

- [ ] Import TokenWarehouse
- [ ] Instantiate with same tokens/content used today
- [ ] Keep old extractor calls in place (parallel path)

```python
# In MarkdownParserCore.parse() - add but don't use yet
from doxstrux.markdown.utils.token_warehouse import TokenWarehouse

# After tokens are generated:
self._warehouse = TokenWarehouse(tokens=tokens, content=self._content)
# ... existing extractor calls continue unchanged ...
```

### TDD Step 3: Verify (No Regressions)

```bash
# Golden tests must still pass
uv run pytest tests/test_*baseline*.py -v
# Expected: ALL PASS

# Full suite
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] TokenWarehouse instantiation exists in parser
- [ ] Old extractor behavior still active (not replaced)
- [ ] All tests still pass
- [ ] No functional change

**Status**: 📋 PLANNED

---

## Task 2.2: Switch to registry + warehouse orchestration

**Objective**: Replace direct extractor calls with collector-based dispatch
**Files**: `doxstrux/markdown_parser_core.py`

### TDD Step 1: Existing Tests Are the Spec

The golden tests from Phase 0 define correct behavior. They must pass after this change.

### TDD Step 2: Replace Extractor Wiring

```python
# Replace direct extractor imports/calls with:
from doxstrux.markdown.collector_registry import register_default_collectors

# In parse():
register_default_collectors(self._warehouse)
self._warehouse.dispatch_all()
metadata_from_collectors = self._warehouse.finalize_all()

# Integrate metadata_from_collectors into existing return structure
# WITHOUT changing: security checks, config handling, top-level schema
```

- [ ] Remove direct extractor imports from `markdown_parser_core.py`
- [ ] Integrate `metadata_from_collectors` into existing metadata structure

### TDD Step 3: Verify (Golden Tests Pass)

```bash
# Golden tests - critical
uv run pytest tests/test_*baseline*.py -v
# Expected: ALL PASS (same structure as before)

# Security baseline
uv run pytest tests/test_security_baseline.py -v
# Expected: PASS

# Full suite
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] No direct imports of extractor modules in `markdown_parser_core.py`
- [ ] All collector outputs flow via TokenWarehouse and registry
- [ ] Golden tests pass unmodified
- [ ] Security baseline passes

**Status**: 📋 PLANNED

---

## ⛔ STOP: Phase 2 Gate

**Before starting Phase 3, ALL must be true:**

```bash
# 1. No direct extractor imports in parser
grep -c "from.*extractors import" doxstrux/markdown_parser_core.py
# Expected: 0

# 2. All tests pass
uv run pytest
# Expected: ALL PASS

# 3. Golden tests unchanged
git diff tests/test_*baseline*.py
# Expected: no changes
```

### Phase 2 Completion Checklist

- [ ] MarkdownParserCore uses TokenWarehouse + registry as orchestration path
- [ ] Direct extractor wiring fully removed from parser
- [ ] All tests (including golden and security) pass
- [ ] No TODOs in parser related to wiring
- [ ] Git checkpoint created

### Create Phase Unlock Artifact

```bash
cat > .phase-2.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 2,
  "phase_name": "Parser Wiring",
  "parser_uses_warehouse": true,
  "direct_extractor_imports_removed": true,
  "golden_tests_pass": true,
  "clean_table": true,
  "git_commit": "$(git rev-parse HEAD)",
  "completion_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

git add .phase-2.complete.json doxstrux/markdown_parser_core.py
git commit -m "Phase 2 complete: parser wired to warehouse + registry"
git tag phase-2-complete
```

**Phase 2 Status**: 📋 PLANNED

---

# Phase 3: Collector Conformance

**Goal**: Implement Collector protocol wrappers for all extractors
**Time Estimate**: 4–8 hours
**Prerequisite**: `.phase-2.complete.json` must exist
**Spec Reference**: DOXSTRUX_SPEC.md §§3–5, §8 Step 3
**Status**: 📋 PLANNED

---

## ⛔ STOP: Verify Phase 2 Complete

```bash
test -f .phase-2.complete.json && echo "✅ Phase 2 complete" || echo "❌ BLOCKED"
```

---

## Task 3.1: Define Collector ↔ Extractor mapping

**Objective**: Document exact mapping before writing any code
**Files**: This document (update table below)

**⚠️ This mapping MUST be completed before coding Task 3.2**

### Collector–Extractor Mapping Table

| Collector Class | Extractor Module | Entry Point | Verified |
|-----------------|------------------|-------------|----------|
| SectionsCollector | `markdown/extractors/sections.py` | `extract_sections(...)` | [ ] |
| HeadingsCollector | `markdown/extractors/sections.py` | (part of sections) | [ ] |
| TablesCollector | `markdown/extractors/tables.py` | `extract_tables(...)` | [ ] |
| ... | ... | ... | [ ] |

**Fill this table by inspecting actual code:**
```bash
# List all extractor modules
ls -1 doxstrux/markdown/extractors/*.py | grep -v __pycache__

# For each, find entry points
grep -n "^def " doxstrux/markdown/extractors/sections.py
```

### ⛔ STOP: Clean Table Check (Mapping Only)

- [ ] Every Collector in DOXSTRUX_SPEC has a row
- [ ] Each row has concrete module path and entry point (no `?`)
- [ ] Number of Collectors matches `default_collectors()` planned count

**Status**: 📋 PLANNED

---

## Task 3.2: Create collectors_phase8 package

**Objective**: Create wrapper classes implementing Collector protocol
**Files**: `doxstrux/markdown/collectors_phase8/` (new directory)

### TDD Step 1: Write Test First

```python
# tests/test_collectors_phase8.py
"""Test collector wrappers implement protocol correctly."""

from doxstrux.markdown.interfaces import Collector

def test_collectors_package_importable():
    from doxstrux.markdown import collectors_phase8
    assert collectors_phase8 is not None

def test_sections_collector_implements_protocol():
    from doxstrux.markdown.collectors_phase8 import SectionsCollector
    collector = SectionsCollector()
    assert isinstance(collector, Collector)
    assert hasattr(collector, 'name')
    assert hasattr(collector, 'interest')
    assert hasattr(collector, 'dispatch')
    assert hasattr(collector, 'finalize')
```

```bash
# Verify test fails (RED)
uv run pytest tests/test_collectors_phase8.py -v
# Expected: ImportError
```

### TDD Step 2: Implement Collectors

```python
# doxstrux/markdown/collectors_phase8/__init__.py
"""Collector wrappers for Phase 8 architecture."""

from .sections import SectionsCollector
from .tables import TablesCollector
# ... etc based on mapping table

__all__ = [
    "SectionsCollector",
    "TablesCollector",
    # ...
]
```

```python
# doxstrux/markdown/collectors_phase8/sections.py
"""Sections collector wrapping existing extractor."""

from typing import Any
from doxstrux.markdown.interfaces import Collector, CollectorInterest, DispatchContext
from doxstrux.markdown.extractors.sections import extract_sections  # existing

class SectionsCollector:
    """Collector wrapper for sections extractor."""
    
    def __init__(self):
        self._collected = []
    
    @property
    def name(self) -> str:
        return "sections"
    
    def interest(self) -> CollectorInterest:
        return CollectorInterest(token_types=frozenset({"heading_open", "paragraph_open"}))
    
    def dispatch(self, ctx: DispatchContext) -> None:
        # Delegate to existing extractor or collect for batch
        self._collected.append(ctx.token)
    
    def finalize(self) -> dict[str, Any]:
        # Call existing extractor with collected data
        # Adapt as needed based on actual extractor signature
        return {"sections": extract_sections(self._collected)}
```

### TDD Step 3: Verify (GREEN)

```bash
# Import check
uv run python -c "from doxstrux.markdown.collector_registry import default_collectors; print([c.name for c in default_collectors()])"
# Expected: list of collector names

# Tests pass
uv run pytest tests/test_collectors_phase8.py -v
# Expected: PASS

# Full suite
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] `collectors_phase8` package exists and is importable
- [ ] For each row in mapping table, Collector class exists
- [ ] `default_collectors()` returns all collectors
- [ ] Tests pass

**Status**: 📋 PLANNED

---

## Task 3.3: Verify golden tests with new collectors

**Objective**: Confirm refactored path produces identical output
**Files**: (no new files - verification only)

### TDD: Golden Tests Are the Verification

```bash
# All golden tests must pass
uv run pytest tests/test_*baseline*.py -v
# Expected: ALL PASS

# Security baseline must pass
uv run pytest tests/test_security_baseline.py -v
# Expected: PASS

# Full suite
uv run pytest
# Expected: ALL PASS
```

### ⛔ STOP: Clean Table Check

- [ ] Each feature's golden test passes with new collectors
- [ ] No algorithmic changes in extractors (only wrappers changed)
- [ ] Security behavior unchanged

**Status**: 📋 PLANNED

---

## ⛔ STOP: Phase 3 Gate (Final)

**Project completion requires ALL:**

```bash
# 1. All tests pass
uv run pytest
# Expected: ALL PASS

# 2. Collectors implemented
uv run python -c "from doxstrux.markdown.collector_registry import default_collectors; print(f'{len(default_collectors())} collectors')"
# Expected: N collectors (matching mapping table)

# 3. No TODOs in new code
grep -rn "TODO\|FIXME" doxstrux/markdown/collectors_phase8/
# Expected: no results
```

### Phase 3 Completion Checklist

- [ ] `collectors_phase8` package contains Collector for all mapped features
- [ ] `collector_registry` imports from `collectors_phase8` only
- [ ] Mapping table fully resolved (no placeholders)
- [ ] All tests pass
- [ ] No TODOs in wrappers, registry, or mapping

### Create Phase Unlock Artifact

```bash
cat > .phase-3.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": 3,
  "phase_name": "Collector Conformance",
  "collectors_created": $(uv run python -c "from doxstrux.markdown.collector_registry import default_collectors; print(len(default_collectors()))"),
  "golden_tests_pass": true,
  "security_tests_pass": true,
  "clean_table": true,
  "git_commit": "$(git rev-parse HEAD)",
  "completion_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

git add .phase-3.complete.json doxstrux/markdown/collectors_phase8/
git commit -m "Phase 3 complete: all collectors implemented"
git tag phase-3-complete
```

**Phase 3 Status**: 📋 PLANNED

---

# File Changes Summary

| File / Directory | Action | Phase |
|------------------|--------|-------|
| `DOXSTRUX_SPEC.md` | UPDATE | -1 |
| `tests/test_extractors_baseline.py` | CREATE | 0 |
| `tests/test_security_baseline.py` | CREATE | 0 |
| `doxstrux/markdown/interfaces.py` | CREATE | 1 |
| `doxstrux/markdown/collector_registry.py` | CREATE | 1 |
| `doxstrux/markdown/utils/token_warehouse.py` | CREATE | 1 |
| `tests/test_interfaces.py` | CREATE | 1 |
| `tests/test_collector_registry.py` | CREATE | 1 |
| `tests/test_token_warehouse.py` | CREATE | 1 |
| `doxstrux/markdown_parser_core.py` | UPDATE | 2 |
| `doxstrux/markdown/collectors_phase8/` | CREATE | 3 |
| `doxstrux/markdown/collectors_phase8/__init__.py` | CREATE | 3 |
| `doxstrux/markdown/collectors_phase8/*.py` | CREATE | 3 |
| `tests/test_collectors_phase8.py` | CREATE | 3 |

---

# Appendix A: Rollback Procedures

## A.1: Single Test Failure

```bash
# 1. Identify failing test
uv run pytest --tb=short 2>&1 | head -50

# 2. If fixable in <15 min, fix it
# 3. If not, revert last change
git diff HEAD~1 --stat
git checkout HEAD~1 -- [affected_file]

# 4. Verify
uv run pytest
```

## A.2: Golden Test Regression

```bash
# Golden test failure = behavior changed unexpectedly
# 1. Do NOT modify the golden test
# 2. Revert the change that broke it
git log --oneline -5
git revert HEAD

# 3. Re-verify
uv run pytest tests/test_*baseline*.py -v
```

## A.3: Phase Gate Failure

```bash
# DO NOT proceed to next phase
# 1. Identify which criterion failed
# 2. Fix the specific issue
# 3. Re-run phase gate verification
# 4. Only proceed when ALL criteria pass
```

---

# Appendix B: AI Assistant Instructions

## Drift Prevention Rules

1. **Before each response**, re-read the current task's objective
2. **After completing code**, immediately run verification commands
3. **If test fails**, fix it before moving on
4. **If blocked**, document why and suggest rollback
5. **Never skip** Clean Table checks
6. **Never modify** golden tests to make them pass

## Verification Frequency

| Action | Verify Immediately |
|--------|-------------------|
| Create new file | Import check passes |
| Modify function | Related tests pass |
| Complete task | Full test suite |
| Complete phase | Phase gate checklist |

## When to Stop and Escalate

- Golden test fails after code change
- Cannot satisfy Clean Table criteria
- Phase gate blocked for >2 attempts
- Unsure about extractor behavior

## Prohibited Actions

- ❌ Starting Phase N+1 without Phase N artifact
- ❌ Marking task complete with failing tests
- ❌ Modifying golden tests to pass
- ❌ Leaving TODOs in "completed" code
- ❌ Skipping Clean Table verification
- ❌ Changing extractor algorithms (only add wrappers)

---

# Appendix C: Progress Log

## Session Log

```
[YYYY-MM-DD HH:MM] Started Phase -1
[YYYY-MM-DD HH:MM] Task -1.1 complete
[YYYY-MM-DD HH:MM] Task -1.2 complete
[YYYY-MM-DD HH:MM] Phase -1 Gate: ✅ ALL PASS
...
```

## Time Tracking

| Phase | Task | Estimated | Actual | Notes |
|-------|------|-----------|--------|-------|
| -1 | -1.1 | 0.5h | - | - |
| -1 | -1.2 | 0.5h | - | - |
| 0 | 0.1 | 2h | - | - |
| 0 | 0.2 | 1h | - | - |
| 1 | 1.1 | 1h | - | - |
| 1 | 1.2 | 1h | - | - |
| 1 | 1.3 | 2h | - | - |
| 2 | 2.1 | 1h | - | - |
| 2 | 2.2 | 2h | - | - |
| 3 | 3.1 | 1h | - | - |
| 3 | 3.2 | 4h | - | - |
| 3 | 3.3 | 1h | - | - |

**Total Estimated**: 17-24 hours

---

**End of DOXSTRUX AI Task List**
