# REGEX_REFACTOR_DETAILED — Merged Execution Plan (UPDATED)

> **Objective**: Remove all regex-based Markdown parsing from `content_context.py` and `markdown_parser_core.py` and replace with **MarkdownIt / mdit-py-plugins** token traversal — with identical outputs and no material perf regression.

> **Status**: Authoritative, ready for execution. Merges policy/gates from UPDATED plan with detailed execution steps from original detailed plan. **UPDATED** with critical bug fixes and architectural improvements.

> **Execution Model**: 8 macro commits (per category), each executed via micro checkpoints internally for safety.

---

## 🔧 CRITICAL UPDATES (Applied)

This plan has been updated to fix critical bugs identified in technical review:

### 1. Test Harness Fixes ✅
- **FIXED**: Result structure access bug (`result['structure']['headings']` not `result['headings']`)
- **ADDED**: Memory profiling with `tracemalloc` for peak memory tracking
- **ADDED**: Memory statistics (median/p95/mean MB) to performance reports
- **UPDATED**: All baseline comparison logic to include memory metrics

### 2. ContentContext Architecture ✅
- **FIXED**: ContentContext double-parsing issue
- **RECOMMENDED**: Option A - Remove ContentContext entirely, integrate into main parser
- **ALTERNATIVE**: Option B - Pass tokens from parent parser (if removal too invasive)
- **DECISION POINT**: Check ContentContext usage before choosing approach

### 3. URL Validation Security ✅
- **FIXED**: Exception handling now fails **closed** (rejects malformed URLs)
- **ADDED**: Blocked URLs tracking in security dict
- **ADDED**: Exception type logging for debugging
- **SECURITY**: Malformed URLs no longer silently pass validation

### 4. Timeout Implementation ✅
- **ADDED**: Specific location guidance (wrap `self.md.parse()` in `parse()` method)
- **ADDED**: Complete cross-platform implementation using `concurrent.futures`
- **ADDED**: Timeout value configuration from security profile

### 5. No Hybrids Policy ✅
- **UPDATED**: Allow feature flags during development for safe A/B testing
- **ADDED**: Clear before/after merge requirements
- **IMPROVED**: Developer experience while maintaining safety

### 6. Token Traversal Order ✅
- **FIXED**: Stack-based traversal replaced with proper depth-first recursion
- **FIXED**: Link text extraction uses adjacent token, not stack peek
- **IMPROVED**: Nested function approach for cleaner code

### 7. Frontmatter Plugin Usage ✅
- **ADDED**: Test script requirement BEFORE implementation
- **ADDED**: Plugin behavior verification steps
- **ADDED**: Multiple implementation options based on plugin behavior
- **CRITICAL**: Must verify `env` structure and callback usage

### 8. Evidence Protocol ✅
- **ADDED**: SHA256 normalization rule (whitespace collapse)
- **ADDED**: Optional validation script template
- **CLARIFIED**: Compute hash on `" ".join(quote.split())`

---

---

## 0. Canonical Rules (Ground Truth)

**FIRST RULE - Canonical Count Calculation**:
- **Canonical count = .md files WITH matching .json siblings ONLY**
- **Never count orphaned .md files** (prevents false drift alarms)
- **Test harness and CI Gate 5 MUST use identical pairing logic**
- See §13 Gate 5 for implementation details

**SECOND RULE - No Hybrids in PRs**:
- Regex + token "mixed" paths are **disallowed in PRs** (see §4.3)
- **Exception**: Feature flags (`USE_TOKEN_*`) allowed in **local branches only** for A/B testing
- **Enforcement**: CI blocks merge if any flags present (automated via check_no_hybrids.sh)
- **Timeline**: All flags + old regex paths must be removed before PR merge

**THIRD RULE - Iterative Token Traversal (MANDATORY)**:
- **ALL token tree traversal MUST use explicit stack** (no recursion)
- **Rationale**: Python recursion limit (~1000) can be hit by pathological markdown
  - Example: 2000 levels of nested quotes (`> > > ...`)
  - Malicious inputs designed to cause RecursionError
- **Applies to**: ALL traversal functions (links, images, plaintext, HTML detection)
- **Test requirement**: 2000-level nested fixture must NOT raise RecursionError
- See §4.1 for implementation details

**Additional Rules**:
- **Single Source of Truth**: This file governs this refactor
- **Evidence-First**: Non-obvious edits require Evidence Blocks (see §6)
- **Bounded Execution**: Only commands in §3 are allowed
- **No Network**: Pure structural validation; no HTTP reachability
- **YAGNI / KISS / SRP**: Implement only what is required; simplify; split responsibilities
- **HTML Hard-Off**: `html=False` at MarkdownIt init is mandatory (see §4.4)
- **Test After Every Checkpoint**: Run test harness after each internal step within a category

---

## 1. Scope & Constraints

- **Edit Only**: `content_context.py`, `markdown_parser_core.py`.
  (Test files may be added; no new runtime modules introduced.)
- **Output Parity**: All MD→JSON outputs must be byte-identical.
- **Perf Budget**: Δ **median** runtime ≤ **5%**, Δ **p95** ≤ **10%** (per-file and aggregate).
- **Timeout Parity**: Cross-platform timeout guard (thread/future+`result(timeout=...)`) must protect all parsing sections previously guarded by `signal`.
- **Dataset (Golden Corpus)**: Path (authoritative):
  `.../src/docpipe/md_parser_testing/test_mds/md_stress_mega/`
  > The **canonical_count** is computed at test start by enumerating `*.md` files with matching JSON siblings and logged to the report. All pass/fail gates use **canonical_count** (resolves prior 494 vs 700+ inconsistency).

- **Reference Materials (Authoritative Inputs)**
  - `Regex clean.md` — canonical regex→token mapping & rationale.
  - `Regex_calls_with_categories__action_queue_.csv` — ordered regex conversion queue.
  - `Regex_occurrences_in_provided_files.csv` — line spans for evidence.
  - `token_replacement_lib.py` — vetted helpers (`iter_blocks`, `extract_links_and_images`).

---

## 2. Deliverables

1. **Refactoring Plan** — `REFACTORING_PLAN_REGEX.md`
   - Table mapping each regex to its MarkdownIt replacement; include file+lines.
   - Evidence appendix with JSON blocks per change set.
2. **Code Changes** — in the two target files only.
3. **Tests** — unit + light integration + performance harness.
4. **Reports** — before/after parity and perf summaries (median, p95).
5. **Evidence** — JSON objects per change set (see §6).

---

## 3. Commands (Execution Boundary)

```bash
uv run ruff check .
uv run mypy src/
uv run pytest --cov=src --cov-report=term-missing
uv run python -m docpipe.md_parser_testing.test_harness_full
```

> If any command is missing/renamed, STOP with a clarification (template §7).

---

## 4. Design & Replacement Strategy

### 4.1 Categories → Strategies (authoritative)

| Category | Strategy |
|---|---|
| **Fences & Indented Code** | Use tokens where `token.type in {'fence','code_block'}`; line ranges from `token.map`; language from `token.info`. |
| **Links & Images** | Traverse `inline` children; for `link_open` read `attrs['href']`; for `image` read `attrs['src']` and derive alt from child text. Use **`urllib.parse.urlparse()`** for scheme extraction (replaces regex). Validate against **scheme allow-list** `["http", "https", "mailto"]`. **Reject** protocol-relative URLs (`//example.com`) and malformed URLs (fail closed). |
| **Headings / Lists / Tasks** | `heading_open` (`tag`→level), `bullet_list_open`, `ordered_list_open`, `list_item_open`; task list plugin for checkbox state. |
| **Inline → Plain Text** | Build text by concatenating inline `text` tokens; **ignore** `strong/em/code_inline` tokens instead of regex-stripping. |
| **Autolinks** | Enable `linkify=True`; validate `href` schemes on produced link tokens. |
| **HTML** | `html=False` mandatory; if a caller toggles `True`, raise or route through a single sanitizer that drops `html_inline/html_block` unless allow-listed. |
| **Frontmatter** | Use `mdit-py-plugins.front_matter_plugin` to extract YAML frontmatter natively instead of regex line scanning. |
| **Table Alignment** | **PRE-DECIDED: RETAINED** (§4.2). GFM table alignment (`:---|:--:|---:`) is format-specific parsing of separator syntax. Tokens don't expose alignment with `html=False` (alignment becomes HTML `style` attrs). Separator regex kept as format parsing. |
| **Slugification** | Use existing `sluggify_util.slugify()` instead of duplicating regex normalization logic. Ensure slug source text comes from tokens, not raw markdown. |

### 4.2 Intentionally Retained Regex (non-structural checks)

**Decision Locked**: These regexes are **format/content parsing**, not Markdown structure. They remain.

- **Table alignment parsing** (`[|:\-\s]+` separator row detection) - GFM format-specific (`:---|:--:|---:` syntax not in tokens)
- **Data URI parsing** (RFC 2397 format: `^data:([^;,]+)?(;base64)?,(.*)$`) - format-specific parsing
- **Unicode confusables / mixed-script heuristics** for security - character-level detection
- **Prompt injection patterns** - content-level semantic checks
- **Path traversal detection** - string-level security checks
- **HTML tag name extraction** (`<(\w+)`) - post-processing for sanitizer hints (not HTML parsing)

> These are *content* checks, not Markdown structure; they remain regex-based and are documented in code.

**Note**: URL scheme extraction now uses `urllib.parse.urlparse()` instead of regex (see §4.1 Links & Images).

### 4.3 No Hybrids Policy (Codified with CI Gate)

**Local Development (Allowed):**
- Use feature flags (`USE_TOKEN_FENCES`, `USE_TOKEN_LINKS`, etc.) for safe A/B testing
- Flags allow comparing token vs regex outputs side-by-side
- Makes debugging and incremental validation possible

**Before PR Merge (Enforced):**
- Remove **all** feature flags AND legacy regex paths in final commit
- No code paths mixing regex + tokens may remain
- CI enforces this automatically

**CI Merge Gate** (add to CI pipeline):
```bash
#!/bin/bash
# check_no_hybrids.sh - Fail PR if any hybrid symbols remain

HYBRID_SYMBOLS=$(grep -r "USE_TOKEN_\|MD_REGEX_COMPAT" src/docpipe/*.py || true)

if [ -n "$HYBRID_SYMBOLS" ]; then
    echo "❌ MERGE BLOCKED: Feature flags still present"
    echo "$HYBRID_SYMBOLS"
    exit 1
fi

echo "✅ No hybrid flags detected"
exit 0
```

**Enforcement**: This gate runs in CI on every PR. Merge is blocked until all flags removed.

### 4.4 MarkdownIt Initialization (hard requirement with enforcement)

```python
# MANDATORY: html=False for security
md = MarkdownIt("commonmark", options_update={"html": False, "linkify": True})
# enable table + tasklist plugins as used in repo
```

**Enforcement**: Raise if caller config attempts to enable HTML:
```python
# In MarkdownParserCore.__init__, BEFORE md initialization:
if config.get("allows_html", False):
    raise ValueError(
        "HTML rendering is disabled for security (§4.4). "
        "Parser enforces html=False. "
        "If HTML sanitization is required, use external sanitizer with bleach."
    )

# Then initialize with html=False:
self.md = MarkdownIt(
    preset,
    options_update={"html": False, "linkify": True}
)
```

**Sanitizer Path** (if bleach available):
```python
def _sanitize_html_if_needed(self, content: str) -> str:
    """Fallback sanitizer if html somehow needs processing.

    Default: reject. Only sanitize if bleach available and explicitly requested.
    """
    if not HAS_BLEACH:
        raise ValueError("HTML sanitization unavailable (bleach not installed)")

    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True
    )
```

### 4.5 Timeout Guard (cross-platform, applied uniformly)

**⚠️ CRITICAL: THE THREE-PARSE PROBLEM**

Markdown-it-py can be invoked in **3 different locations** in the parser. **ALL 3 MUST have timeout protection** to prevent DoS via pathological input (e.g., deeply nested structures triggering infinite loops in native extensions).

**The Three Parse Locations:**
1. **Main parse()** - Primary token generation (✅ MUST PROTECT)
2. **_extract_plain_text_from_tokens()** - Re-parse for plaintext extraction (✅ MUST PROTECT)
3. **_extract_yaml_frontmatter()** - Re-parse for frontmatter extraction (✅ MUST PROTECT)

**Why ThreadPoolExecutor is INSUFFICIENT for strict security:**
- ThreadPoolExecutor **CANNOT interrupt C-level loops** in native markdown-it extensions
- Pathological input (e.g., 100K nested blockquotes) can cause **infinite loops in native code**
- `future.cancel()` does nothing if thread is stuck in native code

**Solution: Process-Based Isolation for Strict Profile**
- **strict** profile uses `ProcessPoolExecutor` (can kill native loops via OS)
- **moderate/permissive** profiles use `ThreadPoolExecutor` (lower overhead, acceptable risk)

---

**Timeout Configuration** (add to SECURITY_LIMITS):
```python
SECURITY_LIMITS = {
    "strict": {
        # ... existing limits ...
        "parse_timeout_sec": 3.0,
        "use_process_isolation": True,  # ← ADDED: Kill native loops
    },
    "moderate": {
        # ... existing limits ...
        "parse_timeout_sec": 5.0,
        "use_process_isolation": False,  # Thread-based (faster)
    },
    "permissive": {
        # ... existing limits ...
        "parse_timeout_sec": 10.0,
        "use_process_isolation": False,
    },
}
```

---

**Implementation: _parse_with_timeout() Helper**

This helper MUST be used in **all 3 parse locations**.

