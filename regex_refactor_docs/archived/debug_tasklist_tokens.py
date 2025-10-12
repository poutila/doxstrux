#!/usr/bin/env python3
"""Debug script to inspect task list token structure."""

from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin

# Test markdown with task lists
test_md = """# Test

- Regular item 1
- [ ] Task item unchecked
- [x] Task item checked
- Regular item 2
"""

# Parse with tasklists plugin enabled
md = MarkdownIt("commonmark").enable('table').use(tasklists_plugin)
tokens = md.parse(test_md)

print("=" * 80)
print("TOKEN STRUCTURE:")
print("=" * 80)

for i, token in enumerate(tokens):
    print(f"\n[{i}] {token.type}")
    print(f"    tag: {token.tag}")
    print(f"    nesting: {token.nesting}")
    print(f"    level: {token.level}")

    if hasattr(token, 'attrs') and token.attrs:
        print(f"    attrs: {token.attrs}")

    if hasattr(token, 'content') and token.content:
        print(f"    content: {repr(token.content)[:100]}")

    if hasattr(token, 'children') and token.children:
        print(f"    children ({len(token.children)}):")
        for j, child in enumerate(token.children):
            print(f"        [{j}] {child.type}", end="")
            if hasattr(child, 'content') and child.content:
                print(f" content={repr(child.content)[:50]}", end="")
            if hasattr(child, 'attrs') and child.attrs:
                print(f" attrs={child.attrs}", end="")
            print()

print("\n" + "=" * 80)
print("FINDING TASK LISTS:")
print("=" * 80)

# Find bullet_list tokens
for i, token in enumerate(tokens):
    if token.type == "bullet_list_open":
        print(f"\nFound bullet_list_open at index {i}")
        print(f"  tag: {token.tag}")
        print(f"  attrs: {token.attrs if hasattr(token, 'attrs') and token.attrs else 'None'}")

        # Check for contains-task-list class
        if hasattr(token, 'attrs') and token.attrs:
            if isinstance(token.attrs, dict):
                class_value = token.attrs.get('class', '')
                print(f"  class attribute: {repr(class_value)}")
                if 'contains-task-list' in class_value:
                    print("  ✓ THIS IS A TASK LIST!")
            elif isinstance(token.attrs, list):
                print(f"  attrs is list: {token.attrs}")
                for attr_name, attr_value in token.attrs:
                    if attr_name == 'class':
                        print(f"  class attribute: {repr(attr_value)}")
                        if 'contains-task-list' in attr_value:
                            print("  ✓ THIS IS A TASK LIST!")

print("\n" + "=" * 80)
print("TASK LIST ITEMS:")
print("=" * 80)

# Find list_item tokens
for i, token in enumerate(tokens):
    if token.type == "list_item_open":
        print(f"\nlist_item_open at index {i}")
        if hasattr(token, 'attrs') and token.attrs:
            print(f"  attrs: {token.attrs}")
            if isinstance(token.attrs, dict):
                class_value = token.attrs.get('class', '')
                print(f"  class: {repr(class_value)}")
            elif isinstance(token.attrs, list):
                for attr_name, attr_value in token.attrs:
                    if attr_name == 'class':
                        print(f"  class: {repr(attr_value)}")
