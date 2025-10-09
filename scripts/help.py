"""
Built-in help system for PTOOL.

This module provides interactive help functions that users and AI assistants
can use to get immediate assistance with PTOOL usage.
"""

from pathlib import Path
from typing import Any

# Version information
__version__ = "2.0.0"


class HelpSystem:
    """Interactive help system for PTOOL."""

    def __init__(self):
        self.help_data = self._load_help_data()
        self.examples_data = self._load_examples_data()

    def _load_help_data(self) -> dict[str, Any]:
        """Load help metadata."""
        return {
            "topics": {
                "basics": {
                    "title": "Basic Usage",
                    "description": "Getting started with PTOOL",
                    "examples": ["basic_usage", "path_access"],
                },
                "validators": {
                    "title": "Custom Validators",
                    "description": "Creating and using custom path validators",
                    "examples": ["custom_validator", "environment_validator"],
                },
                "factory": {
                    "title": "Factory Pattern",
                    "description": "Using factory functions for flexible configuration",
                    "examples": ["factory_usage", "multiple_validators"],
                },
                "builder": {
                    "title": "Builder Pattern",
                    "description": "Fluent interface for complex configurations",
                    "examples": ["builder_pattern", "complex_config"],
                },
                "global": {
                    "title": "Global Validators",
                    "description": "Managing global validator state",
                    "examples": ["global_injection", "global_management"],
                },
                "environment": {
                    "title": "Environment-Specific",
                    "description": "Different validation for dev/staging/production",
                    "examples": ["env_detection", "env_validators"],
                },
                "testing": {
                    "title": "Testing Support",
                    "description": "Testing patterns and utilities",
                    "examples": ["mock_validators", "temp_directories"],
                },
                "troubleshooting": {
                    "title": "Troubleshooting",
                    "description": "Common problems and solutions",
                    "examples": ["common_errors", "diagnostics"],
                },
                "migration": {
                    "title": "Migration Guide",
                    "description": "Upgrading from v1.0 to v2.0",
                    "examples": ["migration_examples", "compatibility"],
                },
            },
            "api": {
                "functions": [
                    "create_project_paths",
                    "create_project_paths_with_validators",
                    "create_minimal_project_paths",
                    "inject_validator",
                    "clear_validators",
                    "combine_validators",
                ],
                "classes": [
                    "BasePathValidator",
                    "ProjectPathsBuilder",
                    "CompositeValidator",
                    "ValidationError",
                ],
            },
            "config": {
                "sources": ["pyproject.toml", ".paths", "environment"],
                "section": "tool.project_paths",
                "required_fields": ["base_dir"],
                "common_fields": ["src_dir", "tests_dir", "docs_dir", "logs_dir"],
            },
        }

    def _load_examples_data(self) -> dict[str, str]:
        """Load code examples."""
        return {
            "basic_usage": """
from project_paths import ProjectPaths

# Original API (still works)
paths = ProjectPaths()
print(paths.base_dir)
""",
            "factory_usage": """
from project_paths import create_project_paths, BasePathValidator

class MyValidator(BasePathValidator):
    def validate_paths(self, paths_instance):
        self.clear_messages()
        if not paths_instance.src_dir.exists():
            self.add_error("Source directory missing!")

ProjectPaths = create_project_paths(validator=MyValidator())
paths = ProjectPaths()
""",
            "custom_validator": """
from project_paths import BasePathValidator

class SecurityValidator(BasePathValidator):
    def __init__(self):
        super().__init__(strict=False)
    
    def validate_paths(self, paths_instance):
        self.clear_messages()
        
        # Check for sensitive files
        sensitive_files = [".env", "secrets.json"]
        for file_name in sensitive_files:
            file_path = paths_instance.base_dir / file_name
            if file_path.exists():
                import os
                stat_info = file_path.stat()
                permissions = oct(stat_info.st_mode)[-3:]
                if permissions[-2:] != "00":
                    self.add_warning(f"Sensitive file has broad permissions: {file_name}")
""",
            "environment_validator": '''
def create_validator_for_environment(env="development"):
    """Factory function for environment-specific validators."""
    
    class DevValidator(BasePathValidator):
        def __init__(self):
            super().__init__(strict=False)
        
        def validate_paths(self, paths_instance):
            # Lenient validation for development
            self.clear_messages()
            if not paths_instance.tests_dir.exists():
                self.add_warning("Tests directory not found")
    
    class ProdValidator(BasePathValidator):
        def __init__(self):
            super().__init__(strict=True)
        
        def validate_paths(self, paths_instance):
            # Strict validation for production
            self.clear_messages()
            if not paths_instance.src_dir.exists():
                self.add_error("Source directory required in production")
    
    validators = {
        "development": DevValidator(),
        "production": ProdValidator(),
    }
    
    return validators.get(env, DevValidator())
''',
            "builder_pattern": """
from project_paths import ProjectPathsBuilder

ProjectPaths = (ProjectPathsBuilder()
    .add_validator(DevValidator())
    .add_validator(SecurityValidator())
    .with_strict_validation()
    .build())

paths = ProjectPaths()
""",
            "global_injection": """
from project_paths import inject_validator, clear_validators, create_project_paths

# Set up global validators
inject_validator(SecurityValidator())
inject_validator(PerformanceValidator())

# All future instances use global validators
ProjectPaths = create_project_paths()
paths = ProjectPaths()

# Clean up
clear_validators()
""",
            "config_template": """
# Add to pyproject.toml:
[tool.project_paths]
base_dir = "."
src_dir = "src"
tests_dir = "tests"
docs_dir = "docs"
build_dir = "build"
logs_dir = "logs"
temp_dir = "temp"
config_dir = "config"
data_dir = "data"
""",
        }


