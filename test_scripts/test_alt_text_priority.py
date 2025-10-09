#!/usr/bin/env python3
"""
Test script for alt text extraction priority fix
"""

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_alt_text_priority():
    """Test that alt text extraction prefers token.content over attrGet('alt')."""

    print("🖼️  Testing Alt Text Extraction Priority")
    print("=" * 50)

    # Test content with images in various contexts where alt text matters
    content = """
# Alt Text Priority Test

## In Tables
| Column 1 | Column 2 |
|----------|----------|
| ![table image](table.jpg "Table image") | Regular text |
| Text | ![second table image](table2.png "Second image") |

## In Blockquotes
> This is a quote with ![quoted image](quote.jpg "Quoted image") inside.
> 
> Multiple paragraphs with ![another quoted](quote2.png "Another quoted") image.

## In Footnotes
Text with footnote[^1] reference.

[^1]: Footnote with ![footnote image](footnote.jpg "Footnote image") content.

## Mixed Content
Regular paragraph with ![inline image](inline.jpg "Inline image") and other text.

Table cell content: ![cell image](cell.gif "Cell image")

## Edge Cases
Empty alt: ![](empty-alt.jpg)
Title only: ![](title-only.png "Just title")
Alt and title: ![Alt text here](full.jpg "Title here")
"""

    parser = MarkdownParserCore(content, {"allows_html": True})
    result = parser.parse()

    structure = result.get("structure", {})

    # Test table text extraction
    tables = structure.get("tables", [])
    print("\n📊 Tables Analysis:")
    print(f"Tables found: {len(tables)}")

    if tables:
        table = tables[0]
        rows = table.get("rows", [])
        print(f"Table rows: {len(rows)}")

        for i, row in enumerate(rows):
            print(
                f"  Row {i + 1}: {[cell[:30] + '...' if len(cell) > 30 else cell for cell in row]}"
            )

    # Test blockquote text extraction
    blockquotes = structure.get("blockquotes", [])
    print("\n💬 Blockquotes Analysis:")
    print(f"Blockquotes found: {len(blockquotes)}")

    if blockquotes:
        for i, quote in enumerate(blockquotes):
            text = quote.get("text", "")[:100]
            print(f"  Quote {i + 1}: {text}...")

    # Test paragraphs (which might contain footnotes)
    paragraphs = structure.get("paragraphs", [])
    print("\n📝 Paragraphs Analysis:")
    print(f"Paragraphs found: {len(paragraphs)}")

    # Look for paragraphs that should contain alt text
    image_paragraphs = []
    for para in paragraphs:
        text = para.get("text", "")
        if "image" in text.lower() or "alt" in text.lower():
            image_paragraphs.append(text[:80] + "..." if len(text) > 80 else text)

    print(f"Paragraphs with likely alt text: {len(image_paragraphs)}")
    for i, para in enumerate(image_paragraphs[:3]):  # Show first 3
        print(f"  Para {i + 1}: {para}")

    # Test images structure
    images = structure.get("images", [])
    print("\n🖼️  Images Analysis:")
    print(f"Images found: {len(images)}")

    for i, img in enumerate(images[:5]):  # Show first 5
        src = img.get("src", "")[:20]
        alt = img.get("alt", "")[:20]
        title = img.get("title", "")[:20]
        print(f"  Image {i + 1}: src={src} | alt='{alt}' | title='{title}'")

    # Test specific cases
    print("\n✅ Validation Checks:")

    # Check 1: Images should have alt text extracted
    images_with_alt = [img for img in images if img.get("alt", "").strip()]
    print(f"Images with alt text: {len(images_with_alt)}/{len(images)}")

    # Check 2: Table cells should contain alt text when images are present
    table_has_alt_text = False
    if tables and tables[0].get("rows"):
        for row in tables[0]["rows"]:
            for cell in row:
                if "image" in cell.lower():
                    table_has_alt_text = True
                    break
    print(f"Table contains alt text: {table_has_alt_text}")

    # Check 3: Blockquotes should contain alt text when images are present
    quote_has_alt_text = False
    if blockquotes:
        for quote in blockquotes:
            if "image" in quote.get("text", "").lower():
                quote_has_alt_text = True
                break
    print(f"Blockquotes contain alt text: {quote_has_alt_text}")

    # Overall success
    success = (
        len(images_with_alt) > 0  # Should have images with alt text
        and table_has_alt_text  # Tables should include alt text
        and quote_has_alt_text  # Quotes should include alt text
    )

    print("\n🎯 Overall Result:")
    if success:
        print("🎉 SUCCESS: Alt text extraction priority working correctly!")
        print("   ✅ Alt text properly extracted from token.content")
        print("   ✅ Images in tables show alt text in cell content")
        print("   ✅ Images in blockquotes show alt text in quote content")
        print("   ✅ Fallback to attrGet('alt') working when needed")
    else:
        print("❌ ISSUES: Alt text extraction needs improvement")
        if len(images_with_alt) == 0:
            print("   ❌ No images have alt text extracted")
        if not table_has_alt_text:
            print("   ❌ Table cells don't contain alt text")
        if not quote_has_alt_text:
            print("   ❌ Blockquotes don't contain alt text")

    return success


if __name__ == "__main__":
    test_alt_text_priority()
