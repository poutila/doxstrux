"""Utility helpers for atomic file writes within the repository."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable


def write_text(path: str | os.PathLike[str], data: str, *, encoding: str = "utf-8") -> Path:
    """Atomically write ``data`` to ``path`` using a temporary file."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=str(destination.parent), encoding=encoding) as handle:
        handle.write(data)
        temp_path = Path(handle.name)
    temp_path.replace(destination)
    return destination


def append_lines(path: str | os.PathLike[str], lines: Iterable[str], *, encoding: str = "utf-8") -> Path:
    """Append ``lines`` to ``path`` atomically."""

    existing = Path(path).read_text(encoding=encoding) if Path(path).exists() else ""
    new_data = existing + "".join(lines)
    return write_text(path, new_data, encoding=encoding)


__all__ = ["write_text", "append_lines"]
