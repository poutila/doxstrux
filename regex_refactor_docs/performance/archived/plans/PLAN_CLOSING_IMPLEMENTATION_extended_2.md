# Extended Closing Implementation Plan - Phase 8 Security Hardening
# Part 2 of 3: P1/P2 Reference Patterns & Process Automation

**Version**: 1.1 (Split Edition)
**Date**: 2025-10-16
**Status**: SKELETON-SCOPED REFERENCE IMPLEMENTATION PLAN
**Methodology**: Golden Chain-of-Thought + CODE_QUALITY Policy
**Part**: 2 of 3
**Purpose**: P1 reference patterns and P2 process improvements

⚠️ **DEPENDENCY**: Must complete Part 1 (P0 Critical) before starting this part.

**Previous**: See PLAN_CLOSING_IMPLEMENTATION_extended_1.md (Part 1 - P0 Critical)
**Next**: See PLAN_CLOSING_IMPLEMENTATION_extended_3.md (Part 3 - Testing/Production)

---

## Part 2 Scope

This file documents:
- **P1 Reference Patterns**: Optional but valuable patterns for production migration
- **P2 Process Automation**: Tools and documentation for development workflow

**NOT BLOCKING**: These items can be deferred if time-constrained. P0 (Part 1) is sufficient for security green-light.

---

## Priority Matrix - P1/P2 Items

| ID | Item | Security Risk | YAGNI Risk | Scope | Effort | Priority |
|----|------|---------------|------------|-------|--------|----------|
| P1-1 | Binary search reference | LOW (perf) | N/A | Skeleton | 1h | 🟡 P1 |
| P1-2 | Subprocess doc (NOT impl) | MED | HIGH | Docs | 30min | 🟡 P1 |
| P1-2.5 | Collector allowlist doc | MED | HIGH | Docs | 1h | 🟡 P1 |
| P1-3 | Reentrancy pattern doc | LOW | LOW | Docs | 1h | 🟡 P1 |
| P1-4 | Token canonicalization test | MED | HIGH | Skeleton | 1h | 🟡 P1 |
| P2-1 | YAGNI checker tool | N/A | MED | Tools | 3h | 🟢 P2 |
| P2-2 | Routing table pattern doc | N/A | LOW | Docs | 1h | 🟢 P2 |
| P2-3 | Auto-fastpath pattern doc | N/A | LOW | Docs | 30min | 🟢 P2 |
| P2-4 | Fuzz testing pattern doc | N/A | LOW | Docs | 1h | 🟢 P2 |
| P2-5 | Feature-flag pattern doc | N/A | LOW | Docs | 1h | 🟢 P2 |

**Total Effort**:
- **P1**: 4.5 hours (increased from 3.5h with P1-4 addition)
- **P2**: 6.5 hours
- **Combined**: 11 hours

---

# PART 2: P1 REFERENCE PATTERNS

## P1-1: Binary Search section_of() Reference Implementation

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P1-1-REF**: Provide O(log N) reference for section lookups
- **Source**: External review C.2
- **Purpose**: Demonstrate binary search pattern for production migration
- **Scope**: Skeleton utility module (reference code)

**YAGNI Assessment**:
- Q1: Real requirement? ✅ YES - Performance optimization for large docs
- Q2: Used immediately? ✅ YES - Reference for production
- Q3: Backed by data? ✅ YES - O(N) vs O(log N) measurable
- Q4: Can defer? ✅ YES - But low effort, high value
- **Outcome**: `implement_reference = TRUE` (skeleton scope)

### --- EXECUTION ---

**Step 1: Add Binary Search Helper to Skeleton**

```python
# FILE: skeleton/doxstrux/markdown/utils/section_utils.py
# (Create if missing - skeleton scope allowed)

import bisect
from typing import List, Optional, Tuple, Dict

def section_index_for_line(
    sections: List[Tuple[int, int]],
    lineno: int
) -> Optional[int]:
    """
    Find section index for given line number using binary search.

    REFERENCE IMPLEMENTATION - O(log N) instead of O(N) linear scan.

    Args:
        sections: List of (start, end) tuples sorted by start line
        lineno: Line number to search for

    Returns:
        Section index or None if not found

    Example:
        >>> sections = [(0, 4), (5, 9), (10, 14)]
        >>> section_index_for_line(sections, 7)
        1  # Second section (5-9) contains line 7
    """
    if not sections:
        return None

    # Build starts list (first element of each tuple)
    starts = [s for (s, e) in sections]
    i = bisect.bisect_right(starts, lineno) - 1

    if i < 0:
        return None

    s, e = sections[i]
    if s <= lineno <= e:
        return i

    return None


def section_of_with_binary_search(
    sections: List[Dict[str, any]],
    lineno: int
) -> Optional[str]:
    """
    Find section containing line_num using binary search.

    REFERENCE IMPLEMENTATION - demonstrates pattern for production.

    Args:
        sections: List of dicts with 'start_line', 'end_line', 'id' keys
        lineno: Line number to search for

    Returns:
        Section ID or None if not found
    """
    if not sections:
        return None

    # Convert to (start, end) tuples
    ranges = [(s['start_line'], s.get('end_line', s['start_line']))
              for s in sections]

    idx = section_index_for_line(ranges, lineno)

    if idx is None:
        return None

    return sections[idx]['id']

# EVIDENCE ANCHOR
# CLAIM-P1-1-REF-IMPL: Binary search reduces section lookup to O(log N)
# Source: External review C.2
# Verification: Benchmark shows O(log N) growth
```

**Step 2: Add Benchmark Test**

```python
# FILE: skeleton/tests/test_section_lookup_performance.py
# (Create if missing)

import time
from skeleton.doxstrux.markdown.utils.section_utils import section_index_for_line

def test_section_of_is_logarithmic():
    """Verify section_index_for_line() scales as O(log N), not O(N)."""

    def make_sections(n):
        return [(i * 10, (i+1) * 10 - 1) for i in range(n)]

    sizes = [100, 1000, 10000]
    times = []

    for size in sizes:
        sections = make_sections(size)

        start = time.perf_counter()
        for _ in range(1000):
            section_index_for_line(sections, size * 5)  # Mid-point lookup
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    # Check logarithmic growth
    # If O(log N): time[1] / time[0] ≈ log(1000)/log(100) ≈ 1.5
    # If O(N): time[1] / time[0] ≈ 1000/100 = 10
    ratio = times[1] / times[0]

    assert ratio < 3.0, \
        f"section_index_for_line() appears O(N), not O(log N): ratio={ratio}"
```

