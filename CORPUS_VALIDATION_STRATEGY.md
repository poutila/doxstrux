# Corpus Validation Strategy

**Issue**: 26 .md files don't have paired .json files
**Question**: How to ensure newly created JSONs are correct?

---

## Current Corpus State

### Files:
- **448 .md files** total
- **422 existing md-json pairs** (validated pairs)
- **26 .md files without .json** (unpaired)
- **1 orphan .json** (test_output.json - should be deleted)

### Unpaired Files (26):

**Documentation/README files (should exclude from baseline):**
- `CLAUDEorig.md`
- `md_stress_mega/README.md`
- `md_refactored_suite/README.md`
- `sec_hardening_suite/README.md`
- `test_mds/README_TEST_SUITE.md`

**Index files (should exclude from baseline):**
- `bad_indentation__INDEX.md`
- `front_matter__INDEX.md`
- `html_chaos__INDEX.md`
- `huge_tables__INDEX.md`
- `link_flood__INDEX.md`
- `math_heavy__INDEX.md`
- `mixed_encoding__INDEX.md`
- `overlapping__INDEX.md`
- `pandoc_features__INDEX.md`

**Test files without JSON (need investigation):**
- `md_brutal_tables.md`
- `md_brutal_tables_nohtml.md`
- `md_brutal_test.md`
- `md_brutal_test_commonmark.md`
- `md_brutal_test_gfm.md`
- `md_nested_lists_checklists.md`
- `md_test_document.md`
- `test_code_blocks.md`
- `test_edge_cases.md`
- `test_mixed_nested_structures.md`
- `test_performance_large.md`
- `test_requirements.md`

---

## Validation Strategies

### Option 1: Generate JSON and Manual Review (Safest)

**Approach**:
1. Generate baseline for all 448 .md files
2. For 26 unpaired files, manually review generated JSON
3. If correct, commit the new .json files to corpus
4. Future baselines will validate against these

**Pros**:
- ✅ Human verification of correctness
- ✅ Creates complete corpus for future
- ✅ One-time manual effort

**Cons**:
- ⏱️ Time-consuming (manual review of 26 files)
- 🤔 Requires domain expertise to validate

**Commands**:
```bash
# 1. Generate baseline (creates JSON for unpaired files)
python3 tools/generate_baseline.py \
  --corpus=src/docpipe/md_parser_testing \
  --emit-baseline=baseline/v0_current.json

# 2. Extract newly generated JSONs from baseline
python3 tools/extract_generated_jsons.py \
  --baseline=baseline/v0_current.json \
  --output-dir=src/docpipe/md_parser_testing

# 3. Manually review the 26 new .json files
# 4. If correct, commit them to repository
git add src/docpipe/md_parser_testing/**/*.json
git commit -m "Add missing JSON pairs from baseline generation"
```

---

### Option 2: Exclude Unpaired Files (Pragmatic)

**Approach**:
1. Create a curated corpus list (only paired files)
2. Exclude README/INDEX files from baseline
3. Generate baseline from 422 validated pairs only

**Pros**:
- ✅ Only validated pairs in baseline
- ✅ No manual review needed
- ✅ Faster baseline generation

**Cons**:
- ⚠️ 26 files not covered by parity tests
- ⚠️ Some legitimate test files might be excluded

**Implementation**:
```python
# Create tools/create_curated_corpus.py
def create_curated_corpus():
    """Create list of validated md-json pairs only."""

    corpus_path = Path('src/docpipe/md_parser_testing')

    # Find all md-json pairs
    paired_files = []
    for md_file in corpus_path.rglob('*.md'):
        json_file = md_file.with_suffix('.json')

        # Only include if JSON exists and not README/INDEX
        if json_file.exists():
            name = md_file.name.lower()
            if 'readme' not in name and 'index' not in name:
                paired_files.append(md_file)

    return paired_files

# Then in baseline generator:
# --corpus-list=curated_corpus.txt (file list instead of directory)
```

---

### Option 3: Two-Tier Validation (Recommended)

**Approach**:
1. **Tier 1 (Validated)**: 422 existing md-json pairs
   - Full parity validation required
   - Performance benchmarks
   - Fail CI if any differences

2. **Tier 2 (Exploratory)**: 26 unpaired files
   - Generate JSON during baseline
   - Track for regressions (compare against self)
   - Warning if changes, but don't fail CI

**Pros**:
- ✅ Validated pairs get strict checking
- ✅ Unpaired files still tested (no silent failures)
- ✅ Can promote Tier 2 → Tier 1 after manual review

**Cons**:
- 🔧 Requires two-tier baseline structure
- 📝 More complex validation logic

**Implementation**:
```python
# Baseline structure:
{
  "validated_pairs": {
    "file1.md": { ... },  # 422 files - strict validation
  },
  "exploratory_files": {
    "unpaired1.md": { ... },  # 26 files - track but don't fail
  }
}

# Validation logic:
def validate_parity(baseline, current):
    failures = []

    # Tier 1: Strict validation (must be 100% identical)
    for file, expected in baseline['validated_pairs'].items():
        current_output = parse(file)
        if current_output != expected:
            failures.append(f"CRITICAL: {file} differs from baseline")

    # Tier 2: Regression tracking (warn but don't fail)
    for file, expected in baseline['exploratory_files'].items():
        current_output = parse(file)
        if current_output != expected:
            print(f"WARNING: {file} changed (not validated)")

    return failures
```

