# Central Audit Backlog - Triage Guide

This document provides instructions for triaging issues in the central audit backlog repository (security/audit-backlog).

## Overview

The audit automation system creates issues in this central repository when it detects unregistered renderer-like files. Issues are created with:

- **Labels**: `security/high`, `security/medium`, `triage`
- **Digest mode**: When >10 repos detected, a single digest issue is created
- **Auto-close labels**: `auto-close:proposed`, `auto-close:confirmed`, `auto-close:blocked`

## Triage Workflow

### Step 1: Review the Issue

1. Check the **Offending files** section for detected patterns
2. Review the **Suggested code_paths** entries
3. If a gist is attached, review the full audit artifact

### Step 2: Classify the Issue

**True Positive** (legitimate unregistered renderer):
- Repo renders metadata/templates
- Not in `consumer_registry.yml`
- Not in `audit_exceptions.yml`
- Action: Register in consumer_registry.yml + add SSTI litmus test

**False Positive** (not actually a renderer):
- Test fixtures, examples, documentation
- Dead code, commented-out imports
- Non-rendering template usage
- Action: Mark as FP (see Step 3) + add to `audit_exceptions.yml`

**Noise** (duplicate, already fixed):
- Already registered/fixed
- Duplicate of existing issue
- Action: Close and mark as FP if duplicate

### Step 3: Mark False Positives

**Why track FPs?** FP metrics feed into Prometheus alerts to detect pattern drift and trigger tuning.

**How to mark FPs**:

**Option 1: Add `fp` label**:
```bash
gh issue edit <issue-number> --add-label "fp"
```

**Option 2: Add `fp=true` comment**:
```markdown
fp=true

This is a false positive - the pattern matched test fixtures, not production renderers.
```

**Effect**: The `audit_fp_marked_total` Prometheus counter is incremented when:
- Issue has `fp` label, OR
- Issue has comment containing `fp=true`

### Step 4: Take Action

**For True Positives**:

1. **Assign owner** (from consumer_registry.yml if available)
2. **Register consumer**:
   ```yaml
   # consumer_registry.yml
   consumers:
     - name: "repo-name"
       repo: "org/repo-name"
       renders_metadata: true
       code_paths:
         - "path/to/code"
       ssti_protection:
         test_file: "tests/test_ssti_litmus.py"
         autoescape_enforced: true
   ```
3. **Add SSTI litmus test** (if renders metadata)
4. **Run probe** in staging:
   ```bash
   python tools/probe_consumers.py \
       --registry consumer_registry.yml \
       --outdir consumer_probe_reports
   ```
5. **Close issue** when fixed and probe passes

**For False Positives**:

1. **Mark as FP** (see Step 3)
2. **Add to exceptions**:
   ```yaml
   # audit_exceptions.yml
   exceptions:
     - path: "tests/fixtures/template_mock.py"
       reason: "Test fixture, not production code"
       approver: "security-lead@example.com"
       expires: "2025-12-31"
   ```
3. **Close issue**

### Step 5: Auto-Close Workflow

**Auto-close labels**:
- `auto-close:proposed` - 72-hour review period before auto-close
- `auto-close:confirmed` - Immediate closure (skip review period)
- `auto-close:blocked` - Prevent auto-close (manual review required)

**When auto-close triggers**:
- Latest audit shows 0 unregistered hits for the repo
- Issue has `auto-close:proposed` label for 72+ hours
- OR issue has `auto-close:confirmed` label

**How to control auto-close**:

**Confirm immediate closure**:
```bash
gh issue edit <issue-number> --add-label "auto-close:confirmed"
```

**Block auto-close**:
```bash
gh issue edit <issue-number> --add-label "auto-close:blocked"
```

**Let auto-close proceed** (default):
- Do nothing - after 72 hours, issue will be auto-closed if resolved

## FP Rate Monitoring

**Prometheus Metrics**:
- `audit_fp_marked_total` - Total FPs marked
- `audit_unregistered_repos_total` - Total repos scanned
- `audit:fp_rate:7d` - FP rate over 7-day window

**Grafana Dashboard**:
- Import `grafana/dashboards/audit_fp_dashboard.json`
- View FP rate trend and issue creation failures

**Alert Thresholds**:
- **Warning**: FP rate > 10% over 7 days
- **Action**: Review patterns and consider tuning

## Common False Positive Patterns

| Pattern | Reason | Fix |
|---------|--------|-----|
| `tests/fixtures/*.py` | Test fixtures | Add to `audit_exceptions.yml` |
| `docs/examples/*.py` | Documentation | Add to `audit_exceptions.yml` |
| `# jinja2.Template` | Commented code | Add to `audit_exceptions.yml` |
| Dead imports | Unused imports | Remove from code |

## Escalation

**If FP rate > 10% for 7+ days**:
1. Review Grafana dashboard for trends
2. Identify common FP patterns
3. File ticket to tune detection patterns
4. Consider excluding specific paths globally

**If issue creation failures**:
1. Check Prometheus alert: `AuditIssueCreateFailed`
2. Verify GitHub token permissions
3. Check API quota: `github_api_quota_remaining`
4. Review fallback artifacts in `adversarial_reports/fallback_*.json`

## Useful Commands

```bash
# List all open triage issues
gh issue list --label triage --state open

# List all FP issues
gh issue list --label fp --state all

# Mark issue as FP
gh issue edit 123 --add-label "fp"
gh issue comment 123 --body "fp=true - test fixture"

# Close issue
gh issue close 123 --comment "Fixed: registered in consumer_registry.yml"

# Query FP rate (requires Prometheus)
curl -s "http://prometheus:9090/api/v1/query?query=audit:fp_rate:7d" | jq '.data.result[0].value[1]'
```

## Contact

| Role | Owner | Responsibility |
|------|-------|----------------|
| **Tech Lead** | @tech-lead | Triage policy, pattern tuning |
| **Security** | @security-lead | Consumer registration, exceptions |
| **SRE** | @sre-lead | Metrics, alerts, automation health |

**Questions or issues?** File a ticket in the audit automation repo or contact security@example.com.
