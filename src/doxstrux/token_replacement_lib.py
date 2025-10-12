"""Token utility functions for traversing and extracting data from markdown-it token streams.

This module provides helpers for working with markdown-it-py tokens during the
zero-regex refactoring project. These utilities enable token-based parsing without
recursion depth issues.

Functions:
    walk_tokens_iter: Iterative DFS traversal of token tree (no recursion)
    collect_text_between_tokens: Extract text content between token pairs
    extract_code_blocks: Extract all code blocks from token stream
    iter_blocks: Legacy block iterator (markdown text → blocks)
    extract_links_and_images: Legacy link/image extractor (markdown text → links/images)

Classes:
    TokenAdapter: Wrapper for safe dual-shape token handling
"""

from typing import Generator, Optional, Any
from markdown_it import MarkdownIt
from markdown_it.token import Token

from mdit_py_plugins.tasklists import tasklists_plugin as tasklists


md = (
    MarkdownIt("commonmark", options_update={"html": False, "linkify": True}).enable('table')
)
md.use(tasklists)


# ============================================================================
# Token Traversal Utilities (Phase 0 additions)
# ============================================================================

def walk_tokens_iter(tokens: list[Token]) -> Generator[Token, None, None]:
    """Iterative DFS traversal of token tree (no recursion).

    This function replaces recursive token walking to avoid RecursionError
    on deeply nested documents. Uses a stack-based approach for depth-first
    traversal.

    Args:
        tokens: List of markdown-it Token objects to traverse

    Yields:
        Token objects in depth-first order

    Example:
        >>> tokens = md.parse("# Hello\\n\\nWorld")
        >>> for token in walk_tokens_iter(tokens):
        ...     print(token.type)
    """
    stack = [(tokens, 0)]
    while stack:
        lst, i = stack.pop()
        if i >= len(lst):
            continue
        tok = lst[i]
        stack.append((lst, i + 1))
        yield tok
        if getattr(tok, "children", None):
            stack.append((tok.children, 0))


def collect_text_between_tokens(
    tokens: list[Token],
    start_idx: int,
    open_type: str = "link_open",
    close_type: str = "link_close"
) -> str:
    """Collect text content between matching open/close token pairs.

    This function traverses tokens between a matched pair (e.g., link_open/link_close)
    and extracts all text content, including from nested children. Handles depth
    tracking to find the matching close token.

    Args:
        tokens: List of markdown-it Token objects
        start_idx: Index to start searching from
        open_type: Token type that opens the pair (default: "link_open")
        close_type: Token type that closes the pair (default: "link_close")

    Returns:
        Concatenated text content from all text tokens within the pair

    Example:
        >>> tokens = md.parse("[**bold** text](url)")
        >>> # Find link_open token at some index i
        >>> text = collect_text_between_tokens(tokens, i)
        >>> # Returns: "bold text"
    """
    depth = 0
    out = []
    for i in range(start_idx, len(tokens)):
        t = tokens[i]
        if t.type == open_type:
            depth += 1
        elif t.type == close_type:
            depth -= 1
            if depth == 0:
                break
        elif depth > 0 and t.type == "text":
            out.append(t.content)
        if t.children:
            # Manually walk children
            for c in walk_tokens_iter(t.children):
                if depth > 0 and c.type == "text":
                    out.append(c.content)
    return "".join(out)


def extract_code_blocks(tokens: list[Token]) -> list[dict[str, Any]]:
    """Extract all code blocks from token stream.

    This function walks the token tree and collects all fence and code_block
    tokens, returning structured information about each block.

    Args:
        tokens: List of markdown-it Token objects

    Returns:
        List of dictionaries with code block information:
        - language: Language identifier (or None if not specified)
        - content: Code block content
        - line: Starting line number (or None if not available)
        - line_end: Ending line number (or None if not available)

    Example:
        >>> tokens = md.parse("```python\\nprint('hello')\\n```")
        >>> blocks = extract_code_blocks(tokens)
        >>> blocks[0]['language']
        'python'
        >>> blocks[0]['content']
        "print('hello')\\n"
    """
    blocks = []
    for token in walk_tokens_iter(tokens):
        if token.type in ('fence', 'code_block'):
            blocks.append({
                'language': getattr(token, 'info', '') or None,
                'content': token.content,
                'line': token.map[0] if token.map else None,
                'line_end': token.map[1] if token.map else None,
            })
    return blocks


