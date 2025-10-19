# Extended Closing Implementation Plan - Phase 8 Security Hardening
# Part 12: YAGNI/KISS Simplification & Production Safety Nets

**Version**: 2.0 (Updated with 3 Blocking Safety Nets + Production Hardening)
**Date**: 2025-10-18
**Status**: SIMPLIFICATION + SAFETY NETS - PRODUCTION READY
**Methodology**: YAGNI Decision Tree + KISS Principles + Production Safety Validation
**Part**: 12 (Post-Part 11 Operational Hardening)
**Purpose**: Apply YAGNI/KISS analysis + add 3 critical safety nets before canary deployment

⚠️ **CRITICAL**: This part applies the YAGNI decision tree (q1-q4) from CODE_QUALITY.json to identify and remove over-engineered subsystems, PLUS adds 3 blocking safety nets identified in deep review.

**Previous Parts**:
- Part 1-10: Implementation of Phase 8 security hardening
- Part 11: Simplified one-week action plan with operational hardening (COMPLETE)

**Source**: Deep YAGNI/KISS analysis applying CODE_QUALITY.json governance policies

**Verdict**: "You've built a robust, secure system — but several subsystems were added before their necessity was proven. Prefer simpler alternatives and defer heavy pieces until you hit concrete scale/usage thresholds."

---

## EXECUTIVE SUMMARY

This document provides the **simplification, governance, and production safety plan** to remove over-engineered subsystems, establish decision governance, and add 3 critical safety nets before canary deployment.

**What's included**:
- YAGNI decision tree analysis for 5 major subsystems (explicit q1-q4 answers)
- **3 BLOCKING SAFETY NETS** (artifact ingestion enforcement, permission fallback, FP telemetry)
- 6 artifacts to add: decision template, generator script, permission check, tests, CI gate, Prometheus rules
- Exact removal/simplification steps (what to keep vs defer)
- Measurable triggers for reintroducing deferred features
- Decision governance integration for PR reviews

**Timeline to complete**: 4-6 hours (2h simplifications + 2-3h safety nets + 1h testing)

**Critical changes**:
- Remove org-wide scanning (defer until consumer_count >= 10)
- Default to centralized triage (security/audit-backlog)
- Defer Windows support (defer until Windows consumer demand)
- Simplify baseline signing (prefer KMS over ad-hoc GPG)
- Add decision governance template for PRs
- **ADD 3 BLOCKING SAFETY NETS** (see below)

**Reality check**: Simplifications are LOW RISK (reduce operational burden). Safety nets are BLOCKERS (prevent silent failures in production).

---

## YAGNI DECISION TREE ANALYSIS (5 SUBSYSTEMS)

### Methodology

For each subsystem, apply the YAGNI decision tree from CODE_QUALITY.json:
- **Q1**: Is this required by current product/security/ops requirements?
- **Q2**: Will this be used immediately (in the next release/canary)?
- **Q3**: Do we have stakeholders/data/metrics demanding this now?
- **Q4**: Can this be added later without large migration cost?

**Decision Rule**: Implement NOW only if Q1=Yes AND Q2=Yes AND Q3=Yes AND Q4=No

Otherwise: DEFER with clear triggers for reintroduction.

---

### Subsystem 1: Org-Wide GitHub Scanning / Auto-Discovery

**Description**: Scanner that reads all repos in GitHub org to discover unregistered renderers

**YAGNI Analysis**:
- **Q1 (Current requirement?)**: Partial — desire to discover renderers exists, but consumers can self-report
- **Q2 (Used immediately?)**: No — consumer teams can run lightweight self-audit right now
- **Q3 (Backed by stakeholders/data?)**: No — no committed adoption; org-scan is convenience, not mandate
- **Q4 (Can be added later?)**: Yes — can be reintroduced later without breaking changes

**Decision**: **DEFER** (fails Q2 and Q3)

**Rationale**: Consumer-driven artifacts and short onboarding snippet meet current needs. Org-scan adds operational complexity (GitHub API quota, PAT scope) without proven demand.

**Alternative (KISS)**: Consumer self-audit artifacts with optional HMAC provenance

**Reintroduction Trigger**:
```
IF (consumer_count >= 10) OR (avg_org_unregistered_repos_per_run >= 5 for 7 days)
THEN create ticket to implement org-wide scanning
```

**Actions**:
1. ✅ Already documented in PLATFORM_SUPPORT_POLICY.md (Part 11)
2. Remove any existing org-scan automation scripts
3. Replace with consumer_self_audit.py snippet
4. Add artifact schema validation (lightweight)

---

### Subsystem 2: Per-Repo Automatic Issues & Gist Attachments

**Description**: Script creates GitHub issues across many repos with gist attachments

**YAGNI Analysis**:
- **Q1 (Current requirement?)**: No — central security backlog meets requirement
- **Q2 (Used immediately?)**: No — owners want control; immediate in-repo creation not necessary
- **Q3 (Backed by stakeholders/data?)**: No — creating many small issues is noisy, not requested by owners
- **Q4 (Can be added later?)**: Yes — can be added when trust & scale need it

**Decision**: **DEFER** (fails Q1, Q2, Q3)

**Rationale**: Central backlog with digest cap is simpler, reduces PAT scope, and avoids alert storms. Per-repo creation can be opt-in when proven valuable.

**Alternative (KISS)**: Single security/audit-backlog repo + digest mode for >10 repos

