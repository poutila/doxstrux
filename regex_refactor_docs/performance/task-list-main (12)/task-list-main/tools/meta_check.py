#!/usr/bin/env python3
"""meta_check.py — one command to validate your task-list repo/package.

Checks:
  1) Schema ↔ JSON v2 root keys
  2) Packaged schema availability (importlib.resources)
  3) Strict render + drift gate (re-renders, diffs)
  4) Placeholder policy ({{...}} always banned; TBD_ banned in --release)
  5) Task IDs unique + numeric-monotone
  6) Gate IDs monotone (G1, G2, ...)
  7) Path safety (repo-relative POSIX; no '..', no backslashes, no absolute)
  8) Command deny-list
  9) Newline-normalized YAML SHA matches render_meta.sha256_of_yaml
 10) Phase-complete artifacts validate against schema (if present)
 11) CLI entry points expose main()

Exit code is non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover - hard failure path
    print("❌ PyYAML not installed. `pip install pyyaml`", file=sys.stderr)
    raise

try:
    from jsonschema import Draft202012Validator
except Exception as exc:  # pragma: no cover - hard failure path
    print("❌ jsonschema not installed. `pip install jsonschema`", file=sys.stderr)
    raise


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def lf_bytes(path: Path) -> bytes:
    """Read file and normalize newlines to LF for SHA comparisons."""

    data = path.read_bytes()
    return data.replace(b"\r\n", b"\n")


def sha256_of_file_lf(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(lf_bytes(path))
    return digest.hexdigest()


def numkey(identifier: str) -> List[int]:
    return [int(part) for part in identifier.split(".") if part.isdigit()]


def is_posix_relative_safe(value: str) -> bool:
    if not value:
        return True
    if value.startswith("/") or re.match(r"^[A-Za-z]:[\\/\\\\]", value):
        return False
    if "\\" in value:
        return False
    parts = value.split("/")
    return ".." not in parts


DENY_CMDS = [
    "rm -rf",
    "sudo ",
    ":(){:|:&};:",
    "mkfs ",
    "shutdown",
    "dd if=",
    "nc -l",
    "openssl enc -in",
    "curl http://",
    "wget http://",
]


# ------------------------------------------------------------
# Checks
# ------------------------------------------------------------


@dataclass
class Ctx:
    repo_root: Path
    yaml_path: Path
    json_path: Path
    md_path: Path
    renderer_cmd: str
    release: bool


def ensure_packaged_schema() -> Tuple[bool, str, Any]:
    try:
        from importlib import resources

        schema_file = resources.files("tasklist.schemas").joinpath(
            "detailed_task_list.schema.json"
        )
        if not schema_file.is_file():
            return (
                False,
                "Packaged schema not found at tasklist/schemas/"
                "detailed_task_list.schema.json",
                None,
            )
        with schema_file.open("rb") as handle:
            schema = json.load(handle)
        return True, "Packaged schema located.", schema
    except Exception as exc:
        return False, f"Cannot import packaged schema via importlib.resources: {exc}", None


def check_schema_vs_json(schema: dict, data: dict) -> Tuple[bool, List[str]]:
    errors = [
        f"{error.message} @ {list(error.path)}"
        for error in Draft202012Validator(schema).iter_errors(data)
    ]
    return len(errors) == 0, errors


def run_renderer(ctx: Ctx) -> Tuple[bool, str]:
    command = f"{ctx.renderer_cmd} --source {shlex.quote(str(ctx.yaml_path))} --strict"
    try:
        subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=ctx.repo_root,
        )
        return True, f"Renderer ok: {command}"
    except subprocess.CalledProcessError as exc:
        return False, f"Renderer failed: {command}\nexit={exc.returncode}"


def drift_gate(ctx: Ctx) -> Tuple[bool, str]:
    try:
        subprocess.run(
            [
                "git",
                "diff",
                "--exit-code",
                str(ctx.json_path),
                str(ctx.md_path),
            ],
            cwd=ctx.repo_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True, "Drift gate ok (JSON/MD committed and in sync)."
    except subprocess.CalledProcessError:
        return False, "Rendered JSON/MD differ from working tree. Re-render and commit."


def placeholder_scan(ctx: Ctx) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    for path in (ctx.yaml_path, ctx.json_path, ctx.md_path):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "{{" in text:
            problems.append(f"Unresolved '{{{{...}}}}' in {path.name}")
        if ctx.release and re.search(r"\bTBD_[A-Z0-9_]+", text):
            problems.append(f"'TBD_' placeholders present in release mode: {path.name}")
    return len(problems) == 0, problems


def ids_and_gates(data: dict) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    phases = data.get("phases", {})
    for phase_name, phase_body in phases.items():
        tasks = phase_body.get("tasks", [])
        identifiers = [task.get("id", "") for task in tasks]
        if len(identifiers) != len(set(identifiers)):
            problems.append(f"{phase_name}: duplicate task ids")
        try:
            sorted_ids = sorted(identifiers, key=numkey)
        except ValueError:
            problems.append(f"{phase_name}: non-numeric task id detected")
            sorted_ids = identifiers
        if identifiers != sorted_ids:
            problems.append(f"{phase_name}: task ids not numeric-monotone")
    gates = data.get("ci_gates", [])
    gate_ids = [gate.get("id", "") for gate in gates]
    if any(not re.match(r"^G[1-9]\d*$", gate or "") for gate in gate_ids):
        problems.append("Gate id pattern violation (expected ^G[1-9]\\d*$).")
    try:
        gate_numbers = [int(gate[1:]) for gate in gate_ids]
        if gate_numbers != sorted(gate_numbers):
            problems.append("Gate ids not monotone ascending.")
    except Exception:
        problems.append("Gate ids not parseable as integers.")
    return len(problems) == 0, problems


def path_and_commands(data: dict) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    for phase_name, phase_body in data.get("phases", {}).items():
        for task in phase_body.get("tasks", []):
            task_id = task.get("id", "<?>")
            for key in ("files", "inputs", "outputs"):
                for value in task.get(key, []) or []:
                    if not is_posix_relative_safe(value):
                        problems.append(f"{task_id}: unsafe {key[:-1]} path '{value}'")
            for command in task.get("command_sequence", []) or []:
                if any(denied in command for denied in DENY_CMDS):
                    problems.append(f"{task_id}: unsafe command '{command}'")
    return len(problems) == 0, problems


def sha_gate(ctx: Ctx, data: dict) -> Tuple[bool, str]:
    meta = data.get("render_meta", {})
    expected = meta.get("sha256_of_yaml")
    if not expected:
        return False, "render_meta.sha256_of_yaml missing in JSON."
    actual = sha256_of_file_lf(ctx.yaml_path)
    if expected != actual:
        return False, f"render_meta SHA mismatch: json={expected} vs yaml={actual}"
    return True, "YAML SHA matches render_meta (LF-normalized)."


def phase_complete_validation(ctx: Ctx) -> Tuple[bool, List[str]]:
    try:
        from importlib import resources

        phase_schema_path = resources.files("tasklist.schemas").joinpath(
            "phase_complete.schema.json"
        )
        if not phase_schema_path.is_file():
            return True, []
        with phase_schema_path.open("rb") as handle:
            schema = json.load(handle)
    except Exception as exc:
        return False, [f"Cannot load phase_complete.schema.json: {exc}"]

    problems: List[str] = []
    for artifact in sorted(ctx.repo_root.glob(".phase-*.complete.json")):
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            issues = list(Draft202012Validator(schema).iter_errors(payload))
            if issues:
                messages = "; ".join(
                    f"{issue.message} @ {list(issue.path)}" for issue in issues
                )
                problems.append(f"{artifact.name}: {messages}")
        except Exception as exc:
            problems.append(f"{artifact.name}: unreadable or invalid JSON: {exc}")
    return len(problems) == 0, problems


def cli_entrypoints_check() -> Tuple[bool, List[str]]:
    problems: List[str] = []
    targets = [
        ("tasklist.render_task_templates", "main"),
        ("tasklist.prose2yaml", "main"),
        ("tasklist.prose_template", "main"),
    ]
    for module_name, attribute in targets:
        try:
            module = __import__(module_name, fromlist=["*"])
            if not hasattr(module, attribute):
                problems.append(f"{module_name} has no '{attribute}()'")
        except Exception as exc:
            problems.append(f"Cannot import {module_name}: {exc}")
    return len(problems) == 0, problems


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser("Run all task-list meta checks.")
    parser.add_argument(
        "--source",
        default="DETAILED_TASK_LIST_template.yaml",
        help="YAML source path",
    )
    parser.add_argument(
        "--json",
        default="DETAILED_TASK_LIST_template.json",
        help="Rendered JSON path",
    )
    parser.add_argument(
        "--md",
        default="DETAILED_TASK_LIST_template.md",
        help="Rendered Markdown path",
    )
    parser.add_argument(
        "--renderer-cmd",
        default="tasklist-render",
        help="Renderer CLI to invoke",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Fail on any 'TBD_' placeholders",
    )
    args = parser.parse_args(argv)

    ctx = Ctx(
        repo_root=Path.cwd(),
        yaml_path=Path(args.source),
        json_path=Path(args.json),
        md_path=Path(args.md),
        renderer_cmd=args.renderer_cmd,
        release=args.release,
    )

    failures: List[str] = []
    notes: List[str] = []

    for required in (ctx.yaml_path,):
        if not required.is_file():
            failures.append(f"Missing YAML source: {required}")
    if failures:
        print("❌ Pre-flight:", *failures, sep="\n  - ")
        return 2

    ok, message, schema = ensure_packaged_schema()
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)
    if not ok:
        print("\n".join(notes))
        print("\n".join(failures))
        return 2

    ok, message = run_renderer(ctx)
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)

    if ctx.json_path.is_file():
        data = json.loads(ctx.json_path.read_text(encoding="utf-8"))
    else:
        failures.append(f"Rendered JSON not found: {ctx.json_path}")
        print("\n".join(notes))
        print("\n".join(failures))
        return 2

    ok, errors = check_schema_vs_json(schema, data)
    (notes if ok else failures).append(
        "✅ Schema validation passed."
        if ok
        else "❌ Schema validation:\n  - " + "\n  - ".join(errors)
    )

    ok, message = drift_gate(ctx)
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)

    ok, problems = placeholder_scan(ctx)
    (notes if ok else failures).append(
        "✅ Placeholder policy ok."
        if ok
        else "❌ Placeholders:\n  - " + "\n  - ".join(problems)
    )

    ok, problems = ids_and_gates(data)
    (notes if ok else failures).append(
        "✅ IDs/gates ok."
        if ok
        else "❌ IDs/Gates:\n  - " + "\n  - ".join(problems)
    )

    ok, problems = path_and_commands(data)
    (notes if ok else failures).append(
        "✅ Paths/commands ok."
        if ok
        else "❌ Paths/Commands:\n  - " + "\n  - ".join(problems)
    )

    ok, message = sha_gate(ctx, data)
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)

    ok, problems = phase_complete_validation(ctx)
    (notes if ok else failures).append(
        "✅ Phase-complete artifacts ok."
        if ok
        else "❌ Phase-complete:\n  - " + "\n  - ".join(problems)
    )

    ok, problems = cli_entrypoints_check()
    (notes if ok else failures).append(
        "✅ CLI entry points ok."
        if ok
        else "❌ CLI entry points:\n  - " + "\n  - ".join(problems)
    )

    print("\n".join(notes))
    if failures:
        print("\n---\n❌ FAILURES:")
        print("\n".join(failures))
        return 1
    print("\n✅ All meta checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
