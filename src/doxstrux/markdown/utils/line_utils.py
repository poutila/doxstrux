"""Line slicing and manipulation utilities.

This module provides pure functions for working with line-based content,
following the markdown-it convention where end_line is the first line AFTER content.

Functions:
    slice_lines: Slice lines from start to end (end-inclusive for markdown-it convention)
    slice_lines_raw: Get raw string from line range
    build_line_offsets: Build character offset map for each line start
"""


def slice_lines(
    lines: list[str],
    start_line: int | None,
    end_line: int | None
) -> list[str]:
    """
    Slice lines with end-inclusive convention for markdown-it compatibility.

    Markdown-it's node.map[1] represents the line AFTER the content, so this
    function uses end-exclusive slicing to capture all content lines.

    Args:
        lines: List of all lines in the document
        start_line: Start line number (inclusive, 0-based)
        end_line: End line number (markdown-it convention: first line AFTER content)

    Returns:
        List of lines from start_line to end_line (inclusive of actual content)

    Examples:
        >>> lines = ["a", "b", "c", "d"]
        >>> slice_lines(lines, 1, 3)  # node.map = [1, 3]
        ['b', 'c']  # lines 1, 2 (line 3 is AFTER content)
    """
    if start_line is None or end_line is None:
        return []

    # Bounds checking
    if start_line < 0 or start_line >= len(lines):
        return []
    if end_line <= start_line:
        return []

    # Use end-exclusive slicing since markdown-it's end_line is already +1
    return lines[start_line:end_line]


def slice_lines_raw(
    lines: list[str],
    start_line: int | None,
    end_line: int | None
) -> str:
    """
    Get raw content string from line range using consistent slicing convention.

    Args:
        lines: List of all lines in the document
        start_line: Start line number (inclusive, 0-based)
        end_line: End line number (markdown-it convention: first line AFTER content)

    Returns:
        Joined string content with newlines preserved

    Examples:
        >>> lines = ["first", "second", "third"]
        >>> slice_lines_raw(lines, 0, 2)
        'first\\nsecond'
    """
    sliced = slice_lines(lines, start_line, end_line)
    return "\n".join(sliced)


def build_line_offsets(lines: list[str]) -> tuple[list[int], int]:
    """
    Build array of character offsets for each line start.

    This is useful for converting line numbers to character spans for
    byte-level operations or span tracking.

    Args:
        lines: List of all lines in the document

    Returns:
        Tuple of (line_start_offsets, total_chars_with_lf) where:
        - line_start_offsets: List of character offsets for each line start
        - total_chars_with_lf: Total character count including line feeds

    Examples:
        >>> lines = ["abc", "def", "ghi"]
        >>> offsets, total = build_line_offsets(lines)
        >>> offsets
        [0, 4, 8]  # 'abc\\n' = 4 chars, 'abc\\ndef\\n' = 8 chars
        >>> total
        11  # 'abc\\ndef\\nghi' = 11 chars
    """
    line_start_offsets = [0]
    offset = 0

    # Calculate offsets for all lines except the last
    for line in lines[:-1]:
        offset += len(line) + 1  # +1 for \n
        line_start_offsets.append(offset)

    # Total chars including final line
    if lines:
        total_chars_with_lf = offset + len(lines[-1])
    else:
        total_chars_with_lf = 0

    return line_start_offsets, total_chars_with_lf