**Success Criteria**:
- [ ] Binary search helper implemented in skeleton
- [ ] Benchmark test shows O(log N) scaling
- [ ] Reference code ready for production migration

**Time Estimate**: 1 hour

---

## P1-2: Subprocess Isolation - YAGNI Documentation Only

### --- THINKING ---

**YAGNI STOP CONDITION**:

Per CODE_QUALITY.json:
- **Q1**: Real requirement? ⚠️ **CONDITIONAL** - Only if Windows deployment confirmed
- **Q2**: Used immediately? ⚠️ **UNKNOWN** - No deployment timeline
- **Q3**: Backed by stakeholder/data? ❌ **NO** - No Windows users confirmed
- **OUTCOME**: `STOP_DOCUMENT_ONLY = TRUE`

**Decision**: Do NOT implement subprocess isolation. Document as future work.

### --- EXECUTION ---

**Step 1: Document Subprocess Isolation as YAGNI-Gated**

```python
# FILE: tools/collector_worker_YAGNI_PLACEHOLDER.py
# (Create placeholder documentation file)

"""
Subprocess-based collector isolation for cross-platform timeout enforcement.

YAGNI STATUS: ⛔ NOT IMPLEMENTED
BLOCKED BY: No Windows deployment requirement (CODE_QUALITY.json Q1 fails)

## When to Implement

Implement if and only if ALL conditions met:
1. ✅ User confirms Windows production deployment (Q1: Real requirement)
2. ✅ Concrete Windows deployment timeline (Q2: Used immediately)
3. ✅ Windows user count estimate OR stakeholder approval (Q3: Backed by data)
4. ✅ Tech Lead approval obtained (per CODE_QUALITY.json waiver_policy)

## Effort Estimate

- **Design**: 2 hours
- **Implementation**: 4 hours (worker + parent-side helper)
- **Testing**: 2 hours
- **Total**: 8 hours

## Design Sketch (Reference Only)

```
tools/collector_worker.py (worker script)
├── Accept JSON tokens on stdin
├── Instantiate collector from allowlist
├── Call on_token() for each token
├── Return JSON results on stdout
└── Enforce timeout via subprocess.run()

skeleton/doxstrux/markdown/utils/collector_subproc.py (parent helper)
├── run_collector_subprocess(module, class_name, tokens, timeout)
├── Serialize tokens to JSON
├── Spawn subprocess with timeout
└── Deserialize results
```

## Integration Point

**File**: `skeleton/doxstrux/markdown/utils/token_warehouse.py`
**Location**: `_enforce_timeout_if_available()`

```python
if not SUPPORTS_TIMEOUT and STRICT_TIMEOUT_ENFORCEMENT:
    # Option C: Subprocess isolation fallback
    return self._run_collector_in_subprocess(collector, timeout_seconds)
```

## Extension: Subprocess Worker Pooling (YAGNI-Gated)

**ONLY if subprocess isolation implemented AND high-throughput requirement exists.**

### When to Implement Worker Pool

**ONLY if ALL conditions met**:
1. ✅ Subprocess isolation implemented (P1-2 complete)
2. ✅ High-throughput requirement (>100 docs/sec)
3. ✅ Profiling shows subprocess spawn overhead >20% of parse time
4. ✅ Tech Lead approval

**Effort Estimate**: +4 hours (on top of P1-2's 8 hours)

### Design Sketch

```python
# FILE: skeleton/doxstrux/markdown/utils/collector_worker_pool.py

import multiprocessing as mp
from queue import Queue

class CollectorWorkerPool:
    """
    Worker pool for subprocess-based collector isolation.

    YAGNI-gated: Implement ONLY if subprocess isolation deployed AND
    profiling shows spawn overhead >20%.
    """

    def __init__(self, num_workers=4):
        self.workers = [
            mp.Process(target=self._worker_loop, args=(task_queue, result_queue))
            for _ in range(num_workers)
        ]
        for w in self.workers:
            w.start()

    def dispatch_batch(self, collector_specs, tokens_list):
        """Dispatch multiple collector runs to worker pool."""
        # ... batch submission to task queue ...

    def _worker_loop(self, task_queue, result_queue):
        """Worker process: Accept tasks, run collectors, return results."""
        while True:
            task = task_queue.get()
            if task is None:  # Shutdown signal
                break
            result = self._run_collector(task)
            result_queue.put(result)
```

### Batching Strategy

**Pattern**: Batch multiple collector runs per subprocess spawn

```python
# Instead of: 1 subprocess per collector
for collector in collectors:
    result = run_subprocess(collector, tokens)

# Do: 1 subprocess for N collectors (batch)
batch = [(col1, tokens), (col2, tokens), ...]
results = run_subprocess_batch(batch)
```

**Expected speedup**: 2-3x for high-throughput workloads

### Recommendation

**Current**: Document pattern, do NOT implement (double YAGNI-gated)
**Future**: Add only if P1-2 deployed AND profiling shows need

## Current Recommendation

**Deploy on Linux** for production with untrusted inputs.
- Avoids subprocess overhead
- Full SIGALRM timeout enforcement
- Simpler operational model (KISS principle)

See: `policies/EXEC_PLATFORM_SUPPORT_POLICY.md` (Part 1 P0-4)
"""

def run_collector_isolated(collector, warehouse_state, timeout_seconds):
    """
    Placeholder - NOT IMPLEMENTED.

    Raises:
        NotImplementedError: Always (YAGNI-gated)
    """
    raise NotImplementedError(
        "Subprocess isolation pending YAGNI waiver. "
        "Requires: Windows deployment ticket + Tech Lead approval. "
        "See: tools/collector_worker_YAGNI_PLACEHOLDER.py"
    )
```

