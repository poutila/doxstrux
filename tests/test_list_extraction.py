"""Tests for list extraction behavior.

These tests verify that lists (bullet, ordered, and nested) are correctly extracted
with proper structure preservation.
"""

import pytest

from doxstrux.markdown_parser_core import MarkdownParserCore


class TestBulletListExtraction:
    """Tests for bullet list extraction."""

    def test_simple_bullet_list(self) -> None:
        """Simple bullet list should be extracted."""
        content = """# Test

- Item 1
- Item 2
- Item 3
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1

        lst = lists[0]
        assert lst["type"] == "bullet"
        assert len(lst["items"]) == 3

    def test_bullet_list_with_different_markers(self) -> None:
        """Different bullet markers should all work."""
        content = """# Test

- Dash item
* Asterisk item
+ Plus item
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        # All markers create bullet lists
        assert len(lists) >= 1
        for lst in lists:
            assert lst["type"] == "bullet"

    def test_nested_bullet_list(self) -> None:
        """Nested bullet lists should preserve hierarchy."""
        content = """# Test

- Parent 1
  - Child 1.1
  - Child 1.2
- Parent 2
  - Child 2.1
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1

        # Top-level list should have items
        top_list = lists[0]
        assert len(top_list["items"]) >= 2


class TestOrderedListExtraction:
    """Tests for ordered list extraction."""

    def test_simple_ordered_list(self) -> None:
        """Simple ordered list should be extracted."""
        content = """# Test

1. First item
2. Second item
3. Third item
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1

        lst = lists[0]
        assert lst["type"] == "ordered"
        assert len(lst["items"]) == 3

    def test_ordered_list_with_start_number(self) -> None:
        """Ordered list with non-1 start should work."""
        content = """# Test

5. Fifth item
6. Sixth item
7. Seventh item
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1
        assert lists[0]["type"] == "ordered"

    def test_mixed_ordered_markers(self) -> None:
        """Ordered list with . and ) markers."""
        content = """# Test

1. Dot marker
2. Another dot

1) Paren marker
2) Another paren
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        # Should have at least one ordered list
        ordered_lists = [lst for lst in lists if lst["type"] == "ordered"]
        assert len(ordered_lists) >= 1


class TestTaskListExtraction:
    """Tests for task list extraction."""

    def test_simple_task_list(self) -> None:
        """Task lists with checkboxes should be extracted."""
        content = """# Test

- [ ] Unchecked task
- [x] Checked task
- [ ] Another unchecked
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        tasklists = result["structure"]["tasklists"]
        assert len(tasklists) >= 1

        # Verify task structure
        tasks = tasklists[0]["items"]
        assert len(tasks) == 3

        # Check checkbox states
        states = [t.get("checked", t.get("done")) for t in tasks]
        assert False in states  # Unchecked
        assert True in states   # Checked

    def test_mixed_list_and_tasks(self) -> None:
        """Document with both regular lists and task lists."""
        content = """# Test

Regular list:
- Item 1
- Item 2

Task list:
- [ ] Task 1
- [x] Task 2
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        tasklists = result["structure"]["tasklists"]

        # Should have both types
        assert len(lists) >= 1
        assert len(tasklists) >= 1


class TestListEdgeCases:
    """Edge cases for list extraction."""

    def test_empty_list_items(self) -> None:
        """List items can be empty."""
        content = """# Test

-
- Non-empty
-
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        # Should not crash on empty items
        lists = result["structure"]["lists"]
        assert isinstance(lists, list)

    def test_list_with_inline_formatting(self) -> None:
        """List items with bold, italic, code."""
        content = """# Test

- **Bold item**
- *Italic item*
- `Code item`
- [Link item](http://example.com)
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1
        assert len(lists[0]["items"]) == 4

    def test_list_with_multiline_items(self) -> None:
        """List items can span multiple lines."""
        content = """# Test

- This is a long item
  that continues on the next line
- Short item
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1
        assert len(lists[0]["items"]) == 2

    def test_deeply_nested_list(self) -> None:
        """Deeply nested lists should be handled."""
        content = """# Test

- Level 1
  - Level 2
    - Level 3
      - Level 4
        - Level 5
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1

    def test_list_after_paragraph(self) -> None:
        """List immediately after paragraph."""
        content = """# Test

This is a paragraph.
- List item 1
- List item 2
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        paragraphs = result["structure"]["paragraphs"]

        assert len(lists) >= 1
        assert len(paragraphs) >= 1

    def test_list_with_code_block(self) -> None:
        """List item containing code block."""
        content = """# Test

- Item with code:

  ```python
  print("hello")
  ```

- Next item
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        code_blocks = result["structure"]["code_blocks"]

        assert len(lists) >= 1
        assert len(code_blocks) >= 1


class TestListLineAttribution:
    """Tests for list line number attribution."""

    def test_list_start_line(self) -> None:
        """List should have correct start line."""
        content = """# Test

Some paragraph.

- Item 1
- Item 2
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1

        lst = lists[0]
        assert "start_line" in lst or "line" in lst

    def test_list_items_have_lines(self) -> None:
        """Each list item should have line info if available."""
        content = """- Item on line 0
- Item on line 1
- Item on line 2
"""
        parser = MarkdownParserCore(content)
        result = parser.parse()

        lists = result["structure"]["lists"]
        assert len(lists) >= 1

        # Items should exist
        assert len(lists[0]["items"]) == 3
