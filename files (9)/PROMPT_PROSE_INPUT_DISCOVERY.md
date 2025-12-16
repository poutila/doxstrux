# PROMPT: PROSE INPUT DISCOVERY (see VERSION.yaml for framework version)

> **Role**: You are a project analyst helping gather facts needed to fill in the prose input template.
>
> **Goal**: Extract concrete, copy-pasteable information from the codebase. NO reasoning, NO decisions - just facts.
>
> **Output**: A structured report the user can use to fill in template placeholders.

---

## Instructions

Run the discovery commands below against the target project. For each section, output the ACTUAL results - not descriptions or summaries.

The user will then copy these facts into their prose input document.

---

## Discovery Sections

### 1. Project Metadata

**Commands to run:**

```bash
# Project name (from pyproject.toml or package.json)
grep -E "^name\s*=" pyproject.toml || grep '"name"' package.json | head -1

# Python version (if Python project)
grep -E "requires-python|python_requires" pyproject.toml

# Package manager / runner
ls -la pyproject.toml uv.lock poetry.lock package-lock.json Cargo.toml go.mod 2>/dev/null | head -5
```

**Output format:**

```
PROJECT_NAME: [[actual name]]
RUNNER: [[uv | npm | cargo | go | poetry]]
RUNNER_PREFIX: [[uv run | npx | cargo run | go run | poetry run]]
SEARCH_TOOL: [[rg | grep]]
```

---

### 2. Directory Structure

**Commands to run:**

```bash
# Source directories
find . -type d -name "src" -o -name "lib" -o -name "pkg" 2>/dev/null | head -10

# Test directories
find . -type d -name "tests" -o -name "test" -o -name "__tests__" 2>/dev/null | head -10

# Tools/scripts directories
find . -type d -name "tools" -o -name "scripts" -o -name "bin" 2>/dev/null | head -10
```

**Output format:**

```
SOURCE_ROOT: [[path]]
TEST_ROOT: [[path]]
TOOLS_ROOT: [[path]]
```

---

### 3. Existing Files in Target Area

**Commands to run (adapt paths to your project):**

```bash
# List files in the area you'll be modifying
ls -la [[TARGET_DIRECTORY]]/

# List existing test files
ls tests/test_*.py 2>/dev/null || ls **/*.test.ts 2>/dev/null | head -20
```

**Output format:**

```
EXISTING_FILES:
- [[file1]]
- [[file2]]
- ...

EXISTING_TESTS:
- [[test1]]
- [[test2]]
- ...
```

---

### 4. Dependencies (Current State)

**Commands to run:**

```bash
# Python dependencies
grep -A 50 "^\[project\]" pyproject.toml | grep -A 30 "^dependencies" | head -30

# Or from requirements.txt
cat requirements.txt 2>/dev/null | head -20

# Node dependencies
cat package.json | jq '.dependencies, .devDependencies' 2>/dev/null | head -30
```

**Output format:**

```
CURRENT_DEPENDENCIES:
- [[package1]] [[version]]
- [[package2]] [[version]]
- ...
```

---

### 5. Sample Outputs (Critical for Schema Work)

**Commands to run (adapt to your project):**

```bash
# If implementing schema/validation, get actual current output shape
# Example for a parser:
[[RUNNER_PREFIX]] python -c "
import json
from [[your_module]] import [[YourClass]]
result = [[YourClass]]([[sample_input]]).[[method]]()
print(json.dumps(result, indent=2, default=str))
"
```

**Output format:**

```json
SAMPLE_OUTPUT:
[[paste actual JSON output here]]
```

---

### 6. CI/Workflow Files

**Commands to run:**

```bash
# GitHub Actions
ls -la .github/workflows/ 2>/dev/null

# GitLab CI
ls -la .gitlab-ci.yml 2>/dev/null

# Other CI
ls -la Jenkinsfile Makefile justfile 2>/dev/null
```

**Output format:**

```
CI_FILES:
- [[workflow1.yml]]
- [[workflow2.yml]]
```

---

### 7. Symbols to Depend On

**Commands to run:**

```bash
# Find key classes/functions you'll depend on
rg "^(class|def|function|export)" [[TARGET_DIRECTORY]]/ | head -30

# Find imports you'll need
rg "^from|^import" [[TARGET_DIRECTORY]]/__init__.py 2>/dev/null | head -20
```

**Output format:**

```
KEY_SYMBOLS:
- [[ClassName]] in [[file.py]]
- [[function_name]] in [[file.py]]
- ...
```

---

### 8. Test Command Patterns

**Commands to run:**

```bash
# Check existing test invocation patterns
grep -r "pytest\|jest\|cargo test\|go test" Makefile justfile .github/workflows/* 2>/dev/null | head -10

# Check coverage settings
grep -A 5 "\[tool.pytest\]" pyproject.toml 2>/dev/null
```

**Output format:**

```
TEST_COMMAND: [[actual command used]]
COVERAGE_COMMAND: [[if any]]
```

---

## Discovery Report Template

After running the commands above, compile results into this format:

```markdown
# Project Discovery Report for [[PROJECT_NAME]]

Generated: [[DATE]]

## 1. Project Metadata
- **Project Name**:
- **Runner**:
- **Runner Prefix**:
- **Search Tool**:
- **Python Version**:

## 2. Directory Structure
- **Source Root**:
- **Test Root**:
- **Tools Root**:

## 3. Existing Files
### In Target Directory
(paste ls output)

### Existing Tests
(paste test file list)

## 4. Current Dependencies
(paste from pyproject.toml/package.json)

## 5. Sample Output
(paste actual JSON/output if relevant)

## 6. CI Configuration
(list workflow files)

## 7. Key Symbols to Depend On
(list classes/functions)

## 8. Test Patterns
- **Test Command**:
- **Coverage Command**:

---

**Ready to fill in PROSE_INPUT_TEMPLATE_v1.md**
```

---

## Usage

1. **Human runs this prompt** with AI assistant that has codebase access
2. AI executes discovery commands and compiles report
3. Human uses report to fill in `PROSE_INPUT_TEMPLATE_v1.md` placeholders
4. Human runs `tools/prose_input_linter.py` to validate
5. Human submits for AI semantic review (`PROSE_INPUT_REVIEW_PROMPT_v1.md`)

---

## Why Discovery First?

| Without Discovery | With Discovery |
|-------------------|----------------|
| AI guesses file structure | AI knows exact paths |
| AI searches for dependencies | User provides dependency list |
| AI might create naming conflicts | User lists existing files |
| AI guesses test patterns | User provides actual commands |
| Multiple iteration loops | Single informed attempt |

**Principle**: Facts over inference. Paste over search.

---

**End of Prompt**
