#!/usr/bin/env python3
"""Validate that task command sequences do not contain dangerous patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_NAME = "DETAILED_TASK_LIST_template.json"

DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r"\brm\s+-rf\b", "rm -rf detected"),
    (r"\bsudo\b", "sudo usage detected"),
    (r"curl\s+[^|]+\|\s*(sh|bash)", "curl | sh detected"),
    (r"\bdd\s+if=", "dd command detected"),
    (r":\(\)\s*\{", "fork bomb pattern detected"),
    (r">\s*/dev/sd[a-z]", "direct disk write detected"),
    (r"\bchmod\s+777\b", "chmod 777 detected"),
    (r"eval\s+\$\(", "eval with command substitution"),
    (r";\s*rm\s+", "command chaining with rm"),
]

DENYLIST = [
    "rm -rf",
    "sudo",
    ":(){:|:&;}",
    ":(){:|:&};:",
    "dd if=",
    "mkfs",
    "shutdown",
]

ALLOWED_PREFIXES = [
    "python",
    "python3",
    "pytest",
    ".venv/bin/python",
    "git",
    "npm",
    "pip",
    "bash -c",
    "mkdir",
    "cp",
    "mv",
    "echo",
    "cat",
    "jq",
    "grep",
    "find",
    "ls",
    "cd",
]


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


def _iter_commands(task: dict) -> Iterable[str]:
    sequences = []
    cmd_seq = task.get("command_sequence")
    if isinstance(cmd_seq, list):
        sequences.extend(cmd_seq)

    commands = task.get("commands")
    if isinstance(commands, list):
        sequences.extend(commands)

    for cmd in sequences:
        if isinstance(cmd, str):
            yield cmd


def is_command_safe(command: str) -> tuple[bool, str]:
    text = command.strip()

    lowered = text.lower()
    collapsed = lowered.replace(" ", "")
    for snippet in DENYLIST:
        snippet_lower = snippet.lower()
        if snippet_lower in lowered or snippet_lower in collapsed:
            return False, f"unsafe command pattern: {snippet}"

    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, message

    if text and "{{" not in text and "}}" not in text:
        first_token = text.split()[0]
        if not any(first_token.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            return False, f"command not in whitelist: {first_token}"

    return True, ""


def validate_commands(data: dict) -> list[str]:
    errors: list[str] = []

    for task in _iter_tasks(data):
        if task.get("dangerous"):
            continue
        task_id = task.get("id", "unknown")
        for index, command in enumerate(_iter_commands(task), start=1):
            safe, reason = is_command_safe(command)
            if not safe:
                errors.append(f"❌ Task {task_id} command {index}: {reason}")
                errors.append(f"   Command: {command}")

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
        prog="tasklist-commands",
        description="Validate shell command safety in rendered task list JSON files.",
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
    errors = validate_commands(data)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print("\n⚠️  If these commands are intentional, add 'dangerous: true' to the task.", file=sys.stderr)
        return 1

    print("✅ All commands are safe")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
