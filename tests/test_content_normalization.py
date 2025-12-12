"""Tests for content normalization (Phase 8 - THREE_ADDITIONS.md).

This module tests the content normalization invariants from THREE_ADDITIONS.md:
- INV-1.1: Line ending equivalence (CRLF/LF produce identical parse results except original_content)
- INV-1.2: No trailing CR in lines
- INV-1.3: Bare CR handling (old Mac style)
- INV-1.4: Unicode composition equivalence (NFC/NFD produce identical slugs)
- INV-1.5: Line-ending normalization does not weaken security
- INV-1.6: Unicode normalization does not weaken security
- INV-1.7: Idempotence (normalizing already-normalized content is no-op)
- INV-1.8: Raw input preservation (original_content preserved)

TDD: These tests are written before implementation and should initially FAIL.
"""

import pytest

from doxstrux.markdown_parser_core import MarkdownParserCore


class TestLineEndingNormalization:
    """Tests for INV-1.1, INV-1.2, INV-1.3: Line ending normalization."""

    def test_crlf_and_lf_produce_identical_structure(self):
        """INV-1.1: CRLF and LF versions produce identical structure.

        Parse the same logical content with CRLF vs LF line endings.
        The 'structure', 'mappings', 'metadata', 'content' keys MUST be identical.
        Only 'original_content' is allowed to differ.
        """
        content_lf = "# Heading\n\nParagraph text.\n\n- Item 1\n- Item 2\n"
        content_crlf = "# Heading\r\n\r\nParagraph text.\r\n\r\n- Item 1\r\n- Item 2\r\n"

        result_lf = MarkdownParserCore(content_lf, security_profile="permissive").parse()
        result_crlf = MarkdownParserCore(content_crlf, security_profile="permissive").parse()

        # These keys MUST be identical
        assert result_lf["structure"] == result_crlf["structure"], (
            "INV-1.1: structure differs between CRLF and LF"
        )
        assert result_lf["mappings"] == result_crlf["mappings"], (
            "INV-1.1: mappings differs between CRLF and LF"
        )
        assert result_lf["content"] == result_crlf["content"], (
            "INV-1.1: content differs between CRLF and LF"
        )
        # metadata.security may differ due to path differences, but structural metadata should match
        # Remove source_path before comparison as it's not relevant
        meta_lf = {k: v for k, v in result_lf["metadata"].items() if k != "source_path"}
        meta_crlf = {k: v for k, v in result_crlf["metadata"].items() if k != "source_path"}
        assert meta_lf == meta_crlf, (
            "INV-1.1: metadata differs between CRLF and LF"
        )

    def test_crlf_and_lf_headings_identical(self):
        """INV-1.1: Heading extraction identical for CRLF vs LF."""
        content_lf = "# First\n\n## Second\n\nText\n"
        content_crlf = "# First\r\n\r\n## Second\r\n\r\nText\r\n"

        result_lf = MarkdownParserCore(content_lf, security_profile="permissive").parse()
        result_crlf = MarkdownParserCore(content_crlf, security_profile="permissive").parse()

        assert result_lf["structure"]["headings"] == result_crlf["structure"]["headings"]

    def test_crlf_and_lf_tables_identical(self):
        """INV-1.1: Table extraction identical for CRLF vs LF."""
        table_lf = "| A | B |\n|---|---|\n| 1 | 2 |\n"
        table_crlf = "| A | B |\r\n|---|---|\r\n| 1 | 2 |\r\n"

        result_lf = MarkdownParserCore(table_lf, security_profile="permissive").parse()
        result_crlf = MarkdownParserCore(table_crlf, security_profile="permissive").parse()

        assert result_lf["structure"]["tables"] == result_crlf["structure"]["tables"]

    def test_crlf_and_lf_code_blocks_identical(self):
        """INV-1.1: Code block extraction identical for CRLF vs LF."""
        code_lf = "```python\nprint('hello')\n```\n"
        code_crlf = "```python\r\nprint('hello')\r\n```\r\n"

        result_lf = MarkdownParserCore(code_lf, security_profile="permissive").parse()
        result_crlf = MarkdownParserCore(code_crlf, security_profile="permissive").parse()

        assert result_lf["structure"]["code_blocks"] == result_crlf["structure"]["code_blocks"]

    def test_no_trailing_cr_in_lines_after_crlf_input(self):
        """INV-1.2: No line in content.lines ends with CR after parsing CRLF input."""
        content_crlf = "Line1\r\nLine2\r\nLine3\r\n"

        result = MarkdownParserCore(content_crlf, security_profile="permissive").parse()
        lines = result["content"]["lines"]

        for i, line in enumerate(lines):
            assert not line.endswith("\r"), (
                f"INV-1.2: Line {i} ends with CR: {repr(line)}"
            )

    def test_no_trailing_cr_in_lines_mixed_input(self):
        """INV-1.2: No trailing CR even with mixed CRLF and LF input."""
        content_mixed = "Line1\r\nLine2\nLine3\r\nLine4\n"

        result = MarkdownParserCore(content_mixed, security_profile="permissive").parse()
        lines = result["content"]["lines"]

        for i, line in enumerate(lines):
            assert not line.endswith("\r"), (
                f"INV-1.2: Line {i} ends with CR: {repr(line)}"
            )

    def test_bare_cr_treated_as_line_separator(self):
        """INV-1.3: Bare CR (old Mac style) treated as line separator."""
        # Old Mac format: lines separated by bare CR (no LF)
        content_bare_cr = "Line1\rLine2\rLine3"

        result = MarkdownParserCore(content_bare_cr, security_profile="permissive").parse()
        lines = result["content"]["lines"]

        # Should have 3 lines
        assert len(lines) == 3, (
            f"INV-1.3: Expected 3 lines from bare CR input, got {len(lines)}: {lines}"
        )
        assert lines[0] == "Line1"
        assert lines[1] == "Line2"
        assert lines[2] == "Line3"

    def test_bare_cr_no_trailing_cr(self):
        """INV-1.3: After bare CR normalization, no lines end with CR."""
        content_bare_cr = "Line1\rLine2\rLine3\r"

        result = MarkdownParserCore(content_bare_cr, security_profile="permissive").parse()
        lines = result["content"]["lines"]

        for i, line in enumerate(lines):
            assert not line.endswith("\r"), (
                f"INV-1.3/INV-1.2: Line {i} ends with CR after bare CR normalization"
            )

    def test_crlf_and_lf_line_counts_match(self):
        """INV-1.1: Line counts match between CRLF and LF versions."""
        content_lf = "Line1\nLine2\nLine3\n"
        content_crlf = "Line1\r\nLine2\r\nLine3\r\n"

        result_lf = MarkdownParserCore(content_lf, security_profile="permissive").parse()
        result_crlf = MarkdownParserCore(content_crlf, security_profile="permissive").parse()

        assert result_lf["metadata"]["total_lines"] == result_crlf["metadata"]["total_lines"]
        assert len(result_lf["content"]["lines"]) == len(result_crlf["content"]["lines"])


