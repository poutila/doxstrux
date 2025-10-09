#!/usr/bin/env python3
"""Protect and monitor critical test directories from deletion.

This script helps prevent the mysterious deletion of test directories
that has occurred multiple times in this project.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

# Critical directories that have been deleted before
# Now using pattern matching for test_* directories
PROTECTED_PATTERNS = [
    "test_*",  # All directories starting with test_
    "edit_regression_tests",  # Special case
    "claude_semantic_test_variants",  # Special case
]

# Files that should exist in each directory (minimum)
EXPECTED_CONTENTS = {
    "edit_regression_tests": ["Regression_Test_Case_Matrix.csv", ".integrity_baseline.json"],
    "test_claudes": ["claude_*.md"],
    "test_false_positives": ["*.md"],
    "test_fowl_play": ["*.md"],
    "claude_semantic_test_variants": ["v*.md"],
}


def calculate_directory_hash(directory: Path) -> str:
    """Calculate hash of directory contents for integrity checking."""
    files = sorted(directory.rglob("*") if directory.exists() else [])
    content = ""
    for file in files:
        if file.is_file():
            content += f"{file.relative_to(directory)}:{file.stat().st_size}\n"
    return hashlib.sha256(content.encode()).hexdigest()


def find_protected_directories() -> list[Path]:
    """Find all directories matching protected patterns."""
    project_root = Path(__file__).parent.parent
    protected_dirs = []

    # Check all patterns
    for pattern in PROTECTED_PATTERNS:
        if "*" in pattern:
            # It's a glob pattern - only keep directories
            for path in project_root.glob(pattern):
                if path.is_dir():
                    protected_dirs.append(path)
        else:
            # It's a specific directory
            dir_path = project_root / pattern
            if dir_path.exists() and dir_path.is_dir():
                protected_dirs.append(dir_path)

    return sorted(set(protected_dirs))


def check_protected_directories() -> dict[str, dict]:
    """Check status of all protected directories."""
    project_root = Path(__file__).parent.parent
    status = {}

    # Find all directories matching patterns
    protected_dirs = find_protected_directories()

    for dir_path in protected_dirs:
        dir_name = dir_path.name

        status[dir_name] = {
            "exists": dir_path.exists(),
            "path": str(dir_path),
            "file_count": 0,
            "hash": "",
            "missing_patterns": [],
        }

        if dir_path.exists():
            files = list(dir_path.glob("*"))
            status[dir_name]["file_count"] = len(files)
            status[dir_name]["hash"] = calculate_directory_hash(dir_path)

            # Check expected contents
            if dir_name in EXPECTED_CONTENTS:
                for pattern in EXPECTED_CONTENTS[dir_name]:
                    if not list(dir_path.glob(pattern)):
                        status[dir_name]["missing_patterns"].append(pattern)

    return status


def create_protection_report() -> str:
    """Create a detailed protection report."""
    status = check_protected_directories()

    report = [
        "# Test Directory Protection Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        "\n## Directory Status\n",
    ]

    missing_dirs = []
    warnings = []

    for dir_name, info in status.items():
        if info["exists"]:
            report.append(f"✅ **{dir_name}** - {info['file_count']} files")
            if info["missing_patterns"]:
                warnings.append(
                    f"{dir_name} missing expected files: {', '.join(info['missing_patterns'])}"
                )
        else:
            report.append(f"❌ **{dir_name}** - MISSING!")
            missing_dirs.append(dir_name)

    if missing_dirs:
        report.append("\n## 🚨 CRITICAL ALERT")
        report.append("\nThe following directories are MISSING:")
        for d in missing_dirs:
            report.append(f"- {d}")
        report.append("\nThese directories have been deleted before. Check backups!")

    if warnings:
        report.append("\n## ⚠️ Warnings")
        for w in warnings:
            report.append(f"- {w}")

    # Add protection measures
    report.append("\n## Protection Measures")
    report.append("\n1. **.gitignore** has been updated with exclusion rules (!directory/)")
    report.append("2. This script monitors directory integrity")
    report.append("3. Consider adding pre-commit hooks to verify directories exist")
    report.append("4. Regular backups recommended for these test directories")

    # Investigation hints
    report.append("\n## Investigation Hints")
    report.append("\nPossible causes of deletion:")
    report.append("- Git clean commands (git clean -fdx)")
    report.append("- Overzealous cleanup scripts")
    report.append("- IDE cleanup operations")
    report.append("- CI/CD pipeline cleanup steps")
    report.append("- Manual deletion by mistake")

    return "\n".join(report)


def save_integrity_baseline():
    """Save current state as baseline for future checks."""
    baseline_file = Path(__file__).parent.parent / ".test_directory_baseline.json"
    status = check_protected_directories()

    baseline = {"created_at": datetime.now().isoformat(), "directories": status}

    with open(baseline_file, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"💾 Baseline saved to {baseline_file}")


def main():
    """Run protection check and generate report."""
    print("🛡️  Test Directory Protection Check")
    print("=" * 50)

    # Check status
    status = check_protected_directories()

    # Quick summary
    missing = sum(1 for d in status.values() if not d["exists"])
    total = len(status)

    print(f"\n📊 Summary: {total - missing}/{total} directories present")

    if missing > 0:
        print("\n🚨 ALERT: Missing directories detected!")

    # Generate full report
    report = create_protection_report()
    report_file = Path(__file__).parent.parent / "test_directory_protection_report.md"

    with open(report_file, "w") as f:
        f.write(report)

    print(f"\n📄 Full report saved to: {report_file}")

    # Save baseline
    save_integrity_baseline()

    # Return non-zero if directories missing
    return missing


if __name__ == "__main__":
    import sys

    sys.exit(main())
