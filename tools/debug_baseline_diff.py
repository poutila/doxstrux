#!/usr/bin/env python3
"""Debug baseline differences.

Compare current parser output against a stored baseline JSON file.

Usage:
    python tools/debug_baseline_diff.py path/to/file.md path/to/baseline.json

Example:
    python tools/debug_baseline_diff.py \\
        tools/test_mds/01_edge_cases/tasks_01.md \\
        tools/baseline_outputs/01_edge_cases/tasks_01.baseline.json
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux.markdown_parser_core import MarkdownParserCore


def compare_dicts(d1: dict, d2: dict, path: str = "") -> list[str]:
    """Deep compare two dicts and return list of differences."""
    diffs = []
    all_keys = set(d1.keys()) | set(d2.keys())
    for key in sorted(all_keys):
        new_path = f"{path}.{key}" if path else key
        if key not in d1:
            diffs.append(f"Missing in current: {new_path}")
        elif key not in d2:
            diffs.append(f"Missing in baseline: {new_path}")
        elif type(d1[key]) != type(d2[key]):
            diffs.append(f"Type mismatch at {new_path}: {type(d1[key]).__name__} vs {type(d2[key]).__name__}")
        elif isinstance(d1[key], dict):
            diffs.extend(compare_dicts(d1[key], d2[key], new_path))
        elif isinstance(d1[key], list):
            if len(d1[key]) != len(d2[key]):
                diffs.append(f"List length mismatch at {new_path}: {len(d1[key])} vs {len(d2[key])}")
                # Show first few items
                print(f"\nCurrent {new_path} ({len(d1[key])} items):", d1[key][:3] if len(d1[key]) > 0 else "[]")
                print(f"Baseline {new_path} ({len(d2[key])} items):", d2[key][:3] if len(d2[key]) > 0 else "[]")
        elif d1[key] != d2[key]:
            diffs.append(f"Value mismatch at {new_path}: {repr(d1[key])[:100]} vs {repr(d2[key])[:100]}")
    return diffs


def debug_structure_details(result: dict, baseline: dict, structure_key: str) -> None:
    """Print detailed comparison for a specific structure key (lists, tasklists)."""
    print(f"\n=== Checking {structure_key} ===")
    if structure_key not in result["structure"] or structure_key not in baseline["structure"]:
        print(f"  Missing '{structure_key}' in one or both outputs")
        return

    result_items = result["structure"][structure_key]
    baseline_items = baseline["structure"][structure_key]

    print(f"Result {structure_key}: {len(result_items)}")
    print(f"Baseline {structure_key}: {len(baseline_items)}")

    if result_items and baseline_items:
        print(f"\nResult {structure_key}[0] keys:", list(result_items[0].keys()))
        print(f"Baseline {structure_key}[0] keys:", list(baseline_items[0].keys()))

        if result_items[0].get("items") and baseline_items[0].get("items"):
            print(f"\nResult {structure_key}[0] item[0] keys:", list(result_items[0]["items"][0].keys()))
            print(f"Baseline {structure_key}[0] item[0] keys:", list(baseline_items[0]["items"][0].keys()))

            print(f"\nResult {structure_key}[0] item[0]:")
            print(json.dumps(result_items[0]["items"][0], indent=2)[:500])
            print(f"\nBaseline {structure_key}[0] item[0]:")
            print(json.dumps(baseline_items[0]["items"][0], indent=2)[:500])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Debug baseline differences between current parser and stored JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/debug_baseline_diff.py file.md baseline.json
  python tools/debug_baseline_diff.py tools/test_mds/example.md tools/baseline_outputs/example.baseline.json
"""
    )
    parser.add_argument("test_file", type=Path, help="Path to .md file to parse")
    parser.add_argument("baseline_file", type=Path, help="Path to baseline .json file")
    parser.add_argument("--max-diffs", type=int, default=30, help="Maximum differences to show (default: 30)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed structure comparison")

    args = parser.parse_args()

    # Validate inputs
    if not args.test_file.exists():
        print(f"❌ Error: Test file not found: {args.test_file}", file=sys.stderr)
        return 1

    if not args.baseline_file.exists():
        print(f"❌ Error: Baseline file not found: {args.baseline_file}", file=sys.stderr)
        return 1

    # Read content
    try:
        content = args.test_file.read_text(encoding="utf-8")
    except OSError as e:
        print(f"❌ Error reading test file: {e}", file=sys.stderr)
        return 1

    # Parse with current parser
    try:
        parser_instance = MarkdownParserCore(content)
        result = parser_instance.parse()
    except Exception as e:
        print(f"❌ Error parsing markdown: {e}", file=sys.stderr)
        return 1

    # Read baseline
    try:
        baseline = json.loads(args.baseline_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing baseline JSON: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"❌ Error reading baseline file: {e}", file=sys.stderr)
        return 1

    # Compare structure
    print("=== Comparing structure ===")
    diffs = compare_dicts(result["structure"], baseline["structure"])

    for diff in diffs[:args.max_diffs]:
        print(diff)

    if len(diffs) > args.max_diffs:
        print(f"\n... and {len(diffs) - args.max_diffs} more differences")

    if not diffs:
        print("✅ No differences found in structure!")

        if args.verbose:
            debug_structure_details(result, baseline, "lists")
            debug_structure_details(result, baseline, "tasklists")

        return 0

    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
