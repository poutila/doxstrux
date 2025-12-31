---
name: evaluate-refactor-plan
description: Validates refactoring plans and specifications by comparing documented claims against actual code metrics from FACTS.parquet. Use when asked to "evaluate [PLAN] against [FILE]" or verify if specification claims are accurate. CRITICAL - Uses fact-file-query-tool to analyze files of ANY size (5,000+ lines) that would be impossible to Read() directly.
allowed-tools: Bash, Read, Glob, Grep, Task
---

# Evaluate Refactor Plan Skill

⚡ **TRIGGER PATTERN**: When user says **"Evaluate [SPEC.md] against [file.py]"** - use this skill immediately.

**Purpose**: Validate refactoring plans empirically before execution by comparing claimed violations against actual metrics from fact-file-query-tool.

**🎯 Key Capability**: Analyze files of ANY size (100 lines to 10,000+ lines) via FACTS.parquet queries - files that would error out with Read() due to token limits.

## The Workflow

1. **Read refactor plan ONLY** - Extract claims about violations, LOC, complexity (DO NOT read target file!)
2. **Query FACTS.parquet** - Use `fact-file-query-tool` CLI to get actual metrics (NOT manual file reading!)
3. **Compare claims vs facts** - Verify plan claims against queried measurements
4. **Recommend GO/NO-GO** - Based on fact-driven verification results

**🚫 CRITICAL**: Never Read() the target implementation file - query FACTS.parquet instead!

## When to Use This

### 🎯 Key Trigger Phrases (USE THIS SKILL WHEN USER SAYS):

- ✅ **"Evaluate [PLAN.md] against [file.py]"**
- ✅ **"Verify claims in [SPEC.md]"**
- ✅ **"Does [implementation] match [specification]?"**
- ✅ **"Check if [plan] is accurate"**
- ✅ **"Validate [refactor plan] before starting"**

### Proactive (Before Refactoring)
- ✅ **Before starting any Phase 1.0+ refactoring** - validate plan matches reality
- ✅ **When reviewing refactor proposals** - verify ROI and feasibility
- ✅ **Before creating refactor branches** - ensure effort matches problem size
- ✅ **When estimating refactor timeline** - validate LOC reduction claims

### Reactive (Quality Assurance)
- ✅ **After receiving refactor plan** - verify claims are empirically grounded
- ✅ **During refactor reviews** - confirm original violations still exist
- ✅ **When questioning plan scope** - check for over-engineering

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

### 1. Reads Refactoring Plan
- Extracts claimed violations (LOC, complexity, fan-out, etc.)
- Identifies target files/functions/classes
- Notes expected improvements

### 2. Runs Empirical Validation
Uses fact-file-query-tool to verify:
- `governance` - Overall governance violations (complexity, docs, errors, types, security)
- `solid-srp` - SRP violations (god classes, oversized functions, high coupling)
- `architecture` - Structural overview (clusters, layers, coupling)
- File LOC counts (`wc -l`)

### 3. Compares Plan vs Reality
- ✅ **Verified**: Claim matches actual metrics
- ⚠️ **Warning**: Claim close but not exact (±10%)
- ❌ **False**: Claim doesn't match reality

### 4. Provides Assessment
- **Recommendation**: GO / NO-GO / REVISE
- **Confidence**: HIGH (>90%) / MEDIUM (70-90%) / LOW (<70%)
- **Risks**: Identified gaps or concerns
- **Predicted Impact**: Quantified improvements

## Instructions

### ⚡ FACT-DRIVEN EVALUATION PHILOSOPHY

This skill embodies the **fact-driven planning** paradigm:

```
"I think there are ~20 violations"     →  Query: 47 violations
"The function is probably complex"      →  Query: CC=368 (exact)
"About 300 lines"                       →  Query: 343 LOC (precise)
"This seems like a god class"           →  Query: fan_out=13, 11 methods (verified)
```

**Core Principle**: Every claim in a refactor plan must be verifiable against facts. No assumptions, no approximations, no guesses.

### ⚡ CRITICAL WORKFLOW PRINCIPLE

**ALWAYS use fact-file-query-tool FIRST, then fall back to file reading only if needed.**

```
Priority Order:
1. Query facts via fact-file-query-tool (get metrics directly from FACTS.parquet)
2. Only if facts unavailable: Read files manually
```

