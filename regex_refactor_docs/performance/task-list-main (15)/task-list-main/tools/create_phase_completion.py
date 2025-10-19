"""Create a phase completion artifact aligned with the packaged schema."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

DEFAULT_OUTPUT_DIR = Path(".")


def current_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no cover - gitless env
        return "UNKNOWN"


def create_artifact(phase: int, phase_name: str, output_dir: Path, gates: list[str]) -> Path:
    artifact = {
        "schema_version": "2.0.0",
        "phase": phase,
        "phase_name": phase_name,
        "completion_date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ci_gates_passed": gates,
        "git_commit": current_commit(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f".phase-{phase}.complete.json"
    path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"✅ Phase completion artifact written to {path}")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", type=int, default=1, help="Phase number to record")
    parser.add_argument("--phase-name", default="phase_1 - Render automation", help="Human readable phase name")
    parser.add_argument(
        "--gate",
        action="append",
        default=["G1", "G2", "G3", "G4", "G5"],
        help="Gate identifiers recorded as passed (may be repeated)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the artifact should be written",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    create_artifact(args.phase, args.phase_name, args.output_dir, list(dict.fromkeys(args.gate)))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
