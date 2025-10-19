#!/usr/bin/env python3
"""
FP Metric Worker - Syncs audit-fp labels to Prometheus metric

Counts issues labeled `audit-fp` in a repo and pushes the count
as a gauge `audit_fp_marked_total` to a Prometheus Pushgateway.

Usage:
  python tools/fp_metric_worker.py --repo ORG/REPO --pushgateway http://pushgateway:9091

Environment:
  GITHUB_TOKEN - required to query the GitHub API
"""
from __future__ import annotations
import argparse
import os
import requests
import sys
import logging

DEFAULT_PUSH_PATH = "/metrics/job"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_audit_fp_count(repo: str, session: requests.Session) -> int:
    """Query GitHub search API for issues labeled audit-fp.

    Args:
        repo: Repository full name (org/repo)
        session: Authenticated requests session

    Returns:
        Count of issues labeled audit-fp
    """
    q = f"repo:{repo} label:audit-fp"
    url = "https://api.github.com/search/issues"
    params = {"q": q, "per_page": 1}

    try:
        r = session.get(url, params=params, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"GitHub search failed: {r.status_code} {r.text}")

        data = r.json()
        count = int(data.get("total_count", 0))
        logging.info(f"Found {count} issues labeled audit-fp in {repo}")
        return count
    except Exception as e:
        logging.error(f"Error querying GitHub: {e}")
        raise


def _put_to_pushgateway(pushgateway: str, job: str, metrics_text: bytes) -> None:
    """Push metrics to Pushgateway using PUT.

    Args:
        pushgateway: Pushgateway base URL
        job: Job name for metrics grouping
        metrics_text: Prometheus exposition format metrics
    """
    url = pushgateway.rstrip("/") + DEFAULT_PUSH_PATH + f"/{job}"

    try:
        r = requests.put(
            url,
            data=metrics_text,
            headers={"Content-Type": "text/plain; version=0.0.4; charset=utf-8"},
            timeout=10
        )
        r.raise_for_status()
        logging.info(f"Pushed metrics to {url}")
    except Exception as e:
        logging.error(f"Error pushing to Pushgateway: {e}")
        raise


def export_metric(pushgateway: str, job: str, count: int) -> None:
    """Export metric in Prometheus exposition format.

    Args:
        pushgateway: Pushgateway base URL
        job: Job name
        count: Metric value
    """
    payload = (
        f"# TYPE audit_fp_marked_total gauge\n"
        f"audit_fp_marked_total {count}\n"
    ).encode("utf8")

    _put_to_pushgateway(pushgateway, job, payload)


def sync_audit_fp_to_metric(
    repo: str,
    pushgateway_url: str,
    session: requests.Session = None
) -> None:
    """Public function for testing - sync FP labels to metric.

    Args:
        repo: Repository full name (org/repo)
        pushgateway_url: Pushgateway base URL
        session: Optional authenticated session (will create if None)
    """
    if session is None:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN required")

        session = requests.Session()
        session.headers.update({
            "Authorization": f"token {token}",
            "User-Agent": "fp-metric-worker/1.0"
        })

    count = get_audit_fp_count(repo, session)
    export_metric(pushgateway_url, "audit_fp_sync", count)
    logging.info(f"Successfully synced {count} FP issues to metric")


def main():
    parser = argparse.ArgumentParser(
        description="Sync audit-fp labeled issues to Prometheus metric"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository in org/repo format"
    )
    parser.add_argument(
        "--pushgateway",
        required=True,
        help="Pushgateway URL (e.g. http://pushgateway:9091)"
    )
    parser.add_argument(
        "--job",
        default="audit_fp_sync",
        help="Pushgateway job name (default: audit_fp_sync)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for CI/cron)"
    )

    args = parser.parse_args()

    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            logging.error("GITHUB_TOKEN environment variable required")
            sys.exit(2)

        session = requests.Session()
        session.headers.update({
            "Authorization": f"token {token}",
            "User-Agent": "fp-metric-worker/1.0"
        })

        count = get_audit_fp_count(args.repo, session)
        export_metric(args.pushgateway, args.job, count)

        logging.info(f"✓ Successfully pushed metric: audit_fp_marked_total={count}")
        sys.exit(0)

    except Exception as e:
        logging.error(f"✗ Error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