def help_ptool(topic: str | None = None) -> None:
    """
    Show interactive help for PTOOL.

    Args:
        topic: Specific help topic to show. If None, shows main help menu.

    Available topics: basics, validators, factory, builder, global,
                     environment, testing, troubleshooting, migration
    """
    help_system = HelpSystem()

    if topic is None:
        _show_main_help(help_system)
    elif topic in help_system.help_data["topics"]:
        _show_topic_help(help_system, topic)
    else:
        print(f"Unknown help topic: {topic}")
        print("Available topics:", ", ".join(help_system.help_data["topics"].keys()))


def _show_main_help(help_system: HelpSystem) -> None:
    """Show main help menu."""
    print("🎯 PTOOL Help System")
    print("=" * 50)
    print(f"Version: {__version__}")
    print()
    print("📚 Available Help Topics:")
    print()

    for topic, info in help_system.help_data["topics"].items():
        print(f"  {topic:15} - {info['description']}")

    print()
    print("💡 Usage:")
    print("  help_ptool('topic')     # Get help on specific topic")
    print("  show_examples('topic')  # Show code examples")
    print("  show_config_template()  # Generate config template")
    print("  diagnose_setup()        # Run diagnostics")
    print()
    print("🔗 Full Documentation:")
    print("  USER_MANUAL.md          # Comprehensive guide")
    print("  API_REFERENCE.md        # Complete API docs")
    print("  QUICK_REFERENCE.md      # Cheat sheet")
    print("  examples/               # Working code examples")


def _show_topic_help(help_system: HelpSystem, topic: str) -> None:
    """Show help for specific topic."""
    topic_info = help_system.help_data["topics"][topic]

    print(f"📖 {topic_info['title']}")
    print("=" * 50)
    print(topic_info["description"])
    print()

    if "examples" in topic_info:
        print("💡 Code Examples:")
        for example_key in topic_info["examples"]:
            if example_key in help_system.examples_data:
                print(f"\n--- {example_key.replace('_', ' ').title()} ---")
                code = help_system.examples_data[example_key].strip()
                print(code)
            else:
                print(f"  • {example_key} (run show_examples('{example_key}') for code)")

    print("\n🔗 For more details: help_ptool() or see USER_MANUAL.md")