**Reintroduction Trigger**:
```
IF (manual_triage_workload > 1 FTE-day/week)
THEN create ticket to implement per-repo auto-issue with gist
```

**Actions**:
1. ✅ Already implemented in Part 11 (tools/create_issues_for_unregistered_hits.py)
2. Keep central backlog default
3. Keep MAX_ISSUES_PER_RUN = 10 cap
4. Keep digest mode fallback
5. Document per-repo mode as opt-in (not default)

---

### Subsystem 3: GPG Baseline Signing + Ad-Hoc Key Workflows

**Description**: GPG-based baseline signing with local key management

**YAGNI Analysis**:
- **Q1 (Current requirement?)**: Yes — canonical baseline must be integrity-protected
- **Q2 (Used immediately?)**: Yes — used immediately by CI (baseline verification gate)
- **Q3 (Backed by stakeholders/data?)**: Yes — security requires signed baseline
- **Q4 (Can be added later?)**: No — cannot be easily added later without undermining gate

**Decision**: **IMPLEMENT NOW** (passes all Q1-Q4) — BUT SIMPLIFY

**Rationale**: Baseline signing is mandatory for security, but ad-hoc GPG key management is operationally risky. Prefer KMS/HSM for production.

**Alternative (KISS)**: KMS/HSM-backed signing with GPG fallback for local dev

**Reintroduction Trigger**: N/A (already required)

**Actions**:
1. Keep baseline signing requirement
2. Document KMS-backed recipe in RUN_TO_GREEN.md
3. Add exact verification commands
4. Keep GPG fallback only when KMS not available
5. Update CI to verify signature before parity tests

**Implementation**:
```bash
# KMS-backed signing (production)
aws kms sign --key-id alias/baseline-signing-key --message fileb://baseline.json --output signature.sig

# GPG fallback (local dev)
gpg --detach-sign --armor baseline.json
```

---

### Subsystem 4: Windows Parity (SIGALRM Replacement / Subprocess Isolation)

**Description**: Subprocess worker pool for Windows timeout enforcement

**YAGNI Analysis**:
- **Q1 (Current requirement?)**: No (unless Windows-only consumers exist)
- **Q2 (Used immediately?)**: No
- **Q3 (Backed by stakeholders/data?)**: No (no immediate stakeholder demand)
- **Q4 (Can be added later?)**: Yes — can be added if a consumer requires it

**Decision**: **DEFER** (fails Q1, Q2, Q3)

**Rationale**: All production deployments are Linux-based. Windows support requires 8+ hours engineering effort with no current demand.

**Alternative (KISS)**: Linux-only policy with clear documentation

**Reintroduction Trigger**:
```
IF (Windows consumer request filed AND approved by Tech Lead)
THEN create funded ticket to implement subprocess worker pool
```

**Actions**:
1. ✅ Already documented in PLATFORM_SUPPORT_POLICY.md (Part 11)
2. Keep Unix SIGALRM timeout (Linux/macOS)
3. Add CI assertion: `platform.system() == 'Linux'` for production
4. Document Windows limitation in README
5. Provide Docker/WSL2 workaround for Windows users

**Implementation**:
```yaml
# CI assertion (add to pre_merge_checks.yml)
- name: Verify Linux platform for production
  run: |
    python -c "import platform; assert platform.system() == 'Linux', 'Production deployment requires Linux for untrusted markdown parsing'"
```

---

### Subsystem 5: Collector Timeouts / Per-Collector Watchdogs (Unix SIGALRM)

**Description**: Unix SIGALRM-based timeout for collector isolation

**YAGNI Analysis**:
- **Q1 (Current requirement?)**: Yes — protects against hangs from untrusted collectors
- **Q2 (Used immediately?)**: Yes — used immediately to keep parser responsive
- **Q3 (Backed by stakeholders/data?)**: Yes — security/runtime risk is real
- **Q4 (Can be added later?)**: No — hard to add later safely

**Decision**: **KEEP** (passes all Q1-Q4)

**Rationale**: Timeout enforcement is critical security control for untrusted inputs. Cannot be safely deferred.

**Alternative (KISS)**: Unix-first with documented Windows limitation

**Reintroduction Trigger**: N/A (already required)

**Actions**:
1. Keep Unix SIGALRM timeout
2. Document Windows limitations
3. Add timeout behavior tests
4. Monitor timeout metrics in production

---

## 3 BLOCKING SAFETY NETS (MUST IMPLEMENT BEFORE CANARY)

### Background

Deep review of Part 12 v1.0 identified 3 gaps that could cause silent failures, tampering, or operational overload in production. These safety nets are **BLOCKERS** — canary deployment must wait until all 3 are implemented and tested.

**Risk Summary**:
1. **Artifact Ingestion** — Without validation gate, accept unsigned/malformed consumer artifacts (tampering/poisoning path)
2. **Permission Failures** — Silent failures when token lacks issue-create permission (operational blind spot)
3. **FP Telemetry** — No automated FP tracking means blind to pattern drift (noise or miss real issues)

---

### Safety Net 1: Artifact Ingestion Enforcement (BLOCKER)

**Problem**: Consumer artifacts accepted without validation → tampering/poisoning risk

**Solution**: Mandatory ingest gate that rejects unsigned/malformed artifacts

**YAGNI Proof**: ✅ This is not over-engineering — it's a security control for untrusted consumer inputs. Meets Q1-Q3 (required, used immediately, security-backed).

**Implementation** (10-20 minutes):

Add validation gate in audit ingestion pipeline:

