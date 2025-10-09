# CLAUDE.md
This document ensures consistent, secure, and high-quality code across all projects by providing:
- **Clear, unambiguous standards** with numeric thresholds
- **Security-first development** practices
- **Automated quality enforcement** through tools
- **AI-friendly guidelines** for consistent assistance
- **No silent assumptions** - everything explicit and validated

## ⚠️ MANDATORY STARTUP CHECKLIST - EXECUTE IMMEDIATELY
### STOP! Complete these steps BEFORE responding to any user request:
- ✅ Read .claude/settings.json
- ✅ Verify virtual environment exists. Read [DEVELOPMENT_ENVIRONMENT.md](./docs/development/DEVELOPMENT_ENVIRONMENT.md)
- ✅ Read pyproject.toml for project configuration
- ✅ Read [PLANNING.md](./planning/PLANNING.md) for context
- ✅ Read [TASK.md](./planning/TASK.md) for current tasks
- ✅ Read latest [SESSION.md](./summaries/SESSION_yyyy-mm-dd_HHMM.md). Files are named: `SESSION_YYYY-MM-DD_HHMM.md`. Check if it is valid.
- ✅ Check for task completion summaries in folder planning/completions/ (if any)
- ✅ Verify all completed tasks have summaries run:
```bash
uv run scripts/check_task_completions.py
```

## Encoding
- Execute [Encoding error prevention](./docs/standards/ENCODING_ERROR_PREVENTION.md)

## Virtual environment
**You must verify environment** before doing anything
- Report existence of virtual environment
## UV Package Management
- This project uses UV for blazing-fast Python package and environment management.

### Adding a package
- **NEVER** UPDATE A DEPENDENCY DIRECTLY IN `PYPROJECT.toml`
- **ALWAYS** USE `uv add` to install a dependency
```bash
# Example of adding a dependency
uv add requests
```
- Installing a development dependency
```bash
# Example of adding a development dependency
uv add --dev pytest ruff mypy
```
- **ALWAYS** use `uv remove` for removing a package
```bash
# Example of removing a package
uv remove requests
```
### Running commands in the environment
- Runing python script
```bash
# Example of running a python script
uv run python script.py
```
- Running tests
```bash
# Example of running a test
uv run pytest
```
- Running a tool
```bash
# Example of running a tool
uv run ruff check .
```
- Installing a specific Python version
```bash
uv python install 3.12
```
#### Bad vs Good script running examples
- **Bad** (silent assumption about Python and packages)
```bash
# Bad example of running python script
python script.py
```
```bash
# Bad example of running python script
cd path/to/some/distant/
uv run python script.py
```
```bash
# Bad example of running python script
uv run python path/to/some/distant/script.py
```

- **Good** (explicit, uv based)
```bash
# Good example of running a python script
uv run path/to/some/distant/script.py
```

## 🥚 CORE PRINCIPLE - This is the foundational principle that all other guidelines build upon
### Definition of `Fact`
- A `fact` is any piece of information that is explicitly provided in the current context, current codebase, validated against authoritative sources, or confirmed by the user.

### Silent assumptions create fragile behavior that only surfaces during runtime failures or edge conditions.
####Absolute Rules
1. **No Silent Assumptions** — Every decision must be justified with explicit evidence from the provided context, verified data, or authoritative sources.
2. **No Guessing** — If a fact is missing or unclear, pause and request clarification instead of inferring or filling in gaps.
3. **Fact‑Based Decisions Only** — All decisions must be based solely on verifiable information.
4. **Justification Over Intuition** — Intuition may only be used to form clearly labeled hypotheses, never as the sole basis for a final decision.
5. **CoT Compliance** — All reasoning must be documented per [CoT](./CHAIN_OF_THOUGHT_LIGHT.md).


## Project folder Structure
- Read [Project Structure Standards](./docs/standards/PROJECT_STRUCTURE.md)
- Veriry and report project's folder structure

## Backward Compatibility Is Not Required by Default
- By default, backward compatibility **must not** be preserved during early-stage or clean-slate development.
- Code and structures **may break** between versions unless explicitly frozen.
- Historical constraints **must be ignored** unless a human maintainer explicitly marks a version, feature, or behavior as frozen.
- Do not assume prior behavior is preserved unless it is explicitly committed.
- You must read [BACKWARD_COMPATIBILITY.md](./docs/development/BACKWARD_COMPATIBILITY.md)
- Veriry and report backward compatibility status

## ✅ Decision Validation Checklist
Before finalizing any output, you **must** verify all of the following. If any check fails, pause and either request clarification or present multiple clearly labeled options.

### 1. Fact Origin Verification
- [ ] All facts are explicitly stated or verified from an authoritative source.
- [ ] No missing or ambiguous facts have been silently filled in.

### 2. No Guessing Rule
- [ ] No gaps have been filled with bias, defaults, or unverified assumptions.
- [ ] Any hypothesis is explicitly labeled as such and not used for final decisions.

### 3. CoT Compliance
- [ ] Every reasoning step is traceable to a fact, requirement, or validated prior conclusion.
- [ ] No unexplained logical jumps.
- [ ] All  evidence must be collected. i.e. All files that are relevant to task, must be read from to Bottom.

