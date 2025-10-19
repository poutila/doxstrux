#!/usr/bin/env python3
"""Render the detailed task list template into JSON and Markdown outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Iterable, Sequence

import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from tasklist.validate_commands import validate_commands
from tasklist.validate_task_ids import (
    validate_acceptance_criteria,
    validate_gate_ids,
    validate_task_ids,
)
from tasklist.sanitize_paths import (
    validate_artifact_paths,
    validate_task_file_paths,
    validate_task_inputs,
)

DEFAULT_SOURCE_NAME = "DETAILED_TASK_LIST_template.yaml"
DEFAULT_JSON_NAME = "DETAILED_TASK_LIST_template.json"
DEFAULT_MD_NAME = "DETAILED_TASK_LIST_template.md"
DEFAULT_HASH_DIR = Path("evidence") / "hashes"
PLACEHOLDER_PATTERN = re.compile(r"\{\{([^{}]+)\}\}")
TBD_PATTERN = re.compile(r"\bTBD_[A-Z0-9_]+\b")


@dataclass(frozen=True)
class PlaceholderIssue:
    """Represents an unresolved placeholder discovered during validation."""

    path: str
    value: str
    kind: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA256 hash of ``file_path`` with normalized newlines."""

    raw_bytes = file_path.read_bytes()
    normalized = raw_bytes.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def expand_placeholders(data: str, strict: bool = False) -> str:
    """Replace ``{{VAR}}`` placeholders with environment or .env values."""

    def repl(match: re.Match[str]) -> str:
        var = match.group(1).strip()
        val = os.getenv(var)
        if val is None and strict:
            raise ValueError(f"Unresolved placeholder: {{{{{var}}}}}")
        return val or match.group(0)

    return PLACEHOLDER_PATTERN.sub(repl, data)


def find_placeholders(data, *, allow_tbd: bool) -> list[PlaceholderIssue]:
    """Return unresolved placeholders present in the rendered data."""

    found: list[PlaceholderIssue] = []

    def _walk(node, path: tuple[str, ...]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                _walk(value, path + (str(key),))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                _walk(value, path + (str(index),))
        elif isinstance(node, str):
            if PLACEHOLDER_PATTERN.search(node):
                found.append(
                    PlaceholderIssue(path=".".join(path), value=node, kind="template"),
                )
            if not allow_tbd and TBD_PATTERN.search(node):
                found.append(
                    PlaceholderIssue(path=".".join(path), value=node, kind="tbd"),
                )

    _walk(data, ())
    return found


def load_env_file(root: Path) -> None:
    """Populate ``os.environ`` with values from ``root/.env`` if present."""
    env_path = root / ".env"
    if not env_path.exists():
        return

    with env_path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key, value)


def add_render_meta(
    data: dict,
    yaml_path: Path,
    root: Path | None,
    *,
    yaml_sha: str | None = None,
    existing_json: dict | None = None,
) -> dict:
    """Attach ``render_meta`` information to the rendered task list.

    When a previously rendered JSON artifact is supplied in ``existing_json`` and its
    stored YAML hash matches the freshly computed ``yaml_sha``, we reuse the prior
    render timestamps. This keeps re-renders idempotent and allows CI drift checks to
    run ``tasklist-render --strict`` followed by ``git diff --exit-code`` without
    observing timestamp-only changes.
    """

    meta = data.setdefault("render_meta", {})
    source_path: Path | str = yaml_path
    if root is not None:
        try:
            source_path = yaml_path.relative_to(root)
        except ValueError:
            source_path = yaml_path

    sha = yaml_sha or compute_sha256(yaml_path)

    previous_rendered: str | None = None
    previous_template_rendered: str | None = None
    if isinstance(existing_json, dict):
        prev_meta = existing_json.get("render_meta")
        if isinstance(prev_meta, dict) and prev_meta.get("sha256_of_yaml") == sha:
            previous_rendered = prev_meta.get("rendered_utc")
        prev_template_meta = existing_json.get("template_metadata")
        if isinstance(prev_template_meta, dict):
            previous_template_rendered = prev_template_meta.get("last_rendered_utc")

    rendered_utc = previous_rendered or _utc_now()

    meta.update(
        {
            "source_file": str(source_path),
            "schema_version": data.get("schema_version", "1.0.0"),
            "sha256_of_yaml": sha,
            "rendered_utc": rendered_utc,
        }
    )

    template_meta = data.setdefault("template_metadata", {})
    template_meta["last_rendered_utc"] = (
        previous_template_rendered
        if previous_rendered and previous_template_rendered
        else rendered_utc
    )

    return data


