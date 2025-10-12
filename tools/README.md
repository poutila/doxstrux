# Tools Directory

**Purpose**: Testing infrastructure for the Docpipe markdown parser, with special focus on baseline regression testing during the zero-regex refactoring.

**Last Updated**: 2025-10-12

---

## Directory Structure

```
tools/
├── README.md                      # This file
├── baseline_test_runner.py        # Parity testing (byte-by-byte comparison)
├── test_feature_counts.py         # Feature extraction validation
├── generate_baseline_outputs.py   # Baseline regeneration tool
├── run_tests_fast.sh              # Quick subset testing
├── preflight_check.sh             # CI gate preflight check
├── exec_util.py                   # Subprocess helpers for CI gates
├── atomic_write.py                # Atomic file operations
├── validate_phase_artifact.py     # Phase unlock validation
├── create_evidence_block.py       # Evidence block creation
├── baseline_outputs/              # Frozen baselines (READ-ONLY)
├── test_mds/                      # SSOT test pairs
└── ci/                            # CI gate scripts
```

---

## Baseline Regression Testing

### Overview

The baseline testing system ensures that parser output remains **byte-for-byte identical** during refactoring. This is critical for the zero-regex migration where internal implementation changes must not alter parser behavior.

### The 4-Step Testing Procedure

#### 1. SSOT Test Pairs in `tools/test_mds/`

The `test_mds/` directory contains **Single Source of Truth** (SSOT) test pairs:
- **542 markdown files** (`.md`) organized in 32 categories
- **542 test specifications** (`.json`) with expected feature counts

**Structure**:
```
tools/test_mds/
├── 01_edge_cases/
│   ├── 00_no_headings.md          # Input markdown
│   ├── 00_no_headings.json        # Test specification
│   ├── 11_mixed_legit_and_traps.md
│   ├── 11_mixed_legit_and_traps.json
│   └── ...
├── 02_stress_pandoc/
├── 03_stress_overlapping/
└── ... (32 categories total)
```

**Test Specification Format** (`.json`):
```json
{
  "id": "test_identifier",
  "title": "Test Description",
  "md_file": "filename.md",
  "md_flavor": "gfm|commonmark|mixed",
  "allows_html": true|false,
  "feature_counts": {
    "headings": 3,
    "tables": 1,
    "code_fences": 2,
    ...
  }
}
```

#### 2. Baselines in `tools/baseline_outputs/`

Parser outputs are **verified** and **frozen** as baselines:
- **542 baseline files** (`.baseline.json`)
- **Read-only permissions** (`dr-xr-xr-x`)
- Contains complete parser output with all four top-level keys: `content`, `metadata`, `structure`, `mappings`

**Structure**:
```
tools/baseline_outputs/
├── 01_edge_cases/
│   ├── 00_no_headings.baseline.json
│   ├── 11_mixed_legit_and_traps.baseline.json
│   └── ...
├── 02_stress_pandoc/
└── ... (mirrors test_mds/ structure)
```

**Baseline Policy**:
- Baselines are **frozen** and **read-only**
- Any difference triggers test failure
- Regeneration requires explicit verification that changes are intentional improvements
- Permissions: `chmod -R a-w tools/baseline_outputs/`

#### 3. Verification: Parser Outputs vs. Baselines

During refactoring, the parser is run on each `.md` file and output is compared **byte-by-byte** against the corresponding baseline.

**Comparison Method**:
```python
# Normalized JSON comparison with sorted keys
expected_str = json.dumps(baseline, sort_keys=True, indent=2, cls=DateTimeEncoder)
actual_str = json.dumps(parser_output, sort_keys=True, indent=2, cls=DateTimeEncoder)

if expected_str != actual_str:
    # Test fails - parser behavior changed
```

#### 4. Requirement: 100% Pass Rate

**Success Criteria**:
- **542/542 tests pass** (100%)
- **Byte-for-byte identical** output
- **Zero differences** in any field

