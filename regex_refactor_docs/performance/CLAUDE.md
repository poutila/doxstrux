CLAUDE.md – Performance Folder Scope

Version: 1.0
Date: 2025-10-16
Purpose: Define clear boundaries for Phase 8 security hardening work in this directory

⚠️ CRITICAL – WORK SCOPE

ALL work happens in this directory:

✅ /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/regex_refactor_docs/performance/

This is the skeleton/reference implementation for Phase 8 security hardening

Goal: Create drop-in refactor plan (complete, tested, documented)

Contains: skeleton code, tests, docs, adversarial corpora, completion reports

Exception for testing verification (READ-ONLY):

✅ /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/

Can use existing test runners for verification only

NO modifications to tools/ allowed without explicit human approval

OFF LIMITS (NEVER modify without explicit human approval):

❌ /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/src/doxstrux/ (production code – separate CLAUDE.md protects this)

❌ /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tests/ (production tests)

❌ /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/baseline_outputs/ (frozen baselines – see below)

❌ /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/test_mds/ (test corpus – see below)

❌ Any directory outside performance/ (except read-only access to tools/)

⚠️ CRITICAL – PYTHON ENVIRONMENT

NEVER use system python (python, python3) – ALWAYS use .venv/bin/python:

System python is OFF LIMITS because it lacks required dependencies (mdit-py-plugins, etc.). Using system python produces silently incorrect results – the code runs but produces wrong output because optional dependencies fail silently.

Example of silent failure:

System python runs generate_baseline_outputs.py without errors

But mdit-py-plugins are missing, so tables/footnotes/tasklists are parsed incorrectly

Baselines are generated with wrong structure – CORRUPTED DATA

No error thrown – failure is silent and undetectable until parity tests fail

CORRECT usage (ALWAYS):

.venv/bin/python tools/generate_baseline_outputs.py
.venv/bin/python tools/baseline_test_runner.py
.venv/bin/python tools/ci/ci_gate_parity.py
.venv/bin/python -m pytest regex_refactor_docs/performance/skeleton/tests/ -v


WRONG usage (NEVER):

python3 tools/generate_baseline_outputs.py  # ❌ Creates corrupted baselines
python tools/baseline_test_runner.py        # ❌ Wrong test results
pytest skeleton/tests/                      # ❌ May use wrong python


Additional Constraints:

PYTHONPATH is not allowed – Do not set PYTHONPATH as it can cause import conflicts

Use editable install – Always install with pip install -e . from .venv

Verify environment – Run .venv/bin/python --version to confirm Python 3.12+

⚠️ CRITICAL – IMMUTABLE DIRECTORIES

NEVER EDIT without explicit human approval:

1. /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/baseline_outputs/

Contains frozen baseline JSON files (542 files)

Ground truth for regression testing

ANY modification breaks parity testing

MUST be generated with .venv/bin/python ONLY

To regenerate: Requires completed phase + human approval

2. /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/test_mds/

Contains test markdown files (542 files)

Test corpus for parser validation

Modifications invalidate all baselines

Changes require human approval only

3. /home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/tools/mds.zip

Compressed backup of test corpus

Do not modify or regenerate

These directories are read-only. Ask for human approval before ANY changes.

Drop-In Refactor Plan Goal

The skeleton in regex_refactor_docs/performance/ must be:

Complete – All Phase 8 security hardening implemented per CLOSING_IMPLEMENTATION.md

Tested – All 62 test functions passing with .venv/bin/python

Documented – All P0/P1/P2 tasks completed with evidence anchors

Reference – Ready to copy to production when human approves migration

Production code in src/ remains untouched until human migration decision.

This is a reference implementation that demonstrates:

Security hardening (URL normalization, HTML sanitization, caps, etc.)

Test infrastructure (62 tests, 9 adversarial corpora, CI/CD)

Documentation (policies, implementation reports, completion artifacts)

Human will review and decide when/how to migrate to production.

Allowed Operations in performance/
File Creation/Editing (✅ ALLOWED)

✅ Create/edit files in skeleton/doxstrux/

✅ Create/edit files in skeleton/tests/

✅ Create/edit files in docs/

✅ Create/edit files in adversarial_corpora/

✅ Create/edit files in archived/ (for completed work)

✅ Create status/completion reports (*.md files)

Testing (✅ ALLOWED with correct python)

✅ Run tests with .venv/bin/python -m pytest skeleton/tests/

✅ Run specific tests with .venv/bin/python -m pytest skeleton/tests/test_*.py -v

✅ Read files from tools/ for verification (READ-ONLY)

Documentation (✅ ALLOWED)

✅ Create implementation reports

✅ Update CLOSING_IMPLEMENTATION.md status

✅ Create policy documents (ALLOW_RAW_HTML_POLICY.md, PLATFORM_SUPPORT_POLICY.md)

✅ Generate completion artifacts

Prohibited Operations (❌ NEVER)
Code Modifications

❌ Modify src/doxstrux/ (production code protected by separate CLAUDE.md)

❌ Modify tests/ (production tests)

❌ Modify files outside performance/ scope

Baseline/Corpus Modifications

❌ Modify tools/baseline_outputs/ (frozen baselines)

❌ Modify tools/test_mds/ (test corpus)

