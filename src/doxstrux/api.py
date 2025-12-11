"""Public API for doxstrux markdown parsing.

This module provides the main entry point for parsing markdown files.
Users should use parse_markdown_file() instead of MarkdownParserCore directly.
"""

from pathlib import Path
from typing import Any

from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.utils.encoding import read_file_robust


def parse_markdown_file(
    path: Path | str,
    *,
    config: dict[str, Any] | None = None,
    security_profile: str = "moderate",
) -> dict[str, Any]:
    """Parse a markdown file with automatic encoding detection.

    This is the main entry point for parsing markdown files. It handles:
    - Robust encoding detection (BOM, charset-normalizer, fallbacks)
    - Security validation based on profile
    - Full structure extraction

    Args:
        path: Path to the markdown file
        config: Optional parser configuration dict with keys:
            - 'plugins': list of markdown-it plugins to enable
            - 'allows_html': bool, whether HTML blocks are allowed
            - 'preset': str, markdown-it preset ('commonmark', 'gfm', etc.)
        security_profile: Security profile ('strict', 'moderate', 'permissive')
            - strict: 100KB max, limited plugins, tighter validation
            - moderate: 1MB max, standard plugins (default)
            - permissive: 10MB max, all plugins

    Returns:
        Parsed result dict containing:
            - metadata: Document metadata including encoding info
            - content: Raw content and lines
            - structure: Extracted markdown structures
            - mappings: Line-to-type mappings for code/prose classification

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
        MarkdownSecurityError: If content violates security limits
        MarkdownSizeError: If content exceeds size limits

    Example:
        >>> from doxstrux import parse_markdown_file
        >>> result = parse_markdown_file("README.md")
        >>> print(result["metadata"]["encoding"])
        {'detected': 'utf-8', 'confidence': 0.99}
    """
    # Read file with robust encoding detection
    file_result = read_file_robust(path)

    # Parse content
    parser = MarkdownParserCore(
        file_result.text,
        config=config,
        security_profile=security_profile,
    )
    result = parser.parse()

    # Add encoding metadata
    result["metadata"]["encoding"] = {
        "detected": file_result.encoding,
        "confidence": file_result.confidence,
    }

    # Add source file path
    result["metadata"]["source_path"] = str(path)

    return result