**Failure Indicates**:
- Unintentional parser behavior change
- Bug introduced during refactoring
- Non-deterministic output (must be fixed immediately)

---

## Tool Documentation

### Core Testing Tools

#### `baseline_test_runner.py`

**Purpose**: Parity testing - compares current parser output against frozen baselines

**Usage**:
```bash
# Run all parity tests
python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs \
  --profile moderate

# Save detailed results
python tools/baseline_test_runner.py \
  --test-dir tools/test_mds \
  --baseline-dir tools/baseline_outputs \
  --output results.json \
  --verbose
```

**Output**:
```
Found 542 test pairs
Security profile: moderate
Test directory: tools/test_mds
--------------------------------------------------------------------------------
[542/542] Testing toc_tree_bounds.md...

================================================================================
BASELINE TEST SUMMARY
================================================================================
Total tests:    542
Passed:         542 (100.0%)
Failed (diff):  0
Failed (error): 0
Total time:     551.98 ms
Average time:   1.02 ms per test
Profile:        moderate

BY CATEGORY:
--------------------------------------------------------------------------------
✓ 01_edge_cases                  114/114 (100.00%)
✓ 02_stress_pandoc                30/ 30 (100.00%)
...
```

**Exit Codes**:
- `0`: All tests passed
- `1`: One or more tests failed

---

#### `test_feature_counts.py`

**Purpose**: Feature extraction validation - verifies parser extracts correct features

**Usage**:
```bash
# Run feature count tests
python tools/test_feature_counts.py --test-dir tools/test_mds

# Test specific category
python tools/test_feature_counts.py --test-dir tools/test_mds/01_edge_cases
```

**What it Tests**:
- Headings count
- Tables count
- Code blocks (fenced vs. indented)
- Lists (ordered, unordered, tasks)
- Links and images
- HTML blocks
- Footnotes

**Tolerance**:
- Some features (`inline_code`, `ref_links`, `hrules`) allow tolerance due to counting difficulty
- Critical features must match exactly

**Expected Results**:
- **512/542 passing** (94.5%)
- 30 Pandoc table failures are expected limitations

---

#### `generate_baseline_outputs.py`

**Purpose**: Regenerate all baseline files (use with extreme caution)

**⚠️ WARNING**: This tool regenerates baselines. Only use when:
1. Intentional parser improvement verified manually
2. All stakeholders approve the change
3. You understand the output differences

**Usage**:
```bash
# Regenerate all baselines
python tools/generate_baseline_outputs.py --profile moderate

# Dry run (show what would be regenerated)
python tools/generate_baseline_outputs.py --dry-run

# Save generation summary
python tools/generate_baseline_outputs.py \
  --summary-output generation_summary.json
```

**After Regeneration**:
```bash
# Verify parser determinism
python tools/baseline_test_runner.py  # Should be 100%

# Verify feature extraction
python tools/test_feature_counts.py   # Should be 94.5%

# Set read-only
chmod -R a-w tools/baseline_outputs/
```

---

#### `run_tests_fast.sh`

**Purpose**: Quick subset testing for rapid iteration

**Usage**:
```bash
# Test edge cases (default)
bash tools/run_tests_fast.sh

# Test specific category
bash tools/run_tests_fast.sh 02_stress_pandoc

# Use different security profile
PROFILE=strict bash tools/run_tests_fast.sh 01_edge_cases
```

**Categories** (32 total):
```
01_edge_cases           14_tables               27_heading_ids_slugs
02_stress_pandoc        15_integration          28_emoji_shortcodes
03_stress_overlapping   16_performance          29_entities_escapes
04_stress_encoding      17_blockquotes          30_fenced_code_info
05_stress_math          18_lists                31_details_summary_html
06_stress_links         19_tasklists            32_toc_invariants
07_stress_html          20_strikethrough_hr
08_stress_indentation   21_inline_formatting
09_stress_huge_tables   22_linebreaks_spacing
10_frontmatter_valid    23_autolink_linkify
11_frontmatter_invalid  24_images_references
12_frontmatter_stress   25_definition_lists
13_security             26_admonitions_containers
```

