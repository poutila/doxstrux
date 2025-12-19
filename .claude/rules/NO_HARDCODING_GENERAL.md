# Code Quality Rule: CQ-004 - No Hardcoding (Dynamic Discovery)

This project enforces dynamic discovery over hardcoded values. Any information that can be collected programmatically at runtime MUST be collected dynamically to prevent drift between code and reality.

> **Hard rule:**  
> - No hardcoded file paths, URLs, or credentials.  
> - No hardcoded lists of modules, classes, or functions—use introspection.  
> - No hardcoded data that can be queried from authoritative sources.  
> - Configuration lives in config files, not in code.

---

## Classification

- **Category:** Code Quality / Maintainability / Drift Prevention
- **Severity:** ERROR
- **Scope:** All production code
- **Enforceability:** Code review + automated checks

---

## 1. Goals

- **Prevent Drift:** Hardcoded values inevitably become stale when reality changes
- **Single Source of Truth:** Information should have exactly one authoritative source
- **Maintainability:** Changes to structure shouldn't require code changes
- **Discoverability:** Code should adapt to what exists, not assume what exists

This rule complements:
- **Module Import Purity:** Don't load data at import time
- **Facts Before Files:** Query extracted facts instead of parsing files
- **Clean Table Principle:** Hardcoded stale data is an impurity
- **SPEKSI Philosophy:** Drift-resistant specifications require dynamic discovery

---

## 2. Core Principle

**If it can be discovered, don't hardcode it.**

The system should inspect its environment and discover:
- What files exist
- What modules are available
- What functions/classes are defined
- What configuration is provided
- What database schema exists
- What API endpoints are available

---

## 3. Forbidden Patterns

### 3.1 Hardcoded File Paths

**❌ FORBIDDEN:**
```python
# Hardcoded absolute path
DATA_FILE = "/home/user/project/data/facts.parquet"

# Hardcoded relative path
CONFIG_FILE = "../../config/settings.toml"

# Hardcoded list of files
DATA_FILES = [
    "file1.csv",
    "file2.csv",
    "file3.csv"
]
```

**✅ CORRECT - Dynamic discovery:**
```python
from pathlib import Path

# Discover project root dynamically
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "facts.parquet"

# Or use package resources
from importlib.resources import files
DATA_FILE = files("myproject.data") / "facts.parquet"

# Discover all CSV files dynamically
def get_data_files(data_dir: Path) -> list[Path]:
    """Discover all CSV files in data directory."""
    return sorted(data_dir.glob("*.csv"))

# Usage:
data_files = get_data_files(PROJECT_ROOT / "data")
```

### 3.2 Hardcoded URLs and Endpoints

**❌ FORBIDDEN:**
```python
# Hardcoded base URL
API_BASE = "https://api.example.com"

# Hardcoded endpoint list
ENDPOINTS = [
    "/users",
    "/orders",
    "/products"
]

def get_user(user_id: int):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()
```

**✅ CORRECT - Configuration-based:**
```python
from dataclasses import dataclass
from pathlib import Path
import tomli

@dataclass
class APIConfig:
    base_url: str
    timeout: int
    endpoints: dict[str, str]

def load_api_config(config_path: Path) -> APIConfig:
    """Load API configuration from file."""
    with open(config_path, "rb") as f:
        config = tomli.load(f)
    return APIConfig(**config["api"])

# config.toml:
# [api]
# base_url = "https://api.example.com"
# timeout = 30
# [api.endpoints]
# users = "/v2/users"
# orders = "/v2/orders"

config = load_api_config(Path("config.toml"))

def get_user(user_id: int):
    url = f"{config.base_url}{config.endpoints['users']}/{user_id}"
    response = requests.get(url, timeout=config.timeout)
    return response.json()
```

**✅ EVEN BETTER - Discover from API:**
```python
def discover_api_endpoints(base_url: str) -> dict[str, str]:
    """Discover available endpoints from API metadata."""
    response = requests.get(f"{base_url}/api/metadata")
    metadata = response.json()
    return metadata["endpoints"]

# Many APIs provide OpenAPI/Swagger specs
def load_openapi_spec(base_url: str) -> dict:
    """Load OpenAPI specification to discover all endpoints."""
    response = requests.get(f"{base_url}/openapi.json")
    return response.json()
```