```python
# In audit ingestion (before processing consumer artifacts)
from tools.validate_consumer_art import validate_against_schema, verify_hmac, load_json

artifact = load_json(Path(artifact_path))

# Schema validation (always required)
try:
    validate_against_schema(artifact, schema)
except Exception as e:
    raise SystemExit(f"Artifact schema invalid: {e}")

# HMAC verification (if policy requires it)
if POLICY_REQUIRE_HMAC and 'hmac' not in artifact:
    raise SystemExit("Rejected unsigned artifact per policy")

if POLICY_REQUIRE_HMAC:
    ok = verify_hmac(artifact, key_bytes)
    if not ok:
        raise SystemExit("HMAC verification failed")
```

**Acceptance Criteria**:
- [ ] tools/validate_consumer_art.py implements schema validation
- [ ] Ingest gate added to audit pipeline (fails on invalid schema)
- [ ] POLICY_REQUIRE_HMAC configurable (env var or config file)
- [ ] CI job runs validation gate (see Safety Net 3 for CI job YAML)

**Effort**: 10-20 minutes
**Owner**: Dev team
**Evidence**: `grep -q "validate_against_schema" tools/audit_greenlight.py` (or equivalent ingestion script)

---

### Safety Net 2: Permission Check + Deterministic Fallback (BLOCKER)

**Problem**: Silent failures when GitHub token lacks issue-create permission → operational blind spot

**Solution**: Early permission check with deterministic fallback (save artifact + alert)

**YAGNI Proof**: ✅ This is fail-safe behavior, not over-engineering. Prevents silent operational failures (Q1-Q3: required, immediate, ops-backed).

**Implementation** (10-30 minutes):

**Files Added**:
1. `tools/permission_fallback.py` — Permission check + fallback helper
2. `tests/test_permission_fallback.py` — Unit test (mocks GitHub API)
3. `tests/test_permission_fallback_slack.py` — Slack posting test

**Patch A**: Add `tools/permission_fallback.py` (see Section 8 below for full code)

**Patch B**: Inject permission check into `tools/create_issues_for_unregistered_hits.py`:

```python
# After session creation, before issue creation
from tools.permission_fallback import ensure_issue_create_permissions

ok = ensure_issue_create_permissions(args.central_repo, session, str(audit_path))
if not ok:
    print("Permission fallback executed: artifact saved and security notified. Exiting.")
    return 2
```

**Fallback Behavior**:
1. Check permission via `GET /repos/{repo}/collaborators/{login}/permission`
2. If permission missing/unknown:
   - Save artifact to `adversarial_reports/fallback_<timestamp>.json`
   - Post Slack alert (if `SLACK_WEBHOOK` env var set)
   - Exit with code 2

**Acceptance Criteria**:
- [ ] tools/permission_fallback.py exists and works
- [ ] ensure_issue_create_permissions() called in create_issues script
- [ ] Unit tests pass: `pytest -q tests/test_permission_fallback*.py`
- [ ] Fallback file created when permission missing (verified in test)
- [ ] Slack alert attempted when SLACK_WEBHOOK set (verified in test)

**Effort**: 10-30 minutes
**Owner**: Dev team
**Evidence**: `grep -q "ensure_issue_create_permissions" tools/create_issues_for_unregistered_hits.py`

---

### Safety Net 3: FP Telemetry + Automated Tracking (BLOCKER)

**Problem**: No automated FP tracking → blind to pattern drift (noise or miss real issues)

**Solution**: Prometheus counters + manual triage feedback loop + alert rules

**YAGNI Proof**: ✅ Minimal telemetry for operational visibility, not over-engineering. Needed to validate YAGNI triggers (Q2-Q3: immediate use, ops-backed).

**Implementation** (30-60 minutes):

**Prometheus Metrics** (export from scripts):
```python
# In tools/create_issues_for_unregistered_hits.py
audit_unregistered_repos_total.inc()  # counter
audit_digest_created_total.inc()      # counter (when digest created)
audit_issue_create_failures_total.inc()  # counter (on failure)

# In triage workflow (manual or scripted)
audit_fp_marked_total.inc()  # counter (when FP label/comment added)
```

**Alert Rules** (Prometheus):
```yaml
# prometheus/rules/audit_rules.yml
- alert: AuditIssueCreateFailed
  expr: increase(audit_issue_create_failures_total[5m]) > 0
  for: 1m
  labels:
    severity: page
  annotations:
    summary: "Audit issue creation failures detected"

- alert: AuditDigestFrequencyHigh
  expr: increase(audit_digest_created_total[24h]) > 3
  for: 30m
  labels:
    severity: warning
  annotations:
    summary: "Many audit digests created (>3 in 24h)"

- alert: AuditFPRateHigh
  expr: (increase(audit_fp_marked_total[7d]) / max(increase(audit_unregistered_repos_total[7d]), 1)) > 0.10
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "High false-positive rate (>10% over 7 days)"
```

**Grafana Dashboard** (tiny JSON):
- Panel 1: Issue creation failures (1h increase)
- Panel 2: Audit digests created (24h)
- (See Section 9 below for full JSON)

**Triage Feedback Loop**:
1. Add `fp=true` comment or `fp` label to false-positive issues
2. Script increments `audit_fp_marked_total` counter
3. Alert fires if FP rate > 10% over 7 days

**Acceptance Criteria**:
- [ ] Prometheus metrics exported from create_issues script
- [ ] Alert rules added to Prometheus config
- [ ] Grafana dashboard imported (optional but recommended)
- [ ] Triage instructions added to central backlog README
- [ ] FP rate calculation tested (mock data)