**Why this matters**:
- Facts are **precise** (not "about 20", but "exactly 47")
- Facts are **current** (regenerated from code, never stale)
- Facts are **verifiable** (can be independently checked)
- Facts are **fast** (<10ms queries vs minutes of manual analysis)

**The shift**:
```
"I think..."  →  "I queried..."
"Probably..."  →  "Verified..."
"About..."     →  "Exactly..."
```

---

### 🚫 CRITICAL: DO NOT READ THE TARGET FILE

**BEFORE starting the workflow, understand this hard rule:**

❌ **FORBIDDEN**: `Read(<target_implementation_file>)`
✅ **REQUIRED**: Query FACTS.parquet via fact-file-query-tool

**The ONLY file you should Read() is the refactor plan (REFACTOR_*.md).**

**Why this is a hard rule:**

1. **Token Limits** - Large files (5,000+ lines) will ERROR OUT:
   - Read() has a 25,000 token limit
   - fact_file_query_tool.py is 50,637 tokens (would fail!)
   - fact-file-query-tool queries FACTS.parquet in <10ms regardless of file size

2. **Precision** - Facts are exact, reading is subjective:
   - Manual: "main() looks very complex, maybe 300+ lines"
   - Facts: "main() CC=368, LOC=1949, nesting=7" (exact, verifiable)

3. **Speed** - Query vs manual analysis:
   - fact-file-query-tool: <10ms for any query
   - Manual reading: minutes to analyze, error-prone counting

4. **Scalability** - fact-file-query-tool handles ANY file size:
   - 100-line file: instant query
   - 10,000-line file: instant query (Read() would fail)
   - Reading defeats the purpose of fact-driven validation

**🎯 Key Advantage**: fact-file-query-tool lets you analyze huge files "like a walk in the park" - files that would be impossible to Read() directly due to token limits.

**Violation consequences:**
- Wasted effort (minutes vs milliseconds)
- Imprecise claims ("about 300" vs "343 exactly")
- Unverifiable results (subjective vs measurable)

**Only read target file if:**
- [ ] You already queried all available facts
- [ ] Facts are missing critical information
- [ ] You need to understand implementation details (not metrics)

---

### Basic Usage (5-Step Workflow)

When user says **"Evaluate [PLAN.md] against [file.py]"**:

```bash
# Step 1: Read the refactor plan ONLY (NOT the target file!)
Read("REFACTOR_<component>.md")
# Extract claims: LOC counts, violation counts, complexity metrics

# Step 2: Query facts for target file (PRIMARY METHOD - USE THIS FIRST!)
uv run python -m golden_validator_hybrid.fact_file_query_tool query \
  --file <target_file> \
  --entity "function.main" \
  --keys complexity loc params nesting fan_out
# Gets: CC, LOC, parameter count, nesting depth, fan-out

# Step 2b: Only if fact-file-query-tool doesn't have the metric:
wc -l <target_file>  # For total file LOC (last resort)

# Step 3: Run governance check
Task(subagent_type="governance-check", prompt="...")
# Get actual violation counts by category

# Step 4: Run SRP check
Task(subagent_type="solid-srp-validator", prompt="...")
# Get actual god classes, oversized functions, complexity metrics

# Step 5: Compare and recommend
# ✅ All claims verified → GO
# ❌ Claims false → NO-GO
# ⚠️ Claims outdated → REVISE
```

### Workflow Option 1: Using Agents (Recommended)

Agents provide better context and can be chained/resumed for complex evaluations:

```python
# 1. Read the refactor plan
Read("REFACTOR_<component>.md")

# 2. Extract target file from plan (usually in Prerequisites or Architecture Overview)
# Example: src/golden_validator_hybrid/fact_file_query_tool.py

# 3. Chain agents for comprehensive validation
Task(
    subagent_type="governance-check",
    description="Verify governance violations",
    prompt="Run governance check on the codebase and report all violations with counts. Focus on complexity, SOLID, documentation, error handling, and security violations."
)
# Returns agentId - save for potential resume

Task(
    subagent_type="solid-srp-validator",
    description="Verify SRP violations",
    prompt="Check for SRP violations in fact_file_query_tool.py specifically. Report god classes, high coupling (fan-out), and oversized functions with exact metrics."
)

Task(
    subagent_type="architecture-map",
    description="Get architecture overview",
    prompt="Generate architecture map showing clusters, layers, and coupling analysis. Include module counts and dependency summary."
)

# 4. Compare claims in plan vs agent outputs
# Verify: LOC counts, complexity metrics, violation counts, function/class names

# 5. Generate assessment report with:
#    - Verified claims (with actual metrics from agents)
#    - Assessment of refactoring approach
#    - Strengths of the plan
#    - Potential risks
#    - Predicted impact table
#    - Final verdict (GO/NO-GO/REVISE)
```

