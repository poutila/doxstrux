# COMMON.md Extraction — Quick Decision Guide

**Question**: Should we extract common content to reduce maintenance?

**Answer**: ✅ **YES — Hybrid approach recommended**

---

## What to Extract (9 Items)

| Content | Current Overlap | Maintenance Saved | Priority |
|---------|----------------|-------------------|----------|
| **1. Version numbers** | 11 files (95%) | 90% | 🔴 CRITICAL |
| **2. SSOT hierarchy** | 3 files (85%) | 100% | 🔴 CRITICAL |
| **3. Mode definitions** | 7 files (90%) | 85% | 🔴 CRITICAL |
| **4. Runner rules** | 4 files (80%) | 75% | 🟠 HIGH |
| **5. Import hygiene** | 3 files (55%) | 60% | 🟠 HIGH |
| **6. Gate patterns** | 3 files (60%) | 50% | 🟡 MEDIUM |
| **7. Placeholder protocol** | 2 files (40%) | 40% | 🟡 MEDIUM |
| **8. Status values** | 3 files (35%) | 35% | 🟡 MEDIUM |
| **9. Evidence requirements** | 2 files (30%) | 30% | 🟡 MEDIUM |

---

## What NOT to Extract (5 Items)

| Content | Why Keep Duplicated |
|---------|---------------------|
| **1. Workflows** | Audience-specific (human vs AI) |
| **2. Examples** | Context-dependent |
| **3. Checklists** | User-facing, inline context needed |
| **4. Release notes** | Temporal, file-specific |
| **5. Error messages** | Linter-specific |

---

## Expected Benefits

**Maintenance reduction**: 30-40%