def show_examples(topic: str | None = None, search: str | None = None) -> None:
    """
    Show code examples for PTOOL usage.

    Args:
        topic: Specific example topic
        search: Search term to find relevant examples
    """
    help_system = HelpSystem()

    if topic is None and search is None:
        print("📝 Available Code Examples:")
        print("=" * 40)
        for key in help_system.examples_data.keys():
            title = key.replace("_", " ").title()
            print(f"  • {key:20} - {title}")
        print("\n💡 Usage: show_examples('example_name')")
        return

    if topic and topic in help_system.examples_data:
        print(f"📝 Example: {topic.replace('_', ' ').title()}")
        print("=" * 40)
        code = help_system.examples_data[topic].strip()
        print(code)
        return

    if search:
        matches = []
        search_lower = search.lower()
        for key, code in help_system.examples_data.items():
            if search_lower in key.lower() or search_lower in code.lower():
                matches.append(key)

        if matches:
            print(f"📝 Examples matching '{search}':")
            print("=" * 40)
            for match in matches:
                print(f"\n--- {match.replace('_', ' ').title()} ---")
                print(help_system.examples_data[match].strip())
        else:
            print(f"No examples found matching '{search}'")
        return

    if topic:
        print(f"Example '{topic}' not found.")
        print("Available examples:", ", ".join(help_system.examples_data.keys()))


def show_config_template(format: str = "toml") -> str:
    """
    Generate a configuration template.

    Args:
        format: Configuration format ('toml', 'dict', 'env')

    Returns:
        Configuration template as string
    """
    if format == "toml":
        template = """# Add to pyproject.toml:
[tool.project_paths]
base_dir = "."
src_dir = "src"
tests_dir = "tests"
docs_dir = "docs"
build_dir = "build"
logs_dir = "logs"
temp_dir = "temp"
config_dir = "config"
data_dir = "data"

# Optional paths
cache_dir = "cache"
media_dir = "media"
static_dir = "static"
templates_dir = "templates"
"""
    elif format == "dict":
        template = """# Python dictionary format:
config = {
    "base_dir": ".",
    "src_dir": "src", 
    "tests_dir": "tests",
    "docs_dir": "docs",
    "build_dir": "build",
    "logs_dir": "logs",
    "temp_dir": "temp",
    "config_dir": "config",
    "data_dir": "data",
}"""
    elif format == "env":
        template = """# Environment variables format:
export PROJECT_BASE_DIR="."
export PROJECT_SRC_DIR="src"
export PROJECT_TESTS_DIR="tests"
export PROJECT_DOCS_DIR="docs"
export PROJECT_BUILD_DIR="build"
export PROJECT_LOGS_DIR="logs"
export PROJECT_TEMP_DIR="temp"
export PROJECT_CONFIG_DIR="config"
export PROJECT_DATA_DIR="data"
"""
    else:
        template = f"Unknown format: {format}. Use 'toml', 'dict', or 'env'"

    print(template)
    return template


