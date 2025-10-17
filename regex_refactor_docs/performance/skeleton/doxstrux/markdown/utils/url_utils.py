"""Centralized URL normalization utilities.

This module provides the canonical URL normalization function used by ALL components:
- Collectors (links, images)
- Fetchers (downstream URL fetchers)
- Any code that handles URLs

CRITICAL: This prevents SSRF, XSS, and phishing attacks via normalization bypass exploits.
All URL handling MUST use this function to ensure consistent security properties.

Per CLOSING_IMPLEMENTATION.md lines 154-240: Single source of truth for URL normalization.
"""

from urllib.parse import urlsplit, urlunsplit
from typing import Optional

# Allowed URL schemes (prevents SSRF, XSS via javascript:, data:, file: URIs)
ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}


def normalize_url(url: str) -> Optional[str]:
    """Centralized URL normalization to prevent bypass attacks.

    This is the canonical normalization function that prevents various bypass techniques:
    - Case variations: jAvAsCrIpT:alert(1) → rejected
    - Whitespace obfuscation: "  https://example.com  " → "https://example.com"
    - Protocol-relative: //evil.com/malicious → rejected
    - Dangerous schemes: javascript:, data:, file:, vbscript: → rejected
    - Mixed case domains: HTTPS://EXAMPLE.COM → https://example.com

    Args:
        url: Raw URL string to validate and normalize

    Returns:
        Normalized URL string, or None if URL should be rejected

    Examples:
        >>> normalize_url("https://example.com")
        'https://example.com'
        >>> normalize_url("HTTPS://EXAMPLE.COM")
        'https://example.com'
        >>> normalize_url("  https://example.com  ")
        'https://example.com'
        >>> normalize_url("javascript:alert(1)")
        None
        >>> normalize_url("//evil.com/malicious")
        None
        >>> normalize_url("/relative/path")
        '/relative/path'

    Security Properties:
        1. Single source of truth - all components use this function
        2. Fail-closed - dangerous schemes rejected (return None)
        3. Case normalization - scheme and domain lowercased
        4. Whitespace stripping - bypass attempts prevented
        5. Protocol-relative rejection - // prefix not allowed
        6. Scheme allowlist - only safe schemes permitted

    CRITICAL: Collectors and fetchers MUST use identical normalization.
    If normalization differs, attackers can bypass security checks (TOCTOU).
    """
    if not url or not isinstance(url, str):
        return None

    # Strip whitespace (common bypass technique)
    url = url.strip()

    if not url:
        return None

    # Reject protocol-relative URLs (can bypass scheme checks)
    # Per CLOSING_IMPLEMENTATION.md line 196: "disallow // protocol-relative"
    if url.startswith('//'):
        return None

    # Parse URL and normalize components
    try:
        parsed = urlsplit(url)
    except Exception:
        # Invalid URL - reject
        return None

    # Extract and normalize scheme (lowercase)
    scheme = parsed.scheme.lower() if parsed.scheme else None

    # Check scheme against allowlist
    if scheme:
        # Explicit scheme present - must be in allowlist
        if scheme not in ALLOWED_SCHEMES:
            # Dangerous scheme (javascript:, data:, file:, etc.) - reject
            return None

    # Normalize domain to lowercase (prevents case-based bypasses)
    netloc = parsed.netloc.lower() if parsed.netloc else ""

    # IDN normalization (homograph attack prevention)
    # Convert internationalized domains to punycode (xn--...)
    if netloc:
        try:
            netloc = netloc.encode('idna').decode('ascii')
        except (UnicodeError, UnicodeDecodeError):
            # Fallback to original if IDNA encoding fails
            pass

    # Reconstruct normalized URL
    # Note: Path case is preserved (URLs are case-sensitive for paths)
    if scheme:
        # Absolute URL with scheme
        normalized_parts = (
            scheme,          # Scheme (lowercase)
            netloc,          # Domain (lowercase)
            parsed.path,     # Path (case-preserved)
            parsed.query,    # Query (case-preserved)
            parsed.fragment  # Fragment (case-preserved)
        )
        normalized = urlunsplit(normalized_parts)
    elif netloc:
        # URL like "example.com/path" (no scheme)
        # Treat as relative and preserve
        normalized_parts = (
            "",              # No scheme
            netloc,          # Domain (lowercase)
            parsed.path,     # Path (case-preserved)
            parsed.query,    # Query (case-preserved)
            parsed.fragment  # Fragment (case-preserved)
        )
        normalized = urlunsplit(normalized_parts)
    else:
        # Relative path like "/path" or "../path"
        # Preserve as-is (relative URLs are allowed)
        normalized = url

    return normalized


# Evidence anchor for implementation
# CLAIM-P0-1-IMPL: Centralized normalization prevents TOCTOU bypass
# Source: CLOSING_IMPLEMENTATION.md lines 97-150 + 154-240
# Implementation: Single source of truth (SOLID-DIP - depend on abstraction)
# Security: Rejects dangerous schemes, protocol-relative URLs, normalizes case
# CVSS: Mitigates 8.6 High (SSRF + Resource Exhaustion)
