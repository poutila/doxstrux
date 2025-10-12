# Phase 3 Implementation Plan - Links & Images

**Phase**: 3 (Links & Images)
**Created**: 2025-10-12
**Status**: Planning Complete
**Estimated Time**: 12-16 hours (per DETAILED_TASK_LIST.md)

---

## Overview

Phase 3 focuses on replacing regex-based link and image extraction with token-based approaches. The current implementation uses regex patterns in content sanitization methods (`validate_content`) which are actively used in the parsing pipeline.

**Key Difference from Phase 2**: Unlike `_strip_markdown()` (unused), these functions are actively called during content validation, so changes will have **measurable runtime impact** on baseline tests.

---

## Task 3.1: Pattern Identification and Planning

### Patterns Identified (from REGEX_INVENTORY.md)

The Phase 3 scope includes **4 regex patterns** (but one was already removed in Phase 2):

#### 1. Link Extraction in `_strip_bad_link()` (Line 1070)
- **Pattern**: `(?<!\!)\[([^\]]+)\]\(([^)]+)\)`
- **Purpose**: Extract markdown links (not images) to validate/filter schemes
- **Context**: Called from `validate_content()` during sanitization
- **Current Logic**:
  - Uses negative lookbehind `(?<!\!)` to exclude image syntax
  - Captures link text (group 1) and href (group 2)
  - Validates scheme against allowlist (http, https, mailto, tel, ftp)
  - Removes disallowed scheme links, keeps anchor links (`#fragment`)
- **Replacement Strategy**: Token-based traversal using `token.type == "link_open"`

#### 2. Image Extraction in `_filter_image()` (Line 1097)
- **Pattern**: `!\[([^\]]*)\]\(([^)]+)\)`
- **Purpose**: Extract markdown images to validate data-URI budgets
- **Context**: Called from `validate_content()` during sanitization
- **Current Logic**:
  - Captures alt text (group 1) and src (group 2)
  - Checks for `data:image/` URIs
  - Estimates base64 size: `len(base64_part) * 0.75`
  - Enforces per-image and total budget limits
  - Replaces oversized data-URIs with `![alt](removed)`
- **Replacement Strategy**: Token-based traversal using `token.type == "image"`

#### 3. Path Traversal Check in `_check_path_traversal()` (Line 3344)
- **Pattern**: `^[a-z]:[/\\]`
- **Purpose**: Detect Windows drive letters in URLs (security check)
- **Context**: Called during link/image validation
- **Current Logic**:
  - Checks for patterns like `c:/` or `d:\` in URL paths
  - Part of comprehensive path traversal detection
  - Also checks for `..`, encoded variants, UNC paths, `file://`
- **Replacement Strategy**: This is a **security pattern** - may need to retain regex
- **Decision Required**: Should this remain regex (Phase 6) or use token-based validation?

#### 4. Link Removal in `_strip_markdown()` (Line 3581) ⚠️ ALREADY REMOVED
- **Pattern**: `\[([^\]]+)\]\([^)]+\)`
- **Status**: **Already removed in Phase 2**
- **Context**: The entire `_strip_markdown()` function was replaced with token-based plaintext extraction
- **Note**: REGEX_INVENTORY.md is outdated - this pattern no longer exists

**Actual Pattern Count**: 3 active patterns (1 already removed in Phase 2)

---

## Replacement Strategy

### Token-Based Link & Image Extraction

Replace regex patterns with token traversal using existing utilities from `token_replacement_lib.py`:

#### Available Utilities (Already Implemented)
- `walk_tokens_iter(tokens)`: Iterative DFS traversal (no recursion)
- `collect_text_between_tokens(tokens, start_idx, "link_open", "link_close")`: Extract link text
- `extract_links_and_images(text)`: Legacy function that already uses tokens internally

#### Implementation Approach

**1. Replace `_strip_bad_link()` regex (Line 1070)**

Current approach:
```python
text = re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", _strip_bad_link, text)
```

