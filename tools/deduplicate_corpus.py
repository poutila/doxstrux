#!/usr/bin/env python3
"""
Deduplicate md-json pairs in test corpus.

This tool recursively scans for .md files, computes checksums,
and removes duplicates while preserving the canonical copy.

Usage:
    # Dry run (show what would be deleted)
    python3 tools/deduplicate_corpus.py \\
        --corpus=src/docpipe/md_parser_testing/test_mds \\
        --dry-run

    # Actually delete duplicates
    python3 tools/deduplicate_corpus.py \\
        --corpus=src/docpipe/md_parser_testing/test_mds \\
        --delete
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of file content.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of SHA-256 hash
    """
    sha256 = hashlib.sha256()

    try:
        with file_path.open('rb') as f:
            # Read in chunks for large files
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        print(f"  ⚠️  Error reading {file_path}: {e}")
        return None


def find_md_json_pairs(corpus_path: Path) -> List[Tuple[Path, Path | None]]:
    """Find all .md files and their corresponding .json files.

    Args:
        corpus_path: Root directory to search

    Returns:
        List of (md_path, json_path) tuples (json_path may be None)
    """
    pairs = []

    # Find all .md files
    md_files = sorted(corpus_path.rglob('*.md'))

    for md_file in md_files:
        # Look for corresponding .json file
        json_file = md_file.with_suffix('.json')

        if json_file.exists():
            pairs.append((md_file, json_file))
        else:
            pairs.append((md_file, None))

    return pairs


def deduplicate_pairs(
    pairs: List[Tuple[Path, Path | None]],
    corpus_root: Path,
    preserve_strategy: str = 'shortest-path'
) -> Tuple[List[Tuple[Path, Path | None]], Dict[str, List[Path]]]:
    """Deduplicate md-json pairs based on content checksum.

    Args:
        pairs: List of (md_path, json_path) tuples
        corpus_root: Root directory for relative path calculation
        preserve_strategy: Which copy to keep ('shortest-path', 'first', 'last')

    Returns:
        (unique_pairs, duplicates_map) where duplicates_map is checksum -> list of duplicate paths
    """
    # Track checksums: checksum -> [(md_path, json_path), ...]
    checksum_to_pairs: Dict[str, List[Tuple[Path, Path | None]]] = {}

    print(f"📊 Computing checksums for {len(pairs)} md-json pairs...")

    for md_path, json_path in pairs:
        # Compute checksum of .md file
        md_checksum = compute_checksum(md_path)

        if md_checksum is None:
            print(f"  ⚠️  Skipping {md_path} (checksum failed)")
            continue

        # If there's a JSON file, include it in the checksum
        if json_path:
            json_checksum = compute_checksum(json_path)
            combined_checksum = hashlib.sha256(
                (md_checksum + json_checksum).encode()
            ).hexdigest()
        else:
            combined_checksum = md_checksum

        # Track this pair
        if combined_checksum not in checksum_to_pairs:
            checksum_to_pairs[combined_checksum] = []

        checksum_to_pairs[combined_checksum].append((md_path, json_path))

    # Find duplicates and select canonical copies
    unique_pairs = []
    duplicates_map = {}

    for checksum, pairs_list in checksum_to_pairs.items():
        if len(pairs_list) == 1:
            # No duplicates
            unique_pairs.append(pairs_list[0])
        else:
            # Duplicates found - select canonical copy
            if preserve_strategy == 'shortest-path':
                # Keep the one with shortest relative path
                canonical = min(
                    pairs_list,
                    key=lambda p: len(str(p[0].relative_to(corpus_root)))
                )
            elif preserve_strategy == 'first':
                canonical = pairs_list[0]
            elif preserve_strategy == 'last':
                canonical = pairs_list[-1]
            else:
                raise ValueError(f"Unknown preserve_strategy: {preserve_strategy}")

            unique_pairs.append(canonical)
            duplicates_map[checksum] = [p[0] for p in pairs_list if p != canonical]

    return unique_pairs, duplicates_map


