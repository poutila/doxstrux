#!/usr/bin/env python3
"""
emit_task_result.py
-------------------
Emit task execution result in standard format.

Usage:
    python tools/emit_task_result.py 1.2 success "Tests passed" "" 0 45.3 build/output.json
    python tools/emit_task_result.py 2.1 failed "Build error" "gcc: error" 1 10.2
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def emit_result(
    task_id: str,
    status: str,
    stdout: str,
    stderr: str,
    return_code: int,
    duration: float,
    artifacts: list = None,
    meta: dict = None
):
    """Emit task execution result to evidence/results/."""
    result = {
        "task_id": task_id,
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "return_code": return_code,
        "duration_sec": duration,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "artifacts": artifacts or [],
        "meta": meta or {}
    }

    result_dir = Path("evidence/results")
    result_dir.mkdir(parents=True, exist_ok=True)

    output_file = result_dir / f"task_{task_id}.json"
    output_file.write_text(json.dumps(result, indent=2))
    print(f"✅ Result written: {output_file}")
    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: emit_task_result.py TASK_ID STATUS STDOUT STDERR RETURN_CODE DURATION [ARTIFACTS...]")
        print("Example: emit_task_result.py 1.2 success 'Tests passed' '' 0 45.3 build/output.json")
        sys.exit(1)

    task_id = sys.argv[1]
    status = sys.argv[2]
    stdout_text = sys.argv[3]
    stderr_text = sys.argv[4]
    return_code = int(sys.argv[5])
    duration = float(sys.argv[6])
    artifacts = sys.argv[7:] if len(sys.argv) > 7 else []

    emit_result(task_id, status, stdout_text, stderr_text, return_code, duration, artifacts)
