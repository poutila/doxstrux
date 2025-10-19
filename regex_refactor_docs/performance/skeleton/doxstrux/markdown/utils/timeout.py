"""
Cross-platform timeout utilities for collector safety.

This module provides timeout protection for collector execution to prevent
infinite loops or pathological performance cases from blocking the parser.

Platform Support:
- Unix/Linux/macOS: Uses SIGALRM (most reliable)
- Windows: Uses threading.Timer (best-effort fallback)
- Other platforms: No-op (graceful degradation)

Usage:
    from skeleton.doxstrux.markdown.utils.timeout import collector_timeout

    try:
        with collector_timeout(5):
            collector.on_token(idx, token, ctx, wh)
    except TimeoutError:
        # Handle timeout
        pass
"""

from __future__ import annotations
import platform
from contextlib import contextmanager
from typing import Generator

# Platform detection (module-level constants)
IS_UNIX = platform.system() in ('Linux', 'Darwin')  # Linux or macOS
IS_WINDOWS = platform.system() == 'Windows'
TIMEOUT_AVAILABLE = IS_UNIX  # SIGALRM only reliably available on Unix


@contextmanager
def collector_timeout(seconds: int) -> Generator[None, None, None]:
    """
    Cross-platform timeout protection for collectors.

    Uses SIGALRM on Unix (most reliable), threading.Timer on Windows (best-effort),
    and no-op on other platforms.

    Args:
        seconds: Timeout in seconds

    Raises:
        TimeoutError: If collector execution exceeds timeout

    Example:
        >>> with collector_timeout(5):
        ...     collector.on_token(idx, token, ctx, wh)

    Platform Notes:
        - Unix (Linux/macOS): SIGALRM can forcefully interrupt execution
        - Windows: Thread-based timeout cannot interrupt running code;
          collector must complete naturally (limitation of Python threading)
        - Other platforms: No timeout enforcement (graceful degradation)

    Security:
        This is a defense-in-depth measure. Well-behaved collectors should
        complete in <100ms. Timeout protection prevents pathological cases
        (infinite loops, ReDoS) from blocking the entire parser.
    """
    if IS_UNIX:
        # Unix/Linux/macOS: Use setitimer (more precise than alarm, supports floats)
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(f"Collector timeout after {seconds}s")

        # Save old handler and set new one
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        # Use setitimer for sub-second precision and explicit timer cancellation
        signal.setitimer(signal.ITIMER_REAL, float(seconds))
        try:
            yield
        finally:
            # Always cancel timer and restore old handler
            signal.setitimer(signal.ITIMER_REAL, 0.0)  # Cancel timer explicitly
            signal.signal(signal.SIGALRM, old_handler)  # Restore previous handler

    elif IS_WINDOWS:
        # Windows: Use threading.Timer (best-effort fallback)
        import threading

        timeout_event = threading.Event()
        timed_out = [False]  # Mutable container to share state

        def timeout_trigger():
            """Set timeout flag (runs in separate thread)."""
            timed_out[0] = True
            # Note: Cannot raise exception in different thread
            # Collector must check timeout_event periodically (limitation)

        timer = threading.Timer(seconds, timeout_trigger)
        timer.start()
        try:
            yield
            # Check if timeout occurred during execution
            if timed_out[0]:
                raise TimeoutError(f"Collector timeout after {seconds}s")
        finally:
            timer.cancel()

    else:
        # Other platforms: No timeout support - graceful degradation
        # Just yield without any timeout enforcement
        yield


# Default timeout for collector execution (seconds)
DEFAULT_COLLECTOR_TIMEOUT = 5


def get_timeout_info() -> dict[str, bool | int]:
    """
    Get information about timeout support on current platform.

    Returns:
        dict with:
            - available: True if timeout protection is available
            - platform: Current platform name
            - method: Timeout method ("sigalrm", "threading", or "none")
            - default_timeout: Default timeout in seconds

    Example:
        >>> info = get_timeout_info()
        >>> print(f"Timeout available: {info['available']}")
        >>> print(f"Method: {info['method']}")
    """
    if IS_UNIX:
        method = "sigalrm"
        available = True
    elif IS_WINDOWS:
        method = "threading"
        available = True  # Best-effort
    else:
        method = "none"
        available = False

    return {
        "available": available,
        "platform": platform.system(),
        "method": method,
        "default_timeout": DEFAULT_COLLECTOR_TIMEOUT
    }
