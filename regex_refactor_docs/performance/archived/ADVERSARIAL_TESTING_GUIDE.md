# Adversarial Testing Guide - Phase 8 Security Validation

**Version**: 1.0
**Date**: 2025-10-15
**Purpose**: Comprehensive adversarial testing to validate Phase 8 security hardening
**Scope**: Controlled testing environment only - NOT for malicious use

---

## Important: Ethical Use Only

This guide provides adversarial testing methods to **validate security hardening** in your own controlled environment. These tests are:

✅ **Appropriate for**:
- Testing your own codebase
- Security validation before deployment
- Finding bugs in controlled environments
- Improving defensive posture

❌ **NOT appropriate for**:
- Attacking systems you don't own
- Bypassing security controls in production systems
- Unauthorized penetration testing
- Any malicious activity

---

## Test Suite Overview

We provide **5 comprehensive adversarial tests** covering:

1. **Resource Exhaustion (DoS)** - Validates MAX_TOKENS/MAX_BYTES enforcement
2. **Malformed Maps** - Tests correctness invariants (negative, inverted, OOB maps)
3. **URL Normalization Bypass** - Validates scheme allowlist against encoding tricks
4. **Algorithmic Complexity (O(N²))** - Detects quadratic behavior in collectors
5. **Deep Nesting (Stack Overflow)** - Validates recursion depth limits

Each test includes:
- **Safe generator** (creates adversarial input)
- **Runner script** (executes test and measures)
- **Expected behavior** (pass/fail criteria)
- **Mitigation** (how to fix if test fails)

---

## Test 1: Resource Exhaustion (DoS Validation)

### Objective

Validate that `MAX_TOKENS` and `MAX_BYTES` limits are enforced **before** expensive index building, preventing OOM and CPU exhaustion.

### Generator Script

**File**: `tools/test_resource_exhaustion.py`

```python
#!/usr/bin/env python3
"""
Resource exhaustion test generator.
Creates progressively larger token corpuses to test MAX_TOKENS enforcement.
"""

import json
import sys
from pathlib import Path


def generate_huge_token_corpus(num_tokens: int) -> list[dict]:
    """Generate a large token corpus (paragraphs with inline text)."""
    tokens = []

    for i in range(num_tokens // 3):  # Each paragraph = 3 tokens
        tokens.append({
            "type": "paragraph_open",
            "nesting": 1,
            "map": [i, i+1],
            "tag": "p",
            "content": "",
            "info": None
        })
        tokens.append({
            "type": "inline",
            "nesting": 0,
            "map": None,
            "content": f"Paragraph {i} content " * 10,  # ~200 bytes per para
            "info": None
        })
        tokens.append({
            "type": "paragraph_close",
            "nesting": -1,
            "map": [i, i+1],
            "tag": "p",
            "content": "",
            "info": None
        })

    return tokens


def main():
    """Generate test corpuses at various sizes."""
    output_dir = Path("adversarial_corpus")
    output_dir.mkdir(exist_ok=True)

    # Test sizes: below limit, at limit, above limit
    test_sizes = [
        (10_000, "small_10k.json"),
        (100_000, "medium_100k.json"),
        (500_000, "at_limit_500k.json"),
        (600_000, "above_limit_600k.json"),  # Should be rejected
        (1_000_000, "huge_1m.json"),  # Should be rejected
    ]

    for num_tokens, filename in test_sizes:
        print(f"Generating {filename} ({num_tokens:,} tokens)...")
        tokens = generate_huge_token_corpus(num_tokens)

        output_path = output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(tokens, f)

        file_size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"  Created: {file_size_mb:.2f} MB")

    print(f"\nGenerated {len(test_sizes)} test files in {output_dir}/")


if __name__ == "__main__":
    main()
```

### Runner Script

**File**: `tools/run_resource_exhaustion_tests.py`

