import argparse
from pathlib import Path


def find_python_files(root: Path) -> list[Path]:
    return [
        p
        for p in root.rglob("*.py")
        if p.name != "__init__.py" and not any(part.startswith("__") for part in p.parts)
    ]


def expected_test_path(src_file: Path, src_root: Path, tests_root: Path) -> Path:
    rel_path = src_file.relative_to(src_root)
    test_filename = f"test_{rel_path.name}"
    return tests_root / rel_path.parent / test_filename


def corresponding_source_path(test_file: Path, tests_root: Path, src_root: Path) -> Path:
    rel_path = test_file.relative_to(tests_root)
    if not test_file.name.startswith("test_"):
        return None
    src_filename = test_file.name[len("test_") :]
    return src_root / rel_path.parent / src_filename


def generate_report(
    missing_tests: list[tuple[Path, Path]],
    stale_tests: list[Path],
    tested: int,
    report_path: Path = None,
):
    lines = [
        "# Test Coverage Report\n",
        f"✅ Source files with tests: **{tested}**",
        f"❌ Missing test files: **{len(missing_tests)}**",
        f"🗑️ Stale test files: **{len(stale_tests)}**\n",
    ]
    if missing_tests:
        lines.append("## ❌ Missing Tests")
        lines += [f"- `{src}` → expected `{test}`" for src, test in missing_tests]
    if stale_tests:
        lines.append("\n## 🗑️ Stale Tests")
        lines += [f"- `{test}`" for test in stale_tests]
    content = "\n".join(lines)

    if report_path:
        report_path.write_text(content)
    print(content)


def main():
    parser = argparse.ArgumentParser(description="Check test coverage in src/tests structure.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Only print the results, do not delete anything."
    )
    parser.add_argument("--delete", action="store_true", help="Delete stale test files.")
    parser.add_argument(
        "--report", action="store_true", help="Write a Markdown report to test_coverage_report.md"
    )
    args = parser.parse_args()

    src_root = Path("src")
    tests_root = Path("tests")
    missing_tests = []
    stale_tests = []
    tested = 0

    # Check for missing test files
    for src_file in find_python_files(src_root):
        test_path = expected_test_path(src_file, src_root, tests_root)
        if test_path.exists():
            tested += 1
        else:
            missing_tests.append((src_file, test_path))

    # Check for stale test files
    for test_file in find_python_files(tests_root):
        if not test_file.name.startswith("test_"):
            continue
        src_path = corresponding_source_path(test_file, tests_root, src_root)
        if src_path and not src_path.exists():
            stale_tests.append(test_file)
            if args.delete and not args.dry_run:
                test_file.unlink()

    # Generate output
    report_path = Path("test_coverage_report.md") if args.report else None
    generate_report(missing_tests, stale_tests, tested, report_path)


if __name__ == "__main__":
    main()