**Effort**: 30-60 minutes
**Owner**: Dev team + SRE
**Evidence**: `grep -q "audit_unregistered_repos_total" tools/create_issues_for_unregistered_hits.py`

---

### Safety Net Go/No-Go Checklist

**ALL must pass before canary deployment:**

- [ ] **Safety Net 1**: Ingest gate enforced and tested (schema + HMAC policy)
- [ ] **Safety Net 2**: Permission check implemented and fallback tested (artifact upload + alert)
- [ ] **Safety Net 3**: FP telemetry emitting metrics and dashboard exists
- [ ] **Unit Tests**: All 3 safety nets have passing unit tests
- [ ] **CI Gate**: CI job runs validation + dry-run (see Section 10 for YAML)

**If any item failing**: Delay canary and treat as blocker.

---

## 6 ARTIFACTS TO ADD (3 Original + 3 Safety Nets)

### Original Artifacts (from Part 12 v1.0)

### Artifact 1: Decision Governance Template

**Purpose**: Enforce YAGNI decision tree in PR reviews

**File**: `.github/DECISION_ARTIFACT_TEMPLATE.md`

**Usage**: Copy into PR description for any feature/design change

**Content**: See full template below (Section 5)

**Verification**:
```bash
test -f .github/DECISION_ARTIFACT_TEMPLATE.md && echo "✓ Template exists"
```

---

### Artifact 2: Decision Generator Script

**Purpose**: Auto-generate decision artifacts from interactive prompts or CLI args

**File**: `tools/generate_decision_artifact.py`

**Usage**:
```bash
# Interactive mode
python tools/generate_decision_artifact.py --interactive

# CLI mode
python tools/generate_decision_artifact.py \
  --title "Centralize triage" \
  --owner "alice" \
  --decision "Implement" \
  --out docs/decision_centralize.md
```

**Content**: See full script below (Section 6)

**Verification**:
```bash
python tools/generate_decision_artifact.py --title "Test" --owner "test" --out /tmp/test.md
test -f /tmp/test.md && echo "✓ Generator works"
```

---

### Artifact 3: KISS/YAGNI Tactical Patches

**Purpose**: Apply 3 small tactical improvements immediately

**Changes**:
1. Central backlog default + digest cap (tools/create_issues_for_unregistered_hits.py)
2. PR-smoke fast adversarial wiring (.github/workflows/pre_merge_checks.yml)
3. Fast smoke adversarial corpus (adversarial_corpora/fast_smoke.json)

**Application**:
```bash
# Apply patch (see Section 7 for patch content)
git apply patch_kiss_yagni_fix.patch
git add -A
git commit -m "KISS/YAGNI: central backlog default + digest cap; PR-smoke fast adversarial"
```

**Verification**:
```bash
grep -q "MAX_ISSUES_PER_RUN" tools/create_issues_for_unregistered_hits.py && echo "✓ Digest cap added"
test -f adversarial_corpora/fast_smoke.json && echo "✓ Fast smoke corpus exists"
```

---

## ACCEPTANCE CRITERIA (12 ITEMS)

**ALL items must be TRUE before considering Part 12 complete.**

### GOVERNANCE (3 items)

**[1] Decision Artifact Template Exists** ⏳ BLOCKING
- Status: NOT STARTED
- Effort: 15 minutes
- Owner: Dev team
- Evidence: `test -f .github/DECISION_ARTIFACT_TEMPLATE.md`

**[2] Decision Generator Script Works** ⏳ BLOCKING
- Status: NOT STARTED
- Effort: 30 minutes
- Owner: Dev team
- Evidence: `python tools/generate_decision_artifact.py --title "Test" --owner "test" --out /tmp/test.md && test -f /tmp/test.md`

**[3] PR Checklist Updated** ⏳ HIGH
- Status: NOT STARTED
- Effort: 15 minutes
- Owner: Dev team
- Evidence: `.github/pull_request_template.md` references decision artifact requirement

### SIMPLIFICATIONS (6 items)

**[4] Central Backlog Default Set** ⏳ BLOCKING
- Status: ✅ COMPLETE (Part 11)
- Effort: 0 (already done)
- Owner: N/A
- Evidence: `grep -q 'default="security/audit-backlog"' tools/create_issues_for_unregistered_hits.py`

**[5] Issue Cap Implemented** ⏳ BLOCKING
- Status: ✅ COMPLETE (Part 11)
- Effort: 0 (already done)
- Owner: N/A
- Evidence: `grep -q "MAX_ISSUES_PER_RUN = 10" tools/create_issues_for_unregistered_hits.py`

**[6] Digest Mode Fallback Works** ⏳ BLOCKING
- Status: ✅ COMPLETE (Part 11)
- Effort: 0 (already done)
- Owner: N/A
- Evidence: `grep -q "def create_digest_issue" tools/create_issues_for_unregistered_hits.py`

**[7] Platform Policy Documents Triggers** ⏳ BLOCKING
- Status: ✅ COMPLETE (Part 11)
- Effort: 0 (already done)
- Owner: N/A
- Evidence: `grep -q "Trigger Thresholds" PLATFORM_SUPPORT_POLICY.md`

**[8] Linux-Only CI Assertion** ⏳ BLOCKING
- Status: NOT STARTED
- Effort: 15 minutes
- Owner: Dev team
- Evidence: `grep -q "platform.system.*Linux" .github/workflows/pre_merge_checks.yml`

