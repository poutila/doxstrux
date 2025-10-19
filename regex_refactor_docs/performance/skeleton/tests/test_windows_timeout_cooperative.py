"""
Test Windows timeout cooperative behavior - RED TEAM BLOCKER TEST 6.

CRITICAL: Verify timeout handling works on Windows with threading.Timer.

Windows doesn't support SIGALRM, so timeout uses threading.Timer as fallback.
This is "cooperative" - the timeout flag is checked AFTER collector completes,
not during execution (threading cannot interrupt running Python code).

This test verifies:
1. Windows timeout detection is available (uses threading.Timer)
2. Timeout flag is raised if collector exceeds timeout
3. Fast collectors complete without triggering timeout

Red-Team Scenario:
If timeout.py uses signal.alarm() only (not threading.Timer fallback),
Windows builds will have NO timeout protection, allowing DoS attacks.
"""

import pytest
import platform
import time
from pathlib import Path
import sys

# Add skeleton to path for imports
SKELETON_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKELETON_ROOT))

try:
    from skeleton.doxstrux.markdown.utils.timeout import (
        collector_timeout, get_timeout_info, IS_WINDOWS, IS_UNIX
    )
    from skeleton.doxstrux.markdown.utils.text_normalization import parse_markdown_normalized
    from skeleton.doxstrux.markdown.utils.token_warehouse import (
        TokenWarehouse, Interest
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Timeout utilities not available"
)


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific timeout test")
def test_windows_timeout_triggers():
    """
    CRITICAL (Windows only): Verify timeout raises TimeoutError.

    On Windows, threading.Timer sets a flag that's checked after collector completes.
    """
    # Simulate long-running collector
    timeout_raised = False

    try:
        with collector_timeout(1):  # 1 second timeout
            time.sleep(2)  # Sleep for 2 seconds (exceeds timeout)
    except TimeoutError:
        timeout_raised = True

    # On Windows, timeout should be raised AFTER sleep completes
    # (cooperative timeout - cannot interrupt sleep)
    assert timeout_raised, \
        "TimeoutError should be raised on Windows after timeout expires"


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific timeout test")
def test_windows_fast_operation_no_timeout():
    """
    Verify fast operations complete without triggering timeout on Windows.
    """
    timeout_raised = False

    try:
        with collector_timeout(5):  # 5 second timeout
            time.sleep(0.1)  # Fast operation (well under timeout)
    except TimeoutError:
        timeout_raised = True

    assert not timeout_raised, \
        "Fast operations should not trigger timeout"


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific timeout test")
def test_windows_timeout_info():
    """
    Verify get_timeout_info() reports threading method on Windows.
    """
    info = get_timeout_info()

    assert info["available"] is True, \
        "Timeout should be available on Windows (threading fallback)"

    assert info["method"] == "threading", \
        f"Windows should use threading method, got {info['method']}"

    assert info["platform"] == "Windows", \
        f"Platform detection wrong: {info['platform']}"


def test_timeout_available_on_all_platforms():
    """
    Verify timeout protection is available on all major platforms.

    Unix: SIGALRM (most reliable)
    Windows: threading.Timer (cooperative)
    """
    info = get_timeout_info()

    if IS_UNIX:
        assert info["method"] == "sigalrm", \
            f"Unix should use sigalrm, got {info['method']}"
        assert info["available"] is True
    elif IS_WINDOWS:
        assert info["method"] == "threading", \
            f"Windows should use threading, got {info['method']}"
        assert info["available"] is True
    else:
        # Other platforms may not have timeout support (graceful degradation)
        assert info["method"] == "none" or info["available"] is True


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific test")
def test_windows_collector_timeout_integration():
    """
    Integration test: Verify TokenWarehouse timeout works on Windows.
    """
    md = "# Heading\n\nParagraph\n"
    tokens, tree, normalized = parse_markdown_normalized(md)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Set very short timeout
    wh.COLLECTOR_TIMEOUT_SECONDS = 1

    timeout_detected = [False]

    class SlowCollector:
        """Collector that exceeds timeout."""
        name = "Slow"
        interest = Interest(types={"heading_open"})

        def should_process(self, token, ctx, wh):
            return True

        def on_token(self, idx, token, ctx, wh):
            # Sleep longer than timeout
            time.sleep(2)

        def finalize(self, wh):
            return {}

    wh.register_collector(SlowCollector())

    # Dispatch (should handle timeout gracefully)
    # Warehouse may catch TimeoutError and log it in _collector_errors
    try:
        wh.dispatch_all()
        # Check if timeout was recorded in errors
        if wh._collector_errors:
            for name, idx, error_type in wh._collector_errors:
                if error_type == 'TimeoutError':
                    timeout_detected[0] = True
    except TimeoutError:
        timeout_detected[0] = True

    # On Windows, timeout should be detected (cooperative)
    assert timeout_detected[0], \
        "Timeout should be detected on Windows (check _collector_errors)"


