# NO_SILENTS_proposal.md - Security Kernel Hardening

**Status**: Phase 1 - COMPLETE
**Version**: 3.4 (Aligned with SECURITY_KERNEL_SPEC.md v0.1.6)
**Last Updated**: 2025-12-10
**Last Verified**: -

**Related Documents**:
- [SECURITY_KERNEL_SPEC.md] - **SSOT** for security kernel API and invariants
- [tests/test_security_kernel_spec.py] - Spec-level contract tests (39/39 passing)
- [BUGS_AND_DRIFTS.md] - Issues #1, #2, #3, #14
- [.claude/rules/CLEAN_TABLE_PRINCIPLE.md] - Governing rule
- [.claude/rules/NO_WEAK_TESTS.md] - Test quality standard

---

## 0. Security Kernel Contract

**Before touching code, these invariants are non-negotiable:**

### 0.1 No Silent Security Failures

Any error in security-related code must either:
- (a) Raise a domain exception that bubbles up, OR
- (b) Mark the document as "dangerous" with a clear reason

`except Exception: pass` is **BANNED** in the security path.

### 0.2 Fail-Closed, Not Fail-Open

If we can't complete a prompt-injection or path-traversal check, we treat the content as **suspicious**, not safe.

### 0.3 No Global False Positives on Benign Content

Per SECURITY_KERNEL_SPEC.md INV-SEC-3:
- Benign URLs (`https://`, `mailto:`, `tel:`, etc.) must **normally** not trip security flags
- Local false positives on ambiguous content are acceptable
- **Global/systematic** false positives (e.g., flagging ALL `https://` URLs) are NOT acceptable

### 0.4 Single Source of Truth for Security Limits

Values like `max_data_uri_size` or `max_injection_scan_chars` live in ONE place (`SECURITY_PROFILES` in `config.py`), not duplicated.

> **Note**: This section summarizes SECURITY_KERNEL_SPEC.md invariants INV-SEC-1 through INV-SEC-4. The spec is the authoritative source.

---

## Baseline Policy

Baseline outputs under `tools/baseline_outputs/` are **derived artifacts**, not a
Source of Truth.

**Order of authority:**

1. `SECURITY_KERNEL_SPEC.md` (contract)
2. `test_security_kernel_spec.py` (spec-level tests)
3. NO_SILENTS implementation tests (`tests/test_path_traversal.py`,
   `tests/test_no_silent_exceptions.py`, `tests/test_security_config.py`, …)
4. Baseline tests (`tools/baseline_test_runner.py` + `tools/baseline_outputs/`)

**Implications:**

- Baselines **must not** block fixes that bring the implementation into
  alignment with `SECURITY_KERNEL_SPEC.md`.
- After security behaviour changes (path traversal, prompt injection, budgets),
  the **old** baselines are intentionally wrong and **must** be regenerated.
- Baseline diffs must be **reviewed and explained**:
  - **Expected changes**: removal of false positives, consistent flagging of real
    traversal/injection, structural changes directly implied by the spec.
  - **Unexpected changes**: lost warnings, missing chunks, IR corruption, fields
    changing that are unrelated to security semantics.

**Policy:**

- Never regenerate baselines before:
  - All non-spec tests are green (`uv run pytest tests/ --ignore=test_security_kernel_spec.py`).
  - Spec-contract tests are green (`uv run pytest test_security_kernel_spec.py`).
- Only accept baseline changes that can be mapped back to specific
  SECURITY_KERNEL_SPEC invariants or clearly documented implementation decisions.
- Any unexplained baseline change is treated as a potential regression and must
  be investigated before proceeding.

**Helper script:**
```bash
# Generate diff and classify changes by type
git diff -- tools/baseline_outputs > /tmp/baseline.diff
uv run python tools/classify_baseline_diff.py /tmp/baseline.diff
```

---

## Current Status

### Quick Status Dashboard

| Phase | Status | Tests | Files Changed | Clean Table |
|-------|--------|-------|---------------|-------------|
| 1.0 - Write Tests (TDD) | 📋 PLANNED | 0/16+ | 3 | - |
| 1.1 - Fix _check_path_traversal | 📋 PLANNED | - | 1 | - |
| 1.2 - Fix _build_mappings | 📋 PLANNED | - | 1 | - |
| 1.3 - Fix check_prompt_injection | 📋 PLANNED | - | 2 | - |
| 1.4 - Consolidate config (SSOT) | 📋 PLANNED | - | 2 | - |
| 1.5 - Final Validation | 📋 PLANNED | - | 1 | - |

---

## Prerequisites

**ALL must be verified before starting Phase 1.0**:

- [ ] **Baseline tests pass (current behaviour)**
  Baselines reflect the current 0.2.1 behaviour. We start from a clean, known snapshot.
  ```bash
  uv run python tools/baseline_test_runner.py \
    --test-dir tools/test_mds \
    --baseline-dir tools/baseline_outputs
  ```
  Expected: 542/542 baseline tests passing.

