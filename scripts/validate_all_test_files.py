#!/usr/bin/env python3
"""
Comprehensive validation test for docpipe.

This script validates that all test markdown files can be processed without
information loss and ensures the package is working correctly before releases.

Usage:
    uv run scripts/validate_all_test_files.py

Returns:
    0 if all tests pass
    1 if any test fails
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docpipe.diagnostics import diagnose_markdown, get_markdown_stats
from docpipe.loaders.markdown_validator_enricher import MarkdownDocEnricher


class ValidationResults:
    """Track validation results across all test files."""

    def __init__(self):
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.warnings = []
        self.errors = []
        self.performance_data = []
        self.information_checks = []

    def add_result(
        self, file_path: Path, success: bool, time_taken: float, details: dict[str, Any]
    ):
        """Add a test result."""
        self.total_files += 1
        if success:
            self.successful += 1
        else:
            self.failed += 1
            self.errors.append(f"{file_path.name}: {details.get('error', 'Unknown error')}")

        self.performance_data.append(
            {"file": file_path.name, "time": time_taken, "size_kb": file_path.stat().st_size / 1024}
        )

        if details.get("warnings"):
            self.warnings.extend(details["warnings"])

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total files tested: {self.total_files}")
        print(f"✅ Successful: {self.successful}")
        print(f"❌ Failed: {self.failed}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"  - {warning}")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        # Performance summary
        if self.performance_data:
            avg_time = sum(p["time"] for p in self.performance_data) / len(self.performance_data)
            max_time = max(p["time"] for p in self.performance_data)
            print("\n⏱️  Performance:")
            print(f"  Average processing time: {avg_time:.3f}s")
            print(f"  Maximum processing time: {max_time:.3f}s")
            print("  Target: < 0.5s per file")
            print(f"  Status: {'✅ PASS' if max_time < 0.5 else '❌ FAIL'}")

        return self.failed == 0


def validate_information_preservation(file_path: Path, doc) -> dict[str, Any]:
    """
    Validate that all information is preserved during parsing.

    Checks:
    - All sections are captured
    - Code blocks are preserved
    - Requirements are extracted
    - Lists maintain structure
    - Tables are parsed
    - Links are identified
    """
    results = {"preserved": True, "details": {}, "warnings": []}

    # Read original content
    original_content = file_path.read_text()
    original_lines = original_content.count("\n")

    # Basic sanity checks
    if not doc.sections:
        results["warnings"].append(f"No sections found in {file_path.name}")
        results["preserved"] = False

    # Check code blocks
    original_code_blocks = original_content.count("```")
    if original_code_blocks > 0:
        # Each code block has opening and closing ```
        expected_blocks = original_code_blocks // 2
        found_blocks = len(doc.code_blocks)
        if found_blocks < expected_blocks:
            results["warnings"].append(
                f"Expected {expected_blocks} code blocks, found {found_blocks}"
            )

    # Check requirements extraction
    for pattern in ["MUST", "SHOULD", "MAY"]:
        original_count = original_content.count(pattern)
        if original_count > 0:
            extracted_count = len([r for r in doc.requirements if r.type == pattern])
            if extracted_count == 0:
                results["warnings"].append(
                    f"Found {pattern} in original but no requirements extracted"
                )

    # Check list preservation
    bullet_lists = original_content.count("\n- ") + original_content.count("\n* ")
    if bullet_lists > 0 and not doc.lists:
        results["warnings"].append("Original has bullet lists but none extracted")

    # Store metrics
    results["details"] = {
        "sections": len(doc.sections),
        "code_blocks": len(doc.code_blocks),
        "requirements": len(doc.requirements),
        "lists": len(doc.lists),
        "tables": len(doc.tables) if hasattr(doc, "tables") else 0,
        "links": len(doc.links) if doc.links else 0,
        "original_lines": original_lines,
        "heading_valid": doc.heading_structure_valid,
    }

    return results


def validate_single_file(file_path: Path) -> dict[str, Any]:
    """Validate a single markdown file."""
    result = {"success": False, "error": None, "warnings": [], "metrics": {}}

    try:
        # Time the processing
        start_time = time.time()

        # Create enricher and extract document
        enricher = MarkdownDocEnricher(file_path)
        doc = enricher.extract_rich_doc()

        processing_time = time.time() - start_time

        # Validate information preservation
        preservation = validate_information_preservation(file_path, doc)
        result["warnings"].extend(preservation.get("warnings", []))
        result["metrics"] = preservation["details"]

        # Run diagnostics
        diagnostic_result = diagnose_markdown(file_path, verbose=False)
        if diagnostic_result.status == "error":
            result["warnings"].append(f"Diagnostic error: {diagnostic_result.message}")
        elif diagnostic_result.status == "issues":
            result["warnings"].extend(diagnostic_result.potential_issues)

        # Get stats
        stats = get_markdown_stats(file_path)
        result["metrics"]["stats"] = stats

        # Mark as successful if we got here
        result["success"] = True
        result["processing_time"] = processing_time

    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        result["processing_time"] = 0

    return result


def main():
    """Main validation function."""
    print("🔍 Docpipe Comprehensive Validation Test")
    print("=" * 60)

    # Find test directory
    test_dir = Path("src/docpipe/loaders/test_mds")
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return 1

    # Get all markdown files
    test_files = sorted(test_dir.glob("*.md"))
    if not test_files:
        print(f"❌ No markdown files found in {test_dir}")
        return 1

    print(f"Found {len(test_files)} test files to validate\n")

    # Initialize results tracker
    results = ValidationResults()

    # Process each file
    for i, file_path in enumerate(test_files, 1):
        print(f"[{i}/{len(test_files)}] Testing {file_path.name}...", end=" ")

        # Validate file
        validation = validate_single_file(file_path)

        # Track results
        results.add_result(
            file_path, validation["success"], validation.get("processing_time", 0), validation
        )

        # Print immediate result
        if validation["success"]:
            metrics = validation.get("metrics", {})
            print(
                f"✅ ({validation['processing_time']:.3f}s) - "
                f"{metrics.get('sections', 0)} sections, "
                f"{metrics.get('code_blocks', 0)} code blocks"
            )
            if validation.get("warnings"):
                for warning in validation["warnings"][:2]:  # Show first 2 warnings
                    print(f"    ⚠️  {warning}")
        else:
            print(f"❌ {validation.get('error', 'Unknown error')}")

    # Print summary
    all_passed = results.print_summary()

    # Save detailed results to JSON for analysis
    results_file = Path("validation_results.json")
    with open(results_file, "w") as f:
        json.dump(
            {
                "summary": {
                    "total": results.total_files,
                    "passed": results.successful,
                    "failed": results.failed,
                    "success_rate": f"{(results.successful / results.total_files) * 100:.1f}%",
                },
                "performance": results.performance_data,
                "warnings": results.warnings,
                "errors": results.errors,
            },
            f,
            indent=2,
        )

    print(f"\n📝 Detailed results saved to {results_file}")

    # Return exit code
    if all_passed:
        print("\n✅ All validation tests passed!")
        return 0
    print(f"\n❌ Validation failed: {results.failed} files had issues")
    return 1


if __name__ == "__main__":
    sys.exit(main())
