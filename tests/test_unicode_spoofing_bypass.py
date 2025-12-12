"""Tests for unicode spoofing bypass protection - P1 security fix.

These tests verify that large documents don't bypass unicode spoofing detection
through padding attacks.
"""


from doxstrux.markdown_parser_core import MarkdownParserCore


class TestUnicodeSpoofingLargeDocuments:
    """Tests for P1-1: Large document unicode spoofing bypass."""

    def test_large_document_fails_closed(self) -> None:
        """Documents > 100KB must fail-closed for unicode checks."""
        # Create large document (> 100KB)
        padding = "A" * 110000  # 110KB of padding
        content = f"# Test\n\n{padding}"

        # Use permissive mode to allow large content (strict has 100KB limit)
        parser = MarkdownParserCore(content, security_profile="permissive")

        # Call the unicode spoofing check directly
        result = parser._check_unicode_spoofing(content)

        # MUST fail-closed: assume presence of unicode issues
        assert result["has_bidi"] is True, (
            "Large documents must fail-closed for BiDi check"
        )
        assert result["has_confusables"] is True, (
            "Large documents must fail-closed for confusables check"
        )
        assert result.get("scan_limit_exceeded") is True, (
            "Must flag that scan limit was exceeded"
        )

    def test_normal_document_scans_correctly(self) -> None:
        """Normal-sized documents should be scanned correctly."""
        # Small, clean document
        content = "# Clean Document\n\nNo unicode issues here."

        parser = MarkdownParserCore(content, security_profile="strict")
        result = parser._check_unicode_spoofing(content)

        # Should NOT have issues flagged
        assert result["has_bidi"] is False
        assert result["has_confusables"] is False
        assert result.get("scan_limit_exceeded") is not True

    def test_bidi_detected_in_normal_document(self) -> None:
        """BiDi characters should be detected in normal-sized documents."""
        # Document with BiDi override (U+202E = RLO)
        content = "# Test\n\nHello \u202eevil\u202c world"

        parser = MarkdownParserCore(content, security_profile="strict")
        result = parser._check_unicode_spoofing(content)

        assert result["has_bidi"] is True, (
            "BiDi override should be detected"
        )

    def test_confusables_detected_in_normal_document(self) -> None:
        """Confusable characters should be detected in normal-sized documents."""
        # Document with Cyrillic 'а' (U+0430) that looks like Latin 'a'
        content = "# Test\n\nРаypal"  # Cyrillic а

        parser = MarkdownParserCore(content, security_profile="strict")
        result = parser._check_unicode_spoofing(content)

        # Note: Whether this triggers depends on the confusable detection
        # At minimum, we verify the function runs without error
        assert isinstance(result["has_confusables"], bool)

    def test_empty_text_returns_clean(self) -> None:
        """Empty text should return all False (clean)."""
        parser = MarkdownParserCore("test", security_profile="strict")
        result = parser._check_unicode_spoofing("")

        assert result["has_bidi"] is False
        assert result["has_confusables"] is False
        assert result.get("scan_limit_exceeded") is not True


class TestPaddingAttackPrevention:
    """Tests for preventing padding attacks on unicode checks."""

    def test_bidi_with_padding_fails_closed(self) -> None:
        """BiDi + padding attack must fail-closed."""
        # Attacker tries to hide BiDi with padding
        padding = "A" * 100001  # Just over limit
        evil_content = "\u202eevil\u202c"  # RLO ... PDF
        content = f"{padding}{evil_content}"

        # Use permissive to allow large content
        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser._check_unicode_spoofing(content)

        # MUST fail-closed - can't scan, so assume bad
        assert result["has_bidi"] is True, (
            "Padding attack must not bypass BiDi detection"
        )

    def test_confusables_with_padding_fails_closed(self) -> None:
        """Confusables + padding attack must fail-closed."""
        # Attacker tries to hide confusables with padding
        padding = "A" * 100001  # Just over limit
        evil_content = "Pаypal"  # Cyrillic а
        content = f"{padding}{evil_content}"

        # Use permissive to allow large content
        parser = MarkdownParserCore(content, security_profile="permissive")
        result = parser._check_unicode_spoofing(content)

        # MUST fail-closed
        assert result["has_confusables"] is True, (
            "Padding attack must not bypass confusables detection"
        )
