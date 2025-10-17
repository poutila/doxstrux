# Extended Closing Implementation Plan - Phase 8 Security Hardening
# Part 4 of 4: Security Audit Response & Green-Light Blockers

**Version**: 1.0
**Date**: 2025-10-17
**Status**: SECURITY AUDIT RESPONSE - BLOCKING ITEMS FOR GREEN-LIGHT
**Methodology**: Golden Chain-of-Thought + CODE_QUALITY Policy + External Security Audit
**Part**: 4 of 4
**Purpose**: Address security audit findings and implement blocking items for production green-light

⚠️ **CRITICAL**: This part documents **BLOCKING SECURITY ITEMS** identified by external security audit that must be resolved before accepting untrusted inputs in production.

**Previous**:
- Part 1: PLAN_CLOSING_IMPLEMENTATION_extended_1.md (P0 Critical)
- Part 2: PLAN_CLOSING_IMPLEMENTATION_extended_2.md (P1/P2 Patterns)
- Part 3: PLAN_CLOSING_IMPLEMENTATION_extended_3.md (Testing/Production)

**Source**: External security audit feedback (deep analysis of skeleton, tests, and documentation)

---

## Part 4 Scope

This file documents security audit findings and implementation plan for:
- **PART 11**: Security Audit Findings (A1-A3: SSTI, Token Canonicalization, URL/SSRF)
- **PART 12**: Runtime Blockers (B1-B2: Cross-platform timeouts, Reentrancy)
- **PART 13**: Performance/Correctness Blockers (C1-C3: Collector caps, Binary search, Auto-fastpath)
- **PART 14**: CI/Observability Blockers (D1-D2: Adversarial CI gates, Metrics/Alerting)
- **PART 15**: Implementation Checklist (Prioritized action items with exact commands)
- **PART 16**: Ready-to-Apply Artifacts (Fetcher, CI YAML, Consumer SSTI test)

**Audit verdict**: "Yes — conditionally. The architecture is sound. Fix the top 4 blockers, re-run adversarial + baseline suites, and you're ready for canary."

---

# PART 11: SECURITY AUDIT FINDINGS (A1-A3)

## A1: SSTI Risk - Detectors Exist But Consumer Enforcement Missing

### Problem Statement

**Why it matters**: Collectors correctly flag template-like tokens, but flagging ≠ safety. A downstream consumer that renders metadata without escaping will execute templates.

**Evidence**:
- PLAN_CLOSING_IMPLEMENTATION_extended_3.md lists SSTI prevention as P0 item
- README shows SSTI prevention documented but still ⏳ Create for full enforcement
- Plan requires end-to-end litmus testing

**Current status**: SSTI prevention policy documented, but enforcement across consumer repos is not proven.

### Fix (Exact Steps)

#### Step 1: Add End-to-End SSTI Litmus Test to Each Consumer Repo

**FILE**: `tests/test_consumer_ssti_litmus.py` (Add to each consumer repository)

```python
# tests/test_consumer_ssti_litmus.py
"""
End-to-end SSTI litmus test for consumer rendering pipeline.

Tests that collected metadata is rendered safely without template evaluation.
Replace jinja2 example with your actual template engine (Django, React SSR, etc.).
"""
import pytest

try:
    import jinja2
    HAS_JINJA = True
except Exception:
    HAS_JINJA = False

MALICIOUS = "{{ 7 * 7 }}"   # Payload that evaluates to "49" in unsafe render


@pytest.mark.skipif(not HAS_JINJA, reason="jinja2 not installed")
def test_consumer_does_not_evaluate_metadata():
    """
    Ensure consumer rendering pipeline does not evaluate untrusted metadata.

    This is a CRITICAL security test - if it fails, SSTI is possible.
    """
    # Sanity check: Template() evaluates (demonstrates the risk)
    naive = jinja2.Template("Title: " + MALICIOUS)
    assert "49" in naive.render().strip(), "Sanity: Jinja2 evaluates templates"

    # Safe approach: autoescape + passing metadata as variable
    env = jinja2.Environment(autoescape=True)
    tm = env.from_string("Title: {{ meta }}")
    res = tm.render(meta=MALICIOUS)

    # CRITICAL ASSERTION: Dangerous payload is NOT evaluated to '49'
    assert "49" not in res, \
        f"❌ CRITICAL: Consumer renders metadata unsafely: {res!r}. SSTI POSSIBLE."
    assert "{{" in res or "{" in res, \
        f"Metadata should be escaped/visible, got: {res!r}"


@pytest.mark.skipif(not HAS_JINJA, reason="jinja2 not installed")
def test_consumer_end_to_end_ssti_prevention():
    """
    Full pipeline test: Parse → Collect → Persist → Render.

    Replace this with your actual consumer flow.
    """
    # Mock: Parse markdown with template-like content
    markdown = """
# {{ config.SECRET_KEY }}

Hello {{ user.password }}
"""

    # Mock: Collect metadata (simulates parser output)
    metadata = {
        "title": "{{ config.SECRET_KEY }}",
        "paragraphs": ["Hello {{ user.password }}"]
    }

    # Mock: Persist to database (simulated)
    # ...

    # ACTUAL: Render using consumer's template engine
    env = jinja2.Environment(autoescape=True)
    template = env.from_string("""
<h1>{{ title }}</h1>
{% for para in paragraphs %}
<p>{{ para }}</p>
{% endfor %}
""")

    rendered = template.render(
        title=metadata["title"],
        paragraphs=metadata["paragraphs"]
    )

    # CRITICAL: Template expressions should NOT be evaluated
    assert "SECRET_KEY" not in rendered, "Template expressions evaluated!"
    assert "{{ config" in rendered or "{{" in rendered, \
        "Template tokens should be visible/escaped"
```

**Success criteria**:
- ✅ Test added to each consumer repository
- ✅ Test runs in consumer CI (blocking)
- ✅ Test uses consumer's actual template engine config
- ✅ Test fails if template tokens evaluate

#### Step 2: Add PR Checklist Entry

**FILE**: `.github/PULL_REQUEST_TEMPLATE.md` (Update in each consumer repo)

Add this section:

