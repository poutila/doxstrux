"""URL fetching utilities with security-first design.

This module provides minimal fetcher implementations that use the canonical
normalize_url function to ensure URL normalization parity across collectors
and fetchers (preventing TOCTOU/SSRF bypass attacks).
"""

__all__ = ['preview']
