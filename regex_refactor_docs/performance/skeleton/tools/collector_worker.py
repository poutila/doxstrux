#!/usr/bin/env python3
"""
Subprocess-based collector isolation harness.

Provides cross-platform timeout enforcement for collectors by running them
in isolated subprocesses. This works on Windows where SIGALRM is not available.

Usage:
    python tools/collector_worker.py \
        --collector doxstrux.markdown.collectors_phase8.heading_collector:HeadingCollector \
        --tokens /tmp/tokens.json \
        --timeout 5 \
        --max-memory-mb 100

Security Features:
    - Hard timeout enforcement via subprocess.Popen.communicate(timeout=...)
    - Memory limit enforcement (platform-specific)
    - Process isolation prevents collector crashes from affecting main process
    - JSON-based IPC prevents code injection

Exit Codes:
    0 - Success
    1 - Collector error (exception raised)
    2 - Timeout exceeded
    3 - Memory limit exceeded
    4 - Invalid arguments or setup error
"""
from __future__ import annotations
import sys
import json
import argparse
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resource limits
DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_MAX_MEMORY_MB = 100


def run_collector_subprocess(
    collector_spec: str,
    tokens_path: Path,
    timeout_seconds: int,
    max_memory_mb: int,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run a collector in an isolated subprocess with timeout and memory limits.

    Args:
        collector_spec: Module path and class name (e.g., "module.path:ClassName")
        tokens_path: Path to JSON file containing serialized tokens
        timeout_seconds: Maximum execution time in seconds
        max_memory_mb: Maximum memory usage in MB
        output_path: Optional path to write collector output JSON

    Returns:
        Dict with keys:
            - success: bool
            - result: collector output (if success=True)
            - error: error message (if success=False)
            - exit_code: subprocess exit code
            - duration_ms: execution time in milliseconds
    """
    # Build subprocess command
    worker_script = Path(__file__).parent / "collector_worker_impl.py"

    cmd = [
        sys.executable,
        str(worker_script),
        "--collector", collector_spec,
        "--tokens", str(tokens_path),
        "--max-memory-mb", str(max_memory_mb),
    ]

    if output_path:
        cmd.extend(["--output", str(output_path)])

    start_time = time.time()

    try:
        # Run subprocess with timeout
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
            exit_code = proc.returncode
            duration_ms = int((time.time() - start_time) * 1000)

            if exit_code == 0:
                # Success - parse output JSON
                try:
                    result = json.loads(stdout) if stdout else {}
                    return {
                        "success": True,
                        "result": result,
                        "exit_code": exit_code,
                        "duration_ms": duration_ms
                    }
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Failed to parse collector output: {e}",
                        "exit_code": exit_code,
                        "duration_ms": duration_ms,
                        "stdout": stdout,
                        "stderr": stderr
                    }
            else:
                # Error
                error_msg = stderr.strip() if stderr else f"Exit code {exit_code}"
                return {
                    "success": False,
                    "error": error_msg,
                    "exit_code": exit_code,
                    "duration_ms": duration_ms,
                    "stderr": stderr
                }

        except subprocess.TimeoutExpired:
            # Kill process on timeout
            proc.kill()
            proc.communicate()  # Wait for cleanup
            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "success": False,
                "error": f"Collector exceeded {timeout_seconds}s timeout",
                "exit_code": 2,
                "duration_ms": duration_ms
            }

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": f"Failed to spawn subprocess: {e}",
            "exit_code": 4,
            "duration_ms": duration_ms
        }


def main():
    """CLI entry point for subprocess collector runner."""
    parser = argparse.ArgumentParser(
        description="Run collector in isolated subprocess with timeout and memory limits"
    )
    parser.add_argument(
        "--collector",
        required=True,
        help="Collector spec: module.path:ClassName (e.g., 'doxstrux.markdown.collectors_phase8.heading_collector:HeadingCollector')"
    )
    parser.add_argument(
        "--tokens",
        required=True,
        type=Path,
        help="Path to JSON file containing serialized tokens"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})"
    )
    parser.add_argument(
        "--max-memory-mb",
        type=int,
        default=DEFAULT_MAX_MEMORY_MB,
        help=f"Maximum memory in MB (default: {DEFAULT_MAX_MEMORY_MB})"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write collector output JSON"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.tokens.exists():
        print(f"ERROR: Tokens file not found: {args.tokens}", file=sys.stderr)
        return 4

    # Run collector
    result = run_collector_subprocess(
        collector_spec=args.collector,
        tokens_path=args.tokens,
        timeout_seconds=args.timeout,
        max_memory_mb=args.max_memory_mb,
        output_path=args.output
    )

    # Print results
    if args.verbose or not result["success"]:
        print(json.dumps(result, indent=2))
    elif result["success"]:
        # Just print collector output on success
        print(json.dumps(result["result"], indent=2))

    # Exit with appropriate code
    return 0 if result["success"] else result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
