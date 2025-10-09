#!/usr/bin/env python3
"""Debug sanitize functionality."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore

content = """![Data URI](data:image/png;base64,iVBORw0KG...)"""

# Test the regex pattern
pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
matches = re.findall(pattern, content)
print(f"Regex matches: {matches}")

# Test with parser
parser = MarkdownParserCore(content)
result = parser.sanitize({"drop_data_uri_images": True})
print(f"Sanitized: {result['sanitized_text']}")
print(f"Reasons: {result['reasons']}")