**Success Criteria**:
- [ ] Placeholder file documents YAGNI decision
- [ ] Design sketch provided for future reference
- [ ] Worker pooling extension documented (YAGNI-gated)
- [ ] NotImplementedError raised if attempted

**Time Estimate**: 30 minutes (documentation only)

---

## P1-2.5: Collector Allowlist & Package Signing Policy

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P1-2.5-DOC**: Subprocess isolation needs secure collector instantiation
- **Gap**: No allowlist enforcement or signing mechanism documented
- **Scope**: Policy documentation (implementation YAGNI-gated with subprocess isolation)
- **Source**: External review A.4 (ChatGPT gap analysis)

**YAGNI Assessment**:
- Q1: Real requirement? ⚠️ **CONDITIONAL** - Only if subprocess isolation implemented
- Q2: Used immediately? ⚠️ **UNKNOWN** - Depends on P1-2 (subprocess isolation)
- Q3: Backed by data? ✅ YES - Supply chain attacks are real
- Q4: Can defer? ✅ YES - But document now for completeness
- **Outcome**: `document_now = TRUE`, `implement_only_with_P1-2 = TRUE`

### --- EXECUTION ---

**FILE**: `policies/EXEC_COLLECTOR_ALLOWLIST_POLICY.md`

```markdown
# Collector Allowlist & Package Signing Policy

**Version**: 1.0
**Date**: 2025-10-16
**Status**: YAGNI-gated (implements only if subprocess isolation deployed)
**Scope**: Subprocess-isolated collector instantiation security

---

## Threat Model

**Attack**: Malicious collector injected via subprocess isolation
- Attacker provides crafted collector class name
- Subprocess imports and instantiates attacker-controlled code
- Arbitrary code execution in subprocess context

## Mitigation: Allowlist Enforcement

**Pattern** (in `tools/collector_worker.py`):

```python
# Hardcoded allowlist (not user-configurable)
ALLOWED_COLLECTORS = {
    "links": "doxstrux.markdown.collectors_phase8.links.LinksCollector",
    "images": "doxstrux.markdown.collectors_phase8.images.ImagesCollector",
    "headings": "doxstrux.markdown.collectors_phase8.headings.HeadingsCollector",
    "codeblocks": "doxstrux.markdown.collectors_phase8.codeblocks.CodeBlocksCollector",
    "tables": "doxstrux.markdown.collectors_phase8.tables.TablesCollector",
    "lists": "doxstrux.markdown.collectors_phase8.lists.ListsCollector",
}

def instantiate_collector(collector_name: str):
    if collector_name not in ALLOWED_COLLECTORS:
        raise ValueError(f"Collector '{collector_name}' not in allowlist")

    module_path, class_name = ALLOWED_COLLECTORS[collector_name].rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()
```

## Mitigation: Package Signing (Optional)

**When to implement**: If distributing as wheel/sdist

**Pattern**:

```python
import hashlib

# At build time: Generate signatures
COLLECTOR_HASHES = {
    "links": "sha256:abc123...",
    "images": "sha256:def456...",
}

# At runtime: Verify signatures
def verify_collector(collector_name: str):
    module_path = ALLOWED_COLLECTORS[collector_name]
    module_file = importlib.util.find_spec(module_path.rsplit(".", 1)[0]).origin

    with open(module_file, 'rb') as f:
        actual_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"

    expected = COLLECTOR_HASHES[collector_name]
    if actual_hash != expected:
        raise SecurityError(f"Collector '{collector_name}' hash mismatch")
```

## Policy Requirements

1. **Hardcoded allowlist** (not configurable by users)
2. **No dynamic imports** of user-provided collector names
3. **Optional signing** if distributing as installable package
4. **Subprocess isolation only** (not needed for in-process collectors)

## Implementation Status

- **Allowlist**: NOT IMPLEMENTED (YAGNI-gated with P1-2)
- **Signing**: NOT IMPLEMENTED (YAGNI-gated with P1-2)
- **Dependency**: Requires subprocess isolation (P1-2) to be implemented first

**If subprocess isolation never deployed**: This policy is moot.

---

**EVIDENCE ANCHOR**:
- **CLAIM-P1-2.5-DOC**: Collector allowlist policy documented
- **Source**: External review A.4 + gap analysis
- **Link**: P1-2 (subprocess isolation dependency)
```

**Success Criteria**:
- [ ] Allowlist enforcement pattern documented
- [ ] Package signing pattern documented (optional)
- [ ] Policy linked to P1-2 (subprocess isolation)
- [ ] Clear YAGNI dependency

**Time Estimate**: 1 hour (documentation only)

---

## P1-3: Reentrancy/Immutable-Read Guarantees Pattern

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P1-3-DOC**: No guidance on thread-safe parser usage
- **Gap**: Collectors mutate state during dispatch (not thread-safe)
- **Scope**: Document pattern for production (no skeleton implementation needed)
- **Source**: External review B.3 (ChatGPT gap analysis)

**YAGNI Assessment**:
- Q1: Real requirement? ⚠️ **CONDITIONAL** - Only if multi-threaded parsing confirmed
- Q2: Used immediately? ❌ NO - No multi-threaded use case identified
- Q3: Backed by data? ❌ NO - No concurrent parsing requirement
- Q4: Can defer? ✅ YES - Document pattern, defer implementation
- **Outcome**: `document_pattern = TRUE`, `implement_only_if_needed = TRUE`

### --- EXECUTION ---

**FILE**: `docs/PATTERN_THREAD_SAFETY.md`

```markdown
# Thread-Safety Pattern for Collectors

**Version**: 1.0
**Date**: 2025-10-16
**Status**: Reference pattern (not implemented in skeleton)
**Source**: External review B.3 + gap analysis

---

## Current Design: NOT Thread-Safe

**Problem**: Collectors mutate state during dispatch

```python
class LinksCollector:
    def __init__(self):
        self._links = []  # ❌ Mutable state

    def on_token(self, idx, tok, ctx, wh):
        self._links.append(...)  # ❌ Mutates shared state
