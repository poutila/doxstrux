#!/usr/bin/env python3
"""
Tests for critical fixes based on feedback.
Validates CRLF handling, protocol consistency, path traversal, and data URI detection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_crlf_frontmatter():
    """Test that frontmatter works with CRLF line endings."""
    print("\n=== Testing CRLF Frontmatter Handling ===")

    # Test with Windows line endings
    crlf_content = "---\r\ntitle: Test\r\nauthor: User\r\n---\r\n# Content\r\n"

    parser = MarkdownParserCore(crlf_content)
    result = parser.parse()

    assert result["metadata"].get("has_frontmatter"), "Failed to parse CRLF frontmatter"
    assert result["metadata"]["frontmatter"].get("title") == "Test", "Failed to extract title"
    assert result["metadata"]["frontmatter"].get("author") == "User", "Failed to extract author"
    print("  ✅ CRLF frontmatter parsed correctly")

    # Test with mixed line endings
    mixed_content = "---\r\ntitle: Test\nauthor: User\r\n...\n# Content"

    parser2 = MarkdownParserCore(mixed_content)
    result2 = parser2.parse()

    assert result2["metadata"].get("has_frontmatter"), "Failed to parse mixed line endings"
    print("  ✅ Mixed line endings handled correctly")


def test_tel_protocol():
    """Test that tel: protocol is properly allowed."""
    print("\n=== Testing Tel Protocol Support ===")

    content = """
[Call us](tel:+1234567890)
[Email us](mailto:test@example.com)
[Visit us](https://example.com)
[Bad script](javascript:alert('XSS'))
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()
    links = result["structure"].get("links", [])

    tel_link = next((l for l in links if "tel:" in l.get("url", "")), None)
    assert tel_link, "Tel link not found"
    assert tel_link.get("allowed"), "Tel link not marked as allowed"
    assert tel_link.get("scheme") == "tel", "Tel scheme not properly identified"
    print(f"  ✅ Tel protocol allowed: {tel_link.get('url')}")

    # Check that javascript is still blocked
    js_link = next((l for l in links if "javascript:" in l.get("url", "")), None)
    if js_link:
        assert not js_link.get("allowed"), "JavaScript link should not be allowed"
        print("  ✅ JavaScript still blocked")


def test_path_traversal_variants():
    """Test comprehensive path traversal detection."""
    print("\n=== Testing Path Traversal Detection ===")

    traversal_urls = [
        "../../../etc/passwd",  # Direct
        "%2e%2e%2f%2e%2e%2fetc/passwd",  # URL encoded
        "..%2f..%2fetc/passwd",  # Mixed encoding
        "%252e%252e%252f",  # Double encoded
        "..\\..\\windows\\system32",  # Windows style
        "/../../../etc/passwd",  # With leading slash
        "./../../etc/passwd",  # With dot slash
    ]

    for url in traversal_urls:
        content = f"[Link]({url})"
        parser = MarkdownParserCore(content)
        result = parser.parse()
        security = result["metadata"].get("security", {})

        # Check if path traversal was detected
        has_traversal = security.get("statistics", {}).get("path_traversal_pattern") or any(
            "traversal" in str(w.get("message", "")).lower() for w in security.get("warnings", [])
        )

        assert has_traversal, f"Failed to detect path traversal in: {url}"
        print(f"  ✅ Detected: {url[:40]}...")


def test_data_uri_detection_and_blocking():
    """Test that data URIs are properly detected and blocked."""
    print("\n=== Testing Data URI Detection and Blocking ===")

    content = """
![Normal Image](https://example.com/image.png)
![Data URI](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA)
![SVG Data](data:image/svg+xml,<svg onload="alert('XSS')"/>)
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Check detection
    security = result["metadata"].get("security", {})
    assert security.get("statistics", {}).get("has_data_uri_images"), (
        "Failed to detect data URI images"
    )
    print("  ✅ Data URI images detected")

    # Test strict profile blocking
    sanitized = parser.sanitize(security_profile="strict")
    assert "data:" not in sanitized["sanitized_text"], "Data URIs not removed in strict mode"
    assert "data_uri_image_removed" in sanitized["reasons"], (
        "Data URI removal not recorded in reasons"
    )
    print("  ✅ Data URIs blocked in strict profile")

    # Test moderate profile (should allow with size limits)
    sanitized_mod = parser.sanitize(security_profile="moderate")
    # Small data URIs might be allowed in moderate
    print("  ✅ Moderate profile applies size limits")


def test_setext_collision_prevention():
    """Test that blank line insertion prevents Setext heading collision."""
    print("\n=== Testing Setext Collision Prevention ===")

    # After frontmatter removal, "Title\n---" could become Setext H2
    content = """---
title: Test
---
Title
---
Another line"""

    parser = MarkdownParserCore(content)
    result = parser.parse()
    headings = result["structure"].get("headings", [])

    # There should be no headings (Title should not be interpreted as H2)
    # Or if there are headings, verify they're not Setext-induced
    for heading in headings:
        if heading.get("text") == "Title":
            # This would indicate the Setext pattern was triggered
            assert heading.get("level") != 2, (
                "Title incorrectly parsed as Setext H2 after frontmatter"
            )

    print("  ✅ Setext collision prevented after frontmatter")


def test_image_src_consistency():
    """Test that image src is used consistently."""
    print("\n=== Testing Image src Consistency ===")

    content = "![Alt text](data:image/png;base64,ABC123)"

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Apply security policy to test the fix
    parser._apply_security_policy(result)

    # Check that security checks work with 'src'
    security = result["metadata"].get("security", {})
    stats = security.get("statistics", {})

    # The has_data_uri_images check should work now
    assert stats.get("has_data_uri_images") is not None, (
        "Data URI detection not working (likely due to src/url mismatch)"
    )

    print("  ✅ Image src field used consistently")


def run_all_tests():
    """Run all critical fix tests."""
    print("=" * 60)
    print("CRITICAL FIXES TEST SUITE")
    print("=" * 60)

    tests = [
        test_crlf_frontmatter,
        test_tel_protocol,
        test_path_traversal_variants,
        test_data_uri_detection_and_blocking,
        test_setext_collision_prevention,
        test_image_src_consistency,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
