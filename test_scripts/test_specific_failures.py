import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from docpipe.loaders.markdown_parser_core import MarkdownParserCore

# Test 44: Mixed schemes
content44 = """[Good](https://example.com)
[Bad](javascript:void(0))
[Good](mailto:test@example.com)
[Bad](file:///etc/passwd)"""

print("Test 44: Mixed schemes")
parser = MarkdownParserCore(content44, security_profile="moderate")
result = parser.parse()
print(f"Link schemes: {result['metadata']['security']['statistics']['link_schemes']}")
print()

# Test 57: Ragged table
content57 = """| Col1 | Col2 | Col3 |
|------|------|
| A | B | C |
| D | E |
| F | G | H | I |"""

print("Test 57: Ragged table")
parser = MarkdownParserCore(content57, security_profile="moderate")
result = parser.parse()
print(f"Ragged tables count: {result['metadata']['security']['statistics']['ragged_tables_count']}")
print(f"Tables found: {len(result['structure']['tables'])}")
if result["structure"]["tables"]:
    table = result["structure"]["tables"][0]
    print(f"Table rows: {len(table['rows'])}")
    for i, row in enumerate(table["rows"]):
        print(f"  Row {i}: {len(row['cells'])} cells")