### 3.3 Hardcoded Module/Class Lists

**❌ FORBIDDEN:**
```python
# Hardcoded list of validators
VALIDATORS = [
    EmailValidator,
    PhoneValidator,
    AddressValidator,
    AgeValidator
]

# Hardcoded list of modules to load
PLUGIN_MODULES = [
    "myproject.plugins.csv_loader",
    "myproject.plugins.json_loader",
    "myproject.plugins.parquet_loader"
]
```

**✅ CORRECT - Dynamic discovery:**
```python
import importlib
import inspect
from pathlib import Path
from typing import Type

def discover_validators(module_name: str) -> list[Type[Validator]]:
    """Discover all Validator subclasses in a module.
    
    Args:
        module_name: Module to search for validators
    
    Returns:
        List of all Validator subclasses found
    """
    module = importlib.import_module(module_name)
    
    validators = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, Validator) and obj is not Validator:
            validators.append(obj)
    
    return validators

def discover_plugins(plugin_dir: Path) -> dict[str, type]:
    """Discover all plugins in plugin directory.
    
    Args:
        plugin_dir: Directory containing plugin modules
    
    Returns:
        Dictionary mapping plugin name to plugin class
    """
    plugins = {}
    
    for py_file in plugin_dir.glob("*_loader.py"):
        if py_file.stem.startswith("_"):
            continue
        
        module_name = f"myproject.plugins.{py_file.stem}"
        module = importlib.import_module(module_name)
        
        # Find loader class
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith("Loader") and hasattr(obj, "load"):
                plugins[py_file.stem] = obj
    
    return plugins

# Usage:
validators = discover_validators("myproject.validators")
plugins = discover_plugins(Path("myproject/plugins"))
```

### 3.4 Hardcoded Database Schema

**❌ FORBIDDEN:**
```python
# Hardcoded table list
TABLES = ["users", "orders", "products", "inventory"]

# Hardcoded column list
USER_COLUMNS = ["id", "email", "username", "created_at"]

def get_all_user_data():
    # Assumes specific columns exist
    return db.execute("SELECT id, email, username, created_at FROM users")
```

**✅ CORRECT - Inspect schema:**
```python
from sqlalchemy import inspect, MetaData

def discover_tables(engine) -> list[str]:
    """Discover all tables in database.
    
    Args:
        engine: SQLAlchemy engine
    
    Returns:
        List of table names
    """
    inspector = inspect(engine)
    return inspector.get_table_names()

def discover_columns(engine, table_name: str) -> list[str]:
    """Discover all columns in a table.
    
    Args:
        engine: SQLAlchemy engine
        table_name: Name of table to inspect
    
    Returns:
        List of column names
    """
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return [col["name"] for col in columns]

def get_all_user_data():
    """Get all user data with dynamically discovered columns."""
    columns = discover_columns(engine, "users")
    column_list = ", ".join(columns)
    return db.execute(f"SELECT {column_list} FROM users")

# For Polars/Parquet:
def discover_parquet_schema(path: Path) -> dict[str, pl.DataType]:
    """Discover schema from Parquet file.
    
    Args:
        path: Path to Parquet file
    
    Returns:
        Dictionary mapping column names to data types
    """
    df = pl.scan_parquet(path).limit(0).collect()
    return {col: df[col].dtype for col in df.columns}
```

### 3.5 Hardcoded Configuration Values

**❌ FORBIDDEN:**
```python
# Hardcoded config in code
MAX_RETRIES = 3
TIMEOUT = 30.0
DATABASE_URL = "postgresql://localhost/mydb"
API_KEY = "secret123"  # NEVER!
LOG_LEVEL = "INFO"

def connect_database():
    return create_engine("postgresql://localhost/mydb")
```

