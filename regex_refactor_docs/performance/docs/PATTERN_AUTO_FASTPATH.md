# Auto-Fastpath for Small Documents

**Version**: 1.0
**Date**: 2025-10-17
**Status**: Reference pattern (implement only if profiling shows need)
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_2.md P2-3 + External review C.1
**Purpose**: Adaptive dispatch pattern for warehouse overhead reduction

---

## Problem Statement

**Warehouse overhead**: For small documents (<1KB), warehouse index building may cost more than linear extraction.

### Hypothetical Performance Profile

**Measured overhead** (example - requires real profiling):
- <1KB docs: Warehouse 0.35ms vs. Linear 0.30ms (1.17x slower)
- 1-10KB docs: Warehouse 0.80ms vs. Linear 1.20ms (1.5x faster)
- >10KB docs: Warehouse 2.0ms vs. Linear 5.5ms (2.75x faster)

**Observation**: Warehouse overhead is amortized over document size
- Small docs: Overhead dominates (warehouse slower)
- Large docs: Speedup dominates (warehouse faster)

---

## Pattern: Adaptive Dispatch

### Approach

Use warehouse only if document exceeds size threshold.

```python
class MarkdownParserCore:
    WAREHOUSE_THRESHOLD_BYTES = 2048  # 2KB (tunable via profiling)

    def parse(self):
        content_size = len(self.content)

        if content_size < self.WAREHOUSE_THRESHOLD_BYTES:
            # Fastpath: Linear extraction (no warehouse)
            return self._extract_linear()
        else:
            # Warehouse path: Index-based extraction
            return self._extract_with_warehouse()

    def _extract_linear(self):
        """Linear extraction without warehouse (small documents)."""
        # Direct token traversal, no index building
        sections = self._extract_sections_linear()
        links = self._extract_links_linear()
        images = self._extract_images_linear()
        # ... other extractors

        return {
            "sections": sections,
            "links": links,
            "images": images,
            # ... other fields
        }

    def _extract_with_warehouse(self):
        """Warehouse-based extraction (large documents)."""
        # Build warehouse index
        wh = TokenWarehouse(self.tokens, self.tree)

        # Register collectors
        wh.register_collector(LinksCollector())
        wh.register_collector(ImagesCollector())
        # ... other collectors

        # Dispatch
        wh.dispatch_all()

        # Finalize
        return wh.finalize()
```

### Threshold Selection

**How to determine threshold**:

1. **Profile across document sizes**:
   - 100 bytes, 500 bytes, 1KB, 2KB, 5KB, 10KB, 50KB, 100KB
   - Measure linear vs. warehouse time for each size

2. **Find crossover point**:
   - Threshold = smallest size where warehouse is consistently faster
   - Example: If warehouse faster at 1.5KB+, set threshold to 2KB (with margin)

3. **Validate with production workload**:
   - Measure P50, P95, P99 latency with/without fastpath
   - Ensure fastpath reduces P95 by >10%

**Example profiling script**:
```python
import time
from pathlib import Path

def benchmark_threshold():
    sizes = [100, 500, 1000, 2000, 5000, 10000]
    results = []

    for size in sizes:
        # Generate markdown of target size
        markdown = "# Test\n" * (size // 7)  # Roughly 7 bytes per line

        # Benchmark linear
        start = time.perf_counter()
        for _ in range(100):
            parse_linear(markdown)
        linear_time = time.perf_counter() - start

        # Benchmark warehouse
        start = time.perf_counter()
        for _ in range(100):
            parse_warehouse(markdown)
        warehouse_time = time.perf_counter() - start

        results.append({
            "size": size,
            "linear_ms": linear_time * 10,  # ms per iteration
            "warehouse_ms": warehouse_time * 10,
            "speedup": linear_time / warehouse_time
        })

    # Find crossover point
    for r in results:
        print(f"{r['size']:5d} bytes: linear={r['linear_ms']:.2f}ms, "
              f"warehouse={r['warehouse_ms']:.2f}ms, "
              f"speedup={r['speedup']:.2f}x")
```

---

## When to Implement

### Required Conditions (ALL must be met)

**ONLY if profiling shows**:
1. ✅ Small documents are >50% of workload
2. ✅ Warehouse overhead >20% of parse time for small docs
3. ✅ Fastpath reduces P95 latency by >10%
4. ✅ Tech Lead approves implementation effort (~4 hours)

### Do NOT Implement If:

**YAGNI violations**:
- ❌ Speculatively (without profiling data)
- ❌ Small docs are <10% of workload (not worth optimizing)
- ❌ Warehouse overhead is <5% of parse time (negligible)
- ❌ No measured latency improvement (premature optimization)

**Example YAGNI gate**:
```python
# ❌ BAD: Speculative optimization without data
if len(content) < 2048:  # Arbitrary threshold, no profiling
    return self._extract_linear()

# ✅ GOOD: Data-driven decision
# Decision backed by profiling showing:
# - 60% of docs <2KB
# - P95 latency reduced from 1.2ms to 0.8ms (33% improvement)
# - Warehouse overhead measured at 0.4ms for <2KB docs
if len(content) < WAREHOUSE_THRESHOLD_BYTES:
    return self._extract_linear()
```

---

## Alternative: Configuration-Based Fastpath

