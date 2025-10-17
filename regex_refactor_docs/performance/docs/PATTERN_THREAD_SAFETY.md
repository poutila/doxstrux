# Thread-Safety Pattern for Collectors

**Version**: 1.0
**Date**: 2025-10-17
**Status**: Reference pattern (not implemented in skeleton)
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_2.md P1-3 + External review B.3

---

## Current Design: NOT Thread-Safe

### Problem: Collectors Mutate State During Dispatch

```python
class LinksCollector:
    def __init__(self):
        self._links = []  # ❌ Mutable state

    def on_token(self, idx, tok, ctx, wh):
        self._links.append(...)  # ❌ Mutates shared state
```

**Consequence**: If same `LinksCollector` instance used across threads → race conditions

### Example Race Condition

```python
# Thread 1 and Thread 2 share same collector instance
collector = LinksCollector()

# Thread 1
def parse_doc_1():
    parser1 = MarkdownParserCore(doc1, collectors=[collector])
    parser1.parse()  # Appends to collector._links

# Thread 2
def parse_doc_2():
    parser2 = MarkdownParserCore(doc2, collectors=[collector])
    parser2.parse()  # Appends to collector._links (RACE!)

# Result: collector._links contains mixed data from both documents
```

---

## Pattern 1: Copy-on-Parse (Simplest) ✅ RECOMMENDED

### Approach: Create New Parser/Collector Instances Per Thread

```python
# Thread-safe: Each thread gets fresh instances
def parse_in_thread(markdown_content):
    parser = MarkdownParserCore(markdown_content)
    result = parser.parse()  # Fresh collectors created per parse
    return result

# Example: Thread pool for parallel parsing
from concurrent.futures import ThreadPoolExecutor

documents = [doc1, doc2, doc3, ...]

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(parse_in_thread, documents))
```

### Pros

- ✅ **No code changes needed**: Existing code is already thread-safe with this pattern
- ✅ **Simple**: Easy to understand and implement
- ✅ **Safe**: No shared mutable state between threads
- ✅ **Python GIL compatible**: Works well with Python's threading model

### Cons

- ⚠️ **Higher memory overhead**: More instances created (one per parse)
- ⚠️ **Parser initialization cost**: Small overhead per thread

### When to Use

- **Always** for skeleton/production (default pattern)
- Multi-threaded web servers (Flask, FastAPI, Django)
- Async frameworks (asyncio, aiohttp)
- Thread pools for batch processing

---

## Pattern 2: Immutable Collectors (Complex) ⚠️ NOT RECOMMENDED

### Approach: Collectors Return Data Instead of Mutating State

```python
class ImmutableLinksCollector:
    """Immutable collector that returns data instead of storing."""

    def on_token(self, idx, tok, ctx, wh):
        """
        Return new link dict instead of appending to internal state.

        Returns:
            Dict if token is a link, None otherwise
        """
        if tok.type == "link_open":
            return {
                "token_index": idx,
                "href": tok.attrGet("href"),
                "text": tok.content,
            }
        return None

    def finalize(self, wh, collected_items):
        """
        Aggregate items collected by warehouse (not self).

        Args:
            wh: TokenWarehouse instance
            collected_items: Items returned by on_token() calls

        Returns:
            Final result dict
        """
        return {
            "name": "links",
            "count": len(collected_items),
            "links": collected_items,
        }
```

### Changes Required

1. **TokenWarehouse**: Must collect items returned by `on_token()`
2. **Collector API**: `finalize()` signature changes to accept collected items
3. **All Collectors**: Must be refactored to return data instead of appending

### Pros

- ✅ **Truly thread-safe**: No shared mutable state
- ✅ **Functional programming style**: Easier to reason about

### Cons

- ❌ **Significant refactor**: All collectors must be rewritten
- ❌ **API breaking change**: Different interface for finalize()
- ❌ **Warehouse complexity**: Must track items per collector
- ❌ **Not needed in Python**: GIL makes multi-threaded parsing uncommon

### When to Use

- **Only if**:
  1. Profiling shows parser instance creation is bottleneck (>10% of parse time)
  2. True multi-threaded parsing required (rare in Python)
  3. Tech Lead approves refactor effort

---

## Recommended Approach for Production

### Use Pattern 1 (Copy-on-Parse)

**Rationale**:
1. **Python GIL**: Multi-threaded parsing uncommon (GIL limits parallelism)
2. **Multiprocessing preferred**: For parallel parsing, use `multiprocessing` (no shared state)
3. **Zero code changes**: Pattern 1 requires no modifications
4. **Simpler**: KISS principle - avoid complexity unless proven necessary

### Example: Parallel Parsing with Multiprocessing

