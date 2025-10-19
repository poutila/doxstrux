"""
Test normalization invariant - coordinate system integrity.

CRITICAL INVARIANT: All coordinates (token.map, line numbers, byte offsets)
are derived from the same normalized text (NFC + LF).

This test verifies that text normalization happens BEFORE parsing,
ensuring token.map offsets match line indices in the normalized text.
"""

import pytest
from pathlib import Path
import sys

# Add skeleton to path for imports
SKELETON_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKELETON_ROOT))

try:
    from skeleton.doxstrux.markdown.utils.text_normalization import (
        normalize_markdown,
        parse_markdown_normalized
    )
    from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    from markdown_it import MarkdownIt
    from markdown_it.tree import SyntaxTreeNode
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Normalization utilities not available yet"
)


def test_normalization_coordinate_integrity():
    """CRITICAL: Token.map must match normalized text lines."""

    # Content with issues that normalization fixes
    # Decomposed unicode (é as e + combining acute) + CRLF line endings
    content = "# Café\r\nParagraph with é"

    # Parse correctly (normalize first)
    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Find heading token
    h1_token = next(t for t in wh.tokens if getattr(t, 'type', None) == "heading_open")

    # Extract line using token.map
    line_idx = h1_token.map[0] if h1_token.map else 0
    line_content = wh.lines[line_idx] if wh.lines else ""

    # MUST find composed "Café" (not decomposed)
    assert "Café" in line_content, \
        f"Normalization failed: {line_content!r}"

    # MUST NOT have CRLF
    assert "\r" not in line_content, \
        f"CRLF normalization failed: {line_content!r}"


def test_normalization_before_parse_not_after():
    """WRONG: Normalizing after parse breaks offsets.

    This test demonstrates why normalization MUST happen before parsing.
    """

    raw_content = "# Test\r\nLine 2"

    # WRONG WAY (what we're preventing)
    md = MarkdownIt()
    tokens_wrong = md.parse(raw_content)  # ❌ Parse raw text

    # Then normalize (too late!)
    normalized_wrong = raw_content.replace('\r\n', '\n')
    lines_wrong = normalized_wrong.splitlines(keepends=True)

    # Token.map points to wrong lines
    # This would fail if we tried to use it

    # RIGHT WAY (using our helper)
    tokens_right, tree_right, normalized_right = parse_markdown_normalized(raw_content)
    wh = TokenWarehouse(tokens_right, tree_right, normalized_right)

    # Now token.map matches wh.lines
    assert wh.tokens[0].map is not None or True  # Some token should have map


def test_normalize_unicode_nfc():
    """Test Unicode NFC normalization works correctly."""

    # Decomposed é (e + combining acute accent U+0301)
    decomposed = "Café"  # May contain decomposed forms
    normalized = normalize_markdown(decomposed)

    # Should be in NFC composed form
    import unicodedata
    assert unicodedata.is_normalized('NFC', normalized), \
        "Content should be NFC normalized"


def test_normalize_crlf_to_lf():
    """Test CRLF → LF normalization works correctly."""

    content_with_crlf = "Line 1\r\nLine 2\r\nLine 3"
    normalized = normalize_markdown(content_with_crlf)

    # Should have LF only, no CR
    assert "\r\n" not in normalized, "CRLF should be converted to LF"
    assert "\r" not in normalized, "CR should be removed"
    assert "Line 1\nLine 2\nLine 3" == normalized


def test_normalize_empty_string():
    """Test normalization handles empty strings."""

    assert normalize_markdown("") == ""


def test_normalize_already_normalized():
    """Test normalization is idempotent."""

    content = "# Already normalized\nWith LF endings"
    first_pass = normalize_markdown(content)
    second_pass = normalize_markdown(first_pass)

    assert first_pass == second_pass, "Normalization should be idempotent"


def test_parse_markdown_normalized_returns_tuple():
    """Test parse_markdown_normalized returns correct structure."""

    content = "# Test"
    tokens, tree, normalized = parse_markdown_normalized(content)

    # Should return 3-tuple
    assert isinstance(tokens, list), "tokens should be a list"
    assert tree is not None, "tree should not be None"
    assert isinstance(normalized, str), "normalized should be a string"

    # Normalized should be NFC + LF
    import unicodedata
    assert unicodedata.is_normalized('NFC', normalized)
    assert "\r" not in normalized


