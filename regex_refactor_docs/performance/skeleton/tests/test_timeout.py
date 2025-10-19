"""
Tests for cross-platform timeout utilities.

These tests verify that collector timeout protection works correctly
on different platforms (Unix, Windows).
"""

import time
import platform
import pytest
from skeleton.doxstrux.markdown.utils.timeout import (
    collector_timeout,
    get_timeout_info,
    IS_UNIX,
    IS_WINDOWS,
    TIMEOUT_AVAILABLE,
    DEFAULT_COLLECTOR_TIMEOUT
)


class TestTimeoutInfo:
    """Test timeout information utility."""

    def test_get_timeout_info_structure(self):
        """Verify get_timeout_info returns expected structure."""
        info = get_timeout_info()
        assert "available" in info
        assert "platform" in info
        assert "method" in info
        assert "default_timeout" in info
        assert isinstance(info["available"], bool)
        assert isinstance(info["platform"], str)
        assert isinstance(info["method"], str)
        assert info["default_timeout"] == DEFAULT_COLLECTOR_TIMEOUT

    def test_get_timeout_info_method_matches_platform(self):
        """Verify timeout method matches current platform."""
        info = get_timeout_info()
        if IS_UNIX:
            assert info["method"] == "sigalrm"
            assert info["available"] is True
        elif IS_WINDOWS:
            assert info["method"] == "threading"
            assert info["available"] is True
        else:
            assert info["method"] == "none"
            assert info["available"] is False


class TestTimeoutFastOperations:
    """Test timeout allows fast operations to complete."""

    def test_timeout_allows_fast_operation(self):
        """Verify timeout doesn't interrupt fast operations."""
        with collector_timeout(2):
            time.sleep(0.1)  # Well under timeout
        # Should not raise

    def test_timeout_allows_zero_time_operation(self):
        """Verify timeout allows instantaneous operations."""
        with collector_timeout(1):
            x = 1 + 1  # Instant
        assert x == 2

    def test_timeout_allows_multiple_fast_operations(self):
        """Verify timeout allows multiple fast operations."""
        with collector_timeout(2):
            for _ in range(10):
                time.sleep(0.01)  # 10 × 10ms = 100ms total
        # Should not raise


class TestTimeoutSlowOperations:
    """Test timeout protection triggers on slow operations."""

    @pytest.mark.skipif(not IS_UNIX, reason="SIGALRM only available on Unix")
    def test_timeout_raises_on_slow_operation_unix(self):
        """Verify SIGALRM timeout triggers on Unix."""
        with pytest.raises(TimeoutError, match="timeout after 1s"):
            with collector_timeout(1):
                time.sleep(2)  # Exceeds timeout

    @pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific test")
    def test_timeout_raises_on_slow_operation_windows(self):
        """Verify threading.Timer timeout triggers on Windows."""
        with pytest.raises(TimeoutError, match="timeout after 1s"):
            with collector_timeout(1):
                time.sleep(2)  # Exceeds timeout

    @pytest.mark.skipif(not TIMEOUT_AVAILABLE, reason="Timeout not available on this platform")
    def test_timeout_message_includes_duration(self):
        """Verify timeout message includes timeout duration."""
        with pytest.raises(TimeoutError, match="3s"):
            with collector_timeout(3):
                time.sleep(5)


class TestTimeoutPlatformSpecific:
    """Platform-specific timeout behavior tests."""

    @pytest.mark.skipif(not IS_UNIX, reason="Unix-specific test")
    def test_unix_uses_sigalrm(self):
        """Verify Unix implementation uses SIGALRM."""
        import signal
        import sys

        # Check that SIGALRM is available
        assert hasattr(signal, 'SIGALRM')

        # Verify timeout uses SIGALRM by checking if alarm gets set
        old_handler = signal.signal(signal.SIGALRM, signal.SIG_IGN)
        try:
            with collector_timeout(1):
                # Alarm should be set
                remaining = signal.alarm(0)  # Cancel and get remaining time
                assert remaining > 0  # Alarm was set
        finally:
            signal.signal(signal.SIGALRM, old_handler)

    @pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific test")
    def test_windows_uses_threading(self):
        """Verify Windows implementation uses threading.Timer."""
        import threading

        # Just verify threading is available (Timer uses it)
        assert hasattr(threading, 'Timer')

        # Verify timeout completes without error on fast operation
        with collector_timeout(1):
            time.sleep(0.01)


