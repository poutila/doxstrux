"""Atomic file write utility.

All evidence and artifact writes MUST use atomic operations to prevent
race conditions in parallel CI jobs.
"""
from pathlib import Path
import os
import tempfile


def atomic_write_text(path: Path, data: str, encoding="utf-8") -> None:
    """Write file atomically using tmp + rename pattern.

    Prevents corruption if two processes write simultaneously.
    POSIX and Windows guarantee rename atomicity.

    Args:
        path: Destination file path
        data: Text content to write
        encoding: Text encoding (default: utf-8)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        text=True
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as f:
            f.write(data)
        os.replace(tmp, path)  # Atomic on POSIX/Windows
    finally:
        try:
            os.remove(tmp)
        except FileNotFoundError:
            pass
