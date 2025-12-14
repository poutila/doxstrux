# AI_TASK_LIST_TEMPLATE — Usage Guide (Refactored)

**Version**: 2.2  
**Goal**: Produce an AI task list that does not drift and stays close to reality.

**Derived governance (inputs)**:
- Clean Table: `CLEAN_TABLE_PRINCIPLE.md`
- No Weak Tests: `NO_WEAK_TESTS.md`
- uv rule: `UV_AS_PACKAGE_MANAGER.md`
- Evidence discipline: `CHAIN_OF_THOUGHT_GOLDEN_ALL_IN_ONE.json`
- KISS/YAGNI quality gates: `CODE_QUALITY.json`

---

## 1) What “close to reality” means (operational)

A task list is “real” when:

- Every “exists / passes / wired” claim has an evidence anchor.
- All commands shown are actually executable in this repo.
- The baseline snapshot includes commit hash + tool versions.
- Tests are the arbiter (not the plan text).

---

## 2) The four drift killers (why v2.2 differs)

1. **Single placeholder syntax** `[[PH:NAME]]`  
   Makes “no placeholders” enforceable and non-noisy.

2. **Phase 0 baseline reality**  
   Forces capture of actual repo state before planning becomes fiction.

3. **Canonical file lists per task**  
   Prevents “Files:” headers diverging from verification scripts.

4. **uv-only execution**  
   Eliminates “works locally but not in CI” command drift.

---

## 3) How to instantiate and execute

1. Copy `AI_TASK_LIST_TEMPLATE_v2_2.md` to `PROJECT_TASKS.md`.
2. Replace every `[[PH:...]]` with real values.
3. Ensure placeholder scan returns zero:
   ```bash
   grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && exit 1 || true
   ```
4. Execute Phase 0 and paste outputs.
5. Only then draft Phase 1+ tasks.

---

## 4) Clean Table in practice (strict interpretation)

- If anything is unverified, it is not “complete.”
- If anything is deferred (“do later”), it is not “clean.”
- If a failure is acceptable, it must be explicitly logged (Drift + Issues Ledger) with the policy justification.

---

## 5) No Weak Tests: enforcement guidance

Replace weak tests with fixture-driven, semantic assertions:

- Use known-good / known-bad fixtures.
- Assert exact codes/messages for rule-based outputs.
- Prefer “fail-before, pass-after” proofs.
- Avoid line-count as primary correctness evidence.

---

## 6) KISS/YAGNI: how to prevent speculative engineering

When implementing a task, require:

- a current requirement (task’s Objective + Scope)
- immediate consumption by at least one known code path today
- “simpler alternative considered” note for anything architectural

If you cannot name a real consumer today, defer the abstraction.

---

## 7) Evidence anchors: minimum viable vs strict

Minimum viable evidence (always required):
- command output for tests and tool versions
- grep evidence for “symbol exists”
- file excerpt for “wired here” claims

Stricter evidence (recommended for high-risk changes):
- SHA-256 hashes of excerpts
- trace links tying decisions to evidence

---

## 8) Common failure modes to guard against

- “I wrote tasks that assume files exist.”  
  Fix: grep + file existence checks before writing the task.

- “I allowed skips locally.”  
  Fix: do not treat skips as clean unless policy explicitly allows it.

- “I claimed green without pasting outputs.”  
  Fix: outputs are mandatory evidence.

End of guide.
