#!/usr/bin/env python3
"""
Generate missing .json files for unpaired .md files.

This tool finds .md files without corresponding .json files and generates
the JSON output using the current parser.

Usage:
    # Generate all missing pairs
    python3 tools/generate_missing_pairs.py \\
        --corpus=src/docpipe/md_parser_testing \\
        --profile=moderate

    # Exclude README/INDEX files
    python3 tools/generate_missing_pairs.py \\
        --corpus=src/docpipe/md_parser_testing \\
        --profile=moderate \\
        --exclude-pattern="README|INDEX|CLAUDEorig"
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from doxstrux.markdown_parser_core import MarkdownParserCore


def should_exclude(file_path: Path, exclude_pattern: str) -> bool:
    """Check if file should be excluded based on pattern.

    Args:
        file_path: Path to file
        exclude_pattern: Regex pattern (e.g., "README|INDEX|CLAUDEorig")

    Returns:
        True if file should be excluded
    """
    if not exclude_pattern:
        return False

    return bool(re.search(exclude_pattern, str(file_path), re.IGNORECASE))


def generate_missing_pairs(
    corpus_path: str,
    profile: str = 'moderate',
    exclude_pattern: str = '',
    dry_run: bool = False
) -> tuple[list[Path], list[Path]]:
    """Generate .json for all .md files that lack pairs.

    Args:
        corpus_path: Path to corpus directory
        profile: Security profile for parser
        exclude_pattern: Regex pattern for files to exclude
        dry_run: If True, only show what would be generated

    Returns:
        (generated_files, skipped_files)
    """
    corpus = Path(corpus_path)
    generated = []
    skipped = []

    if not corpus.exists():
        raise FileNotFoundError(f"Corpus path not found: {corpus}")

    # Find all .md files
    md_files = sorted(corpus.rglob('*.md'))

    print(f"🔍 Scanning corpus: {corpus}")
    print(f"  Found {len(md_files)} .md files")

    # Configuration for parser
    config = {
        'preset': 'commonmark',
        'allows_html': False,
        'plugins': ['table', 'strikethrough'],
    }

    for md_file in md_files:
        json_file = md_file.with_suffix('.json')

        # Skip if JSON already exists
        if json_file.exists():
            continue

        # Check exclusions
        if should_exclude(md_file, exclude_pattern):
            rel_path = md_file.relative_to(corpus)
            print(f"  ⏭️  Skipping (excluded): {rel_path}")
            skipped.append(md_file)
            continue

        rel_path = md_file.relative_to(corpus)
        print(f"  📝 Generating: {rel_path}")

        if dry_run:
            print(f"     Would create: {json_file.name}")
            generated.append(md_file)
            continue

        try:
            content = md_file.read_text(encoding='utf-8')
            parser = MarkdownParserCore(
                content,
                config=config,
                security_profile=profile
            )
            output = parser.parse()

            # Write JSON
            with json_file.open('w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            generated.append(md_file)
            print(f"     ✅ Created {json_file.name}")

        except Exception as e:
            print(f"     ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    return generated, skipped


def main():
    parser = argparse.ArgumentParser(
        description='Generate missing .json files for unpaired .md files'
    )
    parser.add_argument(
        '--corpus',
        required=True,
        help='Path to corpus directory'
    )
    parser.add_argument(
        '--profile',
        default='moderate',
        choices=['strict', 'moderate', 'permissive'],
        help='Security profile for parser (default: moderate)'
    )
    parser.add_argument(
        '--exclude-pattern',
        default='',
        help='Regex pattern for files to exclude (e.g., "README|INDEX")'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be generated without actually creating files'
    )

    args = parser.parse_args()

    try:
        generated, skipped = generate_missing_pairs(
            args.corpus,
            args.profile,
            args.exclude_pattern,
            args.dry_run
        )

        print(f"\n📊 Summary:")
        print(f"  Generated: {len(generated)} new .json files")
        print(f"  Skipped: {len(skipped)} excluded files")

        if args.dry_run:
            print(f"\n💡 This was a dry run. Use without --dry-run to actually create files.")
        else:
            print(f"\n✅ Done! {len(generated)} new JSON files created.")

            if generated:
                print(f"\n📝 Next steps:")
                print(f"  1. Spot-check a few generated files for correctness")
                print(f"  2. Commit new .json files to repository:")
                print(f"     git add {args.corpus}/**/*.json")
                print(f"     git commit -m 'Add missing JSON pairs ({len(generated)} files)'")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
