# Fuzz Testing Pattern for Parser

**Version**: 1.0
**Date**: 2025-10-17
**Status**: Optional enhancement (implement only if crashes/hangs found)
**Source**: PLAN_CLOSING_IMPLEMENTATION_extended_2.md P2-4 + External review E.2
**Purpose**: Discover edge cases via randomized input generation

---

## Purpose

Discover edge cases via randomized input generation:
- **Parser crashes**: Unhandled exceptions
- **Parser hangs**: Infinite loops
- **Memory exhaustion**: OOM conditions
- **Assertion failures**: Invariant violations

**When to use**: Only if crashes/hangs found in production or security audit requires fuzzing

---

## Fuzzing Tools

### Option 1: Hypothesis (Property-Based Testing)

**Recommended for**: Most use cases (pure Python, easy to integrate)

#### Basic Crash Test

```python
# FILE: tests/test_fuzz_parser.py

from hypothesis import given, strategies as st
import pytest
from doxstrux.markdown_parser_core import MarkdownParserCore

@given(st.text(min_size=0, max_size=10000))
def test_parser_never_crashes(markdown):
    """Parser should never crash on any text input."""
    try:
        parser = MarkdownParserCore(markdown)
        result = parser.parse()

        # Invariants that must hold
        assert isinstance(result, dict), "Result must be dict"
        assert "sections" in result, "Must have sections key"
        assert "links" in result, "Must have links key"
        assert "images" in result, "Must have images key"
        assert "paragraphs" in result, "Must have paragraphs key"

    except Exception as e:
        # Capture crash for investigation
        pytest.fail(f"Parser crashed on input: {repr(markdown)[:100]}\nError: {e}")
```

#### Structured Fuzzing (More Targeted)

```python
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
    assert isinstance(result["sections"], list)

@given(st.lists(st.text(min_size=0, max_size=100), min_size=0, max_size=50))
def test_lists_never_crash(items):
    """Lists extractor should handle any number of items."""
    markdown = "\n".join(f"- {item}" for item in items)
    parser = MarkdownParserCore(markdown)
    result = parser.parse()

    # Should complete without crash
    assert "lists" in result
    assert isinstance(result["lists"], list)

@given(
    st.text(min_size=0, max_size=200),
    st.text(min_size=0, max_size=200)
)
def test_links_never_crash(text, url):
    """Links extractor should handle any text/URL."""
    markdown = f"[{text}]({url})"
    parser = MarkdownParserCore(markdown)
    result = parser.parse()

    # Should complete without crash
    assert "links" in result
    assert isinstance(result["links"], list)
```

#### Running Hypothesis Tests

```bash
# Basic run (100 examples per test)
.venv/bin/python -m pytest tests/test_fuzz_parser.py

# Extended run (10,000 examples per test)
.venv/bin/python -m pytest tests/test_fuzz_parser.py \
  --hypothesis-show-statistics \
  --hypothesis-seed=12345 \
  -v

# CI profile (1,000 examples, faster)
.venv/bin/python -m pytest tests/test_fuzz_parser.py \
  --hypothesis-profile=ci
```

#### Hypothesis Configuration

```python
# FILE: conftest.py

from hypothesis import settings, HealthCheck

# Custom profiles
settings.register_profile("dev", max_examples=100, deadline=500)
settings.register_profile("ci", max_examples=1000, deadline=1000)
settings.register_profile("thorough", max_examples=10000, deadline=5000)

# Suppress health checks that are too strict
settings.register_profile(
    "permissive",
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much]
)
```

---

### Option 2: AFL/LibFuzzer (Advanced)

**Recommended for**: C extensions, performance-critical code, or when hypothesis isn't sufficient

#### Atheris Setup (Python-friendly AFL)

