# Live Risk Ledger

**Purpose**: Track top risks during 13-20 day refactoring execution
**Update Frequency**: Daily (5 minutes/day)
**Scoring**: Probability (1-5) × Impact (1-5) = Risk Score (1-25)
**Threshold**: Score ≥12 requires immediate mitigation

---

## Current Status

**Date**: 2025-10-19
**Phase**: Pre-execution (Phase 0 complete, awaiting Phase 1 start)
**Overall Risk Level**: 🟡 MODERATE (highest score: 12)

---

## Top 3 Active Risks

| # | Risk | Probability (1-5) | Impact (1-5) | Score | Owner | Mitigation Status | Target Date |
|---|------|-------------------|--------------|-------|-------|-------------------|-------------|
| **R1** | Baseline parity <80% blocks production | 3 (Moderate) | 4 (High) | **12** 🟡 | Tech Lead | ✅ Mitigation active: baseline_test_runner.py ready, visualize_diffs tool planned | Phase 8 end |
| **R2** | O(N+M) dispatch proves O(N×M) in practice | 2 (Low) | 5 (Critical) | **10** 🟢 | Architect | ✅ Mitigation active: Hard invariant test created, mid-phase benchmark planned | Phase 4 end |
| **R3** | Collector migration incomplete (stalls at 8/12) | 3 (Moderate) | 3 (Moderate) | **9** 🟢 | Dev Team | ⏳ Mitigation pending: Checklist tracker to be created | Phase 5 end |

**Legend**:
- 🔴 **CRITICAL** (Score 16-25): Immediate action required
- 🟡 **HIGH** (Score 12-15): Active monitoring, mitigation in progress
- 🟢 **MODERATE** (Score 6-11): Tracked, mitigation planned
- ⚪ **LOW** (Score 1-5): Awareness only

---

## Risk Details

### R1: Baseline Parity <80% Blocks Production

**Category**: Technical Blocker
**First Identified**: 2025-10-19
**Current Score**: 12 (3 × 4)

**Description**:
The refactored skeleton parser must achieve ≥80% byte-for-byte match against 542 baseline test outputs from src/ parser. If parity falls below 80% (447/542 tests), production deployment is blocked.

**Why It Could Happen**:
- Output structure differences between src/ and skeleton/ extractors
- Edge cases in token.map handling
- Unicode normalization differences
- Collector logic subtle bugs

**Impact if Realized**:
- **Production Deployment Blocked**: Cannot rollout without 80% parity
- **Timeline Risk**: Could add 1-4 days fixing parity issues
- **Team Morale**: Frustrating debugging of subtle output diffs

**Mitigation Plan**:
- ✅ **Active**: `tools/baseline_test_runner.py` exists and tested
- ✅ **Active**: 542 baseline files in `tools/baseline_outputs/` frozen
- ⏳ **Planned**: Create `tools/visualize_baseline_diffs.py` (Phase 9) for faster debugging
- ⏳ **Planned**: Run baseline subset tests after each phase (early detection)

**Probability Rationale** (3/5 - Moderate):
- Existing Phase 7 extractors had high parity
- skeleton/ uses same markdown-it-py engine
- But: 60-70% code rewrite introduces risk

**Impact Rationale** (4/5 - High):
- Hard production blocker (cannot ship <80%)
- High debugging time cost
- But: Not catastrophic (can fix with time)

**Owner**: Tech Lead
**Review Frequency**: Daily during Phase 8
**Target Resolution**: Phase 8 completion (≥80% parity achieved)

---

### R2: O(N+M) Dispatch Proves O(N×M) in Practice

**Category**: Performance Regression
**First Identified**: 2025-10-19
**Current Score**: 10 (2 × 5)

**Description**:
The refactored dispatch_all() aims for O(N+M) single-pass complexity (N tokens, M collector calls). If routing table implementation has bugs, could degrade to O(N×M) where all collectors check all tokens.

**Why It Could Happen**:
- Routing table build logic error (collectors not registered correctly)
- Deduplication bug causes duplicate collector calls
- Nesting mask logic fails, causing all collectors to run on all tokens

**Impact if Realized**:
- **Critical Performance Regression**: 10-100x slower on large documents
- **Production Rollback**: Immediate rollback required
- **Architecture Failure**: Invalidates entire refactoring approach

