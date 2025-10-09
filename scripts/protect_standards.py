#!/usr/bin/env python3
"""
Pre-commit hook to protect canonical standard files.

Prevents accidental modification of protected documentation files.
"""

import subprocess
import sys

PROTECTED_FILES = [
    "docs/standards/CLAUDE_MD_REQUIREMENTS.md",
    "docs/standards/SECURITY_STANDARDS.md",
    "docs/standards/DEVELOPMENT_WORKFLOW.md",
    "docs/standards/PROJECT_STRUCTURE.md",
]


def get_staged_files():
    """Get list of files staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], check=False, capture_output=True, text=True
    )
    return result.stdout.strip().split("\n") if result.stdout else []


def check_protected_files():
    """Check if any protected files are being modified."""
    staged_files = get_staged_files()

    violations = []
    for staged in staged_files:
        if staged in PROTECTED_FILES:
            violations.append(staged)

    if violations:
        print("\n🛡️  PROTECTED FILE MODIFICATION DETECTED!")
        print("=" * 60)
        print("\nThe following protected files cannot be modified directly:")
        for file in violations:
            print(f"  ❌ {file}")

        print("\n📝 These files are canonical standards and require:")
        print("  1. Formal review process")
        print("  2. Version increment")
        print("  3. ADR (Architecture Decision Record)")
        print("\n💡 To propose changes:")
        print("  1. Create an ADR in docs/adr/")
        print("  2. Get team approval")
        print("  3. Update with version increment")
        print("\n🚫 Commit blocked to protect standards integrity.")
        return False

    return True


def main():
    """Main entry point for pre-commit hook."""
    if not check_protected_files():
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
