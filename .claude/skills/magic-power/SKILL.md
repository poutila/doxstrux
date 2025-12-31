---
name: magic-power
description: MANDATORY - Always use fact-file-query-tool for analyzing Python code. Query FACTS.parquet instead of reading files. Reading = guessing. Facts = deterministic truth. Use plain Read only if facts don't have the answer (<1% of cases).
allowed-tools: Bash, Read, fact-file-query-tool
---

# Magic Power: Query Facts, Never Guess from Code

**CORE RULE**: Query FACTS.parquet for Python code analysis. Only read files for implementation details (<1%).

## Why Query Facts

| Reading Files | Querying FACTS.parquet |
|--------------|------------------------|
| Guessing, manual parsing | AST-derived, deterministic |
| Miss nested code | Complete extraction |
| Subjective interpretation | Objective metrics |
| No call graphs | Built-in relationships |
| Slow (minutes) | Fast (10-100ms) |
| "About 20 lines?" | "LOC: 23" (exact) |

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

## Anti-Patterns to Avoid

### ❌ Don't Read to Get Signatures
```
User: "What's the signature of authenticate()?"
WRONG: Read(api.py) → search for "def authenticate" → guess params
RIGHT: fact-file-query-tool query --file api.py --entity function.authenticate --keys signature
```

### ❌ Don't Grep to Find Callers
```
User: "What calls process_request()?"
WRONG: Grep("process_request") → read each file → verify calls
RIGHT: fact-file-query-tool query --file engine.py --entity function.process_request --keys callers fan_in
```

### ❌ Don't Read to Count Complexity
```
User: "Is validate() too complex?"
WRONG: Read file → count if/for/while → estimate "7-8 maybe..."
RIGHT: fact-file-query-tool query --file validator.py --entity function.validate --keys cyclomatic_complexity loc
```

### ❌ Don't Read for Security Review
```
User: "Any security issues?"
WRONG: Read files → manually look for eval/exec/secrets → miss nested issues
RIGHT: fact-file-query-tool security
```

## Decision Rule

```
Python code analysis? → Check if FACTS covers it (99% yes) → Query FACTS
                     ↘ FACTS doesn't have it (1%) → Read file
```

## What FACTS Cover (Use These)

| Question | Command | Don't Read |
|----------|---------|------------|
| Signature? | `query --keys signature` | ❌ |
| Complexity? | `query --keys cyclomatic_complexity loc` | ❌ |
| Who calls it? | `query --keys callers fan_in` | ❌ |
| What does it call? | `query --keys callees fan_out` | ❌ |
| Exceptions? | `query --keys raised_exceptions` | ❌ |
| Security issues? | `security` | ❌ |
| Performance issues? | `performance` | ❌ |
| Magic numbers? | `magic-numbers` | ❌ |
| Type coverage? | `query --keys typed_param_ratio return_typed` | ❌ |
| State mutations? | `query --keys attrs_written global_writes` | ❌ |
| SOLID violations? | `solid-srp`, `solid-lsp` | ❌ |

## When to Read Files (<1%)

| Case | Why | Example |
|------|-----|---------|
| Implementation logic | Algorithm specifics not in facts | "How does the sorting work internally?" |
| Comment content | Only docstrings extracted | "What's in the TODO comment?" |
| String literals | Structure only, not values | "Exact error message text?" |
| Config files | Not Python code | JSON, YAML, TOML |
| Documentation | Not code | README, markdown |

## Quick Commands

### Always Check Freshness First
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
echo "🔍 Running Magic Power..."
uv run fact-file-query-tool freshness
echo "✅ Magic Power passed"
```

### Query Specific Facts
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
echo "🔍 Running Magic Power..."
uv run fact-file-query-tool query --file <file>.py --entity function.<name> --keys signature cyclomatic_complexity loc
echo "✅ Magic Power passed"

uv run fact-file-query-tool query --file <file>.py --entity function.<name> --keys callers callees fan_in fan_out

uv run fact-file-query-tool query --file <file>.py --entity function.<name> --keys dangerous_calls shell_calls hardcoded_secrets
```

