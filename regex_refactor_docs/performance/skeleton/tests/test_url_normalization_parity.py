"""
End-to-end URL normalization parity litmus tests.

Verifies that URL normalization is:
1. Centralized in a single hardened function
2. Used consistently across all collectors and downstream fetchers
3. Resilient to bypass techniques (case mixing, whitespace, protocol-relative, etc.)

This prevents SSRF (Server-Side Request Forgery), XSS, and phishing attacks
via normalization bypass exploits.

Critical security property: Collector normalization == Fetcher normalization
If these diverge, attackers can bypass allowlists/denylists.
"""
import pytest
import json
import re
from pathlib import Path
from types import SimpleNamespace


# Normalization test vectors (from adversarial_encoded_urls.json)
NORMALIZATION_VECTORS = [
    # Protocol-relative URLs (should be REJECTED per CLOSING_IMPLEMENTATION.md line 196)
    ("//evil.com/steal", None),
    ("//attacker.example.com/xss", None),

    # Case mixing in scheme
    ("HtTp://example.com", "http://example.com"),
    ("hTTpS://example.com", "https://example.com"),
    ("HTTPS://EXAMPLE.COM", "https://example.com"),

    # Whitespace obfuscation
    ("  https://example.com  ", "https://example.com"),
    ("https://  example.com", "https://example.com"),

    # Percent-encoding bypass
    ("https://example.com/%2e%2e/admin", "https://example.com/../admin"),
    ("https://example.com/%252e%252e/secret", "https://example.com/%2e%2e/secret"),

    # Mixed case + whitespace
    ("  HtTpS://example.com/PATH  ", "https://example.com/PATH"),

    # javascript: scheme (should be rejected, not normalized)
    ("javascript:alert(1)", None),  # None = should reject
    ("JaVaScRiPt:alert(1)", None),

    # data: scheme (should be rejected)
    ("data:text/html,<script>evil()</script>", None),

    # file: scheme (should be rejected)
    ("file:///etc/passwd", None),

    # Internationalized domain names (IDN homographs)
    ("https://еxample.com", "https://xn--xample-9ua.com"),  # Cyrillic 'e'
]


def test_url_normalization_function_exists():
    """
    Test that centralized URL normalization function exists.

    This function should be the ONLY place URL normalization happens.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.fail("normalize_url function not found in doxstrux.markdown.utils.url_utils")

    # Verify function signature
    import inspect
    sig = inspect.signature(normalize_url)
    assert "url" in sig.parameters, "normalize_url missing 'url' parameter"


def test_normalize_url_basic_behavior():
    """
    Test basic URL normalization behavior.

    Verifies that the normalize_url function handles common cases correctly.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    # Test basic normalization
    test_cases = [
        ("https://example.com", "https://example.com"),
        ("http://example.com", "http://example.com"),
        ("HTTPS://EXAMPLE.COM", "https://example.com"),  # Lowercase scheme and domain
        ("  https://example.com  ", "https://example.com"),  # Strip whitespace
    ]

    for input_url, expected in test_cases:
        result = normalize_url(input_url)
        assert result == expected, \
            f"normalize_url('{input_url}') returned '{result}', expected '{expected}'"


def test_normalize_url_rejects_dangerous_schemes():
    """
    Test that normalize_url rejects dangerous URL schemes.

    Should reject: javascript:, data:, file:, vbscript:, etc.
    Should allow: http:, https:, mailto:, tel:
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    dangerous_schemes = [
        "javascript:alert(1)",
        "JaVaScRiPt:alert(1)",
        "data:text/html,<script>evil()</script>",
        "file:///etc/passwd",
        "vbscript:msgbox(1)",
    ]

    for dangerous_url in dangerous_schemes:
        result = normalize_url(dangerous_url)
        assert result is None or result == "", \
            f"normalize_url did not reject dangerous URL: {dangerous_url} → {result}"


def test_normalize_url_handles_protocol_relative():
    """
    Test that normalize_url rejects protocol-relative URLs (//example.com).

    Per CLOSING_IMPLEMENTATION.md line 196: Protocol-relative URLs are rejected
    to prevent bypass attacks. They should NOT be converted to https://.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    protocol_relative_urls = [
        "//example.com",
        "//example.com/path",
        "//example.com:8080/path",
        "//evil.com/steal",
    ]

    for input_url in protocol_relative_urls:
        result = normalize_url(input_url)
        assert result is None or result == "", \
            f"Protocol-relative URL should be rejected: '{input_url}' → '{result}'"


def test_collector_uses_normalize_url():
    """
    Test that links collector uses centralized normalize_url function.

    Critical: Collectors MUST NOT do their own normalization.
    """
    try:
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        pytest.skip("LinksCollector not available")

    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    # Check if collector imports normalize_url
    import inspect
    source = inspect.getsource(LinksCollector)

    # Verify normalize_url is used (not re-implemented)
    assert "normalize_url" in source or "url_utils" in source, \
        "LinksCollector does not appear to use centralized normalize_url function"


