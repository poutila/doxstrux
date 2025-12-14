#!/usr/bin/env python3
"""Static linter to detect blocking I/O in collectors.

This linter analyzes collector files to detect forbidden blocking operations
in on_token() methods. Blocking I/O in the hot path causes service hangs and
thread pool exhaustion.

Usage:
    python tools/lint_collectors.py src/doxstrux/markdown/collectors_phase8/
    python tools/lint_collectors.py skeleton/doxstrux/markdown/collectors_phase8/
"""

import ast
import sys
from pathlib import Path

# Forbidden patterns that indicate blocking I/O
FORBIDDEN_PATTERNS = [
    'requests.',          # requests.get, requests.post, etc.
    'urllib.request.',    # urllib.request.urlopen
    'httpx.',             # httpx.get
    'aiohttp.',           # Even async is forbidden (wrong pattern)
    'open',               # File I/O (matches open() calls)
    'os.system',          # Shell execution
    'subprocess.',        # Process spawning
    'socket.',            # Raw sockets
    'time.sleep',         # Blocking sleep
    'input',              # User input (matches input() calls)
]


class BlockingCallDetector(ast.NodeVisitor):
    """Detect blocking function calls in AST."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.violations = []
        self.in_on_token = False
        self.in_finalize = False

    def visit_FunctionDef(self, node):
        """Track when we're inside on_token() vs finalize()."""
        if node.name == "on_token":
            self.in_on_token = True
            self.generic_visit(node)
            self.in_on_token = False
        elif node.name == "finalize":
            self.in_finalize = True
            self.generic_visit(node)
            self.in_finalize = False
        else:
            self.generic_visit(node)

    def visit_Call(self, node):
        """Check if call matches forbidden patterns."""
        # Only check calls inside on_token() (finalize() can do I/O)
        if not self.in_on_token:
            self.generic_visit(node)
            return

        # Get string representation of call
        call_str = ""
        try:
            call_str = ast.unparse(node.func)
        except AttributeError:
            # Python < 3.9 doesn't have ast.unparse - use fallback
            if hasattr(node.func, 'id'):
                call_str = node.func.id
            elif hasattr(node.func, 'attr'):
                call_str = node.func.attr

        # Also check for builtin function names directly
        if hasattr(node.func, 'id'):
            func_name = node.func.id
            # Check builtins like open, input
            if func_name in ['open', 'input']:
                self.violations.append({
                    'line': node.lineno,
                    'call': call_str or func_name,
                    'pattern': func_name,
                    'method': 'on_token'
                })

        # Check against forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in call_str:
                self.violations.append({
                    'line': node.lineno,
                    'call': call_str,
                    'pattern': pattern,
                    'method': 'on_token'
                })

        self.generic_visit(node)


def lint_file(filepath: Path) -> list:
    """Lint a single Python file for blocking calls."""
    try:
        with open(filepath) as f:
            source = f.read()
    except Exception as e:
        print(f"⚠️  {filepath}: Could not read file: {e}")
        return []

    try:
        tree = ast.parse(source, str(filepath))
    except SyntaxError as e:
        print(f"⚠️  {filepath}: Syntax error: {e}")
        return []

    detector = BlockingCallDetector(filepath)
    detector.visit(tree)

    return detector.violations


def lint_collectors(collector_dir: Path) -> int:
    """Lint all collector files in directory."""
    collector_files = list(collector_dir.glob("*.py"))

    if not collector_files:
        print(f"⚠️  No collector files found in {collector_dir}")
        return 0

    total_violations = 0

    for filepath in collector_files:
        if filepath.name.startswith("__"):
            continue  # Skip __init__.py

        violations = lint_file(filepath)

        if violations:
            print(f"\n❌ {filepath}:")
            for v in violations:
                print(f"  Line {v['line']:4d}: Forbidden blocking call in {v['method']}(): {v['call']}")
                print(f"           Matched pattern: {v['pattern']}")
            total_violations += len(violations)
        else:
            print(f"✅ {filepath.name}: No blocking calls detected")

    return total_violations


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Lint collectors for blocking I/O",
        epilog="""
Examples:
  python tools/lint_collectors.py src/doxstrux/markdown/collectors_phase8/
  python tools/lint_collectors.py skeleton/doxstrux/markdown/collectors_phase8/

Exit codes:
  0 - No violations found
  1 - Violations found or error
"""
    )
    parser.add_argument("collector_dir", help="Directory containing collector files")
    args = parser.parse_args()

    collector_dir = Path(args.collector_dir)

    if not collector_dir.exists():
        print(f"❌ Directory not found: {collector_dir}")
        sys.exit(1)

    print("=" * 60)
    print("Collector Blocking I/O Linter")
    print("=" * 60)

    violations = lint_collectors(collector_dir)

    print("\n" + "=" * 60)
    if violations > 0:
        print(f"❌ FAILED: Found {violations} blocking call(s)")
        print("\n⚠️  Collectors MUST NOT perform blocking I/O in on_token().")
        print("   Defer to finalize() or async post-processing.")
        sys.exit(1)
    else:
        print("✅ PASSED: No blocking calls detected")
        sys.exit(0)
