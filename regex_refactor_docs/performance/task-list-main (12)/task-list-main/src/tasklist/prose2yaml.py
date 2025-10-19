"""Convert prose refactor notes into a starter detailed task list YAML."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import yaml

_HEADING_RE = re.compile(r"^(#+)\s+(.*)$", re.MULTILINE)
_STEP_RE = re.compile(r"(?im)^\s*(?:step\s+\d+[:.)-]|\d+(?:\.\d+)*[.)-])\s+(.*)$")
_CODE_RE = re.compile(r"```(?:bash|sh|python)?\n([\s\S]*?)\n```", re.MULTILINE)
_CRITERIA_RE = re.compile(r"(?im)\b(verify|ensure|accept|must|assert)\b.+")


@dataclass
class Section:
    title: str
    level: int
    body: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _split_sections(markdown: str) -> List[Section]:
    """Split markdown into sections keyed by heading."""
    matches = list(_HEADING_RE.finditer(markdown))
    if not matches:
        return [Section(title="Refactor", level=1, body=markdown.strip())]

    sections: List[Section] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        sections.append(Section(title=match.group(2).strip(), level=len(match.group(1)), body=body))
    return sections


def _extract_lines(pattern: re.Pattern[str], text: str) -> list[str]:
    return [m.strip() for m in pattern.findall(text) if m.strip()]


def _build_task(section: Section, index: int) -> dict:
    """Build a schema-compliant task entry from a document section."""
    step_candidates = _extract_lines(_STEP_RE, section.body)
    commands = [cmd.strip() for cmd in _CODE_RE.findall(section.body)]
    acceptance = _extract_lines(_CRITERIA_RE, section.body)

    name = step_candidates[0] if step_candidates else section.title[:80] or f"Task {index}"

    steps: list[str] = []
    if step_candidates:
        steps.extend(step_candidates)
    if commands:
        for cmd in commands:
            for line in cmd.splitlines():
                line = line.strip()
                if line:
                    steps.append(f"Run: {line}")
    if not steps:
        steps.append(f"Review section: {section.title or 'Refactor notes'}")

    if not acceptance:
        acceptance = [f"Document updates for '{section.title or 'refactor'}' are complete."]

    return {
        "id": f"0.{index}",
        "name": name,
        "time_estimate": "TBD_TIME",
        "steps": steps,
        "acceptance_criteria": acceptance,
        "status": "⏳ Not started",
    }


def _build_phase_tasks(sections: Iterable[Section]) -> list[dict]:
    tasks: list[dict] = []
    for idx, section in enumerate(sections, start=1):
        task = _build_task(section, idx)
        tasks.append(task)
    if not tasks:
        tasks.append(
            {
                "id": "0.1",
                "name": "Review refactor document",
                "time_estimate": "TBD_TIME",
                "steps": ["Read the source document and outline actionable tasks."],
                "acceptance_criteria": ["Outline reviewed and converted into tasks."],
                "status": "⏳ Not started",
            }
        )
    return tasks


def _phase_template() -> dict:
    return {
        "phase_number": "TBD_PHASE_NUM",
        "name": "TBD_PHASE_NAME",
        "goal": "TBD_PHASE_GOAL",
        "time_estimate": "TBD_PHASE_TIME",
        "status": "⏳ Not started",
        "prerequisites": "Phase TBD_PREV_PHASE complete (.phase-TBD_PREV_PHASE.complete.json exists)",
        "tasks": [
            {
                "id": "TBD_TEMPLATE_TASK",
                "name": "Customize generated tasks",
                "time_estimate": "TBD_TIME",
                "steps": [
                    "Review auto-generated tasks for accuracy.",
                    "Fill in precise time estimates and file references.",
                ],
                "acceptance_criteria": [
                    "All generated tasks reviewed and edited for accuracy.",
                ],
                "status": "⏳ Not started",
            }
        ],
    }


def _default_phase(tasks: list[dict], phase_name: str, phase_goal: str) -> dict:
    return {
        "name": phase_name,
        "goal": phase_goal,
        "time_estimate": "TBD_PHASE_TIME",
        "status": "⏳ Not started",
        "tasks": tasks,
    }


def build_task_list(markdown: str, *, title: str, output_name: str) -> dict:
    sections = _split_sections(markdown)
    tasks = _build_phase_tasks(sections)

    created = _utc_now()

    return {
        "schema_version": "2.0.0",
        "document": {
            "id": f"{title.lower().replace(' ', '-')}-plan",
            "title": title,
            "version": "1.0.0",
            "created": created,
            "owner": "TBD_OWNER",
            "audience": ["engineering", "ai_agents"],
        },
        "metadata": {
            "project_full_name": title,
            "project_goal": f"Execute '{title}' refactor plan.",
            "status": "Draft",
            "total_estimated_time": "TBD_TOTAL_TIME",
            "total_phases": "1",
            "schema_version": "2.0.0",
        },
        "success_criteria": [
            "Detailed task list renders without schema violations.",
            "CI gates execute successfully on generated plan.",
        ],
        "ci_gates": [
            {
                "id": "G1",
                "name": "Render & schema validation",
                "command": "tasklist-render --strict",
            }
        ],
        "phases": {
            "phase_template": _phase_template(),
            "phase_0": _default_phase(tasks, "Bootstrap from prose", "Convert prose refactor brief into executable plan."),
        },
        "render_meta": {
            "source_file": output_name,
            "schema_version": "2.0.0",
            "sha256_of_yaml": "TBD_SHA256",
            "rendered_utc": "TBD_RENDERED_UTC",
        },
    }


def _derive_title(sections: Iterable[Section], fallback: str) -> str:
    first = next(iter(sections), None)
    if first and first.level == 1:
        return first.title
    return fallback


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tasklist-prose2yaml",
        description="Convert prose refactor notes into a schema-valid detailed task list YAML file.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="docs/DOXSTRUX_REFACTOR.md",
        help="Path to the prose refactor document (Markdown).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="DETAILED_TASK_LIST_generated.yaml",
        help="Where to write the generated YAML (default: DETAILED_TASK_LIST_generated.yaml).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"ERROR: source document not found: {source_path}", file=sys.stderr)
        return 2

    markdown = source_path.read_text(encoding="utf-8")
    sections = _split_sections(markdown)
    title = _derive_title(sections, source_path.stem)
    data = build_task_list(markdown, title=title, output_name=Path(args.output).name)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(data, sort_keys=False, width=100), encoding="utf-8")
    print(f"Wrote task list YAML to {output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
