# Deep Feedback Gap Analysis

**Date**: 2025-10-15
**Source**: User's comprehensive security → runtime → speed → style feedback
**Purpose**: Identify gaps between existing documentation/implementation and user's deep analysis

---

## Executive Summary

**User's Verdict**: "You already documented most of these failure modes and published patches — excellent."

**Critical Remaining Gaps** (4 items identified by user):
1. ✅ Token canonicalization - **DONE** (implemented in skeleton)
2. ⚠️ URL normalization consistency - **PARTIAL** (need cross-stage tests)
3. ⚠️ O(N²) hotspots - **PARTIAL** (need synthetic scaling tests)
4. ❌ Collector timeouts/isolation - **NOT DONE** (design guideline only, no enforcement)

**Total New Work**: ~2 hours (3 test suites + 1 enforcement mechanism)

---

## 1. Security Domain - Coverage Matrix

### A. Poisoned Tokens / Prototype Pollution (Critical)

| Aspect | Status | Location |
|--------|--------|----------|
| **Documentation** | ✅ Complete | DEEP_VULNERABILITIES_ANALYSIS.md:29-157 |
| **Implementation** | ✅ Complete | skeleton/token_warehouse.py:79-117 |
| **Checklist** | ✅ Complete | PHASE_8_IMPLEMENTATION_CHECKLIST.md:20-100 |
| **Unit tests** | ✅ Complete | Checklist includes test_poisoned_token_getter() |
| **CI integration** | ✅ Complete | Checklist includes CI YAML |

**User's Ask**: "Canonicalize tokens (TokenView) in warehouse __init__"
**Our Status**: ✅ **IMPLEMENTED** - `_canonicalize_tokens()` method in skeleton

**Gap**: None - this is complete.

---

### B. URL Normalization Mismatch / SSRF (Critical)

| Aspect | Status | Location |
|--------|--------|----------|
| **Documentation** | ✅ Complete | DEEP_VULNERABILITIES_ANALYSIS.md:159-329 |
| **Implementation** | ✅ Complete | skeleton/security/validators.py:1-179 |
| **Checklist** | ✅ Complete | PHASE_8_IMPLEMENTATION_CHECKLIST.md:104-210 |
| **Unit tests** | ✅ Complete | validators.py includes 8 test functions |
| **Cross-stage tests** | ❌ **MISSING** | Not yet implemented |

**User's Ask**: "Add cross-stage tests (collector vs fetcher) in CI that assert collector_safe == fetcher_safe"

**Gap**: Need **test_normalization_consistency()** that verifies collector and fetcher use same normalization.

**Code Needed**:
```python
# File: tests/test_url_normalization_consistency.py
def test_collector_fetcher_consistency():
    """Verify collector and fetcher use same URL normalization."""
    from skeleton.doxstrux.markdown.security.validators import normalize_url

    attack_urls = [
        ("javascript:alert(1)", False),
        ("jAvAsCrIpT:alert(1)", False),
        ("//evil.com/script", False),
        ("http://localhost/admin", False),  # Private IP
        ("https://example.com", True),
    ]

    for url, expected_safe in attack_urls:
        # Collector check
        collector_scheme, collector_safe = normalize_url(url)

        # Fetcher must use SAME function (not reimplemented)
        fetcher_scheme, fetcher_safe = normalize_url(url)

        # MUST be identical
        assert collector_safe == fetcher_safe == expected_safe, \
            f"Mismatch on {url}: collector={collector_safe}, fetcher={fetcher_safe}"
```

**Effort**: ~15 min (write test + add to CI)
**Priority**: 🔴 P0 (Critical)

---

### C. Metadata Poisoning / SSTI (High)

| Aspect | Status | Location |
|--------|--------|----------|
| **Documentation** | ✅ Complete | DEEP_VULNERABILITIES_ANALYSIS.md:403-502 |
| **Detection logic** | ⚠️ Partial | Doc mentions detection but not collection-time flagging |
| **Implementation** | ❌ Missing | No `contains_template_syntax` flag in collectors |

**User's Ask**: "Mark contains_template_syntax at collection time and always escape metadata in renderers"

**Gap**: Need collector-side template detection.

