#!/usr/bin/env python3
"""Debug footnote parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore

content = (
    """
Some text[^1].

[^1]: This is a long footnote """
    + "A" * 600
)

parser = MarkdownParserCore(content, config={"plugins": ["footnote"]})
result = parser.parse()

print("Footnotes:")
footnotes = result["structure"].get("footnotes", {})
print(f"  Definitions: {footnotes.get('definitions', [])}")
print(f"  References: {footnotes.get('references', [])}")

# Check tokens
print("\nFootnote tokens:")
for token in parser.tokens:
    if "footnote" in token.type:
        print(f"  {token.type}: {token}")

# Check tree
print("\nFootnote nodes in tree:")
for node in parser.tree.walk():
    if "footnote" in node.type:
        print(
            f"  {node.type}: children={len(node.children or [])} content='{getattr(node, 'content', '')[:50] if hasattr(node, 'content') else ''}'"
        )
        if node.children:
            for child in node.children:
                print(
                    f"    -> {child.type}: '{getattr(child, 'content', '')[:50] if hasattr(child, 'content') else ''}'"
                )
                if child.children:
                    for gchild in child.children:
                        print(
                            f"      --> {gchild.type}: '{getattr(gchild, 'content', '')[:50] if hasattr(gchild, 'content') else ''}'"
                        )
