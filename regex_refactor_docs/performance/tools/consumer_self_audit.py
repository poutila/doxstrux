#!/usr/bin/env python3
"""
Enhanced consumer repo self-audit script for renderer discovery with provenance tracking.

Runs in consumer CI to discover renderer-like files and publish artifact with:
- Full provenance tracking (repo, branch, commit, timestamp)
- Optional HMAC signing for authenticity
- Compliance with artifact_schema.json

Usage:
  python tools/consumer_self_audit.py --out consumer_audit.json
  python tools/consumer_self_audit.py --out consumer_audit.json --sign

Environment Variables:
  CONSUMER_ARTIFACT_HMAC_KEY: Base64-encoded shared secret for HMAC signing (required if --sign)
  GITHUB_ACTOR: GitHub username (optional, for provenance)
  GITHUB_RUN_ID: GitHub Actions run ID (optional, for provenance)
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional


TOOL_VERSION = "consumer_self_audit/1.1"

# Curated high-confidence patterns (FP rate <10%)
# See renderer_patterns.yml for full documentation
RENDERER_PATTERNS = [
    "jinja2.Template",
    "django.template",
    "render_to_string(",
    "renderToString(",
    ".render(",  # Monitor: may need removal if FP rate >10%
]


def get_git_info() -> Dict[str, Optional[str]]:
    """Get git repository information (repo, branch, commit)."""
    info = {
        "repo": None,
        "branch": None,
        "commit": None
    }

    try:
        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()

        # Get current commit (full SHA)
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()

        # Get repo name from remote origin
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            origin = result.stdout.strip()
            if origin.startswith("git@"):
                # git@github.com:org/repo.git -> org/repo
                info["repo"] = origin.split(":", 1)[1].rsplit(".git", 1)[0]
            elif origin.startswith("https://") or origin.startswith("http://"):
                # https://github.com/org/repo.git -> org/repo
                parts = origin.rstrip("/").split("/")
                if len(parts) >= 2:
                    info["repo"] = "/".join(parts[-2:]).rsplit(".git", 1)[0]

    except Exception as e:
        print(f"Warning: Failed to get git info: {e}")

    return info


def discover_renderers(repo_path: Path) -> List[Dict]:
    """Discover renderer-like files in repo with line numbers and snippets."""
    hits = []

    for pattern in RENDERER_PATTERNS:
        try:
            # Use git grep for speed and accuracy
            result = subprocess.run(
                ["git", "grep", "-n", pattern],  # -n includes line numbers
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue

                    # Parse git grep output: "path:line:content"
                    parts = line.split(":", 2)
                    if len(parts) < 3:
                        continue

                    path, line_num, content = parts

                    # Truncate snippet to 400 chars max (schema limit)
                    snippet = content.strip()[:400]

                    hits.append({
                        "path": path,
                        "pattern": pattern,
                        "snippet": snippet,
                        "line": int(line_num)
                    })

        except Exception as e:
            print(f"Warning: grep failed for pattern {pattern}: {e}")

    return hits


def compute_hmac_signature(artifact: dict, secret_key: bytes) -> str:
    """Compute HMAC-SHA256 signature of artifact."""
    # Canonical JSON representation (sorted keys, no whitespace)
    canonical = json.dumps(artifact, sort_keys=True, separators=(',', ':'))

    # Compute HMAC
    signature = hmac.new(secret_key, canonical.encode('utf-8'), hashlib.sha256)

    return base64.b64encode(signature.digest()).decode('ascii')


def main():
    parser = argparse.ArgumentParser(description="Consumer self-audit with provenance tracking")
    parser.add_argument("--out", "-o", default="consumer_audit.json", help="Output artifact file")
    parser.add_argument("--repo-path", default=".", help="Path to repo root")
    parser.add_argument("--sign", action="store_true", help="Sign artifact with HMAC (requires CONSUMER_ARTIFACT_HMAC_KEY env var)")
    args = parser.parse_args()

    repo_path = Path(args.repo_path)

    # Get git information
    git_info = get_git_info()

    if not git_info["repo"]:
        print("ERROR: Could not determine repo name from git remote", file=sys.stderr)
        sys.exit(1)

    if not git_info["commit"]:
        print("ERROR: Could not determine current commit SHA", file=sys.stderr)
        sys.exit(1)

    # Discover renderer hits
    hits = discover_renderers(repo_path)

    # Build artifact
    artifact = {
        "repo": git_info["repo"],
        "branch": git_info["branch"],
        "commit": git_info["commit"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_version": TOOL_VERSION,
        "hits": hits
    }

    # Add optional provenance fields from CI environment
    github_actor = os.environ.get("GITHUB_ACTOR")
    if github_actor:
        artifact["uploader"] = github_actor

    github_run_id = os.environ.get("GITHUB_RUN_ID")
    if github_run_id:
        artifact["uploader_ci_run_id"] = github_run_id

    # Sign artifact if requested
    if args.sign:
        hmac_key_b64 = os.environ.get("CONSUMER_ARTIFACT_HMAC_KEY")
        if not hmac_key_b64:
            print("ERROR: CONSUMER_ARTIFACT_HMAC_KEY environment variable not set", file=sys.stderr)
            print("       Cannot sign artifact without HMAC key", file=sys.stderr)
            sys.exit(1)

        try:
            hmac_key = base64.b64decode(hmac_key_b64)
        except Exception as e:
            print(f"ERROR: Failed to decode HMAC key from base64: {e}", file=sys.stderr)
            sys.exit(1)

        artifact["hmac"] = compute_hmac_signature(artifact, hmac_key)
        print(f"✓ Artifact signed with HMAC")

    # Write artifact to file
    out_path = Path(args.out)
    out_path.write_text(json.dumps(artifact, indent=2))

    # Print summary
    print(f"✓ Self-audit complete")
    print(f"  Repo: {artifact['repo']}")
    print(f"  Commit: {artifact['commit'][:8]}")
    print(f"  Branch: {artifact['branch']}")
    print(f"  Hits: {len(hits)}")
    print(f"  Artifact: {out_path}")


if __name__ == "__main__":
    import sys
    main()
