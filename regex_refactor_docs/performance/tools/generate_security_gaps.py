#!/usr/bin/env python3
"""
Auto-generate SECURITY_GAPS.md by diffing src/ and skeleton/ security policies (Gap 8).

This tool compares security policy files between src/ and skeleton/ directories
to automatically detect gaps in security coverage.

Usage:
    python tools/generate_security_gaps.py

    # Specify custom directories
    python tools/generate_security_gaps.py --src /path/to/src --skeleton /path/to/skeleton

    # Output to custom file
    python tools/generate_security_gaps.py --output SECURITY_GAPS.md

Exit Codes:
    0: Report generated successfully
    1: Errors during generation
"""

from __future__ import annotations
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def find_policy_files(base_dir: Path) -> List[Path]:
    """
    Find all *_POLICY.md and *_policy.md files recursively.

    Args:
        base_dir: Directory to search

    Returns:
        List of policy file paths
    """
    if not base_dir.exists():
        return []

    # Case-insensitive search for policy files
    policy_files = []
    for pattern in ["*_POLICY.md", "*_policy.md", "*POLICY.md"]:
        policy_files.extend(base_dir.rglob(pattern))

    return sorted(set(policy_files))  # Remove duplicates, sort


def compare_policies(src_policies: List[Path], skeleton_policies: List[Path], src_root: Path, skeleton_root: Path) -> List[Dict[str, Any]]:
    """
    Compare policy files and identify gaps.

    Args:
        src_policies: Policy files from src/
        skeleton_policies: Policy files from skeleton/
        src_root: Root of src directory
        skeleton_root: Root of skeleton directory

    Returns:
        List of gap dicts with keys: type, file, severity, description
    """
    gaps = []

    # Extract relative paths for comparison
    src_names = {p.relative_to(src_root): p for p in src_policies}
    skeleton_names = {p.relative_to(skeleton_root): p for p in skeleton_policies}

    # Find missing policies in skeleton
    missing = set(src_names.keys()) - set(skeleton_names.keys())
    for rel_path in missing:
        gaps.append({
            "type": "missing_policy",
            "file": str(rel_path),
            "severity": "high",
            "description": f"Policy {rel_path} exists in src/ but not in skeleton/",
            "action": f"Copy {src_names[rel_path]} to {skeleton_root / rel_path}"
        })

    # Find extra policies in skeleton (not gaps, but informational)
    extra = set(skeleton_names.keys()) - set(src_names.keys())
    for rel_path in extra:
        gaps.append({
            "type": "extra_policy",
            "file": str(rel_path),
            "severity": "info",
            "description": f"Policy {rel_path} exists in skeleton/ but not in src/ (new policy)",
            "action": "Verify this is intentional"
        })

    # Compare content of matching policies
    matching = set(src_names.keys()) & set(skeleton_names.keys())
    for rel_path in matching:
        src_content = src_names[rel_path].read_text()
        skeleton_content = skeleton_names[rel_path].read_text()

        if src_content != skeleton_content:
            # Content differs - analyze difference
            src_lines = len(src_content.splitlines())
            skeleton_lines = len(skeleton_content.splitlines())
            diff_lines = abs(src_lines - skeleton_lines)

            gaps.append({
                "type": "policy_divergence",
                "file": str(rel_path),
                "severity": "medium" if diff_lines > 10 else "low",
                "description": f"Policy {rel_path} differs between src/ and skeleton/ ({diff_lines} line diff)",
                "action": f"Review differences and sync if needed"
            })

    return gaps


