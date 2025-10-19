#!/usr/bin/env python3
"""
Text normalization utilities for markdown parsing.

CRITICAL INVARIANT: Text MUST be normalized BEFORE parsing with markdown-it.

This ensures token.map offsets match line indices in the normalized text.
Normalizing after parsing causes coordinate system mismatches.
"""

from __future__ import annotations
import unicodedata


def normalize_markdown(content: str) -> str:
    """
    Normalize markdown content BEFORE parsing.

    This ensures token.map offsets match line indices.

    CRITICAL: This must happen BEFORE MarkdownIt.parse().

    Normalization Steps:
    1. Unicode NFC normalization (composed form)
       Example: é (e + combining acute) → é (single character)

    2. CRLF → LF normalization
       Ensures consistent line counting across platforms

    Args:
        content: Raw markdown content (may have decomposed unicode, CRLF)

    Returns:
        Normalized content (NFC composed, LF line endings)

    Example:
        >>> content = "# Café\\r\\nParagraph"  # Decomposed é + CRLF
        >>> normalized = normalize_markdown(content)
        >>> "Café" in normalized  # Composed é
        True
        >>> "\\r" in normalized  # No CRLF
        False
    """
    # Step 1: Unicode NFC normalization (composed form)
    # This ensures decomposed characters (e + combining accent)
    # become single composed characters (é)
    # Prevents byte offset mismatches
    normalized = unicodedata.normalize('NFC', content)

    # Step 2: CRLF → LF normalization
    # Windows uses \\r\\n (2 bytes)
    # Unix uses \\n (1 byte)
    # This ensures consistent line counting
    normalized = normalized.replace('\r\n', '\n')

    return normalized


def parse_markdown_normalized(content: str):
    """
    Parse markdown with proper normalization order.

    CRITICAL: Normalizes BEFORE parsing to ensure coordinate integrity.

    Args:
        content: Raw markdown content

    Returns:
        tuple: (tokens, tree, normalized_text)
               All use the same coordinate system.

    Example:
        >>> content = "# Test\\r\\nParagraph"
        >>> tokens, tree, normalized = parse_markdown_normalized(content)
        >>> # tokens[0].map[0] correctly indexes normalized.splitlines()
    """
    from markdown_it import MarkdownIt
    from markdown_it.tree import SyntaxTreeNode

    # 1. Normalize FIRST (CRITICAL ORDER)
    normalized = normalize_markdown(content)

    # 2. Parse normalized text
    md = MarkdownIt("gfm-like")
    md.enable(["table", "strikethrough"])

    tokens = md.parse(normalized)
    tree = SyntaxTreeNode(tokens)

    # 3. Return normalized text (TokenWarehouse will use this)
    return tokens, tree, normalized