```markdown
### Security & SSTI Checklist (REQUIRED)
- [ ] Consumer SSTI litmus tests added/updated where this code renders metadata
- [ ] If enabling `allow_html`, sanitizer policy documented and litmus tests added
- [ ] Metadata rendering uses autoescape/sanitization (Jinja2: `autoescape=True`)
- [ ] No raw HTML rendering without explicit sanitizer
```

#### Step 3: Verification Commands

```bash
# Run consumer SSTI litmus test
cd <consumer-repo>
.venv/bin/python -m pytest tests/test_consumer_ssti_litmus.py -v

# Expected: All assertions pass (no "49" in output)
```

**Effort estimate**: 1 hour per consumer repository

---

## A2: Token Canonicalization Audit Gap (Bypass Risk)

### Problem Statement

**Why it matters**: Canonicalization is implemented in skeleton, but plan requires every dispatch path to only see canonical tokens. Any bypass yields prototype/method-call side effects.

**Evidence**:
- P1 includes token canonicalization test item
- Tests like `test_malicious_token_methods.py` added to skeleton
- Plan marks them as ⏳ Implement in some parts

**Current status**: Tests exist but must run in CI as blocking tests.

### Fix (Exact Steps)

#### Step 1: Audit Codebase for Direct Token Object Usage

```bash
# Search for dangerous token access patterns
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned

# Search for attrGet usage
grep -r "\.attrGet\(" src/ skeleton/ --include="*.py"

# Search for __getattr__ usage
grep -r "\.__getattr__\(" src/ skeleton/ --include="*.py"

# Search for direct token property access (risky patterns)
grep -r "token\.\w\+(" src/ skeleton/ --include="*.py" | grep -v "token.type\|token.content"
```

**Action**: Replace any direct token object usage with canonicalized dict/namespace access.

**Example refactor**:
```python
# ❌ BAD: Direct token method call
href = token.attrGet("href")

# ✅ GOOD: Canonicalized dict access
href = canonicalized_token.get("attrs", {}).get("href")
```

#### Step 2: Make Token Canonicalization Test Mandatory in CI

**FILE**: `.github/workflows/test.yml` (Update)

Add to existing test workflow:

```yaml
- name: Run token canonicalization security tests
  run: |
    .venv/bin/python -m pytest \
      skeleton/tests/test_malicious_token_methods.py \
      -v \
      --tb=short
  # Fail CI if any canonicalization test fails
```

#### Step 3: Add Test to Adversarial Gates

**FILE**: Update adversarial runner to include canonicalization tests

```bash
# Run token canonicalization test as part of adversarial suite
.venv/bin/python -m pytest \
  skeleton/tests/test_malicious_token_methods.py \
  tests/test_adversarial_*.py \
  -v
```

#### Step 4: Fix API Mismatch If Test Skips

If test skips due to API mismatch, adapt test harness:

```python
# Adapt to your TokenWarehouse constructor signature
try:
    wh = TokenWarehouse(tokens, tree=None)
except TypeError:
    # Try alternative signature
    wh = TokenWarehouse(tokens)
```

**Effort estimate**: 2 hours (audit + test integration)

---

## A3: URL/SSRF Parity - Small Vector Gap

### Problem Statement

**Why it matters**: URL canonicalizer exists, but parity tests counted at 20 vs. actual 13/14 passing shows problematic vectors. If fetcher & collector differ on accept/reject, TOCTOU/SSRF mishaps occur.

**Evidence**:
- README shows URL parity: 13/14 passing (not 20/20)
- Plan expects 20 adversarial URL vectors
- Missing tricky vectors: protocol-relative, IDN weirdness, control chars, etc.

### Fix (Exact Steps)

#### Step 1: Add Minimal Fetcher Wrapper

**FILE**: `doxstrux/markdown/fetchers/preview.py` (Create)

```python
"""
Minimal fetcher/preview helper to ensure URL normalization parity.

This module intentionally re-uses the canonical normalize_url() from
security.validators so that collector and fetcher behaviour is identical.

Notes:
- Keep this file minimal. If you do not want the 'requests' dependency
  in the skeleton, you can remove fetch_preview() and keep only
  normalize_url_for_fetcher().
- The parity tests import a fetcher-side normalizer; include this module
  so parity tests are meaningful and do not skip.
"""
from typing import Optional

try:
    # Canonical normalizer (must be the single source of truth)
    from doxstrux.markdown.security.validators import normalize_url
except Exception:
    # Defensive: if module path differs in your repo, adapt the import
    normalize_url = None  # Tests will skip / fail if canonicalizer missing


def normalize_url_for_fetcher(raw: str) -> Optional[str]:
    """
    Thin wrapper used by parity tests / fetcher path.
    Returns canonicalized URL string or None if disallowed.
    """
    if normalize_url is None:
        return None
    try:
        return normalize_url(raw)
    except Exception:
        return None


# Optional: a tiny preview fetcher that uses normalize_url_for_fetcher()
# This makes the preview/fetcher behaviour explicit, but is not required
# for parity tests to exercise normalization itself.
def fetch_preview(url: str, timeout: int = 3):
    """
    Simple HEAD-based preview. Returns metadata dict or None.
    Requires the 'requests' package (optional).
    """
    norm = normalize_url_for_fetcher(url)
    if norm is None:
        return None
    try:
        import requests  # Optional dependency; install in CI if you use this
        r = requests.head(norm, timeout=timeout, allow_redirects=True)
        if r.status_code == 405:
            r = requests.get(norm, timeout=timeout, allow_redirects=True)
        return {
            "url": norm,
            "status_code": r.status_code,
            "content_type": r.headers.get("content-type"),
            "content_length": r.headers.get("content-length"),
        }
    except Exception:
        return None
```

**Verification**:
```bash
# Quick check
python -c "from doxstrux.markdown.fetchers.preview import normalize_url_for_fetcher; print(normalize_url_for_fetcher('https://example.com'))"
```

#### Step 2: Add 20 Adversarial URL Vectors

**FILE**: `adversarial_corpora/adversarial_encoded_urls.json` (Create)

```json
[
  "//internal/admin",
  "JaVaScRiPt:alert(1)",
  "java\tscript:alert(1)",
  "java\nscript:alert(1)",
  "java%3Ascript:alert(1)",
  "  https://example.com/path  ",
  "https://example.com/\u0000image",
  "http://xn--pple-43d.com",
  "data:text/html,<script>alert(1)</script>",
  "file:///etc/passwd",
  "//user:pass@internal.local/",
  "http://[::1]/",
  "https://example.com/%2e%2e/%2e%2e/etc/passwd",
  "http://example.com@attacker.com/",
  "http://example.com:70000/",
  "http://example.com/%00",
  "https://例子.测试",
  "ftp://example.com/resource",
  "http://user:pa%3Ass@host.com/",
  "http://example.com#\u0000"
]
```

