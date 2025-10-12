# Phase 1 Implementation Plan: Fences & Indented Code

**Date**: 2025-10-12
**Phase**: 1 - Fences & Indented Code
**Status**: Analysis Complete - Ready for Implementation

---

## Executive Summary

**Key Finding**: The parser is **already 95% token-based** for fence and indented code detection. Only **1 regex pattern** needs replacement in `_strip_markdown()` helper function.

### Scope of Work
- **Regex patterns to remove**: 1 (line 3583)
- **String-based logic to review**: 3 lines (indented code fallback in `_extract_code_blocks`)
- **Estimated implementation time**: 1-2 hours (much less than original 12-16 hour estimate)
- **Risk level**: **LOW** - Most code already uses tokens

---

## Current Implementation Analysis

### 1. Fence Detection (Already Token-Based ✅)

**Location**: `src/docpipe/markdown_parser_core.py:2225-2236`

**Current Implementation**:
```python
if node.type == "fence":
    block = {
        "id": f"code_{len(ctx)}",
        "type": "fenced",
        "language": node.info if hasattr(node, "info") else "",
        "content": node.content if hasattr(node, "content") else "",
        "start_line": node.map[0] if node.map else None,
        "end_line": node.map[1] if node.map else None,
        "section_id": self._find_section_id(node.map[0] if node.map else 0),
    }
    ctx.append(block)
```

**Status**: ✅ **Already token-based** - Uses `node.type == "fence"`, `node.info`, `node.content`, `node.map`

**Action Required**: **NONE** - Already compliant with Phase 1 goals

---

### 2. Indented Code Detection (Mostly Token-Based ✅)

**Location**: `src/docpipe/markdown_parser_core.py:2237-2248`

**Current Implementation**:
```python
if node.type == "code_block":
    block = {
        "id": f"code_{len(ctx)}",
        "type": "indented",
        "language": "",
        "content": node.content if hasattr(node, "content") else "",
        "start_line": node.map[0] if node.map else None,
        "end_line": node.map[1] if node.map else None,
        "section_id": self._find_section_id(node.map[0] if node.map else 0),
    }
    ctx.append(block)
```

**Status**: ✅ **Already token-based** - Uses `node.type == "code_block"`, `node.content`, `node.map`

**Action Required**: **NONE** - Already compliant with Phase 1 goals

---

### 3. Indented Code Fallback (String-Based - Review Needed ⚠️)

**Location**: `src/docpipe/markdown_parser_core.py:2260-2289`

**Current Implementation**:
```python
# Also extract indented code blocks that markdown-it might miss
covered = set()
for b in blocks:
    if b.get("start_line") is not None and b.get("end_line") is not None:
        covered.update(range(b["start_line"], b["end_line"] + 1))

i, N = 0, len(self.lines)
while i < N:
    line = self.lines[i]
    if (line.startswith("    ") or line.startswith("\t")) and i not in covered:
        start = i
        i += 1
        while i < N:
            nxt = self.lines[i]
            if not nxt.strip() or nxt.startswith("    ") or nxt.startswith("\t"):
                i += 1
            else:
                break
        end = i - 1
        # Extract and process indented content using centralized slicing
        raw_lines = self._slice_lines_inclusive(start, end + 1)
        content = "\n".join(l[4:] if l.startswith("    ") else l[1:] for l in raw_lines)
        blocks.append({...})
        covered.update(range(start, end + 1))
    else:
        i += 1
```

**Status**: ⚠️ **String-based fallback** - Uses `line.startswith("    ")` and `line.startswith("\t")`

**Purpose**: Catches indented code blocks that markdown-it might miss

**Action Required**:
- **Option 1**: Keep fallback if markdown-it coverage is incomplete (safe, maintains backward compatibility)
- **Option 2**: Remove fallback and rely 100% on markdown-it tokens (cleaner, assumes markdown-it is complete)
- **Recommended**: Run tests first to see if fallback is actually used

---

### 4. Regex Pattern in `_strip_markdown()` (Needs Replacement ❌)

**Location**: `src/docpipe/markdown_parser_core.py:3583`