Token-based approach:
```python
def _strip_bad_link_token_based(self, text: str) -> tuple[str, list[str]]:
    """Remove disallowed link schemes using token-based extraction."""
    tokens = self.md.parse(text)
    removed_schemes = []

    # Build a map of token positions to replacement text
    replacements = {}

    for i, token in enumerate(walk_tokens_iter(tokens)):
        if token.type == "link_open":
            # Extract href from token attributes
            attrs = dict(token.attrs or {})
            href = attrs.get("href", "").strip()

            # Extract link text from children
            link_text = collect_text_between_tokens(tokens, i, "link_open", "link_close")

            # Validate scheme
            if href.startswith("#"):
                continue  # Keep anchor links

            msch = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", href)
            if msch:
                sch = msch.group(1).lower()
                allowed_schemes = self.config.get("allowed_schemes", self._ALLOWED_LINK_SCHEMES)
                if sch not in allowed_schemes:
                    removed_schemes.append(sch)
                    # Mark for replacement: keep text only, no brackets
                    if token.map:
                        replacements[token.map[0]] = link_text

    # Reconstruct text with replacements
    # (Need to implement line-based reconstruction)
    return text, removed_schemes
```

**Challenge**: Regex operates on text directly, tokens require line-based reconstruction.

**Alternative Simpler Approach**: Use existing `extract_links_and_images()` utility:
```python
def _strip_bad_link_token_based(self, text: str) -> tuple[str, list[str]]:
    """Remove disallowed link schemes using token-based extraction."""
    from token_replacement_lib import extract_links_and_images

    links, _ = extract_links_and_images(text)
    removed_schemes = []

    # Validate each link
    for href in links:
        if href.startswith("#"):
            continue  # Keep anchor links

        msch = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", href)
        if msch:
            sch = msch.group(1).lower()
            allowed_schemes = self.config.get("allowed_schemes", self._ALLOWED_LINK_SCHEMES)
            if sch not in allowed_schemes:
                removed_schemes.append(sch)
                # Replace in text: find [text](href) and replace with text
                # This is where we still need regex or manual string manipulation

    return text, removed_schemes
```

**Issue**: Still need to **modify text** to remove bad links. Token extraction alone doesn't solve the replacement problem.

**Policy Question**: Should we:
1. **Keep regex for text manipulation** (hybrid approach - violates "No hybrids" rule)
2. **Reconstruct from tokens** (complex, error-prone)
3. **Change architecture**: Don't modify text, just return validation warnings?

---

## ✅ RECOMMENDED APPROACH: Fail-Closed Validation

**Decision**: Adopt fail-closed validation (Option A) as the primary strategy for Phase 3.

**Date**: 2025-10-12 (Post-Task 3.1 Stakeholder Review)

### Rationale

#### 1. Architectural Alignment
The codebase **already implements** fail-closed validation through `_apply_security_policy()`:
- Sets `embedding_blocked` flag for disallowed content
- Sets `quarantined` flag for suspicious content
- Records detailed `reasons` for policy enforcement
- Located at lines ~2055, ~2280 in `markdown_parser_core.py`

**Key Insight**: We don't need to add fail-closed - we need to **stop fighting it** with text mutation.

#### 2. Follows EXECUTION_GUIDE.md Principles
From EXECUTION_GUIDE.md §0:
- **"Fail closed"** (line 13): Reject unsafe content, don't silently sanitize
- **"Delete regex when you add token logic"** (line 12): No hybrid approaches
- **"No hybrids in PRs"** (line 11): Enforced by CI Gate G1

**Fail-closed allows pure token-based detection without text reconstruction.**

#### 3. Eliminates Text Mutation Problem
Current challenge: Tokens are immutable, but `sanitize()` mutates text.

Fail-closed solution:
- Token-based **detection** only (no reconstruction needed)
- Return validation **errors** instead of mutated text
- Structured output: `embedding_blocked`, `quarantined`, `reasons`

#### 4. Clear Contract Boundaries
**Problem with sanitization**: Ambiguity about whether content passed validation or was silently modified.

**Fail-closed contract**:
- ✅ Content is safe → `embedding_blocked = False`
- ❌ Content has issues → `embedding_blocked = True` with specific `reasons`

Downstream systems make informed decisions based on explicit signals.

