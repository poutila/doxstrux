#!/usr/bin/env python3
"""
Create or update GitHub issues for unregistered renderer hits discovered by tools/audit_greenlight.py

Improvements over original:
- Computes and stores an AUDIT-HASH to detect changes and update existing issues (idempotent).
- If an issue already exists, posts a comment with the delta instead of skipping.
- Creates a private Gist with the full per-repo audit artifact when possible and links it in the issue.
- Applies severity labeling heuristics and suggestions for assignees based on consumer_registry.yml (if present).
- Uses a safe_request wrapper that respects rate-limits and retries with backoff.
- Supports --dry-run and --confirm flags.

Usage:
  export GITHUB_TOKEN=ghp_xxx
  python tools/create_issues_for_unregistered_hits.py --audit adversarial_reports/audit_summary.json --dry-run
  python tools/create_issues_for_unregistered_hits.py --audit adversarial_reports/audit_summary.json --confirm --label security --assignees alice,bob

Notes:
- The script will create issues in the target repo (requires appropriate repo scope).
- Alternate flow: run with --create-in-central to push issues into a central security backlog repo.
"""

from __future__ import annotations
import argparse
import json
import os
import time
import textwrap
import hashlib
import logging
import requests
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

ISSUE_MARKER = "<!-- UNREGISTERED-RENDERER-AUDIT -->"
AUDIT_HASH_MARKER = "<!-- AUDIT-HASH: {} -->"
USER_AGENT = "audit-issue-bot/1.1"
TOOL_VERSION = "1.2.0"  # Increment when making changes to issue format or logic
MAX_RETRIES = 6
BACKOFF_BASE = 2.0
MAX_ISSUES_PER_RUN = 10  # Cap per run to prevent alert storms
GITHUB_QUOTA_THRESHOLD = 500  # Trigger digest mode when quota falls below this

# Prometheus-compatible metrics (exported to file for node_exporter)
# In production, replace with prometheus_client library
class SimpleMetric:
    """Simple metric collector for quota tracking (replace with prometheus_client in production)."""
    def __init__(self, name: str):
        self.name = name
        self.value = 0

    def set(self, value: int):
        self.value = value
        # Write to textfile for node_exporter scraping
        metrics_dir = Path(".metrics")
        metrics_dir.mkdir(exist_ok=True)
        (metrics_dir / f"{self.name}.prom").write_text(f"# TYPE {self.name} gauge\n{self.name} {value}\n")

github_quota_gauge = SimpleMetric("github_api_quota_remaining")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("issue_automation.log"),
        logging.StreamHandler()
    ]
)


def load_audit(audit_path: Path) -> dict:
    if not audit_path.exists():
        raise SystemExit(f"audit file not found: {audit_path}")
    return json.loads(audit_path.read_text())


def group_hits(audit_json: dict) -> Dict[str, List[dict]]:
    groups = defaultdict(list)
    for hit in audit_json.get("org_unregistered_hits", []) or []:
        repo = hit.get("repo")
        path = hit.get("path")
        patt = hit.get("pattern")
        groups[repo].append({"path": path, "pattern": patt})
    for hit in audit_json.get("renderer_unregistered_local", []) or []:
        groups["<local-repo>"].append({"path": hit.get("path"), "pattern": hit.get("pattern")})
    return groups


def suggest_code_paths_from_paths(paths: List[str], top_n: int = 3) -> List[str]:
    candidates = []
    for p in paths:
        p = p.strip("/")
        parts = p.split("/")
        if len(parts) <= 1:
            candidates.append(parts[0])
        else:
            candidates.append("/".join(parts[:-1]))
            if len(parts) > 2:
                candidates.append("/".join(parts[:-2]))
            candidates.append(parts[0])
    c = Counter(candidates)
    out = []
    for k, _ in c.most_common():
        if k and k not in out:
            out.append(k)
        if len(out) >= top_n:
            break
    return out


def compute_hits_hash(hits: List[dict]) -> str:
    s = "\n".join(sorted(h.get("path", "") for h in hits))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def extract_audit_hash(issue_body: str) -> Optional[str]:
    import re
    m = re.search(r"<!--\s*AUDIT-HASH:\s*([0-9a-fA-F]+)\s*-->", issue_body)
    return m.group(1) if m else None