**✅ CORRECT - External configuration:**
```python
from dataclasses import dataclass
from pathlib import Path
import os
import tomli

@dataclass
class AppConfig:
    """Application configuration."""
    max_retries: int
    timeout: float
    database_url: str
    api_key: str
    log_level: str

def load_config(config_path: Path | None = None) -> AppConfig:
    """Load configuration from file and environment.
    
    Precedence: environment variables > config file > defaults
    
    Args:
        config_path: Path to TOML config file (optional)
    
    Returns:
        Application configuration
    """
    # Start with defaults
    config = {
        "max_retries": 3,
        "timeout": 30.0,
        "log_level": "INFO"
    }
    
    # Load from config file if provided
    if config_path and config_path.exists():
        with open(config_path, "rb") as f:
            config.update(tomli.load(f))
    
    # Override with environment variables
    if db_url := os.getenv("DATABASE_URL"):
        config["database_url"] = db_url
    
    if api_key := os.getenv("API_KEY"):
        config["api_key"] = api_key
    
    if log_level := os.getenv("LOG_LEVEL"):
        config["log_level"] = log_level
    
    return AppConfig(**config)

# config.toml:
# max_retries = 3
# timeout = 30.0
# database_url = "postgresql://localhost/mydb"
# log_level = "INFO"
# Note: API_KEY should ONLY be in environment, not config file
```

### 3.6 Hardcoded Test Data

**❌ FORBIDDEN:**
```python
def test_user_creation():
    # Hardcoded test data inline
    user = create_user("alice@example.com", "Alice", "Smith")
    assert user.email == "alice@example.com"

# Hardcoded fixture data
SAMPLE_USERS = [
    {"email": "alice@example.com", "name": "Alice"},
    {"email": "bob@example.com", "name": "Bob"},
]
```

**✅ CORRECT - Generate or load dynamically:**
```python
import pytest
from faker import Faker
from pathlib import Path

fake = Faker()

def generate_test_user() -> dict:
    """Generate random test user data."""
    return {
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "age": fake.random_int(18, 80)
    }

@pytest.fixture
def sample_user():
    """Generate a sample user for testing."""
    return generate_test_user()

@pytest.fixture
def sample_users():
    """Generate multiple sample users."""
    return [generate_test_user() for _ in range(10)]

# Or load from fixture files
@pytest.fixture
def sample_temperature_data():
    """Load sample temperature data from fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / "temperature_data.csv"
    return pl.read_csv(fixture_path)
```

---

## 4. Allowed Patterns

### 4.1 Physical Constants

**✅ ACCEPTABLE - True constants:**
```python
# Physical constants (never change)
SPEED_OF_LIGHT = 299792458  # m/s
AVOGADRO_NUMBER = 6.02214076e23
ABSOLUTE_ZERO_CELSIUS = -273.15

# Mathematical constants
PI = 3.141592653589793
E = 2.718281828459045
```

### 4.2 Enum Values

**✅ ACCEPTABLE - Fixed enumeration:**
```python
from enum import Enum

class LogLevel(Enum):
    """Log levels (fixed by Python logging module)."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class HTTPMethod(Enum):
    """HTTP methods (fixed by HTTP spec)."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
```

### 4.3 Protocol/Format Constants

**✅ ACCEPTABLE - Protocol specifications:**
```python
# HTTP status codes (defined by RFC)
HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500

# File format magic numbers
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
JPEG_SIGNATURE = b'\xff\xd8\xff'
```

---

## 5. Dynamic Discovery Patterns

### 5.1 File Discovery

**✅ CORRECT:**
```python
from pathlib import Path

def discover_data_files(
    directory: Path,
    pattern: str = "*.csv",
    recursive: bool = False
) -> list[Path]:
    """Discover data files matching pattern.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., "*.csv", "data_*.parquet")
        recursive: Search recursively if True
    
    Returns:
        Sorted list of matching files
    """
    glob_func = directory.rglob if recursive else directory.glob
    return sorted(glob_func(pattern))

def discover_python_modules(package_dir: Path) -> list[str]:
    """Discover all Python modules in a package.
    
    Args:
        package_dir: Package directory to search
    
    Returns:
        List of module names (without .py extension)
    """
    modules = []
    for py_file in package_dir.glob("*.py"):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        modules.append(py_file.stem)
    return sorted(modules)
```

### 5.2 Code Introspection

