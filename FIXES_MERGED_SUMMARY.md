# FIXES_MERGED.md — Critical Clarifications Needed

**Grade**: A (96/100)  
**Status**: ✅ **READY** after 3 clarifications (30 minutes)

---

## 3 Decisions Needed Before Implementation

### 1. Spec vs. Linter as SSOT 🔴 CRITICAL

**Your text**: "pick one"  
**Problem**: Doesn't say which one

**REQUIRED DECISION**:
```
✅ RECOMMENDED: Spec is SSOT

Why:
- Spec = human-readable contract
- Linter = implementation (can have bugs)
- Standard practice (spec defines "correct")
- If spec and linter disagree, fix linter

Document: Add "Spec is SSOT" section to spec + README
```

---

### 2. Coverage Enforcement Rules 🟡 IMPORTANT

**Your text**: "warning in plan/instantiated modes"  
**Problem**: Doesn't distinguish missing vs. malformed

**REQUIRED SPECIFICATION**:
```
Warning (don't fail):
- Section completely missing
- Table is empty

Error (fail lint):
- Table malformed (unparseable)
- Tasks referenced don't exist
- Source anchors invalid

Start with warnings only in v1.7
```

---

### 3. Deprecation Timeline 🟡 IMPORTANT

**Your text**: "deprecation timeline"  
**Problem**: No version numbers or dates

**REQUIRED TIMELINE**:
```
v1.6.1 (Release: +2 weeks)
- Add plan mode
- Template RELAXED (warn only)
- Grace period starts

v1.7.0 (Release: +8 weeks after v1.6.1)
- Template STRICT (fail on concrete commands)
- Breaking change enforced
- Users must migrate

Grace period: 8 weeks
```

---

## What You Did Excellently ⭐⭐⭐⭐⭐

1. **Comprehensive**: All 12 gaps from feedback addressed
2. **Ordered**: Perfect priority sequence
3. **Validated**: Real project testing included
4. **Complete**: Edge cases documented
5. **Measured**: Performance benchmarking specified

---

## After Clarifications

**Implementation time**: 5-6 days  
**Risk level**: 🟢 LOW  
**Confidence**: Very high

---

## Quick Decision Template

Copy this to your plan:

```markdown
## Implementation Decisions

### Decision 1: SSOT Hierarchy
**Choice**: Spec is SSOT, linter implements spec
**Rationale**: Standard practice; spec defines correctness
**Implication**: If spec/linter disagree, fix linter

### Decision 2: Coverage Enforcement
**Missing section**: Warning
**Malformed table**: Error
**V1.7**: Start with warnings only

### Decision 3: Deprecation Timeline
**v1.6.1**: Plan mode added, template relaxed (warn)
**v1.7.0**: Template strict (fail) — 8 weeks after v1.6.1
**Grace period**: 8 weeks between warning and enforcement
```

---

## Implementation Checklist

### Week 1 (Days 1-3): Core
- [ ] Spec: Add plan mode + coverage rules
- [ ] Linter: Implement enforcement
- [ ] Examples: Create 3 canonical files
- [ ] Test: Validation suite passes

### Week 2 (Days 4-5): Docs
- [ ] Update 9 docs consistently
- [ ] Write migration guide
- [ ] Test on real project

### Week 3 (Day 6): Ship
- [ ] Gate audit
- [ ] CHANGELOG
- [ ] Release v1.6.1

---

## Bottom Line

Plan is **96% ready**. Make 3 decisions (30 min), then execute confidently.

**See FIXES_MERGED_FEEDBACK.md for exhaustive analysis (25 pages)**
