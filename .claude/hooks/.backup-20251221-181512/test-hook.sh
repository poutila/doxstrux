#!/bin/bash
# Test script for enforce-skill-check.py hook

set -e

HOOK_SCRIPT="$(dirname "$0")/enforce-skill-check.py"
TEST_SESSION="test-session-$(date +%s)"

echo "🧪 Testing enforce-skill-check.py hook"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Block Read before SKILL.md
echo "Test 1: Should BLOCK Read before SKILL.md is read"
echo "───────────────────────────────────────────────"
OUTPUT=$(echo "{
  \"session_id\": \"$TEST_SESSION\",
  \"tool_name\": \"Read\",
  \"tool_input\": {\"file_path\": \"/some/file.md\"},
  \"hook_event_name\": \"PreToolUse\"
}" | "$HOOK_SCRIPT")

if echo "$OUTPUT" | grep -q '"permissionDecision": "deny"'; then
    echo "✅ PASS: Hook correctly blocked Read"
else
    echo "❌ FAIL: Hook should have blocked Read"
    echo "Output: $OUTPUT"
    exit 1
fi
echo ""

# Test 2: Allow reading SKILL.md
echo "Test 2: Should ALLOW reading SKILL.md"
echo "───────────────────────────────────────"
OUTPUT=$(echo "{
  \"session_id\": \"$TEST_SESSION\",
  \"tool_name\": \"Read\",
  \"tool_input\": {\"file_path\": \".claude/skills/SKILL.md\"},
  \"hook_event_name\": \"PreToolUse\"
}" | "$HOOK_SCRIPT")

if echo "$OUTPUT" | grep -q '"permissionDecision": "allow"'; then
    echo "✅ PASS: Hook correctly allowed reading SKILL.md"
else
    echo "❌ FAIL: Hook should have allowed reading SKILL.md"
    echo "Output: $OUTPUT"
    exit 1
fi
echo ""

# Test 3: Allow Read after SKILL.md was read
echo "Test 3: Should ALLOW Read after SKILL.md was read"
echo "────────────────────────────────────────────────"
OUTPUT=$(echo "{
  \"session_id\": \"$TEST_SESSION\",
  \"tool_name\": \"Read\",
  \"tool_input\": {\"file_path\": \"/some/other/file.md\"},
  \"hook_event_name\": \"PreToolUse\"
}" | "$HOOK_SCRIPT")

if [ -z "$OUTPUT" ]; then
    echo "✅ PASS: Hook correctly allowed Read (no output = exit 0 = allow)"
else
    echo "❌ FAIL: Hook should have allowed Read silently"
    echo "Output: $OUTPUT"
    exit 1
fi
echo ""

# Test 4: Also block Grep, Glob, Task before SKILL.md
echo "Test 4: Should also BLOCK Grep before SKILL.md"
echo "────────────────────────────────────────────────"
NEW_SESSION="test-session-$(date +%s)-2"
OUTPUT=$(echo "{
  \"session_id\": \"$NEW_SESSION\",
  \"tool_name\": \"Grep\",
  \"tool_input\": {\"pattern\": \".*\"},
  \"hook_event_name\": \"PreToolUse\"
}" | "$HOOK_SCRIPT")

if echo "$OUTPUT" | grep -q '"permissionDecision": "deny"'; then
    echo "✅ PASS: Hook correctly blocked Grep"
else
    echo "❌ FAIL: Hook should have blocked Grep"
    echo "Output: $OUTPUT"
    exit 1
fi
echo ""

# Test 5: Allow non-analysis tools
echo "Test 5: Should ALLOW non-analysis tools (e.g., Bash)"
echo "──────────────────────────────────────────────────"
OUTPUT=$(echo "{
  \"session_id\": \"$NEW_SESSION\",
  \"tool_name\": \"Bash\",
  \"tool_input\": {\"command\": \"ls\"},
  \"hook_event_name\": \"PreToolUse\"
}" | "$HOOK_SCRIPT")

if [ -z "$OUTPUT" ]; then
    echo "✅ PASS: Hook correctly allowed Bash (not an analysis tool)"
else
    echo "❌ FAIL: Hook should have allowed Bash without blocking"
    echo "Output: $OUTPUT"
    exit 1
fi
echo ""

# Cleanup
echo "🧹 Cleaning up test state files..."
rm -f ~/.cache/claude-hooks/skill-check-${TEST_SESSION}*.flag

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All tests passed!"
echo ""
echo "Hook is working correctly and ready to use."