---

### Supporting Utilities

#### `exec_util.py`

**Purpose**: Subprocess execution helpers for CI gates

**Key Functions**:
- `run_json(cmd, timeout_s)`: Execute command, parse JSON output, fail-closed on error
- `assert_safe(cond, msg)`: Fail-fast assertion with SecurityError

**Usage in CI Gates**:
```python
from exec_util import run_json, assert_safe

result = run_json(["python", "tools/baseline_test_runner.py"], timeout_s=300)
assert_safe(result["passed"] == result["total_tests"], "Parity test failure")
```

---

#### `atomic_write.py`

**Purpose**: Race-condition-free file writes for parallel CI

**Key Functions**:
- `atomic_write_text(path, data)`: Write file atomically using temp + rename

**Pattern**:
```python
from atomic_write import atomic_write_text

# Atomic write (no partial writes if interrupted)
atomic_write_text(Path("output.json"), json.dumps(data))
```

---

#### `validate_phase_artifact.py`

**Purpose**: Validates phase unlock artifacts before allowing Phase N+1

**Schema Validation**:
```python
{
  "schema_version": "1.0",
  "min_schema_version": "1.0",
  "phase": 0,
  "baseline_pass_count": 542,
  "ci_gates_passed": ["G1", "G2", "G3"],
  "git_commit": "abc123def"
}
```

---

#### `create_evidence_block.py`

**Purpose**: Creates evidence blocks with atomic append and secret redaction

**Features**:
- Atomic append using `portalocker`
- Secret redaction (API keys, tokens)
- SHA256 hashing over full snippet
- JSONL format for easy parsing

**Usage**:
```python
from create_evidence_block import create_evidence_block

evidence_id = create_evidence_block(
    evidence_id="E0.1.001",
    phase=0,
    file="src/docpipe/markdown_parser_core.py",
    lines="1215-1215",
    description="Fixed allowed_schemes ordering for determinism"
)
```

---

## Testing Workflows

### Development Workflow

```bash
# 1. Make parser changes
vim src/docpipe/markdown_parser_core.py

# 2. Quick subset test
bash tools/run_tests_fast.sh 01_edge_cases

# 3. If passing, run full parity tests
python tools/baseline_test_runner.py

# 4. If parity fails, investigate differences
python tools/baseline_test_runner.py --verbose --output diff_report.json
```

### Pre-Commit Workflow

```bash
# 1. Run all parity tests (must be 100%)
python tools/baseline_test_runner.py

# 2. Run feature count tests (must be 94.5%+)
python tools/test_feature_counts.py

# 3. If both pass, commit
git add -A
git commit -m "Refactor: [description]"
```

### CI/CD Workflow

```bash
# 1. Preflight check (validates CI gates exist)
bash tools/preflight_check.sh

# 2. Run parity tests
python tools/baseline_test_runner.py --output ci_parity.json

# 3. Verify exit code
if [ $? -ne 0 ]; then
    echo "Parity test failure - blocking merge"
    exit 1
fi
```

---

## Troubleshooting

### Common Issues

#### Issue: Parity tests failing after intentional improvement

**Symptom**: Modified parser to fix bug, now parity tests fail

**Solution**:
1. Verify the fix is correct manually
2. Run feature count tests to ensure no regressions
3. Regenerate baselines with approval
4. Set baselines to read-only

```bash
# Step 1: Verify fix manually
python -c "from src.docpipe.markdown_parser_core import MarkdownParserCore; ..."

# Step 2: Feature count tests
python tools/test_feature_counts.py  # Should still be ~94.5%

# Step 3: Regenerate baselines
python tools/generate_baseline_outputs.py --profile moderate

# Step 4: Verify parity
python tools/baseline_test_runner.py  # Should be 100%

# Step 5: Set read-only
chmod -R a-w tools/baseline_outputs/
```