def yaml_to_json(
    yaml_path: Path,
    strict: bool,
    root: Path | None,
    *,
    yaml_sha: str | None = None,
    existing_json: dict | None = None,
) -> dict:
    """Load ``yaml_path`` and return the expanded Python dictionary."""
    raw_text = yaml_path.read_text(encoding="utf-8")
    expanded = expand_placeholders(raw_text, strict=strict)
    data = yaml.safe_load(expanded)

    metadata_block = data.get("metadata")
    if isinstance(metadata_block, dict):
        metadata_block.setdefault("schema_version", data.get("schema_version", "1.0.0"))

    return add_render_meta(
        data,
        yaml_path,
        root,
        yaml_sha=yaml_sha,
        existing_json=existing_json,
    )


def _task_sort_key(task: dict) -> tuple[int, tuple[int, ...] | str]:
    task_id = str(task.get("id", ""))
    numeric_parts: list[int] = []
    for part in task_id.split("."):
        if part.isdigit():
            numeric_parts.append(int(part))
        else:
            return (1, task_id)
    return (0, tuple(numeric_parts))


def _sort_tasks(tasks: Iterable[dict]) -> list[dict]:
    sortable = [task for task in tasks if isinstance(task, dict)]
    return sorted(sortable, key=_task_sort_key)


def sort_plan_structure(data: dict) -> dict:
    """Ensure deterministic ordering of gates, phases, and tasks."""

    ci_gates = data.get("ci_gates")
    if isinstance(ci_gates, list):
        data["ci_gates"] = sorted(
            [gate for gate in ci_gates if isinstance(gate, dict)],
            key=lambda gate: str(gate.get("id", "")),
        )

    phases = data.get("phases")
    if isinstance(phases, dict):
        sorted_phases: dict[str, dict] = {}
        for name, phase in sorted(
            phases.items(),
            key=lambda item: (
                int(re.search(r"(\d+)", item[0]).group(1))
                if re.search(r"(\d+)", item[0])
                else float("inf"),
                item[0],
            ),
        ):
            if isinstance(phase, dict):
                tasks = phase.get("tasks")
                if isinstance(tasks, list):
                    phase["tasks"] = _sort_tasks(tasks)
                sorted_phases[name] = phase
        data["phases"] = sorted_phases

    phase_template = data.get("phase_template")
    if isinstance(phase_template, dict):
        template_tasks = phase_template.get("tasks")
        if isinstance(template_tasks, list):
            phase_template["tasks"] = _sort_tasks(template_tasks)

    top_level_tasks = data.get("tasks")
    if isinstance(top_level_tasks, list):
        data["tasks"] = _sort_tasks(top_level_tasks)

    return data


def _schema_resource():
    return importlib_resources.files("tasklist.schemas").joinpath("detailed_task_list.schema.json")


def validate_json(data: dict) -> None:
    """Validate ``data`` against the packaged JSON schema."""
    with importlib_resources.as_file(_schema_resource()) as schema_path:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        validate(instance=data, schema=schema)
    except ValidationError as exc:  # pragma: no cover - exercised in CI
        sys.stderr.write(f"[ERROR] JSON schema validation failed:\n{exc}\n")
        sys.exit(1)


