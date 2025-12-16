# ZERO-AMBIGUITY PROMPT — HISTORICAL CONTENT REMOVAL REVIEW (Corrected)

## Target set and input contract

**Target set:** Find **all** markdown documents (`**/*.md`) under:
- `/home/lasse/Dropbox/python/omat/doxstrux/files (9)`
- list **all** markdown documents you found

**Input contract (no guessing):**
- Confirm that you can read complete text of every markdown file you found in the **Target set**.
- Read the complete text of every markdown file in **Target set**
- If you can not read texts from **Target set**, report a **BLOCKER** and STOP the entire run (do not continue with partial coverage).

**No other assumptions allowed:**
- Do not assume filesystem structure beyond what is documented in the texts you read
- Do not assume tooling beyond what is explicitly specified in the texts you read
- Do not assume internal conventions not present in the texts you read
- Do not assume any context not present in the texts you read

---

## Reviewer mindset

You are the implementer who will execute a plan in `VERSION_NORMALIZATION.md` tomorrow.
Documentation is carrying historical content that might not be useful. Historical content is harmful disinformation. It causes guessing and drift.

Costs of ambiguity:
- Every ambiguity = 30 minutes of guessing
- Every undefined term = work blocked
- Every contradiction = wrong assumptions = wasted work

Review approach:
1. Read everything twice
2. Question every term, reference, and assumption
3. Check for contradictions across documents

---

## Context and goal

**Goal:** Remove historical content from framework documentation to reduce drift and maintenance burden.

**Scope (deterministic):**
- Remove deprecated features, obsolete examples, legacy workflows
- Remove references to old versions, old tools, old conventions
- No backward compatibility support needed
- No migration paths needed
- Clean slate: current version only

**Success criteria (deterministic):**
1. Documentation contains only current-state guidance in normative prose
2. No version comparisons in normative prose
3. No deprecated warnings in normative prose
4. No migration/upgrade guides in normative prose
5. One clear path forward: current best practice only

---

## Definitions (no guessing)

### Normative prose
Any line outside fenced code blocks (```…```) and outside blockquotes (Markdown lines starting with `>`).

### Historical content (in-scope for removal)
Historical content is any normative prose matching one or more of the following categories:

1. **Version comparisons / legacy references**
   - Mentions of older versions or comparisons (e.g., “unlike an older version”, “improved from a prior release”)
2. **Migration / upgrade instructions**
   - Any “if upgrading/migrating from X then do Y” guidance
3. **Deprecated/legacy workflows**
   - Any text describing an older approach as still supported, tolerated, or optional
4. **Obsolete tooling references**
   - Any mention of replaced tooling, renamed scripts, or retired commands, unless it is explicitly quarantined (see below)

### Allowed exceptions (must be explicit and quarantined)
Historical information is permitted ONLY if quarantined in one of these ways:

- A dedicated non-normative file or section that is explicitly excluded from “current guidance”, e.g.:
  - `CHANGELOG.md` (if present) — treated as historical record
  - `task_list_archive/**` — treated as historical record

If such quarantined sections/files are present inside normative docs, they MUST be moved out or removed.

---

## Edge-case handling rules (deterministic)

- The words “was”, “used to”, “previously” are NOT automatically violations by themselves.
  - They are violations only if they appear in **normative prose** AND refer to older versions/workflows/tools.
- Code blocks may contain version numbers for compatibility examples ONLY if the surrounding normative prose does not describe legacy workflows as recommended or supported.

---

## STOP condition for missing references

If any referenced artifact/section/path/term is missing or not provided, STOP immediately and report a BLOCKER:

```
SEVERITY: BLOCKER
REFERENCE: "[exact quote that references missing item]"
MISSING: [artifact name / section / path / term]
BLOCKS: [what decision/implementation this makes impossible]
LOCATION: [file + line range, e.g., FILENAME.md:L120-L135]
```

---

## Location / line-numbering contract

All findings MUST cite locations using stable line numbers.

- If the input text does not include line numbers, assume the provider supplied the equivalent of `nl -ba` output or a tool export with stable line numbering.
- LOCATION format MUST be: `FILENAME.md:L<start>-L<end>`.

If line numbers are not available for any target file: report a BLOCKER and STOP.

---

## Output format (per finding)

```
SEVERITY: [BLOCKER | HIGH | MEDIUM | LOW]
LOCATION: [FILENAME.md:L<start>-L<end>]
QUOTE: "[Exact text containing the issue]"
ISSUE: [Why this forces guessing or creates drift]
TEST CASE: [Concrete example showing multiple valid interpretations]
MINIMAL FIX: [Exact replacement text or exact deletion/move instruction]
```

---

## Severity definitions

**BLOCKER**
- Missing target document text (input contract violated)
- Missing referenced artifact/section/path/term
- Undefined term with operational impact (e.g., “historical”, “deprecated”, “obsolete”) not resolved by Definitions above
- Contradictory requirements that cannot both be true
- Line numbers unavailable

**HIGH**
- Ambiguous scope that could produce wrong removal (keep vs delete)
- Conflicting “current” guidance across docs
- Legacy content embedded in normative docs without quarantine

**MEDIUM**
- Ambiguous wording with 2–3 valid interpretations
- Inconsistent terminology across docs
- Missing example that makes keep/remove decision unclear

**LOW**
- Minor wording polish that does not change keep/remove decisions

---

## Review checklist (must be applied)

### 1) References & dependencies
- [ ] All referenced files exist in provided texts/artifacts
- [ ] All referenced sections exist
- [ ] Removal targets are precisely identified (file + lines)
- [ ] Technical terms are defined or referenced

### 2) Identification criteria (historical detection)
- [ ] Each historical category is applied consistently
- [ ] Edge-case rules are applied
- [ ] Quarantine exceptions are explicit

### 3) Scope & boundaries
- [ ] File-by-file scope is specified
- [ ] Section-by-section removals are specified
- [ ] CHANGELOG/history is quarantined (not in normative docs)

### 4) Removal procedures
- [ ] Every “remove X” instruction is executable (exact line range)
- [ ] Replacement text is specified when needed
- [ ] Moves/quarantines specify destination file/section

### 5) Internal consistency
- [ ] No contradictions within a doc
- [ ] No contradictions across docs
- [ ] Only one current best-practice path remains

---

## Output structure

```markdown
# Zero-Ambiguity Review — Historical Content Removal

## Executive Summary
- Total findings: [count]
- BLOCKER: [count]
- HIGH: [count]
- MEDIUM: [count]
- LOW: [count]
- Execution readiness: [X%]

## BLOCKERS
[Findings]

## HIGH Priority
[Findings]

## MEDIUM Priority
[Findings]

## LOW Priority
[Findings]

## Verdict
**Can this be executed without guessing?** [YES/NO]

**Evidence:**
- [Key points]

**Required fixes for execution:**
- [Numbered must-fix items]
```

---

## Critical questions the target documents MUST answer (explicitly)

1. What is considered historical (by the Definitions above)?
2. What is removed vs quarantined, and where does quarantined content live?
3. What replaces removed content (delete, rewrite to current, or redirect)?
4. What happens to file-level history artifacts (CHANGELOG, archives)?
5. What is the single current best-practice path after removal?
