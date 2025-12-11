"""Tests ensuring no silent exception swallowing per CLEAN_TABLE_PRINCIPLE.

This file tests doxstrux-specific behaviour that is *stricter* or more
concrete than SECURITY_KERNEL_SPEC.md. Contract invariants live in
test_security_kernel_spec.py.
"""

import pytest
from unittest.mock import patch, MagicMock
from doxstrux.markdown_parser_core import MarkdownParserCore


def test_build_mappings_propagates_type_errors():
    """_build_mappings must propagate TypeError from malformed data.

    Per CLEAN_TABLE_PRINCIPLE: No silent exceptions.
    This tests that exceptions are NOT swallowed.
    """
    parser = MarkdownParserCore("# Test\n\n```python\ncode\n```")

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
    parser = MarkdownParserCore("# Test\n\n```python\ncode\n```")

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
    parser = MarkdownParserCore("# Heading\n\nParagraph\n\n```python\nx = 1\n```")
    mappings = parser._build_mappings()

    assert mappings["line_to_type"]["0"] == "prose"
    assert mappings["line_to_type"]["4"] == "code"
    assert mappings["line_to_type"]["5"] == "code"
    assert 4 in mappings["code_lines"]
    assert 0 not in mappings["code_lines"]
    assert len(mappings["code_blocks"]) == 1
    assert mappings["code_blocks"][0]["language"] == "python"


# Prompt injection tests - these depend on PromptInjectionCheck dataclass
# which will be implemented in Phase 1.3

def test_prompt_injection_fails_closed_on_error():
    """check_prompt_injection must fail-closed on errors.

    Per SECURITY_KERNEL_SPEC.md section 7.4 and INV-SEC-2.
    """
    # Import here to get whatever current implementation exists
    from doxstrux.markdown.security.validators import check_prompt_injection

    # Try to import PromptInjectionCheck - it may not exist yet
    try:
        from doxstrux.markdown.security.validators import PromptInjectionCheck
    except ImportError:
        pytest.fail("PromptInjectionCheck dataclass not implemented yet")

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

    Per SECURITY_KERNEL_SPEC.md section 7.4: representative injection-like text yields
    suspected=True. For doxstrux, we treat these 10 patterns as mandatory.
    """
    from doxstrux.markdown.security.validators import check_prompt_injection

    try:
        from doxstrux.markdown.security.validators import PromptInjectionCheck
    except ImportError:
        pytest.fail("PromptInjectionCheck dataclass not implemented yet")

    result = check_prompt_injection(injection, profile="strict")
    assert isinstance(result, PromptInjectionCheck), \
        f"Expected PromptInjectionCheck, got {type(result)}"
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

    Per SECURITY_KERNEL_SPEC.md section 7.4: normal text yields suspected=False.
    These specific sentences are doxstrux test fixtures, not spec-mandated.
    """
    from doxstrux.markdown.security.validators import check_prompt_injection

    try:
        from doxstrux.markdown.security.validators import PromptInjectionCheck
    except ImportError:
        pytest.fail("PromptInjectionCheck dataclass not implemented yet")

    result = check_prompt_injection(safe_text, profile="strict")
    assert isinstance(result, PromptInjectionCheck), \
        f"Expected PromptInjectionCheck, got {type(result)}"
    assert result.suspected is False, f"False positive: '{safe_text}'"
    assert result.reason == "no_match"


def test_prompt_injection_unknown_profile_raises():
    """Unknown profile must raise ValueError.

    Per SECURITY_KERNEL_SPEC.md section 7.4 test obligations.
    """
    from doxstrux.markdown.security.validators import check_prompt_injection

    with pytest.raises(ValueError):
        check_prompt_injection("test", profile="nonexistent_profile")


def test_prompt_injection_default_profile_is_strict():
    """Default profile MUST be 'strict'.

    Per SECURITY_KERNEL_SPEC.md section 7.1: Calling check_prompt_injection(text)
    without a profile argument MUST behave identically to
    check_prompt_injection(text, profile="strict").

    Note: Do NOT use _strict_profile_name() helper - must call with no profile
    to actually test the default.
    """
    from doxstrux.markdown.security.validators import check_prompt_injection

    result_default = check_prompt_injection("Just normal text")
    result_explicit = check_prompt_injection("Just normal text", profile="strict")
    assert result_default == result_explicit


def test_prompt_injection_truncation_respects_profile():
    """Truncation must respect profile's max_injection_scan_chars.

    Per SECURITY_KERNEL_SPEC.md section 7.3: patterns after truncation are not detected.

    Note: The cross-profile behaviour below (strict detects what permissive does not)
    is doxstrux-specific. The spec only mandates per-profile truncation semantics,
    not the cross-profile property.
    """
    try:
        from doxstrux.markdown.budgets import get_max_injection_scan_chars
    except ImportError:
        pytest.fail("get_max_injection_scan_chars not implemented yet")

    from doxstrux.markdown.security.validators import check_prompt_injection

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
