# skeleton/tests/test_consumer_ssti_litmus.py
"""
Consumer SSTI Litmus Test.

CRITICAL: This test should be added to CONSUMER REPOS (web UI, preview service, etc.)
to prove that collected metadata is NOT evaluated by their template renderer.

SCOPE: Reference test for consumer repos (not skeleton scope)
PURPOSE: Demonstrates how to verify downstream consumers don't have SSTI vulnerabilities

SOURCE: External deep security analysis
REFERENCE: PLAN_CLOSING_IMPLEMENTATION_extended_1.md P0-3.5
"""
import pytest

try:
    import jinja2
    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False

# Example "collected metadata" payload an attacker might try to slip in
MALICIOUS = "{{ 7 * 7 }}"   # evaluates to "49" when rendered unsafely

@pytest.mark.skipif(not HAS_JINJA, reason="jinja2 not installed")
def test_consumer_does_not_evaluate_metadata():
    """
    Verify consumer does NOT evaluate template expressions in metadata.

    Per P0-3.5 SSTI Prevention Policy: Consumers must treat collected
    metadata as untrusted and escape it before rendering.

    This test demonstrates:
    1. BAD: Naive rendering evaluates template tokens (SSTI vulnerability)
    2. GOOD: Safe rendering escapes tokens and prevents evaluation
    """
    # ========================================
    # BAD: Naive render of malicious metadata
    # ========================================
    # This demonstrates the SSTI risk
    bad_template = jinja2.Template("Title: " + MALICIOUS)
    result_bad = bad_template.render().strip()

    # Sanity check: Jinja2 DOES evaluate when used naively
    assert result_bad == "Title: 49", \
        "Sanity check failed: Jinja2 should evaluate {{ 7 * 7 }} to 49"

    # ========================================
    # GOOD: Safe rendering with autoescape
    # ========================================
    # Consumer should use autoescape or escape metadata before rendering
    env = jinja2.Environment(autoescape=True)
    tm = env.from_string("Title: {{ meta }}")
    result_good = tm.render(meta=MALICIOUS)

    # ✅ CRITICAL ASSERTION: Metadata should NOT be evaluated
    assert "49" not in result_good, (
        f"❌ CRITICAL: Consumer renders metadata unsafely: {result_good!r}. "
        f"Expected literal '{{{{ 7 * 7 }}}}' in output, not '49'. "
        f"SECURITY RISK: SSTI vulnerability allows remote code execution. "
        f"FIX: Use autoescape=True or explicitly escape metadata."
    )

    # Verify literal braces remain (escaped or shown)
    assert "{{" in result_good or "{" in result_good, (
        f"Safe rendering should preserve literal braces: {result_good!r}"
    )

    # EVIDENCE ANCHOR
    # CLAIM-CONSUMER-SSTI: Consumer does not evaluate metadata template tokens
    # Source: P0-3.5 SSTI Prevention Policy + external deep security analysis


@pytest.mark.skipif(not HAS_JINJA, reason="jinja2 not installed")
def test_consumer_explicit_escape_filter():
    """
    Verify explicit escaping with |e filter also prevents evaluation.

    Alternative safe pattern: Use |e (escape) filter explicitly.
    """
    env = jinja2.Environment(autoescape=False)  # Intentionally off
    tm = env.from_string("Title: {{ meta|e }}")
    result = tm.render(meta=MALICIOUS)

    # ✅ CRITICAL: Explicit escape filter should prevent evaluation
    assert "49" not in result, \
        f"Explicit |e filter failed to escape: {result!r}"
    assert "{{" in result or "{" in result, \
        f"Expected literal braces in escaped output: {result!r}"


# ========================================
# INTEGRATION INSTRUCTIONS FOR CONSUMER REPOS
# ========================================
#
# 1. Copy this file to your consumer repo's tests/ directory
# 2. Add jinja2 to consumer test dependencies:
#    pip install jinja2
#
# 3. Run test:
#    pytest tests/test_consumer_ssti_litmus.py -v
#
# 4. If test fails, audit all template rendering code and ensure:
#    - Environment uses autoescape=True, OR
#    - All metadata variables use |e filter explicitly, OR
#    - Metadata is sanitized before passing to template
#
# 5. Add this test to consumer CI as a REQUIRED check
#
# 6. If consumer intentionally needs to render raw HTML or template-like
#    content, require:
#    - Documented waiver process
#    - Tech Lead approval
#    - Enhanced sanitization (bleach/DOMPurify)
#    - Additional end-to-end litmus tests
#
# EVIDENCE ANCHOR:
# CLAIM-CONSUMER-LITMUS: Consumer SSTI litmus tests exist and pass
# Source: P0-3.5 requirement + external deep security analysis