def check_issue_create_permission(repo: str, session: requests.Session, token: str) -> bool:
    """Check if token has issue create permission via quick API check.

    Args:
        repo: Repository full name (org/repo)
        session: Requests session
        token: GitHub API token

    Returns:
        True if token has issue create permission, False otherwise
    """
    api = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"token {token}", "User-Agent": USER_AGENT}
    try:
        r = session.get(api, headers=headers, timeout=10)
        if r.status_code != 200:
            logging.warning(f"Failed to check permissions for {repo}: HTTP {r.status_code}")
            return False
        repo_data = r.json()
        permissions = repo_data.get("permissions", {})
        # push permission implies issue create permission
        has_permission = permissions.get("push", False)
        if not has_permission:
            logging.warning(f"Token lacks issue create permission for {repo} (push: {permissions.get('push', False)})")
        return has_permission
    except Exception as e:
        logging.error(f"Error checking permissions for {repo}: {e}")
        return False


def safe_request(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    for attempt in range(1, MAX_RETRIES + 1):
        r = session.request(method, url, **kwargs)

        # Export quota metric (Prometheus)
        if "X-RateLimit-Remaining" in r.headers:
            remaining = int(r.headers.get("X-RateLimit-Remaining", 0))
            github_quota_gauge.set(remaining)

            # Quota guard: warn when quota falls below threshold
            if remaining < GITHUB_QUOTA_THRESHOLD:
                logging.warning(f"GitHub API quota low: {remaining} remaining (threshold: {GITHUB_QUOTA_THRESHOLD})")
                logging.warning("Consider switching to digest mode or reducing scan frequency")

        if r.status_code in (200, 201):
            return r
        if r.status_code == 202:
            # accepted - treat as ok
            return r
        # rate-limit handling
        if r.status_code == 403 and "rate limit" in (r.text or "").lower():
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + (BACKOFF_BASE ** attempt)))
            sleep_for = max(5, reset - time.time() + 2)
            logging.info(f"Rate limited, sleeping {sleep_for}s until reset")
            time.sleep(sleep_for)
            continue
        # server error backoff
        if 500 <= r.status_code < 600:
            time.sleep(BACKOFF_BASE ** attempt)
            continue
        # otherwise return (client error) - caller will decide
        return r
    raise RuntimeError(f"Exceeded retries for {method} {url}")


def find_existing_issue(repo_full_name: str, session: requests.Session) -> Optional[dict]:
    api = f"https://api.github.com/repos/{repo_full_name}/issues"
    params = {"state": "open", "per_page": 100}
    page = 1
    headers = {"Authorization": f"token {os.environ.get('GITHUB_TOKEN','')}", "User-Agent": USER_AGENT}
    while True:
        r = safe_request(session, "GET", api, headers=headers, params={**params, "page": page}, timeout=20)
        if r.status_code != 200:
            # cannot fetch issues - return None to allow creation attempt to proceed
            return None
        issues = r.json()
        if not issues:
            return None
        for it in issues:
            if ISSUE_MARKER in (it.get("body") or ""):
                # include comments_url for convenience
                return it
        if "next" not in r.links:
            break
        page += 1
    return None


def create_gist(session: requests.Session, filename: str, content: str, public: bool = False) -> Optional[str]:
    api = "https://api.github.com/gists"
    payload = {"public": public, "files": {filename: {"content": content}}, "description": "Audit artifact for unregistered renderer hits"}
    headers = {"Authorization": f"token {os.environ.get('GITHUB_TOKEN','')}", "User-Agent": USER_AGENT}
    try:
        r = safe_request(session, "POST", api, json=payload, headers=headers, timeout=20)
        if r.status_code in (200, 201):
            return r.json().get("html_url")
    except Exception as e:
        logging.warning(f"Failed to create gist: {e}")
    return None


