# Phase 8 Security Quick Reference

**Version**: 1.0
**Date**: 2025-10-15
**Purpose**: Fast lookup for security hardening - apply these NOW
**Format**: Concise checklist with copy/paste fixes

---

## 🔴 Critical Fixes (Apply Immediately)

### Fix #1: Input Size Caps (DoS Prevention)
**Problem**: Huge documents cause OOM
**Fix**:
```python
# Add to parse entry point
MAX_BYTES = 10 * 1024 * 1024  # 10MB
MAX_TOKENS = 500_000

if len(content.encode('utf-8')) > MAX_BYTES:
    raise ValueError("Document exceeds 10MB")
if len(tokens) > MAX_TOKENS:
    raise ValueError("Document exceeds 500K tokens")
```
**Test**: `test_huge_document_rejection()`

---

### Fix #2: Map Normalization (Correctness)
**Problem**: Negative/inverted maps corrupt sections
**Fix**:
```python
# In TokenWarehouse._build_indices()
MAX_LINE = 1_000_000

for i, tok in enumerate(tokens):
    m = getattr(tok, 'map', None)
    if m and len(m) == 2:
        s = max(0, min(int(m[0] or 0), MAX_LINE))
        e = max(s, min(int(m[1] or s), MAX_LINE))
        tok.map = (s, e)

# Sort headings by normalized start
heads = sorted(heads, key=lambda h: (tokens[h].map[0] or 0))
```
**Test**: `test_malformed_maps()`

---

### Fix #3: URL Scheme Allowlist (SSRF/XSS Prevention)
**Problem**: file:, data:, javascript: URIs are unsafe
**Fix**:
```python
from urllib.parse import urlsplit

ALLOWED = {"http", "https", "mailto", "tel"}

def safe_url(url):
    if url.startswith('//'): return False
    parsed = urlsplit(url.strip())
    return parsed.scheme.lower() in ALLOWED if parsed.scheme else True

# In LinksCollector/ImagesCollector
link["allowed"] = safe_url(href)
```
**Test**: `test_unsafe_url_schemes()`

---

### Fix #4: Collector Error Isolation (Fault Tolerance)
**Problem**: One collector crash kills all parsing
**Fix**:
```python
# In TokenWarehouse.dispatch_all()
RAISE = globals().get('RAISE_ON_COLLECTOR_ERROR', False)

for i, tok in enumerate(tokens):
    for col in cols:
        try:
            col.on_token(i, tok, ctx, self)
        except Exception as e:
            self._collector_errors.append((col.name, i, type(e).__name__))
            if RAISE: raise
```
**Test**: `test_collector_exception_isolation()`

---

### Fix #5: HTML Safety (XSS Prevention)
**Problem**: Raw HTML returned, downstream renders it unsafely
**Fix**:
```python
# In HtmlCollector.finalize()
ALLOW = globals().get('ALLOW_RAW_HTML', False)

if not ALLOW:
    return {"html_present": len(items), "count": len(items)}

return {
    "items": items,
    "warning": "MUST sanitize with Bleach/DOMPurify"
}
```
**Test**: `test_html_not_returned_by_default()`

---

### Fix #6: Per-Collector Caps (Memory Bounds)
**Problem**: Unbounded accumulation causes OOM
**Fix**:
```python
# In each collector
MAX_ITEMS = 10_000

class LinksCollector:
    def __init__(self):
        self._truncated = False

    def on_token(self, idx, token, ctx, wh):
        if len(self._links) >= MAX_ITEMS:
            self._truncated = True
            return
        # ... existing logic ...

    def finalize(self, wh):
        return {
            "links": self._links,
            "truncated": self._truncated,
            "count": len(self._links)
        }
```
**Test**: `test_collector_caps()`

---

## ⚠️ Security Checklist

### Before Phase 8.0 Deployment
- [ ] **Fix #1**: Input caps applied (MAX_BYTES, MAX_TOKENS)
- [ ] **Fix #2**: Map normalization in _build_indices
- [ ] **Fix #3**: URL allowlist in Links/Images collectors
- [ ] **Fix #4**: Collector error isolation in dispatch_all
- [ ] **Fix #5**: HTML default-off with ALLOW_RAW_HTML flag
- [ ] **Fix #6**: Per-collector caps with truncation flags

### Testing
- [ ] Run `test_vulnerabilities_extended.py` (all pass)
- [ ] Run adversarial corpus (no crashes)
- [ ] Fuzz test with malformed maps (invariants hold)
- [ ] Load test with huge documents (rejects properly)

### Documentation
- [ ] Document ALLOW_RAW_HTML requirement
- [ ] Document URL scheme allowlist
- [ ] Document collector caps and truncation behavior
- [ ] Update API docs (finalize returns dict with metadata)

### Monitoring (Production)
- [ ] Alert on `tokens_per_parse > 100K`
- [ ] Alert on `_collector_errors > 0`
- [ ] Alert on `unsafe_scheme_count > 0`
- [ ] Dashboard: parse time p95, memory peak, error rate

---

## 🔍 Detection Patterns

### Telemetry to Track
```python
metrics = {
    "tokens_per_parse": len(tokens),
    "parse_duration_ms": elapsed * 1000,
    "peak_memory_mb": peak / 1024 / 1024,
    "collector_errors": len(wh._collector_errors),
    "unsafe_urls": sum(1 for l in links if not l["allowed"]),
    "html_present": len(html_items),
    "truncated_collectors": sum(1 for r in results.values() if r.get("truncated")),
}
```

