#!/usr/bin/env python3
"""
Baseline Signing Tool with GPG

Purpose: Sign baseline JSON with GPG for audit trail
Source: PLAN_CLOSING_IMPLEMENTATION_extended_6.md (Part 6, Action 6)

Creates GPG-signed baseline with:
  - SHA256 hash of baseline content
  - GPG signature from authorized signer
  - Signed timestamp
  - Signer email

Usage:
  # Sign baseline
  python tools/sign_baseline.py \
    --baseline baselines/metrics_baseline_v1.json \
    --signer sre-lead@example.com

  # Verify signature (read-only)
  python tools/sign_baseline.py \
    --verify baselines/metrics_baseline_v1_signed.json
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def calculate_sha256(content: str) -> str:
    """Calculate SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def gpg_sign(content: str, signer_email: str) -> str:
    """
    Sign content with GPG.

    Args:
        content: Content to sign
        signer_email: GPG key email/ID

    Returns:
        GPG armored signature

    Raises:
        Exception if GPG signing fails
    """
    gpg_cmd = ["gpg", "--clearsign", "--armor", "--local-user", signer_email, "-"]

    try:
        result = subprocess.run(
            gpg_cmd,
            input=content.encode(),
            capture_output=True,
            timeout=30
        )

        if result.returncode != 0:
            raise Exception(f"GPG signing failed: {result.stderr.decode()}")

        return result.stdout.decode()

    except subprocess.TimeoutExpired:
        raise Exception("GPG signing timed out after 30 seconds")
    except FileNotFoundError:
        raise Exception("GPG not found. Install gpg: apt-get install gnupg or brew install gnupg")
    except Exception as e:
        raise Exception(f"GPG signing error: {e}")