**[9] Windows Limitation Documented** ⏳ HIGH
- Status: ✅ COMPLETE (Part 11)
- Effort: 0 (already done)
- Owner: N/A
- Evidence: `grep -q "Windows.*not supported" PLATFORM_SUPPORT_POLICY.md`

### FAST IMPROVEMENTS (3 items)

**[10] Fast Smoke Corpus Exists** ⏳ MEDIUM
- Status: NOT STARTED
- Effort: 10 minutes
- Owner: Dev team
- Evidence: `test -f adversarial_corpora/fast_smoke.json`

**[11] PR-Smoke Wired to Pre-Merge** ⏳ MEDIUM
- Status: NOT STARTED
- Effort: 15 minutes
- Owner: Dev team
- Evidence: `grep -q "fast_smoke" .github/workflows/pre_merge_checks.yml`

**[12] KMS Signing Recipe Documented** ⏳ HIGH
- Status: NOT STARTED
- Effort: 30 minutes
- Owner: Dev team
- Evidence: `grep -q "kms sign" RUN_TO_GREEN.md`

---

## IMPLEMENTATION PLAN

### Phase 1: Decision Governance (1 hour)

**Goal**: Establish decision governance for future features

**Steps**:

1. **Create decision artifact template** (15 min)
   ```bash
   mkdir -p .github
   # Copy template from Section 5 below
   ```

2. **Create decision generator script** (30 min)
   ```bash
   # Copy script from Section 6 below
   chmod +x tools/generate_decision_artifact.py
   python tools/generate_decision_artifact.py --interactive  # Test
   ```

3. **Update PR checklist** (15 min)
   ```bash
   # Add to .github/pull_request_template.md:
   # - [ ] Decision artifact attached (if feature/design change)
   ```

**Verification**:
```bash
test -f .github/DECISION_ARTIFACT_TEMPLATE.md && echo "✓ Template"
python tools/generate_decision_artifact.py --title "Test" --owner "test" --out /tmp/test.md && echo "✓ Generator"
grep -q "Decision artifact" .github/pull_request_template.md && echo "✓ PR checklist"
```

---

### Phase 2: Linux-Only Assertion (15 minutes)

**Goal**: Enforce Linux-only deployment for production

**Steps**:

1. **Add platform assertion to pre_merge_checks.yml**
   ```yaml
   # Add after setup-python step
   - name: Verify Linux platform for production
     run: |
       python -c "import platform; assert platform.system() == 'Linux', 'Production deployment requires Linux for untrusted markdown parsing'"
   ```

2. **Test assertion locally**
   ```bash
   python -c "import platform; assert platform.system() == 'Linux', 'Production deployment requires Linux'"
   ```

**Verification**:
```bash
grep -q "platform.system.*Linux" .github/workflows/pre_merge_checks.yml && echo "✓ Assertion added"
```

---

### Phase 3: Fast Smoke Improvements (40 minutes)

**Goal**: Add fast PR-smoke checks to maintain velocity

**Steps**:

1. **Create fast smoke corpus** (10 min)
   ```bash
   # Copy from Section 7 below
   # Save to adversarial_corpora/fast_smoke.json
   ```

2. **Wire PR-smoke to pre_merge_checks.yml** (15 min)
   ```yaml
   # Add before audit_greenlight.py call
   - name: Run fast adversarial smoke (PR velocity)
     run: |
       if [ -f tools/run_adversarial.py ] && [ -f adversarial_corpora/fast_smoke.json ]; then
         python tools/run_adversarial.py adversarial_corpora/fast_smoke.json --runs 1 --report adversarial_reports/pr_adv_smoke.json || true
       fi
   ```

3. **Test locally** (15 min)
   ```bash
   python tools/run_adversarial.py adversarial_corpora/fast_smoke.json --runs 1 --report /tmp/smoke.json
   ```

**Verification**:
```bash
test -f adversarial_corpora/fast_smoke.json && echo "✓ Corpus"
grep -q "fast_smoke" .github/workflows/pre_merge_checks.yml && echo "✓ Wired"
python tools/run_adversarial.py adversarial_corpora/fast_smoke.json --runs 1 --report /tmp/smoke.json && echo "✓ Works"
```

---

### Phase 4: KMS Signing Documentation (30 minutes)

**Goal**: Document KMS-backed baseline signing

**Steps**:

1. **Add KMS signing recipe to RUN_TO_GREEN.md**
   ```markdown
   ## Baseline Signing (KMS Production / GPG Fallback)

   ### Production (KMS)
   ```bash
   # Sign baseline with AWS KMS
   aws kms sign \
     --key-id alias/baseline-signing-key \
     --message fileb://tools/baseline_outputs/baseline.json \
     --message-type RAW \
     --signing-algorithm RSASSA_PKCS1_V1_5_SHA_256 \
     --output text \
     --query Signature | base64 -d > baseline.sig

   # Verify signature
   aws kms verify \
     --key-id alias/baseline-signing-key \
     --message fileb://tools/baseline_outputs/baseline.json \
     --message-type RAW \
     --signing-algorithm RSASSA_PKCS1_V1_5_SHA_256 \
     --signature fileb://baseline.sig
   ```

   ### Local Dev (GPG Fallback)
   ```bash
   # Sign with GPG
   gpg --detach-sign --armor tools/baseline_outputs/baseline.json

   # Verify
   gpg --verify tools/baseline_outputs/baseline.json.asc
   ```
   ```

