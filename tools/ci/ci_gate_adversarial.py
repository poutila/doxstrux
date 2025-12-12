#!/usr/bin/env python3
"""CI Gate: Adversarial Corpus Validation

Phase 3 of THREE_ADDITIONS.md - Adversarial testing CI gate.

This gate uses the shared adversarial_runner module to ensure no drift
between pytest tests and CI validation.

Invariants verified:
- INV-3.1: No crashes (CRASH status = failure)
- INV-3.2: Bounded time (TIMEOUT status = failure)
- INV-3.4: Graceful degradation (NO_RESULT status = failure)

BLOCKED status is acceptable - it means security worked correctly.

Usage:
    python tools/ci/ci_gate_adversarial.py [--verbose] [--timeout MS]

Exit codes:
    0 - All adversarial tests passed (includes BLOCKED)
    1 - One or more tests failed (CRASH, TIMEOUT, NO_RESULT)
"""

import argparse
import sys
from pathlib import Path

# Add tools to path for shared runner
sys.path.insert(0, str(Path(__file__).parent.parent))

from adversarial_runner import (
    AdversarialResult,
    get_timeout_ms,
    run_adversarial_corpus,
    summarize_results,
)

STATUS_ICONS = {
    "PASS": "✅",
    "BLOCKED": "🛡️",
    "CRASH": "💥",
    "TIMEOUT": "⏱️",
    "NO_RESULT": "⚠️",
}


def print_result(result: AdversarialResult, verbose: bool) -> None:
    """Print a single result line."""
    icon = STATUS_ICONS.get(result.status, "❓")
    print(f"{icon} {result.file_path.name}: {result.status} ({result.parse_time_ms:.1f}ms)")
    if result.error and (verbose or not result.passed):
        print(f"    Error: {result.error}")


def print_summary(summary: dict) -> None:
    """Print the summary section."""
    print("-" * 70)
    print("Summary:")
    print(f"  Total:    {summary['total']}")
    print(f"  Passed:   {summary['passed']}")
    print(f"  Blocked:  {summary['blocked']} (security worked)")
    print(f"  Crashed:  {summary['crashed']}")
    print(f"  Timeouts: {summary['timed_out']}")
    print(f"  No result: {summary['no_result']}")
    print("-" * 70)


def print_failures(failures: list) -> None:
    """Print failure details."""
    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"  - {failure['file']}: {failure['status']}")
            if failure["error"]:
                print(f"    {failure['error']}")


def main() -> int:
    """Run adversarial corpus validation."""
    parser = argparse.ArgumentParser(
        description="CI Gate: Adversarial Corpus Validation"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout per file in milliseconds (default: from env or 5000)",
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=Path(__file__).parent.parent / "adversarial_mds",
        help="Path to adversarial corpus directory",
    )
    parser.add_argument(
        "--profile",
        default="strict",
        choices=["strict", "moderate", "permissive"],
        help="Security profile to use (default: strict)",
    )
    args = parser.parse_args()

    timeout_ms = args.timeout or get_timeout_ms()

    print("=" * 70)
    print("CI Gate: Adversarial Corpus Validation")
    print("=" * 70)
    print(f"Corpus: {args.corpus_dir}")
    print(f"Timeout: {timeout_ms}ms per file")
    print(f"Profile: {args.profile}")
    print("-" * 70)

    # Run all adversarial tests
    try:
        results = run_adversarial_corpus(
            args.corpus_dir, timeout_ms=timeout_ms, security_profile=args.profile
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ ERROR: {e}")
        return 1

    # Print results for each file
    for result in results:
        print_result(result, args.verbose)

    # Summary
    summary = summarize_results(results)
    print_summary(summary)

    if summary["all_passed"]:
        print("✅ CI Gate PASSED: All adversarial tests passed")
        return 0

    print("❌ CI Gate FAILED: Some tests failed")
    print_failures(summary["failures"])
    return 1


if __name__ == "__main__":
    sys.exit(main())
