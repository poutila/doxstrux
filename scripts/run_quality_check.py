#!/usr/bin/env python3
"""
Quality Check Runner for docpipe Test Suite

This script automates the execution of docpipe tests against a golden standard,
comparing actual results against predicted outcomes from a markdown table.

Usage:
    python run_quality_check.py <path_to_predicted_table>
    python run_quality_check.py quality_tests_run/plans/TEST_PREDICTED_TABLE.md --dry-run
    python run_quality_check.py quality_tests_run/plans/TEST_PREDICTED_TABLE.md --verbose
    python run_quality_check.py quality_tests_run/plans/TEST_PREDICTED_TABLE.md --rebaseline
"""

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TestPrediction:
    """Represents a single test prediction from the markdown table."""

    def __init__(self, file: str, expected_outcome: str, justification: str):
        self.file = file
        self.expected_outcome = expected_outcome
        self.justification = justification
        self.category = self._extract_category()

    def _extract_category(self) -> str:
        """Extract test category from file path."""
        parts = self.file.split("/")
        if len(parts) > 1:
            return parts[0]
        return "uncategorized"

    def expects_violations(self) -> bool:
        """Check if this test expects violations."""
        outcome_lower = self.expected_outcome.lower()
        return not any(
            phrase in outcome_lower
            for phrase in ["no violations", "minimal violations", "should pass", "sanitized"]
        )


class TestResult:
    """Represents the actual result of running docpipe on a test file."""

    def __init__(
        self,
        file: str,
        status: str,
        violations: int,
        error_count: int,
        warning_count: int,
        raw_output: str,
    ):
        self.file = file
        self.status = status
        self.violations = violations
        self.error_count = error_count
        self.warning_count = warning_count
        self.raw_output = raw_output
        self.has_violations = violations > 0


