"""Utilities for working with prose refactor briefs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Union

__all__ = ["get_template", "check_against_template", "main"]

_CODE_BLOCK_RE = re.compile(r"```\s*([a-z0-9_-]*)\n([\s\S]*?)\n```", re.IGNORECASE)
_STEP_BLOCK_RE = re.compile(r"(?im)^###\s.*?(?=^###|\Z)", re.DOTALL)
_PHASE_BLOCK_RE = re.compile(r"(?im)^##\s*phase\s*(\d+).*?(?=^##\s*phase\s*\d+|\Z)", re.DOTALL)
_ALLOWED_LANGS = {"bash", "sh", "shell", "python", "py", "ps1", "powershell"}


def get_template() -> str:
    """Return the canonical Markdown template for authoring refactor briefs."""
    return dedent(
        """\
        # <Project or Component> — Refactor Brief

        ## Context
        - Why this refactor is needed.
        - Constraints (performance, deadlines, technical debt, dependencies).

        ## Goals / Non-Goals
        - **Goals**
          - Goal 1 …
          - Goal 2 …
        - **Non-Goals**
          - Not in scope …

        ## Risks & Mitigations
        - Risk: …
        - Mitigation: …

        ## Phase 0 — <Title>
        **Time estimate:** 0.5 d
        **Success criteria:**
        - <measurable result>
        - <measurable result>

        ### Step 1: <Imperative verb + noun>
        Rationale: <why this step is needed>
        Expected artifacts: <files or modules affected>

        ```bash
        # example commands or invocations
        python -m package.module --flag
        ```
        Verify: <clear acceptance statement starting with “verify/ensure/assert”>

        ## Phase 1 — <Title>
        **Time estimate:** 1 d
        **Success criteria:**
        - …

        ### Step 1: …
        Rationale: …
        Expected artifacts: …

        ```bash
        # example commands or invocations
        ```
        Verify: …

        ---
        **Author:** TBD_NAME
        **Last updated:** TBD_UTC
        **Review checklist:**
        - [ ] Steps use imperative verbs
        - [ ] Each phase has measurable success criteria
        - [ ] Commands are fenced in ```bash```/```python``` blocks
        - [ ] At least one “Verify:” line per step
        - [ ] No confidential info or credentials
        """
    )


def check_against_template(prose: str) -> Dict[str, Union[bool, List[str], str]]:
    """Check a prose refactor brief against the expected structural template."""

    errors: List[str] = []
    warnings: List[str] = []
    text = prose or ""

    required_sections = [
        r"(?im)^#\s+.+refactor\s+brief",
        r"(?im)^##\s*context",
        r"(?im)^##\s*goals\s*/\s*non-goals",
        r"(?im)^##\s*risks\s*&\s*mitigations",
        r"(?im)^##\s*phase\s*0",
    ]
    for pattern in required_sections:
        if not re.search(pattern, text):
            errors.append(f"Missing section matching: {pattern}")

    step_matches = list(re.finditer(r"(?im)^###\s*step\s*\d+", text))
    if not step_matches:
        errors.append("No '### Step N:' headings found.")

    for index, block in enumerate(_STEP_BLOCK_RE.findall(text), start=1):
        if not re.search(r"(?im)^\s*(verify|ensure|assert)[:\s]", block):
            warnings.append(f"Step {index} missing an explicit Verify/Ensure/Assert line.")

    code_blocks = list(_CODE_BLOCK_RE.finditer(text))
    if not code_blocks:
        warnings.append("No fenced code blocks found.")
    else:
        has_allowed = any(
            (match.group(1) or "").lower() in _ALLOWED_LANGS or not match.group(1)
            for match in code_blocks
        )
        if not has_allowed:
            warnings.append(
                "Code blocks do not use an approved language fence (bash/sh/python/ps1)."
            )

    phase_matches = list(_PHASE_BLOCK_RE.finditer(text))
    if not phase_matches:
        errors.append("No '## Phase N' sections found.")
    else:
        for match in phase_matches:
            phase_block = match.group(0)
            phase_number = match.group(1)
            if not re.search(r"(?im)\*\*\s*Time\s+estimate\s*:", phase_block):
                errors.append(f"Phase {phase_number} missing 'Time estimate:' line.")
            if not re.search(r"(?im)\*\*\s*Success\s+criteria\s*:", phase_block):
                errors.append(f"Phase {phase_number} missing 'Success criteria:' section.")

    grade = "fail" if errors else ("warn" if warnings else "ok")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "grade": grade}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or validate prose templates")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("new", help="Print the canonical refactor brief template")

    check_parser = subparsers.add_parser("check", help="Validate a prose file against the template")
    check_parser.add_argument("file", help="Path to the prose markdown file to validate")

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "new":
        sys.stdout.write(get_template())
        return 0

    if args.command == "check":
        path = Path(args.file)
        try:
            prose = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            parser.error(f"File not found: {path}")
        report = check_against_template(prose)
        grade = report["grade"]
        if grade == "ok":
            print("✅ OK")
            return 0
        if grade == "warn":
            print("⚠️  Warnings detected:")
            for warning in report["warnings"]:
                print(f"- {warning}")
            return 0
        print("❌ Issues detected:")
        for error in report["errors"]:
            print(f"- {error}")
        for warning in report.get("warnings", []):
            print(f"- {warning}")
        return 1

    parser.print_help()
    return 1
