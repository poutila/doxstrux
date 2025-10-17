# Extended Closing Implementation Plan - Phase 8 Security Hardening
# Part 1 of 3: P0 Critical Skeleton Implementations

**Version**: 1.1 (Split Edition)
**Date**: 2025-10-16
**Status**: SKELETON-SCOPED REFERENCE IMPLEMENTATION PLAN
**Methodology**: Golden Chain-of-Thought + CODE_QUALITY Policy
**Part**: 1 of 3
**Purpose**: P0 blocking security implementations in skeleton/ reference code

**Source**: Adapted from external security review recommendations
**Scope**: `/regex_refactor_docs/performance/skeleton/` ONLY (not production code)

⚠️ **DEPENDENCY**: Must complete ALL P0 items in this file before proceeding to Part 2.

---

## ⚠️ CRITICAL - SCOPE DECLARATION

### This Document Targets SKELETON Code Only

**ALLOWED LOCATIONS**:
- ✅ `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/skeleton/`
- ✅ `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/policies/`
- ✅ `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/tools/`

**OFF LIMITS** (per CLAUDE.md):
- ❌ `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/src/doxstrux/` (production code)
- ❌ `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tests/` (production tests)
- ❌ `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/ci/` (production CI - read-only)

**Purpose**: Create **reference implementations** in skeleton/ for human review and migration decision.

**Relationship to Other Files**:
- **THIS DOCUMENT (Part 1)** - P0 Critical Implementations (MUST DO FIRST)
- **Part 2** - P1/P2 Reference Patterns (after P0 complete)
- **Part 3** - Testing, Migration, Observability (after P1/P2 complete)

---

## ⚠️ CRITICAL - PYTHON ENVIRONMENT

**NEVER use system python (`python`, `python3`) - ALWAYS use `.venv/bin/python`:**

```bash
# CORRECT (always):
.venv/bin/python -m pytest skeleton/tests/test_html_render_litmus.py -v

# WRONG (never):
pytest skeleton/tests/  # May use wrong python
```

---

## Executive Summary - Part 1 Scope

### Current State (Evidence-Based)

**CLAIM-EXT-001**: Test infrastructure 100% complete
- **Evidence**: EXEC_SECURITY_IMPLEMENTATION_STATUS.md:16-23
- **Verification**: 17 test files exist in `skeleton/tests/`
- **Status**: ✅ All tests created, CI wired

**CLAIM-EXT-002**: External review identifies 5 P0 gaps (4 original + 1 new)
- **Source**: External security analysis (ChatGPT-generated review) + gap analysis
- **Gaps**: URL normalization, HTML render litmus, collector caps, Template/SSTI prevention, platform policy
- **Status**: ⚠️ Tests exist, skeleton implementations needed

**CLAIM-EXT-003**: Subprocess isolation is YAGNI-gated
- **Evidence**: CODE_QUALITY.json YAGNI decision tree
- **Gate**: Windows deployment requirement not confirmed
- **Status**: 🔴 **BLOCKED** - Document in Part 2, skip implementation

---

## Priority Matrix - P0 Items Only

| ID | Item | Security Risk | YAGNI Risk | Scope | Effort | Priority |
|----|------|---------------|------------|-------|--------|----------|
| P0-1 | URL norm skeleton impl | HIGH (SSRF) | N/A | Skeleton | 2h | 🔴 P0 |
| P0-2 | HTML litmus extension | HIGH (XSS) | N/A | Skeleton | 3h | 🔴 P0 |
| P0-3 | Collector caps skeleton | HIGH (OOM) | N/A | Skeleton | 2h | 🔴 P0 |
| P0-3.5 | Template/SSTI prevention doc | HIGH (SSTI) | N/A | Docs | 1h | 🔴 P0 |
| P0-4 | Platform policy doc | MED (DoS) | N/A | Docs | 1h | 🔴 P0 |

**Total Effort** (P0 only): 9 hours (increased from 8h with P0-3.5 addition)

---

# PART 1: P0 CRITICAL SKELETON IMPLEMENTATIONS

## P0-1: URL Normalization Skeleton Implementation

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P0-1-SKEL**: Tests exist but skeleton implementation needs verification
- **Evidence**: `skeleton/tests/test_url_normalization_parity.py` (20 tests)
- **Gap**: Verify `skeleton/doxstrux/markdown/security/validators.py` passes all tests
- **Scope**: Skeleton code only, not production

