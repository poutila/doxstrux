# Feature-Flag Lifecycle Management

**Version**: 1.0
**Date**: 2025-10-17
**Status**: Reference pattern (implement only if flag count >3)
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_2.md P2-5 + External review G.1
**Purpose**: Flag consolidation and lifecycle guidance for Phase 8 migration

---

## Problem Statement

**Flag proliferation**: During multi-phase migration, feature flags accumulate:
- `USE_WAREHOUSE` (Phase 8.0)
- `USE_WAREHOUSE_LINKS` (Phase 8.1)
- `USE_WAREHOUSE_IMAGES` (Phase 8.2)
- `USE_WAREHOUSE_HEADINGS` (Phase 8.3)
- ... (potentially 12+ flags for all collectors)

**Result**:
- Configuration complexity (2^12 = 4096 possible combinations)
- Testing matrix explosion (cannot test all combinations)
- Dead code accumulation (legacy paths never removed)
- Debugging difficulty (hard to trace which path is active)

---

## Pattern 1: Hierarchical Flags

### Problem: Independent Flags

```python
# ❌ Bad: 12 independent flags (2^12 = 4096 combinations)
USE_WAREHOUSE_LINKS = os.getenv("USE_WAREHOUSE_LINKS", "0") == "1"
USE_WAREHOUSE_IMAGES = os.getenv("USE_WAREHOUSE_IMAGES", "0") == "1"
USE_WAREHOUSE_HEADINGS = os.getenv("USE_WAREHOUSE_HEADINGS", "0") == "1"
USE_WAREHOUSE_PARAGRAPHS = os.getenv("USE_WAREHOUSE_PARAGRAPHS", "0") == "1"
USE_WAREHOUSE_LISTS = os.getenv("USE_WAREHOUSE_LISTS", "0") == "1"
USE_WAREHOUSE_CODEBLOCKS = os.getenv("USE_WAREHOUSE_CODEBLOCKS", "0") == "1"
USE_WAREHOUSE_TABLES = os.getenv("USE_WAREHOUSE_TABLES", "0") == "1"
USE_WAREHOUSE_BLOCKQUOTES = os.getenv("USE_WAREHOUSE_BLOCKQUOTES", "0") == "1"
USE_WAREHOUSE_FOOTNOTES = os.getenv("USE_WAREHOUSE_FOOTNOTES", "0") == "1"
# ... 3 more
```

**Testing nightmare**:
```python
# Cannot test all 4096 combinations
@pytest.mark.parametrize("links_flag", [False, True])
@pytest.mark.parametrize("images_flag", [False, True])
@pytest.mark.parametrize("headings_flag", [False, True])
# ... 9 more parameters → 4096 test runs
def test_warehouse_combinations(...):
    # Infeasible
```

### Solution: Single Hierarchical Flag

```python
# ✅ Good: Single hierarchical flag (3 modes)
WAREHOUSE_MODE = os.getenv("WAREHOUSE_MODE", "off")  # "off", "partial", "full"

if WAREHOUSE_MODE == "full":
    # All collectors use warehouse
    use_warehouse_for_links = True
    use_warehouse_for_images = True
    use_warehouse_for_headings = True
    # ... all True

elif WAREHOUSE_MODE == "partial":
    # Only specific collectors (for gradual rollout)
    use_warehouse_for_links = True
    use_warehouse_for_images = True
    use_warehouse_for_headings = False  # Legacy path
    use_warehouse_for_paragraphs = False  # Legacy path
    # ... mixed (hardcoded for canary testing)

else:  # "off"
    # All collectors use legacy extraction
    use_warehouse_for_links = False
    use_warehouse_for_images = False
    use_warehouse_for_headings = False
    # ... all False
```

**Testing simplified**:
```python
# 3 modes instead of 4096 combinations
@pytest.mark.parametrize("mode", ["off", "partial", "full"])
def test_warehouse_modes(mode):
    with mock.patch.dict(os.environ, {"WAREHOUSE_MODE": mode}):
        result = parse(markdown)
        assert validate(result)
```

---

## Pattern 2: Flag Lifecycle

### Phase 1: Add Flag for New Feature

**When**: Starting Phase 8.1 (warehouse migration)

```python
# Feature flag: Default OFF (safe rollout)
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

def parse(self):
    if USE_WAREHOUSE:
        return self._extract_with_warehouse()  # New path
    else:
        return self._extract_legacy()  # Existing path
```

**Testing**:
```python
# Ensure both paths work
@pytest.mark.parametrize("use_warehouse", [False, True])
def test_warehouse_flag(use_warehouse):
    with mock.patch.dict(os.environ, {"USE_WAREHOUSE": "1" if use_warehouse else "0"}):
        result = parse(markdown)
        assert validate(result)
```

**Monitoring**:
- Log which path is active
- Measure latency for both paths
- Compare outputs (should be identical)