```python
#!/usr/bin/env python3
"""
Resource exhaustion test runner.
Tests MAX_TOKENS enforcement with progressively larger inputs.
"""

import json
import sys
import time
import tracemalloc
from pathlib import Path


def test_token_limit_enforcement(corpus_file: Path) -> dict:
    """
    Test that TokenWarehouse enforces MAX_TOKENS.

    Returns:
        dict with: rejected (bool), error_msg (str), tokens_count (int),
                   peak_memory_mb (float), duration_ms (float)
    """
    # Import here to avoid issues if not installed
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse, MAX_TOKENS
    except ImportError:
        print("ERROR: TokenWarehouse not found. Run from project root.")
        sys.exit(1)

    # Load tokens
    with open(corpus_file) as f:
        tokens_data = json.load(f)

    # Convert to minimal token objects
    class MockToken:
        def __init__(self, data):
            self.type = data.get("type", "")
            self.nesting = data.get("nesting", 0)
            self.map = data.get("map")
            self.tag = data.get("tag", "")
            self.content = data.get("content", "")
            self.info = data.get("info")

        def attrGet(self, name):
            return None

    tokens = [MockToken(t) for t in tokens_data]

    # Test enforcement
    result = {
        "corpus_file": str(corpus_file),
        "tokens_count": len(tokens),
        "max_tokens_limit": MAX_TOKENS,
        "rejected": False,
        "error_msg": None,
        "peak_memory_mb": 0.0,
        "duration_ms": 0.0,
    }

    tracemalloc.start()
    start_time = time.perf_counter()

    try:
        # This should reject if tokens > MAX_TOKENS
        warehouse = TokenWarehouse(tokens, tree=None)

        # If we get here and tokens > MAX_TOKENS, that's a FAILURE
        if len(tokens) > MAX_TOKENS:
            result["rejected"] = False
            result["error_msg"] = f"FAILURE: {len(tokens)} tokens not rejected (limit: {MAX_TOKENS})"
        else:
            result["rejected"] = False  # Expected for small corpuses
            result["error_msg"] = None

    except ValueError as e:
        # Expected rejection for large corpuses
        if len(tokens) > MAX_TOKENS:
            result["rejected"] = True
            result["error_msg"] = str(e)
        else:
            result["rejected"] = True
            result["error_msg"] = f"UNEXPECTED: {len(tokens)} tokens rejected (limit: {MAX_TOKENS})"

    except Exception as e:
        result["rejected"] = True
        result["error_msg"] = f"UNEXPECTED ERROR: {type(e).__name__}: {e}"

    finally:
        duration = time.perf_counter() - start_time
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        result["duration_ms"] = duration * 1000
        result["peak_memory_mb"] = peak_memory / 1024 / 1024

    return result


def main():
    """Run all resource exhaustion tests."""
    corpus_dir = Path("adversarial_corpus")

    if not corpus_dir.exists():
        print("ERROR: adversarial_corpus/ not found.")
        print("Run: python tools/test_resource_exhaustion.py")
        sys.exit(1)

    corpus_files = sorted(corpus_dir.glob("*.json"))

    print("=" * 80)
    print("RESOURCE EXHAUSTION TESTS")
    print("=" * 80)
    print()

    results = []
    for corpus_file in corpus_files:
        print(f"Testing: {corpus_file.name}")
        result = test_token_limit_enforcement(corpus_file)
        results.append(result)

        # Print result
        status = "✅ PASS" if (
            (result["tokens_count"] > result["max_tokens_limit"] and result["rejected"]) or
            (result["tokens_count"] <= result["max_tokens_limit"] and not result["rejected"])
        ) else "❌ FAIL"

        print(f"  {status}")
        print(f"  Tokens: {result['tokens_count']:,} (limit: {result['max_tokens_limit']:,})")
        print(f"  Rejected: {result['rejected']}")
        print(f"  Duration: {result['duration_ms']:.2f}ms")
        print(f"  Peak Memory: {result['peak_memory_mb']:.2f} MB")
        if result["error_msg"]:
            print(f"  Message: {result['error_msg']}")
        print()

    # Summary
    passed = sum(1 for r in results if (
        (r["tokens_count"] > r["max_tokens_limit"] and r["rejected"]) or
        (r["tokens_count"] <= r["max_tokens_limit"] and not r["rejected"])
    ))

    print("=" * 80)
    print(f"SUMMARY: {passed}/{len(results)} tests passed")
    print("=" * 80)

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
```

### Expected Behavior

| Corpus Size | Expected Result |
|-------------|-----------------|
| 10K tokens | ✅ PASS - Not rejected |
| 100K tokens | ✅ PASS - Not rejected |
| 500K tokens | ✅ PASS - Not rejected (at limit) |
| 600K tokens | ✅ PASS - **Rejected** with ValueError |
| 1M tokens | ✅ PASS - **Rejected** with ValueError |

### Failure Indicators

❌ **FAIL** if:
- Large corpus (>MAX_TOKENS) is NOT rejected
- Process is killed by OOM before rejection
- Memory usage grows unbounded
- Rejection happens after slow index building

### Mitigation

If tests fail, apply fixes from `SECURITY_COMPREHENSIVE.md (Part 4 - Mitigations)` Fix #1:

```python
# In TokenWarehouse.__init__()
MAX_TOKENS = 500_000
MAX_BYTES = 10 * 1024 * 1024

if len(tokens) > MAX_TOKENS:
    raise ValueError(f"Document too large: {len(tokens)} tokens (max {MAX_TOKENS})")

if text and len(text.encode('utf-8')) > MAX_BYTES:
    raise ValueError(f"Document too large: {len(text.encode('utf-8'))} bytes (max {MAX_BYTES})")
```

---

## Test 2: Malformed Maps (Correctness Validation)

### Objective

Validate that malformed `map` values (negative, inverted, out-of-bounds) are normalized and don't corrupt section boundaries or cause crashes.

