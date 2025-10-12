#!/usr/bin/env python3
"""
tools/check_security_codes.py - CI helper
Fails if any raise SecurityError(code="...") uses a code not present in SecurityError.CODES
Usage: python tools/check_security_codes.py [repo_root]
"""
import sys, re, pathlib

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")

code_pattern = re.compile(r'raise\s+SecurityError\([^)]*code\s*=\s*([\'"])(?P<code>[^\'"]+)\1')
codes_map_pattern = re.compile(r'class\s+SecurityError.*?CODES\s*=\s*\{(.*?)\}', re.S)
code_key_pattern = re.compile(r'([\'"])(?P<key>[^\'"]+)\1\s*:\s*[\'"][A-Z]+[\'"]')

# 1) collect codes from enum SSOT
codes_seen = set()
for py in ROOT.rglob("*.py"):
    try:
        text = py.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    m = codes_map_pattern.search(text)
    if m:
        for km in code_key_pattern.finditer(m.group(1)):
            codes_seen.add(km.group("key"))

# 2) collect codes used at raise sites
codes_used = {}
for py in ROOT.rglob("*.py"):
    try:
        text = py.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for m in code_pattern.finditer(text):
        codes_used.setdefault(m.group("code"), []).append(str(py))

missing = sorted([c for c in codes_used if c not in codes_seen])
if missing:
    print("ERROR: Unknown SecurityError codes used:", ", ".join(missing))
    for c in missing:
        print("  - {}:".format(c))
        for loc in sorted(set(codes_used[c])):
            print("    * {}".format(loc))
    sys.exit(1)
else:
    print("OK: SecurityError codes synchronized.")
