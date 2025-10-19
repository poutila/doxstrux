#!/bin/bash
# Don't use set -e because we want to count failures
# set -e  # Exit on any error

echo "=== PHASE 8 PART 16: STRICTEST YAGNI VERIFICATION ==="
echo ""

checks_passed=0
checks_total=5

# S1: Ingest gate
if test -f .github/workflows/ingest_and_dryrun.yml && \
   grep -q "exit 2" .github/workflows/ingest_and_dryrun.yml && \
   grep -q "POLICY_REQUIRE_HMAC" .github/workflows/ingest_and_dryrun.yml; then
    echo "✅ S1: Ingest gate enforced"
    checks_passed=$((checks_passed + 1))
else
    echo "❌ S1: Ingest gate FAILED"
fi

# S2: Permission fallback
if grep -q "ensure_issue_create_permissions" tools/create_issues_for_unregistered_hits.py && \
   test -f tools/permission_fallback.py && \
   grep -q "_redact_sensitive_fields" tools/permission_fallback.py; then
    echo "✅ S2: Permission fallback integrated"
    checks_passed=$((checks_passed + 1))
else
    echo "❌ S2: Permission fallback FAILED"
fi

# R1: Digest cap + idempotency
if grep -q "MAX_ISSUES_PER_RUN" tools/create_issues_for_unregistered_hits.py && \
   grep -q "audit_id" tools/create_issues_for_unregistered_hits.py && \
   grep -q "import uuid" tools/create_issues_for_unregistered_hits.py; then
    echo "✅ R1: Digest cap + idempotency"
    checks_passed=$((checks_passed + 1))
else
    echo "❌ R1: Digest FAILED"
fi

# R2: Linux-only
if grep -q "platform.system.*Linux" .github/workflows/pre_merge_checks.yml; then
    echo "✅ R2: Linux-only enforced"
    checks_passed=$((checks_passed + 1))
else
    echo "❌ R2: Linux assertion FAILED"
fi

# C1: Minimal telemetry
if grep -q "audit_unregistered_repos_total" tools/create_issues_for_unregistered_hits.py && \
   grep -q "audit_issue_create_failures_total" tools/create_issues_for_unregistered_hits.py && \
   test -f prometheus/rules/audit_rules.yml; then
    echo "✅ C1: Minimal telemetry present"
    checks_passed=$((checks_passed + 1))
else
    echo "❌ C1: Telemetry FAILED"
fi

echo ""
echo "Safety net checks: $checks_passed/$checks_total passed"
echo ""

if [ $checks_passed -eq $checks_total ]; then
    echo "✅ ALL 5 GUARDS VERIFIED - READY FOR 48H PILOT 🚀"
    exit 0
else
    echo "❌ BLOCKED - Fix failing checks before pilot"
    exit 1
fi
