# Hooks Removed - 2025-12-21

## What Was Removed

All Claude Code hooks have been removed from this project.

### Hooks Previously Active

**SessionStart Hooks (in settings.json):**
- `session-reminder.sh` - Displayed available resources at session start
- `cleanup-skill-check-state.sh` - Cleaned up skill check state

**PreToolUse Hooks (in settings.local.json):**
- `enforce-skill-check.py` - Enforced reading SKILL.md before using Task/Read/Grep/Glob tools
  - Blocked: Task, Read, Grep, Glob
  - Purpose: Prevent "reinventing the wheel" by forcing skill discovery

**Permissions Denied (in settings.local.json):**
- `python:*` - Blocked system Python
- `python3:*` - Blocked system Python 3
- `uv pip install:*` - Blocked direct pip usage
- `.venv/bin/python:*` - Blocked direct venv Python

## Why Removed

Hooks were removed to eliminate workflow friction while maintaining governance through:

1. **Command Guidelines in All Files** - All 49 files (23 agents + 26 skills) now have explicit "Command Guidelines (MANDATORY)" sections that document:
   - ✅ ALWAYS use: `uv run python`
   - ❌ NEVER use: `python3`, `python`, or system Python
   - Examples of correct vs incorrect usage

2. **Self-Documenting System** - Instead of runtime enforcement, guidelines are embedded directly in agent and skill definitions

3. **Trust Over Control** - Agents are now trusted to follow documented guidelines rather than being blocked by enforcement hooks

## What Remains

**Permissions Allow List** - Kept for convenience (pre-approves common safe commands):
- `uv run python:*`
- `uv run pytest:*`
- `fact-file-query-tool:*`
- `fact-file-generator:*`
- And other safe utilities

**Canonical Error Handling** - All agents still have HARD_STOP_CONDITIONS.md compliance with `set -Eeuo pipefail` and error traps

## Archived Files

Hook files have been moved to `.backup-YYYYMMDD-HHMMSS/` subdirectory and can be restored if needed.

## Migration Path

If hook enforcement is needed again:

1. Restore hook files from `.backup-*/` directory
2. Re-add hook registrations to `.claude/settings.json` and `.claude/settings.local.json`
3. Optionally re-enable permissions deny list for system Python

---

**Date Removed:** 2025-12-21
**Reason:** Replaced with embedded Command Guidelines in all 49 agent/skill files
**Status:** Governance maintained through documentation instead of runtime enforcement