def diagnose_setup() -> dict[str, Any]:
    """
    Run diagnostics to identify common setup issues.

    Returns:
        Dictionary with diagnostic results
    """
    print("🔍 Running PTOOL Setup Diagnostics...")
    print("=" * 40)

    diagnostics = {
        "timestamp": "2025-08-09",  # Would be dynamic in real implementation
        "version": __version__,
        "issues": [],
        "warnings": [],
        "recommendations": [],
        "status": "healthy",
    }

    # Check 1: Configuration file exists
    print("1. Checking configuration file...")
    config_files = ["pyproject.toml", ".paths", "setup.cfg"]
    config_found = False

    for config_file in config_files:
        config_path = Path(config_file)
        if config_path.exists():
            print(f"   ✅ Found {config_file}")
            config_found = True

            # Check if it has project_paths section
            if config_file == "pyproject.toml":
                try:
                    content = config_path.read_text()
                    if "[tool.project_paths]" in content:
                        print("   ✅ Found [tool.project_paths] section")
                    else:
                        diagnostics["warnings"].append(
                            f"{config_file} exists but missing [tool.project_paths] section"
                        )
                        print("   ⚠️  Missing [tool.project_paths] section")
                except Exception as e:
                    diagnostics["issues"].append(f"Could not read {config_file}: {e}")
                    print(f"   ❌ Could not read {config_file}: {e}")
            break

    if not config_found:
        diagnostics["issues"].append("No configuration file found")
        diagnostics["recommendations"].append(
            "Run show_config_template() to generate configuration"
        )
        print("   ❌ No configuration file found")

    # Check 2: Python path and imports
    print("\n2. Checking Python imports...")
    try:
        import project_paths

        print("   ✅ Can import project_paths")

        # Check available functions
        required_functions = ["create_project_paths", "BasePathValidator", "inject_validator"]
        for func_name in required_functions:
            if hasattr(project_paths, func_name):
                print(f"   ✅ Found {func_name}")
            else:
                diagnostics["warnings"].append(f"Function {func_name} not available")
                print(f"   ⚠️  Function {func_name} not available")

    except ImportError as e:
        diagnostics["issues"].append(f"Cannot import project_paths: {e}")
        diagnostics["recommendations"].append("Check PYTHONPATH and package installation")
        print(f"   ❌ Cannot import project_paths: {e}")

    # Check 3: Try creating basic paths
    print("\n3. Testing basic functionality...")
    try:
        from project_paths import create_minimal_project_paths

        ProjectPaths = create_minimal_project_paths()
        paths = ProjectPaths()
        print("   ✅ Can create ProjectPaths instance")

        # Check basic attributes
        if hasattr(paths, "base_dir"):
            print(f"   ✅ base_dir: {paths.base_dir}")
        else:
            diagnostics["warnings"].append("ProjectPaths instance missing base_dir")
            print("   ⚠️  ProjectPaths instance missing base_dir")

    except Exception as e:
        diagnostics["issues"].append(f"Cannot create ProjectPaths: {e}")
        print(f"   ❌ Cannot create ProjectPaths: {e}")

    # Check 4: File system permissions
    print("\n4. Checking file system permissions...")
    current_dir = Path.cwd()
    if current_dir.exists():
        print(f"   ✅ Current directory exists: {current_dir}")

        # Check read permissions
        try:
            list(current_dir.iterdir())
            print("   ✅ Can read current directory")
        except PermissionError:
            diagnostics["issues"].append("Cannot read current directory")
            print("   ❌ Cannot read current directory")

        # Check write permissions
        try:
            test_file = current_dir / ".ptool_test"
            test_file.touch()
            test_file.unlink()
            print("   ✅ Can write to current directory")
        except PermissionError:
            diagnostics["warnings"].append("Cannot write to current directory")
            print("   ⚠️  Cannot write to current directory")

    # Determine overall status
    if diagnostics["issues"]:
        diagnostics["status"] = "issues_found"
    elif diagnostics["warnings"]:
        diagnostics["status"] = "warnings"

    # Summary
    print("\n📊 Diagnostic Summary:")
    print(f"   Status: {diagnostics['status']}")
    print(f"   Issues: {len(diagnostics['issues'])}")
    print(f"   Warnings: {len(diagnostics['warnings'])}")

    if diagnostics["issues"]:
        print("\n❌ Issues Found:")
        for issue in diagnostics["issues"]:
            print(f"   • {issue}")

    if diagnostics["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in diagnostics["warnings"]:
            print(f"   • {warning}")

    if diagnostics["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in diagnostics["recommendations"]:
            print(f"   • {rec}")

    return diagnostics


def get_help_metadata() -> dict[str, Any]:
    """
    Get machine-readable help metadata for AI assistants.

    Returns:
        Complete help system metadata
    """
    help_system = HelpSystem()
    return {
        "version": __version__,
        "help_data": help_system.help_data,
        "examples": list(help_system.examples_data.keys()),
        "functions": [
            {
                "name": "help_ptool",
                "description": "Interactive help system",
                "parameters": ["topic (optional)"],
            },
            {
                "name": "show_examples",
                "description": "Display code examples",
                "parameters": ["topic (optional)", "search (optional)"],
            },
            {
                "name": "show_config_template",
                "description": "Generate configuration template",
                "parameters": ["format ('toml', 'dict', 'env')"],
            },
            {
                "name": "diagnose_setup",
                "description": "Run setup diagnostics",
                "parameters": [],
            },
        ],
        "api_functions": help_system.help_data["api"]["functions"],
        "api_classes": help_system.help_data["api"]["classes"],
    }


def search_help(query: str) -> list[dict[str, str]]:
    """
    Search help content for specific terms.

    Args:
        query: Search term

    Returns:
        List of matching help content
    """
    help_system = HelpSystem()
    results = []
    query_lower = query.lower()

    # Search topics
    for topic, info in help_system.help_data["topics"].items():
        if query_lower in topic.lower() or query_lower in info["description"].lower():
            results.append(
                {
                    "type": "topic",
                    "name": topic,
                    "title": info["title"],
                    "description": info["description"],
                    "relevance": "high" if query_lower in topic.lower() else "medium",
                }
            )

    # Search examples
    for example_key, code in help_system.examples_data.items():
        if query_lower in example_key.lower() or query_lower in code.lower():
            results.append(
                {
                    "type": "example",
                    "name": example_key,
                    "title": example_key.replace("_", " ").title(),
                    "description": f"Code example for {example_key.replace('_', ' ')}",
                    "relevance": "high" if query_lower in example_key.lower() else "low",
                }
            )

    # Sort by relevance
    results.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["relevance"]], reverse=True)

    return results


