"""Paragraph extractor - Extract paragraphs with metadata.

This module extracts paragraph elements from the markdown AST, including:
- Paragraph text content
- Line ranges
- Word counts
- Presence of links, emphasis, and inline code

Functions:
    extract_paragraphs: Extract all paragraphs with metadata
"""

from typing import Any


def extract_paragraphs(
    tree: Any,
    process_tree_func: Any,
    get_text_func: Any,
    find_section_id_func: Any,
    has_child_type_func: Any
) -> list[dict]:
    """Extract all paragraphs with metadata.

    Args:
        tree: The markdown AST tree
        process_tree_func: Function to process tree nodes
        get_text_func: Function to extract text from node
        find_section_id_func: Function to find section ID for a line number
        has_child_type_func: Function to check if node has child of type

    Returns:
        List of paragraph dicts with metadata
    """
    paragraphs = []

    def paragraph_processor(node, ctx, level):
        if node.type == "paragraph":
            # Skip if inside a list or blockquote (they handle their own paragraphs)
            parent = getattr(node, "parent", None)
            while parent:
                if parent.type in ["list_item", "blockquote"]:
                    return False
                parent = getattr(parent, "parent", None)

            para = {
                "id": f"para_{len(ctx)}",
                "text": get_text_func(node),
                "start_line": node.map[0] if node.map else None,
                "end_line": node.map[1] if node.map else None,
                "section_id": find_section_id_func(node.map[0] if node.map else 0),
                "word_count": len(get_text_func(node).split()),
                "has_links": has_child_type_func(node, "link"),
                "has_emphasis": has_child_type_func(node, ["em", "strong"]),
                "has_code": has_child_type_func(node, "code_inline"),
            }
            ctx.append(para)
            return False  # Don't recurse, we extracted everything

        return True

    process_tree_func(tree, paragraph_processor, paragraphs)
    return paragraphs