**Notes**:
- `\u0000` encodes null characters in JSON
- Vectors exercise: protocol-relative URLs, mixed-case schemes, whitespace obfuscation, percent-encoding, IDNs, data/file schemes, userinfo, invalid ports, control chars

#### Step 3: Update Parity Tests to Use Fetcher

Update parity test to import from fetcher:

```python
# In test_url_normalization_parity.py
from doxstrux.markdown.fetchers.preview import normalize_url_for_fetcher

def test_fetcher_collector_parity():
    """Verify fetcher and collector use same URL normalization."""
    # ... test code using normalize_url_for_fetcher
```

#### Step 4: Run Parity Tests

```bash
# Run URL normalization parity tests
.venv/bin/python -m pytest skeleton/tests/test_url_normalization_parity.py -v

# Expected: 20/20 tests passing (including new vectors)
```

**Effort estimate**: 1.5 hours

---

# PART 12: RUNTIME BLOCKERS (B1-B2)

## B1: Cross-Platform Timeout Enforcement (SIGALRM vs Windows) - Decision Required

### Problem Statement

**Why it matters**: Skeleton uses SIGALRM/timeouts for collectors (Unix only). Windows lacks SIGALRM; a hung collector on Windows could lock resources. Plan notes this as decision point (YAGNI or implement subprocess isolation).

**Evidence**:
- EXEC_PLATFORM_SUPPORT_POLICY.md mentions SIGALRM limitation
- Windows support is conditional per YAGNI decision tree
- Plan requires explicit decision: Linux-only OR subprocess isolation

### Fix Options

#### Option 1: Declare Linux-Only (RECOMMENDED)

**Why recommended**: Fastest, least code, simplest operational model.

**Steps**:

1. **Update Platform Policy**

**FILE**: `skeleton/policies/EXEC_PLATFORM_SUPPORT_POLICY.md` (Update)

Add explicit declaration:

```markdown
## Production Deployment Policy

**REQUIRED**: Linux-only for untrusted parsing workers

**Rationale**:
- SIGALRM timeout enforcement requires Unix signals
- Windows lacks SIGALRM (timeout enforcement not available)
- Subprocess isolation adds significant complexity (8h implementation)
- YAGNI Q1-Q3: No Windows deployment requirement identified

**Enforcement**:
- CI: Assert canary environment is Linux (`platform.system() == 'Linux'`)
- Docs: Document Windows as unsupported for production untrusted input
- Dev: Windows OK for development/testing (timeouts gracefully degrade)

**Alternative**: If Windows deployment confirmed, implement subprocess isolation (P1-2)
```

2. **Add CI Assertion**

**FILE**: `.github/workflows/test.yml` (Add assertion)

```yaml
- name: Assert Linux environment for production
  run: |
    python -c "import platform; assert platform.system() == 'Linux', 'Production requires Linux for SIGALRM timeout enforcement'"
```

3. **Document in README**

**FILE**: `README.md` (Add note)

```markdown
## Platform Support

**Production**: Linux only (SIGALRM timeout enforcement required)
**Development**: Linux, macOS, Windows (timeouts may not enforce on Windows)
```

**Effort estimate**: 30 minutes

#### Option 2: Implement Subprocess Isolation (If Windows Required)

**ONLY if Windows deployment confirmed with Tech Lead approval.**

**Steps**:

1. **Implement Persistent Subprocess Worker Pool**

**FILE**: `doxstrux/markdown/utils/collector_pool.py` (Create)

See `tools/collector_worker_YAGNI_PLACEHOLDER.py` for design sketch.

```python
import multiprocessing as mp
from queue import Queue
from typing import List, Dict, Any

class CollectorPool:
    """
    Persistent subprocess worker pool with watchdogs and automatic restart.

    YAGNI-gated: Implement ONLY if Windows deployment confirmed.
    """

    def __init__(self, num_workers=4):
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()

        self.workers = [
            mp.Process(target=self._worker_loop, args=(self.task_queue, self.result_queue))
            for _ in range(num_workers)
        ]

        for w in self.workers:
            w.start()

    def dispatch_batch(self, collector_specs: List[Dict[str, Any]], tokens_list: List[List[Dict]]):
        """Dispatch multiple collector runs to worker pool."""
        for spec, tokens in zip(collector_specs, tokens_list):
            self.task_queue.put((spec, tokens))

    def collect_results(self, num_tasks: int) -> List[Dict[str, Any]]:
        """Collect results from worker pool."""
        results = []
        for _ in range(num_tasks):
            result = self.result_queue.get()
            results.append(result)
        return results

    def _worker_loop(self, task_queue: mp.Queue, result_queue: mp.Queue):
        """Worker process: Accept tasks, run collectors, return results."""
        while True:
            task = task_queue.get()
            if task is None:  # Shutdown signal
                break

            spec, tokens = task
            result = self._run_collector(spec, tokens)
            result_queue.put(result)

    def _run_collector(self, spec: Dict[str, Any], tokens: List[Dict]) -> Dict[str, Any]:
        """Run single collector in worker process."""
        # Use worker script from P1-2
        from .collector_subproc import run_collector_subprocess
        return run_collector_subprocess(
            spec["collector_name"],
            tokens,
            spec["warehouse_state"],
            spec["timeout"]
        )

    def shutdown(self):
        """Shutdown worker pool."""
        for _ in self.workers:
            self.task_queue.put(None)  # Shutdown signal

        for w in self.workers:
            w.join()
```

2. **Add Prometheus Metrics**

```python
from prometheus_client import Counter

worker_restarts_total = Counter(
    'doxstrux_worker_restarts_total',
    'Collector worker process restarts',
    labelnames=['worker_id']
)
```

3. **Test Under Adversarial Harness**

```bash
# Run adversarial tests with subprocess pool
.venv/bin/python -m pytest tests/test_adversarial_*.py --use-subprocess-pool -v
```

4. **Ensure Collector Allowlist & Signing**

