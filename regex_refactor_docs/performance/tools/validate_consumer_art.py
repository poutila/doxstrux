#!/usr/bin/env python3
"""
Validate consumer audit artifacts before ingestion (Safety Net 1).

Provides schema validation and optional HMAC verification to prevent
tampering and poisoning of consumer-submitted artifacts.

Usage:
    python tools/validate_consumer_art.py --artifact consumer_artifact.json
    python tools/validate_consumer_art.py --artifact consumer_artifact.json --require-hmac
"""
from __future__ import annotations
import argparse
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any


# Expected schema for consumer artifacts
ARTIFACT_SCHEMA = {
    "required_fields": [
        "org_unregistered_hits",  # List of hits
        "consumer_metadata"        # Provenance metadata
    ],
    "hit_fields": ["repo", "path", "pattern"],
    "metadata_fields": ["timestamp", "consumer_name", "tool_version"]
}


def load_json(path: Path) -> dict:
    """Load JSON file from path."""
    if not path.exists():
        raise SystemExit(f"ERROR: Artifact not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise SystemExit(f"ERROR: Invalid JSON: {e}")


def validate_against_schema(artifact: dict, schema: dict) -> None:
    """
    Validate artifact against expected schema.

    Args:
        artifact: Artifact dict to validate
        schema: Schema definition with required_fields

    Raises:
        SystemExit: If validation fails
    """
    # Check required top-level fields
    for field in schema["required_fields"]:
        if field not in artifact:
            raise SystemExit(f"ERROR: Missing required field: {field}")

    # Validate org_unregistered_hits structure
    hits = artifact.get("org_unregistered_hits", [])
    if not isinstance(hits, list):
        raise SystemExit("ERROR: org_unregistered_hits must be a list")

    for i, hit in enumerate(hits):
        if not isinstance(hit, dict):
            raise SystemExit(f"ERROR: Hit {i} is not a dict")
        for field in schema["hit_fields"]:
            if field not in hit:
                raise SystemExit(f"ERROR: Hit {i} missing field: {field}")

    # Validate consumer_metadata structure
    metadata = artifact.get("consumer_metadata", {})
    if not isinstance(metadata, dict):
        raise SystemExit("ERROR: consumer_metadata must be a dict")

    for field in schema["metadata_fields"]:
        if field not in metadata:
            raise SystemExit(f"ERROR: consumer_metadata missing field: {field}")

    print(f"✓ Schema validation passed ({len(hits)} hits)")


def compute_hmac(artifact: dict, secret_key: bytes) -> str:
    """
    Compute HMAC-SHA256 of artifact (excluding hmac field).

    Args:
        artifact: Artifact dict
        secret_key: Secret key bytes

    Returns:
        Hex-encoded HMAC digest
    """
    # Create copy without hmac field for canonical representation
    canonical = {k: v for k, v in artifact.items() if k != "hmac"}
    canonical_str = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    return hmac.new(secret_key, canonical_str.encode('utf-8'), hashlib.sha256).hexdigest()


def verify_hmac(artifact: dict, secret_key: bytes) -> bool:
    """
    Verify HMAC signature in artifact.

    Args:
        artifact: Artifact dict with hmac field
        secret_key: Secret key bytes

    Returns:
        True if HMAC valid, False otherwise
    """
    if "hmac" not in artifact:
        print("ERROR: Artifact missing hmac field")
        return False

    expected_hmac = artifact["hmac"]
    computed_hmac = compute_hmac(artifact, secret_key)

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_hmac, computed_hmac)


def main():
    parser = argparse.ArgumentParser(description="Validate consumer audit artifacts")
    parser.add_argument("--artifact", required=True, help="Path to consumer artifact JSON")
    parser.add_argument("--require-hmac", action="store_true", help="Require HMAC verification (POLICY_REQUIRE_HMAC)")
    parser.add_argument("--hmac-secret-file", help="Path to HMAC secret key file (or set HMAC_SECRET_KEY env)")
    args = parser.parse_args()

    artifact_path = Path(args.artifact)
    artifact = load_json(artifact_path)

    # Safety Net 1a: Schema validation (always required)
    print(f"Validating artifact: {artifact_path}")
    try:
        validate_against_schema(artifact, ARTIFACT_SCHEMA)
    except SystemExit as e:
        print(e)
        return 2

    # Safety Net 1b: HMAC verification (if policy requires it)
    if args.require_hmac:
        print("HMAC verification required by policy")

        # Get secret key from file or environment
        if args.hmac_secret_file:
            secret_key = Path(args.hmac_secret_file).read_bytes().strip()
        elif "HMAC_SECRET_KEY" in os.environ:
            secret_key = os.environ["HMAC_SECRET_KEY"].encode('utf-8')
        else:
            print("ERROR: HMAC required but no secret key provided")
            print("Set HMAC_SECRET_KEY env var or use --hmac-secret-file")
            return 2

        if not verify_hmac(artifact, secret_key):
            print("ERROR: HMAC verification failed - artifact may be tampered")
            return 2

        print("✓ HMAC verification passed")

    print(f"✓ Artifact validation complete: {artifact_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