### Alert Thresholds
- `tokens_per_parse > 100_000` → Large document
- `parse_duration_ms > 5_000` → Slow parse
- `peak_memory_mb > 500` → Memory spike
- `collector_errors > 0` → Collector failure
- `unsafe_urls > 0` → Security issue
- `html_present > 0` → Review needed

---

## 🧪 Test Coverage

### Required Tests
```python
# Security
test_huge_document_rejection()          # Fix #1
test_malformed_maps()                   # Fix #2
test_unsafe_url_schemes()               # Fix #3
test_collector_exception_isolation()    # Fix #4
test_html_not_returned_by_default()     # Fix #5
test_collector_caps()                   # Fix #6

# Runtime
test_resource_exhaustion_protection()
test_section_invariants_with_bad_maps()
test_partial_state_prevention()

# Adversarial
test_adversarial_corpus()
test_fuzz_random_maps()
```

### Test Fixture
```python
# Adversarial token generator
def malicious_tokens():
    return [
        Tok("heading", map=(-100, -50)),        # Negative map
        Tok("heading", map=(1000, 500)),        # Inverted map
        Tok("link_open", href="file:///etc/passwd"),  # File URI
        Tok("link_open", href="javascript:alert(1)"), # JS URI
        Tok("html_block", content="<script>evil</script>"),  # XSS
    ]
```

---

## 📦 Implementation Status

| Fix | Status | File | Lines |
|-----|--------|------|-------|
| #1: Input caps | ❌ Not implemented | `markdown_parser_core.py` | ~10 |
| #2: Map norm | ✅ In warehouse_phase8_patched | `token_warehouse.py` | ~20 |
| #3: URL allowlist | ⚠️ In patch doc, not applied | `links.py` | ~15 |
| #4: Error isolation | ✅ In warehouse_phase8_patched | `token_warehouse.py` | ~10 |
| #5: HTML safety | ❌ Not implemented | `html.py` | ~8 |
| #6: Collector caps | ⚠️ In patch doc, not applied | `links.py, images.py` | ~5 each |

**Total LOC to apply**: ~73 lines across 4 files

---

## 🚀 Quick Apply Script

```bash
#!/bin/bash
# Apply all security fixes to skeleton

cd /path/to/skeleton

# Fix #1: Input caps
cat >> doxstrux/markdown/core/parser_adapter.py <<'EOF'
MAX_BYTES = 10 * 1024 * 1024
MAX_TOKENS = 500_000

def validate_input(content, tokens):
    if len(content.encode('utf-8')) > MAX_BYTES:
        raise ValueError("Document too large")
    if len(tokens) > MAX_TOKENS:
        raise ValueError("Too many tokens")
EOF

# Fix #3: URL allowlist (apply patch from COMPREHENSIVE_SECURITY_PATCH.md)
# (lines 22-73)

# Fix #5: HTML safety
cat >> doxstrux/markdown/collectors_phase8/html.py <<'EOF'
def finalize(self, wh):
    if not globals().get('ALLOW_RAW_HTML', False):
        return {"html_present": len(self._items), "count": len(self._items)}
    return {"items": self._items, "warning": "MUST sanitize"}
EOF

# Fix #6: Collector caps (apply to all collectors)
# Add MAX_ITEMS = 10_000 and _truncated flag
```

---

## 📚 Related Documentation

### Detailed Analysis
- `ATTACK_SCENARIOS_AND_MITIGATIONS.md` - Full attack modes (850 lines)
- `CRITICAL_VULNERABILITIES_ANALYSIS.md` - Deep dive (650 lines)
- `COMPREHENSIVE_SECURITY_PATCH.md` - Complete patches (450 lines)

### Integration
- `PHASE_8_SECURITY_INTEGRATION_GUIDE.md` - Deployment guide
- `CI_CD_INTEGRATION.md` - CI gates (G1-G7 + P1-P3)

### Testing
- `skeleton/tests/test_vulnerabilities_extended.py` (380 lines)
- `skeleton/tools/generate_adversarial_corpus.py` (37 lines)
- `skeleton/tools/run_adversarial.py` (90 lines)

---

## 🎯 Priority Order

### Phase 8.0 (Must Have)
1. **Fix #2**: Map normalization (correctness)
2. **Fix #4**: Collector error isolation (availability)
3. **Fix #1**: Input caps (DoS prevention)

### Phase 8.1 (Should Have)
4. **Fix #3**: URL allowlist (SSRF prevention)
5. **Fix #6**: Collector caps (memory bounds)

### Phase 8.2 (Nice to Have)
6. **Fix #5**: HTML safety (XSS prevention)

---

## ⚡ Emergency Rollback

If production issues occur:

```bash
# 1. Revert to Phase 7.6
git revert <phase-8-commit>

# 2. Verify baseline parity
.venv/bin/python tools/baseline_test_runner.py

# 3. Check logs for patterns
grep "collector_error" logs/ | wc -l
grep "DocumentTooLarge" logs/ | wc -l

# 4. Isolate issue
python -m pdb tools/reproduce_issue.py
```

---

**Last Updated**: 2025-10-15
**Apply Time**: ~30 minutes for all 6 fixes
**Test Time**: ~10 minutes for verification
**Status**: Ready for immediate application