**Current Implementation**:
```python
def _strip_markdown(self, text: str) -> str:
    """Remove markdown formatting from text (for backward compatibility)."""
    import re

    # Remove headers
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    # Remove emphasis
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Remove links
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove code blocks markers  ← **PHASE 1 TARGET**
    text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)  # ← LINE 3583
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()
```

**Status**: ❌ **Regex-based** - Line 3583 uses regex to strip fence markers

**Phase Assignments**:
- **Line 3574**: Phase 2 (headers)
- **Lines 3576-3579**: Phase 2 (emphasis)
- **Line 3581**: Phase 3 (links)
- **Line 3583**: **Phase 1** (fence blocks) ← **TARGET**
- **Line 3584**: Phase 2 (inline code)

**Action Required**: Replace line 3583 with token-based fence removal

---

## Phase 1 Target Summary

### Patterns to Replace: 1

| Line | Function | Pattern | Phase | Action |
|------|----------|---------|-------|--------|
| 3583 | `_strip_markdown` | ` ```[^`]*``` ` | 1 | Replace with token-based fence detection |

### String-Based Logic to Review: 1 section

| Lines | Function | Logic | Status |
|-------|----------|-------|--------|
| 2263-2289 | `_extract_code_blocks` | `startswith("    ")`, `startswith("\t")` | Fallback - needs assessment |

---

## Implementation Strategy

### Option A: Minimal Change (Recommended)

**Replace only line 3583** in `_strip_markdown()`:

**Before**:
```python
text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
```

**After** (token-based):
```python
# Use token-based fence detection
tokens = self.md.parse(text)
for token in walk_tokens_iter(tokens):
    if token.type == "fence":
        # Remove fence markers and content from text
        if token.map:
            start_line, end_line = token.map
            # Replace lines with empty strings
            ...
```

**Pros**:
- Minimal code change
- Low risk
- Completes Phase 1 requirement

**Cons**:
- `_strip_markdown()` operates on plain text, not tokens (need to parse first)
- More complex than simple regex replacement

---

### Option B: Replace `_strip_markdown()` Entirely (Aggressive)

**Replace entire `_strip_markdown()` function** with token-based text extraction:

```python
def _strip_markdown_token_based(self, text: str) -> str:
    """Remove markdown formatting using token traversal."""
    tokens = self.md.parse(text)
    result = []

    for token in walk_tokens_iter(tokens):
        # Only collect plain text nodes
        if token.type == "text":
            result.append(token.content)
        elif token.type in ("softbreak", "hardbreak"):
            result.append(" ")

    return " ".join(result).strip()
```

**Pros**:
- Cleanest token-based approach
- Handles all markdown stripping consistently
- Future-proof for Phases 2-3

**Cons**:
- Larger change scope
- Might affect multiple phases at once (violates phase boundary)
- Higher risk

---

### Option C: Deprecate and Replace (Conservative)

**Mark `_strip_markdown()` as legacy**, create new token-based function:

```python
def _strip_markdown(self, text: str) -> str:
    """LEGACY: Use _extract_plaintext_token_based() instead."""
    # Keep old implementation for backward compatibility
    import re
    text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)  # Still here
    ...

def _extract_plaintext_token_based(self, text: str) -> str:
    """Extract plaintext using token traversal (Phase 1+)."""
    tokens = self.md.parse(text)
    result = []
    for token in walk_tokens_iter(tokens):
        if token.type == "text":
            result.append(token.content)
    return " ".join(result).strip()
