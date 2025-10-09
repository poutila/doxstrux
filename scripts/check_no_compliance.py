#!/usr/bin/env python3
"""
NO.md Compliance Checker

This script automatically checks for violations of non-negotiable rules defined in NO.md.
It can be used in pre-commit hooks and CI/CD pipelines.
"""

import argparse
import ast
import re
import sys
from pathlib import Path

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ComplianceChecker:
    """Check codebase compliance with NO.md rules."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.violations: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []

    def add_violation(self, rule: str, file: str, line: int, message: str) -> None:
        """Add a rule violation."""
        self.violations.append({"rule": rule, "file": file, "line": line, "message": message})

    def add_warning(self, rule: str, message: str) -> None:
        """Add a warning."""
        self.warnings.append({"rule": rule, "message": message})

    def check_forbidden_patterns(self) -> None:
        """Check for forbidden patterns (NO-CODE-005)."""
        forbidden_patterns = {
            r"\bprint\s*\(": "Use logging instead of print()",
            r"\beval\s*\(": "eval() is a security risk",
            r"\bexec\s*\(": "exec() is a security risk",
            r"\binput\s*\(": "Use proper input validation instead of input()",
            r"\b__import__\s*\(": "Use standard imports instead of __import__()",
        }

        for py_file in self.root_path.rglob("*.py"):
            if "venv" in str(py_file) or ".git" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()

                for pattern, message in forbidden_patterns.items():
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line) and not line.strip().startswith("#"):
                            self.add_violation(
                                "NO-CODE-005",
                                str(py_file.relative_to(self.root_path)),
                                line_num,
                                message,
                            )
            except Exception as e:
                self.add_warning("NO-CODE-005", f"Could not check {py_file}: {e}")

    def check_file_length(self) -> None:
        """Check that files don't exceed 500 lines (NO-CODE-002)."""
        for py_file in self.root_path.rglob("*.py"):
            if "venv" in str(py_file) or ".git" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()

                # Count lines excluding imports at the top
                import_section_ended = False
                line_count = 0

                for line in lines:
                    stripped = line.strip()
                    if not import_section_ended:
                        if stripped and not (
                            stripped.startswith("import ")
                            or stripped.startswith("from ")
                            or stripped.startswith("#")
                        ):
                            import_section_ended = True

                    if import_section_ended or stripped:
                        line_count += 1

                if line_count > 500:
                    self.add_violation(
                        "NO-CODE-002",
                        str(py_file.relative_to(self.root_path)),
                        line_count,
                        f"File has {line_count} lines (max: 500)",
                    )
            except Exception as e:
                self.add_warning("NO-CODE-002", f"Could not check {py_file}: {e}")

    def check_function_parameters(self) -> None:
        """Check functions don't have more than 7 parameters (NO-CODE-004)."""
        for py_file in self.root_path.rglob("*.py"):
            if "venv" in str(py_file) or ".git" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        param_count = len(node.args.args) + len(node.args.posonlyargs)
                        if param_count > 7:
                            self.add_violation(
                                "NO-CODE-004",
                                str(py_file.relative_to(self.root_path)),
                                node.lineno,
                                f"Function '{node.name}' has {param_count} parameters (max: 7)",
                            )
            except Exception as e:
                self.add_warning("NO-CODE-004", f"Could not parse {py_file}: {e}")

    def check_bare_except(self) -> None:
        """Check for bare except statements (NO-CODE-001)."""
        for py_file in self.root_path.rglob("*.py"):
            if "venv" in str(py_file) or ".git" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:
                            self.add_violation(
                                "NO-CODE-001",
                                str(py_file.relative_to(self.root_path)),
                                node.lineno,
                                "Bare except statement found",
                            )
            except Exception as e:
                self.add_warning("NO-CODE-001", f"Could not parse {py_file}: {e}")

    def check_test_coverage(self) -> None:
        """Check that all Python files have tests (NO-TEST-001)."""
        src_path = self.root_path / "src"
        tests_path = self.root_path / "tests"

        if not src_path.exists():
            self.add_warning("NO-TEST-001", "src/ directory not found")
            return

        for py_file in src_path.rglob("*.py"):
            if py_file.name in ("__init__.py", "__version__.py"):
                continue

            # Calculate expected test path
            relative_path = py_file.relative_to(src_path)
            test_file_name = f"test_{relative_path.name}"
            test_path = tests_path / relative_path.parent / test_file_name

            if not test_path.exists():
                self.add_violation(
                    "NO-TEST-001",
                    str(py_file.relative_to(self.root_path)),
                    0,
                    f"Missing test file: {test_path.relative_to(self.root_path)}",
                )

    def check_suppress_directives(self) -> None:
        """Check for suppression directives (NO-DEV-001)."""
        suppress_patterns = [
            (r"#\s*type:\s*ignore", "# type: ignore"),
            (r"#\s*noqa", "# noqa"),
            (r"#\s*fmt:\s*off", "# fmt: off"),
        ]

        for py_file in self.root_path.rglob("*.py"):
            if "venv" in str(py_file) or ".git" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern, directive in suppress_patterns:
                        if re.search(pattern, line):
                            self.add_violation(
                                "NO-DEV-001",
                                str(py_file.relative_to(self.root_path)),
                                line_num,
                                f"Found suppression directive: {directive}",
                            )
            except Exception as e:
                self.add_warning("NO-DEV-001", f"Could not check {py_file}: {e}")

    def check_secrets(self) -> None:
        """Check for potential secrets (NO-SEC-001)."""
        secret_patterns = [
            (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][^"\']+["\']', "Potential API key"),
            (
                r'(?i)(secret|password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
                "Potential password/secret",
            ),
            (r'(?i)(token)\s*=\s*["\'][^"\']+["\']', "Potential token"),
            (r'(?i)aws_[a-z_]+\s*=\s*["\'][^"\']+["\']', "Potential AWS credential"),
        ]

        for py_file in self.root_path.rglob("*.py"):
            if "venv" in str(py_file) or ".git" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    # Skip comments and environment variable references
                    if line.strip().startswith("#") or "os.environ" in line:
                        continue

                    for pattern, message in secret_patterns:
                        if re.search(pattern, line):
                            self.add_violation(
                                "NO-SEC-001",
                                str(py_file.relative_to(self.root_path)),
                                line_num,
                                message,
                            )
            except Exception as e:
                self.add_warning("NO-SEC-001", f"Could not check {py_file}: {e}")

    def run_all_checks(self) -> tuple[list[dict], list[dict]]:
        """Run all compliance checks."""
        print(f"{BLUE}Running NO.md compliance checks...{RESET}\n")

        checks = [
            ("Forbidden patterns", self.check_forbidden_patterns),
            ("File length", self.check_file_length),
            ("Function parameters", self.check_function_parameters),
            ("Bare except", self.check_bare_except),
            ("Test coverage", self.check_test_coverage),
            ("Suppression directives", self.check_suppress_directives),
            ("Secrets", self.check_secrets),
        ]

        for check_name, check_func in checks:
            print(f"Checking {check_name}... ", end="", flush=True)
            try:
                check_func()
                print(f"{GREEN}✓{RESET}")
            except Exception as e:
                print(f"{RED}✗{RESET}")
                self.add_warning("GENERAL", f"Error in {check_name}: {e}")

        return self.violations, self.warnings


