"""Append evidence snippets to ``evidence/evidence_blocks.jsonl`` atomically."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence


EVIDENCE_FILE = Path("evidence") / "evidence_blocks.jsonl"


def append_block(task_id: str, snippet: str, meta: dict[str, str] | None = None) -> Path:
    record = {
        "task_id": task_id,
        "snippet": snippet,
        "meta": meta or {},
    }
    payload = json.dumps(record, ensure_ascii=False)
    EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(EVIDENCE_FILE, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    with os.fdopen(fd, "a", encoding="utf-8", closefd=True) as handle:
        handle.write(payload + "\n")
    print(f"✅ Evidence block appended for task {task_id}")
    return EVIDENCE_FILE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", help="Task identifier associated with the evidence")
    parser.add_argument("snippet", help="Text snippet captured as evidence")
    parser.add_argument(
        "--meta",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Optional metadata entries to attach to the evidence",
    )
    return parser


def parse_meta(pairs: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    for pair in pairs:
        key, value = pair.split("=", 1)
        meta[key] = value
    return meta


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    append_block(args.task_id, args.snippet, parse_meta(args.meta))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
