## 🔍 Type Checking Governance — Static Type Safety (Project Rule)

This project uses **static type checking** to catch errors early and document code contracts. Type hints are required for all new code, and type checking must pass before merging.

> **Hard rule:**  
> - All new functions, methods, and classes must have type hints.  
> - Type checking (via `mypy` or equivalent) must pass in CI with zero errors.  
> - `type: ignore` comments require justification and must be minimized.  
> - No blanket suppression of type errors; each must be addressed individually.

---

### 1. Goals

- **Early error detection:** Catch type errors before runtime, not in production.
- **Self-documenting code:** Type hints serve as inline documentation of expected inputs/outputs.
- **Refactoring safety:** Type checker verifies changes don't break contracts across the codebase.
- **IDE support:** Enable better autocomplete, navigation, and inline error detection.

This rule complements other governance rules:

- **TDD Governance:** Types catch errors statically; tests catch them dynamically.
- **Clean Table Principle:** Type errors are impurities that must be resolved before delivery.
- **No Weak Tests:** Strong types reduce the need for defensive runtime checks in tests.

---

### 2. Type Checker Standard

This project uses **mypy** as the standard type checker.

**Why mypy:**
- Industry standard and most mature Python type checker
- Excellent error messages and documentation
- Configurable strictness levels for gradual adoption
- Works with all major editors and IDEs

**Alternatives** (if explicitly chosen):
- `pyright`: Faster, different inference, stricter defaults
- `pyre`: Facebook's type checker, less common

Once chosen, stick to **one** type checker for consistency. Do not mix multiple type checkers in CI.

---

### 3. What Must Be Typed

#### 3.1 Always require type hints:

- **Function signatures:**
  ```python
  # ✓ CORRECT
  def calculate_total(items: list[Item], tax_rate: float) -> Decimal:
      ...
  
  # ❌ WRONG
  def calculate_total(items, tax_rate):
      ...
  ```

- **Method signatures:**
  ```python
  # ✓ CORRECT
  class DataProcessor:
      def process(self, data: pd.DataFrame) -> pd.DataFrame:
          ...
  
  # ❌ WRONG
  class DataProcessor:
      def process(self, data):
          ...
  ```

- **Class attributes:**
  ```python
  # ✓ CORRECT
  class Config:
      timeout: int
      retries: int
      base_url: str
  
  # ❌ WRONG
  class Config:
      timeout = 30
      retries = 3
      base_url = "http://api.example.com"
  ```

- **Public module-level constants:**
  ```python
  # ✓ CORRECT
  MAX_RETRIES: int = 3
  DEFAULT_TIMEOUT: float = 30.0
  
  # ❌ WRONG
  MAX_RETRIES = 3
  DEFAULT_TIMEOUT = 30.0
  ```

#### 3.2 Optional (but recommended):

- **Local variables** when type isn't obvious from assignment:
  ```python
  # Recommended for clarity
  result: dict[str, Any] = parse_json(data)
  
  # Not needed when obvious
  count = 0  # clearly int
  name = "example"  # clearly str
  ```

- **Lambda functions** in complex contexts:
  ```python
  # Recommended
  filter_func: Callable[[Item], bool] = lambda x: x.price > 100
  ```

#### 3.3 Exceptions (may skip type hints):

- **Test functions:** Type hints optional but encouraged
- **Private helper functions** in test files
- **Scripts in `tools/`** (but still recommended)
- **`__init__` when it only does `self.x = x` assignments** (types on class attributes instead)

---

### 4. Type Checker Configuration

Type checking configuration lives in `pyproject.toml` (preferred) or `mypy.ini`.

**Recommended baseline configuration:**

```toml
[tool.mypy]
python_version = "3.12"  # Match your project's Python version
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true

# Start with these disabled, enable gradually
disallow_any_generics = false
disallow_subclassing_any = false

# Exclude generated or external code
exclude = [
    "^build/",
    "^dist/",
    "^.venv/",
]
```

**Strictness levels:**