### Specialized Agents
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
echo "🔍 Running Magic Power..."
uv run fact-file-query-tool governance          # Overall quality
echo "✅ Magic Power passed"

uv run fact-file-query-tool security            # Security audit

uv run fact-file-query-tool performance         # Performance issues

uv run fact-file-query-tool test-gaps           # What needs tests

uv run fact-file-query-tool magic-numbers       # Magic number detection

uv run fact-file-query-tool solid-srp           # SRP violations
```

### List Entities
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
echo "🔍 Running Magic Power..."
uv run fact-file-query-tool entities --file <file>.py                # All entities
echo "✅ Magic Power passed"

uv run fact-file-query-tool manifest --file <file>.py                # Fact families per entity
```

## Workflow Example

**User**: "Analyze authenticate() in auth.py"

**Wrong** (5-10 min, incomplete):
1. Read auth.py (500 lines)
2. Find function
3. Manually count metrics
4. Guess what it calls
5. Subjective assessment

**Correct** (10 sec, complete):
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
echo "🔍 Running Magic Power..."
uv run fact-file-query-tool freshness
echo "✅ Magic Power passed"

uv run fact-file-query-tool query \
```

Output (deterministic):
```yaml
signature: "authenticate(username: str, password: str) -> Token | None"
cyclomatic_complexity: 8
loc: 35
callers: ["api.login", "middleware.auth_check"]
callees: ["db.get_user", "hash.verify", "token.create"]
fan_in: 2
fan_out: 3
raised_exceptions: ["AuthenticationError", "DatabaseError"]
dangerous_calls: []
```

## Entity Path Format

| Type | Format | Example |
|------|--------|---------|
| Module | `module` | `module` |
| Function | `function.<name>` | `function.parse_query` |
| Class | `class.<name>` | `class.FactStore` |
| Method | `class.<class>.method.<name>` | `class.FactStore.method.query` |
| Nested | `function.<outer>.function.<inner>` | `function.process.function.validate` |

## Key Fact Families

| Family | Contains | Use For |
|--------|----------|---------|
| `identity` | kind, name, qualname, visibility, lines | Basic info |
| `signature` | params, return type, decorators | Function signatures |
| `complexity` | LOC, cyclomatic, nesting, params | Complexity metrics |
| `behavior` | callers, callees, fan_in, fan_out | Call graphs |
| `errors` | raised_exceptions, guards | Exception handling |
| `side_effects` | attrs_written, global_writes | State mutations |
| `security` | dangerous_calls, shell_calls, secrets | Security issues |
| `dependencies` | imports, exports | Module structure |
| `type_safety` | typed_param_ratio, return_typed | Type coverage |
| `performance` | perf_nested_loops, perf_io_in_loop | Performance |

## Three-Step Check Before Reading Python Files

1. **Could FACTS have this?** → 99% yes
2. **Checked freshness?** → Run `freshness` command
3. **Know the fact key?** → Use `get-schema` to see 230 keys

Only if "FACTS doesn't have this" → Read file

## Common Use Cases

### Code Review
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
echo "🔍 Running Magic Power..."
uv run fact-file-query-tool freshness
echo "✅ Magic Power passed"

uv run fact-file-query-tool query --file billing.py --entity function.calculate_total --families complexity errors security type_safety

uv run fact-file-query-tool governance --file billing.py

uv run fact-file-query-tool magic-numbers --file billing.py

uv run fact-file-query-tool security --file billing.py
```

### Impact Analysis
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
echo "🔍 Running Magic Power..."
uv run fact-file-query-tool blast-radius --file email.py --entity function.send_email
echo "✅ Magic Power passed"
```

### Architecture Understanding
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
echo "🔍 Running Magic Power..."
uv run fact-file-query-tool architecture
echo "✅ Magic Power passed"

uv run fact-file-query-tool query --file auth.py --entity module --families dependencies imports exports

uv run fact-file-query-tool query --file auth.py --entity function.authenticate --keys callers callees
```

## Summary

**Rule**: Query FACTS first. Read files last (if at all).

**Default for Python code analysis**:
1. Check freshness
2. Query facts
3. Analyze results
4. Only read if facts don't have it (<1%)

Reading = guessing. Querying = knowing with certainty.
