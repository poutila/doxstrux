"""Profile the task list render pipeline and report timing statistics."""

from __future__ import annotations

import argparse
import math
import statistics
import subprocess
import sys
import time
from typing import Sequence

DEFAULT_COMMAND = ("tasklist-render", "--strict")


def run_once(command: Sequence[str]) -> float:
    start = time.perf_counter()
    result = subprocess.run(command, check=False)
    duration = time.perf_counter() - start
    if result.returncode != 0:
        raise RuntimeError(f"Command {' '.join(command)} failed with exit code {result.returncode}")
    return duration


def profile(command: Sequence[str], samples: int) -> list[float]:
    durations: list[float] = []
    for _ in range(samples):
        durations.append(run_once(command))
    return durations


def percentile(values: Sequence[float], frac: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(frac * len(ordered)) - 1)
    return ordered[index]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=1, help="Number of samples to collect")
    parser.add_argument(
        "--assert-under",
        type=float,
        default=None,
        help="Fail if any sample exceeds this many seconds",
    )
    parser.add_argument(
        "--command",
        nargs=argparse.REMAINDER,
        help="Optional override for the command to profile (defaults to tasklist-render --strict)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    command = tuple(args.command) if args.command else DEFAULT_COMMAND
    try:
        durations = profile(command, max(1, args.samples))
    except RuntimeError as error:
        print(f"❌ {error}", file=sys.stderr)
        return 1
    median = statistics.median(durations)
    p95 = percentile(durations, 0.95)
    maximum = max(durations)

    print(f"Samples collected: {len(durations)}")
    print(f"Median: {median:.3f}s")
    print(f"p95: {p95:.3f}s")
    print(f"Max: {maximum:.3f}s")

    if args.assert_under is not None and maximum > args.assert_under:
        print(
            f"❌ Maximum duration {maximum:.3f}s exceeded assertion threshold {args.assert_under:.3f}s",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