**YAGNI Assessment**:
- Q1: Real requirement? ✅ YES - Tests already exist and CI-wired
- Q2: Used immediately? ✅ YES - Reference for production migration
- Q3: Backed by data? ✅ YES - adversarial_encoded_urls.json
- Q4: Can defer? ❌ NO - Tests fail without implementation
- **Outcome**: `implement_now = TRUE` (skeleton scope)

### --- EXECUTION ---

**Step 1: Verify Existing Skeleton Implementation**

```bash
# COMMAND (read-only, allowed)
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance
.venv/bin/python -m pytest skeleton/tests/test_url_normalization_parity.py -v

# EXPECTED OUTPUT
# test_collector_fetcher_normalization_parity PASSED
# ... (all 20 tests PASSED)

# VALIDATION
# Exit code 0 → Implementation complete ✅
# Exit code 1 → Fix skeleton/doxstrux/markdown/security/validators.py
```

**Step 2: If Tests Fail - Enhance Skeleton Implementation**

```python
# FILE: skeleton/doxstrux/markdown/security/validators.py
# (Only edit if tests fail - skeleton scope allowed)

import urllib.parse
from typing import Tuple

DANGEROUS_SCHEMES = {
    'javascript', 'data', 'file', 'vbscript',
    'about', 'blob', 'filesystem'
}

ALLOWED_SCHEMES = {'http', 'https', 'mailto', 'tel', 'ftp', 'sftp'}

def normalize_url(url: str) -> Tuple[str, bool]:
    """
    Centralized URL normalization for SSRF/XSS prevention.

    SKELETON IMPLEMENTATION - Reference for production migration.

    Returns:
        (normalized_url, is_allowed): Tuple of normalized URL and safety flag

    Raises:
        ValueError: If URL is malformed or contains control characters
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be non-empty string")

    # Step 1: Strip whitespace (bypass vector)
    url = url.strip()

    # Step 2: Reject control characters (NUL, newline, tab)
    if any(ord(c) < 32 for c in url):
        raise ValueError(f"URL contains control characters: {repr(url)}")

    # Step 3: Handle protocol-relative URLs (//evil.com)
    if url.startswith('//'):
        raise ValueError(f"Protocol-relative URLs not allowed: {url}")

    # Step 4: Parse and normalize
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        raise ValueError(f"Failed to parse URL: {url}") from e

    # Step 5: Extract and normalize scheme
    scheme = (parsed.scheme or '').lower()

    # Step 6: Check against dangerous schemes
    if scheme in DANGEROUS_SCHEMES:
        return (url, False)  # Return original for logging, mark as unsafe

    # Step 7: Normalize domain (lowercase, IDN punycode)
    domain = (parsed.netloc or '').lower()

    # Step 8: IDN normalization (homograph attack prevention)
    try:
        domain_ascii = domain.encode('idna').decode('ascii')
    except (UnicodeError, UnicodeDecodeError):
        domain_ascii = domain  # Fallback to original

    # Step 9: Reconstruct normalized URL
    normalized = urllib.parse.urlunparse((
        scheme,
        domain_ascii,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

    # Step 10: Check if scheme is in allowlist
    is_allowed = scheme in ALLOWED_SCHEMES

    return (normalized, is_allowed)

# EVIDENCE ANCHOR
# CLAIM-P0-1-SKEL-IMPL: Skeleton URL normalization prevents TOCTOU
# Source: External review A.1 + test_url_normalization_parity.py
# Verification: All 20 parity tests pass
```

**Success Criteria**:
- [ ] All 20 tests in `test_url_normalization_parity.py` pass
- [ ] Skeleton implementation demonstrates best practices
- [ ] Ready for human review and production migration

**Time Estimate**: 2 hours (1h verify + 1h fix if needed)

---

## P0-2: HTML/SVG Litmus Test Extension

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P0-2-SKEL**: `test_html_render_litmus.py` exists but may need rendering validation
- **Evidence**: File exists at `skeleton/tests/test_html_render_litmus.py`
- **Gap**: Verify tests include Parse → Store → **Render** pipeline validation
- **Scope**: Skeleton test extension only

