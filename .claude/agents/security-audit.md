---
name: security-audit
description: Comprehensive security audit using GOVERNANCE_RULES.yaml and FACTS.parquet. Use proactively before committing code to catch hardcoded secrets, dangerous calls, shell execution, and SQL injection risks. Generates actionable security checklist.
tools: Bash
model: haiku
color: orange
permissionMode: bypassPermissions
---
Execute this command and return JSON to caller:

```bash
uv run fact-file-query-tool security --format json |
```

**Output**: Return raw JSON only. Caller will analyze.