- [ ] **Unit tests (non-spec) pass**
  Run all existing tests excluding the new spec-contract tests. These will be introduced
  in Phase 1.0 and are expected to fail until Phase 1.4 is complete.
  ```bash
  # Run all tests except the spec-contract file
  uv run pytest tests/ -v --ignore=test_security_kernel_spec.py
  ```
  Expected: all collected tests PASS.

- [ ] **No uncommitted changes**: Clean git state
  ```bash
  git status --porcelain
  # Expected: empty output
  ```

**Quick Verification**:
```bash
uv run pytest tests/ -q --ignore=test_security_kernel_spec.py \
  && uv run python tools/baseline_test_runner.py \
       --test-dir tools/test_mds \
       --baseline-dir tools/baseline_outputs \
  && echo "Prerequisites OK"
```

> **Note**: Spec tests (`test_security_kernel_spec.py`) are excluded from prerequisites.
> They define the TARGET behaviour and are expected to fail until implementation is complete.

---

## Rollback Plan

**Before each phase**, create a git tag:

```bash
git tag -a "no-silents-phase-X-start" -m "Before Phase X"
```

**Abort Criteria** - Stop and rethink if:
- Any spec-level tests regress (`test_security_kernel_spec.py`)
- Any NO_SILENTS implementation tests regress
- Baseline diff contains **unexplained** changes (IR structure, content loss, etc.)
- Circular import errors appear

> **Baseline changes explained by SECURITY_KERNEL_SPEC invariants are expected**:
> - Benign URLs no longer flagged as traversal ✅
> - Obvious traversal patterns now consistently flagged ✅
> - Prompt injection results now structured/fail-closed ✅
>
> These must be **reviewed and accepted**, then baselines regenerated.
> Only **unexplained** changes trigger abort.

**Rollback Command**:
```bash
git reset --hard no-silents-phase-X-start
git tag -d no-silents-phase-X-start
```

**Phase Tags**:
| Phase | Tag Name |
|-------|----------|
| 1.0 | `no-silents-phase-1.0-start` |
| 1.1 | `no-silents-phase-1.1-start` |
| 1.2 | `no-silents-phase-1.2-start` |
| 1.3 | `no-silents-phase-1.3-start` |
| 1.4 | `no-silents-phase-1.4-start` |
| 1.5 | `no-silents-phase-1.5-start` |

---

## Phase 1.0 - Write Tests First (TDD)

**Goal**: Create failing tests that prove all bugs exist
**Clean Table Required**: Yes

### Task 1.0.1: Create test files

- [ ] Create `tests/test_path_traversal.py`
- [ ] Create `tests/test_no_silent_exceptions.py`
- [ ] Create `tests/test_security_config.py`

```python
# tests/test_path_traversal.py
"""Tests for path traversal detection - NO false positives on HTTPS.

This file tests doxstrux-specific behaviour that is *stricter* or more
concrete than SECURITY_KERNEL_SPEC.md. Contract invariants live in
test_security_kernel_spec.py.
"""

import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore


# tests/test_no_silent_exceptions.py
"""Tests ensuring no silent exception swallowing per CLEAN_TABLE_PRINCIPLE.

This file tests doxstrux-specific behaviour that is *stricter* or more
concrete than SECURITY_KERNEL_SPEC.md. Contract invariants live in
test_security_kernel_spec.py.
"""

import pytest
from unittest.mock import patch, MagicMock
from doxstrux.markdown_parser_core import MarkdownParserCore
from doxstrux.markdown.security.validators import check_prompt_injection


# tests/test_security_config.py
"""Tests for security config SSOT - no duplicate constants.

This file tests doxstrux-specific behaviour that is *stricter* or more
concrete than SECURITY_KERNEL_SPEC.md. Contract invariants live in
test_security_kernel_spec.py.
"""

import pytest
from doxstrux.markdown.config import SECURITY_PROFILES
from doxstrux.markdown.budgets import get_max_data_uri_size, get_max_injection_scan_chars
```

---

### Task 1.0.2: Test path traversal - NO false positives