```python
# FILE: fuzz_targets/fuzz_parser.py

import atheris
import sys
from doxstrux.markdown_parser_core import MarkdownParserCore


def TestOneInput(data):
    """Fuzz target for AFL/LibFuzzer."""
    try:
        markdown = data.decode("utf-8", errors="ignore")
        parser = MarkdownParserCore(markdown)
        result = parser.parse()

        # Validate invariants
        assert isinstance(result, dict)
        assert "sections" in result

    except Exception:
        # Expected for malformed input - don't crash fuzzer
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
```

#### Running AFL Fuzzing

```bash
# Install atheris
.venv/bin/pip install atheris

# Run fuzzer (10 minutes)
.venv/bin/python fuzz_targets/fuzz_parser.py -max_total_time=600

# With corpus seeding
.venv/bin/python fuzz_targets/fuzz_parser.py \
  fuzz_corpus/ \
  -max_total_time=3600  # 1 hour
```

---

## Fuzzing Corpus Seeding

**Seed fuzzer with known-good inputs** to guide mutation:

```
fuzz_corpus/
├── seed_001_basic.md         # Basic markdown
├── seed_002_tables.md        # Tables
├── seed_003_nested_lists.md  # Complex nesting
├── seed_004_unicode.md       # Unicode edge cases
├── seed_005_large.md         # Large document (50KB)
├── seed_006_empty.md         # Empty file
├── seed_007_malformed.md     # Known malformed input
└── seed_008_xss.md           # XSS payloads
```

**Fuzzer behavior**:
- Loads seeds from corpus directory
- Mutates seeds (bit flips, byte insertions, etc.)
- Discovers new crashes/hangs

**Example seed (unicode edge cases)**:
```markdown
# seed_004_unicode.md

# Heading with emoji 🚀
- List with RTL text: مرحبا
- Zero-width characters: ​‌‍
- Confusables: АВС (Cyrillic)
- BiDi overrides: ‮reversed‬
```

---

## Integration with CI

### GitHub Actions Workflow (Nightly)

```yaml
# FILE: .github/workflows/fuzz.yml

name: Fuzz Testing

on:
  schedule:
    - cron: '0 2 * * *'  # 2am daily
  workflow_dispatch:      # Manual trigger

jobs:
  fuzz-hypothesis:
    runs-on: ubuntu-latest
    timeout-minutes: 60

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
          .venv/bin/pip install hypothesis

      - name: Run hypothesis fuzzing
        run: |
          .venv/bin/python -m pytest \
            tests/test_fuzz_parser.py \
            --hypothesis-profile=thorough \
            --timeout=3600  # 1 hour max

      - name: Upload crash artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: fuzz-failures
          path: .hypothesis/

  fuzz-afl:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"
          .venv/bin/pip install atheris

      - name: Run AFL fuzzing
        run: |
          .venv/bin/python fuzz_targets/fuzz_parser.py \
            fuzz_corpus/ \
            -max_total_time=7200  # 2 hours

      - name: Upload crash corpus
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: afl-crashes
          path: fuzz_corpus/crashes/
```

---

## When to Implement

### Required Conditions (ALL must be met)

**ONLY if**:
1. ✅ Parser crashes found in production
2. ✅ Parser hangs found in production
3. ✅ Security audit requires fuzzing
4. ✅ Tech Lead approves effort (~6 hours)

### Do NOT Implement If:

**YAGNI violations**:
- ❌ Speculatively (without known robustness issues)
- ❌ No crashes/hangs in production
- ❌ Part of skeleton work (production-only concern)
- ❌ No security audit requirement

**Rationale**: Fuzzing is time-intensive and requires ongoing maintenance (corpus updates, CI integration, crash triage)

---

## Crash Triage Process

### When Fuzzing Finds a Crash

**Step 1: Reproduce crash**
```bash
# Hypothesis saves failing examples in .hypothesis/
.venv/bin/python -m pytest tests/test_fuzz_parser.py --hypothesis-seed=<seed>
```

**Step 2: Minimize crashing input**
```python
# Hypothesis auto-minimizes, or manually:
from hypothesis import given, example, seed

@given(st.text())
@seed(12345)  # Use failing seed
def test_reproduce_crash(markdown):
    parser = MarkdownParserCore(markdown)
    result = parser.parse()  # Crashes here
```

