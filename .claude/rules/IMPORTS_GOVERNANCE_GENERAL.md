## 🧩 Import Governance — Absolute Imports by Default (Project Rule)

This project enforces strict rules for Python imports to keep module boundaries clear and avoid fragile coupling.

> **Hard rule:**  
> - Prefer **absolute imports**.  
> - **Do not use** multi-dot relative imports like `from ..foo import bar`.  
> - Wildcard imports (`from x import *`) are banned, except in very narrow, documented cases.

---

### 1. Goals

- **Clarity:** It should always be obvious where a symbol comes from.
- **Stability:** Renames and refactors inside a package should not silently break imports.
- **Boundaries:** Imports should respect package and layer boundaries (no “reaching up and sideways” with `..`).
- **Tooling:** Linters and IDEs should be able to resolve imports reliably.

---

### 2. Allowed Import Patterns

#### 2.1 Absolute imports (preferred everywhere)

Use absolute imports for anything outside the current module’s immediate package.

```python
# Good: absolute imports
from my_project.domain.user import User
from my_project.services.email import send_email
import my_project.utils.time as time_utils
```

This applies both *within* the package and across internal “layers” (domain, infra, api, etc.).

#### 2.2 Single-dot relative imports (optionally allowed within one package)

If you choose to allow them, single-dot relative imports are acceptable **only** for “same-package neighbors”:

```python
# Acceptable (if allowed by project):
from .validators import EmailValidator
from . import helpers
```

Use this only when both modules are part of the same cohesive package and you are not crossing “upwards” into a parent.  

Each project may choose one of these options:

- **Option A (strict):** No relative imports at all; absolute imports only.
- **Option B (moderate):** Allow single-dot relative imports inside a small package; no `..` upwards.

---

### 3. Forbidden Import Patterns

#### 3.1 Multi-dot relative imports (`from ..xxx import yyy`)

Disallowed:

```python
# ❌ Forbidden
from ..utils import parse_config
from ...core.models import User
```

Reasons:

- Coupling to the package layout (“go up twice, then across”) makes re-organizing packages painful.
- It hides true dependencies: you cannot see at a glance which top-level package is being imported.
- It makes partial reuse (e.g., vendoring a subpackage) harder.

Upgrade path:

```python
# ✅ Preferred
from my_project.utils import parse_config
from my_project.core.models import User
```

#### 3.2 Wildcard imports (`from x import *`)

Disallowed:

```python
# ❌ Forbidden
from my_project.settings import *
from .helpers import *
```

Issues:

- Pollutes the namespace and hides where names come from.
- Breaks static analysis and makes refactoring dangerous.

Allowed only in **very narrow**, documented cases, such as:

- Inside a package’s `__init__.py` that is explicitly acting as a façade, AND:
  - You maintain an explicit `__all__` list, AND
  - You treat that `__init__` as part of the public API.

Even there, explicit re-export is better:

```python
# Better than wildcard:
from .core import Engine, EngineConfig

__all__ = ["Engine", "EngineConfig"]
```

#### 3.3 Dynamic imports except in well-defined extension points

Avoid `importlib.import_module`, `__import__`, and runtime `exec`/`eval` for imports except in:

- Plugin systems.
- Optional feature loaders.
- Clearly delimited “extension” or “adapter” modules.

Even there:

- Centralize dynamic imports in a small, well-named module.
- Provide a stable interface (e.g., `load_plugin(name: str)`) so the rest of the codebase never touches `importlib` directly.

---

### 4. Package & Layer Boundary Rules

You can combine import style with architectural boundaries, for example:

- **Domain layer**: may not import from infrastructure or CLI layers.
- **Infrastructure layer**: may import domain, not vice versa.
- **CLI / API layer**: may import domain + infra.

Imports support these rules by being **explicit**:

- Cross-layer imports must be **absolute**, so it is obvious when you violate the architecture.
- Multi-dot relative imports undermine this by letting you “reach up and sideways” out of the layer.

If you have such a layered architecture, codify it briefly alongside this rule and enforce it with a linter (e.g., import-linter, custom Ruff rules).

---

### 5. Enforcement

You can enforce import rules with static analysis and simple checks.

#### 5.1 Static analysis (recommended)

- **Ruff / Flake8**:
  - Disallow wildcard imports (except possibly in `__init__.py` with explicit `__all__`).
  - Flag relative imports; optionally allow `.foo` but reject `..foo`.

- **Import-linter or similar**:
  - Enforce architectural boundaries between packages (e.g., `api` must not be imported by `domain`).

#### 5.2 Simple CI checks (baseline)

Even without dedicated tools, you can add CI checks using ripgrep:

```bash
# Block multi-dot relative imports
rg "from \.\." src/   && echo '❌ Found multi-dot relative imports' && exit 1   || echo '✅ No multi-dot relative imports'

# Block wildcard imports
rg "from .* import \*" src/   && echo '❌ Found wildcard imports' && exit 1   || echo '✅ No wildcard imports'
```

Adjust `src/` to your project’s source root if needed.

---

### 6. Summary

- Prefer **absolute imports** everywhere.
- Optionally allow single-dot relative imports inside a small, cohesive package; decide this policy once per project.
- **Ban** multi-dot relative imports (`from ..xxx import yyy`).
- **Ban** wildcard imports (`from x import *`), except in rare, carefully controlled `__init__.py` façades with explicit `__all__`.
- Keep dynamic imports confined to explicit extension/plug-in points behind a small, well-defined interface.