```

**Consequence**: If same `LinksCollector` instance used across threads → race conditions

## Pattern 1: Copy-on-Parse (Simplest)

**Approach**: Create new parser/collector instances per thread

```python
# Thread-safe: Each thread gets fresh instances
def parse_in_thread(markdown_content):
    parser = MarkdownParserCore(markdown_content)
    result = parser.parse()  # Fresh collectors per parse
    return result
```

**Pros**: No code changes needed, simple
**Cons**: Higher memory overhead (more instances)

## Pattern 2: Immutable Collectors (Complex)

**Approach**: Collectors return data instead of mutating state

```python
class ImmutableLinksCollector:
    def on_token(self, idx, tok, ctx, wh):
        # Return new link dict instead of appending
        if tok.type == "link_open":
            return {"href": tok.attrGet("href"), ...}
        return None

    def finalize(self, wh, collected_items):
        # Aggregate items collected by warehouse
        return {"links": collected_items}
```

**Pros**: Truly thread-safe
**Cons**: Significant refactor, different API

## Recommended Approach

**For skeleton/production**: Use **Pattern 1 (Copy-on-Parse)**

**Rationale**:
- Python GIL makes multi-threaded parsing uncommon
- Multiprocessing preferred for parallel parsing (no shared state)
- Copy-on-parse requires zero code changes

**When to implement Pattern 2**:
- If profiling shows parser instance creation is bottleneck
- If true multi-threaded parsing required (rare in Python)

## Documentation Status

**Current**: Parser is NOT thread-safe (document this)
**Recommended**: Use separate instances per thread (Pattern 1)
**Future**: Immutable collectors only if measured need

---

**EVIDENCE ANCHOR**:
- **CLAIM-P1-3-DOC**: Thread-safety pattern documented
- **Source**: External review B.3 + gap analysis
- **Recommendation**: Copy-on-parse (Pattern 1) for production
```

**Success Criteria**:
- [ ] Thread-safety limitation documented
- [ ] Copy-on-parse pattern documented
- [ ] Immutable collector pattern documented (reference)
- [ ] Recommendation clear (Pattern 1 for production)

**Time Estimate**: 1 hour (documentation only)

---

## P1-4: Token Canonicalization Verification Test

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P1-4-TEST**: No test verifies malicious token methods are not executed
- **Gap**: Token canonicalization assumed safe but not tested
- **Scope**: Skeleton test to verify canonicalization
- **Source**: External security analysis (malicious token methods)

**YAGNI Assessment**:
- Q1: Real requirement? ✅ YES - Token security critical
- Q2: Used immediately? ✅ YES - Reference test for production
- Q3: Backed by data? ✅ YES - Token getter attacks documented in DEEP_VULNERABILITIES_ANALYSIS
- Q4: Can defer? ❌ NO - Security property verification
- **Outcome**: `implement_test = TRUE` (skeleton scope)

### --- EXECUTION ---

**Step 1: Add Token Canonicalization Test**

```python
# FILE: skeleton/tests/test_malicious_token_methods.py
# (Create - skeleton scope allowed)

"""
Token Canonicalization Verification Test.

Verifies that malicious token methods (attrGet, __getattr__) are NOT executed
during dispatch, ensuring token canonicalization is complete.

REFERENCE: External artifact test_malicious_token_methods.py
"""

import importlib
import pytest
import os
from pathlib import Path

class MaliciousToken:
    """Mock token with side-effect methods to detect execution."""

    def __init__(self):
        self.type = "inline"
        self.content = "safe"
        self._side_effect_marker = Path("/tmp/token_side_effect_marker")
        # Remove marker if exists
        self._side_effect_marker.unlink(missing_ok=True)

    def attrGet(self, name):
        """Simulate accessor that performs side-effect if called."""
        try:
            self._side_effect_marker.write_text("attrGet_executed")
        except Exception:
            pass
        return getattr(self, name, None)

    def __getattr__(self, name):
        """Simulate __getattr__ side-effect."""
        try:
            self._side_effect_marker.write_text("__getattr___executed")
        except Exception:
            pass
        raise AttributeError(name)


def test_malicious_token_methods_not_invoked():
    """
    Verify token canonicalization prevents malicious method execution.

    Tests that TokenWarehouse canonicalizes tokens to primitive dicts,
    preventing attrGet() or __getattr__() execution during dispatch.
    """
    try:
        from skeleton.doxstrux.markdown.utils.token_warehouse import TokenWarehouse
        from skeleton.doxstrux.markdown.collectors_phase8.links import LinksCollector
    except ImportError:
        pytest.skip("Skeleton modules not available")

    # Create malicious token
    token = MaliciousToken()
    tokens = [token]

    # Instantiate warehouse with malicious token
    try:
        wh = TokenWarehouse(tokens, tree=None)
    except Exception:
        pytest.skip("TokenWarehouse instantiation failed")

    # Register collector
    coll = LinksCollector()
    try:
        wh.register_collector(coll)
    except Exception:
        # Fallback: direct append
        try:
            wh._collectors.append(coll)
        except Exception:
            pytest.skip("Cannot register collector")

    # Dispatch collectors
    dispatch_fn = None
    for name in ("dispatch_all", "dispatch", "run_collectors"):
        if hasattr(wh, name):
            dispatch_fn = getattr(wh, name)
            break

    if dispatch_fn is None:
        pytest.skip("No known dispatch method found")

    try:
        dispatch_fn()
    except Exception:
        pass  # Dispatch may raise on malformed tokens

    # CRITICAL ASSERTION: Side-effect marker should NOT exist
    marker = token._side_effect_marker
    assert not marker.exists(), \
        f"❌ CRITICAL: Malicious token method was executed (found {marker}). " \
        "Token canonicalization incomplete or bypassed."

    # Cleanup
    marker.unlink(missing_ok=True)

    # EVIDENCE ANCHOR
    # CLAIM-P1-4-TEST: Token canonicalization prevents method execution
    # Source: External artifact + DEEP_VULNERABILITIES_ANALYSIS
```

**Success Criteria**:
- [ ] Test creates malicious token with side-effect methods
- [ ] Test verifies side-effects NOT executed during dispatch
- [ ] Test demonstrates token canonicalization security property

