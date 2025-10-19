#!/usr/bin/env python3
"""Validate task and gate identifiers in the rendered task list."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_NAME = "DETAILED_TASK_LIST_template.json"


def _iter_tasks(data: dict) -> Iterable[dict]:
    """Yield every task dictionary defined in the rendered data."""
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


def _iter_gates(data: dict) -> Iterable[dict]:
    """Yield each CI gate dictionary from the rendered data."""
    gates = data.get("ci_gates")
    if isinstance(gates, list):
        for gate in gates:
            if isinstance(gate, dict):
                yield gate
    elif isinstance(gates, dict):
        for gate in gates.values():
            if isinstance(gate, dict):
                yield gate


def _task_sort_key(task_id: str) -> list[int] | None:
    """Return a sortable key for dotted numeric identifiers."""
    if not task_id or not all(part.isdigit() for part in task_id.split(".")):
        return None
    return [int(part) for part in task_id.split(".")]


def validate_task_ids(data: dict) -> list[str]:
    """Ensure task identifiers are unique and, when numeric, sorted."""
    errors: list[str] = []
    task_ids: list[str] = []

    for task in _iter_tasks(data):
        task_id = task.get("id")
        if not task_id:
            task_name = task.get("name", "<unnamed>")
            errors.append(f"❌ Task missing id (name: {task_name})")
            continue
        task_ids.append(str(task_id))

    if not task_ids:
        return errors

    duplicates = [item for item, count in Counter(task_ids).items() if count > 1]
    if duplicates:
        errors.append(f"❌ Duplicate task IDs detected: {sorted(duplicates)}")

    sortable_ids = [(tid, _task_sort_key(tid)) for tid in task_ids]
    if all(key is not None for _, key in sortable_ids):
        sorted_ids = [tid for tid, _ in sorted(sortable_ids, key=lambda pair: pair[1])]
        if task_ids != sorted_ids:
            errors.append("❌ Task IDs are not in ascending order")
            errors.append(f"   Expected order: {sorted_ids}")
            errors.append(f"   Current order:  {task_ids}")

    return errors


def validate_gate_ids(data: dict) -> list[str]:
    """Ensure gate identifiers are unique and increment sequentially."""
    errors: list[str] = []
    gate_ids: list[str] = []

    for gate in _iter_gates(data):
        gate_id = gate.get("id")
        if not gate_id:
            gate_name = gate.get("name", "<unnamed>")
            errors.append(f"❌ Gate missing id (name: {gate_name})")
            continue
        gate_ids.append(str(gate_id))

    if not gate_ids:
        return errors

    duplicates = [item for item, count in Counter(gate_ids).items() if count > 1]
    if duplicates:
        errors.append(f"❌ Duplicate gate IDs detected: {sorted(duplicates)}")

    numeric_ids: list[int] = []
    for gid in gate_ids:
        if gid.startswith("G") and gid[1:].isdigit():
            numeric_ids.append(int(gid[1:]))
        else:
            errors.append(f"❌ Gate ID '{gid}' does not follow the 'G<number>' pattern")

    if numeric_ids and numeric_ids != sorted(numeric_ids):
        errors.append(f"❌ Gate IDs not in ascending order: {gate_ids}")

    return errors


def validate_acceptance_criteria(data: dict) -> list[str]:
    """Ensure every task declares non-empty acceptance criteria."""

    errors: list[str] = []

    for task in _iter_tasks(data):
        task_id = task.get("id", "unknown")
        criteria = task.get("acceptance_criteria")

        if not isinstance(criteria, list) or not criteria:
            errors.append(
                f"❌ Task {task_id} must define at least one acceptance criterion"
            )
            continue

        for index, criterion in enumerate(criteria, start=1):
            if not isinstance(criterion, str) or not criterion.strip():
                errors.append(
                    f"❌ Task {task_id} acceptance criterion {index} must be a non-empty string"
                )
                continue
            if "{{" in criterion or "}}" in criterion:
                errors.append(
                    f"❌ Task {task_id} acceptance criterion {index} contains a placeholder: {criterion}"
                )

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
        prog="tasklist-validate",
        description="Validate task and gate identifiers in a rendered task list JSON file.",
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
    errors.extend(validate_task_ids(data))
    errors.extend(validate_gate_ids(data))
    errors.extend(validate_acceptance_criteria(data))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("✅ All task, gate, and acceptance criteria validations passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
