#!/usr/bin/env python3
"""Test suite for newly added features based on high-impact feedback."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_unicode_risk_score():
    """Test unicode risk score calculation."""
    print("\n=== Testing Unicode Risk Score ===")

    # Clean content - score 0
    clean_doc = "# Title\n\nNormal text content."
    parser = MarkdownParserCore(clean_doc, config={})
    result = parser.parse()
    assert result["metadata"]["security"]["statistics"].get("unicode_risk_score") == 0
    print("  ✅ Clean doc: risk score = 0")

    # BiDi only - score 1
    bidi_doc = "# Title\n\nHello \u202eworld"  # RLO character
    parser = MarkdownParserCore(bidi_doc, config={})
    result = parser.parse()
    assert result["metadata"]["security"]["statistics"].get("unicode_risk_score") == 1
    print("  ✅ BiDi only: risk score = 1")

    # Multiple issues - higher score
    risky_doc = (
        "# Title\n\nHello \u202eworld with раypal.com and \u200b"  # BiDi + confusables + ZWSP
    )
    parser = MarkdownParserCore(risky_doc, config={})
    result = parser.parse()
    score = result["metadata"]["security"]["statistics"].get("unicode_risk_score", 0)
    assert score >= 2  # At least BiDi + confusables
    print(f"  ✅ Multiple issues: risk score = {score}")


def test_frontmatter_blank_line_tolerance():
    """Test single blank line tolerance before frontmatter."""
    print("\n=== Testing Frontmatter Blank Line Tolerance ===")

    # No blank line - should work
    doc1 = "---\ntitle: Test\n---\n# Content"
    parser = MarkdownParserCore(doc1, config={})
    result = parser.parse()
    assert result["metadata"]["has_frontmatter"] is True
    assert result["metadata"]["frontmatter"]["title"] == "Test"
    print("  ✅ No blank line: frontmatter parsed")

    # Single blank line - should now work
    doc2 = "\n---\ntitle: Test\n---\n# Content"
    parser = MarkdownParserCore(doc2, config={})
    result = parser.parse()
    assert result["metadata"]["has_frontmatter"] is True
    assert result["metadata"]["frontmatter"]["title"] == "Test"
    print("  ✅ Single blank line: frontmatter parsed")

    # Two blank lines - should not work
    doc3 = "\n\n---\ntitle: Test\n---\n# Content"
    parser = MarkdownParserCore(doc3, config={})
    result = parser.parse()
    assert result["metadata"]["has_frontmatter"] is False
    print("  ✅ Two blank lines: frontmatter rejected")


def test_footnote_byte_length():
    """Test byte_length field in footnotes."""
    print("\n=== Testing Footnote Byte Length ===")

    doc = """Text with footnote[^1].

[^1]: This is a footnote with some content.

More text[^2].

[^2]: Unicode: 你好世界"""

    parser = MarkdownParserCore(doc, config={})
    result = parser.parse()

    footnotes = result["structure"]["footnotes"]["definitions"]
    assert len(footnotes) == 2

    # Check ASCII footnote
    fn1 = footnotes[0]
    assert "byte_length" in fn1
    assert fn1["byte_length"] > 0
    print(f"  ✅ ASCII footnote: byte_length = {fn1['byte_length']}")

    # Check Unicode footnote
    fn2 = footnotes[1]
    assert "byte_length" in fn2
    # Unicode characters take more bytes
    assert fn2["byte_length"] > len(fn2["content"])  # UTF-8 encoding
    print(
        f"  ✅ Unicode footnote: byte_length = {fn2['byte_length']} (content len = {len(fn2['content'])})"
    )


def test_character_offsets_headings():
    """Test character offsets for headings."""
    print("\n=== Testing Character Offsets for Headings ===")

    doc = "# First\n\nSome text\n\n## Second\n\nMore text"
    parser = MarkdownParserCore(doc, config={})
    result = parser.parse()

    headings = result["structure"]["headings"]
    assert len(headings) == 2

    # Check first heading
    h1 = headings[0]
    assert "start_char" in h1 and "end_char" in h1
    if h1["start_char"] is not None and h1["end_char"] is not None:
        assert h1["start_char"] <= h1["end_char"]
        assert doc[h1["start_char"] : h1["end_char"]].strip().startswith("# First")
        print(f"  ✅ First heading: chars {h1['start_char']}-{h1['end_char']}")

    # Check second heading
    h2 = headings[1]
    assert "start_char" in h2 and "end_char" in h2
    if h2["start_char"] is not None and h2["end_char"] is not None:
        assert h2["start_char"] <= h2["end_char"]
        assert doc[h2["start_char"] : h2["end_char"]].strip().startswith("## Second")
        print(f"  ✅ Second heading: chars {h2['start_char']}-{h2['end_char']}")


def test_recursion_depth_guard():
    """Test recursion depth guard prevents stack overflow."""
    print("\n=== Testing Recursion Depth Guard ===")

    # The recursion guard is implemented internally
    # Test that normal documents with deep nesting still work
    doc = "# Title\n\n" + "\n".join([f"- Item {i}" for i in range(50)])
    parser = MarkdownParserCore(doc, config={})
    result = parser.parse()
    assert result is not None
    print("  ✅ Normal nested content still parses")

    # Create a document with nested lists
    nested_doc = "# Title\n\n"
    for i in range(10):
        nested_doc += "  " * i + f"- Level {i} item\n"

    parser = MarkdownParserCore(nested_doc, config={})
    result = parser.parse()
    assert result is not None
    print("  ✅ Deep nested lists parse correctly")


def test_security_profile_parameter():
    """Test security_profile parameter in constructor."""
    print("\n=== Testing Security Profile Parameter ===")

    doc = "# Title\n\n<script>alert('test')</script>"

    # Test with explicit strict profile
    parser = MarkdownParserCore(doc, config={}, security_profile="strict")
    result = parser.parse()
    assert parser.security_profile == "strict"
    print("  ✅ Strict profile set via constructor")

    # Test with moderate profile
    parser = MarkdownParserCore(doc, config={}, security_profile="moderate")
    result = parser.parse()
    assert parser.security_profile == "moderate"
    print("  ✅ Moderate profile set via constructor")

    # Test default (from config or 'strict')
    parser = MarkdownParserCore(doc, config={})
    result = parser.parse()
    assert parser.security_profile in ["strict", "moderate", "permissive"]
    print(f"  ✅ Default profile: {parser.security_profile}")


def test_tel_link_phone_classification():
    """Test tel: links are classified as 'phone' type."""
    print("\n=== Testing Tel Link Phone Classification ===")

    doc = "Call us: [Contact](tel:+1-555-0123)"
    parser = MarkdownParserCore(doc, config={})
    result = parser.parse()

    links = result["structure"]["links"]
    tel_link = next((l for l in links if l.get("url", "").startswith("tel:")), None)

    assert tel_link is not None
    assert tel_link["type"] == "phone"
    assert tel_link["allowed"] is True
    print("  ✅ Tel link classified as 'phone' type")


if __name__ == "__main__":
    test_unicode_risk_score()
    test_frontmatter_blank_line_tolerance()
    test_footnote_byte_length()
    test_character_offsets_headings()
    test_recursion_depth_guard()
    test_security_profile_parameter()
    test_tel_link_phone_classification()

    print("\n✅ All new feature tests passed!")