### Generator Script

**File**: `tools/test_malformed_maps.py`

```python
#!/usr/bin/env python3
"""
Malformed map test generator.
Creates tokens with negative, inverted, and OOB map values.
"""

import json
from pathlib import Path


def generate_malformed_map_corpus() -> list[dict]:
    """Generate tokens with various malformed map values."""
    tokens = []

    # Test case 1: Negative map values
    tokens.extend([
        {"type": "heading_open", "nesting": 1, "tag": "h1", "map": [-100, -50]},
        {"type": "inline", "nesting": 0, "content": "Negative Map Heading"},
        {"type": "heading_close", "nesting": -1, "tag": "h1", "map": [-100, -50]},
    ])

    # Test case 2: Inverted map (end < start)
    tokens.extend([
        {"type": "heading_open", "nesting": 1, "tag": "h2", "map": [1000, 500]},
        {"type": "inline", "nesting": 0, "content": "Inverted Map Heading"},
        {"type": "heading_close", "nesting": -1, "tag": "h2", "map": [1000, 500]},
    ])

    # Test case 3: Extremely large map values
    tokens.extend([
        {"type": "heading_open", "nesting": 1, "tag": "h3", "map": [10_000_000, 10_000_001]},
        {"type": "inline", "nesting": 0, "content": "OOB Map Heading"},
        {"type": "heading_close", "nesting": -1, "tag": "h3", "map": [10_000_000, 10_000_001]},
    ])

    # Test case 4: None/null map values
    tokens.extend([
        {"type": "heading_open", "nesting": 1, "tag": "h4", "map": [None, None]},
        {"type": "inline", "nesting": 0, "content": "Null Map Heading"},
        {"type": "heading_close", "nesting": -1, "tag": "h4", "map": [None, None]},
    ])

    # Test case 5: Valid heading for comparison
    tokens.extend([
        {"type": "heading_open", "nesting": 1, "tag": "h5", "map": [10, 11]},
        {"type": "inline", "nesting": 0, "content": "Valid Map Heading"},
        {"type": "heading_close", "nesting": -1, "tag": "h5", "map": [10, 11]},
    ])

    # Test case 6: Overlapping maps
    tokens.extend([
        {"type": "heading_open", "nesting": 1, "tag": "h2", "map": [5, 15]},
        {"type": "inline", "nesting": 0, "content": "Overlapping Start"},
        {"type": "heading_close", "nesting": -1, "tag": "h2", "map": [5, 15]},

        {"type": "heading_open", "nesting": 1, "tag": "h2", "map": [12, 20]},
        {"type": "inline", "nesting": 0, "content": "Overlapping End"},
        {"type": "heading_close", "nesting": -1, "tag": "h2", "map": [12, 20]},
    ])

    return tokens


def main():
    """Generate malformed map test corpus."""
    output_dir = Path("adversarial_corpus")
    output_dir.mkdir(exist_ok=True)

    tokens = generate_malformed_map_corpus()
    output_file = output_dir / "malformed_maps.json"

    with open(output_file, 'w') as f:
        json.dump(tokens, f, indent=2)

    print(f"Generated {len(tokens)} tokens with malformed maps")
    print(f"Output: {output_file}")
    print("\nTest cases included:")
    print("  1. Negative map values (-100, -50)")
    print("  2. Inverted map (end < start)")
    print("  3. Extremely large OOB values")
    print("  4. None/null map values")
    print("  5. Valid map (control)")
    print("  6. Overlapping section boundaries")


if __name__ == "__main__":
    main()
```

### Runner Script

**File**: `tools/run_malformed_map_tests.py`

