#!/usr/bin/env python3
"""Check for recent session summaries to enforce documentation."""

import sys
from datetime import datetime, timedelta
from pathlib import Path


def check_recent_summary(hours_threshold: int = 24) -> bool:
    """
    Ensure a session summary exists from the last N hours.

    Args:
        hours_threshold: Maximum age of summary in hours (default: 24)

    Returns:
        True if recent summary exists, False otherwise
    """
    summaries_dir = Path("summaries")

    # Check if summaries directory exists
    if not summaries_dir.exists():
        print("❌ No summaries/ directory found!")
        print("Please create: mkdir summaries")
        return False

    now = datetime.now()
    cutoff = now - timedelta(hours=hours_threshold)
    recent_summaries = []

    # Check all session files
    for summary_file in summaries_dir.glob("SESSION_*.md"):
        try:
            # Parse timestamp from filename
            timestamp_str = summary_file.stem.replace("SESSION_", "")
            file_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H%M")

            if file_time > cutoff:
                recent_summaries.append((summary_file.name, file_time))
        except ValueError:
            print(f"⚠️  Invalid filename format: {summary_file.name}")
            continue

    if recent_summaries:
        # Sort by date and show most recent
        recent_summaries.sort(key=lambda x: x[1], reverse=True)
        most_recent = recent_summaries[0]

        print(f"✅ Found recent session summary: {most_recent[0]}")
        print(f"   Created: {most_recent[1].strftime('%Y-%m-%d %H:%M')}")

        # Check if summary has required sections
        summary_path = summaries_dir / most_recent[0]
        if validate_summary_content(summary_path):
            return True
        print("⚠️  Summary exists but missing required sections")
        return False
    print(f"❌ No session summary found from last {hours_threshold} hours!")
    print(f"Please create: summaries/SESSION_{now.strftime('%Y-%m-%d_%H%M')}.md")
    print("\nRequired sections:")
    print("  - Completed Work")
    print("  - Current State")
    print("  - Known Issues")
    print("  - Next Steps")
    print("  - Modified Files")
    return False


def validate_summary_content(file_path: Path) -> bool:
    """
    Validate that summary contains required sections.

    Args:
        file_path: Path to summary file

    Returns:
        True if all required sections present, False otherwise
    """
    required_sections = [
        "## Completed Work",
        "## Current State",
        "## Next Steps",
    ]

    try:
        content = file_path.read_text()
        missing_sections = []

        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        if missing_sections:
            print(f"⚠️  Missing required sections in {file_path.name}:")
            for section in missing_sections:
                print(f"   - {section}")
            return False

        return True

    except Exception as e:
        print(f"❌ Error reading summary file: {e}")
        return False


def main():
    """Main entry point for the script."""
    # Check for command line arguments
    hours = 24
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            print(f"Invalid hours argument: {sys.argv[1]}")
            sys.exit(1)

    # Run the check
    if check_recent_summary(hours):
        print("\n✅ Session summary compliance: PASS")
        sys.exit(0)
    else:
        print("\n❌ Session summary compliance: FAIL")
        print("\nPlease create a session summary before continuing.")
        sys.exit(1)


if __name__ == "__main__":
    main()
