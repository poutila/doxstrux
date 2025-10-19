"""Emit task execution results to the evidence store."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Sequence

DEFAULT_RESULTS_DIR = Path("evidence/results")


def emit_result(
    task_id: str,
    status: str,
    stdout: str,
    stderr: str,
    return_code: int,
    duration: float,
    artifacts: list[str] | None = None,
    meta: dict | None = None,
    root: Path | None = None,
) -> Path:
    """Emit task execution result JSON under ``root/evidence/results``."""
    root = root or Path.cwd()
    result = {
        "task_id": task_id,
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "return_code": return_code,
        "duration_sec": duration,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "artifacts": artifacts or [],
        "meta": meta or {},
    }

    result_dir = root / DEFAULT_RESULTS_DIR
    result_dir.mkdir(parents=True, exist_ok=True)

    output_file = result_dir / f"task_{task_id}.json"
    output_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"✅ Result written: {output_file}")
    return output_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit task execution results to evidence/results")
    parser.add_argument("task_id", help="Task identifier, e.g. 1.2")
    parser.add_argument("status", help="Execution status (success, failed, skipped, etc.)")
    parser.add_argument("stdout", help="Captured standard output text")
    parser.add_argument("stderr", help="Captured standard error text")
    parser.add_argument("return_code", type=int, help="Process return code")
    parser.add_argument("duration", type=float, help="Execution duration in seconds")
    parser.add_argument("artifacts", nargs="*", help="Optional artifact paths recorded with the result")
    parser.add_argument(
        "--root",
        help="Repository root for evidence output (defaults to current working directory)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.root).resolve() if args.root else Path.cwd()
    emit_result(
        task_id=args.task_id,
        status=args.status,
        stdout=args.stdout,
        stderr=args.stderr,
        return_code=args.return_code,
        duration=args.duration,
        artifacts=list(args.artifacts or []),
        root=root,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
