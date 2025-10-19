"""Validate phase completion artifacts against the packaged schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from jsonschema import Draft202012Validator

DEFAULT_SCHEMA = Path("src/tasklist/schemas/phase_complete.schema.json")


def validate(artifact_path: Path, schema_path: Path) -> int:
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: error.path)
    if errors:
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            print(f"❌ {error.message} at {location}")
        return 1
    print("✅ Phase completion artifact valid")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Path to the phase completion artifact JSON file")
    parser.add_argument(
        "--schema",
        default=DEFAULT_SCHEMA,
        type=Path,
        help="Optional path to the phase completion schema (defaults to the packaged schema)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return validate(args.artifact, args.schema)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