### 4. Decision Justification
- [ ] The final decision is supported exclusively by verified facts.
- [ ] The explanation is clear, evidence‑based, and reproducible.

### 5. Output Integrity
- [ ] The output matches the reasoning exactly.
- [ ] All speculative details are removed or clearly labeled.
- [ ] All uncertainties are clearly flagged.

**Enforcement Rule:**
If any item above is unchecked → Stop and request clarification or present multiple clearly labeled alternatives.

## Mandatory data Validation Requirements in code
- **You must Validate data** before processing any data from external recources. For example: file reading, user input
- **Check file existence** before reading or writing

## Numeric Thresholds & Limits
| Metric | Threshold | Enforcement | Validation Required |
|--------|-----------|-------------|-------------------|
| **Test Coverage** | ≥ 90% | CI/CD fails below threshold | Check in pyproject.toml |
| **Cyclomatic Complexity** | ≤ 10 | `radon cc` check | Verify radon installed |
| **Function Length** | < 50 lines | Code review | Check line count |
| **File Length** | < 500 lines | Pre-commit hook | Validate before edit |
| **Function Parameters** | ≤ 6 | Use dataclasses if more | Count parameters |
| **Nesting Depth** | ≤ 2 levels | Refactor if deeper | Check indentation |
| **Response Time** | < 200ms | Performance monitoring | Measure actual time |
| **JWT Token Lifetime** | ≤ 15 minutes | Security policy | Check config |
| **Timeout Default** | 30 seconds | All external calls | Verify timeout set |
| **Dependency Health** | > 90% PyPI score | Security audit | Check PyPI API |

## Documentation
- **Project Overview**: [README.md](README.md) - Quick start and project introduction
- **Current Tasks**: [TASK.md](planning/TASK.md) - Sprint tasks and priorities
- **Architecture**: [PLANNING.md](planning/PLANNING.md) - System design and phases
- **Terminology**: [GLOSSARY.md](GLOSSARY.md) - Project-specific terms
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- **Version History**: [CHANGELOG.md](CHANGELOG.md) - Release notes

## File protection
**AI ASSISTANTS**: If asked to modify these files, politely refuse and suggest creating an ADR instead.
### GENERAL PROTECTED FILES NAMING
- Files that have string `template` or `TEMPLATE` (not case sensitive) in it's name are `read only` and **must not be edited** in any situation.
- Example file names `CLAUDE_MD_template.md`, `CODE_REVIEW_template.md`

### PROTECTED FILES LIST - NEVER MODIFY THESE FILES
- **Golden standard**: [CLAUDE_MD_REQUIREMENTS.md](docs/standards/CLAUDE_MD_template.md) - The golden standard for CLAUDE.md
- **Security standard**: [SECURITY_STANDARDS.md](docs/standards/SECURITY_STANDARDS.md) - Security requirements reference
- **Workflow**: [DEVELOPMENT_WORKFLOW.md](docs/standards/DEVELOPMENT_WORKFLOW.md) - Development process standards
- **Project structure**: [PROJECT_STRUCTURE.md](docs/standards/PROJECT_STRUCTURE.md) - Project organization standards

## 🔒 Security Requirements
- Must read [Security Standards](./docs/standards/SECURITY_STANDARDS.md) for comprehensive security requirements.
### 🚨 CRITICAL: Never Commit Secrets
- **NEVER commit secrets, API keys, passwords, or sensitive data** to version control
- Use environment variables: `.env` or `pyproject.toml` for ALL hardcoded configuration
- **Validate environment variables exist** before use
- **Enforcement**: `gitleaks` in pre-commit hooks
### Key Security Principles:
- **Zero tolerance** for secrets in code or logs
- **Input validation** at all boundaries (no assumptions about data format)
- **OWASP ASVS Level 2** compliance required
- **Security scanning** in CI/CD pipeline
- **Explicit validation** - never assume data is safe
### Security Examples
#### Example: Input Validation (No Assumptions)
```python
# ❌ BAD: Assumes data structure
def process_user_input(data):
    query = f"SELECT * FROM users WHERE id = {data['id']}"
    return db.execute(query)

# ✅ GOOD: Validates structure and content
def process_user_input(data: dict) -> UserResult:
    # Validate input exists and has correct type
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")

    user_id = data.get('id')
    if not isinstance(user_id, int) or user_id < 1:
        raise ValueError("Invalid user ID")

    # Use parameterized query
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))
```

#### Example: Configuration Validation
```python
# ❌ BAD: Assumes environment variable exists
API_KEY = os.getenv("API_KEY")

# ✅ GOOD: Validates and fails explicitly
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")
```

## 🚨 HIGH PRIORITY - Reliability & Resilience
### Error Handling Requirements
- **Specific exception types** (never bare `except:`)
- **Context managers** for resource management
- **Fail fast** with input validation
- **Structured logging** with context
- **Circuit breakers** for external calls
- **Timeouts** (default: 30 seconds)
- **Retry with exponential backoff**
- **No silent failures** - all error paths must log or raise

