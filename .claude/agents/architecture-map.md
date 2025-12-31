# Architecture Analysis: your_project

**Analysis Date:** 2025-12-27  
**Source:** FACTS.parquet analysis  
**Status:** Preliminary assessment  

---

## Executive Summary

The `your_project` codebase is organized into **3 architectural clusters** with **13 files** across 4 layers:

- **Root Cluster**: Business logic and data processing (5 files)
- **Utils Cluster**: Utility functions for file locking and sanitization (3 files)
- **New Prompt Builder Cluster**: Prompt generation and building logic (5 files)

**Key Findings:**
- Moderate complexity with one high-complexity function (CC=50)
- Good separation of concerns between clusters
- Heavy concentration of logic in `data_service_turbo.py`
- Documentation is incomplete (11% coverage overall)
- No async/concurrency patterns detected
- Synchronous, blocking I/O operations throughout

---

## 1. Architectural Clusters

### Cluster 1: ROOT CLUSTER (Business Logic)
**Files:** 5  
**Role:** Core business logic and data processing  
**Files:**
```
├── __init__.py                  (0 classes, 0 functions) - 100% documented
├── _global                      (0 classes, 0 functions) - Module scope constants
├── cli_for_this project.py      (0 classes, 0 functions) - CLI entry point [UNDOCUMENTED]
├── data_service_turbo.py        (5 classes, 30 functions) - Heavy lifting [11% documented]
└── insert_docstrings.py         (0 classes, 0 functions) - Utility script [UNDOCUMENTED]
```

**Responsibilities:**
- Data loading and caching (CSV/Parquet via Polars)
- Configuration management
- File system operations with atomic guarantees
- Garbage collection of cache

**Key Components:**
- `TurboPolarsReader` class: Main data access layer
- `_load_csv_cached()`: High-complexity caching logic (CC=50)
- `_gc_parquet_cache()`: Cache cleanup (CC=14)
- `_validate_config()`: Configuration validation (CC=13)

**Dependencies:**
```
Imports: polars, logging, os, errno, time, platform
External calls: Standard library only (OS, time, logging)
```

---

### Cluster 2: UTILS CLUSTER (Utilities)
**Files:** 3  
**Role:** Cross-cutting utility functions  
**Files:**
```
├── __init__.py                  (0 classes, 0 functions) - 100% documented
├── file_lock_util.py            (0 classes, 5 functions) - Locking primitives [UNDOCUMENTED]
└── sanitization.py              (0 classes, 2 functions) - Data cleaning [UNDOCUMENTED]
```

**Responsibilities:**
- Cross-platform file locking (Unix/Windows)
- Column name sanitization for safe access

**Key Functions:**
- `directory_lock()`: Context manager for directory locks (CC=11)
- `file_lock()`: Context manager for file locks (CC=9)
- `_acquire_lock_unix()`: Unix/POSIX locking (CC=7)
- `_acquire_lock_windows()`: Windows locking (CC=7)
- `sanitize_column_name()`: Clean column identifiers

**Dependencies:**
```
Imports: os, time, sys, errno, logging, re, html, unicodedata
External calls: Standard library only
```

**Coupling Profile:**
- **Fan-in:** HIGH (2 callers for each lock function)
- **Fan-out:** HIGH (3 external dependencies per lock function)
- Used by: `data_service_turbo.py` (implicit, inferred from patterns)

---

### Cluster 3: NEW PROMPT BUILDER CLUSTER (Prompt Generation)
**Files:** 5  
**Role:** AI prompt templating and generation  
**Files:**
```
├── __init__.py                               (0 classes, 0 functions) - 100% documented
├── prompt_builder.py                         (2 classes, 12 functions) - Main builder [53% documented]
├── test_target.py                            (3 classes, 17 functions) - Helpers [UNDOCUMENTED]
├── yaml_provider.py                          (0 classes, 0 functions) - Config loader [UNDOCUMENTED]
└── tests/test_additional_prompt_builder.py  (0 classes, 3 functions) - Unit tests
```

**Responsibilities:**
- Prompt templating and variable substitution
- YAML-based configuration management
- Hash-based content validation
- Test data fixtures