1. **Baseline** (minimum): `disallow_untyped_defs = true`
2. **Moderate** (recommended): Add `disallow_any_unimported = true`
3. **Strict**: Add `disallow_any_generics = true`, `disallow_subclassing_any = true`

Choose a strictness level appropriate for your project phase:
- **New projects:** Start at moderate or strict
- **Existing projects:** Start at baseline, increase gradually

---

### 5. Running Type Checks

Type checks must run both locally and in CI.

**Local development:**

```bash
# Run type checker on entire project
uv run mypy src/

# Run on specific module or file
uv run mypy src/my_package/module.py

# Run with verbose output for debugging
uv run mypy --show-error-codes src/
```

**Pattern for all type checking:** Always run via `uv run mypy`, not direct `mypy` or `.venv/bin/mypy`.

---

### 6. Type Hint Patterns and Best Practices

#### 6.1 Use modern syntax (Python 3.9+)

**✓ CORRECT (Python 3.9+):**
```python
def process(items: list[str]) -> dict[str, int]:
    ...

def merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    ...
```

**❌ AVOID (old style):**
```python
from typing import List, Dict

def process(items: List[str]) -> Dict[str, int]:
    ...
```

Use `typing.List`, `typing.Dict` only if you must support Python <3.9.

#### 6.2 Be specific with collection types

**✓ CORRECT:**
```python
def get_user_ids(users: list[User]) -> set[int]:
    ...

def count_by_status(items: list[Item]) -> dict[str, int]:
    ...
```

**❌ TOO VAGUE:**
```python
def get_user_ids(users: list) -> set:  # Missing element types
    ...

def count_by_status(items: list[Any]) -> dict:  # Lazy typing
    ...
```

#### 6.3 Use `Optional` or `| None` for nullable values

**✓ CORRECT:**
```python
# Modern syntax (Python 3.10+)
def find_user(user_id: int) -> User | None:
    ...

# Older syntax (Python 3.9)
from typing import Optional
def find_user(user_id: int) -> Optional[User]:
    ...
```

**❌ WRONG:**
```python
def find_user(user_id: int) -> User:  # Lies about possibly returning None
    return None if not_found else user
```

#### 6.4 Use `Protocol` or `ABC` for interfaces

**✓ CORRECT:**
```python
from typing import Protocol

class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...

def save(obj: Serializable) -> None:
    data = obj.to_dict()
    ...
```

**❌ AVOID:**
```python
# Overly permissive
def save(obj: Any) -> None:
    data = obj.to_dict()  # No type safety
    ...
```

#### 6.5 Use `TypedDict` for structured dictionaries

**✓ CORRECT:**
```python
from typing import TypedDict

class UserDict(TypedDict):
    id: int
    name: str
    email: str

def create_user(data: UserDict) -> User:
    ...
```

**❌ AVOID:**
```python
def create_user(data: dict[str, Any]) -> User:  # Loses structure information
    ...
```

---

### 7. Forbidden Patterns

#### 7.1 Overuse of `Any`

**❌ FORBIDDEN:**
```python
def process_data(data: Any) -> Any:  # Defeats the purpose of type checking
    ...
```

**✓ CORRECT:**
Use specific types, `TypedDict`, `Protocol`, or generics instead.

#### 7.2 Blanket `type: ignore`

**❌ FORBIDDEN:**
```python
result = complex_operation(data)  # type: ignore
```

**✓ CORRECT:**
```python
# Specify error code and justify
result = complex_operation(data)  # type: ignore[arg-type]  # TODO: Fix upstream signature
```

#### 7.3 Skipping return type hints

**❌ FORBIDDEN:**
```python
def compute_score(items: list[Item]):  # No return type
    return sum(item.value for item in items)
```

**✓ CORRECT:**
```python
def compute_score(items: list[Item]) -> float:
    return sum(item.value for item in items)
```

#### 7.4 Per-file type checking disablement

**❌ FORBIDDEN:**
```python
# mypy: ignore-errors
# Top of file - disables all type checking for entire file
```

