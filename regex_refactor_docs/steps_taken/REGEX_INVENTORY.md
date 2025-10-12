# Regex Inventory for Zero-Regex Refactoring

**Generated**: 2025-10-12

**Source**: `src/docpipe/markdown_parser_core.py`

**Total Patterns**: 41

---

## Summary by Phase

| Phase | Count | Description |
|-------|-------|-------------|
| 1 | 1 | Fence/indented code detection... |
| 2 | 12 | Slug generation/text normalization... |
| 3 | 4 | Link/image extraction... |
| 4 | 13 | HTML detection/sanitization... |
| 5 | 1 | Table structure detection... |
| 6 (RETAINED) | 10 | Security validation (schemes,... |

**Total**: 41 patterns

**Note**: All patterns have been manually categorized. Phase 6 patterns are security-critical and will be RETAINED (not replaced with tokens).

---

## Phase 1

**Count**: 1

| Line | Context | Pattern | Purpose | Replacement Strategy |
|------|---------|---------|---------|---------------------|
| 3583 | `_strip_markdown` | ````[^`]*```` | Fence/indented code detection | Token-based: Check token.type == 'fence' or 'code_ |

## Phase 2

**Count**: 12

| Line | Context | Pattern | Purpose | Replacement Strategy |
|------|---------|---------|---------|---------------------|
| 3537 | `_slugify_base` | `[\s/]+` | Slug generation/text normalization | Token-based: Use token.content directly, normalize |
| 3539 | `_slugify_base` | `[^\w-]` | Slug generation/text normalization | Token-based: Use token.content directly, normalize |
| 3541 | `_slugify_base` | `-+` | Slug generation/text normalization | Token-based: Use token.content directly, normalize |
| 3553 | `_slugify` | `[\s/]+` | Slug generation/text normalization | Token-based: Use token.content directly, normalize |
| 3555 | `_slugify` | `[^\w-]` | Slug generation/text normalization | Token-based: Use token.content directly, normalize |
| 3557 | `_slugify` | `-+` | Slug generation/text normalization | Token-based: Use token.content directly, normalize |
| 3574 | `_strip_markdown` | `^#+\s+` | Slug generation/text normalization | Token-based: Use token.content directly, normalize |
| 3576 | `_strip_markdown` | `\*\*([^*]+)\*\*` | Inline formatting (bold/italic/code) | Token-based: Check token.type == 'strong', 'em', ' |
| 3577 | `_strip_markdown` | `\*([^*]+)\*` | Inline formatting (bold/italic/code) | Token-based: Check token.type == 'strong', 'em', ' |
| 3578 | `_strip_markdown` | `__([^_]+)__` | Inline formatting (bold/italic/code) | Token-based: Check token.type == 'strong', 'em', ' |
| 3579 | `_strip_markdown` | `_([^_]+)_` | Inline formatting (bold/italic/code) | Token-based: Check token.type == 'strong', 'em', ' |
| 3584 | `_strip_markdown` | ``([^`]+)`` | Inline formatting (bold/italic/code) | Token-based: Check token.type == 'strong', 'em', ' |

## Phase 3

**Count**: 2 (COMPLETE - 2 removed via sanitize() deprecation, 1 already removed in Phase 2, 1 moved to Phase 6)

**Status**: ✅ COMPLETE (2025-10-12)

| Line | Context | Pattern | Purpose | Replacement Strategy |
|------|---------|---------|---------|---------------------|
| 1070 | `sanitize` (deprecated) | `(?<!\!)\[([^\]]+)\]\(([^)]+)\)` | Link extraction | **REMOVED**: sanitize() deprecated, fail-closed validation via _apply_security_policy() |
| 1097 | `sanitize` (deprecated) | `!\[([^\]]*)\]\(([^)]+)\)` | Image extraction | **REMOVED**: sanitize() deprecated, fail-closed validation via _apply_security_policy() |
| 3581 | `_strip_markdown` | `\[([^\]]+)\]\([^)]+\)` | Link removal | **REMOVED in Phase 2**: Replaced with token-based plaintext extraction |
| 3344 | `_check_path_traversal` | `^[a-z]:[/\\]` | Windows drive detection (security) | **MOVED to Phase 6**: Security-critical string validation (retained) |

**Implementation**: Deprecated `sanitize()` method to non-mutating wrapper. Validation now uses `_apply_security_policy()` which already handles link/image filtering via tokens. Returns `embedding_blocked` flag instead of mutated text.

## Phase 4

**Count**: 4 (COMPLETE - 4 removed, 9 retained as fallbacks/utilities/precompiled)

**Status**: ✅ COMPLETE (2025-10-12)

| Line | Context | Pattern | Purpose | Replacement Strategy |
|------|---------|---------|---------|---------------------|
| 1148-1149 | `_generate_security_metadata` | `<(div\|span\|script...)[\s>]` | HTML block detection | **REMOVED**: Replaced with token-based detection using `structure["html_blocks"]` |
| 1152 | `_generate_security_metadata` | `<(a\|img\|em...)[\s>]` | HTML inline detection | **REMOVED**: Replaced with token-based detection using `structure["html_inline"]` |
| 1156 | `_generate_security_metadata` | `<script[\s>]` | Script detection | **REMOVED**: Replaced with token-based content inspection |
| 1163-1164 | `_generate_security_metadata` | `\bon(load\|error...)\\s*=` | Event handler detection | **REMOVED**: Replaced with token-based content inspection |
| 1023, 1025, 1029, 1031, 1035 | `sanitize` (deprecated) | Various HTML patterns | HTML detection/removal | **ALREADY HANDLED**: Deprecated in Phase 3 |
| 936 | `_sanitize_html_content` | `<[^>]+>` | HTML stripping (bleach fallback) | **RETAINED**: Defensive fallback when bleach unavailable |
| 951 | `_sanitize_html_content` | `\bon\w+\s*=...` | Event handler stripping (bleach fallback) | **RETAINED**: Defensive fallback when bleach unavailable |
| 952 | `_sanitize_html_content` | `javascript:` | JavaScript protocol stripping (bleach fallback) | **RETAINED**: Defensive fallback when bleach unavailable |
| 965-966 | `_sanitize_html_content` | `<script[^>]*>.*?</script>` | Script tag removal (bleach fallback) | **RETAINED**: Defensive fallback when bleach unavailable |
| 2824 | `_extract_html_tag_hints` | `<(\w+)` | Tag name extraction | **RETAINED**: Simple utility, low value to replace |
| 252-253 | Class attributes | `_META_REFRESH_PAT`, `_FRAMELIKE_PAT` | Security detection | **RETAINED**: Already precompiled and optimized |

**Implementation**: Replaced 4 regex detection patterns in `_generate_security_metadata()` with token-based detection using existing `_extract_html()` results. Retained 9 patterns: 5 bleach fallbacks (defensive programming), 1 utility function (low ROI), 2 precompiled security patterns (already optimized), plus 5 deprecated patterns in `sanitize()` (already handled in Phase 3).

## Phase 5

**Count**: 1

| Line | Context | Pattern | Purpose | Replacement Strategy |
|------|---------|---------|---------|---------------------|
| 3077 | `_infer_table_alignment` | `-{3,}` | Table structure detection | Token-based: Check token.type == 'table_open', 'tr |

## Phase 6 (RETAINED)

**Count**: 11 (+1 from Phase 3)

**Note**: These patterns are security-critical and will be RETAINED (not replaced).

| Line | Context | Pattern | Purpose | Replacement Strategy |
|------|---------|---------|---------|---------------------|
| 1058 | `sanitize` (deprecated) | `^([a-zA-Z][a-zA-Z0-9+.\-]*):` | Link scheme validation (security) | KEEP: Security-critical scheme extraction |
| 2575 | `_parse_data_uri` | `^data:([^;,]+)?(;base64)?,(.*)$` | Data URI parsing (security) | KEEP: Security-critical data URI validation |
| 2591 | `_parse_data_uri` | `^[^/]+/([^;]+)` | MIME type extraction (security) | KEEP: Security-critical format validation |
| 3344 | `_check_path_traversal` | `^[a-z]:[/\\]` | Windows drive detection (security) | KEEP: Security-critical string validation (moved from Phase 3) |
| 3420 | `_check_unicode_spoofing` | `[a-zA-Z]` | Unicode script detection (security) | KEEP: Security-critical homograph detection |
| 3421 | `_check_unicode_spoofing` | `[\u0400-\u04FF]` | Cyrillic detection (security) | KEEP: Security-critical homograph detection |
| 3422 | `_check_unicode_spoofing` | `[\u0370-\u03FF]` | Greek detection (security) | KEEP: Security-critical homograph detection |
| 3423 | `_check_unicode_spoofing` | `[\u0600-\u06FF]` | Arabic detection (security) | KEEP: Security-critical homograph detection |
| 3424 | `_check_unicode_spoofing` | `[\u0590-\u05FF]` | Hebrew detection (security) | KEEP: Security-critical homograph detection |
| 3425 | `_check_unicode_spoofing` | `[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]` | CJK detection (security) | KEEP: Security-critical homograph detection |
| 3485 | `_validate_link_scheme` | `^([a-zA-Z][a-zA-Z0-9+.-]*):(.*)$` | Link scheme validation (security) | KEEP: Security-critical scheme parsing |

---

## Detailed Code Snippets

Full code context for each regex pattern:

### Phase 1 - Detailed Snippets

**Line 3583** (`_strip_markdown`)
```python
text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
```

### Phase 2 - Detailed Snippets

**Line 3537** (`_slugify_base`)
```python
s = re.sub(r"[\s/]+", "-", s)
```

**Line 3539** (`_slugify_base`)
```python
s = re.sub(r"[^\w-]", "", s).strip()
```

**Line 3541** (`_slugify_base`)
```python
s = re.sub(r"-+", "-", s)
```

**Line 3553** (`_slugify`)
```python
s = re.sub(r"[\s/]+", "-", s)
```

**Line 3555** (`_slugify`)
```python
s = re.sub(r"[^\w-]", "", s).strip()
```

**Line 3557** (`_slugify`)
```python
s = re.sub(r"-+", "-", s)
```

**Line 3574** (`_strip_markdown`)
```python
text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
```

**Line 3576** (`_strip_markdown`)
```python
text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
```

**Line 3577** (`_strip_markdown`)
```python
text = re.sub(r"\*([^*]+)\*", r"\1", text)
```

**Line 3578** (`_strip_markdown`)
```python
text = re.sub(r"__([^_]+)__", r"\1", text)
```

**Line 3579** (`_strip_markdown`)
```python
text = re.sub(r"_([^_]+)_", r"\1", text)
```

**Line 3584** (`_strip_markdown`)
```python
text = re.sub(r"`([^`]+)`", r"\1", text)
```

### Phase 3 - Detailed Snippets

**Line 1062** (`_strip_bad_link`)
```python
text = re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", _strip_bad_link, text)
```

**Line 1089** (`_filter_image`)
```python
text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _filter_image, text)
```

**Line 3336** (`_check_path_traversal`)
```python
if re.match(r"^[a-z]:[/\\]", decoded_lower):
```

**Line 3581** (`_strip_markdown`)
```python
text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
```

### Phase 4 - Detailed Snippets

**Line 252** (`validate_content`)
```python
_META_REFRESH_PAT = re.compile(r'<meta[^>]+http-equiv\s*=\s*["\']refresh["\'][^>]*>', re.I)
```

**Line 253** (`validate_content`)
```python
_FRAMELIKE_PAT = re.compile(r"<(iframe|object|embed)[^>]*>", re.I)  # Any frame-like element
```

**Line 936** (`_sanitize_html_content`)
```python
return re.sub(r"<[^>]+>", "", html)
```

**Line 951** (`_sanitize_html_content`)
```python
html = re.sub(r"\bon\w+\s*=\s*[\"'][^\"']*[\"']", "", html, flags=re.IGNORECASE)
```

**Line 952** (`_sanitize_html_content`)
```python
html = re.sub(r"javascript:", "", html, flags=re.IGNORECASE)
```

**Line 1023** (`sanitize`)
```python
if re.search(r"<\s*script\b", text, re.I):
```

**Line 1025** (`sanitize`)
```python
text = re.sub(r"<\s*script\b[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.I | re.S)
```

**Line 1035** (`sanitize`)
```python
if re.search(r"<\w+[^>]*>", text):
```

**Line 1270** (`_generate_security_metadata`)
```python
if re.search(r"<(a|img|em|strong|b|i|u|code|kbd|sup|sub)[\s>]", raw_content, re.IGNORECASE):
```

**Line 1274** (`_generate_security_metadata`)
```python
if re.search(r"<script[\s>]", raw_content, re.IGNORECASE):
```

**Line 1029** (`sanitize`)
```python
if re.search(r"\bon[a-z]+\s*=", text, re.I):
```

**Line 1031** (`sanitize`)
```python
text = re.sub(r"\bon[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", text, flags=re.I)
```

**Line 2944** (`_extract_html_tag_hints`)
```python
tags = re.findall(r"<(\w+)", html_content)
```

### Phase 5 - Detailed Snippets

**Line 3077** (`_infer_table_alignment`)
```python
if "|" in line and re.search(r"-{3,}", line):
```

### Phase 6 (RETAINED) - Detailed Snippets

**Line 1050** (`_strip_bad_link`)
```python
msch = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", href)
```

**Line 2575** (`_parse_data_uri`)
```python
match = re.match(r"^data:([^;,]+)?(;base64)?,(.*)$", uri)
```

**Line 2591** (`_parse_data_uri`)
```python
format_match = re.match(r"^[^/]+/([^;]+)", media_type)
```

**Line 3420** (`_check_unicode_spoofing`)
```python
has_latin = bool(re.search(r"[a-zA-Z]", text_sample))
```

**Line 3421** (`_check_unicode_spoofing`)
```python
has_cyrillic = bool(re.search(r"[\u0400-\u04FF]", text_sample))
```

**Line 3422** (`_check_unicode_spoofing`)
```python
has_greek = bool(re.search(r"[\u0370-\u03FF]", text_sample))
```

**Line 3423** (`_check_unicode_spoofing`)
```python
has_arabic = bool(re.search(r"[\u0600-\u06FF]", text_sample))
```

**Line 3424** (`_check_unicode_spoofing`)
```python
has_hebrew = bool(re.search(r"[\u0590-\u05FF]", text_sample))
```

**Line 3425** (`_check_unicode_spoofing`)
```python
has_cjk = bool(re.search(r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]", text_sample))
```

**Line 3485** (`_validate_link_scheme`)
```python
match = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):(.*)$", url)
```

---

## Replacement Strategy Notes

### Phase 1: Fence Patterns
- Replace with token.type checks: `token.type == 'fence'`, `token.type == 'code_block'`
- Use token.info for language detection

### Phase 2: Inline Formatting
- Replace with token.type checks: `token.type in ['strong', 'em', 'code_inline']`
- Use token.content for text extraction

### Phase 3: Links/Images
- Replace with token.type checks: `token.type in ['link_open', 'image']`
- Use token.attrGet() for href/src extraction

### Phase 4: HTML Sanitization
- Replace with token.type checks: `token.type in ['html_block', 'html_inline']`
- Continue using bleach for sanitization (no regex replacement needed)

### Phase 5: Tables
- Replace with token.type checks: `token.type in ['table_open', 'tr_open', 'td_open']`
- Use token.children for cell content

### Phase 6: Security Patterns (RETAINED)
- **DO NOT REPLACE**: These patterns are security-critical
- Includes: scheme validation, control character detection, data-URI parsing
- Must remain as regex for security boundary enforcement

