# Critical Invariants - Implementation Guide
# Fix These 4 Gaps Before Step 1

**Date**: 2025-10-19
**Priority**: 🔴 **BLOCKING** - Must fix before starting refactoring
**Effort**: ~6 hours (1 day)

---

## Quick Start - 4 Critical Fixes

These invariants prevent silent data corruption and nondeterministic behavior. All must be implemented before Step 1 (index building).

---

### 1. Normalize Before Parse (2 hours) - BLOCKS STEP 1

**Problem**: Normalizing after parsing causes token.map to mismatch self.lines.

**Current Flow** (WRONG):
```
1. MarkdownIt.parse(raw_text) → tokens
   token.map = [5, 7]  # Line offsets from raw_text

2. TokenWarehouse.__init__(tokens, text)
   text = normalize(raw_text)  # Lines change!
   self.lines = text.splitlines()

3. wh.lines[token.map[0]]  # ❌ Wrong line! Offsets don't match
```

**Correct Flow**:
```
1. Normalize text FIRST
   normalized = normalize(raw_text)

2. MarkdownIt.parse(normalized) → tokens
   token.map = [5, 7]  # Offsets from normalized text

3. TokenWarehouse.__init__(tokens, normalized)
   self.lines = normalized.splitlines()

4. wh.lines[token.map[0]]  # ✅ Correct! Offsets match
```

**Implementation**:

**File**: `skeleton/doxstrux/markdown_parser_core.py` (or equivalent entry point)

```python
#!/usr/bin/env python3
"""Markdown parser with correct normalization order."""

import unicodedata
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse


def normalize_markdown(content: str) -> str:
    """
    Normalize markdown content BEFORE parsing.

    This ensures token.map offsets match line indices.

    CRITICAL: This must happen BEFORE MarkdownIt.parse().
    """
    # Unicode NFC normalization (composed form)
    # Example: é (e + combining acute) → é (single character)
    normalized = unicodedata.normalize('NFC', content)

    # CRLF → LF normalization
    # Ensures consistent line counting across platforms
    normalized = normalized.replace('\r\n', '\n')

    return normalized


def parse_markdown(content: str) -> tuple[list, SyntaxTreeNode, str]:
    """
    Parse markdown with proper normalization order.

    Returns:
        (tokens, tree, normalized_text) - All use same coordinate system
    """
    # 1. Normalize FIRST
    normalized = normalize_markdown(content)

    # 2. Parse normalized text
    md = MarkdownIt("gfm-like")
    md.enable(["table", "strikethrough"])

    tokens = md.parse(normalized)
    tree = SyntaxTreeNode(tokens)

    # 3. Return normalized text (TokenWarehouse will use this)
    return tokens, tree, normalized


class MarkdownParserCore:
    """Parser with correct normalization."""

    def parse(self, content: str) -> dict:
        # Parse with normalized text
        tokens, tree, normalized = parse_markdown(content)

        # TokenWarehouse receives already-normalized text
        wh = TokenWarehouse(tokens, tree, normalized)

        # Extract all features
        return {
            "sections": wh.extract_sections(),
            "headings": wh.extract_headings(),
            # ... other features
        }
```

**Modify**: `skeleton/doxstrux/markdown/utils/token_warehouse.py`

```python
def __init__(self, tokens, tree, text):
    """
    Initialize warehouse.

    CRITICAL: text must be pre-normalized (NFC + LF).
    Do NOT normalize here - tokens are already parsed from this text.
    """
    self.tokens = tokens
    self.tree = tree

    # Text is already normalized - just store it
    self.text = text
    self.lines = text.splitlines(keepends=True)

    # Build indices
    self.by_type = defaultdict(list)
    self.pairs = {}
    self.pairs_rev = {}
    self.parents = {}
    self.children = defaultdict(list)
    self.sections = []
    self._line_starts = self._compute_line_starts()

    self._build_indices()

def _compute_line_starts(self) -> list[int]:
    """Compute byte offsets of line starts."""
    starts = [0]
    pos = 0
    for line in self.lines:
        pos += len(line)
        starts.append(pos)
    return starts
```

