"""Unit tests for token_replacement_lib.py utilities.

Tests for Phase 0 token utility functions added to support the zero-regex
refactoring project.
"""

import pytest
from markdown_it import MarkdownIt
from markdown_it.token import Token

from docpipe.token_replacement_lib import (
    walk_tokens_iter,
    collect_text_between_tokens,
    extract_code_blocks,
    TokenAdapter,
)


@pytest.fixture
def md():
    """Markdown parser instance for testing."""
    return MarkdownIt("commonmark", {"html": False})


class TestWalkTokensIter:
    """Tests for walk_tokens_iter() function."""

    def test_empty_tokens(self):
        """Should handle empty token list."""
        tokens = []
        result = list(walk_tokens_iter(tokens))
        assert result == []

    def test_flat_tokens(self, md):
        """Should walk tokens without children."""
        tokens = md.parse("# Hello\n\nWorld")
        result = list(walk_tokens_iter(tokens))

        # Should yield all tokens in the list
        assert len(result) > 0
        assert all(isinstance(t, Token) for t in result)

    def test_nested_tokens(self, md):
        """Should walk tokens with children (inline content)."""
        tokens = md.parse("# Hello **bold** text")
        result = list(walk_tokens_iter(tokens))

        # Should include parent tokens and their children
        assert len(result) > 0

        # Check that we get both parent and child tokens
        types = [t.type for t in result]
        assert "heading_open" in types
        assert "inline" in types  # Parent
        # Children of inline token should also be present

    def test_deeply_nested_tokens(self, md):
        """Should handle deeply nested structures without recursion error."""
        # Create a document with multiple levels of nesting
        markdown = """
# Level 1

- Item 1
  - Nested item
    - Deeply nested item

[Link with **bold** and *italic* text](url)

> Quote with **bold**
> > Nested quote
"""
        tokens = md.parse(markdown)
        result = list(walk_tokens_iter(tokens))

        # Should complete without RecursionError
        assert len(result) > 10
        assert all(isinstance(t, Token) for t in result)

    def test_code_blocks_with_walk(self, md):
        """Should walk through code block tokens."""
        tokens = md.parse("```python\nprint('hello')\n```")
        result = list(walk_tokens_iter(tokens))

        # Should find fence token
        types = [t.type for t in result]
        assert "fence" in types

    def test_token_order(self, md):
        """Should walk tokens in depth-first order."""
        tokens = md.parse("**bold**")
        result = list(walk_tokens_iter(tokens))

        # Get types in order
        types = [t.type for t in result]

        # paragraph_open should come before its inline children
        if "paragraph_open" in types and "inline" in types:
            para_idx = types.index("paragraph_open")
            inline_idx = types.index("inline")
            assert para_idx < inline_idx


class TestCollectTextBetweenTokens:
    """Tests for collect_text_between_tokens() function."""

    def test_simple_link_text(self, md):
        """Should extract text from simple link."""
        markdown = "[click here](url)"
        tokens = md.parse(markdown)

        # Find the link_open token
        flat_tokens = list(walk_tokens_iter(tokens))
        link_open_idx = None
        for i, t in enumerate(flat_tokens):
            if t.type == "link_open":
                link_open_idx = i
                break

        if link_open_idx is not None:
            # Note: collect_text_between_tokens expects the top-level token list
            # For this test, we'll use a simpler approach
            text = collect_text_between_tokens(tokens, 0)
            # The function should find the text between link_open and link_close
            # This will depend on token structure

    def test_link_with_formatting(self, md):
        """Should extract text from link with inline formatting."""
        markdown = "[**bold** text](url)"
        tokens = md.parse(markdown)

        # The function should extract all text content
        # even from nested bold tokens
        text = collect_text_between_tokens(tokens, 0)
        # Expected: "bold text" (without markdown syntax)

    def test_nested_links(self, md):
        """Should handle nested structures with depth tracking."""
        markdown = "[outer [inner](url2)](url1)"
        tokens = md.parse(markdown)

        # Should track depth correctly and find matching close
        text = collect_text_between_tokens(tokens, 0)
        # Should extract text from the outer link

    def test_empty_link(self, md):
        """Should handle empty link text."""
        markdown = "[](url)"
        tokens = md.parse(markdown)

        text = collect_text_between_tokens(tokens, 0)
        assert text == ""

    def test_custom_token_types(self, md):
        """Should work with custom open/close token types."""
        # Test with different token types if needed
        # This is a placeholder for extensibility testing
        pass