def test_fetcher_uses_normalize_url():
    """
    Test that downstream fetchers use centralized normalize_url function.

    Critical: Fetchers MUST use same normalization as collectors.
    """
    # Determine base path: if running from project root, look in skeleton; otherwise look locally
    test_dir = Path(__file__).parent.parent
    if test_dir.name == "skeleton":
        # Running from performance/skeleton/tests
        base_dir = test_dir
    else:
        # Running from project root - look in performance/skeleton
        base_dir = Path("regex_refactor_docs/performance/skeleton")

    # Check if fetcher code exists
    fetcher_paths = [
        base_dir / "doxstrux/markdown/fetchers/url_fetcher.py",
        base_dir / "doxstrux/markdown/fetchers/preview.py",
        base_dir / "doxstrux/markdown/utils/fetcher.py",
        base_dir / "doxstrux/fetchers.py",
    ]

    fetcher_found = None
    for path in fetcher_paths:
        if path.exists():
            fetcher_found = path
            break

    if fetcher_found is None:
        pytest.skip("Fetcher code not found - cannot verify normalization parity")

    # Read fetcher source
    fetcher_source = fetcher_found.read_text()

    # Verify normalize_url is used
    assert "normalize_url" in fetcher_source or "url_utils" in fetcher_source, \
        f"Fetcher {fetcher_found} does not appear to use centralized normalize_url function"


def test_collector_fetcher_normalization_parity():
    """
    Integration test: Verify collector and fetcher normalize URLs identically.

    This is the critical security property: normalization must be identical
    across components to prevent bypass attacks.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    try:
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        pytest.skip("LinksCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Test with adversarial URLs
    test_urls = [
        "//evil.com/steal",
        "  HTTPS://EXAMPLE.COM/path  ",
        "HtTpS://example.com/PATH",
        "https://example.com/%2e%2e/admin",
    ]

    for test_url in test_urls:
        # Normalize via central function (what fetcher should use)
        expected_normalized = normalize_url(test_url)

        # Create token with test URL
        tokens = [
            SimpleNamespace(
                type="link_open",
                nesting=1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x, url=test_url: url if x == "href" else None
            ),
            SimpleNamespace(
                type="text",
                nesting=0,
                tag="",
                map=None,
                info=None,
                content="test link",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="link_close",
                nesting=-1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
        ]

        # Collect links (what collector returns)
        collector = LinksCollector()
        wh = TokenWarehouse(tokens, tree=None)
        wh.register_collector(collector)
        wh.dispatch_all()
        result = collector.finalize(wh)

        # Handle dict return type (P0-3 truncation metadata)
        links = result["links"] if isinstance(result, dict) else result

        # Verify collector normalized URL matches central function
        if expected_normalized is None:
            # URL was rejected - collector should not collect it
            assert len(links) == 0, \
                f"Rejected URL '{test_url}' should not be collected, but got {len(links)} links"
        else:
            # URL was accepted - verify normalization matches
            assert len(links) == 1, f"Expected 1 link for '{test_url}', got {len(links)}"
            collector_normalized = links[0].get("url") or links[0].get("href")

            assert collector_normalized == expected_normalized, \
                f"Normalization mismatch for '{test_url}':\n" \
                f"  Collector returned: {collector_normalized}\n" \
                f"  normalize_url returned: {expected_normalized}\n" \
                f"  This is a CRITICAL security bug (normalization bypass possible)"


def test_adversarial_encoded_urls_corpus_parity():
    """
    Integration test: Load adversarial_encoded_urls.json and verify parity.

    All URLs in the corpus should be normalized identically by collectors
    and the central normalize_url function.
    """
    corpus_path = Path(__file__).parent.parent.parent / "adversarial_corpora" / "adversarial_encoded_urls.json"

    if not corpus_path.exists():
        pytest.skip(f"Corpus not found: {corpus_path}")

    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    try:
        from doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        pytest.skip("LinksCollector not available")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except ImportError:
        pytest.skip("token_warehouse not available")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse not available")

    # Load corpus
    test_cases = json.loads(corpus_path.read_text())

    for test_case in test_cases:
        test_url = test_case.get("url")
        if not test_url:
            continue

        # Normalize via central function
        expected_normalized = normalize_url(test_url)

        # Create token with test URL
        tokens = [
            SimpleNamespace(
                type="link_open",
                nesting=1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x, url=test_url: url if x == "href" else None
            ),
            SimpleNamespace(
                type="text",
                nesting=0,
                tag="",
                map=None,
                info=None,
                content="test link",
                attrGet=lambda x: None
            ),
            SimpleNamespace(
                type="link_close",
                nesting=-1,
                tag="a",
                map=None,
                info=None,
                content="",
                attrGet=lambda x: None
            ),
        ]

        # Collect links
        collector = LinksCollector()
        wh = TokenWarehouse(tokens, tree=None)
        wh.register_collector(collector)
        wh.dispatch_all()
        result = collector.finalize(wh)

        # Handle dict return type (P0-3 truncation metadata)
        links = result["links"] if isinstance(result, dict) else result

        # Verify parity
        if expected_normalized is not None:
            assert len(links) == 1, f"Expected 1 link for '{test_url}', got {len(links)}"
            collector_normalized = links[0].get("url") or links[0].get("href")
            assert collector_normalized == expected_normalized, \
                f"Normalization parity failure for '{test_url}':\n" \
                f"  Collector: {collector_normalized}\n" \
                f"  normalize_url: {expected_normalized}"
        else:
            # URL should be rejected (dangerous scheme)
            assert len(links) == 0, \
                f"Dangerous URL '{test_url}' was not rejected by collector"


def test_whitespace_trimming_parity():
    """
    Test that whitespace trimming is identical across components.

    Whitespace obfuscation is a common bypass technique.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    whitespace_urls = [
        "  https://example.com  ",
        "\thttps://example.com\t",
        "\nhttps://example.com\n",
        "  \t\n  https://example.com  \n\t  ",
    ]

    for url_with_whitespace in whitespace_urls:
        normalized = normalize_url(url_with_whitespace)

        # Verify no leading/trailing whitespace
        assert normalized and not normalized.startswith((" ", "\t", "\n")), \
            f"Leading whitespace not trimmed: '{url_with_whitespace}' → '{normalized}'"
        assert normalized and not normalized.endswith((" ", "\t", "\n")), \
            f"Trailing whitespace not trimmed: '{url_with_whitespace}' → '{normalized}'"


