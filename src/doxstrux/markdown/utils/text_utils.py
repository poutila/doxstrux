"""Text extraction utilities for markdown-it tokens.

This module provides functions for extracting text content from markdown-it
token trees, handling inline formatting, and checking token structure.

Functions:
    collect_text_segments: Collect text segments from token stream with line ranges
    extract_text_from_inline: Extract plain text from inline token children
    has_child_type: Check if token has children of specified type(s)
"""

from typing import Any


def collect_text_segments(tokens: list[Any]) -> list[tuple[int, int, str]]:
    """
    Collect text-ish segments with proper line ranges for paragraph boundary detection.

    Processes inline tokens which contain the actual text content, extracting
    text from children and tracking line breaks.

    Args:
        tokens: List of markdown-it Token objects

    Returns:
        List of tuples (start_line, end_line, text) where:
        - start_line: Starting line number (0-based, inclusive)
        - end_line: Ending line number (0-based, inclusive)
        - text: Extracted text content

    Examples:
        >>> # With tokens containing "Hello\\nworld"
        >>> segments = collect_text_segments(tokens)
        >>> segments[0]
        (0, 1, 'Hello\\nworld')
    """
    segs = []

    # Process inline tokens which contain the actual text content
    for token in tokens:
        if token.type == "inline" and token.children and token.map:
            # The token.map gives the range of the containing block (e.g., paragraph)
            start_line = token.map[0]
            end_line = token.map[1] - 1 if token.map[1] else start_line  # Convert to inclusive

            # Extract text from inline children and track line breaks
            text_parts = []
            current_line_offset = 0

            for child in token.children:
                if child.type == "text":
                    content = getattr(child, "content", "") or ""
                    if content:
                        text_parts.append(content)
                        # Count explicit newlines in text content
                        current_line_offset += content.count("\n")
                elif child.type == "code_inline":
                    content = getattr(child, "content", "") or ""
                    if content:
                        text_parts.append(content)
                elif child.type in ("softbreak", "hardbreak"):
                    text_parts.append("\n")
                    current_line_offset += 1

            # If we collected any text, add it as a segment with proper range
            if text_parts:
                full_text = "".join(text_parts)
                # Widen the range based on actual line breaks found
                actual_end_line = min(start_line + current_line_offset, end_line)
                segs.append((start_line, actual_end_line, full_text))

    return segs


def extract_text_from_inline(inline_token: Any) -> str:
    """
    Extract plain text from inline token children.

    Recursively extracts text content from inline tokens, handling nested
    formatting like bold, italic, links, etc.

    Args:
        inline_token: markdown-it inline Token object with children

    Returns:
        Concatenated plain text content from all text nodes

    Examples:
        >>> # Token with children: [text("Hello "), strong_open, text("world"), strong_close]
        >>> extract_text_from_inline(token)
        'Hello world'
    """
    if not hasattr(inline_token, "children") or not inline_token.children:
        return ""

    text_parts = []
    for child in inline_token.children:
        if child.type == "text":
            content = getattr(child, "content", "") or ""
            text_parts.append(content)
        elif child.type == "code_inline":
            content = getattr(child, "content", "") or ""
            text_parts.append(content)
        elif child.type in ("softbreak", "hardbreak"):
            text_parts.append("\n")
        elif hasattr(child, "children") and child.children:
            # Recursively extract from nested children
            text_parts.append(extract_text_from_inline(child))

    return "".join(text_parts)


def has_child_type(node: Any, types: str | list[str]) -> bool:
    """
    Check if node has children of specified type(s).

    Walks the entire subtree of the node to find children matching
    the specified type(s).

    Args:
        node: markdown-it SyntaxTreeNode or Token with walk() method
        types: Single type string or list of type strings to search for

    Returns:
        True if any child has a matching type, False otherwise

    Examples:
        >>> has_child_type(node, "code_block")
        True
        >>> has_child_type(node, ["image", "link"])
        False
    """
    if isinstance(types, str):
        types = [types]

    for child in node.walk():
        if child.type in types:
            return True
    return False
