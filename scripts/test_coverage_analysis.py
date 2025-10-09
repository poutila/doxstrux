#!/usr/bin/env python3
"""Analyze test coverage for docpipe package."""

from pathlib import Path


def get_python_files(src_dir: Path) -> list[Path]:
    """Get all Python files in the source directory, excluding __init__.py and __version__.py."""
    python_files = []
    for file_path in src_dir.rglob("*.py"):
        if file_path.name not in ["__init__.py", "__version__.py"]:
            python_files.append(file_path)
    return sorted(python_files)


def get_test_files(tests_dir: Path) -> list[Path]:
    """Get all test files in the tests directory."""
    test_files = []
    for file_path in tests_dir.rglob("test_*.py"):
        test_files.append(file_path)
    return sorted(test_files)


def get_expected_test_path(src_file: Path, src_root: Path, tests_root: Path) -> Path:
    """Get the expected test file path for a source file."""
    # Get relative path from src root
    rel_path = src_file.relative_to(src_root)

    # Convert to test file name
    test_name = f"test_{rel_path.name}"

    # Build test path
    test_dir = tests_root / rel_path.parent
    return test_dir / test_name


def analyze_coverage() -> tuple[list[Path], list[Path], float]:
    """Analyze test coverage and return files without tests, files with tests, and coverage percentage."""
    # Define paths
    src_root = Path("src/docpipe")
    tests_root = Path("tests/docpipe")

    # Get all Python files (excluding __init__.py and __version__.py)
    src_files = get_python_files(src_root)

    # Get all test files
    test_files = get_test_files(tests_root)
    test_files_set = {f.name for f in test_files}

    # Check which source files have tests
    files_with_tests = []
    files_without_tests = []

    for src_file in src_files:
        expected_test_name = f"test_{src_file.name}"

        # Check if test file exists
        has_test = False
        for test_file in test_files:
            if test_file.name == expected_test_name:
                # Check if it's in the corresponding directory structure
                src_rel_path = src_file.relative_to(src_root).parent
                test_rel_path = test_file.relative_to(tests_root).parent

                if src_rel_path == test_rel_path:
                    has_test = True
                    break

        if has_test:
            files_with_tests.append(src_file)
        else:
            files_without_tests.append(src_file)

    # Calculate coverage percentage
    total_files = len(src_files)
    coverage = (len(files_with_tests) / total_files * 100) if total_files > 0 else 100.0

    return files_without_tests, files_with_tests, coverage


def main():
    """Main function to run the analysis."""
    print("Test Coverage Analysis for docpipe")
    print("=" * 50)

    files_without_tests, files_with_tests, coverage = analyze_coverage()

    print(
        f"\nTotal Python files (excluding __init__.py and __version__.py): {len(files_with_tests) + len(files_without_tests)}"
    )
    print(f"Files with tests: {len(files_with_tests)}")
    print(f"Files without tests: {len(files_without_tests)}")
    print(f"Coverage percentage: {coverage:.1f}%")

    if files_without_tests:
        print("\nFiles WITHOUT tests:")
        print("-" * 30)
        for file_path in files_without_tests:
            print(f"  - {file_path}")

    if files_with_tests:
        print("\nFiles WITH tests:")
        print("-" * 30)
        for file_path in files_with_tests:
            print(f"  ✓ {file_path}")


if __name__ == "__main__":
    main()