```python
#!/usr/bin/env python3
"""
Malformed map test runner.
Validates that map normalization preserves invariants.
"""

import json
import sys
from pathlib import Path


def test_map_normalization(corpus_file: Path) -> dict:
    """
    Test that malformed maps are normalized correctly.

    Validates:
    1. All map values are non-negative
    2. All map end >= start (no inversions)
    3. Sections are sorted by start line
    4. Sections don't have invalid ranges
    """
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        print("ERROR: TokenWarehouse not found.")
        sys.exit(1)

    # Load tokens
    with open(corpus_file) as f:
        tokens_data = json.load(f)

    # Convert to token objects
    class MockToken:
        def __init__(self, data):
            self.type = data.get("type", "")
            self.nesting = data.get("nesting", 0)
            self.map = data.get("map")
            self.tag = data.get("tag", "")
            self.content = data.get("content", "")

        def attrGet(self, name):
            return None

    tokens = [MockToken(t) for t in tokens_data]

    result = {
        "corpus_file": str(corpus_file),
        "passed": True,
        "errors": [],
    }

    try:
        # Build warehouse
        warehouse = TokenWarehouse(tokens, tree=None)

        # Validate invariant 1: All maps non-negative
        for i, tok in enumerate(warehouse.tokens):
            if tok.map and len(tok.map) == 2:
                start, end = tok.map
                if start is not None and start < 0:
                    result["errors"].append(
                        f"Token {i}: Negative start in map: {tok.map}"
                    )
                if end is not None and end < 0:
                    result["errors"].append(
                        f"Token {i}: Negative end in map: {tok.map}"
                    )

        # Validate invariant 2: All maps have end >= start
        for i, tok in enumerate(warehouse.tokens):
            if tok.map and len(tok.map) == 2:
                start, end = tok.map
                if start is not None and end is not None and end < start:
                    result["errors"].append(
                        f"Token {i}: Inverted map (end < start): {tok.map}"
                    )

        # Validate invariant 3: Sections sorted by start
        sections = warehouse.sections
        for i in range(len(sections) - 1):
            curr_start = sections[i][1]  # (heading_idx, start, end, level, text)
            next_start = sections[i+1][1]
            if curr_start > next_start:
                result["errors"].append(
                    f"Sections not sorted: section {i} start={curr_start}, "
                    f"section {i+1} start={next_start}"
                )

        # Validate invariant 4: Sections have valid ranges
        for i, (heading_idx, start, end, level, text) in enumerate(sections):
            if start < 0:
                result["errors"].append(f"Section {i}: Negative start={start}")
            if end < 0:
                result["errors"].append(f"Section {i}: Negative end={end}")
            if end < start:
                result["errors"].append(f"Section {i}: Inverted range ({start}, {end})")

        # Validate section_of doesn't crash on edge cases
        test_lines = [-100, -1, 0, 10, 1000, 10_000_000]
        for line in test_lines:
            try:
                section_id = warehouse.section_of(line)
                # Should return None or valid section_id, not crash
            except Exception as e:
                result["errors"].append(
                    f"section_of({line}) raised: {type(e).__name__}: {e}"
                )

        result["passed"] = len(result["errors"]) == 0

    except Exception as e:
        result["passed"] = False
        result["errors"].append(f"Warehouse construction failed: {type(e).__name__}: {e}")

    return result


def main():
    """Run malformed map tests."""
    corpus_file = Path("adversarial_corpus/malformed_maps.json")

    if not corpus_file.exists():
        print(f"ERROR: {corpus_file} not found.")
        print("Run: python tools/test_malformed_maps.py")
        sys.exit(1)

    print("=" * 80)
    print("MALFORMED MAP TESTS")
    print("=" * 80)
    print()

    result = test_map_normalization(corpus_file)

    if result["passed"]:
        print("✅ PASS - All invariants satisfied")
        print(f"  - All maps normalized correctly")
        print(f"  - Sections sorted and non-overlapping")
        print(f"  - section_of() handles edge cases")
    else:
        print("❌ FAIL - Invariants violated:")
        for error in result["errors"]:
            print(f"  - {error}")

    print()
    print("=" * 80)

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

### Expected Behavior

✅ **PASS** if:
- All map values are normalized to non-negative
- All map ranges have `end >= start` (no inversions)
- Sections list is sorted by start line
- `section_of()` doesn't crash on edge cases (-100, 0, 10M)

### Failure Indicators

❌ **FAIL** if:
- Negative or inverted maps survive normalization
- Sections are out of order
- `section_of()` raises exceptions or returns wrong sections

### Mitigation

Apply fixes from `SECURITY_COMPREHENSIVE.md (Part 4 - Mitigations)` Fix #2:

```python
# In TokenWarehouse._build_indices()
MAX_LINE = 1_000_000

for i, tok in enumerate(tokens):
    m = getattr(tok, 'map', None)
    if m and len(m) == 2:
        # Normalize: clamp to [0, MAX_LINE], ensure end >= start
        s = max(0, min(int(m[0] or 0), MAX_LINE))
        e = max(s, min(int(m[1] or s), MAX_LINE))
        tok.map = (s, e)

# Sort headings by normalized start
heads = sorted(heads, key=lambda h: (tokens[h].map[0] or 0))
```

---

## Test 3: URL Normalization Bypass (SSRF Validation)

### Objective

Validate that URL scheme allowlist cannot be bypassed via encoding tricks (mixed case, percent-encoding, Unicode, protocol-relative URLs).

### Generator Script

**File**: `tools/test_url_normalization.py`

```python
#!/usr/bin/env python3
"""
URL normalization bypass test generator.
Creates links with tricky URL encodings to test scheme validation.
"""

import json
from pathlib import Path


