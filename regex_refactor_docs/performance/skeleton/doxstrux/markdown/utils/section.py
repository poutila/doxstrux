#!/usr/bin/env python3
"""
Section dataclass for markdown document structure.

CRITICAL INVARIANT: Section shape must NEVER change.

This dataclass defines the canonical structure for sections.
All code must use this exact structure to prevent brittle tests and collector errors.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Section:
    """
    Canonical section structure.

    INVARIANT: This shape must NEVER change.
    All code must use this exact structure.

    Fields:
        start_line: Line number where section starts (0-indexed)
        end_line: Line number where section ends (None if section not closed yet)
        token_idx: Index of heading_open token in tokens list
        level: Heading level (1-6 for h1-h6)
        title: Section title text (from inline token content)

    Example:
        >>> section = Section(start_line=5, end_line=10, token_idx=2, level=1, title="Introduction")
        >>> section.to_tuple()
        (5, 10, 2, 1, 'Introduction')
    """
    start_line: int
    end_line: Optional[int]
    token_idx: int
    level: int
    title: str

    def to_tuple(self) -> tuple[int, Optional[int], int, int, str]:
        """
        Convert to legacy tuple format for backward compatibility.

        Returns:
            Tuple: (start_line, end_line, token_idx, level, title)
        """
        return (self.start_line, self.end_line, self.token_idx, self.level, self.title)

    @classmethod
    def from_tuple(cls, t: tuple) -> 'Section':
        """
        Parse legacy tuple format.

        Args:
            t: Tuple in format (start_line, end_line, token_idx, level, title)

        Returns:
            Section instance

        Example:
            >>> section_tuple = (5, 10, 2, 1, "Introduction")
            >>> section = Section.from_tuple(section_tuple)
            >>> section.level
            1
        """
        if len(t) != 5:
            raise ValueError(
                f"Section tuple must have exactly 5 elements, got {len(t)}: {t}"
            )

        start_line, end_line, token_idx, level, title = t
        return cls(
            start_line=start_line,
            end_line=end_line,
            token_idx=token_idx,
            level=level,
            title=title
        )

    def __post_init__(self):
        """Validate section fields."""
        if not isinstance(self.start_line, int) or self.start_line < 0:
            raise ValueError(f"start_line must be non-negative int, got {self.start_line}")

        if self.end_line is not None:
            if not isinstance(self.end_line, int) or self.end_line < 0:
                raise ValueError(f"end_line must be non-negative int or None, got {self.end_line}")
            if self.end_line < self.start_line:
                raise ValueError(
                    f"end_line ({self.end_line}) must be >= start_line ({self.start_line})"
                )

        if not isinstance(self.token_idx, int) or self.token_idx < 0:
            raise ValueError(f"token_idx must be non-negative int, got {self.token_idx}")

        if not isinstance(self.level, int) or not (1 <= self.level <= 6):
            raise ValueError(f"level must be 1-6, got {self.level}")

        if not isinstance(self.title, str):
            raise ValueError(f"title must be str, got {type(self.title)}")