**Key Classes:**
- `PromptArtifact`: Represents a renderable prompt template (CC=8)
- `ApiTestClass`: API testing helper
- `CliTestClass`: CLI testing helper

**Key Functions:**
- `render_with_inputs()`: Template rendering with variable substitution
- Configuration loading and validation

**Dependencies:**
```
Imports: hashlib, re, yaml, json, logging
External calls: Standard library + PyYAML
```

**Coupling Profile:**
- **Fan-in:** LOW (internal usage only)
- **Fan-out:** LOW (minimal external dependencies)
- Isolated subsystem with clear boundary

---

## 2. Architectural Layers

```
┌─────────────────────────────────────────────────────┐
│ Layer 5: new_prompt builder (5 modules)             │
│          - Prompt templating and generation         │
│          - Config management (YAML)                 │
│          - Test fixtures                            │
└─────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────┐
│ Layer 4: Root cluster (5 modules)                   │
│          - CLI entry points                         │
│          - Data service (TurboPolarsReader)         │
│          - Configuration validation                 │
└─────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────┐
│ Layer 3: Utils cluster (3 modules)                  │
│          - File locking primitives                  │
│          - Data sanitization                        │
└─────────────────────────────────────────────────────┘
                        ↑
┌─────────────────────────────────────────────────────┐
│ Layer 2: External Dependencies                      │
│          - polars (data processing)                 │
│          - pyyaml (config)                          │
│          - stdlib (os, logging, time, etc.)         │
└─────────────────────────────────────────────────────┘
```

**Layer Dependencies:**
- new_prompt builder: Minimal dependencies (YAML config)
- Root cluster: Depends on utils (locking, sanitization)
- Utils: Only stdlib + external libs (no internal deps)
- External: Third-party libraries (polars, pyyaml)

---

## 3. Dependency Graph

### Inter-Cluster Dependencies
```
┌──────────────────┐
│  new_prompt      │
│  builder         │
│  (isolated)      │
└──────────────────┘

┌──────────────────┐       ┌──────────────────┐
│  Root Cluster    │←──────│  Utils Cluster   │
│  (data service)  │       │  (locking, etc)  │
└──────────────────┘       └──────────────────┘
  │
  └─→ External: polars, pyyaml, stdlib
```

### Module-Level Call Dependencies (Top Callers/Callees)

**Highest Fan-out (most external calls):**
```
utils/file_lock_util.py::directory_lock      → 3 dependencies
utils/file_lock_util.py::file_lock           → 3 dependencies
data_service_turbo.py::_load_csv_cached      → 2 dependencies
```

**Highest Fan-in (most callers):**
```
utils/file_lock_util.py::_acquire_lock_unix  ← 2 callers
utils/file_lock_util.py::_acquire_lock_windows ← 2 callers
utils/file_lock_util.py::_release_lock       ← 2 callers
```

**Observation:** Utilities are reused (high fan-in), but each function is narrowly focused (low fan-out).

---

## 4. Complexity Analysis

### Cyclomatic Complexity Profile

**CRITICAL (CC > 10):**
```
data_service_turbo.py::_load_csv_cached        CC=50  ⚠️  EXTREME
data_service_turbo.py::TurboPolarsReader::get_data CC=23  ⚠️  HIGH
```

**ELEVATED (CC 10-15):**
```
data_service_turbo.py::_gc_parquet_cache       CC=14
data_service_turbo.py::_validate_config        CC=13
utils/file_lock_util.py::directory_lock        CC=11
```

**ACCEPTABLE (CC < 10):**
```
data_service_turbo.py::TurboPolarsReader::__init__  CC=9
data_service_turbo.py::TurboPolarsReader::_get_base_dataframe  CC=8
new_prompt builder/prompt_builder.py::PromptArtifact::render_with_inputs  CC=8
utils/file_lock_util.py::_acquire_lock_unix   CC=7
utils/file_lock_util.py::_acquire_lock_windows CC=7
```

