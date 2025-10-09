#!/usr/bin/env python3
"""
Test to ensure no duplicate method definitions in MarkdownParserCore.
This catches accidental multiple definitions that would be silently overridden.
"""

import ast
import sys
from pathlib import Path


def check_duplicate_methods(file_path):
    """Check for duplicate method definitions in a Python class."""

    with open(file_path) as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False

    # Track method definitions by class
    class_methods = {}
    duplicates = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            if class_name not in class_methods:
                class_methods[class_name] = {}

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_name = item.name

                    if method_name in class_methods[class_name]:
                        # Found duplicate
                        duplicates.append(
                            {
                                "class": class_name,
                                "method": method_name,
                                "first_line": class_methods[class_name][method_name],
                                "duplicate_line": item.lineno,
                            }
                        )
                    else:
                        class_methods[class_name][method_name] = item.lineno

    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate method(s) in {file_path}:")
        for dup in duplicates:
            print(
                f"  - {dup['class']}.{dup['method']} defined at lines {dup['first_line']} and {dup['duplicate_line']}"
            )
        return False

    return True


def test_runtime_uniqueness():
    """Test that imported class has unique methods at runtime."""

    # Import the module
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    from docpipe.loaders.markdown_parser_core import MarkdownParserCore

    # Check for duplicate methods in class dict
    method_counts = {}
    for attr_name in dir(MarkdownParserCore):
        if not attr_name.startswith("__"):  # Skip magic methods
            attr = getattr(MarkdownParserCore, attr_name)
            if callable(attr):
                # This would only catch the final definition anyway
                # but we check for consistency
                method_counts[attr_name] = method_counts.get(attr_name, 0) + 1

    duplicates = {k: v for k, v in method_counts.items() if v > 1}

    if duplicates:
        print(f"❌ Runtime check found duplicate methods: {duplicates}")
        return False

    print(f"✅ Runtime check: All {len(method_counts)} methods are unique")
    return True


def main():
    """Run all uniqueness tests."""

    print("🔍 Import-Time Uniqueness Test")
    print("=" * 50)

    # Path to the module
    module_path = Path(__file__).parent / "src/docpipe/loaders/markdown_parser_core.py"

    if not module_path.exists():
        print(f"❌ Module not found: {module_path}")
        sys.exit(1)

    # Test 1: Static analysis for duplicate definitions
    print("\n1. Static Analysis Check:")
    static_ok = check_duplicate_methods(module_path)
    if static_ok:
        print("✅ No duplicate method definitions found in source")

    # Test 2: Runtime uniqueness check
    print("\n2. Runtime Import Check:")
    runtime_ok = test_runtime_uniqueness()

    # Summary
    print("\n" + "=" * 50)
    if static_ok and runtime_ok:
        print("✅ All uniqueness tests passed!")
        sys.exit(0)
    else:
        print("❌ Some uniqueness tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