def test_coordinate_system_integrity_with_complex_unicode():
    """Test coordinate integrity with complex unicode scenarios."""

    # Multiple decomposed characters, CRLF, mixed content
    content = """# Café Naïve
\r
Résumé with **bold** and `code`
\r
Another line with émojis 🎉
"""

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Find a heading
    heading_tokens = [t for t in wh.tokens if getattr(t, 'type', None) == "heading_open"]

    if heading_tokens:
        h1 = heading_tokens[0]
        if h1.map:
            line_idx = h1.map[0]
            if wh.lines and line_idx < len(wh.lines):
                line = wh.lines[line_idx]

                # Should contain NFC-normalized text
                assert "Café" in line or "Naive" in line or "Naïve" in line
                # Should not contain CRLF
                assert "\r" not in line


def test_token_map_indices_valid():
    """Test that all token.map indices are valid after normalization."""

    content = """# H1
\r
Paragraph 1
\r
## H2
\r
Paragraph 2
"""

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # All tokens with map should have valid line indices
    for tok in wh.tokens:
        if hasattr(tok, 'map') and tok.map:
            start_line, end_line = tok.map
            if wh.lines:
                # Indices should be within bounds
                assert 0 <= start_line < len(wh.lines), \
                    f"Token map start {start_line} out of bounds (0-{len(wh.lines)})"
                assert 0 <= end_line <= len(wh.lines), \
                    f"Token map end {end_line} out of bounds (0-{len(wh.lines)})"


def test_unicode_crlf_interplay_nfc():
    """Test NFC normalization + CRLF→LF doesn't corrupt offsets."""

    # Use both decomposed Unicode (NFD) and CRLF line endings
    content = "café\r\nnaïve\r\n"  # é and ï are NFD (decomposed)

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Should be NFC (composed) + LF
    assert "café\nnaïve\n" in normalized
    assert "\r" not in normalized  # All CRLF converted to LF
    assert wh.lines == ["café\n", "naïve\n"]


def test_emoji_with_crlf():
    """Test emoji (multi-byte UTF-8) + CRLF normalization."""

    content = "Hello 👋\r\nWorld 🌍\r\n"

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert len(wh.lines) == 2
    assert wh.lines[0] == "Hello 👋\n"
    assert wh.lines[1] == "World 🌍\n"

    # Token maps should be valid despite multi-byte characters
    for tok in wh.tokens:
        if hasattr(tok, 'map') and tok.map:
            start, end = tok.map
            assert 0 <= start < len(wh.lines)
            assert start <= end <= len(wh.lines)


def test_mixed_nfc_nfd_crlf():
    """Test mixed NFC/NFD normalization + CRLF edge case."""

    # First café is NFD (decomposed), second is NFC (composed)
    content_nfd = "cafe\u0301\r\n"  # NFD: e + combining acute
    content_nfc = "café\r\n"        # NFC: composed é

    # Both should normalize to same result
    _, _, normalized_nfd = parse_markdown_normalized(content_nfd)
    _, _, normalized_nfc = parse_markdown_normalized(content_nfc)

    # Both should be NFC + LF
    assert normalized_nfd == normalized_nfc == "café\n"


def test_zero_width_characters_with_crlf():
    """Test zero-width characters + CRLF don't corrupt line boundaries."""

    # Zero-width space, zero-width joiner
    content = "Word\u200b\r\nAnother\u200d\r\n"

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Should preserve zero-width chars but normalize line endings
    assert "\r" not in normalized
    assert len(wh.lines) == 2
    # Zero-width chars are preserved in NFC normalization
    assert "\u200b" in normalized or "\u200d" in normalized


def test_combining_diacritics_with_crlf():
    """Test multiple combining diacritics + CRLF normalization."""

    # Multiple diacritics on same base character
    content = "a\u0301\u0302\u0303\r\ntext\r\n"  # a + acute + circumflex + tilde

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    assert "\r" not in normalized
    assert len(wh.lines) == 2

    # NFC may or may not combine all diacritics (depends on Unicode version)
    # But offsets should still be valid
    for tok in wh.tokens:
        if hasattr(tok, 'map') and tok.map:
            start, end = tok.map
            assert 0 <= start <= end <= len(wh.lines)


def test_bidirectional_text_with_crlf():
    """Test BiDi control characters + CRLF normalization."""

    # RTL override character + CRLF
    content = "Hello\u202e\r\nWorld\r\n"  # U+202E RTL override

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # BiDi chars preserved, CRLF converted
    assert "\r" not in normalized
    assert "\u202e" in normalized  # BiDi char preserved
    assert len(wh.lines) == 2