```python
from multiprocessing import Pool

def parse_document(markdown_content):
    """Parse single document (runs in separate process)."""
    parser = MarkdownParserCore(markdown_content)
    return parser.parse()

# Parallel parsing across CPU cores
documents = [doc1, doc2, doc3, ...]

with Pool(processes=4) as pool:
    results = pool.map(parse_document, documents)
```

**Benefits**:
- ✅ True parallelism (no GIL limitation)
- ✅ No shared state (processes are isolated)
- ✅ No thread-safety concerns

---

## Pattern 3: Thread-Local Storage (Alternative)

### Approach: Store Collector State in Thread-Local Variables

```python
import threading

class ThreadSafeLinksCollector:
    def __init__(self):
        self._thread_local = threading.local()

    @property
    def _links(self):
        """Get thread-local links list."""
        if not hasattr(self._thread_local, 'links'):
            self._thread_local.links = []
        return self._thread_local.links

    def on_token(self, idx, tok, ctx, wh):
        self._links.append(...)  # Thread-safe via thread-local storage

    def finalize(self, wh):
        return {"links": self._links}
```

### Pros

- ✅ **Minimal code changes**: Only modify `__init__` and add property
- ✅ **Thread-safe**: Each thread has isolated state

### Cons

- ⚠️ **Thread-local complexity**: Harder to debug/understand
- ⚠️ **Still requires instance per thread**: Doesn't solve memory overhead
- ⚠️ **Python GIL limitation**: Doesn't improve parallelism

### When to Use

- **Rare**: Only if sharing collector instances across threads is required
- **Not recommended** for skeleton/production (Pattern 1 is simpler)

---

## Documentation Status

### Current Parser Status

**Parser is NOT thread-safe** if:
- Same `MarkdownParserCore` instance used across multiple threads
- Same collector instances shared between parsers in different threads

**Recommended usage**:
- Use separate parser instances per thread (Pattern 1)
- Use multiprocessing for parallel parsing (better than threading)

### When to Implement Pattern 2 (Immutable Collectors)

**Only if**:
1. ✅ Profiling shows parser instance creation is bottleneck (>10% of parse time)
2. ✅ True multi-threaded parsing required (rare in Python)
3. ✅ Measurements show 2x+ speedup from reuse
4. ✅ Tech Lead approves refactor effort (~20 hours)

**Estimated effort for Pattern 2**:
- Design: 4 hours
- Refactor all collectors: 12 hours
- Update TokenWarehouse: 2 hours
- Testing: 2 hours
- **Total**: ~20 hours

---

## Testing Thread-Safety

### Test 1: Pattern 1 (Copy-on-Parse)

```python
import threading

def test_thread_safety_with_separate_instances():
    """Verify separate parser instances are thread-safe."""
    results = []

    def parse_in_thread(markdown):
        parser = MarkdownParserCore(markdown)  # Fresh instance per thread
        result = parser.parse()
        results.append(result)

    threads = [
        threading.Thread(target=parse_in_thread, args=(f"# Doc {i}",))
        for i in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Verify all results are independent (no data mixing)
    assert len(results) == 10
    assert len(set(r['sections'][0]['title'] for r in results)) == 10  # All unique
```

### Test 2: Pattern 2 (Immutable Collectors)

```python
def test_immutable_collector_is_thread_safe():
    """Verify immutable collector can be shared across threads."""
    collector = ImmutableLinksCollector()  # Single shared instance
    results = []

    def parse_with_shared_collector(markdown):
        parser = MarkdownParserCore(markdown, collectors=[collector])
        result = parser.parse()
        results.append(result)

    threads = [
        threading.Thread(target=parse_with_shared_collector, args=(f"[Link {i}](url{i})",))
        for i in range(10)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Verify results are independent (no data mixing)
    assert len(results) == 10
    # Each result should have exactly 1 link
    assert all(r['links']['count'] == 1 for r in results)
```

---

## References

- **External Review B.3**: Thread-safety gap analysis
- **PLAN_CLOSING_IMPLEMENTATION_extended_2.md**: P1-3 specification
- **Python GIL**: [Global Interpreter Lock](https://wiki.python.org/moin/GlobalInterpreterLock)
- **threading module**: [Python threading documentation](https://docs.python.org/3/library/threading.html)
- **multiprocessing module**: [Python multiprocessing documentation](https://docs.python.org/3/library/multiprocessing.html)

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-P1-3-DOC | Thread-safety pattern documented | This file | ✅ Complete |
| CLAIM-P1-3-PATTERN1 | Copy-on-parse documented | Pattern 1 section | ✅ Complete |
| CLAIM-P1-3-PATTERN2 | Immutable collector documented | Pattern 2 section | ✅ Complete |
| CLAIM-P1-3-RECOMMENDATION | Recommendation clear | Recommended Approach section | ✅ Complete |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Recommended Pattern**: Pattern 1 (Copy-on-Parse)
**Approved By**: Pending Human Review
**Next Review**: If multi-threaded parsing requirements emerge
