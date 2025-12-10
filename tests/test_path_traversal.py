"""Tests for path traversal detection - NO false positives on HTTPS.

This file tests doxstrux-specific behaviour that is *stricter* or more
concrete than SECURITY_KERNEL_SPEC.md. Contract invariants live in
test_security_kernel_spec.py.
"""

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore


@pytest.mark.parametrize("url", [
    "https://example.com",
    "https://example.com/path/to/resource",
    "http://example.com/foo/bar",
    "mailto:user@example.com",
    "tel:+3581234567",
    "#anchor-link",
    "relative/path/file.md",
    "Normal text with // but no path traversal",
])
def test_path_traversal_allows_safe_urls(url):
    """Safe URLs must NOT trigger path traversal warnings.

    NO_WEAK_TESTS: Parametrized with specific URL patterns.
    """
    parser = MarkdownParserCore(f"# Test\n\n[link]({url})")
    assert parser._check_path_traversal(url) is False, \
        f"False positive: '{url}' should NOT be flagged"


@pytest.mark.parametrize("url", [
    # Basic traversal
    "../etc/passwd",
    "../../etc/shadow",
    "/../../etc/hosts",
    # Windows traversal
    "..\\..\\Windows\\System32",
    r"C:\Windows\System32\drivers\etc\hosts",
    r"C:\Windows\win.ini",
    r"D:\Users\Admin\Desktop",
    # UNC paths (per SECURITY_KERNEL_SPEC.md section 6.2)
    r"\\server\share\file.txt",
    r"\\192.168.1.1\c$\Windows",
    # file:// scheme
    "file:///etc/passwd",
    "file:///C:/Windows/win.ini",
    # Traversal in URL path
    "https://example.com/../../etc/passwd",
    # URL-encoded traversal (per SECURITY_KERNEL_SPEC.md section 6.2)
    "https://example.com/%2e%2e/%2e%2e/etc/passwd",
    "%2e%2e/%2e%2e/etc/passwd",
])
def test_path_traversal_flags_attacks(url):
    """Path traversal attacks must be detected.

    NO_WEAK_TESTS: Parametrized with specific attack patterns.
    Per SECURITY_KERNEL_SPEC.md section 6.4 test obligations.
    """
    parser = MarkdownParserCore("# Test")
    assert parser._check_path_traversal(url) is True, \
        f"Missed attack: '{url}' should be flagged"
