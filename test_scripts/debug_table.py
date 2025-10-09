#!/usr/bin/env python3
"""Debug table parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore

content = """
| Col1 | Col2 | Col3 |
|------|------|------|
| A    | B    |      |
| C    | D    | E    | F |
"""

parser = MarkdownParserCore(content)
result = parser.parse()

print("Tables found:")
for table in result["structure"]["tables"]:
    print(f"  Headers: {table.get('headers')}")
    print(f"  Rows: {table.get('rows')}")
    print(f"  Row count: {table.get('row_count')}")
    print(f"  Col count: {table.get('column_count')}")
    print(f"  Is ragged: {table.get('is_ragged')}")
    print()

print("Security stats:")
print(
    f"  Ragged tables count: {result['metadata']['security']['statistics']['ragged_tables_count']}"
)