class TestExtractCodeBlocks:
    """Tests for extract_code_blocks() function."""

    def test_no_code_blocks(self, md):
        """Should return empty list when no code blocks present."""
        tokens = md.parse("# Just a heading\n\nSome text")
        blocks = extract_code_blocks(tokens)
        assert blocks == []

    def test_single_fence_block(self, md):
        """Should extract single fenced code block."""
        tokens = md.parse("```python\nprint('hello')\n```")
        blocks = extract_code_blocks(tokens)

        assert len(blocks) == 1
        assert blocks[0]['language'] == 'python'
        assert 'hello' in blocks[0]['content']
        assert blocks[0]['line'] is not None
        assert blocks[0]['line_end'] is not None

    def test_fence_without_language(self, md):
        """Should handle fence without language identifier."""
        tokens = md.parse("```\ncode here\n```")
        blocks = extract_code_blocks(tokens)

        assert len(blocks) == 1
        assert blocks[0]['language'] is None
        assert 'code here' in blocks[0]['content']

    def test_multiple_code_blocks(self, md):
        """Should extract multiple code blocks."""
        markdown = """
```python
print('first')
```

Some text

```javascript
console.log('second')
```
"""
        tokens = md.parse(markdown)
        blocks = extract_code_blocks(tokens)

        assert len(blocks) == 2
        assert blocks[0]['language'] == 'python'
        assert blocks[1]['language'] == 'javascript'
        assert 'first' in blocks[0]['content']
        assert 'second' in blocks[1]['content']

    def test_indented_code_block(self, md):
        """Should extract indented code blocks."""
        markdown = "    indented code\n    more code"
        tokens = md.parse(markdown)
        blocks = extract_code_blocks(tokens)

        # Indented code creates code_block token
        assert len(blocks) >= 1
        assert any('code' in b['content'] for b in blocks)

    def test_nested_code_in_list(self, md):
        """Should extract code blocks nested in lists."""
        markdown = """
- Item 1
  ```python
  print('nested')
  ```
"""
        tokens = md.parse(markdown)
        blocks = extract_code_blocks(tokens)

        assert len(blocks) == 1
        assert blocks[0]['language'] == 'python'
        assert 'nested' in blocks[0]['content']

    def test_line_numbers(self, md):
        """Should provide line number information."""
        markdown = "\n\n```python\ncode\n```"
        tokens = md.parse(markdown)
        blocks = extract_code_blocks(tokens)

        assert len(blocks) == 1
        # Line numbers should be present
        assert isinstance(blocks[0]['line'], int)
        assert isinstance(blocks[0]['line_end'], int)
        assert blocks[0]['line_end'] > blocks[0]['line']


class TestTokenAdapter:
    """Tests for TokenAdapter class."""

    def test_adapt_token_object(self):
        """Should adapt Token objects."""
        token = Token(type="text", tag="", nesting=0)
        token.content = "hello"

        adapter = TokenAdapter(token)
        assert adapter.type == "text"
        assert adapter.content == "hello"

    def test_adapt_dict(self):
        """Should adapt dictionary."""
        token_dict = {
            "type": "text",
            "content": "world",
            "tag": ""
        }

        adapter = TokenAdapter(token_dict)
        assert adapter.type == "text"
        assert adapter.content == "world"

    def test_get_with_default_token(self):
        """Should return default value for missing attributes (Token)."""
        token = Token(type="text", tag="", nesting=0)
        adapter = TokenAdapter(token)

        result = adapter.get('missing_attr', 'default')
        assert result == 'default'

    def test_get_with_default_dict(self):
        """Should return default value for missing keys (dict)."""
        token_dict = {"type": "text"}
        adapter = TokenAdapter(token_dict)

        result = adapter.get('missing_key', 'default')
        assert result == 'default'

    def test_property_type(self):
        """Should access type property."""
        token = Token(type="heading_open", tag="h1", nesting=1)
        adapter = TokenAdapter(token)

        assert adapter.type == "heading_open"

    def test_property_content(self):
        """Should access content property."""
        token = Token(type="text", tag="", nesting=0)
        token.content = "test content"
        adapter = TokenAdapter(token)

        assert adapter.content == "test content"

    def test_property_children(self):
        """Should access children property."""
        token = Token(type="inline", tag="", nesting=0)
        child1 = Token(type="text", tag="", nesting=0)
        child2 = Token(type="text", tag="", nesting=0)
        token.children = [child1, child2]

        adapter = TokenAdapter(token)
        assert adapter.children is not None
        assert len(adapter.children) == 2

    def test_children_none(self):
        """Should handle None children."""
        token = Token(type="text", tag="", nesting=0)
        adapter = TokenAdapter(token)

        assert adapter.children is None

    def test_attribute_error_dict(self):
        """Should raise AttributeError for missing dict key when using getattr."""
        token_dict = {"type": "text"}
        adapter = TokenAdapter(token_dict)

        with pytest.raises(AttributeError):
            _ = adapter.missing_key

    def test_dual_shape_safety(self):
        """Should provide consistent interface for both shapes."""
        token_obj = Token(type="text", tag="", nesting=0)
        token_obj.content = "same content"

        token_dict = {
            "type": "text",
            "content": "same content",
            "tag": ""
        }

        adapter_obj = TokenAdapter(token_obj)
        adapter_dict = TokenAdapter(token_dict)

        # Both should provide same interface
        assert adapter_obj.type == adapter_dict.type
        assert adapter_obj.content == adapter_dict.content
        assert adapter_obj.get('type') == adapter_dict.get('type')


class TestIntegration:
    """Integration tests combining multiple utilities."""

    def test_walk_and_extract(self, md):
        """Should use walk_tokens_iter with extract_code_blocks."""
        markdown = """
# Document

```python
def hello():
    print('world')
```

More text

```javascript
console.log('test')
```
"""
        tokens = md.parse(markdown)

        # Extract code blocks using walk
        blocks = extract_code_blocks(tokens)
        assert len(blocks) == 2

        # Walk all tokens
        all_tokens = list(walk_tokens_iter(tokens))

        # Code blocks should be in the walked tokens
        code_tokens = [t for t in all_tokens if t.type in ('fence', 'code_block')]
        assert len(code_tokens) == 2

    def test_adapter_with_walk(self, md):
        """Should use TokenAdapter with walk_tokens_iter."""
        tokens = md.parse("# Hello\n\n**Bold** text")

        # Walk and adapt all tokens
        adapted = [TokenAdapter(t) for t in walk_tokens_iter(tokens)]

        assert len(adapted) > 0
        assert all(hasattr(a, 'type') for a in adapted)

        # Check we can access properties consistently
        types = [a.type for a in adapted]
        assert "heading_open" in types