**✓ CORRECT:**
Fix the type errors, or use targeted `type: ignore` comments with justification.

---

### 8. Gradual Adoption Strategy

For existing codebases without type hints:

#### Phase 1: Enable type checking in CI
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = false
disallow_untyped_defs = false  # Allow untyped functions for now

# But enforce for new files
[[tool.mypy.overrides]]
module = "my_package.new_module"
disallow_untyped_defs = true
```

#### Phase 2: Type new code and public APIs
- All new functions must have type hints
- Gradually add types to existing public APIs
- Run `mypy --strict` only on new modules

#### Phase 3: Increase strictness
```toml
[tool.mypy]
disallow_untyped_defs = true  # Now require types everywhere
disallow_any_unimported = true
```

#### Phase 4: Eliminate remaining gaps
- Remove all `type: ignore` comments where possible
- Enable `disallow_any_generics = true`
- Achieve zero mypy errors on strictest settings

---

### 9. CI Integration

Type checking must run in CI and block merges on failure.

**Example (GitHub Actions):**

```yaml
- uses: astral-sh/setup-uv@v4

- name: Sync dependencies
  run: uv sync --group dev

- name: Type check
  run: uv run mypy src/

- name: Verify type checking configuration
  run: |
    # Ensure mypy config exists
    if [ ! -f pyproject.toml ] && [ ! -f mypy.ini ]; then
      echo "❌ Missing mypy configuration"
      exit 1
    fi
```

**Enforcement:**
- Type checking failures must block CI
- No PRs can merge with type errors
- `type: ignore` additions should be flagged in code review

---

### 10. Common Type Checking Issues

#### Issue 1: "Missing type hint" errors

**Problem:** Function lacks type hints

**Solution:** Add type hints to signature
```python
# Before
def process(data):
    ...

# After
def process(data: pd.DataFrame) -> pd.DataFrame:
    ...
```

#### Issue 2: "Incompatible return value type"

**Problem:** Function claims to return X but returns Y

**Solution:** Fix the return type or the implementation
```python
# Wrong
def get_count() -> int:
    return None  # ❌

# Fixed - update return type
def get_count() -> int | None:
    return None

# Or fix implementation
def get_count() -> int:
    return 0  # ✓
```

#### Issue 3: "Cannot determine type of variable"

**Problem:** Type inference fails on complex expressions

**Solution:** Add explicit type annotation
```python
# Before - mypy confused
data = json.loads(response.text)

# After - explicit type
data: dict[str, Any] = json.loads(response.text)
```

#### Issue 4: Third-party library without type stubs

**Problem:** `error: Skipping analyzing 'external_lib': module is installed, but missing library stubs or py.typed marker`

**Solution:**
```bash
# Install type stubs if available
uv add --group dev types-requests types-pyyaml

# Or ignore the library in mypy config
[[tool.mypy.overrides]]
module = "external_lib.*"
ignore_missing_imports = true
```

---

### 11. Integration with Other Tools

Type checking complements other development tools:

**With pytest:**
- Type hints improve test clarity
- Type checker catches type errors that tests might miss
- Some test patterns (fixtures, parametrize) benefit from explicit types

**With ruff/linters:**
- Ruff can enforce some typing rules (e.g., require return type hints)
- Combine both for comprehensive static analysis

**With IDEs:**
- Type hints enable better autocomplete
- IDEs show inline type errors from mypy
- Refactoring tools use types for safety

---

### 12. Summary

- **Type hints are required** for all new functions, methods, and public APIs.
- **mypy** (or chosen type checker) must pass with zero errors in CI.
- Use **modern type hint syntax** (`list[T]`, `dict[K, V]`, `X | None`).
- Be **specific** with types; avoid overusing `Any`.
- Minimize **`type: ignore`** comments; always include error code and justification.
- Type checking is a **quality gate** like tests; it must pass before merge.
- For existing codebases, adopt types **gradually** with increasing strictness over time.