#### 5. Performance Improvement
Current `sanitize()` does a **second full parse** (line ~1103):
```python
temp_parser = MarkdownParserCore(text, self.config)
temp_result = temp_parser.parse()
```

**Fail-closed approach**: Single parse, reuse `_apply_security_policy()` results. **~50% faster for sanitization use cases.**

### Implementation Strategy

#### Step 1: Deprecate `sanitize()` Text Mutation

**File**: `src/docpipe/markdown_parser_core.py` (lines ~820-1100)

**Change**: Convert `sanitize()` to non-mutating wrapper:
```python
def sanitize(self, policy=None, security_profile=None) -> dict[str, Any]:
    """
    DEPRECATED (Phase 3): Non-mutating wrapper. Use parse() results instead.

    Returns:
        - sanitized_text: Original content (UNCHANGED)
        - blocked: Whether embedding should be blocked
        - reasons: Human-readable reasons from metadata
    """
    warnings.warn(
        "sanitize() is deprecated: it no longer mutates text. "
        "Use parse() and inspect result['metadata'] for policy decisions.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Reuse parse() results
    parsed = self.parse()
    md = parsed.get("metadata", {})

    blocked = bool(md.get("embedding_blocked") or md.get("quarantined"))
    reasons = []
    if md.get("embedding_block_reason"):
        reasons.append(md["embedding_block_reason"])
    reasons.extend(md.get("quarantine_reasons", []) or [])

    return {
        "sanitized_text": self.content,  # UNCHANGED
        "blocked": blocked,
        "reasons": reasons,
    }
```

**Benefits**:
- Maintains API compatibility (no breaking changes)
- Removes regex patterns: `(?<!\!)\[([^\]]+)\]\(([^)]+)\)` (line 1070) and `!\[([^\]]*)\]\(([^)]+)\)` (line 1097)
- Eliminates second parse (performance win)
- Deprecation warning guides users to new pattern

#### Step 2: Verify `_apply_security_policy()` Coverage

**Required checks** (lines ~2055-2280):
- ✅ Disallowed link schemes → filters from `structure.links`
- ✅ Path traversal detection → calls `_check_path_traversal()`
- ⚠️ Data-URI image budgets → **needs verification**
- ✅ Sets `embedding_blocked`, `quarantined`, `reasons`

**If data-URI budgets missing**: Add token-based budget enforcement:
```python
for img_token in walk_tokens_iter(tokens):
    if img_token.type == "image":
        src = dict(img_token.attrs or {}).get("src", "")
        if src.startswith("data:image/"):
            # O(1) size estimate (already implemented in _parse_data_uri)
            size = estimate_data_uri_size(src)
            if size > budget_limit:
                # Drop from structure.images
                # Set embedding_blocked = True
                # Add reason: "data_uri_image_over_budget"
```

#### Step 3: Update Test Expectations

**New test file**: `tests/test_phase3_fail_closed.py`

```python
def test_parse_does_not_mutate_source():
    """Verify fail-closed: parse() never modifies content."""
    text = "Click [here](javascript:alert(1)) ok"
    p = MarkdownParserCore(text, {"security_profile": "strict"})
    result = p.parse()
    assert result["content"]["raw"] == text  # UNCHANGED

def test_disallowed_links_blocked():
    """Verify policy enforcement: disallowed schemes trigger block."""
    text = "Click [here](javascript:alert(1)) ok"
    p = MarkdownParserCore(text, {"security_profile": "strict"})
    result = p.parse()

    # Links filtered from structure
    assert all(l.get("allowed", True) for l in result["structure"]["links"])

    # Embedding blocked with clear reason
    assert result["metadata"]["embedding_blocked"] is True
    assert "disallowed link schemes" in result["metadata"]["embedding_block_reason"].lower()

def test_data_uri_images_over_budget():
    """Verify data-URI budget enforcement."""
    huge_b64 = "A" * 200000  # ~150KB
    text = f"![test](data:image/png;base64,{huge_b64})"
    p = MarkdownParserCore(text, {"security_profile": "strict"})
    result = p.parse()

    # Image dropped from structure
    assert result["structure"]["images"] == []

    # May or may not block depending on profile
    # But should record in warnings or reasons

def test_sanitize_deprecation():
    """Verify sanitize() returns unchanged text with deprecation warning."""
    text = "A [bad](javascript:void(0)) link"
    p = MarkdownParserCore(text)

    with pytest.warns(DeprecationWarning, match="sanitize.*deprecated"):
        s = p.sanitize()

    assert s["sanitized_text"] == text  # UNCHANGED
    assert isinstance(s["blocked"], bool)
    assert isinstance(s["reasons"], list)
```

