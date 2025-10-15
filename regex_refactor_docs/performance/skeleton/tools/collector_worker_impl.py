#!/usr/bin/env python3
"""
Collector worker implementation - runs in isolated subprocess.

This script is invoked by collector_worker.py and should not be called directly.

Exit Codes:
    0 - Success
    1 - Collector error (exception raised)
    3 - Memory limit exceeded
    4 - Invalid arguments or setup error
"""
from __future__ import annotations
import sys
import json
import argparse
import traceback
import resource
from pathlib import Path
from typing import Any, Dict, List


def set_memory_limit(max_memory_mb: int) -> None:
    """
    Set memory limit for this process (Unix only).

    On Windows, this is a no-op (graceful degradation).
    """
    if not hasattr(resource, 'RLIMIT_AS'):
        # Windows or unsupported platform
        return

    try:
        max_bytes = max_memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
    except Exception:
        # Graceful degradation if setrlimit fails
        pass


def load_collector_class(collector_spec: str):
    """
    Load collector class from module:class specification.

    Args:
        collector_spec: "module.path:ClassName"

    Returns:
        Collector class

    Raises:
        ImportError: If module or class not found
    """
    if ":" not in collector_spec:
        raise ValueError(f"Invalid collector spec (expected 'module:Class'): {collector_spec}")

    module_path, class_name = collector_spec.rsplit(":", 1)

    # Import module
    import importlib
    module = importlib.import_module(module_path)

    # Get class
    collector_class = getattr(module, class_name)

    return collector_class


def load_tokens(tokens_path: Path) -> List[Any]:
    """
    Load serialized tokens from JSON file.

    Args:
        tokens_path: Path to JSON file

    Returns:
        List of token objects (as dicts or SimpleNamespace)
    """
    with open(tokens_path, "r", encoding="utf-8") as f:
        tokens_data = json.load(f)

    # Convert dicts to SimpleNamespace for attribute access
    from types import SimpleNamespace

    tokens = []
    for tok_dict in tokens_data:
        if isinstance(tok_dict, dict):
            tokens.append(SimpleNamespace(**tok_dict))
        else:
            tokens.append(tok_dict)

    return tokens


def run_collector(
    collector_class,
    tokens: List[Any],
    max_memory_mb: int
) -> Dict[str, Any]:
    """
    Run collector on tokens and return finalized results.

    Args:
        collector_class: Collector class to instantiate
        tokens: List of token objects
        max_memory_mb: Memory limit (for monitoring)

    Returns:
        Collector finalization output
    """
    # Set memory limit
    set_memory_limit(max_memory_mb)

    # Import TokenWarehouse
    try:
        from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    except ImportError:
        # Fall back to relative import for skeleton
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
        TokenWarehouse = wh_mod.TokenWarehouse

    # Create warehouse
    wh = TokenWarehouse(tokens, tree=None)

    # Instantiate collector
    collector = collector_class()

    # Register collector
    try:
        wh.register_collector(collector)
    except Exception:
        # Fall back to direct append
        wh._collectors.append(collector)

    # Dispatch
    wh.dispatch_all()

    # Finalize
    result = collector.finalize(wh)

    # Check for collector errors
    if wh._collector_errors:
        errors = [
            {"collector": name, "token_idx": idx, "error_type": err_type}
            for name, idx, err_type in wh._collector_errors
        ]
        return {
            "success": False,
            "errors": errors,
            "partial_result": result
        }

    return {
        "success": True,
        "result": result
    }


def main():
    """Worker process entry point."""
    parser = argparse.ArgumentParser(
        description="Collector worker subprocess (internal use only)"
    )
    parser.add_argument("--collector", required=True)
    parser.add_argument("--tokens", type=Path, required=True)
    parser.add_argument("--max-memory-mb", type=int, required=True)
    parser.add_argument("--output", type=Path)

    args = parser.parse_args()

    try:
        # Load collector class
        collector_class = load_collector_class(args.collector)

        # Load tokens
        tokens = load_tokens(args.tokens)

        # Run collector
        result = run_collector(
            collector_class=collector_class,
            tokens=tokens,
            max_memory_mb=args.max_memory_mb
        )

        # Write output
        output_json = json.dumps(result, indent=2)

        if args.output:
            args.output.write_text(output_json, encoding="utf-8")

        # Print to stdout (for parent process)
        print(output_json)

        # Exit success
        return 0

    except MemoryError:
        error_msg = f"Collector exceeded {args.max_memory_mb}MB memory limit"
        result = {"success": False, "error": error_msg}
        print(json.dumps(result), file=sys.stderr)
        return 3

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        traceback_str = traceback.format_exc()
        result = {
            "success": False,
            "error": error_msg,
            "traceback": traceback_str
        }
        print(json.dumps(result), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