---

#### Issue: Non-deterministic parser output

**Symptom**: Same input produces different output across runs

**Causes**:
- Set iteration (use `sorted(list(my_set))` instead of `list(my_set)`)
- Dict iteration without sorting
- Datetime serialization issues

**Fix**:
```python
# ❌ Non-deterministic
"allowed_schemes": list(self._ALLOWED_LINK_SCHEMES)

# ✅ Deterministic
"allowed_schemes": sorted(list(self._ALLOWED_LINK_SCHEMES))
```

---

#### Issue: Baseline directory is not read-only

**Symptom**: Accidental baseline modifications

**Fix**:
```bash
# Set read-only recursively
chmod -R a-w tools/baseline_outputs/

# Verify
ls -ld tools/baseline_outputs/  # Should show dr-xr-xr-x
```

---

## Architecture Notes

### Why Byte-by-Byte Comparison?

**Traditional Approach**:
- Semantic comparison (check if headings, tables, etc. match)
- Allows internal representation changes
- **Risk**: Subtle bugs slip through

**Our Approach**:
- Byte-by-byte identical JSON output
- Zero tolerance for any changes
- **Benefit**: Catches ALL unintended changes

**Example**:
```python
# Traditional approach might miss:
# Before: "allowed_schemes": ["http", "https", "mailto", "tel"]
# After:  "allowed_schemes": ["tel", "mailto", "http", "https"]
# ✗ Same content, different order - semantic test passes
# ✓ Byte-by-byte comparison catches this

# Our approach catches:
# - Field ordering changes
# - Whitespace changes
# - Type changes (int → string keys)
# - Floating point precision changes
```

---

### Why Frozen Baselines?

**Moving Target Problem**:
- If baselines regenerate on every test run, bugs go undetected
- "Tests always pass" because baselines adapt to bugs

**Frozen Baseline Solution**:
- Baselines are snapshots of verified-correct parser output
- Any change triggers immediate failure
- Forces deliberate verification of all changes

**Workflow**:
1. Baselines verified correct (manual review + feature count tests)
2. Set read-only (`chmod -R a-w`)
3. All refactoring must produce identical output
4. Regeneration requires explicit approval + verification

---

## Integration with Phase 0 Tasks

From `regex_refactor_docs/DETAILED_TASK_LIST.md`, the baseline testing infrastructure enables:

- **Task 0.0**: Fast Testing Infrastructure - ✅ COMPLETE
- **Task 0.4**: CI Gate G3 - Parity (uses `baseline_test_runner.py`)
- **Task 0.5**: CI Gate G4 - Performance (baseline test timing data)
- **Task 0.6**: CI Gate G5 - Evidence Hash (uses `create_evidence_block.py`)

---

## Quick Reference

### Essential Commands

```bash
# Full parity test (542 tests, ~550ms)
python tools/baseline_test_runner.py

# Quick edge case test (~110 tests, ~110ms)
bash tools/run_tests_fast.sh 01_edge_cases

# Feature validation (512/542 expected pass)
python tools/test_feature_counts.py

# Verify baselines are read-only
ls -ld tools/baseline_outputs/
```

### Expected Results

| Test | Expected | Notes |
|------|----------|-------|
| Parity (baseline_test_runner.py) | 542/542 (100%) | Byte-by-byte identical |
| Feature Counts (test_feature_counts.py) | 512/542 (94.5%) | 30 Pandoc failures OK |
| Parse Time | ~1.02 ms average | Per-file average |
| Total Test Time | ~550 ms | All 542 tests |

---

## See Also

- `CLAUDE.md`: Testing Standards section
- `regex_refactor_docs/DETAILED_TASK_LIST.md`: Phase 0 tasks
- `regex_refactor_docs/REGEX_REFACTOR_POLICY_GATES.md`: CI gate requirements

---

**Last Updated**: 2025-10-12
**Maintained By**: Docpipe development team
**Status**: ✅ Production testing infrastructure
