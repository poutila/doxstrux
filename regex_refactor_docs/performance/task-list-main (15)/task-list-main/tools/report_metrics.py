"""Report corpus and gating metrics for the task list repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

DEFAULT_JSON = Path("DETAILED_TASK_LIST_template.json")
SCHEMAS_DIR = Path("schemas")


def report_corpus() -> int:
    if not SCHEMAS_DIR.exists():
        print(f"⚠️ Schemas directory {SCHEMAS_DIR} missing; corpus size is 0")
        return 0
    files = sorted(SCHEMAS_DIR.rglob("*.json"))
    print(f"Corpus files discovered: {len(files)}")
    for path in files:
        print(f" - {path}")
    return 0


def report_gating(json_path: Path) -> int:
    if not json_path.exists():
        print(f"⚠️ Rendered JSON {json_path} not found; run tasklist-render --strict first")
        return 0
    data = json.loads(json_path.read_text(encoding="utf-8"))
    gates = data.get("ci_gates", [])
    print(f"CI gates defined: {len(gates)}")
    for gate in gates:
        name = gate.get("name", "<unknown>")
        command = gate.get("command", "<no command>")
        print(f" - {name}: {command}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices={"corpus", "gating"},
        required=True,
        help="Metric report to generate",
    )
    parser.add_argument(
        "--json",
        default=DEFAULT_JSON,
        type=Path,
        help="Path to rendered JSON (for gating mode)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.mode == "corpus":
        return report_corpus()
    return report_gating(args.json)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
