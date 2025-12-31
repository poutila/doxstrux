# SKILL_TEMPLATE_FOR_POINTING_TO_AGENTS.md

**Purpose**: Standard template for skill files that point to corresponding agents in `.claude/agents/`

**Use this template for**: Skills that have a 1:1 mapping to an agent (e.g., governance-check skill → governance-check agent)

**Do NOT use for**: Meta-skills that chain multiple agents (e.g., evaluate-refactor-plan)

---

## Template Structure

```markdown
---
name: <skill-name>
description: <Brief description of when Claude should use this skill. Include keywords like "Use proactively" or "MUST BE USED" to encourage automatic invocation>
allowed-tools: Bash, Read, Task
---

# <Skill Name> Skill

**This skill invokes the [<agent-name>](../../agents/<agent-name>.md) agent.**

---

## When to Use This

✅ **Use proactively in these scenarios:**

- <Scenario 1>
- <Scenario 2>
- <Scenario 3>
- <Scenario 4>

**Examples**:
- "Before committing code"
- "When reviewing pull requests"
- "During refactoring"
- "As a pre-commit hook"

---

## What It Does

<Brief overview of what the agent checks/analyzes/does>

**Key capabilities**:
- <Capability 1>
- <Capability 2>
- <Capability 3>

**Enforces rules from**: `GOVERNANCE_RULES.yaml` (if applicable)

---

## How to Invoke

### Method 1: Natural Language ⭐ Recommended

For most use cases, simply ask Claude:

```bash
> Use the <agent-name> agent to <action>
```

**Examples**:
```bash
> Use the governance-check agent to verify my code before committing

> Have the security-audit agent check for vulnerabilities

