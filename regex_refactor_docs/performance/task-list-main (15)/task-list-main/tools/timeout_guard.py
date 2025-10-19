"""Lightweight timeout helper used by CI automation steps."""

from __future__ import annotations

import signal
import subprocess
import sys
from contextlib import contextmanager
from typing import Iterator, Sequence

DEFAULT_TIMEOUT = 300


@contextmanager
def _alarm(timeout: int) -> Iterator[None]:
    """Context manager that raises ``TimeoutError`` when the alarm fires."""

    def _handler(signum: int, frame) -> None:  # type: ignore[override]
        raise TimeoutError(f"Process exceeded timeout of {timeout} seconds")

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(timeout)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def run(command: Sequence[str], *, timeout: int = DEFAULT_TIMEOUT) -> int:
    """Execute ``command`` and enforce ``timeout`` seconds."""

    try:
        with _alarm(timeout):
            completed = subprocess.run(list(command), check=False)
    except TimeoutError as exc:  # pragma: no cover - exercised in CI
        print(f"❌ {exc}")
        return 124
    return completed.returncode


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    timeout = DEFAULT_TIMEOUT
    if args and args[0].startswith("--timeout="):
        value = args.pop(0).split("=", 1)[1]
        timeout = int(value)
    if not args:
        print("usage: timeout_guard.py [--timeout=SECONDS] command [arg ...]")
        return 1
    return run(args, timeout=timeout)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