See `skeleton/policies/EXEC_COLLECTOR_ALLOWLIST_POLICY.md` for requirements.

**Effort estimate**: 8 hours (design 2h + implementation 4h + testing 2h)

### Decision Required

**Choose one**:
- [ ] **Option 1** (Linux-only): Update policy, add CI assertion (30 minutes)
- [ ] **Option 2** (Windows support): Implement subprocess pool (8 hours)

---

## B2: Reentrancy & Dispatch Invariants

### Problem Statement

**Why it matters**: `_dispatching` guard was added in skeleton, but plan calls for full reentrancy pattern + negative tests. Any unguarded nested dispatch can corrupt indices or deliver inconsistent context to collectors.

**Evidence**:
- Skeleton has `_dispatching` flag
- Plan requires invariant assertions and negative tests

### Fix (Exact Steps)

#### Step 1: Harden TokenWarehouse with Invariant Assertions

**FILE**: `skeleton/doxstrux/markdown/utils/token_warehouse.py` (Update)

```python
class TokenWarehouse:
    def __init__(self, tokens, tree):
        self.tokens = tokens
        self.tree = tree
        self._collectors = []
        self._dispatching = False
        self._dispatch_count = 0

    def _assert_invariants(self):
        """Assert warehouse invariants (call before/after dispatch)."""
        assert isinstance(self.tokens, list), "tokens must be list"
        assert all(isinstance(t, dict) for t in self.tokens), "tokens must be dicts (canonicalized)"
        assert self._dispatch_count >= 0, "dispatch count negative"

    def dispatch_all(self):
        """Dispatch to all registered collectors."""
        # Assert invariants before dispatch
        self._assert_invariants()

        if self._dispatching:
            raise RuntimeError(
                "Nested dispatch detected. TokenWarehouse.dispatch_all() called while already dispatching. "
                "This indicates a reentrancy bug (collector calling dispatch during on_token)."
            )

        try:
            self._dispatching = True
            self._dispatch_count += 1

            for collector in self._collectors:
                for idx, token in enumerate(self.tokens):
                    collector.on_token(idx, token, None, self)

            # Finalize all collectors
            results = {}
            for collector in self._collectors:
                result = collector.finalize(self)
                results[collector.__class__.__name__] = result

            return results

        except Exception as e:
            # Assert invariants on exception path
            self._assert_invariants()
            raise

        finally:
            self._dispatching = False

            # Assert invariants after dispatch
            self._assert_invariants()
```

#### Step 2: Add Negative Tests for Reentrancy

**FILE**: `skeleton/tests/test_warehouse_reentrancy.py` (Create)

```python
"""
Reentrancy and dispatch invariant tests for TokenWarehouse.

Verifies that nested dispatch is detected and prevented.
"""
import pytest


def test_warehouse_prevents_nested_dispatch():
    """Verify TokenWarehouse raises on nested dispatch."""
    try:
        from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        pytest.skip("TokenWarehouse not available in skeleton")

    tokens = [{"type": "text", "content": "test"}]

    wh = TokenWarehouse(tokens, tree=None)

    # Register a malicious collector that attempts nested dispatch
    class MaliciousCollector:
        def on_token(self, idx, token, ctx, warehouse):
            # Attempt nested dispatch (should raise)
            warehouse.dispatch_all()

        def finalize(self, warehouse):
            return {}

    wh.register_collector(MaliciousCollector())

    # CRITICAL: Nested dispatch must raise RuntimeError
    with pytest.raises(RuntimeError, match="Nested dispatch detected"):
        wh.dispatch_all()


def test_warehouse_invariants_hold_on_exception():
    """Verify invariants are checked even when collector raises."""
    try:
        from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        pytest.skip("TokenWarehouse not available in skeleton")

    tokens = [{"type": "text", "content": "test"}]

    wh = TokenWarehouse(tokens, tree=None)

    # Register a collector that raises
    class FailingCollector:
        def on_token(self, idx, token, ctx, warehouse):
            raise ValueError("Collector intentional failure")

        def finalize(self, warehouse):
            return {}

    wh.register_collector(FailingCollector())

    # Collector failure should propagate, but invariants should still hold
    with pytest.raises(ValueError, match="Collector intentional failure"):
        wh.dispatch_all()

    # Verify warehouse is not in corrupted state
    assert wh._dispatching is False, "Warehouse should not be in dispatching state after exception"
```

#### Step 3: Run Reentrancy Tests

```bash
# Run reentrancy tests
.venv/bin/python -m pytest skeleton/tests/test_warehouse_reentrancy.py -v

# Expected: Both tests pass (nested dispatch raises, invariants hold on exception)
```

**Effort estimate**: 1.5 hours

---

# PART 13: PERFORMANCE/CORRECTNESS BLOCKERS (C1-C3)

## C1: Collector Caps Failing Integration (OOM/Slow Risk)

### Problem Statement

**Why it matters**: Caps exist conceptually and in skeleton, but failing collector caps test indicates some collectors aren't honoring per-collector limits. This allows memory amplification or extremely large result sets.

**Evidence**:
- README flags "Collector caps implemented — ⚠️ 1/9 PASSING (import issue)"
- Plan expects all 9 collector cap tests passing

### Fix (Exact Steps)

#### Step 1: Run Failing Tests with Verbose Debug

```bash
# Run collector caps tests with verbose output
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance

.venv/bin/python -m pytest \
  skeleton/tests/test_collector_caps_end_to_end.py \
  -v \
  --tb=long \
  --capture=no

# Identify which collectors fail to import/register
```

#### Step 2: Fix Import Paths

If tests skip due to import errors:

```python
# Check PYTHONPATH includes skeleton/
import sys
sys.path.insert(0, '/path/to/skeleton')

# Or: Install skeleton in editable mode
cd /path/to/skeleton
pip install -e .
```

#### Step 3: Ensure Every Collector Sets Truncated Flags

**Example pattern** (apply to all collectors):

```python
class LinksCollector:
    HARD_CAP = 10000  # Maximum links per document

    def __init__(self):
        self._links = []

    def on_token(self, idx, token, ctx, warehouse):
        if len(self._links) >= self.HARD_CAP:
            # Stop collecting (cap reached)
            return

        # ... collect link

    def finalize(self, warehouse):
        truncated = len(self._links) >= self.HARD_CAP

        return {
            "links": self._links[:self.HARD_CAP],
            "links_truncated": truncated,
            "links_truncated_count": len(self._links) if truncated else 0
        }
```

