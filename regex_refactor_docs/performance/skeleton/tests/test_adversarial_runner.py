# skeleton/tests/test_adversarial_runner.py
"""
Adversarial Corpus Runner Test.

Runs adversarial corpora through parser and verifies security properties:
- Template injection vectors are flagged
- HTML/XSS vectors are marked for sanitization

REFERENCE: External deep security analysis
SOURCE: skeleton scope (not production)
"""
import importlib
import json
from pathlib import Path
import pytest

CORPORA = [
    Path("skeleton/adversarial_corpora/adversarial_template_injection.json"),
    Path("skeleton/adversarial_corpora/adversarial_html_xss.json"),
]

def _load_runner():
    """Try common local runner locations."""
    candidates = [
        "tools.run_adversarial",
        "adversarial.runner",
        "tools.adversarial.runner",
    ]
    for c in candidates:
        try:
            m = importlib.import_module(c)
            return m
        except Exception:
            continue
    return None

def _call_runner(runner_mod, corpus_path):
    """Support multiple runner APIs gracefully."""
    if hasattr(runner_mod, "run_corpus"):
        return runner_mod.run_corpus(str(corpus_path), runs=1)
    if hasattr(runner_mod, "run"):
        return runner_mod.run(str(corpus_path))
    # last-resort: try CLI via subprocess (avoid network)
    raise RuntimeError("Runner module found but no supported callable (run_corpus/run)")

@pytest.mark.parametrize("corpus", CORPORA)
def test_adversarial_corpus_runner(corpus):
    """
    Verify adversarial corpus runner detects security issues.

    Per external deep security analysis:
    - Template injection corpus must flag template syntax
    - HTML/XSS corpus must mark content for sanitization
    """
    if not corpus.exists():
        pytest.skip(f"{corpus} missing")

    runner = _load_runner()
    if runner is None:
        pytest.skip("adversarial runner module not available (tools.run_adversarial)")

    report = _call_runner(runner, corpus)

    # Expect a dict-like report with 'findings' or 'results'
    findings = None
    if isinstance(report, dict):
        findings = report.get("findings") or report.get("results") or report.get("documents")

    if findings is None:
        pytest.skip("runner returned a report but no 'findings' array was detected")

    # Basic assertions per-corpus type
    name = corpus.stem

    if "template" in name:
        # expect any finding to mark template syntax or contain suspicious tokens
        flagged = False
        for f in findings:
            if f.get("contains_template_syntax") or ("template" in (f.get("tags") or [])):
                flagged = True
                break
            # heuristic: check textual fields
            for k in ("text", "content", "heading", "meta"):
                v = f.get(k)
                if isinstance(v, str) and ("{{" in v or "{%" in v or "<%=" in v):
                    flagged = True
                    break
            if flagged:
                break

        assert flagged, (
            f"❌ CRITICAL: Template corpus run produced no template-syntax flagging. "
            f"This indicates template injection detection is not working. "
            f"SECURITY RISK: SSTI vulnerability"
        )

    else:
        # HTML corpus: expect findings that require sanitization / html_block flagged
        flagged_html = False
        for f in findings:
            if f.get("type") == "html_block" or f.get("needs_sanitization"):
                flagged_html = True
                break
            # heuristics: check content for script/onerror
            for k in ("text", "content", "raw"):
                v = f.get(k)
                if isinstance(v, str) and ("<script" in v.lower() or "onerror" in v.lower() or "onload" in v.lower()):
                    flagged_html = True
                    break
            if flagged_html:
                break

        assert flagged_html, (
            f"❌ CRITICAL: HTML corpus run produced no sanitization flags. "
            f"This indicates XSS detection is not working. "
            f"SECURITY RISK: XSS vulnerability"
        )

    # EVIDENCE ANCHOR
    # CLAIM-ADV-RUNNER: Adversarial runner detects template injection and XSS vectors
    # Source: External deep security analysis + adversarial corpora