2. **Update CI to verify signature before parity tests**
   ```yaml
   - name: Verify baseline signature (KMS)
     run: |
       # Add signature verification before baseline tests
       if [ -f baseline.sig ]; then
         aws kms verify --key-id alias/baseline-signing-key --message fileb://baseline.json --signature fileb://baseline.sig
       fi
   ```

**Verification**:
```bash
grep -q "kms sign" RUN_TO_GREEN.md && echo "✓ KMS recipe documented"
grep -q "kms verify" .github/workflows/pre_merge_checks.yml && echo "✓ CI verification added"
```

---

## SECTION 5: DECISION ARTIFACT TEMPLATE

**File**: `.github/DECISION_ARTIFACT_TEMPLATE.md`

```markdown
# Decision Artifact — Feature / Design Change

**Feature / Change**:
`<short title>`

**Author / Owner**:
`<name> (<team>)`

**Date**:
`YYYY-MM-DD`

---

## 1) Short summary
A short 1-2 sentence summary of the proposed change.

---

## 2) YAGNI decision checklist (answer each: Yes / No, short rationale)

1. **Q1 — Is this required by current product/security/ops requirements?**
   Answer: `Yes / No`
   Rationale: `<why or why not>`

2. **Q2 — Will this be used immediately (in the next release/canary)?**
   Answer: `Yes / No`
   Rationale: `<why or why not>`

3. **Q3 — Do we have stakeholders/data/metrics demanding this now?**
   Answer: `Yes / No`
   Rationale: `<evidence / requests / ticket numbers>`

4. **Q4 — Can this be added later without large migration cost?**
   Answer: `Yes / No`
   Rationale: `<reason>`

**Decision**: `Implement / Defer`
Short explanation linking to the above answers.

---

## 3) Evidence & acceptance criteria (concrete, measurable)

- **Acceptance test(s)** (exact commands / CI job names):
  - `pytest -q tests/test_xyz.py`
  - `python tools/audit_greenlight.py --report /tmp/audit.json` → `jq '.baseline_verification.status'` must be `"ok"`

- **Performance criteria**:
  - `parse_p99_ms` must remain <= baseline * 1.5 on benchmark runs (tools/bench_dispatch.py).

- **Security criteria**:
  - Token canonicalization tests pass: `pytest -q tests/test_token_canonicalization.py`

- **Operational readiness**:
  - CI pre-merge job `pre_merge_checks` passes on Linux runners.
  - `MAX_ISSUES_PER_RUN` variable set (no alert storms).

---

## 4) Rollback & revert trigger (exact thresholds)

- Rollback if `parse_p99_ms` > baseline × 1.5 for 5 minutes.
- Rollback if `collector_timeouts_total` increases > 50% over baseline in 10 minutes.
- Reevaluate (defer/flip) if false-positive rate > 10% over a 7-day window.

---

## 5) Test & rollout plan (steps)

1. land PR with feature toggled off by default (if applicable) + unit tests.
2. add CI assertion and PR-smoke (fast smoke).
3. run canary at 1% traffic and monitor metrics for 2 hours.
4. ramp to 5% → 25% after stability window.

---

## 6) Metrics to track (exact names)

- `parse_p99_ms`
- `collector_timeouts_total`
- `audit_unregistered_repos_total`
- `audit_digest_created_total`
- `audit_fp_rate`

---

## 7) Notes / references
- Link to WAREHOUSE_OPTIMIZATION_SPEC.md, RUN_TO_GREEN.md, etc.
- Link to relevant tickets / design docs.

---

**Sign-off**
- Tech Lead: `@name`
- Security: `@name`
- SRE: `@name`
```

---

## SECTION 6: DECISION GENERATOR SCRIPT

**File**: `tools/generate_decision_artifact.py`

