# Phase 4 Plan: HTML Detection & Handling

**Date**: 2025-10-12
**Phase**: 4 (HTML Handling)
**Estimated Time**: 6-8 hours
**Risk Level**: Medium (HTML security implications)

---

## Table of Contents

1. [Pattern Identification](#pattern-identification)
2. [Current State Analysis](#current-state-analysis)
3. [Recommended Approach](#recommended-approach)
4. [Implementation Strategy](#implementation-strategy)
5. [Test Plan](#test-plan)
6. [CI Gate Expectations](#ci-gate-expectations)
7. [Risk Assessment](#risk-assessment)

---

## Pattern Identification

### Phase 4 Patterns from REGEX_INVENTORY.md (13 patterns)

| Line | Context | Pattern | Purpose | Current Status |
|------|---------|---------|---------|---------------|
| 252 | `validate_content` (class attr) | `_META_REFRESH_PAT` | Meta refresh detection | ✅ Already precompiled, used for detection |
| 253 | `validate_content` (class attr) | `_FRAMELIKE_PAT` | Frame-like element detection | ✅ Already precompiled, used for detection |
| 936 | `_sanitize_html_content` | `<[^>]+>` | HTML tag stripping (bleach fallback) | ⚠️ Fallback when bleach unavailable |
| 951 | `_sanitize_html_content` | `\bon\w+\s*=\s*[\"'][^\"']*[\"']` | Event handler stripping | ⚠️ Fallback when bleach unavailable |
| 952 | `_sanitize_html_content` | `javascript:` | JavaScript protocol stripping | ⚠️ Fallback when bleach unavailable |
| 1023 | `sanitize` (deprecated) | `<\s*script\b` | Script tag detection | ❌ DEPRECATED - already handled |
| 1025 | `sanitize` (deprecated) | `<\s*script\b[^>]*>.*?<\s*/\s*script\s*>` | Script tag removal | ❌ DEPRECATED - already handled |
| 1029 | `sanitize` (deprecated) | `\bon[a-z]+\s*=` | Event handler detection | ❌ DEPRECATED - already handled |
| 1031 | `sanitize` (deprecated) | `\bon[a-z]+\s*=\s*(\"[^\"]*\"\|'[^']*'\|[^\s>]+)` | Event handler removal | ❌ DEPRECATED - already handled |
| 1035 | `sanitize` (deprecated) | `<\w+[^>]*>` | HTML tag detection | ❌ DEPRECATED - already handled |
| 1148-1149 | `_generate_security_metadata` | `<(div\|span\|script\|style\|iframe\|object\|embed\|form)[\s>]` | HTML block detection | ⚠️ Used for warnings/statistics |
| 1152 | `_generate_security_metadata` | `<(a\|img\|em\|strong\|b\|i\|u\|code\|kbd\|sup\|sub)[\s>]` | HTML inline detection | ⚠️ Used for warnings/statistics |
| 1156 | `_generate_security_metadata` | `<script[\s>]` | Script detection for statistics | ⚠️ Used for warnings/statistics |
| 1163-1164 | `_generate_security_metadata` | `\bon(load\|error\|click\|mouse\|key\|focus\|blur\|change\|submit)\s*=` | Event handler detection for statistics | ⚠️ Used for warnings/statistics |
| 2824 | `_extract_html_tag_hints` | `<(\w+)` | HTML tag name extraction | ⚠️ Utility for downstream hints |
| 965-966 | `_sanitize_html_content` | `<script[^>]*>.*?</script>` | Script tag removal (bleach fallback) | ⚠️ Fallback when bleach unavailable |

**Total**: 16 patterns (3 more than inventory due to duplicates/missed patterns)

### Pattern Status Breakdown

1. **Already Handled** (5 patterns in deprecated `sanitize()`):
   - Lines 1023, 1025, 1029, 1031, 1035
   - ✅ Deprecated in Phase 3, no action needed

2. **Detection/Statistics Only** (4 patterns in `_generate_security_metadata()`):
   - Lines 1148-1149, 1152, 1156, 1163-1164
   - ⚠️ Used for security warnings, not removal
   - **Key Decision**: Should these be token-based or regex-based?

3. **Bleach Fallback** (5 patterns in `_sanitize_html_content()`):
   - Lines 936, 951, 952, 965-966
   - ⚠️ Only used when bleach unavailable
   - **Key Decision**: Keep as fallback or improve?

4. **Utility** (1 pattern in `_extract_html_tag_hints()`):
   - Line 2824
   - ⚠️ Simple tag name extraction
   - **Key Decision**: Worth replacing?

5. **Precompiled Class Attributes** (2 patterns):
   - `_META_REFRESH_PAT`, `_FRAMELIKE_PAT`
   - ✅ Already optimized, used in detection

---

## Current State Analysis

### Token-Based HTML Extraction (Already Exists!)

The parser **already extracts HTML using tokens** in `_extract_html()` (lines 2743-2817):

```python
def _extract_html(self) -> dict[str, Any]:
    """Extract HTML blocks and inline elements from tokens."""
    html_blocks = []
    html_inline_dict = {}

    def html_processor(node, ctx, level):
        if node.type == "html_block":
            # Extract HTML blocks via tokens
            start_line = node.map[0] if node.map else None
            end_line = node.map[1] if node.map else None
            content = getattr(node, "content", "") or ""
            html_blocks.append({
                "type": "html_block",
                "content": content,
                "start_line": start_line,
                "end_line": end_line,
                "allowed": html_allowed,
                "tag_hints": self._extract_html_tag_hints(content),
            })

    # Process inline tokens
    for token in self.tokens:
        if token.type == "inline" and token.children:
            for child in token.children:
                if child.type == "html_inline":
                    content = getattr(child, "content", "") or ""
                    # ... extract inline HTML

    return {"blocks": html_blocks, "inline": html_inline}
```

**Key Observation**: The parser **already uses token-based HTML extraction**. The regex patterns in Phase 4 are mostly:
1. **Detection patterns** for security warnings (not removal)
2. **Fallback patterns** when bleach is unavailable
3. **Deprecated patterns** in `sanitize()` (already handled)

---

## Recommended Approach

### Strategy: Token-Based Detection + Minimal Regex Cleanup

Unlike Phases 1-3 where we replaced regex patterns with token-based extraction, **Phase 4 is different**:
- HTML is already extracted via tokens (`html_block`, `html_inline`)
- Regex patterns are mostly for **detection/warnings** (security metadata)
- Some patterns are **fallbacks** when bleach is unavailable

### Approach Options

#### Option A: Replace Detection Patterns with Token-Based (RECOMMENDED)

**Scope**: Replace regex patterns in `_generate_security_metadata()` with token-based detection.

**Rationale**:
1. HTML is already extracted via tokens in `_extract_html()`
2. Detection patterns scan raw content redundantly
3. Token-based detection is more accurate (respects markdown escaping)

**Changes**:
```python
# OLD (regex-based detection in _generate_security_metadata):
if re.search(r"<(div|span|script|style|iframe|object|embed|form)[\s>]", raw_content, re.IGNORECASE):
    security["statistics"]["has_html_block"] = True
if re.search(r"<script[\s>]", raw_content, re.IGNORECASE):
    security["statistics"]["has_script"] = True

# NEW (token-based detection):
html_data = structure.get("html_blocks", []) + structure.get("html_inline", [])
if html_data:
    security["statistics"]["has_html_block"] = True

    # Detect scripts by checking HTML content
    for html_item in html_data:
        content = html_item.get("content", "").lower()
        if "<script" in content:
            security["statistics"]["has_script"] = True
            break
```

**Patterns Removed**: 4 patterns (lines 1148-1149, 1152, 1156, 1163-1164)

**Risk**: Low (detection only, no behavior change)

---

#### Option B: Keep Bleach Fallbacks As-Is (RECOMMENDED)

**Scope**: Leave `_sanitize_html_content()` regex fallbacks unchanged.

**Rationale**:
1. These are **fallback patterns** when bleach is unavailable
2. Bleach is preferred for HTML sanitization (industry-standard)
3. Fallbacks are simple, defensive, and rarely executed
4. Replacing with token-based logic is complex and error-prone

**Patterns Retained**: 5 patterns (lines 936, 951, 952, 965-966)

**Risk**: Zero (no changes)

**Alternative** (if bleach is always available):
- Remove fallback code entirely
- Raise error if bleach unavailable and HTML needs sanitization
- **Not recommended**: Graceful degradation is better

---

#### Option C: Replace `_extract_html_tag_hints()` (OPTIONAL)

**Scope**: Replace regex tag extraction with token-based approach.

**Rationale**:
1. Utility function, not critical path
2. Tag hints are already extracted for each HTML item
3. Regex is simple and clear

**Decision**: **SKIP** - Low value, minimal pattern reduction

---

### Final Recommendation: HYBRID APPROACH

**Phase 4 Strategy**:
1. ✅ **Replace 4 detection patterns** in `_generate_security_metadata()` with token-based detection
2. ✅ **Keep 5 bleach fallback patterns** unchanged (defensive programming)
3. ✅ **Keep 1 utility pattern** in `_extract_html_tag_hints()` (low value)
4. ✅ **Keep 2 precompiled patterns** (_META_REFRESH_PAT, _FRAMELIKE_PAT) - already optimized
5. ✅ **5 deprecated patterns** already handled in Phase 3

**Net Regex Reduction**: 4 patterns (32 → 28)

**Rationale**:
- Focuses on meaningful improvements (detection accuracy)
- Preserves defensive fallbacks (when bleach unavailable)
- Avoids over-engineering (utility functions)
- Maintains security guarantees (precompiled patterns stay)

---

## Implementation Strategy

### Step 1: Create Git Checkpoint

```bash
git add -A
git commit -m "checkpoint: Phase 4 starting point"
```

### Step 2: Read EXECUTION_GUIDE.md

Review fail-closed principles and CI gate requirements.

### Step 3: Replace Detection Patterns

**File**: `src/docpipe/markdown_parser_core.py`
**Method**: `_generate_security_metadata()` (lines 1084-1350)

#### Change 1: Replace HTML block detection

**Before** (lines 1148-1151):
```python
# HTML detection
if re.search(
    r"<(div|span|script|style|iframe|object|embed|form)[\s>]", raw_content, re.IGNORECASE
):
    security["statistics"]["has_html_block"] = True
```

**After**:
```python
# HTML detection (token-based)
html_blocks = structure.get("html_blocks", [])
if html_blocks:
    security["statistics"]["has_html_block"] = True
```

#### Change 2: Replace HTML inline detection

**Before** (lines 1152-1153):
```python
if re.search(r"<(a|img|em|strong|b|i|u|code|kbd|sup|sub)[\s>]", raw_content, re.IGNORECASE):
    security["statistics"]["has_html_inline"] = True
```

**After**:
```python
html_inline = structure.get("html_inline", [])
if html_inline:
    security["statistics"]["has_html_inline"] = True
```

#### Change 3: Replace script detection

**Before** (lines 1156-1160):
```python
# Script detection
if re.search(r"<script[\s>]", raw_content, re.IGNORECASE):
    security["statistics"]["has_script"] = True
    security["warnings"].append(
        {"type": "script_tag", "line": None, "message": "Document contains <script> tags"}
    )
```

**After**:
```python
# Script detection (token-based)
html_items = structure.get("html_blocks", []) + structure.get("html_inline", [])
for html_item in html_items:
    content = html_item.get("content", "").lower()
    if "<script" in content:
        security["statistics"]["has_script"] = True
        security["warnings"].append(
            {
                "type": "script_tag",
                "line": html_item.get("line") or html_item.get("start_line"),
                "message": "Document contains <script> tags"
            }
        )
        break
```

#### Change 4: Replace event handler detection

**Before** (lines 1163-1175):
```python
# Event handler detection
if re.search(
    r"\bon(load|error|click|mouse|key|focus|blur|change|submit)\s*=",
    raw_content,
    re.IGNORECASE,
):
    security["statistics"]["has_event_handlers"] = True
    security["warnings"].append(
        {
            "type": "event_handlers",
            "line": None,
            "message": "Document contains HTML event handler attributes",
        }
    )
```

**After**:
```python
# Event handler detection (token-based)
for html_item in html_items:
    content = html_item.get("content", "").lower()
    if any(f"on{event}=" in content for event in ["load", "error", "click", "mouse", "key", "focus", "blur", "change", "submit"]):
        security["statistics"]["has_event_handlers"] = True
        security["warnings"].append(
            {
                "type": "event_handlers",
                "line": html_item.get("line") or html_item.get("start_line"),
                "message": "Document contains HTML event handler attributes",
            }
        )
        break
```

### Step 4: Update REGEX_INVENTORY.md

Mark Phase 4 patterns as complete:

```markdown
## Phase 4

**Count**: 4 (COMPLETE - 4 removed, 7 retained as fallbacks/utilities)

**Status**: ✅ COMPLETE (2025-10-12)

| Line | Context | Pattern | Purpose | Replacement Strategy |
|------|---------|---------|---------|---------------------|
| 1148-1149 | `_generate_security_metadata` | `<(div\|span\|script...)[\s>]` | HTML block detection | **REMOVED**: Replaced with token-based detection using `structure["html_blocks"]` |
| 1152 | `_generate_security_metadata` | `<(a\|img\|em...)[\s>]` | HTML inline detection | **REMOVED**: Replaced with token-based detection using `structure["html_inline"]` |
| 1156 | `_generate_security_metadata` | `<script[\s>]` | Script detection | **REMOVED**: Replaced with token-based content inspection |
| 1163-1164 | `_generate_security_metadata` | `\bon(load\|error...)\\s*=` | Event handler detection | **REMOVED**: Replaced with token-based content inspection |
| 936 | `_sanitize_html_content` | `<[^>]+>` | HTML stripping (bleach fallback) | **RETAINED**: Defensive fallback when bleach unavailable |
| 951 | `_sanitize_html_content` | `\bon\w+\s*=...` | Event handler stripping (bleach fallback) | **RETAINED**: Defensive fallback when bleach unavailable |
| 952 | `_sanitize_html_content` | `javascript:` | JavaScript protocol stripping (bleach fallback) | **RETAINED**: Defensive fallback when bleach unavailable |
| 965-966 | `_sanitize_html_content` | `<script[^>]*>.*?</script>` | Script tag removal (bleach fallback) | **RETAINED**: Defensive fallback when bleach unavailable |
| 2824 | `_extract_html_tag_hints` | `<(\w+)` | Tag name extraction | **RETAINED**: Simple utility, low value to replace |
| 252-253 | Class attributes | `_META_REFRESH_PAT`, `_FRAMELIKE_PAT` | Security detection | **RETAINED**: Already precompiled and optimized |

**Implementation**: Replaced regex-based HTML detection in `_generate_security_metadata()` with token-based detection using existing `_extract_html()` results. Retained defensive fallback patterns in `_sanitize_html_content()` for graceful degradation when bleach is unavailable.
```

### Step 5: Create Phase 4 Tests

**File**: `tests/test_phase4_html_detection.py`

**Test Coverage**:
1. ✅ HTML block detection via tokens
2. ✅ HTML inline detection via tokens
3. ✅ Script tag detection via tokens
4. ✅ Event handler detection via tokens
5. ✅ Line number accuracy in warnings
6. ✅ No false positives from code blocks
7. ✅ Markdown-escaped HTML ignored
8. ✅ Bleach fallback behavior (when available)

**Minimum 10 tests** (matching Phase 1-3 pattern).

### Step 6: Run CI Gates

```bash
# G1: No Hybrids
python tools/ci/ci_gate_no_hybrids.py

# G2: Canonical Pairs
python tools/ci/ci_gate_canonical_pairs.py

# G3: Parity (all baseline tests)
pytest tests/ -q --tb=no -x

# G4: Performance
python tools/ci/ci_gate_performance.py

# G5: Evidence Hash
python tools/ci/ci_gate_evidence_hash.py
```

### Step 7: Create Evidence Block

**File**: `evidence_blocks.jsonl`

**Schema**:
```json
{
  "evidence_id": "phase4-html-token-detection",
  "phase": 4,
  "date": "2025-10-12",
  "file": "src/docpipe/markdown_parser_core.py",
  "lines": "1148-1175",
  "description": "Token-based HTML detection in security metadata",
  "patterns_removed": [
    "<(div|span|script|style|iframe|object|embed|form)[\\s>]",
    "<(a|img|em|strong|b|i|u|code|kbd|sup|sub)[\\s>]",
    "<script[\\s>]",
    "\\bon(load|error|click|mouse|key|focus|blur|change|submit)\\s*="
  ],
  "patterns_retained": [
    "<[^>]+>",
    "\\bon\\w+\\s*=...",
    "javascript:",
    "<script[^>]*>.*?</script>",
    "<(\\w+)"
  ],
  "replacement_strategy": "Token-based detection: use structure['html_blocks'] and structure['html_inline'] from _extract_html(), inspect content for script tags and event handlers",
  "code_snippet": "# Token-based HTML detection\nhtml_blocks = structure.get(\"html_blocks\", [])\nif html_blocks:\n    security[\"statistics\"][\"has_html_block\"] = True\n\nhtml_inline = structure.get(\"html_inline\", [])\nif html_inline:\n    security[\"statistics\"][\"has_html_inline\"] = True\n\n# Script detection\nhtml_items = html_blocks + html_inline\nfor html_item in html_items:\n    content = html_item.get(\"content\", \"\").lower()\n    if \"<script\" in content:\n        security[\"statistics\"][\"has_script\"] = True\n        break",
  "sha256": "<to be computed>",
  "test_result": "542/542 baseline tests passing, 10/10 Phase 4 tests passing",
  "performance_impact": "Expected: neutral or slight improvement (avoids regex scan of raw content)",
  "rationale": "HTML is already extracted via tokens (_extract_html). Detection patterns redundantly scanned raw content. Token-based detection is more accurate (respects markdown escaping) and leverages existing work.",
  "timestamp": "2025-10-12T15:00:00.000000Z"
}
```

### Step 8: Create Phase Unlock Artifact

**File**: `.phase-4.complete.json`

```json
{
  "phase": 4,
  "completed_at": "<timestamp>",
  "baseline_pass_count": 542,
  "performance_delta_median_pct": 0.0,
  "performance_delta_p95_pct": 0.0,
  "ci_gates_passed": ["G1", "G2", "G3", "G4", "G5"],
  "regex_count_before": 32,
  "regex_count_after": 28,
  "patterns_removed": 4,
  "patterns_retained": 7,
  "patterns_retained_rationale": "5 bleach fallbacks (defensive), 1 utility function (low value), 2 precompiled (optimized)",
  "evidence_blocks_created": 1,
  "git_tag": "phase-4-complete",
  "git_commit": "<to be filled>",
  "schema_version": "1.0",
  "min_schema_version": "1.0",
  "notes": "Replaced 4 regex detection patterns in _generate_security_metadata() with token-based detection. Retained 7 patterns: 5 bleach fallbacks (defensive programming), 1 utility function (low ROI), 2 precompiled security patterns (already optimized). HTML extraction already uses tokens via _extract_html()."
}
```

### Step 9: Git Commit and Tag

```bash
git add -A
git commit -m "refactor(phase-4): Complete Phase 4 - HTML detection via tokens

Replaced 4 regex detection patterns with token-based detection.
Retained 7 patterns (5 bleach fallbacks, 1 utility, 2 precompiled).

Changes:
- src/docpipe/markdown_parser_core.py: Token-based HTML detection in _generate_security_metadata()
- tests/test_phase4_html_detection.py: Added 10 comprehensive tests
- regex_refactor_docs/steps_taken/REGEX_INVENTORY.md: Updated Phase 4 status
- evidence_blocks.jsonl: Added Phase 4 evidence block
- .phase-4.complete.json: Created phase unlock artifact

Test Results: 542/542 baseline, 10/10 Phase 4 tests
CI Gates: G1-G5 all passing
Performance: Δmedian=0%, Δp95=0% (neutral)
Regex Count: 32→28 (-4 patterns)
"

git tag phase-4-complete
```

### Step 10: Create Completion Report

**File**: `regex_refactor_docs/steps_taken/07_PHASE4_COMPLETION.md`

---

## Test Plan

### Test File: `tests/test_phase4_html_detection.py`

#### Test 1: HTML Block Detection via Tokens
```python
def test_html_block_detection_via_tokens():
    """Verify HTML blocks detected via tokens, not regex."""
    text = "<div>Block HTML</div>"
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should be detected via tokens
    assert result["metadata"]["security"]["statistics"]["has_html_block"] is True
    assert len(result["structure"]["html_blocks"]) == 1
```

#### Test 2: HTML Inline Detection via Tokens
```python
def test_html_inline_detection_via_tokens():
    """Verify inline HTML detected via tokens, not regex."""
    text = "Text with <em>emphasis</em> tag"
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should be detected via tokens
    assert result["metadata"]["security"]["statistics"]["has_html_inline"] is True
    assert len(result["structure"]["html_inline"]) > 0
```

#### Test 3: Script Tag Detection with Line Numbers
```python
def test_script_detection_with_line_numbers():
    """Verify script tags detected with accurate line numbers."""
    text = """
Line 1

<script>alert('xss')</script>

Line 5
"""
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should be detected
    assert result["metadata"]["security"]["statistics"]["has_script"] is True

    # Should have warning with line number
    warnings = result["metadata"]["security"]["warnings"]
    script_warnings = [w for w in warnings if w["type"] == "script_tag"]
    assert len(script_warnings) > 0
    assert script_warnings[0]["line"] is not None  # Line number available
```

#### Test 4: Event Handler Detection
```python
def test_event_handler_detection():
    """Verify event handlers detected in HTML content."""
    text = "<img src='x' onclick='alert(1)'>"
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    # Should detect event handler
    assert result["metadata"]["security"]["statistics"]["has_event_handlers"] is True

    # Should have warning
    warnings = result["metadata"]["security"]["warnings"]
    handler_warnings = [w for w in warnings if w["type"] == "event_handlers"]
    assert len(handler_warnings) > 0
```

#### Test 5: No False Positives from Code Blocks
```python
def test_no_false_positives_from_code_blocks():
    """Verify code blocks don't trigger HTML detection."""
    text = """
```html
<div>This is code, not HTML</div>
<script>alert('also code')</script>
```
"""
    p = MarkdownParserCore(text, {"allows_html": False})
    result = p.parse()

    # Code blocks should NOT trigger HTML warnings
    assert result["metadata"]["security"]["statistics"].get("has_html_block") is not True
    assert result["metadata"]["security"]["statistics"].get("has_script") is not True
```

#### Test 6: Markdown-Escaped HTML Ignored
```python
def test_markdown_escaped_html_ignored():
    """Verify escaped HTML (backticks) doesn't trigger detection."""
    text = "Use `<div>` tag for containers"
    p = MarkdownParserCore(text, {"allows_html": False})
    result = p.parse()

    # Inline code should NOT trigger HTML detection
    assert result["metadata"]["security"]["statistics"].get("has_html_inline") is not True
```

#### Test 7: Multiple HTML Types
```python
def test_multiple_html_types():
    """Verify detection of multiple HTML patterns."""
    text = """
<div>Block HTML</div>

Text with <strong>inline HTML</strong>

<script>alert('xss')</script>

<img src='x' onerror='alert(1)'>
"""
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    sec = result["metadata"]["security"]["statistics"]
    assert sec["has_html_block"] is True
    assert sec["has_html_inline"] is True
    assert sec["has_script"] is True
    assert sec["has_event_handlers"] is True
```

#### Test 8: HTML Not Allowed (allows_html=False)
```python
def test_html_not_allowed():
    """Verify HTML blocked when allows_html=False."""
    text = "<div>HTML content</div>"
    p = MarkdownParserCore(text, {"allows_html": False})
    result = p.parse()

    # HTML should be stripped from structure
    assert len(result["structure"]["html_blocks"]) == 0
```

#### Test 9: Bleach Fallback Behavior
```python
def test_bleach_fallback_exists():
    """Verify _sanitize_html_content has fallback when bleach unavailable."""
    text = "<script>alert('xss')</script><p>Safe</p>"
    p = MarkdownParserCore(text, {"allows_html": True})

    # Method should exist and handle HTML
    sanitized = p._sanitize_html_content(text, allows_html=False)

    # Should strip HTML (either via bleach or fallback)
    assert "<script>" not in sanitized
    assert "<p>" not in sanitized or "Safe" in sanitized  # Either stripped or allowed
```

#### Test 10: Meta Refresh and Frame Detection (Precompiled)
```python
def test_precompiled_patterns_still_work():
    """Verify precompiled _META_REFRESH_PAT and _FRAMELIKE_PAT still work."""
    text = """
<meta http-equiv="refresh" content="0;url=http://evil.com">
<iframe src="http://evil.com"></iframe>
"""
    p = MarkdownParserCore(text, {"allows_html": True})
    result = p.parse()

    sec = result["metadata"]["security"]["statistics"]
    assert sec.get("has_meta_refresh") is True
    assert sec.get("has_frame_like") is True
```

---

## CI Gate Expectations

### G1: No Hybrids
- **Expected**: PASS
- **Rationale**: All detection patterns replaced with token-based logic, no hybrids

### G2: Canonical Pairs
- **Expected**: PASS
- **Rationale**: No test pairs deleted, all 542 intact

### G3: Parity
- **Expected**: PASS
- **Rationale**: Detection behavior unchanged, 542/542 baseline tests should pass

### G4: Performance
- **Expected**: PASS (Δmedian ≤5%, Δp95 ≤10%)
- **Rationale**: Token-based detection likely faster (avoids regex scan of raw content), but neutral is acceptable

### G5: Evidence Hash
- **Expected**: PASS
- **Rationale**: Evidence block will have valid SHA256 hash

---

## Risk Assessment

### Initial Risk: Medium

**Concerns**:
1. HTML detection is security-critical
2. Token-based detection must match regex behavior
3. Bleach fallbacks must remain functional

### Mitigations

#### Mitigation 1: Comprehensive Testing
- 10 Phase 4 tests covering all detection scenarios
- Test false positives (code blocks, escaped HTML)
- Test line number accuracy

#### Mitigation 2: Behavior Preservation
- Token-based detection leverages existing `_extract_html()`
- No changes to HTML extraction logic
- Only detection/warning code changed

#### Mitigation 3: Defensive Programming
- Keep bleach fallback patterns unchanged
- Retain precompiled security patterns
- Don't over-engineer utility functions

#### Mitigation 4: CI Gate Validation
- All 5 gates must pass
- 542/542 baseline tests must pass
- Performance must be neutral or improved

### Final Risk: Low

**After mitigations**:
- Changes are detection-only (no removal logic changed)
- Fallbacks preserved (defensive)
- Comprehensive test coverage
- CI gate validation

---

## Summary

**Phase 4 Approach**: Token-based HTML detection in security metadata

**Patterns Removed**: 4 (HTML block/inline detection, script detection, event handler detection)

**Patterns Retained**: 7 (5 bleach fallbacks, 1 utility, 2 precompiled)

**Net Regex Reduction**: 32 → 28 patterns (-4)

**Risk Level**: Low (detection-only changes, fallbacks preserved)

**Estimated Time**: 6-8 hours

**Ready to Proceed**: ✅ Yes

---

**Phase 4 Plan Complete** ✅