def render_markdown(data: dict) -> str:
    """Render a Markdown summary of the rendered task list."""
    lines: list[str] = []
    document = data.get("document", {})
    metadata = data.get("metadata", {})
    render_meta = data.get("render_meta", {})

    lines.append("---")
    lines.append(f"title: \"Detailed Task List - {document.get('title', 'Untitled')}\"")
    lines.append(f"version: \"{document.get('version', '1.0')}\"")
    lines.append(f"schema_version: \"{data.get('schema_version', '1.0.0')}\"")
    lines.append(f"document_id: \"{document.get('id', 'Unknown')}\"")
    lines.append(f"created: \"{document.get('created', 'Unknown')}\"")
    lines.append(f"owner: \"{document.get('owner', 'Unknown')}\"")
    lines.append("audience:")
    for member in document.get("audience", []):
        lines.append(f"  - {member}")
    lines.append("metadata:")
    lines.append(f"  project_full_name: \"{metadata.get('project_full_name', 'Unknown')}\"")
    lines.append(f"  status: \"{metadata.get('status', 'Unknown')}\"")
    lines.append(f"  total_phases: {metadata.get('total_phases', '0')}")
    lines.append(
        f"  schema_version: \"{metadata.get('schema_version', data.get('schema_version', '1.0.0'))}\""
    )
    lines.append("---")
    lines.append("")

    lines.append(f"# Detailed Task List — {document.get('title', 'Untitled')}")
    lines.append(f"Generated: {render_meta.get('rendered_utc', 'Unknown')}")
    lines.append("")

    project_goal = metadata.get("project_goal")
    if project_goal:
        lines.append("## Project Goal")
        lines.append(project_goal)
        lines.append("")

    for phase_name, phase in sorted(data.get("phases", {}).items()):
        if not isinstance(phase, dict):
            continue
        lines.append(f"## {phase_name}: {phase.get('name', 'Unnamed Phase')}")
        goal = phase.get("goal")
        if goal:
            lines.append(goal)
            lines.append("")
        tasks = phase.get("tasks", [])
        if tasks:
            lines.append("| ID | Name | Kind | Impact | Status | Acceptance Criteria |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                lines.append(
                    "| {id} | {name} | {kind} | {impact} | {status} | {criteria} |".format(
                        id=task.get("id", "?"),
                        name=task.get("name", "Unnamed"),
                        kind=task.get("kind", "?"),
                        impact=task.get("impact", "?"),
                        status=task.get("status", ""),
                        criteria=", ".join(task.get("acceptance_criteria", [])),
                    )
                )
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("**Render Metadata**:")
    lines.append(f"- Source: `{render_meta.get('source_file', 'Unknown')}`")
    lines.append(f"- Schema: `{render_meta.get('schema_version', 'Unknown')}`")
    lines.append(f"- YAML SHA256: `{render_meta.get('sha256_of_yaml', 'Unknown')}`")
    lines.append(f"- Rendered: `{render_meta.get('rendered_utc', 'Unknown')}`")
    lines.append("")
    lines.append("_End of auto-generated Markdown summary_")
    return "\n".join(lines)


def write_hashes(root: Path, yaml_path: Path, json_path: Path, md_path: Path) -> None:
    """Write SHA256 hashes to ``root/evidence/hashes``."""
    hash_dir = root / DEFAULT_HASH_DIR
    hash_dir.mkdir(parents=True, exist_ok=True)

    (hash_dir / "yaml_sha256.txt").write_text(compute_sha256(yaml_path))
    (hash_dir / "json_sha256.txt").write_text(compute_sha256(json_path))
    (hash_dir / "md_sha256.txt").write_text(compute_sha256(md_path))
    print(f"[OK] Hashes written → {hash_dir.relative_to(root)}")


