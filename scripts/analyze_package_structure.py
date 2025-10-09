#!/usr/bin/env python3
"""
Package Structure Analysis Script

Analyzes the src/docpipe/ package structure against CLAUDE.md requirements
and provides recommendations for alignment.

Usage:
    python scripts/analyze_package_structure.py
    python scripts/analyze_package_structure.py --create-missing
"""

import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class PackageStructureAnalyzer:
    """Analyzes package structure compliance with CLAUDE.md."""

    def __init__(self, project_root: Path = Path.cwd()):
        """Initialize analyzer."""
        self.project_root = project_root
        self.package_root = project_root / "src" / "docpipe"

        # Expected DDD structure per CLAUDE.md
        self.expected_dirs = {
            "domain": "Core business logic (DDD entities, value objects)",
            "services": "Application services (orchestration layer)",
            "api": "API routes and schemas",
            "database": "Database models and migrations",
            "events": "Event handlers and pub-sub logic",
            "utils": "Utility functions",
            "config": "Configuration management",
        }

        # Current structure mapping
        self.current_to_ddd_mapping = {
            "analyzers": "domain",  # Analysis logic maps to domain
            "core": "services",  # Engine maps to services
            "models": "domain",  # Data models map to domain entities
            "cli": None,  # CLI doesn't have DDD equivalent
        }

    def analyze_current_structure(self) -> dict[str, list[Path]]:
        """Analyze current package structure."""
        structure = {"directories": [], "python_files": [], "other_files": []}

        if not self.package_root.exists():
            logger.error(f"Package root not found: {self.package_root}")
            return structure

        # Scan package directory
        for item in self.package_root.rglob("*"):
            if item.is_dir() and "__pycache__" not in str(item):
                rel_path = item.relative_to(self.package_root)
                structure["directories"].append(rel_path)
            elif item.is_file():
                if item.suffix == ".py":
                    structure["python_files"].append(item.relative_to(self.package_root))
                else:
                    structure["other_files"].append(item.relative_to(self.package_root))

        return structure

    def check_ddd_compliance(self) -> tuple[set[str], set[str], dict[str, str]]:
        """Check compliance with DDD structure."""
        # Get current top-level directories
        current_dirs = set()
        for item in self.package_root.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                current_dirs.add(item.name)

        expected = set(self.expected_dirs.keys())

        # What's missing
        missing = expected - current_dirs

        # What's extra (not in DDD structure)
        extra = current_dirs - expected

        # Check for misnamed or misplaced
        suggestions = {}
        for current in extra:
            if current in self.current_to_ddd_mapping:
                ddd_equivalent = self.current_to_ddd_mapping[current]
                if ddd_equivalent and ddd_equivalent in missing:
                    suggestions[current] = ddd_equivalent

        return missing, extra, suggestions

    def analyze_file_organization(self) -> dict[str, list[str]]:
        """Analyze how files are organized within directories."""
        organization = {}

        # Analyze each directory
        for dir_path in self.package_root.iterdir():
            if dir_path.is_dir() and not dir_path.name.startswith("__"):
                files = []
                for py_file in dir_path.rglob("*.py"):
                    if "__pycache__" not in str(py_file):
                        rel_path = py_file.relative_to(dir_path)
                        files.append(str(rel_path))

                if files:
                    organization[dir_path.name] = sorted(files)

        return organization

    def generate_migration_plan(self) -> list[tuple[str, str, str]]:
        """Generate a migration plan to DDD structure."""
        migration_steps = []

        # Map current directories to DDD equivalents
        mappings = [
            ("analyzers/compliance", "domain/compliance", "Move compliance analysis domain logic"),
            ("analyzers/document", "domain/document", "Move document analysis domain logic"),
            ("analyzers/project", "domain/project", "Move project analysis domain logic"),
            ("analyzers/base.py", "domain/base.py", "Move base analyzer to domain"),
            (
                "core/engine.py",
                "services/analysis_service.py",
                "Refactor engine as analysis service",
            ),
            ("core/exceptions.py", "domain/exceptions.py", "Move domain exceptions"),
            ("models/", "domain/entities/", "Reorganize models as domain entities"),
            ("cli/", "api/cli/", "Move CLI under API as an interface"),
            ("api.py", "api/__init__.py", "Convert api.py to api package"),
        ]

        for src, dst, description in mappings:
            src_path = self.package_root / src
            if src_path.exists():
                migration_steps.append((str(src), str(dst), description))

        return migration_steps

    def create_missing_directories(self, dry_run: bool = True) -> list[Path]:
        """Create missing DDD directories with README files."""
        created = []
        missing, _, _ = self.check_ddd_compliance()

        for dir_name in missing:
            dir_path = self.package_root / dir_name
            readme_path = dir_path / "README.md"
            init_path = dir_path / "__init__.py"

            if dry_run:
                logger.info(f"[DRY RUN] Would create: {dir_path.relative_to(self.project_root)}")
                created.append(dir_path)
            else:
                dir_path.mkdir(exist_ok=True)

                # Create README with description
                readme_content = f"# {dir_name.title()}\n\n{self.expected_dirs[dir_name]}\n"
                readme_path.write_text(readme_content)

                # Create __init__.py
                init_path.write_text(f'"""{self.expected_dirs[dir_name]}"""\n')

                logger.info(f"Created: {dir_path.relative_to(self.project_root)}")
                created.append(dir_path)

        return created

    def print_analysis(self):
        """Print comprehensive analysis."""
        logger.info("\n" + "=" * 70)
        logger.info("📦 PACKAGE STRUCTURE ANALYSIS")
        logger.info("=" * 70)

        # Current structure
        structure = self.analyze_current_structure()
        logger.info("\n📁 Current Structure:")
        logger.info(f"  Directories: {len(structure['directories'])}")
        logger.info(f"  Python files: {len(structure['python_files'])}")
        logger.info(f"  Other files: {len(structure['other_files'])}")

        # DDD compliance
        missing, extra, suggestions = self.check_ddd_compliance()

        logger.info("\n🎯 DDD Compliance Check:")
        logger.info(f"\n  ❌ Missing DDD directories ({len(missing)}):")
        for dir_name in sorted(missing):
            logger.info(f"     - {dir_name}: {self.expected_dirs[dir_name]}")

        logger.info(f"\n  ⚠️  Extra directories not in DDD ({len(extra)}):")
        for dir_name in sorted(extra):
            logger.info(f"     - {dir_name}")

        if suggestions:
            logger.info("\n  💡 Suggested mappings:")
            for current, ddd in suggestions.items():
                logger.info(f"     - {current} → {ddd}")

        # File organization
        organization = self.analyze_file_organization()
        logger.info("\n📂 File Organization:")
        for dir_name, files in sorted(organization.items()):
            logger.info(f"\n  {dir_name}/ ({len(files)} files)")
            for file in files[:3]:  # Show first 3 files
                logger.info(f"    - {file}")
            if len(files) > 3:
                logger.info(f"    ... and {len(files) - 3} more")

        # Architecture analysis
        logger.info("\n🏗️  Architecture Pattern:")
        logger.info("  Current: Feature-based organization (analyzers, cli, core)")
        logger.info("  Expected: Domain-Driven Design layers (domain, services, api)")
        logger.info("  Status: Non-compliant but functional for CLI tool")

        # Recommendations
        logger.info("\n📋 Recommendations:")
        logger.info("\n  Option 1: Minimal Compliance (Recommended)")
        logger.info("  - Create missing directories as placeholders")
        logger.info("  - Document why DDD isn't fully implemented")
        logger.info("  - Keep current functional structure")

        logger.info("\n  Option 2: Full DDD Migration")
        logger.info("  - Reorganize analyzers → domain")
        logger.info("  - Refactor core/engine → services")
        logger.info("  - Convert api.py → api package")
        logger.info("  - Significant refactoring required")

        logger.info("\n  Option 3: Update CLAUDE.md")
        logger.info("  - Document exceptions for CLI tools")
        logger.info("  - Define alternative structures")
        logger.info("  - Maintain architectural flexibility")

        # Migration plan
        if extra:
            logger.info("\n🔄 Migration Plan (if implementing DDD):")
            migration = self.generate_migration_plan()
            for i, (src, dst, desc) in enumerate(migration[:5], 1):
                logger.info(f"  {i}. {desc}")
                logger.info(f"     {src} → {dst}")

        logger.info("\n" + "=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze package structure against CLAUDE.md DDD requirements"
    )
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="Create missing DDD directories with README files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be created without making changes",
    )

    args = parser.parse_args()

    analyzer = PackageStructureAnalyzer()
    analyzer.print_analysis()

    if args.create_missing or args.dry_run:
        logger.info("\n🔨 Creating Missing Directories:")
        created = analyzer.create_missing_directories(dry_run=args.dry_run)
        if created:
            logger.info(
                f"\n{'Would create' if args.dry_run else 'Created'} {len(created)} directories"
            )
        else:
            logger.info("\nNo directories to create")


if __name__ == "__main__":
    main()
