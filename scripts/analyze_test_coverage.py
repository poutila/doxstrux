#!/usr/bin/env python3
"""Analyze test coverage between src/ and tests/ directories."""

import os
from pathlib import Path


def get_python_files(directory: str, exclude_init: bool = True) -> list[Path]:
    """Get all Python files in a directory, optionally excluding __init__.py."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and directories starting with __
        dirs[:] = [d for d in dirs if not d.startswith("__")]

        for file in files:
            if file.endswith(".py"):
                if exclude_init and file == "__init__.py":
                    continue
                if file == "__version__.py":  # Also exclude version files
                    continue
                python_files.append(Path(root) / file)

    return sorted(python_files)


def get_relative_path(file_path: Path, base_dir: str) -> Path:
    """Get relative path from base directory."""
    return file_path.relative_to(base_dir)


def src_to_test_path(src_path: Path) -> Path:
    """Convert src path to expected test path."""
    # Remove 'src/' prefix and add 'tests/' prefix
    relative = src_path.relative_to("src")
    # Add 'test_' prefix to filename
    test_filename = f"test_{relative.name}"
    # Construct test path
    return Path("tests") / relative.parent / test_filename


def test_to_src_path(test_path: Path) -> Path:
    """Convert test path to expected src path."""
    # Remove 'tests/' prefix
    relative = test_path.relative_to("tests")
    # Remove 'test_' prefix from filename
    if relative.name.startswith("test_"):
        src_filename = relative.name[5:]  # Remove 'test_' prefix
    else:
        src_filename = relative.name
    # Construct src path
    return Path("src") / relative.parent / src_filename


def analyze_coverage() -> tuple[list[Path], list[Path], list[Path], list[Path]]:
    """Analyze test coverage and return findings."""
    # Get all source files (excluding __init__.py and __version__.py)
    src_files = get_python_files("src", exclude_init=True)

    # Get all test files (excluding __init__.py)
    test_files = get_python_files("tests", exclude_init=True)
    test_files = [f for f in test_files if f.name.startswith("test_")]

    # Find source files without tests
    missing_tests = []
    covered_files = []

    for src_file in src_files:
        expected_test = src_to_test_path(src_file)
        if expected_test.exists():
            covered_files.append(src_file)
        else:
            missing_tests.append(src_file)

    # Find stale tests (tests without corresponding source files)
    stale_tests = []
    valid_tests = []

    for test_file in test_files:
        expected_src = test_to_src_path(test_file)
        if expected_src.exists():
            valid_tests.append(test_file)
        else:
            stale_tests.append(test_file)

    return covered_files, missing_tests, valid_tests, stale_tests


def print_report():
    """Print coverage analysis report."""
    covered, missing_tests, valid_tests, stale_tests = analyze_coverage()

    total_src_files = len(covered) + len(missing_tests)
    coverage_percentage = (len(covered) / total_src_files * 100) if total_src_files > 0 else 0

    print("=" * 80)
    print("TEST COVERAGE ANALYSIS REPORT")
    print("=" * 80)
    print()

    print("📊 Summary:")
    print(f"  • Total source files: {total_src_files}")
    print(f"  • ✅ Files with tests: {len(covered)} ({coverage_percentage:.1f}%)")
    print(f"  • ❌ Files missing tests: {len(missing_tests)}")
    print(f"  • 🗑️  Stale test files: {len(stale_tests)}")
    print()

    if missing_tests:
        print("❌ Source files MISSING tests:")
        print("-" * 40)
        for src_file in missing_tests:
            expected_test = src_to_test_path(src_file)
            print(f"  {src_file}")
            print(f"    → Expected test: {expected_test}")
        print()

    if stale_tests:
        print("🗑️  STALE test files (no corresponding source):")
        print("-" * 40)
        for test_file in stale_tests:
            expected_src = test_to_src_path(test_file)
            print(f"  {test_file}")
            print(f"    → Missing source: {expected_src}")
        print()

    if covered:
        print("✅ Source files WITH tests:")
        print("-" * 40)
        for src_file in covered:
            test_file = src_to_test_path(src_file)
            print(f"  {src_file} → {test_file}")
        print()

    # Print actionable items
    if missing_tests or stale_tests:
        print("🔧 Actionable Items:")
        print("-" * 40)
        if missing_tests:
            print(f"  • Create {len(missing_tests)} missing test file(s)")
        if stale_tests:
            print(f"  • Review/remove {len(stale_tests)} stale test file(s)")


if __name__ == "__main__":
    print_report()
