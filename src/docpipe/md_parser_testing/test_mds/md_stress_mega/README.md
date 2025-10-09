# Heading Creepage & Missing-Heading Suite

Focus: ensure headings are recognized **only** when valid, and never creep from code, tables, YAML, inline code, or mid-paragraph.
Each `.json` lists the expected heading line numbers (0-based, counting the full file with two-line test prefix).

## Cases
- 00_no_headings: Document with no headings anywhere.
- 01_hash_in_code_fence: Hashes inside fences must not become headings.
- 02_indented_four_spaces: ATX markers indented ≥4 are code blocks.
- 03_indented_tab: Tab-indented lines are code; not headings.
- 04_escaped_hash: Escaped hash should be literal, not a heading.
- 05_missing_space_after_hash: No space after #: not a heading under CommonMark.
- 06_nbsp_after_hash: Non-breaking space after # is not a space; not a heading.
- 07_fullwidth_hash: Fullwidth ＃ is not an ATX marker.
- 08_hash_in_table_cell: Hash inside table cells must not become headings.
- 09_hash_in_inline_code: Inline code containing # at line start must not create headings.
- 10_hash_mid_paragraph: A # appearing mid-line is not a heading.
- 11_mixed_legit_and_traps: Has real headings plus traps nearby.
- 12_heading_in_blockquote: Heading inside a blockquote is still a heading.
- 13_heading_in_list_item: Heading inside list item is legit.
- 14_setext_valid: Setext headings should parse (H1 '=' and H2 '-').
- 15_setext_table_conflict: Underlines with pipes form a table, not setext.
- 16_unclosed_fence_followed_by_hashes: If a fence remains open, following lines are code; no headings should leak.
- 17_three_space_indent_valid: Headings indented by up to 3 spaces remain headings.
- 18_four_space_indent_invalid: Four-space indent converts to code; not heading.
- 19_trailing_hashes_legit: ATX headings may have closing hashes, separated by space.
- 20_heading_is_only_link: A heading may consist solely of a link.
- 21_whitespace_only_after_hash: Only whitespace after #: invalid heading.
- 22_html_h1_not_markdown: HTML-level heading shouldn't be counted as markdown heading.
- 23_yaml_block_with_hashes: Hashes inside YAML frontmatter must not become markdown headings.
- 24_hash_not_at_bol: Hash not at BOL should not start a heading.
- 25_mixed_nbsp_and_spaces: NBSP followed by spaces after # should still be invalid (no immediate space).
- 26_setext_one_dash_valid: One dash underline is still a valid H2 setext.
- 27_heading_then_continuation_text: Heading followed by plain line; continuation isn't part of heading.
- 28_too_many_hashes: More than 6 # at start is invalid.
- 29_list_text_hash_at_start_of_item: List item line that starts with '# ' should still create a heading (valid); this catches parsers that miss it.
