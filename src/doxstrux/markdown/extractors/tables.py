"""Table extractor - Extract GFM tables with structure and validation.

This module extracts table structures from the markdown AST, including:
- Headers with alignment detection
- Body rows with content extraction
- Ragged table detection (security: inconsistent column counts)
- Malformed row detection (rows not following |...| format)
- Pure table validation (strict GFM compliance)
- Raw markdown preservation

Functions:
    extract_tables: Extract all tables with validation metadata
    parse_gfm_table_line: Parse a single GFM table line using polars
"""

from io import StringIO
from typing import Any

import polars as pl


def parse_gfm_table_line(line: str) -> tuple[int, list[str]] | None:
    """Parse a GFM table line into columns.

    A valid GFM table line must:
    - Start with |
    - End with |
    - Be parseable as pipe-separated values

    Args:
        line: A single line from a markdown table

    Returns:
        Tuple of (column_count, cell_values) or None if invalid format
    """
    # Strip blockquote markers
    stripped = line.lstrip()
    while stripped.startswith('>'):
        stripped = stripped[1:].lstrip()
    # Strip list markers
    while stripped.startswith('-') or stripped.startswith('*'):
        stripped = stripped[1:].lstrip()
    stripped = stripped.strip()

    if not stripped:
        return None

    # Must start AND end with | for pure GFM
    if not stripped.startswith('|') or not stripped.endswith('|'):
        return None

    # Extract inner content (between leading and trailing pipes)
    inner = stripped[1:-1]

    if not inner:
        return (0, [])

    # Handle escaped pipes: replace \| with placeholder before parsing
    placeholder = '\x00PIPE\x00'
    inner_escaped = inner.replace('\\|', placeholder)

    try:
        df = pl.read_csv(StringIO(inner_escaped), separator='|', has_header=False)
        # Restore escaped pipes and strip whitespace from cells
        cells = [
            (str(v) if v is not None else '').replace(placeholder, '|').strip()
            for v in df.row(0)
        ]
        return (len(cells), cells)
    except Exception:
        return None


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
                                (grandchild.content or "") for grandchild in (th.children or [])
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
                    actual_end_line = start_line + 2 if start_line is not None else None  # Header + separator
                    for tr in child.children or []:
                        # Workaround for markdown-it bug: it includes lines without pipes
                        # as table rows when there's no blank line after the table.
                        # Check if source line actually contains a pipe character.
                        # This is forward-compatible: once markdown-it is fixed, this
                        # check becomes a no-op since all tr nodes will have valid lines.
                        row_line = tr.map[0] if tr.map else None
                        if row_line is not None and row_line < len(lines):
                            if "|" not in lines[row_line]:
                                # Not a valid table row - stop processing tbody
                                # Fix end_line and raw_content to exclude invalid rows
                                if actual_end_line is not None:
                                    table["end_line"] = actual_end_line
                                    if start_line is not None:
                                        table["raw_content"] = "\n".join(lines[start_line:actual_end_line])
                                break
                            actual_end_line = row_line + 1
                        row = [
                            "".join((grandchild.content or "") for grandchild in (td.children or []))
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

            # SECURITY: Detect ragged and malformed tables using polars-based parsing
            # This gives accurate GFM-compliant column counting that handles:
            # - Escaped pipes (\|)
            # - Proper |...| format validation
            is_ragged = False
            align_mismatch = False
            malformed_lines: list[int] = []
            source_col_counts: list[int] = []

            # Parse source lines with polars for accurate column counting
            if start_line is not None and table["end_line"] is not None:
                for line_idx in range(start_line, table["end_line"]):
                    if line_idx < len(lines):
                        line = lines[line_idx]
                        # Skip separator line (contains only dashes and pipes)
                        if line_idx == start_line + 1:
                            continue
                        result = parse_gfm_table_line(line)
                        if result is not None:
                            col_count, _ = result
                            source_col_counts.append(col_count)
                        elif '|' in line:
                            # Has pipes but doesn't follow |...| format
                            malformed_lines.append(line_idx)

            # Check for ragged: different column counts in valid rows
            if len(source_col_counts) > 1:
                unique_counts = set(source_col_counts)
                if len(unique_counts) > 1:
                    is_ragged = True

            # Check for alignment mismatch
            if table["align"] and cols > 0:
                if len(table["align"]) != cols:
                    align_mismatch = True

            # Determine if table is "pure" GFM (no malformed lines, not ragged)
            is_pure = len(malformed_lines) == 0 and not is_ragged

            table["is_ragged"] = is_ragged
            table["align_mismatch"] = align_mismatch
            table["malformed_lines"] = malformed_lines
            table["is_pure"] = is_pure
            table["table_valid_md"] = is_pure and not align_mismatch
            table["column_count"] = cols
            table["row_count"] = len(table["rows"])
            # Add metadata
            if table["align"]:
                table["align_meta"] = {"heuristic": True}
            if is_ragged:
                table["is_ragged_meta"] = {"source_col_counts": list(set(source_col_counts))}

            ctx.append(table)
            return False  # Don't recurse, we handled the table

        return True

    process_tree_func(tree, table_processor, tables)
    return tables
