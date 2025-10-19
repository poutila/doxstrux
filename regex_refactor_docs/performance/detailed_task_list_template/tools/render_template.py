#!/usr/bin/env python3
"""
render_template.py — minimal template renderer for files with {{PLACEHOLDER}} tokens.

Features
- Replaces tokens like {{FOO}} with values from a replacements YAML/JSON file or environment variables.
- Replacements file may be YAML or JSON.
- Outputs rendered file to stdout or to a target path.
- --strict mode exits non-zero if unresolved placeholders remain.
- No external templating dependency required (no Jinja2).

Usage
    # render with replacements.yaml and write to stdout
    python tools/render_template.py --template docs/phase_template.yaml --replacements config/phase08_values.yml

    # render and write to file
    python tools/render_template.py -t docs/phase_template.yaml -r config/phase08_values.yml -o RUN_TO_GREEN.md

    # render using only environment variables, strict mode (fail if unresolved)
    POLICY_REQUIRE_HMAC=true python tools/render_template.py -t docs/phase_template.yaml --strict

Replacements file examples (YAML or JSON):
    document_id: "phase-08-warehouse"
    title: "Phase 8 Warehouse"
    phase_number: 8
    ARTIFACT_FILENAME: "consumer_artifact.json"

Notes
- Token names are alphanumeric and may contain underscores: {{MY_TOKEN}}
- Environment variables take precedence if a key exists in both env and replacements file.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path

# Try to import yaml, but gracefully degrade to JSON-only if not present.
try:
    import yaml  # PyYAML
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False

TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z0-9_./:-]+)\s*\}\}")  # allow dots/slashes/colons for some keys


def load_replacements(path: Path | None) -> dict:
    if path is None:
        return {}
    txt = path.read_text(encoding="utf8")
    # Try JSON first (fast), then YAML if available
    try:
        data = json.loads(txt)
        if not isinstance(data, dict):
            raise ValueError("replacements JSON must be an object/dict at top-level")
        return data
    except Exception:
        if _HAS_YAML:
            try:
                data = yaml.safe_load(txt)
                if data is None:
                    return {}
                if not isinstance(data, dict):
                    raise ValueError("replacements YAML must be a mapping at top-level")
                return data
            except Exception as e:
                raise RuntimeError(f"Failed to parse replacements file as YAML/JSON: {e}")
        else:
            raise RuntimeError("Replacements file is not valid JSON and PyYAML not installed to parse YAML.")


def render_template(template_text: str, context: dict, strict: bool = False) -> str:
    """
    Replace tokens in template_text with context values. context keys and env vars are strings.
    If strict=True, raise a RuntimeError when unresolved placeholders remain.
    """
    def repl(m: re.Match):
        key = m.group(1)
        if key in context:
            return str(context[key])
        # allow nested keys via dot lookup: a.b -> context['a']['b'] if dict-like
        if "." in key:
            parts = key.split(".")
            cur = context
            for p in parts:
                if isinstance(cur, dict) and p in cur:
                    cur = cur[p]
                else:
                    cur = None
                    break
            if cur is not None:
                return str(cur)
        # fallback to environment
        env_val = os.environ.get(key)
        if env_val is not None:
            return env_val
        # unresolved -> keep token or raise later
        return m.group(0)

    rendered = TOKEN_RE.sub(repl, template_text)

    # if strict mode, detect unresolved tokens
    if strict:
        unresolved = TOKEN_RE.findall(rendered)
        if unresolved:
            raise RuntimeError(f"Unresolved placeholders after rendering (strict mode): {sorted(set(unresolved))}")
    return rendered


def find_placeholders(template_text: str) -> list:
    return sorted(set(TOKEN_RE.findall(template_text)))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="render_template.py", description="Render {{PLACEHOLDER}} tokens in a template file.")
    p.add_argument("-t", "--template", required=True, help="Path to template file (YAML/MD/JSON/etc.)")
    p.add_argument("-r", "--replacements", required=False, help="Path to replacements file (YAML or JSON)")
    p.add_argument("-o", "--output", required=False, help="Output path; if omitted prints to stdout")
    p.add_argument("--strict", action="store_true", help="Fail if any placeholders remain unresolved")
    p.add_argument("--list-placeholders", action="store_true", help="Only list placeholders found in template and exit 0")
    args = p.parse_args(argv)

    tpl_path = Path(args.template)
    if not tpl_path.exists():
        print(f"ERROR: template not found: {tpl_path}", file=sys.stderr)
        return 2

    repl_path = Path(args.replacements) if args.replacements else None
    try:
        replacements = load_replacements(repl_path) if repl_path else {}
    except Exception as e:
        print(f"ERROR: failed to load replacements: {e}", file=sys.stderr)
        return 3

    # environment variables override replacements file
    env_context = {k: v for k, v in os.environ.items()}
    # Merge: env takes precedence
    context = {**replacements, **env_context}

    template_text = tpl_path.read_text(encoding="utf8")

    if args.list_placeholders:
        placeholders = find_placeholders(template_text)
        for ph in placeholders:
            print(ph)
        return 0

    try:
        out_text = render_template(template_text, context, strict=args.strict)
    except Exception as e:
        print(f"ERROR: rendering failed: {e}", file=sys.stderr)
        return 4

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_text, encoding="utf8")
        print(f"Wrote rendered template to: {out_path}")
    else:
        sys.stdout.write(out_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