**✅ CORRECT:**
```python
import ast
import inspect
from typing import Callable

def discover_functions_in_module(module) -> list[tuple[str, Callable]]:
    """Discover all functions defined in a module.
    
    Args:
        module: Module to inspect
    
    Returns:
        List of (function_name, function_object) tuples
    """
    functions = []
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if obj.__module__ == module.__name__:  # Defined in this module
            functions.append((name, obj))
    return functions

def discover_classes_with_method(
    module,
    method_name: str
) -> list[type]:
    """Discover all classes in module that have a specific method.
    
    Args:
        module: Module to inspect
        method_name: Name of method to look for
    
    Returns:
        List of classes that have the specified method
    """
    classes = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if hasattr(obj, method_name) and callable(getattr(obj, method_name)):
            classes.append(obj)
    return classes

def discover_function_signatures(module_path: Path) -> dict[str, str]:
    """Discover function signatures by parsing AST.
    
    Args:
        module_path: Path to Python module
    
    Returns:
        Dictionary mapping function names to signature strings
    """
    with open(module_path) as f:
        tree = ast.parse(f.read())
    
    signatures = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]
            signatures[node.name] = f"{node.name}({', '.join(args)})"
    
    return signatures
```

### 5.3 FACTS.parquet Pattern (Your Project)

**✅ CORRECT - Query extracted facts:**
```python
import polars as pl
from pathlib import Path

def get_available_fact_keys(facts_path: Path) -> list[str]:
    """Discover all available fact keys from FACTS.parquet.
    
    Args:
        facts_path: Path to FACTS.parquet
    
    Returns:
        Sorted list of unique fact keys
    """
    df = pl.read_parquet(facts_path)
    return sorted(df["key"].unique().to_list())

def discover_functions_in_file(facts_path: Path, file_name: str) -> list[str]:
    """Discover all functions defined in a specific file.
    
    Args:
        facts_path: Path to FACTS.parquet
        file_name: Name of file to query
    
    Returns:
        List of function names defined in the file
    """
    df = pl.read_parquet(facts_path)
    functions = df.filter(
        (pl.col("source_file") == file_name) &
        (pl.col("type") == "function")
    )
    return functions["key"].to_list()

def get_function_signature(
    facts_path: Path,
    function_name: str
) -> dict[str, any]:
    """Get function signature from facts.
    
    Args:
        facts_path: Path to FACTS.parquet
        function_name: Name of function
    
    Returns:
        Dictionary with signature information
    """
    df = pl.read_parquet(facts_path)
    sig_data = df.filter(
        (pl.col("key") == f"function.{function_name}") &
        (pl.col("family") == "signature")
    )
    
    if len(sig_data) == 0:
        raise ValueError(f"Function '{function_name}' not found in facts")
    
    return {
        "parameters": sig_data.filter(pl.col("type") == "parameter")["value"].to_list(),
        "return_type": sig_data.filter(pl.col("type") == "return_type")["value"][0],
    }
```

### 5.4 Configuration Discovery

**✅ CORRECT:**
```python
from pathlib import Path
import os

def discover_config_file() -> Path:
    """Discover configuration file in standard locations.
    
    Search order:
    1. CONFIG_FILE environment variable
    2. ./config.toml (current directory)
    3. ~/.config/myapp/config.toml (user config)
    4. /etc/myapp/config.toml (system config)
    
    Returns:
        Path to first config file found
    
    Raises:
        FileNotFoundError: If no config file found
    """
    # Check environment variable
    if config_path := os.getenv("CONFIG_FILE"):
        path = Path(config_path)
        if path.exists():
            return path
    
    # Check standard locations
    locations = [
        Path.cwd() / "config.toml",
        Path.home() / ".config" / "myapp" / "config.toml",
        Path("/etc/myapp/config.toml")
    ]
    
    for location in locations:
        if location.exists():
            return location
    
    raise FileNotFoundError(
        "No config file found. Searched: " + 
        ", ".join(str(loc) for loc in locations)
    )
```

### 5.5 Plugin/Extension Discovery

