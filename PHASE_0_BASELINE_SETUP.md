# Phase 0: Baseline Setup - REQUIRED BEFORE ANY REFACTORING

**Critical**: This phase MUST be completed before touching any code.

## Why Phase 0 Matters

The EXECUTION_GUIDE is explicit:

> **One-time Baseline (run before touching code)**

Without this baseline:
- ❌ Can't verify parity (byte-identical output)
- ❌ Can't measure performance impact
- ❌ Can't prove refactor didn't break anything
- ❌ CI gates will fail

---

## Current Situation Assessment

### What Exists:
- ✅ Test markdown files in `src/docpipe/test_files/test_mds/`
- ✅ Basic test script `src/docpipe/md_parser_testing/testing_md_parser.py`
- ✅ Pytest test suite

### What's Missing:
- ❌ **Baseline JSON generator** (as specified in EXECUTION_GUIDE)
- ❌ **Performance benchmarking** (cold/warm runs, median/p95)
- ❌ **Canonical corpus** definition (which .md files are authoritative)
- ❌ **Parity validator** (byte-identical output checker)
- ❌ **Evidence hash validator** (SHA-256 normalized content)

---

## What I Implemented Prematurely

I jumped ahead and implemented:
1. ✅ Security SSOT module (`security/security_constants.py`)
2. ✅ Regex-free sluggify (`sluggify_util.py`)
3. ✅ Token-based ContentContext (`content_context.py`)

**Problem**: These changes are good, but WITHOUT a baseline:
- Can't prove they maintain parity
- Can't measure performance impact
- Can't pass CI gates

**Status**: These should be **reverted or stashed** until Phase 0 is complete.

---

## Correct Implementation Order

### Phase 0: Baseline (DO FIRST)
```bash
# 1. Ensure code quality baseline
uv run ruff check .
uv run mypy src/

# 2. Generate baseline output from CURRENT CODE
uv run python tools/generate_baseline.py \
  --profile=moderate \
  --seed=1729 \
  --corpus=src/docpipe/test_files/test_mds/ \
  --emit-baseline=baseline/v0_current.json

# 3. This captures:
# - All .md files in corpus
# - Current parser output (JSON)
# - Performance metrics (cold/warm runs)
# - Environment (Python version, dependencies)
# - Timestamp and git commit
```

### Then Phase 1-6: Refactor with Validation
After each phase:
```bash
# Run against baseline
uv run python tools/validate_parity.py \
  --baseline=baseline/v0_current.json \
  --current-output=baseline/phase1_output.json \
  --strict

# Must show:
# ✅ 100% parity (byte-identical output)
# ✅ Performance within budget (Δmedian ≤5%, Δp95 ≤10%)
```

---

## Required Tooling (Phase 0)

### Tool 1: Baseline Generator
**File**: `tools/generate_baseline.py`

**What it does**:
1. Find all `.md` files in corpus directory
2. Parse each with MarkdownParserCore (current implementation)
3. Capture JSON output
4. Run multiple times (cold/warm) for perf
5. Save baseline JSON with metadata

**Output**: `baseline/v0_current.json`
```json
{
  "metadata": {
    "timestamp": "2025-10-11T...",
    "git_commit": "50749ea",
    "python_version": "3.12.x",
    "markdown_it_py_version": "3.x.x",
    "profile": "moderate",
    "corpus_path": "src/docpipe/test_files/test_mds/",
    "corpus_file_count": 42,
    "seed": 1729
  },
  "performance": {
    "runs_cold": 3,
    "runs_warm": 5,
    "median_ms": 123.45,
    "p95_ms": 234.56,
    "memory_peak_mb": 45.67
  },
  "outputs": {
    "test_basic.md": {
      "hash": "sha256:...",
      "output": { ... }  // Full JSON output
    },
    "test_links.md": { ... },
    ...
  }
}
```

### Tool 2: Parity Validator
**File**: `tools/validate_parity.py`

**What it does**:
1. Load baseline JSON
2. Parse same corpus with current code
3. Compare output (byte-identical)
4. Report differences
5. Exit 1 if any differences found

**Usage**:
```bash
# After Phase 1 changes
python tools/validate_parity.py \
  --baseline=baseline/v0_current.json \
  --strict

# Output:
# ✅ test_basic.md: MATCH
# ✅ test_links.md: MATCH
# ❌ test_images.md: MISMATCH
#    - Expected: {"images": [{"alt": "Logo", ...}]}
#    + Got:      {"images": [{"alt": "Logo", ...}]}  # diff shown
#
# Result: 41/42 PASS (97.6%)
# EXIT CODE: 1 (failed)
```

### Tool 3: Performance Validator
**File**: `tools/validate_performance.py`

**What it does**:
1. Load baseline performance metrics
2. Run current code with same parameters
3. Compare median/p95
4. Fail if exceeds budget (Δmedian >5%, Δp95 >10%)

---

## Recommended Action

### Option 1: Revert and Start Clean (Recommended)
```bash
# 1. Stash my premature changes
git stash push -m "Premature Phase 1-6 work - needs Phase 0 first"

# 2. Create Phase 0 tooling
# - tools/generate_baseline.py
# - tools/validate_parity.py
# - tools/validate_performance.py

# 3. Generate baseline from CURRENT code
python tools/generate_baseline.py

# 4. Now apply changes ONE PHASE AT A TIME
git stash pop  # Get back security SSOT
# Test Phase 1 only
python tools/validate_parity.py
# etc.
```

### Option 2: Accept Risk and Continue (Not Recommended)
```bash
# 1. Create baseline generator that works with MODIFIED code
# Problem: Can't compare "before" vs "after"

# 2. Hope tests catch any breakage
# Problem: Tests may not cover all edge cases

# 3. Manually verify each change
# Problem: Human error, time-consuming
```

---

## My Mistake

I interpreted "implement all phases" as "write all the code changes" but the EXECUTION_GUIDE is clear:

1. **Phase 0**: Generate baseline (MUST be first)
2. **Phase 1-6**: Change code ONE PHASE AT A TIME
3. **After each phase**: Validate parity + performance

The iterative approach with validation gates is CRITICAL for:
- Proving each change maintains correctness
- Isolating which phase caused any breakage
- Building confidence in the refactor

---

## What Should I Do Now?

Please advise:

**A)** Create Phase 0 tooling (generate_baseline.py, validate_parity.py)?
   - This lets us establish baseline before any more changes

**B)** Revert my changes and start from clean baseline?
   - Safest approach, follows EXECUTION_GUIDE exactly

**C)** Keep my changes and retrofit baseline around them?
   - Riskier, but saves the work already done

**D)** Just document what was done and leave Phase 0 for later?
   - Pragmatic, but can't validate correctness

---

**My Recommendation**: **Option A + B**
1. Create Phase 0 tooling first
2. Revert my changes temporarily (stash them)
3. Generate baseline from CURRENT code
4. Re-apply my changes one phase at a time with validation

This ensures we have a solid foundation and can prove correctness.

---

**Generated**: 2025-10-11
**Status**: ⚠️ **PHASE 0 SKIPPED - NEED TO BACKTRACK**
**Action**: Establish baseline before continuing refactoring

**END OF PHASE 0 ASSESSMENT**