def print_metadata(root: Path, yaml_path: Path, json_path: Path, md_path: Path) -> None:
    """Print metadata and hash information for the current task list."""
    existing_json: dict | None = None
    if json_path.exists():
        try:
            existing_json = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing_json = None

    yaml_sha = compute_sha256(yaml_path)
    data = yaml_to_json(
        yaml_path,
        strict=False,
        root=root,
        yaml_sha=yaml_sha,
        existing_json=existing_json,
    )

    print("📊 Task List Metadata")
    print("=" * 60)
    print(f"Schema Version: {data.get('schema_version', 'Unknown')}")
    document = data.get("document", {})
    print(f"Document ID: {document.get('id', 'Unknown')}")
    print(f"Title: {document.get('title', 'Unknown')}")
    print(f"Owner: {document.get('owner', 'Unknown')}")
    print()
    print("📁 File Hashes (SHA256)")
    print(f"  YAML: {yaml_sha}")
    if json_path.exists():
        print(f"  JSON: {compute_sha256(json_path)}")
    if md_path.exists():
        print(f"  MD:   {compute_sha256(md_path)}")
    print()
    print(f"🕒 Last Rendered: {data.get('render_meta', {}).get('rendered_utc', 'Never')}")
    print("=" * 60)


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render YAML → JSON + Markdown for refactor tasks",
    )
    parser.add_argument("--strict", action="store_true", help="Fail on unresolved {{VAR}} placeholders")
    parser.add_argument("--meta", action="store_true", help="Print metadata and hashes and exit")
    parser.add_argument("--root", help="Repository root (defaults to current working directory)")
    parser.add_argument("--source", help=f"Source YAML path (default: {DEFAULT_SOURCE_NAME})")
    parser.add_argument("--json-out", help=f"JSON output path (default: {DEFAULT_JSON_NAME})")
    parser.add_argument("--md-out", help=f"Markdown output path (default: {DEFAULT_MD_NAME})")
    parser.add_argument(
        "--allow-tbd",
        action="store_true",
        help="Permit TBD_ placeholders when validating the rendered output",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.root).resolve() if args.root else Path.cwd()

    def resolve_path(value: str | None, default_name: str) -> Path:
        if value:
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = (root / candidate).resolve()
            return candidate
        return (root / default_name).resolve()

    source_path = resolve_path(args.source, DEFAULT_SOURCE_NAME)
    json_path = resolve_path(args.json_out, DEFAULT_JSON_NAME)
    md_path = resolve_path(args.md_out, DEFAULT_MD_NAME)

    load_env_file(root)

    if args.meta:
        print_metadata(root, source_path, json_path, md_path)
        return 0

    print(f"[INFO] Rendering {_display_path(source_path, root)}")

    existing_json: dict | None = None
    if json_path.exists():
        try:
            existing_json = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            sys.stderr.write(
                f"[ERROR] Failed to parse existing JSON artifact: {json_path}\n"
            )
            sys.stderr.write(f"        {exc}\n")
            return 1

    yaml_sha = compute_sha256(source_path)
    data = yaml_to_json(
        source_path,
        strict=args.strict,
        root=root,
        yaml_sha=yaml_sha,
        existing_json=existing_json,
    )

    data = sort_plan_structure(data)

    unresolved = find_placeholders(data, allow_tbd=args.allow_tbd)
    if unresolved:
        sys.stderr.write("❌ Unresolved template placeholders detected:\n")
        for issue in unresolved:
            sys.stderr.write(f"   - [{issue.kind}] {issue.path}: {issue.value!r}\n")
        if any(issue.kind == "tbd" for issue in unresolved):
            sys.stderr.write("Use --allow-tbd for draft renders or replace TBD_ markers.\n")
        if any(issue.kind == "template" for issue in unresolved):
            sys.stderr.write("Use environment variables or update the YAML to remove {{...}} blocks.\n")
        return 1

    validation_errors: list[str] = []
    validation_errors.extend(validate_task_ids(data))
    validation_errors.extend(validate_acceptance_criteria(data))
    validation_errors.extend(validate_gate_ids(data))
    validation_errors.extend(validate_commands(data))
    validation_errors.extend(validate_artifact_paths(data))
    validation_errors.extend(validate_task_file_paths(data))
    validation_errors.extend(validate_task_inputs(data))

    if validation_errors:
        for err in validation_errors:
            sys.stderr.write(f"{err}\n")
        return 1

    json_output = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False)
    if not json_output.endswith("\n"):
        json_output += "\n"
    json_path.write_text(json_output, encoding="utf-8")
    print(f"[OK] JSON written → {_display_path(json_path, root)}")

    validate_json(data)
    with importlib_resources.as_file(_schema_resource()) as schema_path:
        print(f"[OK] Schema validated against {_display_path(schema_path, root)}")

    md_text = render_markdown(data)
    if not md_text.endswith("\n"):
        md_text += "\n"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"[OK] Markdown summary written → {_display_path(md_path, root)}")

    write_hashes(root, source_path, json_path, md_path)

    print("[DONE] Render completed successfully.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
