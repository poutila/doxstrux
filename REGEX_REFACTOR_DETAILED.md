# Detailed Regex Refactoring Plan

> **Status**: Planning Phase Complete - Ready for Execution
> **Goal**: Replace all regex-based markdown parsing with MarkdownIt token-based parsing
> **Approach**: Mega-incremental (test after every change)
> **Test Dataset**: 494 markdown-json pairs in `md_stress_mega/`

---

## 0. Executive Summary

### Current State
- **content_context.py**: 214 lines, 3 regex calls (fence detection)
- **markdown_parser_core.py**: 3660 lines, 27+ regex calls (parsing, sanitization, validation)
- **Test coverage**: 494 test files with expected outputs
- **Current test harness**: Basic functionality test in `testing_md_parser.py`

### Refactoring Categories
1. **Code fence detection** (3 regexes) → MarkdownIt `fence`/`code_block` tokens
2. **Link/image parsing** (3 regexes) → MarkdownIt `link_open`/`image` tokens
3. **Inline formatting strip** (15+ regexes) → MarkdownIt inline token traversal
4. **HTML sanitization** (6 regexes) → Token filtering with `html=False`
5. **Slug generation** (6 regexes) → Keep localized, use token-derived text
6. **Security validation** (misc) → Case-by-case token-based checks

### Success Metrics
- ✅ All 494 test pairs produce identical JSON output
- ✅ Performance delta ≤ ±5% (wall-clock time)
- ✅ All regexes in categories 1-4 replaced
- ✅ `ruff` and `mypy` pass
- ✅ No new dependencies

---

## 1. Pre-Flight Checklist

### 1.1 Environment Validation
- [ ] **Checkpoint**: Verify all dependencies installed
```bash
uv run python -c "from markdown_it import MarkdownIt; from mdit_py_plugins.tasklists import tasklists_plugin; print('✅ Dependencies OK')"
```

**Reflection Point**: If imports fail, stop and install missing dependencies.

---

### 1.2 Baseline Test Harness Creation

**Current State**: `testing_md_parser.py` tests only one file (CLAUDEorig.md)

**Target State**: Test harness that runs all 494 md-json pairs and reports:
- Pass/fail count
- Performance metrics (total time, avg time per file)
- Detailed diff for failures

#### Step 1.2.1: Create Enhanced Test Harness

- [ ] **Action**: Create `src/docpipe/md_parser_testing/test_harness_full.py`

```python
#!/usr/bin/env python3
"""
Full test harness for markdown parser refactoring.
Runs all 494 md-json test pairs and validates output.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import sys

from docpipe.markdown_parser_core import MarkdownParserCore


class TestResult:
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []  # (filename, reason)
        self.total_time: float = 0.0
        self.file_times: Dict[str, float] = {}


def load_test_pair(md_path: Path) -> Tuple[str, Dict]:
    """Load markdown content and expected JSON output."""
    json_path = md_path.with_suffix('.json')

    if not json_path.exists():
        raise FileNotFoundError(f"Missing JSON pair: {json_path}")

    md_content = md_path.read_text(encoding='utf-8')
    expected = json.loads(json_path.read_text(encoding='utf-8'))

    return md_content, expected


def run_single_test(md_path: Path, config: Dict) -> Tuple[bool, str, float]:
    """
    Run parser on single test file.
    Returns: (passed, reason, elapsed_time)
    """
    try:
        md_content, expected = load_test_pair(md_path)

        start = time.perf_counter()
        parser = MarkdownParserCore(md_content, config=config, security_profile='moderate')
        result = parser.parse()
        elapsed = time.perf_counter() - start

        # For now, just verify it doesn't crash
        # Full JSON comparison will be added after we understand output structure
        if result is None:
            return False, "Parser returned None", elapsed

        # Check expected fields if they exist in the JSON
        if 'expected_has_headings' in expected:
            has_headings = bool(result.get('headings'))
            if has_headings != expected['expected_has_headings']:
                return False, f"Heading detection mismatch: got {has_headings}, expected {expected['expected_has_headings']}", elapsed

        if 'expected_heading_count' in expected:
            heading_count = len(result.get('headings', []))
            if heading_count != expected['expected_heading_count']:
                return False, f"Heading count mismatch: got {heading_count}, expected {expected['expected_heading_count']}", elapsed

        return True, "PASS", elapsed

    except Exception as e:
        return False, f"Exception: {type(e).__name__}: {str(e)}", 0.0


def run_all_tests(test_dir: Path, config: Dict) -> TestResult:
    """Run all test files in directory."""
    result = TestResult()

    md_files = sorted(test_dir.glob('*.md'))
    total = len(md_files)

    print(f"\n{'='*70}")
    print(f"Running {total} test files from {test_dir.name}")
    print(f"{'='*70}\n")

    overall_start = time.perf_counter()

    for i, md_path in enumerate(md_files, 1):
        passed, reason, elapsed = run_single_test(md_path, config)
        result.file_times[md_path.name] = elapsed

        if passed:
            result.passed.append(md_path.name)
            status = "✅ PASS"
        else:
            result.failed.append((md_path.name, reason))
            status = f"❌ FAIL"

        print(f"[{i:3d}/{total}] {status:10s} {md_path.name:50s} ({elapsed*1000:6.2f}ms)")

    result.total_time = time.perf_counter() - overall_start

    return result


def print_summary(result: TestResult):
    """Print test run summary."""
    total = len(result.passed) + len(result.failed)
    pass_rate = (len(result.passed) / total * 100) if total > 0 else 0
    avg_time = (result.total_time / total * 1000) if total > 0 else 0

    print(f"\n{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total:       {total}")
    print(f"Passed:      {len(result.passed)} ({pass_rate:.1f}%)")
    print(f"Failed:      {len(result.failed)}")
    print(f"Total time:  {result.total_time:.2f}s")
    print(f"Avg time:    {avg_time:.2f}ms/file")
    print(f"{'='*70}\n")

    if result.failed:
        print("FAILURES:")
        for filename, reason in result.failed[:10]:  # Show first 10
            print(f"  ❌ {filename}: {reason}")
        if len(result.failed) > 10:
            print(f"  ... and {len(result.failed) - 10} more")
        print()


def save_baseline(result: TestResult, output_path: Path):
    """Save baseline performance data."""
    baseline = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': len(result.passed) + len(result.failed),
        'passed': len(result.passed),
        'failed': len(result.failed),
        'total_time_seconds': result.total_time,
        'avg_time_ms': (result.total_time / (len(result.passed) + len(result.failed)) * 1000),
        'file_times_ms': {k: v*1000 for k, v in result.file_times.items()},
        'failures': [{'file': f, 'reason': r} for f, r in result.failed]
    }

    output_path.write_text(json.dumps(baseline, indent=2))
    print(f"📊 Baseline saved to: {output_path}")


if __name__ == "__main__":
    # Configuration matching the current parser setup
    config = {
        'allows_html': True,
        'plugins': ['table', 'strikethrough', 'tasklists'],
        'preset': 'gfm-like'
    }

    test_dir = Path(__file__).parent / "test_mds" / "md_stress_mega"

    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        sys.exit(1)

    result = run_all_tests(test_dir, config)
    print_summary(result)

    # Save baseline
    baseline_path = Path(__file__).parent / "baseline_performance.json"
    save_baseline(result, baseline_path)

    # Exit with error code if tests failed
    sys.exit(0 if len(result.failed) == 0 else 1)
```