### Workflow Option 2: Direct CLI Commands

For simpler evaluations or when agents aren't available:

```bash
# 1. Read the refactor plan
Read("REFACTOR_<component>.md")

# 2. Extract target file from plan
# Example: src/golden_validator_hybrid/fact_file_query_tool.py

# 3. Query specific entity facts (PRIMARY METHOD - use this first!)
uv run python -m golden_validator_hybrid.fact_file_query_tool query \
  --path <target_file> \
  --entity "function.main" \
  --keys complexity loc params nesting fan_out
# Example: Get main() function metrics

uv run python -m golden_validator_hybrid.fact_file_query_tool query \
  --path <target_file> \
  --entity "class.FactStore" \
  --keys loc methods fan_out
# Example: Get FactStore class metrics

# 4. Run governance check for violation counts
uv run python -m golden_validator_hybrid.fact_file_query_tool governance --path <target_file> --format summary

# 5. Run SRP check for god classes and oversized functions
uv run python -m golden_validator_hybrid.fact_file_query_tool solid-srp --path <target_file> --format summary

# 6. Only if needed: Get file LOC count (fallback)
wc -l <target_file>

# 7. Optional: Get architecture overview
uv run python -m golden_validator_hybrid.fact_file_query_tool architecture --format summary

# 8. Compare claims in plan vs actual output
# Verify: LOC counts, complexity metrics, violation counts, function/class names

# 9. Generate assessment report
```

## Examples

### Example 0: User Request Pattern (MOST COMMON)

**User says**:
```
"Evaluate REFACTOR_FACT_FILE_QUERY_TOOL.md against fact_file_query_tool.py"
```

**What this means**:
1. Read `REFACTOR_FACT_FILE_QUERY_TOOL.md` (the refactor plan)
2. Extract claims: "4,944 LOC", "18 violations", "main() CC=368", etc.
3. Verify claims against `fact_file_query_tool.py` using `fact-file-query-tool` CLI
4. Report: ✅ VERIFIED / ❌ FALSE / ⚠️ OUTDATED
5. Recommend: GO / NO-GO / REVISE

**How to proceed** (PROPER WORKFLOW):
```bash
# Step 1: Read the plan
Read("REFACTOR_FACT_FILE_QUERY_TOOL.md")
# Extract claims: main() CC=368, FactStore 343 LOC, etc.

# Step 2: Query specific entity facts (PRIMARY METHOD)
# Verify main() complexity claim
Bash("uv run python -m golden_validator_hybrid.fact_file_query_tool query \
  --path src/golden_validator_hybrid/fact_file_query_tool.py \
  --entity 'function.main' \
  --keys complexity loc nesting")
# Gets: actual CC, LOC, nesting depth for main()

# Verify FactStore class claim
Bash("uv run python -m golden_validator_hybrid.fact_file_query_tool query \
  --path src/golden_validator_hybrid/fact_file_query_tool.py \
  --entity 'class.FactStore' \
  --keys loc methods fan_out")
# Gets: actual LOC, method count, coupling for FactStore

# Step 3: Verify governance violations (via agent or CLI)
Task(subagent_type="governance-check",
     prompt="Check governance violations in fact_file_query_tool.py")
# OR via CLI:
# Bash("uv run python -m golden_validator_hybrid.fact_file_query_tool governance --path ...")

# Step 4: Verify SRP violations
Task(subagent_type="solid-srp-validator",
     prompt="Check SRP violations in fact_file_query_tool.py")

# Step 5: Only if needed as fallback - total file LOC
Bash("wc -l src/golden_validator_hybrid/fact_file_query_tool.py")

# Step 6: Compare and report
# Compare plan claims vs actual facts from queries
```

---

### Example 1: Verifying LOC Claims

**Plan claims**: "fact_file_query_tool.py is 4,944 lines"

**Verification**:
```bash
wc -l src/golden_validator_hybrid/fact_file_query_tool.py
# Output: 4944 src/golden_validator_hybrid/fact_file_query_tool.py
```

