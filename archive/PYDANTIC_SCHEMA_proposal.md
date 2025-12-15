Here’s a draft src/doxstrux/markdown/output_models.py that matches the
  parser’s current output shape (dicts emitted by MarkdownParserCore.parse()
  and parse_markdown_file). It treats optional fields and conditional plugins
  (footnotes, encoding, source_path, embedding/quarantine flags) the way the code
  actually does today.

  from __future__ import annotations

  from typing import Annotated, Any, Literal

  from pydantic import BaseModel, ConfigDict, Field


  class DoxBaseModel(BaseModel):
      model_config = ConfigDict(extra="forbid")


  class SecurityWarning(DoxBaseModel):
      """Security warnings carry flexible payloads (scheme/url/size/etc)."""
      model_config = ConfigDict(extra="allow")

      type: str
      message: str | None = None
      line: int | None = None
      blocks: int | None = None
      inline: int | None = None
      scheme: str | None = None
      url: str | None = None
      size: int | None = None
      table_cells: int | None = None
      schemes: list[str] | None = None


  class SecurityStatistics(DoxBaseModel):
      frontmatter_at_bof: bool
      ragged_tables_count: int
      allowed_schemes: list[str]
      table_align_mismatches: int
      nested_headings_blocked: int
      has_html_block: bool
      has_html_inline: bool
      has_script: bool
      has_event_handlers: bool
      has_data_uri_images: bool
      confusables_present: bool
      nbsp_present: bool
      zwsp_present: bool
      path_traversal_pattern: bool
      link_schemes: dict[str, int]
      unicode_risk_score: int

      # Optional/conditional flags
      has_style_scriptless: bool | None = None
      has_meta_refresh: bool | None = None
      has_frame_like: bool | None = None
      disallowed_link_schemes: dict[str, int] | None = None
      has_bidi_controls: bool | None = None
      bidi_controls_present: bool | None = None
      has_confusables: bool | None = None
      mixed_scripts: bool | None = None
      invisible_chars: bool | None = None
      html_disallowed: bool | None = None
      raw_dangerous_schemes: bool | None = None
      suspected_prompt_injection: bool | None = None
      prompt_injection_in_images: bool | None = None
      prompt_injection_in_links: bool | None = None
      prompt_injection_in_code: bool | None = None
      prompt_injection_in_tables: bool | None = None
      footnote_injection: bool | None = None
      oversized_footnotes: bool | None = None
      has_csp_header: bool | None = None
      has_xframe_options: bool | None = None


  class SecuritySummary(DoxBaseModel):
      ragged_tables_count: int
      total_warnings: int
      has_dangerous_content: bool
      unicode_risk_score: int


  class Security(DoxBaseModel):
      warnings: list[SecurityWarning]
      statistics: SecurityStatistics
      summary: SecuritySummary
      profile_used: str | None = None
      rejected_plugins: list[str] | None = None
      link_disallowed_schemes_raw: bool | None = None

      # Prompt-injection/quarantine signals not in statistics
      prompt_injection_in_content: bool | None = None
      prompt_injection_in_footnotes: bool | None = None

      # Rarely set inside security (oversized data URIs)
      embedding_blocked: bool | None = None
      embedding_blocked_reason: str | None = None


  class Encoding(DoxBaseModel):
      detected: str
      confidence: float


  class Metadata(DoxBaseModel):
      total_lines: int
      total_chars: int
      has_sections: bool
      has_code: bool
      has_tables: bool
      has_lists: bool
      node_counts: dict[str, int]
      has_frontmatter: bool
      security: Security
      frontmatter: Any | None = None
      frontmatter_error: str | None = None
      security_policies_applied: list[str] | None = None

      # Added by parse_markdown_file
      encoding: Encoding | None = None
      source_path: str | None = None

      # Applied by _apply_security_policy
      embedding_blocked: bool | None = None
      embedding_block_reason: str | None = None
      quarantined: bool | None = None
      quarantine_reasons: list[str] | None = None


  class Content(DoxBaseModel):
      raw: str
      lines: list[str]


  class Section(DoxBaseModel):
      id: str
      level: int
      title: str
      slug: str
      start_line: int | None
      end_line: int | None
      start_char: int | None
      end_char: int | None
      parent_id: str | None
      child_ids: list[str]
      raw_content: str
      text_content: str


  class Paragraph(DoxBaseModel):
      id: str
      text: str
      start_line: int | None
      end_line: int | None
      section_id: str | None
      word_count: int
      has_links: bool
      has_emphasis: bool
      has_code: bool


  class BlockRef(DoxBaseModel):
      type: str
      start_line: int | None = None
      end_line: int | None = None


  class ListItem(DoxBaseModel):
      text: str | None = None
      children: list["ListItem"] = Field(default_factory=list)
      blocks: list[BlockRef] = Field(default_factory=list)


  class List(DoxBaseModel):
      id: str
      type: Literal["bullet", "ordered"]
      start_line: int | None
      end_line: int | None
      section_id: str | None
      items: list[ListItem]
      items_count: int


  class TasklistItem(DoxBaseModel):
      text: str | None = None
      checked: bool | None = None
      children: list["TasklistItem"] = Field(default_factory=list)
      blocks: list[BlockRef] = Field(default_factory=list)


  class Tasklist(DoxBaseModel):
      id: str
      type: Literal["bullet", "ordered"]
      start_line: int | None
      end_line: int | None
      section_id: str | None
      items: list[TasklistItem]
      items_count: int
      checked_count: int
      unchecked_count: int
      has_mixed_task_items: bool


  class Table(DoxBaseModel):
      id: str
      raw_content: str
      headers: list[str]
      rows: list[list[str]]
      align: list[str] | None
      start_line: int | None
      end_line: int | None
      section_id: str | None
      is_ragged: bool
      align_mismatch: bool
      malformed_lines: list[int]
      is_pure: bool
      table_valid_md: bool
      column_count: int
      row_count: int
      align_meta: dict[str, Any] | None = None
      is_ragged_meta: dict[str, Any] | None = None


  class CodeBlock(DoxBaseModel):
      id: str
      type: Literal["fenced", "indented"]
      language: str
      content: str
      start_line: int | None
      end_line: int | None
      section_id: str | None


  class Heading(DoxBaseModel):
      id: str
      level: int
      text: str
      line: int | None
      slug: str
      parent_heading_id: str | None
      start_char: int | None
      end_char: int | None


  class RegularLink(DoxBaseModel):
      text: str
      url: str
      line: int | None
      type: Literal["absolute", "relative", "anchor", "malformed"]
      scheme: str | None
      allowed: bool


  class ImageLink(DoxBaseModel):
      image_id: str
      text: str
      url: str
      src: str
      alt: str | None
      title: str | None
      line: int | None
      type: Literal["image"]
      image_kind: str
      format: str


  Link = Annotated[RegularLink | ImageLink, Field(discriminator="type")]


  class Image(DoxBaseModel):
      image_id: str
      src: str
      alt: str | None
      title: str | None
      line: int | None
      image_kind: str
      format: str
      has_alt: bool
      has_title: bool
      scheme: str | None
      allowed: bool


  class BlockquoteChildrenSummary(DoxBaseModel):
      lists: int
      tables: int
      code: int


  class Blockquote(DoxBaseModel):
      content: str
      start_line: int | None
      end_line: int | None
      section_id: str | None
      children_summary: BlockquoteChildrenSummary
      children_blocks: list[BlockRef]


  class MathBlock(DoxBaseModel):
      id: str
      kind: Literal["display", "fenced"]
      content: str
      start_line: int | None
      end_line: int | None


  class MathInline(DoxBaseModel):
      id: str
      content: str
      line: int | None


  class Math(DoxBaseModel):
      blocks: list[MathBlock]
      inline: list[MathInline]


  class FootnoteNestedStructure(DoxBaseModel):
      type: str
      start_line: int | None
      end_line: int | None


  class FootnoteDefinition(DoxBaseModel):
      label: str
      id: str | int
      start_line: int | None
      end_line: int | None
      content: str
      byte_length: int
      nested_structures: list[FootnoteNestedStructure]
      section_id: str | None


  class FootnoteReference(DoxBaseModel):
      label: str
      id: str | int
      line: int | None
      section_id: str | None


  class Footnotes(DoxBaseModel):
      definitions: list[FootnoteDefinition]
      references: list[FootnoteReference]


  class HtmlBlock(DoxBaseModel):
      content: str
      raw_content: str
      start_line: int | None
      end_line: int | None
      inline: Literal[False]
      allowed: bool
      section_id: str | None
      tag_hints: list[str]


  class HtmlInline(DoxBaseModel):
      content: str
      line: int | None
      inline: Literal[True]
      allowed: bool
      section_id: str | None
      tag_hints: list[str]


  class Structure(DoxBaseModel):
      sections: list[Section]
      paragraphs: list[Paragraph]
      lists: list[List]
      tables: list[Table]
      code_blocks: list[CodeBlock]
      headings: list[Heading]
      links: list[Link]
      images: list[Image]
      blockquotes: list[Blockquote]
      frontmatter: Any | None
      tasklists: list[Tasklist]
      math: Math
      footnotes: Footnotes | None = None  # Only present when footnotes plugin is
  enabled
      html_blocks: list[HtmlBlock]
      html_inline: list[HtmlInline]


  class MappingCodeBlock(DoxBaseModel):
      start_line: int
      end_line: int
      language: str | None = None


  class Mappings(DoxBaseModel):
      line_to_type: dict[str, str]
      line_to_section: dict[str, str]
      prose_lines: list[int]
      code_lines: list[int]
      code_blocks: list[MappingCodeBlock]


  class ParserOutput(DoxBaseModel):
      metadata: Metadata
      content: Content
      structure: Structure
      mappings: Mappings


  # Resolve forward references for recursive items
  ListItem.model_rebuild()
  TasklistItem.model_rebuild()
  ParserOutput.model_rebuild()

  Notes:

  - footnotes is optional because the strict profile omits that key (plugin
    disabled).
  - Embedding/quarantine flags live on metadata (set by _apply_security_policy),
    but oversized data URIs can also set embedding_blocked inside metadata.security;
    both are modeled.
  - Warnings are extra="allow" because warning payload keys vary (scheme, url, size,
    etc.).
  - encoding/source_path are optional; they’re only added by parse_markdown_file.

  Next steps: add pydantic>=2 to pyproject.toml, drop this file into src/doxstrux/
  markdown/output_models.py, then add a small schema-conformance test to ensure
  ParserOutput.model_validate() accepts real parser outputs (including strict
  profile without footnotes).