```python
def _parse_with_timeout(self, content: str, timeout_sec: float = None):
    """Parse with cross-platform timeout protection.

    Uses ProcessPoolExecutor for strict profile (can kill native loops),
    ThreadPoolExecutor for moderate/permissive (lower overhead).

    Args:
        content: Markdown content to parse
        timeout_sec: Timeout in seconds (defaults to profile setting)

    Returns:
        Token list from markdown-it-py

    Raises:
        TimeoutError: If parsing exceeds timeout
    """
    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, TimeoutError

    # Get timeout and isolation setting from security profile
    limits = self.SECURITY_LIMITS[self.security_profile]
    if timeout_sec is None:
        timeout_sec = limits.get("parse_timeout_sec", 5.0)

    use_process_isolation = limits.get("use_process_isolation", False)

    # Choose executor based on security profile
    if use_process_isolation:
        executor_class = ProcessPoolExecutor  # ✅ Can kill native code loops
    else:
        executor_class = ThreadPoolExecutor  # Lower overhead

    with executor_class(max_workers=1) as executor:
        future = executor.submit(self.md.parse, content)
        try:
            return future.result(timeout=timeout_sec)
        except TimeoutError:
            future.cancel()
            raise TimeoutError(
                f"Markdown parsing exceeded {timeout_sec}s timeout "
                f"(profile: {self.security_profile}, "
                f"process_isolation: {use_process_isolation})"
            )
```

---

**Location 1: Main Parse (MarkdownParserCore.parse(), ~line 500)**

```python
def parse(self) -> dict[str, Any]:
    """Parse markdown with timeout protection."""
    # Get timeout from security profile
    limits = self.SECURITY_LIMITS[self.security_profile]
    timeout_sec = limits.get("parse_timeout_sec", 5.0)

    # ✅ LOCATION 1: Main parse with timeout
    try:
        self.tokens = self._parse_with_timeout(
            self.content,
            timeout_sec=timeout_sec
        )
    except TimeoutError as e:
        # Surface timeout as domain error in results
        return {
            "error": "parsing_timeout",
            "message": f"Parsing exceeded {timeout_sec}s limit",
            "security": {
                "timeout_triggered": True,
                "limit_sec": timeout_sec,
                "profile": self.security_profile,
            }
        }

    # Rest of parse() continues with self.tokens...
```

---

**Location 2: Plain Text Extraction Re-Parse**

**⚠️ CRITICAL**: If `_extract_plain_text_from_tokens()` re-parses content (instead of using `self.tokens`), it MUST use timeout protection.

```python
def _extract_plain_text_from_tokens(self, tokens: list = None) -> str:
    """Extract plain text from tokens.

    Args:
        tokens: Pre-parsed tokens (preferred - no re-parse)
                If None, will re-parse self.content WITH TIMEOUT
    """
    # PREFER: Use passed tokens or self.tokens (no re-parse needed)
    if tokens is None:
        if hasattr(self, 'tokens') and self.tokens:
            tokens = self.tokens
        else:
            # ✅ LOCATION 2: Re-parse with timeout (if unavoidable)
            limits = self.SECURITY_LIMITS[self.security_profile]
            timeout_sec = limits.get("parse_timeout_sec", 5.0)
            tokens = self._parse_with_timeout(self.content, timeout_sec=timeout_sec)

    # Traverse tokens to extract plain text (see §4.1 for iterative traversal)
    # ... rest of method
```

**BEST PRACTICE**: Always pass `self.tokens` to avoid re-parsing.

---

**Location 3: Frontmatter Extraction Re-Parse**

**⚠️ CRITICAL**: Frontmatter plugin may require re-parse with `env` dict. MUST use timeout.

```python
def _extract_yaml_frontmatter(self) -> dict[str, Any]:
    """Extract YAML frontmatter using frontmatter plugin.

    NOTE: Plugin may require re-parse to populate env dict.
    """
    from mdit_py_plugins.front_matter import front_matter_plugin

    # Create temporary parser with frontmatter plugin
    md_with_fm = MarkdownIt("gfm").use(front_matter_plugin)

    env = {}

    # ✅ LOCATION 3: Frontmatter re-parse with timeout
    limits = self.SECURITY_LIMITS[self.security_profile]
    timeout_sec = limits.get("parse_timeout_sec", 5.0)

    # NOTE: Can't use _parse_with_timeout directly since we need env dict
    # Workaround: Wrap in lambda or extract frontmatter before timeout
    try:
        from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, TimeoutError

        use_process_isolation = limits.get("use_process_isolation", False)
        executor_class = ProcessPoolExecutor if use_process_isolation else ThreadPoolExecutor

        with executor_class(max_workers=1) as executor:
            future = executor.submit(md_with_fm.parse, self.content, env)
            tokens = future.result(timeout=timeout_sec)
    except TimeoutError:
        # Frontmatter extraction timeout - return empty
        return {}

    # Extract frontmatter from env dict (plugin populates env['front_matter'])
    frontmatter = env.get('front_matter', {})

    # ... rest of method
```

---

**Testing Requirements:**

1. **Process Isolation Test** (strict profile):
   ```python
   # Test with pathological input (deeply nested structure)
   pathological_md = "> " * 10000 + "text"  # 10K nested blockquotes

   parser = MarkdownParserCore(
       pathological_md,
       security_profile='strict'  # Uses ProcessPoolExecutor
   )

   # Should timeout cleanly, not hang forever
   result = parser.parse()
   assert result.get('error') == 'parsing_timeout'
   ```

2. **Thread Timeout Test** (moderate profile):
   ```python
   # Moderate profile should still timeout (but may not kill native loops)
   parser = MarkdownParserCore(
       pathological_md,
       security_profile='moderate'  # Uses ThreadPoolExecutor
   )

   result = parser.parse()
   # May timeout or complete slowly (native loop may continue)
   ```

---

**Summary: Apply Timeout to ALL 3 Locations**

| Location | Function | Status | Isolation Mode |
|----------|----------|--------|----------------|
| 1 | `parse()` | ✅ MUST PROTECT | Process (strict) / Thread (moderate) |
| 2 | `_extract_plain_text_from_tokens()` | ✅ MUST PROTECT | Process (strict) / Thread (moderate) |
| 3 | `_extract_yaml_frontmatter()` | ✅ MUST PROTECT | Process (strict) / Thread (moderate) |

**Failure to protect all 3 locations = DoS vulnerability.**

---

## 5. Test & Performance Methodology

### 5.1 Golden Parity

- Enumerate **canonical_count** from the dataset (see §1).
- For each MD file, compare produced JSON to the expected reference (byte-identical or JSON-equivalent with deep comparison).

### 5.2 Performance Harness

- **3× cold runs** (cleared cache) + **5× warm runs**.
- Report **per-file** and **aggregate** **median** and **p95** (ms/file).
- Shuffle file order once to reduce cache bias.
- Pin Python + MarkdownIt versions in the report header.

### 5.3 Edge Fixtures (must pass)

- Unterminated fences; lazy-indented blocks; code inside lists.
- Links with titles, escaped brackets `\[`, nested brackets.
- Tables with complex headers; task lists.
- Bare URLs; `data:image/*` with size near limit.
- Malicious HTML input (should be dropped with `html=False`).

---

## 6. Evidence Protocol (authoritative)

- For each non-trivial change, add an Evidence JSON object to `REFACTORING_PLAN_REGEX.md` appendix.
- **sha256** is computed on the **normalized-whitespace** version of the quoted snippet.

**Schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Evidence",
  "type": "object",
  "required": ["quote", "source_path", "line_start", "line_end", "sha256", "rationale"],
  "properties": {
    "quote": {"type": "string", "minLength": 1},
    "source_path": {"type": "string", "minLength": 1},
    "line_start": {"type": "integer", "minimum": 1},
    "line_end": {"type": "integer", "minimum": 1},
    "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    "rationale": {"type": "string", "minLength": 1}
  }
}
```

**SHA256 Normalization Rule:**
- Compute SHA256 on **whitespace-normalized** version of quote
- Normalization: `" ".join(quote.split())` (collapse all whitespace to single spaces)
- This prevents hash mismatches from formatting differences

**Validation Script** (optional):
```python
#!/usr/bin/env python3
"""Validate evidence SHA256 hashes in REFACTORING_PLAN_REGEX.md"""
import json, hashlib, re

def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())

def compute_hash(quote: str) -> str:
    normalized = normalize_whitespace(quote)
    return hashlib.sha256(normalized.encode()).hexdigest()

# Read REFACTORING_PLAN_REGEX.md and extract JSON blocks
# Verify each sha256 matches computed hash
# Exit 1 if any mismatch found
```

**Example (Fence Detection → Token)**

```json
{
  "quote": "m = re.match(r'^\\s*([`~])\\1{2,}(\\s*\\S.*)?\\s*$', line)",
  "source_path": "src/docpipe/content_context.py",
  "line_start": 44,
  "line_end": 50,
  "sha256": "<compute-on-normalized-whitespace>",
  "rationale": "Use `fence`/`code_block` tokens and `token.map` for line ranges; language from `token.info`."
}
```

---

## 7. STOP Clarification Template

```json
{
  "type": "STOP_CLARIFICATION_REQUIRED",
  "reason": "<ambiguous construct | missing test harness | evidence gap | command unavailable>",
  "need": [
    {"what": "<file or command>", "why": "<1 sentence>", "proposed_next_step": "<smallest unblocker>"}
  ]
}
```

Trigger when confidence < 0.8, evidence missing, or boundaries exceeded.

---

## 8. Sequencing (Commit Order)

1. **Test Harness Setup** — create enhanced test harness with baseline
2. **Fences (regex → tokens)** — delete fence/indent regex and state machine
3. **Inline→Plain-Text + Slugification** — remove all markdown-stripping regex; use inline token text; replace duplicate `_slugify_base()` with `sluggify_util.slugify()`
4. **Links & Images + URL Parsing** — token traversal only; remove `[...](...)` regex; replace URL scheme regex with `urllib.parse.urlparse()`. **No hybrids**
5. **HTML** — enforce `html=False`; drop `html_inline/html_block` unless whitelisted
6. **Tables + Alignment** — move entirely to token ranges; delete pipe/dash heuristics; investigate alignment extraction from tokens
7. **Frontmatter** — add `front_matter_plugin`; replace `_extract_yaml_frontmatter()` regex
8. **Security & Cleanup** — retain content regexes (data URI, confusables, injection patterns) and document as retained; remove any redundant code

> Each step must maintain green tests on the entire corpus before proceeding.

---

## 9. Review Checklist (Gate to Merge)

- [ ] **Parity**: All outputs identical for **canonical_count** files.
- [ ] **Performance**: Δ median ≤ 5%, Δ p95 ≤ 10% (per-file & aggregate).
- [ ] **No Hybrids**: No code paths mixing regex and tokens remain.
- [ ] **Timeouts**: Cross-platform guard in place.
- [ ] **HTML**: `html=False` enforced; sanitizer path documented if toggled.
- [ ] **Evidence**: Complete JSON objects with sha256 for each change set.
- [ ] **Tooling**: `ruff` + `mypy` clean; tests green.
- [ ] **Flag Removal**: Any temporary `MD_REGEX_COMPAT` removed (or PR fails).

---

## 10. Detailed Execution Steps (Micro Checkpoints)

### STEP 1: Test Harness Setup & Baseline

**Goal**: Create production-quality test harness with performance tracking.

#### 1.1 Create Enhanced Test Harness

- [ ] **Action**: Create `src/docpipe/md_parser_testing/test_harness_full.py`

```python
#!/usr/bin/env python3
"""
Full test harness for markdown parser refactoring.
Runs all canonical test pairs with performance tracking.
"""

import json
import time
import random
import sys
import tracemalloc
from pathlib import Path
from typing import Dict, List, Tuple
import platform

from docpipe.markdown_parser_core import MarkdownParserCore


class TestResult:
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []  # (filename, reason)
        self.file_times: List[Tuple[str, float]] = []  # (filename, time_ms)
        self.file_memory: List[Tuple[str, int]] = []  # (filename, peak_bytes)
        self.cold_run_times: List[float] = []
        self.warm_run_times: List[float] = []
        self.cold_run_memory: List[int] = []  # peak bytes per run
        self.warm_run_memory: List[int] = []


def load_test_pair(md_path: Path) -> Tuple[str, Dict]:
    """Load markdown content and expected JSON output."""
    json_path = md_path.with_suffix('.json')

    if not json_path.exists():
        raise FileNotFoundError(f"Missing JSON pair: {json_path}")

    md_content = md_path.read_text(encoding='utf-8')
    expected = json.loads(json_path.read_text(encoding='utf-8'))

    return md_content, expected


def run_single_test(md_path: Path, config: Dict, track_memory: bool = True) -> Tuple[bool, str, float, int]:
    """
    Run parser on single test file.
    Returns: (passed, reason, elapsed_ms, peak_memory_bytes)
    """
    try:
        md_content, expected = load_test_pair(md_path)

        # Start memory tracking
        if track_memory:
            tracemalloc.start()

        start = time.perf_counter()
        parser = MarkdownParserCore(md_content, config=config, security_profile='moderate')
        result = parser.parse()
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Measure peak memory
        peak_bytes = 0
        if track_memory:
            current, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        if result is None:
            return False, "Parser returned None", elapsed_ms, peak_bytes

        # Check expected fields if they exist in the JSON
        # Access structure from result (parser returns result['structure']['headings'], not result['headings'])
        structure = result.get('structure', {})

        if 'expected_has_headings' in expected:
            has_headings = bool(structure.get('headings'))
            if has_headings != expected['expected_has_headings']:
                return False, f"Heading detection mismatch: got {has_headings}, expected {expected['expected_has_headings']}", elapsed_ms, peak_bytes

        if 'expected_heading_count' in expected:
            heading_count = len(structure.get('headings', []))
            if heading_count != expected['expected_heading_count']:
                return False, f"Heading count mismatch: got {heading_count}, expected {expected['expected_heading_count']}", elapsed_ms, peak_bytes

        return True, "PASS", elapsed_ms, peak_bytes

    except Exception as e:
        if track_memory and tracemalloc.is_tracing():
            tracemalloc.stop()
        return False, f"Exception: {type(e).__name__}: {str(e)}", 0.0, 0


