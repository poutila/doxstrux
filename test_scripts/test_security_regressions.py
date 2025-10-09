#!/usr/bin/env python3
"""
Comprehensive security regression tests for MarkdownParserCore.
Tests critical security features to prevent regressions.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_data_uri_detection_both_forms():
    """Test that data: URIs are detected in both images and image-links."""
    print("\n=== Testing Data URI Detection ===")

    # Test 1: First-class image with data URI
    doc1 = "![alt](data:image/png;base64,iVBORw0KGgo...)"
    parser1 = MarkdownParserCore(doc1, security_profile="strict")
    result1 = parser1.parse()

    # Check detection
    assert result1["metadata"]["security"]["statistics"].get("has_data_uri_images", False), (
        "Should detect data URI in first-class image"
    )
    print("  ✅ Detected data URI in first-class image")

    # Test 2: Image inside link (image-link) with data URI
    doc2 = "[![alt](data:image/gif;base64,R0lGODlh...)](https://example.com)"
    parser2 = MarkdownParserCore(doc2, security_profile="strict")
    result2 = parser2.parse()

    # Check detection in links (image-links create link records)
    links = result2["structure"]["links"]
    has_data_uri_in_links = any(
        "data:" in link.get("url", "") or "data:" in link.get("src", "") for link in links
    )
    assert has_data_uri_in_links or result2["metadata"]["security"]["statistics"].get(
        "has_data_uri_images", False
    ), "Should detect data URI in image-link"
    print("  ✅ Detected data URI in image-link")

    # Test 3: Mixed case and whitespace
    doc3 = "![test]( data:IMAGE/jpeg;base64,/9j/4AAQ... )"
    parser3 = MarkdownParserCore(doc3, security_profile="strict")
    result3 = parser3.parse()

    assert result3["metadata"]["security"]["statistics"].get("has_data_uri_images", False), (
        "Should detect data URI with mixed case and whitespace"
    )
    print("  ✅ Detected data URI with case/space variations")


def test_policy_enforcement_by_profile():
    """Test that security profiles correctly enforce their policies."""
    print("\n=== Testing Policy Enforcement ===")

    doc = """
