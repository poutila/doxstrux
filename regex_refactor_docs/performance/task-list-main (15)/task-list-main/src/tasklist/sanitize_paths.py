#!/usr/bin/env python3
"""Utilities to validate artifact and output paths in task definitions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_NAME = "DETAILED_TASK_LIST_template.json"

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


def _resolve_json_path(root: Path | None, json_path: str | None) -> Path:
    base = root or Path.cwd()
    if json_path:
        candidate = Path(json_path)
        if not candidate.is_absolute():
            candidate = (base / candidate).resolve()
        return candidate
    return (base / DEFAULT_JSON_NAME).resolve()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tasklist-sanitize",
        description="Validate file/input/output paths in a rendered task list JSON file.",
    )
    parser.add_argument("--root", help="Repository root containing the rendered artifacts")
    parser.add_argument(
        "--json",
        help=f"Path to the rendered JSON (default: {DEFAULT_JSON_NAME} relative to --root)",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve() if args.root else None
    json_path = _resolve_json_path(root, args.json)

    data = _load_rendered_json(json_path)
    errors: list[str] = []
    errors.extend(validate_artifact_paths(data))
    errors.extend(validate_task_file_paths(data))
    errors.extend(validate_task_inputs(data))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("✅ All artifact, file, and input paths are safe")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