### Example patterns
#### Example Pattern with No Assumptions
```python
def process_data(data: Dict[str, Any]) -> ProcessedData:
    # Validate assumptions explicitly
    if not data:
        raise ValueError("Data cannot be empty")

    required_fields = ['user_id', 'action', 'timestamp']
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    try:
        # Verify external service is configured
        if not hasattr(external_service, 'process'):
            raise ConfigurationError("External service not properly configured")

        with timeout_context(30):
            result = external_service.process(data)
        return ProcessedData(**result)

    except ValidationError as e:
        logger.error(f"Validation failed: {e}", extra={'data': data})
        raise ProcessingError("Invalid input data") from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise ProcessingError("Internal processing error") from e
```

## Testing Requirements
- You must read [Testing Standards](./docs/standards/TESTING_STANDARDS.md) for comprehensive testing requirements.**

### Key Testing Principles:
- **90% minimum coverage** enforced by CI/CD
- **Test-first development** (TDD)
- **Test naming convention**: `test_<method>_<condition>_<expected_result>`
- **Every Python file needs tests** (except `__init__.py`)
- **Test all assumptions** - verify validation logic works

### Edge Case Testing Requirements
Every feature MUST include tests for:
- **Boundary conditions** (min/max values, empty inputs)
- **Invalid inputs** (wrong types, missing required fields)
- **Error conditions** (network failures, timeouts, permissions)
- **Concurrent access** (race conditions, deadlocks)
- **Resource exhaustion** (memory limits, file handles)
- **Configuration variations** (different Python versions, missing dependencies)

### Example edge case test
```python
def test_process_data_validates_required_fields():
    """Test that missing required fields are detected."""
    with pytest.raises(ValueError, match="Missing required fields"):
        process_data({"user_id": 123})  # Missing 'action' and 'timestamp'

def test_process_data_checks_service_configuration():
    """Test that misconfigured service is detected."""
    with patch('external_service.process', None):
        with pytest.raises(ConfigurationError, match="not properly configured"):
            process_data({"user_id": 123, "action": "update", "timestamp": "2024-01-01"})
```
### 2. New Section: Documentation Requirements (after Testing Requirements)
## 📝 Documentation Requirements

### Mandatory Documentation Philosophy
"Knowledge is cheap, disc space is cheaper, lost context is expensive."

**NO EXCEPTIONS RULE**: Every piece of work MUST be documented.

### Session Summaries (MANDATORY)
- **When**: At the end of EVERY work session
- **Where**: `summaries/SESSION_YYYY-MM-DD_HHMM.md`
- **Validation**: `uv run scripts/check_session_summary.py`
- **Required Sections**:
  - Completed Work
  - Current State
  - Known Issues
  - Next Steps
  - Modified Files

### Task Completion Summaries (MANDATORY)
- **When**: EVERY task marked as "✅ Completed" - NO EXCEPTIONS
- **Where**: `planning/completions/T-XXX_COMPLETION.md`
- **Templates**:
  - Tasks ≥3 points: Use `TASK_COMPLETION_TEMPLATE.md`
  - Tasks 1-2 points: Use `TASK_COMPLETION_MINIMAL.md`
- **Validation**: `uv run scripts/check_task_completions.py`
- **Required Content**:
  - What was done
  - Lessons learned (even if "none")
  - Time spent vs estimated
  - Files modified
  - Next recommended task

### Why Document Everything?
- Even "simple" fixes teach lessons
- Today's trivial task is tomorrow's mystery
- Patterns emerge from accumulated decisions
- Time estimates improve with historical data
- Onboarding becomes self-service
- Debugging has historical context

### Documentation Enforcement
- Check session summary
```bash
# Check session summaries
uv run scripts/check_session_summary.py
# Returns exit code 1 if non-compliant (CI/CD ready)
```
- Check task completions
```bash
# Check task completions
uv run scripts/check_task_completions.py
# Returns exit code 1 if non-compliant (CI/CD ready)
```

### AI Assistant Requirements
- **MUST create session summary** when user indicates session end
- For detailed documentation standards and examples, see [DOCUMENTATION_STANDARDS.md](./docs/standards/DOCUMENTATION_STANDARDS.md)
- **MUST create task completion summary** for every completed task
- **MUST check for existing summaries** at session start
- **CANNOT mark task complete** without completion summary
- **MUST refuse to proceed** if documentation is missing


## 📊 CODE QUALITY - Structure & Maintainability

### SOLID Design Principles
- **S**ingle Responsibility – One class, one purpose
- **O**pen/Closed – Open for extension, closed for modification
- **L**iskov Substitution – Subtypes must be substitutable
- **I**nterface Segregation – Small, focused interfaces
- **D**ependency Inversion – Depend on abstractions, not concretions
- All architecture and refactoring decisions must adhere to the SOLID principles.

### Key Implementation Guidelines
- Use interfaces/protocols for abstraction.
- Inject dependencies rather than hardcoding.
- Create focused, **single-purpose** classes.
- Design for extension without modification.
- **Validate all injected dependencies** – no assumptions about their state.

