"""Table extractor - Extract GFM tables with structure and validation.

This module extracts table structures from the markdown AST, including:
- Headers with alignment detection
- Body rows with content extraction
- Ragged table detection (security: inconsistent column counts)
- Alignment mismatch detection (column count vs alignment spec)
- Raw markdown preservation

Functions:
    extract_tables: Extract all tables with validation metadata
"""

from typing import Any


def extract_tables(
    tree: Any,
    lines: list[str],
    process_tree_func: Any,
    find_section_id_func: Any
) -> list[dict]:
    """Extract all tables with structure preserved and security validation.

    Args:
        tree: The markdown AST tree
        lines: List of source lines
        process_tree_func: Function to process tree nodes
        find_section_id_func: Function to find section ID for a line number

    Returns:
        List of table dicts with headers, rows, alignment, and validation metadata
    """
    tables = []

    def table_processor(node, ctx, level):
        if node.type == "table":
            start_line = node.map[0] if node.map else None
            end_line = node.map[1] if node.map else None

            # Extract raw table content (preserve original markdown)
            raw_content = ""
            if start_line is not None and end_line is not None:
                raw_content = "\n".join(lines[start_line:end_line])

            table = {
                "id": f"table_{len(ctx)}",
                "raw_content": raw_content,  # Original markdown table (unchanged)
                "headers": [],  # Parsed headers (polished)
                "rows": [],     # Parsed rows (polished)
                "align": None,  # Parsed alignment (polished)
                "start_line": start_line,
                "end_line": end_line,
                "section_id": find_section_id_func(start_line if start_line is not None else 0),
            }

            # Extract headers, rows, and alignment (Phase 5: token-based, zero regex)
            for child in node.children or []:
                if child.type == "thead":
                    for tr in child.children or []:
                        # Extract header text and alignment from th nodes
                        headers = []
                        aligns = []
                        for th in tr.children or []:
                            # Header text from inline children
                            header_text = "".join(
                                grandchild.content for grandchild in (th.children or [])
                            )
                            headers.append(header_text)

                            # Alignment from th.attrs (markdown-it provides this)
                            align = "left"  # default
                            if hasattr(th, 'attrs') and th.attrs:
                                style = th.attrs.get('style', '')
                                if 'text-align:center' in style:
                                    align = "center"
                                elif 'text-align:right' in style:
                                    align = "right"
                                elif 'text-align:left' in style:
                                    align = "left"
                            aligns.append(align)

                        table["headers"] = headers
                        table["align"] = aligns
                elif child.type == "tbody":
                    for tr in child.children or []:
                        row = [
                            "".join(grandchild.content for grandchild in (td.children or []))
                            for td in tr.children or []
                        ]
                        if row:
                            table["rows"].append(row)
            # Normalize align to column count (defensive against escaped pipe miscounts)
            # Safety guard: if header count is zero but there are body rows, use max row width
            header_cols = len(table["headers"])
            body_max_cols = (
                max((len(r) for r in table["rows"]), default=0) if table["rows"] else 0
            )
            cols = max(header_cols, body_max_cols)

            # Guard against degenerate zero-column tables
            if cols == 0:
                table["align"] = []
                table["is_ragged"] = False  # Empty table is not ragged
                ctx.append(table)
                return False
            if table["align"]:
                if len(table["align"]) < cols:
                    # Extend with 'left' for missing columns
                    table["align"] += ["left"] * (cols - len(table["align"]))
                elif len(table["align"]) > cols:
                    # Truncate if we have too many (likely from escaped pipe miscount)
                    table["align"] = table["align"][:cols]
            else:
                # Fallback: all left-aligned if alignment detection completely failed
                table["align"] = ["left"] * cols

            # SECURITY: Detect ragged tables and alignment mismatches
            # Token-based detection first (more accurate)
            is_ragged = False
            align_mismatch = False

            # Check for ragged rows using tokenized data
            # Markdown-it fills missing cells with empty strings, so we check for that
            if table["rows"]:
                for row in table["rows"]:
                    if len(row) != cols:
                        is_ragged = True
                        break
                    # Check for trailing empty cells which likely indicate missing cells in source
                    # A row like "| 1 |" becomes ["1", ""] for a 2-column table
                    if cols > 1 and row[-1] == "" and any(cell != "" for cell in row):
                        # Has trailing empty and at least one non-empty cell
                        is_ragged = True
                        break

            # Check for alignment mismatch
            if table["align"] and cols > 0:
                if len(table["align"]) != cols:
                    align_mismatch = True

            table["is_ragged"] = is_ragged
            table["align_mismatch"] = align_mismatch
            table["table_valid_md"] = not is_ragged and not align_mismatch
            table["column_count"] = cols
            table["row_count"] = len(table["rows"])
            # Add heuristic metadata for alignment and ragged detection
            if table["align"]:
                table["align_meta"] = {"heuristic": True}
            if is_ragged:
                table["is_ragged_meta"] = {"heuristic": True}

            ctx.append(table)
            return False  # Don't recurse, we handled the table

        return True

    process_tree_func(tree, table_processor, tables)
    return tables