**Result**: ✅ **VERIFIED** - Exact match

---

### Example 2: Verifying Complexity Claims

**Plan claims**: "main() function has CC=368 (37x over limit)"

**Verification**:
```bash
uv run python -m golden_validator_hybrid.fact_file_query_tool solid-srp \
  --file fact_file_query_tool.py --format summary
# Output: fact_file_query_tool.py::function.main: High Complexity (368 > 10)
```

**Result**: ✅ **VERIFIED** - Exact match (368 confirmed)

---

### Example 3: Verifying SRP Violations

**Plan claims**: "7 SRP violations in fact_file_query_tool.py"

**Verification**:
```bash
uv run python -m golden_validator_hybrid.fact_file_query_tool solid-srp \
  --file fact_file_query_tool.py --format summary
# Output: Total Violations: 7
```

**Result**: ✅ **VERIFIED** - Count matches exactly

---

### Example 4: Full Evaluation (what we just did)

**Plan**: `REFACTOR_FACT_FILE_QUERY_TOOL.md`
**Target**: `src/golden_validator_hybrid/fact_file_query_tool.py`

**Commands run**:
```bash
# File size
wc -l src/golden_validator_hybrid/fact_file_query_tool.py
# → 4944 lines ✅

# Governance violations
uv run python -m golden_validator_hybrid.fact_file_query_tool governance --format summary
# → 109 violations (102 complexity + 4 SOLID + 3 error handling) ✅

# SRP violations
uv run python -m golden_validator_hybrid.fact_file_query_tool solid-srp \
  --file fact_file_query_tool.py --format summary
# → 7 violations (main() CC=368, blast_radius CC=20, etc.) ✅

# Architecture overview
uv run python -m golden_validator_hybrid.fact_file_query_tool architecture --format summary
# → 2 clusters, 35 modules in root, coupling analysis ✅
```

**Verified Claims**:
- ✅ File LOC: 4,944 (exact)
- ✅ main() CC: 368 (exact)
- ✅ main() fan-out: 15 (exact)
- ✅ SRP violations: 7 (exact)
- ✅ Specific function complexities: all confirmed

**Assessment Result**:
```
RECOMMENDATION: PROCEED WITH REFACTORING
Confidence Level: HIGH (95%)

Predicted Impact:
  File LOC:           4,944 → ~700   (85% ↓)
  main() CC:          368 → <10      (97% ↓)
  SRP Violations:     7 → 0          (100% ↓)
  Governance Total:   109 → ~70      (36% ↓)
```

---

### Example 5: Agent-Based Evaluation (Recommended Workflow)

**Plan**: `REFACTOR_FACT_FILE_QUERY_TOOL.md`
**Target**: `src/golden_validator_hybrid/fact_file_query_tool.py`

**Workflow using agents**:

```python
# Step 1: Read the plan
Read("REFACTOR_FACT_FILE_QUERY_TOOL.md")
# Identified claims: 4,944 LOC, main() CC=368, 18 violations, etc.

# Step 2: Verify with governance-check agent
Task(
    subagent_type="governance-check",
    description="Verify governance violations",
    prompt="Run governance check. Report exact violation counts by category and identify violations in fact_file_query_tool.py specifically."
)
# Agent returns: 109 violations (102 complexity, 4 SOLID, 3 error handling)
# ✅ Verified: Plan claimed 18, actual 109 (more violations than claimed - plan conservative)

# Step 3: Verify with solid-srp-validator agent
Task(
    subagent_type="solid-srp-validator",
    description="Verify SRP violations",
    prompt="Check fact_file_query_tool.py for SRP violations. Report all god classes, oversized functions, and exact complexity metrics for main() function."
)
# Agent returns: 7 SRP violations, main() CC=368
# ✅ Verified: Exact match on both counts

# Step 4: Verify with architecture-map agent
Task(
    subagent_type="architecture-map",
    description="Get architecture overview",
    prompt="Generate architecture map. Include cluster count, module distribution, and coupling analysis."
)
# Agent returns: 2 clusters, 35 modules in root, coupling metrics
# ✅ Verified: Structural claims confirmed

# Step 5: Get file LOC (bash still needed for this)
Bash("wc -l src/golden_validator_hybrid/fact_file_query_tool.py")
# Returns: 4944
# ✅ Verified: Exact match

# Step 6: Generate assessment
# All claims verified, recommend PROCEED with HIGH confidence
```