```python
# tests/test_path_traversal.py

@pytest.mark.parametrize("url", [
    "https://example.com",
    "https://example.com/path/to/resource",
    "http://example.com/foo/bar",
    "mailto:user@example.com",
    "tel:+3581234567",
    "#anchor-link",
    "relative/path/file.md",
    "Normal text with // but no path traversal",
])
def test_path_traversal_allows_safe_urls(url):
    """Safe URLs must NOT trigger path traversal warnings.

    NO_WEAK_TESTS: Parametrized with specific URL patterns.
    """
    parser = MarkdownParserCore(f"# Test\n\n[link]({url})")
    assert parser._check_path_traversal(url) is False, \
        f"False positive: '{url}' should NOT be flagged"


@pytest.mark.parametrize("url", [
    # Basic traversal
    "../etc/passwd",
    "../../etc/shadow",
    "/../../etc/hosts",
    # Windows traversal
    "..\\..\\Windows\\System32",
    r"C:\Windows\System32\drivers\etc\hosts",
    r"C:\Windows\win.ini",
    r"D:\Users\Admin\Desktop",
    # UNC paths (per SECURITY_KERNEL_SPEC.md §6.2)
    r"\\server\share\file.txt",
    r"\\192.168.1.1\c$\Windows",
    # file:// scheme
    "file:///etc/passwd",
    "file:///C:/Windows/win.ini",
    # Traversal in URL path
    "https://example.com/../../etc/passwd",
    # URL-encoded traversal (per SECURITY_KERNEL_SPEC.md §6.2)
    "https://example.com/%2e%2e/%2e%2e/etc/passwd",
    "%2e%2e/%2e%2e/etc/passwd",
])
def test_path_traversal_flags_attacks(url):
    """Path traversal attacks must be detected.

    NO_WEAK_TESTS: Parametrized with specific attack patterns.
    Per SECURITY_KERNEL_SPEC.md §6.4 test obligations.
    """
    parser = MarkdownParserCore("# Test")
    assert parser._check_path_traversal(url) is True, \
        f"Missed attack: '{url}' should be flagged"
```

**Test Immediately**:
```bash
uv run pytest tests/test_path_traversal.py -v
# Expected: FAILED on test_path_traversal_allows_safe_urls (https:// triggers false positive)
```

---

### Task 1.0.3: Test _build_mappings exception propagation

```python
# tests/test_no_silent_exceptions.py

def test_build_mappings_propagates_type_errors():
    """_build_mappings must propagate TypeError from malformed data.

    Per CLEAN_TABLE_PRINCIPLE: No silent exceptions.
    This tests that exceptions are NOT swallowed.
    """
    content = "# Test\n\n```python\ncode\n```"
    parser = MarkdownParserCore(content)

    # Inject non-iterable where list expected - triggers TypeError
    def mock_get_cached(key, extractor):
        if key == "code_blocks":
            return None  # for b in None raises TypeError
        return extractor()

    with patch.object(parser, '_get_cached', side_effect=mock_get_cached):
        parser._cache.clear()
        with pytest.raises(TypeError):
            parser._build_mappings()


def test_build_mappings_handles_missing_keys_gracefully():
    """_build_mappings handles None start_line/end_line via continue.

    This is INTENTIONAL behavior - missing keys skip the block.
    Separate from exception propagation.
    """
    content = "# Test\n\n```python\ncode\n```"
    parser = MarkdownParserCore(content)

    # Block with missing keys - should be skipped, not crash
    def mock_get_cached(key, extractor):
        if key == "code_blocks":
            return [{"start_line": None, "end_line": None}]  # Skipped via continue
        return extractor()

    with patch.object(parser, '_get_cached', side_effect=mock_get_cached):
        parser._cache.clear()
        mappings = parser._build_mappings()
        # Should complete without error, code_blocks list empty (skipped)
        assert mappings["code_blocks"] == []


def test_build_mappings_correct_classification():
    """_build_mappings correctly classifies code vs prose.

    NO_WEAK_TESTS: Assert specific line numbers, not just key existence.

    NOTE: We intentionally use string keys for line_to_type (e.g., "0", "4").
    This is a stable internal representation for doxstrux. If this changes,
    tests must be updated accordingly.
    """
    # Line 0: # Heading -> prose
    # Line 1: (empty)  -> prose
    # Line 2: Para     -> prose
    # Line 3: (empty)  -> prose
    # Line 4: ```py    -> code
    # Line 5: x = 1    -> code
    # Line 6: ```      -> code
    content = "# Heading\n\nParagraph\n\n```python\nx = 1\n```"
    parser = MarkdownParserCore(content)
    mappings = parser._build_mappings()

    assert mappings["line_to_type"]["0"] == "prose"
    assert mappings["line_to_type"]["4"] == "code"
    assert mappings["line_to_type"]["5"] == "code"
    assert 4 in mappings["code_lines"]
    assert 0 not in mappings["code_lines"]
    assert len(mappings["code_blocks"]) == 1
    assert mappings["code_blocks"][0]["language"] == "python"
```

**Test Immediately**:
```bash
uv run pytest tests/test_no_silent_exceptions.py::test_build_mappings_propagates_errors -v
# Expected: FAILED (exception currently swallowed)
```

---

### Task 1.0.4: Test prompt injection fail-closed

```python
# tests/test_no_silent_exceptions.py

from doxstrux.markdown.security.validators import check_prompt_injection, PromptInjectionCheck

def test_prompt_injection_fails_closed_on_error():
    """check_prompt_injection must fail-closed on errors.

    Per SECURITY_KERNEL_SPEC.md §7.4 and INV-SEC-2.
    """
    with patch('doxstrux.markdown.security.validators.PROMPT_INJECTION_PATTERNS',
               [MagicMock(search=MagicMock(side_effect=RuntimeError("Regex exploded")))]):
        result = check_prompt_injection("test content", profile="strict")
        # Must return suspected=True with reason="validator_error"
        assert isinstance(result, PromptInjectionCheck)
        assert result.suspected is True, "Must fail-closed on error"
        assert result.reason == "validator_error"
        assert result.error is not None


