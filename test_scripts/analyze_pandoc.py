#!/usr/bin/env python3
"""Analyze why pandoc tests expect 3 tables."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore

content = """---
title: "Pandoc Features 01"
---

# Pandoc Goodies

Term 1
: Definition 1
: Definition 2

::: note
Block with attributes {.class #id}
:::

Paragraph with attributes {.lead}

### Heading {#dup-id}
#### Another {#dup-id}

A table:

| k | v |
|:-:|:-:|
| a | b |
"""

parser = MarkdownParserCore(content)
result = parser.parse()

# Check what structures are found
print("Structures found:")
print(f"Tables: {len(result['structure']['tables'])}")
print(f"Lists: {len(result['structure']['lists'])}")
print(f"Paragraphs: {len(result['structure']['paragraphs'])}")
print(f"Headings: {len(result['structure']['headings'])}")

# Look at the tokens
print("\nToken types found:")
token_types = {}
for token in parser.tokens:
    t = token.type
    token_types[t] = token_types.get(t, 0) + 1

for t, count in sorted(token_types.items()):
    print(f"  {t}: {count}")

# Check for definition list syntax
print("\nChecking lines that might be misinterpreted:")
lines = content.split("\n")
for i, line in enumerate(lines):
    if line.startswith(":"):
        print(f"Line {i}: {line[:50]}")