def create_issue(repo_full_name: str, title: str, body: str, session: requests.Session, labels: List[str] = None, assignees: List[str] = None) -> Optional[dict]:
    api = f"https://api.github.com/repos/{repo_full_name}/issues"
    payload: Dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    if assignees:
        payload["assignees"] = assignees
    headers = {"Authorization": f"token {os.environ.get('GITHUB_TOKEN','')}", "User-Agent": USER_AGENT}
    r = safe_request(session, "POST", api, json=payload, headers=headers, timeout=20)
    if r.status_code in (200, 201):
        return r.json()
    return None


def post_comment(issue_comments_url: str, body: str, session: requests.Session) -> bool:
    headers = {"Authorization": f"token {os.environ.get('GITHUB_TOKEN','')}", "User-Agent": USER_AGENT}
    r = safe_request(session, "POST", issue_comments_url, json={"body": body}, headers=headers, timeout=20)
    return r.status_code in (200, 201)


def load_consumer_registry(cfg_path: Path) -> dict:
    try:
        import yaml
    except Exception:
        return {}
    if not cfg_path.exists():
        return {}
    return yaml.safe_load(cfg_path.read_text()) or {}


def build_issue_body(repo: str, hits: List[dict], gist_url: Optional[str], suggested_yaml: str, audit_path: Path, severity: str, audit_hash: str) -> str:
    paths = [h["path"] for h in hits if h.get("path")]
    patterns = sorted(set(h.get("pattern") for h in hits if h.get("pattern")))
    snippet_lines = []
    for h in hits[:5]:  # Max 5 files in body
        snippet_lines.append(f"- `{h.get('path')}` (pattern: `{h.get('pattern')}`)")
    if len(hits) > 5:
        snippet_lines.append(f"... and {len(hits) - 5} more (see gist)")
    snippet = "\n".join(snippet_lines)
    gist_line = f"\n\nFull artifact (private gist): {gist_url}\n" if gist_url else "\n\nFull artifact attached to repo artifacts or available to security.\n"
    body = f"""{ISSUE_MARKER}
<!-- AUDIT-HASH: {audit_hash} -->
# Security: Unregistered renderer-like files detected ({severity})

The automated parser audit detected the following files which appear to render templates/metadata and are not registered in `consumer_registry.yml` nor covered by `audit_exceptions.yml`.

**Offending files**
{snippet}

**Suggested `code_paths` entries**
```yaml
code_paths:
{suggested_yaml}
```

{gist_line}**Audit report**: `{audit_path}`

## Recommended actions
- If this repo intentionally renders metadata, add the appropriate `code_paths` and a consumer-level SSTI litmus test.
- If these are tests/examples, add to `audit_exceptions.yml` with an approver and expiry.
- If accidental, fix to sanitize/escape metadata before rendering.

## Triage checklist
- [ ] Confirm owner and plan
- [ ] Apply registry change or fix code
- [ ] Run `tools/probe_consumers.py` in staging to ensure no reflection

"""
    return body


def determine_severity(hits: List[dict]) -> str:
    high_patterns = {"jinja2.Template", "django.template", "render_to_string(", "renderToString("}
    for h in hits:
        if any(p in (h.get("pattern") or "") for p in high_patterns):
            return "high"
    return "medium"


