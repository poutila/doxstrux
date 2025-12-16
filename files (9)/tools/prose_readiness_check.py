#!/usr/bin/env python3
"""
prose_readiness_check.py

Pre-flight validation for prose documents before AI Task List framework conversion.

This tool validates that a prose document (design doc, spec, requirements) has
sufficient structure and content to produce a useful AI task list.

Exit codes:
    0 = Ready (all checks pass)
    1 = Warnings (quality issues but conversion possible)
    2 = Blockers (missing required structure; do not proceed)
    3 = Usage/file error

Usage:
    uv run python tools/prose_readiness_check.py PYDANTIC_SCHEMA.md
    uv run python tools/prose_readiness_check.py --json PYDANTIC_SCHEMA.md
    uv run python tools/prose_readiness_check.py --strict PYDANTIC_SCHEMA.md  # warnings become blockers

SSOT: This tool validates input prose; tools/ai_task_list_linter.py validates output task lists.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Pattern, Tuple


TOOL_VERSION = "1.0.0"


class Severity(Enum):
    """Check result severity levels."""
    BLOCKER = "blocker"      # Cannot proceed; framework will fail
    WARNING = "warning"      # Quality issue; framework may produce poor output
    INFO = "info"            # Suggestion; no impact on conversion


@dataclass
class CheckResult:
    """Result of a single readiness check."""
    check_id: str
    name: str
    severity: Severity
    passed: bool
    message: str
    evidence: List[str] = field(default_factory=list)  # Matching lines or locations
    line_numbers: List[int] = field(default_factory=list)


@dataclass
class ReadinessReport:
    """Complete readiness assessment for a prose document."""
    file_path: str
    ready: bool  # True if no blockers
    blocker_count: int
    warning_count: int
    info_count: int
    checks: List[CheckResult]

    def exit_code(self, strict: bool = False) -> int:
        """Determine exit code based on results."""
        if self.blocker_count > 0:
            return 2
        if strict and self.warning_count > 0:
            return 1
        if self.warning_count > 0:
            return 1
        return 0


# =============================================================================
# CHECK DEFINITIONS
# =============================================================================

# Required structure patterns (BLOCKERS if missing)
REQUIRED_CHECKS: List[Tuple[str, str, Pattern[str], str, str]] = [
    (
        "REQ-001",
        "Phases or milestones defined",
        re.compile(r"^#{1,3}\s+(Phase|Milestone|Step|Stage)\s+", re.MULTILINE | re.IGNORECASE),
        "No phase/milestone headings found. The framework requires identifiable phases to map to `## Phase N`.",
        "Add headings like `## Phase 0 — Discovery` or `## Milestone A — Core Implementation`.",
    ),
    (
        "REQ-002",
        "File paths specified",
        re.compile(r"[`'\"]?(?:src|tests|tools|lib|app)/[\w/._-]+\.(?:py|js|ts|jsx|tsx|md|json|yaml|yml|toml)[`'\"]?", re.IGNORECASE),
        "No explicit file paths found. The framework requires paths for `TASK_N_M_PATHS` arrays.",
        "Include concrete paths like `src/module/file.py` or `tests/test_feature.py`.",
    ),
    (
        "REQ-003",
        "Success criteria present",
        re.compile(r"(-\s*\[[ x]\]|Done when|Exit criteria|Success criteria|Acceptance criteria|Definition of done|✅|☑)", re.IGNORECASE),
        "No success criteria found. The framework maps these to STOP block checklists.",
        "Add checklists (`- [ ] Item`) or explicit success criteria sections.",
    ),
    (
        "REQ-004",
        "Executable commands present",
        re.compile(r"(^\$\s+\w+|```(?:bash|sh|shell|console)|pytest|python\s|uv\s+run|npm\s+run|cargo\s+|go\s+run)", re.MULTILINE | re.IGNORECASE),
        "No executable commands found. The framework requires commands for TDD steps and evidence capture.",
        "Include concrete commands like `$ uv run pytest tests/` or fenced bash blocks.",
    ),
]

# Quality signal patterns (WARNINGS if missing)
QUALITY_CHECKS: List[Tuple[str, str, Pattern[str], str, str]] = [
    (
        "QUAL-001",
        "SSOT declaration",
        re.compile(r"(SSOT|single source of truth|authoritative|canonical|this (?:document|file) is the)", re.IGNORECASE),
        "No SSOT declaration found. Without this, drift between prose and other docs is likely.",
        "Add a declaration like 'This document is the SSOT for X' or 'Authoritative source for...'.",
    ),
    (
        "QUAL-002",
        "Explicit decisions section",
        re.compile(r"(^#{1,3}\s*Decisions?|Decision:|Decided:|Binding|ADR|Architecture Decision|\bResolved\b)", re.MULTILINE | re.IGNORECASE),
        "No explicit decisions section. Open questions mixed with decisions cause ambiguous tasks.",
        "Add a 'Decisions' section that distinguishes binding decisions from open questions.",
    ),
    (
        "QUAL-003",
        "Dependencies stated",
        re.compile(r"(depends on|requires|prerequisite|after completing|before starting|blocked by|unlocks)", re.IGNORECASE),
        "No explicit dependencies found. The framework uses Phase Unlock artifacts for gating.",
        "State dependencies like 'Phase B requires Phase A complete' or 'Task 2.1 depends on 1.3'.",
    ),
    (
        "QUAL-004",
        "Scope boundaries defined",
        re.compile(r"(in scope|out of scope|scope:|not included|excluded|boundaries|constraints)", re.IGNORECASE),
        "No scope boundaries found. Unbounded scope leads to unbounded task lists.",
        "Add 'In scope: X, Y, Z' and 'Out of scope: A, B, C' sections.",
    ),
    (
        "QUAL-005",
        "Test strategy mentioned",
        re.compile(r"(test strategy|testing approach|test plan|unit test|integration test|TDD|test-driven)", re.IGNORECASE),
        "No test strategy mentioned. The framework enforces TDD structure for every task.",
        "Describe how features will be tested (unit tests, integration tests, etc.).",
    ),
]

# Anti-patterns (WARNINGS when found)
ANTI_PATTERN_CHECKS: List[Tuple[str, str, Pattern[str], str, str]] = [
    (
        "ANTI-001",
        "Time estimates present",
        re.compile(r"\b(\d+[-–]\d+\s*(hours?|days?|weeks?|mins?|minutes?)|\d+\s*(hours?|days?|weeks?)\s*(estimate|estimated|approx))", re.IGNORECASE),
        "Contains time estimates. The framework tracks completion status, not time.",
        "Remove time estimates or move them to a separate planning document.",
    ),
    (
        "ANTI-002",
        "Unresolved TBD/TODO markers",
        re.compile(r"\b(TBD|TODO|TBC|FIXME|XXX|PLACEHOLDER)\b(?!\s*:?\s*\d)", re.IGNORECASE),  # Exclude "TODO: 123" style refs
        "Contains unresolved TBD/TODO markers. These cannot become concrete tasks.",
        "Resolve all TBD items before conversion, or explicitly mark as 'deferred to Phase X'.",
    ),
    (
        "ANTI-003",
        "Conditional/branching logic",
        re.compile(r"(if\s+(?:we|you|the|this).+then|otherwise\s+(?:we|you)|alternatively,?\s+(?:we|you)|depending on)", re.IGNORECASE),
        "Contains conditional logic. The framework doesn't support conditional tasks.",
        "Resolve conditions into concrete decisions, or split into separate task lists.",
    ),
    (
        "ANTI-004",
        "Vague action verbs",
        re.compile(r"(consider\s+(?:adding|implementing|using)|maybe\s+(?:add|use|implement)|might\s+(?:need|want|have)|should probably|could potentially)", re.IGNORECASE),
        "Contains vague/tentative language. Tasks must be concrete and actionable.",
        "Replace 'consider adding X' with 'Add X' or explicitly defer to future phase.",
    ),
    (
        "ANTI-005",
        "Questions without answers",
        re.compile(r"(\?\s*$|^[\s>]*Q:|Open question:|To be determined:|Need to decide:)", re.MULTILINE | re.IGNORECASE),
        "Contains unanswered questions. Unresolved questions create ambiguous tasks.",
        "Answer questions or move them to an 'Open Questions' section marked out-of-scope.",
    ),
]

# Structural quality checks (INFO level)
STRUCTURE_CHECKS: List[Tuple[str, str, Callable[[str, List[str]], Tuple[bool, str, List[str], List[int]]], str]] = [
    (
        "STRUCT-001",
        "Reasonable document length",
        lambda content, lines: (
            len(lines) <= 3000,
            f"Document has {len(lines)} lines. Very large documents may exceed AI context limits.",
            [],
            [],
        ),
        "Consider splitting into multiple documents if over 2000 lines.",
    ),
    (
        "STRUCT-002",
        "Heading hierarchy consistent",
        lambda content, lines: _check_heading_hierarchy(lines),
        "Use consistent heading levels (## for phases, ### for tasks, #### for substeps).",
    ),
    (
        "STRUCT-003",
        "Code blocks are fenced",
        lambda content, lines: (
            content.count("```") % 2 == 0 and content.count("```") >= 2,
            f"Found {content.count('```') // 2} fenced code blocks." if content.count("```") % 2 == 0 else "Unclosed fenced code block detected.",
            [],
            [],
        ),
        "Ensure all code blocks use triple backticks and are properly closed.",
    ),
]


def _check_heading_hierarchy(lines: List[str]) -> Tuple[bool, str, List[str], List[int]]:
    """Check that heading levels follow a logical hierarchy."""
    headings: List[Tuple[int, int, str]] = []  # (line_num, level, text)

    for i, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            text = match.group(2)
            headings.append((i + 1, level, text))

    if not headings:
        return False, "No headings found in document.", [], []

    issues: List[str] = []
    issue_lines: List[int] = []

    prev_level = 0
    for line_num, level, text in headings:
        # Check for level skip (e.g., # to ### without ##)
        if prev_level > 0 and level > prev_level + 1:
            issues.append(f"Line {line_num}: Skipped heading level (#{prev_level} to #{level}): {text[:40]}")
            issue_lines.append(line_num)
        prev_level = level

    if issues:
        return False, f"Found {len(issues)} heading hierarchy issues.", issues[:5], issue_lines[:5]

    return True, f"Found {len(headings)} headings with consistent hierarchy.", [], []


def _find_pattern_matches(
    content: str,
    lines: List[str],
    pattern: Pattern[str],
    max_matches: int = 5
) -> Tuple[List[str], List[int]]:
    """Find pattern matches and return evidence with line numbers."""
    evidence: List[str] = []
    line_numbers: List[int] = []

    for i, line in enumerate(lines):
        if pattern.search(line):
            # Truncate long lines
            display = line.strip()[:80]
            if len(line.strip()) > 80:
                display += "..."
            evidence.append(display)
            line_numbers.append(i + 1)
            if len(evidence) >= max_matches:
                break

    return evidence, line_numbers


def run_checks(content: str, lines: List[str]) -> List[CheckResult]:
    """Run all readiness checks against the document."""
    results: List[CheckResult] = []

    # Required checks (blockers)
    for check_id, name, pattern, fail_msg, fix_hint in REQUIRED_CHECKS:
        matches = pattern.findall(content)
        evidence, line_nums = _find_pattern_matches(content, lines, pattern)

        if matches:
            results.append(CheckResult(
                check_id=check_id,
                name=name,
                severity=Severity.BLOCKER,
                passed=True,
                message=f"Found {len(matches)} match(es).",
                evidence=evidence,
                line_numbers=line_nums,
            ))
        else:
            results.append(CheckResult(
                check_id=check_id,
                name=name,
                severity=Severity.BLOCKER,
                passed=False,
                message=f"{fail_msg} {fix_hint}",
                evidence=[],
                line_numbers=[],
            ))

    # Quality checks (warnings)
    for check_id, name, pattern, fail_msg, fix_hint in QUALITY_CHECKS:
        matches = pattern.findall(content)
        evidence, line_nums = _find_pattern_matches(content, lines, pattern)

        if matches:
            results.append(CheckResult(
                check_id=check_id,
                name=name,
                severity=Severity.WARNING,
                passed=True,
                message=f"Found {len(matches)} match(es).",
                evidence=evidence,
                line_numbers=line_nums,
            ))
        else:
            results.append(CheckResult(
                check_id=check_id,
                name=name,
                severity=Severity.WARNING,
                passed=False,
                message=f"{fail_msg} {fix_hint}",
                evidence=[],
                line_numbers=[],
            ))

    # Anti-pattern checks (warnings when FOUND)
    for check_id, name, pattern, found_msg, fix_hint in ANTI_PATTERN_CHECKS:
        matches = pattern.findall(content)
        evidence, line_nums = _find_pattern_matches(content, lines, pattern)

        if matches:
            results.append(CheckResult(
                check_id=check_id,
                name=name,
                severity=Severity.WARNING,
                passed=False,  # Anti-patterns are bad when found
                message=f"{found_msg} Found {len(matches)} instance(s). {fix_hint}",
                evidence=evidence,
                line_numbers=line_nums,
            ))
        else:
            results.append(CheckResult(
                check_id=check_id,
                name=name,
                severity=Severity.WARNING,
                passed=True,
                message="No instances found.",
                evidence=[],
                line_numbers=[],
            ))

    # Structural checks (info)
    for check_id, name, check_func, fix_hint in STRUCTURE_CHECKS:
        passed, message, evidence, line_nums = check_func(content, lines)
        results.append(CheckResult(
            check_id=check_id,
            name=name,
            severity=Severity.INFO,
            passed=passed,
            message=f"{message} {fix_hint}" if not passed else message,
            evidence=evidence,
            line_numbers=line_nums,
        ))

    return results


def generate_report(file_path: str, checks: List[CheckResult]) -> ReadinessReport:
    """Generate a complete readiness report from check results."""
    blocker_count = sum(1 for c in checks if c.severity == Severity.BLOCKER and not c.passed)
    warning_count = sum(1 for c in checks if c.severity == Severity.WARNING and not c.passed)
    info_count = sum(1 for c in checks if c.severity == Severity.INFO and not c.passed)

    return ReadinessReport(
        file_path=file_path,
        ready=blocker_count == 0,
        blocker_count=blocker_count,
        warning_count=warning_count,
        info_count=info_count,
        checks=checks,
    )


def format_human_output(report: ReadinessReport, verbose: bool = False) -> str:
    """Format report for human-readable output."""
    lines: List[str] = []

    # Header
    lines.append(f"{'=' * 70}")
    lines.append(f"PROSE READINESS CHECK: {report.file_path}")
    lines.append(f"{'=' * 70}")
    lines.append("")

    # Summary
    status = "READY" if report.ready else "NOT READY"
    status_icon = "✅" if report.ready else "❌"
    lines.append(f"Status: {status_icon} {status}")
    lines.append(f"  Blockers: {report.blocker_count}")
    lines.append(f"  Warnings: {report.warning_count}")
    lines.append(f"  Info:     {report.info_count}")
    lines.append("")

    # Group checks by severity
    blockers = [c for c in report.checks if c.severity == Severity.BLOCKER]
    warnings = [c for c in report.checks if c.severity == Severity.WARNING]
    infos = [c for c in report.checks if c.severity == Severity.INFO]

    # Blockers section
    if blockers:
        lines.append(f"{'-' * 70}")
        lines.append("REQUIRED STRUCTURE (blockers if missing)")
        lines.append(f"{'-' * 70}")
        for check in blockers:
            icon = "✅" if check.passed else "❌"
            lines.append(f"  [{check.check_id}] {icon} {check.name}")
            if not check.passed or verbose:
                lines.append(f"           {check.message}")
            if check.evidence and (verbose or not check.passed):
                for ev in check.evidence[:3]:
                    lines.append(f"           → {ev}")
        lines.append("")

    # Warnings section
    if warnings:
        lines.append(f"{'-' * 70}")
        lines.append("QUALITY SIGNALS (warnings)")
        lines.append(f"{'-' * 70}")
        for check in warnings:
            icon = "✅" if check.passed else "⚠️"
            lines.append(f"  [{check.check_id}] {icon} {check.name}")
            if not check.passed or verbose:
                lines.append(f"           {check.message}")
            if check.evidence and (verbose or not check.passed):
                for ev in check.evidence[:3]:
                    lines.append(f"           → {ev}")
        lines.append("")

    # Info section (only if verbose or failures)
    info_failures = [c for c in infos if not c.passed]
    if verbose or info_failures:
        lines.append(f"{'-' * 70}")
        lines.append("STRUCTURAL QUALITY (info)")
        lines.append(f"{'-' * 70}")
        for check in infos:
            if verbose or not check.passed:
                icon = "✅" if check.passed else "ℹ️"
                lines.append(f"  [{check.check_id}] {icon} {check.name}")
                lines.append(f"           {check.message}")
                if check.evidence:
                    for ev in check.evidence[:3]:
                        lines.append(f"           → {ev}")
        lines.append("")

    # Recommendation
    lines.append(f"{'=' * 70}")
    if report.ready and report.warning_count == 0:
        lines.append("RECOMMENDATION: Proceed with AI Task List conversion.")
    elif report.ready:
        lines.append("RECOMMENDATION: Proceed with caution. Address warnings for better output.")
    else:
        lines.append("RECOMMENDATION: Do NOT proceed. Resolve blockers first.")
        lines.append("")
        lines.append("Required actions:")
        for check in blockers:
            if not check.passed:
                lines.append(f"  - {check.check_id}: {check.name}")
    lines.append(f"{'=' * 70}")

    return "\n".join(lines)


def format_json_output(report: ReadinessReport) -> str:
    """Format report as JSON."""
    return json.dumps({
        "file": report.file_path,
        "ready": report.ready,
        "blocker_count": report.blocker_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
        "checks": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "severity": c.severity.value,
                "passed": c.passed,
                "message": c.message,
                "evidence": c.evidence,
                "line_numbers": c.line_numbers,
            }
            for c in report.checks
        ],
    }, indent=2)


def main(argv: List[str]) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="prose_readiness_check.py",
        description="Pre-flight validation for prose documents before AI Task List conversion.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  Ready (all checks pass)
  1  Warnings (quality issues but conversion possible)
  2  Blockers (missing required structure)
  3  Usage/file error

Examples:
  uv run python tools/prose_readiness_check.py DESIGN.md
  uv run python tools/prose_readiness_check.py --json DESIGN.md
  uv run python tools/prose_readiness_check.py --strict DESIGN.md
  uv run python tools/prose_readiness_check.py --verbose DESIGN.md
""",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {TOOL_VERSION}")
    parser.add_argument("path", help="Path to prose document to check")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as blockers (exit 2)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all checks, not just failures")
    args = parser.parse_args(argv)

    # Read file
    file_path = Path(args.path)
    if not file_path.exists():
        if args.json:
            print(json.dumps({"error": f"File not found: {file_path}", "ready": False}))
        else:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 3

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e), "ready": False}))
        else:
            print(f"Error reading file: {e}", file=sys.stderr)
        return 3

    # Run checks
    checks = run_checks(content, lines)
    report = generate_report(str(file_path), checks)

    # Output
    if args.json:
        print(format_json_output(report))
    else:
        print(format_human_output(report, verbose=args.verbose))

    # Exit code
    if args.strict and (report.blocker_count > 0 or report.warning_count > 0):
        return 2 if report.blocker_count > 0 else 1

    return report.exit_code(strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