#### Step 4: Add Metrics for Truncation

**FILE**: `src/doxstrux/markdown/observability.py` (Add metric)

```python
from prometheus_client import Counter

collector_truncated_total = Counter(
    'doxstrux_collector_truncated_total',
    'Documents hitting collector caps',
    labelnames=['collector_type']
)

# Usage in collector finalize():
if truncated:
    collector_truncated_total.labels(collector_type='links').inc()
```

#### Step 5: Add Alert Rule

```promql
# Alert if cap truncations spike (>100/min for 5 minutes)
rate(doxstrux_collector_truncated_total[5m]) > 100
```

#### Step 6: Verify All Caps Tests Pass

```bash
# Re-run collector caps tests
.venv/bin/python -m pytest skeleton/tests/test_collector_caps_end_to_end.py -v

# Expected: 9/9 tests passing
```

**Effort estimate**: 2 hours

---

## C2: section_of Must Be O(log N) (Binary Search)

### Problem Statement

**Why it matters**: Plan requires binary search for `section_of` to avoid linear scans on large docs. If implementation is linear, large docs will regress.

**Evidence**:
- P1-1 task: Binary search O(log N) | ✅ Complete (reference implementation exists)
- Must verify production code uses binary search (not linear scan)

### Fix (Exact Steps)

#### Step 1: Verify Production Uses Binary Search

Check production code:

```python
# In src/doxstrux/markdown_parser_core.py or equivalent
# Should use bisect-based lookup (not linear scan)

import bisect

def section_of(self, line_num: int) -> Optional[str]:
    """Find section containing line_num (O(log N) binary search)."""
    if not self._sections:
        return None

    # Build sorted list of start lines
    starts = [s['start_line'] for s in self._sections]
    idx = bisect.bisect_right(starts, line_num) - 1

    if idx < 0:
        return None

    section = self._sections[idx]
    if section['start_line'] <= line_num <= section.get('end_line', float('inf')):
        return section['id']

    return None
```

#### Step 2: Add Microbenchmark Test

**FILE**: `tests/test_section_lookup_performance.py` (Add to production tests/)

```python
"""
Performance benchmark for section_of() - must be O(log N).

Verifies that section lookup scales logarithmically, not linearly.
"""
import time
import pytest


def test_section_of_is_logarithmic():
    """Verify section_of() scales as O(log N), not O(N)."""
    from doxstrux.markdown_parser_core import MarkdownParserCore

    def make_sections(n):
        """Create n sections with non-overlapping line ranges."""
        lines = [f"# Section {i}\n" for i in range(n)]
        markdown = "\n".join(lines)
        return markdown

    sizes = [100, 1000, 10000]
    times = []

    for size in sizes:
        markdown = make_sections(size)
        parser = MarkdownParserCore(markdown)
        result = parser.parse()

        # Benchmark section lookup (mid-point, worst case for linear)
        start = time.perf_counter()
        for _ in range(1000):
            parser.section_of(size // 2)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    # Check logarithmic growth
    # If O(log N): time[1] / time[0] ≈ log(1000)/log(100) ≈ 1.5
    # If O(N): time[1] / time[0] ≈ 1000/100 = 10
    ratio = times[1] / times[0] if times[0] > 0 else float('inf')

    assert ratio < 3.0, \
        f"section_of() appears O(N), not O(log N): ratio={ratio:.2f}. Times: {times}"

    # EVIDENCE ANCHOR
    # CLAIM-C2-PERF: section_of() shows O(log N) scaling
    # Source: External audit C.2
    # Verification: Ratio < 3.0 indicates logarithmic growth
```

#### Step 3: Assert P95 Latency Threshold

Add to production tests:

```python
def test_section_of_p95_latency():
    """Assert section_of P95 latency ≤ threshold for 10k sections."""
    from doxstrux.markdown_parser_core import MarkdownParserCore
    import numpy as np

    # Create large document (10k sections)
    markdown = "\n".join([f"# Section {i}\n" for i in range(10000)])
    parser = MarkdownParserCore(markdown)
    result = parser.parse()

    # Measure 1000 lookups
    latencies = []
    for i in range(1000):
        start = time.perf_counter()
        parser.section_of(i * 10)
        latencies.append(time.perf_counter() - start)

    # Compute P95
    p95 = np.percentile(latencies, 95)

    # Assert P95 < 10 microseconds (aggressive threshold for O(log N))
    assert p95 < 0.00001, f"section_of P95 latency too high: {p95*1000000:.2f}µs"
```

#### Step 4: Run Performance Tests

```bash
# Run section lookup performance tests
.venv/bin/python -m pytest tests/test_section_lookup_performance.py -v

# Expected: Both tests pass (ratio < 3.0, P95 < threshold)
```

**Effort estimate**: 1 hour

---

## C3: Auto-Fastpath for Tiny Docs (Avoid Index Overhead)

### Problem Statement

**Why it matters**: Building indices for tiny docs regresses. Plan suggests threshold to bypass warehouse for very small docs.

**Evidence**:
- P2-3: Auto-fastpath pattern documented
- YAGNI-gated: Implement only if profiling shows warehouse overhead >20%

### Fix (Exact Steps - ONLY IF PROFILING SHOWS NEED)

#### Step 1: Profile Warehouse Overhead for Tiny Docs

```python
# Profile script
import time
from doxstrux.markdown_parser_core import MarkdownParserCore

tiny_doc = "# Test\nHello world\n"  # ~20 bytes

# Benchmark warehouse path
start = time.perf_counter()
for _ in range(1000):
    parser = MarkdownParserCore(tiny_doc, use_warehouse=True)
    parser.parse()
warehouse_time = time.perf_counter() - start

# Benchmark linear path (if available)
start = time.perf_counter()
for _ in range(1000):
    parser = MarkdownParserCore(tiny_doc, use_warehouse=False)
    parser.parse()
linear_time = time.perf_counter() - start

overhead_pct = ((warehouse_time - linear_time) / linear_time) * 100
print(f"Warehouse overhead for tiny docs: {overhead_pct:.1f}%")

# Only implement if overhead >20%
if overhead_pct > 20:
    print("✅ Implement auto-fastpath")
else:
    print("❌ YAGNI - warehouse overhead acceptable")
```