**Advantages of agent-based approach**:
- ✅ Agents provide structured output with context
- ✅ Can be resumed if evaluation interrupted
- ✅ Better error handling and validation
- ✅ Agents understand GOVERNANCE_RULES.yaml context
- ✅ Can chain multiple validations in sequence

## Output Format

### Assessment Report Template

**MANDATORY**: Every claim must include its **fact source**. No claim without verification.

```markdown
## Evaluation of <PLAN_NAME>

**Validated Against**: FACTS.parquet (generated: YYYY-MM-DD)

---

### ✅ Verified Claims (with Fact Sources)

#### Claim 1: [Plan's claim]
- **Plan States**: "main() has CC=368"
- **Fact Source**: `query --entity 'function.main' --keys complexity`
- **Actual Value**: CC=368
- **Status**: ✅ CONFIRMED (exact match)

#### Claim 2: [Plan's claim]
- **Plan States**: "FactStore is 343 LOC"
- **Fact Source**: `query --entity 'class.FactStore' --keys loc`
- **Actual Value**: 346 LOC
- **Status**: ⚠️ CLOSE (within 1%, acceptable drift)

#### Claim 3: [Plan's claim]
- **Plan States**: "18 governance violations"
- **Fact Source**: `governance-check agent output`
- **Actual Value**: 47 violations
- **Status**: ❌ FALSE (plan underestimated by 162%)

**Verification Summary**:
- ✅ Confirmed: X claims
- ⚠️ Close: Y claims (within acceptable tolerance)
- ❌ False: Z claims (require plan revision)

---

### 📊 Assessment of Refactoring Approach

**Phase 1.0 - FactStore Extraction**:
- **Verdict**: GO / REVISE / SKIP
- **Evidence**: [Fact-based justification]
- **Verified Scope**: 343 LOC → 5 modules (40-80 LOC each)

**Phase 2.0 - Agent Framework**:
- **Verdict**: GO / REVISE / SKIP
- **Evidence**: [Fact-based justification]
- **Verified Scope**: 1,600 LOC → 10 classes (80-120 LOC each)

---

### 🎯 Strengths of the Plan
1. **[Strength]** - Verified by: [fact source]
2. **[Strength]** - Verified by: [fact source]

### ⚠️ Potential Risks
1. **[Risk]** - Evidence: [fact source]
2. **[Risk]** - Evidence: [fact source]

---

### 📈 Predicted Impact (Fact-Based)

| Metric | Before (Queried) | After (Planned) | Improvement | Fact Source |
|--------|------------------|-----------------|-------------|-------------|
| File LOC | 4,944 | ~700 | 85% ↓ | `wc -l` |
| main() CC | 368 | <10 | 97% ↓ | `query --entity 'function.main' --keys complexity` |
| FactStore LOC | 346 | N/A (deleted) | 100% ↓ | `query --entity 'class.FactStore' --keys loc` |
| SRP Violations | 15 | 0 | 100% ↓ | `solid-srp agent` |
| Governance Total | 47 | ~20 | 57% ↓ | `governance-check agent` |

---

### ✅ Final Verdict

**RECOMMENDATION**: PROCEED / REVISE / REJECT

**Confidence Level**: HIGH/MEDIUM/LOW (XX%)

**Rationale** (fact-based):
- [Key fact 1 that supports decision]
- [Key fact 2 that supports decision]
- [Key fact 3 that supports decision]

**Conditions for Success**:
- [ ] All claims verified with ≤10% drift
- [ ] No false claims that invalidate approach
- [ ] Blast radius understood and acceptable
- [ ] All refactored code will pass governance checks
```

**Remember**: If you cannot provide a **fact source** for a claim, mark it as ⚠️ UNVERIFIED and note the limitation.

## Agent Integration

### Related Agents

This skill leverages the following agents from `.claude/agents/`:

| Agent | Purpose | Agent File |
|-------|---------|------------|
| **governance-check** | Verifies overall governance violations against GOVERNANCE_RULES.yaml | [governance-check.md](../../agents/governance-check.md) |
| **solid-srp-validator** | Detects SRP violations (god classes, high coupling, oversized functions) | [solid-srp-validator.md](../../agents/solid-srp-validator.md) |
| **architecture-map** | Generates structural overview (clusters, layers, coupling analysis) | [architecture-map.md](../../agents/architecture-map.md) |
| **governance-report** | Provides comprehensive compliance dashboard with all metrics | [governance-report.md](../../agents/governance-report.md) |
| **blast-radius** | Analyzes function coupling and blast radius for impact assessment | [blast-radius.md](../../agents/blast-radius.md) |

