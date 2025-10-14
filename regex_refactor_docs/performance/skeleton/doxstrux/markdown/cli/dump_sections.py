#!/usr/bin/env python3
"""CLI tool to dump section boundaries from markdown files.

This utility helps visualize section boundaries and confirm that the O(H)
section builder behaves correctly: no overlap, correct hierarchy, etc.

Usage:
    python -m doxstrux.markdown.cli.dump_sections <markdown-file>

    # Or directly:
    python dump_sections.py README.md

Example output:
    [00] L1    0-  12 | 'Introduction'
    [01] L2   13-  45 | 'Background'
    [02] L2   46-  89 | 'Methodology'
    [03] L3   90- 123 | 'Data Collection'
    [04] L3  124- 156 | 'Analysis Methods'
    [05] L2  157- 234 | 'Results'
"""

import sys
from pathlib import Path


def main():
    """Dump section boundaries from a markdown file."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: Missing required argument <markdown-file>")
        print("\nUsage: python dump_sections.py <markdown-file>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Try to import dependencies
    try:
        from markdown_it import MarkdownIt
        from markdown_it.tree import SyntaxTreeNode
    except ImportError as e:
        print(f"Error: Missing dependency: {e}")
        print("\nPlease install markdown-it-py:")
        print("  pip install markdown-it-py")
        sys.exit(1)

    try:
        # Import from installed package (if used as module)
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        # Import from local skeleton (if run directly)
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
            from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        except ImportError as e:
            print(f"Error: Cannot import TokenWarehouse: {e}")
            print("\nMake sure you're running from the skeleton directory or have installed doxstrux.")
            sys.exit(1)

    # Parse markdown
    try:
        md = MarkdownIt("commonmark")
        tokens = md.parse(text)
        tree = SyntaxTreeNode(tokens)
        wh = TokenWarehouse(tokens, tree, text=text)
    except Exception as e:
        print(f"Error parsing markdown: {e}")
        sys.exit(1)

    # Dump sections
    print(f"File: {path}")
    print(f"Lines: {wh.line_count}")
    print(f"Sections: {len(wh.sections)}")
    print()

    if not wh.sections:
        print("No headings found in document.")
        return

    print("Section Map:")
    print("=" * 60)
    print(wh.debug_dump_sections())
    print("=" * 60)

    # Additional statistics
    print()
    print("Statistics:")
    print(f"  Total sections: {len(wh.sections)}")
    print(f"  Heading levels: {sorted(set(lvl for _, _, _, lvl, _ in wh.sections))}")
    print(f"  Deepest nesting: L{max((lvl for _, _, _, lvl, _ in wh.sections), default=0)}")


if __name__ == "__main__":
    main()
