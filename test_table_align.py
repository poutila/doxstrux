#!/usr/bin/env python3
"""Test table alignment extraction from tokens."""

from src.docpipe.markdown_parser_core import MarkdownParserCore

# Test table with different alignments
md = """| Left | Center | Right |
|:-----|:------:|------:|
| A    | B      | C     |
| 1    | 2      | 3     |"""

parser = MarkdownParserCore(md)
result = parser.parse()
table = result['structure']['tables'][0]

print('Headers:', table['headers'])
print('Alignment:', table['align'])
print('Rows:', table['rows'])
print('Test PASSED!' if table['align'] == ['left', 'center', 'right'] else 'Test FAILED!')
