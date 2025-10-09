#!/usr/bin/env python3
"""Detailed test coverage analysis for docpipe package."""

from pathlib import Path


def find_python_files(root: Path, exclude_init: bool = True) -> list[Path]:
    """Find all Python files in a directory tree."""
    files = []
    for p in root.rglob("*.py"):
        # Skip __init__.py files if requested
        if exclude_init and p.name == "__init__.py":
            continue
        # Skip directories starting with __
        if any(part.startswith("__") and part != "__init__.py" for part in p.parts):
            continue
        # Skip __version__.py as per CLAUDE guidelines
        if p.name == "__version__.py":
            continue
        files.append(p)
    return sorted(files)


def get_test_path(src_file: Path, src_root: Path, tests_root: Path) -> Path:
    """Get the expected test file path for a source file."""
    rel_path = src_file.relative_to(src_root)
    test_filename = f"test_{rel_path.name}"
    return tests_root / rel_path.parent / test_filename


def get_source_path(test_file: Path, tests_root: Path, src_root: Path) -> Path:
    """Get the expected source file path for a test file."""
    rel_path = test_file.relative_to(tests_root)
    if not test_file.name.startswith("test_"):
        return None
    src_filename = test_file.name[len("test_") :]
    return src_root / rel_path.parent / src_filename


def analyze_coverage():
    """Perform detailed coverage analysis."""
    src_root = Path("src")
    tests_root = Path("tests")

    # Find all source files
    src_files = find_python_files(src_root)

    # Find all test files
    test_files = [
        f for f in find_python_files(tests_root, exclude_init=False) if f.name.startswith("test_")
    ]

    # Analyze source files
    sources_with_tests = []
    sources_without_tests = []

    print("=" * 80)
    print("DETAILED TEST COVERAGE ANALYSIS")
    print("=" * 80)
    print("\n📁 Source Files Analysis:")
    print("-" * 40)

    for src_file in src_files:
        expected_test = get_test_path(src_file, src_root, tests_root)
        rel_src = src_file.relative_to(src_root)

        if expected_test.exists():
            sources_with_tests.append((src_file, expected_test))
            print(f"✅ {rel_src}")
            print(f"   └─ Test: {expected_test.relative_to(tests_root)}")
        else:
            sources_without_tests.append((src_file, expected_test))
            print(f"❌ {rel_src}")
            print(f"   └─ Missing: {expected_test.relative_to(tests_root)}")

    # Analyze test files
    print("\n\n🧪 Test Files Analysis:")
    print("-" * 40)

    valid_tests = []
    stale_tests = []

    for test_file in test_files:
        expected_src = get_source_path(test_file, tests_root, src_root)
        rel_test = test_file.relative_to(tests_root)

        if expected_src and expected_src.exists():
            valid_tests.append((test_file, expected_src))
            print(f"✅ {rel_test}")
            print(f"   └─ Source: {expected_src.relative_to(src_root)}")
        else:
            stale_tests.append(test_file)
            print(f"🗑️  {rel_test}")
            if expected_src:
                print(f"   └─ Missing source: {expected_src.relative_to(src_root)}")
            else:
                print("   └─ Invalid test file name pattern")

    # Summary
    print("\n\n📊 SUMMARY:")
    print("=" * 80)
    print(f"Total source files (excluding __init__.py, __version__.py): {len(src_files)}")
    print(f"Total test files: {len(test_files)}")
    print(f"\n✅ Source files with tests: {len(sources_with_tests)}")
    print(f"❌ Source files WITHOUT tests: {len(sources_without_tests)}")
    print(f"🗑️  Stale test files: {len(stale_tests)}")

    # Coverage percentage
    if src_files:
        coverage = (len(sources_with_tests) / len(src_files)) * 100
        print(f"\n📈 Test Coverage: {coverage:.1f}%")

    # List problematic files
    if sources_without_tests:
        print("\n\n⚠️  ACTION REQUIRED - Missing Tests:")
        print("-" * 40)
        for src, expected_test in sources_without_tests:
            print(f"• Create: {expected_test.relative_to(tests_root)}")
            print(f"  For: {src.relative_to(src_root)}")

    if stale_tests:
        print("\n\n🧹 CLEANUP - Stale Tests:")
        print("-" * 40)
        for test in stale_tests:
            print(f"• Remove: {test.relative_to(tests_root)}")


if __name__ == "__main__":
    analyze_coverage()