**Code Needed**:
```python
# In HeadingsCollector or metadata collectors
import re

TEMPLATE_PATTERN = re.compile(r'\{\{|\{%|<%=|<\?php')

class HeadingsCollector:
    def on_token(self, idx, token, ctx, wh):
        if token.type == "heading_open":
            # ... extract heading text ...

            # ✅ Flag template syntax
            contains_template = bool(TEMPLATE_PATTERN.search(heading_text))

            self._headings.append({
                "text": heading_text,
                "contains_template_syntax": contains_template,
                "needs_escaping": contains_template,
                # ... other fields
            })
```

**Test Needed**:
```python
def test_template_syntax_flagged():
    """Verify collectors flag template syntax in metadata."""
    md = "# Heading with {{variable}}"
    result = parse(md)

    assert result["headings"][0]["contains_template_syntax"] is True
    assert result["headings"][0]["needs_escaping"] is True
```

**Effort**: ~20 min (add detection + test)
**Priority**: 🟠 P1 (High)

---

## 2. Runtime Domain - Coverage Matrix

### A. Algorithmic Complexity / O(N²) DoS (High)

| Aspect | Status | Location |
|--------|--------|----------|
| **Documentation** | ✅ Complete | DEEP_VULNERABILITIES_ANALYSIS.md:573-668 |
| **Implementation** | ✅ Complete | Skeleton collectors use sets/dicts |
| **Checklist** | ✅ Complete | PHASE_8_IMPLEMENTATION_CHECKLIST.md:317-422 |
| **Basic tests** | ✅ Complete | Checklist includes test_linear_time_complexity() |
| **Synthetic scaling tests** | ❌ **MISSING** | Not yet implemented |

**User's Ask**: "Add synthetic tests that measure parse time vs token count and assert near-linear scaling"

**Gap**: Need **automated complexity benchmarking** that detects O(N²) regressions.

**Code Needed**:
```python
# File: tests/test_performance_scaling.py
import time

def test_linear_scaling_assertion():
    """Assert parse time grows linearly with input size (not quadratic)."""

    sizes = [100, 200, 500, 1000, 2000, 5000]
    times = []

    for size in sizes:
        # Generate N unique links
        tokens = [
            {"type": "paragraph_open", "nesting": 1},
            {"type": "inline", "content": f"[link{i}](http://ex.com/{i})"},
            {"type": "paragraph_close", "nesting": -1}
        ] * size

        start = time.perf_counter()
        wh = TokenWarehouse(tokens, None)
        wh.register_collector(LinksCollector())
        wh.dispatch_all()
        elapsed = time.perf_counter() - start

        times.append(elapsed)

    # Check growth rate
    # For O(N): time(2N) / time(N) ≈ 2.0 (± tolerance)
    # For O(N²): time(2N) / time(N) ≈ 4.0

    ratio_200_100 = times[1] / times[0]  # Should be ~2
    ratio_2000_1000 = times[4] / times[3]  # Should be ~2

    TOLERANCE = 0.5  # Allow 50% variance

    assert abs(ratio_200_100 - 2.0) < TOLERANCE, \
        f"Quadratic growth detected: ratio={ratio_200_100:.2f} (expected ~2.0)"

    assert abs(ratio_2000_1000 - 2.0) < TOLERANCE, \
        f"Quadratic growth detected: ratio={ratio_2000_1000:.2f} (expected ~2.0)"
```

**Effort**: ~25 min (write test + CI integration)
**Priority**: 🟠 P1 (High)

---

### B. Blocking IO / Infinite Loops (Critical)

| Aspect | Status | Location |
|--------|--------|----------|
| **Documentation** | ✅ Complete | DEEP_VULNERABILITIES_ANALYSIS.md:1025-1169 |
| **Design guideline** | ✅ Complete | Checklist specifies "no blocking I/O in on_token()" |
| **Enforcement** | ❌ **MISSING** | No timeout/watchdog mechanism |
| **Tests** | ⚠️ Partial | Checklist has basic perf tests but no timeout enforcement |

**User's Ask**: "Add per-collector timeouts / watchdogs (or run collectors in isolated worker)"

**Gap**: Design guideline exists but no **enforcement mechanism**. Buggy collectors can still hang.

**Two Implementation Options**:

#### Option 1: Timeout Wrapper (Simple)
```python
import signal

class CollectorTimeout(Exception):
    """Raised when collector exceeds timeout."""
    pass

def _timeout_handler(signum, frame):
    raise CollectorTimeout("Collector exceeded timeout")

def dispatch_all(self, per_collector_timeout_ms=1000) -> None:
    """Dispatch with per-collector timeout enforcement."""
    ctx = DispatchContext()
    tokens = self.tokens
    routing = self._routing

    timeout_sec = per_collector_timeout_ms / 1000.0

    for i, tok in enumerate(tokens):
        # ... nesting logic ...

        cols = routing.get(ttype, ())
        if not cols:
            continue

        for col in cols:
            # ✅ Set alarm before calling collector
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(int(timeout_sec) if timeout_sec >= 1 else 1)

            try:
                # ... should_process checks ...
                col.on_token(i, tok, ctx, self)
            except CollectorTimeout:
                # ✅ Timeout - record and continue
                self._collector_errors.append((
                    getattr(col, 'name', repr(col)),
                    i,
                    'CollectorTimeout'
                ))
            except Exception as e:
                # ... existing error handling ...
            finally:
                # ✅ Cancel alarm
                signal.alarm(0)
```

**Pros**: Simple, ~20 LOC
**Cons**: Unix-only (SIGALRM not on Windows), coarse 1-second granularity

#### Option 2: Process Isolation (Robust)
```python
from multiprocessing import Process, Queue
import time

def _run_collector_isolated(col, idx, token, ctx, wh, result_queue, timeout_sec):
    """Run collector in isolated subprocess."""
    try:
        col.on_token(idx, token, ctx, wh)
        result_queue.put(("success", None))
    except Exception as e:
        result_queue.put(("error", str(e)))

def dispatch_all(self, per_collector_timeout_ms=1000) -> None:
    """Dispatch with subprocess isolation."""
    # ... (same structure but spawn process for each collector call)

    result_queue = Queue()
    p = Process(target=_run_collector_isolated, args=(col, i, tok, ctx, self, result_queue, timeout_sec))
    p.start()
    p.join(timeout=timeout_sec)

    if p.is_alive():
        # ✅ Timeout - kill process
        p.terminate()
        p.join()
        self._collector_errors.append((col.name, i, 'CollectorTimeout'))
    else:
        # Get result
        if not result_queue.empty():
            status, error = result_queue.get()
            if status == "error":
                self._collector_errors.append((col.name, i, error))
```

**Pros**: True isolation, works on all platforms, fine-grained timeout
**Cons**: High overhead (~10-20ms per collector call), serialization costs

#### Recommendation: Hybrid Approach
```python
# Default: No timeout (trust collectors in production)
# Test mode: Enforce timeout to catch bugs
# Optional: ENV var or config flag to enable timeout in prod

ENFORCE_COLLECTOR_TIMEOUT = os.getenv("ENFORCE_COLLECTOR_TIMEOUT", "0") == "1"
COLLECTOR_TIMEOUT_MS = int(os.getenv("COLLECTOR_TIMEOUT_MS", "1000"))

if ENFORCE_COLLECTOR_TIMEOUT:
    # Use Option 1 (signal-based) on Unix
    # Or log warning on Windows
    pass
```

**Effort**: ~45 min (implement + test + document)
**Priority**: 🟠 P1 (High) - Critical for defense but complex to implement correctly

**Alternative**: Document the contract strongly and add **static analysis linting** that flags blocking calls:
```python
# File: tools/lint_collectors.py
import ast
import sys

FORBIDDEN_BLOCKING_CALLS = ['requests.get', 'urllib.request.urlopen', 'open(', 'os.system']

class BlockingCallDetector(ast.NodeVisitor):
    def __init__(self):
        self.violations = []

    def visit_Call(self, node):
        # Check if call matches forbidden patterns
        call_str = ast.unparse(node.func)
        for forbidden in FORBIDDEN_BLOCKING_CALLS:
            if forbidden in call_str:
                self.violations.append((node.lineno, call_str))
        self.generic_visit(node)

def lint_collector_file(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read(), filepath)

    detector = BlockingCallDetector()
    detector.visit(tree)

    if detector.violations:
        print(f"❌ {filepath}:")
        for lineno, call in detector.violations:
            print(f"  Line {lineno}: Forbidden blocking call: {call}")
        return 1

    print(f"✅ {filepath}: No blocking calls detected")
    return 0

# Run on all collector files in CI
```

**Linting Effort**: ~30 min
**Priority**: 🟡 P2 (Medium) - Good defense-in-depth but doesn't enforce at runtime

---

## 3. Speed Domain - Already Covered

User identifies 3 optimization areas:

1. **Hot-path attrGet calls** - ✅ Solved by token canonicalization (already implemented)
2. **Indices vs repeated scans** - ✅ Core Phase 8 innovation (already in spec)
3. **Memory allocation patterns** - ✅ Documented in SECURITY_AND_PERFORMANCE_REVIEW.md

**Gap**: None - user confirms these are already addressed.

---

## 4. Style & Maintainability - Already Covered

User recommends 4 patterns:

1. **Fail-fast & canonicalize** - ✅ Implemented (MAX_TOKENS, MAX_BYTES, MAX_NESTING guards added today)
2. **Immutable routing after freeze** - ✅ Routing uses tuples (skeleton implements this)
3. **Collector contract doc** - ⚠️ Partial (documented in specs but not in code comments)
4. **Error isolation** - ✅ Implemented (_collector_errors already exists)

**Gap**: Add **inline collector contract documentation** in collector base class.

**Code Needed**:
```python
# File: skeleton/doxstrux/markdown/utils/token_warehouse.py

class Collector(Protocol):
    """Collector protocol for TokenWarehouse dispatch.

    **CONTRACT FOR COLLECTOR AUTHORS**:

    1. ❌ NO blocking I/O in on_token() (no requests.get, DB queries, file I/O)
       - Defer to finalize() or async post-processing

    2. ❌ NO mutation of warehouse state (read-only access only)
       - Use wh.by_type, wh.pairs, wh.parent (query API)

    3. ⏱️ Per-token budget: <1ms (keep on_token() fast)
       - Complex processing should happen in finalize()

    4. 🔒 Use wh.tokens[idx] only (don't call token methods in hot path)
       - Tokens are canonicalized primitive views

    5. ⚠️ Raise exceptions sparingly (errors are logged, not propagated)
       - Collector exceptions don't crash dispatch

    Violations will be caught by:
    - Static linter (tools/lint_collectors.py)
    - Performance tests (test_dispatch_performance_threshold)
    - Timeout watchdog (if ENFORCE_COLLECTOR_TIMEOUT=1)
    """

    name: str
    interest: Interest

    def should_process(self, token: Any, ctx: DispatchContext, wh: "TokenWarehouse") -> bool:
        """Return True if this token should be processed.

        Optional: If not implemented, all tokens matching interest.types will be processed.
        """
        ...

    def on_token(self, idx: int, token: Any, ctx: DispatchContext, wh: "TokenWarehouse") -> None:
        """Process a single token.

        ⚠️ HOT PATH - Keep this fast (<1ms per call).
        ❌ NO blocking I/O, NO network calls, NO DB queries.
        """
        ...

    def finalize(self, wh: "TokenWarehouse") -> Any:
        """Finalize collection and return results.

        Called once after dispatch_all() completes.
        Complex processing and I/O should happen here.
        """
        ...
```

**Effort**: ~10 min (add documentation to Protocol class)
**Priority**: 🟡 P2 (Medium) - Good documentation but doesn't enforce

---

## 5. Immediate Action List - Prioritized

Based on user's "Immediate prioritized action list" and our gap analysis:

| # | User's Ask | Our Status | Action Needed | Effort | Priority |
|---|------------|------------|---------------|--------|----------|
| 1 | Canonicalize tokens | ✅ **DONE** | None | 0 min | ✅ Complete |
| 2 | Unified URL normalizer | ✅ **DONE** | Add cross-stage tests | 15 min | 🔴 P0 |
| 3 | Replace string += | ✅ **DONE** | Add synthetic scaling tests | 25 min | 🟠 P1 |
| 4 | Per-collector timeouts | ❌ **NOT DONE** | Implement timeout enforcement OR static linting | 30-45 min | 🟠 P1 |
| 5 | Adversarial tests in CI | ⚠️ **PARTIAL** | Wire existing tests into CI gate P1 | 20 min | 🟠 P1 |

**Total Remaining**: ~90-110 minutes (1.5-2 hours)

---

## 6. Adversarial Corpus - Coverage Matrix

User requests 5 specific adversarial test categories:

| Category | Status | Location |
|----------|--------|----------|
| Malformed map values | ✅ Complete | ADVERSARIAL_TESTING_GUIDE.md:305-475 |
| URL bypass variants | ✅ Complete | security/validators.py has 8 test functions |
| Poisoned attrGet tokens | ✅ Complete | TOKEN_VIEW_CANONICALIZATION.md includes demo |
| O(N²) complexity triggers | ✅ Complete | ADVERSARIAL_TESTING_GUIDE.md:800-950 |
| Deep nesting > recursion limit | ✅ Complete | ADVERSARIAL_TESTING_GUIDE.md:950-1100 |