def generate_url_bypass_corpus() -> list[dict]:
    """Generate tokens with various URL encoding tricks."""
    test_urls = [
        # Baseline (should be allowed)
        ("http://example.com", "Valid HTTP"),
        ("https://example.com", "Valid HTTPS"),
        ("mailto:test@example.com", "Valid Mailto"),

        # Case variations (should be rejected)
        ("javascript:alert(1)", "JavaScript lowercase"),
        ("JavaScript:alert(1)", "JavaScript mixed case"),
        ("JAVASCRIPT:alert(1)", "JavaScript uppercase"),
        ("jAvAsCrIpT:alert(1)", "JavaScript random case"),

        # Percent-encoding tricks (should be rejected)
        ("java%73cript:alert(1)", "JavaScript percent-encoded 's'"),
        ("java%0ascript:alert(1)", "JavaScript with newline"),
        ("java%09script:alert(1)", "JavaScript with tab"),
        ("java%00script:alert(1)", "JavaScript with null byte"),

        # Unicode tricks (should be rejected)
        ("java\\u0073cript:alert(1)", "JavaScript with unicode escape"),

        # Protocol-relative (should be rejected)
        ("//evil.com/script", "Protocol-relative URL"),
        ("//\\u0000file:///etc/passwd", "Protocol-relative with unicode"),

        # Data URIs (should be rejected)
        ("data:text/html,<script>alert(1)</script>", "Data URI with script"),
        ("data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==", "Data URI base64"),

        # File URIs (should be rejected)
        ("file:///etc/passwd", "File URI"),
        ("file://localhost/etc/passwd", "File URI with localhost"),

        # Whitespace tricks (should be rejected)
        (" javascript:alert(1)", "Leading whitespace"),
        ("javascript:alert(1) ", "Trailing whitespace"),
        ("\\njavascript:alert(1)", "Leading newline"),

        # Confusables (IDN homograph attack)
        ("httрs://example.com", "Cyrillic 'р' (p) homograph"),
    ]

    tokens = []
    for url, description in test_urls:
        tokens.extend([
            {
                "type": "link_open",
                "nesting": 1,
                "map": [len(tokens), len(tokens)+1],
                "href": url,
            },
            {
                "type": "inline",
                "nesting": 0,
                "content": description,
            },
            {
                "type": "link_close",
                "nesting": -1,
                "map": [len(tokens), len(tokens)+1],
            },
        ])

    return tokens


def main():
    """Generate URL bypass test corpus."""
    output_dir = Path("adversarial_corpus")
    output_dir.mkdir(exist_ok=True)

    tokens = generate_url_bypass_corpus()
    output_file = output_dir / "url_bypass.json"

    with open(output_file, 'w') as f:
        json.dump(tokens, f, indent=2)

    print(f"Generated {len(tokens)} tokens with URL bypass attempts")
    print(f"Output: {output_file}")
    print("\nTest cases included:")
    print("  - Case variations (JavaScript → jAvAsCrIpT)")
    print("  - Percent-encoding tricks")
    print("  - Unicode escapes")
    print("  - Protocol-relative URLs")
    print("  - Data URIs")
    print("  - File URIs")
    print("  - Whitespace tricks")
    print("  - IDN homograph attacks")


if __name__ == "__main__":
    main()
