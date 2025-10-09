#!/usr/bin/env python3
"""
Test script for enhanced parser quality metrics
"""

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def extract_enhanced_metrics(result, parser=None):
    """Extract enhanced feature counts including quality metrics."""
    counts = {}
    structure = result.get("structure", {})

    # Basic structures
    counts["headings"] = len(structure.get("headings", []))
    counts["blockquotes"] = len(structure.get("blockquotes", []))
    counts["tables"] = len(structure.get("tables", []))
    counts["links"] = len([l for l in structure.get("links", []) if l.get("type") != "image"])
    counts["images"] = len(structure.get("images", []))

    # Enhanced HTML metrics - now in separate structures
    html_blocks = structure.get("html_blocks", [])
    html_inline = structure.get("html_inline", [])
    counts["html_blocks"] = len(html_blocks)
    counts["html_inline"] = len(html_inline)

    # Enhanced link classification
    links = structure.get("links", [])
    counts["file_links"] = len([l for l in links if l.get("url", "").startswith("file:")])
    counts["mailto_links"] = len([l for l in links if l.get("url", "").startswith("mailto:")])
    counts["autolinks"] = len(
        [
            l
            for l in links
            if l.get("url", "").startswith(("http://", "https://"))
            and l.get("text") == l.get("url")
        ]
    )

    # Enhanced footnote metrics
    footnotes = structure.get("footnotes", {})
    if isinstance(footnotes, dict):
        counts["footnotes"] = len(footnotes.get("definitions", []))
        # Check for duplicate labels
        definitions = footnotes.get("definitions", [])
        labels = [fn.get("label", "") for fn in definitions if fn.get("label")]
        unique_labels = set(labels)
        counts["dup_footnote_labels"] = len(labels) - len(unique_labels)
    else:
        counts["footnotes"] = 0
        counts["dup_footnote_labels"] = 0

    # Table quality validation
    tables = structure.get("tables", [])
    counts["table_align_mismatches"] = 0
    counts["table_ragged_rows"] = 0

    for table in tables:
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        align = table.get("align", [])

        # Check alignment specification vs actual columns
        header_count = len(headers)
        align_count = len(align)
        if header_count > 0 and align_count > 0 and header_count != align_count:
            counts["table_align_mismatches"] += 1

        # Check row width consistency
        if rows:
            expected_width = len(headers) if headers else len(rows[0]) if rows[0] else 0
            if expected_width > 0:
                row_widths = [len(row) for row in rows if isinstance(row, list)]
                mismatched_rows = [w for w in row_widths if w != expected_width]
                if mismatched_rows:
                    counts["table_ragged_rows"] += len(mismatched_rows)

    return counts


def test_enhanced_metrics():
    """Test the enhanced quality metrics on sample content."""

    print("🔬 Testing Enhanced Parser Quality Metrics")
    print("=" * 50)

    # Test 1: Table quality validation
    print("\n📊 Test 1: Table Quality Validation")
    table_content = """
| Name | Age | City |
|------|:---:|-----:|
| John | 25 | NYC |
| Jane | 30 | LA |
| Bob | 35 |
| Alice | 28 | Chicago | Extra |
"""

    parser = MarkdownParserCore(table_content, {"allows_html": True})
    result = parser.parse()
    metrics = extract_enhanced_metrics(result, parser)

    print(f"Tables detected: {metrics['tables']}")
    print(f"Alignment mismatches: {metrics['table_align_mismatches']}")
    print(f"Ragged rows: {metrics['table_ragged_rows']}")

    # Test 2: HTML inline detection
    print("\n🏷️  Test 2: HTML Inline Detection")
    html_content = """
This paragraph has <span class="highlight">inline HTML</span> and <em>emphasis</em>.

<div class="container">
Block HTML content
</div>

More text with <a href="http://example.com">inline links</a>.
"""

    parser2 = MarkdownParserCore(html_content, {"allows_html": True})
    result2 = parser2.parse()
    metrics2 = extract_enhanced_metrics(result2, parser2)

    print(f"HTML blocks: {metrics2['html_blocks']}")
    print(f"HTML inline elements: {metrics2['html_inline']}")

    # Test 3: Link scheme classification
    print("\n🔗 Test 3: Link Scheme Classification")
    link_content = """
Here are various links:
- [Web link](https://example.com)
- [Email](mailto:test@example.com)
- [File link](file:///path/to/file.txt)
- [Relative link](./readme.md)
- [Auto link](https://autolink.com)
"""

    parser3 = MarkdownParserCore(link_content, {"allows_html": True})
    result3 = parser3.parse()
    metrics3 = extract_enhanced_metrics(result3, parser3)

    print(f"Total links: {metrics3['links']}")
    print(f"File links: {metrics3['file_links']}")
    print(f"Mailto links: {metrics3['mailto_links']}")
    print(f"Autolinks: {metrics3['autolinks']}")

    # Test 4: Footnote deduplication
    print("\n📝 Test 4: Footnote Deduplication")
    footnote_content = """
Text with footnote[^1] and another[^2] and duplicate[^1].

[^1]: First definition
[^2]: Second definition  
[^1]: Duplicate definition (should be ignored)
"""

    parser4 = MarkdownParserCore(
        footnote_content, {"allows_html": True, "external_plugins": ["footnote"]}
    )
    result4 = parser4.parse()
    metrics4 = extract_enhanced_metrics(result4, parser4)

    print(f"Footnotes: {metrics4['footnotes']}")
    print(f"Duplicate labels: {metrics4['dup_footnote_labels']}")

    print("\n✅ Enhanced metrics testing complete!")
    return True


if __name__ == "__main__":
    test_enhanced_metrics()