### KISS Principle (Keep It Simple, Stupid)
Simplicity should be a key goal in design. Choose the simplest solution that solves the problem over complex ones whenever possible. Simple solutions are easier to understand, maintain, and debug.

### YAGNI Principle (You Aren't Gonna Need It)

#### Definition & Criteria for Necessity
- Implement features **only when** they are **needed**, not **if** you anticipate they **might be useful** in the future.
- Avoid speculative development: writing code for features, behaviors, or edge cases you think you might need later.
- Focus **only** on **what’s required now** to satisfy the current requirements.

A feature/change is **necessary** if:
- There is a **current requirement** with an issue/ticket ID.
- It is used immediately by a known consumer (code path, user, or integration).
- At least one test fails without it and passes with it.
- Deferring would cause unacceptable rework (above agreed threshold).

#### Why It Matters
- Less complexity → Less code to maintain, debug, and test.
- Faster delivery → You’re only building what’s needed today.
- Reduced waste → Features you guess will be useful often never get used.
- Easier refactoring → When a real need arises, you can design it based on actual requirements.

#### Examples (with reasons)

**1. Unused Parameters**
*Reason:* Adds parameters that are never used, increasing complexity without value.
```python
# ❌ Violates YAGNI
def calculate_price(items, apply_discount=False, discount_rate=0.05):
    # apply_discount is never used in the current product
    total = sum(items)
    if apply_discount:
        total *= (1 - discount_rate)
    return total

# ✅ YAGNI-friendly
def calculate_price(items):
    return sum(items)
```

**2. Premature Abstraction**
*Reason:* Introduces abstraction before there is a second implementation, adding unnecessary maintenance overhead.
```python
# ❌ Violates YAGNI
class Storage(Protocol):
    def put(self, key: str, value: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...

class S3Storage(Storage): ...  # Not needed yet

# ✅ YAGNI-friendly
class LocalStorage:
    def put(self, key: str, value: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...
```

**3. Speculative Configuration Flags**
*Reason:* Adds unused configuration options that create future maintenance cost.
```python
# ❌ Violates YAGNI
def export(report, format="pdf", enable_delta_mode=False):
    ...

# ✅ YAGNI-friendly
def export_pdf(report):
    ...
```

**4. Unused Extension Points**
*Reason:* Adds hooks without consumers, increasing API surface unnecessarily.
```python
# ❌ Violates YAGNI
def process(data, pre_hook=None, post_hook=None):
    if pre_hook:
        pre_hook(data)
    ...
    if post_hook:
        post_hook(data)

# ✅ YAGNI-friendly
def process(data):
    ...
```

#### Decision Tree & JSON
Answer these questions sequentially to determine whether a feature should be implemented now or deferred.

```json
{
  "YAGNI": "You Aren't Gonna Need It",
  "description": "A principle in software development that states you should not add functionality until it is necessary.",
  "purpose": "To avoid unnecessary complexity and waste in software projects by focusing only on current requirements.",
  "version": "1.0.0",
  "last_updated": "2025-08-09T17:35:00Z",
  "risk_score_threshold": 4,
  "questions": [
    {
      "id": "q1",
      "question_number": 1,
      "question": "Is there a real, current requirement for this?",
      "if_no": "Do not add it. (YAGNI triggered)",
      "if_yes": "Continue",
      "risk_score": 5,
      "severity": "blocker"
    },
    {
      "id": "q2",
      "question_number": 2,
      "question": "Will it be used immediately after it's built?",
      "if_no": "Do not add it. (YAGNI triggered)",
      "if_yes": "Continue",
      "risk_score": 4,
      "severity": "blocker"
    },
    {
      "id": "q3",
      "question_number": 3,
      "question": "Is it backed by stakeholder request or concrete data (not speculation)?",
      "if_no": "Do not add it. (YAGNI triggered)",
      "if_yes": "Continue",
      "risk_score": 4,
      "severity": "blocker"
    },
    {
      "id": "q4",
      "question_number": 4,
      "question": "Can it be added later without massive rework?",
      "if_no": "Consider implementing now only if requirement is confirmed and unavoidable",
      "if_yes": "Wait until needed. (YAGNI triggered)",
      "risk_score": 3,
      "severity": "warning"
    }
  ],
  "risk_score_scale": {
    "1": "Low risk (minor complexity cost)",
    "3": "Moderate risk (noticeable waste or refactor cost)",
    "5": "Very high risk (likely to cause major wasted effort and maintenance burden)"
  },
  "outcome_logic": "implement_now = q1_yes && q2_yes && q3_yes && !q4_yes",
  "must_be_true": ["q1_yes", "q2_yes", "q3_yes"],
  "must_be_false": ["q4_yes"],
  "required_fields": ["q1_yes", "q2_yes", "q3_yes", "q4_yes"],
  "tags": ["software-development", "agile", "extreme-programming", "code-quality", "decision-framework"],
  "source": "Extreme Programming (XP)"
}
```

### Pull Request Checklist
Use this in pull requests to enforce **KISS**, **YAGNI**, and **SOLID**:

```markdown
**KISS / YAGNI / SOLID PR Checklist**
- [ ] PR_CHECK_REQ_ID: Current requirement ID is referenced.
- [ ] PR_CHECK_IMMEDIATE_USE: Feature is used immediately by at least one code path.
- [ ] PR_CHECK_NO_SPECULATIVE: No speculative flags, hooks, or abstractions added.
- [ ] PR_CHECK_REAL_CONSUMERS: Generalizations have ≥2 real consumers today.
- [ ] PR_CHECK_TESTS: Tests prove current necessity (fail-before, pass-after).
- [ ] PR_CHECK_KISS: Simpler alternative considered and documented (KISS).
```


### Architecture & Structure (Strict)
- **NEVER create files longer than 500 lines** (including comments, excluding imports)
  - **Consequence**: Pre-commit hook blocks commit, refactor required
- **NEVER nest functions more than 3 levels deep**
  - **Consequence**: Code review rejection, must flatten logic
  ```python
  # ❌ BAD: Too deeply nested
  def process():
      if condition:
          for item in items:
              if item.valid:
                  with context:
                      result = calculate()  # 4 levels deep!

  # ✅ GOOD: Flattened logic
  def process():
      if not condition:
          return
      valid_items = [item for item in items if item.valid]
      for item in valid_items:
          _process_item(item)
  ```
- **NEVER create functions with more than 5 parameters** (use dataclasses/Pydantic models)
- **Cyclomatic complexity MUST be ≤ 10** per function (check with `radon`)
- **No circular imports** - design proper dependency hierarchy
- **No global variables** - use dependency injection or configuration objects
- **Single Responsibility Principle** - each function/class has ONE clear purpose

### AI Agent Security & Standards
- **PROMPT INJECTION PROTECTION**: Sanitize all user inputs, use input validation schemas
- **TOOL METADATA CONTRACT**: All agent tools MUST use Pydantic models for input/output schemas
- **JAILBREAK PREVENTION**: Implement content filtering and output validation
- **ASSUMPTION VALIDATION**: All tool inputs must be validated before execution
- **TOOL SCHEMA EXAMPLE**:
  ```python
  class ToolInput(BaseModel):
      """Input schema for agent tool."""
      query: str = Field(..., max_length=1000, description="Search query")
      filters: Dict[str, Any] = Field(default_factory=dict)

      @validator('query')
      def validate_query(cls, v):
          if not v.strip():
              raise ValueError("Query cannot be empty")
          return v

  class ToolOutput(BaseModel):
      """Output schema for agent tool."""
      results: List[Dict[str, Any]]
      metadata: Dict[str, Any]
      success: bool
  ```

### Code Quality Rules
- **Use type hints for EVERYTHING** - functions, variables, class attributes
- **NO `# type: ignore`** - fix typing errors properly
- **NO `# noqa`** - fix linting errors properly
- **NO `# fmt: off`** - fix formatting errors properly
- **NO commented-out code** - delete it or use version control
- **NO print statements** - use structured logging only
- **NO magic numbers** - define as named constants with clear purpose
- **NO hardcoded values** - use configuration, environment variables, or constants
- **NO duplicate code** - refactor into reusable functions (DRY principle)
- **NO unused imports, variables, or functions** - delete immediately
- **NO assumptions without validation** - check everything explicitly
- **FORBIDDEN PATTERNS** - CI will reject code containing these dangerous functions:
  ```python
  # BAD: These patterns are forbidden for security reasons
  # The following are shown as documentation examples only:
  print(          # Use logging instead
  eval(           # Security risk - dynamic code execution
  exec(           # Security risk - arbitrary code execution
  input(          # Use proper input validation frameworks
  __import__(     # Use standard import statements
  ```

### Performance Requirements
- **Profile performance** for all critical paths using `cProfile`
- **Use async/await** for ALL I/O-bound operations (file, network, database)
- **Implement caching** for expensive computations and external API calls
- **Database queries MUST be optimized** - no N+1 queries, use proper indexing
- **Memory usage monitoring** - no memory leaks, proper resource management
- **Response time targets**: APIs < 200ms, background tasks < 5 minutes
- **Use connection pooling** for database and external service connections
- **Validate cache keys** - no assumptions about cache state

### File & Naming Conventions
- **Python files**: Use `snake_case.py` naming (e.g., `user_service.py`, `data_processor.py`)
- **Test files**: Name as `test_<module>.py` (e.g., `test_user_service.py`)
- **Config files**: Use `<tool>file.py` or `.<tool>rc` (e.g., `noxfile.py`, `.coveragerc`)
- **Classes**: Use `PascalCase` (e.g., `UserService`, `DataProcessor`)
- **Functions/variables**: Use `snake_case` (e.g., `get_user_data`, `process_request`)
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private items**: Prefix with underscore (e.g., `_internal_method`, `_private_var`)

## 🔧 DEVELOPMENT PROCESS - Workflow & Standards
### Development Workflow
- You must read [Development Workflow Standards](./docs/standards/DEVELOPMENT_WORKFLOW.md) for Git, branching, and review processes.

