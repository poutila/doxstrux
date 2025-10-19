#!/usr/bin/env python3
"""
render_task_templates.py
------------------------------------
Converts DETAILED_TASK_LIST_template.yaml → JSON + Markdown.

Features:
- Enforces --strict placeholder resolution ({{VAR}} must resolve or fail)
- Expands environment variables and .env values
- Validates JSON output against schemas/detailed_task_list.schema.json
- Regenerates Markdown table view for human review
- Adds SHA256 synchronization metadata (Phase 1)

Usage:
    python tools/render_task_templates.py --strict
    python tools/render_task_templates.py --meta  # Print metadata
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from validate_commands import validate_commands
from validate_task_ids import validate_gate_ids, validate_task_ids
from sanitize_paths import validate_artifact_paths

# --- Constants ---------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
SRC_YAML = ROOT / "DETAILED_TASK_LIST_template.yaml"
OUT_JSON = ROOT / "DETAILED_TASK_LIST_template.json"
OUT_MD = ROOT / "DETAILED_TASK_LIST_template.md"
SCHEMA = ROOT / "schemas" / "detailed_task_list.schema.json"

PLACEHOLDER_PATTERN = re.compile(r"\{\{([^{}]+)\}\}")


# --- Helpers -----------------------------------------------------------------

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of file."""
    with file_path.open('rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def expand_placeholders(data: str, strict: bool = False) -> str:
    """Replace {{VAR}} with environment or .env values."""
    def repl(match):
        var = match.group(1).strip()
        val = os.getenv(var)
        if val is None and strict:
            raise ValueError(f"Unresolved placeholder: {{ {var} }}")
        return val or match.group(0)

    return PLACEHOLDER_PATTERN.sub(repl, data)


def load_env_file():
    """Read .env if present and populate os.environ."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    with env_path.open() as f:
        for line in f:
            if not line.strip() or line.strip().startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.strip().split("=", 1)
            os.environ.setdefault(k, v)


def add_render_meta(data: dict, yaml_path: Path) -> dict:
    """Add render_meta block to output (Phase 1: SHA synchronization)."""
    data.setdefault("render_meta", {})
    data["render_meta"].update({
        "source_file": str(yaml_path.relative_to(ROOT)),
        "schema_version": data.get("schema_version", "1.0.0"),
        "sha256_of_yaml": compute_sha256(yaml_path),
        "rendered_utc": datetime.utcnow().isoformat() + "Z"
    })
    return data


def yaml_to_json(yaml_path: Path, strict: bool) -> dict:
    """Load YAML, expand placeholders, return dict."""
    raw_text = yaml_path.read_text(encoding="utf-8")
    expanded = expand_placeholders(raw_text, strict=strict)
    data = yaml.safe_load(expanded)
    data.setdefault("meta", {})
    data["meta"]["rendered_utc"] = datetime.utcnow().isoformat() + "Z"

    # Add render metadata (Phase 1)
    data = add_render_meta(data, yaml_path)

    return data


def validate_json(data: dict, schema_path: Path):
    """Validate data against JSON Schema."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        sys.stderr.write(f"[ERROR] JSON schema validation failed:\n{e}\n")
        sys.exit(1)


def render_markdown(data: dict) -> str:
    """Render a lightweight Markdown view for human review."""
    lines = []
    meta = data.get("meta", {})
    render_meta = data.get("render_meta", {})

    # YAML front matter (Phase 6: Meta propagation)
    lines.append("---")
    lines.append(f"phase: {meta.get('phase', 0)}")
    lines.append(f"title: \"{meta.get('title', 'Untitled')}\"")
    lines.append(f"author: \"{meta.get('author', 'Unknown')}\"")
    lines.append(f"schema_version: \"{data.get('schema_version', '1.0.0')}\"")
    lines.append(f"rendered_utc: \"{render_meta.get('rendered_utc', 'Unknown')}\"")
    lines.append(f"source_sha256: \"{render_meta.get('sha256_of_yaml', 'Unknown')}\"")
    lines.append("---")
    lines.append("")

    lines.append(f"# Detailed Task List — Phase {meta.get('phase', '?')}")
    lines.append(f"Generated: {meta.get('rendered_utc', '')}")
    lines.append("")
    lines.append("## AI Runbook")
    ai = data.get("ai", {})
    for k, v in ai.items():
        lines.append(f"- **{k}**: {v if not isinstance(v, (list, dict)) else json.dumps(v, indent=2)}")
    lines.append("")
    lines.append("## Tasks")
    lines.append("| ID | Name | Kind | Impact | Acceptance |")
    lines.append("|:--|:--|:--|:--|:--|")
    for task in data.get("tasks", []):
        lines.append(f"| {task.get('id','')} | {task.get('name','')} | {task.get('kind','')} | "
                     f"{task.get('impact','')} | {', '.join(task.get('acceptance_criteria', []))} |")
    lines.append("")
    lines.append("## Gates")
    lines.append("| ID | Name | Command |")
    lines.append("|:--|:--|:--|")
    for gate in data.get("gates", []):
        lines.append(f"| {gate.get('id','')} | {gate.get('name','')} | `{gate.get('command','')}` |")
    lines.append("")

    # Render metadata footer (Phase 1)
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


def write_hashes(yaml_path: Path, json_path: Path, md_path: Path):
    """Write SHA256 hashes to evidence/hashes/ (Phase 4)."""
    hash_dir = ROOT / "evidence" / "hashes"
    hash_dir.mkdir(parents=True, exist_ok=True)

    (hash_dir / "yaml_sha256.txt").write_text(compute_sha256(yaml_path))
    (hash_dir / "json_sha256.txt").write_text(compute_sha256(json_path))
    (hash_dir / "md_sha256.txt").write_text(compute_sha256(md_path))
    print(f"[OK] Hashes written → {hash_dir}")


def print_metadata(yaml_path: Path, json_path: Path, md_path: Path):
    """Print current metadata and hashes (Phase 9)."""
    data = yaml_to_json(yaml_path, strict=False)

    print("📊 Task List Metadata")
    print("=" * 60)
    print(f"Schema Version: {data.get('schema_version', 'Unknown')}")
    print(f"Phase: {data.get('meta', {}).get('phase', 'Unknown')}")
    print(f"Title: {data.get('meta', {}).get('title', 'Unknown')}")
    print(f"Author: {data.get('meta', {}).get('author', 'Unknown')}")
    print()
    print("📁 File Hashes (SHA256)")
    print(f"  YAML: {compute_sha256(yaml_path)}")
    if json_path.exists():
        print(f"  JSON: {compute_sha256(json_path)}")
    if md_path.exists():
        print(f"  MD:   {compute_sha256(md_path)}")
    print()
    print(f"🕒 Last Rendered: {data.get('render_meta', {}).get('rendered_utc', 'Never')}")
    print("=" * 60)


# --- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Render YAML → JSON + Markdown for refactor tasks")
    parser.add_argument("--strict", action="store_true", help="Fail on unresolved {{VAR}} placeholders")
    parser.add_argument("--meta", action="store_true", help="Print metadata and hashes (Phase 9)")
    args = parser.parse_args()

    load_env_file()

    # Print metadata only (Phase 9)
    if args.meta:
        print_metadata(SRC_YAML, OUT_JSON, OUT_MD)
        sys.exit(0)

    print(f"[INFO] Rendering {SRC_YAML.relative_to(ROOT)}")

    data = yaml_to_json(SRC_YAML, strict=args.strict)

    validation_errors: list[str] = []
    validation_errors.extend(validate_task_ids(data))
    validation_errors.extend(validate_gate_ids(data))
    validation_errors.extend(validate_commands(data))
    validation_errors.extend(validate_artifact_paths(data))

    if validation_errors:
        for err in validation_errors:
            sys.stderr.write(f"{err}\n")
        sys.exit(1)

    OUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] JSON written → {OUT_JSON.relative_to(ROOT)}")

    validate_json(data, SCHEMA)
    print(f"[OK] Schema validated against {SCHEMA.relative_to(ROOT)}")

    md_text = render_markdown(data)
    OUT_MD.write_text(md_text, encoding="utf-8")
    print(f"[OK] Markdown summary written → {OUT_MD.relative_to(ROOT)}")

    # Write hashes to evidence/ (Phase 4)
    write_hashes(SRC_YAML, OUT_JSON, OUT_MD)

    print("[DONE] Render completed successfully.")


if __name__ == "__main__":
    main()

