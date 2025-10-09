#!/usr/bin/env python3
"""
Real-time validation of edited Python files against CLAUDE.md requirements.

This script is designed to be used as a Claude Code hook to provide immediate
feedback when files are edited, preventing accumulation of technical debt.

Usage:
    python validate_edited_file.py <filepath> [options]

Example:
    python validate_edited_file.py src/module.py --strict
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


class CLAUDEViolation:
    """Represents a violation of CLAUDE.md requirements."""

    def __init__(
        self,
        severity: str,
        message: str,
        line_number: int | None = None,
        claude_section: str | None = None,
        suggestion: str | None = None,
    ):
        self.severity = severity  # "ERROR", "WARNING", "INFO"
        self.message = message
        self.line_number = line_number
        self.claude_section = claude_section
        self.suggestion = suggestion

    def format(self) -> str:
        """Format violation for display."""
        prefix = {"ERROR": "❌", "WARNING": "⚠️ ", "INFO": "ℹ️ "}.get(self.severity, "")

        msg = f"{prefix} {self.message}"
        if self.line_number:
            msg = f"Line {self.line_number}: {msg}"
        if self.claude_section:
            msg += f" [CLAUDE.md: {self.claude_section}]"
        if self.suggestion:
            msg += f"\n    💡 Suggestion: {self.suggestion}"
        return msg


class CLAUDEValidator:
    """Validates Python files against CLAUDE.md requirements."""

    # Forbidden patterns from CLAUDE.md
    FORBIDDEN_PATTERNS = [
        (r"\bprint\s*\(", "print(", "Use logging instead"),
        (r"\beval\s*\(", "eval(", "Security risk - dynamic code execution"),
        (r"\bexec\s*\(", "exec(", "Security risk - arbitrary code execution"),
        (r"\binput\s*\(", "input(", "Use proper input validation frameworks"),
        (r"\b__import__\s*\(", "__import__(", "Use standard import statements"),
        (r"#\s*type:\s*ignore", "# type: ignore", "Fix typing errors properly"),
        (r"#\s*noqa", "# noqa", "Fix linting errors properly"),
        (r"#\s*fmt:\s*off", "# fmt: off", "Fix formatting errors properly"),
    ]

    # Security patterns to check
    SECURITY_PATTERNS = [
        (r'password\s*=\s*["\'][\w\d]+["\']', "Hardcoded password"),
        (r'api_key\s*=\s*["\'][\w\d]+["\']', "Hardcoded API key"),
        (r'secret\s*=\s*["\'][\w\d]+["\']', "Hardcoded secret"),
        (r'token\s*=\s*["\'][\w\d]+["\']', "Hardcoded token"),
    ]

    # CLAUDE.md thresholds
    MAX_FILE_LINES = 500
    MAX_FUNCTION_LINES = 50
    MAX_FUNCTION_PARAMS = 7
    MAX_COMPLEXITY = 10
    MAX_NESTING_DEPTH = 3

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.violations: list[CLAUDEViolation] = []

    def validate_file(self, filepath: Path) -> list[CLAUDEViolation]:
        """Validate a Python file against CLAUDE.md requirements."""
        self.violations = []

        if not filepath.exists():
            self.violations.append(CLAUDEViolation("ERROR", f"File not found: {filepath}"))
            return self.violations

        if filepath.suffix != ".py":
            return []  # Only validate Python files

        try:
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except Exception as e:
            self.violations.append(CLAUDEViolation("ERROR", f"Failed to parse file: {e}"))
            return self.violations

        # Run all validations
        self._check_file_length(content)
        self._check_forbidden_patterns(content)
        self._check_security_patterns(content)
        self._check_test_file_exists(filepath)
        self._analyze_ast(tree, content)

        return self.violations

    def _check_file_length(self, content: str) -> None:
        """Check if file exceeds maximum line limit."""
        lines = content.count("\n") + 1
        if lines > self.MAX_FILE_LINES:
            self.violations.append(
                CLAUDEViolation(
                    "ERROR",
                    f"File has {lines} lines, exceeds limit of {self.MAX_FILE_LINES}",
                    claude_section="Code Quality Rules",
                    suggestion="Split into smaller modules following Single Responsibility Principle",
                )
            )

    def _check_forbidden_patterns(self, content: str) -> None:
        """Check for forbidden patterns in code."""
        for pattern, name, suggestion in self.FORBIDDEN_PATTERNS:
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            for match in matches:
                line_no = content[: match.start()].count("\n") + 1
                self.violations.append(
                    CLAUDEViolation(
                        "ERROR",
                        f"Forbidden pattern '{name}' found",
                        line_number=line_no,
                        claude_section="Code Quality Rules - FORBIDDEN PATTERNS",
                        suggestion=suggestion,
                    )
                )

    def _check_security_patterns(self, content: str) -> None:
        """Check for security issues."""
        for pattern, description in self.SECURITY_PATTERNS:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches:
                line_no = content[: match.start()].count("\n") + 1
                self.violations.append(
                    CLAUDEViolation(
                        "ERROR",
                        f"Security issue: {description}",
                        line_number=line_no,
                        claude_section="Security Requirements",
                        suggestion="Use environment variables for sensitive data",
                    )
                )

    def _check_test_file_exists(self, filepath: Path) -> None:
        """Check if corresponding test file exists."""
        # Skip if this is a test file or __init__.py
        if filepath.name.startswith("test_") or filepath.name == "__init__.py":
            return

        # Look for test file
        test_name = f"test_{filepath.stem}.py"
        test_locations = [
            filepath.parent / test_name,
            filepath.parent.parent / "tests" / filepath.parent.name / test_name,
        ]

        # Add src-based test location if applicable
        try:
            if "src" in filepath.parts:
                src_idx = filepath.parts.index("src")
                relative_from_src = Path(*filepath.parts[src_idx + 1 :])
                test_path = Path("tests") / relative_from_src.parent / test_name
                test_locations.append(test_path)
        except Exception:
            pass  # Ignore path issues

        test_found = any(loc and loc.exists() for loc in test_locations if loc)

        if not test_found:
            self.violations.append(
                CLAUDEViolation(
                    "ERROR" if self.strict else "WARNING",
                    f"No test file found for {filepath.name}",
                    claude_section="Testing Requirements",
                    suggestion=f"Create test file: tests/{filepath.parent.name}/{test_name}",
                )
            )

    def _analyze_ast(self, tree: ast.AST, content: str) -> None:
        """Analyze AST for various CLAUDE.md requirements."""
        visitor = ASTVisitor(self, content)
        visitor.visit(tree)


class ASTVisitor(ast.NodeVisitor):
    """AST visitor to check function-level requirements."""

    def __init__(self, validator: CLAUDEValidator, content: str):
        self.validator = validator
        self.content = content
        self.lines = content.splitlines()
        self.current_class = None
        self.nesting_depth = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name

        # Check class docstring
        if not ast.get_docstring(node):
            self.validator.violations.append(
                CLAUDEViolation(
                    "WARNING",
                    f"Class '{node.name}' missing docstring",
                    line_number=node.lineno,
                    claude_section="Documentation Requirements",
                    suggestion="Add Google-style docstring with class description",
                )
            )

        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self._check_function(node)

        # Track nesting depth
        self.nesting_depth += 1
        self.generic_visit(node)
        self.nesting_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self._check_function(node)

        self.nesting_depth += 1
        self.generic_visit(node)
        self.nesting_depth -= 1

    def _check_function(self, node: Any) -> None:
        """Check function against CLAUDE.md requirements."""
        # Skip private methods and test methods from some checks
        is_private = node.name.startswith("_")
        is_test = node.name.startswith("test_")

        # Check function length
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        function_lines = end_line - start_line + 1

        if function_lines > self.validator.MAX_FUNCTION_LINES:
            self.validator.violations.append(
                CLAUDEViolation(
                    "ERROR",
                    f"Function '{node.name}' has {function_lines} lines, exceeds limit of {self.validator.MAX_FUNCTION_LINES}",
                    line_number=node.lineno,
                    claude_section="Code Quality Rules",
                    suggestion="Break down into smaller functions",
                )
            )

        # Check parameter count
        total_params = len(node.args.args) + len(node.args.kwonlyargs)
        if node.args.vararg:
            total_params += 1
        if node.args.kwarg:
            total_params += 1

        if total_params > self.validator.MAX_FUNCTION_PARAMS:
            self.validator.violations.append(
                CLAUDEViolation(
                    "ERROR",
                    f"Function '{node.name}' has {total_params} parameters, exceeds limit of {self.validator.MAX_FUNCTION_PARAMS}",
                    line_number=node.lineno,
                    claude_section="Code Quality Rules",
                    suggestion="Use dataclasses or Pydantic models to group related parameters",
                )
            )

        # Check nesting depth
        if self.nesting_depth > self.validator.MAX_NESTING_DEPTH:
            self.validator.violations.append(
                CLAUDEViolation(
                    "ERROR",
                    f"Function '{node.name}' nested {self.nesting_depth} levels deep, exceeds limit of {self.validator.MAX_NESTING_DEPTH}",
                    line_number=node.lineno,
                    claude_section="Code Quality Rules",
                    suggestion="Flatten nested functions or extract to module level",
                )
            )

        # Check docstring (less strict for private/test methods)
        if not is_private and not is_test and not ast.get_docstring(node):
            self.validator.violations.append(
                CLAUDEViolation(
                    "WARNING",
                    f"Function '{node.name}' missing docstring",
                    line_number=node.lineno,
                    claude_section="Documentation Requirements",
                    suggestion="Add Google-style docstring with Args, Returns, Raises sections",
                )
            )

        # Check type hints
        self._check_type_hints(node)

    def _check_type_hints(self, node: Any) -> None:
        """Check if function has proper type hints."""
        # Check return type
        if node.returns is None and node.name != "__init__":
            self.validator.violations.append(
                CLAUDEViolation(
                    "WARNING",
                    f"Function '{node.name}' missing return type hint",
                    line_number=node.lineno,
                    claude_section="Code Quality Rules",
                    suggestion="Add return type hint (use -> None for functions without return)",
                )
            )

        # Check parameter types
        for arg in node.args.args:
            if arg.annotation is None and arg.arg != "self" and arg.arg != "cls":
                self.validator.violations.append(
                    CLAUDEViolation(
                        "WARNING",
                        f"Parameter '{arg.arg}' in function '{node.name}' missing type hint",
                        line_number=node.lineno,
                        claude_section="Code Quality Rules",
                        suggestion=f"Add type hint for parameter '{arg.arg}'",
                    )
                )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Python files against CLAUDE.md requirements"
    )
    parser.add_argument("filepath", type=Path, help="Path to the Python file to validate")
    parser.add_argument(
        "--strict", action="store_true", help="Enable strict mode (warnings become errors)"
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--quiet", action="store_true", help="Only show errors, suppress warnings and info"
    )

    args = parser.parse_args()

    # Validate file
    validator = CLAUDEValidator(strict=args.strict)
    violations = validator.validate_file(args.filepath)

    # Filter by severity if quiet mode
    if args.quiet:
        violations = [v for v in violations if v.severity == "ERROR"]

    # Output results
    if args.json:
        results = {
            "filepath": str(args.filepath),
            "violations": [
                {
                    "severity": v.severity,
                    "message": v.message,
                    "line_number": v.line_number,
                    "claude_section": v.claude_section,
                    "suggestion": v.suggestion,
                }
                for v in violations
            ],
            "error_count": sum(1 for v in violations if v.severity == "ERROR"),
            "warning_count": sum(1 for v in violations if v.severity == "WARNING"),
        }
        print(json.dumps(results, indent=2))
    # Print header
    elif violations:
        print(f"\n🔍 CLAUDE.md Validation Results for {args.filepath}")
        print("=" * 60)

        # Group by severity
        errors = [v for v in violations if v.severity == "ERROR"]
        warnings = [v for v in violations if v.severity == "WARNING"]
        info = [v for v in violations if v.severity == "INFO"]

        # Print violations
        for violation in violations:
            print(f"\n{violation.format()}")

        # Summary
        print(f"\n{'=' * 60}")
        print(f"Summary: {len(errors)} errors, {len(warnings)} warnings")

        if errors:
            print("\n❌ VALIDATION FAILED - Fix errors before continuing")
    else:
        print(f"✅ {args.filepath} passes all CLAUDE.md checks!")

    # Exit with error code if there are errors
    error_count = sum(1 for v in violations if v.severity == "ERROR")
    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
