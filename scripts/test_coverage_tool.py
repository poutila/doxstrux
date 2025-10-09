#!/usr/bin/env python3
"""
Comprehensive Test Coverage Analysis Tool

This tool consolidates functionality from multiple coverage scripts to provide:
- Source to test file mapping verification
- Stale test detection and cleanup
- Multiple output formats (console, markdown, json)
- CI/CD integration with proper exit codes
- Configurable paths and exclusions

Complies with CLAUDE.md requirements:
- 90% minimum coverage threshold
- Test naming conventions (test_<module_name>.py)
- Comprehensive reporting
"""

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@dataclass
class CoverageResult:
    """Results of coverage analysis."""

    total_source_files: int
    source_files_with_tests: int
    source_files_missing_tests: list[Path]
    stale_test_files: list[Path]
    coverage_percentage: float
    timestamp: str = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TestCoverageAnalyzer:
    """Comprehensive test coverage analyzer."""

    def __init__(
        self,
        src_dir: Path = Path("src"),
        test_dir: Path = Path("tests"),
        exclude_patterns: list[str] | None = None,
        verbose: bool = False,
    ):
        """Initialize analyzer with paths and options."""
        self.src_dir = src_dir
        self.test_dir = test_dir
        self.exclude_patterns = exclude_patterns or ["__init__.py", "__version__.py"]
        self.verbose = verbose

        # Validate directories exist
        if not self.src_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.src_dir}")
        if not self.test_dir.exists():
            raise FileNotFoundError(f"Test directory not found: {self.test_dir}")

    def should_exclude(self, path: Path) -> bool:
        """Check if file should be excluded from analysis."""
        # Exclude files matching patterns
        if any(pattern in path.name for pattern in self.exclude_patterns):
            return True

        # Exclude directories starting with __
        for part in path.parts:
            if part.startswith("__") and part != "__init__.py":
                return True

        return False

    def get_test_path(self, source_path: Path) -> Path:
        """Get expected test path for a source file."""
        # Get relative path from src directory
        relative_path = source_path.relative_to(self.src_dir)

        # Replace filename with test_filename
        test_filename = f"test_{source_path.name}"
        test_path = self.test_dir / relative_path.parent / test_filename

        return test_path

    def get_source_path(self, test_path: Path) -> Path:
        """Get expected source path for a test file."""
        # Get relative path from test directory
        relative_path = test_path.relative_to(self.test_dir)

        # Remove test_ prefix from filename
        if test_path.name.startswith("test_"):
            source_filename = test_path.name[5:]
        else:
            # Handle edge case where test file doesn't follow convention
            source_filename = test_path.name

        source_path = self.src_dir / relative_path.parent / source_filename

        return source_path

    def analyze(self) -> CoverageResult:
        """Perform comprehensive coverage analysis."""
        # Find all Python files
        source_files = {p for p in self.src_dir.rglob("*.py") if not self.should_exclude(p)}

        test_files = {p for p in self.test_dir.rglob("test_*.py") if not self.should_exclude(p)}

        # Find source files with and without tests
        source_with_tests = set()
        source_missing_tests = []

        for source_file in sorted(source_files):
            expected_test = self.get_test_path(source_file)
            if expected_test in test_files:
                source_with_tests.add(source_file)
            else:
                source_missing_tests.append(source_file)

        # Find stale test files
        stale_tests = []
        for test_file in sorted(test_files):
            expected_source = self.get_source_path(test_file)
            if expected_source not in source_files:
                stale_tests.append(test_file)

        # Calculate coverage
        total_source = len(source_files)
        coverage = (len(source_with_tests) / total_source * 100) if total_source > 0 else 0

        return CoverageResult(
            total_source_files=total_source,
            source_files_with_tests=len(source_with_tests),
            source_files_missing_tests=source_missing_tests,
            stale_test_files=stale_tests,
            coverage_percentage=coverage,
        )

    def format_console_output(self, result: CoverageResult) -> str:
        """Format results for console display."""
        output = []
        output.append("\n" + "=" * 70)
        output.append("📊 TEST COVERAGE ANALYSIS REPORT")
        output.append("=" * 70)
        output.append(f"Generated: {result.timestamp}")
        output.append(f"Source Directory: {self.src_dir}")
        output.append(f"Test Directory: {self.test_dir}")
        output.append("")

        # Summary
        output.append("📈 SUMMARY")
        output.append("-" * 50)
        output.append(f"Total Source Files: {result.total_source_files}")
        output.append(f"Files with Tests: {result.source_files_with_tests} ✅")
        output.append(f"Files Missing Tests: {len(result.source_files_missing_tests)} ❌")
        output.append(f"Stale Test Files: {len(result.stale_test_files)} 🗑️")
        output.append(f"Coverage: {result.coverage_percentage:.1f}%")

        # Coverage status
        if result.coverage_percentage >= 90:
            output.append("\n✅ Coverage meets 90% requirement!")
        else:
            output.append(
                f"\n❌ Coverage below 90% requirement (need {90 - result.coverage_percentage:.1f}% more)"
            )

        # Missing tests
        if result.source_files_missing_tests:
            output.append("\n\n❌ SOURCE FILES MISSING TESTS")
            output.append("-" * 50)
            for source_file in result.source_files_missing_tests:
                expected_test = self.get_test_path(source_file)
                output.append(f"  {source_file}")
                output.append(f"    → Expected test: {expected_test}")

        # Stale tests
        if result.stale_test_files:
            output.append("\n\n🗑️  STALE TEST FILES")
            output.append("-" * 50)
            for test_file in result.stale_test_files:
                expected_source = self.get_source_path(test_file)
                output.append(f"  {test_file}")
                output.append(f"    → Missing source: {expected_source}")

        # Action items
        output.append("\n\n📋 ACTION ITEMS")
        output.append("-" * 50)
        if result.source_files_missing_tests:
            output.append(f"1. Create {len(result.source_files_missing_tests)} missing test files")
        if result.stale_test_files:
            output.append(f"2. Review and remove {len(result.stale_test_files)} stale test files")
        if result.coverage_percentage < 90:
            output.append(
                f"3. Increase coverage by {90 - result.coverage_percentage:.1f}% to meet requirement"
            )

        if (
            not result.source_files_missing_tests
            and not result.stale_test_files
            and result.coverage_percentage >= 90
        ):
            output.append("✅ No action items - excellent test coverage!")

        output.append("\n" + "=" * 70)

        return "\n".join(output)

    def format_markdown_output(self, result: CoverageResult) -> str:
        """Format results as markdown report."""
        output = []
        output.append("# 📊 Test Coverage Analysis Report")
        output.append("")
        output.append(f"**Generated**: {result.timestamp}")
        output.append(f"**Source Directory**: `{self.src_dir}`")
        output.append(f"**Test Directory**: `{self.test_dir}`")
        output.append("")

        # Summary table
        output.append("## 📈 Summary")
        output.append("")
        output.append("| Metric | Value | Status |")
        output.append("|--------|-------|--------|")
        output.append(f"| Total Source Files | {result.total_source_files} | - |")
        output.append(f"| Files with Tests | {result.source_files_with_tests} | ✅ |")
        output.append(
            f"| Files Missing Tests | {len(result.source_files_missing_tests)} | {'❌' if result.source_files_missing_tests else '✅'} |"
        )
        output.append(
            f"| Stale Test Files | {len(result.stale_test_files)} | {'🗑️' if result.stale_test_files else '✅'} |"
        )
        output.append(
            f"| Coverage | {result.coverage_percentage:.1f}% | {'✅' if result.coverage_percentage >= 90 else '❌'} |"
        )
        output.append("")

        # Missing tests
        if result.source_files_missing_tests:
            output.append("## ❌ Source Files Missing Tests")
            output.append("")
            output.append("| Source File | Expected Test File |")
            output.append("|-------------|-------------------|")
            for source_file in result.source_files_missing_tests:
                expected_test = self.get_test_path(source_file)
                output.append(f"| `{source_file}` | `{expected_test}` |")
            output.append("")

        # Stale tests
        if result.stale_test_files:
            output.append("## 🗑️ Stale Test Files")
            output.append("")
            output.append("| Test File | Expected Source File |")
            output.append("|-----------|---------------------|")
            for test_file in result.stale_test_files:
                expected_source = self.get_source_path(test_file)
                output.append(f"| `{test_file}` | `{expected_source}` |")
            output.append("")

        # Recommendations
        output.append("## 📋 Recommendations")
        output.append("")
        if result.source_files_missing_tests:
            output.append(
                f"1. **Create {len(result.source_files_missing_tests)} missing test files** to improve coverage"
            )
        if result.stale_test_files:
            output.append(
                f"2. **Review and remove {len(result.stale_test_files)} stale test files** to maintain clean test suite"
            )
        if result.coverage_percentage < 90:
            output.append(
                f"3. **Increase coverage by {90 - result.coverage_percentage:.1f}%** to meet the 90% requirement"
            )

        if (
            not result.source_files_missing_tests
            and not result.stale_test_files
            and result.coverage_percentage >= 90
        ):
            output.append("✅ **Excellent!** Test coverage meets all requirements.")

        return "\n".join(output)

    def delete_stale_tests(self, stale_tests: list[Path], dry_run: bool = True) -> list[Path]:
        """Delete stale test files."""
        deleted = []

        for test_file in stale_tests:
            if dry_run:
                logger.info(f"[DRY RUN] Would delete: {test_file}")
            else:
                try:
                    test_file.unlink()
                    deleted.append(test_file)
                    logger.info(f"Deleted: {test_file}")
                except Exception as e:
                    logger.error(f"Failed to delete {test_file}: {e}")

        return deleted


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test coverage analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python test_coverage_tool.py
  
  # Custom directories
  python test_coverage_tool.py --src src/myproject --test tests/unit
  
  # Generate markdown report
  python test_coverage_tool.py --format markdown --output coverage_report.md
  
  # Delete stale tests (with confirmation)
  python test_coverage_tool.py --delete
  
  # CI/CD mode (exits with 1 if coverage < 90%)
  python test_coverage_tool.py --ci
