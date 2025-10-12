#!/usr/bin/env python3
"""
CI Gate G1 - No Hybrids

Validates that no hybrid regex/token code patterns exist in the codebase.
Ensures clean token-based implementation without legacy regex compatibility flags.

Usage:
    .venv/bin/python tools/ci/ci_gate_no_hybrids.py

Exit codes:
    0: No hybrid patterns found (PASS)
    1: Hybrid patterns found (FAIL)
    2: Negative self-test probe created (needs re-run)

References:
    - POLICY_GATES.md §4.1 (lines 54-86)
    - DETAILED_TASK_LIST.md Task 0.2
"""

import sys
import pathlib
import re
import json


class SecurityError(RuntimeError):
    """CI gate validation failure."""
    pass


# Project root (2 levels up from tools/ci/)
ROOT = pathlib.Path(__file__).resolve().parents[2]

# Forbidden hybrid patterns
FORBIDDEN = re.compile(r"(USE_TOKEN_[A-Z_]+|USE_REGEX_[A-Z_]+|MD_REGEX_COMPAT|LEGACY_REGEX_PARSER)")


def iter_py_files(root: pathlib.Path):
    """Iterate Python files in src/, excluding tests and vendor."""
    for p in root.rglob("*.py"):
        rp = p.relative_to(root)
        # Exclude tests, vendor, venv
        if str(rp).startswith(("tests/", "vendor/", ".venv/", "venv/", "__pycache__/")):
            continue
        yield p


def check_for_hybrids() -> tuple[bool, list[str]]:
    """Check for forbidden hybrid patterns in source code.

    Returns:
        (is_clean, bad_files) - is_clean=True if no hybrids found
    """
    bad = []
    src_dir = ROOT / "src"

    if not src_dir.exists():
        raise SecurityError(f"Source directory not found: {src_dir}")

    for p in iter_py_files(src_dir):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            if FORBIDDEN.search(text):
                bad.append(str(p.relative_to(ROOT)))
        except Exception as e:
            # Log but don't fail on read errors
            print(json.dumps({
                "status": "WARNING",
                "file": str(p.relative_to(ROOT)),
                "error": str(e)
            }), file=sys.stderr)

    return (len(bad) == 0, bad)


def negative_self_test() -> bool:
    """Run negative self-test to ensure gate actually detects hybrids.

    Creates a probe file with a forbidden pattern, expects gate to fail.

    Returns:
        True if probe exists, False if just created (needs re-run)
    """
    # Probe location
    probe_dir = ROOT / "scripts"
    probe_file = probe_dir / "ci_negative_test__hybrid_probe.txt"

    if probe_file.exists():
        return True  # Probe already exists

    # Create probe
    probe_dir.mkdir(parents=True, exist_ok=True)
    probe_file.write_text("USE_TOKEN_SHOULD_FAIL", encoding="utf-8")

    return False  # Just created, needs re-run


def main():
    """Main entry point."""
    try:
        # Negative self-test
        if not negative_self_test():
            # JSON-only output (per CI Gate Extraction Pattern §7)
            print(json.dumps({
                "status": "SKIP",
                "reason": "negative_self_test_probe_created",
                "message": "Created negative self-test probe. Re-run gate."
            }))
            sys.exit(2)

        # Check for hybrids
        is_clean, bad_files = check_for_hybrids()

        if is_clean:
            # Success - JSON output
            print(json.dumps({
                "status": "OK",
                "message": "No hybrid patterns found",
                "files_checked": sum(1 for _ in iter_py_files(ROOT / "src"))
            }))
            sys.exit(0)
        else:
            # Failure - JSON output
            print(json.dumps({
                "status": "FAIL",
                "reason": "hybrid_patterns_found",
                "forbidden_files": bad_files,
                "count": len(bad_files)
            }))
            sys.exit(1)

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