def generate_report(gaps: List[Dict[str, Any]], output_path: Path, src_root: Path, skeleton_root: Path) -> None:
    """
    Generate SECURITY_GAPS.md markdown report.

    Args:
        gaps: List of gap dicts
        output_path: Path to write report
        src_root: Source directory
        skeleton_root: Skeleton directory
    """
    with open(output_path, 'w') as f:
        f.write("# Security Gaps Report\n\n")
        f.write(f"**Generated**: {datetime.now().isoformat()}\n")
        f.write(f"**Source**: {src_root}\n")
        f.write(f"**Skeleton**: {skeleton_root}\n\n")

        # Summary
        high_gaps = [g for g in gaps if g["severity"] == "high"]
        medium_gaps = [g for g in gaps if g["severity"] == "medium"]
        low_gaps = [g for g in gaps if g["severity"] == "low"]
        info_gaps = [g for g in gaps if g["severity"] == "info"]

        f.write("## Summary\n\n")
        f.write(f"**Total Gaps**: {len(gaps)}\n\n")
        f.write(f"- 🔴 **High Severity**: {len(high_gaps)} (missing policies)\n")
        f.write(f"- 🟡 **Medium Severity**: {len(medium_gaps)} (significant divergence)\n")
        f.write(f"- 🟢 **Low Severity**: {len(low_gaps)} (minor divergence)\n")
        f.write(f"- ℹ️ **Info**: {len(info_gaps)} (extra policies in skeleton)\n\n")

        # Details by severity
        if high_gaps:
            f.write("## 🔴 High Severity Gaps\n\n")
            for gap in high_gaps:
                f.write(f"### {gap['type']}: {gap['file']}\n\n")
                f.write(f"**Description**: {gap['description']}\n\n")
                f.write(f"**Action**: {gap['action']}\n\n")

        if medium_gaps:
            f.write("## 🟡 Medium Severity Gaps\n\n")
            for gap in medium_gaps:
                f.write(f"### {gap['type']}: {gap['file']}\n\n")
                f.write(f"**Description**: {gap['description']}\n\n")
                f.write(f"**Action**: {gap['action']}\n\n")

        if low_gaps:
            f.write("## 🟢 Low Severity Gaps\n\n")
            for gap in low_gaps:
                f.write(f"### {gap['type']}: {gap['file']}\n\n")
                f.write(f"**Description**: {gap['description']}\n\n")
                f.write(f"**Action**: {gap['action']}\n\n")

        if info_gaps:
            f.write("## ℹ️ Informational\n\n")
            for gap in info_gaps:
                f.write(f"### {gap['type']}: {gap['file']}\n\n")
                f.write(f"**Description**: {gap['description']}\n\n")
                f.write(f"**Action**: {gap['action']}\n\n")

        # Recommendations
        f.write("## Recommendations\n\n")
        if high_gaps:
            f.write("1. **Address High Severity gaps immediately** - Missing policies represent security coverage holes\n")
        if medium_gaps:
            f.write("2. **Review Medium Severity divergences** - Ensure skeleton maintains src/ security guarantees\n")
        if low_gaps:
            f.write("3. **Verify Low Severity differences** - Minor divergences may be intentional\n")

        f.write("\n---\n\n")
        f.write("**Note**: This report is auto-generated. Run `python tools/generate_security_gaps.py` to update.\n")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate security gaps report")
    parser.add_argument(
        "--src",
        type=Path,
        default=Path("src"),
        help="Source directory (default: src)"
    )
    parser.add_argument(
        "--skeleton",
        type=Path,
        default=Path("regex_refactor_docs/performance/skeleton"),
        help="Skeleton directory (default: regex_refactor_docs/performance/skeleton)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("regex_refactor_docs/performance/SECURITY_GAPS.md"),
        help="Output report path (default: regex_refactor_docs/performance/SECURITY_GAPS.md)"
    )
    args = parser.parse_args()

    # Validate directories
    if not args.src.exists():
        print(f"❌ Source directory not found: {args.src}", file=sys.stderr)
        return 1

    if not args.skeleton.exists():
        print(f"❌ Skeleton directory not found: {args.skeleton}", file=sys.stderr)
        return 1

    # Find policy files
    print(f"🔍 Scanning {args.src} for policy files...")
    src_policies = find_policy_files(args.src)
    print(f"   Found {len(src_policies)} policy files")

    print(f"🔍 Scanning {args.skeleton} for policy files...")
    skeleton_policies = find_policy_files(args.skeleton)
    print(f"   Found {len(skeleton_policies)} policy files")

    # Compare policies
    print("📊 Comparing policies...")
    gaps = compare_policies(src_policies, skeleton_policies, args.src, args.skeleton)

    # Generate report
    print(f"📝 Generating report: {args.output}")
    generate_report(gaps, args.output, args.src, args.skeleton)

    # Summary
    high_gaps = sum(1 for g in gaps if g["severity"] == "high")
    print(f"\n✅ Report generated successfully")
    print(f"   Total gaps: {len(gaps)}")
    print(f"   High severity: {high_gaps}")

    if high_gaps > 0:
        print(f"\n⚠️  {high_gaps} high-severity gaps detected")
        print(f"   Review {args.output} for details")

    return 0


if __name__ == "__main__":
    sys.exit(main())