**Add Invariant Test**:

```python
def test_normalization_coordinate_integrity():
    """CRITICAL: Token.map must match normalized text lines."""

    # Content with issues that normalization fixes
    content = "# Café\r\nParagraph with é"  # Decomposed unicode + CRLF

    # Parse correctly (normalize first)
    tokens, tree, normalized = parse_markdown(content)
    wh = TokenWarehouse(tokens, tree, normalized)

    # Find heading token
    h1_token = next(t for t in tokens if t.type == "heading_open")

    # Extract line using token.map
    line_idx = h1_token.map[0]
    line_content = wh.lines[line_idx]

    # MUST find composed "Café" (not decomposed)
    assert "Café" in line_content, \
        f"Normalization failed: {line_content!r}"

    # MUST NOT have CRLF
    assert "\r" not in line_content, \
        f"CRLF normalization failed: {line_content!r}"

    # Verify get_token_text works correctly
    h1_text = wh.get_token_text(tokens.index(h1_token))
    assert "Café" in h1_text


def test_normalization_before_parse_not_after():
    """WRONG: Normalizing after parse breaks offsets."""

    raw_content = "# Test\r\nLine 2"

    # WRONG WAY (what we're fixing)
    md = MarkdownIt()
    tokens_wrong = md.parse(raw_content)  # ❌ Parse raw text

    # Then normalize (too late!)
    normalized_wrong = raw_content.replace('\r\n', '\n')
    lines_wrong = normalized_wrong.splitlines(keepends=True)

    # Token.map points to wrong lines
    h1_token = next(t for t in tokens_wrong if t.type == "heading_open")
    # h1_token.map[1] might be 1 (second line in raw)
    # but lines_wrong[1] is different because CRLF removed

    # RIGHT WAY
    tokens_right, tree_right, normalized_right = parse_markdown(raw_content)
    wh = TokenWarehouse(tokens_right, tree_right, normalized_right)

    # Now token.map matches wh.lines
    assert tokens_right[0].map is not None
```

**Add to Docs** (DOXSTRUX_REFACTOR.md → Executive Summary → Assumptions):

```markdown
### INVARIANT 1: Coordinate System Integrity

**All coordinates (token.map, line numbers, byte offsets) are derived from the same normalized text (NFC + LF).**

**Order of Operations** (CRITICAL):
1. Normalize content (NFC + CRLF→LF)
2. Parse with MarkdownIt (tokens.map uses normalized offsets)
3. Pass normalized text to TokenWarehouse
4. All get_line_range(), get_token_text(), section_of() use consistent offsets

**Implementation**:
- `parse_markdown()` normalizes BEFORE calling MarkdownIt.parse()
- TokenWarehouse receives pre-normalized text (do NOT normalize in `__init__`)
- Test: `token.map[0]` must correctly index into `wh.lines`

**Why This Matters**:
- Unicode decomposed forms (é = e + combining acute) have different byte lengths
- CRLF vs LF changes line counts
- If normalization happens after parsing, token.map points to wrong lines
- Results in silent bugs: extracted text doesn't match expected content
```

---

### 2. Freeze Section Shape (1 hour) - BLOCKS STEP 1

**Problem**: Multiple tuple formats make code brittle.

**Solution**: Use dataclass internally, convert to tuple for API.

