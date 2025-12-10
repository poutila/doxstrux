"""Section and heading extractors - Document structure with hierarchy.

This module extracts sections and headings from the markdown AST, including:
- Sections defined by headings with content ranges
- Heading hierarchy with parent relationships
- Stable slug-based IDs for linking

Functions:
    extract_sections: Extract document sections with preserved content
    extract_headings: Extract all headings with hierarchy
    slugify_base: Convert text to base slug format
"""

import unicodedata
from typing import Any


def extract_sections(
    tree: Any,
    lines: list[str],
    process_tree_func: Any,
    heading_level_func: Any,
    get_text_func: Any,
    slice_lines_raw_func: Any,
    plain_text_in_range_func: Any,
    span_from_lines_func: Any,
    cache: dict[str, Any] | None = None
) -> list[dict]:
    """Extract document sections with preserved content.

    Sections are defined by headings and contain all content
    until the next heading of equal or higher level.

    Args:
        tree: The markdown AST tree
        lines: List of source lines
        process_tree_func: Function to process tree nodes
        heading_level_func: Function to get heading level from node
        get_text_func: Function to extract text from node
        slice_lines_raw_func: Function to slice raw lines
        plain_text_in_range_func: Function to get plain text in range
        span_from_lines_func: Function to get character spans
        cache: Optional cache dict

    Returns:
        List of section dicts with hierarchy and content
    """
    # Return cached result if available
    if cache and cache.get("sections") is not None:
        return cache["sections"]

    sections = []
    section_stack = []  # Track hierarchy
    slug_counts = {}  # Track slug usage for stable IDs

    def section_processor(node, ctx, level):
        if node.type == "heading":
            # Extract heading info
            heading_level = heading_level_func(node)
            heading_text = get_text_func(node)
            base_slug = slugify_base(heading_text)

            # Generate stable ID with running count
            if base_slug in slug_counts:
                slug_counts[base_slug] += 1
                stable_slug = f"{base_slug}-{slug_counts[base_slug]}"
            else:
                slug_counts[base_slug] = 1
                stable_slug = base_slug

            stable_id = f"section_{stable_slug}"

            # Create new section
            start_line = node.map[0] if node.map else None
            start_char, _ = (
                span_from_lines_func(start_line, start_line)
                if start_line is not None
                else (None, None)
            )

            section = {
                "id": stable_id,
                "level": heading_level,
                "title": heading_text,
                "slug": stable_slug,
                "start_line": start_line,
                "end_line": None,  # Set when next section starts
                "start_char": start_char,
                "end_char": None,  # Set when section content is finalized
                "parent_id": None,
                "child_ids": [],
            }

            # Set end line of previous section at same or higher level
            while ctx["stack"] and ctx["stack"][-1]["level"] >= heading_level:
                prev = ctx["stack"].pop()
                if prev["end_line"] is None:
                    prev["end_line"] = section["start_line"] - 1

            # Set parent relationship
            if ctx["stack"]:
                parent = ctx["stack"][-1]
                section["parent_id"] = parent["id"]
                parent["child_ids"].append(section["id"])

            # Add to stack and results
            ctx["stack"].append(section)
            ctx["sections"].append(section)

        return True  # Always continue traversing

    context = {"sections": [], "stack": []}
    process_tree_func(tree, section_processor, context)

    # Set end lines for remaining sections
    for section in context["stack"]:
        if section["end_line"] is None:
            section["end_line"] = len(lines) - 1

    # Fill in section content from original lines
    for section in context["sections"]:
        if section["start_line"] is not None and section["end_line"] is not None:
            start = section["start_line"]
            end = section["end_line"] + 1
            # Use centralized slicing utility for consistency
            section["raw_content"] = slice_lines_raw_func(start, end)
            section["text_content"] = plain_text_in_range_func(start, end - 1)
            # Update end_char for completed section
            _, section["end_char"] = span_from_lines_func(
                section["start_line"], section["end_line"]
            )
        else:
            section["raw_content"] = ""
            section["text_content"] = ""

    # Cache the result
    if cache is not None:
        cache["sections"] = context["sections"]

    return context["sections"]