**Step 3: Create regression test**
```python
def test_regression_crash_issue_123():
    """Regression test for fuzzing crash (issue #123)."""
    # Minimized crashing input
    markdown = "specific\ncrashing\ninput"

    # Should not crash after fix
    parser = MarkdownParserCore(markdown)
    result = parser.parse()

    assert isinstance(result, dict)
```

**Step 4: Fix root cause**
- Add input validation
- Fix infinite loop
- Handle edge case

**Step 5: Verify fix**
```bash
# Re-run fuzzer to confirm fix
.venv/bin/python -m pytest tests/test_fuzz_parser.py --hypothesis-seed=<seed>
```

---

## Recommended Approach

### Current

**Skip fuzzing** (YAGNI compliant)

**Rationale**:
- No known crashes/hangs in production
- No security audit requirement
- Parser has extensive unit tests (542 test cases)
- Adversarial corpora already test edge cases

### Future

**If crashes/hangs discovered**:
1. Add hypothesis tests (2 hours)
2. Integrate into nightly CI (1 hour)
3. Set up corpus seeding (1 hour)
4. Triage and fix crashes (variable)

**Total effort**: ~6 hours + crash triage time

---

## Testing Strategy

### Invariant Checks

**Define parser invariants** that must always hold:

```python
def check_parser_invariants(result: dict):
    """Verify parser output invariants."""
    assert isinstance(result, dict), "Result must be dict"

    # Required keys
    required_keys = ["sections", "links", "images", "paragraphs", "lists"]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
        assert isinstance(result[key], list), f"{key} must be list"

    # Sections must have valid structure
    for section in result["sections"]:
        assert "id" in section, "Section missing id"
        assert "title" in section, "Section missing title"
        assert isinstance(section.get("start_line"), (int, type(None)))
        assert isinstance(section.get("end_line"), (int, type(None)))

    # Links must have href
    for link in result["links"]:
        assert "href" in link, "Link missing href"

    # Images must have src
    for image in result["images"]:
        assert "src" in image, "Image missing src"
```

### Coverage-Guided Fuzzing

**Use hypothesis to maximize code coverage**:

```python
from hypothesis import given, strategies as st, settings

@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=10000))
@settings(max_examples=10000)
def test_parser_coverage(markdown):
    """Maximize code coverage via fuzzing."""
    parser = MarkdownParserCore(markdown)
    result = parser.parse()
    check_parser_invariants(result)
```

**Measure coverage**:
```bash
.venv/bin/python -m pytest tests/test_fuzz_parser.py \
  --cov=src/doxstrux \
  --cov-report=html
```

---

## References

- **External review E.2**: Fuzz testing gap analysis
- **PLAN_CLOSING_IMPLEMENTATION_extended_2.md**: P2-4 specification (lines 503-702)
- **Hypothesis documentation**: https://hypothesis.readthedocs.io/
- **Atheris documentation**: https://github.com/google/atheris

---

## Evidence Anchors

| Claim ID | Statement | Evidence | Status |
|----------|-----------|----------|--------|
| CLAIM-P2-4-DOC | Fuzz testing pattern documented | This file | ✅ Complete |
| CLAIM-P2-4-HYPOTHESIS | Hypothesis pattern provided | Option 1 section | ✅ Complete |
| CLAIM-P2-4-AFL | AFL/LibFuzzer pattern provided | Option 2 section | ✅ Complete |
| CLAIM-P2-4-CI | CI integration pattern provided | Integration with CI section | ✅ Complete |
| CLAIM-P2-4-YAGNI | YAGNI conditions explicit | When to Implement section | ✅ Complete |

---

**Document Status**: Complete
**Last Updated**: 2025-10-17
**Version**: 1.0
**Recommended Approach**: Skip fuzzing (YAGNI - no known crashes/hangs)
**Approved By**: Pending Human Review
**Next Review**: If/when crashes/hangs discovered in production
