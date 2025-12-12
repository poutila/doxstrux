#!/usr/bin/env python3
"""Adversarial Corpus Runner - Shared logic for adversarial testing.

Phase 8 (THREE_ADDITIONS.md) - Adversarial Corpus.

This module provides the core logic for running adversarial tests.
Both pytest tests and CI gate use this shared implementation to avoid drift.

Invariants (from THREE_ADDITIONS.md):
- INV-3.1: No crashes (parser MUST NOT raise uncaught exceptions)
- INV-3.2: Bounded time (parsing MUST complete within timeout)
- INV-3.4: Graceful degradation (MUST return non-None parse result)

Usage:
    from tools.adversarial_runner import run_adversarial_file, run_adversarial_corpus

    # Single file
    result = run_adversarial_file(Path("file.md"), timeout_ms=5000)

    # Full corpus
    results = run_adversarial_corpus(Path("tools/adversarial_mds"))
"""

import os
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doxstrux import parse_markdown_file
from doxstrux.markdown.exceptions import MarkdownSecurityError

# Default timeout in milliseconds (5 seconds per THREE_ADDITIONS.md)
DEFAULT_TIMEOUT_MS = 5000


@dataclass
class AdversarialResult:
    """Result of running an adversarial test on a single file.

    Status values:
    - PASS: Parsed successfully with valid result
    - BLOCKED: Intentionally rejected by security checks (not a crash)
    - CRASH: Unexpected exception (actual bug)
    - TIMEOUT: Parsing exceeded timeout
    - NO_RESULT: Parser returned None or missing metadata.security
    """

    file_path: Path
    status: str  # "PASS", "BLOCKED", "CRASH", "TIMEOUT", "NO_RESULT"
    parse_time_ms: float
    error: str | None = None
    parse_result: dict[str, Any] | None = None

    @property
    def passed(self) -> bool:
        """Check if this result represents a passing test.

        BLOCKED is considered passing - it means security worked correctly.
        """
        return self.status in ("PASS", "BLOCKED")


class ParsingTimeoutError(Exception):
    """Raised when parsing exceeds timeout."""


def _timeout_handler(_signum: int, _frame: Any) -> None:
    """Signal handler for timeout."""
    raise ParsingTimeoutError("Parsing timed out")


def get_timeout_ms() -> int:
    """Get timeout in milliseconds from environment or default.

    Environment variable: DOXSTRUX_ADVERSARIAL_TIMEOUT_MS
    """
    env_timeout = os.environ.get("DOXSTRUX_ADVERSARIAL_TIMEOUT_MS")
    if env_timeout:
        try:
            return int(env_timeout)
        except ValueError:
            pass
    return DEFAULT_TIMEOUT_MS


def run_adversarial_file(
    file_path: Path,
    timeout_ms: int | None = None,
    security_profile: str = "strict",
) -> AdversarialResult:
    """Run adversarial test on a single file.

    INV-3.1: Parser MUST NOT crash on adversarial input.
    INV-3.2: Parsing MUST complete within timeout.
    INV-3.4: MUST return non-None parse result.

    Args:
        file_path: Path to the adversarial markdown file.
        timeout_ms: Timeout in milliseconds (None = use env/default).
        security_profile: Security profile to use (default: "strict").

    Returns:
        AdversarialResult with status and details.
    """
    if timeout_ms is None:
        timeout_ms = get_timeout_ms()

    timeout_seconds = timeout_ms / 1000.0

    # Set up timeout handler (Unix only)
    old_handler = None
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout_seconds)

    start_time = time.perf_counter()

    try:
        # INV-3.1, INV-3.4: Parse file and expect non-None result
        result = parse_markdown_file(file_path, security_profile=security_profile)
        parse_time_ms = (time.perf_counter() - start_time) * 1000

        # INV-3.4: Verify we got a valid parse result
        if result is None:
            return AdversarialResult(
                file_path=file_path,
                status="NO_RESULT",
                parse_time_ms=parse_time_ms,
                error="parse_markdown_file returned None",
            )

        # Verify metadata.security exists
        if "metadata" not in result or "security" not in result.get("metadata", {}):
            return AdversarialResult(
                file_path=file_path,
                status="NO_RESULT",
                parse_time_ms=parse_time_ms,
                error="Parse result missing metadata.security",
            )

        return AdversarialResult(
            file_path=file_path,
            status="PASS",
            parse_time_ms=parse_time_ms,
            parse_result=result,
        )

    except ParsingTimeoutError:
        parse_time_ms = (time.perf_counter() - start_time) * 1000
        return AdversarialResult(
            file_path=file_path,
            status="TIMEOUT",
            parse_time_ms=parse_time_ms,
            error=f"Parsing exceeded {timeout_ms}ms timeout",
        )

    except MarkdownSecurityError as e:
        # Security rejection is intentional, not a crash
        # This means the parser correctly identified and blocked malicious content
        parse_time_ms = (time.perf_counter() - start_time) * 1000
        return AdversarialResult(
            file_path=file_path,
            status="BLOCKED",
            parse_time_ms=parse_time_ms,
            error=f"{type(e).__name__}: {e}",
        )

    except Exception as e:
        # INV-3.1: Any other exception means the parser crashed
        parse_time_ms = (time.perf_counter() - start_time) * 1000
        return AdversarialResult(
            file_path=file_path,
            status="CRASH",
            parse_time_ms=parse_time_ms,
            error=f"{type(e).__name__}: {e}",
        )

    finally:
        # Restore signal handler
        if old_handler is not None and hasattr(signal, "SIGALRM"):
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)


