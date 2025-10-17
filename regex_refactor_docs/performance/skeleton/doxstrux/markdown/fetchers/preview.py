"""Minimal URL fetcher/preview with canonical normalization.

CRITICAL SECURITY REQUIREMENT:
This module MUST use the same normalize_url function as collectors
to prevent TOCTOU (Time-Of-Check-Time-Of-Use) bypass attacks.

Attack Vector Example:
1. Collector normalizes URL and stores "https://safe.example.com"
2. Fetcher normalizes differently, resolves to "https://evil.attacker.com"
3. Result: SSRF vulnerability (fetcher bypasses collector's security check)

Prevention:
Both collector and fetcher import from utils.url_utils.normalize_url
(single source of truth).

Per CLOSING_IMPLEMENTATION.md P0-1:
- Collectors and fetchers MUST use identical normalization
- This parity is enforced by test_url_normalization_parity.py
"""

from typing import Optional

# CRITICAL: Import canonical normalize_url (single source of truth)
from ..utils.url_utils import normalize_url


def normalize_url_for_fetcher(raw: str) -> Optional[str]:
    """
    Fetcher-side URL normalization wrapper.

    This is a thin wrapper around the canonical normalize_url function
    to make it explicit that fetchers use the same normalization as collectors.

    Args:
        raw: Raw URL string from user input or markdown content

    Returns:
        Normalized URL string, or None if URL should be rejected

    Examples:
        >>> normalize_url_for_fetcher("HTTPS://EXAMPLE.COM")
        'https://example.com'

        >>> normalize_url_for_fetcher("//evil.com/steal")  # Protocol-relative
        None

        >>> normalize_url_for_fetcher("javascript:alert(1)")  # Dangerous scheme
        None
    """
    try:
        return normalize_url(raw)
    except Exception:
        # Any exception during normalization = reject URL
        return None


def fetch_preview(url: str, timeout: int = 3) -> Optional[dict]:
    """
    Fetch URL metadata (HEAD request, fallback to GET).

    **Security Note**: This is a minimal reference implementation for testing.
    Production fetchers should add:
    - Rate limiting
    - User-Agent headers
    - Redirect limits
    - Content-Length checks before GET
    - DNS rebinding protection

    Args:
        url: Raw URL string to fetch
        timeout: Request timeout in seconds (default: 3)

    Returns:
        Dict with metadata (url, status_code, content_type, content_length),
        or None if URL rejected or fetch failed

    Example:
        >>> fetch_preview("https://example.com")
        {
            "url": "https://example.com",
            "status_code": 200,
            "content_type": "text/html",
            "content_length": "1234"
        }
    """
    # Step 1: Normalize URL (reject if dangerous)
    normalized = normalize_url_for_fetcher(url)
    if normalized is None:
        return None

    # Step 2: Fetch metadata
    # NOTE: requests is optional dependency for skeleton
    # Production implementation should use httpx or similar
    try:
        import requests
    except ImportError:
        # Graceful degradation if requests not available
        return {
            "url": normalized,
            "status_code": None,
            "content_type": None,
            "content_length": None,
            "error": "requests library not available"
        }

    try:
        # Try HEAD first (lightweight)
        r = requests.head(normalized, timeout=timeout, allow_redirects=True)

        # Some servers return 405 Method Not Allowed for HEAD
        if r.status_code == 405:
            r = requests.get(normalized, timeout=timeout, allow_redirects=True, stream=True)
            # Close connection immediately (don't download body)
            r.close()

        return {
            "url": normalized,
            "status_code": r.status_code,
            "content_type": r.headers.get("content-type"),
            "content_length": r.headers.get("content-length"),
        }
    except Exception:
        # Network errors, timeouts, etc.
        return None
