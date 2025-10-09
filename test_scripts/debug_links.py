#!/usr/bin/env python3
"""Debug link parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore

content = """
[Click me](javascript:alert('XSS'))
[File access](file:///etc/passwd)
[Safe link](https://example.com)
"""

parser = MarkdownParserCore(content)
result = parser.parse()

print("Links found:")
for link in result["structure"]["links"]:
    print(f"  - URL: {link.get('url')}")
    print(f"    Text: {link.get('text')}")
    print(f"    Scheme: {link.get('scheme')}")
    print(f"    Allowed: {link.get('allowed')}")
    print()

# Check tokens
print("\nTokens:")
for token in parser.tokens:
    if token.type == "inline" and token.children:
        for child in token.children:
            if "link" in child.type:
                print(f"  {child.type}: {child}")