**✅ CORRECT:**
```python
import importlib.metadata
from typing import Protocol

class Plugin(Protocol):
    """Protocol for plugin classes."""
    name: str
    version: str
    
    def initialize(self) -> None:
        ...

def discover_installed_plugins() -> list[Plugin]:
    """Discover plugins installed as Python packages.
    
    Uses entry points to discover plugins that register themselves.
    
    Returns:
        List of discovered plugin instances
    """
    plugins = []
    
    # Discover via entry points (setup.py/pyproject.toml)
    for entry_point in importlib.metadata.entry_points().get("myapp.plugins", []):
        plugin_class = entry_point.load()
        plugin = plugin_class()
        plugins.append(plugin)
    
    return plugins

# In setup.py or pyproject.toml, plugins register themselves:
# [project.entry-points."myapp.plugins"]
# csv_plugin = "myapp_csv_plugin:CSVPlugin"
# json_plugin = "myapp_json_plugin:JSONPlugin"
```

---

## 6. Code Smell Detection

### 6.1 Hardcoded Magic Numbers

**❌ CODE SMELL:**
```python
def calculate_tax(amount):
    return amount * 0.08  # What is 0.08?

def resize_image(image):
    return image.resize((800, 600))  # Why 800x600?
```

**✅ CORRECT:**
```python
# Configuration
TAX_RATE = 0.08  # 8% sales tax (from config)
DEFAULT_IMAGE_WIDTH = 800
DEFAULT_IMAGE_HEIGHT = 600

def calculate_tax(amount, tax_rate=TAX_RATE):
    """Calculate tax on amount.
    
    Args:
        amount: Amount to calculate tax on
        tax_rate: Tax rate (default from config)
    
    Returns:
        Tax amount
    """
    return amount * tax_rate

def resize_image(image, width=DEFAULT_IMAGE_WIDTH, height=DEFAULT_IMAGE_HEIGHT):
    """Resize image to specified dimensions.
    
    Args:
        image: Image to resize
        width: Target width in pixels
        height: Target height in pixels
    
    Returns:
        Resized image
    """
    return image.resize((width, height))
```

### 6.2 Hardcoded Conditional Logic

**❌ CODE SMELL:**
```python
def get_shipping_cost(country):
    if country == "US":
        return 5.0
    elif country == "CA":
        return 7.0
    elif country == "UK":
        return 10.0
    elif country == "AU":
        return 15.0
    else:
        return 20.0
```

**✅ CORRECT:**
```python
# Load from configuration
def load_shipping_rates(config_path: Path) -> dict[str, float]:
    """Load shipping rates from configuration."""
    with open(config_path, "rb") as f:
        config = tomli.load(f)
    return config["shipping"]["rates"]

# config.toml:
# [shipping.rates]
# US = 5.0
# CA = 7.0
# UK = 10.0
# AU = 15.0
# default = 20.0

shipping_rates = load_shipping_rates(Path("config.toml"))

def get_shipping_cost(country: str) -> float:
    """Get shipping cost for country.
    
    Args:
        country: Two-letter country code
    
    Returns:
        Shipping cost in USD
    """
    return shipping_rates.get(country, shipping_rates["default"])
```

---

## 7. Testing Dynamic Discovery

### 7.1 Test Discovery Functions

**✅ CORRECT:**
```python
import pytest
from pathlib import Path

def test_discover_csv_files(tmp_path):
    """Test CSV file discovery."""
    # Create test files
    (tmp_path / "data1.csv").write_text("col1,col2\n1,2")
    (tmp_path / "data2.csv").write_text("col1,col2\n3,4")
    (tmp_path / "readme.txt").write_text("info")
    
    # Discover CSV files
    csv_files = discover_data_files(tmp_path, "*.csv")
    
    assert len(csv_files) == 2
    assert all(f.suffix == ".csv" for f in csv_files)

def test_discover_functions_in_module():
    """Test function discovery via introspection."""
    import myproject.validators as validators_module
    
    functions = discover_functions_in_module(validators_module)
    
    # Check specific functions exist
    function_names = [name for name, _ in functions]
    assert "validate_email" in function_names
    assert "validate_phone" in function_names

def test_config_discovery_precedence(tmp_path, monkeypatch):
    """Test config file discovery precedence."""
    # Create config in current directory
    local_config = tmp_path / "config.toml"
    local_config.write_text('[app]\nname = "local"')
    
    # Set environment variable to override
    env_config = tmp_path / "env_config.toml"
    env_config.write_text('[app]\nname = "env"')
    monkeypatch.setenv("CONFIG_FILE", str(env_config))
    
    # Environment variable should take precedence
    discovered = discover_config_file()
    assert discovered == env_config
```