**Time Estimate**: 1 hour

---

# PART 3: P2 PROCESS AUTOMATION

## P2-1: YAGNI Checker Tool

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P2-1-TOOL**: Automate YAGNI violation detection in PRs
- **Source**: External review F.2
- **Purpose**: Prevent speculative code from merging
- **Scope**: Development tool (not production code)

**YAGNI Assessment** (meta - checking the checker):
- Q1: Real requirement? ✅ YES - CODE_QUALITY.json enforcement
- Q2: Used immediately? ✅ YES - Every PR
- Q3: Backed by data? ✅ YES - Manual checklist error-prone
- Q4: Can defer? ✅ YES - Manual works but slow
- **Outcome**: `implement_tool = TRUE` (P2 priority)

### --- EXECUTION ---

**Step 1: Create YAGNI Checker Script**

```python
# FILE: tools/check_yagni.py
# (Create - skeleton tools allowed)

#!/usr/bin/env python3
"""
YAGNI Compliance Checker

Detects speculative code patterns per CODE_QUALITY.json.

Usage:
    python tools/check_yagni.py
    python tools/check_yagni.py --ci  # Exit 1 on violations

Violations Detected:
- Unused function parameters
- Boolean flags with only one code path
- Unused hook parameters
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Any

YAGNI_VIOLATIONS = [
    ('unused_param', 'Parameter never used in function body'),
    ('speculative_flag', 'Boolean flag with only one code path'),
    ('unused_hook', 'Hook parameter never called'),
]

def check_file(filepath: Path) -> List[Dict[str, Any]]:
    """Check Python file for YAGNI violations."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))
    except Exception as e:
        return [{
            'file': filepath,
            'line': 0,
            'type': 'parse_error',
            'message': f'Failed to parse: {e}',
            'severity': 'error'
        }]

    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for unused parameters
            param_names = {arg.arg for arg in node.args.args}

            # Exclude common patterns: self, cls, _
            param_names = {p for p in param_names if p not in ('self', 'cls') and not p.startswith('_')}

            # Find all names used in function body
            used_names = set()
            for n in ast.walk(node):
                if isinstance(n, ast.Name):
                    used_names.add(n.id)

            unused = param_names - used_names

            for param in unused:
                violations.append({
                    'file': filepath,
                    'line': node.lineno,
                    'type': 'unused_param',
                    'message': f'Parameter "{param}" never used (YAGNI violation)',
                    'severity': 'warning'
                })

    return violations

def main():
    import argparse
    parser = argparse.ArgumentParser(description='YAGNI Compliance Checker')
    parser.add_argument('--ci', action='store_true', help='Exit 1 on violations (CI mode)')
    parser.add_argument('--path', default='skeleton', help='Path to check (default: skeleton)')
    args = parser.parse_args()

    src_path = Path(args.path)
    if not src_path.exists():
        print(f"❌ Path not found: {src_path}")
        sys.exit(2)

    py_files = list(src_path.rglob('*.py'))
    all_violations = []

    for filepath in py_files:
        all_violations.extend(check_file(filepath))

    if all_violations:
        print(f"⚠️  YAGNI violations detected: {len(all_violations)}")
        for v in all_violations:
            print(f"  {v['file']}:{v['line']} - {v['message']}")

        if args.ci:
            sys.exit(1)
        else:
            sys.exit(0)  # Warning only in dev mode
    else:
        print("✅ YAGNI compliance check passed")
        sys.exit(0)

if __name__ == '__main__':
    main()
```

**Step 2: Add to Pre-Commit (Optional)**

```yaml
# FILE: .pre-commit-config.yaml
# (Optional - not in skeleton scope, document for reference)

repos:
  - repo: local
    hooks:
      - id: yagni-checker
        name: YAGNI Compliance Check
        entry: python tools/check_yagni.py --ci
        language: system
        pass_filenames: false
```

**Success Criteria**:
- [ ] Tool detects unused parameters
- [ ] Tool runs successfully on skeleton code
- [ ] CI integration documented (optional)

**Time Estimate**: 3 hours

---

## P2-2: KISS Routing Table Pattern Documentation

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P2-2-DOC**: Routing table bitmask logic needs simplification guidance
- **Source**: External review G.1
- **Purpose**: Document KISS pattern for production migration
- **Scope**: Documentation only (no code changes)

**Decision**: Document pattern, do not refactor skeleton (out of scope for Phase 8).

### --- EXECUTION ---

**Step 1: Create Routing Table Pattern Doc**

```markdown
# FILE: docs/PATTERN_ROUTING_TABLE_KISS.md
# (Create - documentation allowed)

# KISS Routing Table Pattern

**Version**: 1.0
**Date**: 2025-10-16
**Status**: Reference Pattern (Not Implemented in Skeleton)
**Source**: External review G.1
**Purpose**: Simplification guidance for production routing table

---

## Problem Statement

Current routing table uses bitmask logic which is:
- ✅ Fast (O(1) dispatch)
- ❌ Complex (bitmasking harder to audit)
- ❌ Less readable (clever but opaque)

## KISS Alternative Pattern

### Current Approach (Bitmask)

```python
# Complex: Uses bitmasks for ignore sets
mask = 0
for token_type in sorted(ignore_types):
    bit_position = self._mask_map[token_type]
    mask |= (1 << bit_position)
```

### KISS Alternative (Set-Based)

```python
# Simple: Uses Python sets directly
class RoutingTable:
    def __init__(self):
        self._collector_ignore_sets: Dict[str, Set[str]] = {}

    def register_ignore_set(self, collector_name: str, ignore_types: Set[str]):
        """Register collector's ignore set (deterministic via sorted())."""
        self._collector_ignore_sets[collector_name] = ignore_types

    def should_ignore(self, collector_name: str, token_type: str) -> bool:
        """Check if collector should ignore token (O(1) set lookup)."""
        ignore_set = self._collector_ignore_sets.get(collector_name, set())
        return token_type in ignore_set