@pytest.mark.parametrize("injection", [
    "ignore previous instructions",
    "disregard previous instructions",
    "forget previous instructions",
    "system: you are a",
    "you are now acting as",
    "pretend you are",
    "simulate being",
    "act as if",
    "bypass your instructions",
    "override your instructions",
])
def test_prompt_injection_detects_all_patterns(injection):
    """Representative injection-like text must be detected.

    Per SECURITY_KERNEL_SPEC.md §7.4: representative injection-like text yields
    suspected=True. For doxstrux, we treat these 10 patterns as mandatory.
    """
    result = check_prompt_injection(injection, profile="strict")
    assert result.suspected is True, f"Missed pattern: '{injection}'"
    assert result.reason == "pattern_match"
    assert result.pattern is not None and result.pattern != ""


@pytest.mark.parametrize("safe_text", [
    "This is normal documentation.",
    "The system processes requests.",
    "Users can ignore this warning.",
    "Previous versions had bugs.",
])
def test_prompt_injection_no_false_positives(safe_text):
    """Safe text must not trigger false positives.

    Per SECURITY_KERNEL_SPEC.md §7.4: normal text yields suspected=False.
    These specific sentences are doxstrux test fixtures, not spec-mandated.
    """
    result = check_prompt_injection(safe_text, profile="strict")
    assert result.suspected is False, f"False positive: '{safe_text}'"
    assert result.reason == "no_match"


def test_prompt_injection_unknown_profile_raises():
    """Unknown profile must raise ValueError.

    Per SECURITY_KERNEL_SPEC.md §7.4 test obligations.
    """
    with pytest.raises(ValueError):
        check_prompt_injection("test", profile="nonexistent_profile")


def test_prompt_injection_default_profile_is_strict():
    """Default profile MUST be 'strict'.

    Per SECURITY_KERNEL_SPEC.md §7.1: Calling check_prompt_injection(text)
    without a profile argument MUST behave identically to
    check_prompt_injection(text, profile="strict").

    Note: Do NOT use _strict_profile_name() helper - must call with no profile
    to actually test the default.
    """
    result_default = check_prompt_injection("Just normal text")
    result_explicit = check_prompt_injection("Just normal text", profile="strict")
    assert result_default == result_explicit


def test_prompt_injection_truncation_respects_profile():
    """Truncation must respect profile's max_injection_scan_chars.

    Per SECURITY_KERNEL_SPEC.md §7.3: patterns after truncation are not detected.

    Note: The cross-profile behaviour below (strict detects what permissive does not)
    is doxstrux-specific. The spec only mandates per-profile truncation semantics,
    not the cross-profile property.
    """
    from doxstrux.markdown.budgets import get_max_injection_scan_chars

    # For permissive (1024 chars), injection beyond that is not detected
    max_len = get_max_injection_scan_chars("permissive")
    payload = "x" * (max_len + 100) + "ignore previous instructions"
    result = check_prompt_injection(payload, profile="permissive")
    assert result.suspected is False, "Pattern after truncation should not be detected"
    assert result.reason == "no_match"

    # For strict (4096 chars), same injection IS detected
    # (doxstrux-specific: strict scans more chars than permissive)
    result_strict = check_prompt_injection(payload, profile="strict")
    assert result_strict.suspected is True, "Strict profile scans more, should detect"
```

**Test Immediately**:
```bash
uv run pytest tests/test_no_silent_exceptions.py -v
# Expected: test_prompt_injection_fails_closed_on_error FAILED
```

---

### Task 1.0.5: Test config SSOT

```python
# tests/test_security_config.py

import pytest
from doxstrux.markdown.config import SECURITY_PROFILES
from doxstrux.markdown.budgets import get_max_data_uri_size, get_max_injection_scan_chars


@pytest.mark.parametrize("profile,expected", [
    ("strict", 0),
    ("moderate", 10240),
    ("permissive", 102400),
])
def test_max_data_uri_size_from_config(profile, expected):
    """Budget values must come from SECURITY_PROFILES (SSOT)."""
    assert get_max_data_uri_size(profile) == expected
    assert SECURITY_PROFILES[profile]["max_data_uri_size"] == expected


@pytest.mark.parametrize("profile,expected", [
    ("strict", 4096),
    ("moderate", 2048),
    ("permissive", 1024),
])
def test_max_injection_scan_chars_from_config(profile, expected):
    """Injection scan chars must come from SECURITY_PROFILES (SSOT).

    Per SECURITY_KERNEL_SPEC.md §8.3 test obligations.

    Note: These exact values (4096/2048/1024) are normative for doxstrux.
    The spec lists them as "recommended defaults"; we enforce them as requirements.
    """
    assert get_max_injection_scan_chars(profile) == expected
    assert SECURITY_PROFILES[profile]["max_injection_scan_chars"] == expected


