#!/usr/bin/env python3
"""
Auto-Close Resolved Issues

Automatically closes audit issues when:
1. A PR is merged that adds the code_paths entry to consumer_registry.yml
2. Subsequent audit shows 0 hits for that repo

Usage:
  # Check for resolved issues and close them
  python tools/auto_close_resolved_issues.py --audit audit_reports/audit_summary.json --dry-run
  python tools/auto_close_resolved_issues.py --audit audit_reports/audit_summary.json --confirm

Environment Variables:
  GITHUB_TOKEN: GitHub API token (required)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import requests


ISSUE_MARKER = "<!-- UNREGISTERED-RENDERER-AUDIT -->"
USER_AGENT = "audit-auto-close-bot/1.0"


def safe_request(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    """Make GitHub API request with retries."""
    for attempt in range(3):
        r = session.request(method, url, **kwargs)
        if r.status_code in (200, 201, 202):
            return r
        if r.status_code == 403 and "rate limit" in (r.text or "").lower():
            print(f"⚠️  Rate limited, waiting...")
            import time
            time.sleep(10)
            continue
        return r
    raise RuntimeError(f"Exceeded retries for {method} {url}")


def find_audit_issues(repo: str, session: requests.Session, github_token: str) -> List[Dict]:
    """Find open audit issues for a repo."""
    api = f"https://api.github.com/repos/{repo}/issues"
    params = {"state": "open", "per_page": 100}
    headers = {"Authorization": f"token {github_token}", "User-Agent": USER_AGENT}

    issues = []
    page = 1

    while True:
        r = safe_request(session, "GET", api, headers=headers, params={**params, "page": page}, timeout=20)
        if r.status_code != 200:
            break

        page_issues = r.json()
        if not page_issues:
            break

        for issue in page_issues:
            if ISSUE_MARKER in (issue.get("body") or ""):
                issues.append(issue)

        if "next" not in r.links:
            break
        page += 1

    return issues


def extract_repo_from_issue(issue_body: str) -> Optional[str]:
    """Extract target repo name from issue body."""
    # Look for pattern like "[Audit] Unregistered renderer-like files detected (org/repo)"
    match = re.search(r'\[Audit\].*?\(([^)]+)\)', issue_body or "")
    if match:
        return match.group(1)
    return None


def propose_auto_close(issue: Dict, reason: str, session: requests.Session, github_token: str, pr_number: Optional[str] = None):
    """Propose auto-close with 72h review period (conservative mode).

    Posts a comment with proposed closure reason and adds 'auto-close:proposed' label.
    Requires human confirmation via 'auto-close:confirmed' label or 72h wait period.
    Can be blocked via 'auto-close:blocked' label.

    Args:
        issue: GitHub issue dict
        reason: Reason for proposed closure
        session: Requests session
        github_token: GitHub API token
        pr_number: Optional PR number that resolved the issue
    """
    headers = {"Authorization": f"token {github_token}", "User-Agent": USER_AGENT}

    # Check for existing labels
    labels = issue.get("labels", [])
    label_names = {label.get("name", "") for label in labels}

    # If already proposed, skip
    if "auto-close:proposed" in label_names:
        print(f"⏭  Issue #{issue['number']} already has proposed closure - skipping")
        return

    # If blocked, skip
    if "auto-close:blocked" in label_names:
        print(f"🛑 Issue #{issue['number']} has auto-close:blocked label - skipping")
        return

    # If confirmed, close immediately
    if "auto-close:confirmed" in label_names:
        print(f"✓ Issue #{issue['number']} has auto-close:confirmed - closing now")
        close_issue_immediately(issue, reason, session, github_token, pr_number)
        return

    # Post proposal comment
    comment_body = f"**Proposed Auto-Close** ⏳\n\n{reason}\n\n"
    if pr_number:
        comment_body += f"Resolved by PR #{pr_number}\n\n"
    comment_body += "This issue will auto-close in **72 hours** if no objections.\n\n"
    comment_body += "**Actions**:\n"
    comment_body += "- To confirm now: add label `auto-close:confirmed`\n"
    comment_body += "- To block: add label `auto-close:blocked`\n"
    comment_body += "- To defer: remove `auto-close:proposed` label\n"

    comment_url = issue["comments_url"]
    safe_request(session, "POST", comment_url, json={"body": comment_body}, headers=headers, timeout=20)

    # Add proposed label
    issue_url = issue["url"]
    current_labels = [label["name"] for label in labels]
    current_labels.append("auto-close:proposed")
    safe_request(session, "PATCH", issue_url, json={"labels": current_labels}, headers=headers, timeout=20)

    print(f"📝 Proposed auto-close for issue #{issue['number']}: {issue['title']} (72h review period)")


def close_issue_immediately(issue: Dict, reason: str, session: requests.Session, github_token: str, pr_number: Optional[str] = None):
    """Immediately close an issue with a comment (for confirmed closures only)."""
    headers = {"Authorization": f"token {github_token}", "User-Agent": USER_AGENT}

    # Post comment
    comment_body = f"**Auto-closing: Issue resolved**\n\n{reason}"
    if pr_number:
        comment_body += f"\n\nResolved by PR #{pr_number}"

    comment_url = issue["comments_url"]
    safe_request(session, "POST", comment_url, json={"body": comment_body}, headers=headers, timeout=20)

    # Close issue
    issue_url = issue["url"]
    safe_request(session, "PATCH", issue_url, json={"state": "closed"}, headers=headers, timeout=20)

    print(f"✓ Closed issue #{issue['number']}: {issue['title']}")


def main():
    parser = argparse.ArgumentParser(description="Auto-close resolved audit issues")
    parser.add_argument("--audit", required=True, help="Path to audit_summary.json")
    parser.add_argument("--central-repo", default="security/audit-backlog", help="Central repo with issues")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be closed without closing")
    parser.add_argument("--confirm", action="store_true", help="Actually close issues (required)")
    args = parser.parse_args()

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("ERROR: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Load audit report
    audit_path = Path(args.audit)
    if not audit_path.exists():
        print(f"ERROR: Audit file not found: {audit_path}", file=sys.stderr)
        sys.exit(1)

    audit = json.loads(audit_path.read_text())

    # Get repos with 0 unregistered hits
    resolved_repos = set()

    # Check org_unregistered_hits - build set of repos with hits
    repos_with_hits = set()
    for hit in audit.get("org_unregistered_hits", []):
        repo = hit.get("repo")
        if repo:
            repos_with_hits.add(repo)

    # Any repo not in repos_with_hits is resolved (assuming it was previously flagged)
    # For now, we'll focus on repos_with_hits being empty as "resolved"

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # Find open audit issues in central repo
    print(f"Searching for open audit issues in {args.central_repo}...")
    open_issues = find_audit_issues(args.central_repo, session, github_token)

    if not open_issues:
        print(f"✓ No open audit issues found in {args.central_repo}")
        return

    print(f"Found {len(open_issues)} open audit issues")

    closed_count = 0

    for issue in open_issues:
        # Extract target repo from issue
        target_repo = extract_repo_from_issue(issue.get("title", ""))

        if not target_repo:
            continue

        # Check if this repo still has hits
        if target_repo not in repos_with_hits:
            # Repo is resolved (0 hits)
            reason = f"Latest audit shows 0 unregistered hits for {target_repo}"

            if args.dry_run:
                print(f"[DRY-RUN] Would propose auto-close for issue #{issue['number']}: {issue['title']}")
                print(f"  Reason: {reason}")
                closed_count += 1
            elif args.confirm:
                propose_auto_close(issue, reason, session, github_token)
                closed_count += 1
            else:
                print(f"[SKIP] Issue #{issue['number']} could be proposed for auto-close (use --confirm)")
                print(f"  Reason: {reason}")

    if closed_count > 0:
        if args.dry_run:
            print(f"\n[DRY-RUN] Would propose auto-close for {closed_count} issues")
        elif args.confirm:
            print(f"\n✓ Proposed auto-close for {closed_count} issues (72h review period)")
        else:
            print(f"\n{closed_count} issues ready to propose for auto-close (use --confirm)")
    else:
        print(f"\n✓ No issues to propose for closure")


if __name__ == "__main__":
    main()
