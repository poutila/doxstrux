# AI_TASK_LIST_TEMPLATE — Usage Guide (Refactored)

**Version**: 2.1 (refactor of v2.0)
**Objective**: Help an author produce an executable AI task list that is drift-resistant and anchored to observed reality.

---

## 1. What “close to reality” means operationally

A task list is “close to reality” when:

- Every “it exists / it passes / it’s wired” statement has an evidence anchor.
- The task list never substitutes imagined outputs for executed command results.
- The task list does not prescribe symbols or files without verifying they exist.

This is not philosophical; it is a documentation protocol: claims must be backed by outputs.

---

## 2. The three primary drift failure modes (and how v2.1 blocks them)

### 2.1 Duplicate SSOTs
The template must not maintain two lists of the same thing (files, tasks, commands).
Fix: **Canonical file list arrays** per task; reuse for header + verification.

### 2.2 Ambiguous placeholders
Bracket placeholders like `[TEST_COMMAND]` collide with normal markdown and are hard to lint reliably.
Fix: **Single placeholder syntax** `[[PH:NAME]]` and a hard “zero placeholders” pre-flight rule.

### 2.3 Aspirational execution commands
If CI uses one style and docs show another, the docs become fiction.
Fix: **One runner**. For Python projects using uv, all examples and gates must use `uv run ...`.

---

## 3. How to instantiate the template

1. Copy `AI_TASK_LIST_TEMPLATE_v2_1.md` to `PROJECT_TASKS.md`.
2. Replace all `[[PH:...]]` placeholders with real values.
3. Run placeholder scan:
   ```bash
   grep -RInE '\[\[PH:[A-Z0-9_]+\]\]' PROJECT_TASKS.md && exit 1 || true
   ```
4. Execute Phase 0 first. Do not plan Phase 1+ until baseline reality is captured.

---

## 4. Evidence anchors: required vs optional

Required evidence anchors:
- Test pass/fail claims
- Security/safety claims
- Performance claims
- Architectural “this is wired correctly” claims
- “This symbol exists” claims (grep output)

Optional evidence anchors:
- Pure refactors with no observable behavior change (still recommended to cite tests run)

---

## 5. Test strength: what you must forbid

Forbidden (weak) patterns:
- “exit code in (0,1)” acceptance
- “file exists” without content assertions
- “import-only” tests
- “smoke test: runs without asserting semantics”

Required (strong) patterns:
- assertions that fail under stub/no-op implementations
- content/structure assertions (not just presence)
- negative tests for critical error/safety paths

---

## 6. Clean Table, in practice

Clean Table is not a mood. It is a short list of executable checks:
- tests green
- no placeholders
- no TODOs (per repo policy)
- no silent error paths introduced

If your repo allows TODOs, change the TODO check to target *newly introduced* TODOs in the diff, not the whole tree.

---

## 7. Minimalism guidance (anti-overengineering)

If a mechanism is not necessary to prevent drift or deliver the next milestone, remove it.
Smaller templates drift less.

Practical tests:
- If a rule is not enforced by a command, it is guidance, not governance.
- If a rule exists in both guide and template, prefer keeping it only in the template (single SSOT).

End of guide.