### Approach

Allow per-use-case tuning via configuration parameter.

```python
class MarkdownParserCore:
    def __init__(self, content, use_warehouse="auto"):
        """
        Initialize parser.

        Args:
            content: Markdown content string
            use_warehouse: "auto", "always", "never"
                - "auto": Adaptive dispatch based on content size
                - "always": Always use warehouse (large docs expected)
                - "never": Never use warehouse (small docs expected)
        """
        self.content = content
        self.use_warehouse = use_warehouse

    def parse(self):
        if self.use_warehouse == "never":
            return self._extract_linear()
        elif self.use_warehouse == "always":
            return self._extract_with_warehouse()
        else:  # "auto"
            content_size = len(self.content)
            if content_size < self.WAREHOUSE_THRESHOLD_BYTES:
                return self._extract_linear()
            else:
                return self._extract_with_warehouse()
```

**Use cases**:
- **API endpoints**: Small docs (e.g., chat messages) → `use_warehouse="never"`
- **Batch processing**: Large docs (e.g., documentation) → `use_warehouse="always"`
- **Mixed workload**: Unknown doc sizes → `use_warehouse="auto"`

**Benefit**: Allows per-use-case optimization without profiling every workload

---

## Implementation Checklist

### If Implementing Fastpath

**Step 1: Profile current performance** (2 hours)
- [ ] Measure linear extraction baseline (no warehouse)
- [ ] Measure warehouse extraction baseline
- [ ] Identify crossover point (where warehouse becomes faster)
- [ ] Validate with production workload (P50, P95, P99)

**Step 2: Implement adaptive dispatch** (1 hour)
- [ ] Add `WAREHOUSE_THRESHOLD_BYTES` constant
- [ ] Add `_extract_linear()` method
- [ ] Update `parse()` to switch based on content size
- [ ] Ensure behavioral equivalence (output identical)

**Step 3: Test** (1 hour)
- [ ] Add parameterized test for both paths
- [ ] Verify output is byte-for-byte identical
- [ ] Benchmark with/without fastpath
- [ ] Document performance improvement

**Total effort**: ~4 hours

---

## Recommended Approach

### For Skeleton/Production

**Current**: Do NOT implement (YAGNI)

**Rationale**:
- No profiling data showing warehouse overhead
- No production workload analysis
- Violates CODE_QUALITY.json Q2 (used immediately?)

**Future**: Add only if profiling shows measurable benefit

### For Future Work

**If profiling shows need**:
1. Measure crossover point (profiling)
2. Implement adaptive dispatch (4 hours)
3. Validate latency improvement (>10%)
4. Document decision in implementation report

**If profiling shows no need**:
- Document that warehouse overhead is acceptable
- Skip implementation (YAGNI compliance)

---

## Testing Strategy

### Functional Equivalence Test

```python
@pytest.mark.parametrize("content_size", [100, 500, 1000, 2000, 5000, 10000])
def test_fastpath_equivalence(content_size):
    """Verify fastpath and warehouse produce identical output."""
    # Generate markdown of target size
    markdown = "# Test\n" * (content_size // 7)

    # Parse with fastpath (linear)
    parser_linear = MarkdownParserCore(markdown, use_warehouse="never")
    result_linear = parser_linear.parse()

    # Parse with warehouse
    parser_warehouse = MarkdownParserCore(markdown, use_warehouse="always")
    result_warehouse = parser_warehouse.parse()

    # Results must be identical
    assert result_linear == result_warehouse, \
        f"Fastpath mismatch at {content_size} bytes"
```

### Performance Benchmark

```python
def test_fastpath_performance():
    """Benchmark fastpath vs warehouse for small documents."""
    small_doc = "# Small\nHello world\n" * 10  # ~200 bytes

    # Benchmark fastpath
    start = time.perf_counter()
    for _ in range(1000):
        parse(small_doc, use_warehouse="never")
    fastpath_time = time.perf_counter() - start

    # Benchmark warehouse
    start = time.perf_counter()
    for _ in range(1000):
        parse(small_doc, use_warehouse="always")
    warehouse_time = time.perf_counter() - start

    print(f"Fastpath: {fastpath_time*1000:.2f}ms, Warehouse: {warehouse_time*1000:.2f}ms")

    # Fastpath should be faster for small docs
    assert fastpath_time < warehouse_time, "Fastpath slower than warehouse"
```

---

## References

- **External review C.1**: Warehouse overhead analysis
- **PLAN_CLOSING_IMPLEMENTATION_extended_2.md**: P2-3 specification (lines 397-500)
- **CODE_QUALITY.json**: YAGNI decision tree (Q1-Q4)

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-P2-3-DOC | Auto-fastpath pattern documented | This file | ✅ Complete |
| CLAIM-P2-3-PATTERN | Adaptive dispatch pattern provided | Code examples above | ✅ Complete |
| CLAIM-P2-3-YAGNI | YAGNI constraints explicit | When to Implement section | ✅ Complete |
| CLAIM-P2-3-PROFILING | Profiling requirements clear | Threshold Selection section | ✅ Complete |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Recommended Approach**: Do NOT implement (YAGNI - no profiling data)
**Approved By**: Pending Human Review
**Next Review**: If/when profiling shows warehouse overhead >20%
