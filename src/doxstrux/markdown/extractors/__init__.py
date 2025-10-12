"""
Doxstrux Extractors Package

Feature-specific extraction modules for markdown elements.

Each extractor focuses on a single markdown feature:
- sections: Heading hierarchy and section structure
- paragraphs: Paragraph extraction
- lists: Ordered and unordered lists
- codeblocks: Fenced and indented code blocks
- tables: Table structure and data
- media: Images and other media
- links: Link extraction and validation
- footnotes: Footnote references
- blockquotes: Blockquote extraction
- html: HTML block and inline detection

All extractors follow the pattern:
    extract(token, context) -> dict
"""
