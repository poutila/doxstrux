#!/usr/bin/env python3
"""
False-Positive Telemetry Tracker

Tracks false-positive rates for renderer discovery patterns to enable data-driven pattern tuning.

Usage:
  python tools/fp_telemetry.py --record <issue_id> --pattern "<pattern>" --verdict <true|false>
  python tools/fp_telemetry.py --dashboard
  python tools/fp_telemetry.py --report /tmp/fp_report.json
"""

import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


DB_PATH = Path("audit_reports/fp_telemetry.db")


def init_db():
    """Initialize FP telemetry database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fp_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id TEXT NOT NULL,
            pattern TEXT NOT NULL,
            repo TEXT,
            path TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verdict TEXT,  -- 'true_positive', 'false_positive', 'pending'
            verdict_at TIMESTAMP,
            verdict_by TEXT,
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pattern ON fp_records(pattern)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_verdict ON fp_records(verdict)
    """)

    conn.commit()
    conn.close()


def record_hit(issue_id: str, pattern: str, repo: Optional[str] = None, path: Optional[str] = None):
    """Record a new renderer hit (verdict pending)."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO fp_records (issue_id, pattern, repo, path, verdict)
        VALUES (?, ?, ?, ?, 'pending')
    """, (issue_id, pattern, repo, path))

    conn.commit()
    record_id = cursor.lastrowid
    conn.close()

    print(f"✓ Recorded hit: issue={issue_id}, pattern={pattern}, id={record_id}")
    return record_id


