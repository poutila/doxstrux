# Using Sub-Agents in Claude Code

**Purpose**: Comprehensive guide to using, chaining, and resuming sub-agents for task-specific workflows in this project.

---

## Table of Contents

1. [What Are Sub-Agents?](#what-are-sub-agents)
2. [Quick Start](#quick-start)
3. [Available Agents in This Project](#available-agents-in-this-project)
4. [Using Agents](#using-agents)
5. [Chaining Agents](#chaining-agents)
6. [Resumable Agents](#resumable-agents)
7. [Common Patterns](#common-patterns)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

---

## What Are Sub-Agents?

Sub-agents are **specialized AI assistants** that handle specific types of tasks. Each sub-agent:

- ✅ Has a **specific purpose** and expertise area
- ✅ Uses its **own context window** (separate from main conversation)
- ✅ Can be configured with **specific tools**
- ✅ Includes a **custom system prompt** that guides its behavior

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **Context Isolation** | Each agent operates in its own context, preventing pollution of the main conversation |
| **Task Specialization** | Fine-tuned with detailed instructions for specific domains (governance, security, performance, etc.) |
| **Reusability** | Once created, use across different projects and share with team |
| **Tool Control** | Each agent can have different tool access levels |

---

## Quick Start

### Creating Your First Agent

```bash
# Interactive agent creation
/agents

# Choose:
# 1. Project-level (.claude/agents/) or user-level (~/.claude/agents/)
# 2. Generate with Claude (recommended) or write manually
# 3. Describe the agent's purpose
# 4. Select tools to grant access to
```

### Using an Existing Agent

```bash
# Explicit invocation
> Use the governance-check agent to verify code quality

# Implicit (Claude decides)
> Check if my code follows governance rules
# (Claude automatically delegates to governance-check agent)
```

---

## Available Agents in This Project

This project has **24 specialized agents** in `.claude/agents/`:

### Governance & Quality Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **governance-check** | Verifies compliance with GOVERNANCE_RULES.yaml | Before committing code |
| **governance-report** | Comprehensive compliance dashboard | Code quality audits |
| **doc-quality-validator** | Checks docstring quality (Args, Returns, Raises) | When documenting code |
| **naming-validator** | Validates naming conventions | Before committing code |
| **type-coverage-enforcer** | Enforces 100% type coverage for public APIs | Before committing code |

### Security Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **security-audit** | Comprehensive security audit (secrets, SQL injection, etc.) | Before committing code |
| **hardcoding-detector** | Detects hardcoded paths, URLs, credentials | Before committing code |

### Performance Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **performance-hotspots** | Finds performance bottlenecks (nested loops, I/O in loops) | Performance optimization |

### Testing Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **test-gap-analysis** | Identifies where tests are most needed based on risk | Planning test improvements |
| **weak-test-detector** | Detects weak tests (import-only, no assertions) | When writing tests |

### Architecture & Design Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **architecture-map** | Generates architecture overview (clusters, layers, coupling) | Understanding codebase structure |
| **blast-radius** | Analyzes blast radius of changes | Before refactoring or incident response |
| **drift-detector** | Detects drift between FACTS snapshots | CI/CD gating, release validation |
| **module-purity-check** | Detects import-time side effects | Before committing code |

### SOLID Principle Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **solid-lsp-validator** | Detects Liskov Substitution Principle violations | Before committing code |
| **solid-srp-validator** | Detects Single Responsibility Principle violations (god classes) | Refactoring planning |

### Code Pattern Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **error-pattern-audit** | Detects error handling anti-patterns | Before committing code |
| **import-audit** | Checks import style violations | Before committing code |
| **logging-audit** | Detects logging anti-patterns (print() in production) | Before committing code |
| **magic-number-detector** | Detects magic numbers that should be named constants | Code reviews |
| **modern-syntax-validator** | Enforces modern Python syntax (PEP 604, PEP 585) | Before committing code |
| **mutable-defaults-detector** | Detects mutable default arguments | Before committing code |

### Fact System Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **query-pack** | Executes pre-built query packs (scorecards, docs, architecture) | Comprehensive analysis |

---

## Using Agents

### Method 1: Explicit Invocation (Recommended)

Direct your request to a specific agent:

```bash
> Use the governance-check agent to verify my code

> Have the security-audit agent check for vulnerabilities

> Ask the architecture-map agent to show the system structure
```

### Method 2: Via Task Tool (Programmatic)

When you're already in code/workflow context:

```python
# Single agent invocation
Task(
    subagent_type="governance-check",
    description="Verify governance compliance",
    prompt="Run governance check and report all violations"
)

# Returns: { status, violations, agentId }
```

### Method 3: Implicit Delegation

Claude automatically delegates when task matches agent description:

```bash
> Check if my code follows governance rules
# Claude recognizes this matches governance-check and delegates automatically
```

---

## Chaining Agents

**Chaining** = Running multiple agents in sequence for complex workflows.

### Pattern 1: Sequential Chain (One After Another)

```python
# Step 1: Check governance
Task(
    subagent_type="governance-check",
    description="Check code quality",
    prompt="Run governance check on the entire codebase"
)

# Step 2: Check security (after governance results)
Task(
    subagent_type="security-audit",
    description="Check security",
    prompt="Run comprehensive security audit"
)

# Step 3: Check performance (after security results)
Task(
    subagent_type="performance-hotspots",
    description="Find bottlenecks",
    prompt="Identify performance hotspots"
)
```

### Pattern 2: Parallel Chain (Independent Tasks)

When agents don't depend on each other's results:

```python
# All can run independently - send in single message
Task(subagent_type="governance-check", description="...", prompt="...")
Task(subagent_type="security-audit", description="...", prompt="...")
Task(subagent_type="architecture-map", description="...", prompt="...")
```

### Pattern 3: Conditional Chain (Based on Results)

```python
# Step 1: Check for violations
result = Task(
    subagent_type="governance-check",
    description="Check violations",
    prompt="Check for any governance violations"
)

# Step 2: If violations found, analyze blast radius
if result['violations'] > 0:
    Task(
        subagent_type="blast-radius",
        description="Analyze impact",
        prompt="Analyze blast radius of violated functions"
    )
```

### Pattern 4: Validation Chain (Pre-Commit)

Complete pre-commit validation workflow:

```python
# Chain 1: Code Quality
Task(subagent_type="governance-check", ...)
Task(subagent_type="solid-srp-validator", ...)
Task(subagent_type="type-coverage-enforcer", ...)

# Chain 2: Security
Task(subagent_type="security-audit", ...)
Task(subagent_type="hardcoding-detector", ...)

# Chain 3: Patterns
Task(subagent_type="error-pattern-audit", ...)
Task(subagent_type="mutable-defaults-detector", ...)
Task(subagent_type="logging-audit", ...)

# Chain 4: Documentation
Task(subagent_type="doc-quality-validator", ...)
```

---

## Resumable Agents

**Resumable agents** = Continue previous agent conversations across multiple invocations.

### How It Works

1. Each agent execution gets a unique `agentId`
2. Agent conversation stored in `agent-{agentId}.jsonl`
3. Resume using `resume` parameter with the `agentId`
4. Agent continues with **full context** from previous conversation

### Example Workflow

#### Initial Invocation

```bash
> Use the code-analyzer agent to start reviewing the authentication module

[Agent completes analysis]
[Returns agentId: "abc123"]
```

#### Resume Later

```bash
> Resume agent abc123 and now analyze the authorization logic as well

[Agent continues with full context from previous conversation]
```

### Programmatic Usage

```python
# Initial invocation
result = Task(
    subagent_type="governance-check",
    description="Phase 1 validation",
    prompt="Validate Phase 1.0 of refactor plan"
)
# Save agentId: result.agentId = "abc123"

# Resume later
Task(
    subagent_type="governance-check",
    description="Phase 2 validation",
    prompt="Now validate Phase 2.0 claims",
    resume="abc123"  # Continues with full context
)
```

### Use Cases for Resumable Agents

| Use Case | Example |
|----------|---------|
| **Long-running research** | Break large codebase analysis into multiple sessions |
| **Iterative refinement** | Continue refining agent's work without losing context |
| **Multi-step workflows** | Have agent work on related tasks sequentially |
| **Multi-phase validation** | Validate refactor plan phases incrementally |

---

## Common Patterns

### Pattern 1: Pre-Commit Quality Gate

Run before every commit to ensure code quality:

```bash
> Run pre-commit checks

# Claude chains:
# 1. governance-check
# 2. security-audit
# 3. solid-srp-validator
# 4. type-coverage-enforcer
# 5. doc-quality-validator
```

### Pattern 2: Refactor Validation

Before starting refactoring:

```bash
> Validate refactor plan in REFACTOR_XYZ.md

# Claude chains:
# 1. governance-check (verify claimed violations)
# 2. solid-srp-validator (verify SRP violations)
# 3. architecture-map (verify structural claims)
```

### Pattern 3: Incident Response

When investigating production issues:

```bash
> Analyze blast radius of function X

# Claude chains:
# 1. blast-radius (who calls it, what it calls)
# 2. test-gap-analysis (what tests are missing)
# 3. error-pattern-audit (error handling issues)
```

### Pattern 4: Code Review

Comprehensive code review workflow:

```bash
> Review my recent changes

# Claude chains:
# 1. governance-check (code quality)
# 2. security-audit (security issues)
# 3. performance-hotspots (performance concerns)
# 4. doc-quality-validator (documentation)
# 5. naming-validator (naming conventions)
```

### Pattern 5: Architecture Analysis

Understanding codebase structure:

```bash
> Show me the architecture overview

# Claude chains:
# 1. architecture-map (clusters, layers, coupling)
# 2. drift-detector (compare against baseline)
# 3. module-purity-check (import-time side effects)
```

---

## Best Practices

### 1. Design Focused Agents

✅ **DO**: Create agents with single, clear responsibilities
```yaml
name: error-pattern-audit
description: Detect error handling anti-patterns only
```

❌ **DON'T**: Create one agent that does everything
```yaml
name: code-checker
description: Check everything about code quality
```

### 2. Write Detailed Prompts

✅ **DO**: Include specific instructions and examples
```markdown
You are an error handling validator.

When invoked:
1. Check for bare except clauses
2. Check for swallowed exceptions
3. Report violations with line numbers
```

❌ **DON'T**: Use vague prompts
```markdown
Check error handling.
```

### 3. Limit Tool Access

✅ **DO**: Grant only necessary tools
```yaml
tools: Bash, Read  # Only needs to read and query
```

❌ **DON'T**: Grant all tools when not needed
```yaml
tools: Bash, Read, Edit, Write, Grep, Glob, ...
```

### 4. Use Proactive Language in Descriptions

✅ **DO**: Encourage proactive use
```yaml
description: Use PROACTIVELY before committing code to catch error handling anti-patterns
```

❌ **DON'T**: Use passive language
```yaml
description: Can check error handling if asked
```

### 5. Chain Related Agents

✅ **DO**: Chain agents for comprehensive analysis
```python
Task(subagent_type="governance-check", ...)
Task(subagent_type="security-audit", ...)
Task(subagent_type="performance-hotspots", ...)
```

❌ **DON'T**: Use one agent for unrelated tasks
```python
Task(
    prompt="Check governance, security, performance, docs, tests, and everything else"
)
```

### 6. Use Resume for Multi-Step Tasks

✅ **DO**: Resume for related follow-up tasks
```python
# Initial
result = Task(subagent_type="code-analyzer", ...)

# Resume
Task(subagent_type="code-analyzer", resume=result.agentId, ...)
```

❌ **DON'T**: Start fresh each time (loses context)
```python
# Step 1
Task(subagent_type="code-analyzer", prompt="Analyze auth")

# Step 2 (loses context!)
Task(subagent_type="code-analyzer", prompt="Now analyze auth again")
```

---

## Examples

### Example 1: Pre-Commit Validation Chain

**Goal**: Validate code before commit

```bash
> Run pre-commit validation on my changes
```

**Claude's chain**:
```python
# Step 1: Governance
Task(
    subagent_type="governance-check",
    description="Check governance compliance",
    prompt="Run governance check. Report complexity, SOLID, docs, errors, security violations."
)

# Step 2: Security
Task(
    subagent_type="security-audit",
    description="Security audit",
    prompt="Check for hardcoded secrets, SQL injection risks, dangerous calls."
)

# Step 3: Performance
Task(
    subagent_type="performance-hotspots",
    description="Performance check",
    prompt="Find performance hotspots: nested loops, I/O in loops, blocking in async."
)

# Step 4: Patterns
Task(
    subagent_type="error-pattern-audit",
    description="Error handling check",
    prompt="Check for silent exceptions, bare except, swallowed errors."
)

# Step 5: Documentation
Task(
    subagent_type="doc-quality-validator",
    description="Documentation check",
    prompt="Verify docstring quality: Args, Returns, Raises sections."
)
```

**Result**: Comprehensive report with violations from all agents

---

### Example 2: Refactor Plan Validation (Resumable)

**Goal**: Validate a multi-phase refactor plan incrementally

```bash
> Validate Phase 1.0 of REFACTOR_FACT_FILE_QUERY_TOOL.md
```

**Initial validation**:
```python
result = Task(
    subagent_type="governance-check",
    description="Phase 1.0 validation",
    prompt="Validate Phase 1.0 claims: FactStore extraction should reduce god class violations. Check current state."
)
# Returns: agentId = "agent_phase1_abc123"
```

**Later: Validate Phase 2.0**:
```bash
> Resume agent_phase1_abc123 and validate Phase 2.0 claims
```

```python
Task(
    subagent_type="governance-check",
    description="Phase 2.0 validation",
    prompt="Now validate Phase 2.0 claims about agent framework extraction. Compare with Phase 1.0 baseline.",
    resume="agent_phase1_abc123"  # Maintains context from Phase 1.0
)
```

---

### Example 3: Incident Response Chain

**Goal**: Analyze impact of a function change

```bash
> Analyze blast radius of function calculate_total in src/billing.py
```

**Claude's chain**:
```python
# Step 1: Blast radius
Task(
    subagent_type="blast-radius",
    description="Analyze impact",
    prompt="Analyze blast radius of calculate_total: who calls it, what it calls, error contract, side effects."
)

# Step 2: Test gaps (based on blast radius results)
Task(
    subagent_type="test-gap-analysis",
    description="Find test gaps",
    prompt="Identify missing tests for calculate_total and its callers based on risk factors."
)

# Step 3: Error patterns
Task(
    subagent_type="error-pattern-audit",
    description="Check error handling",
    prompt="Check error handling in calculate_total and all callers."
)
```

**Result**: Complete impact assessment with test gaps and error handling issues

---

### Example 4: Architecture Analysis

**Goal**: Understand codebase structure

```bash
> Show me the architecture overview and identify coupling issues
```

**Claude's chain**:
```python
# Step 1: Architecture map
Task(
    subagent_type="architecture-map",
    description="Generate architecture overview",
    prompt="Generate architecture map: clusters, layers, dependencies, coupling, boundaries."
)

# Step 2: SOLID SRP (based on architecture results)
Task(
    subagent_type="solid-srp-validator",
    description="Find god classes",
    prompt="Identify god classes and high coupling violations (fan-out > 10)."
)

# Step 3: Module purity
Task(
    subagent_type="module-purity-check",
    description="Check import-time side effects",
    prompt="Detect import-time side effects that cause coupling."
)
```

**Result**: Architecture overview with coupling issues and god classes identified

---

### Example 5: Security Review Chain

**Goal**: Comprehensive security audit

```bash
> Run security review on authentication module
```

**Claude's chain**:
```python
# Step 1: Security audit
Task(
    subagent_type="security-audit",
    description="Security audit",
    prompt="Run comprehensive security audit: secrets, dangerous calls, shell execution, SQL injection."
)

# Step 2: Hardcoding detector
Task(
    subagent_type="hardcoding-detector",
    description="Detect hardcoded values",
    prompt="Detect hardcoded paths, URLs, credentials, connection strings in authentication module."
)

# Step 3: Error patterns (security-relevant)
Task(
    subagent_type="error-pattern-audit",
    description="Check error handling security",
    prompt="Check for error handling that might leak sensitive information."
)
```

**Result**: Complete security assessment with all vulnerabilities

---

## Performance Considerations

### Context Efficiency

✅ **Agents preserve main context** → Longer overall sessions possible
- Main conversation stays focused on high-level objectives
- Agent results summarized back to main conversation
- Detailed exploration happens in agent's isolated context

### Latency

⚠️ **Agents add latency** → Each agent starts with clean slate
- Must gather context for their task
- Sequential chains slower than direct commands
- Use for complex tasks where isolation benefits outweigh latency

**When to use agents**:
- ✅ Complex multi-step tasks
- ✅ Tasks requiring specialized expertise
- ✅ Tasks that would clutter main conversation
- ✅ Reusable workflows (pre-commit, code review, etc.)

**When to use direct commands**:
- ✅ Simple one-off queries
- ✅ Tasks where you need immediate result
- ✅ Tasks where context is already in main conversation

---

## Quick Reference

### Agent Invocation Methods

| Method | Syntax | Use When |
|--------|--------|----------|
| **Explicit** | `> Use the X agent to do Y` | You know exactly which agent to use |
| **Task Tool** | `Task(subagent_type="X", ...)` | Programmatic/workflow context |
| **Implicit** | `> Check governance rules` | Let Claude decide best agent |

### Chaining Patterns

| Pattern | Syntax | Use When |
|---------|--------|----------|
| **Sequential** | Multiple `Task()` calls in order | Each step depends on previous results |
| **Parallel** | Multiple `Task()` in single message | Steps are independent |
| **Conditional** | `if result: Task(...)` | Next step depends on result condition |
| **Resumable** | `Task(resume="agentId")` | Multi-phase or long-running tasks |

### Available Agents Quick List

```
Governance:     governance-check, governance-report, doc-quality-validator,
                naming-validator, type-coverage-enforcer

Security:       security-audit, hardcoding-detector

Performance:    performance-hotspots

Testing:        test-gap-analysis, weak-test-detector

Architecture:   architecture-map, blast-radius, drift-detector,
                module-purity-check

SOLID:          solid-lsp-validator, solid-srp-validator

Patterns:       error-pattern-audit, import-audit, logging-audit,
                magic-number-detector, modern-syntax-validator,
                mutable-defaults-detector

Fact System:    query-pack
```

---

## See Also

- **`.claude/agents/`** - All 24 agent definitions
- **`.claude/skills/SKILL.md`** - Skills directory index
- **`.claude/skills/evaluate-refactor-plan/`** - Agent chaining example
- **`GOVERNANCE_RULES.yaml`** - Rules enforced by governance agents

---

**Last Updated**: 2025-12-21
**Agent Count**: 24 specialized agents
**Project**: hybrid_validate (golden-docs validation system)