#### Step 2: Implement Threshold (If Needed)

**ONLY if profiling shows >20% overhead:**

```python
class MarkdownParserCore:
    SMALL_DOC_TOKEN_THRESHOLD = 100  # Tokens

    def parse(self):
        # Count tokens
        token_count = len(self.tokens)

        # Auto-fastpath for tiny docs
        if token_count < self.SMALL_DOC_TOKEN_THRESHOLD:
            return self._extract_linear()  # Skip warehouse
        else:
            return self._extract_with_warehouse()  # Use warehouse
```

#### Step 3: Add Performance Regression Test

```python
def test_tiny_docs_not_slower_with_warehouse():
    """Ensure tiny docs are not slower under warehouse-enabled path."""
    tiny_doc = "# Test\nHello\n"

    # Benchmark warehouse path
    start = time.perf_counter()
    for _ in range(1000):
        parser = MarkdownParserCore(tiny_doc)
        parser.parse()
    warehouse_time = time.perf_counter() - start

    # Assert reasonable latency (< 1ms per parse)
    assert warehouse_time < 1.0, f"Tiny docs too slow: {warehouse_time*1000:.2f}ms for 1000 parses"
```

**Effort estimate**: 2 hours (IF profiling shows need - otherwise skip per YAGNI)

---

# PART 14: CI/OBSERVABILITY BLOCKERS (D1-D2)

## D1: Adversarial Corpora Must Be Blocking Gate with Artifacts

### Problem Statement

**Why it matters**: Docs include adversarial corpora and runner, but plan insists these are P3 CI gates and artifacts must be uploaded for triage. Without blocking CI, you can merge regressions.

**Evidence**:
- P3-1 documented adversarial CI gates
- External audit requires blocking CI job

### Fix (Exact Steps)

#### Step 1: Add Adversarial CI Workflow

**FILE**: `.github/workflows/adversarial_full.yml` (Create)

```yaml
name: Adversarial Full Suite (PR + Nightly)

on:
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 4 * * *'   # Nightly 04:00 UTC

jobs:
  adversarial:
    runs-on: ubuntu-latest
    timeout-minutes: 40

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          # Install optional sanitizers/test helpers
          pip install bleach jinja2 requests

      - name: Create reports directory
        run: mkdir -p adversarial_reports

      - name: Run adversarial corpora (fail on any nonzero)
        run: |
          set -euo pipefail
          for corpus in adversarial_corpora/adversarial_*.json; do
            out="adversarial_reports/$(basename ${corpus%.*}).report.json"
            echo "Running: $corpus -> $out"

            # Run runner and fail if it returns non-zero
            .venv/bin/python -u tools/run_adversarial.py "$corpus" --runs 1 --report "$out"

            if [ ! -f "$out" ]; then
              echo "ERROR: runner did not produce report for $corpus"
              exit 2
            fi
          done

      - name: Upload adversarial reports
        uses: actions/upload-artifact@v4
        with:
          name: adversarial-reports
          path: adversarial_reports/*.report.json
          retention-days: 30
```

#### Step 2: Make Job Required

**GitHub Settings**:
1. Go to Settings → Branches → Branch protection
2. Select `main` branch
3. Add required status check: `adversarial / adversarial`

**Alternative** (PR smoke + nightly full):
- Run small smoke corpus on PRs (required)
- Run full suite nightly (upload artifacts)

#### Step 3: Local Debug

```bash
# Run adversarial suite locally
python -u tools/run_adversarial.py \
  adversarial_corpora/adversarial_encoded_urls.json \
  --runs 1 \
  --report /tmp/encoded_urls.report.json

# Inspect report
cat /tmp/encoded_urls.report.json | jq
```

**Effort estimate**: 1 hour

---

## D2: Concrete Metrics & Alerting

### Problem Statement

**Why it matters**: Need concrete SLO indicators to detect regressions or attacks quickly.

**Evidence**:
- P3-2 documented production observability patterns
- External audit requires minimum metrics implemented

### Fix (Exact Steps)

#### Step 1: Add Required Metrics

**FILE**: `src/doxstrux/markdown/observability.py` (Add to existing)

```python
from prometheus_client import Histogram, Counter, Gauge

# Performance metrics
parse_p95_ms = Histogram(
    'doxstrux_parse_p95_ms',
    'P95 parse latency in milliseconds',
    labelnames=['document_size_bucket'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0]
)

parse_p99_ms = Histogram(
    'doxstrux_parse_p99_ms',
    'P99 parse latency in milliseconds',
    labelnames=['document_size_bucket'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0]
)

parse_peak_rss_mb = Gauge(
    'doxstrux_parse_peak_rss_mb',
    'Peak RSS memory per parse in MB'
)

# Runtime metrics
collector_timeouts_total = Counter(
    'doxstrux_collector_timeouts_total',
    'Collector timeout events',
    labelnames=['collector_type']
)

collector_restarts_total = Counter(
    'doxstrux_collector_restarts_total',
    'Collector worker restarts',
    labelnames=['worker_id']
)

collector_truncated_total = Counter(
    'doxstrux_collector_truncated_total',
    'Documents hitting collector caps',
    labelnames=['collector_type']
)

# CI/Test metrics
adversarial_suite_failures_total = Counter(
    'doxstrux_adversarial_suite_failures_total',
    'Adversarial suite test failures',
    labelnames=['corpus_name']
)
```

#### Step 2: Add Dashboards

**Grafana Dashboard JSON** (import in Grafana UI):

```json
{
  "dashboard": {
    "title": "Doxstrux Parser SLOs",
    "panels": [
      {
        "title": "Parse P95 Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(doxstrux_parse_p95_ms_bucket[5m]))"
        }]
      },
      {
        "title": "Parse P99 Latency",
        "targets": [{
          "expr": "histogram_quantile(0.99, rate(doxstrux_parse_p99_ms_bucket[5m]))"
        }]
      },
      {
        "title": "Collector Truncations (24h)",
        "targets": [{
          "expr": "increase(doxstrux_collector_truncated_total[24h])"
        }]
      },
      {
        "title": "Adversarial Suite Failures",
        "targets": [{
          "expr": "rate(doxstrux_adversarial_suite_failures_total[5m])"
        }]
      }
    ]
  }
}
```