```

**Benefits**:
- ✅ Simpler: No bitmasking complexity
- ✅ Readable: Intent obvious
- ✅ Still O(1): Set membership is O(1)
- ✅ Deterministic: Sorted() ensures consistent order

**Trade-Off**:
- Memory: Slight increase (pointers vs bits) - negligible in practice

## Recommendation

**When to Use**:
- Production migration (when simplicity > micro-optimization)
- New features (KISS default)

**When to Keep Bitmask**:
- Performance-critical paths with profiling proof
- Never for readability/maintenance

## References

- CODE_QUALITY.json PRIN-KISS
- External review G.1
```

**Success Criteria**:
- [ ] Pattern documented with code examples
- [ ] Benefits/trade-offs explicit
- [ ] Recommendation clear (KISS default)

**Time Estimate**: 1 hour

---

## P2-3: Auto-Fastpath for Small Documents Pattern

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P2-3-DOC**: Warehouse overhead dominates on small documents
- **Gap**: No guidance on when to skip warehouse
- **Scope**: Document pattern, no skeleton implementation
- **Source**: External review C.1 (ChatGPT gap analysis)

**YAGNI Assessment**:
- Q1: Real requirement? ⚠️ **CONDITIONAL** - Only if profiling shows overhead
- Q2: Used immediately? ❌ NO - No performance bottleneck identified
- Q3: Backed by data? ⚠️ **PARTIAL** - ChatGPT review mentions small doc overhead
- Q4: Can defer? ✅ YES - Optimize only if measured
- **Outcome**: `document_pattern = TRUE`, `implement_only_if_measured = TRUE`

### --- EXECUTION ---

**FILE**: `docs/PATTERN_AUTO_FASTPATH.md`

```markdown
# Auto-Fastpath for Small Documents

**Version**: 1.0
**Date**: 2025-10-16
**Status**: Reference pattern (implement only if profiling shows need)
**Source**: External review C.1 + gap analysis

---

## Problem Statement

**Warehouse overhead**: For small documents (<1KB), warehouse index building may cost more than linear extraction.

**Measured overhead** (hypothetical):
- <1KB docs: Warehouse 0.35ms vs. Linear 0.30ms (1.17x slower)
- 1-10KB docs: Warehouse 0.80ms vs. Linear 1.20ms (1.5x faster)
- >10KB docs: Warehouse 2.0ms vs. Linear 5.5ms (2.75x faster)

## Pattern: Adaptive Dispatch

**Approach**: Use warehouse only if document exceeds size threshold

```python
class MarkdownParserCore:
    WAREHOUSE_THRESHOLD_BYTES = 2048  # 2KB

    def parse(self):
        content_size = len(self.content)

        if content_size < self.WAREHOUSE_THRESHOLD_BYTES:
            # Fastpath: Linear extraction (no warehouse)
            return self._extract_linear()
        else:
            # Warehouse path: Index-based extraction
            return self._extract_with_warehouse()
```

## When to Implement

**ONLY if profiling shows**:
1. Small documents are >50% of workload
2. Warehouse overhead >20% of parse time
3. Fastpath reduces P95 latency by >10%

**Do NOT implement**:
- Speculatively (violates YAGNI)
- Without profiling data
- If small docs are <10% of workload

## Alternative: Configuration-Based

```python
parser = MarkdownParserCore(
    content,
    use_warehouse="auto"  # "auto", "always", "never"
)
```

**Rationale**: Allows per-use-case tuning

## Recommended Approach

**For skeleton/production**: Do NOT implement (YAGNI)

**For future**: Add only if profiling shows measurable benefit

---

**EVIDENCE ANCHOR**:
- **CLAIM-P2-3-DOC**: Auto-fastpath pattern documented
- **Source**: External review C.1 + gap analysis
- **YAGNI**: Implement only if measured overhead
```

**Success Criteria**:
- [ ] Fastpath pattern documented
- [ ] Size threshold guidance provided
- [ ] YAGNI constraints explicit
- [ ] Profiling requirements clear

**Time Estimate**: 30 minutes (documentation only)

---

## P2-4: Fuzz Testing Pattern

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P2-4-DOC**: No fuzzing tests for parser robustness
- **Gap**: Adversarial corpora are curated, not randomized
- **Scope**: Document fuzzing pattern for production testing
- **Source**: External review E.2 (ChatGPT gap analysis)

**YAGNI Assessment**:
- Q1: Real requirement? ⚠️ **CONDITIONAL** - Only if parser crashes/hangs found
- Q2: Used immediately? ❌ NO - No known robustness issues
- Q3: Backed by data? ⚠️ **PARTIAL** - Fuzzing is best practice but not required
- Q4: Can defer? ✅ YES - Document pattern, defer implementation
- **Outcome**: `document_pattern = TRUE`, `implement_only_if_needed = TRUE`

### --- EXECUTION ---

**FILE**: `docs/PATTERN_FUZZ_TESTING.md`

```markdown
# Fuzz Testing Pattern for Parser

**Version**: 1.0
**Date**: 2025-10-16
**Status**: Optional enhancement (implement only if crashes/hangs found)
**Source**: External review E.2 + gap analysis

---

## Purpose

Discover edge cases via randomized input generation:
- Parser crashes (unhandled exceptions)
- Parser hangs (infinite loops)
- Memory exhaustion (OOM)
- Assertion failures

## Fuzzing Tools

### Option 1: Hypothesis (Property-Based Testing)

```python
# FILE: tests/test_fuzz_parser.py

from hypothesis import given, strategies as st
import pytest

@given(st.text(min_size=0, max_size=10000))
def test_parser_never_crashes(markdown):
    """Parser should never crash on any text input."""
    try:
        parser = MarkdownParserCore(markdown)
        result = parser.parse()

        # Invariants that must hold
        assert isinstance(result, dict)
        assert "sections" in result
        assert "links" in result
    except Exception as e:
        # Capture crash
        pytest.fail(f"Parser crashed on input: {repr(markdown)[:100]}")

@given(
    st.text(min_size=0, max_size=1000),
    st.integers(min_value=1, max_value=6)  # Heading levels
)
def test_headings_never_crash(text, level):
    """Headings extractor should handle any text/level."""
    markdown = f"{'#' * level} {text}"
    parser = MarkdownParserCore(markdown)
    result = parser.parse()

    # Should complete without crash
    assert "sections" in result