def test_unknown_profile_raises():
    """Unknown profile must raise ValueError.

    Per SECURITY_KERNEL_SPEC.md §8.3 test obligations.
    """
    with pytest.raises(ValueError):
        get_max_data_uri_size("unknown_profile")
    with pytest.raises(ValueError):
        get_max_injection_scan_chars("unknown_profile")
```

**Clean Table Check for Phase 1.0**:
- [ ] 16+ tests created across 3 test files
- [ ] Path traversal tests: FAILED (false positive bug, missing UNC/URL-decode)
- [ ] Exception tests: FAILED (silent swallow)
- [ ] Prompt injection tests: FAILED (returns bool not PromptInjectionCheck, no profile param)
- [ ] Default profile test: FAILED (default is not "strict")
- [ ] Config tests: FAILED (missing `max_injection_scan_chars`, `get_max_injection_scan_chars()`)
- [ ] Spec tests in `test_security_kernel_spec.py`: EXPECTED TO FAIL (implementation not done)

---

## Phase 1.1 - Fix _check_path_traversal

**Goal**: No more false positives on `https://` URLs
**Clean Table Required**: Yes

### Task 1.1.1: Replace pattern-based check with URL parsing

- [ ] Edit `src/doxstrux/markdown_parser_core.py`

**New implementation** (per SECURITY_KERNEL_SPEC.md §6.2):
```python
from urllib.parse import urlparse, unquote

def _check_path_traversal(self, target: str) -> bool:
    """
    Return True if the string looks like a path traversal attempt.

    Per SECURITY_KERNEL_SPEC.md §6.2:
    - Parse URLs using urlparse for benign schemes
    - Only inspect path component for http/https/mailto/tel
    - Normalize slashes and decode URL-encoded segments
    - Flag traversal (..), file://, Windows drives, UNC paths

    Per SECURITY_KERNEL_SPEC.md §6.3:
    - MUST NOT treat '//' as sufficient evidence of traversal
    """
    if not target:
        return False

    # URL-decode to catch %2e%2e encoded traversal
    decoded = unquote(target)

    # IMPORTANT: Check UNC paths BEFORE normalizing \ to /
    # Otherwise \\server\share becomes //server/share and we miss it
    # Per spec §6.3: Only Windows UNC (\\), NOT // which could be protocol-relative
    if decoded.startswith("\\\\"):
        return True

    # Windows absolute path (C:\, D:\, etc.) - also check before normalizing
    if len(decoded) >= 2 and decoded[1] == ":" and decoded[0].isalpha():
        return True

    # Parse as URL
    parsed = urlparse(decoded)

    # Safe schemes: only inspect path component
    if parsed.scheme.lower() in ("http", "https", "mailto", "tel"):
        candidate = parsed.path or ""
    else:
        candidate = decoded

    # Normalize backslashes to forward slashes (AFTER UNC check)
    normalized = candidate.replace("\\", "/")

    # Check for traversal segments
    if ".." in normalized.split("/"):
        return True

    # file:// scheme is always suspicious
    if parsed.scheme.lower() == "file":
        return True

    return False
```

**Test Immediately**:
```bash
uv run pytest tests/test_path_traversal.py -v
# Expected: ALL PASSED
```

**Clean Table Check**:
- [ ] `https://example.com` returns `False`
- [ ] `../etc/passwd` returns `True`
- [ ] `file:///etc/passwd` returns `True`
- [ ] All path traversal tests pass
- [ ] Baseline tests still pass (542/542)

---

## Phase 1.2 - Fix _build_mappings

**Goal**: Remove silent exception swallowing
**Clean Table Required**: Yes

### Task 1.2.1: Remove bare except

- [ ] Edit `src/doxstrux/markdown_parser_core.py`

**Find location**:
```bash
grep -n "except Exception:" src/doxstrux/markdown_parser_core.py | grep -A1 "pass"
# Look for the one in _build_mappings method
```

**Current** (REMOVE):
```python
try:
    code_blocks = self._get_cached(...)
    for b in code_blocks:
        ...
except Exception:
    pass
```

**Fixed** (no try/except):
```python
# Per CLEAN_TABLE_PRINCIPLE: No silent exceptions
code_blocks = self._get_cached("code_blocks", self._extract_code_blocks)
for b in code_blocks:
    s, e = b.get("start_line"), b.get("end_line")
    if s is None or e is None:
        continue
    # ... rest of processing ...
```

**Test Immediately**:
```bash
uv run pytest tests/test_no_silent_exceptions.py::test_build_mappings_propagates_errors -v
# Expected: PASSED
```

**Clean Table Check**:
- [ ] No `except Exception: pass` in `_build_mappings`
- [ ] Test passes
- [ ] Baseline tests pass (542/542)

---

## Phase 1.3 - Fix check_prompt_injection

