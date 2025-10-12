#!/usr/bin/env python3
"""
Generate baseline output for parity testing.

This tool captures the CURRENT parser output before any refactoring,
establishing a baseline for byte-identical parity validation.

Usage:
    python tools/generate_baseline.py \\
        --profile=moderate \\
        --seed=1729 \\
        --corpus=src/docpipe/test_files/test_mds/ \\
        --emit-baseline=baseline/v0_current.json
"""

import argparse
import hashlib
import json
import sys
import time
import traceback
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from doxstrux.markdown_parser_core import MarkdownParserCore


def hash_content(content: str) -> str:
    """Generate SHA-256 hash of normalized content."""
    # Normalize: \r\n → \n, collapse whitespace
    normalized = content.replace('\r\n', '\n').strip()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def parse_with_timing(content: str, config: dict, profile: str) -> tuple[dict, float, int]:
    """Parse content and measure timing + memory.

    Returns:
        (output_dict, elapsed_ms, peak_memory_bytes)
    """
    tracemalloc.start()
    start = time.perf_counter()

    try:
        parser = MarkdownParserCore(content, config=config, security_profile=profile)
        result = parser.parse()
    except Exception as e:
        result = {
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        }

    elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return result, elapsed, peak


def find_markdown_files(corpus_path: Path) -> list[Path]:
    """Find all .md files in corpus directory."""
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus path not found: {corpus_path}")

    if corpus_path.is_file():
        return [corpus_path]

    # Recursively find all .md files
    return sorted(corpus_path.rglob('*.md'))


def generate_baseline(
    corpus_path: str,
    profile: str = 'moderate',
    seed: int = 1729,
    runs_cold: int = 3,
    runs_warm: int = 5,
    config: dict | None = None
) -> dict[str, Any]:
    """Generate baseline output for all files in corpus.

    Args:
        corpus_path: Path to corpus directory or single .md file
        profile: Security profile (strict/moderate/permissive)
        seed: Random seed for reproducibility
        runs_cold: Number of cold runs for timing
        runs_warm: Number of warm runs for timing
        config: Optional parser configuration

    Returns:
        Baseline dictionary with metadata, performance, and outputs
    """
    corpus = Path(corpus_path)
    md_files = find_markdown_files(corpus)

    if not md_files:
        raise ValueError(f"No .md files found in {corpus_path}")

    print(f"📁 Found {len(md_files)} markdown files")

    # Default config if not provided
    if config is None:
        config = {
            'preset': 'commonmark',  # Use commonmark (gfm not available in all versions)
            'allows_html': False,
            'plugins': ['table', 'strikethrough'],  # No linkify by default
        }

    # Collect baseline data
    baseline = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'profile': profile,
            'corpus_path': str(corpus),
            'corpus_file_count': len(md_files),
            'seed': seed,
            'config': config,
        },
        'performance': {
            'runs_cold': runs_cold,
            'runs_warm': runs_warm,
            'timings_ms': [],
            'memory_peak_mb': [],
        },
        'outputs': {}
    }

    # Try to get git commit
    try:
        import subprocess
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
        baseline['metadata']['git_commit'] = result.stdout.strip()[:8]
    except Exception:
        baseline['metadata']['git_commit'] = 'unknown'

    # Try to get markdown-it-py version
    try:
        import markdown_it
        baseline['metadata']['markdown_it_py_version'] = markdown_it.__version__
    except Exception:
        baseline['metadata']['markdown_it_py_version'] = 'unknown'

    # Parse each file
    for i, md_file in enumerate(md_files, 1):
        rel_path = md_file.relative_to(corpus) if md_file.is_relative_to(corpus) else md_file.name
        print(f"  [{i}/{len(md_files)}] Parsing {rel_path}...", end='')

        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f" ❌ Read error: {e}")
            baseline['outputs'][str(rel_path)] = {
                'error': f'File read error: {e}',
                'hash': None,
                'output': None,
            }
            continue

        # Run multiple times for performance measurement
        timings = []
        memory_peaks = []

        # Cold runs
        for _ in range(runs_cold):
            _, elapsed, peak = parse_with_timing(content, config, profile)
            timings.append(elapsed)
            memory_peaks.append(peak)

        # Warm runs (parser already initialized)
        for _ in range(runs_warm):
            _, elapsed, peak = parse_with_timing(content, config, profile)
            timings.append(elapsed)
            memory_peaks.append(peak)

        # Final parse for output capture
        output, _, _ = parse_with_timing(content, config, profile)

        # Store results
        baseline['outputs'][str(rel_path)] = {
            'hash': hash_content(content),
            'size_bytes': len(content.encode('utf-8')),
            'line_count': content.count('\n') + 1,
            'output': output,
            'timings_ms': timings,
            'memory_peaks_bytes': memory_peaks,
        }

        # Aggregate performance metrics
        baseline['performance']['timings_ms'].extend(timings)
        baseline['performance']['memory_peak_mb'].extend([p / (1024 * 1024) for p in memory_peaks])

        print(f" ✅ ({timings[0]:.2f}ms)")

    # Calculate aggregate statistics
    if baseline['performance']['timings_ms']:
        timings = sorted(baseline['performance']['timings_ms'])
        baseline['performance']['median_ms'] = timings[len(timings) // 2]
        baseline['performance']['p95_ms'] = timings[int(len(timings) * 0.95)]

    if baseline['performance']['memory_peak_mb']:
        memory = sorted(baseline['performance']['memory_peak_mb'])
        baseline['performance']['median_memory_mb'] = memory[len(memory) // 2]

    return baseline


def main():
    parser = argparse.ArgumentParser(description='Generate baseline for parity testing')
    parser.add_argument('--profile', default='moderate', choices=['strict', 'moderate', 'permissive'],
                        help='Security profile')
    parser.add_argument('--seed', type=int, default=1729, help='Random seed')
    parser.add_argument('--corpus', required=True, help='Path to corpus directory or .md file')
    parser.add_argument('--emit-baseline', required=True, help='Output path for baseline JSON')
    parser.add_argument('--runs-cold', type=int, default=3, help='Number of cold runs')
    parser.add_argument('--runs-warm', type=int, default=5, help='Number of warm runs')

    args = parser.parse_args()

    print(f"🧪 Generating baseline...")
    print(f"  Profile: {args.profile}")
    print(f"  Corpus: {args.corpus}")
    print(f"  Seed: {args.seed}")

    try:
        baseline = generate_baseline(
            corpus_path=args.corpus,
            profile=args.profile,
            seed=args.seed,
            runs_cold=args.runs_cold,
            runs_warm=args.runs_warm
        )

        # Write baseline
        output_path = Path(args.emit_baseline)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open('w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Baseline saved to: {output_path}")
        print(f"  Files processed: {baseline['metadata']['corpus_file_count']}")
        print(f"  Median time: {baseline['performance'].get('median_ms', 0):.2f}ms")
        print(f"  P95 time: {baseline['performance'].get('p95_ms', 0):.2f}ms")
        print(f"  Median memory: {baseline['performance'].get('median_memory_mb', 0):.2f}MB")

    except Exception as e:
        print(f"\n❌ Error generating baseline: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
