#!/usr/bin/env python3
"""
Test script for YAML frontmatter handling.
"""

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_yaml_frontmatter():
    """Test YAML frontmatter extraction and handling."""

    print("🔧 Testing YAML Frontmatter Handling")
    print("=" * 50)

    # Test content similar to the failing test case
    content = """---
title: "FM Stress 01"
id: fm_stress_01
md_flavor: commonmark
allows_html: false
note: front-matter-conflict
---

---
title: dup fm
---
Content
---
other: block
---
"""

    print("📄 Test Content:")
    print(content)
    print()

    parser = MarkdownParserCore(content, {"allows_html": False})
    result = parser.parse()

    structure = result.get("structure", {})
    metadata = result.get("metadata", {})

    print("📊 Analysis Results:")

    # Check frontmatter extraction
    frontmatter = metadata.get("frontmatter")
    has_frontmatter = metadata.get("has_frontmatter", False)

    print(f"Has frontmatter: {has_frontmatter}")
    if frontmatter:
        print(f"Frontmatter keys: {list(frontmatter.keys())}")
        print(f"Frontmatter content: {frontmatter}")
    else:
        print("No frontmatter detected")

    # Check content cleaning
    print(f"\nOriginal content length: {len(parser.original_content)}")
    print(f"Cleaned content length: {len(parser.content)}")
    print("Content after YAML extraction:")
    print(repr(parser.content[:100] + "..." if len(parser.content) > 100 else parser.content))

    # Check hrule counting
    total_hrules = parser.get_total_hrule_count()
    yaml_hrules = parser.yaml_hrule_count

    print("\nHrule Analysis:")
    print(f"YAML delimiter hrules: {yaml_hrules}")
    print(f"Total hrules: {total_hrules}")

    # Check headings
    headings = structure.get("headings", [])
    print(f"\nHeadings detected: {len(headings)}")
    for i, heading in enumerate(headings, 1):
        print(f"  {i}. '{heading.get('text', '')}' (level {heading.get('level', 'unknown')})")

    # Expected vs Actual comparison
    print("\n✅ Validation against ground truth:")
    expected_headings = 0
    expected_hrules = 6
    actual_headings = len(headings)
    actual_hrules = total_hrules

    headings_match = expected_headings == actual_headings
    hrules_match = expected_hrules == actual_hrules

    print(
        f"Headings: expected {expected_headings}, got {actual_headings} {'✅' if headings_match else '❌'}"
    )
    print(
        f"Hrules: expected {expected_hrules}, got {actual_hrules} {'✅' if hrules_match else '❌'}"
    )

    overall_success = headings_match and hrules_match

    print("\n🎯 Overall Result:")
    if overall_success:
        print("🎉 SUCCESS: YAML frontmatter handling works correctly!")
        print("   ✅ YAML content excluded from markdown parsing")
        print("   ✅ Correct hrule count including YAML delimiters")
        print("   ✅ No false headings from YAML keys")
    else:
        print("❌ ISSUES: YAML frontmatter handling needs adjustment")
        if not headings_match:
            print(
                f"   ❌ Heading count mismatch: expected {expected_headings}, got {actual_headings}"
            )
        if not hrules_match:
            print(f"   ❌ Hrule count mismatch: expected {expected_hrules}, got {actual_hrules}")

    return overall_success


if __name__ == "__main__":
    test_yaml_frontmatter()