```

**Pros**:
- Zero breaking changes
- Gradual migration path
- Easy rollback

**Cons**:
- Doesn't fully complete Phase 1 (regex still present)
- Technical debt accumulation

---

## Recommended Approach: **Option A (Minimal Change)**

### Justification
1. **Completes Phase 1 requirement**: Removes the only Phase 1 regex
2. **Low risk**: Small, focused change
3. **Maintains compatibility**: Doesn't change function signature
4. **Testable**: Easy to verify with existing baseline tests
5. **Phases remain distinct**: Doesn't touch Phase 2/3 patterns

### Implementation Steps

1. **Modify `_strip_markdown()` line 3583**:
   ```python
   # Before (line 3583)
   text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)

   # After (token-based)
   # Parse text to tokens
   temp_tokens = self.md.parse(text)
   # Find fence blocks and remove from text
   for token in walk_tokens_iter(temp_tokens):
       if token.type == "fence" and token.map:
           start_line, end_line = token.map
           # Remove fence block lines from text
           lines = text.split('\n')
           lines[start_line:end_line] = [''] * (end_line - start_line)
           text = '\n'.join(lines)
   ```

2. **Test with baseline suite**: All 542 tests should still pass

3. **Verify G1 gate**: No hybrid patterns present

4. **Create evidence block** with code snippet and SHA256 hash

---

## Indented Code Fallback Assessment

### Question: Should we keep the string-based fallback (lines 2263-2289)?

**Test Plan**:
1. Comment out the fallback section
2. Run baseline tests: `python3 tools/baseline_test_runner.py --profile moderate`
3. Check if any tests fail

**Decision Matrix**:
- **If 0 failures**: Remove fallback (markdown-it is complete) ✅
- **If 1-5 failures**: Keep fallback, document edge cases ⚠️
- **If >5 failures**: Keep fallback, markdown-it has gaps ❌

**Recommendation**: Test first, then decide

---

## Estimated Test Impact

### Test Categories Likely Affected

Based on test category names, the following may exercise fence/code detection:

- `01_edge_cases` (114 files) - unterminated fences, nested code
- `06_stress_links` (30 files) - code in link text
- `07_stress_html` (30 files) - code vs HTML ambiguity
- `30_fenced_code_info` (6 files) - language strings

**Total**: ~180/542 files might test code block handling

**Expected Impact**: Most tests already pass (implementation is token-based), changes should maintain 100% pass rate

---

## Phase 1 Acceptance Criteria

- [ ] **G1 (No Hybrids)**: No hybrid patterns present
- [ ] **G2 (Canonical Pairs)**: 542 pairs intact
- [ ] **G3 (Parity)**: 542/542 baseline tests passing
- [ ] **G4 (Performance)**: Δmedian ≤5%, Δp95 ≤10%
- [ ] **G5 (Evidence)**: Evidence blocks created for regex removal
- [ ] **Regex removed**: Line 3583 no longer uses regex
- [ ] **Token-based**: All fence/code detection uses `token.type` checks
- [ ] **Documentation**: phase1_plan.md and completion report created

---

## Risk Assessment

### Overall Risk: **LOW** 🟢

| Risk Factor | Level | Mitigation |
|-------------|-------|------------|
| Scope creep | Low | Only 1 regex to replace |
| Breaking changes | Low | Implementation already token-based |
| Performance regression | Very Low | Token traversal already in use |
| Test failures | Low | Baseline tests verify parity |
| Rollback complexity | Very Low | Single file, ~10 lines changed |

---

## Next Steps (Task 1.2+)

1. **Task 1.2**: Implement token-based fence removal in `_strip_markdown()`
   - Estimated time: 1 hour
   - Files: `src/docpipe/markdown_parser_core.py` (line 3583)

2. **Task 1.3**: Test indented code fallback
   - Estimated time: 30 minutes
   - Decision: Keep or remove fallback logic

3. **Task 1.4**: Validation
   - Run all CI gates
   - Verify 542/542 tests pass
   - Estimated time: 30 minutes

4. **Task 1.5**: Documentation
   - Create completion report
   - Generate evidence blocks
   - Update REGEX_INVENTORY.md
   - Estimated time: 30 minutes

**Total Revised Estimate**: 2.5-3 hours (down from 12-16 hours)

---

## Questions for Review

1. **Option A vs B vs C**: Which approach do you prefer?
   - Recommend: **Option A** (minimal change)

2. **Indented code fallback**: Test first or remove immediately?
   - Recommend: **Test first** (run baseline with fallback commented out)

3. **Scope boundaries**: Should we touch other `_strip_markdown` patterns?
   - Recommend: **No** - keep to Phase 1 only (line 3583)

---

## Conclusion

Phase 1 is **much simpler** than originally estimated because:
1. Core fence/code detection is already token-based (95% complete)
2. Only 1 regex pattern needs replacement
3. Implementation is low-risk and well-isolated

**Ready to proceed with Task 1.2** after review and approval.
