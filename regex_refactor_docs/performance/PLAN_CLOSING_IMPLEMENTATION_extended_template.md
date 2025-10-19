# {{DOCUMENT_TITLE}}
**Version**: {{VERSION}}  
**Date**: {{DATE}}  
**Status**: {{STATUS}}  
**Methodology**: {{METHODOLOGY}}  
**Part**: {{PART}}  
**Purpose**: {{PURPOSE}}

---

## EXECUTIVE SUMMARY
**One-line verdict**: {{ONE_LINE_VERDICT}}

**Includes**:
- {{INCLUDES_1}}
- {{INCLUDES_2}}
- {{INCLUDES_3}}

**Timeline to green-light**: {{TIMELINE_ESTIMATE}}  
**Critical blockers**: {{TOP_BLOCKER_COUNT}} items

---

## 13-ITEM GREEN-LIGHT CHECKLIST (or N-item)
**ALL items must be TRUE before production deployment.**

### SECURITY (N items)
- **[S1] {{SECURITY_ITEM_NAME}}** ⏳ {{PRIORITY}}
  - Status: {{STATUS}}
  - Effort: {{EFFORT}}
  - Owner: {{OWNER}}
  - Evidence (machine-verifiable): `{{VERIFICATION_COMMAND}}`

- **[S2] {{SECURITY_ITEM_NAME}}**
  - Status: {{STATUS}}
  - Effort: {{EFFORT}}
  - Owner: {{OWNER}}
  - Evidence: `{{VERIFICATION_COMMAND}}`

### RUNTIME (N items)
- **[R1] {{RUNTIME_ITEM_NAME}}**
  - Status: {{STATUS}}
  - Effort: {{EFFORT}}
  - Owner: {{OWNER}}
  - Evidence: `{{VERIFICATION_COMMAND}}`

### PERFORMANCE (N items)
- **[P1] {{PERF_ITEM_NAME}}**
  - Status: {{STATUS}}
  - Effort: {{EFFORT}}
  - Owner: {{OWNER}}
  - Evidence: `{{VERIFICATION_COMMAND}}`

### CI / OBSERVABILITY (N items)
- **[C1] {{CI_ITEM_NAME}}**
  - Status: {{STATUS}}
  - Effort: {{EFFORT}}
  - Owner: {{OWNER}}
  - Evidence: `{{VERIFICATION_COMMAND}}`

### GOVERNANCE (N items)
- **[G1] {{GOV_ITEM_NAME}}**
  - Status: {{STATUS}}
  - Effort: {{EFFORT}}
  - Owner: {{OWNER}}
  - Evidence: `{{VERIFICATION_COMMAND}}`

---

## DECISION & ENFORCEMENT MATRIX
> Copy this table into the repo README or CI doc. Fill one row per acceptance criterion.

| # | Item | Owner | Deadline | Verification Command | CI Job Name | Required Check Name | Contingency |
|---:|------|-------|----------|----------------------|-------------|---------------------|-------------|
| 1 | {{ITEM_NAME}} | {{OWNER}} | {{DEADLINE}} | `{{COMMAND}}` | `{{CI_JOB}}` | `{{REQUIRED_CHECK}}` | {{CONTINGENCY}} |
| 2 | ... | ... | ... | `...` | `...` | `...` | ... |

---

