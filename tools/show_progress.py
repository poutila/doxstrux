#!/usr/bin/env python3
"""Progress dashboard for regex refactoring project."""

import json
from pathlib import Path
from datetime import datetime

PHASE_NAMES = [
    "Pre-Implementation Setup",
    "Fences & Indented Code",
    "Inline → Plaintext",
    "Links & Images",
    "HTML Handling",
    "Tables",
    "Security Regex (Retained)"
]

def show_progress():
    """Display progress dashboard."""
    print("=" * 70)
    print("REGEX REFACTORING PROGRESS DASHBOARD")
    print("=" * 70)
    print()

    total_phases = len(PHASE_NAMES)
    completed_phases = 0

    for phase_num in range(total_phases):
        artifact_path = Path(f".phase-{phase_num}.complete.json")
        phase_name = PHASE_NAMES[phase_num]

        if artifact_path.exists():
            data = json.loads(artifact_path.read_text(encoding="utf-8"))
            completed_phases += 1

            completed_at = datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))
            regex_count = data["regex_count_after"]
            perf_delta = data["performance_delta_median_pct"]

            print(f"✅ Phase {phase_num}: {phase_name}")
            print(f"   Completed: {completed_at.strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"   Regex remaining: {regex_count}")
            print(f"   Performance: Δmedian={perf_delta:+.1f}%")
            print(f"   Tests: {data['baseline_pass_count']} passing")
            print()
        else:
            print(f"⏸️  Phase {phase_num}: {phase_name}")
            print(f"   Status: Not started")
            print()
            break

    # Summary
    progress_pct = (completed_phases / total_phases) * 100
    print("=" * 70)
    print(f"OVERALL PROGRESS: {completed_phases}/{total_phases} phases ({progress_pct:.0f}%)")

    if completed_phases == total_phases:
        print("🎉 PROJECT COMPLETE!")
    elif completed_phases > 0:
        print(f"📍 NEXT: Phase {completed_phases} - {PHASE_NAMES[completed_phases]}")
    else:
        print(f"📍 START: Phase 0 - {PHASE_NAMES[0]}")

    print("=" * 70)

if __name__ == "__main__":
    show_progress()