class TestUnicodeNormalization:
    """Tests for INV-1.4: Unicode composition equivalence."""

    def test_nfc_and_nfd_headings_produce_identical_slugs(self):
        """INV-1.4: NFC and NFD forms produce identical heading slugs.

        The character 'é' can be represented as:
        - NFC (precomposed): U+00E9 (é as single codepoint)
        - NFD (decomposed): U+0065 U+0301 (e + combining acute accent)

        Both forms MUST produce identical slug and text.
        """
        import unicodedata

        # Create NFC and NFD versions of heading with é
        heading_nfc = unicodedata.normalize("NFC", "# Café\n")
        heading_nfd = unicodedata.normalize("NFD", "# Café\n")

        # Verify they're actually different byte sequences
        assert heading_nfc != heading_nfd, "Test setup: NFC and NFD should differ"

        result_nfc = MarkdownParserCore(heading_nfc, security_profile="permissive").parse()
        result_nfd = MarkdownParserCore(heading_nfd, security_profile="permissive").parse()

        headings_nfc = result_nfc["structure"]["headings"]
        headings_nfd = result_nfd["structure"]["headings"]

        assert len(headings_nfc) == 1
        assert len(headings_nfd) == 1

        # Text and slug MUST be identical
        assert headings_nfc[0]["text"] == headings_nfd[0]["text"], (
            "INV-1.4: Heading text differs between NFC and NFD"
        )
        assert headings_nfc[0]["slug"] == headings_nfd[0]["slug"], (
            "INV-1.4: Heading slug differs between NFC and NFD"
        )

    def test_nfc_and_nfd_produce_identical_structure(self):
        """INV-1.4: Full document structure identical for NFC vs NFD."""
        import unicodedata

        # Document with various Unicode characters that have NFC/NFD differences
        doc = "# Naïve Résumé\n\nCafé naïf.\n"
        doc_nfc = unicodedata.normalize("NFC", doc)
        doc_nfd = unicodedata.normalize("NFD", doc)

        result_nfc = MarkdownParserCore(doc_nfc, security_profile="permissive").parse()
        result_nfd = MarkdownParserCore(doc_nfd, security_profile="permissive").parse()

        assert result_nfc["structure"] == result_nfd["structure"], (
            "INV-1.4: Structure differs between NFC and NFD"
        )


