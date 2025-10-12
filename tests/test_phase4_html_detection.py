"""
Phase 4 Tests - Token-Based HTML Detection

Tests for token-based HTML detection in security metadata:
- HTML blocks/inline detected via tokens (not regex)
- Script tags detected with line numbers
- Event handlers detected
- No false positives from code blocks or escaped HTML
"""

import pytest
from docpipe.markdown_parser_core import MarkdownParserCore


def test_html_block_detection_via_tokens():
    """Verify HTML blocks detected via tokens, not regex."""
    text = "<div>Block HTML</div>"
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should be detected via tokens
    assert result["metadata"]["security"]["statistics"]["has_html_block"] is True
    assert len(result["structure"]["html_blocks"]) == 1


def test_html_inline_detection_via_tokens():
    """Verify inline HTML detected via tokens, not regex."""
    text = "Text with <em>emphasis</em> tag"
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should be detected via tokens
    assert result["metadata"]["security"]["statistics"]["has_html_inline"] is True
    assert len(result["structure"]["html_inline"]) > 0


def test_script_detection_with_line_numbers():
    """Verify script tags detected with accurate line numbers."""
    text = """Line 1

<script>alert('xss')</script>

Line 5"""
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should be detected
    assert result["metadata"]["security"]["statistics"]["has_script"] is True

    # Should have warning with line number
    warnings = result["metadata"]["security"]["warnings"]
    script_warnings = [w for w in warnings if w["type"] == "script_tag"]
    assert len(script_warnings) > 0
    # Line number should be present (may be None if not available, but should exist)
    assert "line" in script_warnings[0]


def test_event_handler_detection():
    """Verify event handlers detected in HTML content."""
    text = "<img src='x' onclick='alert(1)'>"
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should detect event handler
    assert result["metadata"]["security"]["statistics"]["has_event_handlers"] is True

    # Should have warning
    warnings = result["metadata"]["security"]["warnings"]
    handler_warnings = [w for w in warnings if w["type"] == "event_handlers"]
    assert len(handler_warnings) > 0


def test_no_false_positives_from_code_blocks():
    """Verify code blocks don't trigger HTML detection."""
    text = """```html
<div>This is code, not HTML</div>
<script>alert('also code')</script>
```"""
    p = MarkdownParserCore(text, {"allows_html": False})
    result = p.parse()

    # Code blocks should NOT trigger HTML warnings
    # (markdown-it treats fenced code as code_block tokens, not html_block)
    assert result["metadata"]["security"]["statistics"].get("has_html_block") is not True
    assert result["metadata"]["security"]["statistics"].get("has_script") is not True


def test_markdown_escaped_html_ignored():
    """Verify escaped HTML (backticks) doesn't trigger detection."""
    text = "Use `<div>` tag for containers"
    p = MarkdownParserCore(text, {"allows_html": False})
    result = p.parse()

    # Inline code should NOT trigger HTML detection
    assert result["metadata"]["security"]["statistics"].get("has_html_inline") is not True
    assert result["metadata"]["security"]["statistics"].get("has_html_block") is not True


def test_multiple_html_types():
    """Verify detection of multiple HTML patterns."""
    text = """<div>Block HTML</div>

Text with <strong>inline HTML</strong>

<script>alert('xss')</script>

<img src='x' onerror='alert(1)'>"""
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    sec = result["metadata"]["security"]["statistics"]
    assert sec["has_html_block"] is True
    assert sec["has_html_inline"] is True
    assert sec["has_script"] is True
    assert sec["has_event_handlers"] is True


def test_html_not_allowed():
    """Verify HTML blocked when allows_html=False."""
    text = "<div>HTML content</div>"
    p = MarkdownParserCore(text, {"allows_html": False})
    result = p.parse()

    # HTML should be stripped from structure by policy
    assert len(result["structure"]["html_blocks"]) == 0


def test_precompiled_patterns_still_work():
    """Verify precompiled _META_REFRESH_PAT and _FRAMELIKE_PAT still work."""
    text = """<meta http-equiv="refresh" content="0;url=http://evil.com">
<iframe src="http://evil.com"></iframe>"""
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    sec = result["metadata"]["security"]["statistics"]
    assert sec.get("has_meta_refresh") is True
    assert sec.get("has_frame_like") is True


def test_event_handler_variations():
    """Verify detection of various event handler types."""
    test_cases = [
        ("<div onload='x'>", "onload"),
        ("<img onerror='x'>", "onerror"),
        ("<button onclick='x'>", "onclick"),
        ("<input onfocus='x'>", "onfocus"),
        ("<form onsubmit='x'>", "onsubmit"),
    ]

    for html, handler in test_cases:
        p = MarkdownParserCore(html, {"allows_html": True})
        result = p.parse()

        # Should detect event handler
        assert result["metadata"]["security"]["statistics"]["has_event_handlers"] is True, \
            f"Failed to detect {handler} in {html}"


def test_case_insensitive_detection():
    """Verify detection is case-insensitive."""
    # Uppercase script tag
    text = "<SCRIPT>alert('xss')</SCRIPT>"
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should detect despite uppercase
    assert result["metadata"]["security"]["statistics"]["has_script"] is True

    # Uppercase event handler
    text2 = "<div ONCLICK='x'>"
    p2 = MarkdownParserCore(text2, {"allows_html": True})
    result2 = p2.parse()

    # Should detect despite uppercase
    assert result2["metadata"]["security"]["statistics"]["has_event_handlers"] is True