#### Step 3: Add Alert Rules

**Prometheus Alert Rules** (alerting.rules.yml):

```yaml
groups:
  - name: doxstrux_slos
    interval: 30s
    rules:
      # Page if P99 latency > baseline × 2
      - alert: DoxstruxParseP99High
        expr: histogram_quantile(0.99, rate(doxstrux_parse_p99_ms_bucket[5m])) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Doxstrux parse P99 latency > 10ms"
          description: "P99 latency {{ $value }}ms for 5 minutes"

      # Alert if collector truncations spike
      - alert: DoxstruxCollectorTruncationsHigh
        expr: rate(doxstrux_collector_truncated_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Collector truncations > 100/min"
          description: "Truncation rate {{ $value }}/min for 5 minutes"

      # Alert on adversarial suite failures
      - alert: DoxstruxAdversarialSuiteFailing
        expr: rate(doxstrux_adversarial_suite_failures_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Adversarial suite failures detected"
          description: "{{ $labels.corpus_name }} failing"
```

**Effort estimate**: 2 hours

---

# PART 15: IMPLEMENTATION CHECKLIST (Prioritized)

## Blockers (Must Finish Before Green-Light)

### Blocker 1: Adversarial CI Gate + Artifact Upload

**Priority**: 🔴 CRITICAL
**Effort**: 1 hour
**Owner**: DevOps

**Tasks**:
- [ ] Add `.github/workflows/adversarial_full.yml` (see PART 14 D1)
- [ ] Mark PR smoke as required OR run full suite nightly
- [ ] Upload artifacts (30-day retention)

**Verification**:
```bash
# Run locally
python -u tools/run_adversarial.py \
  adversarial_corpora/adversarial_combined.json \
  --report /tmp/adversarial.report.json

# Expected: All tests pass, report generated
```

**Evidence**: Job runs on every PR, artifacts uploaded on failure

---

### Blocker 2: SSTI End-to-End Litmus Across Consumers

**Priority**: 🔴 CRITICAL
**Effort**: 1 hour per consumer
**Owner**: Consumer teams

**Tasks**:
- [ ] Add `tests/test_consumer_ssti_litmus.py` to each consumer repo (see PART 11 A1)
- [ ] Update PR template with SSTI checklist
- [ ] Run test in consumer CI (blocking)

**Verification**:
```bash
# Run consumer SSTI litmus
cd <consumer-repo>
pytest tests/test_consumer_ssti_litmus.py -v

# Expected: All assertions pass (no "49" in output)
```

**Evidence**: Test exists in each consumer repo, runs in CI, blocks PRs

---

### Blocker 3: Fix Collector Caps Integration

**Priority**: 🔴 CRITICAL
**Effort**: 2 hours
**Owner**: Dev

**Tasks**:
- [ ] Run failing cap tests with verbose debug (see PART 13 C1)
- [ ] Fix import/registration issues
- [ ] Ensure all collectors set truncated flags
- [ ] Add `collector_truncated_total` metric
- [ ] Add alert rule

**Verification**:
```bash
# Run collector caps tests
.venv/bin/python -m pytest \
  skeleton/tests/test_collector_caps_end_to_end.py \
  -v

# Expected: 9/9 tests passing
```

**Evidence**: All 9 collector cap tests passing

---

### Blocker 4: Decide Platform Policy (Linux Only vs Subprocess on Windows)

**Priority**: 🔴 CRITICAL (Decision Required)
**Effort**: 30 minutes (Linux-only) OR 8 hours (Windows support)
**Owner**: Tech Lead

**Tasks**:

**Option 1 (Linux-only - RECOMMENDED)**:
- [ ] Update `EXEC_PLATFORM_SUPPORT_POLICY.md` (see PART 12 B1)
- [ ] Add CI assertion for Linux environment
- [ ] Document in README

**Option 2 (Windows support)**:
- [ ] Implement subprocess worker pool (see PART 12 B1)
- [ ] Add Prometheus metrics for worker restarts
- [ ] Test under adversarial harness
- [ ] Implement collector allowlist & signing

**Verification**:
```bash
# Option 1: Assert Linux
python -c "import platform; assert platform.system() == 'Linux'"

# Option 2: Test subprocess pool
pytest tests/test_adversarial_*.py --use-subprocess-pool -v
```

**Evidence**: Policy documented, CI enforces choice

---

## High Priority (Next)

### HP-5: Make Token Canonicalization Tests Blocking

**Priority**: 🟠 HIGH
**Effort**: 2 hours
**Owner**: Dev

**Tasks**:
- [ ] Audit codebase for `.attrGet()`, `.__getattr__()` usage (see PART 11 A2)
- [ ] Add `test_malicious_token_methods.py` to PR CI
- [ ] Add to adversarial suite
- [ ] Fix API mismatch if tests skip

**Verification**:
```bash
# Search for dangerous patterns
grep -r "\.attrGet\(" src/ skeleton/ --include="*.py"

# Run canonicalization tests
pytest skeleton/tests/test_malicious_token_methods.py -v

# Expected: All tests pass (no side effects detected)
```

---

### HP-6: Implement section_of Binary Search

**Priority**: 🟠 HIGH
**Effort**: 1 hour
**Owner**: Dev

**Tasks**:
- [ ] Verify production uses `bisect` (not linear scan) (see PART 13 C2)
- [ ] Add microbenchmark test
- [ ] Assert P95 latency ≤ threshold

**Verification**:
```bash
# Run performance tests
pytest tests/test_section_lookup_performance.py -v

# Expected: Ratio < 3.0 (logarithmic), P95 < 10µs
```

---

### HP-7: Add collector_truncated_total Metric and Alert

**Priority**: 🟠 HIGH
**Effort**: 30 minutes
**Owner**: SRE

**Tasks**:
- [ ] Add metric to `observability.py` (see PART 14 D2)
- [ ] Add alert rule (rate > 100/min)
- [ ] Add to Grafana dashboard

**Verification**:
```bash
# Check metric exposed
curl localhost:8000/metrics | grep collector_truncated_total

# Expected: Metric present
```

---

## Medium/Longer Term

### MT-8: Fuzzing Job (Hypothesis/Nightly)

**Priority**: 🟢 MEDIUM
**Effort**: 4 hours
**Owner**: QA

