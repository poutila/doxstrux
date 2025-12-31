#!/usr/bin/env python3
"""PreToolUse hook: Enforce reading SKILL.md before manual analysis.

This hook prevents Claude from using analysis tools (Read, Grep, Glob, Task)
without first checking the available skills in SKILL.md.

Enforcement strategy:
1. Track whether SKILL.md has been read in this session
2. Block "analysis" tools if SKILL.md hasn't been read yet
3. Provide clear guidance on what to do instead
"""

import json
import sys
from pathlib import Path

# Analysis tools that require skill check
ANALYSIS_TOOLS = {"Read", "Grep", "Glob", "Task"}

# Paths that indicate skill awareness
SKILL_PATHS = {
    ".claude/skills/SKILL.md",
    "/home/lasse/Dropbox/python/omat/hybrid_validate/.claude/skills/SKILL.md",
}

# State file to track SKILL.md reads per session
STATE_DIR = Path.home() / ".cache" / "claude-hooks"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def get_state_file(session_id: str) -> Path:
    """Get state file path for this session."""
    return STATE_DIR / f"skill-check-{session_id}.flag"


def has_read_skills(session_id: str) -> bool:
    """Check if SKILL.md has been read in this session."""
    return get_state_file(session_id).exists()


def mark_skills_read(session_id: str) -> None:
    """Mark that SKILL.md has been read in this session."""
    get_state_file(session_id).touch()


def is_reading_skills(tool_name: str, tool_input: dict) -> bool:
    """Check if this tool call is reading SKILL.md."""
    if tool_name != "Read":
        return False

    file_path = tool_input.get("file_path", "")
    return any(skill_path in file_path for skill_path in SKILL_PATHS)


def should_enforce(tool_name: str, session_id: str) -> bool:
    """Determine if we should enforce the skill check."""
    # Don't enforce if SKILL.md already read
    if has_read_skills(session_id):
        return False

    # Only enforce for analysis tools
    if tool_name not in ANALYSIS_TOOLS:
        return False

    return True


def main() -> None:
    # Load input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    session_id = input_data.get("session_id", "")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # If reading SKILL.md, mark it as read and allow
    if is_reading_skills(tool_name, tool_input):
        mark_skills_read(session_id)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Reading SKILL.md - good practice!"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Check if we should enforce
    if not should_enforce(tool_name, session_id):
        sys.exit(0)

    # BLOCK: Enforce reading SKILL.md first
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"🚫 WORKFLOW VIOLATION: Using {tool_name} without checking available skills first.\n\n"
                "📚 MANDATORY WORKFLOW:\n"
                "1. Read('.claude/skills/SKILL.md') - Check available skills/agents\n"
                "2. Evaluate if a skill matches the task\n"
                "3. ONLY use manual tools if no skill exists\n\n"
                "This prevents reinventing the wheel and ensures you use the tools we've built.\n\n"
                "▶️  ACTION REQUIRED: Read('.claude/skills/SKILL.md') first, then retry."
            )
        },
        "systemMessage": "⚠️  Hook blocked tool use - Claude must read SKILL.md first"
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
