"""Tests for security config SSOT - no duplicate constants.

This file tests doxstrux-specific behaviour that is *stricter* or more
concrete than SECURITY_KERNEL_SPEC.md. Contract invariants live in
test_security_kernel_spec.py.
"""

import pytest
from doxstrux.markdown.config import SECURITY_PROFILES


@pytest.mark.parametrize("profile,expected", [
    ("strict", 0),
    ("moderate", 10240),
    ("permissive", 102400),
])
def test_max_data_uri_size_from_config(profile, expected):
    """Budget values must come from SECURITY_PROFILES (SSOT)."""
    try:
        from doxstrux.markdown.budgets import get_max_data_uri_size
    except ImportError:
        pytest.fail("get_max_data_uri_size not implemented yet")

    assert get_max_data_uri_size(profile) == expected
    assert SECURITY_PROFILES[profile]["max_data_uri_size"] == expected


@pytest.mark.parametrize("profile,expected", [
    ("strict", 4096),
    ("moderate", 2048),
    ("permissive", 1024),
])
def test_max_injection_scan_chars_from_config(profile, expected):
    """Injection scan chars must come from SECURITY_PROFILES (SSOT).

    Per SECURITY_KERNEL_SPEC.md section 8.3 test obligations.

    Note: These exact values (4096/2048/1024) are normative for doxstrux.
    The spec lists them as "recommended defaults"; we enforce them as requirements.
    """
    try:
        from doxstrux.markdown.budgets import get_max_injection_scan_chars
    except ImportError:
        pytest.fail("get_max_injection_scan_chars not implemented yet")

    assert get_max_injection_scan_chars(profile) == expected
    assert SECURITY_PROFILES[profile]["max_injection_scan_chars"] == expected


def test_unknown_profile_raises():
    """Unknown profile must raise ValueError.

    Per SECURITY_KERNEL_SPEC.md section 8.3 test obligations.
    """
    try:
        from doxstrux.markdown.budgets import get_max_data_uri_size, get_max_injection_scan_chars
    except ImportError:
        pytest.fail("Budget functions not implemented yet")

    with pytest.raises(ValueError):
        get_max_data_uri_size("unknown_profile")
    with pytest.raises(ValueError):
        get_max_injection_scan_chars("unknown_profile")