**Mitigation Plan**:
- ✅ **Active**: Hard invariant test created: `visited_tokens == len(tokens)`
- ✅ **Active**: Complexity verification test in `test_dispatch.py`
- ⏳ **Planned**: Mid-phase benchmark after Phase 3 (Recommendation #3)
- ⏳ **Planned**: Large document smoke test (1.5MB adversarial_large.json)

**Probability Rationale** (2/5 - Low):
- Routing table pattern is well-understood
- Hard invariant test catches most bugs
- Mid-phase benchmark adds safety net

**Impact Rationale** (5/5 - Critical):
- Would invalidate core architecture
- Immediate production rollback
- Could require re-architecture (weeks of delay)

**Owner**: Architect
**Review Frequency**: After Phase 4 completion, before Phase 5
**Target Resolution**: Phase 4 end (complexity proof passes)

---

### R3: Collector Migration Incomplete (Stalls at 8/12)

**Category**: Execution Risk
**First Identified**: 2025-10-19
**Current Score**: 9 (3 × 3)

**Description**:
Migrating all 12 collectors from Phase 7 extractors to Phase 8 index-first pattern could stall before completion. Some collectors (tables, lists, blockquotes) have complex logic that may be hard to refactor.

**Why It Could Happen**:
- Complex collectors (tables, lists) have nested iteration logic
- Developer fatigue during migration (repetitive work)
- Unclear how to convert some extractor patterns to index-first
- Testing each collector is time-consuming

**Impact if Realized**:
- **Partial Migration**: Some collectors still use old pattern (no performance gain)
- **Mixed Architecture**: Inconsistent codebase (maintainability issue)
- **Timeline Risk**: Could add 1-2 days debugging complex collectors

**Mitigation Plan**:
- ⏳ **Planned**: Create collector migration checklist (12/12 status tracker)
- ⏳ **Planned**: Migrate simple collectors first (links, images, headings)
- ⏳ **Planned**: Pair programming for complex collectors (tables, lists)
- ⏳ **Planned**: Add "no iteration" lint check to CI (ban `for tok in wh.tokens`)

**Probability Rationale** (3/5 - Moderate):
- 12 collectors is significant work
- Some collectors are complex
- But: Pattern is clear from Phase 1-4 work

**Impact Rationale** (3/5 - Moderate):
- Partial migration still provides some value
- Can finish remaining collectors post-launch
- But: Mixed architecture is technical debt

**Owner**: Dev Team
**Review Frequency**: Daily during Phase 5
**Target Resolution**: Phase 5 completion (12/12 collectors migrated)

---

## Risk History (Closed/Mitigated)

| # | Risk | Score Peak | Resolution Date | Outcome |
|---|------|------------|-----------------|---------|
| R0 | Test infrastructure missing blocks refactoring | 20 (4×5) | 2025-10-19 | ✅ **RESOLVED**: Phase 0 complete (4 test files + CI created) |

---

## Risk Categories

### Technical Risks
- R1: Baseline parity <80%
- R2: O(N+M) dispatch regression

### Execution Risks
- R3: Collector migration incomplete

### Security Risks
- (None currently active - Phase 10 validation planned)

### Timeline Risks
- R1, R3 could add 1-4 days delay

---

## Daily Update Template

**Date**: YYYY-MM-DD
**Phase**: [Current phase]
**Updates**:
- Risk [ID]: [Status change or new information]
- New risks identified: [List any new risks]
- Risks closed: [List any resolved risks]

**Top 3 Risks**: [Update scores if changed]
**Overall Risk Level**: [RED/YELLOW/GREEN]

---

## Scoring Guide

### Probability Scale (1-5)
1. **Very Low** (1-10%): Highly unlikely
2. **Low** (10-30%): Unlikely but possible
3. **Moderate** (30-50%): Could reasonably happen
4. **High** (50-70%): Likely to happen
5. **Very High** (70-90%+): Almost certain

### Impact Scale (1-5)
1. **Minimal**: <1 day delay, no production impact
2. **Low**: 1-2 day delay, minor workaround needed
3. **Moderate**: 2-5 day delay, temporary degradation
4. **High**: 1-2 week delay, production blocker
5. **Critical**: >2 week delay or architecture failure

### Risk Score Thresholds
- **1-5** (LOW): Monitor only
- **6-11** (MODERATE): Plan mitigation
- **12-15** (HIGH): Active mitigation required
- **16-25** (CRITICAL): Immediate action, escalate

---

## Mitigation Status Legend

- ✅ **Active**: Mitigation currently in place
- ⏳ **Planned**: Mitigation designed, not yet implemented
- 🔴 **Blocked**: Mitigation waiting on dependency
- ❌ **Failed**: Mitigation ineffective, need new approach

---

## Risk Owner Responsibilities

**Tech Lead**:
- Owns baseline parity risk (R1)
- Reviews parity tests daily during Phase 8
- Decides when to escalate if parity <70%

**Architect**:
- Owns performance risks (R2)
- Reviews complexity proofs
- Approves mid-phase benchmark results

**Dev Team**:
- Owns execution risks (R3)
- Updates collector migration checklist daily
- Flags complex collectors early

---

**Last Updated**: 2025-10-19
**Next Review**: Daily at start of Phase 1
**Escalation Path**: If score ≥16, escalate to project sponsor immediately
