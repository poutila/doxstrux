#!/usr/bin/env python3
"""Test detection of HTML/CSS scriptless attack vectors."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_style_javascript_injection():
    """Test detection of JavaScript in style attributes."""
    content = """
# Document with Style-based XSS

<div style="background: url(javascript:alert('XSS'))">Content</div>

<span style="behavior: expression(alert('XSS'))">Text</span>
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Check security detection
    security = result["metadata"]["security"]
    assert security["statistics"].get("has_style_scriptless") == True

    # Check warning was added
    warnings = security.get("warnings", [])
    assert any(w["type"] == "style_scriptless" for w in warnings)

    # Check embedding is blocked
    assert result["metadata"].get("embedding_blocked") == True
    assert "style-based JavaScript" in result["metadata"].get("embedding_block_reason", "")
    assert "embedding_blocked_style_js" in result["metadata"].get("security_policies_applied", [])

    print("✅ Style JavaScript injection detection works")


def test_meta_refresh():
    """Test detection of meta refresh tags."""
    content = """
# Document with Meta Refresh

<meta http-equiv="refresh" content="0; url=http://evil.com">

Normal content here.
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Check security detection
    security = result["metadata"]["security"]
    assert security["statistics"].get("has_meta_refresh") == True

    # Check warning was added
    warnings = security.get("warnings", [])
    assert any(w["type"] == "meta_refresh" for w in warnings)

    # Check embedding is blocked
    assert result["metadata"].get("embedding_blocked") == True
    assert "meta refresh" in result["metadata"].get("embedding_block_reason", "")
    assert "embedding_blocked_meta_refresh" in result["metadata"].get(
        "security_policies_applied", []
    )

    print("✅ Meta refresh detection works")


def test_iframe_detection():
    """Test detection of iframe elements."""
    content = """
# Document with Iframe

<iframe src="http://evil.com/malware"></iframe>

Normal content.
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Check security detection
    security = result["metadata"]["security"]
    assert security["statistics"].get("has_frame_like") == True

    # Check warning was added
    warnings = security.get("warnings", [])
    assert any(w["type"] == "frame_like" for w in warnings)

    # Check embedding is blocked
    assert result["metadata"].get("embedding_blocked") == True
    assert "frame-like elements" in result["metadata"].get("embedding_block_reason", "")
    assert "embedding_blocked_frame" in result["metadata"].get("security_policies_applied", [])

    print("✅ Iframe detection works")


def test_object_embed_detection():
    """Test detection of object and embed elements."""
    content = """
# Document with Object/Embed

<object data="http://evil.com/flash.swf"></object>

<embed src="javascript:alert('XSS')">

Normal content.
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Check security detection
    security = result["metadata"]["security"]
    assert security["statistics"].get("has_frame_like") == True

    # Check warning was added
    warnings = security.get("warnings", [])
    assert any(w["type"] == "frame_like" for w in warnings)

    print("✅ Object/embed detection works")


def test_mixed_vectors():
    """Test detection of multiple attack vectors."""
    content = """
# Mixed Attack Vectors

<div style="background: url(javascript:alert(1))">Style XSS</div>

<meta http-equiv="refresh" content="0">

<iframe src="data:text/html,<script>alert(2)</script>"></iframe>

<object data="http://evil.com"></object>
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Check all vectors detected
    security = result["metadata"]["security"]
    assert security["statistics"].get("has_style_scriptless") == True
    assert security["statistics"].get("has_meta_refresh") == True
    assert security["statistics"].get("has_frame_like") == True

    # Check multiple warnings
    warnings = security.get("warnings", [])
    warning_types = [w["type"] for w in warnings]
    assert "style_scriptless" in warning_types
    assert "meta_refresh" in warning_types
    assert "frame_like" in warning_types

    # Check multiple policies applied
    policies = result["metadata"].get("security_policies_applied", [])
    assert "embedding_blocked_style_js" in policies
    assert "embedding_blocked_meta_refresh" in policies
    assert "embedding_blocked_frame" in policies

    print("✅ Mixed vector detection works")


def test_safe_styles():
    """Test that legitimate styles are not flagged."""
    content = """
# Safe Styles

<div style="color: red; background: white;">Normal styling</div>

<span style="font-size: 14px;">Text</span>
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Should not detect style-based attacks
    security = result["metadata"]["security"]
    assert security["statistics"].get("has_style_scriptless", False) == False, (
        "Incorrectly flagged safe styles"
    )

    # But should detect HTML (div and span are block HTML)
    assert (
        security["statistics"].get("has_html_block") == True
        or security["statistics"].get("has_html_inline") == True
    )

    print("✅ Safe styles not flagged")


def test_case_insensitive_detection():
    """Test that detection is case-insensitive."""
    content = """
# Case Variations

<DIV STYLE="background: URL(JAVASCRIPT:alert('XSS'))">Upper case</DIV>

<Meta Http-Equiv="Refresh" Content="0">

<IFRAME SRC="http://evil.com"></IFRAME>
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    # Should detect despite case variations
    security = result["metadata"]["security"]
    assert security["statistics"].get("has_style_scriptless") == True
    assert security["statistics"].get("has_meta_refresh") == True
    assert security["statistics"].get("has_frame_like") == True

    print("✅ Case-insensitive detection works")


def main():
    """Run all scriptless vector tests."""
    print("Testing HTML/CSS Scriptless Attack Vector Detection")
    print("=" * 60)

    tests = [
        test_style_javascript_injection,
        test_meta_refresh,
        test_iframe_detection,
        test_object_embed_detection,
        test_mixed_vectors,
        test_safe_styles,
        test_case_insensitive_detection,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    if failed == 0:
        print("✅ All scriptless vector tests passed!")
    else:
        print(f"❌ {failed} tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
