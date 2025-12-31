# Claude Code Hooks

This directory contains hooks that enforce best practices and workflows for this project.

## Active Hooks

### 1. Skill Check Enforcement (`enforce-skill-check.py`)

**Purpose**: Prevents Claude from using analysis tools without first checking available skills.

**Event**: `PreToolUse`
**Matcher**: `Read|Grep|Glob|Task`
**Behavior**:
- Blocks analysis tools (Read, Grep, Glob, Task) if SKILL.md hasn't been read in the current session
- Allows the tool call once SKILL.md has been read
- Tracks state per session using flag files in `~/.cache/claude-hooks/`

**Why this exists**:
Prevents Claude from reinventing the wheel by doing manual analysis when specialized skills already exist. Enforces the workflow:
1. Read `.claude/skills/SKILL.md` to discover available skills
2. Evaluate if a skill matches the task
3. Only use manual tools if no skill exists

**Example violation**:
```
User: "Evaluate the refactoring plan"
Claude: Read("REFACTOR_PLAN.md")  ❌ BLOCKED
Hook: "Read .claude/skills/SKILL.md first!"
```

**Correct workflow**:
```
User: "Evaluate the refactoring plan"
Claude: Read(".claude/skills/SKILL.md")  ✅ ALLOWED
Claude: "Found 'evaluate-refactor-plan' skill, using it..."
Claude: [Uses skill instead of manual work]
```

### 2. Session Reminder (`session-reminder.sh`)

**Purpose**: Displays available resources at session start

**Event**: `SessionStart`
**Behavior**: Shows skills, agents, and governance rules available in the project

### 3. Skill Check State Cleanup (`cleanup-skill-check-state.sh`)

**Purpose**: Removes stale state files from previous sessions

**Event**: `SessionStart` (should be added)
**Behavior**: Deletes skill-check flag files older than 24 hours from `~/.cache/claude-hooks/`

## Hook State Management

### State Files Location
`~/.cache/claude-hooks/skill-check-{session_id}.flag`

### State Lifecycle
1. **Session Start**: No state file exists
2. **First SKILL.md Read**: State file created
3. **Subsequent Tool Use**: State file checked, tools allowed
4. **Session End**: State file remains (cleaned up after 24h)

### Manual State Reset
```bash
# Clear all skill check state (forces re-reading SKILL.md)
rm -f ~/.cache/claude-hooks/skill-check-*.flag

# Clear state for specific session
rm -f ~/.cache/claude-hooks/skill-check-YOUR_SESSION_ID.flag
```

## Testing Hooks

### Test the skill check enforcement:
```bash
# Simulate PreToolUse for Read (should block initially)
echo '{
  "session_id": "test123",
  "tool_name": "Read",
  "tool_input": {"file_path": "some-file.md"}
}' | .claude/hooks/enforce-skill-check.py

# Simulate reading SKILL.md (should allow and create state)
echo '{
  "session_id": "test123",
  "tool_name": "Read",
  "tool_input": {"file_path": ".claude/skills/SKILL.md"}
}' | .claude/hooks/enforce-skill-check.py

# Simulate Read again (should now allow)
echo '{
  "session_id": "test123",
  "tool_name": "Read",
  "tool_input": {"file_path": "some-file.md"}
}' | .claude/hooks/enforce-skill-check.py
```

## Configuration

Hooks are configured in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Grep|Glob|Task",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/enforce-skill-check.py",
            "timeout": 5
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-reminder.sh"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/cleanup-skill-check-state.sh"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting

### Hook not firing
- Check file permissions: `chmod +x .claude/hooks/*.py .claude/hooks/*.sh`
- Verify JSON syntax in settings files
- Check Claude Code logs for hook errors

### Hook blocking incorrectly
- Clear state: `rm -f ~/.cache/claude-hooks/skill-check-*.flag`
- Check if SKILL.md path matches: `.claude/skills/SKILL.md`
- Test hook manually (see Testing section above)

### Disable hooks temporarily
Comment out the hook in `.claude/settings.local.json` or use bypass mode:
```bash
# In Claude Code CLI
claude --bypass-hooks
```

## Related Documentation

- [Claude Code Hooks Guide](https://docs.anthropic.com/en/docs/claude-code/hooks-guide)
- [Hooks Reference](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Project SKILL.md](../.claude/skills/SKILL.md)
