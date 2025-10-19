"""
Test Section dataclass shape invariant.

CRITICAL INVARIANT: Section tuple must have exact shape:
(start_line:int, end_line:int|None, token_idx:int, level:int, title:str)

This test ensures the Section shape never changes.
"""

import pytest
from pathlib import Path
import sys

# Add skeleton to path for imports
SKELETON_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKELETON_ROOT))

try:
    from doxstrux.markdown.utils.section import Section
    from doxstrux.markdown.utils.text_normalization import parse_markdown_normalized
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE,
    reason="Section utilities not available yet"
)


def test_section_dataclass_fields():
    """Test Section dataclass has correct fields."""
    section = Section(
        start_line=5,
        end_line=10,
        token_idx=2,
        level=1,
        title="Introduction"
    )

    assert section.start_line == 5
    assert section.end_line == 10
    assert section.token_idx == 2
    assert section.level == 1
    assert section.title == "Introduction"


def test_section_frozen():
    """Test Section is immutable (frozen=True)."""
    section = Section(
        start_line=5,
        end_line=10,
        token_idx=2,
        level=1,
        title="Introduction"
    )

    # Attempting to modify should raise error
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        section.start_line = 99


def test_section_to_tuple():
    """Test Section.to_tuple() returns canonical format."""
    section = Section(
        start_line=5,
        end_line=10,
        token_idx=2,
        level=1,
        title="Introduction"
    )

    tuple_form = section.to_tuple()

    # CRITICAL: Tuple must have exact shape
    assert len(tuple_form) == 5, f"Section tuple wrong length: {tuple_form}"
    assert tuple_form == (5, 10, 2, 1, "Introduction")

    # Verify types
    start_line, end_line, token_idx, level, title = tuple_form
    assert isinstance(start_line, int)
    assert end_line is None or isinstance(end_line, int)
    assert isinstance(token_idx, int)
    assert isinstance(level, int) and 1 <= level <= 6
    assert isinstance(title, str)


def test_section_from_tuple():
    """Test Section.from_tuple() parses correctly."""
    tuple_form = (5, 10, 2, 1, "Introduction")
    section = Section.from_tuple(tuple_form)

    assert section.start_line == 5
    assert section.end_line == 10
    assert section.token_idx == 2
    assert section.level == 1
    assert section.title == "Introduction"


def test_section_none_end_line():
    """Test Section with None end_line (unclosed section)."""
    section = Section(
        start_line=5,
        end_line=None,  # Unclosed section
        token_idx=2,
        level=1,
        title="Introduction"
    )

    tuple_form = section.to_tuple()
    assert tuple_form == (5, None, 2, 1, "Introduction")


def test_section_validation_start_line():
    """Test Section validates start_line."""
    # Negative start_line should fail
    with pytest.raises(ValueError, match="start_line"):
        Section(start_line=-1, end_line=10, token_idx=0, level=1, title="Test")

    # Non-int start_line should fail
    with pytest.raises(ValueError, match="start_line"):
        Section(start_line="5", end_line=10, token_idx=0, level=1, title="Test")


def test_section_validation_end_line():
    """Test Section validates end_line."""
    # end_line < start_line should fail
    with pytest.raises(ValueError, match="end_line"):
        Section(start_line=10, end_line=5, token_idx=0, level=1, title="Test")

    # Negative end_line should fail
    with pytest.raises(ValueError, match="end_line"):
        Section(start_line=5, end_line=-1, token_idx=0, level=1, title="Test")


def test_section_validation_level():
    """Test Section validates level (1-6)."""
    # Level < 1 should fail
    with pytest.raises(ValueError, match="level"):
        Section(start_line=5, end_line=10, token_idx=0, level=0, title="Test")

    # Level > 6 should fail
    with pytest.raises(ValueError, match="level"):
        Section(start_line=5, end_line=10, token_idx=0, level=7, title="Test")


def test_section_validation_title():
    """Test Section validates title."""
    # Non-string title should fail
    with pytest.raises(ValueError, match="title"):
        Section(start_line=5, end_line=10, token_idx=0, level=1, title=123)


def test_warehouse_sections_canonical_format():
    """Test TokenWarehouse returns sections in canonical format."""
    content = """# H1
Paragraph in H1

## H2
Paragraph in H2

### H3
Paragraph in H3
"""

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Every section must have exact shape
    for section in wh.sections:
        assert len(section) == 5, f"Section wrong length: {section}"

        start_line, end_line, token_idx, level, title = section

        # Validate types
        assert isinstance(start_line, int), f"start_line not int: {start_line}"
        assert end_line is None or isinstance(end_line, int), f"end_line wrong type: {end_line}"
        assert isinstance(token_idx, int), f"token_idx not int: {token_idx}"
        assert isinstance(level, int) and 1 <= level <= 6, f"level invalid: {level}"
        assert isinstance(title, str), f"title not str: {title}"


def test_warehouse_sections_closed():
    """Test TokenWarehouse closes sections with end_line."""
    content = """# H1
Para 1

## H2
Para 2
"""

    tokens, tree, normalized = parse_markdown_normalized(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # All sections should be closed (have end_line)
    for section in wh.sections:
        start_line, end_line, token_idx, level, title = section
        # In this content, all sections should have end_line set
        assert end_line is not None, f"Section not closed: {section}"
        assert end_line >= start_line, f"end_line < start_line: {section}"


def test_section_roundtrip():
    """Test Section → tuple → Section roundtrip."""
    original = Section(
        start_line=5,
        end_line=10,
        token_idx=2,
        level=2,
        title="Test Section"
    )

    # Convert to tuple
    as_tuple = original.to_tuple()

    # Convert back to Section
    reconstructed = Section.from_tuple(as_tuple)

    # Should be identical
    assert reconstructed == original