### Phase 2: Default to ON

**When**: After testing (1 release cycle with flag OFF)

```python
# Feature flag: Default ON (warehouse is now preferred)
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "1") == "1"  # Changed default to "1"

def parse(self):
    if USE_WAREHOUSE:
        return self._extract_with_warehouse()  # Preferred path
    else:
        return self._extract_legacy()  # Fallback path
```

**Testing**:
- Same tests as Phase 1
- Ensure flag can still disable warehouse (emergency rollback)

**Monitoring**:
- Ensure no production issues with default ON
- Track % of users still using legacy path (should be low)

### Phase 3: Remove Flag

**When**: After 1 release cycle with default ON (2 total releases since flag added)

```python
# Flag removed, warehouse is always used
def parse(self):
    return self._extract_with_warehouse()
    # Legacy path deleted
```

**Testing**:
- Remove flag-based tests
- Keep functional tests for warehouse path

**Cleanup**:
- Delete `_extract_legacy()` method
- Remove flag from environment variables documentation
- Update changelog

---

## Flag Consolidation Rules

### When to Consolidate

**Consolidate if ALL conditions met**:
1. ✅ >3 related flags (e.g., per-collector warehouse flags)
2. ✅ Flags always toggled together (not independent)
3. ✅ After migration phase complete (all collectors migrated)

**Example**:
- Phase 8.1: `USE_WAREHOUSE_LINKS = True`, all others `False`
- Phase 8.2: `USE_WAREHOUSE_IMAGES = True`, all others `False`
- ... (10 more phases)
- Phase 8.12: All `True`
- **Consolidation time**: Replace 12 flags with 1 `WAREHOUSE_MODE = "full"`

### When NOT to Consolidate

**Keep independent flags if**:
- ❌ <3 flags (premature consolidation)
- ❌ Flags are truly independent (not related)
- ❌ During migration (need granularity for rollback)

**Example**:
```python
# These are independent, do NOT consolidate
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "1") == "1"
ALLOW_RAW_HTML = os.getenv("ALLOW_RAW_HTML", "0") == "1"
STRICT_MODE = os.getenv("STRICT_MODE", "0") == "1"
```

---

## Testing Strategy with Flags

### Parameterized Tests

```python
@pytest.mark.parametrize("warehouse_mode", ["off", "partial", "full"])
def test_all_warehouse_modes(warehouse_mode):
    """Test all warehouse modes."""
    with mock.patch.dict(os.environ, {"WAREHOUSE_MODE": warehouse_mode}):
        parser = MarkdownParserCore(markdown)
        result = parser.parse()

        # Common assertions for all modes
        assert isinstance(result, dict)
        assert "sections" in result
        assert "links" in result

        # Mode-specific assertions
        if warehouse_mode == "full":
            # Verify warehouse was used
            assert parser._warehouse_used is True
        elif warehouse_mode == "off":
            # Verify legacy path was used
            assert parser._warehouse_used is False
```

### Equivalence Tests

```python
def test_warehouse_equivalence():
    """Verify warehouse and legacy paths produce identical output."""
    markdown = "# Test\n[link](url)\n![image](img.png)"

    # Parse with warehouse
    with mock.patch.dict(os.environ, {"WAREHOUSE_MODE": "full"}):
        result_warehouse = parse(markdown)

    # Parse with legacy
    with mock.patch.dict(os.environ, {"WAREHOUSE_MODE": "off"}):
        result_legacy = parse(markdown)

    # Outputs must be identical
    assert result_warehouse == result_legacy
```

### Integration Tests

```python
def test_warehouse_mode_transitions():
    """Test transitioning between warehouse modes."""
    markdown = "# Test\n- item 1\n- item 2"

    # Start with off
    with mock.patch.dict(os.environ, {"WAREHOUSE_MODE": "off"}):
        result_off = parse(markdown)

    # Transition to partial
    with mock.patch.dict(os.environ, {"WAREHOUSE_MODE": "partial"}):
        result_partial = parse(markdown)

    # Transition to full
    with mock.patch.dict(os.environ, {"WAREHOUSE_MODE": "full"}):
        result_full = parse(markdown)

    # All results should be valid (may differ in implementation details)
    for result in [result_off, result_partial, result_full]:
        assert isinstance(result, dict)
        assert "lists" in result
```

---

## Recommended Timeline for Phase 8

### Timeline

| Release | Flag State | Default | Duration | Rollback |
|---------|-----------|---------|----------|----------|
| v0.8.0 | Add `USE_WAREHOUSE` | OFF | 1 release | Delete flag |
| v0.8.1 | Change default | ON | 1 release | Set to OFF |
| v0.9.0 | Remove flag | N/A | Permanent | Revert commit |

**Total duration**: 2 release cycles (assuming 1 month per release = 2 months)

### Decision Points

