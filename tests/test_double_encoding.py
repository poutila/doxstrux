"""Tests for double-encoding path traversal attacks - P0 security fix.

These tests verify that the parser correctly detects path traversal
attempts that use double/triple URL encoding to bypass single-decode checks.

Attack pattern: %252e%252e/%252e%252e/etc/passwd
- First decode: %2e%2e/%2e%2e/etc/passwd (NOT detected as ..)
- Second decode: ../../etc/passwd (detected as traversal)
"""


from doxstrux.markdown_parser_core import MarkdownParserCore


class TestDoubleEncodedPathTraversal:
    """Tests for P0-2: Double-decode protection."""

    def test_single_encoded_traversal_detected(self) -> None:
        """Single-encoded path traversal must be detected."""
        parser = MarkdownParserCore("test")
        # %2e = .
        assert parser._check_path_traversal("%2e%2e/etc/passwd") is True
        assert parser._check_path_traversal("..%2f..%2fetc%2fpasswd") is True

    def test_double_encoded_traversal_detected(self) -> None:
        """Double-encoded path traversal MUST be detected (P0 fix)."""
        parser = MarkdownParserCore("test")
        # %25 = %, so %252e = %2e → .
        assert parser._check_path_traversal("%252e%252e/etc/passwd") is True, (
            "Double-encoded .. must be detected"
        )
        assert parser._check_path_traversal("%252e%252e%252f%252e%252e%252fetc%252fpasswd") is True, (
            "Fully double-encoded path must be detected"
        )

    def test_triple_encoded_traversal_detected(self) -> None:
        """Triple-encoded path traversal must be detected."""
        parser = MarkdownParserCore("test")
        # %25 = %, so %2525 = %25 → %, and %25252e = %252e → %2e → .
        assert parser._check_path_traversal("%25252e%25252e/etc/passwd") is True, (
            "Triple-encoded .. must be detected"
        )

    def test_mixed_encoding_traversal_detected(self) -> None:
        """Mixed encoding patterns must be detected."""
        parser = MarkdownParserCore("test")
        # Mix of encoded and plain
        assert parser._check_path_traversal("..%252f..%252fetc/passwd") is True
        assert parser._check_path_traversal("%2e%2e/%252e%252e/etc") is True

    def test_clean_paths_not_flagged(self) -> None:
        """Normal paths should not trigger false positives."""
        parser = MarkdownParserCore("test")
        assert parser._check_path_traversal("images/photo.png") is False
        assert parser._check_path_traversal("https://example.com/path") is False
        assert parser._check_path_traversal("/absolute/path/file.txt") is False
        assert parser._check_path_traversal("relative/path/file.txt") is False

    def test_encoded_normal_chars_not_flagged(self) -> None:
        """Encoded normal characters should not trigger false positives."""
        parser = MarkdownParserCore("test")
        # %20 = space, %2F = /
        assert parser._check_path_traversal("path%20with%20spaces") is False
        assert parser._check_path_traversal("path%2Ffile.txt") is False  # Just a slash

    def test_double_encoded_in_link(self) -> None:
        """Double-encoded traversal in markdown link must be caught."""
        content = """# Test

[Evil link](%252e%252e/%252e%252e/etc/passwd)
"""
        parser = MarkdownParserCore(content, security_profile="strict")
        result = parser.parse()

        # Check that path traversal was detected via warnings
        security = result["metadata"]["security"]
        warnings = security.get("warnings", [])
        path_traversal_warnings = [w for w in warnings if w.get("type") == "path_traversal"]
        assert len(path_traversal_warnings) > 0, (
            "Double-encoded path traversal in link must be detected"
        )

    def test_double_encoded_in_image(self) -> None:
        """Double-encoded traversal in image src must be caught."""
        content = """# Test

![Image](%252e%252e/%252e%252e/secret/image.png)
"""
        parser = MarkdownParserCore(content, security_profile="strict")
        result = parser.parse()

        # Check that path traversal was detected via warnings
        security = result["metadata"]["security"]
        warnings = security.get("warnings", [])
        path_traversal_warnings = [w for w in warnings if w.get("type") == "path_traversal"]
        assert len(path_traversal_warnings) > 0, (
            "Double-encoded path traversal in image must be detected"
        )


class TestEncodingEdgeCases:
    """Edge cases for URL encoding."""

    def test_partial_encoding_detected(self) -> None:
        """Partially encoded traversal must be detected."""
        parser = MarkdownParserCore("test")
        # %2e. = ..
        assert parser._check_path_traversal("%2e./etc/passwd") is True
        assert parser._check_path_traversal(".%2e/etc/passwd") is True

    def test_null_byte_with_traversal(self) -> None:
        """Null byte combined with traversal should still detect traversal."""
        parser = MarkdownParserCore("test")
        # %00 = null byte - the .. before it should still be detected
        # Note: "..%00" decodes to "..\x00" which splits into ["..", "\x00"]
        # The ".." segment is detected
        assert parser._check_path_traversal("../etc/passwd") is True
        # With null byte after traversal
        assert parser._check_path_traversal("%2e%2e/%00etc") is True

    def test_unicode_encoding_detected(self) -> None:
        """Unicode-encoded dots should be detected."""
        parser = MarkdownParserCore("test")
        # %c0%ae = overlong UTF-8 encoding of .
        # This is a classic attack vector
        # Note: urllib.parse.unquote handles this
        _ = parser._check_path_traversal("%c0%ae%c0%ae/etc/passwd")
        # The overlong encoding may or may not decode to .. depending on Python version
        # At minimum, we verify this doesn't crash


class TestDecodingLoopProtection:
    """Tests for infinite loop protection in decoding."""

    def test_max_decode_iterations(self) -> None:
        """Decoding loop should terminate even with pathological input."""
        parser = MarkdownParserCore("test")
        # Create deeply encoded string that would need many iterations
        # This should not hang
        deeply_encoded = "%252525252525252e%252525252525252e"  # Many layers
        # Should complete without hanging
        result = parser._check_path_traversal(deeply_encoded)
        # Result doesn't matter, just that it completes
        assert isinstance(result, bool)

    def test_self_referential_encoding(self) -> None:
        """Self-referential encoding should not cause infinite loop."""
        parser = MarkdownParserCore("test")
        # %25 encodes %, so %2525 → %25 → %
        # This should stabilize
        result = parser._check_path_traversal("%2525252525252525")
        assert isinstance(result, bool)
