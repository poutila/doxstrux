#!/usr/bin/env python3
"""
Comprehensive test script for all markdown files in test_mds directory.
This script tests the markdown enricher with various edge cases and formats.
"""

import sys
import traceback
from pathlib import Path
from typing import Any

from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher


def check_nesting_depth(items: list, level: int = 0) -> int:
    """Recursively check the maximum nesting depth of list items."""
    if not items:
        return level - 1 if level > 0 else 0

    max_depth = level
    for item in items:
        if hasattr(item, "children") and item.children:
            child_depth = check_nesting_depth(item.children, level + 1)
            max_depth = max(max_depth, child_depth)

    return max_depth


def analyze_document(file_path: Path) -> dict[str, Any]:
    """Analyze a single markdown document and return statistics."""
    try:
        enricher = MarkdownDocEnricher(file_path)
        doc = enricher.extract_rich_doc()

        # Collect statistics
        stats = {
            "file": file_path.name,
            "status": "success",
            "sections": len(doc.sections),
            "code_blocks": len(doc.code_blocks),
            "code_languages": doc.meta.get("code_languages", []),
            "total_lists": 0,
            "list_types": {"bullet": 0, "ordered": 0, "task": 0},
            "max_nesting_depth": 0,
            "deep_nesting_sections": [],
            "tables_count": 0,
            "requirements_count": 0,
            "checklist_items_count": 0,
            "errors": [],
        }

        # Analyze each section
        for section in doc.sections:
            # Count lists and their types
            stats["total_lists"] += len(section.lists)
            for lst in section.lists:
                stats["list_types"][lst.type] += 1

                # Check nesting depth
                depth = check_nesting_depth(lst.items)
                stats["max_nesting_depth"] = max(stats["max_nesting_depth"], depth)

                if depth >= 2:  # 3-level nesting (0, 1, 2)
                    stats["deep_nesting_sections"].append(
                        {"section": section.title, "depth": depth + 1, "type": lst.type}
                    )

            # Count other elements
            stats["tables_count"] += len(section.tables)
            stats["requirements_count"] += len(section.requirements)
            stats["checklist_items_count"] += len(section.checklist_items)

        return stats

    except Exception as e:
        return {
            "file": file_path.name,
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
        }


def print_results(results: list[dict[str, Any]]) -> None:
    """Print formatted test results."""
    print("\n" + "=" * 80)
    print("📊 MARKDOWN ENRICHER COMPREHENSIVE TEST RESULTS")
    print("=" * 80)

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]

    print("\n📈 Overall Statistics:")
    print(f"  Total files tested: {len(results)}")
    print(f"  ✅ Successful: {len(successful)}")
    print(f"  ❌ Failed: {len(failed)}")

    if successful:
        print("\n✅ Successfully Processed Files:")
        print("-" * 40)

        for result in successful:
            print(f"\n📄 {result['file']}")
            print(f"  • Sections: {result['sections']}")
            print(f"  • Code blocks: {result['code_blocks']}")
            if result["code_languages"]:
                print(f"  • Languages: {', '.join(result['code_languages'])}")
            print(f"  • Lists: {result['total_lists']} total")
            if result["total_lists"] > 0:
                print(f"    - Bullet: {result['list_types']['bullet']}")
                print(f"    - Ordered: {result['list_types']['ordered']}")
                print(f"    - Task: {result['list_types']['task']}")
                print(f"    - Max nesting: {result['max_nesting_depth'] + 1} levels")
            if result["deep_nesting_sections"]:
                print(
                    f"  • Deep nesting (≥3 levels) in {len(result['deep_nesting_sections'])} sections:"
                )
                for item in result["deep_nesting_sections"][:3]:  # Show first 3
                    print(f"    - {item['section']}: {item['depth']} levels ({item['type']})")
            if result["tables_count"]:
                print(f"  • Tables: {result['tables_count']}")
            if result["requirements_count"]:
                print(f"  • Requirements: {result['requirements_count']}")
            if result["checklist_items_count"]:
                print(f"  • Checklist items: {result['checklist_items_count']}")

    if failed:
        print("\n❌ Failed Files:")
        print("-" * 40)

        for result in failed:
            print(f"\n📄 {result['file']}")
            print(f"  Error: {result['error_type']}: {result['error_message']}")
            if "--verbose" in sys.argv:
                print(f"  Traceback:\n{result['traceback']}")

    # Summary of capabilities
    print("\n🎯 Capability Summary:")
    print("-" * 40)

    if successful:
        max_depth_overall = max(r["max_nesting_depth"] for r in successful)
        total_lists = sum(r["total_lists"] for r in successful)
        total_code_blocks = sum(r["code_blocks"] for r in successful)
        all_languages = set()
        for r in successful:
            all_languages.update(r.get("code_languages", []))

        print(f"  ✅ Maximum nesting depth achieved: {max_depth_overall + 1} levels")
        print(f"  ✅ Total lists processed: {total_lists}")
        print(f"  ✅ Total code blocks extracted: {total_code_blocks}")
        if all_languages:
            print(f"  ✅ Code languages detected: {', '.join(sorted(all_languages))}")
        print(
            f"  ✅ Files with 3+ level nesting: {sum(1 for r in successful if r['max_nesting_depth'] >= 2)}"
        )

    print("\n" + "=" * 80)


def main():
    """Main test execution."""
    # Get test directory
    test_dir = Path("src/docpipe/loaders/test_mds")

    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        sys.exit(1)

    # Find all markdown files
    md_files = sorted(test_dir.glob("*.md"))

    if not md_files:
        print(f"❌ No markdown files found in {test_dir}")
        sys.exit(1)

    print(f"🔍 Found {len(md_files)} markdown files to test")
    print(f"📁 Directory: {test_dir}")

    # Test each file
    results = []
    for i, file_path in enumerate(md_files, 1):
        print(f"\n[{i}/{len(md_files)}] Testing: {file_path.name}...", end=" ")
        result = analyze_document(file_path)
        results.append(result)
        if result["status"] == "success":
            print("✅")
        else:
            print("❌")

    # Print results
    print_results(results)

    # Exit with error code if any failures
    failed_count = sum(1 for r in results if r["status"] == "error")
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} file(s) failed processing")
        sys.exit(1)
    else:
        print(f"\n✨ All {len(results)} files processed successfully!")


if __name__ == "__main__":
    main()
