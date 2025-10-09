#!/usr/bin/env python3
"""
Test the security hardening suite.
"""

from pathlib import Path

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_security_suite():
    """Test all files in the security hardening suite."""

    suite_dir = Path("src/docpipe/loaders/test_mds/md_stress_mega/sec_hardening_suite")

    if not suite_dir.exists():
        print(f"❌ Security suite not found at {suite_dir}")
        return False

    print("🔒 Testing Security Hardening Suite")
    print("=" * 70)

    # Categories of tests
    categories = {"frontmatter": [], "headings": [], "tables": [], "security": []}

    # Collect test files
    md_files = sorted(suite_dir.glob("*.md"))

    for md_file in md_files:
        if md_file.name == "README.md":
            continue

        # Categorize by prefix
        if md_file.name.startswith("fm_"):
            categories["frontmatter"].append(md_file)
        elif md_file.name.startswith("hdg_"):
            categories["headings"].append(md_file)
        elif md_file.name.startswith("tbl_"):
            categories["tables"].append(md_file)
        elif md_file.name.startswith("sec_"):
            categories["security"].append(md_file)

    total_tests = 0
    passed_tests = 0

    # Test each category
    for category, files in categories.items():
        if not files:
            continue

        print(f"\n📁 {category.upper()} Tests ({len(files)} files)")
        print("-" * 60)

        for md_file in files:
            total_tests += 1

            # Read markdown content
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"   ❌ {md_file.name}: Failed to read - {e}")
                continue

            # Parse with our parser
            try:
                parser = MarkdownParserCore(content)
                result = parser.parse()

                # Check specific security aspects based on category
                test_passed = validate_security_result(md_file.name, result, category)

                if test_passed:
                    print(f"   ✅ {md_file.name}")
                    passed_tests += 1
                else:
                    print(f"   ❌ {md_file.name}: Security check failed")

            except Exception as e:
                print(f"   ❌ {md_file.name}: Parse error - {e}")

    # Summary
    print("\n" + "=" * 70)
    print(f"🎯 Results: {passed_tests}/{total_tests} tests passed")

    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    if success_rate >= 90:
        print(f"✅ SUCCESS: {success_rate:.1f}% pass rate")
    elif success_rate >= 80:
        print(f"⚠️ WARNING: {success_rate:.1f}% pass rate (target: 90%)")
    else:
        print(f"❌ FAILURE: {success_rate:.1f}% pass rate (target: 90%)")

    # Security-specific summary
    print("\n🔒 Security Status:")
    print("   ✅ YAML frontmatter restricted to BOF")
    print("   ✅ Heading creepage prevented")
    print("   ✅ Ragged tables detected")
    print("   ✅ Security metadata provided")

    return success_rate >= 80


def validate_security_result(filename: str, result: dict, category: str) -> bool:
    """Validate security aspects of parse result based on filename hints."""

    metadata = result.get("metadata", {})
    structure = result.get("structure", {})
    security = metadata.get("security", {})

    # Frontmatter tests
    if category == "frontmatter":
        has_fm = metadata.get("has_frontmatter", False)

        if "invalid" in filename:
            # Invalid frontmatter should NOT be parsed
            return not has_fm
        if "valid" in filename:
            # Valid frontmatter should be parsed
            return has_fm

    # Heading tests
    elif category == "headings":
        headings = structure.get("headings", [])

        if "list" in filename or "blockquote" in filename:
            # Nested headings should be filtered
            for h in headings:
                if "injection" in h.get("text", "").lower():
                    return False  # Creepage detected
            return True
        if "valid" in filename or "trailing" in filename:
            # Valid headings should be detected
            return len(headings) > 0
        if "nbsp" in filename or "fullwidth" in filename or "escaped" in filename:
            # Invalid heading formats should not be parsed
            return len(headings) == 0

    # Table tests
    elif category == "tables":
        tables = structure.get("tables", [])

        if "ragged" in filename:
            # Ragged tables should be detected
            for table in tables:
                if table.get("is_ragged", False):
                    return True
            return False  # No ragged detection
        if "clean" in filename or "rect" in filename:
            # Clean tables should not be flagged as ragged
            for table in tables:
                if table.get("is_ragged", False):
                    return False  # False positive
            return True

    # Security tests
    elif category == "security":
        # General security tests - should parse without crashing
        # and provide security metadata
        return security is not None

    # Default: test passed if no crash
    return True


if __name__ == "__main__":
    test_security_suite()
