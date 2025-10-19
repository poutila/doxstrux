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
    Path("results"),
]


def _validate_repo_relative(path_str: str) -> None:
    candidate = Path(path_str)

    if candidate.is_absolute():
        raise ValueError(f"Absolute paths not allowed: {path_str}")

    if ".." in candidate.parts:
        raise ValueError(f"Path traverses upward: {path_str}")

    if "\\" in path_str:
        raise ValueError(f"Backslashes are not permitted: {path_str}")

    normalized = candidate.as_posix()
    if normalized != path_str:
        raise ValueError(f"Path must use normalized POSIX form: {path_str}")


def sanitize_artifact_path(path_str: str) -> Path:
    """Validate a relative path stays within the approved roots."""
    try:
        candidate = Path(path_str)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid path: {path_str}") from exc

    if "\\" in path_str:
        raise ValueError(f"Backslashes are not permitted in artifact paths: {path_str}")

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


def _extract_path_values(raw_value) -> list[str]:
    """Normalize task path fields into a flat list of path strings."""

    if raw_value is None:
        return []

    if isinstance(raw_value, str):
        candidates: list[str] = []
        for chunk in raw_value.replace("\r", "").splitlines():
            candidates.extend(part.strip() for part in chunk.split(","))
        return [candidate for candidate in candidates if candidate]

    if isinstance(raw_value, list):
        paths: list[str] = []
        for item in raw_value:
            if isinstance(item, str):
                paths.extend(_extract_path_values(item))
            else:
                raise ValueError(f"Non-string path entry: {item!r}")
        return paths

    raise ValueError(f"Unsupported path container: {type(raw_value).__name__}")


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


def validate_task_file_paths(data: dict) -> list[str]:
    """Ensure task ``files`` entries stay within the repository sandbox."""

    errors: list[str] = []

    for task in _iter_tasks(data):
        task_id = task.get("id", "unknown")
        files_value = task.get("files")
        if files_value is None:
            continue

        try:
            file_paths = _extract_path_values(files_value)
        except ValueError as exc:
            errors.append(f"❌ Task {task_id} invalid files specification: {exc}")
            continue

        for file_path in file_paths:
            if not file_path:
                errors.append(f"❌ Task {task_id} includes an empty file path entry")
                continue

            try:
                _validate_repo_relative(file_path)
            except ValueError as exc:
                errors.append(f"❌ Task {task_id} file path invalid: {exc}")

    return errors


def validate_task_inputs(data: dict) -> list[str]:
    """Ensure task ``inputs`` entries do not escape the repository sandbox."""

    errors: list[str] = []

    for task in _iter_tasks(data):
        task_id = task.get("id", "unknown")
        inputs_value = task.get("inputs")
        if inputs_value is None:
            continue

        try:
            input_paths = _extract_path_values(inputs_value)
        except ValueError as exc:
            errors.append(f"❌ Task {task_id} invalid inputs specification: {exc}")
            continue

        for input_path in input_paths:
            if not input_path:
                errors.append(f"❌ Task {task_id} includes an empty input path entry")
                continue

            try:
                _validate_repo_relative(input_path)
            except ValueError as exc:
                errors.append(f"❌ Task {task_id} input path invalid: {exc}")

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
