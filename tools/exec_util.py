"""Subprocess timeout helper for CI gates.

All long-running subprocess calls MUST use this helper to enforce timeouts
and prevent CI hangs.
"""
import subprocess
import json
from typing import List, Dict, Any


class SecurityError(RuntimeError):
    """Security validation failure."""
    pass


def run_json(cmd: List[str], timeout_s: int) -> Dict[str, Any]:
    """Execute command with timeout, parse JSON output, fail-closed on error.

    Args:
        cmd: Command as list (never use shell=True)
        timeout_s: Timeout in seconds (600 for moderate, 300 for strict)

    Returns:
        Parsed JSON from stdout

    Raises:
        SecurityError: On timeout or JSON parse failure
    """
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_s
        )
        return json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired as e:
        raise SecurityError(f"TIMEOUT({timeout_s}s): {' '.join(cmd)}") from e
    except json.JSONDecodeError as e:
        raise SecurityError(f"Invalid JSON from: {' '.join(cmd)}") from e


def assert_safe(cond: bool, msg: str) -> None:
    """Assertion with SecurityError instead of assert (CI-friendly).

    Usage: Replace `assert expr, "msg"` with `assert_safe(expr, "msg")`
    """
    if not cond:
        raise SecurityError(msg)