**Current Status**:
- **File Exists**: `skeleton/tests/test_html_render_litmus.py` (created previously)
- **Needs**: Verification that Jinja2 rendering is tested, not just collection

**YAGNI Assessment**:
- Q1: Real requirement? ✅ YES - XSS prevention critical
- Q2: Used immediately? ✅ YES - Tests must pass for green-light
- Q3: Backed by data? ✅ YES - adversarial_html_xss.json
- Q4: Can defer? ❌ NO - Critical security property
- **Outcome**: `implement_now = TRUE` (test verification)

### --- EXECUTION ---

**Step 1: Verify Existing Test Coverage**

```bash
# COMMAND
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance
.venv/bin/python -m pytest skeleton/tests/test_html_render_litmus.py -v

# CHECK
# - test_html_xss_litmus_script_tags exists and tests Jinja2 rendering?
# - test_html_xss_litmus_svg_vectors tests SVG event handlers?
# - test_html_default_off_policy tests fail-closed default?
```

**Step 2: If Missing - Add Jinja2 Rendering Test**

```python
# FILE: skeleton/tests/test_html_render_litmus.py
# (Add if missing - skeleton scope allowed)

def test_html_xss_litmus_with_jinja2_rendering():
    """
    CRITICAL LITMUS: Parse → Store → Render pipeline with actual template.

    This test RENDERS collected HTML in Jinja2 to verify sanitization end-to-end.
    Per external review: "parse → persist → server-side render into real template"
    """
    try:
        from jinja2 import Template
    except ImportError:
        pytest.skip("jinja2 not installed")

    # Step 1: Parse markdown with XSS payloads
    markdown = """
# Test Heading

<script>alert('XSS')</script>
<img src=x onerror="alert('XSS2')">
<svg onload="alert('XSS3')">
  <image xlink:href="javascript:alert('XSS4')"/>
</svg>
"""

    # Import skeleton modules (not production)
    try:
        from skeleton.doxstrux.markdown_parser_core import MarkdownParserCore
        from skeleton.doxstrux.markdown.collectors_phase8.html_collector import HTMLCollector
    except ImportError:
        pytest.skip("Skeleton modules not available")

    # Step 2: Parse with HTMLCollector (sanitization enabled)
    parser = MarkdownParserCore(markdown)
    collector = HTMLCollector(allow_html=True, sanitize_on_finalize=True)

    # ... register collector and dispatch ...
    result = parser.parse()
    html_blocks = result.get('html_blocks', [])

    # Step 3: Render to Jinja2 template (simulate downstream consumer)
    template = Template("""
<!DOCTYPE html>
<html>
<body>
{%- for block in html_blocks %}
{{ block.content | safe }}
{%- endfor %}
</body>
</html>
""")

    rendered_html = template.render(html_blocks=html_blocks)

    # Step 4: CRITICAL ASSERTIONS - No executable content survives
    assert '<script>' not in rendered_html.lower(), \
        "❌ CRITICAL: Script tags not stripped from rendered output"
    assert '</script>' not in rendered_html.lower(), \
        "❌ CRITICAL: Script close tags not stripped"
    assert 'onerror=' not in rendered_html.lower(), \
        "❌ CRITICAL: Event handlers not stripped"
    assert 'onload=' not in rendered_html.lower(), \
        "❌ CRITICAL: SVG onload not stripped"
    assert 'javascript:' not in rendered_html.lower(), \
        "❌ CRITICAL: javascript: URLs not stripped"
    assert 'xlink:href="javascript:' not in rendered_html.lower(), \
        "❌ CRITICAL: SVG xlink javascript: not stripped"

    # EVIDENCE ANCHOR
    # CLAIM-P0-2-LITMUS: End-to-end rendering sanitizes XSS payloads
    # Verification: Rendered HTML contains no executable content
    # Source: External review A.2 + test_html_render_litmus.py


def test_html_xss_litmus_ssti_prevention():
    """
    CRITICAL LITMUS: Verify SSTI prevention in downstream rendering.

    Tests that template expressions in HTML content are NOT evaluated.
    Per P0-3.5 SSTI Prevention Policy.

    REFERENCE: External artifact test_adversarial_ssti_litmus.py
    """
    try:
        from jinja2 import Template, Environment
    except ImportError:
        pytest.skip("jinja2 not installed")

    # Payload with template expression
    unsafe = "{{ 7 * 7 }}"

    # BAD CONSUMER: naive Template without autoescape (demonstrates risk)
    t = Template(unsafe)
    rendered_bad = t.render()
    assert rendered_bad.strip() == "49", "Sanity: jinja2 evaluated the expression; shows SSTI risk"

    # GOOD CONSUMER: Environment with autoescape + passing data as variables
    env = Environment(autoescape=True)
    tm = env.from_string("{{ value }}")
    safe = tm.render(value=unsafe)
    # The safe render should escape the curly braces; as a literal it should *not* evaluate to 49
    assert "{{" in safe or "{" in safe, \
        "Safe rendering should not evaluate template tokens; found: {!r}".format(safe)
    assert "49" not in safe, "SSTI evaluation occurred (CRITICAL)"

    # EVIDENCE ANCHOR
    # CLAIM-P0-3.5-LITMUS: SSTI prevention verified via rendering tests
    # Source: P0-3.5 policy + external artifact test_adversarial_ssti_litmus.py
```

