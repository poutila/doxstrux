#!/usr/bin/env python3
"""Utilities to validate artifact and output paths in task definitions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "DETAILED_TASK_LIST_template.json"

ALLOWED_ROOTS = [
    Path("evidence"),
    Path("baselines"),
    Path("adversarial_corpora"),
    Path("prometheus"),
    Path("grafana"),
]


def sanitize_artifact_path(path_str: str) -> Path:
    """Validate a relative path stays within the approved roots."""
    try:
        candidate = Path(path_str)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid path: {path_str}") from exc

    if candidate.is_absolute():
        raise ValueError(f"Absolute paths not allowed: {path_str}")

    if ".." in candidate.parts:
        raise ValueError(f"Path traversal detected (..): {path_str}")

    if not candidate.parts:
        raise ValueError("Empty artifact path")

    if candidate.parts[0] not in {root.parts[0] for root in ALLOWED_ROOTS}:
        allowed = ", ".join(sorted(str(root) for root in ALLOWED_ROOTS))
        raise ValueError(
            "Path outside allowed roots: "
            f"{path_str}\nAllowed roots: {allowed}"
        )

    return candidate


def _iter_tasks(data: dict) -> Iterable[dict]:
    tasks = data.get("tasks")
    if isinstance(tasks, list):
        for task in tasks:
            if isinstance(task, dict):
                yield task

    phases = data.get("phases")
    if isinstance(phases, dict):
        for phase in phases.values():
            if isinstance(phase, dict):
                for task in phase.get("tasks", []) or []:
                    if isinstance(task, dict):
                        yield task

    phase_template = data.get("phase_template")
    if isinstance(phase_template, dict):
        for task in phase_template.get("tasks", []) or []:
            if isinstance(task, dict):
                yield task


def validate_artifact_paths(data: dict) -> list[str]:
    errors: list[str] = []

    for task in _iter_tasks(data):
        task_id = task.get("id", "unknown")
        outputs = task.get("outputs", [])
        if not isinstance(outputs, list):
            continue
        for output_path in outputs:
            if not isinstance(output_path, str):
                errors.append(f"❌ Task {task_id} has non-string output path: {output_path}")
                continue
            try:
                sanitize_artifact_path(output_path)
            except ValueError as exc:
                errors.append(f"❌ Task {task_id} invalid output path: {exc}")

    return errors


def _load_rendered_json(path: Path) -> dict:
    if not path.exists():
        print(f"❌ File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    data = _load_rendered_json(JSON_PATH)
    errors = validate_artifact_paths(data)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)

    print("✅ All artifact paths are safe")


if __name__ == "__main__":
    main()
