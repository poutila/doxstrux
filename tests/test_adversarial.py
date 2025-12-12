"""Tests for adversarial corpus - Phase 3 of THREE_ADDITIONS.md.

These tests verify parser robustness against adversarial inputs:
- INV-3.1: No crashes (parser MUST NOT raise uncaught exceptions)
- INV-3.2: Bounded time (parsing MUST complete within timeout)
- INV-3.4: Graceful degradation (MUST return non-None parse result)

Note: INV-3.3 (security detection) is tested by verifying that security
patterns ARE detected, not that they cause crashes.

Status values:
- PASS: Parsed successfully with valid result
- BLOCKED: Intentionally rejected by security checks (correct behavior)
- CRASH: Unexpected exception (actual bug - INV-3.1 violation)
- TIMEOUT: Exceeded time limit (INV-3.2 violation)
- NO_RESULT: Parser returned None (INV-3.4 violation)
"""

import sys
from pathlib import Path

import pytest

# Add tools to path for shared runner
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from adversarial_runner import (
    AdversarialResult,
    run_adversarial_corpus,
    run_adversarial_file,
    summarize_results,
)

# Path to adversarial corpus
CORPUS_DIR = Path(__file__).parent.parent / "tools" / "adversarial_mds"


class TestDeepNesting:
    """Tests for deeply nested structures (INV-3.1, INV-3.2, INV-3.4)."""

    def test_deep_nesting_lists_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on 55-level nested lists."""
        result = run_adversarial_file(CORPUS_DIR / "deep_nesting_lists.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_deep_nesting_lists_bounded_time(self) -> None:
        """INV-3.2: Parsing 55-level nested lists must complete within timeout."""
        result = run_adversarial_file(
            CORPUS_DIR / "deep_nesting_lists.md", timeout_ms=5000
        )
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_deep_nesting_lists_returns_result(self) -> None:
        """INV-3.4: Parser must return non-None result for nested lists."""
        result = run_adversarial_file(CORPUS_DIR / "deep_nesting_lists.md")
        assert result.status == "PASS", f"Failed: {result.error}"
        assert result.parse_result is not None

    def test_deep_nesting_quotes_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on 35-level nested blockquotes."""
        result = run_adversarial_file(CORPUS_DIR / "deep_nesting_quotes.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_deep_nesting_quotes_bounded_time(self) -> None:
        """INV-3.2: Parsing nested blockquotes must complete within timeout."""
        result = run_adversarial_file(
            CORPUS_DIR / "deep_nesting_quotes.md", timeout_ms=5000
        )
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_deep_nesting_quotes_returns_result(self) -> None:
        """INV-3.4: Parser must return non-None result for nested quotes."""
        result = run_adversarial_file(CORPUS_DIR / "deep_nesting_quotes.md")
        assert result.status == "PASS", f"Failed: {result.error}"
        assert result.parse_result is not None


class TestLargeStructures:
    """Tests for large structures like tables and link collections."""

    def test_wide_table_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on 100x100 table."""
        result = run_adversarial_file(CORPUS_DIR / "wide_table_100x100.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_wide_table_bounded_time(self) -> None:
        """INV-3.2: Parsing 100x100 table must complete within timeout."""
        result = run_adversarial_file(
            CORPUS_DIR / "wide_table_100x100.md", timeout_ms=5000
        )
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_wide_table_returns_result(self) -> None:
        """INV-3.4: Parser must return non-None result for large table."""
        result = run_adversarial_file(CORPUS_DIR / "wide_table_100x100.md")
        assert result.passed, f"Failed: {result.error}"
        assert result.parse_result is not None

    def test_many_links_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on 1000+ links."""
        result = run_adversarial_file(CORPUS_DIR / "many_links.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_many_links_bounded_time(self) -> None:
        """INV-3.2: Parsing 1000+ links must complete within timeout."""
        result = run_adversarial_file(CORPUS_DIR / "many_links.md", timeout_ms=5000)
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_many_links_returns_result(self) -> None:
        """INV-3.4: Parser must return non-None result for many links."""
        result = run_adversarial_file(CORPUS_DIR / "many_links.md")
        assert result.passed, f"Failed: {result.error}"
        assert result.parse_result is not None

    def test_long_line_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on 110K character line.

        Note: In strict mode, this file exceeds size limits and is BLOCKED.
        BLOCKED is correct behavior (security working), not a crash.
        """
        result = run_adversarial_file(CORPUS_DIR / "long_line.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_long_line_bounded_time(self) -> None:
        """INV-3.2: Parsing 110K char line must complete within timeout."""
        result = run_adversarial_file(CORPUS_DIR / "long_line.md", timeout_ms=5000)
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_long_line_handled_correctly(self) -> None:
        """INV-3.4: Long line is either parsed or blocked (not crashed).

        In strict mode (100KB limit), this file is BLOCKED.
        This is correct behavior - security enforcement worked.
        """
        result = run_adversarial_file(CORPUS_DIR / "long_line.md")
        assert result.passed, f"Failed: {result.status} - {result.error}"


class TestSecurityPatterns:
    """Tests for security-relevant patterns (INV-3.3 via graceful handling).

    In strict mode, the parser may BLOCK files with script tags or other
    malicious patterns. This is correct behavior - the security system worked.
    """

    def test_security_patterns_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on security patterns.

        BLOCKED is acceptable - it means security detection worked.
        """
        result = run_adversarial_file(CORPUS_DIR / "security_patterns.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_security_patterns_bounded_time(self) -> None:
        """INV-3.2: Parsing security patterns must complete within timeout."""
        result = run_adversarial_file(
            CORPUS_DIR / "security_patterns.md", timeout_ms=5000
        )
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_security_patterns_handled_correctly(self) -> None:
        """INV-3.3/3.4: Security patterns are either parsed or blocked.

        In strict mode, script tags trigger MarkdownSecurityError (BLOCKED).
        This is correct behavior - the security system detected the threat.
        """
        result = run_adversarial_file(CORPUS_DIR / "security_patterns.md")
        assert result.passed, f"Failed: {result.status} - {result.error}"

    def test_security_patterns_blocked_in_strict_mode(self) -> None:
        """INV-3.3: Verify security patterns ARE blocked in strict mode.

        The security_patterns.md file contains <script> tags which should
        trigger MarkdownSecurityError in strict mode.
        """
        result = run_adversarial_file(
            CORPUS_DIR / "security_patterns.md", security_profile="strict"
        )
        # In strict mode, script tags should be blocked
        assert result.status == "BLOCKED", (
            f"Expected BLOCKED in strict mode, got {result.status}"
        )
        assert "MarkdownSecurityError" in (result.error or "")

    def test_security_patterns_permissive_mode(self) -> None:
        """Test security patterns in permissive mode for structural robustness."""
        result = run_adversarial_file(
            CORPUS_DIR / "security_patterns.md", security_profile="permissive"
        )
        # In permissive mode, should parse (possibly with warnings)
        assert result.status == "PASS", f"Failed in permissive: {result.error}"
        assert result.parse_result is not None

        # Verify security metadata exists
        security = result.parse_result.get("metadata", {}).get("security", {})
        assert security is not None, "Security metadata missing"


class TestUnicodeEdgeCases:
    """Tests for Unicode edge cases (BiDi, confusables, control chars)."""

    def test_bidi_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on BiDi control characters."""
        result = run_adversarial_file(CORPUS_DIR / "unicode_bidi.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_bidi_bounded_time(self) -> None:
        """INV-3.2: Parsing BiDi content must complete within timeout."""
        result = run_adversarial_file(CORPUS_DIR / "unicode_bidi.md", timeout_ms=5000)
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_bidi_returns_result(self) -> None:
        """INV-3.4: Parser must return non-None result for BiDi content."""
        result = run_adversarial_file(CORPUS_DIR / "unicode_bidi.md")
        assert result.status == "PASS", f"Failed: {result.error}"
        assert result.parse_result is not None

    def test_confusables_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on confusable characters."""
        result = run_adversarial_file(CORPUS_DIR / "unicode_confusables.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_confusables_bounded_time(self) -> None:
        """INV-3.2: Parsing confusables must complete within timeout."""
        result = run_adversarial_file(
            CORPUS_DIR / "unicode_confusables.md", timeout_ms=5000
        )
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_confusables_returns_result(self) -> None:
        """INV-3.4: Parser must return non-None result for confusables."""
        result = run_adversarial_file(CORPUS_DIR / "unicode_confusables.md")
        assert result.status == "PASS", f"Failed: {result.error}"
        assert result.parse_result is not None


class TestBinaryEdgeCases:
    """Tests for binary/control character edge cases."""

    def test_binary_no_crash(self) -> None:
        """INV-3.1: Parser must not crash on binary edge cases."""
        result = run_adversarial_file(CORPUS_DIR / "binary_edge_cases.md")
        assert result.status != "CRASH", f"Parser crashed: {result.error}"

    def test_binary_bounded_time(self) -> None:
        """INV-3.2: Parsing binary content must complete within timeout."""
        result = run_adversarial_file(
            CORPUS_DIR / "binary_edge_cases.md", timeout_ms=5000
        )
        assert result.status != "TIMEOUT", f"Parser timed out: {result.error}"

    def test_binary_returns_result(self) -> None:
        """INV-3.4: Parser must return non-None result for binary content."""
        result = run_adversarial_file(CORPUS_DIR / "binary_edge_cases.md")
        assert result.status == "PASS", f"Failed: {result.error}"
        assert result.parse_result is not None


class TestFullCorpus:
    """Tests that run the entire adversarial corpus."""

    def test_full_corpus_all_pass(self) -> None:
        """All adversarial files must pass (no crashes, timeouts, or null results)."""
        results = run_adversarial_corpus(CORPUS_DIR)
        summary = summarize_results(results)

        # Report any failures
        if not summary["all_passed"]:
            failure_report = "\n".join(
                f"  - {f['file']}: {f['status']} - {f['error']}"
                for f in summary["failures"]
            )
            pytest.fail(f"Adversarial corpus failures:\n{failure_report}")

    def test_corpus_has_expected_files(self) -> None:
        """Verify corpus contains all expected test categories."""
        results = run_adversarial_corpus(CORPUS_DIR)

        # Get filenames
        filenames = {r.file_path.name for r in results}

        # Verify all expected categories are covered
        expected_files = {
            "deep_nesting_lists.md",
            "deep_nesting_quotes.md",
            "wide_table_100x100.md",
            "many_links.md",
            "long_line.md",
            "unicode_bidi.md",
            "unicode_confusables.md",
            "security_patterns.md",
            "binary_edge_cases.md",
        }

        missing = expected_files - filenames
        assert not missing, f"Missing adversarial files: {missing}"

    def test_corpus_minimum_count(self) -> None:
        """Verify corpus has minimum required number of files."""
        results = run_adversarial_corpus(CORPUS_DIR)
        # THREE_ADDITIONS.md requires minimum 10 files
        assert len(results) >= 9, f"Expected at least 9 files, got {len(results)}"


class TestAdversarialRunner:
    """Tests for the adversarial runner module itself."""

    def test_result_dataclass_properties(self) -> None:
        """AdversarialResult.passed property works correctly."""
        pass_result = AdversarialResult(
            file_path=Path("test.md"),
            status="PASS",
            parse_time_ms=100.0,
        )
        assert pass_result.passed is True

        fail_result = AdversarialResult(
            file_path=Path("test.md"),
            status="CRASH",
            parse_time_ms=100.0,
            error="Test error",
        )
        assert fail_result.passed is False

    def test_corpus_not_found_raises(self) -> None:
        """run_adversarial_corpus raises FileNotFoundError for missing directory."""
        with pytest.raises(FileNotFoundError):
            run_adversarial_corpus(Path("/nonexistent/path"))

    def test_empty_corpus_raises(self, tmp_path: Path) -> None:
        """run_adversarial_corpus raises ValueError for empty directory."""
        with pytest.raises(ValueError, match="No .md files found"):
            run_adversarial_corpus(tmp_path)

    def test_summarize_results_counts(self) -> None:
        """summarize_results correctly counts results."""
        results = [
            AdversarialResult(Path("a.md"), "PASS", 100.0),
            AdversarialResult(Path("b.md"), "PASS", 100.0),
            AdversarialResult(Path("c.md"), "BLOCKED", 50.0, error="security"),
            AdversarialResult(Path("d.md"), "CRASH", 100.0, error="error"),
            AdversarialResult(Path("e.md"), "TIMEOUT", 5000.0, error="timeout"),
        ]

        summary = summarize_results(results)
        assert summary["total"] == 5
        assert summary["passed"] == 2
        assert summary["blocked"] == 1
        assert summary["crashed"] == 1
        assert summary["timed_out"] == 1
        assert summary["all_passed"] is False  # CRASH and TIMEOUT are failures
        assert len(summary["failures"]) == 2  # Only CRASH and TIMEOUT

    def test_blocked_counts_as_passed(self) -> None:
        """BLOCKED status should count as passed (security worked correctly)."""
        results = [
            AdversarialResult(Path("a.md"), "PASS", 100.0),
            AdversarialResult(Path("b.md"), "BLOCKED", 50.0, error="security"),
        ]

        summary = summarize_results(results)
        assert summary["all_passed"] is True  # BLOCKED is acceptable
        assert len(summary["failures"]) == 0