def run_all_tests(test_dir: Path, config: Dict, shuffle: bool = False) -> TestResult:
    """Run all test files in directory."""
    result = TestResult()

    md_files = sorted(test_dir.glob('*.md'))

    # Filter to only files with JSON pairs
    md_files = [f for f in md_files if f.with_suffix('.json').exists()]

    canonical_count = len(md_files)

    if shuffle:
        random.shuffle(md_files)

    print(f"\n{'='*70}")
    print(f"Running {canonical_count} test files (canonical count)")
    print(f"Test dir: {test_dir.name}")
    print(f"Shuffle: {shuffle}")
    print(f"{'='*70}\n")

    overall_start = time.perf_counter()

    for i, md_path in enumerate(md_files, 1):
        passed, reason, elapsed_ms, peak_mem = run_single_test(md_path, config, track_memory=True)
        result.file_times.append((md_path.name, elapsed_ms))
        result.file_memory.append((md_path.name, peak_mem))

        if passed:
            result.passed.append(md_path.name)
            status = "✅"
        else:
            result.failed.append((md_path.name, reason))
            status = "❌"

        if i % 50 == 0 or not passed:  # Print every 50th or failures
            mem_mb = peak_mem / (1024 * 1024)
            print(f"[{i:3d}/{canonical_count}] {status} {md_path.name:50s} ({elapsed_ms:6.2f}ms, {mem_mb:.2f}MB)")

    total_time_s = time.perf_counter() - overall_start

    print(f"\n{'='*70}")
    print(f"Batch complete: {len(result.passed)} passed, {len(result.failed)} failed")
    print(f"Total time: {total_time_s:.2f}s")
    print(f"{'='*70}\n")

    return result, canonical_count


