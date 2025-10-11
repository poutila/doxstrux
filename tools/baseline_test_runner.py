#!/usr/bin/env python3
"""
Baseline Test Runner for Docpipe Markdown Parser

Tests the current parser implementation against all test pairs in tools/test_mds/
Validates that .md files produce output matching their corresponding .json files.

Usage:
    python tools/baseline_test_runner.py
    python tools/baseline_test_runner.py --profile moderate
    python tools/baseline_test_runner.py --verbose
"""

import json
import sys
import time
from pathlib import Path
from typing import Any
from collections import defaultdict
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docpipe.markdown_parser_core import MarkdownParserCore


def normalize_json(data: Any) -> str:
    """Normalize JSON for comparison."""
    return json.dumps(data, sort_keys=True, indent=2)


def compare_outputs(expected: dict, actual: dict) -> tuple[bool, list[str]]:
    """Compare expected and actual outputs, return (matches, differences)."""
    differences = []

    # Normalize and compare
    expected_str = normalize_json(expected)
    actual_str = normalize_json(actual)

    if expected_str == actual_str:
        return True, []

    # Find specific differences
    expected_keys = set(expected.keys())
    actual_keys = set(actual.keys())

    missing_keys = expected_keys - actual_keys
    extra_keys = actual_keys - expected_keys

    if missing_keys:
        differences.append(f"Missing keys: {missing_keys}")
    if extra_keys:
        differences.append(f"Extra keys: {extra_keys}")

    # Compare common keys
    for key in expected_keys & actual_keys:
        if expected[key] != actual[key]:
            differences.append(f"Key '{key}' differs")

    return False, differences


def run_test_pair(md_file: Path, json_file: Path, security_profile: str = "moderate") -> dict:
    """Run a single test pair and return results."""
    result = {
        "md_file": str(md_file.relative_to(md_file.parents[2])),
        "json_file": str(json_file.relative_to(json_file.parents[2])),
        "status": "unknown",
        "error": None,
        "differences": [],
        "parse_time_ms": 0,
    }

    try:
        # Read input and expected output
        md_content = md_file.read_text(encoding="utf-8")
        expected_output = json.loads(json_file.read_text(encoding="utf-8"))

        # Parse with current implementation
        start_time = time.perf_counter()
        parser = MarkdownParserCore(md_content, security_profile=security_profile)
        actual_output = parser.parse()
        parse_time = (time.perf_counter() - start_time) * 1000

        result["parse_time_ms"] = round(parse_time, 2)

        # Compare outputs
        matches, differences = compare_outputs(expected_output, actual_output)

        if matches:
            result["status"] = "PASS"
        else:
            result["status"] = "DIFF"
            result["differences"] = differences

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()

    return result


def find_test_pairs(test_dir: Path) -> list[tuple[Path, Path]]:
    """Find all .md/.json test pairs in the test directory."""
    pairs = []

    for md_file in sorted(test_dir.rglob("*.md")):
        json_file = md_file.with_suffix(".json")
        if json_file.exists():
            pairs.append((md_file, json_file))

    return pairs


def run_all_tests(test_dir: Path, security_profile: str = "moderate", verbose: bool = False) -> dict:
    """Run all tests and return summary."""
    pairs = find_test_pairs(test_dir)

    print(f"Found {len(pairs)} test pairs")
    print(f"Security profile: {security_profile}")
    print(f"Test directory: {test_dir}")
    print("-" * 80)

    results = []
    by_category = defaultdict(list)

    total_time = 0

    for i, (md_file, json_file) in enumerate(pairs, 1):
        category = md_file.parent.name

        if verbose or i % 50 == 0:
            print(f"[{i}/{len(pairs)}] Testing {md_file.name}...", end="\r")

        result = run_test_pair(md_file, json_file, security_profile)
        results.append(result)
        by_category[category].append(result)
        total_time += result["parse_time_ms"]

    print()  # Clear progress line

    # Compute statistics
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed_diff = sum(1 for r in results if r["status"] == "DIFF")
    failed_error = sum(1 for r in results if r["status"] == "ERROR")

    summary = {
        "total_tests": len(pairs),
        "passed": passed,
        "failed_diff": failed_diff,
        "failed_error": failed_error,
        "pass_rate": round(passed / len(pairs) * 100, 2) if pairs else 0,
        "total_time_ms": round(total_time, 2),
        "avg_time_ms": round(total_time / len(pairs), 2) if pairs else 0,
        "security_profile": security_profile,
        "by_category": {},
        "results": results,
    }

    # Category statistics
    for category, cat_results in by_category.items():
        cat_passed = sum(1 for r in cat_results if r["status"] == "PASS")
        summary["by_category"][category] = {
            "total": len(cat_results),
            "passed": cat_passed,
            "failed": len(cat_results) - cat_passed,
            "pass_rate": round(cat_passed / len(cat_results) * 100, 2),
        }

    return summary


def print_summary(summary: dict, verbose: bool = False):
    """Print test summary."""
    print("\n" + "=" * 80)
    print("BASELINE TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests:    {summary['total_tests']}")
    print(f"Passed:         {summary['passed']} ({summary['pass_rate']}%)")
    print(f"Failed (diff):  {summary['failed_diff']}")
    print(f"Failed (error): {summary['failed_error']}")
    print(f"Total time:     {summary['total_time_ms']:.2f} ms")
    print(f"Average time:   {summary['avg_time_ms']:.2f} ms per test")
    print(f"Profile:        {summary['security_profile']}")
    print()

    # Category breakdown
    print("BY CATEGORY:")
    print("-" * 80)
    for category, stats in sorted(summary["by_category"].items()):
        status = "✓" if stats["passed"] == stats["total"] else "✗"
        print(f"{status} {category:30s} {stats['passed']:3d}/{stats['total']:3d} ({stats['pass_rate']:6.2f}%)")

    print()

    # Show failures
    failures = [r for r in summary["results"] if r["status"] != "PASS"]
    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        print("-" * 80)

        for failure in failures[:20]:  # Show first 20 failures
            print(f"\n{failure['status']}: {failure['md_file']}")
            if failure.get("error"):
                print(f"  Error: {failure['error']}")
            if failure.get("differences"):
                for diff in failure["differences"][:3]:  # Show first 3 differences
                    print(f"  - {diff}")

        if len(failures) > 20:
            print(f"\n... and {len(failures) - 20} more failures (see JSON output)")

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run baseline tests for docpipe parser")
    parser.add_argument(
        "--profile",
        default="moderate",
        choices=["strict", "moderate", "permissive"],
        help="Security profile to use",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output JSON file for results",
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path(__file__).parent / "test_mds",
        help="Test directory (default: tools/test_mds)",
    )

    args = parser.parse_args()

    # Ensure test directory exists
    if not args.test_dir.exists():
        print(f"Error: Test directory not found: {args.test_dir}", file=sys.stderr)
        sys.exit(1)

    # Run tests
    start_time = time.time()
    summary = run_all_tests(args.test_dir, args.profile, args.verbose)
    elapsed = time.time() - start_time

    summary["elapsed_seconds"] = round(elapsed, 2)

    # Print summary
    print_summary(summary, args.verbose)

    # Save JSON output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\nDetailed results saved to: {args.output}")

    # Exit with appropriate code
    if summary["failed_diff"] > 0 or summary["failed_error"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