## MACHINE-VERIFIABLE EXAMPLES (copy-paste)
```bash
# Example verification commands (replace placeholders)
pytest -q {{TEST_PATH}}                      # expect rc 0
python -u tools/run_adversarial.py {{CORPUS}} --runs 1 --report /tmp/{{REPORT}}  # expect rc 0 and report file
PRIORITIZED EXECUTION ORDER
IMMEDIATE (Next 48 hours) - CRITICAL
{{IMMEDIATE_ACTION_1}} — Effort: {{HOURS}} — Owner: {{OWNER}}

{{IMMEDIATE_ACTION_2}} — Effort: {{HOURS}} — Owner: {{OWNER}}

SHORT-TERM (48–96 hours)
{{SHORT_ACTION_1}} — Effort: {{HOURS}} — Owner: {{OWNER}}

MEDIUM-TERM (Next week)
{{MEDIUM_ACTION_1}} — Effort: {{HOURS}} — Owner: {{OWNER}}

ARTIFACTS (ready-to-paste)
Artifact A: {{ARTIFACT_A_PATH}} — Purpose: {{ARTIFACT_A_PURPOSE}}

Artifact B: {{ARTIFACT_B_PATH}} — Purpose: {{ARTIFACT_B_PURPOSE}}

Artifact C: {{ARTIFACT_C_PATH}} — Purpose: {{ARTIFACT_C_PURPOSE}}

VERIFICATION COMMANDS (copy-paste)
# Run critical tests
pytest -q {{TEST_1}} -v
pytest -q {{TEST_2}} -v

# Adversarial run
python -u tools/run_adversarial.py {{CORPUS_PATH}} --runs 1 --report /tmp/{{REPORT_NAME}}
TIMELINE TO GREEN-LIGHT
Phase	Duration	Effort	Items	Notes
Immediate	{{DURATION}}	{{EFFORT}}	{{ITEMS}}	{{NOTES}}
Short-term	{{DURATION}}	{{EFFORT}}	{{ITEMS}}	{{NOTES}}
Medium-term	{{DURATION}}	{{EFFORT}}	{{ITEMS}}	{{NOTES}}
CANARY DEPLOYMENT RUNBOOK
Pre-Canary checklist
 {{PRECHECK_1}}

 {{PRECHECK_2}}

 {{PRECHECK_3}}

Canary stages
Stage	Traffic %	Duration	Gate Condition
1	{{PERCENT}}	{{DURATION}}	{{GATE}}
2	{{PERCENT}}	{{DURATION}}	{{GATE}}
Rollback procedure (exact commands)
# emergency rollback
{{ROLLBACK_COMMAND}}
METRICS & ALERT THRESHOLDS
Required metrics:

{{METRIC_1}} — description: {{DESC}}

{{METRIC_2}} — description: {{DESC}}

Alert rules (prometheus style):

- alert: {{ALERT_NAME}}
  expr: {{PROMQL_EXPRESSION}}
  for: {{DURATION}}
  labels:
    severity: {{SEVERITY}}
  annotations:
    summary: "{{SUMMARY}}"
RISK MATRIX
Risk	Likelihood	Impact	Mitigation
{{RISK_1}}	{{LIKELIHOOD}}	{{IMPACT}}	{{MITIGATION}}
{{RISK_2}}	{{LIKELIHOOD}}	{{IMPACT}}	{{MITIGATION}}
CONSUMER ONBOARDING CHECKLIST (per consumer)
 Add SSTI litmus test: {{TEST_PATH}}

 Make test required in branch protection: {{CHECK_NAME}}

 Document metadata rendering / autoescape setting

 Update routing (fallback) if non-compliant

Consumer registry sample (consumer_registry.yml):

version: "1.0"
consumers:
  - name: "{{CONSUMER_NAME}}"
    repo: "{{ORG/REPO}}"
    branch: "main"
    owner: "{{OWNER_EMAIL}}"
    renders_metadata: {{true|false}}
    probe_url: "{{STAGING_PROBE_URL}}"
    required_checks:
      - "{{REQUIRED_CHECK_NAME}}"
AUTOMATION & TOOLING (script stubs)
tools/verify_branch_protection.py — usage: python tools/verify_branch_protection.py --registry consumer_registry.yml

tools/triage_adversarial_failure.py — usage: python tools/triage_adversarial_failure.py /path/to/report.json

Example script header stub:

#!/usr/bin/env python3
"""
{{SCRIPT_PURPOSE}}
"""
import sys
def main():
    # TODO: implement
    pass

if __name__ == "__main__":
    main()
TESTING MATRIX (PR smoke vs nightly)
PR smoke: corpora {{CORPUS_A}}, {{CORPUS_B}} — timeout: {{TIME}}

Nightly full: all corpora in adversarial_corpora/ — retention: {{DAYS}}

ACCEPTANCE (go / no-go)
Green-light if:

All checklist items marked ✅

All verification commands return rc 0

Canary metrics within thresholds for {{DAYS}} days

APPENDIX
Links: {{LINK_TO_WAREHOUSE_SPEC}}, {{LINK_TO_EXECUTION_PLAN}}

Contact: Tech Lead — {{TECH_LEAD_EMAIL}}, SRE — {{SRE_EMAIL}}