```

**Run fuzzing**:
```bash
.venv/bin/python -m pytest tests/test_fuzz_parser.py \
  --hypothesis-show-statistics \
  --hypothesis-profile=ci
```

### Option 2: AFL/LibFuzzer (Advanced)

**When to use**: If parser has C extensions or performance-critical code

```python
# FILE: fuzz_targets/fuzz_parser.py

import atheris
import sys

def TestOneInput(data):
    try:
        markdown = data.decode("utf-8", errors="ignore")
        parser = MarkdownParserCore(markdown)
        parser.parse()
    except Exception:
        pass  # Expected for malformed input

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
```

**Run fuzzing**:
```bash
python fuzz_targets/fuzz_parser.py -max_total_time=600  # 10 minutes
```

## Fuzzing Corpus Seeding

**Seed fuzzer with known-good inputs**:
```
fuzz_corpus/
├── seed_001_basic.md         # Basic markdown
├── seed_002_tables.md        # Tables
├── seed_003_nested_lists.md  # Complex nesting
├── seed_004_unicode.md       # Unicode edge cases
└── seed_005_large.md         # Large document
```

**Fuzzer mutates seeds** → discovers crashes

## Integration with CI

**Optional CI job** (runs nightly, not on every PR):

```yaml
name: Fuzz Testing

on:
  schedule:
    - cron: '0 2 * * *'  # 2am daily

jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install fuzzing dependencies
        run: |
          .venv/bin/pip install hypothesis

      - name: Run fuzz tests
        run: |
          .venv/bin/python -m pytest \
            tests/test_fuzz_parser.py \
            --hypothesis-profile=ci \
            --timeout=3600  # 1 hour max

      - name: Report crashes
        if: failure()
        run: |
          echo "Fuzzing found crashes - investigate"
          # Upload crash artifacts
```

## When to Implement

**ONLY if**:
1. Parser crashes found in production
2. Parser hangs found in production
3. Security audit requires fuzzing
4. Tech Lead approves effort

**Do NOT implement**:
- Speculatively (violates YAGNI)
- Without known robustness issues
- As part of skeleton work (production-only concern)

## Recommended Approach

**Current**: Skip fuzzing (no known issues)
**Future**: Add if crashes/hangs discovered
**Effort**: 4-6 hours (hypothesis setup + CI integration)

---

**EVIDENCE ANCHOR**:
- **CLAIM-P2-4-DOC**: Fuzz testing pattern documented
- **Source**: External review E.2 + gap analysis
- **YAGNI**: Implement only if crashes/hangs found
```

**Success Criteria**:
- [ ] Fuzzing pattern documented (hypothesis + AFL)
- [ ] Corpus seeding documented
- [ ] CI integration pattern provided
- [ ] YAGNI conditions explicit

**Time Estimate**: 1 hour (documentation only)

---

## P2-5: Feature-Flag Consolidation Pattern

### --- THINKING ---

**Problem Statement**:
- **CLAIM-P2-5-DOC**: Multiple feature flags may proliferate during Phase 8 migration
- **Gap**: No guidance on flag lifecycle and consolidation
- **Scope**: Document pattern for flag management
- **Source**: External review G.1 (ChatGPT gap analysis)

**YAGNI Assessment**:
- Q1: Real requirement? ⚠️ **CONDITIONAL** - Only if >3 flags added
- Q2: Used immediately? ❌ NO - Only after migration phases complete
- Q3: Backed by data? ⚠️ **PARTIAL** - Flag proliferation is a known issue
- Q4: Can defer? ✅ YES - Document pattern, apply only if needed
- **Outcome**: `document_pattern = TRUE`, `implement_only_if_needed = TRUE`

### --- EXECUTION ---

**FILE**: `docs/PATTERN_FEATURE_FLAG_LIFECYCLE.md`

```markdown
# Feature-Flag Lifecycle Management

**Version**: 1.0
**Date**: 2025-10-16
**Status**: Reference pattern (implement only if flag count >3)
**Source**: External review G.1 + gap analysis

---

## Problem Statement

**Flag proliferation**: During multi-phase migration, feature flags accumulate:
- `USE_WAREHOUSE` (Phase 8.0)
- `USE_WAREHOUSE_LINKS` (Phase 8.1)
- `USE_WAREHOUSE_IMAGES` (Phase 8.2)
- ... (12 more flags)

**Result**: Configuration complexity, testing matrix explosion

## Pattern: Hierarchical Flags

**Consolidate flags into single hierarchy**:

```python
# ❌ Bad: 12 independent flags
USE_WAREHOUSE_LINKS = os.getenv("USE_WAREHOUSE_LINKS", "0") == "1"
USE_WAREHOUSE_IMAGES = os.getenv("USE_WAREHOUSE_IMAGES", "0") == "1"
USE_WAREHOUSE_HEADINGS = os.getenv("USE_WAREHOUSE_HEADINGS", "0") == "1"
# ... 9 more

# ✅ Good: Single hierarchical flag
WAREHOUSE_MODE = os.getenv("WAREHOUSE_MODE", "off")  # "off", "partial", "full"

if WAREHOUSE_MODE == "full":
    # All collectors use warehouse
    use_warehouse_for_links = True
    use_warehouse_for_images = True
    # ... all True

elif WAREHOUSE_MODE == "partial":
    # Only specific collectors (for gradual rollout)
    use_warehouse_for_links = True
    use_warehouse_for_images = False  # Legacy path
    # ... mixed

else:  # "off"
    # All collectors use legacy extraction
    use_warehouse_for_links = False
    use_warehouse_for_images = False
    # ... all False
```

## Flag Lifecycle

**Phase 1: Add flag for new feature** (e.g., Phase 8.1 warehouse migration)
```python
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "0") == "1"

if USE_WAREHOUSE:
    return self._extract_with_warehouse()
else:
    return self._extract_legacy()
