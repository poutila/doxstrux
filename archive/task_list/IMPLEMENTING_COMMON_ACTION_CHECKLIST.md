# IMPLEMENTING_COMMON.md — Action Checklist

**Current Status**: 92% ready (A-)

**Target Status**: 98% ready (A+) 

**What to do**: Add 6 sections (30-45 minutes)

---

## ❌ 3 CRITICAL MISSING (Must Add)

### 1. Reference Format Specification ❌

**Where**: After "Steps" section, before "Execution order"

**What to add**:
```markdown
## Reference Format Specification

[Copy full section from IMPLEMENTING_COMMON_FEEDBACK_V2.md Issue #1]
```

**Why critical**: Without this, implementer won't know WHERE to place comments

---

### 2. Detailed Validation Checks ❌

**Where**: Expand Step 4 in "Steps" section

**What to add**:
```markdown
## Validation Checks (Step 4 — Detailed Commands)

[Copy full section from IMPLEMENTING_COMMON_FEEDBACK_V2.md Issue #2]
```

**Why critical**: "Grep for version strings" is too vague

---

### 3. Rollback Plan ❌

**Where**: Replace current "Execution order" section

**What to add**:
```markdown
## Execution Order (REVISED)

[Copy full section from IMPLEMENTING_COMMON_FEEDBACK_V2.md Issue #3]
```

**Why critical**: Need recovery path if validation fails

---

## ⚠️ 3 IMPORTANT MISSING (Should Add)

### 4. Content Removal Guidelines

**Where**: Expand Step 2 in "Steps" section

**What to add**: See Missing #4 in feedback

**Why**: Clarifies "where safe" decision rule

---

### 5. COMMON.md Structure Spec

**Where**: After "Scope" section, before "Steps"

**What to add**: See Missing #5 in feedback

**Why**: Specifies header/footer/sections format

---

### 6. Timeline to 8 Hours

**Where**: Update "Execution order" section

**What to change**: 6 hours → 8 hours (realistic buffer)

**Why**: Accounts for edge cases

---

## Quick Copy-Paste Instructions

1. Open IMPLEMENTING_COMMON.md
2. Open IMPLEMENTING_COMMON_FEEDBACK_V2.md side-by-side
3. Copy-paste these sections:

   **From Issue #1** → Add "Reference Format Specification"
   **From Issue #2** → Add "Validation Checks (Detailed Commands)"
   **From Issue #3** → Replace "Execution Order" + add "Rollback Plan"
   **From Missing #4** → Add "Content Removal Guidelines"
   **From Missing #5** → Add "COMMON.md Structure Specification"
   **From Timeline** → Adjust 6h → 8h

4. Review for consistency (10 min)
5. Save

**Total time**: 30-45 minutes

---

## Verification Checklist

Before implementing, confirm:

- [ ] Reference format: WHERE to place comments specified?
- [ ] Validation: 6 specific bash commands with expected outputs?
- [ ] Rollback: Backup branch creation + rollback procedure?
- [ ] Content removal: "Safe vs unsafe" decision rules?
- [ ] COMMON.md structure: Header/footer/sections specified?
- [ ] Timeline: 8 hours instead of 6?

**All checked?** → ✅ Ready to implement (98% ready)

**Any unchecked?** → ⚠️ Add missing sections first

---

## After Adding Sections

Ask me: **"Review updated plan"**

I'll confirm it's 98% ready, then you can implement with confidence.

---

## Why Not Skip This Step?

**If you implement NOW without adding these**:

- Hour 2: "Wait, where do I place this comment?"
- Hour 4: "What exact command checks versions?"
- Hour 5: "Validation failed, how do I roll back?"
- Hour 6: "Is it safe to remove this text?"

**Result**: Wasted time, inconsistent decisions, potential rework

**If you add 6 sections FIRST** (45 min):

- Hour 2: Follow placement spec
- Hour 4: Run 6 specific commands
- Hour 5: Execute rollback procedure
- Hour 6: Apply removal guidelines

**Result**: Smooth implementation, no ambiguity, done in 8h

---

## Bottom Line

**Current plan**: 92% ready

**30-45 minutes** to reach 98% ready

**Don't skip this step**

**Do it now, implement later with confidence**

---

**See IMPLEMENTING_COMMON_FEEDBACK_V2.md for full details of what to copy-paste**