def extract_headings(
    tree: Any,
    tokens: list[Any],
    process_tree_func: Any,
    heading_level_func: Any,
    get_text_func: Any,
    span_from_lines_func: Any
) -> list[dict]:
    """Extract all headings with hierarchy using stable slug-based IDs.

    SECURITY: Only extracts top-level headings (not nested in lists/blockquotes)
    to prevent heading creepage vulnerabilities.

    Args:
        tree: The markdown AST tree
        tokens: List of markdown-it Token objects
        process_tree_func: Function to process tree nodes
        heading_level_func: Function to get heading level from node
        get_text_func: Function to extract text from node
        span_from_lines_func: Function to get character spans

    Returns:
        List of heading dicts with hierarchy
    """
    headings = []
    heading_stack = []
    slug_counts = {}  # Track slug usage for stable IDs

    # First pass: collect heading tokens at document level (level=0)
    # This prevents heading creepage from list continuations
    heading_tokens = []
    for token in tokens:
        if token.type == "heading_open" and token.level == 0:
            # This is a document-level heading, not nested
            heading_tokens.append(token)

    def heading_processor(node, ctx, level):
        if node.type == "heading":
            # SECURITY: Check if this heading corresponds to a document-level token
            # by verifying its line mapping matches a level=0 heading token
            is_document_level = False
            if node.map:
                for h_token in heading_tokens:
                    if h_token.map and h_token.map[0] == node.map[0]:
                        is_document_level = True
                        break

            if not is_document_level:
                # Skip nested headings (security: prevent creepage)
                return False

            heading_level = heading_level_func(node)
            heading_text = get_text_func(node)
            base_slug = slugify_base(heading_text)

            # Generate stable ID with running count
            if base_slug in slug_counts:
                slug_counts[base_slug] += 1
                stable_slug = f"{base_slug}-{slug_counts[base_slug]}"
            else:
                slug_counts[base_slug] = 1
                stable_slug = base_slug

            stable_id = f"heading_{stable_slug}"

            # Find parent heading
            parent_id = None
            while heading_stack and heading_stack[-1]["level"] >= heading_level:
                heading_stack.pop()
            if heading_stack:
                parent_id = heading_stack[-1]["id"]

            # Add character offsets for RAG chunking
            line_num = node.map[0] if node.map else None
            start_char, end_char = (
                span_from_lines_func(line_num, line_num)
                if line_num is not None
                else (None, None)
            )

            heading = {
                "id": stable_id,
                "level": heading_level,
                "text": heading_text,
                "line": line_num,
                "slug": stable_slug,
                "parent_heading_id": parent_id,
                "start_char": start_char,
                "end_char": end_char,
            }

            ctx.append(heading)
            heading_stack.append(heading)

        return True

    process_tree_func(tree, heading_processor, headings)
    return headings


def slugify_base(text: str) -> str:
    """Convert text to base slug format without de-duplication for stable IDs.

    Phase 8: Zero-regex implementation using string operations.

    Args:
        text: Text to slugify

    Returns:
        Slugified text or "untitled" if empty
    """
    s = unicodedata.normalize("NFKD", text).lower()

    # Replace whitespace and slashes with hyphens
    result = []
    prev_hyphen = False
    for char in s:
        if char.isspace() or char == "/":
            if not prev_hyphen:  # Collapse consecutive
                result.append("-")
                prev_hyphen = True
        elif char.isalnum() or char == "_":
            result.append(char)
            prev_hyphen = False
        elif char == "-":
            if not prev_hyphen:  # Collapse consecutive
                result.append("-")
                prev_hyphen = True
        # Skip other characters

    slug = "".join(result).strip("-")
    return slug or "untitled"  # Fallback for empty slugs
