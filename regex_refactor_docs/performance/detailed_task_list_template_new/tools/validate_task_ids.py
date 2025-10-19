#!/usr/bin/env python3
"""Validate task and gate identifiers in the rendered task list."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "DETAILED_TASK_LIST_template.json"


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


def _load_rendered_json(path: Path) -> dict:
    if not path.exists():
        print(f"❌ File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    data = _load_rendered_json(JSON_PATH)
    errors: list[str] = []
    errors.extend(validate_task_ids(data))
    errors.extend(validate_gate_ids(data))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)

    print("✅ All task and gate IDs are unique and properly ordered")


if __name__ == "__main__":
    main()
