"""Code block extractor - Extract fenced and indented code blocks.

This module extracts code blocks from the markdown AST, including:
- Fenced code blocks (``` or ~~~) with language detection
- Indented code blocks (4 spaces or tab)
- Content extraction with line ranges
- Security: Skips code blocks nested in table cells

Functions:
    extract_code_blocks: Extract all code blocks with caching
"""

from typing import Any


def extract_code_blocks(
    tree: Any,
    lines: list[str],
    process_tree_func: Any,
    find_section_id_func: Any,
    slice_lines_inclusive_func: Any,
    cache: dict[str, Any]
) -> list[dict]:
    """Extract all code blocks (fenced and indented).

    Note: Fences inside table cells won't be parsed as fence nodes by markdown-it.
    They'll appear as text and may be caught by the indented code scanner below.
    This is expected behavior - markdown-it doesn't nest blocks in table cells.

    Args:
        tree: The markdown AST tree
        lines: List of source lines
        process_tree_func: Function to process tree nodes
        find_section_id_func: Function to find section ID for a line number
        slice_lines_inclusive_func: Function to slice lines inclusively
        cache: Cache dict for storing results

    Returns:
        List of code block dicts with metadata
    """
    # Return cached result if available
    if cache["code_blocks"] is not None:
        return cache["code_blocks"]

    blocks = []

    def code_processor(node, ctx, level):
        # Skip fence/code nodes that are inside table cells (defensive)
        # markdown-it shouldn't create these, but be safe
        parent = getattr(node, "parent", None)
        while parent:
            if getattr(parent, "type", "") in ("td", "th"):
                return True  # Skip this node, it's in a table cell
            parent = getattr(parent, "parent", None)

        if node.type == "fence":
            block = {
                "id": f"code_{len(ctx)}",
                "type": "fenced",
                "language": node.info if hasattr(node, "info") else "",
                "content": node.content if hasattr(node, "content") else "",
                "start_line": node.map[0] if node.map else None,
                "end_line": node.map[1] if node.map else None,
                "section_id": find_section_id_func(node.map[0] if node.map else 0),
            }
            ctx.append(block)
            return False
        if node.type == "code_block":
            block = {
                "id": f"code_{len(ctx)}",
                "type": "indented",
                "language": "",
                "content": node.content if hasattr(node, "content") else "",
                "start_line": node.map[0] if node.map else None,
                "end_line": node.map[1] if node.map else None,
                "section_id": find_section_id_func(node.map[0] if node.map else 0),
            }
            ctx.append(block)
            return False

        return True

    process_tree_func(tree, code_processor, blocks)

    # Also extract indented code blocks that markdown-it might miss
    covered = set()
    for b in blocks:
        if b.get("start_line") is not None and b.get("end_line") is not None:
            covered.update(range(b["start_line"], b["end_line"] + 1))

    i, N = 0, len(lines)
    while i < N:
        line = lines[i]
        if (line.startswith("    ") or line.startswith("\t")) and i not in covered:
            start = i
            i += 1
            while i < N:
                nxt = lines[i]
                if not nxt.strip() or nxt.startswith("    ") or nxt.startswith("\t"):
                    i += 1
                else:
                    break
            end = i - 1
            # Extract and process indented content using centralized slicing
            raw_lines = slice_lines_inclusive_func(start, end + 1)
            content = "\n".join(l[4:] if l.startswith("    ") else l[1:] for l in raw_lines)
            blocks.append(
                {
                    "id": f"code_{len(blocks)}",
                    "type": "indented",
                    "language": "",
                    "content": content,
                    "start_line": start,
                    "end_line": end,
                    "section_id": find_section_id_func(start),
                }
            )
            covered.update(range(start, end + 1))
        else:
            i += 1

    # Cache the result
    cache["code_blocks"] = blocks
    return blocks