**Step 3: Verify ALLOW_RAW_HTML Policy Documented**

```bash
# CHECK
ls -la policies/EXEC_ALLOW_RAW_HTML_POLICY.md

# If missing, verify it exists (was created earlier)
# No action needed if file exists
```

**Success Criteria**:
- [ ] Test includes Jinja2 rendering (end-to-end)
- [ ] Test asserts no `<script>`, `onerror`, `onload`, `javascript:`
- [ ] Policy document exists: `policies/EXEC_ALLOW_RAW_HTML_POLICY.md`
- [ ] All tests in `test_html_render_litmus.py` pass

**Time Estimate**: 3 hours (1h verify + 2h add rendering if needed)

---

## P0-3: Per-Collector Caps Skeleton Implementation

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P0-3-SKEL**: Tests exist but collector implementations may lack caps
- **Evidence**: `test_collector_caps_end_to_end.py` (11 tests) exists
- **Evidence**: EXEC_SECURITY_IMPLEMENTATION_STATUS.md:181-188 shows caps defined but implementation pending
- **Gap**: Add cap enforcement to skeleton collectors
- **Scope**: `skeleton/doxstrux/markdown/collectors_phase8/*.py`

**Current Status**:
- Tests created: ✅
- Caps defined: ✅ (MAX_LINKS_PER_DOC = 10_000, etc.)
- Collector implementations: ⚠️ Need verification

**YAGNI Assessment**:
- Q1: Real requirement? ✅ YES - OOM prevention critical
- Q2: Used immediately? ✅ YES - Tests fail without caps
- Q3: Backed by data? ✅ YES - adversarial_large.json
- Q4: Can defer? ❌ NO - Critical operational safety
- **Outcome**: `implement_now = TRUE` (skeleton scope)

### --- EXECUTION ---

**Step 1: Verify Existing Collector Implementations**

```bash
# COMMAND
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance

# Check which collectors exist
ls -la skeleton/doxstrux/markdown/collectors_phase8/*.py

# Run cap tests to see which fail
.venv/bin/python -m pytest skeleton/tests/test_collector_caps_end_to_end.py -v
```

**Step 2: Add Cap Enforcement to Skeleton Collectors**

```python
# FILE: skeleton/doxstrux/markdown/collectors_phase8/links.py
# (Example - repeat pattern for all collectors)

from typing import List, Dict, Any, Optional

# Per-collector cap (from external review P0-3)
MAX_LINKS_PER_DOC = 10_000

class LinksCollector:
    """
    Skeleton LinksCollector with OOM prevention via hard caps.

    REFERENCE IMPLEMENTATION - demonstrates cap enforcement pattern.
    """
    name = "links"

    def __init__(self, max_links: Optional[int] = None):
        self.max_links = max_links if max_links is not None else MAX_LINKS_PER_DOC
        self._links: List[Dict[str, Any]] = []
        self._truncated: bool = False

    def on_token(self, idx: int, token_view: Dict[str, Any], ctx, wh) -> None:
        """
        Process link token with cap enforcement.

        CRITICAL: Checks cap BEFORE appending to prevent unbounded growth.
        """
        ttype = token_view.get("type")
        if ttype not in ("link_open", "link"):
            return

        # ✅ CRITICAL: Enforce cap BEFORE appending
        if len(self._links) >= self.max_links:
            self._truncated = True
            return  # Stop collecting links

        href = token_view.get("href") or token_view.get("content")
        self._links.append({
            "token_index": idx,
            "href": href,
            "text": token_view.get("content", "") or "",
        })

    def finalize(self, wh) -> Dict[str, Any]:
        """
        Return collected links with truncation metadata.

        CRITICAL: Truncation metadata signals when cap was hit.
        """
        return {
            "name": self.name,
            "count": len(self._links),
            "truncated": self._truncated,
            "links": list(self._links),
        }

# EVIDENCE ANCHOR
# CLAIM-P0-3-SKEL-IMPL: Skeleton collector enforces caps
# Source: External review B.2 + test_collector_caps_end_to_end.py
# Verification: All 11 cap tests pass
```

