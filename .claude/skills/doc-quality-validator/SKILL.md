---
name: doc-quality-validator
description: Check docstring quality before documenting. Use proactively when writing documentation to ensure complete docstrings with Args, Returns, and Raises sections. Enforces documentation standards.
allowed-tools: Bash, Read, Task
---

# Doc Quality Validator Skill

**This skill invokes the [doc-quality-validator](../../agents/doc-quality-validator.md) agent.**

---

## When to Use This

✅ **Use proactively in these scenarios:**

- Before committing code to git
- During code reviews or pull requests
- As a pre-commit hook validation
- In CI/CD pipelines as a quality gate
- When refactoring or making significant changes

---

## Command Guidelines (MANDATORY)

**Python Execution:**
- ✅ ALWAYS use: `uv run python`
- ❌ NEVER use: `python3`, `python`, `python3.11`, or any system Python
- Rationale: Project uses uv for dependency management and environment isolation

**Tool Execution:**
- ✅ ALWAYS use: `uv run <tool-name>`
- ❌ NEVER use: bare tool names without `uv run` prefix

**Examples:**
```bash
# ✅ CORRECT
uv run python -m json.tool < data.json
uv run python -c "import sys; print(sys.version)"
uv run fact-file-query-tool naming

# ❌ WRONG - Will be blocked by hooks
python3 -m json.tool < data.json
python -c "import sys; print(sys.version)"
fact-file-query-tool naming
```

**If you need to process JSON, parse text, or run any Python code:**
- Use `uv run python -c "..."` for inline scripts
- Use `uv run python -m <module>` for module execution
- Use `uv run python <script.py>` for script execution

## What It Does

1. **Args section** - All parameters documented
2. **Returns section** - Return value documented
3. **Raises section** - Exceptions documented
4. **Examples** - Code examples present

---

## How to Invoke

### Method 1: Natural Language ⭐ Recommended

For most use cases, simply ask Claude:

```bash
> Use the doc-quality-validator agent to verify my code
```

**Examples**:
```bash
> Use the doc-quality-validator agent before committing

> Have the doc-quality-validator agent check for issues

> Ask the doc-quality-validator agent to analyze the codebase
```

Claude will automatically delegate to the agent.

### Method 2: Programmatic (For Chaining/Workflows)

When chaining multiple agents or in automated workflows:

```python
Task(
    subagent_type="doc-quality-validator",
    description="Check code quality",
    prompt="Run doc-quality-validator analysis and report all findings with exact locations."
)
```

**When to use programmatic invocation**:
- ✅ Chaining multiple agents in sequence
- ✅ Automated workflows or scripts
- ✅ Resumable multi-step processes
- ✅ When you need to capture agent results programmatically

### Method 3: Direct CLI (Manual Testing)

For direct command-line usage without Claude:

```bash
set -Eeuo pipefail

# Helper functions
require_cmd() { command -v "$1" >/dev/null || { echo "❌ Missing required command: $1" >&2; exit 2; }; }
require_file() { [[ -f "$1" ]] || { echo "❌ Missing required file: $1" >&2; exit 2; }; }

# Canonical hard stop trap (HARD_STOP_CONDITIONS.md)
trap 'rc=$?; 
  echo "❌ HARD STOP (rc=$rc)" >&2;
  echo "   file: ${BASH_SOURCE[0]}" >&2;
  echo "   line: $LINENO" >&2;
  echo "   func: ${FUNCNAME[1]:-MAIN}" >&2;
  echo "   cmd : $BASH_COMMAND" >&2;
  exit "$rc"' ERR

# Validate prerequisites
echo "🔍 Validating prerequisites..."
require_cmd uv
echo "✅ Prerequisites validated"

# Run validation
echo "🔍 Running Doc Quality Validator..."
uv run fact-file-query-tool doc-quality
echo "✅ Doc Quality Validator passed"
```

