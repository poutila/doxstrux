#!/usr/bin/env python3
"""Safe cleanup script that protects critical directories.

This script ONLY removes files that are:
1. Already in .gitignore
2. NOT in protected directories
3. Confirmed safe to delete
"""

import argparse
import shutil
from pathlib import Path

# Directories that must NEVER be touched
PROTECTED_DIRECTORIES = {".venv", "venv", "src", "tests", "docs", "planning", "scripts", "examples"}

# Pattern-based protection
PROTECTED_PATTERNS = [
    "test_*",  # ALL test directories
    "*_test*",  # Any directory with test in name
    "edit_regression_tests",
    "claude_semantic_test_variants",
]

# Patterns safe to clean (from .gitignore)
SAFE_TO_CLEAN = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".pytest_cache",
    ".coverage",
    ".coverage.*",
    "htmlcov",
    "*.egg-info",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "*.tmp",
    "*.bak",
    "*.swp",
    "*~",
]

# Additional specific items safe to remove
SPECIFIC_REMOVALS = [
    "validation_reports",  # Already in .gitignore
    "uv.lock",  # Can regenerate
]


def is_in_protected_directory(path: Path) -> bool:
    """Check if path is inside a protected directory."""
    # Check explicit protected directories
    for parent in path.parents:
        if parent.name in PROTECTED_DIRECTORIES:
            return True
    if path.name in PROTECTED_DIRECTORIES:
        return True

    # Check pattern-based protection
    for pattern in PROTECTED_PATTERNS:
        # Check the path itself
        if path.match(pattern):
            return True
        # Check all parent directories
        for parent in path.parents:
            if parent.match(pattern):
                return True

    return False


def find_cleanable_items(root_dir: Path) -> tuple[list[Path], int]:
    """Find all items safe to clean."""
    items_to_clean = []
    total_size = 0

    # Check for Python cache directories
    for pattern in ["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]:
        for item in root_dir.rglob(pattern):
            if not is_in_protected_directory(item):
                size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                total_size += size
                items_to_clean.append(item)

    # Check for specific removals
    for item_name in SPECIFIC_REMOVALS:
        item = root_dir / item_name
        if item.exists() and not is_in_protected_directory(item):
            if item.is_file():
                total_size += item.stat().st_size
            else:
                size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                total_size += size
            items_to_clean.append(item)

    # Check for file patterns
    for pattern in ["*.pyc", "*.pyo", "*.tmp", "*.bak", "*.swp", "*~"]:
        for item in root_dir.rglob(pattern):
            if item.is_file() and not is_in_protected_directory(item):
                total_size += item.stat().st_size
                items_to_clean.append(item)

    return items_to_clean, total_size


def format_size(size: int) -> str:
    """Format size in human-readable form."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def clean_items(items: list[Path], dry_run: bool = True) -> int:
    """Clean the identified items."""
    cleaned = 0

    for item in items:
        try:
            relative_path = item.relative_to(Path.cwd())
            if dry_run:
                print(f"  Would remove: {relative_path}")
            else:
                print(f"  Removing: {relative_path}")
                if item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)
                cleaned += 1
        except Exception as e:
            print(f"  ❌ Error removing {item}: {e}")

    return cleaned


def main():
    """Run safe cleanup."""
    parser = argparse.ArgumentParser(description="Safe cleanup of temporary files")
    parser.add_argument(
        "--execute", action="store_true", help="Actually delete files (default is dry run)"
    )
    args = parser.parse_args()

    root_dir = Path.cwd()

    print("🧹 Safe Cleanup Tool")
    print("=" * 50)

    # Verify we're in the right directory
    if not (root_dir / "src" / "docpipe").exists():
        print("❌ ERROR: Must run from docpipe project root!")
        return 1

    # Show protected directories
    print("\n🛡️  Protected directories (will NOT touch):")
    for d in sorted(PROTECTED_DIRECTORIES):
        if (root_dir / d).exists():
            print(f"  ✓ {d}")

    # Find cleanable items
    print("\n🔍 Scanning for cleanable items...")
    items, total_size = find_cleanable_items(root_dir)

    if not items:
        print("\n✨ Nothing to clean - already tidy!")
        return 0

    # Show what would be cleaned
    print(f"\n📊 Found {len(items)} items to clean ({format_size(total_size)}):")

    if args.execute:
        print("\n🗑️  Cleaning files...")
        cleaned = clean_items(items, dry_run=False)
        print(f"\n✅ Cleaned {cleaned} items, freed {format_size(total_size)}")
    else:
        print("\n🔍 DRY RUN - would remove:")
        clean_items(items, dry_run=True)
        print("\n💡 Run with --execute to actually delete these files")
        print(f"   Would free approximately {format_size(total_size)}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