**Risk Assessment:**
- `_load_csv_cached()` at CC=50 is a **refactoring candidate**
- `get_data()` at CC=23 should be **split into smaller functions**
- Multiple lock functions at CC=7-11 suggest **platform-specific branching**

---

## 5. Coupling Patterns

### Fan-in/Fan-out Analysis

**High Reusability (High Fan-in):**
```
file_lock_util.py functions
  - _acquire_lock_unix:    2 callers (high reuse)
  - _acquire_lock_windows: 2 callers (high reuse)
  - _release_lock:         2 callers (high reuse)
```

**High Coupling (High Fan-out):**
```
file_lock_util.py functions
  - directory_lock: 3 outgoing dependencies
  - file_lock:      3 outgoing dependencies
```

**Observation:** Utility functions are correctly designed as low-level primitives with high reuse and minimal external coupling.

### Import Dependencies

**External Libraries Used:**
```
├── polars         (data_service_turbo.py) - DataFrame operations
├── pyyaml         (new_prompt builder/prompt_builder.py) - YAML parsing
├── logging        (data_service_turbo.py, file_lock_util.py, test_target.py)
├── json           (insert_docstrings.py, test_target.py)
├── os/errno/time  (utilities for file ops and timing)
├── re/html        (sanitization.py)
└── hashlib        (prompt_builder.py)
```

**No Internal Cross-Cluster Imports Found:**
- Clusters are loosely coupled
- No detected circular dependencies
- Potential issue: Import graph not fully resolved in FACTS (may be runtime imports)

---

## 6. Documentation & Quality

### Documentation Coverage

**Well Documented (100%):**
```
__init__.py
new_prompt builder/__init__.py
utils/__init__.py
```

**Partially Documented (50%+):**
```
new_prompt builder/prompt_builder.py  (53%)
```

**Undocumented (0%):**
```
cli_for_this project.py         - CLI entry point [CRITICAL]
data_service_turbo.py           - Data service (11%) [CRITICAL]
insert_docstrings.py            - Utility [LOW]
new_prompt builder/test_target.py - Test helpers [LOW]
new_prompt builder/yaml_provider.py - Config loader [LOW]
utils/file_lock_util.py         - Locking primitives [MEDIUM]
utils/sanitization.py           - Data cleaning [LOW]
```

**Quality Issues:**
- CLI entry point completely undocumented
- Data service (core business logic) at 11% coverage
- Public APIs lack docstrings explaining contracts

### Exception Handling

**Exception Density (handlers per function):**
```
data_service_turbo.py       - 9 handlers (file ops, caching, I/O errors)
                            - 5 handlers (retry logic)
                            - 3 handlers (config validation)
new_prompt builder.py       - 3 handlers (parsing, template errors)
                            - 3 handlers
                            - 2 handlers
utils/file_lock_util.py     - 2 handlers (OS errors)
                            - 2 handlers
```

**Observation:** Good exception handling in data_service_turbo.py, moderate in prompt builder, minimal in utils.

---

## 7. Architectural Patterns Detected

### 1. Data Service Pattern (Root Cluster)
```
[Client Code] → [TurboPolarsReader API] → [Cache Manager] → [File System]
```
- Implements caching layer with atomic operations
- Platform-aware file operations
- Multi-format support (CSV, Parquet)

### 2. Utility Abstraction Pattern (Utils Cluster)
```
[Lock Context Manager] → [OS-specific primitives]
```
- Cross-platform abstraction
- Clean resource management (try/finally)
- High reusability, low coupling

### 3. Template Builder Pattern (New Prompt Builder)
```
[Config (YAML)] → [PromptArtifact] → [Rendered Output]
```
- Template-based configuration
- Variable substitution
- Test fixture support

### 4. No Async/Concurrency Pattern
```
Observation: All I/O is blocking/synchronous
Risk: Potential bottleneck under concurrent load
Opportunity: Migration path to async patterns
```

---

## 8. Strengths

✅ **Clear cluster separation** - Three distinct domains with minimal coupling  
✅ **Reusable utilities** - File locking primitives are well-designed  
✅ **Good exception handling** - Comprehensive error recovery in core module  
✅ **Platform awareness** - Unix/Windows compatibility for locking  
✅ **Caching strategy** - Atomic cache operations prevent corruption  

