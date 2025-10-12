"""
normalize_yaml_like_blocks.py
--------------------------------
Tiny normalizer to match legacy baseline formatting around **non-front-matter**
YAML-looking blocks that are fenced with '---' / '...'.

Rules (applied after STRICT BOF front-matter stripping):
- Only consider blocks that start with a line exactly '---' and have a closing
  line exactly '---' or '...'
- Only if the opening fence is **not** at BOF (i.e., this is *not* top front-matter)
- Heuristic: treat as "YAML-like" if at least one payload line contains a colon ":"
- Normalization:
  (a) Ensure there is exactly ONE blank line **before** the closing fence,
      i.e., between payload and closing fence
  (b) Ensure there is exactly ONE blank line **after** the closing fence
      (if the next line is non-blank), compressing multiple blank lines to one
- Do not alter content inside payload, only blank-line boundaries
- Avoid modifying code fences: best-effort by skipping when fenced block
  payload contains common code fence markers like "```" or "~~~"

This is a formatting shim to preserve legacy JSON baselines; prefer disabling it
if you adopt the simpler fail-closed approach.
"""

from __future__ import annotations

import re
from typing import List

__all__ = ["strip_front_matter_strict", "normalize_yaml_like_blocks", "prepare_content_raw"]

_FENCE_OPEN = re.compile(r"^---\s*$")
_FENCE_CLOSE = re.compile(r"^(?:---|\.\.\.)\s*$")

def _normalize_newlines(s: str) -> str:
    if s and s[:1] == "\\ufeff":
        s = s[1:]
    return s.replace("\\r\\n", "\\n").replace("\\r", "\\n")

def strip_front_matter_strict(md: str) -> str:
    """
    Remove BOF front-matter only if the very first line is exactly '---'
    and the first matching closing line is exactly '---' or '...'. No trailing
    spaces/tabs allowed on fence lines.
    """
    s = _normalize_newlines(md)
    if s.startswith("\\ufeff"):
        s = s[1:]
    if not s.startswith("---\\n"):
        return s

    # find closing fence
    pos = 4  # after '---\\n'
    end = None
    while True:
        nxt = s.find("\\n", pos)
        if nxt == -1:
            break
        line = s[pos:nxt+1]
        if line in ("---\\n", "...\\n"):
            end = nxt + 1
            break
        pos = nxt + 1
    return s[end:] if end is not None else s

def normalize_yaml_like_blocks(md_after_bof_strip: str) -> str:
    """
    Apply boundary-blank-line normalization to YAML-like fenced blocks that are
    *not* BOF front-matter.
    """
    lines: List[str] = _normalize_newlines(md_after_bof_strip).split("\\n")
    out: List[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        # Detect opening fence (not at BOF: i > 0)
        if i > 0 and _FENCE_OPEN.match(line):
            # scan for closing fence
            j = i + 1
            has_colon = False
            looks_like_code = False
            while j < n and not _FENCE_CLOSE.match(lines[j]):
                if ":" in lines[j]:
                    has_colon = True
                if "```" in lines[j] or "~~~" in lines[j]:
                    looks_like_code = True
                j += 1
            if j < n and _FENCE_CLOSE.match(lines[j]) and has_colon and not looks_like_code:
                # We have a YAML-like block [i .. j]
                # Payload is lines[i+1:j]
                # (a) ensure exactly one blank line before closing fence
                payload = lines[i+1:j]
                # Remove trailing blank lines in payload
                while payload and payload[-1] == "":
                    payload.pop()
                # Insert exactly one blank line
                payload.append("")
                # (b) after the closing fence, ensure exactly one blank if the next is non-blank
                # We'll emit: open, payload..., close, postblank?, then continue
                out.append(lines[i])  # opening '---'
                out.extend(payload)
                out.append(lines[j])  # closing

                # Determine next line after closing
                k = j + 1
                # collapse any number of blanks to at most one
                blanks = 0
                while k < n and lines[k] == "":
                    blanks += 1
                    k += 1
                # if next is non-blank, we enforce a single blank line
                if k < n and lines[k] != "":
                    out.append("")

                # advance i to k (we consumed through j and skipped over blank run)
                i = j + 1
                # drop extra blanks we already normalized
                while i < n and lines[i] == "":
                    i += 1
                continue
            # Not a valid YAML-like block; fall through

        out.append(line)
        i += 1

    return "\\n".join(out)

def prepare_content_raw(md_text: str, enable_yaml_block_normalization: bool = True) -> str:
    """
    High-level helper:
      1) strict BOF front-matter strip
      2) optional YAML-like block normalization (for compatibility)
    """
    s = strip_front_matter_strict(md_text)
    if enable_yaml_block_normalization:
        s = normalize_yaml_like_blocks(s)
    return s

if __name__ == "__main__":
    import sys, argparse, io

    ap = argparse.ArgumentParser(description="Normalize YAML-like blocks for legacy baseline parity.")
    ap.add_argument("file", help="Markdown file to normalize (reads from stdin if '-')")
    ap.add_argument("--no-yaml-normalize", action="store_true", help="Disable YAML-like block normalization")
    args = ap.parse_args()

    data = sys.stdin.read() if args.file == "-" else io.open(args.file, "r", encoding="utf-8").read()
    out = prepare_content_raw(data, enable_yaml_block_normalization=not args.no_yaml_normalize)
    sys.stdout.write(out)