> Ask the architecture-map agent to show the system structure
```

Claude will automatically delegate to the agent.

### Method 2: Programmatic (For Chaining/Workflows)

When chaining multiple agents or in automated workflows:

```python
Task(
    subagent_type="<agent-name>",
    description="<Short description of what this agent will do>",
    prompt="<Detailed instructions for the agent. Be specific about what to check, report, or analyze.>"
)
```

**Example**:
```python
Task(
    subagent_type="governance-check",
    description="Verify governance compliance",
    prompt="Run governance check on the entire codebase. Report all violations with exact counts by category (complexity, SOLID, documentation, error handling, security)."
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
echo "🔍 Running Skill_template_for_pointing_to_agents..."
uv run fact-file-query-tool <command> [options]
echo "✅ Skill_template_for_pointing_to_agents passed"
```

**Example**:
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
echo "🔍 Running Skill_template_for_pointing_to_agents..."
uv run fact-file-query-tool governance
echo "✅ Skill_template_for_pointing_to_agents passed"

uv run fact-file-query-tool governance --format summary

uv run fact-file-query-tool governance --file path/to/file.py
```

**When to use direct CLI**:
- ✅ Quick manual testing
- ✅ Shell scripts or CI/CD pipelines
- ✅ When you want immediate results without LLM interaction

---

## Agent Details

For complete information about the agent's behavior:

**Agent file**: [<agent-name>](../../agents/<agent-name>.md)

The agent file contains:
- Full system prompt
- Available tools
- Governance rules enforced
- Detailed detection logic
- Model configuration

---

## Output Format

<Describe what the agent returns>

**Example output**:
```
<Show example output from the agent or CLI command>
```

**Exit codes** (if applicable):
- `0` - Success (no violations found)
- `1` - Failure (violations found)

---

## Examples

### Example 1: <Use Case 1>

**Scenario**: <Describe the scenario>

**Invocation**:
```bash
> Use the <agent-name> agent to <action>
```

**Result**:
```
<Show expected result>
```

---

### Example 2: <Use Case 2>

**Scenario**: <Describe the scenario>

**Invocation (Programmatic)**:
```python
Task(
    subagent_type="<agent-name>",
    description="<description>",
    prompt="<prompt>"
)
```

**Result**:
```
<Show expected result>
```

---

### Example 3: <Use Case 3>

**Scenario**: <Describe the scenario>

**Invocation (CLI)**:
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
echo "🔍 Running Skill_template_for_pointing_to_agents..."
uv run fact-file-query-tool <command> --option value
echo "✅ Skill_template_for_pointing_to_agents passed"
```

**Result**:
```
<Show expected result>
```

---

## Chaining with Other Agents

This agent works well with:

- **<related-agent-1>**: <Why/when to chain>
- **<related-agent-2>**: <Why/when to chain>
- **<related-agent-3>**: <Why/when to chain>

**Example chain**:
```python
# Step 1: This agent
Task(subagent_type="<agent-name>", ...)

# Step 2: Related agent
Task(subagent_type="<related-agent>", ...)
```

---

## Related Resources

- **Agent**: [<agent-name>](../../agents/<agent-name>.md)
- **Governance Rules**: `.claude/rules/GOVERNANCE_RULES.yaml`
- **Using Agents Guide**: [USING_SUB_AGENTS.md](../USING_SUB_AGENTS.md)
- **Related Skills**:
  - [<related-skill-1>](../<related-skill-1>/<related-skill-1>.md)
  - [<related-skill-2>](../<related-skill-2>/<related-skill-2>.md)

---

## Success Criteria

You'll know the skill worked correctly when:

- [ ] <Criterion 1>
- [ ] <Criterion 2>
- [ ] <Criterion 3>
- [ ] Agent returned expected results
- [ ] No errors or warnings (unless violations found)

---

## Notes

<Any additional notes, caveats, or important information>

**Performance**: <Performance characteristics, if relevant>

**Limitations**: <Any known limitations>

**Best Practices**:
- <Best practice 1>
- <Best practice 2>
```

---

## Field-by-Field Guide

### Frontmatter

```yaml
---
name: governance-check
  # Must match the directory name and agent name
  # Use lowercase with hyphens (kebab-case)

description: Check code governance compliance before committing...
  # Natural language description
  # Include "Use proactively" or "MUST BE USED" to encourage automatic use
  # Mention key scenarios when this should be used

allowed-tools: Bash, Read, Task
  # MUST include "Task" for agent invocation
  # Bash - for running CLI commands
  # Read - for reading files if needed
  # Task - for invoking agents programmatically
---
```

### Key Sections

1. **Header with Agent Link**
   - Immediately tell users this skill invokes an agent
   - Link to the agent file

2. **When to Use This**
   - Clear scenarios with checkboxes
   - Proactive language ("Before X", "When Y")

3. **What It Does**
   - Brief overview of capabilities
   - Note if it enforces GOVERNANCE_RULES.yaml

4. **How to Invoke (3 Methods)**
   - **Natural Language**: For most users
   - **Programmatic**: For chaining/workflows
   - **Direct CLI**: For manual testing

5. **Agent Details**
   - Link to agent file
   - Describe what's in the agent file

6. **Examples**
   - Show all 3 invocation methods
   - Real-world scenarios

7. **Chaining**
   - Related agents to chain with
   - Example chain

8. **Related Resources**
   - Links to agent, rules, guides

---

## Example: Applying Template to `governance-check`

```markdown
---
name: governance-check
description: Check code governance compliance before committing. Use proactively to verify complexity limits, documentation standards, error handling rules, type coverage, security patterns, and SOLID principles.
allowed-tools: Bash, Read, Task
---

# Governance Check Skill

**This skill invokes the [governance-check](../../agents/governance-check.md) agent.**

---

## When to Use This

✅ **Use proactively in these scenarios:**

- Before committing code to git
- Before creating a pull request
- As a pre-push hook validation
- During code reviews
- Before merging to main branch
- In CI/CD pipelines as a quality gate

---

## What It Does

Validates code compliance across **6 governance categories** defined in GOVERNANCE_RULES.yaml:

**Key capabilities**:
- Checks cyclomatic complexity ≤ 10
- Enforces documentation standards (Args, Returns, Raises)
- Validates error handling patterns (no bare except)
- Verifies 100% type coverage for public APIs
- Detects security anti-patterns (hardcoded secrets, dangerous calls)
- Enforces SOLID principles (SRP, LSP)

**Enforces rules from**: `.claude/rules/GOVERNANCE_RULES.yaml`

---

## How to Invoke

### Method 1: Natural Language ⭐ Recommended

```bash
> Use the governance-check agent to verify my code before committing
```

### Method 2: Programmatic (For Chaining/Workflows)

```python
Task(
    subagent_type="governance-check",
    description="Verify governance compliance",
    prompt="Run governance check on the entire codebase. Report all violations with exact counts by category."
)
```

### Method 3: Direct CLI (Manual Testing)

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
echo "🔍 Running Skill_template_for_pointing_to_agents..."
uv run fact-file-query-tool governance --format summary
echo "✅ Skill_template_for_pointing_to_agents passed"
```

---

## Agent Details

**Agent file**: [governance-check](../../agents/governance-check.md)

Contains:
- System prompt for governance validation
- Access to Bash and Read tools
- Integration with GOVERNANCE_RULES.yaml
- Violation reporting format

---

## Examples

### Example 1: Pre-commit Check

**Scenario**: Verify code before committing

**Invocation**:
```bash
> Use the governance-check agent to verify my code before committing
```

**Result**: Agent reports 0 violations → safe to commit

---

## Chaining with Other Agents

Works well with:

- **security-audit**: For comprehensive security + quality check
- **solid-srp-validator**: For focused SOLID principle analysis
- **performance-hotspots**: For performance + quality analysis

**Example chain**:
```python
Task(subagent_type="governance-check", ...)
Task(subagent_type="security-audit", ...)
```

---

## Related Resources

- **Agent**: [governance-check](../../agents/governance-check.md)
- **Rules**: `.claude/rules/GOVERNANCE_RULES.yaml`
- **Guide**: [USING_SUB_AGENTS.md](../USING_SUB_AGENTS.md)
```

---

## When NOT to Use This Template

### Special Cases

**Do NOT use this template for**:

1. **Meta-skills** that chain multiple agents
   - Example: `evaluate-refactor-plan`
   - These skills orchestrate workflows, not invoke a single agent

2. **Utility skills** without corresponding agents
   - Example: `fact-query` (if it just wraps CLI, not an agent)

3. **Workflow skills** that coordinate multiple tools
   - These need custom structure

### Template for Meta-Skills

Meta-skills like `evaluate-refactor-plan` should have:

```markdown
---
name: evaluate-refactor-plan
description: Validates refactoring plans...
allowed-tools: Bash, Read, Task  # Still needs Task for chaining
---

# <Skill Name>

## What This Does

<Describes the workflow>

## Agents Used

This skill chains multiple agents:
1. [governance-check](../../agents/governance-check.md)
2. [solid-srp-validator](../../agents/solid-srp-validator.md)
3. [architecture-map](../../agents/architecture-map.md)

## Workflow

### Step 1: ...
### Step 2: ...
### Step 3: ...

## Examples

<Show complete workflow examples>
```

---

## Validation Checklist

Use this checklist when creating/updating skills:

### Frontmatter
- [ ] `name` matches directory name and agent name
- [ ] `description` includes "Use proactively" or similar
- [ ] `allowed-tools` includes `Bash, Read, Task`

### Content
- [ ] Links to agent file in first paragraph
- [ ] "When to Use This" section with scenarios
- [ ] "What It Does" section with capabilities
- [ ] "How to Invoke" with all 3 methods
- [ ] "Agent Details" section linking to agent
- [ ] At least 3 examples
- [ ] "Chaining" section with related agents
- [ ] "Related Resources" section

### Quality
- [ ] All links work (use relative paths)
- [ ] Examples are realistic and tested
- [ ] Language is clear and actionable
- [ ] Formatting is consistent

---

## Quick Reference

| Section | Purpose | Required |
|---------|---------|----------|
| Header with agent link | Show this invokes an agent | ✅ Yes |
| When to Use | Scenarios for automatic invocation | ✅ Yes |
| What It Does | Capabilities overview | ✅ Yes |
| How to Invoke (3 methods) | Natural + Programmatic + CLI | ✅ Yes |
| Agent Details | Link to agent file | ✅ Yes |
| Examples | Real-world usage | ✅ Yes |
| Chaining | Related agents | ⚠️ Recommended |
| Related Resources | Links to docs | ⚠️ Recommended |

---

**Last Updated**: 2025-12-21
**Template Version**: 1.0
**For**: Skills that point to agents in `.claude/agents/`
