#!/usr/bin/env python3
"""
Validate parity against baseline.

This tool compares current parser output against the baseline,
ensuring byte-identical output (100% parity requirement).

Usage:
    # After making changes
    python tools/validate_parity.py \\
        --baseline=baseline/v0_current.json \\
        --strict

    # Compare two baseline files
    python tools/validate_parity.py \\
        --baseline=baseline/v0_current.json \\
        --compare=baseline/phase1_output.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from doxstrux import parse_markdown_file


def deep_compare(obj1: Any, obj2: Any, path: str = "root") -> list[str]:
    """Deep compare two objects and return list of differences.

    Args:
        obj1: First object
        obj2: Second object
        path: Current path in object tree (for error messages)

    Returns:
        List of difference descriptions
    """
    diffs = []

    if type(obj1) != type(obj2):
        diffs.append(f"{path}: Type mismatch ({type(obj1).__name__} vs {type(obj2).__name__})")
        return diffs

    if isinstance(obj1, dict):
        # Check keys
        keys1 = set(obj1.keys())
        keys2 = set(obj2.keys())

        missing_in_2 = keys1 - keys2
        missing_in_1 = keys2 - keys1

        if missing_in_2:
            diffs.append(f"{path}: Keys in first but not second: {missing_in_2}")
        if missing_in_1:
            diffs.append(f"{path}: Keys in second but not first: {missing_in_1}")

        # Compare common keys
        for key in keys1 & keys2:
            diffs.extend(deep_compare(obj1[key], obj2[key], f"{path}.{key}"))

    elif isinstance(obj1, list):
        if len(obj1) != len(obj2):
            diffs.append(f"{path}: List length mismatch ({len(obj1)} vs {len(obj2)})")
            # Still compare common elements
            min_len = min(len(obj1), len(obj2))
        else:
            min_len = len(obj1)

        for i in range(min_len):
            diffs.extend(deep_compare(obj1[i], obj2[i], f"{path}[{i}]"))

    else:
        # Primitive comparison
        if obj1 != obj2:
            # Truncate long strings for readability
            str1 = str(obj1)[:100]
            str2 = str(obj2)[:100]
            diffs.append(f"{path}: Value mismatch\n  Expected: {str1}\n  Got:      {str2}")

    return diffs


def validate_against_baseline(baseline_path: str, compare_path: str | None = None) -> tuple[int, int, list[dict]]:
    """Validate current code against baseline.

    Args:
        baseline_path: Path to baseline JSON
        compare_path: Optional path to comparison baseline (if None, parse current code)

    Returns:
        (passed_count, total_count, failures_list)
    """
    # Load baseline
    with open(baseline_path, 'r', encoding='utf-8') as f:
        baseline = json.load(f)

    corpus_path = Path(baseline['metadata']['corpus_path'])
    profile = baseline['metadata']['profile']
    config = baseline['metadata']['config']

    print(f"📊 Validating against baseline...")
    print(f"  Baseline: {baseline_path}")
    print(f"  Profile: {profile}")
    print(f"  Files: {baseline['metadata']['corpus_file_count']}")

    if compare_path:
        # Compare two baseline files
        with open(compare_path, 'r', encoding='utf-8') as f:
            comparison = json.load(f)
        print(f"  Comparing: {compare_path}")
    else:
        # Parse current code
        comparison = None
        print(f"  Comparing: current code")

    passed = 0
    total = 0
    failures = []

    for file_path, baseline_data in baseline['outputs'].items():
        total += 1
        full_path = corpus_path / file_path

        if not full_path.exists():
            print(f"  ⚠️  [{total}] {file_path} - file not found")
            failures.append({
                'file': file_path,
                'error': 'File not found in corpus',
                'diffs': []
            })
            continue

        # Get comparison output
        if comparison:
            # Use comparison baseline
            if file_path not in comparison['outputs']:
                print(f"  ❌ [{total}] {file_path} - missing in comparison")
                failures.append({
                    'file': file_path,
                    'error': 'Missing in comparison baseline',
                    'diffs': []
                })
                continue
            current_output = comparison['outputs'][file_path]['output']
        else:
            # Parse with current code
            try:
                current_output = parse_markdown_file(full_path, config=config, security_profile=profile)
            except Exception as e:
                print(f"  ❌ [{total}] {file_path} - parse error: {e}")
                failures.append({
                    'file': file_path,
                    'error': f'Parse error: {e}',
                    'diffs': []
                })
                continue

        # Compare outputs
        baseline_output = baseline_data['output']
        diffs = deep_compare(baseline_output, current_output, f"{file_path}:output")

        if diffs:
            print(f"  ❌ [{total}] {file_path} - {len(diffs)} differences")
            failures.append({
                'file': file_path,
                'error': None,
                'diffs': diffs[:10]  # Limit to first 10 diffs per file
            })
        else:
            print(f"  ✅ [{total}] {file_path}")
            passed += 1

    return passed, total, failures


def main():
    parser = argparse.ArgumentParser(description='Validate parity against baseline')
    parser.add_argument('--baseline', required=True, help='Path to baseline JSON')
    parser.add_argument('--compare', help='Optional path to comparison baseline')
    parser.add_argument('--strict', action='store_true', help='Exit with code 1 if any failures')
    parser.add_argument('--verbose', action='store_true', help='Show all differences')

    args = parser.parse_args()

    try:
        passed, total, failures = validate_against_baseline(args.baseline, args.compare)

        print(f"\n📈 Parity Results:")
        print(f"  Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"  Failed: {len(failures)}/{total} ({len(failures)/total*100:.1f}%)")

        if failures:
            print(f"\n❌ Failures:")
            for failure in failures:
                print(f"\n  File: {failure['file']}")
                if failure['error']:
                    print(f"    Error: {failure['error']}")
                if failure['diffs']:
                    print(f"    Differences ({len(failure['diffs'])}):")
                    for diff in failure['diffs'][:5 if not args.verbose else None]:
                        print(f"      - {diff}")
                    if len(failure['diffs']) > 5 and not args.verbose:
                        print(f"      ... and {len(failure['diffs']) - 5} more (use --verbose)")

        if args.strict and failures:
            print(f"\n⚠️  Strict mode: Exiting with code 1 due to {len(failures)} failures")
            sys.exit(1)
        elif passed == total:
            print(f"\n✅ Perfect parity! All {total} files match baseline.")
            sys.exit(0)
        else:
            print(f"\n⚠️  Parity incomplete: {len(failures)} files differ from baseline")
            sys.exit(0 if not args.strict else 1)

    except Exception as e:
        print(f"\n❌ Error validating parity: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