**Goal**: Fail-closed on errors, profile-driven, structured return type
**Clean Table Required**: Yes

> **Per SECURITY_KERNEL_SPEC.md §7**: The prompt injection detector MUST expose a structured result and be profile-driven.

### Task 1.3.1: Add PromptInjectionCheck dataclass

- [ ] Edit `src/doxstrux/markdown/security/validators.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class PromptInjectionCheck:
    """Result of prompt injection check - structured for traceability.

    Per SECURITY_KERNEL_SPEC.md §7.1 (INV-SEC-5).
    """
    suspected: bool           # True if injection found OR error occurred
    reason: str               # 'pattern_match', 'validator_error', 'no_match'
    pattern: Optional[str]    # Matched pattern (if any)
    error: Optional[Exception] = None  # For internal diagnostics
```

### Task 1.3.2: Implement profile-driven check_prompt_injection

**New signature per SECURITY_KERNEL_SPEC.md §7.1:**

```python
from ..config import SECURITY_PROFILES

def check_prompt_injection(text: str, profile: str = "strict") -> PromptInjectionCheck:
    """
    Check for prompt injection patterns. FAIL-CLOSED on errors.

    Per SECURITY_KERNEL_SPEC.md §7.2:
    1. Resolve profile via SECURITY_PROFILES
    2. Determine max_len from profile's max_injection_scan_chars
    3. Truncate text to max_len
    4. Check patterns, return structured result
    5. On error, return suspected=True (fail-closed)

    Args:
        text: Content to check
        profile: Security profile name (strict/moderate/permissive)

    Returns:
        PromptInjectionCheck with suspected=True if injection OR error

    Raises:
        ValueError: If profile is unknown
    """
    # Resolve profile (fail hard on unknown)
    if profile not in SECURITY_PROFILES:
        raise ValueError(f"Unknown security profile: {profile}")

    max_len = SECURITY_PROFILES[profile]["max_injection_scan_chars"]

    if not text:
        return PromptInjectionCheck(suspected=False, reason="no_match", pattern=None)

    check_text = text[:max_len]

    try:
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(check_text):
                return PromptInjectionCheck(
                    suspected=True,
                    reason="pattern_match",
                    pattern=pattern.pattern,
                )
        return PromptInjectionCheck(suspected=False, reason="no_match", pattern=None)
    except Exception as exc:
        # FAIL-CLOSED per INV-SEC-2
        return PromptInjectionCheck(
            suspected=True,
            reason="validator_error",
            pattern=None,
            error=exc,
        )
```

**API Change**: This is a breaking change. The new API returns `PromptInjectionCheck` instead of `bool`. Document in CHANGELOG for 0.2.2. No backward compatibility shim needed.

**Module Exports**: Ensure `validators.py` exposes `PROMPT_INJECTION_PATTERNS` for spec tests:
```python
# validators.py - add to module-level exports
__all__ = ["PromptInjectionCheck", "check_prompt_injection", "PROMPT_INJECTION_PATTERNS"]
```
This allows `test_security_kernel_spec.py` to patch the patterns for fail-closed testing.

**Test Immediately**:
```bash
uv run pytest tests/test_no_silent_exceptions.py -v -k "prompt"
# Expected: ALL PASSED
```

**Clean Table Check**:
- [ ] `PromptInjectionCheck` dataclass exists (per SECURITY_KERNEL_SPEC.md §7.1)
- [ ] `check_prompt_injection(text, profile=...)` returns `PromptInjectionCheck`
- [ ] Returns `suspected=True` and `reason="validator_error"` on error (fail-closed)
- [ ] Unknown profile raises `ValueError` (hard failure per spec §7.2)
- [ ] All prompt injection tests pass
- [ ] Spec tests in `test_security_kernel_spec.py` pass

---

## Phase 1.4 - Consolidate Config (SSOT)

**Goal**: Single source of truth for security limits
**Clean Table Required**: Yes

> **Per SECURITY_KERNEL_SPEC.md §8**: All security budgets MUST be defined in `SECURITY_PROFILES`. Other modules MUST access via thin helpers.

### Task 1.4.1: Remove duplicate MAX_DATA_URI_SIZE from budgets.py

- [ ] Edit `src/doxstrux/markdown/budgets.py`

**Remove**:
```python
MAX_DATA_URI_SIZE = {
    "strict": 0,
    "moderate": 10240,
    "permissive": 102400,
}
```

**Add** (per SECURITY_KERNEL_SPEC.md §8.2):
```python
from .config import SECURITY_PROFILES

def get_max_data_uri_size(profile: str) -> int:
    """Get max data URI size from SECURITY_PROFILES (SSOT).

    Per SECURITY_KERNEL_SPEC.md §8.2.
    """
    try:
        return SECURITY_PROFILES[profile]["max_data_uri_size"]
    except KeyError as exc:
        raise ValueError(f"Unknown profile: {profile}") from exc


def get_max_injection_scan_chars(profile: str) -> int:
    """Get max injection scan chars from SECURITY_PROFILES (SSOT).

    Per SECURITY_KERNEL_SPEC.md §8.2.
    """
    try:
        return SECURITY_PROFILES[profile]["max_injection_scan_chars"]
    except KeyError as exc:
        raise ValueError(f"Unknown profile: {profile}") from exc
```