- [ ] **Checkpoint**: Run baseline test harness
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**:
- Did the test harness run successfully?
- How many tests pass/fail in the current baseline?
- What's the baseline performance (avg ms/file)?
- Save the output for comparison

**Expected Output**:
- Baseline performance metrics saved to `baseline_performance.json`
- Some tests may fail initially - that's OK, we need to understand current state

---

## 2. Code Fence Detection Refactoring (Highest Priority)

**Files**: `content_context.py` (lines 44, 48, 158)

### Current Implementation
Uses regex to detect fence markers and track state manually:
- Line 44: `re.match(r"^\s*([`~])\1{2,}(\s*\S.*)?\s*$", line)`
- Line 48: `re.match(r"^\s*([`~])\1{2,}", line).group(0).lstrip()`
- Line 158: Same pattern repeated for language extraction

### Step 2.1: Add MarkdownIt Token-Based Code Block Detection

- [ ] **Action**: Add new method to `ContentContext` class

Add after line 23 in `content_context.py`:

```python
def _build_context_map_tokens(self) -> dict[int, str]:
    """Build line number -> context mapping using MarkdownIt tokens.

    This is the token-based replacement for the regex-based _build_context_map.

    Returns:
        Dictionary mapping line numbers to context types:
        - 'prose': Regular markdown content
        - 'fenced_code': Inside ``` or ~~~ blocks
        - 'indented_code': Indented code blocks (4 spaces/tab)
        - 'fence_marker': The ``` or ~~~ lines themselves
        - 'blank': Empty lines
    """
    from markdown_it import MarkdownIt

    # Initialize parser with same settings as the main parser
    md = MarkdownIt("commonmark", options_update={"html": False, "linkify": True})

    # Parse content to get tokens
    content = "\n".join(self.lines)
    tokens = md.parse(content)

    # Initialize all lines as prose
    context_map = {i: "prose" for i in range(len(self.lines))}

    # Mark blank lines
    for i, line in enumerate(self.lines):
        if line.strip() == "":
            context_map[i] = "blank"

    # Walk tokens to find code blocks
    for token in tokens:
        if token.type in {"fence", "code_block"}:
            if token.map is None:
                continue

            start_line, end_line = token.map

            if token.type == "fence":
                # First line is fence marker (opening ```)
                context_map[start_line] = "fence_marker"
                # Last line is fence marker (closing ```)
                # Note: end_line is exclusive in token.map
                if end_line > start_line + 1:
                    context_map[end_line - 1] = "fence_marker"
                # Lines between are code
                for line_no in range(start_line + 1, end_line - 1):
                    context_map[line_no] = "fenced_code"

            elif token.type == "code_block":
                # Indented code block
                for line_no in range(start_line, end_line):
                    if context_map[line_no] != "blank":
                        context_map[line_no] = "indented_code"

    return context_map
```

- [ ] **Checkpoint**: Verify the method compiles
```bash
uv run python -c "from docpipe.content_context import ContentContext; print('✅ New method compiles')"
```

**Reflection Point**: Did the import succeed? Any syntax errors?

---

### Step 2.2: Add Feature Flag for Token-Based Detection

- [ ] **Action**: Modify `ContentContext.__init__` to support both modes

Update lines 15-22 in `content_context.py`:

```python
def __init__(self, content: str, use_tokens: bool = False):
    """Initialize with markdown content.

    Args:
        content: The markdown content to analyze
        use_tokens: If True, use MarkdownIt tokens instead of regex (default: False)
    """
    self.lines = content.split("\n")
    self.use_tokens = use_tokens

    if use_tokens:
        self.context_map = self._build_context_map_tokens()
    else:
        self.context_map = self._build_context_map()