class TestNormalizationSecurity:
    """Tests for INV-1.5, INV-1.6: Normalization does not weaken security."""

    def test_javascript_scheme_detected_with_crlf(self):
        """INV-1.5: javascript: scheme detected even with CRLF line endings.

        Security checks run on raw input before normalization.
        CRLF doesn't bypass detection - the pattern is caught in raw content scan.
        In strict mode, this causes early rejection (exception).
        """
        from doxstrux.markdown.exceptions import MarkdownSecurityError

        # Content with javascript: and CRLF line endings
        content = '[click](javascript:alert(1))\r\n'

        # Strict mode: should raise exception (detection works on raw input)
        with pytest.raises(MarkdownSecurityError) as exc_info:
            MarkdownParserCore(content, security_profile="strict").parse()

        assert "javascript" in str(exc_info.value).lower(), (
            "INV-1.5: javascript: scheme not mentioned in security error"
        )

    def test_javascript_scheme_detected_after_bare_cr(self):
        """INV-1.5: javascript: scheme detected even with bare CR in content."""
        from doxstrux.markdown.exceptions import MarkdownSecurityError

        content = 'text\r[click](javascript:alert(1))\rmore'

        # Strict mode: should raise exception (detection works on raw input)
        with pytest.raises(MarkdownSecurityError) as exc_info:
            MarkdownParserCore(content, security_profile="strict").parse()

        assert "javascript" in str(exc_info.value).lower(), (
            "INV-1.5: javascript: scheme not mentioned in security error"
        )

    def test_crlf_does_not_bypass_script_tag_detection(self):
        """INV-1.5: CRLF doesn't allow script tags to bypass detection."""
        from doxstrux.markdown.exceptions import MarkdownSecurityError

        # Script tag with CRLF line endings
        content = '<script>alert(1)</script>\r\n'

        with pytest.raises(MarkdownSecurityError) as exc_info:
            MarkdownParserCore(content, security_profile="strict").parse()

        assert "script" in str(exc_info.value).lower()

    def test_confusable_detection_after_nfc_normalization(self):
        """INV-1.6: Confusable characters detected after Unicode normalization.

        Some homoglyph attacks use characters that look like ASCII but aren't.
        NFC normalization MUST NOT weaken confusable detection.
        """
        import unicodedata

        # Cyrillic 'а' (U+0430) looks like Latin 'a' (U+0061)
        # This could be used for phishing: "pаypal.com" with Cyrillic а
        confusable_text = "# Pаypal\n"  # Contains Cyrillic а

        # Normalize to NFC (shouldn't change Cyrillic)
        confusable_nfc = unicodedata.normalize("NFC", confusable_text)

        result = MarkdownParserCore(confusable_nfc, security_profile="strict").parse()

        security = result["metadata"]["security"]
        stats = security.get("statistics", {})

        # Parser should detect confusables
        assert stats.get("confusables_present", False), (
            "INV-1.6: Confusable characters not detected after NFC normalization"
        )


