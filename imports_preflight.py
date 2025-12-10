#!/usr/bin/env python3
"""
imports_preflight.py — diagnostic for Python import setup,
customized for the 'doxstrux' package.
"""

from __future__ import annotations
import sys, os, subprocess
from pathlib import Path
from typing import List, Tuple
import importlib

OK = "✅"
WARN = "⚠️"
ERR = "❌"

def header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def try_import(name: str) -> Tuple[bool, str]:
    try:
        mod = importlib.import_module(name)
        return True, getattr(mod, "__file__", "builtin")
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def run_module(module: str) -> Tuple[bool, str]:
    """Try running `python -m module` as a dry run (syntax check only)."""
    try:
        subprocess.run(
            [sys.executable, "-m", module, "--help"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=5, check=False,
        )
        return True, "Executed with -m (no ImportError)."
    except subprocess.CalledProcessError as e:
        return False, f"Return code {e.returncode}: {e.stderr.decode(errors='ignore')[:120]}"
    except Exception as e:
        return False, str(e)

def find_repo_root(start: Path) -> Path:
    for parent in [start] + list(start.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return start

def main() -> int:
    cwd = Path.cwd()
    repo_root = find_repo_root(cwd)
    print(f"🧭 Working directory: {cwd}")
    print(f"Detected repo root:   {repo_root}")

    header("1. Environment summary")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Executable: {sys.executable}")
    print(f"Virtualenv active: {'yes' if 'VIRTUAL_ENV' in os.environ else 'no'}")

    header("2. sys.path top entries")
    for i, p in enumerate(sys.path[:6]):
        print(f"  {i}: {p}")

    header("3. docpipe import tests")
    modules = [
        "docpipe",
        "docpipe.markdown_parser_core",
        "docpipe.json_utils",
    ]
    for m in modules:
        ok, info = try_import(m)
        if ok:
            print(f"{OK} import {m:45s} -> {info}")
        else:
            print(f"{ERR} import {m:45s} failed -> {info}")

    header("4. -m execution checks (dry run)")
    targets = [
        "docpipe",
        "docpipe.markdown_parser_core.test_package",
    ]
    for t in targets:
        ok, info = run_module(t)
        if ok:
            print(f"{OK} python -m {t} succeeded ({info})")
        else:
            print(f"{ERR} python -m {t} failed ({info})")

    header("5. Installation status")
    import site
    site_dirs: List[str] = site.getsitepackages() if hasattr(site, "getsitepackages") else []
    print("Site-packages directories:")
    for d in site_dirs:
        print(f"  - {d}")
    found = None
    for d in site_dirs + sys.path:
        candidate = Path(d) / "docpipe"
        if candidate.exists():
            found = candidate
            break
    if found:
        print(f"{OK} 'docpipe' package detected at: {found}")
    else:
        print(f"{WARN} 'docpipe' not found in site-packages — probably needs 'uv pip install -e .'")

    header("6. Quick guidance")
    print("""
- If any imports fail, check that you installed your package in editable mode:
    uv pip install -e .
- Always run inside the project root, not src/.
- Use absolute imports inside code, and 'python -m docpipe...' to execute.
- Keep __init__.py in each subpackage (but not in src/).
""")

    print("\n✅ Done.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