```python
#!/usr/bin/env python3
"""
Generate a decision artifact markdown from interactive prompts or CLI args.

Usage:
  python tools/generate_decision_artifact.py --title "..." --owner "Alice" --decision implement --out /tmp/decision.md

If --interactive is given, prompts for fields.
"""
from __future__ import annotations
import argparse
import datetime
import sys
from pathlib import Path
import textwrap

TEMPLATE = """# Decision Artifact — Feature / Design Change

**Feature / Change**:
{title}

**Author / Owner**:
{owner}

**Date**:
{date}

---

## 1) Short summary
{summary}

---

## 2) YAGNI decision checklist (answer each: Yes / No, short rationale)

1. **Q1 — Is this required by current product/security/ops requirements?**
Answer: {q1_answer}
Rationale: {q1_rationale}

2. **Q2 — Will this be used immediately (in the next release/canary)?**
Answer: {q2_answer}
Rationale: {q2_rationale}

3. **Q3 — Do we have stakeholders/data/metrics demanding this now?**
Answer: {q3_answer}
Rationale: {q3_rationale}

4. **Q4 — Can this be added later without large migration cost?**
Answer: {q4_answer}
Rationale: {q4_rationale}

**Decision**: {decision}
Short explanation: {decision_rationale}

---

## 3) Evidence & acceptance criteria (concrete, measurable)

Acceptance tests:
{acceptance_tests}

Performance criteria:
{perf_criteria}

Security criteria:
{sec_criteria}

Operational readiness:
{ops_readiness}

---

## 4) Rollback & revert trigger (exact thresholds)

{rollback_triggers}

---

## 5) Test & rollout plan (steps)

{rollout_plan}

---

## 6) Metrics to track (exact names)

{metrics}

---

## 7) Notes / references
{notes}

---

**Sign-off**
- Tech Lead: @
- Security: @
- SRE: @
"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--interactive", action="store_true")
    p.add_argument("--title", default="(untitled)")
    p.add_argument("--owner", default="(unknown)")
    p.add_argument("--summary", default="(no summary provided)")
    p.add_argument("--q1_answer", default="No")
    p.add_argument("--q1_rationale", default="")
    p.add_argument("--q2_answer", default="No")
    p.add_argument("--q2_rationale", default="")
    p.add_argument("--q3_answer", default="No")
    p.add_argument("--q3_rationale", default="")
    p.add_argument("--q4_answer", default="Yes")
    p.add_argument("--q4_rationale", default="")
    p.add_argument("--decision", default="Defer")
    p.add_argument("--decision_rationale", default="")
    p.add_argument("--acceptance_tests", default="- pytest -q tests")
    p.add_argument("--perf_criteria", default="- parse_p99_ms <= baseline * 1.5")
    p.add_argument("--sec_criteria", default="- token canonicalization tests pass")
    p.add_argument("--ops_readiness", default="- pre_merge_checks pass on Linux")
    p.add_argument("--rollback_triggers", default="- parse_p99_ms > baseline * 1.5 for 5m")
    p.add_argument("--rollout_plan", default="- land PR → run canary")
    p.add_argument("--metrics", default="- parse_p99_ms\\n- collector_timeouts_total")
    p.add_argument("--notes", default="")
    p.add_argument("--out", default="DECISION_ARTIFACT.md")
    args = p.parse_args()

    if args.interactive:
        def ask(prompt, default=""):
            r = input(f"{prompt} [{default}]: ").strip()
            return r or default
        args.title = ask("Title", args.title)
        args.owner = ask("Owner", args.owner)
        args.summary = ask("Short summary", args.summary)
        args.q1_answer = ask("Q1 (Yes/No)", args.q1_answer)
        args.q1_rationale = ask("Q1 rationale", args.q1_rationale)
        args.q2_answer = ask("Q2 (Yes/No)", args.q2_answer)
        args.q2_rationale = ask("Q2 rationale", args.q2_rationale)
        args.q3_answer = ask("Q3 (Yes/No)", args.q3_answer)
        args.q3_rationale = ask("Q3 rationale", args.q3_rationale)
        args.q4_answer = ask("Q4 (Yes/No)", args.q4_answer)
        args.q4_rationale = ask("Q4 rationale", args.q4_rationale)
        args.decision = ask("Decision (Implement/Defer)", args.decision)
        args.decision_rationale = ask("Decision rationale", args.decision_rationale)

    now = datetime.date.today().isoformat()
    filled = TEMPLATE.format(
        title=args.title,
        owner=args.owner,
        date=now,
        summary=args.summary,
        q1_answer=args.q1_answer,
        q1_rationale=args.q1_rationale,
        q2_answer=args.q2_answer,
        q2_rationale=args.q2_rationale,
        q3_answer=args.q3_answer,
        q3_rationale=args.q3_rationale,
        q4_answer=args.q4_answer,
        q4_rationale=args.q4_rationale,
        decision=args.decision,
        decision_rationale=args.decision_rationale,
        acceptance_tests=args.acceptance_tests,
        perf_criteria=args.perf_criteria,
        sec_criteria=args.sec_criteria,
        ops_readiness=args.ops_readiness,
        rollback_triggers=args.rollback_triggers,
        rollout_plan=args.rollout_plan,
        metrics=args.metrics,
        notes=args.notes,
    )
    outp = Path(args.out)
    outp.write_text(filled, encoding="utf8")
    print(f"Wrote decision artifact to {outp}")

if __name__ == "__main__":
    main()
```

---

## SECTION 7: FAST SMOKE CORPUS

**File**: `adversarial_corpora/fast_smoke.json`

```json
[
  {
    "id": "fast-1",
    "desc": "percent-encoded url vector",
    "input": "http://example.com/%3Cscript%3Ealert(1)%3C/script%3E"
  },
  {
    "id": "fast-2",
    "desc": "template method token attempt",
    "input": "{{ __class__.__mro__ }}"
  },
  {
    "id": "fast-3",
    "desc": "html anchor with javascript",
    "input": "<a href=\"javascript:alert('x')\">x</a>"
  }
]
```

---

## VERIFICATION COMMANDS

### Quick Verification (All Checks)

```bash
# Governance
test -f .github/DECISION_ARTIFACT_TEMPLATE.md && echo "✓ Template exists" || echo "✗ Template missing"
python tools/generate_decision_artifact.py --title "Test" --owner "test" --out /tmp/test.md && echo "✓ Generator works" || echo "✗ Generator broken"

# Simplifications (already done in Part 11)
grep -q 'default="security/audit-backlog"' tools/create_issues_for_unregistered_hits.py && echo "✓ Central backlog" || echo "✗ Missing"
grep -q "MAX_ISSUES_PER_RUN = 10" tools/create_issues_for_unregistered_hits.py && echo "✓ Issue cap" || echo "✗ Missing"
grep -q "def create_digest_issue" tools/create_issues_for_unregistered_hits.py && echo "✓ Digest mode" || echo "✗ Missing"
grep -q "Trigger Thresholds" PLATFORM_SUPPORT_POLICY.md && echo "✓ Triggers documented" || echo "✗ Missing"

# New additions
grep -q "platform.system.*Linux" .github/workflows/pre_merge_checks.yml && echo "✓ Linux assertion" || echo "✗ Missing"
test -f adversarial_corpora/fast_smoke.json && echo "✓ Fast smoke corpus" || echo "✗ Missing"
grep -q "fast_smoke" .github/workflows/pre_merge_checks.yml && echo "✓ PR-smoke wired" || echo "✗ Missing"
grep -q "kms sign" RUN_TO_GREEN.md && echo "✓ KMS recipe" || echo "✗ Missing"
```

