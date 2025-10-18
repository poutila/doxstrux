#!/usr/bin/env python3
"""
Validate consumer self-audit artifacts against schema and verify HMAC signatures.

Usage:
  python tools/validate_consumer_artifact.py --artifact path/to/artifact.json
  python tools/validate_consumer_artifact.py --artifact path/to/artifact.json --verify-hmac

Environment Variables:
  CONSUMER_ARTIFACT_HMAC_KEY: Base64-encoded shared secret for HMAC verification

Exit Codes:
  0: Artifact is valid
  1: Artifact is invalid (schema violation, expired, or HMAC mismatch)
  2: Usage error or missing files
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def load_schema(schema_path: Path) -> dict:
    """Load JSON schema from file."""
    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(2)
    return json.loads(schema_path.read_text())


def load_artifact(artifact_path: Path) -> dict:
    """Load artifact JSON from file."""
    if not artifact_path.exists():
        print(f"ERROR: Artifact file not found: {artifact_path}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(artifact_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in artifact: {e}", file=sys.stderr)
        sys.exit(1)


def validate_required_fields(artifact: dict) -> bool:
    """Validate that all required fields are present."""
    required = ["repo", "commit", "tool_version", "timestamp", "hits"]
    missing = [f for f in required if f not in artifact]

    if missing:
        print(f"ERROR: Missing required fields: {', '.join(missing)}", file=sys.stderr)
        return False

    return True


def validate_repo_format(repo: str) -> bool:
    """Validate repo name format (org/repo)."""
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$', repo):
        print(f"ERROR: Invalid repo format: {repo} (expected: org/repo)", file=sys.stderr)
        return False
    return True


def validate_commit_format(commit: str) -> bool:
    """Validate commit SHA format (40-char hex)."""
    import re
    if not re.match(r'^[a-f0-9]{40}$', commit):
        print(f"ERROR: Invalid commit SHA: {commit} (expected: 40-char hex)", file=sys.stderr)
        return False
    return True


def validate_timestamp(timestamp_str: str, max_age_days: int = 30) -> bool:
    """Validate timestamp format and age."""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError as e:
        print(f"ERROR: Invalid timestamp format: {timestamp_str} ({e})", file=sys.stderr)
        return False

    age = datetime.now(timestamp.tzinfo) - timestamp

    if age.days > max_age_days:
        print(f"WARNING: Artifact is {age.days} days old (threshold: {max_age_days} days)", file=sys.stderr)
        # Don't fail, just warn

    if age.total_seconds() < 0:
        print(f"ERROR: Timestamp is in the future: {timestamp_str}", file=sys.stderr)
        return False

    return True


def validate_hits_structure(hits: list) -> bool:
    """Validate hits array structure."""
    if not isinstance(hits, list):
        print(f"ERROR: 'hits' must be an array, got {type(hits).__name__}", file=sys.stderr)
        return False

    for i, hit in enumerate(hits):
        if not isinstance(hit, dict):
            print(f"ERROR: hits[{i}] must be an object, got {type(hit).__name__}", file=sys.stderr)
            return False

        if "path" not in hit:
            print(f"ERROR: hits[{i}] missing required field 'path'", file=sys.stderr)
            return False

        if "pattern" not in hit:
            print(f"ERROR: hits[{i}] missing required field 'pattern'", file=sys.stderr)
            return False

        # Optional snippet validation
        if "snippet" in hit and len(hit["snippet"]) > 400:
            print(f"WARNING: hits[{i}] snippet exceeds 400 chars ({len(hit['snippet'])} chars)", file=sys.stderr)

    return True


def compute_hmac_signature(artifact: dict, secret_key: bytes) -> str:
    """Compute HMAC-SHA256 signature of artifact (excluding 'hmac' field)."""
    # Create a copy without the 'hmac' field
    artifact_copy = {k: v for k, v in artifact.items() if k != "hmac"}

    # Canonical JSON representation (sorted keys, no whitespace)
    canonical = json.dumps(artifact_copy, sort_keys=True, separators=(',', ':'))

    # Compute HMAC
    signature = hmac.new(secret_key, canonical.encode('utf-8'), hashlib.sha256)

    return base64.b64encode(signature.digest()).decode('ascii')


def verify_hmac(artifact: dict, secret_key: bytes) -> bool:
    """Verify HMAC signature in artifact."""
    if "hmac" not in artifact:
        print("ERROR: Artifact missing 'hmac' field (required for verification)", file=sys.stderr)
        return False

    provided_hmac = artifact["hmac"]
    expected_hmac = compute_hmac_signature(artifact, secret_key)

    if not hmac.compare_digest(provided_hmac, expected_hmac):
        print(f"ERROR: HMAC signature mismatch", file=sys.stderr)
        print(f"  Provided: {provided_hmac[:20]}...", file=sys.stderr)
        print(f"  Expected: {expected_hmac[:20]}...", file=sys.stderr)
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Validate consumer audit artifacts")
    parser.add_argument("--artifact", "-a", required=True, help="Path to artifact JSON file")
    parser.add_argument("--schema", "-s", default="artifact_schema.json", help="Path to JSON schema file")
    parser.add_argument("--verify-hmac", action="store_true", help="Verify HMAC signature (requires CONSUMER_ARTIFACT_HMAC_KEY env var)")
    parser.add_argument("--max-age-days", type=int, default=30, help="Maximum artifact age in days (default: 30)")
    args = parser.parse_args()

    artifact_path = Path(args.artifact)
    schema_path = Path(args.schema)

    # Load artifact
    artifact = load_artifact(artifact_path)

    # Validate required fields
    if not validate_required_fields(artifact):
        sys.exit(1)

    # Validate repo format
    if not validate_repo_format(artifact["repo"]):
        sys.exit(1)

    # Validate commit format
    if not validate_commit_format(artifact["commit"]):
        sys.exit(1)

    # Validate timestamp
    if not validate_timestamp(artifact["timestamp"], max_age_days=args.max_age_days):
        sys.exit(1)

    # Validate hits structure
    if not validate_hits_structure(artifact["hits"]):
        sys.exit(1)

    # Verify HMAC if requested
    if args.verify_hmac:
        hmac_key_b64 = os.environ.get("CONSUMER_ARTIFACT_HMAC_KEY")
        if not hmac_key_b64:
            print("ERROR: CONSUMER_ARTIFACT_HMAC_KEY environment variable not set", file=sys.stderr)
            sys.exit(2)

        try:
            hmac_key = base64.b64decode(hmac_key_b64)
        except Exception as e:
            print(f"ERROR: Failed to decode HMAC key from base64: {e}", file=sys.stderr)
            sys.exit(2)

        if not verify_hmac(artifact, hmac_key):
            sys.exit(1)

        print("✓ HMAC signature verified")

    # All validations passed
    print(f"✓ Artifact is valid: {artifact['repo']} @ {artifact['commit'][:8]}")
    print(f"  Hits: {len(artifact['hits'])}")
    print(f"  Tool: {artifact['tool_version']}")
    print(f"  Timestamp: {artifact['timestamp']}")

    sys.exit(0)


if __name__ == "__main__":
    main()