**After v0.8.0 (Flag OFF)**:
- ✅ If no issues: Proceed to v0.8.1 (default ON)
- ❌ If issues: Fix issues, stay at v0.8.0

**After v0.8.1 (Flag ON)**:
- ✅ If no issues: Proceed to v0.9.0 (remove flag)
- ❌ If issues: Revert default to OFF, investigate

**After v0.9.0 (Flag removed)**:
- ✅ If no issues: Warehouse is permanent
- ❌ If issues: Revert to v0.8.1 (flag ON, default ON)

---

## Anti-Pattern: Permanent Flags

### Problem

**Permanent flags** that are never removed:

```python
# ❌ Anti-pattern: Flag never removed (permanent complexity)
if os.getenv("USE_LEGACY_EXTRACTION", "0") == "1":
    return self._extract_legacy()  # Dead code after 1 year
else:
    return self._extract_with_warehouse()
```

**Issues**:
- Dead code accumulation (legacy path unused)
- Maintenance burden (tests for both paths)
- Confusion (why does this flag still exist?)

### Solution

**Set sunset date** for flag removal:

```python
# ✅ Good: Flag with sunset date (documented)
# FLAG: USE_WAREHOUSE
# ADDED: 2025-01-15 (v0.8.0)
# DEFAULT_ON: 2025-02-15 (v0.8.1)
# SUNSET: 2025-03-15 (v0.9.0) - flag will be removed
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "1") == "1"
```

**Enforce sunset**:
- Document sunset date in migration plan
- Add reminder in changelog for each release
- Remove flag on sunset date (delete both flag and legacy code)

---

## Configuration Documentation

### Environment Variables Documentation

```markdown
# FILE: docs/ENVIRONMENT_VARIABLES.md

## Feature Flags

### WAREHOUSE_MODE

**Status**: Active (since v0.8.0)
**Default**: `full`
**Sunset**: v0.9.0 (2025-03-15)

**Description**: Controls warehouse-based extraction.

**Values**:
- `off`: Legacy extraction (deprecated)
- `partial`: Canary mode (links + images use warehouse)
- `full`: All collectors use warehouse (recommended)

**Example**:
```bash
export WAREHOUSE_MODE=full
python main.py
```

**Migration timeline**:
- v0.8.0: Default `off` (safe rollout)
- v0.8.1: Default `full` (warehouse preferred)
- v0.9.0: Flag removed (warehouse always ON)
```

---

## Monitoring and Logging

### Flag Usage Logging

```python
import logging

logger = logging.getLogger(__name__)

def parse(self):
    warehouse_mode = os.getenv("WAREHOUSE_MODE", "off")

    # Log flag state (helps debug production issues)
    logger.info(f"Parsing with WAREHOUSE_MODE={warehouse_mode}")

    if warehouse_mode == "full":
        return self._extract_with_warehouse()
    elif warehouse_mode == "partial":
        return self._extract_partial_warehouse()
    else:
        return self._extract_legacy()
```

### Metrics

**Track flag usage in production**:

```python
# Prometheus metrics example
from prometheus_client import Counter

warehouse_mode_counter = Counter(
    "parser_warehouse_mode",
    "Warehouse mode usage",
    ["mode"]
)

def parse(self):
    mode = os.getenv("WAREHOUSE_MODE", "off")
    warehouse_mode_counter.labels(mode=mode).inc()

    # ... parsing logic
```

**Dashboard queries**:
```promql
# % of requests using each mode
rate(parser_warehouse_mode[5m]) / sum(rate(parser_warehouse_mode[5m]))

# Alert if >5% still using legacy mode after v0.8.1
(rate(parser_warehouse_mode{mode="off"}[5m]) / sum(rate(parser_warehouse_mode[5m]))) > 0.05
```

---

## References

- **External review G.1**: Flag proliferation analysis
- **PLAN_CLOSING_IMPLEMENTATION_extended_2.md**: P2-5 specification (lines 704-863)
- **CODE_QUALITY.json**: YAGNI decision tree

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-P2-5-DOC | Feature-flag consolidation pattern documented | This file | ✅ Complete |
| CLAIM-P2-5-LIFECYCLE | Flag lifecycle documented (add → default ON → remove) | Pattern 2 section | ✅ Complete |
| CLAIM-P2-5-CONSOLIDATION | Consolidation pattern documented (hierarchical flags) | Pattern 1 section | ✅ Complete |
| CLAIM-P2-5-TESTING | Testing strategy provided (parameterized tests) | Testing Strategy section | ✅ Complete |
| CLAIM-P2-5-ANTI-PATTERN | Anti-pattern documented (permanent flags) | Anti-Pattern section | ✅ Complete |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Recommended Pattern**: Hierarchical flags + 3-phase lifecycle
**Approved By**: Pending Human Review
**Next Review**: If/when flag count >3 during Phase 8 migration