### Chaining Agents for Evaluation

For comprehensive refactor plan validation, chain multiple agents in sequence:

```python
# Step 1: Overall governance violations
Task(
    subagent_type="governance-check",
    description="Verify governance violations",
    prompt="Run comprehensive governance check. Report violation counts by category (complexity, SOLID, docs, errors, security)."
)

# Step 2: SRP-specific analysis
Task(
    subagent_type="solid-srp-validator",
    description="Verify SRP violations",
    prompt="Focus on fact_file_query_tool.py. Report all god classes and oversized functions with exact LOC and complexity metrics."
)

# Step 3: Architecture validation
Task(
    subagent_type="architecture-map",
    description="Architecture overview",
    prompt="Generate architecture map. Show cluster count, module distribution, and coupling metrics."
)
```

### Resumable Multi-Phase Evaluation

For large refactor plans with multiple phases, use resumable agents:

```python
# Initial evaluation (Phase 1.0 validation)
result1 = Task(
    subagent_type="governance-check",
    description="Phase 1.0 validation",
    prompt="Validate Phase 1.0 of refactor plan. Check if FactStore extraction will reduce violations as claimed."
)
# Save agentId from result: agent_abc123

# Later: Resume for Phase 2.0 validation
Task(
    subagent_type="governance-check",
    description="Phase 2.0 validation",
    prompt="Now validate Phase 2.0 claims about agent framework extraction.",
    resume="agent_abc123"  # Continues with full context
)
```

**Benefits of resumable evaluation:**
- ✅ Maintain context across multi-phase validation
- ✅ Compare before/after metrics incrementally
- ✅ Track validation progress for complex plans
- ✅ Resume interrupted evaluations without losing work

## Related Skills

- **fact-query**: Query specific facts from FACTS.parquet for detailed metrics
- **query-pack**: Execute pre-built query bundles for scorecards

## Implementation Notes

### What to Verify (Priority Order)

1. **Critical Claims** (must verify):
   - File LOC counts
   - Function/class complexity (CC)
   - SRP violations count
   - Specific violation examples (main(), FactStore, etc.)

2. **Important Claims** (should verify):
   - Governance violation breakdown
   - Fan-out/fan-in metrics
   - Nesting depth
   - Documentation violations

3. **Nice to Verify** (optional):
   - Architecture patterns
   - Coupling analysis
   - Layer violations

### Common Discrepancies

- **LOC drift**: Plan may be outdated (file changed since plan written)
  - **Action**: Note in assessment, recalculate predicted impact

- **Violation count drift**: Governance rules may have changed
  - **Action**: Verify rules version, note in risks

- **New violations**: Code changed since plan
  - **Action**: Recommend plan update before execution

### Red Flags (Automatic NO-GO)

- ❌ **Claimed violations don't exist** - Plan based on false assumptions
- ❌ **Target file doesn't exist** - Plan references wrong path
- ❌ **LOC mismatch >20%** - Plan severely outdated
- ❌ **Complexity claims off by >50%** - Unreliable metrics

### Green Lights (Strong GO Signal)

- ✅ **All claims verified exactly** - Plan empirically grounded
- ✅ **Multiple independent metrics confirm** - Cross-validated
- ✅ **Tool validates its own violations** - Dogfooding (like we just did)
- ✅ **Clean Table enforced** - Quality gates at each phase

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 0: Reading Target File Before Querying Facts (CRITICAL VIOLATION)

**Wrong**:
```bash
# Evaluate plan
Read("REFACTOR_PLAN.md")           # OK
Read("implementation_file.py")      # ❌ FORBIDDEN - DO NOT DO THIS!
# Manually count lines, estimate complexity...
```

**Right**:
```bash
# Evaluate plan
Read("REFACTOR_PLAN.md")                              # OK - Read the plan only
Bash("uv run ... fact_file_query_tool query ...")     # ✅ Query facts FIRST
Task(subagent_type="governance-check", ...)           # ✅ Use agents for validation
# Only if absolutely necessary:
Bash("wc -l implementation_file.py")                  # Last resort for file LOC
```

