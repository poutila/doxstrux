# CLEANING.md — Plan to Reduce Maintenance Burden in `files (9)/`

## Executive Summary

| Category | Issues Found | Impact |
|----------|--------------|--------|
| Maintenance Burden | 5 | HIGH |
| Overlap/Duplication | 7 | HIGH |
| Drift Sources | 5 | CRITICAL |
| Confusing Content | 4 | MEDIUM |
| Stale/Orphan Files | 3 | LOW |

**Root cause**: Documentation grew organically; rules are now stated in 5+ places. Any change requires updating multiple files, and they drift.

---

## File Inventory (19 markdown files)

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| COMMON.md | Version metadata, shared definitions | 50 | KEEP (refactor) |
| AI_TASK_LIST_SPEC_v1.md | Authoritative spec | 601 | KEEP (SSOT) |
| AI_TASK_LIST_TEMPLATE_v6.md | Template scaffold | 333 | KEEP |
| README_ai_task_list_linter_v1_9.md | Linter usage | 128 | KEEP (simplify) |
| USER_MANUAL.md | User manual | 125 | MERGE candidate |
| AI_ASSISTANT USER_MANUAL.md | AI manual | 150 | MERGE candidate |
| PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md | Runtime prompt | 212 | KEEP |
| INDEX.md | File index | 21 | KEEP |
| VALIDATION_SUITE.md | Test plan | 46 | KEEP |
| CHANGELOG.md | Version history | 20 | KEEP (quarantined) |
| VERSION_NORMALIZATION.md | Executed plan | 157 | ARCHIVE |
| HISTORICAL_REMOVAL_REVIEW_PROMPT_correct.md | Prompt file | ~100 | ARCHIVE |
| validation/canaries/MANIFEST.md | Canary tracking | 14 | FIX or DELETE |
| canonical_examples/example_template.md | Template example | 80 | KEEP (review) |
| canonical_examples/example_plan.md | Plan example | 180 | KEEP |
| canonical_examples/example_instantiated.md | Instantiated example | 191 | KEEP |
| canonical_examples/negatives/*.md (3) | Negative fixtures | ~130 each | KEEP |

---

## Issue 1: Two Manuals with Overlapping Content (CRITICAL)

### Problem
`USER_MANUAL.md` and `AI_ASSISTANT USER_MANUAL.md` cover the same topics:
- Quickstart workflows
- Linter usage
- Enforcement rules
- Checklists

Any rule change requires updating BOTH.

### Evidence of Overlap

| Topic | USER_MANUAL.md | AI_ASSISTANT USER_MANUAL.md |
|-------|----------------|----------------------------|
| Core concepts | §1 (L11-19) | §1 Inputs (L8-17) |
| Quickstart | §2 (L34-43) | §3-4 (L25-48) |
| Linter usage | §3 (L44-55) | §9 (L113-115) |
| Enforcement | §4 (L57-74) | §6 (L73-95) |
| Checklists | §9 (L105-124) | §11 (L129-149) |

### Options

**Option A: Merge into single MANUAL.md** (RECOMMENDED)
- One manual covering human and AI workflows
- Sections: Overview, Workflows, Enforcement, Checklists
- Removes duplication entirely

**Option B: Make one primary, one reference**
- USER_MANUAL.md is authoritative
- AI_ASSISTANT USER_MANUAL.md references it: "See USER_MANUAL.md for rules"
- AI manual adds only AI-specific guidance (orchestrator usage)

### Recommendation
**Option A** — Delete both manuals; create fresh `MANUAL.md`. The distinction between "user" and "AI assistant" is artificial; both need the same rules. Fresh creation avoids carrying over duplicated content and aligns with Clean Table principle.

### New MANUAL.md Structure

```markdown
# AI Task List Framework — Manual

## 1. Overview
- SSOT hierarchy (from both manuals)
- Mode definitions (template/plan/instantiated)
- File inventory (spec, template, linter, orchestrator)

## 2. Creating a Task List
### 2.1 From Prose (AI-assisted)
- Orchestrator usage (from AI_ASSISTANT §Orchestrator entry point)
- Prose coverage mapping (from AI_ASSISTANT §Prose Coverage Mapping)
### 2.2 From Template (Manual)
- Copy template, fill YAML, replace placeholders (from USER §2 Quickstart)

## 3. Task List Structure
- Baseline Snapshot requirements (from AI_ASSISTANT §4)
- Phase and Task design (from AI_ASSISTANT §5)
- TDD steps, STOP blocks, checklists (combined)

## 4. Running the Linter
- Commands (from USER §3) — SINGLE AUTHORITATIVE LOCATION
- Exit codes
- --require-captured-evidence flag

## 5. Enforcement Rules (Reference Only)
- "See AI_TASK_LIST_SPEC_v1.md for authoritative rules"
- Rule ID quick reference table (R-ATL-xxx → one-line summary)

## 6. Evidence and Commands
- $ prefix requirements (from AI_ASSISTANT §6)
- Captured headers (from AI_ASSISTANT §7)
- No comment compliance (combined)

## 7. Common Mistakes and Fixes
- Linter failure patterns (from USER §6)
- Common authoring mistakes (from AI_ASSISTANT §Common linter failures)

## 8. Checklists
### 8.1 Plan Mode Checklist
### 8.2 Instantiated Mode Checklist
(Merged from USER §9 and AI_ASSISTANT §11 — ONE checklist per mode)

## 9. CI Integration
- Recommended CI usage (from USER §7)

## 10. Limitations
- Reality verification limits (from USER §8, AI_ASSISTANT §10)
```

### Files Requiring Reference Updates

| File | Line(s) | Current | New |
|------|---------|---------|-----|
| INDEX.md | 11-12 | Two manual entries | `- \`MANUAL.md\` — Framework manual (workflows, linter usage, checklists).` |
| README_ai_task_list_linter_v1_9.md | 9 | `USER_MANUAL.md`, `AI_ASSISTANT USER_MANUAL.md` | `MANUAL.md` |
| PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md | 6 | `Manual: AI_ASSISTANT USER_MANUAL.md` | `Manual: MANUAL.md` |
| PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md | 30 | `AI_ASSISTANT USER_MANUAL.md` link | `MANUAL.md` link |
| VERSION_NORMALIZATION.md | 25, 48, 85, 97 | Both manual names | `MANUAL.md` (or archive file first) |
| tools/check_version_consistency.py | 175-176 | Both paths | `ROOT / "MANUAL.md"` |

### Exact Edits for Reference Updates

**INDEX.md** (replace lines 11-12):
```markdown
# Before
- `USER_MANUAL.md` — Framework user manual (spec/template/linter usage, workflows, checklists).
- `AI_ASSISTANT USER_MANUAL.md` — AI-oriented manual for converting prose to task lists (template vs instantiated, gates, coverage).

# After
- `MANUAL.md` — Framework manual (spec/template/linter usage, workflows, checklists, prose conversion).
```

**README_ai_task_list_linter_v1_9.md** (replace line 9):
```markdown
# Before
- **Manuals/Docs**: `USER_MANUAL.md`, `AI_ASSISTANT USER_MANUAL.md`, `COMMON.md` for shared rules, plus `INDEX.md` for orientation (planning docs in `task_list_archive/`).

# After
- **Manuals/Docs**: `MANUAL.md`, `COMMON.md` for shared rules, plus `INDEX.md` for orientation (planning docs in `task_list_archive/`).
```

**PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md** (replace lines 6 and 30):
```markdown
# Line 6 before
> Manual: AI_ASSISTANT USER_MANUAL.md

# Line 6 after
> Manual: MANUAL.md

# Line 30 before
5. **AI Assistant Manual**: [AI_ASSISTANT USER_MANUAL.md](./AI_ASSISTANT USER_MANUAL.md).

# Line 30 after
5. **Manual**: [MANUAL.md](./MANUAL.md).
```

**tools/check_version_consistency.py** (replace lines 175-176):
```python
# Before
        ROOT / "USER_MANUAL.md",
        ROOT / "AI_ASSISTANT USER_MANUAL.md",

# After
        ROOT / "MANUAL.md",
```

### Content Deduplication During Merge

| Content | Keep From | Delete From |
|---------|-----------|-------------|
| SSOT hierarchy | USER §1 | AI_ASSISTANT §1 (duplicate) |
| Mode definitions | USER §1 | AI_ASSISTANT §1 (duplicate) |
| Quickstart steps | USER §2 | — |
| Prose → task list workflow | AI_ASSISTANT §2-5 | — |
| Orchestrator usage | AI_ASSISTANT §Orchestrator | — |
| Linter run commands | USER §3 | AI_ASSISTANT §9 (duplicate) |
| Enforcement rules list | Neither (reference spec) | Both (duplicates spec) |
| Evidence/$ prefix rules | AI_ASSISTANT §6-7 | USER §4 (partial duplicate) |
| Linter failure fixes | USER §6 | AI_ASSISTANT §Common failures (merge) |
| CI usage | USER §7 | — |
| Limitations | USER §8 | AI_ASSISTANT §10 (duplicate) |
| Checklists | Merge both | — |

### Writing Order for Fresh MANUAL.md

When creating MANUAL.md fresh, reference archived originals in this order:

| Section | Source for Reference | Notes |
|---------|---------------------|-------|
| §1 Overview | USER §1 | Rewrite concisely |
| §2 Creating a Task List | AI_ASSISTANT §2-5 + USER §2 | Combine workflows |
| §3 Task List Structure | AI_ASSISTANT §3-5 | Unique content |
| §4 Running the Linter | USER §3 | Copy verbatim (authoritative) |
| §5 Enforcement Rules | Neither | Write as reference table to spec |
| §6 Evidence and Commands | AI_ASSISTANT §6-7 | Unique content |
| §7 Common Mistakes | USER §6 + AI_ASSISTANT §9 | Merge lists |
| §8 Checklists | Both §9/§11 | Dedupe into one per mode |
| §9 CI Integration | USER §7 | Copy verbatim |
| §10 Limitations | USER §8 | Copy verbatim |

---

## Issue 2: COMMON.md Duplicates Spec Content (HIGH)

### Problem
COMMON.md was created to centralize definitions but now duplicates spec rules:

| COMMON.md Section | Duplicates Spec Rule |
|-------------------|---------------------|
| §Runner Rules | R-ATL-070, R-ATL-071, R-ATL-072 |
| §Import Hygiene | R-ATL-063 |
| §Gate Patterns | R-ATL-050, R-ATL-060 gate semantics |
| §Placeholder Protocol | R-ATL-003 |
| §Status Values | R-ATL-090 |
| §Evidence Requirements | R-ATL-021, R-ATL-023, R-ATL-024 |
| §Prose Coverage Mapping | R-ATL-NEW-02 |

### Fix
Reduce COMMON.md to **only**:
- §Version Metadata (SSOT tuple)
- §SSOT Hierarchy
- §Mode Definitions

Delete all rule sections. Other docs reference spec rules directly:
```markdown
Import hygiene rules: See AI_TASK_LIST_SPEC_v1.md R-ATL-063.
```

### New COMMON.md Structure (target: ~20 lines)
```markdown
# COMMON.md — Shared Framework Definitions

## §Version Metadata
- Spec: v1.9 (schema_version: "1.7")
- Linter: v1.9 (`ai_task_list_linter_v1_9.py`)
- Template: v6.0

## §SSOT Hierarchy
1) Spec (authoritative contract)
2) Linter (implements the spec)
3) Template, manuals, orchestrator
4) Prose (lowest)

## §Mode Definitions
- `template`: placeholders allowed; generic scaffolds.
- `plan`: real commands; evidence placeholders allowed.
- `instantiated`: no placeholders; real evidence required.
- Lifecycle: template → plan → instantiated.
```

---

## Issue 3: Import Hygiene Documented in 5 Places (CRITICAL DRIFT)

### Problem
The import hygiene rule is stated in:
1. AI_TASK_LIST_SPEC_v1.md R-ATL-063 (lines 385-408) — AUTHORITATIVE
2. COMMON.md §Import Hygiene (lines 25-28) — DUPLICATE
3. README_ai_task_list_linter_v1_9.md (line 26) — DUPLICATE
4. USER_MANUAL.md §4 (line 68) — DUPLICATE
5. AI_ASSISTANT USER_MANUAL.md §6 (line 77) — DUPLICATE

### Fix
1. Keep only spec R-ATL-063 as authoritative
2. Delete COMMON.md §Import Hygiene
3. README/Manuals: Replace rule text with reference:
   ```markdown
   - Import hygiene (R-ATL-063): See spec for required `$ rg` command lines.
   ```

---

## Issue 4: Linter Run Commands in 4 Places (OVERLAP)

### Problem
```bash
uv run python ai_task_list_linter_v1_9.py PROJECT_TASKS.md
```
This command appears in:
1. README_ai_task_list_linter_v1_9.md §Run (lines 72-80)
2. USER_MANUAL.md §3 (lines 46-53)
3. AI_ASSISTANT USER_MANUAL.md §9 (lines 113-115)
4. VALIDATION_SUITE.md (lines 7, 12, 17)

### Fix
1. README is the authoritative place for run commands
2. Manuals reference README: "See README_ai_task_list_linter_v1_9.md §Run"
3. VALIDATION_SUITE keeps commands (it's a test script, not docs)

---

## Issue 5: Quick Checklists Duplicated (HIGH)

### Problem
- USER_MANUAL.md §9 Quick Checklists (lines 105-124)
- AI_ASSISTANT USER_MANUAL.md §11 Quick Checklist (lines 129-149)

Nearly identical content.

### Fix
If manuals merge (Issue 1), this resolves automatically.
If not: Keep checklist in USER_MANUAL only; AI manual references it.

---

## Issue 6: Stale/Orphan Files (MEDIUM)

### VERSION_NORMALIZATION.md
- Contains executed plan with "Post-Execution" section
- States: "Move to `task_list_archive/` after successful execution"
- **Action**: Move to `task_list_archive/VERSION_NORMALIZATION_executed.md`

### HISTORICAL_REMOVAL_REVIEW_PROMPT_correct.md
- Prompt file used to trigger historical content removal
- Not framework documentation
- **Action**: Move to `task_list_archive/` or delete

### validation/canaries/MANIFEST.md
- Line 13 is corrupted: contains `template"  # Modes:...` garbage
- All entries show "NOT RUN" — never used
- **Action**: Fix or delete; if kept, run the canary tests to populate

---

## Issue 7: Template vs Example Template Confusion (MEDIUM)

### Problem
Three files are template-like:
1. `AI_TASK_LIST_TEMPLATE_v6.md` (333 lines) — THE template
2. `canonical_examples/example_template.md` (80 lines) — minimal example
3. `canonical_examples/negatives/template_missing_clean_table_placeholder.md` (333 lines) — copy with break

### Confusion
- Is `example_template.md` the same as the main template?
- The negative fixture is a full copy modified to fail — hard to maintain

### Fix
1. `example_template.md` should be clearly labeled as "minimal lint-passing example"
2. Consider generating negative fixtures from main template via script rather than maintaining copies
3. Add header comments to clarify purpose:
   ```markdown
   <!-- This is a MINIMAL lint-passing example, not the full template -->
   ```

---

## Issue 8: README Duplicates INDEX and Framework Overview (LOW)

### Problem
- INDEX.md lists artifacts with one-line descriptions
- README_ai_task_list_linter_v1_9.md §"What this framework is for" duplicates this

### Fix
README should focus on linter usage only. Remove §"What this framework is for" or reduce to one line pointing to INDEX.md.

---

## Execution Plan

**Execution order matters**: Phases 1-3 must complete before Phase 4. The new manual should reference the cleaned COMMON.md (after Phase 3), not the bloated version with duplicated rules. Phase 5-6 can run after Phase 4.

```
Phase 1 (archive stale) ─┐
Phase 2 (fix broken)    ─┼─► Phase 4 (create manual) ─► Phase 5 (dedupe) ─► Phase 6 (clarify)
Phase 3 (reduce COMMON) ─┘
```

### Phase 1: Archive Stale Files (LOW RISK)
```bash
# From files (9)/ directory
mkdir -p task_list_archive
mv VERSION_NORMALIZATION.md task_list_archive/VERSION_NORMALIZATION_executed.md
mv "HISTORICAL_REMOVAL_REVIEW_PROMPT_correct.md" task_list_archive/
```

### Phase 2: Fix Broken Files (LOW RISK)
- Fix or delete `validation/canaries/MANIFEST.md`

### Phase 3: Reduce COMMON.md (MEDIUM RISK)
1. Delete §Runner Rules, §Import Hygiene, §Gate Patterns, §Placeholder Protocol, §Status Values, §Evidence Requirements, §Prose Coverage Mapping
2. Keep only: §Version Metadata, §SSOT Hierarchy, §Mode Definitions
3. Update files that referenced deleted sections to reference spec rules instead

### Phase 4: Create Fresh Manual (MEDIUM RISK)

**Prerequisite**: Complete Phases 1-3 first. The new manual should reference the cleaned COMMON.md, not the bloated version.

1. Archive originals for reference:
   ```bash
   mkdir -p task_list_archive/manual_originals
   cp USER_MANUAL.md task_list_archive/manual_originals/
   cp "AI_ASSISTANT USER_MANUAL.md" task_list_archive/manual_originals/
   ```
2. Delete from main folder:
   ```bash
   rm USER_MANUAL.md "AI_ASSISTANT USER_MANUAL.md"
   ```
3. Create fresh `MANUAL.md` using structure from Issue 1 (10 sections)
4. Reference archived originals during writing per "Writing Order for Fresh MANUAL.md" table
5. Apply "Exact Edits for Reference Updates" to 4 files:
   - INDEX.md (lines 11-12)
   - README_ai_task_list_linter_v1_9.md (line 9)
   - PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md (lines 6, 30)
   - tools/check_version_consistency.py (lines 175-176)
6. Verify: `rg "USER_MANUAL|AI_ASSISTANT USER_MANUAL" . --glob "*.md" --glob "*.py"` returns nothing
7. Delete archived originals after MANUAL.md is verified (optional)

### Phase 5: Deduplicate Enforcement Descriptions (MEDIUM RISK)
1. README: Remove enforcement feature descriptions, keep only Run commands
2. Manuals: Reference spec rule IDs instead of restating rules
3. Result: One authoritative description per rule (in spec)

### Phase 6: Clarify Examples (LOW RISK)
1. Add header comments to canonical_examples explaining their purpose
2. Consider script to generate negative fixtures from main template

---

## Definition of Done

After cleaning:
- [ ] COMMON.md is ≤25 lines (version metadata + modes only)
- [ ] ONE manual file exists (not two)
- [ ] README contains only linter run commands (no enforcement prose)
- [ ] Import hygiene rule stated in exactly ONE place (spec R-ATL-063)
- [ ] Quick checklist exists in exactly ONE place
- [ ] VERSION_NORMALIZATION.md is in task_list_archive/
- [ ] HISTORICAL_REMOVAL_REVIEW_PROMPT_correct.md is archived or deleted
- [ ] validation/canaries/MANIFEST.md is fixed or deleted
- [ ] Linter passes on all canonical examples
- [ ] `rg` search for rule text finds spec + at most one reference per other file

---

## Verification Commands

```bash
# Count lines in COMMON.md (target: ≤25)
wc -l COMMON.md

# Check for import hygiene rule duplication
rg -l "from \\\.\\\." . --glob "*.md" | wc -l
# Should be 3 max: spec, template, one example

# Check for stale files in main folder
ls *.md | grep -E "(NORMALIZATION|HISTORICAL|PROMPT.*correct)"
# Should return nothing after archival

# Verify linter passes
uv run python ai_task_list_linter_v1_9.py AI_TASK_LIST_TEMPLATE_v6.md
uv run python ai_task_list_linter_v1_9.py canonical_examples/example_plan.md
uv run python ai_task_list_linter_v1_9.py --require-captured-evidence canonical_examples/example_instantiated.md
```

---

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|------------|
| 1 | LOW | Git revert if needed |
| 2 | LOW | File is already broken |
| 3 | MEDIUM | Run linter after; check all COMMON.md references |
| 4 | MEDIUM | Originals archived; write fresh from spec; verify references |
| 5 | MEDIUM | Incremental changes; verify lint after each |
| 6 | LOW | Comments only; no structural change |

---

## Post-Cleaning File Structure (Target)

```
files (9)/
├── COMMON.md                          # ~20 lines: versions + modes only
├── AI_TASK_LIST_SPEC_v1.md            # UNCHANGED (SSOT)
├── AI_TASK_LIST_TEMPLATE_v6.md        # UNCHANGED
├── README_ai_task_list_linter_v1_9.md # ~50 lines: run commands only
├── MANUAL.md                          # MERGED from two manuals
├── PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md  # UNCHANGED
├── INDEX.md                           # Updated references
├── VALIDATION_SUITE.md                # UNCHANGED
├── CHANGELOG.md                       # UNCHANGED (quarantined)
├── canonical_examples/
│   ├── example_template.md            # With clarifying header
│   ├── example_plan.md
│   ├── example_instantiated.md
│   └── negatives/
│       └── *.md                       # With clarifying headers
└── task_list_archive/
    ├── VERSION_NORMALIZATION_executed.md
    ├── HISTORICAL_REMOVAL_REVIEW_PROMPT_correct.md
    └── (other planning docs)
```

**File count**: 19 → ~14 (excluding archive)
**Lines of duplicated rule text**: ~200 → ~0
**Drift sources for import hygiene rule**: 5 → 1

---

## Notes for Tomorrow's Reviewer

When reading this folder tomorrow, you should NOT need to guess:
1. **Where is the authoritative rule?** → AI_TASK_LIST_SPEC_v1.md (always)
2. **What versions are current?** → COMMON.md §Version Metadata (only place)
3. **How do I run the linter?** → README_ai_task_list_linter_v1_9.md §Run (only place)
4. **What's the workflow?** → MANUAL.md (one manual, not two)
5. **What are the examples for?** → Headers in each example file explain

The current state requires cross-referencing 5+ files and guessing which version of a rule is authoritative. After cleaning, each question has exactly one answer location.