class TokenAdapter:
    """Wrapper for safe dual-shape token handling.

    This class provides a consistent interface for accessing token properties
    whether working with Token objects or dictionaries, enabling safe refactoring
    from dict-based to Token-based code.

    Attributes:
        token: The underlying Token object or dict

    Example:
        >>> token = Token(type="text", tag="", nesting=0)
        >>> adapter = TokenAdapter(token)
        >>> adapter.type
        'text'
        >>> adapter.get('content', '')
        ''
    """

    def __init__(self, token: Token | dict[str, Any]):
        """Initialize TokenAdapter.

        Args:
            token: Token object or dictionary to wrap
        """
        self.token = token

    def __getattr__(self, name: str) -> Any:
        """Get attribute from underlying token.

        Args:
            name: Attribute name

        Returns:
            Attribute value

        Raises:
            AttributeError: If attribute not found
        """
        if isinstance(self.token, dict):
            if name in self.token:
                return self.token[name]
            raise AttributeError(f"Token dict has no key '{name}'")
        return getattr(self.token, name)

    def get(self, name: str, default: Any = None) -> Any:
        """Get attribute with default value.

        Args:
            name: Attribute name
            default: Default value if attribute not found

        Returns:
            Attribute value or default
        """
        if isinstance(self.token, dict):
            return self.token.get(name, default)
        return getattr(self.token, name, default)

    @property
    def type(self) -> str:
        """Get token type."""
        return self.get('type', '')

    @property
    def content(self) -> str:
        """Get token content."""
        return self.get('content', '')

    @property
    def children(self) -> Optional[list]:
        """Get token children."""
        return self.get('children', None)


# ============================================================================
# Legacy Utilities (Pre-Phase 0)
# ============================================================================

text = "- [ ] An item that needs doing\n- [x] An item that is complete"

def iter_blocks(text: str) -> Generator[dict[str, Any], None, None]:
    """Legacy block iterator using markdown text as input.

    NOTE: This function will be replaced by token-based iteration in Phase 1.

    Args:
        text: Markdown text to parse

    Yields:
        Block dictionaries with 'kind', and type-specific fields
    """
    tokens = md.parse(text)
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type in {"fence", "code_block"}:
            yield {"kind": "code", "lang": (t.info or "").strip() or None, "map": t.map}
        elif t.type == "heading_open":
            inline = tokens[i+1] if i + 1 < len(tokens) else None
            heading_text = ""
            if inline and inline.type == "inline" and inline.children:
                heading_text = "".join(c.content for c in inline.children if c.type == "text")
            yield {"kind": "heading", "level": int(t.tag[1]), "text": heading_text, "map": t.map}
        i += 1


def extract_links_and_images(text: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Legacy link/image extractor using markdown text as input.

    NOTE: This function will be replaced by token-based extraction in Phase 3.

    Args:
        text: Markdown text to parse

    Returns:
        Tuple of (links, images) where:
        - links: List of href strings
        - images: List of (src, alt) tuples
    """
    tokens = md.parse(text)
    links, images = [], []
    stack = list(tokens)
    while stack:
        tok = stack.pop()
        if tok.children:
            stack.extend(tok.children)
        if tok.type == "link_open":
            href = dict(tok.attrs or {}).get("href","")
            links.append(href)
        elif tok.type == "image":
            attrs = dict(tok.attrs or {})
            src = attrs.get("src","")
            alt = ""
            if tok.children:
                alt = "".join(c.content for c in tok.children if c.type == "text")
            images.append((src, alt))
    return links, images
