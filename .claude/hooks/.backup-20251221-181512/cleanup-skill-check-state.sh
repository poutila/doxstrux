#!/bin/bash
# SessionStart hook: Clean up stale skill-check state files from previous sessions

STATE_DIR="$HOME/.cache/claude-hooks"

if [ -d "$STATE_DIR" ]; then
    # Remove state files older than 24 hours
    find "$STATE_DIR" -name 'skill-check-*.flag' -type f -mtime +1 -delete 2>/dev/null
fi

exit 0
