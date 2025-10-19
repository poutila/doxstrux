"""
Profiling decorators for performance analysis.

This module provides lightweight profiling tools to measure function
execution time during development and optimization.

Usage:
    from skeleton.doxstrux.markdown.utils.profiling import profile

    @profile
    def dispatch_all(self):
        # ... implementation

    # Enable profiling for development
    import skeleton.doxstrux.markdown.utils.profiling as profiling
    profiling.PROFILING_ENABLED = True

    # Run parser - will print timing info
    parser.parse()

Security Note:
    Profiling is disabled by default in production. Enable only during
    development/optimization to avoid performance overhead.
"""

from __future__ import annotations
import functools
import time
from typing import Callable, Any, TypeVar

# Global toggle (disable in production)
PROFILING_ENABLED = False

# Type variable for generic decorator
F = TypeVar('F', bound=Callable[..., Any])


def profile(func: F) -> F:
    """
    Decorator to measure function execution time.

    Prints execution time to stdout when PROFILING_ENABLED is True.
    Has minimal overhead when disabled (~1 function call check).

    Args:
        func: Function to profile

    Returns:
        Wrapped function that measures execution time

    Example:
        >>> @profile
        ... def expensive_operation():
        ...     time.sleep(0.1)
        >>> expensive_operation()  # No output (profiling disabled)

        >>> import skeleton.doxstrux.markdown.utils.profiling as profiling
        >>> profiling.PROFILING_ENABLED = True
        >>> expensive_operation()
        expensive_operation: 100.234 ms

    Notes:
        - Only measures wall-clock time (not CPU time)
        - Not suitable for micro-benchmarks (use timeit module instead)
        - Use for identifying slow methods during optimization
    """
    if not PROFILING_ENABLED:
        # Fast path: profiling disabled, return original function
        # (avoids wrapper overhead entirely)
        return func

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start
            # Print to stdout (not logger) for simplicity
            print(f"{func.__name__}: {elapsed*1000:.3f} ms")

    return wrapper  # type: ignore


def profile_section(name: str) -> "ProfileContext":
    """
    Context manager to profile a code section.

    Useful for profiling code blocks that aren't functions.

    Args:
        name: Description of the code section

    Returns:
        Context manager that measures execution time

    Example:
        >>> with profile_section("index building"):
        ...     build_indices()
        index building: 5.234 ms
    """
    return ProfileContext(name)


class ProfileContext:
    """Context manager for profiling code sections."""

    def __init__(self, name: str):
        self.name = name
        self.start: float = 0.0

    def __enter__(self) -> "ProfileContext":
        if PROFILING_ENABLED:
            self.start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        if PROFILING_ENABLED:
            elapsed = time.perf_counter() - self.start
            print(f"{self.name}: {elapsed*1000:.3f} ms")


def enable_profiling() -> None:
    """Enable profiling globally."""
    global PROFILING_ENABLED
    PROFILING_ENABLED = True


def disable_profiling() -> None:
    """Disable profiling globally."""
    global PROFILING_ENABLED
    PROFILING_ENABLED = False


def is_profiling_enabled() -> bool:
    """Check if profiling is currently enabled."""
    return PROFILING_ENABLED