**File**: `skeleton/doxstrux/markdown/utils/token_warehouse.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Section:
    """
    Canonical section structure.

    INVARIANT: This shape must NEVER change.
    All code must use this exact structure.
    """
    start_line: int
    end_line: Optional[int]  # None if section not closed yet
    token_idx: int
    level: int  # 1-6 (h1-h6)
    title: str

    def to_tuple(self) -> tuple[int, Optional[int], int, int, str]:
        """Convert to legacy tuple format for backward compatibility."""
        return (self.start_line, self.end_line, self.token_idx, self.level, self.title)

    @classmethod
    def from_tuple(cls, t: tuple) -> 'Section':
        """Parse legacy tuple format."""
        return cls(*t)


def _build_indices(self):
    """Build indices with frozen Section dataclass."""
    sections: list[Section] = []
    section_stack: list[Section] = []

    for idx, tok in enumerate(self.tokens):
        if tok.type == "heading_open":
            level = int(tok.tag[1])
            start_line = tok.map[0] if tok.map else 0

            # Close higher/equal level sections
            while section_stack and section_stack[-1].level >= level:
                old_section = section_stack.pop()
                end_line = tok.map[0] - 1 if tok.map else None

                # Replace with closed version
                closed_section = Section(
                    old_section.start_line,
                    end_line,  # Fill end_line
                    old_section.token_idx,
                    old_section.level,
                    old_section.title
                )
                # Find and replace in sections list
                for i, s in enumerate(sections):
                    if s.token_idx == old_section.token_idx:
                        sections[i] = closed_section
                        break

            # Open new section
            new_section = Section(start_line, None, idx, level, "")
            sections.append(new_section)
            section_stack.append(new_section)

        elif tok.type == "inline" and section_stack:
            # Fill title for most recent section
            current = section_stack[-1]
            titled_section = Section(
                current.start_line,
                current.end_line,
                current.token_idx,
                current.level,
                tok.content  # Fill title
            )

            # Replace in both lists
            for i, s in enumerate(sections):
                if s.token_idx == current.token_idx:
                    sections[i] = titled_section
                    break
            section_stack[-1] = titled_section

    # Close any remaining open sections
    for section in section_stack:
        end_line = len(self.lines) - 1
        closed = Section(
            section.start_line,
            end_line,
            section.token_idx,
            section.level,
            section.title
        )
        for i, s in enumerate(sections):
            if s.token_idx == section.token_idx:
                sections[i] = closed
                break

    # Store as tuples for API compatibility
    self.sections = [s.to_tuple() for s in sections]
```

**Test**:

```python
def test_section_shape_frozen():
    """Section tuple must have exact shape."""
    content = "# H1\nPara\n## H2\nPara"

    wh = TokenWarehouse.from_markdown(content)

    # Every section must be (int, int|None, int, int, str)
    for section in wh.sections:
        assert len(section) == 5, f"Section wrong length: {section}"

        start_line, end_line, token_idx, level, title = section

        assert isinstance(start_line, int)
        assert end_line is None or isinstance(end_line, int)
        assert isinstance(token_idx, int)
        assert isinstance(level, int) and 1 <= level <= 6
        assert isinstance(title, str)
```

**Add to Docs**:

```markdown
### INVARIANT 2: Section Contract Frozen

**Section = (start_line:int, end_line:int|None, token_idx:int, level:int, title:str)**

**Implementation**:
- Use `@dataclass Section` internally (type-safe, immutable)
- Convert to tuple via `section.to_tuple()` for API compatibility
- NEVER use alternate tuple shapes (no temp tuples with extra fields)

**Why This Matters**:
- Multiple tuple shapes cause hard-to-debug errors
- Tests break when shape changes
- Collectors expect consistent structure
```

---

### 3. Deterministic Dispatch (2 hours) - BLOCKS STEP 3

**Problem**: `list(set(...))` makes order nondeterministic.

**File**: `skeleton/doxstrux/markdown/utils/token_warehouse.py`

