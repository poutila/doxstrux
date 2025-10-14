"""Math extractor - Extract mathematical expressions from markdown AST.

This module extracts math elements from the markdown AST, including:
- Inline math: $E = mc^2$ (via texmath plugin)
- Display math: $$...$$  (via texmath plugin)
- Fenced math blocks: ```math ... ``` (standard fence with math info string)

The texmath plugin must be enabled in the parser for inline/display math detection.

Functions:
    extract_math: Extract all math expressions with metadata
"""

from typing import Any


def extract_math(
    tokens: list[Any],
) -> dict[str, list[dict]]:
    """Extract all math expressions from tokens.

    Returns both block-level and inline math expressions with line attribution.

    Args:
        tokens: Token list from markdown-it parser (must have texmath plugin enabled)

    Returns:
        Dictionary with 'blocks' and 'inline' lists:
        {
            'blocks': [
                {
                    'id': 'math_block_0',
                    'kind': 'display' | 'fenced',  # $$...$$ or ```math
                    'content': 'a^2 + b^2 = c^2',
                    'start_line': 10,
                    'end_line': 12
                }
            ],
            'inline': [
                {
                    'id': 'math_inline_0',
                    'content': 'E = mc^2',
                    'line': 5
                }
            ]
        }

    Examples:
        >>> tokens = parser.tokens  # Parser with texmath_plugin enabled
        >>> math_data = extract_math(tokens)
        >>> math_data['blocks'][0]['content']
        '\\int_0^1 x^2\\,dx = \\tfrac{1}{3}'
    """
    blocks = []
    inline = []

    for tok in tokens:
        # Block-level display math: $$...$$
        if tok.type == "math_block":
            start_line, end_line = tok.map if tok.map else (None, None)
            blocks.append({
                "id": f"math_block_{len(blocks)}",
                "kind": "display",
                "content": tok.content.strip(),
                "start_line": start_line,
                "end_line": end_line
            })

        # Fenced code blocks with math info string: ```math ... ```
        elif tok.type == "fence" and tok.info and tok.info.strip() == "math":
            start_line, end_line = tok.map if tok.map else (None, None)
            blocks.append({
                "id": f"math_block_{len(blocks)}",
                "kind": "fenced",
                "content": tok.content.strip(),
                "start_line": start_line,
                "end_line": end_line
            })

        # Inline math: $...$
        # Look inside inline token children (texmath plugin injects math_inline tokens)
        if tok.children:
            for child in tok.children:
                if child.type == "math_inline":
                    line = tok.map[0] if tok.map else None
                    inline.append({
                        "id": f"math_inline_{len(inline)}",
                        "content": child.content,
                        "line": line
                    })

    return {
        "blocks": blocks,
        "inline": inline
    }
