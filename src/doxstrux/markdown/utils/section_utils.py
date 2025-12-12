"""Section lookup utilities - O(log N) line-to-section mapping.

Phase 8 (THREE_ADDITIONS.md) - Section Lookup Helper.

This module provides efficient lookup of which section contains a given line number.
Uses binary search for O(log N) lookup performance.

Invariants (from THREE_ADDITIONS.md):
- INV-2.1: section_of_line returns section where start_line <= line <= end_line
- INV-2.2: Boundary lines (start_line, end_line) are included in section
- INV-2.3: Lines in gaps between sections return None
- INV-2.4: Negative lines and empty sections return None
- INV-2.5: Single-line sections (start == end) correctly identified
- INV-2.6: SectionIndex builds index once per instance (amortized)

Preconditions (enforced by TestParserSectionInvariants):
- Sections are sorted by start_line (ascending)
- Sections have start_line and end_line fields (0-indexed)
- Sections are non-overlapping

Functions:
    section_of_line: Single lookup (convenience wrapper)

Classes:
    SectionIndex: Efficient repeated lookups with pre-built index
"""

from bisect import bisect_right
from typing import Any


def section_of_line(sections: list[dict[str, Any]], line: int) -> dict[str, Any] | None:
    """Find which section contains the given line number.

    Convenience wrapper for single lookups. For repeated lookups,
    use SectionIndex instead for better performance.

    Args:
        sections: List of section dicts with start_line and end_line fields.
                  Must be sorted by start_line (ascending).
        line: 0-indexed line number to look up.

    Returns:
        The section dict containing the line, or None if:
        - line is negative
        - sections list is empty
        - line falls in a gap between sections
        - line is beyond all sections

    Examples:
        >>> sections = [
        ...     {"id": "intro", "start_line": 0, "end_line": 5},
        ...     {"id": "main", "start_line": 6, "end_line": 15},
        ... ]
        >>> section_of_line(sections, 3)
        {'id': 'intro', 'start_line': 0, 'end_line': 5}
        >>> section_of_line(sections, 100)
        None
    """
    # INV-2.4: Negative line numbers return None
    if line < 0:
        return None

    # INV-2.4: Empty sections list returns None
    if not sections:
        return None

    # Linear search for simplicity (use SectionIndex for repeated lookups)
    for section in sections:
        start = section.get("start_line")
        end = section.get("end_line")

        # Skip sections with missing line info
        if start is None:
            continue

        # Handle sections with no end_line (extends to infinity)
        if end is None:
            if line >= start:
                return section
            continue

        # INV-2.1, INV-2.2: Check if line is within [start_line, end_line]
        if start <= line <= end:
            return section

    # INV-2.3: Line in gap or beyond all sections
    return None


class SectionIndex:
    """Efficient section lookup with pre-built index.

    Builds an internal index for O(log N) lookups via binary search.
    The index is built once per instance (eager, in __init__).

    INV-2.6: Index is built at most once per instance.

    Args:
        sections: List of section dicts with start_line and end_line fields.
                  Must be sorted by start_line (ascending).

    Example:
        >>> sections = [
        ...     {"id": "intro", "start_line": 0, "end_line": 5},
        ...     {"id": "main", "start_line": 6, "end_line": 15},
        ... ]
        >>> index = SectionIndex(sections)
        >>> index.get(3)
        {'id': 'intro', 'start_line': 0, 'end_line': 5}
        >>> index.get(100)
        None
    """

    def __init__(self, sections: list[dict[str, Any]]) -> None:
        """Initialize index from sections list.

        Builds the lookup index eagerly for consistent performance.
        """
        self._sections = sections
        self._build_count = 0
        self._start_lines: list[int] = []
        self._section_map: list[dict[str, Any]] = []

        self._build_index()

    def _build_index(self) -> None:
        """Build the binary search index.

        Internal method - builds sorted list of start lines for binary search.
        """
        self._build_count += 1

        if not self._sections:
            return

        # Build parallel arrays for binary search
        # _start_lines[i] is the start_line of _section_map[i]
        for section in self._sections:
            start = section.get("start_line")
            if start is not None:
                self._start_lines.append(start)
                self._section_map.append(section)

    def get(self, line: int) -> dict[str, Any] | None:
        """Look up which section contains the given line.

        Uses binary search for O(log N) performance.

        Args:
            line: 0-indexed line number to look up.

        Returns:
            The section dict containing the line, or None if not found.
        """
        # INV-2.4: Negative line numbers return None
        if line < 0:
            return None

        # INV-2.4: Empty index returns None
        if not self._start_lines:
            return None

        # Binary search: find rightmost section with start_line <= line
        # bisect_right gives insertion point, so we need idx - 1
        idx = bisect_right(self._start_lines, line)

        if idx == 0:
            # Line is before all sections
            return None

        # Check the candidate section (the one just before insertion point)
        candidate = self._section_map[idx - 1]
        start = candidate.get("start_line")
        end = candidate.get("end_line")

        # INV-2.2: Verify line is within [start_line, end_line]
        if start is not None:
            if end is None:
                # Section extends to infinity
                if line >= start:
                    return candidate
            elif start <= line <= end:
                return candidate

        # INV-2.3: Line is in gap (after candidate's end, before next start)
        return None

    def __len__(self) -> int:
        """Return number of indexed sections."""
        return len(self._section_map)
