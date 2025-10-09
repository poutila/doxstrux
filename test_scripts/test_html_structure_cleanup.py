#!/usr/bin/env python3
"""
Test script for HTML structure naming cleanup
"""

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_html_structure_cleanup():
    """Test that HTML structure is now cleanly separated into html_blocks and html_inline."""

    print("🏗️  Testing HTML Structure Cleanup")
    print("=" * 50)

    # Test content with both block and inline HTML
    content = """
# HTML Structure Test

This is a paragraph with <span class="highlight">inline HTML</span> content.

<div class="container">
    <p>This is block HTML content</p>
    <p>Multiple block elements</p>
</div>

Another paragraph with <em>inline emphasis</em> and <strong>strong text</strong>.

<blockquote>
Another block HTML element
</blockquote>

Final paragraph with <code>inline code HTML</code> and <a href="#">inline link</a>.
"""

    parser = MarkdownParserCore(content, {"allows_html": True})
    result = parser.parse()

    structure = result.get("structure", {})

    print("\n📊 HTML Structure Analysis:")

    # Check that we have separate structures
    has_html_blocks = "html_blocks" in structure
    has_html_inline = "html_inline" in structure

    print(f"Has html_blocks key: {has_html_blocks}")
    print(f"Has html_inline key: {has_html_inline}")

    if has_html_blocks:
        html_blocks = structure["html_blocks"]
        print(f"html_blocks type: {type(html_blocks)}")
        print(f"html_blocks count: {len(html_blocks)}")

        print("\n🧱 HTML Blocks:")
        for i, block in enumerate(html_blocks, 1):
            content_preview = block.get("content", "")[:50].replace("\n", "\\n")
            inline_flag = block.get("inline", "Unknown")
            print(f"  {i}. Content: {content_preview}... | Inline: {inline_flag}")

    if has_html_inline:
        html_inline = structure["html_inline"]
        print(f"\nhtml_inline type: {type(html_inline)}")
        print(f"html_inline count: {len(html_inline)}")

        print("\n🏷️  HTML Inline:")
        for i, inline in enumerate(html_inline, 1):
            content_preview = inline.get("content", "")[:30]
            inline_flag = inline.get("inline", "Unknown")
            print(f"  {i}. Content: {content_preview} | Inline: {inline_flag}")

    # Test the consumer experience
    print("\n✅ Consumer Experience Test:")

    # Before: Required conditional logic
    print("OLD WAY (would have required):")
    print("  html = structure.get('html_blocks', {})")
    print("  if isinstance(html, dict):")
    print("    blocks = html.get('blocks', [])")
    print("    inline = html.get('inline', [])")
    print("  else:")
    print("    blocks = html if html else []")
    print("    inline = []")

    # Now: Direct access
    print("\nNEW WAY (clean and simple):")
    print("  html_blocks = structure.get('html_blocks', [])")
    print("  html_inline = structure.get('html_inline', [])")

    # Validate the new approach works
    html_blocks = structure.get("html_blocks", [])
    html_inline = structure.get("html_inline", [])

    print("\n📈 Results:")
    print(f"  Block HTML elements: {len(html_blocks)}")
    print(f"  Inline HTML elements: {len(html_inline)}")

    # Validation checks
    print("\n✅ Validation Checks:")

    # Check 1: Both structures should exist when HTML is allowed
    structures_exist = has_html_blocks and has_html_inline
    print(f"Both structures exist: {structures_exist}")

    # Check 2: Structures should be lists, not dicts
    blocks_is_list = isinstance(html_blocks, list)
    inline_is_list = isinstance(html_inline, list)
    print(f"html_blocks is list: {blocks_is_list}")
    print(f"html_inline is list: {inline_is_list}")

    # Check 3: Should have detected HTML content
    has_content = len(html_blocks) > 0 or len(html_inline) > 0
    print(f"Has HTML content: {has_content}")

    # Check 4: Inline elements should be marked as inline
    inline_properly_marked = all(elem.get("inline", False) for elem in html_inline)
    print(f"Inline elements properly marked: {inline_properly_marked}")

    # Check 5: Block elements should be marked as not inline
    blocks_properly_marked = all(not elem.get("inline", True) for elem in html_blocks)
    print(f"Block elements properly marked: {blocks_properly_marked}")

    # Overall success
    success = (
        structures_exist
        and blocks_is_list
        and inline_is_list
        and has_content
        and inline_properly_marked
        and blocks_properly_marked
    )

    print("\n🎯 Overall Result:")
    if success:
        print("🎉 SUCCESS: HTML structure cleanup working perfectly!")
        print("   ✅ Clean separation into html_blocks and html_inline")
        print("   ✅ No more conditional logic needed for consumers")
        print("   ✅ Direct list access instead of nested dict structure")
        print("   ✅ Clear semantics: html_blocks = blocks, html_inline = inline")
        print("   ✅ Reduced consumer confusion and code complexity")
    else:
        print("❌ ISSUES: HTML structure cleanup needs improvement")
        if not structures_exist:
            print("   ❌ Missing html_blocks or html_inline structures")
        if not (blocks_is_list and inline_is_list):
            print("   ❌ Structures are not lists as expected")
        if not has_content:
            print("   ❌ No HTML content detected")
        if not (inline_properly_marked and blocks_properly_marked):
            print("   ❌ Elements not properly marked as inline/block")

    return success


if __name__ == "__main__":
    test_html_structure_cleanup()
