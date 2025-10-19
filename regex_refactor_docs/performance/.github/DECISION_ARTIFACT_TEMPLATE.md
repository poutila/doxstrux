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
