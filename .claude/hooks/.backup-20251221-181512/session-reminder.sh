#!/bin/bash
# Session reminder hook - reminds Claude of available resources

cat <<'EOF'
📚 Available Resources:

• 25 Skills (.claude/skills/) - Use for discovery: magic-power, security-audit, governance-check, etc.
• 23 Agents (.claude/agents/) - Specialized analysis with Task(subagent_type="...")
• GOVERNANCE_RULES.yaml (.claude/rules/) - All quality rules and thresholds (831 lines)

Use skills proactively before committing code. Query FACTS.parquet instead of reading files.
EOF

exit 0