**Specific wins**:
- Version bump: Update 1 file instead of 11 ✅
- SSOT drift: Resolved (fixes Drift #2) ✅
- Mode definitions: Single source (prevents future drift) ✅
- Runner rules: Canonical reference ✅

**Costs**:
- Implementation: 1 day (7 hours)
- Slight cognitive load: Must reference COMMON.md
- Cross-file dependencies: 12 files → 13 files

**ROI**: Positive after 2-3 version bumps

---

## COMMON.md Structure (Proposed)

```markdown
# COMMON.md — Shared Framework Definitions

## §Version Metadata
- Current Release: v1.7 (spec) / v1.9 (linter)
- Schema Version: "1.6"
- Template Version: v6.0

## §Mode Definitions
### template, plan, instantiated
[Full definitions + lifecycle diagram]

## §SSOT Hierarchy
1. Spec (authoritative contract)
2. Linter (implementation)
3. Template, Manuals, Orchestrator, Prose

## §Runner Rules
### uv: Required/Forbidden commands

## §Import Hygiene (Python/uv)
Required checks with examples

## §Gate Patterns
Correct patterns + Anti-patterns list

## §Placeholder Protocol
Format + Pre-flight check

## §Status Values
📋 PLANNED | ⏳ IN PROGRESS | ✅ COMPLETE | ❌ BLOCKED

## §Evidence Requirements
Headers, output, non-empty rules
```

---

## Implementation Plan

### Phase 1: Critical (Day 1 — 4 hours)

1. ✅ Create COMMON.md
2. ✅ Extract version metadata → Fixes 90% of version update burden
3. ✅ Extract SSOT hierarchy → Fixes Drift #2
4. ✅ Extract mode definitions → Prevents future drift
5. ✅ Extract runner rules → Canonical reference

**Effort**: 4 hours  
**Benefit**: Addresses 4 of 7 drifts + version management

---

### Phase 2: High-Value (Day 1 — 3 hours)

6. ✅ Extract import hygiene
7. ✅ Extract gate patterns
8. ✅ Extract placeholder protocol

**Effort**: 3 hours  
**Benefit**: Further reduces duplication

---

### Phase 3: References (Day 1 — 1 hour)

9. ✅ Add `<!-- See COMMON.md §Section -->` to 12 files
10. ✅ Validate references
11. ✅ Update INDEX.md

**Effort**: 1 hour

---

**Total**: 1 day (8 hours)

---

## Reference Format

### In each file

```markdown
<!-- Version: See COMMON.md §Version Metadata -->
# AI Task List Spec v1.9

<!-- Modes: See COMMON.md §Mode Definitions -->
This framework supports three modes...

<!-- SSOT: See COMMON.md §SSOT Hierarchy -->
If files disagree, spec wins...
```

### For readers

Comments are invisible to end users but help maintainers know where canonical definitions live.

---

## Comparison: Before vs. After

### Before (Current State)

**Version bump v1.7 → v1.8**:
- Update 11 files ❌
- 15-20 minutes ❌
- Risk of missing one ❌

**SSOT question**:
- Check 3 files ❌
- Find ambiguity ❌
- Guess intent ❌

**Mode definitions**:
- Check 7 files ❌
- Find slight variations ❌
- Reconcile manually ❌

---

### After (With COMMON.md)

**Version bump v1.7 → v1.8**:
- Update COMMON.md ✅
- 2 minutes ✅
- Propagates automatically ✅

**SSOT question**:
- Check COMMON.md §SSOT Hierarchy ✅
- Find unambiguous answer ✅
- Clear hierarchy ✅

**Mode definitions**:
- Check COMMON.md §Mode Definitions ✅
- Single canonical source ✅
- No reconciliation needed ✅

---

## Example: Version Bump Workflow

### Current (v1.7 → v1.8)

```bash
# Manual updates needed in 11 files:
1. AI_TASK_LIST_SPEC_v1.md (line 1)
2. ai_task_list_linter_v1_9.py (docstring)
3. README_ai_task_list_linter_v1_8.md (line 1)
4. PROMPT_AI_TASK_LIST_ORCHESTRATOR_v1.md (line 2)
5. USER_MANUAL.md (line 5)
6. AI_ASSISTANT USER_MANUAL.md (line 5)
7. DESCRIPTION.md (line 6)
8. INDEX.md (line 4)
9. CHANGELOG.md (new entry)
10. MIGRATION_GUIDE.md (header)
11. VALIDATION_SUITE.md (header)
```

**Time**: 15-20 minutes  
**Risk**: Forgetting one file

---

### With COMMON.md (v1.8 → v1.9)

```bash
# Single update:
$ edit COMMON.md
  - Current Release: v1.8 (spec) / v1.10 (linter)
  
$ git commit -m "Bump to v1.8/v1.10"

# All 12 files reference COMMON.md automatically
```

**Time**: 2 minutes  
**Risk**: Zero (single source)

---

## Alternative: Doc Generation (Future)

**If extraction becomes cumbersome**, consider v1.8+ enhancement:

```bash
# Template files with variables:
AI_TASK_LIST_SPEC_v1.tpl.md

# Generation script:
$ python generate_docs.py

# Output:
AI_TASK_LIST_SPEC_v1.md (with variables resolved)
```

**Benefits**:
- DRY principle (single source)
- Self-contained output (no cross-refs needed)
- Best of both worlds

**When to consider**: If COMMON.md references become too frequent

---

## Decision Matrix

| Scenario | Current Approach | With COMMON.md | With Generation |
|----------|------------------|----------------|-----------------|
| **Version bump** | 11 files, 20 min | 1 file, 2 min | 1 file, 2 min |
| **Mode definition change** | 7 files, 15 min | 1 file, 3 min | 1 file, 3 min |
| **Reading docs offline** | ✅ Works | ⚠️ Need COMMON.md | ✅ Works |
| **Finding definition** | 🟡 Search multiple | ✅ One place | ✅ One place |
| **Git blame** | ✅ Per-file | ⚠️ Points to COMMON | ✅ Per-file |
| **Implementation cost** | ✅ Zero | 🟡 1 day | 🟠 3 days |

---

## Recommendation

**Immediate (v1.7 → v1.7.1)**:
✅ Implement COMMON.md extraction (1 day)

**Why now**:
- Fixes Drift #2 (SSOT ambiguity)
- Prepares for v1.8 version bump
- ROI positive after 2 updates

**Future (v1.8+)**:
⚠️ Monitor if cross-references become burdensome
⚠️ Consider doc generation if needed

---

## Bottom Line

**Should we extract**: ✅ **YES**

**How much**: **Selective** (9 high-overlap items)

**Effort**: 1 day

**Benefit**: 30-40% maintenance reduction + fixes SSOT drift

**Start with**: Version metadata, SSOT hierarchy, mode definitions (critical items)

**Recommendation**: Implement after v1.7 release as v1.7.1 polish

---

**See COMMON_MD_ANALYSIS.md for comprehensive 40-page analysis with full reasoning**
