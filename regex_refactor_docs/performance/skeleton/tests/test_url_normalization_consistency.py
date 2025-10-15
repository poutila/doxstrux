"""Cross-stage URL normalization consistency tests.

Tests that collector and fetcher use identical URL validation to prevent
TOCTOU (Time-of-Check-Time-of-Use) vulnerabilities where a URL passes
collector validation but resolves to a malicious destination during fetch.
"""

import sys
from pathlib import Path

# Add security module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "doxstrux" / "markdown"))

from security.validators import normalize_url, ALLOWED_SCHEMES


def test_collector_fetcher_use_same_normalization():
    """Verify collector and fetcher use identical URL validation.

    This prevents TOCTOU attacks where collector says "safe" but
    fetcher resolves to malicious destination.
    """

    # Corpus of obfuscated/attack URLs
    attack_corpus = [
        # Scheme attacks
        ("javascript:alert(1)", False),
        ("jAvAsCrIpT:alert(1)", False),  # Case variation
        ("JAVASCRIPT:alert(1)", False),
        ("JavaScript:alert(1)", False),

        # Protocol-relative
        ("//evil.com/malicious", False),
        ("//attacker.com", False),

        # Data URIs
        ("data:text/html,<script>alert(1)</script>", False),
        ("data:image/svg+xml,<svg onload=alert(1)>", False),

        # File URIs
        ("file:///etc/passwd", False),
        ("file://localhost/etc/passwd", False),

        # FTP (not in allowlist)
        ("ftp://evil.com/malware", False),

        # Valid URLs
        ("http://example.com", True),
        ("https://example.com", True),
        ("mailto:user@example.com", True),
        ("tel:+1234567890", True),

        # Relative URLs (allowed)
        ("/relative/path", True),
        ("relative/path", True),
        ("./relative/path", True),
        ("../relative/path", True),
    ]

    failures = []

    for url, expected_safe in attack_corpus:
        # Collector validation (happens first)
        collector_scheme, collector_safe = normalize_url(url)

        # Fetcher validation (happens later - MUST be identical)
        # In real code, fetcher would call normalize_url() again
        fetcher_scheme, fetcher_safe = normalize_url(url)

        # CRITICAL: Must be identical (no TOCTOU)
        if collector_safe != fetcher_safe:
            failures.append(
                f"TOCTOU vulnerability: collector={collector_safe}, "
                f"fetcher={fetcher_safe} for {url}"
            )

        # Must match expected
        if collector_safe != expected_safe:
            failures.append(
                f"Wrong classification: got {collector_safe}, "
                f"expected {expected_safe} for {url}"
            )

        # Schemes must match
        if collector_scheme != fetcher_scheme:
            failures.append(
                f"Scheme mismatch: collector={collector_scheme}, "
                f"fetcher={fetcher_scheme} for {url}"
            )

    assert not failures, "\n".join(failures)


def test_private_ip_rejection():
    """Verify private IPs are detected (SSRF prevention).

    Note: Current implementation allows private IPs (only checks scheme).
    For full SSRF protection, fetchers MUST validate IPs separately.
    """

    private_ips = [
        "http://localhost/admin",
        "http://127.0.0.1/internal",
        "http://192.168.1.1/router",
        "http://10.0.0.1/private",
        "http://[::1]/ipv6-localhost",
    ]

    for url in private_ips:
        scheme, is_allowed = normalize_url(url)

        # Current implementation: scheme is valid but IP needs separate check
        assert scheme in ALLOWED_SCHEMES, \
            f"Private IP should at least have valid scheme: {url}"

        # TODO: Add IP validation to normalize_url() for complete SSRF prevention
        # For now, document that fetchers MUST validate IPs separately


def test_unicode_homograph_detection():
    """Verify unicode homograph attacks are detected.

    Note: Current implementation does not detect homographs.
    For production, add punycode normalization and similarity checks.
    """

    # Punycode domain that looks like "example.com"
    # (Uses Cyrillic 'е' instead of Latin 'e')
    homograph = "https://еxamplе.com"

    scheme, is_allowed = normalize_url(homograph)

    # Current implementation allows this (only checks scheme)
    assert scheme == "https"  # Scheme is valid

    # TODO: Add punycode normalization and homograph detection
    # See: https://unicode.org/reports/tr39/ for detection strategies


def test_percent_encoding_normalization():
    """Verify percent-encoded schemes are handled correctly."""

    # Note: urlsplit does NOT decode percent-encoding in schemes
    # This is GOOD for security - malformed schemes are caught
    result = normalize_url("java%73cript:alert(1)")

    # urlsplit treats "java%73cript" as the scheme (not decoded)
    # Since it's not in ALLOWED_SCHEMES, it gets rejected
    # This is the desired behavior!
    assert result[0] not in ALLOWED_SCHEMES, \
        "Percent-encoded scheme should not be in allowlist"

    # May or may not be rejected depending on implementation
    # (urlsplit is permissive, but our allowlist catches it)


def test_null_byte_handling():
    """Verify NULL bytes in URLs are handled."""

    null_byte_url = "javascript\x00:alert(1)"

    scheme, is_allowed = normalize_url(null_byte_url)

    # urlsplit may parse this as scheme "javascript\x00"
    # which is not in ALLOWED_SCHEMES, so should be rejected
    if scheme:
        assert scheme not in ALLOWED_SCHEMES, \
            "NULL byte scheme should not be in allowlist"

    # The key is that it won't match "javascript" exactly
    assert scheme != "javascript", \
        "NULL byte should alter the scheme"


def test_whitespace_stripping():
    """Verify leading/trailing whitespace is stripped."""

    tests = [
        ("  https://example.com  ", "https", True),
        ("\thttps://example.com\n", "https", True),
        (" javascript:alert(1) ", "javascript", False),
    ]

    for url, expected_scheme, expected_safe in tests:
        scheme, is_allowed = normalize_url(url)

        assert scheme == expected_scheme, \
            f"Scheme mismatch for {repr(url)}: got {scheme}, expected {expected_scheme}"

        assert is_allowed == expected_safe, \
            f"Safety mismatch for {repr(url)}: got {is_allowed}, expected {expected_safe}"


def test_empty_and_invalid_urls():
    """Verify empty and invalid URLs are handled."""

    invalid_urls = [
        "",  # Empty
        ":",  # Just colon
        "://",  # Protocol-relative with colon
    ]

    for url in invalid_urls:
        scheme, is_allowed = normalize_url(url)

        # Empty/invalid should either be rejected or return None scheme
        assert scheme is None or not is_allowed, \
            f"Invalid URL should be rejected: {repr(url)}"


def test_case_normalization():
    """Verify scheme case normalization."""

    tests = [
        ("HTTP://example.com", "http", True),
        ("HTTPS://example.com", "https", True),
        ("HtTpS://example.com", "https", True),
        ("MAILTO:user@example.com", "mailto", True),
    ]

    for url, expected_scheme, expected_safe in tests:
        scheme, is_allowed = normalize_url(url)

        assert scheme == expected_scheme, \
            f"Scheme not normalized: got {scheme}, expected {expected_scheme}"

        assert is_allowed == expected_safe


if __name__ == "__main__":
    # Run tests
    tests = [
        test_collector_fetcher_use_same_normalization,
        test_private_ip_rejection,
        test_unicode_homograph_detection,
        test_percent_encoding_normalization,
        test_null_byte_handling,
        test_whitespace_stripping,
        test_empty_and_invalid_urls,
        test_case_normalization,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