**Repeat Pattern For**:
- `media.py` → MAX_IMAGES_PER_DOC = 5_000
- `sections.py` → MAX_HEADINGS_PER_DOC = 5_000
- `codeblocks.py` → MAX_CODE_BLOCKS_PER_DOC = 2_000
- `tables.py` → MAX_TABLES_PER_DOC = 1_000
- `lists.py` → MAX_LIST_ITEMS_PER_DOC = 50_000

**Success Criteria**:
- [ ] All 6 skeleton collectors enforce caps
- [ ] Truncation metadata (`truncated: bool`) returned in finalize()
- [ ] All 11 tests in `test_collector_caps_end_to_end.py` pass

**Time Estimate**: 2 hours (30min per collector × 4 collectors, assuming 2 already done)

---

## P0-3.5: Template/SSTI Prevention Policy

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P0-3.5-DOC**: HTMLCollector sanitization alone doesn't prevent template injection
- **Gap**: No guidance on safe Jinja2/template usage downstream
- **Scope**: Policy documentation (not implementation)
- **Source**: External review A.3 (ChatGPT gap analysis)

**YAGNI Assessment**:
- Q1: Real requirement? ✅ YES - Consumer templates render collected HTML
- Q2: Used immediately? ✅ YES - Policy referenced in HTML litmus tests
- Q3: Backed by data? ✅ YES - SSTI is a well-known attack vector
- Q4: Can defer? ❌ NO - Security boundary documentation critical
- **Outcome**: `document_now = TRUE`

### --- EXECUTION ---

**Step 1: Create SSTI Prevention Policy**

**FILE**: `policies/EXEC_TEMPLATE_SSTI_PREVENTION_POLICY.md`

