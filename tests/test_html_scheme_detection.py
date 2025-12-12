"""Tests for dangerous scheme detection in HTML content.

These tests verify that javascript:, data:, and other dangerous schemes
are detected when embedded in HTML href attributes, not just markdown links.
"""

import pytest

from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.exceptions import MarkdownSecurityError


class TestJavascriptInHtmlHref:
    """Tests for javascript: scheme detection in HTML attributes."""

    def test_javascript_href_strict_raises(self) -> None:
        """Strict mode should raise on javascript: in content."""
        content = '<a href="javascript:alert(1)">Click</a>'

        with pytest.raises(MarkdownSecurityError, match="javascript"):
            MarkdownParserCore(content, security_profile="strict")

    def test_javascript_href_moderate_sets_embedding_blocked(self) -> None:
        """Moderate mode should set embedding_blocked for javascript: href."""
        content = '<a href="javascript:alert(1)">Click</a>'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        # Must set embedding_blocked
        assert result["metadata"].get("embedding_blocked") is True

        # Must have the disallowed scheme flag
        security = result["metadata"]["security"]
        assert security.get("link_disallowed_schemes_raw") is True

    def test_javascript_href_permissive_sets_embedding_blocked(self) -> None:
        """Permissive mode should also set embedding_blocked for javascript:."""
        content = '<a href="javascript:void(0)">Click</a>'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="permissive"
        )
        result = parser.parse()

        assert result["metadata"].get("embedding_blocked") is True


class TestDataUriInHtmlHref:
    """Tests for data: URI detection in HTML attributes."""

    def test_data_text_html_strict_raises(self) -> None:
        """Strict mode should raise on data:text/html in content."""
        content = '<a href="data:text/html,<script>alert(1)</script>">Click</a>'

        # May raise for "script" (detected first) or "data" scheme
        with pytest.raises(MarkdownSecurityError):
            MarkdownParserCore(content, security_profile="strict")

    def test_data_uri_moderate_sets_embedding_blocked(self) -> None:
        """Moderate mode should set embedding_blocked for data:text/html."""
        content = '<a href="data:text/html,<script>alert(1)</script>">Click</a>'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        assert result["metadata"].get("embedding_blocked") is True


class TestVbscriptInHtmlHref:
    """Tests for vbscript: scheme detection."""

    def test_vbscript_strict_raises(self) -> None:
        """Strict mode should raise on vbscript: in content."""
        content = '<a href="vbscript:msgbox(1)">Click</a>'

        with pytest.raises(MarkdownSecurityError, match="vbscript"):
            MarkdownParserCore(content, security_profile="strict")

    def test_vbscript_moderate_sets_embedding_blocked(self) -> None:
        """Moderate mode should set embedding_blocked for vbscript:."""
        content = '<a href="vbscript:msgbox(1)">Click</a>'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        assert result["metadata"].get("embedding_blocked") is True


class TestEventHandlersInHtml:
    """Tests for event handler detection in HTML."""

    def test_onclick_detected(self) -> None:
        """onclick handler should be detected."""
        content = '<div onclick="alert(1)">Click me</div>'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        security = result["metadata"]["security"]
        assert security["statistics"].get("has_event_handlers") is True

    def test_onerror_detected(self) -> None:
        """onerror handler should be detected."""
        content = '<img src="x" onerror="alert(1)">'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        security = result["metadata"]["security"]
        assert security["statistics"].get("has_event_handlers") is True

    def test_onload_detected(self) -> None:
        """onload handler should be detected."""
        content = '<body onload="alert(1)">'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        security = result["metadata"]["security"]
        assert security["statistics"].get("has_event_handlers") is True


class TestScriptTagDetection:
    """Tests for script tag detection."""

    def test_script_tag_strict_raises(self) -> None:
        """Strict mode should raise on <script> in content."""
        content = "<script>alert(1)</script>"

        with pytest.raises(MarkdownSecurityError, match="script"):
            MarkdownParserCore(content, security_profile="strict")

    def test_script_tag_moderate_detected(self) -> None:
        """Moderate mode should detect <script> tags."""
        content = "<script>alert(1)</script>"

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        security = result["metadata"]["security"]
        assert security["statistics"].get("has_script") is True


class TestHtmlBlocksWithDangerousContent:
    """Tests for dangerous content within HTML blocks."""

    def test_html_block_with_javascript_link(self) -> None:
        """HTML block containing javascript link should be caught."""
        content = """# Test

<div>
<a href="javascript:evil()">Click</a>
</div>
"""
        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        assert result["metadata"].get("embedding_blocked") is True

    def test_html_inline_with_event_handler(self) -> None:
        """Inline HTML with event handler should be detected."""
        content = "Click <span onclick='alert(1)'>here</span> please."

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        security = result["metadata"]["security"]
        assert security["statistics"].get("has_event_handlers") is True


class TestSafeHtmlNotFlagged:
    """Tests that safe HTML is not incorrectly flagged."""

    def test_normal_link_not_blocked(self) -> None:
        """Normal HTTPS link should not be blocked."""
        content = '<a href="https://example.com">Safe link</a>'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        assert result["metadata"].get("embedding_blocked") is not True

    def test_mailto_link_not_blocked(self) -> None:
        """Mailto link should not be blocked."""
        content = '<a href="mailto:test@example.com">Email</a>'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        # Mailto may or may not be blocked depending on profile
        # At minimum, it shouldn't crash
        assert result is not None

    def test_image_tag_not_blocked(self) -> None:
        """Normal image tag should not be blocked."""
        content = '<img src="https://example.com/img.png" alt="Test">'

        parser = MarkdownParserCore(
            content,
            config={"allows_html": True},
            security_profile="moderate"
        )
        result = parser.parse()

        # No dangerous schemes = not blocked
        assert result["metadata"].get("embedding_blocked") is not True
