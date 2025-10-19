"""
Test normalization map fidelity - RED TEAM BLOCKER TEST 1.

CRITICAL: Verify CRLF + NFC normalization doesn't corrupt token.map coordinates.

This test ensures that:
1. Text normalization happens BEFORE parsing (not after)
2. token.map offsets match line indices in the normalized text
3. get_line_range() returns content from the SAME coordinate system

Red-Team Scenario:
If normalization happens AFTER parsing, token.map will point to wrong lines
because CRLF (2 bytes) vs LF (1 byte) causes line index drift.
"""

import pytest
from pathlib import Path
import sys

# Add skeleton to path for imports
SKELETON_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKELETON_ROOT))

try:
    from skeleton.doxstrux.markdown.utils.text_normalization import parse_markdown_normalized
    from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Normalization utilities not available"
)


def test_normalization_map_fidelity():
    """
    CRITICAL: token.map must reference normalized text lines.

    Test with decomposed unicode (é as e + combining acute) + CRLF line endings.
    """
    # Content with BOTH normalization issues:
    # - Decomposed é (e + U+0301 combining acute)
    # - CRLF line endings
    content = "# Titre\u0301\r\n\r\nParagraphe\r\n"  # Decomposed é + CRLF

    # Parse with correct normalization order
    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Find heading_open token
    h_open_indices = wh.by_type.get("heading_open", [])
    assert len(h_open_indices) > 0, "Should have heading_open token"

    h_open_idx = h_open_indices[0]
    h_token = wh.tokens[h_open_idx]

    # Extract line using token.map
    a, b = getattr(h_token, 'map', (0, 1))
    assert wh.lines is not None, "Warehouse should have lines"

    # Get line content from warehouse
    line_content = "".join(wh.lines[a:b])

    # CRITICAL ASSERTIONS:
    # 1. Must find composed é (NFC normalization worked)
    assert "é" in line_content, \
        f"NFC normalization failed: expected 'é', got {line_content!r}"

    # 2. Must NOT have CRLF (line ending normalization worked)
    assert "\r\n" not in line_content, \
        f"CRLF normalization failed: {line_content!r}"

    # 3. Must NOT have decomposed form
    assert "\u0301" not in line_content, \
        f"Decomposed unicode not normalized: {line_content!r}"

    # 4. Normalized text in warehouse must match what parser saw
    assert wh.lines == normalized.splitlines(True), \
        "Warehouse lines don't match normalized text"


def test_crlf_line_count_integrity():
    """
    Verify CRLF normalization doesn't cause line count drift.

    If normalization happens after parsing, Windows CRLF files will have
    mismatched line counts between token.map and actual line indices.
    """
    # Document with CRLF (Windows line endings)
    content = "# H1\r\n\r\nParagraph\r\n\r\n## H2\r\n"

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Count lines in normalized text
    normalized_line_count = len(normalized.splitlines(True))

    # Count lines in original (would be different if CRLF not normalized)
    original_line_count = len(content.splitlines(True))

    # Normalized should have SAME line count (CRLF -> LF doesn't change count)
    assert normalized_line_count == original_line_count, \
        f"Line count changed: {original_line_count} -> {normalized_line_count}"

    # Warehouse line_count should match normalized
    assert wh.line_count == normalized_line_count, \
        f"Warehouse line_count mismatch: {wh.line_count} != {normalized_line_count}"

    # Verify no CRLF in normalized text
    assert "\r\n" not in normalized, \
        "CRLF found in normalized text"

    # Verify all token.map coordinates are within line count
    for i, tok in enumerate(wh.tokens):
        m = getattr(tok, 'map', None)
        if m and isinstance(m, (list, tuple)) and len(m) == 2:
            start, end = m
            if start is not None:
                assert 0 <= start <= wh.line_count, \
                    f"Token {i} map start {start} out of range [0, {wh.line_count}]"
            if end is not None:
                assert 0 <= end <= wh.line_count, \
                    f"Token {i} map end {end} out of range [0, {wh.line_count}]"


def test_unicode_nfc_token_content():
    """
    Verify NFC normalization applies to token content (not just coordinates).

    Token content must also be normalized so string comparisons work correctly.
    """
    # Content with decomposed accented characters
    content = "# Cafe\u0301\r\n"  # Café with decomposed é

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Find inline token (contains heading text)
    inline_indices = wh.by_type.get("inline", [])
    assert len(inline_indices) > 0, "Should have inline token"

    inline_tok = wh.tokens[inline_indices[0]]
    content_text = getattr(inline_tok, 'content', '')

    # Content must be NFC normalized
    assert "Café" in content_text or "é" in content_text, \
        f"Content not normalized: {content_text!r}"

    # Must NOT have decomposed form
    assert "\u0301" not in content_text, \
        f"Decomposed unicode in token content: {content_text!r}"


def test_mixed_normalization_edge_cases():
    """
    Test combinations of CRLF, LF, and decomposed unicode.

    Real-world documents may have mixed line endings (copy-paste from different sources).
    """
    # Mixed line endings + decomposed unicode
    content = (
        "# Title\u0301\r\n"  # CRLF + decomposed é
        "\n"                  # LF only
        "Para 1\r\n"         # CRLF
        "\r\n"                # CRLF blank line
        "Para 2\n"           # LF only
    )

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Normalized text should have:
    # - No CRLF (all converted to LF)
    # - No decomposed unicode (all NFC)
    assert "\r\n" not in normalized, "CRLF not normalized"
    assert "\u0301" not in normalized, "Decomposed unicode not normalized"

    # All token.map coordinates should be valid
    for i, tok in enumerate(wh.tokens):
        m = getattr(tok, 'map', None)
        if m and len(m) == 2:
            a, b = m
            if a is not None and b is not None:
                # Should be able to slice lines without IndexError
                try:
                    line_slice = wh.lines[a:b] if wh.lines else []
                    # Verify no CRLF in extracted lines
                    for line in line_slice:
                        assert "\r\n" not in line, \
                            f"CRLF in line {a}-{b}: {line!r}"
                except IndexError:
                    pytest.fail(
                        f"Token {i} map ({a}, {b}) out of bounds "
                        f"(line_count={wh.line_count})"
                    )


def test_section_title_from_normalized_content():
    """
    Verify section titles are extracted from normalized text.

    Section titles must reflect NFC normalization, not original decomposed form.
    """
    # Heading with decomposed accented character
    content = "# Cafe\u0301\r\n\r\nContent\r\n"  # Café decomposed

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Get first section
    assert len(wh.sections) > 0, "Should have at least one section"
    section = wh.sections[0]

    # Section is tuple: (start_line, end_line, token_idx, level, title)
    title = section[4]

    # Title must be NFC normalized
    assert "Café" in title or "é" in title, \
        f"Section title not normalized: {title!r}"

    # Must NOT have decomposed form
    assert "\u0301" not in title, \
        f"Decomposed unicode in section title: {title!r}"