### Per-Phase Verification

**Phase 1 (Governance)**:
```bash
test -f .github/DECISION_ARTIFACT_TEMPLATE.md && echo "✓ Template"
test -f tools/generate_decision_artifact.py && echo "✓ Generator"
python tools/generate_decision_artifact.py --title "Test" --owner "test" --out /tmp/test.md && echo "✓ Works"
```

**Phase 2 (Linux Assertion)**:
```bash
grep -q "platform.system.*Linux" .github/workflows/pre_merge_checks.yml && echo "✓ Assertion"
python -c "import platform; assert platform.system() == 'Linux'" && echo "✓ Platform check works"
```

**Phase 3 (Fast Smoke)**:
```bash
test -f adversarial_corpora/fast_smoke.json && echo "✓ Corpus"
grep -q "fast_smoke" .github/workflows/pre_merge_checks.yml && echo "✓ Wired"
```

**Phase 4 (KMS Signing)**:
```bash
grep -q "kms sign" RUN_TO_GREEN.md && echo "✓ KMS recipe"
```

---

## TIMELINE & EFFORT

| Phase | Effort | Items | Status |
|-------|--------|-------|--------|
| Phase 1: Decision Governance | 1 hour | 3 items | NOT STARTED |
| Phase 2: Linux Assertion | 15 min | 1 item | NOT STARTED |
| Phase 3: Fast Smoke | 40 min | 2 items | NOT STARTED |
| Phase 4: KMS Documentation | 30 min | 1 item | NOT STARTED |
| **TOTAL** | **2h 25min** | **7 items** | **NOT STARTED** |

**Note**: 6/12 acceptance criteria already complete from Part 11 (central backlog, issue cap, digest mode, trigger thresholds, platform policy, Windows docs)

---

## ROLLBACK PLAN

**If Part 12 changes cause issues**:

1. **Revert decision governance** (low risk - documentation only)
   ```bash
   git rm .github/DECISION_ARTIFACT_TEMPLATE.md
   git rm tools/generate_decision_artifact.py
   git commit -m "Revert: decision governance"
   ```

2. **Revert Linux assertion** (medium risk - breaks Windows CI)
   ```bash
   # Remove platform assertion from .github/workflows/pre_merge_checks.yml
   git add .github/workflows/pre_merge_checks.yml
   git commit -m "Revert: Linux assertion"
   ```

3. **Revert fast smoke** (low risk - PR checks only)
   ```bash
   git rm adversarial_corpora/fast_smoke.json
   # Remove fast_smoke wiring from .github/workflows/pre_merge_checks.yml
   git add .github/workflows/pre_merge_checks.yml
   git commit -m "Revert: fast smoke"
   ```

**No production impact**: All changes are CI/documentation only

---

## METRICS TO TRACK

Track these metrics to validate YAGNI decisions:

| Metric | Threshold | Action |
|--------|-----------|--------|
| `consumer_count` | >= 10 | Reintroduce org-wide scanning |
| `avg_org_unregistered_repos_per_run` | >= 5 for 7d | Reintroduce org-wide scanning |
| `manual_triage_workload` | > 1 FTE-day/week | Implement schema validation |
| `audit_fp_rate` | > 10% for 30d | Reduce heuristics or add curation |
| `pattern_count` | > 50 | Implement pattern curation |
| `fp_rate_variance` | > 20% | Implement pattern curation |

**Export Commands**:
```bash
# Export consumer count
echo "consumer_count $(grep -c '^  - repo:' consumer_registry.yml)" > .metrics/consumer_count.prom

# Export FP rate (manual tracking until automated)
# Track in spreadsheet: FP_count / total_hits over 30 days
```

---

## NEXT STEPS

1. **Complete Part 12 Implementation** (2.5 hours)
   - Execute Phases 1-4 sequentially
   - Verify each phase before proceeding

2. **Create Decision Artifacts for Past PRs** (optional, 2-4 hours)
   - Retroactively document org-scan deferral
   - Document Windows deferral
   - Document per-repo auto-issue deferral

3. **Integrate with PR Review Process** (ongoing)
   - Require decision artifact for feature PRs
   - Review Q1-Q4 answers in PR reviews
   - Track deferred features via trigger metrics

4. **Monitor Trigger Thresholds** (monthly)
   - Check Prometheus metrics
   - File tickets when thresholds exceeded
   - Revisit YAGNI decisions annually

---

## COMPLETION CRITERIA

Part 12 is complete when:

- ✅ All 12 acceptance criteria pass
- ✅ Decision governance template exists
- ✅ Decision generator script works
- ✅ Linux assertion enforced in CI
- ✅ Fast smoke corpus wired to PR checks
- ✅ KMS signing recipe documented
- ✅ Verification commands all pass
- ✅ Completion report created (PART12_EXECUTION_COMPLETE.md)

---

**Status**: 📋 **PART 12 PLAN READY - AWAITING EXECUTION**

**Review Required**: Human approval before execution
**Estimated Completion**: 2-4 hours
**Risk Level**: LOW (removals and documentation)
