#!/usr/bin/env python3
"""
CI Gate G2 - Canonical Pairs

Validates that test corpus structure is intact by counting canonical pairs.
Each .md test file must have a corresponding .json specification file.

Usage:
    .venv/bin/python tools/ci/ci_gate_canonical_pairs.py [test_dir]

Exit codes:
    0: All .md files have .json specs (PASS)
    1: Orphaned files or validation failure (FAIL)

References:
    - POLICY_GATES.md §4.2 (lines 88-109)
    - DETAILED_TASK_LIST.md Task 0.3
"""

import sys
import json
from pathlib import Path


class SecurityError(RuntimeError):
    """CI gate validation failure."""
    pass


# Project root (2 levels up from tools/ci/)
ROOT = Path(__file__).resolve().parents[2]

# Default test corpus location
DATASET = ROOT / "tools" / "test_mds"


def canonical_pairs(root: Path) -> list[tuple[Path, Path]]:
    """Find all canonical pairs (.md files with corresponding .json specs).

    Args:
        root: Root directory to search for test files

    Returns:
        List of (md_path, json_path) tuples for valid pairs
    """
    pairs = []
    for md in root.rglob("*.md"):
        js = md.with_suffix(".json")
        if js.exists():
            pairs.append((md, js))
    return pairs


def find_orphaned_files(root: Path) -> tuple[list[Path], list[Path]]:
    """Find orphaned .md and .json files without pairs.

    Args:
        root: Root directory to search

    Returns:
        (orphaned_mds, orphaned_jsons) - lists of files without pairs
    """
    orphaned_mds = []
    orphaned_jsons = []

    # Find .md files without .json
    for md in root.rglob("*.md"):
        js = md.with_suffix(".json")
        if not js.exists():
            orphaned_mds.append(md.relative_to(root))

    # Find .json files without .md
    for js in root.rglob("*.json"):
        md = js.with_suffix(".md")
        if not md.exists():
            orphaned_jsons.append(js.relative_to(root))

    return orphaned_mds, orphaned_jsons


def main():
    """Main entry point."""
    try:
        # Determine corpus root (allow override via command line)
        if len(sys.argv) > 1:
            root = Path(sys.argv[1])
        else:
            root = DATASET

        # Validate root exists
        if not root.exists():
            raise SecurityError(f"Test corpus directory not found: {root}")

        if not root.is_dir():
            raise SecurityError(f"Test corpus path is not a directory: {root}")

        # Count canonical pairs
        pairs = canonical_pairs(root)
        pair_count = len(pairs)

        # Check for orphaned files
        orphaned_mds, orphaned_jsons = find_orphaned_files(root)

        # Calculate relative root path (handle paths outside project)
        try:
            root_display = str(root.relative_to(ROOT))
        except ValueError:
            # Path is outside project root, use absolute path
            root_display = str(root)

        # Report results
        if orphaned_mds or orphaned_jsons:
            # Failure - corpus integrity compromised
            result = {
                "status": "FAIL",
                "reason": "orphaned_files_found",
                "canonical_count": pair_count,
                "orphaned_md_count": len(orphaned_mds),
                "orphaned_json_count": len(orphaned_jsons),
                "root": root_display
            }

            # Include first few orphans for diagnostics
            if orphaned_mds:
                result["orphaned_mds_sample"] = [str(p) for p in orphaned_mds[:5]]
            if orphaned_jsons:
                result["orphaned_jsons_sample"] = [str(p) for p in orphaned_jsons[:5]]

            print(json.dumps(result))
            sys.exit(1)
        else:
            # Success - all pairs intact
            print(json.dumps({
                "status": "OK",
                "canonical_count": pair_count,
                "root": root_display
            }))
            sys.exit(0)

    except SecurityError as e:
        print(json.dumps({
            "status": "FAIL",
            "reason": "security_error",
            "error": str(e)
        }))
        sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "status": "FAIL",
            "reason": "unexpected_error",
            "error": str(e)
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
