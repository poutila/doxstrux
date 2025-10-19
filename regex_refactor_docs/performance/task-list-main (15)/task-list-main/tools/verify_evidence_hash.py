"""Verify the integrity of ``evidence/evidence_blocks.jsonl``."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

EVIDENCE_FILE = Path("evidence") / "evidence_blocks.jsonl"


def verify(path: Path) -> int:
    if not path.exists():
        print(f"⚠️ Evidence file {path} does not exist; skipping hash verification")
        return 0

    issues: list[str] = []
    hashes: list[str] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            issues.append(f"Line {line_no}: invalid JSON ({exc})")
            continue
        if "snippet" not in record or "task_id" not in record:
            issues.append(f"Line {line_no}: missing task_id/snippet keys")
            continue
        digest = hashlib.sha256(raw_line.encode("utf-8")).hexdigest()
        hashes.append(digest)

    if issues:
        for issue in issues:
            print(f"❌ {issue}")
        return 1

    combined = hashlib.sha256("".join(hashes).encode("utf-8")).hexdigest()
    print(f"✅ Evidence hash: {combined}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default=EVIDENCE_FILE,
        type=Path,
        help="Path to the evidence JSONL file (defaults to evidence/evidence_blocks.jsonl)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    return verify(args.path)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