---

## 8. Migration Strategy

### 8.1 Identify Hardcoded Values

**Search patterns:**
```bash
# Find hardcoded URLs
rg 'https?://[a-zA-Z0-9.-]+' src/ --type py

# Find hardcoded paths
rg '"/[a-z/]+"' src/ --type py
rg '"[A-Z]:\\\\' src/ --type py  # Windows paths

# Find hardcoded lists
rg '\[.*".*",.*".*"\]' src/ --type py

# Find magic numbers (numbers not 0, 1, -1)
rg '[^0-9]([2-9][0-9]+|[0-9]+\.[0-9]+)[^0-9]' src/ --type py
```

### 8.2 Refactoring Process

1. **Extract to configuration:**
   - Move hardcoded values to config files
   - Use environment variables for secrets
   - Document configuration schema

2. **Replace with discovery:**
   - Use filesystem APIs for file discovery
   - Use introspection for code discovery
   - Query authoritative sources

3. **Test thoroughly:**
   - Verify discovery works in different environments
   - Test with empty/missing directories
   - Test configuration precedence

---

## 9. Enforcement

### 9.1 Code Review Checklist

- ✅ No hardcoded file paths (use Path, importlib.resources)
- ✅ No hardcoded URLs (use configuration)
- ✅ No hardcoded credentials (use environment variables)
- ✅ No hardcoded lists that can be discovered
- ✅ Configuration in external files, not code
- ✅ Magic numbers have named constants

### 9.2 Automated Detection

```python
# Custom linting rule to detect hardcoded paths
import ast

class HardcodedPathDetector(ast.NodeVisitor):
    """Detect potential hardcoded paths in AST."""
    
    def __init__(self):
        self.violations = []
    
    def visit_Str(self, node):
        """Check string literals for path-like patterns."""
        if "/" in node.s or "\\" in node.s:
            if node.s.startswith("/") or ":\\" in node.s:
                self.violations.append({
                    "line": node.lineno,
                    "value": node.s,
                    "message": "Potential hardcoded path"
                })
        self.generic_visit(node)

# Usage in CI:
def check_file_for_hardcoded_paths(file_path: Path):
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    detector = HardcodedPathDetector()
    detector.visit(tree)
    
    if detector.violations:
        print(f"Found {len(detector.violations)} hardcoded paths in {file_path}")
        for v in detector.violations:
            print(f"  Line {v['line']}: {v['value']}")
        return False
    return True
```

---

## 10. Related Rules

- **Module Import Purity:** Don't load data at import time
- **Facts Before Files:** Query facts instead of parsing files
- **Clean Table Principle:** Stale hardcoded data is an impurity
- **Configuration Management:** (future rule) How to structure config

---

## 11. Summary

**Core Principle:**
If it can be discovered programmatically, don't hardcode it.

**Forbidden:**
- Hardcoded file paths, URLs, credentials
- Hardcoded lists of modules, classes, functions
- Hardcoded database schema
- Hardcoded configuration values
- Hardcoded test data
- Magic numbers without named constants

**Required:**
- Use filesystem APIs for file discovery
- Use introspection for code discovery
- Load configuration from external files
- Use environment variables for secrets
- Generate or load test data dynamically
- Query authoritative sources (FACTS.parquet, database schema, API metadata)

**Benefits:**
- Prevents drift between code and reality
- Single source of truth
- Adapts to changes automatically
- Reduces maintenance burden

Hardcoding creates a second source of truth that inevitably drifts from reality. Dynamic discovery keeps code synchronized with the actual state of the system.

---

**Adoption Status:** ⚠️ DRAFT  
**Owner:** Architecture Team  
**Last Updated:** 2025-12-18  
**Review Cycle:** Quarterly
