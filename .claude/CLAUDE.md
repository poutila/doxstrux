# CLAUDE.md

## Read this FIRST to understand why to use `fact-file-query-tool`

**🚀 RUN THESE NOW** (30 seconds):

```bash
# See the proof: 60x productivity multiplier, 185 files in 12H vs 3 files manually
uv run fact-file-query-tool parquet-help --section productivity_evidence --item real_world_sprint

# See the speed: 100-3000x faster than reading files (0.1-0.5s vs 1-5 minutes per query)
uv run fact-file-query-tool parquet-help --section key_takeaways --item speed_comparison
```
**The productivity_evidence section converts skepticism into adoption with hard numbers.**

📋 Structured Reference

**Quick preview of time savings**:
- Exercise 1: Find high-complexity functions (15 min → 3 sec)
- Exercise 2: Get method signature (2 min → 0.3 sec)
- Exercise 3: Security audit (30 min → 2 sec)
- Exercise 4: Architecture overview (2 hours → 1 sec)

---

## 📦 For AI Assistants: Auto-Discover Package Documentation

## 📑 Quick Navigation

**Start Here**:
- [🎬 You've Seen the Proof](#youve-seen-the-proof---now-use-it) - New workflow (MANDATORY)
- [🚨 Using the Tools](#critical-using-the-tools-weve-built) - fact-query, agents, governance

**Planning & Development**:
- [🤖 FDP Protocol](#ai-assistants-fact-driven-planning-protocol) - Evidence-based planning
- [🏗️ Project Structure](#project-structure) - Directory layout

**Reference**:
- [📖 Project Overview](#project-overview)
- [🎯 Development Workflow](#development-workflow)
- [🧪 Testing](#testing)
- [⚠️ Known Issues](#known-issues--recommendations)

**Contributing**:
- [🎓 For New Contributors](#for-new-contributors)

---

## 🎬 You've Seen the Proof - Now Use It

### ⚠️ MANDATORY CHECKPOINT - Do NOT proceed until complete

**Complete these tasks before reading further:**

- [ ] **I have run the first command** (`parquet-help --section productivity_evidence --item real_world_sprint`)
- [ ] **I have run the second command** (`parquet-help --section key_takeaways --item speed_comparison`)
- [ ] **I have read the output** and understand: 60x productivity multiplier, 100-3000x speedup
- [ ] **I acknowledge** this tool changes my workflow permanently

**You cannot appreciate the tool until you've USED it.** The commands above are not optional.

If you have not completed ALL checkboxes above, go back to the top and run the commands NOW.

### Your New Workflow (MANDATORY)

**Before ANY code analysis**:

```bash
# Step 1: Check what facts are available
uv run fact-file-query-tool parquet-help --list-families  # See all 37 families

# Step 2: Query instead of read
uv run fact-file-query-tool query --file <file> --entity <entity> --families <families>
```

**Old habit** ❌: Read file → understand code → answer question
**New habit** ✅: Query facts → get instant answer → move on

### 📚 Quick Reference: Common Mistakes

From `key_takeaways.common_mistakes`:
- ❌ **Guessing entity names** → 90% empty results
- ❌ **Skipping manifest check** → Wasted time on empty families
- ❌ **Inferring facts from code** → Hallucination risk
- ❌ **Reading files for analysis** → 100-3000x slower

✅ **Correct workflow**: `entities → manifest → query` (see three_step_workflow)

### 🚀 Next Steps

```bash
# Learn all available commands
uv run fact-file-query-tool parquet-help --section commands

# Master the 3-step workflow
uv run fact-file-query-tool parquet-help --section three_step_workflow

# Browse all documentation sections
uv run fact-file-query-tool parquet-help --list-sections
```

**Remember**: These exercises aren't hypothetical - you just ran them. The tool works, the speedup is real, and **reading files is now your LAST resort, not first instinct.**

### ✅ Test Your Understanding

**Before proceeding to the rest of this documentation, answer these questions:**

1. **Q**: How much faster is fact-querying than file reading?
   - **A**: 100-3000x (0.1-0.5s vs 1-5 minutes)

2. **Q**: What's the 3-step workflow?
   - **A**: `entities → manifest → query`

3. **Q**: What happens if you guess entity names?
   - **A**: 90% empty results

4. **Q**: When should you read files?
   - **A**: LAST resort (after exhausting fact queries)

### ⚠️ SECOND CHECKPOINT - Verify understanding

**Confirm you can answer all questions above:**

- [ ] **I can answer question 1** (speedup is 100-3000x)
- [ ] **I can answer question 2** (3-step workflow: entities → manifest → query)
- [ ] **I can answer question 3** (guessing names = 90% empty results)
- [ ] **I can answer question 4** (read files as LAST resort only)
- [ ] **I commit** to using fact-file-query-tool BEFORE reading files

**If you cannot check ALL boxes above**, re-run the commands at the top and read the output carefully..

## 📖 Project Overview

**[PROJECT_NAME]** - [Brief one-line description]

[Brief 2-4 sentence description of what this project does and its key characteristics]

**Architecture**: `[PRIMARY_SOURCE_DIR]/` contains [description of main components]
**Status**: [Development|Production-ready], [key metrics or status indicators]

## 🚨 CRITICAL: Using the Tools We've Built

**READ THIS FIRST**: [USING_TOOLS.md](USING_TOOLS.md) _(if you have project-specific tooling documentation)_

We've built powerful tools that are **USELESS if not used**:
- ✅ **[Tool/Skill 1]** - [Purpose and when to use]
- ✅ **[Tool/Skill 2]** - [Purpose and when to use]
- ✅ **[Configuration files]** - [What they define]

**MANDATORY workflows**:

1. **BEFORE [common action 1]**:
   - Check if [prerequisite or better approach]
   - Command: `[example command]`

2. **BEFORE [common action 2]**:
   - Check if [prerequisite or better approach]
   - Reference [documentation or rules]

**Quick reference**:
```bash
# [Common task 1]
[command or approach]

# [Common task 2]
[command or approach]
```

**🎵 These tools are an instrument - you must play it!**

## 🤖 AI Assistants: Fact-Driven Planning Protocol

**MANDATORY** when implementing features or planning code changes:

**Read First**: [FDP/FDP_AI_WORKFLOW.md](FDP/FDP_AI_WORKFLOW.md) _(if using FDP)_

### Core Principle

**Query code facts BEFORE making design decisions.** Every claim must be backed by evidence blocks with runnable `verification_command`.

Evidence blocks are REQUIRED for:
- **Schema assumptions** (YAML/JSON/Parquet structure) — never infer, always verify
- **Uniqueness claims** (entity collisions) — measure collision rate before deciding API design
- **Import paths** (module locations) — verify filesystem before writing imports
- **Contract definitions** (CLI ↔ API alignment) — enforce with contract tables + end-to-end tests

### Self-Check: "Probably Detector"

Before delivering any plan, run this check on your output:
```bash
grep -E '\b(probably|should|seems|verified|confirmed)\b' your_plan.md
```

If matches found **without** corresponding `fact_query:` evidence blocks → **STOP and add evidence**.

### Quality Gate: "9am Implementer Test"

Ask: **"Can a fresh implementer execute this plan at 9am tomorrow without guessing?"**

If NO → plan has ambiguities. Common causes:
- Claims without evidence blocks
- Schema parsed without reading actual file
- Import paths guessed instead of verified
- CLI/API semantics diverge (contract drift)

### Quick Reference

**Failure modes** to avoid:
- Treating FDP as documentation style instead of circuit-breaker workflow
- Assuming uniqueness without measuring collisions
- Inferring schema without reading files
- Guessing import paths instead of `ls` verification
- Writing "verified" without `verification_command`
- Designing patch points after implementation (late imports → broken monkeypatch)

**Documentation** _(adjust paths as needed)_:
- **Protocol**: [FDP/FDP_AI_WORKFLOW.md](FDP/FDP_AI_WORKFLOW.md) (phases, gates, examples)
- **Playbook**: [FDP/FDP_OPERATIONS.md](FDP/FDP_OPERATIONS.md) (templates, decision ledger)
- **Schema**: [FDP/FDP_SCHEMA.md](FDP/FDP_SCHEMA.md) (evidence block structure)

**Rule Files**: See [rules/RULES.md](rules/RULES.md) for complete documentation on all governance rules, workflows, and tool usage.

## 🏗️ Project Structure

```
[project_root]/
├── pyproject.toml                         # Package configuration
├── uv.lock / requirements.txt            # Dependencies
├── README.md                             # Main documentation
│
├── src/[package_name]/                   # Production code (src-layout)
│   ├── __init__.py                       # Package exports
│   ├── [primary modules]                 # Core functionality
│   └── [supporting modules]              # Utilities, helpers
│
├── tests/                                # Test suite
│   ├── test_*.py                         # Test modules
│   └── conftest.py                       # Pytest configuration
│
├── [additional directories]              # Project-specific
│   ├── [docs/]                           # Documentation
│   ├── [scripts/]                        # Utility scripts
│   └── [examples/]                       # Usage examples
│
├── .claude/                              # Claude-specific config
│   ├── CLAUDE.md                         # This file
│   ├── rules/                            # Governance rules
│   └── agents/                           # Sub-agents
│
└── [configuration files]                 # .gitignore, etc.
```

## 🎯 Development Workflow

### Quick Commands

```bash
# Setup environment
uv venv                    # or: python -m venv .venv
uv sync                    # or: pip install -e ".[dev]"

# Run tests
uv run pytest tests/ -v

# Run [main application/tool]
uv run [command]

# Code quality checks
[linting/formatting commands]
```

### Common Tasks

**[Task 1: e.g., Running validation]**
```bash
[commands and explanation]
```

**[Task 2: e.g., Generating documentation]**
```bash
[commands and explanation]
```

**[Task 3: e.g., Building/deploying]**
```bash
[commands and explanation]
```

## 📊 Quality Standards

### Code Quality Metrics

- **Test Coverage**: [target]% (measure: `[coverage command]`)
- **Type Coverage**: [target]% (measure: `[type checking command]`)
- **Linting**: [standard] (enforce: `[linting command]`)
- **Formatting**: [standard] (enforce: `[formatting command]`)

### Governance Rules

Governance rules define:
- Complexity thresholds
- Documentation requirements
- Security requirements
- Performance benchmarks

**Never guess quality standards** - always reference [rules/RULES.md](rules/RULES.md) for complete documentation.

## 🔍 File Organization Summary

### Production Code (USE THESE)
- **`src/[package_name]/`** - [Number] modules ([description])
- **`tests/`** - Test suite ([number] tests)

### Documentation
- **`README.md`** - Main documentation
- **`.claude/CLAUDE.md`** - This file
- **[other key docs]** - [Purpose]

### Reference Files (READ-ONLY)
- **[reference file]** - [Purpose]. **DO NOT MODIFY.**

### Configuration
- **`pyproject.toml`** - Package configuration
- **`uv.lock`** - Dependency lockfile
- **`.venv/`** - Virtual environment

## 📈 Performance & Metrics

### [Relevant Metrics Section]

- **[Metric 1]**: [Value/target]
- **[Metric 2]**: [Value/target]
- **[Metric 3]**: [Value/target]

## 📚 Key APIs

```python
# [Core API 1]
from [package].[module] import [function]
result = [function](args)

# [Core API 2]
from [package].[module] import [class]
instance = [class](args)

# [Core API 3]
from [package].[module] import [function]
output = [function](args)
```

## ⚠️ Known Issues & Recommendations

### 1. [Issue Category 1]

**Status**: [✅ Complete | ⚠️ In Progress | 🚧 Planned]
**Impact**: [Description]
**Fix**: [Solution or next steps]
**Priority**: [P0|P1|P2|P3]

### 2. [Issue Category 2]

**Status**: [Status indicator]
**Impact**: [Description]
**Fix**: [Solution or next steps]
**Priority**: [P0|P1|P2|P3]

## 🎓 For New Contributors

### First-Time Setup

```bash
# 1. Clone repository
cd [path/to/project]

# 2. Setup environment
uv venv                    # or: python -m venv .venv
uv sync                    # or: pip install -e ".[dev]"

# 3. Verify environment
uv run python --version    # Should show [version requirement]

# 4. Set environment variables (if needed)
export [VAR_NAME]="[value]"

# 5. Verify installation
uv run [verification command]
uv run pytest tests/ -v
```

### Daily Development

```bash
# Check project status
cat README.md              # Main documentation
cat [key_spec_file]        # Primary specification

# Run [main tool/application]
uv run [command]

# Run tests
uv run pytest tests/ -v

# Add new dependency
uv add package-name

# Sync dependencies
uv sync
```

### Understanding the Codebase

1. **Start here**: `README.md` (main documentation)
2. **Architecture**: `[architecture_doc]` (system design)
3. **Quick start**: `[quickstart_doc]` (getting started)
4. **Contributing**: `[contributing_doc]` (contribution guidelines)
5. **Code quality**: [Quality standards and analysis]

## 🔗 Additional Resources

### Documentation Links

- [Key documentation 1]
- [Key documentation 2]
- [External resources]

### Community & Support

- [Issue tracker]
- [Discussions/Forum]
- [Contributing guidelines]

---

**Last Updated**: [YYYY-MM-DD]
**Status**: [Development|Alpha|Beta|Production-Ready]
**Version**: [X.Y.Z]
**Python**: [version requirement]
**Package**: `[package-name]`
**Tests**: [passing/total] ([coverage]%)
**Dependencies**: [key dependencies]
