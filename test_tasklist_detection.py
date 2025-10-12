#!/usr/bin/env python3
"""Test that tasklist detection still works after simplification."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from docpipe.markdown_parser_core import MarkdownParserCore

# Test markdown
md = """# Mixed regular list items and tasks

- Regular item 1
- [ ] Task item 1
- Regular item 2
- [x] Task item 2 done
- Regular item 3
  - [ ] Nested task
  - Regular nested item
  - [x] Another nested task
"""

# Parse
parser = MarkdownParserCore(md)
result = parser.parse()

# Check results
lists = result['structure']['lists']
if lists:
    print('First list:')
    for i, item in enumerate(lists[0]['items'][:4]):
        checked = item.get('checked')
        text = item.get('text', '')
        print(f'  Item {i}: checked={checked}, text="{text}"')

    # Verify
    items = lists[0]['items']
    assert items[0]['checked'] is None, "Regular item should have checked=None"
    assert items[0]['text'] == "Regular item 1"

    assert items[1]['checked'] is False, "[ ] should have checked=False"
    assert items[1]['text'] == "Task item 1"

    assert items[2]['checked'] is None, "Regular item should have checked=None"
    assert items[2]['text'] == "Regular item 2"

    assert items[3]['checked'] is True, "[x] should have checked=True"
    assert items[3]['text'] == "Task item 2 done"

    print('\n✓ All task detection tests passed!')
else:
    print('ERROR: No lists found!')
    sys.exit(1)