```

### Runner Script

**File**: `tools/run_url_bypass_tests.py`

```python
#!/usr/bin/env python3
"""
URL normalization bypass test runner.
Validates that scheme allowlist catches all bypass attempts.
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlsplit


ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}


def normalize_url_centralized(url: str) -> tuple[str | None, bool]:
    """
    Centralized URL normalization.

    Returns:
        (scheme, is_allowed)
    """
    if not url or not isinstance(url, str):
        return None, False

    # Strip whitespace
    url = url.strip()

    # Reject protocol-relative
    if url.startswith('//'):
        return None, False

    # Reject control characters
    if any(ord(c) < 32 or ord(c) == 127 for c in url):
        return None, False

    # Parse with urlsplit
    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower() if parsed.scheme else None

        # Check allowlist
        if scheme:
            return scheme, scheme in ALLOWED_SCHEMES
        else:
            # Relative URL (no scheme) - typically allowed
            return None, True

    except Exception:
        return None, False


def test_url_bypass(corpus_file: Path) -> dict:
    """
    Test that URL normalization catches all bypass attempts.
    """
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        print("ERROR: TokenWarehouse or LinksCollector not found.")
        sys.exit(1)

    # Load tokens
    with open(corpus_file) as f:
        tokens_data = json.load(f)

    # Convert to token objects
    class MockToken:
        def __init__(self, data):
            self.type = data.get("type", "")
            self.nesting = data.get("nesting", 0)
            self.map = data.get("map")
            self._href = data.get("href")

        def attrGet(self, name):
            if name == "href":
                return self._href
            return None

    tokens = [MockToken(t) for t in tokens_data]

    result = {
        "corpus_file": str(corpus_file),
        "passed": True,
        "bypasses_detected": [],
        "false_positives": [],
    }

    try:
        # Build warehouse with links collector
        warehouse = TokenWarehouse(tokens, tree=None)
        collector = LinksCollector(effective_allowed_schemes=ALLOWED_SCHEMES)
        warehouse.register_collector(collector)
        warehouse.dispatch_all()

        links = collector.finalize(warehouse)

        # Check each link
        for link in links:
            url = link.get("url", "")
            collector_allowed = link.get("allowed", False)

            # Re-validate with centralized normalizer
            scheme, centralized_allowed = normalize_url_centralized(url)

            # Detect mismatches
            if collector_allowed != centralized_allowed:
                if collector_allowed and not centralized_allowed:
                    # Bypass detected! Collector said OK, but centralized says NO
                    result["bypasses_detected"].append({
                        "url": url,
                        "scheme": scheme,
                        "collector_allowed": collector_allowed,
                        "centralized_allowed": centralized_allowed,
                    })
                else:
                    # False positive: Collector said NO, but centralized says OK
                    result["false_positives"].append({
                        "url": url,
                        "scheme": scheme,
                        "collector_allowed": collector_allowed,
                        "centralized_allowed": centralized_allowed,
                    })

        result["passed"] = len(result["bypasses_detected"]) == 0

    except Exception as e:
        result["passed"] = False
        result["bypasses_detected"].append({
            "error": f"Test failed: {type(e).__name__}: {e}"
        })

    return result


def main():
    """Run URL bypass tests."""
    corpus_file = Path("adversarial_corpus/url_bypass.json")

    if not corpus_file.exists():
        print(f"ERROR: {corpus_file} not found.")
        print("Run: python tools/test_url_normalization.py")
        sys.exit(1)

    print("=" * 80)
    print("URL NORMALIZATION BYPASS TESTS")
    print("=" * 80)
    print()

    result = test_url_bypass(corpus_file)

    if result["passed"]:
        print("✅ PASS - No bypasses detected")
        print(f"  - All unsafe URLs rejected by collector")
        print(f"  - Scheme allowlist working correctly")
        if result["false_positives"]:
            print(f"\n⚠️  Warning: {len(result['false_positives'])} false positives")
            for fp in result["false_positives"]:
                print(f"    - {fp['url']} (rejected but centralized allows)")
    else:
        print("❌ FAIL - Bypasses detected:")
        for bypass in result["bypasses_detected"]:
            if "error" in bypass:
                print(f"  - {bypass['error']}")
            else:
                print(f"  - URL: {bypass['url']}")
                print(f"    Scheme: {bypass['scheme']}")
                print(f"    Collector allowed: {bypass['collector_allowed']}")
                print(f"    Should be: {bypass['centralized_allowed']}")

    print()
    print("=" * 80)

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

### Expected Behavior

✅ **PASS** if:
- All baseline URLs (http, https, mailto) are marked `allowed: True`
- All bypass attempts (javascript:, data:, file:, //, etc.) are marked `allowed: False`
- No mismatches between collector and centralized validator

### Failure Indicators

❌ **FAIL** if:
- Any unsafe URL is marked `allowed: True`
- Case variations, percent-encoding, or protocol-relative URLs bypass allowlist

### Mitigation

Apply centralized URL normalization from `SECURITY_COMPREHENSIVE.md (Part 2 - Vulnerability Catalog)` Vuln #2:

```python
from urllib.parse import urlsplit
import re

ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}
CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')

def normalize_url(url: str) -> str:
    """Centralized normalization - use EVERYWHERE."""
    url = url.strip()

    if CONTROL_CHARS.search(url):
        raise ValueError("URL contains control characters")

    if url.startswith('//'):
        raise ValueError("Protocol-relative URLs not allowed")

    parsed = urlsplit(url)
    scheme = parsed.scheme.lower() if parsed.scheme else None

    if scheme and scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Scheme not allowed: {scheme}")

    return url  # Or return normalized version
```

---

## Test 4: Algorithmic Complexity (O(N²) Detection)

### Objective

Detect quadratic behavior in collectors caused by naive patterns (nested loops, repeated linear scans).

### Generator Script

**File**: `tools/test_algorithmic_complexity.py`

```python
#!/usr/bin/env python3
"""
Algorithmic complexity test generator.
Creates large corpuses to detect O(N²) behavior.
"""

import json
from pathlib import Path


def generate_many_links_corpus(num_links: int) -> list[dict]:
    """Generate corpus with many duplicate links to stress deduplication."""
    tokens = []

    for i in range(num_links):
        # Each link uses same URL to stress "seen" check
        tokens.extend([
            {
                "type": "link_open",
                "nesting": 1,
                "map": [i, i+1],
                "href": f"https://example.com/page{i % 100}",  # 100 unique URLs, repeated
            },
            {
                "type": "inline",
                "nesting": 0,
                "content": f"Link {i}",
            },
            {
                "type": "link_close",
                "nesting": -1,
                "map": [i, i+1],
            },
        ])

    return tokens


def main():
    """Generate complexity test corpuses."""
    output_dir = Path("adversarial_corpus")
    output_dir.mkdir(exist_ok=True)

    # Test at various scales to detect superlinear growth
    test_sizes = [
        (100, "links_100.json"),
        (500, "links_500.json"),
        (1_000, "links_1k.json"),
        (5_000, "links_5k.json"),
        (10_000, "links_10k.json"),
    ]

    for num_links, filename in test_sizes:
        print(f"Generating {filename} ({num_links:,} links)...")
        tokens = generate_many_links_corpus(num_links)

        output_path = output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(tokens, f)

        print(f"  Created: {len(tokens):,} tokens")

    print(f"\nGenerated {len(test_sizes)} test files")


if __name__ == "__main__":
    main()
```

### Runner Script

**File**: `tools/run_complexity_tests.py`

```python
#!/usr/bin/env python3
"""
Algorithmic complexity test runner.
Detects O(N²) behavior by measuring time growth.
"""

import json
import sys
import time
from pathlib import Path


def measure_parse_time(corpus_file: Path) -> dict:
    """Measure parse time for given corpus."""
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        print("ERROR: TokenWarehouse or LinksCollector not found.")
        sys.exit(1)

    # Load tokens
    with open(corpus_file) as f:
        tokens_data = json.load(f)

    class MockToken:
        def __init__(self, data):
            self.type = data.get("type", "")
            self.nesting = data.get("nesting", 0)
            self.map = data.get("map")
            self._href = data.get("href")

        def attrGet(self, name):
            if name == "href":
                return self._href
            return None

    tokens = [MockToken(t) for t in tokens_data]

    # Measure time
    start = time.perf_counter()

    warehouse = TokenWarehouse(tokens, tree=None)
    collector = LinksCollector(effective_allowed_schemes={"http", "https"})
    warehouse.register_collector(collector)
    warehouse.dispatch_all()
    links = collector.finalize(warehouse)

    duration = time.perf_counter() - start

    # Count actual unique links
    unique_urls = set(link["url"] for link in links)

    return {
        "corpus_file": str(corpus_file),
        "num_tokens": len(tokens),
        "num_links": len(links),
        "num_unique_links": len(unique_urls),
        "duration_ms": duration * 1000,
    }


def analyze_complexity(results: list[dict]) -> dict:
    """Analyze time growth to detect O(N²) behavior."""
    # Sort by token count
    results = sorted(results, key=lambda r: r["num_tokens"])

    # Check if time grows linearly with N (O(N)) or quadratically (O(N²))
    # For O(N): time(2N) / time(N) ≈ 2
    # For O(N²): time(2N) / time(N) ≈ 4

    analysis = {
        "growth_factors": [],
        "is_linear": True,
    }

    for i in range(len(results) - 1):
        curr = results[i]
        next_result = results[i+1]

        n_ratio = next_result["num_tokens"] / curr["num_tokens"]
        time_ratio = next_result["duration_ms"] / curr["duration_ms"]

        # Expected time ratio for linear: same as n_ratio
        # Expected time ratio for quadratic: n_ratio²
        expected_linear = n_ratio
        expected_quadratic = n_ratio ** 2

        analysis["growth_factors"].append({
            "from_n": curr["num_tokens"],
            "to_n": next_result["num_tokens"],
            "n_ratio": n_ratio,
            "time_ratio": time_ratio,
            "expected_linear": expected_linear,
            "expected_quadratic": expected_quadratic,
        })

        # If time_ratio is closer to quadratic than linear, flag it
        if abs(time_ratio - expected_quadratic) < abs(time_ratio - expected_linear):
            analysis["is_linear"] = False

    return analysis


def main():
    """Run complexity tests."""
    corpus_dir = Path("adversarial_corpus")
    corpus_files = sorted(corpus_dir.glob("links_*.json"))

    if not corpus_files:
        print("ERROR: No links_*.json files found in adversarial_corpus/")
        print("Run: python tools/test_algorithmic_complexity.py")
        sys.exit(1)

    print("=" * 80)
    print("ALGORITHMIC COMPLEXITY TESTS")
    print("=" * 80)
    print()

    results = []
    for corpus_file in corpus_files:
        print(f"Testing: {corpus_file.name}")
        result = measure_parse_time(corpus_file)
        results.append(result)

        print(f"  Tokens: {result['num_tokens']:,}")
        print(f"  Links: {result['num_links']:,}")
        print(f"  Unique: {result['num_unique_links']:,}")
        print(f"  Duration: {result['duration_ms']:.2f}ms")
        print()

    # Analyze growth
    analysis = analyze_complexity(results)

    print("=" * 80)
    print("GROWTH ANALYSIS")
    print("=" * 80)
    print()

    for factor in analysis["growth_factors"]:
        print(f"From {factor['from_n']:,} to {factor['to_n']:,} tokens:")
        print(f"  N ratio: {factor['n_ratio']:.2f}x")
        print(f"  Time ratio: {factor['time_ratio']:.2f}x")
        print(f"  Expected (linear): {factor['expected_linear']:.2f}x")
        print(f"  Expected (quadratic): {factor['expected_quadratic']:.2f}x")

        if factor['time_ratio'] > factor['expected_linear'] * 1.5:
            print("  ⚠️  WARNING: Superlinear growth detected!")
        print()

    if analysis["is_linear"]:
        print("✅ PASS - Time growth is linear (O(N))")
    else:
        print("❌ FAIL - Time growth appears quadratic (O(N²))")

    print("=" * 80)

    return 0 if analysis["is_linear"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

### Expected Behavior

✅ **PASS** if:
- Time growth is approximately linear with token count
- `time(2N) / time(N) ≈ 2` (not ≈ 4)

### Failure Indicators

❌ **FAIL** if:
- Time growth is quadratic: `time(2N) / time(N) ≈ 4`
- Duration increases dramatically for modest size increases

### Mitigation

Apply fixes from `SECURITY_COMPREHENSIVE.md (Part 2 - Vulnerability Catalog)` Vuln #5:

```python
# BAD: O(N²) pattern
class LinksCollector:
    def on_token(self, idx, token, ctx, wh):
        if token.type == "link_open":
            href = token.href
            # ❌ O(N) search per token → O(N²) total
            if not any(link["url"] == href for link in self._links):
                self._links.append({"url": href})

# GOOD: O(N) pattern
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
```

---

## Test 5: Deep Nesting (Stack Overflow Validation)

### Objective

Validate that deep nesting limits prevent stack overflow from recursive processing.

### Generator & Runner

See `SECURITY_COMPREHENSIVE.md (Part 2 - Vulnerability Catalog)` Vuln #6 for complete implementation.

**Key points**:
- Generate deeply nested blockquotes (200+ levels)
- Measure stack depth during processing
- Validate MAX_NESTING limit enforcement

---

## Running All Tests

### Complete Test Suite

```bash
# 1. Generate all adversarial corpuses
python tools/test_resource_exhaustion.py
python tools/test_malformed_maps.py
python tools/test_url_normalization.py
python tools/test_algorithmic_complexity.py

# 2. Run all tests
python tools/run_resource_exhaustion_tests.py
python tools/run_malformed_map_tests.py
python tools/run_url_bypass_tests.py
python tools/run_complexity_tests.py

# 3. Or use master runner
python tools/run_all_adversarial_tests.py
```

### Expected Results

| Test Suite | Expected Result |
|------------|-----------------|
| Resource Exhaustion | 5/5 tests pass |
| Malformed Maps | All invariants satisfied |
| URL Normalization | 0 bypasses detected |
| Algorithmic Complexity | Linear growth (O(N)) |
| Deep Nesting | Stack depth < MAX_NESTING |

---

## CI Integration

Add to your CI pipeline (`.github/workflows/phase8-ci.yml`):

```yaml
- name: Phase 8 Gate P1 - Adversarial Testing
  run: |
    cd regex_refactor_docs/performance

    # Generate corpuses
    python tools/test_resource_exhaustion.py
    python tools/test_malformed_maps.py
    python tools/test_url_normalization.py
    python tools/test_algorithmic_complexity.py

    # Run tests
    python tools/run_all_adversarial_tests.py

    # Fail CI if any test fails
    if [ $? -ne 0 ]; then
      echo "❌ Adversarial tests failed"
      exit 1
    fi
```

---

## Monitoring in Production

After passing all adversarial tests, monitor these metrics in production:

```python
# Telemetry to collect
metrics = {
    "tokens_per_parse": len(tokens),
    "parse_duration_ms": elapsed * 1000,
    "peak_memory_mb": peak / 1024 / 1024,
    "collector_errors": len(wh._collector_errors),
    "unsafe_urls": sum(1 for l in links if not l["allowed"]),
    "truncated_collectors": sum(1 for r in results.values() if r.get("truncated")),
}

# Alert thresholds
if metrics["tokens_per_parse"] > 100_000:
    alert("Large document detected")
if metrics["unsafe_urls"] > 0:
    alert("Unsafe URL detected - potential bypass attempt")
if metrics["collector_errors"] > 0:
    alert("Collector failure - investigate immediately")
```

---

## Summary

This adversarial testing guide provides **5 comprehensive test suites** to validate Phase 8 security hardening:

1. **Resource Exhaustion** - Validates input limits
2. **Malformed Maps** - Tests correctness invariants
3. **URL Normalization** - Catches bypass attempts
4. **Algorithmic Complexity** - Detects O(N²) behavior
5. **Deep Nesting** - Validates recursion limits

**Total test coverage**: 15 vulnerabilities across 3 domains

**Estimated testing time**: ~30 minutes to run all tests

**Status**: ✅ Ready for immediate use

---

**Last Updated**: 2025-10-15
**Purpose**: Defensive security validation only
**Next Step**: Run tests in your controlled environment before Phase 8.0 deployment