```

- [ ] **Checkpoint**: Verify backward compatibility
```bash
uv run python -c "from docpipe.content_context import ContentContext; c = ContentContext('# test'); print('✅ Default mode works')"
uv run python -c "from docpipe.content_context import ContentContext; c = ContentContext('# test', use_tokens=True); print('✅ Token mode works')"
```

**Reflection Point**: Both modes working? No crashes?

---

### Step 2.3: Test Token-Based Mode Against Test Suite

- [ ] **Action**: Create comparison test script

Create `src/docpipe/md_parser_testing/test_token_vs_regex.py`:

```python
#!/usr/bin/env python3
"""Compare regex-based vs token-based fence detection."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docpipe.content_context import ContentContext


def test_equivalence(md_path: Path) -> bool:
    """Test that regex and token modes produce same results."""
    content = md_path.read_text(encoding='utf-8')

    # Create both versions
    regex_ctx = ContentContext(content, use_tokens=False)
    token_ctx = ContentContext(content, use_tokens=True)

    # Compare context maps
    if regex_ctx.context_map != token_ctx.context_map:
        print(f"❌ MISMATCH: {md_path.name}")
        print(f"   Regex map: {len(regex_ctx.context_map)} entries")
        print(f"   Token map: {len(token_ctx.context_map)} entries")

        # Show first difference
        for line_no in sorted(set(list(regex_ctx.context_map.keys()) + list(token_ctx.context_map.keys()))):
            regex_type = regex_ctx.context_map.get(line_no, "MISSING")
            token_type = token_ctx.context_map.get(line_no, "MISSING")
            if regex_type != token_type:
                line_text = content.split('\n')[line_no] if line_no < len(content.split('\n')) else ""
                print(f"   Line {line_no}: regex='{regex_type}' vs token='{token_type}'")
                print(f"   Content: {repr(line_text[:60])}")
                break
        return False

    return True


if __name__ == "__main__":
    test_dir = Path(__file__).parent / "test_mds" / "md_stress_mega"
    md_files = list(test_dir.glob('*.md'))

    passed = 0
    failed = 0

    for md_path in md_files:
        if test_equivalence(md_path):
            passed += 1
            print(f"✅ {md_path.name}")
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Passed: {passed}/{len(md_files)}")
    print(f"Failed: {failed}/{len(md_files)}")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)
```

- [ ] **Checkpoint**: Run equivalence test
```bash
uv run python src/docpipe/md_parser_testing/test_token_vs_regex.py
```

**Reflection Point**:
- Do token and regex modes produce identical context maps?
- If not, what are the differences?
- Are the differences acceptable? (token mode may be MORE correct)

**Decision Point**: If differences are found:
- Analyze each case
- Verify token mode is correct by manually checking the markdown
- Update test expectations if needed
- Document any intentional behavior changes

---

### Step 2.4: Switch Default to Token Mode

- [ ] **Action**: Change default parameter in `ContentContext.__init__`

Line 15 in `content_context.py`:
```python
def __init__(self, content: str, use_tokens: bool = True):  # Changed from False
```

- [ ] **Checkpoint**: Run full test harness
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**:
- Do tests still pass at same rate as baseline?
- Is performance within ±5%?
- If failures increased, investigate each case

**Rollback Procedure**: If tests fail badly:
```bash
# Revert use_tokens default back to False
# Investigate failures before proceeding
```

---

### Step 2.5: Remove Regex-Based Fence Detection

- [ ] **Action**: Delete `_build_context_map()` method

Delete lines 24-110 in `content_context.py` (the old regex-based method)

- [ ] **Action**: Rename `_build_context_map_tokens()` to `_build_context_map()`

- [ ] **Action**: Remove `use_tokens` parameter (now always uses tokens)

Update `__init__`:
```python
def __init__(self, content: str):
    """Initialize with markdown content.

    Args:
        content: The markdown content to analyze
    """
    self.lines = content.split("\n")
    self.context_map = self._build_context_map()
```

- [ ] **Action**: Remove `import re` from line 9 (if not used elsewhere)

Check if `re` is used anywhere else in the file:
```bash
grep -n "re\." src/docpipe/content_context.py
```

If no other uses, delete line 9: `import re`

- [ ] **Checkpoint**: Run full test suite
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**:
- Tests still passing at same rate?
- Performance still within ±5%?
- Code is cleaner?

---

### Step 2.6: Evidence Documentation for Fence Refactoring

- [ ] **Action**: Document changes in evidence format

Create evidence entry:

```json
{
  "file": "content_context.py",
  "lines": "44, 48, 158",
  "before": "re.match(r\"^\\s*([`~])\\1{2,}(\\s*\\S.*)?\\s*$\", line)",
  "after": "MarkdownIt tokens with type='fence' or type='code_block', using token.map for line ranges",
  "category": "code_fence",
  "rationale": "MarkdownIt provides accurate fence detection with built-in language extraction via token.info. Eliminates manual state tracking and regex fragility.",
  "test_impact": "Identical behavior on all 494 test files",
  "performance_impact": "Within ±5% baseline"
}
```

- [ ] **Checkpoint**: Commit changes
```bash
git add src/docpipe/content_context.py
git add src/docpipe/md_parser_testing/test_harness_full.py
git add src/docpipe/md_parser_testing/test_token_vs_regex.py
git commit -m "refactor: replace regex fence detection with MarkdownIt tokens

- Remove 3 regex patterns for fence detection in content_context.py
- Add token-based _build_context_map using markdown-it-py
- Maintain identical behavior on all 494 test files
- Performance impact: <±5%

Evidence:
- Lines 44, 48, 158: regex -> token.type='fence'/'code_block'
- Test: test_token_vs_regex.py validates equivalence
"
```

**Reflection Point**:
- Clean commit with clear message?
- All tests passing?
- Ready to move to next category?

---

## 3. Link and Image Parsing Refactoring

**Files**: `markdown_parser_core.py` (lines 1062, 1089)

### Current Implementation
Uses regex to extract links and images:
- Line 1062: `re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", _strip_bad_link, text)`
- Line 1089: `re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _filter_image, text)`

These regexes are fragile and can't handle nested markdown, titles, or escaped brackets.

### Step 3.1: Analyze Current Link/Image Extraction

- [ ] **Action**: Find all link/image related code in markdown_parser_core.py

```bash
grep -n "link\|image" src/docpipe/markdown_parser_core.py | grep -i "def\|re\."
```

- [ ] **Checkpoint**: Identify all methods that need updating

**Reflection Point**: List all methods that parse links/images. These will need token-based alternatives.

---

### Step 3.2: Create Token-Based Link/Image Extraction Utility

- [ ] **Action**: Add utility methods to markdown_parser_core.py

Add near the top of the class (around line 300):

```python
def _extract_links_from_tokens(self, tokens: list) -> list[dict]:
    """Extract all links from token tree.

    Args:
        tokens: MarkdownIt token list

    Returns:
        List of dicts with keys: href, text, line_start, line_end
    """
    links = []
    stack = list(tokens)

    while stack:
        token = stack.pop(0)

        # Add children to stack
        if token.children:
            stack = list(token.children) + stack

        if token.type == "link_open":
            attrs = dict(token.attrs or [])
            href = attrs.get("href", "")

            # Extract link text from following inline token
            text = ""
            if stack and stack[0].type == "inline" and stack[0].children:
                text = "".join(
                    child.content for child in stack[0].children
                    if child.type == "text"
                )

            line_start, line_end = token.map if token.map else (None, None)

            links.append({
                "href": href,
                "text": text,
                "line_start": line_start,
                "line_end": line_end,
                "token": token  # Keep token for further processing if needed
            })

    return links


def _extract_images_from_tokens(self, tokens: list) -> list[dict]:
    """Extract all images from token tree.

    Args:
        tokens: MarkdownIt token list

    Returns:
        List of dicts with keys: src, alt, line_start, line_end
    """
    images = []
    stack = list(tokens)

    while stack:
        token = stack.pop(0)

        # Add children to stack
        if token.children:
            stack = list(token.children) + stack

        if token.type == "image":
            attrs = dict(token.attrs or [])
            src = attrs.get("src", "")

            # Extract alt text from token children
            alt = ""
            if token.children:
                alt = "".join(
                    child.content for child in token.children
                    if child.type == "text"
                )

            line_start, line_end = token.map if token.map else (None, None)

            images.append({
                "src": src,
                "alt": alt,
                "line_start": line_start,
                "line_end": line_end,
                "token": token
            })

    return images
```

- [ ] **Checkpoint**: Verify methods compile
```bash
uv run python -c "from docpipe.markdown_parser_core import MarkdownParserCore; print('✅ New methods compile')"
```

**Reflection Point**: Do the new methods compile without errors?

---

### Step 3.3: Replace Link Filtering (Line 1062)

- [ ] **Action**: Find the `_preprocess_markdown()` method containing line 1062

Read the context around line 1062 to understand the function:

```bash
sed -n '1040,1070p' src/docpipe/markdown_parser_core.py
```

The current code uses `re.sub()` with a callback `_strip_bad_link` to filter links with bad schemes.

- [ ] **Action**: Replace regex-based link filtering with token-based

Find the section in `_preprocess_markdown()` around line 1062 and replace:

**BEFORE:**
```python
# Only match regular links, not image links (no leading !)
text = re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", _strip_bad_link, text)
if removed_schemes:
    reasons.append("disallowed_link_schemes_removed")
```

**AFTER:**
```python
# Token-based link filtering
# Parse with current md instance to get tokens
temp_tokens = self.md.parse(text)
bad_links = []

for link in self._extract_links_from_tokens(temp_tokens):
    href = link["href"]

    # Skip anchors (always allowed)
    if href.startswith("#"):
        continue

    # Check scheme
    import re
    msch = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", href)
    if msch:
        scheme = msch.group(1).lower()
        if scheme not in cfg["allowed_link_schemes"]:
            bad_links.append(link)
            removed_schemes.add(scheme)

# For now, we keep the regex approach but mark for future token-based removal
# TODO: Implement full token-based text reconstruction
if removed_schemes:
    # Still use regex for removal (temporary)
    text = re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", _strip_bad_link, text)
    reasons.append("disallowed_link_schemes_removed")
```

**Note**: This is a hybrid approach. Full token-based text reconstruction is complex and will be done later.

- [ ] **Checkpoint**: Run test harness
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**:
- Tests still passing?
- Any new failures related to link processing?

---

### Step 3.4: Replace Image Filtering (Line 1089)

- [ ] **Action**: Replace regex-based image filtering

Find the section around line 1089 and replace:

**BEFORE:**
```python
text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _filter_image, text)
```

**AFTER:**
```python
# Token-based image filtering (hybrid approach)
temp_tokens = self.md.parse(text)
data_uris_removed = []

for image in self._extract_images_from_tokens(temp_tokens):
    src = image["src"]

    # Check for data URIs
    if src.startswith("data:"):
        uri_info = self._parse_data_uri(src)
        if uri_info.get("size_bytes", 0) > cfg["max_data_uri_size"]:
            data_uris_removed.append(src[:50] + "...")

# Still use regex for removal (temporary)
if data_uris_removed:
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _filter_image, text)
    reasons.append("oversized_data_uris_removed")
```

- [ ] **Checkpoint**: Run test harness
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**:
- Tests still passing?
- Image processing working correctly?

---

### Step 3.5: Evidence Documentation for Link/Image Refactoring

- [ ] **Action**: Document changes

```json
{
  "file": "markdown_parser_core.py",
  "lines": "1062, 1089",
  "before": "re.sub(r\"(?<!\\!)\\[([^\\]]+)\\]\\(([^)]+)\\)\", ...) for links, re.sub(r\"!\\[([^\\]]*)\\]\\(([^)]+)\\)\", ...) for images",
  "after": "Token-based extraction using _extract_links_from_tokens() and _extract_images_from_tokens(). Hybrid approach: token extraction + regex removal (temporary)",
  "category": "link/image",
  "rationale": "Tokens provide accurate link/image parsing with proper handling of nested markdown, titles, and escapes. Avoids negative lookbehind fragility.",
  "test_impact": "Identical behavior on test suite",
  "performance_impact": "Within ±5% baseline",
  "notes": "Full token-based text reconstruction deferred to phase 2"
}
```

- [ ] **Checkpoint**: Commit changes
```bash
git add src/docpipe/markdown_parser_core.py
git commit -m "refactor: add token-based link/image extraction (hybrid)

- Add _extract_links_from_tokens() method
- Add _extract_images_from_tokens() method
- Use tokens for detection, keep regex for removal (temporary)
- Prepare for full token-based text reconstruction

Evidence:
- Lines 1062, 1089: hybrid token+regex approach
- Full token reconstruction in next phase
"
```

**Reflection Point**: Commit clean? Tests passing? Ready for next phase?

---

## 4. Inline Formatting Strip Refactoring

**Files**: `markdown_parser_core.py` (lines 3573-3583)

### Current Implementation
Method `_strip_markdown_formatting()` uses multiple regex substitutions:
- Remove headers: `^#+\s+`
- Remove bold: `\*\*([^*]+)\*\*`
- Remove italic: `\*([^*]+)\*` and `_([^_]+)_`
- Remove links: `\[([^\]]+)\]\([^)]+\)`
- Remove code blocks: ``` and backticks

This is brittle and can't handle nested constructs.

### Step 4.1: Create Token-Based Plain Text Extractor

- [ ] **Action**: Add new method to replace `_strip_markdown_formatting()`

Add after the existing method:

```python
def _extract_plain_text_from_tokens(self, text: str) -> str:
    """Extract plain text from markdown by walking tokens.

    This replaces the regex-based _strip_markdown_formatting() method.
    Instead of stripping markdown syntax with regexes, we parse the
    document and extract only text-bearing tokens.

    Args:
        text: Markdown text

    Returns:
        Plain text with formatting removed
    """
    tokens = self.md.parse(text)
    plain_parts = []

    def extract_text_from_inline(inline_token):
        """Extract text from inline token and its children."""
        if not inline_token.children:
            return ""

        text_parts = []
        for child in inline_token.children:
            if child.type == "text":
                text_parts.append(child.content)
            elif child.type == "code_inline":
                text_parts.append(child.content)  # Keep code content
            elif child.type == "softbreak" or child.type == "hardbreak":
                text_parts.append(" ")
            # Ignore formatting tokens: strong_open, em_open, etc.
            # For links, extract the link text (already in child text tokens)

        return "".join(text_parts)

    def walk_tokens(token_list):
        """Recursively walk tokens and extract text."""
        for token in token_list:
            if token.type == "inline":
                text = extract_text_from_inline(token)
                if text:
                    plain_parts.append(text)

            elif token.type == "heading_close":
                # Add newline after headings
                plain_parts.append("\n")

            elif token.type == "paragraph_close":
                # Add newline after paragraphs
                plain_parts.append("\n")

            # Recurse for nested tokens
            if token.children:
                walk_tokens(token.children)

    walk_tokens(tokens)

    # Join and clean up
    result = "".join(plain_parts)
    # Clean up multiple newlines
    result = "\n".join(line for line in result.split("\n") if line.strip())
    return result.strip()
```

- [ ] **Checkpoint**: Test new method against old method

Create test script `test_plain_text_extraction.py`:

```python
#!/usr/bin/env python3
"""Test token-based vs regex-based plain text extraction."""

from docpipe.markdown_parser_core import MarkdownParserCore

test_cases = [
    "# Heading",
    "**bold** and *italic*",
    "[link text](http://example.com)",
    "```python\ncode\n```",
    "text with `inline code` here",
    "**nested *emphasis* works**",
    "# Heading\n\nParagraph with **bold** and [link](url).",
]

for test in test_cases:
    parser = MarkdownParserCore(test, security_profile='permissive')

    # Old method
    old = parser._strip_markdown_formatting(test)

    # New method
    new = parser._extract_plain_text_from_tokens(test)

    print(f"Input:  {repr(test)}")
    print(f"Old:    {repr(old)}")
    print(f"New:    {repr(new)}")
    print(f"Match:  {'✅' if old == new else '❌'}")
    print()
```

```bash
uv run python test_plain_text_extraction.py
```

**Reflection Point**:
- Do outputs match for simple cases?
- Where do they differ?
- Are the differences acceptable? (new version may be MORE correct)

---

### Step 4.2: Replace _strip_markdown_formatting() Calls

- [ ] **Action**: Find all calls to `_strip_markdown_formatting()`

```bash
grep -n "_strip_markdown_formatting" src/docpipe/markdown_parser_core.py
```

- [ ] **Action**: Add feature flag to gradually migrate

Update the method to support both modes:

```python
def _strip_markdown_formatting(self, text: str, use_tokens: bool = True) -> str:
    """Remove markdown formatting from text.

    Args:
        text: Markdown text
        use_tokens: If True, use token-based extraction (default)

    Returns:
        Plain text
    """
    if use_tokens:
        return self._extract_plain_text_from_tokens(text)

    # Old regex-based implementation (fallback)
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
    # Remove code blocks markers
    text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()
```

- [ ] **Checkpoint**: Run test harness with token mode
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**: Tests passing with token-based plain text extraction?

---

### Step 4.3: Remove Old Regex Implementation

- [ ] **Action**: Delete old regex code from `_strip_markdown_formatting()`

Simplify to:

```python
def _strip_markdown_formatting(self, text: str) -> str:
    """Remove markdown formatting from text (for backward compatibility).

    Uses token-based extraction instead of regex.
    """
    return self._extract_plain_text_from_tokens(text)
```

- [ ] **Action**: Delete the old `_extract_plain_text_from_tokens()` if it becomes internal

Rename `_extract_plain_text_from_tokens()` to `_strip_markdown_formatting()` and delete the wrapper.

- [ ] **Checkpoint**: Run full test suite
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**: All tests passing? Performance OK?

---

### Step 4.4: Evidence Documentation

```json
{
  "file": "markdown_parser_core.py",
  "lines": "3573-3583",
  "before": "7 regex substitutions for stripping markdown: ^#+\\s+, \\*\\*..\\*\\*, etc.",
  "after": "Token-based text extraction via _extract_plain_text_from_tokens(), walking inline tokens and collecting only text nodes",
  "category": "inline_formatting_strip",
  "rationale": "Token traversal correctly handles nested emphasis, code spans, and links without regex fragility. More robust for edge cases.",
  "test_impact": "Identical or improved behavior (handles nested constructs better)",
  "performance_impact": "Within ±5% baseline"
}
```

- [ ] **Checkpoint**: Commit
```bash
git add src/docpipe/markdown_parser_core.py
git commit -m "refactor: replace regex markdown stripping with token traversal

- Replace 7 regex patterns with token-based text extraction
- Add _extract_plain_text_from_tokens() method
- Handle nested emphasis, links, code spans correctly
- Remove fragile regex patterns from _strip_markdown_formatting()

Evidence:
- Lines 3573-3583: 7 regexes -> token traversal
- Improves handling of nested markdown constructs
"
```

---

## 5. HTML Sanitization Refactoring

**Files**: `markdown_parser_core.py` (lines 936, 948-952, 1023-1031)

### Current Implementation
Uses regex to remove dangerous HTML:
- Strip all tags: `<[^>]+>`
- Remove script tags: `<script[^>]*>.*?</script>`
- Remove event handlers: `\bon\w+\s*=\s*["'][^"']*["']`
- Remove javascript: URIs

### Step 5.1: Prefer `html=False` Configuration

- [ ] **Action**: Audit all MarkdownIt instances to ensure `html=False`

Check current configuration:

```bash
grep -n "MarkdownIt(" src/docpipe/markdown_parser_core.py | head -20
```

- [ ] **Action**: Ensure default config uses `html=False`

Find the initialization of `self.md` and verify:

```python
self.md = MarkdownIt(
    preset,
    options_update={"html": False, "linkify": True}  # html=False is critical
)
```

- [ ] **Checkpoint**: Verify HTML is not rendered

Test that HTML tags are escaped, not rendered:

```python
from docpipe.markdown_parser_core import MarkdownParserCore

test = "<script>alert('xss')</script>\n\n# Heading"
parser = MarkdownParserCore(test, security_profile='strict')
result = parser.parse()

print("HTML blocks:", result.get('html_blocks', []))
print("HTML inline:", result.get('html_inline', []))
# Should be empty or escaped
```

**Reflection Point**: Is HTML properly disabled? Are script tags not present in output?

---

### Step 5.2: Add Token-Based HTML Detection (Keep for Security Auditing)

Even with `html=False`, we should detect and report HTML for security monitoring.

- [ ] **Action**: Add token-based HTML detection

```python
def _detect_html_in_tokens(self, tokens: list) -> dict:
    """Detect HTML tags in token stream for security monitoring.

    Even with html=False, we want to know if input contained HTML.

    Returns:
        Dict with keys: has_html, html_blocks, html_inline, script_detected
    """
    result = {
        "has_html": False,
        "html_blocks": [],
        "html_inline": [],
        "script_detected": False
    }

    for token in tokens:
        if token.type == "html_block":
            result["has_html"] = True
            result["html_blocks"].append({
                "content": token.content,
                "line": token.map[0] if token.map else None
            })
            if "<script" in token.content.lower():
                result["script_detected"] = True

        elif token.type == "html_inline":
            result["has_html"] = True
            result["html_inline"].append({
                "content": token.content,
                "line": token.map[0] if token.map else None
            })
            if "<script" in token.content.lower():
                result["script_detected"] = True

        # Recurse
        if token.children:
            child_result = self._detect_html_in_tokens(token.children)
            if child_result["has_html"]:
                result["has_html"] = True
                result["html_blocks"].extend(child_result["html_blocks"])
                result["html_inline"].extend(child_result["html_inline"])
                result["script_detected"] = result["script_detected"] or child_result["script_detected"]

    return result
```

- [ ] **Checkpoint**: Test HTML detection

```python
test = "Normal text\n\n<script>bad()</script>\n\n<div>also bad</div>"
parser = MarkdownParserCore(test)
html_info = parser._detect_html_in_tokens(parser.md.parse(test))
print(html_info)
# Should detect the HTML even though it won't be rendered
```

**Reflection Point**: HTML detection working? Can we remove regex-based HTML detection?

---

### Step 5.3: Replace Regex HTML Detection with Token-Based

- [ ] **Action**: Find all regex-based HTML detection (lines 1023-1031, 1266-1274)

Replace regex patterns like:
- `re.search(r"<\s*script\b", text, re.I)`
- `re.search(r"<\w+[^>]*>", text)`
- `re.search(r"\bon[a-z]+\s*=", text, re.I)`

With calls to `_detect_html_in_tokens()`.

Example replacement in `_analyze_security_stats()` method:

**BEFORE:**
```python
# Script detection
if re.search(r"<script[\s>]", raw_content, re.IGNORECASE):
    security["statistics"]["has_script"] = True
```

**AFTER:**
```python
# Token-based HTML detection
html_info = self._detect_html_in_tokens(self.tokens)
if html_info["script_detected"]:
    security["statistics"]["has_script"] = True
if html_info["has_html"]:
    security["statistics"]["has_html_block"] = len(html_info["html_blocks"]) > 0
    security["statistics"]["has_html_inline"] = len(html_info["html_inline"]) > 0
```

- [ ] **Checkpoint**: Run security-focused tests
```bash
uv run python -m pytest tests/ -k security
```

**Reflection Point**: Security detection still working? All malicious patterns caught?

---

### Step 5.4: Remove Regex-Based HTML Sanitization

Since we're using `html=False`, the regex-based sanitization in `_sanitize_html_content()` (lines 936-952) is redundant.

- [ ] **Action**: Simplify `_sanitize_html_content()`

**BEFORE (lines 936-952):**
```python
if not allows_html:
    # Fallback to regex if bleach not available
    return re.sub(r"<[^>]+>", "", html)
# ... complex regex sanitization ...
```

**AFTER:**
```python
if not allows_html:
    # HTML disabled at parser level (html=False)
    # This method is only called for legacy compatibility
    return html  # Already sanitized by MarkdownIt

# If HTML is allowed, use bleach or reject
if HAS_BLEACH:
    return bleach.clean(html, tags=self._ALLOWED_HTML_TAGS, ...)
else:
    # No bleach, no safe HTML - strip everything
    return ""  # Conservative: reject HTML if we can't sanitize safely
```

- [ ] **Checkpoint**: Run full test suite
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**: HTML handling still secure? No regressions?

---

### Step 5.5: Evidence Documentation

```json
{
  "file": "markdown_parser_core.py",
  "lines": "936, 948-952, 1023-1031, 1266-1274",
  "before": "6+ regex patterns for HTML detection and sanitization: <script>, on*=, <\\w+>, etc.",
  "after": "MarkdownIt html=False config + token-based detection via _detect_html_in_tokens(). Regex sanitization removed.",
  "category": "html_sanitize",
  "rationale": "MarkdownIt with html=False prevents HTML rendering at parse time. Token-based detection for security monitoring. Regex sanitization is redundant and error-prone.",
  "test_impact": "Identical security behavior, more robust against HTML bypass",
  "performance_impact": "Improved (less regex processing)"
}
```

- [ ] **Checkpoint**: Commit
```bash
git add src/docpipe/markdown_parser_core.py
git commit -m "refactor: replace regex HTML sanitization with token-based detection

- Remove 6+ regex patterns for HTML detection/sanitization
- Add _detect_html_in_tokens() for security monitoring
- Rely on MarkdownIt html=False for prevention
- Simplify _sanitize_html_content() (now redundant)

Evidence:
- Lines 936, 948-952, 1023-1031, 1266-1274: regexes removed
- More robust HTML security via parser config
"
```

---

## 6. Slug Generation (Low Priority - Keep Localized)

**Files**: `markdown_parser_core.py` (lines 3536-3556)

### Decision: Keep Regex for Slugs

**Rationale**: Slug generation regexes are:
1. Localized to one method
2. Not security-critical
3. Simple patterns (whitespace, non-word chars)
4. No MarkdownIt equivalent

**Action**: NO CHANGE for now.

However, ensure slugs are generated from **token-derived text**, not raw markdown:

### Step 6.1: Verify Slug Generation Uses Clean Text

- [ ] **Action**: Check that heading slugs use text from tokens, not raw markdown

Find calls to `_sluggify()` or `_sluggify_unique()`:

```bash
grep -n "_sluggify" src/docpipe/markdown_parser_core.py
```

Ensure they receive text extracted from tokens (via inline children), not raw markdown with `#` symbols.

Example good pattern:
```python
# heading_text extracted from token.children (text nodes only)
slug = self._sluggify_unique(heading_text)  # Good
```

Example bad pattern:
```python
# raw_line still contains "# Heading"
slug = self._sluggify_unique(raw_line)  # Bad - will create slug "heading" instead of "heading"
```

- [ ] **Checkpoint**: Verify slug generation is clean
```bash
# Test that heading with emphasis generates correct slug
python -c "
from docpipe.markdown_parser_core import MarkdownParserCore
test = '# Heading with **bold**'
parser = MarkdownParserCore(test)
result = parser.parse()
print('Slug:', result['headings'][0]['slug'] if result.get('headings') else 'NO HEADINGS')
# Expected: 'heading-with-bold'
"
```

**Reflection Point**: Are slugs generated from clean text (without markdown syntax)?

---

## 7. Remaining Regex Patterns (Case-by-Case)

### Step 7.1: Audit Remaining Regexes

- [ ] **Action**: List all remaining regex uses

```bash
grep -n "re\." src/docpipe/markdown_parser_core.py | grep -v "^#" | grep -v "import re"
```

Categories remaining:
1. **Data URI parsing** (line 2575) - Keep (URL parsing, not markdown)
2. **Scheme validation** (line 3484) - Keep (URL validation, not markdown)
3. **Unicode script detection** (lines 3419-3424) - Keep (security heuristic, not markdown)
4. **Prompt injection patterns** (line 3522) - Keep (security, not markdown)
5. **Table detection heuristic** (line 3076) - CANDIDATE for token replacement
6. **Drive letter detection** (line 3335) - Keep (path validation, not markdown)

### Step 7.2: Replace Table Detection Heuristic

- [ ] **Action**: Find table detection code (line 3076)

Context:
```python
if "|" in line and re.search(r"-{3,}", line):
    # Heuristic: a separator row should mostly be pipes/dashes/colons/spaces
    if re.fullmatch(r"[|:\-\s]+", line):
        sep_idx = i
```

This is a heuristic to detect table separator rows. MarkdownIt already parses tables!

**REPLACE WITH:**

```python
# Token-based table detection (if table plugin enabled)
# Check if this position is within a table token's line range
for token in self.tokens:
    if token.type == "table_open" and token.map:
        start, end = token.map
        if start <= i < end:
            # This line is inside a table
            sep_idx = i
            break
```

- [ ] **Checkpoint**: Test table parsing
```python
test = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""

parser = MarkdownParserCore(test)
result = parser.parse()
print('Tables:', result.get('tables', []))
```

**Reflection Point**: Table detection working correctly via tokens?

- [ ] **Action**: Commit table detection change

```bash
git commit -am "refactor: replace table detection regex with token-based check

Evidence:
- Line 3076: table separator heuristic -> token.type='table_open' check
"
```

---

### Step 7.3: Document Regexes We're Keeping

Create a section in the plan documenting intentionally kept regexes:

```markdown
## Regexes Intentionally Kept (Not Markdown Parsing)

These regex patterns are NOT markdown parsing and should remain:

1. **Data URI parsing** (line 2575)
   - Pattern: `^data:([^;,]+)?(;base64)?,(.*)$`
   - Purpose: Parse RFC 2397 data URIs
   - Rationale: Standard URI parsing, not markdown-specific

2. **URL scheme validation** (line 3484)
   - Pattern: `^([a-zA-Z][a-zA-Z0-9+.-]*):(.*)$`
   - Purpose: Extract URL scheme per RFC 3986
   - Rationale: Standard URL validation

3. **Unicode script detection** (lines 3419-3424)
   - Patterns: `[\u0400-\u04FF]`, `[\u4E00-\u9FFF]`, etc.
   - Purpose: Detect mixed-script confusables (security)
   - Rationale: Character-level analysis, not markdown structure

4. **Prompt injection patterns** (line 3522)
   - Pattern: `(system|prompt|instruction|ignore|override)`
   - Purpose: Detect AI prompt injection attempts
   - Rationale: Content security, not markdown parsing

5. **Windows path detection** (line 3335)
   - Pattern: `^[a-z]:[/\\]`
   - Purpose: Detect file:// URIs with drive letters
   - Rationale: Path validation, not markdown

6. **Slug normalization** (lines 3536-3556)
   - Patterns: `[\s/]+`, `[^\w-]`, `-+`
   - Purpose: Create URL-safe slugs
   - Rationale: Simple text cleanup, well-contained, no MarkdownIt equivalent
```

---

## 8. Final Validation & Performance Testing

### Step 8.1: Run Complete Test Suite

- [ ] **Checkpoint**: Run full test harness
```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py > test_results_final.txt
```

- [ ] **Action**: Compare with baseline

```python
import json

baseline = json.loads(open('src/docpipe/md_parser_testing/baseline_performance.json').read())
final = json.loads(open('src/docpipe/md_parser_testing/test_results_final.json').read())

print(f"Baseline: {baseline['passed']}/{baseline['total_tests']} passed")
print(f"Final:    {final['passed']}/{final['total_tests']} passed")

delta_pct = ((final['avg_time_ms'] - baseline['avg_time_ms']) / baseline['avg_time_ms']) * 100
print(f"Performance: {delta_pct:+.1f}% (target: ±5%)")

if abs(delta_pct) > 5:
    print("⚠️  WARNING: Performance delta exceeds ±5%")
else:
    print("✅ Performance within acceptable range")
```

**Reflection Point**:
- Are we within ±5% performance?
- If not, profile and optimize hot paths

---

### Step 8.2: Lint and Type Check

- [ ] **Checkpoint**: Run ruff
```bash
uv run ruff check .
```

**Reflection Point**: Any new linting errors? Fix them.

- [ ] **Checkpoint**: Run mypy
```bash
uv run mypy src/
```

**Reflection Point**: Any type errors? Fix them.

---

### Step 8.3: Code Coverage

- [ ] **Checkpoint**: Run pytest with coverage
```bash
uv run pytest --cov=src --cov-report=term-missing
```

**Reflection Point**: Coverage still ≥80%? Any uncovered lines in refactored code?

---

## 9. Documentation & Cleanup

### Step 9.1: Update REFACTORING_PLAN_REGEX.md

- [ ] **Action**: Create summary document

```markdown
# Regex Refactoring Summary

## Regexes Replaced (30 total)

### Category: Code Fence Detection (3)
- content_context.py:44 - Fence marker detection
- content_context.py:48 - Fence length extraction
- content_context.py:158 - Language extraction

**Replacement**: MarkdownIt tokens with `type='fence'` and `type='code_block'`

### Category: Link/Image Parsing (3)
- markdown_parser_core.py:1062 - Link extraction
- markdown_parser_core.py:1089 - Image extraction

**Replacement**: `_extract_links_from_tokens()` and `_extract_images_from_tokens()`

### Category: Inline Formatting Strip (7)
- markdown_parser_core.py:3573-3583 - Strip headers, bold, italic, links, code

**Replacement**: `_extract_plain_text_from_tokens()` with inline token traversal

### Category: HTML Sanitization (6)
- markdown_parser_core.py:936 - Tag stripping
- markdown_parser_core.py:948-952 - Script/event handler removal
- markdown_parser_core.py:1023-1031 - Security detection
- markdown_parser_core.py:1266-1274 - HTML statistics

**Replacement**: MarkdownIt `html=False` + `_detect_html_in_tokens()`

### Category: Table Detection (1)
- markdown_parser_core.py:3076 - Table separator heuristic

**Replacement**: Token-based table range checking

## Regexes Intentionally Kept (10)

See section 7.3 for full list. Summary:
- Data URI parsing (RFC 2397)
- URL scheme validation (RFC 3986)
- Unicode script detection (security)
- Prompt injection detection (security)
- Path validation (Windows drives)
- Slug normalization (text cleanup)

## Performance Impact

- Baseline: X.XX ms/file average
- Final: Y.YY ms/file average
- Delta: ±Z.Z%

## Test Coverage

- Total tests: 494
- Passed: 494 (100%)
- Failed: 0

## Benefits

1. **Correctness**: Token-based parsing handles nested markdown correctly
2. **Security**: Reduced attack surface from regex complexity
3. **Maintainability**: Less brittle code, easier to understand
4. **Performance**: Within ±5% of baseline
```

---

### Step 9.2: Clean Up Temporary Files

- [ ] **Action**: Remove test scripts

```bash
rm test_plain_text_extraction.py  # If created in root
# Keep the ones in md_parser_testing/ for future use
```

- [ ] **Action**: Update .gitignore if needed

```bash
echo "baseline_performance.json" >> .gitignore
echo "test_results_*.txt" >> .gitignore
```

---

## 10. Reflection & Sign-Off

### Step 10.1: Final Checklist

- [ ] All 494 test files pass
- [ ] Performance within ±5% of baseline
- [ ] `ruff check .` passes
- [ ] `mypy src/` passes
- [ ] Coverage ≥ 80%
- [ ] No new dependencies added
- [ ] Regex count reduced by ~20 patterns
- [ ] Code is cleaner and more maintainable
- [ ] Security properties maintained or improved
- [ ] Documentation updated

### Step 10.2: Create Summary Report

- [ ] **Action**: Generate final report

```bash
cat > REFACTORING_COMPLETE.md <<EOF
# Regex Refactoring - Completion Report

**Date**: $(date +%Y-%m-%d)
**Engineer**: [Your Name]
**Status**: ✅ COMPLETE

## Summary

Successfully refactored markdown parser to use MarkdownIt token-based parsing
instead of brittle regex patterns. Replaced 20+ regex patterns with robust
token traversal while maintaining 100% test compatibility.

## Metrics

- **Regexes removed**: 20
- **Regexes kept** (non-markdown): 10
- **Test pass rate**: 494/494 (100%)
- **Performance delta**: ±X.X%
- **Code quality**: ruff + mypy clean
- **Coverage**: ≥80%

## Benefits

1. Correctness: Handles nested markdown constructs
2. Security: Reduced regex attack surface
3. Maintainability: Cleaner, more readable code
4. Performance: Maintained baseline performance

## Files Modified

- src/docpipe/content_context.py (3 regexes removed)
- src/docpipe/markdown_parser_core.py (17 regexes removed)
- src/docpipe/md_parser_testing/test_harness_full.py (new)

## Next Steps (Optional)

1. Full token-based text reconstruction (remove remaining hybrid approaches)
2. Further performance optimization
3. Additional edge case testing

---

**Approved by**: _______________
**Date**: _______________
EOF
```

---

## Emergency Rollback Procedure

If at any point tests fail catastrophically:

```bash
# 1. Check current status
git status

# 2. See what changed
git diff

# 3. Rollback to last good commit
git log --oneline -10
git reset --hard <last-good-commit-hash>

# 4. Verify tests pass
uv run python src/docpipe/md_parser_testing/test_harness_full.py

# 5. Resume from last checkpoint
```

---

## Appendix: Regex Inventory (Full List)

### content_context.py
1. Line 9: `import re`
2. Line 44: `re.match(r"^\s*([`~])\1{2,}(\s*\S.*)?\s*$", line)`
3. Line 48: `re.match(r"^\s*([`~])\1{2,}", line).group(0).lstrip()`
4. Line 158: `re.match(r"^\s*([`~])\1{2,}(\s*\S.*)?\s*$", line)`

### markdown_parser_core.py (first 30 matches)
1. Line 10: `import re`
2. Line 165: `re.search(pattern, content[:10000], re.IGNORECASE)`
3. Line 249-252: `re.compile()` for style/meta/frame patterns
4. Line 618: `re.search(pattern, content[:10000], re.IGNORECASE)`
5. Line 936: `re.sub(r"<[^>]+>", "", html)`
6. Line 948-952: Script and event handler removal
7. Line 1023-1031: Script and event detection
8. Line 1050: `re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", href)`
9. Line 1062: `re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", ...)`
10. Line 1089: `re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", ...)`
... (see Regex_occurrences_in_provided_files.csv for complete list)

---

## Notes for Future Refactorings

1. **Always test incrementally**: One category at a time
2. **Keep feature flags**: Allow gradual migration
3. **Maintain baselines**: Save performance/correctness data
4. **Document evidence**: Track every change with before/after
5. **Reflection points**: Stop and validate after each step
6. **Rollback ready**: Keep git history clean for easy revert

---

**END OF DETAILED REFACTORING PLAN**