### Key Workflow Requirements:
- **Conventional Commits** format required
- **GitFlow branching** with protected main/develop
- **Pre-commit hooks** mandatory (see configuration below)
- **Code review** for all changes
- **Nox task runner** for quality checks
- **Configuration validation** before any compatibility changes

### Pre-commit Configuration
- All projects MUST use pre-commit hooks with this minimum configuration:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-config
        name: validate-config
        entry: python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"
        language: system
        files: pyproject.toml
      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
      - id: ruff
        name: ruff
        entry: ruff check
        language: system
        types: [python]
      - id: black
        name: black
        entry: black
        language: system
        types: [python]
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
      - id: gitleaks
        name: gitleaks
        entry: gitleaks detect --source . --verbose
        language: system
        pass_filenames: false
```

### Tool Chain Requirements
All projects MUST pass these tools with specific commands:
- `mypy src/ --strict --no-error-summary`
- `ruff check src/ --fix --exit-non-zero-on-fix`
- `ruff format src/ --check`
- `pytest --cov=src --cov-fail-under=90 --tb=short`
- `vulture src/ --min-confidence=70`
- `bandit -r src/ -f json -o bandit_report.json`

### Nox Configuration Example
```python
# noxfile.py
import nox

@nox.session
def validate_config(session):
    """Validate project configuration before other checks."""
    session.run("python", "-c",
                "import tomllib; config = tomllib.load(open('pyproject.toml','rb')); "
                "print(f'Python {config['project']['requires-python']} required')")

@nox.session
def tests(session):
    """Run unit tests with coverage."""
    session.install("-r", "requirements-dev.txt")
    session.run("pytest", "--cov=src", "--cov-fail-under=90")

@nox.session
def lint(session):
    """Run linting and type checking."""
    session.install("mypy", "ruff")
    session.run("mypy", "src/")
    session.run("ruff", "check", "src/")

@nox.session
def security(session):
    """Run security scans."""
    session.install("bandit", "safety")
    session.run("bandit", "-r", "src/")
    session.run("safety", "check")
```

## Documentation Requirements
**Code Documentation:**
- Google-style docstrings for all public functions
- Document all assumptions and their validations
- API docs auto-generated from schemas
- ADRs for major decisions

## Monitoring & Observability (Required)
- **Structured logging** using JSON format with correlation IDs
- **Log all assumption validations** - both successful and failed
- **Log levels properly used**:
  - DEBUG: Detailed diagnostic info (including validated assumptions)
  - INFO: General application flow
  - WARNING: Potentially harmful situations (e.g., fallback to defaults)
  - ERROR: Error conditions that don't stop execution
  - CRITICAL: Serious errors that MUST cause termination
- **Health check endpoints** for all services (`/health`, `/ready`)
- **Metrics collection** for business KPIs and system performance
- **Request tracing** with unique request IDs in logs and responses
- **Performance monitoring** with alerts for SLA violations

## Environment Management

### Configuration
- Use `python-dotenv` for environment variables
- **Validate all configuration on startup**
- Environment-specific configs (`.env.development`, `.env.production`)

### Environment Configuration Example
```python
# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment-specific config
env = os.getenv("ENVIRONMENT", "development")
env_file = Path(f".env.{env}")
if not env_file.exists():
    raise FileNotFoundError(f"Configuration file {env_file} not found")
load_dotenv(env_file)