**With options**:
```bash
set -Eeuo pipefail

# Helper functions
require_cmd() { command -v "$1" >/dev/null || { echo "❌ Missing required command: $1" >&2; exit 2; }; }
require_file() { [[ -f "$1" ]] || { echo "❌ Missing required file: $1" >&2; exit 2; }; }

# Canonical hard stop trap (HARD_STOP_CONDITIONS.md)
trap 'rc=$?; 
  echo "❌ HARD STOP (rc=$rc)" >&2;
  echo "   file: ${BASH_SOURCE[0]}" >&2;
  echo "   line: $LINENO" >&2;
  echo "   func: ${FUNCNAME[1]:-MAIN}" >&2;
  echo "   cmd : $BASH_COMMAND" >&2;
  exit "$rc"' ERR

# Validate prerequisites
echo "🔍 Validating prerequisites..."
require_cmd uv
echo "✅ Prerequisites validated"

# Run validation
echo "🔍 Running Doc Quality Validator..."
uv run fact-file-query-tool doc-quality --format summary
echo "✅ Doc Quality Validator passed"

uv run fact-file-query-tool doc-quality --format json

uv run fact-file-query-tool doc-quality --file path/to/file.py
```

---

## Agent Details

For complete information about the agent's behavior:

**Agent file**: [doc-quality-validator](../../agents/doc-quality-validator.md)

The agent file contains:
- Full system prompt
- Available tools
- Detection logic and rules
- Model configuration

---

## Examples

### Example 1: Pre-commit Validation

**Scenario**: Verify code before committing

**Invocation**:
```bash
> Use the doc-quality-validator agent to verify my code before committing
```

**Expected Result**: Agent analyzes code and reports any issues found.

---

### Example 2: Programmatic Chain

**Scenario**: Chain with other agents for comprehensive validation

**Invocation**:
```python
# Step 1: Run this agent
Task(
    subagent_type="doc-quality-validator",
    description="Check for issues",
    prompt="Analyze the codebase and report all findings."
)

# Step 2: Chain with related agent
Task(
    subagent_type="governance-check",
    description="Overall governance check",
    prompt="Run comprehensive governance validation."
)
```

---

### Example 3: Direct CLI

**Scenario**: Quick manual check from command line

**Invocation**:
```bash
set -Eeuo pipefail

# Helper functions
require_cmd() { command -v "$1" >/dev/null || { echo "❌ Missing required command: $1" >&2; exit 2; }; }
require_file() { [[ -f "$1" ]] || { echo "❌ Missing required file: $1" >&2; exit 2; }; }

# Canonical hard stop trap (HARD_STOP_CONDITIONS.md)
trap 'rc=$?; 
  echo "❌ HARD STOP (rc=$rc)" >&2;
  echo "   file: ${BASH_SOURCE[0]}" >&2;
  echo "   line: $LINENO" >&2;
  echo "   func: ${FUNCNAME[1]:-MAIN}" >&2;
  echo "   cmd : $BASH_COMMAND" >&2;
  exit "$rc"' ERR

# Validate prerequisites
echo "🔍 Validating prerequisites..."
require_cmd uv
echo "✅ Prerequisites validated"

# Run validation
echo "🔍 Running Doc Quality Validator..."
uv run fact-file-query-tool doc-quality --format summary
echo "✅ Doc Quality Validator passed"
```

---

## Chaining with Other Agents

This agent works well with:

- **governance-check**: For overall quality validation
- **security-audit**: For security-focused analysis
- **performance-hotspots**: For performance optimization

**Example chain**:
```python
# Comprehensive validation
Task(subagent_type="doc-quality-validator", ...)
Task(subagent_type="governance-check", ...)
Task(subagent_type="security-audit", ...)
```

---

## Related Resources

- **Agent**: [doc-quality-validator](../../agents/doc-quality-validator.md)
- **Governance Rules**: `.claude/rules/GOVERNANCE_RULES.yaml`
- **Using Agents Guide**: [USING_SUB_AGENTS.md](../USING_SUB_AGENTS.md)
- **All Skills**: [SKILL.md](../SKILL.md)

---

## Success Criteria

You'll know the skill worked correctly when:

- [ ] Agent completed analysis without errors
- [ ] Results are clear and actionable
- [ ] Any issues found include file paths and line numbers
- [ ] Recommendations are specific and implementable

---

## Notes

**Performance**: Agent queries FACTS.parquet for fast, deterministic analysis.

**Best Practices**:
- Use proactively before commits to catch issues early
- Chain with related agents for comprehensive validation
- Review all findings and address systematically
- Re-run after fixes to verify resolution

---

**Last Updated**: 2025-12-21
**Template Version**: 1.0
**Agent Status**: ✅ Exists