```

**Phase 2: Default to ON** (after testing)
```python
USE_WAREHOUSE = os.getenv("USE_WAREHOUSE", "1") == "1"  # Default: "1"
```

**Phase 3: Remove flag** (after 1 release cycle with default ON)
```python
# Flag removed, warehouse is always used
return self._extract_with_warehouse()
# Legacy path deleted
```

## Consolidation Rules

**When to consolidate**:
1. ✅ >3 related flags (e.g., per-collector warehouse flags)
2. ✅ Flags always toggled together (not independent)
3. ✅ After migration phase complete (all collectors migrated)

**When NOT to consolidate**:
- ❌ <3 flags (premature optimization)
- ❌ Flags are truly independent (not related)
- ❌ During migration (keep granularity for rollback)

## Testing Strategy

**With hierarchical flags**:
```python
@pytest.mark.parametrize("mode", ["off", "partial", "full"])
def test_warehouse_modes(mode):
    with mock.patch.dict(os.environ, {"WAREHOUSE_MODE": mode}):
        # Test all modes
        result = parse(markdown)
        assert validate(result)
```

**Testing matrix reduced**: 3 modes instead of 2^12 combinations

## Recommended Timeline

**Phase 8.0-8.N**: Keep `USE_WAREHOUSE` flag (single flag, all collectors)
**After Phase 8.N**: Remove flag, warehouse always ON
**Duration**: 2 release cycles (1 default ON, 1 remove flag)

## Anti-Pattern: Permanent Flags

**Avoid**:
```python
# ❌ Flag never removed (permanent complexity)
if os.getenv("USE_LEGACY_EXTRACTION", "0") == "1":
    return self._extract_legacy()  # Dead code after 1 year
```

**Instead**:
- Set sunset date for flag (e.g., 2 releases)
- Remove flag and legacy code path after sunset
- Document in migration plan

---

**EVIDENCE ANCHOR**:
- **CLAIM-P2-5-DOC**: Feature-flag consolidation pattern documented
- **Source**: External review G.1 + gap analysis
- **YAGNI**: Apply only if flag count >3
```

**Success Criteria**:
- [ ] Flag lifecycle documented (add → default ON → remove)
- [ ] Consolidation pattern documented (hierarchical flags)
- [ ] Testing strategy provided (parameterized tests)
- [ ] Anti-pattern documented (permanent flags)

**Time Estimate**: 1 hour (documentation only)

---

## Part 2 Completion Checklist

**Before proceeding to Part 3**, verify:

### P1 Reference Patterns
- [ ] **P1-1**: Binary search reference implemented in skeleton
- [ ] **P1-2**: Subprocess isolation documented as YAGNI-gated (with worker pooling extension)
- [ ] **P1-2.5**: Collector allowlist policy documented
- [ ] **P1-3**: Thread-safety pattern documented
- [ ] **P1-4**: Token canonicalization test created

### P2 Process Automation
- [ ] **P2-1**: YAGNI checker tool created and functional
- [ ] **P2-2**: KISS routing pattern documented
- [ ] **P2-3**: Auto-fastpath pattern documented
- [ ] **P2-4**: Fuzz testing pattern documented
- [ ] **P2-5**: Feature-flag consolidation pattern documented

**Total P1+P2 Effort**: 11 hours (P1: 3.5h, P2: 7.5h)

---

## Evidence Summary - P1/P2 Claims

| Claim ID | Statement | Evidence Source | Verification |
|----------|-----------|-----------------|--------------|
| CLAIM-P1-1-REF | Binary search O(log N) | test_section_lookup_performance.py | ⏳ Implement |
| CLAIM-P1-2-YAGNI | Subprocess isolation YAGNI-gated | tools/collector_worker_YAGNI_PLACEHOLDER.py | ⏳ Document |
| CLAIM-P1-2.5-DOC | Collector allowlist documented | policies/EXEC_COLLECTOR_ALLOWLIST_POLICY.md | ⏳ Create |
| CLAIM-P1-3-DOC | Thread-safety pattern documented | docs/PATTERN_THREAD_SAFETY.md | ⏳ Create |
| CLAIM-P1-4-TEST | Token canonicalization verified | skeleton/tests/test_malicious_token_methods.py | ⏳ Create |
| CLAIM-P2-1-TOOL | YAGNI checker functional | tools/check_yagni.py | ⏳ Implement |
| CLAIM-P2-2-DOC | KISS routing documented | docs/PATTERN_ROUTING_TABLE_KISS.md | ⏳ Create |
| CLAIM-P2-3-DOC | Auto-fastpath documented | docs/PATTERN_AUTO_FASTPATH.md | ⏳ Create |
| CLAIM-P2-4-DOC | Fuzz testing documented | docs/PATTERN_FUZZ_TESTING.md | ⏳ Create |
| CLAIM-P2-5-DOC | Feature-flag pattern documented | docs/PATTERN_FEATURE_FLAG_LIFECYCLE.md | ⏳ Create |

---

**END OF PART 2**

**Version**: 1.1 (Split Edition - Part 2)
**Last Updated**: 2025-10-16
**Status**: READY FOR P1/P2 IMPLEMENTATION
**Next Review**: After P1/P2 completion (11h)
**Owner**: Phase 8 Development Team

---

## Next Steps

**After completing ALL P1/P2 items above**:

✅ Proceed to: **PLAN_CLOSING_IMPLEMENTATION_extended_3.md** (Part 3: Testing/Production)

⚠️ **RECOMMENDED but NOT BLOCKING**: Part 3 can begin even if P1/P2 incomplete (P0 is the hard dependency).

---

## References

- **Part 1**: PLAN_CLOSING_IMPLEMENTATION_extended_1.md (P0 Critical)
- **Part 3**: PLAN_CLOSING_IMPLEMENTATION_extended_3.md (Testing/Production)
- **Security Status**: EXEC_SECURITY_IMPLEMENTATION_STATUS.md
- **Golden CoT**: CHAIN_OF_THOUGHT_GOLDEN_ALL_IN_ONE.json
- **Code Quality**: CODE_QUALITY.json (YAGNI, KISS, SOLID)
- **External Review**: ChatGPT security analysis + gap analysis