---

## 9. Weaknesses & Risk Areas

⚠️ **CRITICAL:**
- `_load_csv_cached()` at CC=50 is unmaintainable
- CLI entry point undocumented (breaking for onboarding)
- Data service at 11% documentation (hard to understand contracts)

⚠️ **HIGH:**
- `get_data()` at CC=23 should be decomposed
- Synchronous I/O will bottleneck under concurrent load
- No async patterns despite data-heavy operations

⚠️ **MEDIUM:**
- Utility functions (CC=7-11) suggest complex branching
- Platform-specific code not isolated in separate modules
- Test coverage information missing from FACTS

---

## 10. Refactoring Recommendations

### Priority 1: Complexity Reduction
```python
# BEFORE: data_service_turbo.py::_load_csv_cached (CC=50)
def _load_csv_cached(...):
    # 50+ branches of caching logic

# AFTER: Extract into smaller functions
def _load_csv_cached(...):
    metadata = _check_cache_metadata(...)
    if metadata.is_valid:
        return _load_from_cache(...)
    else:
        return _load_fresh_and_cache(...)
```

**Expected Outcome:** Reduce CC=50 → CC=8-10 per function

### Priority 2: Documentation
```python
# Add docstrings to all public APIs
def cli_for_this_project():
    """Main CLI entry point.
    
    Args:
        ...
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
```

### Priority 3: Test Coverage
- Add integration tests for cache invalidation
- Test cross-platform file locking on both Unix/Windows
- Add property-based tests for prompt rendering

### Priority 4: Async Migration
```python
# Consider async data loading for concurrent requests
async def get_data_async(self, ...):
    """Async version for non-blocking I/O."""
    return await asyncio.to_thread(self.get_data, ...)
```

---

## 11. Governance Checkpoints

**Code Quality Standards (from GOVERNANCE_RULES.yaml):**

| Metric | Threshold | Current | Status |
|--------|-----------|---------|--------|
| Cyclomatic Complexity | ≤ 10 | MAX=50 | ❌ FAIL |
| Lines per Function | ≤ 50 | [Pending] | [Check needed] |
| Type Coverage | ≥ 80% | [Pending] | [Check needed] |
| Docstring Coverage | ≥ 80% | 11-100% | ⚠️ MIXED |
| SOLID: SRP | Single responsibility | Violated in TurboPolarsReader | ⚠️ REVIEW |

**Governance Report Status:** Run `uv run fact-file-query-tool governance` for detailed compliance check.

---

## 12. Metrics Summary

```
Total Modules:            13 files
Total Classes:            10 classes
Total Functions:          69 functions
Total LOC:                [Pending line count]
Total Complexity (CC):    [Pending sum]
Max Complexity:           CC=50 (CRITICAL)
Avg Complexity:           [Pending calc]
Documentation:           11-100% (avg ~35%)
Exception Handlers:       29 total
Coupling (fan-in):        Moderate
Coupling (fan-out):       Low-to-Moderate
Async Patterns:           NONE
Global State:             NONE detected
```

---

## 13. Next Steps

1. **Immediate (This Sprint):**
   - [ ] Document CLI entry point
   - [ ] Add docstrings to TurboPolarsReader public methods
   - [ ] Run governance check: `uv run fact-file-query-tool governance`

2. **Short-term (Next Sprint):**
   - [ ] Refactor `_load_csv_cached()` (CC=50 → 20)
   - [ ] Decompose `get_data()` (CC=23 → 15)
   - [ ] Add unit tests for critical paths

3. **Medium-term (This Quarter):**
   - [ ] Increase docstring coverage to 80%
   - [ ] Profile async migration opportunity
   - [ ] Measure test coverage baseline

---

**Analysis Metadata:**
- FACTS File: FACTS-20251227-035532.parquet
- Commit SHA: 378e6af
- Schema Families: 265 fact keys across 13 files
- Query Timestamp: 2025-12-27T06:15:34
- Last Updated: 2025-12-27

