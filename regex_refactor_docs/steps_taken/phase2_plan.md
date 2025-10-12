# Phase 2 Implementation Plan - Inline → Plaintext

**Phase**: 2 (Inline → Plaintext)
**Created**: 2025-10-12
**Status**: Planning Complete
**Estimated Time**: 1-2 hours (Task 2.1 only - pattern identification and planning)

---

## Overview

Phase 2 focuses on replacing regex-based markdown stripping with token-based text extraction in the `_strip_markdown()` function. This function removes markdown formatting to extract plain text.

**Key Finding**: Like Phase 1, the `_strip_markdown()` function is **NOT currently called anywhere** in the codebase, so changes will have **zero runtime impact** on baseline tests.

---

## Task 2.1: Pattern Identification and Planning

### Patterns Identified (from REGEX_INVENTORY.md)

The `_strip_markdown()` function at lines 3577-3616 contains **7 regex patterns**:

#### Header Removal (1 pattern)
- **Line 3582**: `re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)`
  - Purpose: Remove header markers (`#`, `##`, etc.)
  - Replacement: Token-based header detection using `token.type == "heading_open"`

#### Emphasis/Bold Removal (4 patterns)
- **Line 3584**: `re.sub(r"\*\*([^*]+)\*\*", r"\1", text)`
  - Purpose: Remove bold markers (`**text**`)
  - Replacement: Token-based using `token.type == "strong"`

- **Line 3585**: `re.sub(r"\*([^*]+)\*", r"\1", text)`
  - Purpose: Remove italic markers (`*text*`)
  - Replacement: Token-based using `token.type == "em"`

- **Line 3586**: `re.sub(r"__([^_]+)__", r"\1", text)`
  - Purpose: Remove bold markers (`__text__`)
  - Replacement: Token-based using `token.type == "strong"`

- **Line 3587**: `re.sub(r"_([^_]+)_", r"\1", text)`
  - Purpose: Remove italic markers (`_text_`)
  - Replacement: Token-based using `token.type == "em"`

#### Link Removal (1 pattern)
- **Line 3589**: `re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)`
  - Purpose: Remove link markers, keep text
  - Replacement: Token-based using `token.type == "link_open"`

#### Inline Code Removal (1 pattern)
- **Line 3616**: `re.sub(r"`([^`]+)`", r"\1", text)`
  - Purpose: Remove inline code markers
  - Replacement: Token-based using `token.type == "code_inline"`

**Note**: Fence removal (line 3590-3614) was already replaced in Phase 1.

---

## Replacement Strategy

### Token-Based Plaintext Extraction

Replace all regex patterns with a single token traversal that:

1. **Parse once**: `tokens = self.md.parse(text)`
2. **Walk tokens iteratively**: Use `walk_tokens_iter()` from `token_replacement_lib`
3. **Collect text nodes**: Extract only `token.type == "text"` content
4. **Handle breaks**: Convert `softbreak`/`hardbreak` to spaces
5. **Policy decision on `code_inline`**:
   - **Decision**: EXCLUDE `code_inline` text (treat as non-prose, similar to code blocks)
   - Rationale: Inline code is technical content, not natural language plaintext

### Implementation Approach

```python
def _strip_markdown_token_based(self, text: str) -> str:
    """Remove markdown formatting using token-based extraction."""
    if not HAS_TOKEN_UTILS or walk_tokens_iter is None:
        # Fallback to regex (should not happen in normal operation)
        return self._strip_markdown_regex_fallback(text)

    try:
        tokens = self.md.parse(text)
        plaintext_parts = []

        for token in walk_tokens_iter(tokens):
            if token.type == "text":
                # Pure text content - include it
                plaintext_parts.append(token.content)
            elif token.type in ("softbreak", "hardbreak"):
                # Convert breaks to spaces
                plaintext_parts.append(" ")
            # Skip all other token types:
            # - "strong", "em" markers (we want their content, not markers)
            # - "code_inline" (technical content, excluded from plaintext)
            # - "link_open"/"link_close" (we want text, not URLs)
            # - "heading_open" (we want text, not markers)
            # - etc.

        # Join and normalize whitespace
        plaintext = "".join(plaintext_parts)
        # Collapse multiple spaces
        plaintext = " ".join(plaintext.split())
        return plaintext

    except Exception:
        # Fallback to regex on parse failure
        return self._strip_markdown_regex_fallback(text)
```

---

## Testing Strategy

### Expected Impact
- **Baseline tests**: No changes expected (function is unused)
- **Unit tests**: Should add tests for `_strip_markdown()` if we want to maintain it
- **CI Gates**: All should pass without changes

### Validation Steps
1. Verify `_strip_markdown()` is still not called anywhere
2. Run all CI gates to ensure no regression
3. Consider adding unit tests for the function (even though unused)

---

## Implementation Steps (Task 2.1 - Analysis Complete)

- [x] Review `REGEX_INVENTORY.md` for Phase 2 patterns
- [x] Identify all inline formatting patterns in `_strip_markdown()`
- [x] Document current "strip markdown" logic (7 regex patterns identified)
- [x] Plan token-based replacement strategy
- [x] Make policy decision on `code_inline`: **EXCLUDE** from plaintext
- [x] Create `phase2_plan.md` (this document)

---

## Next Steps (Task 2.2 - Implementation)

**NOT STARTED** - Waiting for approval to proceed

1. Create git checkpoint before modifications
2. Implement `_strip_markdown_token_based()` method
3. Add regex fallback method `_strip_markdown_regex_fallback()`
4. Replace existing `_strip_markdown()` with token-based version
5. Remove all 7 regex patterns
6. Run full baseline tests (expect no changes since function is unused)
7. Run all CI gates
8. Create evidence block with SHA256 hash
9. Document completion in `05_PHASE2_COMPLETION.md`

---

## Risk Assessment

**Risk Level**: Very Low

- Function is unused, so no runtime impact
- Token-based approach is simpler and more maintainable
- Fallback to regex preserves backward compatibility
- All CI gates will validate no regression

---

## References

- **DETAILED_TASK_LIST.md**: Task 2.1 (lines 1676-1696)
- **REGEX_REFACTOR_EXECUTION_GUIDE.md**: §3 Phase 2 (lines 54-57)
- **REGEX_INVENTORY.md**: Phase 2 patterns (lines 36-53)
- **Source code**: `src/docpipe/markdown_parser_core.py:3577-3616`

---

## Policy Decision: Code Inline Handling

**Question**: Should plaintext extraction include or exclude `code_inline` content?

**Decision**: **EXCLUDE** `code_inline` from plaintext extraction

**Rationale**:
1. Consistency with code blocks (already excluded in Phase 1)
2. Inline code represents technical content, not natural language
3. RAG/embedding systems typically want prose text, not code
4. More conservative approach (can always add back if needed)

**Impact**:
- `code_inline` tokens will be skipped during plaintext extraction
- Only `text` token content will be included
- Breaks (`softbreak`/`hardbreak`) converted to spaces

---

**Status**: Task 2.1 Complete ✅
**Next**: Await approval to proceed with Task 2.2 (implementation)