**Tasks**:
- [ ] Add Hypothesis-based fuzzing tests (see P2-4)
- [ ] Add to nightly CI
- [ ] Upload crash artifacts

**YAGNI Gate**: Only if crashes/hangs found in production

---

### MT-9: Worker Pool Tuning and Load Testing

**Priority**: 🟢 MEDIUM
**Effort**: 6 hours
**Owner**: SRE

**Tasks**:
- [ ] Benchmark subprocess pool performance
- [ ] Tune worker count
- [ ] Load test with production traffic patterns

**YAGNI Gate**: Only if Windows support required (Blocker 4 Option 2)

---

### MT-10: Code Signing for External Collectors

**Priority**: 🟢 LOW
**Effort**: 4 hours
**Owner**: Security

**Tasks**:
- [ ] Implement package signing (see P1-2.5)
- [ ] Build-time hash generation
- [ ] Runtime hash verification

**YAGNI Gate**: Only if distributing as package on PyPI

---

# PART 16: READY-TO-APPLY ARTIFACTS

## Artifact 1: Minimal Fetcher + 20 Adversarial URL Vectors

### File 1: doxstrux/markdown/fetchers/preview.py

**Location**: `src/doxstrux/markdown/fetchers/preview.py`

**Content**: (See PART 11 A3 Step 1)

### File 2: adversarial_corpora/adversarial_encoded_urls.json

**Location**: `adversarial_corpora/adversarial_encoded_urls.json`

**Content**: (See PART 11 A3 Step 2)

### Application Instructions

```bash
# Create directories
mkdir -p src/doxstrux/markdown/fetchers
mkdir -p adversarial_corpora

# Copy files (paste content from PART 11 A3)
# ... (files provided above)

# Verify imports
python -c "from doxstrux.markdown.fetchers.preview import normalize_url_for_fetcher; print('✅ Import OK')"

# Run parity tests
pytest tests/test_url_normalization_parity.py -v
```

---

## Artifact 2: Blocking Adversarial CI Job (Artifacts + Fail-on-Error)

### File: .github/workflows/adversarial_full.yml

**Location**: `.github/workflows/adversarial_full.yml`

**Content**: (See PART 14 D1 Step 1)

### Application Instructions

```bash
# Create workflow file
mkdir -p .github/workflows

# Copy content (paste from PART 14 D1)
# ... (YAML provided above)

# Test locally
python -u tools/run_adversarial.py \
  adversarial_corpora/adversarial_encoded_urls.json \
  --runs 1 \
  --report /tmp/test.report.json

# Commit and push
git add .github/workflows/adversarial_full.yml
git commit -m "Add adversarial CI gate (blocking)"
git push
```

### Make Required

**GitHub Settings → Branches → Branch protection**:
- Add required status check: `adversarial / adversarial`

---

## Artifact 3: Consumer SSTI Litmus Test + PR Checklist

### File 1: tests/test_consumer_ssti_litmus.py

**Location**: `tests/test_consumer_ssti_litmus.py` (in each consumer repo)

**Content**: (See PART 11 A1 Step 1)

### File 2: PR Checklist Snippet

**Location**: `.github/PULL_REQUEST_TEMPLATE.md` (in each consumer repo)

**Content**: (See PART 11 A1 Step 2)

### Application Instructions

```bash
# In each consumer repository:

# Add SSTI litmus test
# ... (paste content from PART 11 A1)

# Update PR template
# ... (add checklist from PART 11 A1)

# Install jinja2 (if not already)
pip install jinja2

# Run test
pytest tests/test_consumer_ssti_litmus.py -v

# Expected: All assertions pass
```

---

# FINAL STATUS AND NEXT STEPS

## Audit Verdict

**Conditionally YES - Ready for Canary After Blockers Resolved**

**Quote from audit**: "The architecture, token canonicalization, canonical URL normalizer, HTML default-off, and the adversarial tooling are all in place and documented; that's a big win. The remaining blockers are operational (CI gating, consumer enforcement, cross-platform timeouts, and a small set of failing tests) rather than architectural."

## Green-Light Criteria

**Complete when**:
- ✅ **Blocker 1**: Adversarial CI gate active + artifacts uploaded
- ✅ **Blocker 2**: Consumer SSTI litmus tests added to all consumer repos
- ✅ **Blocker 3**: All 9 collector cap tests passing
- ✅ **Blocker 4**: Platform policy decided (Linux-only OR subprocess pool)
- ✅ **HP-5**: Token canonicalization tests blocking in CI
- ✅ **HP-6**: section_of binary search verified (O(log N))
- ✅ **HP-7**: Collector truncation metric + alert active
- ✅ Full adversarial suite passing (all corpora)
- ✅ 542/542 baseline parity maintained
- ✅ Observability alerts configured

## Timeline Estimate

**Blockers (1-4)**: 5-6 hours (or 13-14 hours if Windows support required)
**High Priority (5-7)**: 3.5 hours
**Total to green-light**: 8.5-9.5 hours (or 16.5-17.5 hours with Windows support)

## Recommended Execution Order

1. **Day 1** (4 hours):
   - Blocker 1: Adversarial CI gate (1h)
   - Blocker 3: Fix collector caps (2h)
   - Blocker 4: Decide platform policy (30min)
   - HP-7: Add truncation metric (30min)

2. **Day 2** (3 hours):
   - Blocker 2: SSTI litmus tests (1h per consumer × 2 consumers)
   - HP-5: Token canonicalization blocking (1h)

3. **Day 3** (2 hours):
   - HP-6: Binary search verification (1h)
   - Final verification: Run full adversarial + baseline suites (1h)

**Total**: 3 days, 9 hours

## Post-Green-Light

**Canary deployment**:
1. Deploy to 1% of traffic
2. Monitor metrics for 24 hours
3. Verify no regressions (P95 latency, error rate, truncations)
4. Gradual rollout: 1% → 10% → 50% → 100%

**Success criteria**:
- P95 latency not regressed
- Error rate < 0.1%
- No SSTI/XSS/SSRF incidents
- Adversarial suite passing nightly

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Source**: External security audit (deep analysis)
**Blockers**: 4 critical, 3 high-priority
**Total Effort**: 8.5-9.5 hours to green-light
**Approved By**: Pending Human Review + Blocker Resolution
**Next Review**: After all blockers resolved and canary deployed
