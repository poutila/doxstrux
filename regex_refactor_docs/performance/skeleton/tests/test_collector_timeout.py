"""
Test that slow collectors are terminated and recorded as timeout errors.

SIGALRM is Unix-only. On Windows, SIGALRM is unavailable so timeouts are not enforced.
These tests will skip gracefully on Windows.
"""
import pytest
import sys
import signal
import time

def test_collector_timeout_enforced():
    """
    A collector that sleeps for >2 seconds should be killed by SIGALRM and recorded as TimeoutError.
    """
    # Skip if SIGALRM not available (Windows)
    if not hasattr(signal, 'SIGALRM'):
        pytest.skip("SIGALRM not available (Windows) - timeout enforcement not supported")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except Exception:
        pytest.skip("token_warehouse module not importable")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse class not available")

    class Tok:
        type = "inline"
        nesting = 0
        tag = ""
        map = None
        info = None
        content = "x"
        def attrGet(self, name):
            return None

    tokens = [Tok()]
    wh = TokenWarehouse(tokens, tree=None)

    # Set timeout to 1 second for fast test
    wh.COLLECTOR_TIMEOUT_SECONDS = 1

    class SlowCollector:
        name = "slow"
        @property
        def interest(self):
            class I:
                types = {"inline"}
                tags = set()
                ignore_inside = set()
                predicate = None
            return I()
        def should_process(self, token, ctx, wh_local):
            return True
        def on_token(self, idx, token, ctx, wh_local):
            # Sleep for 3 seconds - should be killed by SIGALRM after 1 second
            time.sleep(3)
        def finalize(self, wh_local):
            return {}

    try:
        wh.register_collector(SlowCollector())
    except Exception:
        try:
            wh._collectors.append(SlowCollector())
        except Exception:
            pytest.skip("unable to register collector")

    # Dispatch should not raise (error is caught and recorded)
    wh.dispatch_all()

    # Check that timeout error was recorded
    assert len(wh._collector_errors) == 1, f"Expected 1 error, got {len(wh._collector_errors)}"
    col_name, token_idx, error_type = wh._collector_errors[0]
    assert col_name == "slow", f"Expected collector name 'slow', got {col_name}"
    assert error_type == "TimeoutError", f"Expected TimeoutError, got {error_type}"


def test_collector_timeout_fast_collector_ok():
    """
    A fast collector that completes within timeout should succeed without errors.
    """
    # Skip if SIGALRM not available (Windows)
    if not hasattr(signal, 'SIGALRM'):
        pytest.skip("SIGALRM not available (Windows) - timeout enforcement not supported")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except Exception:
        pytest.skip("token_warehouse module not importable")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse class not available")

    class Tok:
        type = "inline"
        nesting = 0
        tag = ""
        map = None
        info = None
        content = "x"
        def attrGet(self, name):
            return None

    tokens = [Tok()]
    wh = TokenWarehouse(tokens, tree=None)

    # Set timeout to 2 seconds
    wh.COLLECTOR_TIMEOUT_SECONDS = 2

    class FastCollector:
        name = "fast"
        call_count = 0
        @property
        def interest(self):
            class I:
                types = {"inline"}
                tags = set()
                ignore_inside = set()
                predicate = None
            return I()
        def should_process(self, token, ctx, wh_local):
            return True
        def on_token(self, idx, token, ctx, wh_local):
            # Fast collector - completes immediately
            FastCollector.call_count += 1
        def finalize(self, wh_local):
            return {}

    try:
        wh.register_collector(FastCollector())
    except Exception:
        try:
            wh._collectors.append(FastCollector())
        except Exception:
            pytest.skip("unable to register collector")

    # Dispatch should succeed
    wh.dispatch_all()

    # Check that collector was called
    assert FastCollector.call_count == 1, f"Expected collector to be called once, got {FastCollector.call_count}"

    # Check that no errors were recorded
    assert len(wh._collector_errors) == 0, f"Expected no errors, got {len(wh._collector_errors)}"


def test_collector_timeout_disabled():
    """
    When COLLECTOR_TIMEOUT_SECONDS is None or 0, timeouts should be disabled.
    """
    # Skip if SIGALRM not available (Windows)
    if not hasattr(signal, 'SIGALRM'):
        pytest.skip("SIGALRM not available (Windows) - timeout enforcement not supported")

    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except Exception:
        pytest.skip("token_warehouse module not importable")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse class not available")

    class Tok:
        type = "inline"
        nesting = 0
        tag = ""
        map = None
        info = None
        content = "x"
        def attrGet(self, name):
            return None

    tokens = [Tok()]
    wh = TokenWarehouse(tokens, tree=None)

    # Disable timeout
    wh.COLLECTOR_TIMEOUT_SECONDS = None

    class SlowCollector:
        name = "slow_no_timeout"
        call_count = 0
        @property
        def interest(self):
            class I:
                types = {"inline"}
                tags = set()
                ignore_inside = set()
                predicate = None
            return I()
        def should_process(self, token, ctx, wh_local):
            return True
        def on_token(self, idx, token, ctx, wh_local):
            # Sleep briefly - should complete successfully with timeout disabled
            time.sleep(0.1)
            SlowCollector.call_count += 1
        def finalize(self, wh_local):
            return {}

    try:
        wh.register_collector(SlowCollector())
    except Exception:
        try:
            wh._collectors.append(SlowCollector())
        except Exception:
            pytest.skip("unable to register collector")

    # Dispatch should succeed
    wh.dispatch_all()

    # Check that collector was called
    assert SlowCollector.call_count == 1, f"Expected collector to be called once, got {SlowCollector.call_count}"

    # Check that no errors were recorded
    assert len(wh._collector_errors) == 0, f"Expected no errors, got {len(wh._collector_errors)}"
