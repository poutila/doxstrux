"""Blockquote extractor - Extract blockquotes with nested structure analysis.

This module extracts blockquote elements from the markdown AST, including:
- Blockquote content and line ranges
- Nested structure summaries (lists, tables, code blocks)
- Section attribution for context

Functions:
    extract_blockquotes: Extract all blockquotes with metadata
"""

from typing import Any


def extract_blockquotes(
    tree: Any,
    process_tree_func: Any,
    find_section_id_func: Any,
    get_text_func: Any
) -> list[dict]:
    """Extract all blockquotes from the document.

    Args:
        tree: The markdown AST tree
        process_tree_func: Function to process tree nodes (usually parser.process_tree)
        find_section_id_func: Function to find section ID for a line number
        get_text_func: Function to extract text from a node

    Returns:
        List of blockquote records with content and metadata.

    Note: For richer nested data extraction, existing extractors can be reused
    with line-range filters on the children_blocks ranges.
    """
    blockquotes = []

    def blockquote_processor(node, ctx, level):
        if node.type == "blockquote":
            # Get blockquote content
            content = get_text_func(node)
            # Get line range
            start_line = node.map[0] if node.map else None
            end_line = node.map[1] if node.map else None

            # Summarize nested structures inside this blockquote
            counts = {"lists": 0, "tables": 0, "code": 0}
            for n in node.walk():
                if n.type in ("bullet_list", "ordered_list"):
                    counts["lists"] += 1
                elif n.type == "table":
                    counts["tables"] += 1
                elif n.type in ("fence", "code_block"):
                    counts["code"] += 1

            ctx.append(
                {
                    "content": content,
                    "start_line": start_line,
                    "end_line": end_line,
                    "section_id": find_section_id_func(start_line)
                    if start_line is not None
                    else None,
                    "children_summary": counts,
                    "children_blocks": [
                        {
                            "type": n.type,
                            "start_line": (n.map[0] if getattr(n, "map", None) else None),
                            "end_line": (n.map[1] if getattr(n, "map", None) else None),
                        }
                        for n in node.walk()
                        if n.type
                        in ("bullet_list", "ordered_list", "table", "fence", "code_block")
                    ],
                }
            )

            # Don't recurse into blockquote children to avoid duplication
            return False

        return True  # Continue traversing for other nodes

    process_tree_func(tree, blockquote_processor, blockquotes)
    return blockquotes
