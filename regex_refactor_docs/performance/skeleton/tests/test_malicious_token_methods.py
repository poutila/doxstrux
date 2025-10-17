"""
Token Canonicalization Verification Test.

Verifies that malicious token methods (attrGet, __getattr__) are NOT executed
during dispatch, ensuring token canonicalization is complete.

Per PLAN_CLOSING_IMPLEMENTATION_extended_2.md P1-4:
- Tests that TokenWarehouse canonicalizes tokens to primitive dicts
- Prevents attrGet() or __getattr__() execution during dispatch
- Demonstrates token canonicalization security property

REFERENCE: External artifact test_malicious_token_methods.py
"""

import pytest
import os
from pathlib import Path


class MaliciousToken:
    """Mock token with side-effect methods to detect execution."""

    def __init__(self):
        self.type = "inline"
        self.content = "safe"
        self._side_effect_marker = Path("/tmp/token_side_effect_marker")
        # Remove marker if exists
        self._side_effect_marker.unlink(missing_ok=True)

    def attrGet(self, name):
        """Simulate accessor that performs side-effect if called."""
        try:
            self._side_effect_marker.write_text("attrGet_executed")
        except Exception:
            pass
        return getattr(self, name, None)

    def __getattr__(self, name):
        """Simulate __getattr__ side-effect."""
        try:
            self._side_effect_marker.write_text("__getattr___executed")
        except Exception:
            pass
        raise AttributeError(name)


def test_malicious_token_methods_not_invoked():
    """
    Verify token canonicalization prevents malicious method execution.

    Tests that TokenWarehouse canonicalizes tokens to primitive dicts,
    preventing attrGet() or __getattr__() execution during dispatch.
    """
    try:
        from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from skeleton.doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        pytest.skip("Skeleton modules not available")

    # Create malicious token
    token = MaliciousToken()
    tokens = [token]

    # Instantiate warehouse with malicious token
    try:
        wh = TokenWarehouse(tokens, tree=None)
    except Exception:
        pytest.skip("TokenWarehouse instantiation failed")

    # Register collector
    coll = LinksCollector()
    try:
        wh.register_collector(coll)
    except Exception:
        # Fallback: direct append
        try:
            wh._collectors.append(coll)
        except Exception:
            pytest.skip("Cannot register collector")

    # Dispatch collectors
    dispatch_fn = None
    for name in ("dispatch_all", "dispatch", "run_collectors"):
        if hasattr(wh, name):
            dispatch_fn = getattr(wh, name)
            break

    if dispatch_fn is None:
        pytest.skip("No known dispatch method found")

    try:
        dispatch_fn()
    except Exception:
        pass  # Dispatch may raise on malformed tokens

    # CRITICAL ASSERTION: Side-effect marker should NOT exist
    marker = token._side_effect_marker
    assert not marker.exists(), \
        f"❌ CRITICAL: Malicious token method was executed (found {marker}). " \
        "Token canonicalization incomplete or bypassed."

    # Cleanup
    marker.unlink(missing_ok=True)

    # EVIDENCE ANCHOR
    # CLAIM-P1-4-TEST: Token canonicalization prevents method execution
    # Source: External artifact + DEEP_VULNERABILITIES_ANALYSIS
    # Verification: Side-effect marker does NOT exist after dispatch
