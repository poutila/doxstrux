#!/usr/bin/env python3
"""
Test if we extract math/LaTeX content
"""

from src.docpipe.loaders.markdown_parser_core import MarkdownParserCore


def test_math_extraction():
    """Test if math/LaTeX is extracted."""

    content = """# Math Document

Inline math $E=mc^2$ in a paragraph.

Display math:
$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

Another inline $\\alpha + \\beta = \\gamma$ formula.

Multi-line display:
$$
\\begin{align}
x &= \\sin(\\theta) \\\\
y &= \\cos(\\theta)
\\end{align}
$$

Code block comparison:
```python
# Not math
x = 2
```
"""

    parser = MarkdownParserCore(content)
    result = parser.parse()

    print("🔬 Math/LaTeX Extraction Test")
    print("=" * 50)

    # Check paragraphs for inline math
    print("\n📝 Paragraphs:")
    for i, para in enumerate(result["structure"]["paragraphs"]):
        print(f"{i}: {para['text'][:50]}...")
        if "$" in para["text"]:
            print("   ⚠️ Contains $ (math delimiters)")

    # Check code blocks
    print("\n📦 Code Blocks:")
    for block in result["structure"]["code_blocks"]:
        print(f"Type: {block['type']}, Language: {block.get('language', 'none')}")
        print(f"Content preview: {block['content'][:50]}...")
        if "$$" in block["content"] or "\\int" in block["content"]:
            print("   ⚠️ Might be math content")

    # Check if math is in any special structure
    print("\n🔍 Looking for math in structure keys:")
    for key in result["structure"].keys():
        print(f"  - {key}")
        if "math" in key.lower() or "equation" in key.lower() or "latex" in key.lower():
            print("    ✅ Found math-related key!")

    # Check raw content preservation
    print("\n📄 Raw Content Check:")
    raw = result["content"]["raw"]
    inline_math_count = raw.count("$") - raw.count("$$") * 2
    display_math_count = raw.count("$$") // 2
    print(f"Inline math delimiters ($): ~{inline_math_count // 2} instances")
    print(f"Display math blocks ($$): {display_math_count} blocks")

    # Conclusion
    print("\n🎯 Conclusion:")
    math_extracted = False

    # Check if we have any indication of special math handling
    if any(
        "math" in key.lower() or "equation" in key.lower() for key in result["structure"].keys()
    ):
        print("✅ Math is extracted as a special structure")
        math_extracted = True
    else:
        print("❌ Math is NOT specially extracted")
        print("   - Inline math ($...$) is kept in paragraph text")
        print("   - Display math ($$...$$) might be treated as paragraphs or code")
        print("   - No semantic math extraction for AI/ML use cases")

    return math_extracted


if __name__ == "__main__":
    test_math_extraction()