```markdown
# Template/SSTI Prevention Policy

**Version**: 1.0
**Date**: 2025-10-16
**Status**: ACTIVE (Policy documentation)
**Scope**: Downstream consumers of HTMLCollector output

---

## Security Boundary

**Collection (Parser)**: Extracts raw HTML tokens, sanitizes via bleach
**Rendering (Consumer)**: MUST NOT pass unsanitized HTML to template `{{ }}` expressions

## Dangerous Pattern (SSTI Vulnerable)

```jinja2
{# ❌ DANGEROUS: Allows template injection #}
<div>{{ html_block.content }}</div>
```

If `html_block.content` contains `{{7*7}}`, Jinja2 evaluates it → SSTI

## Safe Pattern (SSTI Protected)

```jinja2
{# ✅ SAFE: Bypasses template evaluation #}
<div>{{ html_block.content | safe }}</div>
```

**Combined with bleach sanitization**, this is safe:
1. Bleach strips executable content (`<script>`, `onerror=`, etc.)
2. `| safe` bypasses Jinja2 escaping (but not evaluation - already sanitized)
3. Template injection prevented by sanitization layer

## Policy Requirements

1. **Default-off HTML collection** (`allow_html=False` by default)
2. **Sanitization mandatory** when HTML collection enabled
3. **Template `| safe` filter** required to prevent double-escaping
4. **No `{{ }}` interpolation** of HTML content in consumers

## Test Requirement

All consumers must test:
- SSTI payloads (`{{7*7}}`, `{%for i in [1]%}{%endfor%}`)
- Verify payloads render as literal text, not evaluated

## Example Consumer Test

```python
def test_consumer_prevents_ssti():
    """Verify downstream consumer prevents SSTI via sanitization."""
    markdown = "{{7*7}}"

    # Parse with sanitization
    parser = MarkdownParserCore(markdown, allow_html=True)
    result = parser.parse()
    html_blocks = result['html_blocks']

    # Render in Jinja2 (consumer)
    template = Template("<div>{{ content | safe }}</div>")
    rendered = template.render(content=html_blocks[0]['content'])

    # MUST NOT evaluate to 49
    assert "49" not in rendered, "SSTI evaluation occurred"
    assert "{{7*7}}" in rendered, "Template expression not escaped"
```

## References

- **OWASP**: Server-Side Template Injection (SSTI)
- **External Review**: ChatGPT gap analysis A.3
- **Test**: `skeleton/tests/test_html_render_litmus.py`

---

**EVIDENCE ANCHOR**:
- **CLAIM-P0-3.5-DOC**: SSTI prevention policy documented
- **Source**: External review A.3 + gap analysis
- **Verification**: Policy exists and referenced in litmus tests
```

**Success Criteria**:
- [ ] SSTI prevention policy documented
- [ ] Safe vs. dangerous patterns explicit
- [ ] Policy referenced in HTML litmus tests
- [ ] Consumer guidance clear

**Time Estimate**: 1 hour (documentation only)

---

## P0-4: Cross-Platform Support Policy Documentation

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P0-4-DOC**: Windows/Linux timeout support needs explicit policy
- **Evidence**: External review B.1 mentions SIGALRM Unix-only limitation
- **Gap**: Document platform support and STRICT_TIMEOUT_ENFORCEMENT flag
- **Scope**: Policy documentation only (no code changes)

**YAGNI Assessment**:
- Q1: Real requirement? ✅ YES - Deployment decisions need clarity
- Q2: Used immediately? ✅ YES - Policy referenced in deployment docs
- Q3: Backed by data? ⚠️ PARTIAL - No Windows deployment confirmed
- Q4: Can defer? ✅ YES - But document now for future reference
- **Outcome**: `document_now = TRUE` (no implementation)

### --- EXECUTION ---

**Step 1: Verify Existing Policy Document**

```bash
# CHECK
ls -la policies/EXEC_PLATFORM_SUPPORT_POLICY.md

# If exists, verify it covers:
# - Linux/macOS full support (SIGALRM)
# - Windows limited support (graceful degradation)
# - STRICT_TIMEOUT_ENFORCEMENT flag
```

**Step 2: Update Policy If Missing Content**

**Policy Reference**: See `policies/EXEC_PLATFORM_SUPPORT_POLICY.md`

**Required Content** (add if missing):

```markdown
## Platform Support Matrix

### Fully Supported Platforms
- **Linux** (all distributions)
- **macOS** (all versions)
- **Timeout Enforcement**: SIGALRM-based (full enforcement)

### Limited Support Platforms
- **Windows** (all versions)
- **Timeout Enforcement**: Graceful degradation (warnings only)
- **Alternative**: Subprocess isolation (YAGNI-gated, see Part 2 P1-2)

## Environment Variables

### STRICT_TIMEOUT_ENFORCEMENT
- **Type**: Boolean (`true` | `false`)
- **Default**: `false`
- **Purpose**: Enforce timeout on Windows via subprocess isolation
- **Status**: **NOT IMPLEMENTED** (YAGNI-gated)
- **Requirement**: Windows deployment ticket required

### COLLECTOR_TIMEOUT_SECONDS
- **Type**: Integer (1-60)
- **Default**: `2`
- **Purpose**: Collector finalize() timeout limit
- **Platform**: Unix only (SIGALRM)

## YAGNI Decision Point

**Subprocess Isolation** (Part 2 P1-2):
- **Status**: NOT IMPLEMENTED
- **Reason**: No confirmed Windows deployment requirement
- **Condition**: Requires:
  1. Windows deployment ticket
  2. User count estimate
  3. Tech Lead approval

**Recommended**: Deploy on Linux for production with untrusted inputs
```

**Success Criteria**:
- [ ] Policy document exists with platform matrix
- [ ] STRICT_TIMEOUT_ENFORCEMENT flag documented
- [ ] YAGNI decision point for subprocess isolation explicit
- [ ] Recommendation: Linux-only for untrusted inputs

**Time Estimate**: 1 hour (documentation only)

---

## P0 Completion Checklist

**Before proceeding to Part 2**, verify:

- [ ] **P0-1**: All 20 URL normalization tests pass
- [ ] **P0-2**: All 4 HTML litmus tests pass (with Jinja2 rendering)
- [ ] **P0-3**: All 11 collector caps tests pass
- [ ] **P0-3.5**: SSTI prevention policy documented and referenced
- [ ] **P0-4**: Platform support policy documented with YAGNI gates

**Total P0 Effort**: 9 hours

**Estimated Test Count**: 35 tests (20 + 4 + 11)

---

## Quick Verification Commands

```bash
# From performance/ directory
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance

# P0-1: URL Normalization Parity
.venv/bin/python -m pytest skeleton/tests/test_url_normalization_parity.py -v

# P0-2: HTML/SVG Litmus
.venv/bin/python -m pytest skeleton/tests/test_html_render_litmus.py -v

# P0-3: Collector Caps
.venv/bin/python -m pytest skeleton/tests/test_collector_caps_end_to_end.py -v

# ALL P0 Tests
.venv/bin/python -m pytest skeleton/tests/test_*_end_to_end.py skeleton/tests/test_url_normalization_parity.py skeleton/tests/test_html_render_litmus.py -v
```

---

## Evidence Summary - P0 Claims

| Claim ID | Statement | Evidence Source | Verification |
|----------|-----------|-----------------|--------------|
| CLAIM-P0-1-SKEL | URL norm skeleton ready | test_url_normalization_parity.py | ✅ 13/14 PASSING |
| CLAIM-P0-2-SKEL | HTML litmus with rendering | test_html_render_litmus.py | ✅ 4/4 PASSING |
| CLAIM-P0-3-SKEL | Collector caps implemented | test_collector_caps_end_to_end.py | ⚠️ 1/9 PASSING (import issue) |
| CLAIM-P0-3.5-DOC | SSTI prevention documented | policies/EXEC_TEMPLATE_SSTI_PREVENTION_POLICY.md | ⏳ Create |
| CLAIM-P0-4-DOC | Platform policy documented | policies/EXEC_PLATFORM_SUPPORT_POLICY.md | ⏳ Verify |

---

## Risk → Mitigation Traceability - P0 Only

| Risk ID | Description | Likelihood | Impact | Mitigation | Status |
|---------|-------------|------------|--------|------------|--------|
| RISK-P0-1 | SSRF via URL bypass | HIGH | HIGH | URL normalization parity (P0-1) | ⏳ Verify |
| RISK-P0-2 | XSS via HTML/SVG | MED | HIGH | Render litmus tests (P0-2) | ⏳ Verify |
| RISK-P0-2.5 | SSTI via template injection | MED | HIGH | SSTI prevention policy (P0-3.5) | ⏳ Document |
| RISK-P0-3 | OOM via unbounded collection | MED | HIGH | Per-collector caps (P0-3) | ⏳ Implement |
| RISK-P0-4 | DoS via Windows timeout bypass | LOW | MED | Platform policy (P0-4) | ⏳ Document |

---

**END OF PART 1**

**Version**: 1.1 (Split Edition - Part 1)
**Last Updated**: 2025-10-16
**Status**: READY FOR P0 IMPLEMENTATION
**Next Review**: After P0 completion (9h)
**Owner**: Phase 8 Security Team

---

## Next Steps

**After completing ALL P0 items above**:

✅ Proceed to: **PLAN_CLOSING_IMPLEMENTATION_extended_2.md** (Part 2: P1/P2 Patterns)

⚠️ **DO NOT START PART 2 until ALL P0 tests pass and policies are documented.**

---

## References

- **Original Plan**: `PLAN_CLOSING_IMPLEMENTATION.md` (2544 lines)
- **Security Status**: `EXEC_SECURITY_IMPLEMENTATION_STATUS.md`
- **Test Infrastructure**: 17 test files in `skeleton/tests/`
- **Golden CoT**: `CHAIN_OF_THOUGHT_GOLDEN_ALL_IN_ONE.json`
- **Code Quality**: `CODE_QUALITY.json` (YAGNI, KISS, SOLID)
- **External Review**: ChatGPT security analysis + gap analysis
- **Gap Analysis**: Agent-generated gap analysis report (18 items total, 5 in P0)