def delete_duplicates(
    duplicates_map: Dict[str, List[Path]],
    dry_run: bool = True
) -> int:
    """Delete duplicate files.

    Args:
        duplicates_map: Map of checksum -> list of duplicate file paths
        dry_run: If True, only print what would be deleted

    Returns:
        Number of files deleted (or would be deleted)
    """
    deleted_count = 0

    for checksum, duplicate_paths in duplicates_map.items():
        for md_path in duplicate_paths:
            # Also delete corresponding .json if it exists
            json_path = md_path.with_suffix('.json')

            files_to_delete = [md_path]
            if json_path.exists():
                files_to_delete.append(json_path)

            for file_path in files_to_delete:
                if dry_run:
                    print(f"  🔍 Would delete: {file_path}")
                else:
                    try:
                        file_path.unlink()
                        print(f"  🗑️  Deleted: {file_path}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"  ❌ Error deleting {file_path}: {e}")

    return deleted_count


def generate_dedup_report(
    total_pairs: int,
    unique_pairs: int,
    duplicates_map: Dict[str, List[Path]],
    corpus_root: Path
) -> str:
    """Generate deduplication report.

    Args:
        total_pairs: Total number of md-json pairs found
        unique_pairs: Number of unique pairs
        duplicates_map: Map of duplicates
        corpus_root: Root directory

    Returns:
        Report string
    """
    report = []
    report.append(f"\n📊 Deduplication Report")
    report.append(f"=" * 60)
    report.append(f"  Total pairs found: {total_pairs}")
    report.append(f"  Unique pairs: {unique_pairs}")
    report.append(f"  Duplicate groups: {len(duplicates_map)}")
    report.append(f"  Duplicate files: {sum(len(v) for v in duplicates_map.values())}")

    if duplicates_map:
        report.append(f"\n🔍 Duplicate Groups:")

        for i, (checksum, duplicate_paths) in enumerate(duplicates_map.items(), 1):
            report.append(f"\n  Group {i} (checksum: {checksum[:16]}...):")
            report.append(f"    {len(duplicate_paths)} duplicates:")

            for dup_path in duplicate_paths:
                rel_path = dup_path.relative_to(corpus_root)
                report.append(f"      - {rel_path}")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description='Deduplicate md-json pairs in test corpus'
    )
    parser.add_argument(
        '--corpus',
        required=True,
        help='Path to corpus directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Actually delete duplicate files'
    )
    parser.add_argument(
        '--preserve',
        default='shortest-path',
        choices=['shortest-path', 'first', 'last'],
        help='Which copy to preserve (default: shortest-path)'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Only generate report, do not delete'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.delete and args.dry_run:
        print("❌ Error: Cannot use both --delete and --dry-run")
        sys.exit(1)

    if not args.delete and not args.dry_run and not args.report_only:
        print("⚠️  No action specified. Use --dry-run, --delete, or --report-only")
        args.dry_run = True
        print("   Defaulting to --dry-run mode")

    corpus_path = Path(args.corpus)

    if not corpus_path.exists():
        print(f"❌ Error: Corpus path not found: {corpus_path}")
        sys.exit(1)

    print(f"🔍 Scanning corpus: {corpus_path}")

    # Find all md-json pairs
    pairs = find_md_json_pairs(corpus_path)
    print(f"📁 Found {len(pairs)} md-json pairs")

    # Deduplicate
    unique_pairs, duplicates_map = deduplicate_pairs(
        pairs,
        corpus_path,
        preserve_strategy=args.preserve
    )

    # Generate report
    report = generate_dedup_report(
        len(pairs),
        len(unique_pairs),
        duplicates_map,
        corpus_path
    )
    print(report)

    # Delete duplicates (if requested)
    if duplicates_map:
        if args.report_only:
            print(f"\n📋 Report-only mode: No files were deleted")
        elif args.delete:
            print(f"\n🗑️  Deleting {sum(len(v) for v in duplicates_map.values())} duplicate files...")
            deleted = delete_duplicates(duplicates_map, dry_run=False)
            print(f"\n✅ Deleted {deleted} files")
        elif args.dry_run:
            print(f"\n🔍 Dry-run mode: Showing what would be deleted...")
            delete_duplicates(duplicates_map, dry_run=True)
            print(f"\n💡 Use --delete to actually remove duplicates")
    else:
        print(f"\n✅ No duplicates found! Corpus is clean.")

    sys.exit(0)


if __name__ == '__main__':
    main()