def gpg_verify(signature: str) -> Dict[str, Any]:
    """
    Verify GPG signature.

    Args:
        signature: GPG armored signature

    Returns:
        Dict with verification status
    """
    gpg_cmd = ["gpg", "--verify"]

    try:
        result = subprocess.run(
            gpg_cmd,
            input=signature.encode(),
            capture_output=True,
            timeout=30
        )

        # GPG writes verification status to stderr
        stderr = result.stderr.decode()

        # Check for good signature
        good_sig = "Good signature" in stderr
        signer = None

        if good_sig:
            # Extract signer from stderr
            for line in stderr.split('\n'):
                if "Good signature from" in line:
                    # Parse: Good signature from "Name <email>"
                    parts = line.split('"')
                    if len(parts) >= 2:
                        signer = parts[1]
                    break

        return {
            "valid": good_sig,
            "signer": signer,
            "gpg_output": stderr
        }

    except subprocess.TimeoutExpired:
        return {"valid": False, "error": "GPG verification timed out"}
    except FileNotFoundError:
        return {"valid": False, "error": "GPG not found"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def sign_baseline(baseline_path: Path, signer_email: str, output_path: Path = None) -> int:
    """
    Sign baseline JSON with GPG.

    Args:
        baseline_path: Path to baseline JSON
        signer_email: GPG signer email
        output_path: Output path (defaults to <baseline>_signed.json)

    Returns:
        0 on success, 1 on failure
    """
    if not baseline_path.exists():
        print(f"ERROR: Baseline not found: {baseline_path}")
        return 1

    # Read baseline
    try:
        baseline_text = baseline_path.read_text()
        baseline = json.loads(baseline_text)
    except Exception as e:
        print(f"ERROR: Failed to read baseline: {e}")
        return 1

    # Calculate SHA256 hash
    print(f"Calculating SHA256 hash...")
    sha256 = calculate_sha256(baseline_text)
    print(f"SHA256: {sha256}")

    # GPG sign
    print(f"Signing with GPG (signer: {signer_email})...")
    try:
        signature = gpg_sign(baseline_text, signer_email)
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    print(f"✅ GPG signature created")

    # Add signature to baseline
    baseline["signature"] = {
        "signer": signer_email,
        "signed_at": datetime.utcnow().isoformat() + "Z",
        "signature_sha256": sha256,
        "gpg_signature": signature
    }

    # Write signed baseline
    if output_path is None:
        output_path = baseline_path.parent / f"{baseline_path.stem}_signed.json"

    output_path.write_text(json.dumps(baseline, indent=2))
    print(f"✅ Signed baseline written to {output_path}")

    # Verify signature immediately
    print()
    print("Verifying signature...")
    verify_result = gpg_verify(signature)

    if verify_result["valid"]:
        print(f"✅ Signature valid")
        print(f"   Signer: {verify_result['signer']}")
        return 0
    else:
        print(f"❌ Signature verification failed")
        print(f"   Error: {verify_result.get('error', 'Unknown error')}")
        return 1


def verify_signed_baseline(signed_baseline_path: Path) -> int:
    """
    Verify GPG signature in signed baseline.

    Args:
        signed_baseline_path: Path to signed baseline JSON

    Returns:
        0 if valid, 1 if invalid
    """
    if not signed_baseline_path.exists():
        print(f"ERROR: Signed baseline not found: {signed_baseline_path}")
        return 1

    try:
        baseline = json.loads(signed_baseline_path.read_text())
    except Exception as e:
        print(f"ERROR: Failed to read signed baseline: {e}")
        return 1

    # Check signature field exists
    if "signature" not in baseline:
        print(f"ERROR: No signature field in baseline")
        return 1

    signature_data = baseline["signature"]
    gpg_signature = signature_data.get("gpg_signature")

    if not gpg_signature:
        print(f"ERROR: No GPG signature in baseline")
        return 1

    print(f"Verifying GPG signature...")
    print(f"Signer (claimed): {signature_data.get('signer')}")
    print(f"Signed at: {signature_data.get('signed_at')}")
    print(f"SHA256: {signature_data.get('signature_sha256')}")

    # Verify signature
    verify_result = gpg_verify(gpg_signature)

    if verify_result["valid"]:
        print()
        print(f"✅ Signature VALID")
        print(f"   Verified signer: {verify_result['signer']}")
        return 0
    else:
        print()
        print(f"❌ Signature INVALID")
        print(f"   Error: {verify_result.get('error', 'Unknown error')}")
        if verify_result.get("gpg_output"):
            print()
            print("GPG output:")
            print(verify_result["gpg_output"])
        return 1


def main():
    parser = argparse.ArgumentParser(description="Sign baseline with GPG for audit trail")
    parser.add_argument("--baseline", help="Baseline JSON path to sign")
    parser.add_argument("--signer", help="GPG signer email")
    parser.add_argument("--output", help="Output path (default: <baseline>_signed.json)")
    parser.add_argument("--verify", help="Verify signed baseline (read-only)")

    args = parser.parse_args()

    print("=" * 60)
    print("BASELINE GPG SIGNING TOOL")
    print("=" * 60)
    print()

    # Verify mode (read-only)
    if args.verify:
        signed_baseline_path = Path(args.verify)
        result = verify_signed_baseline(signed_baseline_path)
        print()
        print("=" * 60)
        return result

    # Sign mode
    if not args.baseline:
        print("ERROR: --baseline required (or use --verify for verification)")
        parser.print_help()
        return 1

    if not args.signer:
        print("ERROR: --signer required")
        parser.print_help()
        return 1

    baseline_path = Path(args.baseline)
    output_path = Path(args.output) if args.output else None

    result = sign_baseline(baseline_path, args.signer, output_path)

    print()
    print("=" * 60)
    if result == 0:
        print("Next steps:")
        print("  1. Verify signature: python tools/sign_baseline.py --verify <signed_baseline>")
        print("  2. Commit signed baseline to repository")
        print("  3. Reference in audit_greenlight.py (baselines/metrics_baseline_v1_signed.json)")
        print("=" * 60)

    return result


if __name__ == "__main__":
    sys.exit(main())
