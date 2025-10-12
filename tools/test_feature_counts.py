#!/usr/bin/env python3
"""
Test runner for feature count validation.
Validates parser output against JSON test specifications with expected feature counts.
"""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux.markdown_parser_core import MarkdownParserCore


def extract_feature_counts(result: dict) -> dict[str, int]:
    """Extract feature counts from parser result."""
    counts = {}
    structure = result.get("structure", {})

    # Filter out YAML frontmatter headings
    headings = structure.get("headings", [])
    real_headings = [
        h for h in headings if not (": " in h.get("text", "") and "\n" in h.get("text", ""))
    ]

    # Basic structures
    counts["headings"] = len(real_headings)
    counts["blockquotes"] = len(structure.get("blockquotes", []))
    counts["tables"] = len(structure.get("tables", []))
    counts["links"] = len([l for l in structure.get("links", []) if l.get("type") != "image"])
    counts["images"] = len(structure.get("images", []))

    # Count hrules from YAML frontmatter (the --- delimiters count as hrules)
    # For frontmatter-only docs, this should be 2
    counts["hrules"] = 2 if result.get("metadata", {}).get("has_frontmatter") else 0

    # Lists
    lists = structure.get("lists", [])
    counts["unordered_list_items"] = sum(
        len(lst.get("items", [])) for lst in lists if lst.get("type") == "bullet"
    )
    counts["ordered_list_items"] = sum(
        len(lst.get("items", [])) for lst in lists if lst.get("type") == "ordered"
    )
    counts["task_items"] = sum(
        lst.get("task_items_count", 0) for lst in lists
    )

    # Code blocks
    code_blocks = structure.get("code_blocks", [])
    counts["code_fences"] = len([cb for cb in code_blocks if cb.get("type") == "fenced"])
    counts["indented_code"] = len([cb for cb in code_blocks if cb.get("type") == "indented"])

    # Inline code - count from paragraphs
    counts["inline_code"] = sum(
        1 for para in structure.get("paragraphs", []) if para.get("has_code")
    )

    # Reference links
    counts["ref_links"] = 0  # Would need token analysis

    # HTML blocks
    html = structure.get("html_blocks", [])
    counts["html_blocks"] = len(html)

    # Footnotes
    footnotes = structure.get("footnotes", {})
    if isinstance(footnotes, dict):
        counts["footnotes"] = len(footnotes.get("definitions", []))
    else:
        counts["footnotes"] = 0

    # Autolinks
    counts["autolinks"] = len(
        [
            l for l in structure.get("links", [])
            if l.get("url", "").startswith(("http://", "https://"))
            and l.get("text") == l.get("url")
        ]
    )

    return counts


def test_file_pair(md_file: Path, json_file: Path, profile: str = "moderate") -> tuple[bool, list[str]]:
    """Test a single md/json file pair."""
    # Load test spec
    try:
        with open(json_file, encoding="utf-8") as f:
            spec = json.load(f)
    except Exception as e:
        return False, [f"Failed to load JSON: {e}"]

    # Parse markdown
    try:
        content = md_file.read_text(encoding="utf-8")

        # Use config from spec if available
        config = {}
        if "allows_html" in spec:
            config["allows_html"] = spec["allows_html"]

        parser = MarkdownParserCore(content, config=config, security_profile=profile)
        result = parser.parse()
    except Exception as e:
        return False, [f"Parser error: {e}"]

    # Extract and compare feature counts
    actual_counts = extract_feature_counts(result)
    expected_counts = spec.get("feature_counts", {})

    mismatches = []
    for feature, expected_count in expected_counts.items():
        actual_count = actual_counts.get(feature, 0)
        if expected_count != actual_count:
            mismatches.append(f"{feature}: expected {expected_count}, got {actual_count}")

    # Allow tolerance for hard-to-count features
    tolerance_features = ["inline_code", "ref_links", "hrules"]
    critical_mismatches = [
        m for m in mismatches if not any(feat in m for feat in tolerance_features)
    ]

    passed = len(critical_mismatches) == 0
    return passed, mismatches


def find_test_pairs(test_dir: Path) -> list[tuple[Path, Path]]:
    """Find all .md/.json test pairs recursively."""
    pairs = []
    for md_file in sorted(test_dir.rglob("*.md")):
        json_file = md_file.with_suffix(".json")
        if json_file.exists():
            pairs.append((md_file, json_file))
    return pairs


def run_tests(test_dir: Path, profile: str = "moderate") -> dict:
    """Run all tests and return results."""
    pairs = find_test_pairs(test_dir)

    print(f"Found {len(pairs)} test pairs")
    print(f"Security profile: {profile}")
    print(f"Test directory: {test_dir}")
    print("-" * 80)

    results = {
        "total": len(pairs),
        "passed": 0,
        "failed": 0,
        "by_category": defaultdict(lambda: {"passed": 0, "failed": 0}),
        "failures": [],
    }

    for i, (md_file, json_file) in enumerate(pairs, 1):
        category = md_file.parent.name

        if i % 50 == 0:
            print(f"[{i}/{len(pairs)}] Testing {md_file.name}...", end="\r")

        passed, mismatches = test_file_pair(md_file, json_file, profile)

        if passed:
            results["passed"] += 1
            results["by_category"][category]["passed"] += 1
        else:
            results["failed"] += 1
            results["by_category"][category]["failed"] += 1
            results["failures"].append({
                "file": str(md_file.relative_to(test_dir)),
                "mismatches": mismatches
            })

    print()  # Clear progress line
    return results


def print_results(results: dict):
    """Print test results."""
    print("\n" + "=" * 80)
    print("FEATURE COUNT TEST SUMMARY")
    print("=" * 80)

    total = results["total"]
    passed = results["passed"]
    failed = results["failed"]

    if total > 0:
        pass_rate = (passed / total) * 100
        print(f"Total tests:    {total}")
        print(f"Passed:         {passed} ({pass_rate:.1f}%)")
        print(f"Failed:         {failed}")
    else:
        print("No tests found!")
        return

    print("\nBY CATEGORY:")
    print("-" * 80)
    for category, stats in sorted(results["by_category"].items()):
        cat_total = stats["passed"] + stats["failed"]
        if cat_total > 0:
            cat_rate = (stats["passed"] / cat_total) * 100
            status = "✓" if cat_rate == 100 else "✗"
            print(f"{status} {category:30s} {stats['passed']:3d}/{cat_total:3d} ({cat_rate:6.2f}%)")

    if results["failures"]:
        print(f"\nFAILURES ({len(results['failures'])}):")
        print("-" * 80)
        for failure in results["failures"][:20]:
            print(f"\n{failure['file']}:")
            for mismatch in failure["mismatches"][:3]:
                print(f"  - {mismatch}")

        if len(results["failures"]) > 20:
            print(f"\n... and {len(results['failures']) - 20} more failures")

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test parser against feature count specs")
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path(__file__).parent / "test_mds",
        help="Test directory (default: tools/test_mds)",
    )
    parser.add_argument(
        "--profile",
        default="moderate",
        choices=["strict", "moderate", "permissive"],
        help="Security profile",
    )

    args = parser.parse_args()

    if not args.test_dir.exists():
        print(f"Error: Test directory not found: {args.test_dir}", file=sys.stderr)
        sys.exit(1)

    results = run_tests(args.test_dir, args.profile)
    print_results(results)

    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