class QualityCheckRunner:
    """Main test runner class."""

    def __init__(
        self,
        predictions_file: Path,
        dry_run: bool = False,
        verbose: bool = False,
        rebaseline: bool = False,
    ):
        self.predictions_file = predictions_file
        self.dry_run = dry_run
        self.verbose = verbose
        self.rebaseline = rebaseline
        self.predictions: list[TestPrediction] = []
        self.results: list[TestResult] = []
        self.timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        self.output_dir = Path("quality_tests_run/runs") / f"{self.timestamp}_q_check"
        self.checksums_file = Path("quality_tests_run/plans/CHECKSUMS_BASELINE.json")
        self.golden_standard = "docs/standards/CLAUDE_MD_REQUIREMENTS.md"

    def setup_output_directory(self):
        """Create output directory structure."""
        if not self.dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "raw_results").mkdir(exist_ok=True)
            logger.info(f"Created output directory: {self.output_dir}")

    def load_predictions(self):
        """Load predictions from markdown table."""
        logger.info(f"Loading predictions from: {self.predictions_file}")

        with open(self.predictions_file) as f:
            content = f.read()

        # Extract table rows (skip headers and category rows)
        table_pattern = r"^\| ([^|]+) \| ([^|]+) \| ([^|]+) \|$"

        for line in content.split("\n"):
            match = re.match(table_pattern, line.strip())
            if match:
                file, expected, justification = [x.strip() for x in match.groups()]

                # Skip header rows and category separators
                if file in [
                    "File",
                    "---",
                    "**test_claudes/**",
                    "**test_claude_semantic_test_variants/**",
                    "**test_edit_regression_tests/**",
                    "**test_false_positives/**",
                    "**test_foul_play/**",
                    "**test_invalid_input/**",
                ]:
                    continue

                # Convert relative paths to full paths
                if not file.startswith("test_"):
                    file = f"src/docpipe/quality_tests/{file}"
                else:
                    file = f"src/docpipe/quality_tests/{file}"

                self.predictions.append(TestPrediction(file, expected, justification))

        logger.info(f"Loaded {len(self.predictions)} predictions")

    def verify_checksums(self) -> dict[str, str]:
        """Verify file checksums against baseline."""
        if not self.checksums_file.exists():
            logger.warning("No checksums baseline found")
            return {}

        with open(self.checksums_file) as f:
            baseline_checksums = json.load(f)

        current_checksums = {}
        changes = []

        for prediction in self.predictions:
            file_path = Path(prediction.file)
            if file_path.exists():
                with open(file_path, "rb") as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                    current_checksums[file_path.name] = current_hash

                baseline_key = str(file_path).replace("src/docpipe/quality_tests/", "")
                if baseline_key in baseline_checksums:
                    if baseline_checksums[baseline_key] != current_hash:
                        changes.append(f"Changed: {file_path}")
                else:
                    changes.append(f"Added: {file_path}")

        if changes:
            logger.warning(f"Found {len(changes)} checksum changes:")
            for change in changes[:5]:  # Show first 5
                logger.warning(f"  {change}")
            if len(changes) > 5:
                logger.warning(f"  ... and {len(changes) - 5} more")

        return current_checksums

    def run_docpipe(self, test_file: str) -> TestResult:
        """Run docpipe on a single test file."""
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would run: python -m docpipe {test_file} {self.golden_standard}"
            )
            return TestResult(test_file, "dry_run", 0, 0, 0, "")

        try:
            cmd = ["python", "-m", "docpipe", test_file, self.golden_standard]
            if self.verbose:
                logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)

            # Parse output to extract key metrics
            output = result.stdout + result.stderr

            # Extract status
            status_match = re.search(r"Overall Status: (\w+)", output)
            status = status_match.group(1) if status_match else "unknown"

            # Extract violation counts
            violations_match = re.search(r"Total Violations: (\d+)", output)
            violations = int(violations_match.group(1)) if violations_match else 0

            errors_match = re.search(r"Errors: (\d+)", output)
            errors = int(errors_match.group(1)) if errors_match else 0

            warnings_match = re.search(r"Warnings: (\d+)", output)
            warnings = int(warnings_match.group(1)) if warnings_match else 0

            return TestResult(test_file, status, violations, errors, warnings, output)

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout running docpipe on {test_file}")
            return TestResult(test_file, "timeout", 0, 0, 0, "TIMEOUT")
        except Exception as e:
            logger.error(f"Error running docpipe on {test_file}: {e}")
            return TestResult(test_file, "error", 0, 0, 0, str(e))

    def save_raw_result(self, result: TestResult):
        """Save raw docpipe output to JSON file."""
        if self.dry_run:
            return

        filename = Path(result.file).name.replace(".md", ".json")
        output_path = self.output_dir / "raw_results" / filename

        data = {
            "file": result.file,
            "status": result.status,
            "violations": result.violations,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "raw_output": result.raw_output,
            "timestamp": datetime.now().isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def compare_result(self, prediction: TestPrediction, result: TestResult) -> str:
        """Compare actual result with prediction."""
        expects_violations = prediction.expects_violations()
        has_violations = result.has_violations

        if expects_violations and has_violations:
            return "Pass"  # Expected violations and found them
        if not expects_violations and not has_violations:
            return "Pass"  # Expected clean and was clean
        if expects_violations and not has_violations:
            return "Fail"  # Expected violations but found none (false negative)
        if not expects_violations and has_violations:
            return "Fail"  # Expected clean but found violations (false positive)
        return "Partial"  # Edge case

    def run_tests(self):
        """Run all tests and collect results."""
        logger.info(f"Running {len(self.predictions)} tests...")

        for i, prediction in enumerate(self.predictions, 1):
            if self.verbose or i % 10 == 0:
                logger.info(f"Progress: {i}/{len(self.predictions)}")

            result = self.run_docpipe(prediction.file)
            self.results.append(result)
            self.save_raw_result(result)

    def generate_summary(self) -> dict:
        """Generate summary statistics."""
        if len(self.predictions) != len(self.results):
            logger.error("Mismatch between predictions and results count")
            return {}

        comparisons = []
        for pred, result in zip(self.predictions, self.results, strict=False):
            comparison = self.compare_result(pred, result)
            comparisons.append(
                {
                    "file": pred.file,
                    "expected": pred.expected_outcome,
                    "actual_status": result.status,
                    "actual_violations": result.violations,
                    "comparison": comparison,
                }
            )

        # Calculate metrics
        passes = sum(1 for c in comparisons if c["comparison"] == "Pass")
        fails = sum(1 for c in comparisons if c["comparison"] == "Fail")
        partials = sum(1 for c in comparisons if c["comparison"] == "Partial")

        # Identify false positives and negatives
        false_positives = [
            c
            for c in comparisons
            if c["comparison"] == "Fail"
            and c["actual_violations"] > 0
            and "no violations" in c["expected"].lower()
        ]
        false_negatives = [
            c
            for c in comparisons
            if c["comparison"] == "Fail"
            and c["actual_violations"] == 0
            and "no violations" not in c["expected"].lower()
        ]

        summary = {
            "total_tests": len(self.predictions),
            "passes": passes,
            "fails": fails,
            "partials": partials,
            "pass_rate": f"{(passes / len(self.predictions) * 100):.1f}%",
            "false_positives": len(false_positives),
            "false_negatives": len(false_negatives),
            "comparisons": comparisons,
            "timestamp": self.timestamp,
        }

        return summary

    def save_summary(self, summary: dict):
        """Save test run summary to markdown file."""
        if self.dry_run:
            logger.info("[DRY RUN] Would save summary")
            return

        output_path = self.output_dir / "TEST_RUN_SUMMARY.md"

        with open(output_path, "w") as f:
            f.write("# Test Run Summary\n\n")
            f.write(f"**Timestamp**: {summary['timestamp']}\n\n")
            f.write("## Overall Results\n\n")
            f.write(f"- **Total Tests**: {summary['total_tests']}\n")
            f.write(f"- **Passes**: {summary['passes']}\n")
            f.write(f"- **Fails**: {summary['fails']}\n")
            f.write(f"- **Partials**: {summary['partials']}\n")
            f.write(f"- **Pass Rate**: {summary['pass_rate']}\n")
            f.write(f"- **False Positives**: {summary['false_positives']}\n")
            f.write(f"- **False Negatives**: {summary['false_negatives']}\n\n")

            f.write("## Detailed Results\n\n")
            f.write("| File | Expected | Status | Violations | Result |\n")
            f.write("|------|----------|--------|------------|--------|\n")

            for comp in summary["comparisons"]:
                file_name = Path(comp["file"]).name
                expected_short = (
                    comp["expected"][:50] + "..."
                    if len(comp["expected"]) > 50
                    else comp["expected"]
                )
                f.write(
                    f"| {file_name} | {expected_short} | {comp['actual_status']} | "
                    f"{comp['actual_violations']} | {comp['comparison']} |\n"
                )

        logger.info(f"Summary saved to: {output_path}")

    def rebaseline_checksums(self, current_checksums: dict[str, str]):
        """Update the baseline checksums file."""
        if not self.rebaseline:
            return

        logger.info("Updating checksums baseline...")
        with open(self.checksums_file, "w") as f:
            json.dump(current_checksums, f, indent=2)
        logger.info("Checksums baseline updated")

    def run(self):
        """Main execution flow."""
        self.setup_output_directory()
        self.load_predictions()
        current_checksums = self.verify_checksums()
        self.run_tests()
        summary = self.generate_summary()
        self.save_summary(summary)

        if self.rebaseline and current_checksums:
            self.rebaseline_checksums(current_checksums)

        # Print summary to console
        logger.info("=" * 60)
        logger.info("TEST RUN COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Pass Rate: {summary.get('pass_rate', 'N/A')}")
        logger.info(f"False Positives: {summary.get('false_positives', 0)}")
        logger.info(f"False Negatives: {summary.get('false_negatives', 0)}")

        if not self.dry_run:
            logger.info(f"Full results saved to: {self.output_dir}")

        # Exit with appropriate code
        if summary.get("fails", 0) > 0:
            sys.exit(1)
        else:
            sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run docpipe quality checks")
    parser.add_argument("predictions_file", help="Path to TEST_PREDICTED_TABLE.md")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without executing"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--rebaseline", action="store_true", help="Update checksums baseline")

    args = parser.parse_args()

    runner = QualityCheckRunner(
        Path(args.predictions_file),
        dry_run=args.dry_run,
        verbose=args.verbose,
        rebaseline=args.rebaseline,
    )

    runner.run()


if __name__ == "__main__":
    main()