def compute_statistics(times: List[float]) -> Dict:
    """Compute median and p95 from time list with statistical correctness.

    Uses proper median calculation (average of two middle values for even N)
    and ceil-based p95 to avoid undercount for small samples.
    """
    import math

    if not times:
        return {"median": 0, "p95": 0, "mean": 0}

    sorted_times = sorted(times)
    n = len(sorted_times)

    # Median: average two middle values for even N
    if n % 2 == 0:
        median = (sorted_times[n // 2 - 1] + sorted_times[n // 2]) / 2
    else:
        median = sorted_times[n // 2]

    # P95: use ceil to avoid undercount for small n
    p95_idx = math.ceil(0.95 * (n - 1))
    p95 = sorted_times[p95_idx]

    mean = sum(sorted_times) / n

    return {"median": median, "p95": p95, "mean": mean}


def print_performance_report(cold_results: List[TestResult], warm_results: List[TestResult], canonical_count: int):
    """Print detailed performance report with memory profiling.

    Uses per-run medians for gate evaluation to avoid bias from long documents.
    Pooled stats provided for diagnostics only.
    """

    # CORRECT APPROACH: Compute per-run medians, then aggregate
    # This avoids bias where long docs dominate the pooled stats
    cold_run_medians = []
    warm_run_medians = []
    cold_run_mem_medians = []
    warm_run_mem_medians = []

    for res in cold_results:
        run_times = [t for _, t in res.file_times]
        run_memory = [m for _, m in res.file_memory]
        cold_run_medians.append(compute_statistics(run_times)['median'])
        cold_run_mem_medians.append(compute_statistics(run_memory)['median'])

    for res in warm_results:
        run_times = [t for _, t in res.file_times]
        run_memory = [m for _, m in res.file_memory]
        warm_run_medians.append(compute_statistics(run_times)['median'])
        warm_run_mem_medians.append(compute_statistics(run_memory)['median'])

    # Stats for gate evaluation (per-run medians)
    cold_stats = compute_statistics(cold_run_medians)
    warm_stats = compute_statistics(warm_run_medians)
    cold_mem_stats = compute_statistics(cold_run_mem_medians)
    warm_mem_stats = compute_statistics(warm_run_mem_medians)

    # Pooled stats for diagnostics (can show bias)
    all_cold_times = []
    all_warm_times = []
    for res in cold_results:
        all_cold_times.extend([t for _, t in res.file_times])
    for res in warm_results:
        all_warm_times.extend([t for _, t in res.file_times])

    cold_pooled = compute_statistics(all_cold_times)
    warm_pooled = compute_statistics(all_warm_times)

    print(f"\n{'='*70}")
    print(f"PERFORMANCE REPORT (Per-Run Medians)")
    print(f"{'='*70}")
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Canonical count: {canonical_count}")
    print(f"")
    print(f"NOTE: Using per-run medians to avoid long-document bias")
    print(f"      Pooled stats available at end for diagnostics")
    print(f"")
    print(f"Cold runs (3×) - TIME (per-run medians):")
    print(f"  Median:  {cold_stats['median']:.2f} ms/file")
    print(f"  P95:     {cold_stats['p95']:.2f} ms/file")
    print(f"  Mean:    {cold_stats['mean']:.2f} ms/file")
    print(f"")
    print(f"Cold runs (3×) - MEMORY (per-run medians):")
    print(f"  Median:  {cold_mem_stats['median'] / (1024*1024):.2f} MB/file")
    print(f"  P95:     {cold_mem_stats['p95'] / (1024*1024):.2f} MB/file")
    print(f"  Mean:    {cold_mem_stats['mean'] / (1024*1024):.2f} MB/file")
    print(f"")
    print(f"Warm runs (5×) - TIME (per-run medians):")
    print(f"  Median:  {warm_stats['median']:.2f} ms/file")
    print(f"  P95:     {warm_stats['p95']:.2f} ms/file")
    print(f"  Mean:    {warm_stats['mean']:.2f} ms/file")
    print(f"")
    print(f"Warm runs (5×) - MEMORY (per-run medians):")
    print(f"  Median:  {warm_mem_stats['median'] / (1024*1024):.2f} MB/file")
    print(f"  P95:     {warm_mem_stats['p95'] / (1024*1024):.2f} MB/file")
    print(f"  Mean:    {warm_mem_stats['mean'] / (1024*1024):.2f} MB/file")
    print(f"")
    print(f"--- POOLED STATS (Diagnostic Only - May Show Bias) ---")
    print(f"Warm pooled median: {warm_pooled['median']:.2f} ms/file")
    print(f"Warm pooled p95:    {warm_pooled['p95']:.2f} ms/file")
    print(f"{'='*70}\n")

    return cold_stats, warm_stats, cold_mem_stats, warm_mem_stats


def save_baseline(cold_stats: Dict, warm_stats: Dict, cold_mem_stats: Dict, warm_mem_stats: Dict, canonical_count: int, output_path: Path):
    """Save baseline performance data with memory profiling."""
    import markdown_it

    baseline = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'python_version': platform.python_version(),
        'platform': f"{platform.system()} {platform.release()}",
        'markdown_it_version': markdown_it.__version__,
        'canonical_count': canonical_count,
        'cold_runs': {
            'median_ms': cold_stats['median'],
            'p95_ms': cold_stats['p95'],
            'mean_ms': cold_stats['mean'],
            'median_mb': cold_mem_stats['median'] / (1024*1024),
            'p95_mb': cold_mem_stats['p95'] / (1024*1024),
            'mean_mb': cold_mem_stats['mean'] / (1024*1024),
        },
        'warm_runs': {
            'median_ms': warm_stats['median'],
            'p95_ms': warm_stats['p95'],
            'mean_ms': warm_stats['mean'],
            'median_mb': warm_mem_stats['median'] / (1024*1024),
            'p95_mb': warm_mem_stats['p95'] / (1024*1024),
            'mean_mb': warm_mem_stats['mean'] / (1024*1024),
        }
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

    print("Running 3 cold runs...")
    cold_results = []
    for i in range(3):
        print(f"\n--- Cold run {i+1}/3 ---")
        result, canonical_count = run_all_tests(test_dir, config, shuffle=(i==0))
        cold_results.append(result)
        if result.failed:
            print(f"⚠️  Cold run {i+1} had {len(result.failed)} failures")

    print("\nRunning 5 warm runs...")
    warm_results = []
    for i in range(5):
        print(f"\n--- Warm run {i+1}/5 ---")
        result, _ = run_all_tests(test_dir, config, shuffle=False)
        warm_results.append(result)
        if result.failed:
            print(f"⚠️  Warm run {i+1} had {len(result.failed)} failures")

    # Print performance report
    cold_stats, warm_stats, cold_mem_stats, warm_mem_stats = print_performance_report(cold_results, warm_results, canonical_count)

    # Check for failures in final warm run
    final_result = warm_results[-1]

    print(f"\n{'='*70}")
    print(f"FINAL SUMMARY")
    print(f"{'='*70}")
    print(f"Passed: {len(final_result.passed)}/{canonical_count}")
    print(f"Failed: {len(final_result.failed)}/{canonical_count}")

    if final_result.failed:
        print(f"\nFAILURES (showing first 10):")
        for filename, reason in final_result.failed[:10]:
            print(f"  ❌ {filename}: {reason}")
        if len(final_result.failed) > 10:
            print(f"  ... and {len(final_result.failed) - 10} more")
    print(f"{'='*70}\n")

    # Save baseline
    baseline_path = Path(__file__).parent / "baseline_performance.json"
    save_baseline(cold_stats, warm_stats, cold_mem_stats, warm_mem_stats, canonical_count, baseline_path)

    # Exit with error code if tests failed
    sys.exit(0 if len(final_result.failed) == 0 else 1)
```

- [ ] **Checkpoint**: Run baseline test harness

```bash
cd /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned
uv run python src/docpipe/md_parser_testing/test_harness_full.py
```

**Reflection Point**:
- Did the test harness run successfully?
- What is the canonical_count?
- What are the baseline median/p95 times?
- How many tests pass/fail currently?
- Is `baseline_performance.json` created?

**Expected Output**:
- Canonical count logged
- 3 cold runs + 5 warm runs complete
- Baseline performance saved to `baseline_performance.json`
- Some tests may fail initially (document current state)

**Rollback**: If harness crashes, check Python version and markdown-it installation.

---

### STEP 2: Code Fence Detection Refactoring

**Goal**: Replace 3 regex patterns in `content_context.py` with token-based detection.

**Evidence Location**: `REFACTORING_PLAN_REGEX.md` appendix, category "fences"

#### 2.1 Check for signal.alarm Usage

- [ ] **Action**: Search for Unix-specific timeout code

```bash
grep -n "signal.alarm\|signal.SIGALRM" src/docpipe/content_context.py src/docpipe/markdown_parser_core.py
```

**Reflection Point**: Any signal usage found? If yes, note for cross-platform replacement in §4.5.

---

#### 2.2 Refactor ContentContext Architecture

**CRITICAL ARCHITECTURAL DECISION:**

ContentContext should **NOT** parse tokens itself. It's a helper class for line classification, not a parser.

**Option A: Remove ContentContext entirely** (RECOMMENDED)
- ContentContext is only 214 lines and used minimally
- Main parser already has tokens - can classify lines directly
- Eliminates double-parsing overhead
- Simpler architecture

**Option B: Pass tokens from parent parser** (if removal is too invasive)
- Modify `ContentContext.__init__` to accept optional `tokens` parameter
- Parent parser passes tokens it already computed
- ContentContext uses passed tokens instead of re-parsing

**RECOMMENDED APPROACH: Option A**

- [ ] **Action**: Add token-based line classification directly in `MarkdownParserCore`

```python
def _build_line_context_map(self, tokens: list) -> dict[int, str]:
    """Build line number -> context mapping from already-parsed tokens.

    Uses tokens from self.md.parse() - no re-parsing.

    Returns:
        Dictionary mapping line numbers to context types:
        - 'prose': Regular markdown content
        - 'fenced_code': Inside ``` or ~~~ blocks
        - 'indented_code': Indented code blocks (4 spaces/tab)
        - 'fence_marker': The ``` or ~~~ lines themselves
        - 'blank': Empty lines
    """
    lines = self.content.split("\n")

    # Initialize all lines as prose
    context_map = {i: "prose" for i in range(len(lines))}

    # Mark blank lines
    for i, line in enumerate(lines):
        if line.strip() == "":
            context_map[i] = "blank"

    # Walk tokens to find code blocks
    for token in tokens:
        if token.type in {"fence", "code_block"}:
            if token.map is None:
                continue

            start_line, end_line = token.map  # end_line is exclusive

            if token.type == "fence":
                # First line is opening fence marker
                context_map[start_line] = "fence_marker"
                # Last line is closing fence marker (end_line - 1 since exclusive)
                if end_line > start_line + 1:
                    context_map[end_line - 1] = "fence_marker"
                # Lines between are fenced code
                for line_no in range(start_line + 1, end_line - 1):
                    if line_no < len(lines):
                        context_map[line_no] = "fenced_code"

            elif token.type == "code_block":
                # Indented code block
                for line_no in range(start_line, end_line):
                    if line_no < len(lines) and context_map[line_no] != "blank":
                        context_map[line_no] = "indented_code"

    return context_map
```

- [ ] **Decision Point**: Check ContentContext usage with concrete threshold

```bash
#!/bin/bash
# Automated decision for ContentContext refactoring approach

USAGE_COUNT=$(grep -r "ContentContext" src/docpipe/*.py | wc -l)
echo "ContentContext usage count: $USAGE_COUNT"
echo ""

if [ $USAGE_COUNT -le 5 ]; then
    echo "✅ DECISION: REMOVE ContentContext (≤5 uses - minimal)"
    echo "   → Follow Option A (removal steps below)"
    echo "   → Delete content_context.py"
    echo "   → Integrate _build_line_context_map() into MarkdownParserCore"
    DECISION="REMOVE"
elif [ $USAGE_COUNT -le 15 ]; then
    echo "⚠️  DECISION: KEEP with token passing (6-15 uses - moderate)"
    echo "   → Follow Option B (pass tokens from parent)"
    echo "   → Modify ContentContext.__init__ to accept tokens parameter"
    echo "   → Update all call sites to pass tokens"
    DECISION="KEEP_WITH_TOKENS"
else
    echo "❌ DECISION: KEEP but refactor later (>15 uses - extensive)"
    echo "   → Document as technical debt for separate PR"
    echo "   → For now: use Option B as temporary bridge"
    echo "   → File issue: 'Refactor ContentContext architecture'"
    DECISION="DEFER"
fi

echo ""
echo "Chosen path: $DECISION"
```

**Expected Output**: Usage count + automated decision

**Action Based on Decision**:
- If **REMOVE**: Follow Option A steps (delete file, integrate method)
- If **KEEP_WITH_TOKENS**: Follow Option B steps (modify __init__, pass tokens)
- If **DEFER**: Follow Option B now, file technical debt issue

- [ ] **Checkpoint**: Verify method compiles

```bash
uv run python -c "from docpipe.content_context import ContentContext; print('✅ New method added')"
```

**Reflection Point**: Does it compile? Any import errors?

---

#### 2.3 Switch to Token Mode (No Feature Flag - Direct Replacement)

Per §4.3 (No Hybrids Policy), we replace the old method entirely in this commit.

- [ ] **Action**: Replace `_build_context_map()` with token version

1. Delete lines 24-110 (old `_build_context_map()` with regex)
2. Rename `_build_context_map_tokens()` to `_build_context_map()`
3. Update `__init__` to just call the new method (no flag needed)

**Updated `__init__`:**

```python
def __init__(self, content: str):
    """Initialize with markdown content.

    Args:
        content: The markdown content to analyze
    """
    self.lines = content.split("\n")
    self.context_map = self._build_context_map()  # Now uses tokens
```

- [ ] **Action**: Remove `import re` from line 9 if no other regex usage

```bash
grep -n "re\." src/docpipe/content_context.py
```

If no other matches, delete the import.

---

#### 2.4 Test Token-Based Fence Detection

- [ ] **Checkpoint**: Run full test harness

```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py 2>&1 | tee fence_refactor_test.log
```

**Reflection Point**:
- Do tests pass at same rate as baseline?
- Are performance metrics within budget (median ≤ +5%, p95 ≤ +10%)?
- Any new failures?

**Decision Point**:
- If failures appear, examine each case:
  - Is token mode MORE correct? (unterminated fences, edge cases)
  - If yes, update test expectations
  - If no, fix the token logic

**Rollback Procedure**:
```bash
git diff src/docpipe/content_context.py
git checkout src/docpipe/content_context.py  # Revert if needed
```

---

#### 2.5 Create Evidence Block

- [ ] **Action**: Add to `REFACTORING_PLAN_REGEX.md` appendix

```json
{
  "quote": "m = re.match(r'^\\s*([`~])\\1{2,}(\\s*\\S.*)?\\s*$', line)",
  "source_path": "src/docpipe/content_context.py",
  "line_start": 44,
  "line_end": 50,
  "sha256": "<compute-sha256-of-normalized-whitespace>",
  "rationale": "Replaced regex fence detection with MarkdownIt token.type='fence'/'code_block'. Uses token.map for line ranges and token.info for language. Eliminates manual state tracking and handles unterminated fences correctly."
}
```

Compute SHA256:
```python
import hashlib
quote = "m = re.match(r'^\\s*([`~])\\1{2,}(\\s*\\S.*)?\\s*$', line)"
normalized = " ".join(quote.split())
sha = hashlib.sha256(normalized.encode()).hexdigest()
print(sha)
```

---

#### 2.6 Commit Fence Refactoring

- [ ] **Checkpoint**: Commit changes

```bash
git add src/docpipe/content_context.py
git add REFACTORING_PLAN_REGEX.md
git commit -m "refactor(fences): replace regex fence detection with MarkdownIt tokens

- Remove 3 regex patterns for fence/indent detection (lines 44, 48, 158)
- Replace _build_context_map() with token-based implementation
- Use token.type='fence'/'code_block' and token.map for line ranges
- Language extraction now via token.info (no regex needed)

Evidence: See REFACTORING_PLAN_REGEX.md appendix, category 'fences'

Performance: Median Δ <±5%, P95 Δ <±10%
Tests: All canonical_count tests passing
"
```

**Reflection Point**:
- Clean commit?
- All tests green?
- Ready for next category?

---

### STEP 3: Inline Formatting Strip Refactoring

**Goal**: Replace 7 regex patterns in `_strip_markdown_formatting()` with token-based text extraction.

**Evidence Location**: `REFACTORING_PLAN_REGEX.md` appendix, category "inline_formatting"

#### 3.1 Add Token-Based Plain Text Extractor

- [ ] **Action**: Add method to `MarkdownParserCore` (around line 3600)

```python
def _extract_plain_text_from_tokens(self, tokens: list = None) -> str:
    """Extract plain text from markdown using ITERATIVE token traversal.

    ⚠️ CRITICAL: Uses explicit stack to avoid RecursionError on deeply nested markdown.
    Python's recursion limit (~1000) can be hit by pathological input (e.g., 2000-level
    nested blockquotes). Stack-based DFS handles arbitrary depth.

    Replaces regex-based _strip_markdown_formatting(). Instead of
    stripping markdown syntax with regexes, we parse the document
    and extract only text-bearing tokens.

    Args:
        tokens: Pre-parsed tokens (preferred - no re-parse)
                If None, will re-parse self.content WITH TIMEOUT (see §4.5)

    Returns:
        Plain text with formatting removed
    """
    # PREFER: Use passed tokens or self.tokens (no re-parse needed)
    if tokens is None:
        if hasattr(self, 'tokens') and self.tokens:
            tokens = self.tokens
        else:
            # ✅ Re-parse with timeout (see §4.5 Location 2)
            limits = self.SECURITY_LIMITS[self.security_profile]
            timeout_sec = limits.get("parse_timeout_sec", 5.0)
            tokens = self._parse_with_timeout(self.content, timeout_sec=timeout_sec)

    plain_parts = []

    def extract_text_from_inline(inline_token):
        """Extract text from inline token and its children (iterative)."""
        if not inline_token.children:
            return ""

        text_parts = []
        # Inline children are typically shallow (no deep nesting)
        # But use iterative approach for consistency
        child_stack = list(reversed(inline_token.children))

        while child_stack:
            child = child_stack.pop()

            if child.type == "text":
                text_parts.append(child.content)
            elif child.type == "code_inline":
                text_parts.append(child.content)  # Keep code content
            elif child.type in ("softbreak", "hardbreak"):
                text_parts.append(" ")
            # Ignore formatting tokens: strong_open/close, em_open/close, etc.
            # For links, text is already in child text tokens

        return "".join(text_parts)

    # Explicit stack for iterative DFS: (token_list, index)
    stack = [(tokens, 0)]

    while stack:
        token_list, idx = stack.pop()

        # Bounds check
        if idx >= len(token_list):
            continue

        token = token_list[idx]

        # Push next sibling onto stack (processed later)
        stack.append((token_list, idx + 1))

        # Process current token
        if token.type == "inline":
            text = extract_text_from_inline(token)
            if text:
                plain_parts.append(text)

        elif token.type == "heading_close":
            plain_parts.append("\n")

        elif token.type == "paragraph_close":
            plain_parts.append("\n")

        # Push children onto stack (processed before next sibling)
        if token.children:
            stack.append((token.children, 0))

    # Join and clean up multiple newlines
    result = "".join(plain_parts)
    # Collapse multiple newlines to single
    lines = [line.strip() for line in result.split("\n") if line.strip()]
    return "\n".join(lines)
```

---

#### 3.2 Replace _strip_markdown_formatting()

Per §4.3 (No Hybrids), directly replace the method.

- [ ] **Action**: Find `_strip_markdown_formatting()` (around line 3570)

Delete the old regex-based implementation (lines 3570-3585).

Replace with:

```python
def _strip_markdown_formatting(self, text: str) -> str:
    """Remove markdown formatting from text.

    Uses token-based extraction instead of regex (refactored).

    Args:
        text: Markdown text

    Returns:
        Plain text
    """
    return self._extract_plain_text_from_tokens(text)
```

---

#### 3.3 Test Inline Formatting Strip

- [ ] **Checkpoint**: Run test harness

```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py 2>&1 | tee inline_refactor_test.log
```

**Reflection Point**:
- Tests passing at baseline rate?
- Performance within budget?
- Text extraction handling nested emphasis correctly?

**Edge Cases to Verify**:
```python
# Manual verification
from docpipe.markdown_parser_core import MarkdownParserCore

tests = [
    "**bold** and *italic*",
    "**nested *emphasis* works**",
    "[link text](http://example.com)",
    "text with `inline code` here",
    "# Heading\n\nParagraph",
]

for test in tests:
    parser = MarkdownParserCore(test, security_profile='permissive')
    result = parser._strip_markdown_formatting(test)
    print(f"Input:  {repr(test)}")
    print(f"Output: {repr(result)}")
    print()
```

---

#### 3.4 Evidence Block

- [ ] **Action**: Add to `REFACTORING_PLAN_REGEX.md`

```json
{
  "quote": "text = re.sub(r'^#+\\s+', '', text, flags=re.MULTILINE)",
  "source_path": "src/docpipe/markdown_parser_core.py",
  "line_start": 3573,
  "line_end": 3583,
  "sha256": "<compute>",
  "rationale": "Replaced 7 regex patterns (header strip, bold, italic, links, code blocks) with token-based text extraction. Handles nested emphasis and escaped characters correctly. Uses inline token traversal to collect only text nodes."
}
```

---

#### 3.5 Commit

```bash
git add src/docpipe/markdown_parser_core.py
git add REFACTORING_PLAN_REGEX.md
git commit -m "refactor(inline): replace regex markdown stripping with token traversal

- Remove 7 regex patterns from _strip_markdown_formatting()
- Add _extract_plain_text_from_tokens() using inline token walk
- Correctly handle nested emphasis, links, code spans
- No regex fragility for escaped characters or nested constructs

Evidence: See REFACTORING_PLAN_REGEX.md appendix, category 'inline_formatting'

Performance: Within budget
Tests: Passing
"
```

---

#### 3.6 Slugification Cleanup (Bonus Enhancement)

**Goal**: Remove duplicate slugification logic, use existing utility.

- [ ] **Action**: Remove `_slugify_base()` method

Find and delete the `_slugify_base()` method (likely around line 3536-3545).

- [ ] **Action**: Import `sluggify_util`

Add at top of file:
```python
from docpipe.sluggify_util import slugify
```

- [ ] **Action**: Replace all calls to `_slugify_base()`

Find calls (likely in `_extract_headings()` and `_extract_sections()`):
```python
# OLD:
base_slug = self._slugify_base(heading_text)

# NEW:
base_slug = slugify(heading_text) or "untitled"
```

- [ ] **Checkpoint**: Test slugification

```python
from docpipe.markdown_parser_core import MarkdownParserCore

test = "# Heading with **Bold** and [Link](url)\n\n## Äöü Ñoñ-ASCII"
parser = MarkdownParserCore(test, security_profile='moderate')
result = parser.parse()

for heading in result.get('headings', []):
    print(f"Text: {heading['text']}, Slug: {heading['slug']}")
# Verify slugs are clean and derived from token text (not raw markdown)
```

**Reflection Point**: Are slugs generated correctly from clean text (without markdown syntax)?

- [ ] **Action**: Update evidence block

```json
{
  "quote": "s = re.sub(r'[\\s/]+', '-', s)",
  "source_path": "src/docpipe/markdown_parser_core.py",
  "line_start": 3536,
  "line_end": 3545,
  "sha256": "<compute>",
  "rationale": "Removed duplicate slugification logic. Use existing sluggify_util.slugify() per DRY principle. Slug source text already comes from tokens (heading inline children)."
}
```

---

### STEP 4: Links & Images Refactoring + URL Parsing Enhancement

**Goal**: Replace link/image regex patterns with token traversal. Replace URL scheme regex with `urllib.parse.urlparse()`. **No hybrids** per §4.3.

**Evidence Location**: `REFACTORING_PLAN_REGEX.md` appendix, category "links_images"

#### 4.1 Add Token-Based Link/Image Extraction

- [ ] **Action**: Add utility methods (around line 300 in `MarkdownParserCore`)

```python
def _extract_links_from_tokens(self, tokens: list) -> list[dict]:
    """Extract all links from token tree using ITERATIVE traversal.

    ⚠️ CRITICAL: Uses explicit stack to avoid RecursionError on deeply nested markdown.
    Python's recursion limit (~1000) can be hit by pathological input (e.g., 2000-level
    nested blockquotes). Stack-based DFS handles arbitrary depth.

    Args:
        tokens: MarkdownIt token list

    Returns:
        List of dicts with keys: href, text, line_start, line_end
    """
    links = []

    # Explicit stack for iterative DFS: (token_list, index)
    stack = [(tokens, 0)]

    while stack:
        token_list, idx = stack.pop()

        # Bounds check
        if idx >= len(token_list):
            continue

        token = token_list[idx]

        # Push next sibling onto stack (processed later)
        stack.append((token_list, idx + 1))

        # Process current token
        if token.type == "link_open":
            attrs = dict(token.attrs or [])
            href = attrs.get("href", "")

            # Extract link text from NEXT token (should be inline with children)
            text = ""
            if idx + 1 < len(token_list) and token_list[idx + 1].type == "inline":
                inline_token = token_list[idx + 1]
                if inline_token.children:
                    text = "".join(
                        child.content for child in inline_token.children
                        if child.type == "text"
                    )

            line_start, line_end = token.map if token.map else (None, None)

            links.append({
                "href": href,
                "text": text,
                "line_start": line_start,
                "line_end": line_end,
            })

        # Push children onto stack (processed before next sibling)
        if token.children:
            stack.append((token.children, 0))

    return links


def _extract_images_from_tokens(self, tokens: list) -> list[dict]:
    """Extract all images from token tree using ITERATIVE traversal.

    ⚠️ CRITICAL: Uses explicit stack to avoid RecursionError on deeply nested markdown.
    Python's recursion limit (~1000) can be hit by pathological input (e.g., 2000-level
    nested blockquotes). Stack-based DFS handles arbitrary depth.

    Args:
        tokens: MarkdownIt token list

    Returns:
        List of dicts with keys: src, alt, line_start, line_end
    """
    images = []

    # Explicit stack for iterative DFS: (token_list, index)
    stack = [(tokens, 0)]

    while stack:
        token_list, idx = stack.pop()

        # Bounds check
        if idx >= len(token_list):
            continue

        token = token_list[idx]

        # Push next sibling onto stack (processed later)
        stack.append((token_list, idx + 1))

        # Process current token
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
            })

        # Push children onto stack (processed before next sibling)
        if token.children:
            stack.append((token.children, 0))

    return images
```

---

#### 4.2 Replace Link/Image Regex in _preprocess_markdown()

Find the section around line 1062 (link filtering) and 1089 (image filtering).

**Strategy**: Since we're using `html=False` and token validation, the preprocessing regex is less critical. However, per §4.3 (no hybrids), we must remove the regex entirely.

- [ ] **Action**: Locate `_preprocess_markdown()` method

- [ ] **Action**: Replace link scheme filtering (around line 1062)

**BEFORE:**
```python
text = re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)", _strip_bad_link, text)
if removed_schemes:
    reasons.append("disallowed_link_schemes_removed")
```

**AFTER:**
```python
# Token-based link validation (scheme checking moved to token extraction phase)
# Regex removal per §4.3 (No Hybrids Policy)
# Scheme validation now happens in _extract_links_from_tokens() during parse phase
# This preprocessing step is no longer needed with token-first architecture
if cfg.get("validate_link_schemes", True):
    # Validation deferred to token phase
    pass
```

- [ ] **Action**: Replace image filtering (around line 1089)

**BEFORE:**
```python
text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _filter_image, text)
```

**AFTER:**
```python
# Token-based image validation (moved to token extraction phase)
# Regex removal per §4.3 (No Hybrids Policy)
if cfg.get("validate_image_sources", True):
    # Validation deferred to token phase
    pass
```

**Note**: The actual scheme/size validation will happen when we walk tokens in the parse phase, not in preprocessing. This aligns with token-first architecture.

---

#### 4.3 Replace URL Scheme Regex with urllib.parse

**Enhancement**: Use stdlib instead of regex for URL parsing.

- [ ] **Action**: Replace scheme extraction regex

Find existing regex (likely in `_validate_link_scheme()` or inline):
```python
# OLD (regex):
import re
msch = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", href)
if msch:
    scheme = msch.group(1).lower()
```

Replace with:
```python
# NEW (urllib.parse):
from urllib.parse import urlparse

try:
    parsed = urlparse(href)
    scheme = parsed.scheme.lower() if parsed.scheme else None
except Exception:
    scheme = None
```

- [ ] **Action**: Add Comprehensive URL Validation Helper (6 Security Layers)

Add this method to `MarkdownParserCore`:

```python
def _validate_and_normalize_url(self, url: str) -> tuple[bool, str, list[str]]:
    """Comprehensive URL validation with 6 security layers.

    ⚠️ CRITICAL: Defense-in-depth approach prevents various attack vectors.

    Security Layers:
    1. Control characters & zero-width joiners (CR/LF injection, homograph attacks)
    2. Anchors (explicit allowance)
    3. Protocol-relative URLs (rejected)
    4. Scheme validation (allow-list enforcement)
    5. IDNA encoding for internationalized domains (fail-closed)
    6. Percent-encoding validation (malformed escapes)

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, normalized_url, warnings)
        - is_valid: True if URL passes all security checks
        - normalized_url: URL with IDNA encoding applied (if applicable)
        - warnings: List of security warnings (empty if valid)
    """
    from urllib.parse import urlparse, quote, unquote

    warnings = []

    # ======= LAYER 1: Control Characters & Zero-Width Joiners =======
    # Prevents: CR/LF injection, homograph attacks, Unicode tricks
    FORBIDDEN_CHARS = set(chr(i) for i in range(32)) | {
        '\u200B',  # Zero-width space
        '\u200C',  # Zero-width non-joiner
        '\u200D',  # Zero-width joiner
        '\uFEFF',  # Zero-width no-break space (BOM)
    }

    if any(c in url for c in FORBIDDEN_CHARS):
        warnings.append("Control characters or zero-width joiners in URL")
        return False, url, warnings

    # ======= LAYER 2: Anchors (Explicit Allowance) =======
    # Fragment-only URLs are always safe
    if url.startswith("#"):
        return True, url, []

    # ======= LAYER 3: Protocol-Relative URLs =======
    # Reject //example.com (ambiguous protocol)
    if url.startswith("//"):
        warnings.append("Protocol-relative URL rejected")
        return False, url, warnings

    # ======= LAYER 4: Parse URL & Validate Scheme =======
    try:
        parsed = urlparse(url)
    except Exception as e:
        warnings.append(f"Malformed URL: {type(e).__name__}")
        return False, url, warnings

    scheme = parsed.scheme.lower() if parsed.scheme else None

    # Scheme allow-list (codified in §4.1)
    ALLOWED_SCHEMES = ["http", "https", "mailto"]

    if scheme:
        if scheme not in ALLOWED_SCHEMES:
            warnings.append(f"Disallowed scheme: {scheme}")
            return False, url, warnings
    else:
        # Empty scheme (e.g., "example.com" without protocol)
        # Reject - unclear if it's a path or a URL
        warnings.append("No scheme in URL")
        return False, url, warnings

    # ======= LAYER 5: IDNA Encoding (Internationalized Domains) =======
    # Convert Unicode domains to ASCII (punycode)
    # Fail-closed: If encoding fails, URL is invalid
    if parsed.netloc:
        try:
            netloc_normalized = parsed.netloc.encode('idna').decode('ascii')
        except Exception as e:
            warnings.append(f"IDNA encoding failed: {type(e).__name__}")
            return False, url, warnings

        # Reconstruct URL with normalized netloc
        normalized_url = parsed._replace(netloc=netloc_normalized).geturl()
    else:
        normalized_url = url

    # ======= LAYER 6: Percent-Encoding Validation =======
    # Check that all % are followed by valid hex digits
    # Prevents: %00 (null byte), %0A (newline), malformed escapes
    import re
    percent_pattern = re.compile(r'%([0-9A-Fa-f]{2})')

    # Find all % in URL
    idx = 0
    while idx < len(url):
        if url[idx] == '%':
            # Check if followed by valid hex
            if idx + 2 >= len(url):
                warnings.append("Malformed percent-encoding (truncated)")
                return False, url, warnings

            hex_part = url[idx+1:idx+3]
            if not re.match(r'^[0-9A-Fa-f]{2}$', hex_part):
                warnings.append(f"Malformed percent-encoding: %{hex_part}")
                return False, url, warnings

        idx += 1

    # ======= ALL CHECKS PASSED =======
    return True, normalized_url, []
```

- [ ] **Action**: Use Comprehensive Validation in Parse Phase

```python
# After tokens = self.md.parse(content)

# Validate links
links = self._extract_links_from_tokens(tokens)
for link in links:
    href = link["href"]

    # Comprehensive 6-layer validation
    is_valid, normalized_url, validation_warnings = self._validate_and_normalize_url(href)

    if not is_valid:
        # Log all security warnings
        for warning in validation_warnings:
            security["warnings"].append(f"URL validation failed ({href[:50]}): {warning}")

        # Track blocked URL
        security["blocked_urls"] = security.get("blocked_urls", [])
        security["blocked_urls"].append(href[:100])
        continue  # Skip invalid URLs

    # If warnings exist but URL is still valid (should not happen with current logic)
    for warning in validation_warnings:
        security["warnings"].append(f"URL warning ({href[:50]}): {warning}")

# Validate images
images = self._extract_images_from_tokens(tokens)
for image in images:
    src = image["src"]

    # Check data URIs (keep this regex - it's RFC 2397 format parsing per §4.2)
    if src.startswith("data:"):
        uri_info = self._parse_data_uri(src)
        max_size = cfg.get("max_data_uri_size", 10000)
        if uri_info.get("size_bytes", 0) > max_size:
            security["warnings"].append(f"Oversized data URI: {uri_info['size_bytes']} bytes")
```

- [ ] **Checkpoint**: Test URL parsing edge cases

```python
from docpipe.markdown_parser_core import MarkdownParserCore

edge_cases = [
    "[safe](http://example.com)",
    "[javascript](javascript:alert(1))",
    "[protocol-relative](//evil.com)",
    "[data uri](data:text/plain,hello)",
    "[anchor](#heading)",
    "[malformed](:://broken)",
]

for test in edge_cases:
    parser = MarkdownParserCore(test, security_profile='strict')
    result = parser.parse()
    print(f"Input: {test}")
    print(f"Warnings: {result.get('security', {}).get('warnings', [])}")
    print()
```

**Reflection Point**:
- Does `urlparse()` correctly handle all edge cases?
- Are malicious schemes (javascript:, data:) caught?
- Are legitimate URLs allowed?

---

#### 4.4 Test Link/Image Refactoring

- [ ] **Checkpoint**: Run test harness

```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py 2>&1 | tee links_images_test.log
```

**Edge Cases to Verify Manually**:
```python
from docpipe.markdown_parser_core import MarkdownParserCore

tests = [
    "[text](http://example.com)",
    "[text](http://example.com \"title\")",
    "[escaped \\[brackets\\]](url)",
    "[nested [brackets]](url)",
    "![alt](image.png)",
    "![](data:image/png;base64,abc123)",
]

for test in tests:
    parser = MarkdownParserCore(test, security_profile='moderate')
    tokens = parser.md.parse(test)
    links = parser._extract_links_from_tokens(tokens)
    images = parser._extract_images_from_tokens(tokens)
    print(f"Input: {repr(test)}")
    print(f"Links: {links}")
    print(f"Images: {images}")
    print()
```

---

#### 4.5 Evidence Block

```json
{
  "quote": "text = re.sub(r'(?<!\\!)\\[([^\\]]+)\\]\\(([^)]+)\\)', _strip_bad_link, text)",
  "source_path": "src/docpipe/markdown_parser_core.py",
  "line_start": 1062,
  "line_end": 1065,
  "sha256": "<compute>",
  "rationale": "Replaced regex link/image extraction with token traversal. Uses link_open/image tokens with attrs['href'/'src']. Handles nested brackets, titles, and escapes correctly. Scheme validation moved to token phase (URI regex retained per §4.2)."
}
```

---

#### 4.6 Commit

```bash
git add src/docpipe/markdown_parser_core.py
git add REFACTORING_PLAN_REGEX.md
git commit -m "refactor(links): replace regex link/image parsing with tokens

- Remove regex patterns for [text](url) and ![alt](src)
- Add _extract_links_from_tokens() and _extract_images_from_tokens()
- Move scheme/size validation to token phase
- Handle nested brackets, titles, escapes correctly
- No hybrids: regex fully removed per §4.3

Evidence: See REFACTORING_PLAN_REGEX.md appendix, category 'links_images'

Retained regexes (per §4.2): URI scheme parsing, data URI validation
"
```

---

### STEP 5: HTML Sanitization Refactoring

**Goal**: Enforce `html=False`, replace regex HTML detection with tokens.

**Evidence Location**: `REFACTORING_PLAN_REGEX.md` appendix, category "html"

#### 5.1 Enforce html=False at Initialization

- [ ] **Action**: Find all `MarkdownIt()` initializations

```bash
grep -n "MarkdownIt(" src/docpipe/markdown_parser_core.py
```

- [ ] **Action**: Ensure all instances have `html=False`

Example:
```python
self.md = MarkdownIt(
    preset,
    options_update={"html": False, "linkify": True}  # html=False is mandatory
)
```

- [ ] **Action**: Document behavior if caller tries to enable HTML

Add to docstring or raise error:
```python
if config.get("allows_html", False):
    # Per §4.4: html=False is mandatory at init
    # If caller needs HTML, they must use external sanitizer
    raise ValueError(
        "HTML rendering is disabled for security. "
        "Use html=False and sanitize externally if needed."
    )
```

---

#### 5.2 Add Token-Based HTML Detection

- [ ] **Action**: Add method for security monitoring

```python
def _detect_html_in_tokens(self, tokens: list) -> dict:
    """Detect HTML in token stream for security monitoring using ITERATIVE traversal.

    ⚠️ CRITICAL: Uses explicit stack to avoid RecursionError on deeply nested markdown.
    Python's recursion limit (~1000) can be hit by pathological input (e.g., 2000-level
    nested blockquotes). Stack-based DFS handles arbitrary depth.

    Even with html=False, we detect HTML in input for logging.

    Returns:
        Dict with: has_html, html_blocks, html_inline, script_detected
    """
    result = {
        "has_html": False,
        "html_blocks": [],
        "html_inline": [],
        "script_detected": False
    }

    # Explicit stack for iterative DFS: (token_list, index)
    stack = [(tokens, 0)]

    while stack:
        token_list, idx = stack.pop()

        # Bounds check
        if idx >= len(token_list):
            continue

        token = token_list[idx]

        # Push next sibling onto stack (processed later)
        stack.append((token_list, idx + 1))

        # Process current token
        if token.type == "html_block":
            result["has_html"] = True
            result["html_blocks"].append({
                "content": token.content[:100],  # Truncate for safety
                "line": token.map[0] if token.map else None
            })
            if "<script" in token.content.lower():
                result["script_detected"] = True

        elif token.type == "html_inline":
            result["has_html"] = True
            result["html_inline"].append({
                "content": token.content[:100],
                "line": token.map[0] if token.map else None
            })
            if "<script" in token.content.lower():
                result["script_detected"] = True

        # Push children onto stack (processed before next sibling)
        if token.children:
            stack.append((token.children, 0))

    return result
```

---

#### 5.3 Replace Regex HTML Detection

Find regex patterns for HTML detection (lines 1023-1031, 1266-1274):

**BEFORE:**
```python
if re.search(r"<\s*script\b", text, re.I):
    reasons.append("script_tag_removed")
text = re.sub(r"<\s*script\b[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.I | re.S)

if re.search(r"\bon[a-z]+\s*=", text, re.I):
    reasons.append("event_handlers_removed")
text = re.sub(r"\bon[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", text, flags=re.I)
```

**AFTER:**
```python
# Token-based HTML detection (regex removed per §4.3)
html_info = self._detect_html_in_tokens(self.tokens)

if html_info["script_detected"]:
    reasons.append("script_tag_detected")
    security["warnings"].append("Script tags found in input (blocked by html=False)")

if html_info["has_html"]:
    reasons.append("html_detected")
    security["statistics"]["has_html_block"] = len(html_info["html_blocks"]) > 0
    security["statistics"]["has_html_inline"] = len(html_info["html_inline"]) > 0

# No need to strip - html=False prevents rendering
```

---

#### 5.4 Simplify _sanitize_html_content()

Since `html=False` is enforced, this method is mostly redundant.

**BEFORE (lines 936-952):** Complex regex sanitization

**AFTER:**
```python
def _sanitize_html_content(self, html: str, allows_html: bool = False) -> str:
    """Sanitize HTML content.

    Note: With html=False at init (§4.4), this is rarely called.
    Kept for legacy compatibility.

    Args:
        html: HTML content
        allows_html: If False, strip all HTML (default)

    Returns:
        Sanitized HTML or empty string
    """
    if not allows_html:
        # HTML disabled at parser level - return empty
        return ""

    # If HTML somehow needs to be allowed, use bleach
    if HAS_BLEACH:
        return bleach.clean(
            html,
            tags=self._ALLOWED_HTML_TAGS,
            attributes=self._ALLOWED_ATTRIBUTES,
            strip=True
        )
    else:
        # No bleach available - reject HTML for safety
        return ""
```

---

#### 5.5 Test HTML Refactoring

- [ ] **Checkpoint**: Run test harness

```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py 2>&1 | tee html_test.log
```

**Edge Cases** (manual verification):
```python
from docpipe.markdown_parser_core import MarkdownParserCore

malicious = [
    "<script>alert('xss')</script>",
    "<div onclick='bad()'>text</div>",
    "<iframe src='evil.com'></iframe>",
    "# Heading\n\n<script>bad()</script>\n\nNormal text",
]

for test in malicious:
    parser = MarkdownParserCore(test, security_profile='strict')
    result = parser.parse()
    html_info = parser._detect_html_in_tokens(parser.md.parse(test))

    print(f"Input: {repr(test[:50])}")
    print(f"Script detected: {html_info['script_detected']}")
    print(f"HTML detected: {html_info['has_html']}")
    print()
```

Expected: All HTML detected but not rendered (blocked by `html=False`)

---

#### 5.6 Evidence Block

```json
{
  "quote": "if re.search(r'<\\s*script\\b', text, re.I):",
  "source_path": "src/docpipe/markdown_parser_core.py",
  "line_start": 1023,
  "line_end": 1031,
  "sha256": "<compute>",
  "rationale": "Replaced 6+ regex patterns for HTML detection/sanitization with token-based detection via _detect_html_in_tokens(). Enforced html=False at MarkdownIt init per §4.4. HTML is blocked at parse time, regex sanitization no longer needed."
}
```

---

#### 5.7 Commit

```bash
git add src/docpipe/markdown_parser_core.py
git add REFACTORING_PLAN_REGEX.md
git commit -m "refactor(html): enforce html=False, replace regex detection with tokens

- Enforce html=False at all MarkdownIt init points (§4.4)
- Add _detect_html_in_tokens() for security monitoring
- Remove 6+ regex patterns for HTML detection/sanitization
- Simplify _sanitize_html_content() (now mostly redundant)
- HTML blocked at parse time, not via regex stripping

Evidence: See REFACTORING_PLAN_REGEX.md appendix, category 'html'
"
```

---

### STEP 6: Table Detection + Alignment Refactoring

**Goal**: Replace table separator regex heuristic with token-based detection. Investigate alignment extraction from tokens.

#### 6.1 Replace Table Detection Heuristic (Line 3076)

- [ ] **Action**: Find table detection code

```bash
grep -n "table.*separator\|pipe.*dash" src/docpipe/markdown_parser_core.py
```

Context around line 3076:
```python
if "|" in line and re.search(r"-{3,}", line):
    if re.fullmatch(r"[|:\-\s]+", line):
        sep_idx = i
```

**REPLACE WITH:**
```python
# Token-based table detection (§4.1)
# Check if current line is within a table token's range
for token in self.tokens:
    if token.type == "table_open" and token.map:
        start, end = token.map
        if start <= i < end:
            # Line is inside a table
            # Look for separator row (thead_close position)
            for child in tokens:
                if child.type == "thead_close" and child.map:
                    sep_idx = child.map[0]
                    break
            break
```

---

#### 6.2 Investigate Table Alignment Extraction

**Goal**: Check if MarkdownIt tokens provide alignment information.

- [ ] **Action**: Examine table token structure

```python
from markdown_it import MarkdownIt
from mdit_py_plugins.table import table_plugin

md = MarkdownIt("commonmark").use(table_plugin)

table_test = """
| Left | Center | Right |
|:-----|:------:|------:|
| L1   | C1     | R1    |
"""

tokens = md.parse(table_test)

def print_tokens(token_list, indent=0):
    for token in token_list:
        print("  " * indent + f"{token.type} | attrs={token.attrs} | meta={token.meta}")
        if token.children:
            print_tokens(token.children, indent + 1)

print_tokens(tokens)
# Look for alignment info in: token.attrs, token.meta, or token.attrGet()
```

**Reflection Point**:
- Is alignment information available in tokens?
- Where is it stored? (`attrs`, `meta`, `markup`, child th/td tokens?)
- If not available, document as **retained regex** (separator parsing is format-specific)

---

#### 6.3 Determine Alignment Extraction Strategy

**EXPECTED PATH: Alignment NOT in tokens** (90% probability)

With `html=False`, the GFM table plugin does **NOT** expose alignment in tokens.
Alignment is rendered as HTML `style` attributes which are not accessible when HTML rendering is disabled.

- [ ] **Action**: Verify with investigation script (Step 6.2)

**IF alignment NOT found (EXPECTED PATH)**:

- [ ] **Action**: Document separator regex as RETAINED (§4.2)

- [ ] **Action**: Add to retained regex inventory in REFACTORING_PLAN_REGEX.md:

```markdown
| `[|:\-\s]+` | line 3076 | Table alignment parsing | GFM format-specific (`:---\|:--:\|---:` syntax) |
```

- [ ] **Action**: Add inline comment in code:

```python
# REGEX RETAINED (per REGEX_REFACTOR §4.2): Table alignment parsing
# GFM table alignment is format-specific parsing of `:---|:--:|---:` separator syntax
# Not available in tokens with html=False (verified during refactor - see STEP 6.2)
# This is table format parsing, not Markdown structure parsing
if re.fullmatch(r"[|:\-\s]+", line):
    # Parse alignment from separator characters
    # : on left  → left-align
    # : on both  → center-align
    # : on right → right-align
```

- [ ] **Checkpoint**: Mark as expected outcome, no regression

**IF alignment IS found in tokens** (10% probability - unlikely):

> This would be a pleasant surprise! It means the plugin behavior changed or html=False doesn't prevent style attrs.

- [ ] **Action**: Use token-based extraction instead:

```python
def _extract_table_alignment_from_tokens(self, table_token) -> list[str]:
    """Extract column alignments from table tokens.

    Returns:
        List of alignment strings: 'left', 'center', 'right', 'none'
    """
    alignments = []

    # Find thead token
    for child in table_token.children if hasattr(table_token, 'children') else []:
        if child.type == 'thead_open':
            # Look for th tokens
            for subchild in child.children:
                if subchild.type == 'th_open':
                    # Check for alignment in attrs
                    style = dict(subchild.attrs or {}).get('style', '')
                    if 'text-align: left' in style:
                        alignments.append('left')
                    elif 'text-align: center' in style:
                        alignments.append('center')
                    elif 'text-align: right' in style:
                        alignments.append('right')
                    else:
                        alignments.append('none')
            break

    return alignments
```

- [ ] **Action**: Document discovery in REFACTORING_PLAN_REGEX.md

- [ ] **Action**: Remove `[|:\-\s]+` pattern from retained regex list

**Reflection Point**:
- Expected: Alignment regex RETAINED (format-specific)
- Unlikely: Alignment available in tokens → remove regex
- Proceed based on investigation results

---

#### 6.4 Test Table Detection

```python
from docpipe.markdown_parser_core import MarkdownParserCore

table_test = """
| Left | Center | Right |
|:-----|:------:|------:|
| L1   | C1     | R1    |
| L2   | C2     | R2    |
"""

parser = MarkdownParserCore(table_test, security_profile='moderate')
result = parser.parse()
print("Tables found:", result.get('tables', []))

# Check alignment extraction
if result.get('tables'):
    for table in result['tables']:
        print(f"Alignment: {table.get('alignment', [])}")
```

---

#### 6.5 Evidence & Commit

```json
{
  "quote": "if re.fullmatch(r'[|:\\-\\s]+', line):",
  "source_path": "src/docpipe/markdown_parser_core.py",
  "line_start": 3076,
  "line_end": 3078,
  "sha256": "<compute>",
  "rationale": "Replaced table separator heuristic regex with token-based detection. Use table_open token.map for range checking. More reliable than pipe/dash regex."
}
```

```bash
git add src/docpipe/markdown_parser_core.py
git add REFACTORING_PLAN_REGEX.md
git commit -m "refactor(tables): replace regex heuristic with token detection

- Remove pipe/dash regex patterns for table detection
- Use table_open/thead_close tokens for separator detection
- More robust than character-based heuristics

Evidence: See REFACTORING_PLAN_REGEX.md appendix
"
```

---

### STEP 7: Frontmatter Refactoring

**Goal**: Replace regex-based YAML frontmatter extraction with `mdit-py-plugins.front_matter_plugin`.

**Evidence Location**: `REFACTORING_PLAN_REGEX.md` appendix, category "frontmatter"

**⚠️ BLOCKER**: This step has a hard verification requirement BEFORE proceeding.

---

#### 7.1A VERIFY Frontmatter Plugin Behavior (REQUIRED FIRST)

**CRITICAL**: Do NOT proceed to 7.1B until plugin behavior verified and findings documented.

- [ ] **Action**: Create and run verification script

Save as `verify_frontmatter_plugin.py`:

```python
#!/usr/bin/env python3
"""Verify frontmatter plugin behavior before implementing refactor."""

import json
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

md = MarkdownIt("commonmark").use(front_matter_plugin)

test_content = """---
title: Test Document
tags: [python, markdown]
date: 2025-10-11
---

# Content here

Regular markdown."""

print("="*70)
print("FRONTMATTER PLUGIN VERIFICATION")
print("="*70)
print()

# Parse with env
env = {}
tokens = md.parse(test_content, env)

print("1. Checking env contents:")
print(f"   env keys: {list(env.keys())}")
print(f"   env contents: {env}")
print()

print("2. Checking frontmatter location:")
frontmatter_raw = env.get('front_matter')
if frontmatter_raw:
    print(f"   ✅ Found in env['front_matter']")
    print(f"   Type: {type(frontmatter_raw).__name__}")
    print(f"   Value: {frontmatter_raw}")
else:
    print(f"   ❌ NOT found in env['front_matter']")
print()

print("3. Checking tokens:")
print(f"   Token count: {len(tokens)}")
print(f"   First 3 token types: {[t.type for t in tokens[:3]]}")
print()

print("4. Checking if frontmatter stripped from tokens:")
# If frontmatter is stripped, first token should be heading, not frontmatter
first_content_token = next((t for t in tokens if t.type != 'front_matter'), None)
if first_content_token:
    print(f"   First content token type: {first_content_token.type}")
print()

# Determine findings
findings = {
    "frontmatter_location": "env['front_matter']" if env.get('front_matter') else "unknown",
    "is_dict": isinstance(env.get('front_matter'), dict),
    "is_string": isinstance(env.get('front_matter'), str),
    "is_none": env.get('front_matter') is None,
    "tokens_modified": len(tokens) > 0 and tokens[0].type != 'paragraph',
    "env_keys": list(env.keys()),
}

# Save findings
with open('frontmatter_plugin_findings.json', 'w') as f:
    json.dump(findings, f, indent=2)

print("="*70)
print("FINDINGS SUMMARY")
print("="*70)
print(json.dumps(findings, indent=2))
print()
print("✅ Findings saved to: frontmatter_plugin_findings.json")
print()

# Decision guidance
print("="*70)
print("IMPLEMENTATION DECISION")
print("="*70)
if findings['is_dict']:
    print("✅ PROCEED: Use env['front_matter'] directly (Option A)")
    print()
    print("Next step: Proceed to Step 7.1B")
elif findings['is_string']:
    print("⚠️  PROCEED: Parse YAML from env['front_matter'] string (Option A modified)")
    print()
    print("Next step: Proceed to Step 7.1B with YAML parsing")
elif findings['frontmatter_location'] == "unknown":
    print("❌ EXECUTION BLOCKED")
    print("="*70)
    print()
    print("Frontmatter plugin does NOT store data in env['front_matter']")
    print()
    print("DO NOT PROCEED TO STEP 7.1B")
    print()
    print("Required Actions:")
    print("1. Document frontmatter regex as RETAINED (§4.2)")
    print("2. Add to retained regex inventory")
    print("3. File issue with mdit-py-plugins project")
    print("4. Skip to STEP 8 (leave regex in place)")
    print()
    print("="*70)
    import sys
    sys.exit(1)  # ⚠️ CRITICAL: Hard exit to prevent proceeding
print("="*70)
```

- [ ] **Checkpoint**: Run verification script

```bash
python verify_frontmatter_plugin.py
```

- [ ] **Checkpoint**: Review findings file

```bash
cat frontmatter_plugin_findings.json
```

**Decision Rules**:
1. **If `is_dict: true`** → Proceed to 7.1B with Option A (use dict directly)
2. **If `is_string: true`** → Proceed to 7.1B with Option A-modified (parse YAML)
3. **If `frontmatter_location: "unknown"`** → **STOP**, use Fallback Strategy below

**Fallback Strategy** (if plugin doesn't work as expected):

- [ ] **Action**: Document frontmatter regex as RETAINED
- [ ] **Action**: Add to retained regex inventory:

```markdown
| `^---\\s*$` (frontmatter markers) | line XXXX | YAML frontmatter detection | Plugin unavailable or incompatible |
```

- [ ] **Action**: File issue with `mdit-py-plugins` project
- [ ] **Action**: Skip to STEP 8 (leave regex-based extraction in place)
- [ ] **Action**: Note in REFACTORING_PLAN_REGEX.md: "Frontmatter plugin verification failed, regex retained pending upstream fix"

**Reflection Point**: Only proceed to 7.1B if verification succeeds.

---

#### 7.1B Add Front Matter Plugin (After Verification)

**⚠️ CRITICAL PRE-REQUISITE**: Step 7.1A verification MUST complete successfully.

- [ ] **Pre-Flight Check**: Verify `frontmatter_plugin_findings.json` exists and shows valid frontmatter location

```bash
# Check that verification passed
if [ ! -f frontmatter_plugin_findings.json ]; then
    echo "❌ ERROR: Step 7.1A verification not run"
    echo "Run: python verify_frontmatter_plugin.py"
    exit 1
fi

# Check that plugin works
if grep -q '"frontmatter_location": "unknown"' frontmatter_plugin_findings.json; then
    echo "❌ ERROR: Frontmatter plugin verification FAILED"
    echo "Use fallback strategy - DO NOT proceed to 7.1B"
    exit 1
fi

echo "✅ Verification passed - proceeding with plugin implementation"
```

- [ ] **Action**: Enable the plugin in MarkdownIt initialization

Find where `self.md` is initialized and add the plugin:

```python
from mdit_py_plugins.front_matter import front_matter_plugin

# Existing init:
self.md = MarkdownIt(
    preset,
    options_update={"html": False, "linkify": True}
)
self.md.use(table_plugin)
self.md.use(tasklists_plugin)

# ADD (based on 7.1A verification):
self.md.use(front_matter_plugin)
```

---

#### 7.2 Replace _extract_yaml_frontmatter()

Find the current implementation (likely uses regex to detect `---` markers):

**BEFORE (regex-based)**:
```python
def _extract_yaml_frontmatter(self, content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from content."""
    import re

    lines = content.split('\n')
    if not lines or not re.match(r'^---\s*$', lines[0]):
        return {}, content

    # Find closing ---
    for i in range(1, len(lines)):
        if re.match(r'^---\s*$', lines[i]):
            yaml_content = '\n'.join(lines[1:i])
            # Parse YAML...
            remaining = '\n'.join(lines[i+1:])
            return frontmatter_dict, remaining

    return {}, content
```

**CRITICAL: VERIFY PLUGIN BEHAVIOR FIRST**

Before implementing, test how `front_matter_plugin` actually works:

```python
# TEST SCRIPT - Run this BEFORE refactoring
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

md = MarkdownIt("commonmark").use(front_matter_plugin)

test_content = """---
title: Test
tags: [a, b]
---

# Content here"""

env = {}
tokens = md.parse(test_content, env)

print("env keys:", env.keys())
print("env contents:", env)
print("\nFirst 3 tokens:")
for token in tokens[:3]:
    print(f"  {token.type}: {token.content[:50] if token.content else ''}")
```

**Expected behavior investigation:**
1. Check if frontmatter is in `env['front_matter']` or elsewhere
2. Check if frontmatter is stored as dict or raw YAML string
3. Check if tokens include frontmatter block or if it's stripped
4. Check if plugin uses callback instead of env

**AFTER (plugin-based) - CORRECT IMPLEMENTATION**:
```python
def _extract_yaml_frontmatter(self, content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter using front_matter_plugin.

    NOTE: This implementation depends on verified plugin behavior.
    See STEP 7.3 test script for verification.
    """
    import yaml

    # Option A: If plugin stores in env
    env = {}
    tokens = self.md.parse(content, env)

    # Check where plugin stores frontmatter (verify first!)
    frontmatter_raw = env.get('front_matter')  # May be dict or string

    if frontmatter_raw:
        # If it's already a dict, use it; if string, parse it
        if isinstance(frontmatter_raw, dict):
            frontmatter = frontmatter_raw
        else:
            try:
                frontmatter = yaml.safe_load(frontmatter_raw)
            except yaml.YAMLError:
                frontmatter = {}

        # Remove frontmatter from content (line-based slice)
        lines = content.split('\n')
        if lines and lines[0].strip() == '---':
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    remaining = '\n'.join(lines[i+1:])
                    return frontmatter, remaining

    return {}, content

# Option B: If plugin uses callback (check docs)
# May need to register callback during md.use() instead
```

**Action Item**: MUST run test script in STEP 7.3 before implementing.

---

#### 7.3 Test Frontmatter Extraction

- [ ] **Checkpoint**: Test with various frontmatter

```python
from docpipe.markdown_parser_core import MarkdownParserCore

tests = [
    # Valid frontmatter
    """---
title: Test
author: Claude
---

# Content""",

    # No frontmatter
    "# Just Content",

    # Multiline frontmatter
    """---
title: Multi
tags:
  - python
  - markdown
---

Content here""",

    # Malformed frontmatter
    """---
invalid yaml: [
---

Content"""
]

for i, test in enumerate(tests):
    parser = MarkdownParserCore(test, security_profile='moderate')
    result = parser.parse()
    print(f"Test {i+1}:")
    print(f"  Frontmatter: {result.get('frontmatter', {})}")
    print(f"  Content starts with: {result.get('content', '')[:50]}")
    print()
```

**Reflection Point**:
- Does the plugin extract frontmatter correctly?
- Is the frontmatter dict properly populated?
- Is the content cleanly separated (no `---` markers in output)?
- How are YAML parsing errors handled?

---

#### 7.4 Evidence Block

```json
{
  "quote": "if not lines or not re.match(r'^---\\s*$', lines[0]):",
  "source_path": "src/docpipe/markdown_parser_core.py",
  "line_start": "<find-actual-line>",
  "line_end": "<find-actual-line>",
  "sha256": "<compute>",
  "rationale": "Replaced regex-based YAML frontmatter detection with mdit-py-plugins.front_matter_plugin. Plugin handles marker detection and YAML parsing natively. More robust for edge cases (empty frontmatter, nested markers)."
}
```

---

#### 7.5 Commit

```bash
git add src/docpipe/markdown_parser_core.py
git add REFACTORING_PLAN_REGEX.md
git commit -m "refactor(frontmatter): replace regex extraction with front_matter_plugin

- Remove regex patterns for --- marker detection
- Add mdit-py-plugins.front_matter_plugin to parser init
- Replace _extract_yaml_frontmatter() with plugin-based extraction
- More robust handling of edge cases and malformed YAML

Evidence: See REFACTORING_PLAN_REGEX.md appendix, category 'frontmatter'
"
```

---

### STEP 8: Document Retained Regexes & Final Cleanup

**Goal**: Document regexes we're keeping per §4.2. Clean up any redundant code.

#### 8.1 Add Comment Block to Retained Regexes

For each retained regex, add clear comment:

```python
# REGEX RETAINED (per REGEX_REFACTOR §4.2): Data URI parsing (RFC 2397)
# Not markdown structure - URI format validation
match = re.match(r"^data:([^;,]+)?(;base64)?,(.*)$", uri)

# URL scheme validation now uses urllib.parse.urlparse() - NO LONGER REGEX
# See §4.1 Links & Images enhancement

# REGEX RETAINED (per REGEX_REFACTOR §4.2): Unicode confusables detection
# Security heuristic - character-level analysis, not markdown parsing
has_cyrillic = bool(re.search(r"[\u0400-\u04FF]", text_sample))

# REGEX RETAINED (per REGEX_REFACTOR §4.2): Prompt injection patterns
# Security content check, not markdown structure
if re.search(r"(system|prompt|instruction|ignore|override)", content, re.IGNORECASE):

# REGEX RETAINED (per REGEX_REFACTOR §4.2): Slug normalization
# Text cleanup utility, well-contained, no MarkdownIt equivalent
s = re.sub(r"[\s/]+", "-", s)
```

---

#### 8.2 Create Retained Regex Inventory

- [ ] **Action**: Add section to `REFACTORING_PLAN_REGEX.md`

```markdown
## Regexes Intentionally Retained (§4.2)

These regex patterns are **not markdown parsing** and are kept:

| Pattern | Location | Purpose | Rationale |
|---------|----------|---------|-----------|
| `^data:([^;,]+)?(;base64)?,(.*)$` | line 2575 | Data URI parsing | RFC 2397 standard, not markdown |
| `[\u0400-\u04FF]` (and similar) | lines 3419-3424 | Unicode script detection | Security heuristic, character-level |
| `(system\|prompt\|instruction...)` | line 3522 | Prompt injection detection | Security content check |
| `^[a-z]:[/\\]` | line 3335 | Windows path detection | Path validation, not markdown |
| `<(\w+)` | (HTML tag extraction) | HTML tag name extraction | Post-processing for sanitizer hints |
| `[|:\-\s]+` | (if needed) | Table alignment parsing | Table format-specific (only if not in tokens) |

**Total retained**: ~8-9 regex patterns (depending on table alignment availability in tokens)
**Total removed**: ~23+ regex patterns

**Replaced with stdlib/plugins**:
- URL scheme extraction: Now uses `urllib.parse.urlparse()` (§4.1)
- Slugification: Now uses `sluggify_util.slugify()` (§3.6)
- Frontmatter: Now uses `front_matter_plugin` (§7)
```

---

#### 8.3 Commit Documentation

```bash
git add src/docpipe/markdown_parser_core.py
git add REFACTORING_PLAN_REGEX.md
git commit -m "docs: document retained regexes per §4.2

- Add inline comments to all retained regex patterns
- Create inventory section in REFACTORING_PLAN_REGEX.md
- Clarify: retained regexes are content/format validation, not markdown parsing

Total removed: ~23+ regex patterns
Total retained: ~8-9 (documented)
Replaced with stdlib/plugins: 3 (urlparse, slugify, frontmatter plugin)
"
```

---

### STEP 8: Final Validation

#### 8.1 Run Complete Test Suite with Performance Comparison

- [ ] **Checkpoint**: Final test run

```bash
uv run python src/docpipe/md_parser_testing/test_harness_full.py 2>&1 | tee final_test_results.txt
```

- [ ] **Action**: Compare with baseline

```python
import json

baseline = json.load(open('src/docpipe/md_parser_testing/baseline_performance.json'))
final = json.load(open('src/docpipe/md_parser_testing/final_performance.json'))  # Save from last run

print("="*70)
print("PERFORMANCE COMPARISON")
print("="*70)
print(f"Canonical count: {baseline['canonical_count']} (baseline) vs {final['canonical_count']} (final)")
print()
print("COLD RUNS:")
print(f"  Median:  {baseline['cold_runs']['median_ms']:.2f} ms → {final['cold_runs']['median_ms']:.2f} ms")
delta_cold_median = ((final['cold_runs']['median_ms'] - baseline['cold_runs']['median_ms']) / baseline['cold_runs']['median_ms']) * 100
print(f"  Delta:   {delta_cold_median:+.1f}% (target: ≤+5%)")
print()
print(f"  P95:     {baseline['cold_runs']['p95_ms']:.2f} ms → {final['cold_runs']['p95_ms']:.2f} ms")
delta_cold_p95 = ((final['cold_runs']['p95_ms'] - baseline['cold_runs']['p95_ms']) / baseline['cold_runs']['p95_ms']) * 100
print(f"  Delta:   {delta_cold_p95:+.1f}% (target: ≤+10%)")
print()
print("WARM RUNS:")
print(f"  Median:  {baseline['warm_runs']['median_ms']:.2f} ms → {final['warm_runs']['median_ms']:.2f} ms")
delta_warm_median = ((final['warm_runs']['median_ms'] - baseline['warm_runs']['median_ms']) / baseline['warm_runs']['median_ms']) * 100
print(f"  Delta:   {delta_warm_median:+.1f}% (target: ≤+5%)")
print()
print(f"  P95:     {baseline['warm_runs']['p95_ms']:.2f} ms → {final['warm_runs']['p95_ms']:.2f} ms")
delta_warm_p95 = ((final['warm_runs']['p95_ms'] - baseline['warm_runs']['p95_ms']) / baseline['warm_runs']['p95_ms']) * 100
print(f"  Delta:   {delta_warm_p95:+.1f}% (target: ≤+10%)")
print()

# MEMORY ANALYSIS (ADDED)
print("="*70)
print("MEMORY ANALYSIS")
print("="*70)

# Warm memory comparison (more stable than cold)
baseline_mem = baseline['warm_runs']['median_mb']
final_mem = final['warm_runs']['median_mb']
delta_mem = ((final_mem - baseline_mem) / baseline_mem) * 100

print(f"Median Memory: {baseline_mem:.2f} MB → {final_mem:.2f} MB")
print(f"Delta: {delta_mem:+.1f}%")
print()

# Memory thresholds
# NOTE: tracemalloc reports Python allocator peaks, not RSS
# Token trees use more memory than regex - this is expected
if delta_mem > 50:
    print("❌ CRITICAL: Memory increased >50% - investigate leaks")
    print("   This likely indicates a memory leak, not expected overhead")
    memory_gate_fail = True
elif delta_mem > 20:
    print("⚠️  WARNING: Memory increased >20% (expected for token-based)")
    print("   Token trees use more memory than regex - this is normal")
    print("   If delta >30%, consider optimization opportunities")
    memory_gate_fail = False
else:
    print(f"✅ Memory delta within acceptable range (<20%)")
    memory_gate_fail = False

print("="*70)
print()

# Time gates
if abs(delta_warm_median) > 5:
    print("⚠️  WARNING: Median performance delta exceeds ±5%")
if abs(delta_warm_p95) > 10:
    print("⚠️  WARNING: P95 performance delta exceeds ±10%")

# Memory gate (informational, not blocking)
if memory_gate_fail:
    print("⚠️  CRITICAL: Memory regression detected - review before merge")
```

---

#### 8.2 Lint & Type Check

- [ ] **Checkpoint**: Run ruff

```bash
uv run ruff check .
```

Fix any new issues.

- [ ] **Checkpoint**: Run mypy

```bash
uv run mypy src/
```

Fix any type errors.

---

#### 8.3 Code Coverage

- [ ] **Checkpoint**: Run pytest

```bash
uv run pytest --cov=src --cov-report=term-missing
```

Ensure coverage ≥ 80%.

---

### STEP 9: Final Documentation & Sign-Off

#### 9.1 Complete REFACTORING_PLAN_REGEX.md

- [ ] **Action**: Finalize all evidence blocks with SHA256

- [ ] **Action**: Add summary section:

```markdown
# Regex Refactoring - Summary

## Execution Results

**Date**: <YYYY-MM-DD>
**Status**: ✅ COMPLETE

### Metrics

- **Canonical count**: <N> test files
- **Regexes removed**: 20
- **Regexes retained**: 10 (documented in §4.2)
- **Test pass rate**: <N>/<N> (100%)
- **Performance delta**:
  - Median: <±X.X%> (target: ±5%)
  - P95: <±Y.Y%> (target: ±10%)
- **Code quality**: ruff + mypy clean
- **Coverage**: ≥80%

### Files Modified

- `src/docpipe/content_context.py` (3 regexes removed)
- `src/docpipe/markdown_parser_core.py` (17 regexes removed)
- `src/docpipe/md_parser_testing/test_harness_full.py` (new)

### Commits

1. Test harness setup & baseline
2. Fence detection refactoring
3. Inline formatting refactoring
4. Links & images refactoring
5. HTML sanitization refactoring
6. Table detection refactoring
7. Documentation of retained regexes

### Review Checklist (§9)

- [x] Parity: All outputs identical
- [x] Performance: Within budget
- [x] No Hybrids: All removed
- [x] Timeouts: Cross-platform (if applicable)
- [x] HTML: html=False enforced
- [x] Evidence: Complete with SHA256
- [x] Tooling: ruff + mypy clean
- [x] Flag Removal: No MD_REGEX_COMPAT left

## Benefits Achieved

1. **Correctness**: Token-based parsing handles nested markdown correctly
2. **Security**: Reduced regex attack surface, enforced html=False
3. **Maintainability**: Cleaner, more readable code
4. **Performance**: Maintained baseline (within ±5%/±10%)

## Next Steps (Optional)

1. Further performance optimization if needed
2. Additional edge case testing
3. Consider full token-based text reconstruction for remaining use cases
```

---

#### 9.2 Create Final Sign-Off Document

```bash
cat > REFACTORING_COMPLETE.md <<EOF
# Regex Refactoring - Completion Report

**Date**: $(date +%Y-%m-%d)
**Status**: ✅ COMPLETE

## Summary

Successfully refactored markdown parser to use MarkdownIt token-based parsing
instead of brittle regex patterns. Replaced 20+ regex patterns with robust
token traversal while maintaining 100% test compatibility and performance.

## Compliance

All requirements from REGEX_REFACTOR_DETAILED_MERGED.md met:

- ✅ §1: Scope & Constraints met (output parity, perf budget)
- ✅ §3: Commands all passing
- ✅ §4: Design strategy followed (no hybrids, html=False)
- ✅ §5: Test methodology applied (3+5 runs, median/p95)
- ✅ §6: Evidence protocol followed (SHA256 blocks)
- ✅ §8: Sequencing order followed
- ✅ §9: Review checklist complete

## Performance

- Median delta: <±X.X%> ✅
- P95 delta: <±Y.Y%> ✅

## Code Quality

- ruff: ✅ clean
- mypy: ✅ clean
- pytest: ✅ coverage ≥80%

---

**Ready for merge.**
EOF
```

---

## 11. Appendix: Implementation Hints (from §10 of UPDATED plan)

- Prefer one **parse pass** and walk the token stream to collect all structures; avoid re-parsing per category.
- Use `token.map` for line spans (start inclusive, end exclusive).
- For headings: `level = int(token.tag[1])`; text from `inline.children[text]`.
- For links: `href = dict(open.attrs or {}).get('href', '')`; link text from inline text children.
- For images: `src` + `alt` (inline text children).
- Keep the small slug utility but **derive source text from tokens**, not by stripping markdown with regex.

---

## 12. Emergency Rollback Procedure

If tests fail catastrophically at any checkpoint:

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
# Review what went wrong before proceeding
```

---

## 13. CI Gates & Automated Enforcement

These checks run in CI on every PR. Merge is **blocked** if any gate fails.

### Gate 1: No Hybrids (enforced via §4.3)
```bash
#!/bin/bash
# .github/workflows/check_no_hybrids.sh

set -e

echo "Checking for hybrid regex/token flags..."

# CRITICAL: Recursive search, excluding tests and vendored code
# Prevents false positives from test fixtures
HYBRID_FILES=$(find src/docpipe -name "*.py" \
    -not -path "*/test*" \
    -not -path "*/vendor/*" \
    -not -path "*/__pycache__/*" \
    -type f \
    -exec grep -l "USE_TOKEN_\|MD_REGEX_COMPAT" {} + 2>/dev/null || true)

if [ -n "$HYBRID_FILES" ]; then
    echo "❌ MERGE BLOCKED: Feature flags still present"
    echo ""
    echo "Files containing hybrid flags:"
    echo "$HYBRID_FILES"
    echo ""
    echo "Occurrences:"
    find src/docpipe -name "*.py" \
        -not -path "*/test*" \
        -not -path "*/vendor/*" \
        -type f \
        -exec grep -Hn "USE_TOKEN_\|MD_REGEX_COMPAT" {} + 2>/dev/null || true
    exit 1
fi

echo "✅ No hybrid flags detected"
exit 0
```

**Negative Test** (validates gate actually works):
```bash
#!/bin/bash
# .github/workflows/test_check_no_hybrids.sh
# Run this BEFORE the actual gate to verify gate is working

echo "Testing hybrid flag detection (negative test)..."

# Create temporary file with forbidden symbols
TEMP_FILE="src/docpipe/_test_hybrid_detection.py"
echo "# Temporary test file for CI gate validation" > "$TEMP_FILE"
echo "USE_TOKEN_FENCES = True  # This should trigger the gate" >> "$TEMP_FILE"

# Run the gate check
if bash .github/workflows/check_no_hybrids.sh 2>&1 | grep -q "MERGE BLOCKED"; then
    echo "✅ Hybrid gate correctly detects forbidden symbols"
    rm -f "$TEMP_FILE"
    exit 0
else
    echo "❌ CRITICAL: Hybrid gate FAILED to detect test symbol"
    echo "   Gate is misconfigured and would allow hybrids to merge"
    rm -f "$TEMP_FILE"
    exit 1
fi
```

### Gate 2: Parity Check
```bash
#!/bin/bash
# .github/workflows/check_parity.sh

echo "Running parity tests on canonical corpus..."
uv run python src/docpipe/md_parser_testing/test_harness_full.py > test_output.txt

FAILURES=$(grep "Failed:" test_output.txt | awk '{print $2}' | cut -d'/' -f1)

if [ "$FAILURES" != "0" ]; then
    echo "❌ MERGE BLOCKED: $FAILURES test failures"
    grep "❌" test_output.txt | head -20
    exit 1
fi

echo "✅ All tests passing"
exit 0
```

### Gate 3: Performance Regression
```bash
#!/bin/bash
# .github/workflows/check_performance.sh

echo "Comparing performance to baseline..."
python3 << 'PYTHON'
import json, sys

baseline = json.load(open('src/docpipe/md_parser_testing/baseline_performance.json'))
final = json.load(open('src/docpipe/md_parser_testing/final_performance.json'))

# Check median delta
delta_median = ((final['warm_runs']['median_ms'] - baseline['warm_runs']['median_ms']) / baseline['warm_runs']['median_ms']) * 100
delta_p95 = ((final['warm_runs']['p95_ms'] - baseline['warm_runs']['p95_ms']) / baseline['warm_runs']['p95_ms']) * 100

print(f"Median delta: {delta_median:+.1f}% (threshold: ±5%)")
print(f"P95 delta: {delta_p95:+.1f}% (threshold: ±10%)")

if abs(delta_median) > 5:
    print(f"❌ MERGE BLOCKED: Median delta {delta_median:+.1f}% exceeds ±5%")
    sys.exit(1)

if abs(delta_p95) > 10:
    print(f"❌ MERGE BLOCKED: P95 delta {delta_p95:+.1f}% exceeds ±10%")
    sys.exit(1)

print("✅ Performance within budget")
PYTHON
```

### Gate 4: Evidence Hash Validation & Completeness
```bash
#!/bin/bash
# .github/workflows/check_evidence.sh

echo "Validating evidence SHA256 hashes and completeness..."
python3 << 'PYTHON'
import json, hashlib, re, sys

def normalize_whitespace(text):
    return " ".join(text.split())

def compute_hash(quote):
    normalized = normalize_whitespace(quote)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

# Extract JSON blocks from REFACTORING_PLAN_REGEX.md
with open('REFACTORING_PLAN_REGEX.md', 'r') as f:
    content = f.read()

# Find all JSON evidence blocks
json_blocks = re.findall(r'```json\n(\{.*?\})\n```', content, re.DOTALL)

# Required fields per evidence schema (§6)
required_fields = ['quote', 'source_path', 'line_start', 'line_end', 'sha256', 'rationale']

errors = []
warnings = []

for i, block_text in enumerate(json_blocks, 1):
    try:
        evidence = json.loads(block_text)

        # Check completeness
        missing = [f for f in required_fields if f not in evidence]
        if missing:
            warnings.append(f"Evidence block {i}: Missing fields {missing}")

        # Check hash validity
        if 'quote' in evidence and 'sha256' in evidence:
            expected_hash = evidence['sha256']
            actual_hash = compute_hash(evidence['quote'])

            # Check hash format
            if not re.match(r'^[a-f0-9]{64}$', expected_hash):
                errors.append(f"Evidence block {i}: Invalid SHA256 format '{expected_hash}'")
            elif expected_hash != actual_hash:
                errors.append(f"Evidence block {i}: Hash mismatch\n  Expected: {expected_hash}\n  Actual: {actual_hash}")

    except json.JSONDecodeError as e:
        errors.append(f"Evidence block {i}: Invalid JSON - {str(e)}")

# Report results
print(f"Checked {len(json_blocks)} evidence blocks")
print()

if warnings:
    print("⚠️  WARNINGS (incomplete evidence blocks):")
    for warning in warnings:
        print(f"  {warning}")
    print()

if errors:
    print("❌ MERGE BLOCKED: Evidence validation failed")
    for error in errors:
        print(f"  {error}")
    sys.exit(1)

print(f"✅ All {len(json_blocks)} evidence blocks valid")
print(f"   - Hash format: valid")
print(f"   - Hash match: all correct")
if warnings:
    print(f"   - Completeness: {len(warnings)} warnings (non-blocking)")
else:
    print(f"   - Completeness: all fields present")
PYTHON
```

### Gate 5: Canonical Count Verification (Paired Files)
```bash
#!/bin/bash
# .github/workflows/check_canonical_count.sh

echo "Verifying canonical count consistency..."

# CRITICAL: Count ONLY .md files with matching .json siblings (matches test harness logic)
# Prevents false positives when unpaired .md files exist
ACTUAL_COUNT=0
for md_file in $(find src/docpipe/md_parser_testing/test_mds/md_stress_mega -name '*.md' -type f); do
    json_file="${md_file%.md}.json"
    if [ -f "$json_file" ]; then
        ((ACTUAL_COUNT++))
    fi
done

EXPECTED_COUNT=$(jq -r '.canonical_count' src/docpipe/md_parser_testing/baseline_performance.json)

if [ "$EXPECTED_COUNT" != "$ACTUAL_COUNT" ]; then
    # Check baseline age (stat command varies by OS)
    if [ "$(uname)" = "Linux" ]; then
        BASELINE_AGE=$((($(date +%s) - $(stat -c %Y src/docpipe/md_parser_testing/baseline_performance.json 2>/dev/null)) / 86400))
    else
        BASELINE_AGE=$((($(date +%s) - $(stat -f %m src/docpipe/md_parser_testing/baseline_performance.json 2>/dev/null)) / 86400))
    fi

    if [ $BASELINE_AGE -lt 7 ]; then
        echo "❌ MERGE BLOCKED: Canonical count mismatch with fresh baseline"
        echo "  Expected: $EXPECTED_COUNT (from baseline)"
        echo "  Actual:   $ACTUAL_COUNT (paired .md+.json files only)"
        echo "  Baseline age: $BASELINE_AGE days"
        echo ""
        echo "  This indicates test corpus was modified after baseline capture."
        echo "  Action: Regenerate baseline or revert corpus changes."
        exit 1
    else
        echo "⚠️  WARNING: Canonical count drift"
        echo "  Expected: $EXPECTED_COUNT"
        echo "  Actual:   $ACTUAL_COUNT"
        echo "  Baseline is >7 days old, drift may be acceptable"
    fi
fi

echo "✅ Canonical count: $ACTUAL_COUNT (paired files only)"
exit 0
```

### Gate Summary
| Gate | Check | Threshold | Action |
|------|-------|-----------|--------|
| 1 | No hybrid flags | Zero occurrences | **Block** |
| 2 | Test parity | 100% pass rate | **Block** |
| 3 | Performance | Median ≤±5%, P95 ≤±10% | **Block** |
| 4 | Evidence hashes | All valid | **Block** |
| 5 | Canonical count | Matches baseline | **Warn** |

---

## 14. Notes for Executor

1. **Always test incrementally**: Run test harness after every internal checkpoint
2. **Feature flags**: Allowed locally, MUST remove before PR (CI enforces)
3. **Maintain baselines**: baseline_performance.json is source of truth
4. **Document evidence**: SHA256 required for each change (CI validates)
5. **Reflection points**: Stop and validate after each checkpoint
6. **Rollback ready**: Keep git history clean for easy revert
7. **CI gates**: All 5 gates must pass before merge

---

**END OF MERGED EXECUTION PLAN (UPDATED)**

This plan integrates:
- Policy/gates from REGEX_REFACTOR_DETAILED_UPDATED.md (no hybrids, html=False, perf rigor)
- Detailed execution steps from original REGEX_REFACTOR_DETAILED.md (40+ checkpoints)
- Critical bug fixes from technical review (8 major updates)
- Automated CI gates for enforcement (5 blocking checks)

**Ready to execute with high confidence, low risk, and automated guardrails.**