def help_for_error(error: Exception) -> None:
    """
    Provide context-specific help for errors.

    Args:
        error: Exception that occurred
    """
    error_type = type(error).__name__
    error_message = str(error)

    print(f"🚨 Error Help: {error_type}")
    print("=" * 40)
    print(f"Error: {error_message}")
    print()

    # Provide specific help based on error type
    if "ValidationError" in error_type:
        print("💡 This is a path validation error.")
        print("Common causes:")
        print("  • Required paths don't exist")
        print("  • Strict validator found validation issues")
        print("  • Path permissions are incorrect")
        print()
        print("Solutions:")
        print("  1. Run diagnose_setup() to check configuration")
        print("  2. Create missing directories")
        print("  3. Use strict=False for lenient validation")
        print("  4. Check validator logic")
        print()
        print("Example:")
        print("  validator = MyValidator()")
        print("  validator.strict = False  # Use warnings instead of errors")

    elif "ModuleNotFoundError" in error_type:
        print("💡 This is an import error.")
        print("Common causes:")
        print("  • PTOOL not in Python path")
        print("  • Missing dependencies")
        print("  • Wrong working directory")
        print()
        print("Solutions:")
        print("  1. Add PTOOL to Python path:")
        print("     sys.path.insert(0, 'path/to/PTOOL/src')")
        print("  2. Check working directory")
        print("  3. Verify PTOOL installation")

    elif "FileNotFoundError" in error_type and "pyproject.toml" in error_message:
        print("💡 Configuration file not found.")
        print("Solutions:")
        print("  1. Create pyproject.toml:")
        print("     show_config_template()")
        print("  2. Change to project root directory")
        print("  3. Use alternative config file:")
        print("     create_project_paths(config_source='.paths')")

    else:
        print("💡 General troubleshooting:")
        print("  1. Run diagnose_setup() for diagnostic information")
        print("  2. Check help_ptool('troubleshooting') for common issues")
        print("  3. See USER_MANUAL.md troubleshooting section")


# Convenience functions for AI assistants
def ptool_status() -> dict[str, Any]:
    """Get current PTOOL status for AI assistants."""
    return {
        "version": __version__,
        "available_functions": [
            "help_ptool",
            "show_examples",
            "show_config_template",
            "diagnose_setup",
            "get_help_metadata",
            "search_help",
        ],
        "documentation_files": ["USER_MANUAL.md", "API_REFERENCE.md", "QUICK_REFERENCE.md"],
        "example_files": [
            "examples/basic_example.py",
            "examples/custom_validator_example.py",
            "examples/environment_example.py",
            "examples/advanced_example.py",
        ],
    }


def quick_start() -> None:
    """Quick start guide for new users."""
    print("🚀 PTOOL Quick Start")
    print("=" * 30)
    print("1. Create configuration:")
    print("   show_config_template()")
    print()
    print("2. Basic usage:")
    print("   from project_paths import ProjectPaths")
    print("   paths = ProjectPaths()")
    print()
    print("3. With validation:")
    print("   show_examples('custom_validator')")
    print()
    print("4. Get help:")
    print("   help_ptool('basics')")
    print()
    print("5. Run diagnostics:")
    print("   diagnose_setup()")


if __name__ == "__main__":
    # When run as module, show main help
    help_ptool()