@pytest.mark.skipif(not IS_UNIX, reason="Unix-specific test")
def test_unix_timeout_triggers():
    """
    CRITICAL (Unix only): Verify SIGALRM timeout raises immediately.

    On Unix, SIGALRM can interrupt execution (not cooperative).
    """
    timeout_raised = False

    try:
        with collector_timeout(1):  # 1 second timeout
            time.sleep(2)  # Should be interrupted by SIGALRM
    except TimeoutError:
        timeout_raised = True

    assert timeout_raised, \
        "TimeoutError should be raised on Unix (SIGALRM interrupts)"


@pytest.mark.skipif(not IS_UNIX, reason="Unix-specific test")
def test_unix_timeout_handler_restored():
    """
    Verify Unix timeout restores previous SIGALRM handler.

    setitimer cleanup must restore old handler to avoid breaking other code.
    """
    import signal

    # Set a custom handler
    custom_called = [False]

    def custom_handler(signum, frame):
        custom_called[0] = True

    old_handler = signal.signal(signal.SIGALRM, custom_handler)

    try:
        # Use collector_timeout (should restore custom handler after)
        with collector_timeout(1):
            pass  # Fast operation

        # Trigger alarm manually to verify handler was restored
        signal.setitimer(signal.ITIMER_REAL, 0.1)
        time.sleep(0.2)

        assert custom_called[0], \
            "Custom SIGALRM handler was not restored"

    finally:
        # Cleanup: restore original handler
        signal.signal(signal.SIGALRM, old_handler)
        signal.setitimer(signal.ITIMER_REAL, 0.0)


def test_timeout_zero_or_none_is_noop():
    """
    Verify timeout=0 or timeout=None is a no-op (no protection).

    This allows disabling timeout for trusted collectors.
    """
    # timeout=None should not raise
    try:
        with collector_timeout(None):
            time.sleep(0.1)
    except TimeoutError:
        pytest.fail("timeout=None should not raise TimeoutError")

    # timeout=0 should not raise
    try:
        with collector_timeout(0):
            time.sleep(0.1)
    except TimeoutError:
        pytest.fail("timeout=0 should not raise TimeoutError")


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific test")
def test_windows_timeout_does_not_interrupt():
    """
    Verify Windows timeout is cooperative (does not interrupt execution).

    This is a LIMITATION of threading.Timer - it cannot interrupt running code.
    Timeout is checked AFTER collector completes.
    """
    # Track if sleep was interrupted
    sleep_completed = [False]

    try:
        with collector_timeout(1):  # 1 second timeout
            time.sleep(2)  # 2 second sleep
            sleep_completed[0] = True  # This will execute (not interrupted)
    except TimeoutError:
        pass  # Expected after sleep completes

    # On Windows, sleep WILL complete (not interrupted)
    assert sleep_completed[0], \
        "Windows timeout should be cooperative (sleep not interrupted)"


@pytest.mark.skipif(not IS_UNIX, reason="Unix-specific test")
def test_unix_timeout_does_interrupt():
    """
    Verify Unix timeout interrupts execution (not cooperative).

    SIGALRM can interrupt sleep and raise TimeoutError immediately.
    """
    # Track if sleep completed
    sleep_completed = [False]

    try:
        with collector_timeout(1):  # 1 second timeout
            time.sleep(2)  # 2 second sleep (should be interrupted)
            sleep_completed[0] = True  # Should NOT execute
    except TimeoutError:
        pass  # Expected (sleep was interrupted)

    # On Unix, sleep should be interrupted (not complete)
    assert not sleep_completed[0], \
        "Unix timeout should interrupt execution (SIGALRM)"
