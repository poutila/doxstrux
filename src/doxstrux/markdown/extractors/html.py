"""HTML extractor - Extract HTML blocks and inline HTML for security scanning.

This module extracts HTML elements from markdown, including:
- HTML blocks (full-line HTML tags)
- Inline HTML (tags within paragraphs)
- Tag hints for downstream sanitizers

Functions:
    extract_html: Extract all HTML with security metadata
    extract_html_tag_hints: Extract tag names from HTML content
"""

from typing import Any


def extract_html(
    tree: Any,
    tokens: list[Any],
    config: dict[str, Any],
    process_tree_func: Any,
    find_section_id_func: Any,
    slice_lines_raw_func: Any
) -> dict[str, list[dict]]:
    """Extract both HTML blocks and inline HTML (always, for security scanning).

    RAG Safety: Always extracts HTML but marks with 'allowed' flag based on config.

    Args:
        tree: The markdown AST tree
        tokens: List of markdown-it Token objects
        config: Parser configuration dict
        process_tree_func: Function to process tree nodes
        find_section_id_func: Function to find section ID for a line number
        slice_lines_raw_func: Function to extract raw lines from source

    Returns:
        Dictionary with 'blocks' and 'inline' lists.
        Inline HTML includes <span>, <em>, <strong>, etc. that appear in paragraphs.
    """
    html_blocks = []
    html_inline_dict = {}  # Use dict for deduplication

    # RAG Safety: Check if HTML is allowed by configuration
    html_allowed = config.get("allows_html", False)

    def html_processor(node, ctx, level):
        # Handle HTML blocks
        if node.type == "html_block":
            start_line = node.map[0] if node.map else None
            end_line = node.map[1] if node.map else None
            content = getattr(node, "content", "") or ""

            # Extract raw HTML content from original lines if map available
            raw_content = content
            if start_line is not None and end_line is not None:
                raw_content = slice_lines_raw_func(start_line, end_line)

            ctx["blocks"].append(
                {
                    "content": content,
                    "raw_content": raw_content,
                    "start_line": start_line,
                    "end_line": end_line,
                    "inline": False,  # This is a block element
                    "allowed": ctx["html_allowed"],  # RAG Safety: flag if HTML is allowed
                    "section_id": find_section_id_func(start_line)
                    if start_line is not None
                    else None,
                    "tag_hints": extract_html_tag_hints(content),
                }
            )
            return False  # Don't recurse into HTML content

        # Skip inline HTML during tree traversal - we'll get them from tokens
        return True

    context = {
        "blocks": html_blocks,
        "inline_dict": html_inline_dict,
        "html_allowed": html_allowed,  # Pass allowed flag to processor
    }

    process_tree_func(tree, html_processor, context)

    # Process inline tokens which contain html_inline with proper line info
    for token in tokens:
        if token.type == "inline" and token.children:
            line_num = token.map[0] if token.map else None

            for child in token.children:
                if child.type == "html_inline":
                    content = getattr(child, "content", "") or ""
                    if content.strip():
                        # Create unique key for deduplication
                        key = (content, line_num)
                        html_inline_dict[key] = {
                            "content": content,
                            "line": line_num,
                            "inline": True,
                            "allowed": html_allowed,  # RAG Safety: flag if HTML is allowed
                            "section_id": find_section_id_func(line_num)
                            if line_num is not None
                            else None,
                            "tag_hints": extract_html_tag_hints(content),
                        }

    # Convert dict to list for final output
    html_inline = list(html_inline_dict.values())

    # Return both blocks and inline HTML
    return {"blocks": html_blocks, "inline": html_inline}


def extract_html_tag_hints(html_content: str) -> list[str]:
    """Extract HTML tag names for downstream sanitizer hints.

    Phase 8: Zero-regex implementation using string operations.

    Args:
        html_content: HTML content string

    Returns:
        List of tag names found in the HTML (deduplicated)
    """
    tags = set()
    i = 0
    while i < len(html_content):
        # Find opening <
        start = html_content.find("<", i)
        if start == -1:
            break
        # Skip if it's a closing tag or comment
        if start + 1 < len(html_content) and html_content[start + 1] in "/!":
            i = start + 1
            continue
        # Extract tag name (alphanumeric characters after <)
        tag_start = start + 1
        tag_end = tag_start
        while tag_end < len(html_content) and html_content[tag_end].isalnum():
            tag_end += 1
        if tag_end > tag_start:
            tags.add(html_content[tag_start:tag_end])
        i = tag_end
    return list(tags)