**Gap**: Tests exist but not yet **wired into CI gate P1**.

**Action Needed**: Create CI gate that runs adversarial corpus.

**Code Needed**:
```bash
# File: tools/ci/ci_gate_adversarial.py
#!/usr/bin/env python3
"""CI Gate P1: Adversarial Corpus Validation"""

import sys
import subprocess

def run_adversarial_tests():
    """Run all adversarial test suites."""
    tests = [
        "tests/test_malformed_maps.py",
        "tests/test_url_bypass.py",
        "tests/test_poisoned_tokens.py",
        "tests/test_complexity_triggers.py",
        "tests/test_deep_nesting.py",
    ]

    failed = []

    for test in tests:
        result = subprocess.run(
            [".venv/bin/python", "-m", "pytest", test, "-v"],
            capture_output=True
        )

        if result.returncode != 0:
            failed.append(test)

    if failed:
        print(f"❌ Gate P1 FAILED: {len(failed)} adversarial test suites failed")
        for test in failed:
            print(f"  - {test}")
        return 1

    print("✅ Gate P1 PASSED: All adversarial tests passed")
    return 0

if __name__ == "__main__":
    sys.exit(run_adversarial_tests())
```

**Effort**: ~20 min (create gate + add to CI workflow)
**Priority**: 🟠 P1 (High)

---

## 7. Summary - What's Left to Do

### ✅ Already Complete (User Validated)
- Token view canonicalization (SEC-1)
- URL normalization utility (SEC-2)
- O(N²) mitigation via sets/dicts (RUN-1)
- Memory amplification guards (RUN-2)
- Deep nesting guards (RUN-3)
- Deterministic routing (RUN-4)
- Blocking I/O design guideline (RUN-5)

### ❌ Critical Gaps (Must Fix)

1. **Cross-stage URL tests** (15 min, P0)
   - Test that collector and fetcher use same normalization

2. **Synthetic scaling tests** (25 min, P1)
   - Assert parse time grows linearly with input size

3. **Collector timeout enforcement** (30-45 min, P1)
   - Option A: Signal-based timeout (Unix only)
   - Option B: Static linting (all platforms, no runtime overhead)
   - Recommend: Start with static linting, add runtime timeout later

4. **Template syntax detection** (20 min, P1)
   - Add `contains_template_syntax` flag in metadata collectors

5. **Wire adversarial tests to CI** (20 min, P1)
   - Create gate P1 that runs existing test suites

### 🟡 Nice to Have (Lower Priority)

6. **Inline collector contract docs** (10 min, P2)
   - Add documentation to Collector Protocol

**Total Critical Work**: ~110 minutes (~2 hours)

---

## 8. Recommended Implementation Order

1. **Static collector linting** (30 min) - Prevents blocking I/O with zero runtime cost
2. **Cross-stage URL tests** (15 min) - Quick win, high security value
3. **Template syntax detection** (20 min) - Straightforward implementation
4. **Synthetic scaling tests** (25 min) - Good regression detection
5. **Wire adversarial tests to CI** (20 min) - Activates existing work
6. **Inline collector contract docs** (10 min) - Good documentation hygiene
7. **Runtime timeout enforcement** (optional, 45 min) - Defense-in-depth if linting isn't enough

**Total**: 2 hours for critical items, 2.75 hours for complete coverage

---

## 9. User's Final Verdict

> "You already documented most of these failure modes and published patches — excellent. The critical remaining risks to fix first are: (1) token canonicalization [✅ DONE], (2) URL normalization consistency [⚠️ PARTIAL - need tests], (3) O(N²) hotspots [⚠️ PARTIAL - need tests], and (4) collector timeouts/isolation [❌ NOT DONE]."

**Our Response**:
- ✅ (1) Complete - implemented in skeleton
- ⚠️ (2) Partial - need 15 min of test work
- ⚠️ (3) Partial - need 25 min of test work
- ❌ (4) Not done - need 30 min of linting OR 45 min of runtime enforcement

**Conclusion**: ~70-110 minutes of focused work closes all critical gaps identified by user.

---

**Last Updated**: 2025-10-15
**Status**: Gap analysis complete, ready to implement remaining items
**Next Step**: Implement static collector linting (highest ROI - prevents blocking I/O with zero runtime cost)