def create_digest_issue(groups: Dict[str, List[dict]], session: requests.Session, args, audit_path: Path) -> None:
    """Create single digest issue for multiple repos with provenance metadata."""
    total_repos = len(groups)
    total_hits = sum(len(hits) for hits in groups.values())
    logging.info(f"Creating digest issue for {total_repos} repos (exceeds limit {MAX_ISSUES_PER_RUN})")

    # Provenance metadata
    timestamp = datetime.now(timezone.utc).isoformat()
    run_id = os.environ.get("GITHUB_RUN_ID", "local")

    body_sections = [ISSUE_MARKER, "\n# Audit Digest: Multiple repos with unregistered renderers\n\n"]

    # Provenance section
    body_sections.append("## Provenance\n\n")
    body_sections.append(f"- **Audit Run**: {timestamp}\n")
    body_sections.append(f"- **Tool Version**: {TOOL_VERSION}\n")
    body_sections.append(f"- **Run ID**: {run_id}\n")
    body_sections.append(f"- **Scan Count**: {total_repos} repos scanned\n")
    body_sections.append(f"- **Total Hits**: {total_hits} unregistered files\n")
    body_sections.append(f"- **Audit Report**: `{audit_path}`\n\n")

    body_sections.append("---\n\n")

    # Sort repos by hit count (descending) for prioritization
    sorted_repos = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)

    for repo, hits in sorted_repos:
        severity = determine_severity(hits)
        body_sections.append(f"## {repo} ({severity})\n")
        body_sections.append(f"**Hits**: {len(hits)}\n\n")
        for h in hits[:3]:
            body_sections.append(f"- `{h.get('path')}` (pattern: `{h.get('pattern')}`)\n")
        if len(hits) > 3:
            body_sections.append(f"... and {len(hits) - 3} more\n")
        body_sections.append("\n")

    body = "".join(body_sections)
    labels = ["security/digest", "triage"]

    created = create_issue(args.central_repo,
                          f"[Audit Digest] {len(groups)} repos with unregistered renderers",
                          body, session, labels=labels)
    if created:
        logging.info(f"Created digest issue: {created.get('html_url')}")
    else:
        logging.error("Failed to create digest issue")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", "-a", default="adversarial_reports/audit_summary.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--label", help="Label(s) to add (comma separated)")
    parser.add_argument("--assignees", help="Comma-separated GitHub usernames")
    parser.add_argument("--confirm", action="store_true", help="Actually create/update issues (required)")
    parser.add_argument("--central-repo", default="security/audit-backlog", help="Central repo for issues (org/repo, default: security/audit-backlog)")
    parser.add_argument("--update-existing", action="store_true", default=True, help="Update existing issues if hits changed")
    parser.add_argument("--no-update", dest="update_existing", action="store_false", help="Skip updating existing issues")
    args = parser.parse_args()

    audit_path = Path(args.audit)
    audit_json = load_audit(audit_path)
    groups = group_hits(audit_json)
    if not groups:
        logging.info("No unregistered hits found. Nothing to do.")
        return

    token = os.environ.get("GITHUB_TOKEN")
    if not token and not args.dry_run:
        raise SystemExit("GITHUB_TOKEN not set - required to create issues (or run --dry-run)")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # Check permissions before attempting issue creation (fail-fast with graceful fallback)
    if not args.dry_run and args.confirm:
        if not check_issue_create_permission(args.central_repo, session, token):
            logging.error(f"PERMISSIONS CHECK FAILED: Token lacks issue create permission for {args.central_repo}")
            logging.info("Falling back to artifact upload for manual triage")
            # Upload audit artifact to GitHub Actions artifacts or local file
            artifact_dir = Path("adversarial_reports")
            artifact_dir.mkdir(exist_ok=True)
            artifact_path = artifact_dir / "audit_summary_failed_permissions.json"
            artifact_path.write_text(json.dumps(audit_json, indent=2))
            logging.info(f"Audit artifact saved to {artifact_path}")
            logging.info("MANUAL ACTION REQUIRED: Grant issue create permission or triage manually from artifact")
            # Exit gracefully with non-zero code to signal failure
            raise SystemExit(1)

    registry = load_consumer_registry(Path("consumer_registry.yml"))
    # labels and assignees from args
    label_list = [l.strip() for l in (args.label or "").split(",") if l.strip()]
    assignees = [a.strip() for a in (args.assignees or "").split(",") if a.strip()]

    # Check if hit count exceeds cap
    if len(groups) > MAX_ISSUES_PER_RUN:
        logging.warning(f"Hit count ({len(groups)}) exceeds limit ({MAX_ISSUES_PER_RUN})")
        create_digest_issue(groups, session, args, audit_path)
        return

    for repo, hits in groups.items():
        if not hits:
            continue
        if repo == "<local-repo>":
            # resolve local repo name from git remote
            repo_full_name = "<local>"
            try:
                import subprocess
                out = subprocess.run(["git", "config", "--get", "remote.origin.url"], stdout=subprocess.PIPE, text=True, check=False)
                origin = (out.stdout or "").strip()
                if origin.startswith("git@"):
                    repo_full_name = origin.split(":", 1)[1].rsplit(".git", 1)[0]
                elif origin.startswith("https://") or origin.startswith("http://"):
                    repo_full_name = "/".join(origin.rstrip("/").split("/")[-2:]).rsplit(".git", 1)[0]
            except Exception:
                pass
        else:
            repo_full_name = repo

        logging.info(f"Processing repo: {repo_full_name} ({len(hits)} hits)")
        # compute hash and suggested code_paths
        audit_hash = compute_hits_hash(hits)
        suggested = suggest_code_paths_from_paths([h["path"] for h in hits if h.get("path")], top_n=4)
        suggested_yaml = "\n".join(f'  - "{s}"' for s in suggested)
        severity = determine_severity(hits)

        # prepare gist with per-repo portion of audit if token present
        gist_url = None
        if token:
            try:
                per_repo_json = {"repo": repo_full_name, "hits": hits}
                gist_url = create_gist(session, f"audit_{repo_full_name.replace('/', '_')}.json", json.dumps(per_repo_json, indent=2), public=False)
            except Exception as e:
                logging.warning(f"Could not create gist: {e}")

        title = f"[Audit] Unregistered renderer-like files detected ({repo_full_name})"
        body = build_issue_body(repo_full_name, hits, gist_url, suggested_yaml, audit_path, severity, audit_hash)
        if args.dry_run:
            logging.info(f"Dry-run: would create/update issue for {repo_full_name}")
            logging.info(f"Title: {title}")
            logging.info(f"Suggested code_paths: {suggested}")
            continue

        existing = None
        if token and repo_full_name != "<local>":
            existing = find_existing_issue(repo_full_name, session)

        if existing:
            if not args.update_existing:
                logging.info("Existing issue found, skipping (--no-update)")
                continue
            old_hash = extract_audit_hash(existing.get("body") or "")
            if old_hash == audit_hash:
                logging.info(f"No changes since last issue (hash match: {audit_hash}). Skipping.")
                continue
            # post comment with delta and update body by adding new hash comment
            comment = f"Automated update: new audit found. Previous hash: {old_hash or '<none>'}, new: {audit_hash}\n\nFiles:\n"
            comment += "\n".join(f"- `{h['path']}` (pattern: `{h['pattern']}`)" for h in hits)
            success = post_comment(existing.get("comments_url"), comment, session)
            if success:
                logging.info(f"Posted update comment to existing issue: {existing.get('html_url')}")
            else:
                logging.warning("Failed to post comment to existing issue.")
            # Optionally update the issue body with new hash by patching the issue
            api = f"https://api.github.com/repos/{repo_full_name}/issues/{existing.get('number')}"
            headers = {"Authorization": f"token {os.environ.get('GITHUB_TOKEN','')}", "User-Agent": USER_AGENT}
            new_body = existing.get("body", "") or ""
            # replace or append AUDIT-HASH
            if "<!-- AUDIT-HASH:" in new_body:
                import re
                new_body = re.sub(r"<!--\s*AUDIT-HASH:.*?-->", AUDIT_HASH_MARKER.format(audit_hash), new_body, flags=re.DOTALL)
            else:
                new_body = new_body + "\n\n" + AUDIT_HASH_MARKER.format(audit_hash)
            r = safe_request(session, "PATCH", api, json={"body": new_body}, headers=headers, timeout=20)
            if r.status_code in (200, 201):
                logging.info("Updated issue body audit-hash.")
            else:
                logging.warning("Failed to update issue body.")
            continue

        # create new issue
        if not args.confirm:
            logging.info("Not creating issue because --confirm flag is not present. Use --confirm to actually create.")
            continue

        # gather labels and assignees; add severity label
        labels = list(label_list)
        labels.append(f"security/{severity}")
        labels.append("triage")
        # try to pick assignee from registry if present
        candidate_assignees = assignees[:]
        if registry:
            for c in registry.get("consumers", []):
                if c.get("repo") == repo_full_name:
                    owner = c.get("owner")
                    if owner and owner not in candidate_assignees:
                        candidate_assignees.append(owner)
        created = create_issue(repo_full_name if not args.central_repo else args.central_repo, title, body, session, labels=labels, assignees=candidate_assignees or None)
        if created:
            logging.info(f"Created issue: {created.get('html_url')}")
        else:
            logging.warning(f"Failed to create issue for {repo_full_name}")


if __name__ == "__main__":
    main()
