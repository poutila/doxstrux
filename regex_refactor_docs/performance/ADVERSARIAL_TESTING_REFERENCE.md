# Adversarial Testing - Quick Reference

**Purpose**: Quick reference for adversarial corpus testing
**For complete details**: See archived documentation in `archived/` directory

---

## Adversarial Corpora (9 Files)

**Location**: `./adversarial_corpora/`

1. **adversarial_large.json** - Large token corpus (5k tokens, mixed links)
2. **adversarial_malformed_maps.json** - Malformed map entries (negative/inverted)
3. **adversarial_encoded_urls.json** - Encoded/tricky URLs (percent, NUL, protocol-relative, data:)
4. **adversarial_attrget.json** - Token with href sentinel 'RAISE_ATTRGET' to simulate attrGet raising
5. **adversarial_deep_nesting.json** - Deep nesting (2000 levels) to test nesting limits
6. **adversarial_regex_pathological.json** - Regex-pathological inline content (100k 'a')
7. **adversarial_combined.json** - Combined small corpus exercising multiple vectors
8. **adversarial_template_injection.json** - Template injection vectors (Jinja, EJS, ERB, etc.)
9. **adversarial_html_xss.json** - HTML/XSS vectors (script tags, event handlers, SVG)

---

## Quick Start

### Run Single Corpus
```bash
.venv/bin/python tools/run_adversarial.py \
    adversarial_corpora/adversarial_combined.json \
    --runs 3
```

### Run All Corpora
```bash
for corpus in adversarial_corpora/adversarial_*.json; do
    .venv/bin/python tools/run_adversarial.py "$corpus" --runs 1
done
```

### Run Pytest Tests
```bash
.venv/bin/python -m pytest tests/test_adversarial.py -v
```

---

## Vulnerability Coverage (10/10)

| ID | Vulnerability | Corpus File | Status |
|----|---------------|-------------|--------|
| SEC-1 | Poisoned tokens / attrGet | adversarial_attrget.json | ✅ |
| SEC-2 | URL normalization bypass | adversarial_encoded_urls.json | ✅ |
| SEC-3 | Template injection (SSTI) | adversarial_template_injection.json | ✅ |
| SEC-4 | HTML/XSS | adversarial_html_xss.json | ✅ |
| RUN-1 | Memory amplification (OOM) | adversarial_large.json | ✅ |
| RUN-2 | Integer overflow (maps) | adversarial_malformed_maps.json | ✅ |
| RUN-3 | Deep nesting (stack) | adversarial_deep_nesting.json | ✅ |
| RUN-4 | O(N²) complexity | adversarial_regex_pathological.json | ✅ |
| RUN-5 | Combined vectors | adversarial_combined.json | ✅ |
| ALL | Multi-vector testing | All 9 corpora | ✅ |

---

## CI Integration

### Quick CI Check (for PRs)
```yaml
- name: Adversarial Tests
  run: |
    python tools/run_adversarial.py \
      adversarial_corpora/adversarial_combined.json --runs 1
    pytest tests/test_adversarial.py -v
```

### Full CI Suite (for main branch)
```yaml
- name: Full Adversarial Suite
  run: |
    for corpus in adversarial_corpora/adversarial_*.json; do
      python tools/run_adversarial.py "$corpus" --runs 3
    done
```

---

## Expected Performance Baselines

| Corpus | Expected Time | Expected Memory | Notes |
|--------|---------------|-----------------|-------|
| adversarial_combined | <10ms | <5MB | Small, fast baseline |
| adversarial_malformed_maps | <5ms | <2MB | Map normalization only |
| adversarial_encoded_urls | <10ms | <5MB | URL validation |
| adversarial_attrget | <5ms | <2MB | Should not call attrGet |
| adversarial_deep_nesting | <10ms | <5MB | Should reject early |
| adversarial_regex_pathological | <500ms | <50MB | Large content, may be slow |
| adversarial_large | <200ms | <100MB | 5K tokens |
| adversarial_template_injection | <5ms | <2MB | Detection only |
| adversarial_html_xss | <5ms | <2MB | Detection only |

