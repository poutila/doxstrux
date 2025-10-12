#!/usr/bin/env python3
"""
Generate Baseline Outputs for Docpipe Markdown Parser

This script generates baseline JSON outputs from the current parser implementation
for all .md files in the test suite. These outputs represent the current behavior
and can be used for regression testing during refactoring.

Usage:
    python tools/generate_baseline_outputs.py
    python tools/generate_baseline_outputs.py --profile moderate
    python tools/generate_baseline_outputs.py --output-dir tools/baseline_outputs
"""

import json
import sys
import time
from pathlib import Path
from typing import Any
from collections import defaultdict
from datetime import date, datetime
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux.markdown_parser_core import MarkdownParserCore


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime and date objects."""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def generate_baseline(md_file: Path, security_profile: str = "moderate") -> dict:
    """Generate baseline output for a single markdown file."""
    result = {
        "md_file": str(md_file.relative_to(md_file.parents[2])),
        "status": "unknown",
        "error": None,
        "output": None,
        "parse_time_ms": 0,
    }

    try:
        # Read and parse
        md_content = md_file.read_text(encoding="utf-8")

        start_time = time.perf_counter()
        parser = MarkdownParserCore(md_content, security_profile=security_profile)
        output = parser.parse()
        parse_time = (time.perf_counter() - start_time) * 1000

        result["status"] = "SUCCESS"
        result["output"] = output
        result["parse_time_ms"] = round(parse_time, 2)

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()

    return result


def find_md_files(test_dir: Path) -> list[Path]:
    """Find all .md files in the test directory."""
    return sorted(test_dir.rglob("*.md"))


def generate_all_baselines(
    test_dir: Path,
    output_dir: Path,
    security_profile: str = "moderate",
    verbose: bool = False
) -> dict:
    """Generate baseline outputs for all test files."""
    md_files = find_md_files(test_dir)

    print(f"Found {len(md_files)} markdown files")
    print(f"Security profile: {security_profile}")
    print(f"Test directory: {test_dir}")
    print(f"Output directory: {output_dir}")
    print("-" * 80)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    by_category = defaultdict(list)
    total_time = 0

    for i, md_file in enumerate(md_files, 1):
        category = md_file.parent.name

        if verbose or i % 50 == 0:
            print(f"[{i}/{len(md_files)}] Processing {md_file.name}...", end="\r")

        result = generate_baseline(md_file, security_profile)
        results.append(result)
        by_category[category].append(result)
        total_time += result["parse_time_ms"]

        # Save individual baseline output
        if result["status"] == "SUCCESS" and result["output"]:
            # Mirror directory structure
            rel_path = md_file.relative_to(test_dir)
            output_file = output_dir / rel_path.with_suffix(".baseline.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w", encoding="utf-8") as f:
                json.dump(result["output"], f, indent=2, sort_keys=True, cls=DateTimeEncoder)

    print()  # Clear progress line

    # Compute statistics
    successful = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "ERROR")

    summary = {
        "total_files": len(md_files),
        "successful": successful,
        "failed": failed,
        "success_rate": round(successful / len(md_files) * 100, 2) if md_files else 0,
        "total_time_ms": round(total_time, 2),
        "avg_time_ms": round(total_time / len(md_files), 2) if md_files else 0,
        "security_profile": security_profile,
        "output_directory": str(output_dir),
        "by_category": {},
        "results": results,
    }

    # Category statistics
    for category, cat_results in by_category.items():
        cat_success = sum(1 for r in cat_results if r["status"] == "SUCCESS")
        summary["by_category"][category] = {
            "total": len(cat_results),
            "successful": cat_success,
            "failed": len(cat_results) - cat_success,
            "success_rate": round(cat_success / len(cat_results) * 100, 2),
        }

    return summary


def print_summary(summary: dict, verbose: bool = False):
    """Print generation summary."""
    print("\n" + "=" * 80)
    print("BASELINE GENERATION SUMMARY")
    print("=" * 80)
    print(f"Total files:    {summary['total_files']}")
    print(f"Successful:     {summary['successful']} ({summary['success_rate']}%)")
    print(f"Failed:         {summary['failed']}")
    print(f"Total time:     {summary['total_time_ms']:.2f} ms")
    print(f"Average time:   {summary['avg_time_ms']:.2f} ms per file")
    print(f"Profile:        {summary['security_profile']}")
    print(f"Output dir:     {summary['output_directory']}")
    print()

    # Category breakdown
    print("BY CATEGORY:")
    print("-" * 80)
    for category, stats in sorted(summary["by_category"].items()):
        status = "✓" if stats["successful"] == stats["total"] else "✗"
        print(f"{status} {category:30s} {stats['successful']:3d}/{stats['total']:3d} ({stats['success_rate']:6.2f}%)")

    print()

    # Show failures
    failures = [r for r in summary["results"] if r["status"] != "SUCCESS"]
    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        print("-" * 80)

        for failure in failures[:20]:  # Show first 20 failures
            print(f"\nERROR: {failure['md_file']}")
            print(f"  {failure['error']}")

        if len(failures) > 20:
            print(f"\n... and {len(failures) - 20} more failures (see JSON output)")

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate baseline outputs for docpipe parser")
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
        "--summary-output",
        type=Path,
        help="Output JSON file for summary",
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path(__file__).parent / "test_mds",
        help="Test directory (default: tools/test_mds)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "baseline_outputs",
        help="Output directory for baseline files (default: tools/baseline_outputs)",
    )

    args = parser.parse_args()

    # Ensure test directory exists
    if not args.test_dir.exists():
        print(f"Error: Test directory not found: {args.test_dir}", file=sys.stderr)
        sys.exit(1)

    # Generate baselines
    start_time = time.time()
    summary = generate_all_baselines(
        args.test_dir,
        args.output_dir,
        args.profile,
        args.verbose
    )
    elapsed = time.time() - start_time

    summary["elapsed_seconds"] = round(elapsed, 2)

    # Print summary
    print_summary(summary, args.verbose)

    # Save summary JSON
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_output.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, cls=DateTimeEncoder)
        print(f"\nSummary saved to: {args.summary_output}")

    # Exit with appropriate code
    if summary["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