# Configuration with validation
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """Ensure required config is set."""
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in environment")
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in environment")

        # Validate Python version matches project requirements
        import sys
        import tomllib
        with open("pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
            required = pyproject["project"]["requires-python"]
            current = f"{sys.version_info.major}.{sys.version_info.minor}"
            if not current.startswith(required.replace(">=", "")):
                raise ValueError(f"Python {required} required, but running {current}")

# Validate on import
Config.validate()
```

## Package Management
### Local Development
- Use `uv` (10-100x faster than pip)
### Production/CI**
- Use standard `pip`
- Exact versions in `requirements-dev.txt`
- Version ranges in `requirements.txt`
### Validate package availability** before import
### Dependency Requirements (Enforced by CI)
- PyPI health score >90% (check with `pip-audit`)
- No packages abandoned >2 years (check last release date)
- Security audit with `safety` - zero known vulnerabilities
- Only `.py` files in `src/` directory (reject PRs with other extensions)
- Maximum 50 direct dependencies in `requirements.txt`
- All dev dependencies pinned to exact versions in `requirements-dev.txt`

## 📋 PROJECT MANAGEMENT - Task & Context Awareness

### Mandatory Project Files
- **ALWAYS read `PLANNING.md`** at conversation start for context
- **CHECK `TASK.md`** before starting work:
  - If task exists: follow specifications exactly
  - If task missing: add with description, acceptance criteria, and date
  - Mark completed tasks immediately with completion date
- **UPDATE documentation** when features change
- **VALIDATE project state** before making assumptions

### Task Management (Enforced Standards)
- **Break large tasks** into sub-tasks (< 4 hours each, maximum 8 sub-tasks per epic)
- **Add discovered tasks** to `TASK.md` under "Discovered During Work" within 24 hours
- **Include acceptance criteria** for each task (minimum 3 testable criteria)
- **Estimate effort** using T-shirt sizes: Small (1-4h), Medium (4-16h), Large (16-40h)
- **Track dependencies** between tasks using explicit dependency notation
- **Update task status** within 2 hours of completion
- **Document all assumptions** made during task execution

## 🧠 AI BEHAVIOR RULES - Development Assistant Guidelines

### Code Generation Standards
- **CHECK PROJECT CONFIGURATION FIRST** - Read pyproject.toml, package.json, or equivalent before making version/compatibility assumptions
- **NEVER hallucinate libraries** - only use verified, existing packages
- **ALWAYS verify file paths** and module names before referencing
- **ASK for clarification** when requirements are ambiguous
- **PROVIDE examples** when suggesting new patterns or libraries
- **EXPLAIN reasoning** for architectural decisions
- **EVALUATE alternatives** and document trade-offs
- **STATE ALL ASSUMPTIONS** explicitly in your output

### Documentation Generation Requirements
- **AI MUST create session summaries** at session end
- **AI MUST create task completion summaries** for all completed tasks
- **AI MUST verify documentation exists** before marking tasks complete
- **AI MUST refuse to end session** without creating summary
- **AI MUST check for summaries** at session start
- **AI CANNOT claim task completion** without documentation

### AI Code Generation Test Requirements
- **AI MUST create test files** when generating Python modules
- **AI MUST verify test coverage** before marking tasks complete
- **AI MUST suggest test scenarios** for complex logic
- **AI MUST test assumption validation** code
- **AI assistants cannot claim completion** without corresponding tests

### ADR Approval Policy (ADR-003)
- **AI CAN create ADR proposals** with status "Proposed"
- **AI CANNOT approve ADRs** - only humans can change status to "Approved"
- **AI MUST verify human approval** before implementing protected document changes
- **AI MUST NOT modify** documents marked as "PROTECTED" without approved ADR
- **Protected documents include**: CLAUDE_MD_REQUIREMENTS.md, core architecture docs, security policies

### Quality Assurance
- **RUN quality checks** after each code change using `nox`:
  ```bash
  # First, verify project configuration
  python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb')))"

  # Then run quality pipeline
  nox -s validate_config  # Check project configuration
  nox -s lint            # Type checking, linting, security
  nox -s tests           # Unit tests with coverage
  nox -s format          # Code formatting (ruff + black)
  nox -s security        # Security and vulnerability scans
  ```
- **VERIFY all imports** are available and correctly specified
- **TEST code examples** before providing them
- **VALIDATE against requirements** before marking tasks complete

### Communication Standards
- **Be explicit about assumptions** when generating code
- **Warn about potential issues** or limitations
- **Suggest improvements** to existing code when relevant
- **Reference specific files** when discussing project structure
- **Provide step-by-step instructions** for complex setup or deployment
- **Document validation logic** for all assumptions

### File Naming Conventions (2 points)
- **Python files**: `snake_case.py` (e.g., `user_service.py`)
- **Test files**: `test_<module>.py` (e.g., `test_user_service.py`)
- **Config files**: `<tool>file.py` or `.<tool>rc`
- **Classes**: `PascalCase` (e.g., `UserService`)
- **Functions**: `snake_case` (e.g., `get_user_data`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)

---

## ✅ AI Self-Check Checklist

This checklist enables autonomous verification after edits to maintain continuous quality.

> ⚠️ This checklist is **mandatory**. It must be run after every code-editing action that affects functionality, structure, security, or documentation. No item is optional unless explicitly exempted via ADR.

### Pre-execution Checks (NEW - No Assumptions)
- [ ] Check project configuration (pyproject.toml, package.json, etc.)
- [ ] Verify Python/Node/etc. version requirements
- [ ] Confirm all dependencies are available
- [ ] State all assumptions explicitly in output

### Required Checklist Items:
- [ ] Clean up all temporary and development artifacts
- [ ] Formatting applied: `ruff format`
- [ ] Type checking passes: `mypy`
- [ ] Linting passes: `ruff check --fix`
- [ ] No unused code: `vulture`
- [ ] Security scan clean: `bandit -r src/`
- [ ] No forbidden patterns in code
- [ ] Test coverage ≥ 90%
- [ ] All functions under 50 lines
- [ ] No files over 500 lines
- [ ] Documentation updated for any API or behavior changes
- [ ] Test file exists for every Python file (except `__init__.py`)
- [ ] All tests pass: `pytest`
- [ ] CHANGELOG.md updated for features/fixes
- [ ] All assumption validations in place
- [ ] No Silent Assumptions principle included (10) **NEW**

## 🎯 QUICK CHECKLIST - After Edit

> ⚠️ This checklist is **mandatory**. It must be run after every code-editing action that affects functionality, structure, security, or documentation. No item is optional unless explicitly exempted via ADR.

### Golden Egg Compliance (NEW)
- [ ] Project configuration checked before version-specific changes
- [ ] All assumptions stated explicitly in output
- [ ] Input validation implemented for all external data
- [ ] Environment variables validated before use
- [ ] File paths verified before access

### Completeness Checklist (40 points)
- [ ] All forbidden patterns listed (5) - `print`, `eval`, `exec`, `# type: ignore`, `# noqa`
- [ ] All required tools specified (5) - `mypy`, `ruff`, `pytest`, `vulture`, `bandit`
- [ ] Test requirements complete (5) - 90% coverage, test naming, edge cases
- [ ] Security rules comprehensive (5) - Input validation, secrets handling, OWASP compliance
- [ ] Error handling patterns (5) - Specific exceptions, timeouts, retry logic
- [ ] File/function limits defined (5) - <500 lines/file, <50 lines/function
- [ ] Development workflow clear (5) - Git flow, PR process, CI/CD pipeline
- [ ] Project structure defined (5) - DDD/Non-DDD/Agent patterns specified

### Clarity Score (30 points)
- [ ] Every rule has example (10) - All rules include ❌ BAD and ✅ GOOD examples
- [ ] No ambiguous language (10) - Uses MUST/NEVER, not should/try
- [ ] Clear consequences stated (10) - Each rule specifies what happens on violation

### Consistency Score (20 points)
- [ ] No contradictions (10) - All rules align without conflicts
- [ ] All references valid (5) - All linked documents exist
- [ ] Proper hierarchy (5) - Rules organized logically by importance

### Enforceability Score (10 points)
- [ ] Tools can verify rules (5) - mypy, ruff, pytest, vulture, bandit enforce rules
- [ ] CI/CD can enforce (5) - All rules checked in automated pipeline

### Additional Scoring Items (Bonus 10 points)
- [ ] File naming conventions specified (2) - snake_case, PascalCase rules defined
- [ ] AI self-check checklist included (3) - Comprehensive AI verification steps
- [ ] Security section with examples (3) - Input validation, secrets, headers examples
- [ ] Consistent header formatting (2) - Emoji markers, proper hierarchy

### Tool Execution Checklist
- [ ] Clean up all temporary and development artifacts (`nox -s cleanup`)
- [ ] All tests pass with ≥90% coverage (`pytest`)
- [ ] Session summary created if ending session
- [ ] Task completion summaries created for all completed tasks
- [ ] Documentation compliance verified (`uv run scripts/check_task_completions.py`)
- [ ] Type checking passes (`mypy`)
- [ ] Linting passes: `ruff check --fix`
- [ ] Code formatting applied: `ruff format`
- [ ] No unused code: `vulture`
- [ ] Security scan clean: `bandit -r src/`
- [ ] No forbidden patterns in code
- [ ] Test coverage ≥ 90%
- [ ] All functions under 50 lines
- [ ] No files over 500 lines
- [ ] Test file exists for every Python file (except `__init__.py`)
- [ ] Documentation updated for any API or behavior changes
- [ ] CHANGELOG.md updated for features/fixes

### Alternative: Using Nox Task Runner

If your project uses `nox` as a task runner, you can run the equivalent commands:
- [ ] Configuration validated (`nox -s validate_config`)
- [ ] All tests pass with ≥90% coverage (`nox -s tests`)
- [ ] Type checking passes (`nox -s lint`)
- [ ] Code formatting applied (`nox -s format`)
- [ ] Security scan clean (`nox -s security`)

## 🚩 Red Flags (Automatic Failures)

### BLOCKING CONDITIONS - Work Cannot Proceed
- **Silent assumptions in code** - missing validation
- **Python file without corresponding test file**
- **Test coverage below 90% threshold**
- **Tests not following naming conventions**
- **Missing edge case or failure scenario tests**
- **Integration tests absent for complex modules**
- **Configuration not checked before compatibility changes**
- **Completed task without completion summary**
- **Session end without session summary**
- **Missing documentation for any completed work**

### Critical System Issues
- **Any security vulnerability** detected
- **Tests failing** in critical business logic
- **Memory leaks** or performance degradation
- **Circular imports** or architectural violations
- **Hardcoded secrets** or configuration
- **Missing error handling** in production code
- **Uncaught exceptions** reaching users
- **Data integrity issues** or potential corruption
- **Assumptions without validation** in any code path

### Immediate Action Required
When any red flag is detected:
1. **STOP** all current work immediately
2. **FIX** the issue before proceeding
3. **TEST** the fix thoroughly
4. **DOCUMENT** the issue and resolution
5. **REVIEW** with team if architectural

*These conditions trigger immediate work stoppage and remediation.*

*Remember: It's better to take time to do it right than to rush and create technical debt or security vulnerabilities.*

---

## 🆘 EMERGENCY RESPONSE

For critical incidents (security breach, data corruption, outage):
1. **Contain** - Isolate affected systems (< 15 min)
2. **Assess** - Determine scope and impact
3. **Mitigate** - Roll back or apply temporary fix (< 2 hours)
4. **Document** - Create postmortem in `docs/incidents/`
5. **Learn** - Update procedures based on findings

**Postmortem Template Location:** [INCIDENT_template.md](./docs/incidents/INCIDENT_template.md)
- Naming `incident_name<timestamp>`


## 📝 Change History
