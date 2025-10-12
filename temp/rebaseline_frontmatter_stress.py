"""
rebaseline_frontmatter_stress.py
--------------------------------
Mode (2) helper: rewrite baseline JSONs for the front-matter stress suite
to the **strict** interpretation (no mid-file YAML normalization).

- Finds "test_mds" and "baseline_outputs" under a given root
- For each pair key, recomputes:
    content.raw   := strip_front_matter_strict(md)
    content.lines := content.raw.split("\\n")
- Writes updated JSON in place (backups optional)

Usage:
  python rebaseline_frontmatter_stress.py --root /path/to/archive_or_repo
"""

from __future__ import annotations

import json
from pathlib import Path
import argparse

def _normalize_newlines(s: str) -> str:
    if s and s[:1] == "\\ufeff":
        s = s[1:]
    return s.replace("\\r\\n","\\n").replace("\\r","\\n")

def strip_front_matter_strict(s: str) -> str:
    s = _normalize_newlines(s)
    if s.startswith("\\ufeff"):
        s = s[1:]
    if not s.startswith("---\\n"):
        return s
    pos = 4
    end = None
    while True:
        nxt = s.find("\\n", pos)
        if nxt == -1:
            break
        line = s[pos:nxt+1]
        if line in ("---\\n", "...\\n"):
            end = nxt+1
            break
        pos = nxt+1
    return s[end:] if end is not None else s

def main(root: Path, dry_run: bool, backup: bool):
    test_dir = next(root.rglob("test_mds"))
    base_dir = next(root.rglob("baseline_outputs"))

    # Build maps
    md_map = {str(p.relative_to(test_dir).with_suffix("")).replace("\\\\","/"): p
              for p in test_dir.rglob("*.md")}
    js_map = {}
    for p in base_dir.rglob("*.json"):
        key = str(p.relative_to(base_dir).with_suffix("")).replace("\\\\","/")
        if key.endswith(".baseline"):
            key = key[:-len(".baseline")]
        js_map[key] = p

    updated = 0
    touched = []
    for key, mdp in md_map.items():
        if key not in js_map:
            continue
        jsp = js_map[key]
        md = mdp.read_text(encoding="utf-8")
        raw = strip_front_matter_strict(md)
        lines = raw.split("\\n")

        obj = json.loads(jsp.read_text(encoding="utf-8"))
        changed = (obj.get("content",{}).get("raw") != raw or obj.get("content",{}).get("lines") != lines)
        if changed:
            if not dry_run:
                if backup:
                    bak = jsp.with_suffix(jsp.suffix + ".bak")
                    bak.write_text(jsp.read_text(encoding="utf-8"), encoding="utf-8")
                obj.setdefault("content", {})["raw"] = raw
                obj["content"]["lines"] = lines
                jsp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
            updated += 1
            touched.append(str(jsp))

    print(f"Pairs: {len(md_map)}  Updated: {updated}")
    if touched:
        print("Examples:")
        for p in touched[:10]:
            print(" -", p)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=".", help="Root folder that contains test_mds and baseline_outputs")
    ap.add_argument("--dry-run", action="store_true", help="Compute changes but do not write")
    ap.add_argument("--backup", action="store_true", help="Write .bak files before updating")
    args = ap.parse_args()
    main(Path(args.root), dry_run=args.dry_run, backup=args.backup)
