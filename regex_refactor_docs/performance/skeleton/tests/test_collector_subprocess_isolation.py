"""
Test subprocess-based collector isolation.

Validates that the cross-platform subprocess harness correctly enforces
timeouts and isolates collector failures.
"""
import pytest
import sys
import json
import time
from pathlib import Path
from types import SimpleNamespace


def test_subprocess_timeout_enforcement():
    """
    Test that subprocess harness kills slow collectors.

    This works on all platforms including Windows (unlike SIGALRM).
    """
    # Import subprocess runner
    tools_dir = Path(__file__).parent.parent.parent / "tools"
    sys.path.insert(0, str(tools_dir))

    try:
        from collector_worker import run_collector_subprocess
    except ImportError:
        pytest.skip("collector_worker module not available")

    # Create a simple slow collector for testing
    slow_collector_code = '''
from types import SimpleNamespace
import time

class SlowCollector:
    name = "slow"

    @property
    def interest(self):
        class I:
            types = {"inline"}
            tags = set()
            ignore_inside = set()
            predicate = None
        return I()

    def should_process(self, token, ctx, wh_local):
        return True

    def on_token(self, idx, token, ctx, wh_local):
        # Sleep for 10 seconds - should be killed
        time.sleep(10)

    def finalize(self, wh_local):
        return {"processed": 0}
'''

    # Write temporary collector module
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Write collector module
        collector_file = tmpdir / "slow_collector.py"
        collector_file.write_text(slow_collector_code)

        # Write tokens JSON
        tokens = [
            {
                "type": "inline",
                "nesting": 0,
                "tag": "",
                "map": None,
                "info": None,
                "content": "test"
            }
        ]
        tokens_file = tmpdir / "tokens.json"
        tokens_file.write_text(json.dumps(tokens))

        # Add tmpdir to sys.path
        sys.path.insert(0, str(tmpdir))

        try:
            # Run with 1 second timeout
            start = time.time()
            result = run_collector_subprocess(
                collector_spec="slow_collector:SlowCollector",
                tokens_path=tokens_file,
                timeout_seconds=1,
                max_memory_mb=100
            )
            duration = time.time() - start

            # Verify timeout was enforced
            assert not result["success"], "Expected timeout failure"
            assert result["exit_code"] == 2, f"Expected exit code 2 (timeout), got {result['exit_code']}"
            assert duration < 3, f"Timeout not enforced - took {duration}s (expected ~1s)"
            assert "timeout" in result["error"].lower(), f"Expected timeout error, got: {result['error']}"

        finally:
            sys.path.remove(str(tmpdir))


def test_subprocess_fast_collector_succeeds():
    """
    Test that fast collectors complete successfully.
    """
    # Import subprocess runner
    tools_dir = Path(__file__).parent.parent.parent / "tools"
    sys.path.insert(0, str(tools_dir))

    try:
        from collector_worker import run_collector_subprocess
    except ImportError:
        pytest.skip("collector_worker module not available")

    # Create a simple fast collector
    fast_collector_code = '''
class FastCollector:
    name = "fast"
    processed_count = 0

    @property
    def interest(self):
        class I:
            types = {"inline"}
            tags = set()
            ignore_inside = set()
            predicate = None
        return I()

    def should_process(self, token, ctx, wh_local):
        return True

    def on_token(self, idx, token, ctx, wh_local):
        FastCollector.processed_count += 1

    def finalize(self, wh_local):
        return {"processed": FastCollector.processed_count}
'''

    # Write temporary collector module
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Write collector module
        collector_file = tmpdir / "fast_collector.py"
        collector_file.write_text(fast_collector_code)

        # Write tokens JSON
        tokens = [
            {
                "type": "inline",
                "nesting": 0,
                "tag": "",
                "map": None,
                "info": None,
                "content": "test"
            }
        ]
        tokens_file = tmpdir / "tokens.json"
        tokens_file.write_text(json.dumps(tokens))

        # Add tmpdir to sys.path
        sys.path.insert(0, str(tmpdir))

        try:
            # Run with 5 second timeout (plenty of time)
            result = run_collector_subprocess(
                collector_spec="fast_collector:FastCollector",
                tokens_path=tokens_file,
                timeout_seconds=5,
                max_memory_mb=100
            )

            # Verify success
            assert result["success"], f"Expected success, got error: {result.get('error')}"
            assert result["exit_code"] == 0, f"Expected exit code 0, got {result['exit_code']}"
            assert "duration_ms" in result, "Missing duration metric"
            assert result["duration_ms"] < 5000, f"Took too long: {result['duration_ms']}ms"

        finally:
            sys.path.remove(str(tmpdir))


def test_subprocess_isolation_prevents_crash():
    """
    Test that collector crashes are isolated and don't affect main process.
    """
    # Import subprocess runner
    tools_dir = Path(__file__).parent.parent.parent / "tools"
    sys.path.insert(0, str(tools_dir))

    try:
        from collector_worker import run_collector_subprocess
    except ImportError:
        pytest.skip("collector_worker module not available")

    # Create a collector that crashes
    crash_collector_code = '''
class CrashCollector:
    name = "crash"

    @property
    def interest(self):
        class I:
            types = {"inline"}
            tags = set()
            ignore_inside = set()
            predicate = None
        return I()

    def should_process(self, token, ctx, wh_local):
        return True

    def on_token(self, idx, token, ctx, wh_local):
        raise RuntimeError("Intentional crash for testing")

    def finalize(self, wh_local):
        return {}
'''

    # Write temporary collector module
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Write collector module
        collector_file = tmpdir / "crash_collector.py"
        collector_file.write_text(crash_collector_code)

        # Write tokens JSON
        tokens = [
            {
                "type": "inline",
                "nesting": 0,
                "tag": "",
                "map": None,
                "info": None,
                "content": "test"
            }
        ]
        tokens_file = tmpdir / "tokens.json"
        tokens_file.write_text(json.dumps(tokens))

        # Add tmpdir to sys.path
        sys.path.insert(0, str(tmpdir))

        try:
            # Run collector - should catch crash
            result = run_collector_subprocess(
                collector_spec="crash_collector:CrashCollector",
                tokens_path=tokens_file,
                timeout_seconds=5,
                max_memory_mb=100
            )

            # Verify crash was isolated
            assert not result["success"], "Expected failure due to crash"
            assert result["exit_code"] == 1, f"Expected exit code 1 (collector error), got {result['exit_code']}"
            assert "error" in result, "Expected error message"

            # Main process should still be alive (if we got here, it is!)
            assert True, "Main process survived collector crash"

        finally:
            sys.path.remove(str(tmpdir))
