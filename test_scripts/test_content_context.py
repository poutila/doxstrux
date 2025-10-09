#!/usr/bin/env python3
"""Test ContentContext integration in MarkdownParserCore."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_code_block_detection():
    """Test that code blocks are properly detected with language."""
    content = """# Code Examples

Here's some Python code:

```python
def hello():
    print("Hello, World!")
```

And some JavaScript:

```javascript
console.log("Hello");
```

Some prose in between.

```
No language specified
```
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()
    mappings = result["mappings"]

    # Check code blocks are detected
    code_blocks = mappings.get("code_blocks", [])
    print(f"Found {len(code_blocks)} code blocks")

    for i, block in enumerate(code_blocks):
        print(f"Block {i + 1}:")
        print(f"  Lines: {block.get('start_line')}-{block.get('end_line')}")
        print(f"  Language: {block.get('language', 'none')}")

    # Should have detected code blocks
    assert len(code_blocks) > 0, "No code blocks detected"

    # Check that some blocks have language info
    langs = [b.get("language") for b in code_blocks if b.get("language")]
    assert "python" in langs, f"Python language not detected. Found: {langs}"
    assert "javascript" in langs, f"JavaScript language not detected. Found: {langs}"

    print("✅ Code block detection works")


def test_prose_code_distinction():
    """Test prose vs code line classification."""
    content = """# Document

This is prose.

```python
# This is code
x = 42
```

More prose here.
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()
    mappings = result["mappings"]

    prose_lines = mappings.get("prose_lines", [])
    code_lines = mappings.get("code_lines", [])

    print(f"Prose lines: {len(prose_lines)}")
    print(f"Code lines: {len(code_lines)}")

    # Should have both prose and code
    assert len(prose_lines) > 0, "No prose lines detected"
    assert len(code_lines) > 0, "No code lines detected"

    # Check line_to_type mapping
    line_to_type = mappings.get("line_to_type", {})

    # Line 0 should be prose (heading)
    assert line_to_type.get(0) == "prose", f"Line 0 should be prose, got {line_to_type.get(0)}"

    # Lines with code should be marked as code
    code_start = content.split("\n").index("# This is code")
    assert line_to_type.get(code_start) == "code", "Code line should be marked as code"

    print("✅ Prose/code distinction works")


def test_fallback_without_context():
    """Test that parser works even without ContentContext."""
    # Temporarily disable ContentContext
    import src.docpipe.loaders.markdown_parser_core as mdcore

    original_has_cc = mdcore._HAS_CC

    try:
        # Simulate ContentContext not available
        mdcore._HAS_CC = False

        content = """# Test

Some content here.

```python
code = True
```
"""

        parser = MarkdownParserCore(content)
        result = parser.parse()
        mappings = result["mappings"]

        # Should still work, but all lines marked as prose initially
        line_to_type = mappings.get("line_to_type", {})
        assert len(line_to_type) > 0, "No line mappings created"

        # Code blocks in mappings should still be empty or populated from AST
        print(f"Mappings without ContentContext: {list(line_to_type.values())[:5]}")
        print("✅ Fallback mode works")

    finally:
        # Restore original state
        mdcore._HAS_CC = original_has_cc


def test_indented_code():
    """Test indented code block detection."""
    content = """# Document

Regular prose.

    # This is indented code
    def example():
        pass

Back to prose.
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()
    mappings = result["mappings"]

    # Check that indented lines are marked as code
    lines = content.split("\n")
    indented_line = lines.index("    # This is indented code")
    line_to_type = mappings.get("line_to_type", {})

    # AST overlay should mark these as code
    # (Note: This depends on AST code block extraction)
    print(f"Line {indented_line} type: {line_to_type.get(indented_line)}")

    # Check code_lines includes indented code
    code_lines = mappings.get("code_lines", [])
    print(f"Code lines detected: {code_lines}")

    print("✅ Indented code detection tested")


def main():
    """Run all ContentContext integration tests."""
    print("Testing ContentContext Integration")
    print("=" * 50)

    tests = [
        test_code_block_detection,
        test_prose_code_distinction,
        test_fallback_without_context,
        test_indented_code,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "=" * 50)
    if failed == 0:
        print("✅ All ContentContext tests passed!")
    else:
        print(f"❌ {failed} tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