**Note**: Times are for single parse run. Multiply by `--runs` value for total duration.

---

## Defensive Patches Applied

The skeleton implementation includes these defensive patches:

1. **Token Canonicalization** (`token_warehouse.py:98-136`)
   - Converts token objects to primitive dicts
   - Prevents poisoned getters from executing
   - ~9% performance improvement

2. **Dispatch Error Isolation** (`token_warehouse.py:301-309`)
   - Wraps collector calls in try/except
   - Records errors without crashing dispatch
   - Configurable via `RAISE_ON_COLLECTOR_ERROR` flag

3. **URL Normalization** (`security/validators.py`)
   - Centralized URL validation
   - Control character rejection
   - Protocol-relative URL blocking
   - IDN normalization

4. **Resource Limits** (`token_warehouse.py:7-14`)
   - MAX_TOKENS = 100_000
   - MAX_BYTES = 10_000_000
   - MAX_NESTING = 150

---

## Test Implementation Files

### Runner Tool
**Location**: `tools/run_adversarial.py`
**Features**:
- Flexible module path configuration
- Memory/time profiling (tracemalloc + perf_counter)
- Sentinel support (`RAISE_ATTRGET` for testing)
- JSON report generation
- Multi-run support

### Pytest Integration
**Location**: `tests/test_adversarial.py`
**Tests**:
1. `test_max_tokens_enforced()` - Validates MAX_TOKENS limit
2. `test_malformed_maps_clamped()` - Validates map normalization
3. `test_attrget_does_not_crash_dispatch()` - Validates token canonicalization
4. `test_encoded_url_flags()` - Validates URL normalization

### Additional Security Tests
**Location**: `skeleton/tests/test_vulnerabilities_extended.py`
**Tests**: 7 comprehensive vulnerability tests (see SECURITY_GAP_ANALYSIS.md)

---

## Troubleshooting

### Problem: Import errors for TokenWarehouse
**Solution**: Check module paths with `--token-module` flag
```bash
python tools/run_adversarial.py corpus.json \
    --token-module skeleton.doxstrux.markdown.utils.token_warehouse
```

### Problem: Corpus file not found
**Solution**: Use absolute or relative path from project root
```bash
python tools/run_adversarial.py \
    regex_refactor_docs/performance/adversarial_corpora/adversarial_combined.json
```

### Problem: Tests skip due to missing modules
**Solution**: Install package in development mode
```bash
pip install -e ".[dev]"
```

### Problem: Performance much slower than baseline
**Solution**: Check if canonicalization is enabled and collectors use O(1) data structures

---

## References

**Complete Documentation** (archived):
- `archived/ADVERSARIAL_CORPUS_IMPLEMENTATION.md` - Complete implementation guide (999 lines)
- `archived/ADVERSARIAL_TESTING_GUIDE.md` - Detailed test suite guide (1382 lines)
- `archived/TEMPLATE_XSS_ADVERSARIAL_COMPLETE.md` - Template/XSS guide (882 lines)

**Security Documentation**:
- `SECURITY_COMPREHENSIVE.md` - Main security guide
- `SECURITY_GAP_ANALYSIS.md` - Implementation status
- `SECURITY_AND_PERFORMANCE_REVIEW.md` - Deep technical review

**Implementation**:
- `PHASE_8_IMPLEMENTATION_CHECKLIST.md` - Current status (95% complete)
- `TOKEN_VIEW_CANONICALIZATION.md` - Token view pattern guide

**CI/CD**:
- `CI_CD_INTEGRATION.md` - Complete CI/CD integration guide

---

**Last Updated**: 2025-10-15
**Status**: Production-ready, all 9 corpora operational
**Coverage**: 10/10 vulnerabilities, 100% coverage achieved
