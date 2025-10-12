#!/usr/bin/env python3
"""
CI Gate G5 - Evidence Hash

Validates that evidence blocks have correct SHA256 hashes after normalization.
Ensures evidence integrity for audit trail during refactoring.

Usage:
    python3 tools/ci/ci_gate_evidence_hash.py [evidence_file]

Exit codes:
    0: All evidence hashes valid (PASS) or no evidence (SKIP)
    1: Invalid hashes found (FAIL)

References:
    - POLICY_GATES.md §4.3 (lines 111-147)
    - DETAILED_TASK_LIST.md Task 0.6
"""

import sys
import re
import json
import hashlib
from pathlib import Path


class SecurityError(RuntimeError):
    """Evidence validation failure."""
    pass


# Project root (2 levels up from tools/ci/)
ROOT = Path(__file__).resolve().parents[2]

# Default evidence file
DEFAULT_EVIDENCE_FILE = ROOT / "evidence_blocks.jsonl"

# Whitespace normalization pattern
WHITESPACE = re.compile(r"\s+")


def norm(s: str) -> str:
    """Normalize text for hash computation.

    Normalization:
    - CRLF → LF
    - CR → LF
    - Strip leading/trailing whitespace
    - Collapse all whitespace to single space

    Args:
        s: Text to normalize

    Returns:
        Normalized text
    """
    s = s.replace("\r\n", "\n").replace("\r", "\n").strip()
    s = WHITESPACE.sub(" ", s)
    return s


def sha256_norm(s: str) -> str:
    """Compute SHA256 hash of normalized text.

    Args:
        s: Text to hash

    Returns:
        Hex-encoded SHA256 hash
    """
    return hashlib.sha256(norm(s).encode("utf-8")).hexdigest()


def validate_evidence_file(evidence_path: Path) -> tuple[bool, list[dict]]:
    """Validate all evidence blocks in file.

    Args:
        evidence_path: Path to evidence JSONL file

    Returns:
        (all_valid, failures) - all_valid=True if all hashes match
    """
    failures = []
    valid_count = 0

    for line_num, line in enumerate(evidence_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue  # Skip empty lines

        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            failures.append({
                "line": line_num,
                "error": "invalid_json",
                "detail": str(e)
            })
            continue

        # Extract fields
        evidence_id = obj.get("evidence_id", f"<unknown-line-{line_num}>")
        want_hash = obj.get("sha256")
        quote = obj.get("code_snippet", "")

        if not want_hash:
            # No hash provided - skip validation
            continue

        # Compute hash of quoted text
        have_hash = sha256_norm(quote)

        if want_hash != have_hash:
            failures.append({
                "line": line_num,
                "evidence_id": evidence_id,
                "error": "hash_mismatch",
                "expected": want_hash[:16] + "...",
                "actual": have_hash[:16] + "...",
                "source_file": obj.get("file", "<unknown>")
            })
        else:
            valid_count += 1

    return (len(failures) == 0, failures)


def main():
    """Main entry point."""
    try:
        # Parse arguments
        if len(sys.argv) > 1:
            evidence_path = Path(sys.argv[1])
        else:
            evidence_path = DEFAULT_EVIDENCE_FILE

        # Check if evidence file exists
        if not evidence_path.exists():
            print(json.dumps({
                "status": "SKIP",
                "reason": "no_evidence_file",
                "message": f"Evidence file not found: {evidence_path}"
            }))
            sys.exit(0)

        # Check if file is empty
        if evidence_path.stat().st_size == 0:
            print(json.dumps({
                "status": "SKIP",
                "reason": "evidence_empty",
                "message": "Evidence file is empty"
            }))
            sys.exit(0)

        # Validate evidence
        all_valid, failures = validate_evidence_file(evidence_path)

        if all_valid:
            # Count total blocks
            total_blocks = sum(1 for line in evidence_path.read_text(encoding="utf-8").splitlines() if line.strip())

            print(json.dumps({
                "status": "OK",
                "message": "All evidence hashes valid",
                "blocks_validated": total_blocks,
                "evidence_file": str(evidence_path.relative_to(ROOT) if evidence_path.is_relative_to(ROOT) else evidence_path)
            }))
            sys.exit(0)
        else:
            print(json.dumps({
                "status": "FAIL",
                "reason": "invalid_evidence_hashes",
                "failures": failures,
                "failure_count": len(failures),
                "evidence_file": str(evidence_path.relative_to(ROOT) if evidence_path.is_relative_to(ROOT) else evidence_path)
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