def print_results(violations: list[dict], warnings: list[dict]) -> None:
    """Print check results."""
    print("\n" + "=" * 80)

    if warnings:
        print(f"\n{YELLOW}Warnings ({len(warnings)}):{RESET}")
        for warning in warnings:
            print(f"  - [{warning['rule']}] {warning['message']}")

    if violations:
        print(f"\n{RED}Violations ({len(violations)}):{RESET}")

        # Group by rule
        by_rule: dict[str, list[dict]] = {}
        for violation in violations:
            rule = violation["rule"]
            if rule not in by_rule:
                by_rule[rule] = []
            by_rule[rule].append(violation)

        for rule, rule_violations in sorted(by_rule.items()):
            print(f"\n  {RED}{rule}{RESET} ({len(rule_violations)} violations):")
            for v in rule_violations[:5]:  # Show first 5
                print(f"    - {v['file']}:{v['line']} - {v['message']}")
            if len(rule_violations) > 5:
                print(f"    ... and {len(rule_violations) - 5} more")

    print("\n" + "=" * 80)

    if not violations:
        print(f"\n{GREEN}✓ All NO.md compliance checks passed!{RESET}")
    else:
        print(f"\n{RED}✗ Found {len(violations)} compliance violations!{RESET}")
        print("\nRun with --fix to attempt automatic fixes for some issues.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check NO.md compliance")
    parser.add_argument(
        "--path", type=Path, default=Path.cwd(), help="Path to check (default: current directory)"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix some violations automatically"
    )
    parser.add_argument(
        "--ci", action="store_true", help="CI mode - exit with error code if violations found"
    )

    args = parser.parse_args()

    checker = ComplianceChecker(args.path)
    violations, warnings = checker.run_all_checks()

    print_results(violations, warnings)

    if args.ci and violations:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
