# Security Hardening Test Suite

Covers: (1) BOF-only YAML frontmatter, (2) Heading creepage prevention,
(3) Table ragged detection, (4) Security metadata reporting.

## Index
- fm_invalid_in_code.md ⇄ fm_invalid_in_code.json — frontmatter
- fm_invalid_inline.md ⇄ fm_invalid_inline.json — frontmatter
- fm_invalid_json.md ⇄ fm_invalid_json.json — frontmatter
- fm_invalid_nbsp_fence.md ⇄ fm_invalid_nbsp_fence.json — frontmatter
- fm_invalid_not_bof.md ⇄ fm_invalid_not_bof.json — frontmatter
- fm_invalid_toml.md ⇄ fm_invalid_toml.json — frontmatter
- fm_invalid_trailing_spaces.md ⇄ fm_invalid_trailing_spaces.json — frontmatter
- fm_invalid_unclosed.md ⇄ fm_invalid_unclosed.json — frontmatter
- fm_valid_bom.md ⇄ fm_valid_bom.json — frontmatter
- fm_valid_ellipsis_close.md ⇄ fm_valid_ellipsis_close.json — frontmatter
- fm_valid_folded.md ⇄ fm_valid_folded.json — frontmatter
- fm_valid_simple.md ⇄ fm_valid_simple.json — frontmatter
- hdg_code_fence.md ⇄ hdg_code_fence.json — heading
- hdg_escaped_hash.md ⇄ hdg_escaped_hash.json — heading
- hdg_fullwidth_hash.md ⇄ hdg_fullwidth_hash.json — heading
- hdg_in_blockquote.md ⇄ hdg_in_blockquote.json — heading
- hdg_in_list_item.md ⇄ hdg_in_list_item.json — heading
- hdg_list_cont_4sp.md ⇄ hdg_list_cont_4sp.json — heading
- hdg_nbsp_after_hash.md ⇄ hdg_nbsp_after_hash.json — heading
- hdg_no_space.md ⇄ hdg_no_space.json — heading
- hdg_setext_valid.md ⇄ hdg_setext_valid.json — heading
- hdg_three_space_indent.md ⇄ hdg_three_space_indent.json — heading
- hdg_trailing_hashes.md ⇄ hdg_trailing_hashes.json — heading
- hdg_unclosed_fence_then_hash.md ⇄ hdg_unclosed_fence_then_hash.json — heading
- sec_confusables.md ⇄ sec_confusables.json — security
- sec_data_uri_image.md ⇄ sec_data_uri_image.json — security
- sec_footnote_injection.md ⇄ sec_footnote_injection.json — security
- sec_html_comment.md ⇄ sec_html_comment.json — security
- sec_html_inline.md ⇄ sec_html_inline.json — security
- sec_html_script.md ⇄ sec_html_script.json — security
- sec_img_onerror.md ⇄ sec_img_onerror.json — security
- sec_kitchen_sink.md ⇄ sec_kitchen_sink.json — security
- sec_link_schemes.md ⇄ sec_link_schemes.json — security
- sec_link_wrapped_image.md ⇄ sec_link_wrapped_image.json — security
- sec_prompt_injection.md ⇄ sec_prompt_injection.json — security
- sec_relative_paths.md ⇄ sec_relative_paths.json — security
- tbl_align_mismatch.md ⇄ tbl_align_mismatch.json — table
- tbl_align_mismatch_bad.md ⇄ tbl_align_mismatch_bad.json — table
- tbl_clean_2x2.md ⇄ tbl_clean_2x2.json — table
- tbl_escaped_pipes_rect.md ⇄ tbl_escaped_pipes_rect.json — table
- tbl_in_blockquote.md ⇄ tbl_in_blockquote.json — table
- tbl_in_code_fence.md ⇄ tbl_in_code_fence.json — table
- tbl_large_rect.md ⇄ tbl_large_rect.json — table
- tbl_loose_pipes.md ⇄ tbl_loose_pipes.json — table
- tbl_missing_header_sep.md ⇄ tbl_missing_header_sep.json — table
- tbl_ragged_missing_cells.md ⇄ tbl_ragged_missing_cells.json — table
- tbl_ragged_rows.md ⇄ tbl_ragged_rows.json — table
- tbl_trailing_pipes_rect.md ⇄ tbl_trailing_pipes_rect.json — table