**Why it matters**:
- Reading 5,000-line files wastes tokens and time
- Manual analysis is subjective and error-prone
- FACTS.parquet has precise, verifiable metrics
- **This is the #1 most common mistake - never read the target implementation file until you've exhausted fact queries**

**Hard rule**: The ONLY file you should Read() during evaluation is the refactor plan (REFACTOR_*.md). Everything else must come from fact-file-query-tool.

---

### ❌ Anti-Pattern 1: Assumed Metrics

**Wrong**:
```markdown
Plan claims: "main() is very complex"
Evaluation: "Yes, the function does look complex" ✅ CONFIRMED
```

**Right**:
```markdown
Plan claims: "main() has CC=368"
Fact query: `query --entity 'function.main' --keys complexity`
Actual: CC=368
Evaluation: ✅ CONFIRMED (exact match)
```

**Why it matters**: "Very complex" is subjective. CC=368 is measurable and verifiable.

---

### ❌ Anti-Pattern 2: Approximation Acceptance

**Wrong**:
```markdown
Plan: "About 300 lines"
Actual: 346 lines
Evaluation: ✅ CONFIRMED (close enough)
```

**Right**:
```markdown
Plan: "About 300 lines"
Actual: 346 lines (queried)
Evaluation: ⚠️ CLOSE (15% drift, plan may be outdated)
Recommendation: Update plan to reflect actual 346 LOC
```

**Why it matters**: 15% drift suggests the plan is stale. Precision matters for effort estimation.

---

### ❌ Anti-Pattern 3: Missing Fact Sources

**Wrong**:
```markdown
✅ Verified Claims:
- File is 4,944 lines
- main() is highly complex
- Many violations exist
```

**Right**:
```markdown
✅ Verified Claims:
1. **File LOC**: 4,944
   - Source: `wc -l fact_file_query_tool.py`
   - Status: ✅ CONFIRMED

2. **main() complexity**: CC=368
   - Source: `query --entity 'function.main' --keys complexity`
   - Status: ✅ CONFIRMED

3. **Governance violations**: 47
   - Source: `governance-check agent output`
   - Status: ❌ FALSE (plan claimed 18)
```

**Why it matters**: Claims without sources are unverifiable and untrustworthy.

---

### ❌ Anti-Pattern 4: Reading Code Instead of Querying

**Wrong**:
```bash
# Evaluate plan
Read("REFACTOR_PLAN.md")           # OK
Read("implementation_file.py")      # ❌ WRONG
# Manually count lines, estimate complexity...
```

**Right**:
```bash
# Evaluate plan
Read("REFACTOR_PLAN.md")                           # OK
Bash("query --entity 'function.main' --keys ...")  # ✅ CORRECT
Task(subagent_type="governance-check", ...)        # ✅ CORRECT
```

**Why it matters**: Manual analysis is slow, error-prone, and can't be independently verified.

---

### ❌ Anti-Pattern 5: Trusting Plan Without Verification

**Wrong**:
```markdown
Plan says there are 18 violations.
Recommendation: PROCEED (plan looks good)
```

**Right**:
```markdown
Plan says: 18 violations
Query result: 47 violations (162% more than claimed)
Recommendation: REVISE (plan significantly underestimates scope)
```

**Why it matters**: Plans can be outdated, optimistic, or based on faulty assumptions. Always verify.

---

## Success Criteria

An evaluation is complete when:
- [ ] All major claims verified (LOC, CC, violations)
- [ ] **Every claim has a fact source** (mandatory)
- [ ] Comparison table created (plan vs actual)
- [ ] Assessment provided for each phase
- [ ] Risks identified **with evidence**
- [ ] Predicted impact quantified **from queries**
- [ ] Final verdict given (GO/NO-GO/REVISE)
- [ ] Confidence level stated with **fact-based rationale**
- [ ] ≥90% of critical claims verified with ≤10% drift

---

## Notes

- **This skill prevents over-engineering**: Verifying claims ensures effort matches problem size
- **Empirical validation**: All claims must be backed by fact-file-query-tool output
- **Living plans**: Plans should be re-evaluated if codebase changes significantly
- **Dogfooding**: Using the tool to validate its own refactoring plan (like we did) is ideal validation
- **Fact-driven paradigm**: "I think..." → "I queried..." / "About..." → "Exactly..."