### Task 1.4.2: Add max_injection_scan_chars to config

- [ ] Edit `src/doxstrux/markdown/config.py`

**Per SECURITY_KERNEL_SPEC.md §5 (PROF-3)**, use `max_injection_scan_chars`:

```python
SECURITY_PROFILES = {
    "strict": {
        "max_data_uri_size": 0,
        "max_injection_scan_chars": 4096,  # Strict scans more chars
        # ...
    },
    "moderate": {
        "max_data_uri_size": 10240,
        "max_injection_scan_chars": 2048,
        # ...
    },
    "permissive": {
        "max_data_uri_size": 102400,
        "max_injection_scan_chars": 1024,  # Permissive scans fewer
        # ...
    },
}
```

**Semantics Documentation** (add to config.py docstring):

```python
# SECURITY_PROFILES semantics (per SECURITY_KERNEL_SPEC.md §5):
#
# Most limits: strict < moderate < permissive (smaller = stricter)
#   - max_content_size: 100KB < 1MB < 10MB
#   - max_data_uri_size: 0 < 10KB < 100KB
#
# Exception - max_injection_scan_chars: strict > moderate > permissive
#   - Scanning MORE chars = more thorough = stricter security
#   - 4096 > 2048 > 1024 chars scanned
#   - Recommended defaults per SECURITY_KERNEL_SPEC.md §5 PROF-3
```

**Test Immediately**:
```bash
uv run pytest tests/test_security_config.py -v
# Expected: ALL PASSED
```

**Clean Table Check**:
- [ ] No duplicate `MAX_DATA_URI_SIZE` dict in budgets.py
- [ ] `get_max_data_uri_size()` reads from `SECURITY_PROFILES`
- [ ] `get_max_injection_scan_chars()` reads from `SECURITY_PROFILES`
- [ ] `max_injection_scan_chars` in all profiles with semantics comment
- [ ] All config tests pass
- [ ] No circular imports between budgets.py and config.py
- [ ] Spec tests in `test_security_kernel_spec.py` pass

---

## Phase 1.5 - Final Validation

**Goal**: Verify all fixes work together, spec tests pass, and baselines are updated to the new, correct behaviour.

**Clean Table Required**: Yes — after this phase, SECURITY_KERNEL_SPEC.md and tests are the SSOT for security behaviour.

### Task 1.5.1: Run full unit test suite (non-spec + implementation tests)

```bash
# All unit tests (including NO_SILENTS tests)
uv run pytest tests/ -v --ignore=test_security_kernel_spec.py
# Expected: ALL PASSED
```

### Task 1.5.2: Run spec-contract tests

```bash
# Spec-level tests (THE KEY CONTRACT VALIDATION)
uv run pytest test_security_kernel_spec.py -v
# Expected: ALL PASSED
```

At this point:
- SECURITY_KERNEL_SPEC.md and `test_security_kernel_spec.py` agree.
- NO_SILENTS implementation tests and all other tests are green.

### Task 1.5.3: Regenerate and validate baselines

Once all tests above are green, baselines are now out of date and **must be regenerated**
to reflect the fixed security behaviour.

**Step 1**: Regenerate baselines against the fixed engine:
```bash
uv run python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs \
  --update
```

**Step 2**: Manually review baseline diffs:
```bash
git diff -- tools/baseline_outputs
```

**Step 3**: Classify changes:

| Category | Examples | Action |
|----------|----------|--------|
| ✅ **Expected** | Benign HTTPS URLs no longer marked as traversal | Accept |
| ✅ **Expected** | Obvious traversal now consistently flagged | Accept |
| ✅ **Expected** | Prompt injection results now structured / fail-closed | Accept |
| ❌ **Unexpected** | Lost warnings that should still exist | **ABORT - investigate** |
| ❌ **Unexpected** | Structural IR changes unrelated to security semantics | **ABORT - investigate** |
| ❌ **Unexpected** | Missing chunks or broken document structure | **ABORT - investigate** |

**Abort Phase 1.5 if there are any unexpected baseline changes.**
Investigate and fix the underlying issue, then re-run Tasks 1.5.1–1.5.3.

**Step 4**: If all baseline changes are expected and explained, stage the updated baselines:
```bash
git add tools/baseline_outputs
```

### Task 1.5.4: Verify no silent exceptions remain

```bash
grep -rn "except.*:" src/doxstrux/ --include="*.py" -A1 | grep -E "pass$"
# Expected: No matches in security modules
```

```bash
# Meta-test: no bare except:pass in security modules
uv run pytest test_security_kernel_spec.py::test_security_modules_do_not_use_bare_except_pass -v
# Expected: PASSED
```