class TestNormalizationIdempotence:
    """Tests for INV-1.7: Normalization idempotence."""

    def test_double_normalization_produces_same_result(self):
        """INV-1.7: Parsing already-normalized content produces identical result.

        Normalizing already-normalized content MUST NOT change it.
        This tests idempotence by parsing the content field from first parse.
        """
        content = "# Heading\r\n\r\nParagraph\r\n"

        result1 = MarkdownParserCore(content, security_profile="permissive").parse()

        # Get the raw content from first parse and parse again
        # After normalization, content["raw"] should be normalized
        normalized_content = result1["content"]["raw"]
        result2 = MarkdownParserCore(normalized_content, security_profile="permissive").parse()

        # Structure should be identical
        assert result1["structure"] == result2["structure"], (
            "INV-1.7: Structure differs after double parse (not idempotent)"
        )
        assert result1["content"] == result2["content"], (
            "INV-1.7: Content differs after double parse (not idempotent)"
        )

    def test_normalized_content_has_no_crlf(self):
        """INV-1.7: After normalization, content.raw has no CRLF sequences."""
        content = "Line1\r\nLine2\r\n"

        result = MarkdownParserCore(content, security_profile="permissive").parse()
        raw = result["content"]["raw"]

        assert "\r\n" not in raw, "INV-1.7: CRLF still present after normalization"
        assert "\r" not in raw, "INV-1.7: Bare CR still present after normalization"


class TestRawInputPreservation:
    """Tests for INV-1.8: Raw input preservation."""

    def test_original_content_preserved_for_crlf(self):
        """INV-1.8: original_content preserves raw CRLF input."""
        content_crlf = "Line1\r\nLine2\r\n"

        parser = MarkdownParserCore(content_crlf, security_profile="permissive")
        result = parser.parse()

        # original_content should be accessible (either in result or on parser)
        # Per INV-1.8, if exposed it MUST equal raw input
        if "original_content" in result:
            assert result["original_content"] == content_crlf
        elif hasattr(parser, "original_content"):
            assert parser.original_content == content_crlf
        else:
            pytest.fail("INV-1.8: No original_content field found")

    def test_original_content_differs_from_normalized_content(self):
        """INV-1.8: original_content differs from content.raw for CRLF input."""
        content_crlf = "Line1\r\nLine2\r\n"

        parser = MarkdownParserCore(content_crlf, security_profile="permissive")
        result = parser.parse()

        # After normalization, content.raw should be LF-only
        normalized_raw = result["content"]["raw"]

        # Get original content
        if "original_content" in result:
            original = result["original_content"]
        elif hasattr(parser, "original_content"):
            original = parser.original_content
        else:
            pytest.fail("INV-1.8: No original_content field found")

        # They should differ for CRLF input
        assert original != normalized_raw, (
            "INV-1.8: original_content should differ from normalized content.raw"
        )
        assert "\r\n" in original, "INV-1.8: original_content should contain CRLF"
        assert "\r\n" not in normalized_raw, "Normalized raw should not contain CRLF"

    def test_original_content_equals_input_for_lf(self):
        """INV-1.8: original_content equals input for LF-only content."""
        content_lf = "Line1\nLine2\n"

        parser = MarkdownParserCore(content_lf, security_profile="permissive")
        result = parser.parse()

        if "original_content" in result:
            assert result["original_content"] == content_lf
        elif hasattr(parser, "original_content"):
            assert parser.original_content == content_lf
        else:
            pytest.fail("INV-1.8: No original_content field found")
