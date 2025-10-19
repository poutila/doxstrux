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
    p.add_argument("--metrics", default="- parse_p99_ms\n- collector_timeouts_total")
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