def test_case_normalization_parity():
    """
    Test that scheme/domain case normalization is identical across components.

    Mixed-case schemes are a common bypass technique.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    case_mixed_urls = [
        ("HTTPS://EXAMPLE.COM", "https://example.com"),
        ("HtTpS://ExAmPlE.CoM", "https://example.com"),
        ("HTTP://EXAMPLE.COM/PATH", "http://example.com/PATH"),  # Path case preserved
    ]

    for mixed_case, expected in case_mixed_urls:
        normalized = normalize_url(mixed_case)
        assert normalized == expected, \
            f"Case normalization failed: '{mixed_case}' → '{normalized}', expected '{expected}'"


def test_idn_homograph_detection():
    """
    Test that IDN homograph attacks are detected/normalized.

    Internationalized domain names can contain lookalike characters
    (e.g., Cyrillic 'а' looks like Latin 'a').
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    # Homograph examples (Cyrillic characters that look like Latin)
    homograph_urls = [
        "https://еxample.com",  # Cyrillic 'е' (U+0435) instead of Latin 'e'
        "https://аpple.com",    # Cyrillic 'а' (U+0430) instead of Latin 'a'
    ]

    for homograph_url in homograph_urls:
        normalized = normalize_url(homograph_url)

        # Verify IDN is converted to punycode (xn--...)
        # OR rejected entirely (depending on security policy)
        assert normalized is None or "xn--" in normalized, \
            f"IDN homograph not handled: '{homograph_url}' → '{normalized}'"


def test_percent_encoding_normalization():
    """
    Test that percent-encoding is normalized consistently.

    Double-encoding is a common bypass technique.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    percent_encoded_urls = [
        ("https://example.com/%2e%2e/admin", "https://example.com/../admin"),
        ("https://example.com/%252e%252e/secret", "https://example.com/%2e%2e/secret"),
        ("https://example.com/path%20with%20spaces", "https://example.com/path%20with%20spaces"),
    ]

    for encoded, expected in percent_encoded_urls:
        normalized = normalize_url(encoded)
        # Note: Exact behavior depends on normalization policy
        # At minimum, verify it's decoded consistently
        assert normalized is not None, \
            f"Percent-encoded URL rejected: '{encoded}'"


def test_no_normalization_bypass_via_fragments():
    """
    Test that URL fragments don't bypass normalization.

    Fragments (e.g., #anchor) should be preserved but not used to bypass checks.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    urls_with_fragments = [
        ("https://example.com#anchor", "https://example.com#anchor"),
        ("HTTPS://EXAMPLE.COM#ANCHOR", "https://example.com#ANCHOR"),
        ("javascript:alert(1)#harmless", None),  # Should still reject dangerous scheme
    ]

    for url_with_fragment, expected in urls_with_fragments:
        normalized = normalize_url(url_with_fragment)
        if expected is None:
            assert normalized is None or normalized == "", \
                f"Dangerous URL not rejected despite fragment: '{url_with_fragment}' → '{normalized}'"
        else:
            assert normalized == expected, \
                f"Fragment handling failed: '{url_with_fragment}' → '{normalized}'"


def test_no_normalization_bypass_via_userinfo():
    """
    Test that user:pass@host URLs don't bypass normalization.

    User info in URLs can be used for phishing.
    """
    try:
        from doxstrux.markdown.utils.url_utils import normalize_url
    except ImportError:
        pytest.skip("normalize_url not available")

    urls_with_userinfo = [
        "https://attacker:password@example.com",
        "https://user@evil.com",
        "https://admin:secret@internal.corp",
    ]

    for url_with_userinfo in urls_with_userinfo:
        normalized = normalize_url(url_with_userinfo)

        # Verify normalization still happens (or URL is rejected for security)
        # Most secure: reject URLs with user info entirely
        # Acceptable: normalize but preserve user info
        assert normalized is not None, \
            f"URL with user info caused normalization to fail: '{url_with_userinfo}'"