> **Note**: The AST-based bare-except detection in `test_security_kernel_spec.py` is
> **stricter than spec INV-SEC-1** which only bans `except Exception: pass`. We ban
> ALL pass-only handlers in security modules as defense in depth.

### Task 1.5.5: Update BUGS_AND_DRIFTS.md

- [ ] Mark Issue #1 (path traversal) as RESOLVED
- [ ] Mark Issue #2 (silent exception) as RESOLVED
- [ ] Mark Issue #3 (fail-open) as RESOLVED
- [ ] Mark Issue #14 (config duplication) as RESOLVED

---

## File Changes Summary

| File | Action | Phase | Description |
|------|--------|-------|-------------|
| `tests/test_path_traversal.py` | CREATE | 1.0 | Path traversal tests (incl. UNC, URL-encoded) |
| `tests/test_no_silent_exceptions.py` | CREATE | 1.0 | Exception handling + prompt injection tests |
| `tests/test_security_config.py` | CREATE | 1.0 | Config SSOT tests |
| `markdown_parser_core.py` | UPDATE | 1.1, 1.2 | Fix path traversal (URL decode, UNC), remove bare except |
| `markdown/security/validators.py` | UPDATE | 1.3 | `PromptInjectionCheck`, profile-driven API |
| `markdown/budgets.py` | UPDATE | 1.4 | Remove duplicate, add `get_max_data_uri_size()`, `get_max_injection_scan_chars()` |
| `markdown/config.py` | UPDATE | 1.4 | Add `max_injection_scan_chars` with semantics comment |
| `tools/classify_baseline_diff.py` | CREATE | - | Helper for reviewing baseline diffs |
| `BUGS_AND_DRIFTS.md` | UPDATE | 1.5 | Mark issues resolved |

---

## Success Criteria (Overall)

- [ ] **Path traversal**
  - No false positives on benign HTTPS/HTTP URLs
  - UNC paths, Windows paths, URL-encoded traversal (`%2e%2e`) are flagged
  - Path traversal guard never returns "safe" (`False`) on internal error

- [ ] **No silent exceptions**
  - Zero `except ...: pass` in security-related modules
  - (`markdown_parser_core`, `validators.py`, `budgets.py`, `config.py`)

- [ ] **Fail-closed**
  - `check_prompt_injection()` returns `PromptInjectionCheck(suspected=True, reason="validator_error")` on internal errors

- [ ] **Profile-driven injection scan**
  - `check_prompt_injection(text, profile=...)` uses `max_injection_scan_chars` from `SECURITY_PROFILES`
  - No hard-coded `1024` anywhere

- [ ] **Structured results**
  - Public API returns `PromptInjectionCheck` (dataclass) instead of bare `bool`
  - Default call `check_prompt_injection(text)` behaves identically to `check_prompt_injection(text, profile="strict")`

- [ ] **Backward compatibility story is explicit**
  - Breaking change is documented in 0.2.2 CHANGELOG
  - No silent API changes

- [ ] **SSOT for security limits**
  - All security budgets (`max_data_uri_size`, `max_injection_scan_chars`) live in `SECURITY_PROFILES`
  - Helpers in `budgets.py` are the only access path; no duplicate budget dicts elsewhere

- [ ] **Tests**
  - All non-spec tests pass (`uv run pytest tests/ -v --ignore=test_security_kernel_spec.py`)

- [ ] **Spec tests**
  - `uv run pytest test_security_kernel_spec.py -v` passes

- [ ] **Baselines**
  - Baselines have been **regenerated after** all tests are green
  - 542/542 baseline tests pass against the **new** behaviour
  - All baseline diffs were manually reviewed and classified as expected

- [ ] **NO_WEAK_TESTS**
  - All new tests have concrete assertions (no "smoke-only" tests)

- [ ] **Rollback**
  - Git tags created for each phase (before/after), so reverting is trivial

---

## Clean Table Principle

> A final answer is considered CLEAN only if ALL of the following are true:
> - ✅ No unresolved errors, warnings, TODOs, placeholders
> - ✅ No unverified assumptions
> - ✅ No duplicated or conflicting logic
> - ✅ Solution is canonical and production-ready
> - ✅ No workarounds masking symptoms

**Each phase must pass Clean Table check before proceeding.**

---

## What's Next

**After this document is complete**:
1. Update BUGS_AND_DRIFTS.md to mark Issues #1, #2, #3, #14 as RESOLVED
2. Add ruff/flake8 rule to catch future `except Exception: pass`
3. Export `PromptInjectionCheck` and `check_prompt_injection` in package `__init__.py`
4. Document API change in CHANGELOG for 0.2.2 (breaking: `check_prompt_injection` returns structured result)
5. Document `max_injection_scan_chars` semantics in README (strict scans more, unlike other limits)
6. Update SECURITY_KERNEL_SPEC.md if any implementation deviates from spec

---

**End of NO_SILENTS_proposal.md**