def run_adversarial_corpus(
    corpus_dir: Path,
    timeout_ms: int | None = None,
    security_profile: str = "strict",
) -> list[AdversarialResult]:
    """Run adversarial tests on all files in corpus directory.

    Args:
        corpus_dir: Path to the adversarial corpus directory.
        timeout_ms: Timeout per file in milliseconds.
        security_profile: Security profile to use.

    Returns:
        List of AdversarialResult for each file.
    """
    results = []

    if not corpus_dir.exists():
        raise FileNotFoundError(f"Adversarial corpus not found: {corpus_dir}")

    md_files = sorted(corpus_dir.glob("*.md"))
    if not md_files:
        raise ValueError(f"No .md files found in {corpus_dir}")

    for md_file in md_files:
        result = run_adversarial_file(md_file, timeout_ms, security_profile)
        results.append(result)

    return results


def summarize_results(results: list[AdversarialResult]) -> dict[str, Any]:
    """Summarize adversarial test results.

    Returns:
        Dictionary with pass/fail counts and details.
    """
    passed = sum(1 for r in results if r.status == "PASS")
    blocked = sum(1 for r in results if r.status == "BLOCKED")
    crashed = sum(1 for r in results if r.status == "CRASH")
    timed_out = sum(1 for r in results if r.status == "TIMEOUT")
    no_result = sum(1 for r in results if r.status == "NO_RESULT")

    # BLOCKED is considered "passed" - security worked correctly
    all_passed = all(r.passed for r in results)

    return {
        "total": len(results),
        "passed": passed,
        "blocked": blocked,
        "crashed": crashed,
        "timed_out": timed_out,
        "no_result": no_result,
        "all_passed": all_passed,
        "failures": [
            {"file": str(r.file_path.name), "status": r.status, "error": r.error}
            for r in results
            if not r.passed
        ],
    }


if __name__ == "__main__":
    # Quick test when run directly
    import argparse

    parser = argparse.ArgumentParser(description="Run adversarial corpus tests")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=Path(__file__).parent / "adversarial_mds",
        help="Path to adversarial corpus directory",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout per file in milliseconds",
    )
    parser.add_argument(
        "--profile",
        default="strict",
        choices=["strict", "moderate", "permissive"],
        help="Security profile to use",
    )

    args = parser.parse_args()

    print(f"Running adversarial corpus: {args.corpus_dir}")
    print(f"Timeout: {args.timeout or get_timeout_ms()}ms")
    print(f"Profile: {args.profile}")
    print("-" * 60)

    results = run_adversarial_corpus(args.corpus_dir, args.timeout, args.profile)

    for result in results:
        status_icon = "✓" if result.passed else "✗"
        print(f"{status_icon} {result.file_path.name}: {result.status} ({result.parse_time_ms:.1f}ms)")
        if result.error:
            print(f"    Error: {result.error}")

    print("-" * 60)
    summary = summarize_results(results)
    print(f"Total: {summary['total']}, Passed: {summary['passed']}, Failed: {summary['total'] - summary['passed']}")

    sys.exit(0 if summary["all_passed"] else 1)