""",
    )

    parser.add_argument(
        "--src", type=Path, default=Path("src"), help="Source directory path (default: src)"
    )
    parser.add_argument(
        "--test", type=Path, default=Path("tests"), help="Test directory path (default: tests)"
    )
    parser.add_argument(
        "--format",
        choices=["console", "markdown", "json"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument("--output", type=Path, help="Output file path (defaults to stdout)")
    parser.add_argument("--delete", action="store_true", help="Delete stale test files")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument("--ci", action="store_true", help="CI mode: exit with 1 if coverage < 90%")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=90.0,
        help="Minimum coverage percentage required (default: 90)",
    )

    args = parser.parse_args()

    try:
        # Create analyzer
        analyzer = TestCoverageAnalyzer(src_dir=args.src, test_dir=args.test, verbose=args.verbose)

        # Run analysis
        result = analyzer.analyze()

        # Handle stale test deletion
        if args.delete or args.dry_run:
            if result.stale_test_files:
                if not args.dry_run and not args.ci:
                    # Confirm deletion
                    response = input(
                        f"\nDelete {len(result.stale_test_files)} stale test files? [y/N]: "
                    )
                    if response.lower() != "y":
                        logger.info("Deletion cancelled.")
                        args.delete = False

                if args.delete or args.dry_run:
                    analyzer.delete_stale_tests(result.stale_test_files, dry_run=args.dry_run)

        # Format output
        if args.format == "console":
            output = analyzer.format_console_output(result)
        elif args.format == "markdown":
            output = analyzer.format_markdown_output(result)
        elif args.format == "json":
            output = json.dumps(asdict(result), indent=2, default=str)

        # Write output
        if args.output:
            args.output.write_text(output)
            logger.info(f"Report written to: {args.output}")
        else:
            print(output)

        # CI mode exit code
        if args.ci and result.coverage_percentage < args.min_coverage:
            logger.error(
                f"\n❌ Coverage {result.coverage_percentage:.1f}% is below required {args.min_coverage}%"
            )
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
