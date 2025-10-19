"""Utilities for working with prose refactor briefs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Union

__all__ = ["get_template", "check_against_template", "main"]


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


def check_against_template(prose: str) -> Dict[str, Union[bool, List[str]]]:
    """Check a prose refactor brief against the expected structural template."""

    errors: List[str] = []

    required_sections = [
        r"(?im)^#\s+.+refactor brief",
        r"(?im)^##\s*context",
        r"(?im)^##\s*goals\s*/\s*non-goals",
        r"(?im)^##\s*risks\s*&\s*mitigations",
        r"(?im)^##\s*phase\s*0",
    ]
    for pattern in required_sections:
        if not re.search(pattern, prose):
            errors.append(f"Missing section matching: {pattern}")

    if not re.search(r"(?im)^###\s*step\s*\d+", prose):
        errors.append("No '### Step N:' headings found.")

    step_pattern = re.compile(r"(?im)^###.*?(?=^###|\Z)", re.DOTALL)
    for index, block in enumerate(step_pattern.findall(prose), start=1):
        if not re.search(r"(?im)^\s*(verify|ensure|assert)[:\s]", block):
            errors.append(f"Step {index} missing a 'Verify:' line.")

    if not re.search(r"```(?:bash|sh|python|ps1)?\n[\s\S]+?\n```", prose):
        errors.append("No fenced code block (```bash/```sh/```python) found.")

    phase_pattern = re.compile(r"(?im)^##\s*phase\s*(\d+).*?(?=^##|\Z)", re.DOTALL)
    phase_matches = list(phase_pattern.finditer(prose))
    if not phase_matches:
        errors.append("No '## Phase N' sections found.")
    for match in phase_matches:
        phase_block = match.group(0)
        phase_number = match.group(1)
        if not re.search(r"(?im)\*\*\s*Time\s+estimate\s*:", phase_block):
            errors.append(f"Phase {phase_number} missing 'Time estimate:' line.")
        if not re.search(r"(?im)\*\*\s*Success\s+criteria\s*:", phase_block):
            errors.append(f"Phase {phase_number} missing 'Success criteria:' section.")

    return {"ok": not errors, "errors": errors}


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
        if report["ok"]:
            print("✅ OK")
            return 0
        print("❌ Issues detected:")
        for error in report["errors"]:
            print(f"- {error}")
        return 1

    parser.print_help()
    return 1