---

### Option 4: Generate Pairs Immediately (Quick Fix)

**Approach**:
1. Run parser NOW on 26 unpaired .md files
2. Generate their .json outputs
3. Commit to corpus
4. Include in baseline validation

**Pros**:
- ✅ Quick - can be done in minutes
- ✅ Creates complete corpus
- ✅ Assumes current parser is "correct"

**Cons**:
- ⚠️ No validation that generated JSON is correct
- ⚠️ If current parser has bugs, we lock them in

**Commands**:
```bash
# Create tool to generate missing JSONs
python3 tools/generate_missing_pairs.py \
  --corpus=src/docpipe/md_parser_testing \
  --profile=moderate

# This will:
# 1. Find all .md files without .json
# 2. Parse them with current parser
# 3. Save output as .json
# 4. Report what was created

# Then commit
git add src/docpipe/md_parser_testing/**/*.json
git commit -m "Generate missing JSON pairs (26 files)"
```

---

## Recommended Approach: **Option 1 + Option 4 Hybrid**

### Step 1: Clean Up Corpus (Immediate)
```bash
# 1. Delete orphan JSON
rm src/docpipe/md_parser_testing/test_output.json

# 2. Exclude README/INDEX files from baseline corpus
# Create a .baseline-ignore file
cat > src/docpipe/md_parser_testing/.baseline-ignore <<EOF
**/README*.md
**/*__INDEX.md
CLAUDEorig.md
EOF

# This reduces unpaired from 26 → 12 (only test files)
```

### Step 2: Generate Missing Pairs (Tool Creation)
```bash
# Generate .json for the 12 legitimate test files
python3 tools/generate_missing_pairs.py \
  --corpus=src/docpipe/md_parser_testing \
  --profile=moderate \
  --exclude-pattern="README|INDEX|CLAUDEorig"

# Creates 12 new .json files
```

### Step 3: Manual Spot Check (Validation)
```bash
# Randomly review 3-5 of the generated JSONs
# Look for:
# - Reasonable structure
# - Expected elements extracted
# - No obvious errors
```

### Step 4: Commit New Pairs
```bash
git add src/docpipe/md_parser_testing/**/*.json
git commit -m "Generate missing JSON pairs for test files

- Added 12 missing .json files
- Excluded README/INDEX documentation files
- Spot-checked for correctness
- Corpus now has 434 validated pairs (422 existing + 12 new)
"
```

### Step 5: Generate Baseline
```bash
# Now generate baseline with complete, validated corpus
python3 tools/generate_baseline.py \
  --corpus=src/docpipe/md_parser_testing \
  --emit-baseline=baseline/v0_current.json \
  --exclude-pattern="README|INDEX|CLAUDEorig"

# Result: 434 validated md-json pairs in baseline
```

---

## Tool Needed: generate_missing_pairs.py

```python
#!/usr/bin/env python3
"""Generate missing .json files for unpaired .md files."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, 'src')
from docpipe.markdown_parser_core import MarkdownParserCore

def generate_missing_pairs(corpus_path, profile, exclude_pattern):
    """Generate .json for all .md files that lack pairs."""

    corpus = Path(corpus_path)
    generated = []

    for md_file in corpus.rglob('*.md'):
        # Check exclusions
        if exclude_pattern and exclude_pattern in md_file.name:
            continue

        json_file = md_file.with_suffix('.json')

        # Skip if JSON already exists
        if json_file.exists():
            continue

        print(f"Generating: {md_file.relative_to(corpus)}")

        try:
            content = md_file.read_text(encoding='utf-8')
            parser = MarkdownParserCore(content, security_profile=profile)
            output = parser.parse()

            # Write JSON
            with json_file.open('w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            generated.append(md_file)
            print(f"  ✅ Created {json_file.name}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    return generated

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', required=True)
    parser.add_argument('--profile', default='moderate')
    parser.add_argument('--exclude-pattern', default='')
    args = parser.parse_args()

    generated = generate_missing_pairs(
        args.corpus,
        args.profile,
        args.exclude_pattern
    )

    print(f"\n✅ Generated {len(generated)} new JSON files")
```

---

## Summary: Recommended Path Forward

1. ✅ **Delete orphan JSON** (`test_output.json`)
2. ✅ **Create generate_missing_pairs.py tool**
3. ✅ **Generate 12 missing JSON files** (exclude README/INDEX)
4. ✅ **Spot-check 3-5 generated files** for sanity
5. ✅ **Commit new pairs to corpus**
6. ✅ **Generate baseline from 434 validated pairs**

**Result**: Complete, validated corpus with all md-json pairs ready for baseline generation.

---

**Generated**: 2025-10-11
**Recommendation**: Hybrid approach (generate + spot-check + commit)
**Time Estimate**: 30 minutes total

**END OF VALIDATION STRATEGY**
