"""Evidence block creation utility.

Centralized evidence block creation with truly atomic append via portalocker.
"""
from pathlib import Path
import json
import sys
import hashlib
from datetime import datetime

# Requires: pip install portalocker
try:
    import portalocker
except ImportError:
    raise ImportError(
        "portalocker required for atomic evidence append. "
        "Install with: pip install portalocker"
    )


class SecurityError(RuntimeError):
    """Security validation failure."""
    pass


def create_evidence_block(
    evidence_id: str,
    phase: int,
    file: str,
    lines: str,
    description: str
) -> str:
    """Create evidence block with truly atomic append.

    Uses portalocker for cross-platform file locking with O_APPEND.
    Prevents race conditions in parallel CI jobs.

    Snippets truncated to 1000 chars after redaction to minimize
    secret leakage while preserving audit context.

    Args:
        evidence_id: Unique identifier
        phase: Phase number (0-6)
        file: Source file path
        lines: Line range (e.g., "450-475")
        description: Change description

    Returns:
        evidence_id on success

    Raises:
        SecurityError: On file read, write failure, or timeout
    """
    # Read source with explicit encoding
    file_path = Path(file)
    if not file_path.exists():
        raise SecurityError(f"Evidence file not found: {file}")

    content = file_path.read_text(encoding="utf-8")

    # Extract line range
    start, end = map(int, lines.split("-"))
    snippet_lines = content.split("\n")[start-1:end]
    snippet = "\n".join(snippet_lines)

    # Compute hash over FULL snippet (before redaction/truncation)
    sha256 = hashlib.sha256(snippet.encode("utf-8")).hexdigest()

    # Redact probable secrets before truncation
    snippet = _redact_secrets(snippet)

    # Truncate for storage (prevents secret leakage)
    # 1000 chars post-redaction captures context without exposing full tokens/keys
    truncated_snippet = snippet[:1000]

    # Create evidence block
    evidence = {
        "evidence_id": evidence_id,
        "phase": phase,
        "file": file,
        "lines": lines,
        "description": description,
        "code_snippet": truncated_snippet,
        "sha256": sha256,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # Truly atomic append with portalocker
    # - O_APPEND ensures atomic writes even from multiple processes
    # - LOCK_EX provides exclusive lock during write
    # - timeout=10 prevents indefinite hangs
    evidence_file = Path("evidence_blocks.jsonl")
    evidence_file.parent.mkdir(parents=True, exist_ok=True)

    with portalocker.Lock(
        evidence_file,
        mode="a",
        timeout=10,
        flags=portalocker.LOCK_EX
    ) as f:
        f.write(json.dumps(evidence, ensure_ascii=False) + "\n")

    return evidence_id


def _redact_secrets(snippet: str) -> str:
    """Remove probable secrets before truncation.

    Patterns:
    - Long base64-like strings (40+ chars)
    - token=, key=, secret=, password=, auth= patterns
    - API keys, tokens in common formats

    Preserves code structure while removing sensitive values.
    """
    import re

    # Remove long base64-like strings
    snippet = re.sub(r'[A-Za-z0-9+/]{40,}={0,2}', '<REDACTED_BASE64>', snippet)

    # Remove token/key/secret patterns
    snippet = re.sub(
        r'\b(token|key|secret|password|auth|api_key|api_secret)\s*[=:]\s*["\']?[\w\-_+/]{20,}["\']?',
        r'\1=<REDACTED>',
        snippet,
        flags=re.IGNORECASE
    )

    # Remove bearer tokens
    snippet = re.sub(r'Bearer\s+[\w\-_+/\.]{20,}', 'Bearer <REDACTED>', snippet, flags=re.IGNORECASE)

    return snippet


if __name__ == "__main__":
    # Read JSON from stdin
    try:
        block_data = json.load(sys.stdin)
        evidence_id = create_evidence_block(**block_data)
        print(json.dumps({"status": "OK", "evidence_id": evidence_id}))
        sys.exit(0)
    except SecurityError as e:
        print(json.dumps({"status": "FAIL", "reason": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "FAIL", "reason": f"Unexpected error: {e}"}), file=sys.stderr)
        sys.exit(1)
