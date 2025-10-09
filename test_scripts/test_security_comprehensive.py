#!/usr/bin/env python3
"""
Comprehensive security validation test.
Tests all security fixes together.
"""

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_comprehensive_security():
    """Run comprehensive security validation."""

    print("🔒 Comprehensive Security Validation")
    print("=" * 60)

    # Test document with multiple security issues
    test_content = """---
title: Security Test Document
author: Test Author
---

# Main Heading

This is a normal paragraph with some content.

## Section 1

- List item 1
    # This should NOT be a heading (list continuation)
    More list content
- List item 2

## Section 2

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   |
| Cell 4   | Cell 5   | Cell 6   | Extra    |

This table is ragged and should be detected.

---
malicious: attempt
should_not: be parsed as frontmatter
---

This YAML block is not at BOF and should be ignored.

## Section 3

```python
# This is code, not a heading
def foo():
    pass
```

> ## Quoted Heading
> This heading is in a blockquote

# Another Document Heading

Final content.
"""

    parser = MarkdownParserCore(test_content)
    result = parser.parse()

    # Extract components
    metadata = result.get("metadata", {})
    structure = result.get("structure", {})
    security = metadata.get("security", {})

    print("\n📊 Document Analysis:")
    print(f"   Total lines: {metadata.get('total_lines')}")
    print(f"   Has frontmatter: {metadata.get('has_frontmatter')}")

    # Test 1: YAML Frontmatter Security
    print("\n✅ Test 1: YAML Frontmatter (BOF-only)")
    frontmatter = metadata.get("frontmatter")
    if frontmatter:
        print(f"   ✓ Frontmatter extracted: {list(frontmatter.keys())}")
        print(f"   ✓ Title: {frontmatter.get('title')}")

        # Check that the malicious YAML block was not parsed
        if "malicious" not in frontmatter:
            print("   ✓ Non-BOF YAML block correctly ignored")
        else:
            print("   ✗ SECURITY BREACH: Non-BOF YAML was parsed!")
    else:
        print("   ✗ Expected frontmatter not found")

    # Test 2: Heading Creepage Prevention
    print("\n✅ Test 2: Heading Creepage Prevention")
    headings = structure.get("headings", [])
    print(f"   Found {len(headings)} document-level headings")

    # Check that list continuation "heading" was not parsed
    creepage_found = False
    for h in headings:
        if "should NOT be a heading" in h.get("text", ""):
            creepage_found = True
            print(f"   ✗ SECURITY BREACH: List heading creepage at line {h.get('line')}")

    if not creepage_found:
        print("   ✓ No heading creepage detected")

    # List actual headings found
    print("   Document headings found:")
    for h in headings:
        print(f"      - Level {h['level']}: {h['text']}")

    # Test 3: Table Ragged Detection
    print("\n✅ Test 3: Table Ragged Detection")
    tables = structure.get("tables", [])
    print(f"   Found {len(tables)} tables")

    ragged_tables = [t for t in tables if t.get("is_ragged", False)]
    if ragged_tables:
        print(f"   ✓ Detected {len(ragged_tables)} ragged table(s)")
        for t in ragged_tables:
            print(f"      - Table at line {t.get('start_line')}: RAGGED")
    else:
        print("   ✗ No ragged tables detected (expected 1)")

    # Test 4: Security Metadata
    print("\n✅ Test 4: Security Metadata")
    if security:
        print("   ✓ Security metadata present")
        stats = security.get("statistics", {})
        print(f"   Frontmatter at BOF: {stats.get('frontmatter_at_bof')}")
        print(f"   Ragged tables count: {stats.get('ragged_tables_count')}")

        warnings = security.get("warnings", [])
        if warnings:
            print(f"   Security warnings ({len(warnings)}):")
            for w in warnings:
                print(f"      - {w.get('type')}: {w.get('message')} (line {w.get('line')})")
    else:
        print("   ✗ Security metadata missing")

    # Test 5: Content Integrity
    print("\n✅ Test 5: Content Integrity")
    raw_content = result.get("content", {}).get("raw", "")

    # Check that malicious YAML content is still in the document
    if "malicious: attempt" in raw_content:
        print("   ✓ Non-BOF YAML content preserved (not deleted)")
    else:
        print("   ✗ Content deletion detected!")

    # Check that list continuation content is preserved
    if "More list content" in raw_content:
        print("   ✓ List continuation content preserved")
    else:
        print("   ✗ List content deletion detected!")

    # Summary
    print("\n" + "=" * 60)
    print("🎯 Security Validation Summary:")

    all_tests_passed = True

    # Check each security fix
    tests = {
        "YAML BOF-only": frontmatter and "malicious" not in frontmatter,
        "Heading creepage blocked": not creepage_found,
        "Ragged tables detected": len(ragged_tables) > 0,
        "Security metadata present": security is not None,
        "Content integrity maintained": "malicious: attempt" in raw_content,
    }

    for test_name, passed in tests.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_tests_passed = False

    if all_tests_passed:
        print("\n🔒 SUCCESS: All security vulnerabilities fixed!")
        print("   ✅ YAML frontmatter restricted to BOF")
        print("   ✅ Heading creepage prevented")
        print("   ✅ Ragged tables detected")
        print("   ✅ Security metadata provided")
        print("   ✅ Content integrity maintained")
    else:
        print("\n⚠️ SECURITY ISSUES DETECTED!")
        print("   Review failed tests above")

    return all_tests_passed


if __name__ == "__main__":
    test_comprehensive_security()
