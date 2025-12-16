---
speksi:
  spec_id: AI_TASK_LIST_GOAL
  version: 1.0.0
  status: DRAFT
  tier: STANDARD
  layers:
    META: "§M"
    ARCHITECTURE: "§A"
    DEFINITIONS: "§D"
    VALIDATION: "§V"
    CHANGELOG: "§C"
    GLOSSARY: "§G"
---

# AI Task List Framework Goals (SPEKSI Informative Companion)

§M META

§M.1 Purpose

This document describes the intended outcomes, success criteria, and explicit non-goals for the “AI Task List” framework. It is a companion to the normative rule specification and exists to preserve intent without embedding enforceable constraints in goal prose.

§M.2 Relationship to the Rule Specification

- This document is informative and does not define linter-enforceable requirements.
- Enforceable requirements belong in the rule specification: → AI_TASK_LIST_SPEC_SPEKSI.md
- If a statement in this document conflicts with the rule specification, treat the rule specification as authoritative.

§M.3 Scope

In scope:

- The intended properties of an AI-generated task list when derived from prose.
- The conceptual pipeline and the framework components used to reduce drift and invention.
- The definition of “success” in terms of validation and review outcomes.
- Non-goals that bound expectations and prevent over-claims.

Out of scope:

- Judging whether a set of product requirements is correct, complete, or feasible.
- Guaranteeing that a correct-looking task list is truthful (the framework can raise the cost of fabrication; it cannot eliminate it).
- Replacing human judgment for meaning, priority, or real-world constraints.

§A ARCHITECTURE

§A.1 Goal Statement

The framework targets an AI Task List produced from prose that:

- Remains faithful to the input prose, minimizing interpretation creep.
- Reflects repository reality by using discovered facts (paths, symbols, tool outputs) rather than fabricated details.
- Can be checked deterministically via a linter against a published specification.
- Embeds governance expectations (TDD cadence, “no weak tests”, runner discipline, clean-table hygiene, import/search discipline).
- Minimizes iteration loops by making the initial input sufficiently grounded and constrained.

§A.2 Conceptual Pipeline

A typical end-to-end flow is:

1) Prose input is prepared (requirements, constraints, and context).
2) Repository discovery is performed to collect facts (paths, symbols, key outputs).
3) The AI converts prose + facts into an AI Task List artifact in a fixed template shape.
4) Deterministic validation is performed (linters and structured review prompts).
5) Execution begins with minimal clarifying questions, because preconditions and evidence hooks are embedded in the artifact.

§A.3 Components and Why They Exist

| Component | Classification | Purpose |
|-----------|----------------|---------|
| Linters | Deterministic | Repeatable validation: same artifact, same findings |
| Templates | Deterministic | Fixed structure; the AI fills values rather than inventing structure |
| Discovery | Heuristic plus captured facts | Grounding inputs: paths/symbols/outputs are collected and pasted |
| Conversion | Heuristic plus captured facts | Reformatting and mapping, with minimal semantic invention |
| Review | Heuristic plus explicit criteria | Human-like judgment constrained by a checklist and evidence requirements |

§A.4 Invention-Resistance Mechanisms

The framework uses multiple levers to reduce AI invention risk:

| Mechanism | Intended effect |
|----------|------------------|
| Facts precede instructions | Reduces “vacuum reasoning”; nudges reuse of real paths/symbols |
| Sample artifacts | Lowers ambiguity by showing real directory and command outputs |
| Explicit decision tables | Prevents the AI from choosing alternatives that were not decided |
| Bounded vocabulary | Stabilizes meaning of terms across artifacts |
| Preconditions / symbol checks | Ensures tasks reference real symbols and preconditions, not imagined APIs |

§A.5 Prompt Construction Preferences (Informative)

When preparing prompts that lead to an AI Task List:

- Place captured facts before requests or instructions.
- Resolve open questions before prompting (avoid leaving decision points undecided).
- State constraints in concrete terms (explicit paths, symbols, and commands).
- Require a fixed output structure that matches the target template.
- Include explicit rejection criteria (examples: invented paths, new terminology, unexplained deviations).

§A.6 Common Failure Modes to Detect Early

| Failure mode | Description |
|--------------|-------------|
| Drift | Output diverges from prose requirements or changes intent |
| Orphan tasks | Tasks that cannot be traced to a prose requirement |
| Missing negative tests | Tests only cover the happy path for critical behavior |
| Invented paths/symbols | References that do not exist in the discovered repository facts |
| AI-chosen alternatives | The AI decides between options that were never decided in inputs |

§A.7 Non-Goals (Explicit Boundaries)

The framework does not aim to:

| Non-goal | Reason |
|----------|--------|
| Guarantee technical correctness | A spec-compliant task list can still describe the wrong solution |
| Ensure feasibility | Some tasks can be impractical given real constraints |
| Complete requirements | The source prose may be incomplete |
| Prevent evidence fabrication | The framework can detect inconsistencies and increase effort to fake; it cannot eliminate the possibility |
| Replace human judgment | Review and prioritization remain human responsibilities |

§D DEFINITIONS

§D.1 Terms

Drift
Any mismatch between the source prose and the produced task list (scope, intent, constraints, sequencing, or assumptions).

Discovery facts
Concrete repository-derived information (paths, symbols, tool outputs) captured before conversion and reused as constraints.

AI Task List artifact
A structured Markdown plan with phases, tasks, gates, and evidence hooks that is intended to be executable and mechanically reviewable.

Governance
A set of quality constraints applied to tasks and their verification steps (e.g., TDD cadence, test strength, hygiene checks, runner discipline).

No weak tests
A testing quality expectation emphasizing semantic assertions, negative cases for critical behavior, and rejection of existence-only or import-only checks.

Clean table
A “ready to proceed” condition where unfinished markers and placeholders are absent (per the applicable mode), and verification checks pass.

Bounded vocabulary
A glossary-backed set of terms whose meanings are stabilized to prevent redefinition across prompts and artifacts.

Decision table
A pre-filled list of choices and resolutions that prevents the AI from selecting an option by default when the input is ambiguous.

Preconditions / symbol checks
Explicit checks embedded in tasks to confirm referenced symbols, paths, or assumptions exist in the actual codebase.

§V VALIDATION

§V.1 Success Criteria (Informative)

The framework is considered successful when all of the following hold:

1) Prose input passes its deterministic checks and review gate (as defined by the project’s prose input validation pipeline).
2) The AI Task List artifact passes the deterministic linter checks defined by the rule specification.
3) Prose coverage is complete as represented by a Prose Coverage Mapping.
4) Execution can begin without additional clarifying questions for basic facts (paths, symbols, runner, baseline commands).
5) Evidence hooks are present and usable, and captured outputs are reproducible in principle.
6) Governance expectations are visible throughout tasks (tests, verification steps, hygiene checks).
7) Invention risk is materially reduced by requiring that paths/symbols/commands trace back to discovery facts or the source prose.

§C CHANGELOG

- 1.0.0 (2025-12-16): Converted GOAL.md into a SPEKSI-formatted informative companion document, separating intent (goals, success criteria, non-goals) from enforceable rules.

§G GLOSSARY

AI Task List Framework
A workflow and set of artifacts (templates, discovery facts, validators, and review prompts) designed to produce an execution-oriented task list from prose with minimized drift and reduced invention.

Deterministic validation
Validation that produces consistent results for the same artifact and rule set, typically implemented as a linter.

Evidence hook
A pre-defined location in an artifact where command lines and captured outputs are expected to be pasted, enabling verification and auditability.

End of Document
