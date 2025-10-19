#!/usr/bin/env python3
"""
Permission fallback helper for GitHub issue creation.

Provides early permission check with deterministic fallback:
- Checks if token has issue-create permission
- If missing/unknown, saves artifact and posts Slack alert
- Returns True if permission OK, False if fallback executed

Usage:
    from tools.permission_fallback import ensure_issue_create_permissions

    ok = ensure_issue_create_permissions(central_repo, session, artifact_path)
    if not ok:
        print("Permission fallback executed")
        sys.exit(2)
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
import requests


def _get_authenticated_user_login(session: requests.Session) -> str | None:
    """
    Get the login of the authenticated user.

    Returns:
        Login string if successful, None if API call fails
    """
    try:
        resp = session.get("https://api.github.com/user", timeout=10)
        if resp.status_code == 200:
            return resp.json().get("login")
        return None
    except Exception as e:
        print(f"WARNING: Failed to get authenticated user: {e}", file=sys.stderr)
        return None


def _check_repo_write_permission(
    session: requests.Session,
    repo: str,
    login: str
) -> bool | None:
    """
    Check if user has write/admin permission to create issues in repo.

    Args:
        session: Authenticated requests session
        repo: Repository in format "owner/repo"
        login: GitHub username to check

    Returns:
        True if user has permission, False if no permission, None if unknown
    """
    try:
        # Check collaborator permission level
        url = f"https://api.github.com/repos/{repo}/collaborators/{login}/permission"
        resp = session.get(url, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            permission = data.get("permission", "")
            # write, admin, or maintain can create issues
            return permission in ["write", "admin", "maintain"]
        elif resp.status_code == 404:
            # User is not a collaborator
            return False
        else:
            print(f"WARNING: Permission check returned {resp.status_code}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"WARNING: Permission check failed: {e}", file=sys.stderr)
        return None


def _redact_sensitive_fields(artifact: dict) -> dict:
    """
    Redact sensitive fields from artifact before fallback storage.

    Removes full code snippets while keeping metadata for triage.

    Args:
        artifact: Artifact dict

    Returns:
        Redacted artifact with snippets removed
    """
    redacted = artifact.copy()

    # Redact full snippets from hits
    if "org_unregistered_hits" in redacted:
        for hit in redacted["org_unregistered_hits"]:
            if "snippet" in hit:
                hit["snippet"] = "<REDACTED>"  # Keep structure, remove content

    return redacted


def _save_artifact_fallback(artifact_path: str) -> Path:
    """
    Save artifact to fallback directory with timestamp.

    Uses atomic write (tmp + rename) and redacts sensitive snippets.

    Args:
        artifact_path: Path to original artifact

    Returns:
        Path to saved fallback artifact
    """
    fallback_dir = Path("adversarial_reports")
    fallback_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    fallback_filename = f"fallback_{timestamp}.json"
    fallback_path = fallback_dir / fallback_filename

    # Load and redact artifact
    if Path(artifact_path).exists():
        content = Path(artifact_path).read_text()
        try:
            artifact = json.loads(content)
            # Redact sensitive fields
            redacted = _redact_sensitive_fields(artifact)
            redacted_content = json.dumps(redacted, indent=2)
        except json.JSONDecodeError:
            # If not valid JSON, save as-is (shouldn't happen)
            redacted_content = content
    else:
        # Create empty fallback marker
        redacted_content = json.dumps({
            "error": "Original artifact not found",
            "artifact_path": artifact_path,
            "timestamp": timestamp
        })

    # Atomic write: tmp file + rename
    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=fallback_dir,
        delete=False,
        suffix=".tmp"
    ) as tmp:
        tmp.write(redacted_content)
        tmp.flush()
        os.fsync(tmp.fileno())  # Force write to disk
        tmp_path = Path(tmp.name)

    # Atomic rename
    tmp_path.rename(fallback_path)

    print(f"Artifact saved to fallback (redacted, atomic): {fallback_path}")
    return fallback_path


def _post_slack_alert(
    fallback_path: Path,
    central_repo: str,
    slack_webhook: str
) -> bool:
    """
    Post Slack alert about permission failure.

    Args:
        fallback_path: Path to fallback artifact
        central_repo: Repository that was inaccessible
        slack_webhook: Slack webhook URL

    Returns:
        True if alert posted successfully, False otherwise
    """
    try:
        message = {
            "text": f":warning: GitHub Permission Failure - Issue Creation Blocked",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*GitHub Permission Failure*\n\n"
                                f"Unable to create issues in repository: `{central_repo}`\n"
                                f"Artifact saved to: `{fallback_path}`\n\n"
                                f"*Action Required*: Verify GitHub token has write permission to {central_repo}"
                    }
                }
            ]
        }

        resp = requests.post(slack_webhook, json=message, timeout=10)
        if resp.status_code == 200:
            print(f"Slack alert posted successfully")
            return True
        else:
            print(f"WARNING: Slack alert failed ({resp.status_code})", file=sys.stderr)
            return False
    except Exception as e:
        print(f"WARNING: Failed to post Slack alert: {e}", file=sys.stderr)
        return False


def ensure_issue_create_permissions(
    central_repo: str,
    session: requests.Session,
    artifact_path: str
) -> bool:
    """
    Ensure we have permission to create issues in central_repo.

    If permission is missing or unknown, saves artifact to fallback path
    and posts Slack alert (if SLACK_WEBHOOK env var set).

    Args:
        central_repo: Repository in format "owner/repo"
        session: Authenticated requests session with GitHub token
        artifact_path: Path to audit artifact

    Returns:
        True if permission OK, False if fallback executed
    """
    # Get authenticated user login
    login = _get_authenticated_user_login(session)
    if not login:
        print("ERROR: Unable to determine authenticated user", file=sys.stderr)
        fallback_path = _save_artifact_fallback(artifact_path)
        slack_webhook = os.environ.get("SLACK_WEBHOOK")
        if slack_webhook:
            _post_slack_alert(fallback_path, central_repo, slack_webhook)
        return False

    # Check repository permission
    has_permission = _check_repo_write_permission(session, central_repo, login)

    if has_permission is True:
        print(f"✓ User '{login}' has issue-create permission in {central_repo}")
        return True

    # Permission missing or unknown - execute fallback
    if has_permission is False:
        print(f"ERROR: User '{login}' lacks write permission to {central_repo}", file=sys.stderr)
    else:
        print(f"ERROR: Unable to verify permission for '{login}' in {central_repo}", file=sys.stderr)

    fallback_path = _save_artifact_fallback(artifact_path)
    slack_webhook = os.environ.get("SLACK_WEBHOOK")
    if slack_webhook:
        _post_slack_alert(fallback_path, central_repo, slack_webhook)

    return False


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description="Check GitHub issue-create permissions")
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument("--artifact", required=True, help="Path to artifact")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env)")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: No GitHub token provided", file=sys.stderr)
        sys.exit(1)

    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    })

    ok = ensure_issue_create_permissions(args.repo, session, args.artifact)
    sys.exit(0 if ok else 2)