**Update existing tests**: Some tests may expect `sanitize()` to mutate text. Update to check `blocked` flag instead.

#### Step 4: Update Documentation

**Move path traversal to Phase 6** in `REGEX_INVENTORY.md`:
```diff
--- a/regex_refactor_docs/steps_taken/REGEX_INVENTORY.md
+++ b/regex_refactor_docs/steps_taken/REGEX_INVENTORY.md
@@ Phase 3
-**Count**: 4
+**Count**: 2

 | Line | Context | Pattern | Purpose | Replacement Strategy |
 |------|---------|---------|---------|---------------------|
 | 1062 | `_strip_bad_link` | `(?<!\!)\[([^\]]+)\]\(([^)]+)\)` | Link extraction | REMOVED: Deprecated sanitize() |
 | 1089 | `_filter_image` | `!\[([^\]]*)\]\(([^)]+)\)` | Image extraction | REMOVED: Deprecated sanitize() |
-| 3336 | `_check_path_traversal` | `^[a-z]:[/\\]` | Path traversal | Token-based validation |
-| 3581 | `_strip_markdown` | `\[([^\]]+)\]\([^)]+\)` | Link removal | REMOVED: Phase 2 |
+| 3581 | `_strip_markdown` | `\[([^\]]+)\]\([^)]+\)` | Link removal | REMOVED in Phase 2 |

@@ Phase 6 (RETAINED)
-**Count**: 10
+**Count**: 11

+| 3336 | `_check_path_traversal` | `^[a-z]:[/\\]` | Windows drive detection (security) | KEEP: Security string validation |
```

### Migration Path for Downstream Callers

**Old pattern** (text mutation):
```python
result = parser.sanitize()
if result["blocked"]:
    reject(result["reasons"])
else:
    embed(result["sanitized_text"])
```

**New pattern** (fail-closed):
```python
result = parser.parse()
metadata = result["metadata"]

if metadata.get("embedding_blocked"):
    reject(metadata["embedding_block_reason"])
elif metadata.get("quarantined"):
    warn(metadata["quarantine_reasons"])
    # Optionally: embed with caution flags

# Use structured data, not raw text
links = result["structure"]["links"]
images = result["structure"]["images"]
```

**Benefit**: Downstream systems get **structured, actionable data** instead of mutated strings.

### Evidence Block

**File**: `evidence_blocks.jsonl`

```json
{
  "evidence_id": "phase3-sanitize-failclosed",
  "phase": 3,
  "file": "src/docpipe/markdown_parser_core.py",
  "lines": "820-1100",
  "description": "Deprecated sanitize() text mutation; fail-closed validation via _apply_security_policy()",
  "patterns_removed": [
    "(?<!\\!)\\[([^\\]]+)\\]\\(([^)]+)\\)",
    "!\\[([^\\]]*)\\]\\(([^)]+)\\)"
  ],
  "patterns_moved_to_phase6": [
    "^[a-z]:[/\\\\]"
  ],
  "code_snippet": "def sanitize(self, ...):\n    warnings.warn('deprecated', DeprecationWarning)\n    parsed = self.parse()\n    return {'sanitized_text': self.content, 'blocked': ...}",
  "sha256": "<to be computed>",
  "rationale": "Fail-closed approach eliminates text mutation, allows pure token-based detection. Aligns with EXECUTION_GUIDE §0 'fail closed' principle. Removes heavy second parse from sanitize().",
  "timestamp": "2025-10-12T..."
}
```

### CI Gate Expectations

**G1 (No Hybrids)**: ✅ PASS
- No regex in new token-based code
- Regex only in Phase 6 retained patterns