```python
def __init__(self, tokens, tree, text):
    # ... existing code ...

    # Track registered collectors for dedup
    self._registered_collector_ids = set()  # Use IDs for dedup
    self._collectors_in_order = []  # Preserve registration order

def register_collector(self, collector):
    """
    Register collector with deterministic order.

    INVARIANT: Dispatch order matches registration order (stable).
    """
    collector_id = id(collector)  # Unique ID

    # Skip if already registered (stable dedup)
    if collector_id in self._registered_collector_ids:
        return

    self._registered_collector_ids.add(collector_id)
    self._collectors_in_order.append(collector)

    # Add to routing tables (type-based and tag-based)
    for token_type in getattr(collector, 'handles_types', []):
        self._routing[token_type].append(collector)

    for tag in getattr(collector, 'handles_tags', []):
        self._tag_routing[tag].append(collector)

def dispatch_all(self):
    """
    Dispatch to collectors in deterministic order.

    INVARIANT: Order is identical across runs.
    """
    # Collectors run in registration order (not set() random order)
    for collector in self._collectors_in_order:
        try:
            results = collector.collect(self)
            self._results[collector.name] = results
        except Exception as e:
            self._errors[collector.name] = str(e)
```

**Test**:

```python
def test_dispatch_order_deterministic():
    """Dispatch order must be identical across runs."""
    content = "# Test\n[link](url)\n**bold**"

    # Run 10 times, record dispatch order
    orders = []

    for _ in range(10):
        wh = TokenWarehouse.from_markdown(content)

        # Track collector execution order
        execution_order = []

        # Monkey-patch collectors to record calls
        for collector in wh._collectors_in_order:
            original_collect = collector.collect

            def make_wrapper(name):
                def wrapper(wh):
                    execution_order.append(name)
                    return original_collect(wh)
                return wrapper

            collector.collect = make_wrapper(collector.name)

        wh.dispatch_all()
        orders.append(tuple(execution_order))

    # All runs must have identical order
    unique_orders = set(orders)
    assert len(unique_orders) == 1, \
        f"Nondeterministic dispatch! Got {len(unique_orders)} different orders: {unique_orders}"
```

**Add to Docs**:

```markdown
### INVARIANT 3: Deterministic Dispatch Order

**Collectors execute in registration order (not set() random order).**

**Implementation**:
- Track `_collectors_in_order` list (preserves order)
- Use `set()` only for dedup check, not for storage
- Dispatch iterates `_collectors_in_order` (stable)

**Why This Matters**:
- `set()` has random iteration order (hash-based)
- Nondeterministic order causes flaky tests
- Baseline parity breaks unpredictably
- Debugging becomes impossible
```

---

### 4. Zero-Mismatch Canary Gate (1 hour) - BLOCKS PRODUCTION

**Problem**: Canary doesn't enforce 0.00% mismatch requirement.

**File**: `tools/check_canary_promotion.py` (new file)

