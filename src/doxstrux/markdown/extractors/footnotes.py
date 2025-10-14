"""Footnote extractor - Definitions and references with rich metadata.

This module extracts footnote elements from the markdown AST, including:
- Footnote definitions with content and metadata
- Footnote references (inline citations)
- Nested structures within footnotes

Functions:
    extract_footnotes: Extract all footnote definitions and references
"""

from typing import Any


def extract_footnotes(
    tree: Any,
    process_tree_func: Any,
    find_section_id_func: Any,
    get_text_func: Any
) -> dict[str, Any]:
    """Extract footnote definitions and back-references with rich metadata.

    Args:
        tree: The markdown AST tree
        process_tree_func: Function to process tree nodes (usually parser.process_tree)
        find_section_id_func: Function to find section ID for a line number
        get_text_func: Function to extract text from a node

    Returns:
        Dictionary with 'definitions' and 'references' lists.
        Definitions are deduplicated by label (last-writer-wins).
        Both label and numeric ID are extracted for stability.
    """
    # Use dict for deduplication of definitions
    definitions_dict = {}
    references = []

    def get_footnote_ids(node):
        """Extract both label (stable) and numeric id from footnote node.
        Prefer label for stability, but include both."""
        label = None
        numeric_id = None

        if hasattr(node, "token") and node.token:
            meta = getattr(node.token, "meta", {})
            label = meta.get("label", "")
            numeric_id = meta.get("id", "")

        if not label and hasattr(node, "meta"):
            meta = getattr(node, "meta", {})
            label = meta.get("label", "")
            if not numeric_id:
                numeric_id = meta.get("id", "")

        # Use label as primary key, fallback to numeric id
        key = label if label else numeric_id
        return key, label, numeric_id

    def footnote_processor(node, ctx, level):
        # Handle footnote references (inline)
        if node.type == "footnote_ref":
            key, label, numeric_id = get_footnote_ids(node)
            line_num = node.map[0] if node.map else None

            ctx["references"].append(
                {
                    "label": label if label else key,  # Prefer label
                    "id": numeric_id if numeric_id else key,  # Include numeric id
                    "line": line_num,
                    "section_id": find_section_id_func(line_num)
                    if line_num is not None
                    else None,
                }
            )

        # Handle footnote definitions
        elif node.type == "footnote":
            key, label, numeric_id = get_footnote_ids(node)

            # Skip if no identifier found
            if not key:
                return True

            start_line = node.map[0] if node.map else None
            end_line = node.map[1] if node.map else None
            # Get text from the footnote content (recursively)
            content = get_text_func(node)

            # Collect nested structures for richer analysis
            nested_structures = []
            for child in node.walk():
                if child.type in (
                    "bullet_list",
                    "ordered_list",
                    "table",
                    "fence",
                    "code_block",
                ):
                    if hasattr(child, "map") and child.map:
                        nested_structures.append(
                            {
                                "type": child.type,
                                "start_line": child.map[0],
                                "end_line": child.map[1],
                            }
                        )

            # Use dict for deduplication (last-writer-wins)
            ctx["definitions_dict"][key] = {
                "label": label if label else key,  # Stable identifier
                "id": numeric_id if numeric_id else key,  # Numeric identifier
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "byte_length": len(content.encode("utf-8")) if content else 0,
                "nested_structures": nested_structures,
                "section_id": find_section_id_func(start_line)
                if start_line is not None
                else None,
            }

        return True  # Continue traversing

    context = {"definitions_dict": definitions_dict, "references": references}

    process_tree_func(tree, footnote_processor, context)

    # Convert definitions dict to list
    return {
        "definitions": list(context["definitions_dict"].values()),
        "references": context["references"],
    }