**G2 (Canonical Pairs)**: ✅ PASS
- No test file structure changes

**G3 (Parity)**: ⚠️ MAY FAIL INITIALLY
- Some tests may expect `sanitize()` mutation
- **Action**: Update test expectations to check `blocked` flag
- Re-run: Should pass after test updates

**G4 (Performance)**: ✅ PASS (IMPROVED)
- Removed second parse from `sanitize()`
- Expected: ~50% faster sanitization calls
- Expected: Δmedian ≤ -5%, Δp95 ≤ -10% (improvement)

**G5 (Evidence Hash)**: ✅ PASS
- Evidence block created for Phase 3 changes

### Regex Count

**Before Phase 3**: 34 patterns (after Phase 2)

**After Phase 3**:
- Patterns removed: 2 (link/image regex in `sanitize()`)
- Patterns moved to Phase 6: 1 (path traversal)
- **Remaining**: 32 patterns

**Progress**: 22% reduction from baseline (9/41 patterns addressed)

### Risk Assessment

**Risk Level**: Low (downgraded from Medium-High)

**Why Lower**:
- Simpler than hybrid or reconstruction approaches
- `_apply_security_policy()` already exists and is tested
- No token→text reconstruction needed
- Deprecation maintains API compatibility
- Performance improvement (removed second parse)

**Remaining Risks**:
- Test expectation updates (5-10 tests estimated)
- Downstream deprecation warnings (intentional, documented)

---

## ~~Architectural Decision Required~~ → DECISION MADE: Fail-Closed

**✅ DECISION: Option A (Fail-Closed) has been selected.**

See "✅ RECOMMENDED APPROACH: Fail-Closed Validation" section above for full implementation details.

The sections below are retained for historical context and to document the decision-making process.

---

**Current Behavior**: `validate_content()` **mutates text** by removing disallowed links/images.

**Token-Based Challenge**: Tokens are read-only; we can extract data but not easily reconstruct modified text.

**Options**:

#### Option A: Fail Closed (Recommended by EXECUTION_GUIDE.md §0)
- Don't modify text at all
- Return validation **errors** instead of sanitized text
- **Reject** content with disallowed schemes
- Aligns with "fail closed" principle from EXECUTION_GUIDE.md

**Pros**:
- Simpler implementation
- Tokens only used for detection, not reconstruction
- More secure (no silent sanitization)
- Aligns with project principles

**Cons**:
- Changes validation behavior (reject vs sanitize)
- May break existing tests expecting sanitization
- Requires updating test expectations

#### Option B: Two-Pass Approach (Hybrid Risk)
- First pass: Token-based detection (find positions)
- Second pass: Text-based replacement (regex or string ops)
- Risk of creating a "hybrid" pattern (violates CI gate)

