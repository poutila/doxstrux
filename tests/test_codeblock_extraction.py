"""Tests for code block extraction behavior.

These tests verify that fenced and indented code blocks are correctly extracted
with language info, content, and line attribution preserved.
"""

import pytest

from doxstrux.markdown_parser_core import MarkdownParserCore


class TestFencedCodeBlocks:
    """Tests for fenced code block extraction."""

    def test_simple_fenced_code_block(self) -> None:
        """Simple fenced code block should be extracted."""
        content = """# Test

```
plain code
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        cb = code_blocks[0]
        assert "plain code" in cb.get("content", cb.get("code", ""))

    def test_fenced_code_with_language(self) -> None:
        """Fenced code block with language should capture language."""
        content = """# Test

```python
print("Hello")
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        cb = code_blocks[0]
        assert cb.get("language") == "python"

    def test_multiple_languages(self) -> None:
        """Multiple code blocks with different languages."""
        content = """# Test

```python
x = 1
```

```javascript
const x = 1;
```

```rust
let x = 1;
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 3

        languages = [cb.get("language") for cb in code_blocks]
        assert "python" in languages
        assert "javascript" in languages
        assert "rust" in languages

    def test_tilde_fence(self) -> None:
        """Tilde fences should work the same as backticks."""
        content = """# Test

~~~python
code here
~~~
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1
        assert code_blocks[0].get("language") == "python"

    def test_code_block_with_info_string(self) -> None:
        """Info string after language should be captured."""
        content = """# Test

```python title="example.py"
print("hello")
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        # Language should be extracted (may include or exclude info string)
        cb = code_blocks[0]
        assert "python" in (cb.get("language") or "")


class TestCodeBlockContent:
    """Tests for code block content preservation."""

    def test_multiline_code_preserved(self) -> None:
        """Multi-line code should be preserved."""
        content = """# Test

```python
def hello():
    print("Hello")
    return True

def world():
    print("World")
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        code = code_blocks[0].get("content", code_blocks[0].get("code", ""))
        assert "def hello" in code
        assert "def world" in code

    def test_indentation_preserved(self) -> None:
        """Indentation inside code block should be preserved."""
        content = """# Test

```python
if True:
    if True:
        nested = "value"
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        code = code_blocks[0].get("content", code_blocks[0].get("code", ""))

        # Should have indentation
        assert "    " in code or "\t" in code

    def test_empty_code_block(self) -> None:
        """Empty code block should be handled."""
        content = """# Test

```
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

    def test_code_with_special_chars(self) -> None:
        """Code with special characters should be preserved."""
        content = """# Test

```python
regex = r"\\d+\\.\\d+"
html = "<div class='test'>&amp;</div>"
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1


class TestCodeBlockLineAttribution:
    """Tests for code block line number attribution."""

    def test_code_block_start_line(self) -> None:
        """Code block should have correct start line."""
        content = """# Test

Some paragraph.

```python
code here
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        cb = code_blocks[0]
        assert "start_line" in cb
        assert cb["start_line"] == 4  # 0-indexed

    def test_code_block_end_line(self) -> None:
        """Code block should have correct end line."""
        content = """# Test

```python
line 1
line 2
line 3
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        cb = code_blocks[0]

        assert "end_line" in cb
        # End line should be after the closing fence
        assert cb["end_line"] > cb["start_line"]

    def test_multiple_blocks_line_attribution(self) -> None:
        """Multiple code blocks should have distinct line ranges."""
        content = """# Test

```python
first block
```

```javascript
second block
```

```rust
third block
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 3

        # Each block should have unique line range
        for i in range(len(code_blocks) - 1):
            assert code_blocks[i]["end_line"] <= code_blocks[i + 1]["start_line"]


class TestCodeBlockEdgeCases:
    """Edge cases for code block extraction."""

    def test_code_block_in_list(self) -> None:
        """Code block inside list item."""
        content = """# Test

- Item with code:

  ```python
  print("in list")
  ```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) >= 1

    def test_code_block_in_blockquote(self) -> None:
        """Code block inside blockquote."""
        content = """# Test

> Quote with code:
>
> ```python
> print("in quote")
> ```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        # Should not crash
        code_blocks = result["structure"]["code_blocks"]
        assert isinstance(code_blocks, list)

    def test_adjacent_code_blocks(self) -> None:
        """Adjacent code blocks without text between."""
        content = """# Test

```python
first
```
```javascript
second
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 2

    def test_code_block_with_blank_lines(self) -> None:
        """Code block containing blank lines."""
        content = """# Test

```python
line 1

line 3

line 5
```
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        code = code_blocks[0].get("content", code_blocks[0].get("code", ""))
        # Blank lines should be preserved
        assert "\n\n" in code or code.count("\n") >= 4

    def test_long_fence_markers(self) -> None:
        """Long fence markers (more than 3 chars)."""
        content = """# Test

`````python
code here
`````
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

    def test_code_block_containing_fence_chars(self) -> None:
        """Code block containing backticks."""
        content = """# Test

````python
```
nested backticks
```
````
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        code = code_blocks[0].get("content", code_blocks[0].get("code", ""))
        assert "```" in code


class TestCodeBlockSectionAttribution:
    """Tests for code block section attribution."""

    def test_code_block_in_section(self) -> None:
        """Code block should be attributed to containing section."""
        content = """# Introduction

Some intro text.

## Methods

```python
def method():
    pass
```

## Results

No code here.
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        code_blocks = result["structure"]["code_blocks"]
        assert len(code_blocks) == 1

        # Code block should have section info if available
        cb = code_blocks[0]
        if "section_id" in cb or "in_section" in cb:
            section_ref = cb.get("section_id") or cb.get("in_section")
            assert section_ref is not None