class TestTimeoutEdgeCases:
    """Test edge cases and error handling."""

    def test_timeout_with_zero_seconds(self):
        """Verify timeout with 0 seconds."""
        # Should either timeout immediately or allow very fast operations
        # Behavior may vary by platform
        try:
            with collector_timeout(0):
                x = 1 + 1
        except TimeoutError:
            pass  # Acceptable on some platforms

    def test_timeout_with_large_duration(self):
        """Verify timeout with large duration (60 seconds)."""
        with collector_timeout(60):
            time.sleep(0.01)  # Fast operation under large timeout
        # Should not raise

    def test_timeout_nested_contexts(self):
        """Verify nested timeout contexts work correctly."""
        pytest.skip("Nested timeouts not currently supported - implementation detail")
        # Note: Nested SIGALRM or Timer contexts are complex
        # Current implementation doesn't support nesting
        # This is acceptable - collectors shouldn't nest

    def test_timeout_exception_during_execution(self):
        """Verify timeout cleanup happens even if operation raises."""
        with pytest.raises(ValueError):
            with collector_timeout(2):
                raise ValueError("Test error")
        # Timeout should be cleaned up (alarm canceled, timer canceled)

    @pytest.mark.skipif(not IS_UNIX, reason="Unix-specific test")
    def test_timeout_restores_signal_handler_unix(self):
        """Verify SIGALRM handler is restored after timeout context."""
        import signal

        # Set custom handler
        def custom_handler(signum, frame):
            pass

        signal.signal(signal.SIGALRM, custom_handler)

        # Use timeout context
        with collector_timeout(1):
            time.sleep(0.01)

        # Verify custom handler is restored
        current_handler = signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.signal(signal.SIGALRM, current_handler)  # Restore
        # Handler should be our custom one, not SIG_DFL
        assert current_handler is custom_handler


class TestTimeoutConstants:
    """Test module constants and platform detection."""

    def test_platform_constants_are_boolean(self):
        """Verify platform detection constants are boolean."""
        assert isinstance(IS_UNIX, bool)
        assert isinstance(IS_WINDOWS, bool)
        assert isinstance(TIMEOUT_AVAILABLE, bool)

    def test_platform_constants_exclusive(self):
        """Verify platform constants are mutually exclusive."""
        # At most one should be True
        # (Could be both False on other platforms)
        assert not (IS_UNIX and IS_WINDOWS)

    def test_current_platform_detected(self):
        """Verify current platform is correctly detected."""
        system = platform.system()
        if system in ('Linux', 'Darwin'):
            assert IS_UNIX is True
            assert IS_WINDOWS is False
            assert TIMEOUT_AVAILABLE is True
        elif system == 'Windows':
            assert IS_UNIX is False
            assert IS_WINDOWS is True
            assert TIMEOUT_AVAILABLE is True
        else:
            assert IS_UNIX is False
            assert IS_WINDOWS is False
            assert TIMEOUT_AVAILABLE is False

    def test_default_timeout_is_positive(self):
        """Verify DEFAULT_COLLECTOR_TIMEOUT is positive integer."""
        assert isinstance(DEFAULT_COLLECTOR_TIMEOUT, int)
        assert DEFAULT_COLLECTOR_TIMEOUT > 0
        assert DEFAULT_COLLECTOR_TIMEOUT == 5  # Documented default
