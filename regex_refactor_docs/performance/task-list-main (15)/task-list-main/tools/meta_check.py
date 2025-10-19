#!/usr/bin/env python3
"""
meta_check.py — one-shot validation for the task-list package & repo.

Draft mode (default): allows 'TBD_' placeholders.
Release mode (--release): fails if any 'TBD_' placeholders remain.

Checks
  1) Packaged schema availability (importlib.resources)
  2) Strict render (invokes your renderer CLI)
  3) JSON ↔ Schema v2 validation
  4) Drift gate (git diff JSON/MD after render)
  5) Placeholder policy ({{...}} always banned; TBD_ banned in --release)
  6) Task IDs unique & numeric-monotone; Gate IDs monotone
  7) Path safety (repo-relative POSIX, no '..', no backslashes, no absolute)
  8) Command deny list (fail-closed)
  9) YAML SHA (LF-normalized) matches render_meta.sha256_of_yaml
 10) Markdown front-matter has render_meta keys (parity)
 11) Phase-complete artifacts validate (if schema present)
 12) CLI entry points expose main()
 13) YAML anchors/tabs blocked
 14) schema_version sync (YAML vs schema)
 15) Manual heuristic drift (warn if v1-only keys referenced)

Exit codes:
  0 = all checks passed
  1 = checks failed
  2 = preflight failed (missing files etc.)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.is_dir():
    sys.path.insert(0, str(SRC_DIR))

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - hard failure path
    print("❌ PyYAML not installed. `pip install pyyaml`", file=sys.stderr)
    raise

try:
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover - hard failure path
    print("❌ jsonschema not installed. `pip install jsonschema`", file=sys.stderr)
    raise

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

RE_V1_DOC_KEYS = re.compile(r'(?m)^"?(meta|ai|tasks|gates)"?\s*:', re.I)


@dataclass
class Ctx:
    repo_root: Path
    yaml_path: Path
    json_path: Path
    md_path: Path
    renderer_cmd: str
    release: bool
    manual_path: Optional[Path]


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


def load_packaged_schema() -> Tuple[bool, str, Optional[dict]]:
    try:
        from importlib import resources

        schema_file = resources.files("tasklist.schemas").joinpath(
            "detailed_task_list.schema.json"
        )
        if not schema_file.is_file():
            return (
                False,
                "Packaged schema missing: tasklist/schemas/detailed_task_list.schema.json",
                None,
            )
        with schema_file.open("rb") as handle:
            schema = json.load(handle)
        return True, "Packaged schema located.", schema
    except Exception as exc:  # pragma: no cover - importlib failure
        return False, f"Cannot import packaged schema via importlib.resources: {exc}", None


def run_renderer(ctx: Ctx) -> Tuple[bool, str]:
    base_cmd = shlex.split(ctx.renderer_cmd)
    command = base_cmd + ["--source", str(ctx.yaml_path), "--strict"]
    env = os.environ.copy()
    src_path = str(ctx.repo_root / "src")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        if "PYTHONPATH" in env and env["PYTHONPATH"]
        else src_path
    )
    try:
        subprocess.run(
            command,
            check=True,
            cwd=ctx.repo_root,
            env=env,
        )
        return True, "Renderer ok."
    except subprocess.CalledProcessError as exc:
        return False, f"Renderer failed (exit {exc.returncode})."


def schema_validate(schema: dict, data: dict) -> Tuple[bool, List[str]]:
    errors = [
        f"{error.message} @ {list(error.path)}" for error in Draft202012Validator(schema).iter_errors(data)
    ]
    return len(errors) == 0, errors


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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True, "Drift gate ok (JSON/MD up to date)."
    except subprocess.CalledProcessError:
        return False, "Rendered JSON/MD differ from working tree. Re-render & commit."


def placeholder_policy(ctx: Ctx) -> Tuple[bool, List[str]]:
    problems: List[str] = []
    for path in (ctx.yaml_path, ctx.json_path, ctx.md_path):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "{{" in text:
            problems.append(f"Unresolved '{{{{...}}}}' in {path.name}")
        if ctx.release and re.search(r"\bTBD_[A-Z0-9_]+", text):
            problems.append(f"'TBD_' placeholders present in release mode: {path.name}")
    return len(problems) == 0, problems


def validate_ids_and_gates(data: dict) -> Tuple[bool, List[str]]:
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


def validate_paths_and_commands(data: dict) -> Tuple[bool, List[str]]:
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


def md_front_matter_has_render_meta(ctx: Ctx) -> Tuple[bool, str]:
    if not ctx.md_path.exists():
        return False, "Markdown render not found."
    text = ctx.md_path.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        return False, "Markdown missing YAML front-matter."
    try:
        header = yaml.safe_load(match.group(1))
    except Exception as exc:
        return False, f"Markdown front-matter not valid YAML: {exc}"
    if not isinstance(header, dict):
        return False, "Markdown front-matter not a mapping."
    render_meta = header.get("render_meta")
    if not isinstance(render_meta, dict):
        return False, "Markdown front-matter missing render_meta block."
    required_keys = ["source_file", "schema_version", "sha256_of_yaml", "rendered_utc"]
    missing = [key for key in required_keys if key not in render_meta]
    if missing:
        return False, f"Markdown render_meta missing keys: {', '.join(missing)}"
    return True, "Markdown front-matter has render_meta keys."


def validate_phase_complete(ctx: Ctx) -> Tuple[bool, List[str]]:
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


def yaml_hygiene(ctx: Ctx) -> Tuple[bool, List[str]]:
    text = ctx.yaml_path.read_text(encoding="utf-8", errors="ignore")
    errors: List[str] = []
    if "\t" in text:
        errors.append("YAML contains tab characters (use spaces only).")
    if re.search(r"(^|\n)\s*[&*][A-Za-z0-9_-]+", text):
        errors.append("YAML uses anchors/aliases (&, *). Avoid for deterministic dumps.")
    return len(errors) == 0, errors


def schema_version_sync(schema: dict, data: dict, yaml_text: str) -> Tuple[bool, str]:
    want = data.get("schema_version")
    schema_version = schema.get("model_version") or schema.get("schema_version")
    if not want or not schema_version:
        return True, "schema_version sync: OK (schema or document missing explicit version)."
    if want != schema_version:
        return False, f"schema_version mismatch: YAML/JSON={want} vs schema={schema_version}"
    if f'schema_version: "{want}"' not in yaml_text and f"schema_version: {want}" not in yaml_text:
        return False, "schema_version not found or mismatched in YAML text."
    return True, "schema_version sync OK."


def manual_v1_drift_warn(ctx: Ctx) -> Tuple[bool, str]:
    if not ctx.manual_path or not ctx.manual_path.exists():
        return True, "Manual not provided; skipping v1/v2 drift heuristic."
    text = ctx.manual_path.read_text(encoding="utf-8", errors="ignore")
    if RE_V1_DOC_KEYS.search(text) and "document" in text and "phases" in text:
        return False, "Manual may reference both v1 and v2 keys. Consider pruning v1-only mentions (meta/ai/tasks/gates)."
    return True, "Manual heuristic: no obvious v1/v2 drift."


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        raise SystemExit(f"Failed to load JSON from {path}: {exc}")


def ensure_metadata_block(data: dict) -> dict:
    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        metadata.setdefault("schema_version", data.get("schema_version", "2.0.0"))
        return metadata
    metadata = {"schema_version": data.get("schema_version", "2.0.0")}
    data["metadata"] = metadata
    return metadata


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run all task-list meta checks.")
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
        default="python src/tasklist/render_task_templates.py",
        help="Renderer CLI to invoke",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Fail on any 'TBD_' placeholders",
    )
    parser.add_argument(
        "--manual",
        default="USER_MANUAL.md",
        help="Path to manual for drift heuristic",
    )
    args = parser.parse_args(argv)

    ctx = Ctx(
        repo_root=Path.cwd(),
        yaml_path=Path(args.source),
        json_path=Path(args.json),
        md_path=Path(args.md),
        renderer_cmd=args.renderer_cmd,
        release=args.release,
        manual_path=Path(args.manual) if args.manual else None,
    )

    notes: List[str] = []
    failures: List[str] = []

    if not ctx.yaml_path.is_file():
        print(f"❌ Missing YAML source: {ctx.yaml_path}", file=sys.stderr)
        return 2

    ok, message, schema = load_packaged_schema()
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)
    if not ok or not schema:
        print("\n".join(notes + failures))
        return 2

    ok, message = run_renderer(ctx)
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)

    if not ctx.json_path.exists():
        failures.append(f"Rendered JSON not found: {ctx.json_path}")
        print("\n".join(notes + failures))
        return 2

    data = load_json(ctx.json_path)
    ensure_metadata_block(data)

    ok, errors = schema_validate(schema, data)
    (notes if ok else failures).append(
        "✅ Schema validation passed."
        if ok
        else "❌ Schema validation:\n  - " + "\n  - ".join(errors)
    )

    ok, message = drift_gate(ctx)
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)

    ok, problems = placeholder_policy(ctx)
    (notes if ok else failures).append(
        "✅ Placeholder policy ok."
        if ok
        else "❌ Placeholders:\n  - " + "\n  - ".join(problems)
    )

    ok, problems = validate_ids_and_gates(data)
    (notes if ok else failures).append(
        "✅ IDs/Gates ok."
        if ok
        else "❌ IDs/Gates:\n  - " + "\n  - ".join(problems)
    )

    ok, problems = validate_paths_and_commands(data)
    (notes if ok else failures).append(
        "✅ Paths/Commands ok."
        if ok
        else "❌ Paths/Commands:\n  - " + "\n  - ".join(problems)
    )

    ok, message = sha_gate(ctx, data)
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)

    ok, message = md_front_matter_has_render_meta(ctx)
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)

    ok, problems = validate_phase_complete(ctx)
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

    ok, problems = yaml_hygiene(ctx)
    (notes if ok else failures).append(
        "✅ YAML hygiene ok."
        if ok
        else "❌ YAML hygiene:\n  - " + "\n  - ".join(problems)
    )

    yaml_text = ctx.yaml_path.read_text(encoding="utf-8", errors="ignore")
    ok, message = schema_version_sync(schema, data, yaml_text)
    (notes if ok else failures).append(("✅ " if ok else "❌ ") + message)

    ok, message = manual_v1_drift_warn(ctx)
    prefix = "✅ " if ok else "⚠️  "
    notes.append(prefix + message)

    print("\n".join(notes))
    if failures:
        print("\n---\n❌ FAILURES:")
        print("\n".join(failures))
        return 1

    print("\n✅ All meta checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
