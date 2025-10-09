#!/usr/bin/env python3
"""Check that all completed tasks have completion summaries."""

import re
import sys
from pathlib import Path


def extract_completed_tasks(task_file: Path) -> list[str]:
    """
    Extract task IDs marked as completed from TASK.md.

    Returns:
        List of task IDs (e.g., ['T-001', 'T-002'])
    """
    completed_tasks = []

    try:
        content = task_file.read_text()

        # Look for completed tasks in the table
        # Format: | T-XXX | ... | ✅ Completed | ...
        pattern = r"\|\s*(T-\d+)\s*\|.*\|.*✅\s*Completed\s*\|"
        matches = re.findall(pattern, content)
        completed_tasks.extend(matches)

        # Also check detailed sections for "✅ COMPLETED"
        pattern2 = r"###\s*(T-\d+):.*✅\s*COMPLETED"
        matches2 = re.findall(pattern2, content)
        completed_tasks.extend(matches2)

        # Deduplicate
        completed_tasks = list(set(completed_tasks))
        completed_tasks.sort()

    except Exception as e:
        print(f"❌ Error reading TASK.md: {e}")
        return []

    return completed_tasks


def check_completion_summaries(completed_tasks: list[str]) -> tuple[list[str], list[str]]:
    """
    Check which completed tasks have completion summaries.

    Returns:
        Tuple of (tasks_with_summaries, tasks_missing_summaries)
    """
    completions_dir = Path("planning/completions")

    if not completions_dir.exists():
        print("❌ No completions directory found at planning/completions/")
        return [], completed_tasks

    tasks_with_summaries = []
    tasks_missing_summaries = []

    for task_id in completed_tasks:
        summary_file = completions_dir / f"{task_id}_COMPLETION.md"
        if summary_file.exists():
            tasks_with_summaries.append(task_id)
        else:
            tasks_missing_summaries.append(task_id)

    return tasks_with_summaries, tasks_missing_summaries


def main():
    """Main entry point."""
    task_file = Path("planning/TASK.md")

    if not task_file.exists():
        print("❌ TASK.md not found at planning/TASK.md")
        sys.exit(1)

    # Extract completed tasks
    completed_tasks = extract_completed_tasks(task_file)

    if not completed_tasks:
        print("ℹ️  No completed tasks found in TASK.md")
        sys.exit(0)

    print(f"📋 Found {len(completed_tasks)} completed tasks: {', '.join(completed_tasks)}")

    # Check for completion summaries
    with_summaries, missing_summaries = check_completion_summaries(completed_tasks)

    # Report results
    if with_summaries:
        print(f"\n✅ Tasks with completion summaries ({len(with_summaries)}):")
        for task in with_summaries:
            print(f"   - {task}: planning/completions/{task}_COMPLETION.md")

    if missing_summaries:
        print(f"\n❌ Tasks MISSING completion summaries ({len(missing_summaries)}):")
        for task in missing_summaries:
            print(f"   - {task}: Please create planning/completions/{task}_COMPLETION.md")
        print("\n⚠️  Policy: ALL completed tasks MUST have completion summaries!")
        print("   Use TASK_COMPLETION_TEMPLATE.md for tasks ≥3 points")
        print("   Use TASK_COMPLETION_MINIMAL.md for 1-2 point tasks")
        sys.exit(1)
    else:
        print("\n✅ Completion summary compliance: PASS")
        print("   All completed tasks have summaries!")

    # Bonus: Check if summaries have required sections
    print("\n📊 Summary Quality Check:")
    for task in with_summaries:
        summary_file = Path(f"planning/completions/{task}_COMPLETION.md")
        content = summary_file.read_text()

        required_sections = ["What Was Done", "Lessons Learned", "Next"]
        missing = [s for s in required_sections if s not in content]

        if missing:
            print(f"   ⚠️  {task}: Missing sections: {', '.join(missing)}")
        else:
            print(f"   ✅ {task}: All required sections present")


if __name__ == "__main__":
    main()
