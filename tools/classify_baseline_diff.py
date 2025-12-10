#!/usr/bin/env python
"""
Helper for classifying baseline diffs by change type.

Usage:

    # 1. Generate a diff only for baseline outputs
    git diff -- tools/baseline_outputs > /tmp/baseline.diff

    # 2. Classify changes
    uv run python tools/classify_baseline_diff.py /tmp/baseline.diff

This does NOT decide what is "good" or "bad". It just groups changes to make
manual review easier.

Buckets:
- danger: has_dangerous_content changes
- warnings: warning list changes
- prompt: prompt_injection related
- traversal: path_traversal related
- security_profile: profile changes
- other: everything else (investigate these!)
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


# Simple buckets by substring; extend as needed.
BUCKET_PATTERNS: List[Tuple[str, str]] = [
    ("danger", "has_dangerous_content"),
    ("warnings", "warnings"),
    ("prompt", "prompt_injection"),
    ("traversal", "path_traversal"),
    ("security_profile", "security_profile"),
]


def classify_line(line: str) -> str:
    """Return a bucket name for a single added/removed line."""
    # Strip leading diff marker (+ / -) and whitespace for classification
    content = line[1:].strip()

    for bucket, needle in BUCKET_PATTERNS:
        if needle in content:
            return bucket
    return "other"


def parse_diff(diff_text: str) -> Dict[str, Dict[str, Dict[str, int]]]:
    """
    Parse a unified diff and return counts:

    {
      "tools/baseline_outputs/foo.json": {
         "added":   {"danger": 3, "traversal": 1, "other": 2},
         "removed": {"danger": 7, "other": 1},
      },
      ...
    }
    """
    per_file: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
        lambda: {"added": defaultdict(int), "removed": defaultdict(int)}
    )

    current_file: str | None = None

    for raw in diff_text.splitlines():
        line = raw.rstrip("\n")

        # File header in unified diff: +++ b/path or --- a/path
        if line.startswith("+++ "):
            # Example: "+++ b/tools/baseline_outputs/foo.json"
            path = line[4:].strip()
            # Strip leading a/ or b/
            if path.startswith("a/") or path.startswith("b/"):
                path = path[2:]
            current_file = path
            continue

        if current_file is None:
            continue

        # Only consider added/removed lines (not context, not hunk headers)
        if line.startswith("+") and not line.startswith("+++"):
            bucket = classify_line(line)
            per_file[current_file]["added"][bucket] += 1
        elif line.startswith("-") and not line.startswith("---"):
            bucket = classify_line(line)
            per_file[current_file]["removed"][bucket] += 1

    return per_file


def print_summary(stats: Dict[str, Dict[str, Dict[str, int]]]) -> None:
    """Pretty-print the classification summary."""
    files = sorted(stats.keys())
    if not files:
        print("No baseline changes detected.")
        return

    # Aggregate totals
    totals: Dict[str, Dict[str, int]] = {"added": defaultdict(int), "removed": defaultdict(int)}
    for path in files:
        for kind in ("added", "removed"):
            for bucket, count in stats[path][kind].items():
                totals[kind][bucket] += count

    print("=== Baseline diff classification ===\n")

    # Print totals first
    print("TOTALS:")
    for kind in ("added", "removed"):
        if totals[kind]:
            print(f"  {kind}:")
            for bucket, count in sorted(totals[kind].items()):
                marker = "  " if bucket != "other" else "⚠️"
                print(f"    {marker} {bucket:24s} {count:4d}")
    print()

    # Per-file breakdown
    print(f"FILES CHANGED: {len(files)}\n")
    for path in files:
        file_stats = stats[path]
        has_changes = any(file_stats[k] for k in ("added", "removed"))
        if not has_changes:
            continue

        print(f"  {path}")
        for kind in ("added", "removed"):
            bucket_counts = file_stats[kind]
            if bucket_counts:
                items = ", ".join(f"{b}:{c}" for b, c in sorted(bucket_counts.items()))
                print(f"    {kind}: {items}")


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print(
            f"Usage: {Path(argv[0]).name} /path/to/baseline.diff",
            file=sys.stderr,
        )
        return 1

    diff_path = Path(argv[1])
    if not diff_path.is_file():
        print(f"Diff file not found: {diff_path}", file=sys.stderr)
        return 1

    diff_text = diff_path.read_text(encoding="utf-8")
    stats = parse_diff(diff_text)
    print_summary(stats)

    # Exit with warning code if "other" bucket has changes
    total_other = sum(
        stats[f][k].get("other", 0)
        for f in stats
        for k in ("added", "removed")
    )
    if total_other > 0:
        print(f"\n⚠️  WARNING: {total_other} changes in 'other' bucket need manual review!")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