def record_verdict(issue_id: str, verdict: str, verdict_by: Optional[str] = None, notes: Optional[str] = None):
    """
    Record verdict for a hit.

    verdict: 'true_positive' or 'false_positive'
    """
    if verdict not in ('true_positive', 'false_positive'):
        raise ValueError(f"Invalid verdict: {verdict}")

    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE fp_records
        SET verdict = ?,
            verdict_at = CURRENT_TIMESTAMP,
            verdict_by = ?,
            notes = ?
        WHERE issue_id = ?
    """, (verdict, verdict_by, notes, issue_id))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    if updated > 0:
        print(f"✓ Recorded verdict: issue={issue_id}, verdict={verdict}, updated={updated} records")
    else:
        print(f"⚠️  No records found for issue={issue_id}")

    return updated


def get_fp_rate_by_pattern() -> List[Dict]:
    """Calculate false-positive rate per pattern."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pattern,
            COUNT(*) as total_hits,
            SUM(CASE WHEN verdict = 'true_positive' THEN 1 ELSE 0 END) as true_positives,
            SUM(CASE WHEN verdict = 'false_positive' THEN 1 ELSE 0 END) as false_positives,
            SUM(CASE WHEN verdict = 'pending' THEN 1 ELSE 0 END) as pending,
            CAST(SUM(CASE WHEN verdict = 'false_positive' THEN 1 ELSE 0 END) AS FLOAT) /
            NULLIF(SUM(CASE WHEN verdict IN ('true_positive', 'false_positive') THEN 1 ELSE 0 END), 0) as fp_rate
        FROM fp_records
        GROUP BY pattern
        ORDER BY fp_rate DESC, total_hits DESC
    """)

    results = []
    for row in cursor.fetchall():
        pattern, total, tp, fp, pending, fp_rate = row
        results.append({
            "pattern": pattern,
            "total_hits": total,
            "true_positives": tp,
            "false_positives": fp,
            "pending": pending,
            "fp_rate": round(fp_rate, 3) if fp_rate is not None else None
        })

    conn.close()
    return results


def get_recent_pending(days: int = 7) -> List[Dict]:
    """Get hits with pending verdicts from last N days."""
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    cursor.execute("""
        SELECT id, issue_id, pattern, repo, path, recorded_at
        FROM fp_records
        WHERE verdict = 'pending'
          AND recorded_at >= ?
        ORDER BY recorded_at DESC
    """, (cutoff,))

    results = []
    for row in cursor.fetchall():
        id_, issue_id, pattern, repo, path, recorded_at = row
        results.append({
            "id": id_,
            "issue_id": issue_id,
            "pattern": pattern,
            "repo": repo,
            "path": path,
            "recorded_at": recorded_at
        })

    conn.close()
    return results


def print_dashboard():
    """Print FP rate dashboard to console."""
    print("=" * 80)
    print("FALSE-POSITIVE RATE DASHBOARD")
    print("=" * 80)
    print()

    stats = get_fp_rate_by_pattern()

    if not stats:
        print("No data available yet. Start recording hits with --record.")
        return

    print(f"{'Pattern':<40} {'Total':<8} {'TP':<8} {'FP':<8} {'Pending':<10} {'FP Rate':<10}")
    print("-" * 80)

    for stat in stats:
        fp_rate_str = f"{stat['fp_rate']:.1%}" if stat['fp_rate'] is not None else "N/A"
        print(f"{stat['pattern']:<40} {stat['total_hits']:<8} {stat['true_positives']:<8} {stat['false_positives']:<8} {stat['pending']:<10} {fp_rate_str:<10}")

    print()
    print("=" * 80)
    print("PENDING VERDICTS (Last 7 Days)")
    print("=" * 80)
    print()

    pending = get_recent_pending(days=7)

    if not pending:
        print("✓ No pending verdicts")
    else:
        print(f"{'Issue ID':<20} {'Pattern':<30} {'Repo':<20} {'Days Old':<10}")
        print("-" * 80)

        for p in pending[:20]:  # Show first 20
            recorded = datetime.fromisoformat(p['recorded_at'])
            days_old = (datetime.now() - recorded).days
            print(f"{p['issue_id']:<20} {p['pattern']:<30} {p['repo'] or 'N/A':<20} {days_old:<10}")

        if len(pending) > 20:
            print(f"\n... and {len(pending) - 20} more")

    print()


def generate_report(output_path: Path):
    """Generate JSON report with FP metrics."""
    stats = get_fp_rate_by_pattern()
    pending = get_recent_pending(days=7)

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_patterns": len(stats),
        "pattern_stats": stats,
        "pending_verdicts": pending,
        "summary": {
            "total_hits": sum(s["total_hits"] for s in stats),
            "total_true_positives": sum(s["true_positives"] for s in stats),
            "total_false_positives": sum(s["false_positives"] for s in stats),
            "total_pending": sum(s["pending"] for s in stats),
        }
    }

    # Calculate overall FP rate
    verdicted = report["summary"]["total_true_positives"] + report["summary"]["total_false_positives"]
    if verdicted > 0:
        report["summary"]["overall_fp_rate"] = round(report["summary"]["total_false_positives"] / verdicted, 3)
    else:
        report["summary"]["overall_fp_rate"] = None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2))

    print(f"✓ Report written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="FP telemetry tracker")
    parser.add_argument("--record", help="Record a new hit (provide issue ID)")
    parser.add_argument("--pattern", help="Pattern for the hit")
    parser.add_argument("--repo", help="Repository name (optional)")
    parser.add_argument("--path", help="File path (optional)")
    parser.add_argument("--verdict", help="Record verdict for issue (issue_id from --record)")
    parser.add_argument("--verdict-type", choices=["true_positive", "false_positive"], help="Type of verdict")
    parser.add_argument("--verdict-by", help="Who recorded the verdict (optional)")
    parser.add_argument("--notes", help="Notes about the verdict (optional)")
    parser.add_argument("--dashboard", action="store_true", help="Show FP rate dashboard")
    parser.add_argument("--report", help="Generate JSON report")
    args = parser.parse_args()

    if args.dashboard:
        print_dashboard()

    elif args.record and args.pattern:
        record_hit(args.record, args.pattern, args.repo, args.path)

    elif args.verdict and args.verdict_type:
        record_verdict(args.verdict, args.verdict_type, args.verdict_by, args.notes)

    elif args.report:
        generate_report(Path(args.report))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