```python
#!/usr/bin/env python3
"""Check if canary meets promotion gates."""

import json
import sys
from pathlib import Path


def check_promotion_gates(current_metrics: dict, baseline_metrics: dict) -> tuple[bool, list[str]]:
    """
    Validate canary against BINDING gates.

    Returns:
        (should_promote, reasons)
    """
    errors = []

    # GATE 1: Zero baseline mismatches (BINDING - 0.00% tolerance)
    mismatch_rate = current_metrics.get("baseline_mismatch_rate_pct", 100.0)
    if mismatch_rate > 0.0:
        errors.append(
            f"❌ GATE 1 FAILED: Baseline mismatch rate {mismatch_rate:.2f}% "
            f"(required: 0.00%)"
        )

    # GATE 2: Error rate threshold
    error_rate = current_metrics.get("error_rate_pct", 100.0)
    if error_rate > 0.1:
        errors.append(
            f"❌ GATE 2 FAILED: Error rate {error_rate:.2f}% (threshold: 0.1%)"
        )

    # GATE 3: Performance p50 aggregate
    delta_p50 = (
        (current_metrics.get("latency_p50_ms", 0) - baseline_metrics.get("latency_p50_ms", 1))
        / baseline_metrics.get("latency_p50_ms", 1) * 100
    )
    if delta_p50 > 3.0:
        errors.append(
            f"❌ GATE 3 FAILED: p50 regression {delta_p50:.1f}% (threshold: 3%)"
        )

    # GATE 4: Performance p95 aggregate
    delta_p95 = (
        (current_metrics.get("latency_p95_ms", 0) - baseline_metrics.get("latency_p95_ms", 1))
        / baseline_metrics.get("latency_p95_ms", 1) * 100
    )
    if delta_p95 > 8.0:
        errors.append(
            f"❌ GATE 4 FAILED: p95 regression {delta_p95:.1f}% (threshold: 8%)"
        )

    # GATE 5: Sample size
    parse_count = current_metrics.get("parse_count", 0)
    if parse_count < 1000:
        errors.append(
            f"❌ GATE 5 FAILED: Insufficient sample size {parse_count} (minimum: 1000)"
        )

    should_promote = len(errors) == 0
    return should_promote, errors


def main():
    current_path = Path("metrics/canary_current.json")
    baseline_path = Path("metrics/baseline.json")

    if not current_path.exists():
        print(f"❌ Missing current metrics: {current_path}", file=sys.stderr)
        sys.exit(1)

    if not baseline_path.exists():
        print(f"❌ Missing baseline metrics: {baseline_path}", file=sys.stderr)
        sys.exit(1)

    current = json.loads(current_path.read_text())
    baseline = json.loads(baseline_path.read_text())

    should_promote, errors = check_promotion_gates(current, baseline)

    if should_promote:
        print("✅ All promotion gates passed - PROMOTE")
        sys.exit(0)
    else:
        print("❌ Promotion gates failed - ROLLBACK")
        for error in errors:
            print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Add to CI** (`.github/workflows/canary_monitor.yml`):

```yaml
- name: Check promotion gates
  run: |
    python tools/check_canary_promotion.py

- name: Auto-rollback if gates fail
  if: failure()
  run: |
    echo "❌ Canary gates failed - triggering rollback"
    python tools/set_feature_flag.py USE_SKELETON_PARSER 0
    python tools/alert_oncall.py "Skeleton parser auto-rolled back"
```

**Add to Docs**:

```markdown
### INVARIANT 4: Zero-Mismatch Canary Gate (BINDING)

**Baseline mismatch rate must be 0.00% (zero tolerance).**

**Gates** (BINDING - automatic rollback):
1. Mismatch rate = 0.00% (any non-zero → rollback)
2. Error rate ≤ 0.1%
3. p50 latency ≤ baseline + 3%
4. p95 latency ≤ baseline + 8%
5. Sample size ≥ 1000 parses

**Why This Matters**:
- Even 0.01% mismatch = 1 in 10,000 documents broken
- Silent data corruption harder to detect than crashes
- Baseline parity is the PRIMARY safety net
```

---

## Testing All 4 Invariants

**Run these tests before Step 1**:

```bash
# 1. Normalization
pytest skeleton/tests/test_normalization_invariant.py -v

# 2. Section shape
pytest skeleton/tests/test_section_shape.py -v

# 3. Deterministic dispatch
pytest skeleton/tests/test_dispatch_determinism.py -v

# 4. Canary gates
python tools/check_canary_promotion.py

# All must pass
```

---

## Summary

**4 Critical Invariants** (6 hours total):

| # | Invariant | Effort | Blocks | Test |
|---|-----------|--------|--------|------|
| 1 | Normalize before parse | 2h | Step 1 | test_normalization_invariant.py |
| 2 | Freeze section shape | 1h | Step 1 | test_section_shape.py |
| 3 | Deterministic dispatch | 2h | Step 3 | test_dispatch_determinism.py |
| 4 | Zero-mismatch canary | 1h | Production | check_canary_promotion.py |

**All 4 must pass before proceeding to Step 1 (index building).**

---

**Created**: 2025-10-19
**Status**: 🔴 **BLOCKING** - Implement before refactoring starts
**Next**: Add invariants to DOXSTRUX_REFACTOR.md Executive Summary