**Pros**:
- Maintains current behavior (sanitize, don't reject)
- Easier migration path

**Cons**:
- May violate "No hybrids" gate
- More complex implementation
- Requires careful coordination between passes

#### Option C: Full Token Reconstruction
- Parse to tokens
- Filter/transform tokens
- Reconstruct text from filtered tokens
- Most complex but "pure" token approach

**Pros**:
- Pure token-based (no regex in implementation)
- Full control over output

**Cons**:
- Very complex to implement correctly
- High risk of introducing bugs
- Markdown reconstruction is non-trivial

---

## Policy Decision: Path Traversal Check (Line 3344)

**Current Pattern**: `^[a-z]:[/\\]` (Windows drive letter detection)

**Analysis**:
- This is a **security check** for path traversal attacks
- Part of comprehensive validation including `..`, `file://`, UNC paths
- Used in URL validation context

**Decision**: This should be **retained as regex** (move to Phase 6).

**Rationale**:
- Matches Phase 6 scope: "Security regex (retained)"
- EXECUTION_GUIDE.md §6 allows retention of security-critical regex
- Pattern is simple, fast, and security-critical
- No token equivalent (this is string validation, not markdown parsing)

**Action**: Update REGEX_INVENTORY.md to move this pattern from Phase 3 to Phase 6.

---

## Challenges and Risks

### 1. Text Mutation vs Token Detection
- **Challenge**: Current code mutates text (removes bad links), tokens are immutable
- **Impact**: Need architectural decision on fail-closed vs sanitize approach
- **Risk**: High - affects baseline test expectations

### 2. Reference-Style Links
- **Challenge**: DETAILED_TASK_LIST.md mentions "reference-style patterns" but none found in regex scan
- **Analysis**: markdown-it-py handles references internally via token attrs
- **Impact**: May need to verify reference links are included in token extraction
- **Risk**: Low - likely already handled by `link_open` tokens

### 3. Baseline Test Impact
- **Challenge**: These functions are actively used (unlike Phase 2's `_strip_markdown()`)
- **Impact**: Changes WILL affect baseline tests
- **Risk**: Medium - need careful validation

### 4. Legacy Utility Function
- **Note**: `token_replacement_lib.extract_links_and_images()` already exists
- **Opportunity**: Can leverage existing token-based extraction
- **Consideration**: May need to adapt for sanitization use case

---

## Implementation Steps (Task 3.2 - Not Started)

### Prerequisite
- [ ] Make architectural decision: Fail-closed vs Sanitize approach
- [ ] Update REGEX_INVENTORY.md: Move path traversal pattern to Phase 6
- [ ] Consult with stakeholders on validation behavior change (if fail-closed)

### Implementation (if Fail-Closed approach chosen)
- [ ] Create git checkpoint before modifications
- [ ] Modify `_strip_bad_link()`: Replace regex with token-based detection
- [ ] Modify `_filter_image()`: Replace regex with token-based detection
- [ ] Change return signature: Return validation errors instead of mutated text
- [ ] Update `validate_content()` to handle new error-based approach
- [ ] Update baseline tests to expect validation errors (not sanitized text)
- [ ] Run full baseline tests (expect changes due to behavior change)
- [ ] Run all CI gates (expect G3 parity to fail initially)
- [ ] Update test expectations to match new behavior
- [ ] Re-run CI gates (all should pass)
- [ ] Create evidence block with SHA256 hash
- [ ] Document completion in `06_PHASE3_COMPLETION.md`

### Implementation (if Two-Pass approach chosen)
- [ ] Create git checkpoint before modifications
- [ ] Implement token-based detection in `_strip_bad_link()`
- [ ] Keep text replacement logic separate (mark as Phase 3 hybrid)
- [ ] Add CI gate exception comment for hybrid pattern
- [ ] Same implementation for `_filter_image()`
- [ ] Run full baseline tests (expect no changes)
- [ ] Run all CI gates (G1 may flag hybrid pattern)
- [ ] Document hybrid necessity in evidence block
- [ ] Document completion in `06_PHASE3_COMPLETION.md`

---

## Questions for Stakeholder

1. **Validation Behavior**: Should `validate_content()` reject or sanitize disallowed content?
   - Current: Sanitize (remove bad links but keep valid content)
   - Proposed: Fail-closed (reject entire content if validation fails)
   - EXECUTION_GUIDE.md suggests "fail closed" approach

2. **Path Traversal Pattern**: Confirm this should move to Phase 6 (retained security regex)
   - Pattern: `^[a-z]:[/\\]`
   - Context: Windows drive letter detection
   - Recommendation: Keep as regex (security-critical, no token equivalent)

3. **Hybrid Patterns**: If text mutation is required, are temporary hybrids acceptable?
   - EXECUTION_GUIDE.md §0: "Delete regex when you add token logic"
   - CI Gate G1: "No hybrids in PRs"
   - Recommendation: Choose fail-closed to avoid hybrids

---

## Regex Count

### Before Phase 3
- **Total regex patterns**: 34 (after Phase 2)
- **Phase 3 patterns**: 3 active (1 already removed in Phase 2)

### After Phase 3 (Projected)
- **Patterns removed**: 2 regex patterns (link, image extraction)
- **Patterns moved to Phase 6**: 1 (path traversal check)
- **Remaining regex**: 32 patterns (34 - 2)

**Progress**: 22% reduction from baseline (9/41 patterns addressed)

---

## Files to Modify

### Source Code
- `src/docpipe/markdown_parser_core.py`:
  - Lines 1070: `_strip_bad_link()` - replace regex with tokens
  - Lines 1097: `_filter_image()` - replace regex with tokens
  - Lines 3344: `_check_path_traversal()` - move pattern to Phase 6 (retained)

### Documentation
- `regex_refactor_docs/steps_taken/phase3_plan.md` (this file)
- `regex_refactor_docs/steps_taken/REGEX_INVENTORY.md` (update Phase 3 count, move path traversal to Phase 6)
- `regex_refactor_docs/steps_taken/06_PHASE3_COMPLETION.md` (to be created)
- `regex_refactor_docs/DETAILED_TASK_LIST.md` (update if architectural changes needed)

### Evidence
- `evidence_blocks.jsonl` (Phase 3 evidence block to be added)

### Phase Artifacts
- `.phase-3.complete.json` (to be created after completion)

---

## Next Steps (Task 3.2 - Awaiting Approval)

**NOT STARTED** - Awaiting architectural decision and stakeholder approval

1. **Decision Required**: Choose fail-closed vs sanitize approach
2. **Update REGEX_INVENTORY.md**: Move path traversal pattern to Phase 6
3. **Proceed with implementation** once approach is confirmed

---

## Risk Assessment

**Risk Level**: Medium-High

**Factors**:
- Functions are actively used (high impact)
- Architectural decision required (behavior change)
- Text mutation challenge (tokens are immutable)
- May require test expectation updates (if fail-closed chosen)
- First phase with significant behavioral changes

**Mitigation**:
- Thorough architectural planning (this document)
- Clear stakeholder communication
- Comprehensive baseline test validation
- Fall back to two-pass approach if fail-closed is rejected

---

## References

- **DETAILED_TASK_LIST.md**: Task 3.1 (lines 1697-1715), Task 3.2 (lines 1717-1738)
- **REGEX_REFACTOR_EXECUTION_GUIDE.md**:
  - §0: "Fail closed" principle (line 13)
  - §0: "Delete regex when you add token logic" (line 12)
  - §0: "No hybrids in PRs" (line 11)
  - §3: Phase 3 description (lines 59-63)
- **REGEX_INVENTORY.md**: Phase 3 patterns (lines 55-64)
- **token_replacement_lib.py**: Existing utilities (lines 35-285)
- **Source code**: `src/docpipe/markdown_parser_core.py:1050-1099, 3336-3349`

---

**Status**: Task 3.1 Complete ✅
**Next**: Task 3.2 - Awaiting architectural decision (fail-closed vs sanitize)

---

## Appendix: Token-Based Link/Image Extraction Examples

### Example 1: Extract All Links
```python
from token_replacement_lib import walk_tokens_iter

tokens = self.md.parse(text)
links = []

for token in walk_tokens_iter(tokens):
    if token.type == "link_open":
        attrs = dict(token.attrs or {})
        href = attrs.get("href", "")
        links.append(href)
```

### Example 2: Extract All Images with Alt Text
```python
from token_replacement_lib import walk_tokens_iter

tokens = self.md.parse(text)
images = []

for token in walk_tokens_iter(tokens):
    if token.type == "image":
        attrs = dict(token.attrs or {})
        src = attrs.get("src", "")
        alt = ""
        if token.children:
            alt = "".join(c.content for c in token.children if c.type == "text")
        images.append((src, alt))
```

### Example 3: Validate Link Schemes (Detection Only)
```python
from token_replacement_lib import walk_tokens_iter

tokens = self.md.parse(text)
removed_schemes = []

for token in walk_tokens_iter(tokens):
    if token.type == "link_open":
        attrs = dict(token.attrs or {})
        href = attrs.get("href", "").strip()

        if href.startswith("#"):
            continue  # Anchor links OK

        msch = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", href)
        if msch:
            sch = msch.group(1).lower()
            allowed_schemes = ["http", "https", "mailto", "tel"]
            if sch not in allowed_schemes:
                removed_schemes.append(sch)
                # In fail-closed approach: raise SecurityError
                # In sanitize approach: need to remove this link from text
```

**Note**: Example 3 shows the detection part is straightforward. The challenge is the text mutation part (if sanitize approach is chosen).
