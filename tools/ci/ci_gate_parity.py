#!/usr/bin/env python3
"""
CI Gate G3 - Parity

Validates that parser output matches frozen baselines byte-for-byte.
Ensures no regressions during refactoring by comparing current output
against known-good baseline JSON files.

Usage:
    python3 tools/ci/ci_gate_parity.py [--profile moderate]

Exit codes:
    0: All baselines match (PASS) or no baselines exist (SKIP)
    1: Parity failures found (FAIL)

References:
    - POLICY_GATES.md §2 (G3) - "Byte-identical JSONs for all canonical pairs"
    - DETAILED_TASK_LIST.md Task 0.4
"""

import sys
import json
import subprocess
from pathlib import Path


class SecurityError(RuntimeError):
    """CI gate validation failure."""
    pass


# Project root (2 levels up from tools/ci/)
ROOT = Path(__file__).resolve().parents[2]

# Default paths
BASELINE_RUNNER = ROOT / "tools" / "baseline_test_runner.py"
BASELINE_RESULTS = ROOT / "tools" / "baseline_results.json"
BASELINE_OUTPUTS_DIR = ROOT / "tools" / "baseline_outputs"


def run_baseline_tests(profile: str = "moderate", timeout_s: int = 600) -> dict:
    """Run baseline test suite and return results.

    Args:
        profile: Security profile to use (strict, moderate, permissive)
        timeout_s: Timeout in seconds

    Returns:
        Baseline test results dictionary

    Raises:
        SecurityError: On test runner failure or timeout
    """
    try:
        # Run baseline test runner
        result = subprocess.run(
            ["python3", str(BASELINE_RUNNER), "--profile", profile],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(ROOT)
        )

        # Test runner should create baseline_results.json
        if not BASELINE_RESULTS.exists():
            raise SecurityError(f"Baseline test runner did not create results file: {BASELINE_RESULTS}")

        # Load results
        results = json.loads(BASELINE_RESULTS.read_text(encoding="utf-8"))
        return results

    except subprocess.TimeoutExpired as e:
        raise SecurityError(f"Baseline tests timed out after {timeout_s}s") from e
    except json.JSONDecodeError as e:
        raise SecurityError(f"Invalid JSON in baseline results: {e}") from e
    except Exception as e:
        raise SecurityError(f"Failed to run baseline tests: {e}") from e


def main():
    """Main entry point."""
    try:
        # Parse arguments
        profile = "moderate"
        if len(sys.argv) > 1:
            if sys.argv[1] == "--profile":
                if len(sys.argv) < 3:
                    raise SecurityError("--profile requires a value (strict|moderate|permissive)")
                profile = sys.argv[2]
            else:
                raise SecurityError(f"Unknown argument: {sys.argv[1]}")

        # Check if baselines exist
        if not BASELINE_OUTPUTS_DIR.exists():
            # No baselines - SKIP
            print(json.dumps({
                "status": "SKIP",
                "reason": "no_baselines",
                "message": "Baseline outputs directory not found - generate baselines first"
            }))
            sys.exit(0)

        # Check if baseline test runner exists
        if not BASELINE_RUNNER.exists():
            raise SecurityError(f"Baseline test runner not found: {BASELINE_RUNNER}")

        # Run baseline tests
        results = run_baseline_tests(profile=profile)

        # Check results
        total = results.get("total_tests", 0)
        passed = results.get("passed", 0)
        failed_diff = results.get("failed_diff", 0)
        failed_error = results.get("failed_error", 0)

        if total == 0:
            # No tests run - SKIP
            print(json.dumps({
                "status": "SKIP",
                "reason": "no_tests",
                "message": "No baseline tests were run"
            }))
            sys.exit(0)

        if passed == total:
            # All tests passed - SUCCESS
            print(json.dumps({
                "status": "OK",
                "message": "All baseline tests passed",
                "total_tests": total,
                "passed": passed,
                "profile": profile
            }))
            sys.exit(0)
        else:
            # Some tests failed - FAIL
            print(json.dumps({
                "status": "FAIL",
                "reason": "parity_failures",
                "total_tests": total,
                "passed": passed,
                "failed_diff": failed_diff,
                "failed_error": failed_error,
                "pass_rate": results.get("pass_rate", 0.0),
                "profile": profile
            }))
            sys.exit(1)

    except SecurityError as e:
        print(json.dumps({
            "status": "FAIL",
            "reason": "security_error",
            "error": str(e)
        }))
        sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "status": "FAIL",
            "reason": "unexpected_error",
            "error": str(e)
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