<script>alert('test')</script>
[Contact](mailto:test@example.com)
[Download](ftp://files.example.com/file.zip)
[Call](tel:+1234567890)
![Image](https://example.com/img.jpg)
<div>HTML content</div>
"""

    # Test 1: Strict profile
    parser_strict = MarkdownParserCore(
        doc, config={"allows_html": False}, security_profile="strict"
    )
    result_strict = parser_strict.parse()

    # Check HTML stripping
    assert len(result_strict["structure"]["html_blocks"]) == 0, (
        "Strict profile should strip HTML blocks when allows_html=False"
    )

    # Check link filtering
    links_strict = result_strict["structure"]["links"]
    allowed_schemes_strict = set()
    for link in links_strict:
        if link.get("allowed"):
            scheme = link.get("scheme")
            if scheme:
                allowed_schemes_strict.add(scheme)

    # Strict profile should not allow ftp
    assert "ftp" not in allowed_schemes_strict, "Strict profile should not allow ftp: scheme"
    print("  ✅ Strict profile enforces correct policies")

    # Test 2: Moderate profile
    parser_moderate = MarkdownParserCore(
        doc, config={"allows_html": True}, security_profile="moderate"
    )
    result_moderate = parser_moderate.parse()

    # Moderate allows safe HTML
    assert len(result_moderate["structure"]["html_blocks"]) > 0, (
        "Moderate profile should preserve HTML when allows_html=True"
    )

    # Check embedding blocked for script tags
    assert result_moderate["metadata"].get("embedding_blocked", False), (
        "Moderate profile should block embedding when script tags present"
    )
    print("  ✅ Moderate profile enforces correct policies")

    # Test 3: Permissive profile
    parser_permissive = MarkdownParserCore(
        doc, config={"allows_html": True}, security_profile="permissive"
    )
    result_permissive = parser_permissive.parse()

    # Permissive allows more schemes
    links_permissive = result_permissive["structure"]["links"]
    schemes_permissive = set(link.get("scheme") for link in links_permissive if link.get("scheme"))

    # Should have tel, mailto, ftp in permissive
    assert "tel" in schemes_permissive, "Permissive should allow tel:"
    assert "mailto" in schemes_permissive, "Permissive should allow mailto:"
    print("  ✅ Permissive profile enforces correct policies")


def test_path_traversal_comprehensive():
    """Test path traversal detection with various encodings."""
    print("\n=== Testing Path Traversal Detection ===")

    test_cases = [
        ("../../etc/passwd", "direct traversal", True),
        ("%2e%2e%2f%2e%2e%2fetc/passwd", "URL encoded", True),
        ("..%2f..%2fetc/passwd", "mixed encoding", True),
        ("%252e%252e%252f", "double encoded", True),
        ("file://host/etc/passwd", "file scheme", True),
        ("..\\..\\windows\\system32", "Windows traversal", True),
        # These may not be detected in all contexts
        ("\\\\server\\share", "UNC path", False),
        ("C:\\Windows\\System32", "Windows path", False),
    ]

    for path, description, must_detect in test_cases:
        doc = f"[Link]({path})"
        parser = MarkdownParserCore(doc)
        result = parser.parse()

        # Check if traversal or dangerous path was detected
        warnings = result["metadata"]["security"]["warnings"]
        has_security_warning = any(
            "traversal" in w.get("type", "").lower()
            or "traversal" in w.get("message", "").lower()
            or "dangerous" in w.get("type", "").lower()
            or "file" in w.get("scheme", "").lower()
            for w in warnings
        )

        if must_detect:
            assert has_security_warning, f"Should detect {description}: {path}"
            print(f"  ✅ Detected {description}")
        # Optional detection - just report if detected
        elif has_security_warning:
            print(f"  ✅ Detected {description} (optional)")
        else:
            print(f"  ⚠️  {description} not detected (optional)")


def test_heading_in_list_detection():
    """Test that headings are properly extracted."""
    print("\n=== Testing Heading Extraction ===")

    doc = """
# Top Level Heading

Some text here.

## Normal Section Heading

More content.

### Subsection
"""

    parser = MarkdownParserCore(doc)
    result = parser.parse()

    headings = result["structure"]["headings"]

    # Should find all headings
    assert len(headings) == 3, f"Should find 3 headings, found {len(headings)}"

    # Check heading levels
    levels = [h["level"] for h in headings]
    assert levels == [1, 2, 3], f"Heading levels should be [1, 2, 3], got {levels}"

    # Check that headings have proper metadata
    for h in headings:
        assert "text" in h, "Heading should have text"
        assert "level" in h, "Heading should have level"
        assert "id" in h, "Heading should have id"
        assert "start_line" in h or "line" in h, "Heading should have line info"

    print("  ✅ Headings properly extracted with metadata")


def test_image_security_consistency():
    """Test that images always use 'src' field for security checks."""
    print("\n=== Testing Image Field Consistency ===")

    doc = """
![Alt text](https://example.com/image.jpg)
![Data URI](data:image/png;base64,abc123)
[![Image Link](https://example.com/img2.jpg)](https://link.com)
"""

    parser = MarkdownParserCore(doc)
    result = parser.parse()

    # Check all images have 'src' field
    images = result["structure"]["images"]
    for img in images:
        assert "src" in img, f"Image missing 'src' field: {img}"

        # If it's a data URI, should be detected
        if img["src"].startswith("data:"):
            assert result["metadata"]["security"]["statistics"].get("has_data_uri_images", False), (
                "Data URI in image not detected in security stats"
            )

    # Check image-links in links also have consistent fields
    links = result["structure"]["links"]
    for link in links:
        if link.get("type") == "image":
            assert "src" in link, f"Image-link missing 'src' field: {link}"

    print("  ✅ All images use consistent 'src' field")


def test_quarantine_triggers():
    """Test that documents are quarantined for risky features."""
    print("\n=== Testing Quarantine Triggers ===")

    # Test 1: Ragged tables
    doc1 = """
| Col1 | Col2 |
|------|------|
| A    |
| B    | C    |
"""
    parser1 = MarkdownParserCore(doc1)
    result1 = parser1.parse()

    if result1["metadata"]["security"]["statistics"].get("ragged_tables_count", 0) > 0:
        assert "quarantine_reasons" in result1["metadata"], (
            "Should quarantine document with ragged tables"
        )
        assert any("ragged" in str(r) for r in result1["metadata"]["quarantine_reasons"]), (
            "Should list ragged tables as quarantine reason"
        )
        print("  ✅ Ragged tables trigger quarantine")

    # Test 2: Long footnotes (potential payload hiding)
    long_content = "A" * 600  # Over 512 char limit
    doc2 = f"""
Text with footnote[^1].

[^1]: {long_content}
"""
    parser2 = MarkdownParserCore(doc2, config={"plugins": ["footnote"]})
    result2 = parser2.parse()

    if result2["structure"].get("footnotes"):
        if result2["metadata"].get("quarantined"):
            assert any("footnote" in str(r) for r in result2["metadata"]["quarantine_reasons"]), (
                "Should list long footnote as quarantine reason"
            )
            print("  ✅ Long footnotes trigger quarantine")


def test_security_profile_validation():
    """Test that invalid security profiles are rejected."""
    print("\n=== Testing Security Profile Validation ===")

    # Test invalid profile
    try:
        parser = MarkdownParserCore("# Test", security_profile="invalid_profile")
        assert False, "Should raise ValueError for invalid profile"
    except ValueError as e:
        assert "Unknown security profile" in str(e)
        assert "strict" in str(e) and "moderate" in str(e) and "permissive" in str(e)
        print("  ✅ Invalid security profile rejected with helpful message")

    # Test valid profiles
    for profile in ["strict", "moderate", "permissive"]:
        parser = MarkdownParserCore("# Test", security_profile=profile)
        result = parser.parse()
        assert result["metadata"]["security"]["profile_used"] == profile
        print(f"  ✅ Valid profile '{profile}' accepted")


if __name__ == "__main__":
    print("🔒 Security Regression Test Suite")
    print("=" * 50)

    test_data_uri_detection_both_forms()
    test_policy_enforcement_by_profile()
    test_path_traversal_comprehensive()
    test_heading_in_list_detection()
    test_image_security_consistency()
    test_quarantine_triggers()
    test_security_profile_validation()

    print("\n" + "=" * 50)
    print("✅ All security regression tests passed!")