❌ Regenerate baselines without human approval

Environment/Execution

❌ Use system python (corrupts baselines, produces wrong results)

❌ Set PYTHONPATH (causes import conflicts)

❌ Run commands outside performance/ scope without approval

Phase 8 Implementation Status

Current Phase: Phase 8 Security Hardening (Performance Optimization + Security)

Work Location: All in regex_refactor_docs/performance/

Completion Tracking:

CLOSING_IMPLEMENTATION.md – Master implementation plan

SECURITY_IMPLEMENTATION_STATUS.md – Security status (62 tests)

P0_TASKS_IMPLEMENTATION_COMPLETE.md – P0 progress report

PHASE_8_IMPLEMENTATION_CHECKLIST.md – Overall checklist

Goal: Complete all P0/P1/P2 tasks, verify all 62 tests pass, document for human review

Quick Reference Commands
Testing (ALWAYS use .venv/bin/python)
# Run all skeleton tests
.venv/bin/python -m pytest regex_refactor_docs/performance/skeleton/tests/ -v

# Run specific test file
.venv/bin/python -m pytest skeleton/tests/test_url_normalization_parity.py -v

# Run with coverage
.venv/bin/python -m pytest skeleton/tests/ --cov=skeleton/doxstrux --cov-report=term-missing

Verification (READ-ONLY access to tools/)
# Verify baseline parity (if needed)
.venv/bin/python tools/baseline_test_runner.py --test-dir tools/test_mds --baseline-dir tools/baseline_outputs

# Check Python version
.venv/bin/python --version

Documentation
# Create completion report
# (just write markdown files in performance/)

# Update status docs
# (edit CLOSING_IMPLEMENTATION.md, SECURITY_IMPLEMENTATION_STATUS.md)

Emergency Stop Conditions

STOP immediately and ask for human guidance if:

❌ Any command requires modifying src/doxstrux/

❌ Any test requires modifying tools/baseline_outputs/

❌ System python is the only available option

❌ PYTHONPATH needs to be set

❌ Baseline parity tests fail unexpectedly

❌ Scope extends outside performance/ folder

❌ Emergent blocker detected (any new ambiguity, missing component, or contradiction discovered mid-execution — even if not documented yet)

In these cases: Document the blocker, explain the issue, and wait for human decision.

⚖️ Golden CoT Enforcement – Clean Table Rule

Rule ID: CLEAN_TABLE_RULE
Source: CHAIN_OF_THOUGHT_GOLDEN_ALL_IN_ONE.json §governance.stop_on_ambiguity
Linked Principles: KISS, YAGNI, fail-closed, reflection_loop_required

Directive:
Absolutely no progression is allowed if any obstacle, ambiguity, or missing piece exists.
Every uncertainty must be resolved immediately, not postponed.
All reasoning and implementation must occur on a clean table — meaning:

No unverified assumptions

No TODOs or speculative placeholders

No skipped validation

No unresolved warnings or test failures

Proceeding with partial or ambiguous work violates Golden CoT stop rules and triggers an automatic STOP_CLARIFICATION_REQUIRED condition.

Emergent Blockers Clause (NEW):
If a new blocker appears at any time (during analysis or execution), it must be addressed immediately, even if it is not mentioned in existing documentation or requirements.
Do not defer. Treat Clean Table as a real-time invariant: fix the blocker now, then update documentation and tests accordingly.

AI Assistant Behavior:

Fail-closed: If anything is unclear, incomplete, or contradictory → stop and request clarification.

Sequential progression: Next task begins only after all blockers are resolved and validated.

Validation check: Confidence ≥ 0.8, schema validation passes, all tests green.

Reflection required: If confidence below threshold, trigger reflection loop before retrying.

No speculative deferrals: Simpler, complete, and verified now beats clever but deferred fixes (KISS + YAGNI compliance).

Rationale:

Prevents propagation of half-baked or uncertain logic.

Enforces Golden-only reasoning discipline (stop_on_ambiguity=true).

Aligns with Code Quality simplicity and necessity principles.

Ensures every phase is stable, evidence-backed, and production-ready before migration.

Rationale

Why this scope?

Drop-in refactor: Human wants complete, tested reference implementation to review

No production risk: Changes isolated to performance/ until human approves migration

Evidence-based: All work traceable via completion reports and test results

YAGNI compliant: Only implement what's in CLOSING_IMPLEMENTATION.md spec

Safe rollback: If something breaks, performance/ can be deleted with no production impact

Production code is safe: src/doxstrux/ has its own CLAUDE.md protection and is not modified during this phase.

Last Updated: 2025-10-16
Owner: Performance/Security Teams
Review Cycle: After all P0/P1/P2 tasks complete
Migration Decision: Human approval required

Related Documentation

CLOSING_IMPLEMENTATION.md – Master implementation plan (P0/P1/P2 tasks)

SECURITY_IMPLEMENTATION_STATUS.md – Security status (62 tests, 9 corpora)

P0_TASKS_IMPLEMENTATION_COMPLETE.md – P0 progress report

PHASE_8_IMPLEMENTATION_CHECKLIST.md – Overall Phase 8 tracking

skeleton/README.md – Reference implementation guide

Remember: Everything stays in performance/ until human reviews and approves migration to production.
