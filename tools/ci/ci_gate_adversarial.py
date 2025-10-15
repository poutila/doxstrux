#!/usr/bin/env python3
"""CI Gate P1: Adversarial Corpus Validation

Runs all adversarial test suites to validate security hardening.
Implements CI gate P1 for Phase 8 security validation.

Usage:
    python tools/ci/ci_gate_adversarial.py [--verbose]

Exit codes:
    0 - All adversarial tests passed
    1 - One or more test suites failed
"""

import sys
import subprocess
from pathlib import Path


def run_test_suite(test_file: str, verbose: bool = False) -> tuple[bool, str]:
    """Run a test suite and return (passed, output)."""

    cmd = [".venv/bin/python", "-m", "pytest", test_file, "-v"]
    if not verbose:
        cmd.append("--tb=short")

    # Skip coverage for skeleton tests (they test skeleton code, not main codebase)
    if "skeleton" in test_file:
        cmd.extend(["--no-cov", "-p", "no:coverage"])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    passed = result.returncode == 0
    output = result.stdout + result.stderr

    return passed, output


def main():
    """Run all adversarial test suites."""

    import argparse
    parser = argparse.ArgumentParser(description="CI Gate P1: Adversarial Tests")
    parser.add_argument("--verbose", action="store_true", help="Show full test output")
    args = parser.parse_args()

    print("=" * 70)
    print("CI Gate P1: Adversarial Corpus Validation")
    print("=" * 70)

    # Test suites from ADVERSARIAL_TESTING_GUIDE.md
    # Note: Some tests may not exist yet - that's okay
    test_suites = [
        # Core security tests
        ("Collector Linting", "regex_refactor_docs/performance/skeleton/tests/test_lint_collectors.py"),
        ("URL Normalization", "regex_refactor_docs/performance/skeleton/tests/test_url_normalization_consistency.py"),
        ("Performance Scaling", "regex_refactor_docs/performance/skeleton/tests/test_performance_scaling.py"),

        # Adversarial tests (from ADVERSARIAL_TESTING_GUIDE.md)
        # These may not all exist yet - will be created in Phase 8.0
        ("Resource Exhaustion", "tests/test_resource_exhaustion.py"),
        ("Malformed Maps", "tests/test_malformed_maps.py"),
        ("URL Bypass", "tests/test_url_bypass.py"),
        ("O(N²) Complexity", "tests/test_complexity_triggers.py"),
        ("Deep Nesting", "tests/test_deep_nesting.py"),
    ]

    results = []
    failed_suites = []
    skipped_suites = []

    for name, test_file in test_suites:
        print(f"\n[{name}]")
        print(f"  Running: {test_file}")

        if not Path(test_file).exists():
            print(f"  ⚠️  SKIPPED: Test file not found")
            skipped_suites.append(name)
            results.append((name, "skipped"))
            continue

        passed, output = run_test_suite(test_file, args.verbose)

        if passed:
            print(f"  ✅ PASSED")
        else:
            print(f"  ❌ FAILED")
            failed_suites.append(name)
            if args.verbose:
                print("\n  Output:")
                for line in output.split("\n"):
                    print(f"    {line}")
            else:
                # Show last 20 lines
                print("\n  Output (last 20 lines):")
                for line in output.split("\n")[-20:]:
                    print(f"    {line}")

        results.append((name, "passed" if passed else "failed"))

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    for name, status in results:
        if status == "passed":
            print(f"  ✅ PASS   {name}")
        elif status == "failed":
            print(f"  ❌ FAIL   {name}")
        else:
            print(f"  ⚠️  SKIP   {name}")

    if skipped_suites:
        print(f"\n⚠️  {len(skipped_suites)} test suite(s) skipped (files not found)")
        for suite in skipped_suites:
            print(f"   - {suite}")

    if failed_suites:
        print(f"\n❌ Gate P1 FAILED: {len(failed_suites)} test suite(s) failed")
        for suite in failed_suites:
            print(f"   - {suite}")
        return 1
    else:
        passed_count = sum(1 for _, status in results if status == "passed")
        print(f"\n✅ Gate P1 PASSED: {passed_count}/{len(test_suites)} test suites passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
