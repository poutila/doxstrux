# Phase/Test/Gate Dependency Matrix

**Date**: 2025-10-19
**Purpose**: One-page visual mapping of phases → test scaffolds → CI gates → unlocks
**Audience**: Newcomers and execution team

---

## Quick Reference: What Unlocks What

```
Phase 0 (Prep) → Creates test scaffolds → Enables Phase 1-4
Phase 1 (Indices) → Unlocks Phase 2 (section_of needs indices)
Phase 2 (section_of) → Unlocks Phase 3 (helpers need section lookup)
Phase 3 (Helpers) → Unlocks Phase 4 (dispatch needs helpers)
Phase 4 (Dispatch) → Unlocks Phase 5 (collectors need dispatch)
Phase 5 (Collectors) → Unlocks Phase 6 (API needs collectors)
Phase 6 (API Shim) → Unlocks Phase 8 (baseline parity)
Phase 8 (Parity) → Unlocks Phase 9 (CI/monitoring)
Phase 9 (CI Tools) → Unlocks Phase 10 (security validation)
```

---

## Detailed Dependency Matrix

| Phase | Test Scaffolds Required | CI Gates | Success Criteria | Unlocks | Estimated Time |
|-------|------------------------|----------|------------------|---------|----------------|
| **Phase 0: Preparation** | - | - | 4 test files + 1 CI workflow created | Phase 1-4 can begin | ✅ 0.75d (DONE) |
| **Phase 1: Build Indices** | `test_indices.py` (20 tests) | Unit tests green | All 7 indices built & tested:<br>- by_type<br>- pairs + pairs_rev<br>- parents<br>- children<br>- sections<br>- _line_starts | Phase 2 (section_of) | 1-2 days |
| **Phase 2: section_of()** | `test_section_of.py` (13 tests) | Unit tests green + O(log N) verified | Binary search working:<br>- starts[] + ends[] arrays<br>- Edge cases handled<br>- Performance O(log N) | Phase 3 (helpers) | 0.5-1 day |
| **Phase 3: Helper Methods** | `test_helper_methods.py` (18 tests) | Unit tests green + **Benchmark gate** | 8 helpers implemented:<br>- find_close(), find_parent()<br>- tokens_between(), text_between()<br>- get_line_range(), get_token_text()<br>- **Mid-phase benchmark passed** | Phase 4 (dispatch) | 1 day |
| **Phase 4: O(N+M) Dispatch** | `test_dispatch.py` (17 tests) | Unit tests green + Complexity proof | Single-pass dispatch:<br>- Routing table built<br>- O(N+M) verified (not O(N×M))<br>- visited_tokens == len(tokens) | Phase 5 (collectors) | 1-2 days |
| **Phase 5: Collector Migration** | Existing 23 collector tests | Collector tests green + No-iteration check | All 12 collectors migrated:<br>- Use indices (not iteration)<br>- Checklist: 12/12 ✓<br>- Performance maintained | Phase 6 (API) | 2-3 days |
| **Phase 6: API Shim** | `test_api_compat.py` | API compatibility tests green | MarkdownParserCore matches src:<br>- All extract_*() methods<br>- parse() returns compatible dict<br>- Import path works | Phase 8 (parity) | 1 day |
| **Phase 7: Complete Tests** | 15 additional test files | ≥80% coverage gate | 38 total test files:<br>- 23 existing<br>- 15 new<br>- Coverage ≥80% | Parallel to Phase 8 | 1.5 days |
| **Phase 8: Baseline Parity** | 542 baseline tests | ≥80% parity gate (447/542) | Baseline compatibility:<br>- 542 test_mds files<br>- ≥80% byte-for-byte match<br>- No critical regressions | Phase 9 (CI) | 2-4 days |
| **Phase 9: CI & Monitoring** | - | CI pipeline green | 3 monitoring tools created:<br>- check_performance_regression.py<br>- visualize_baseline_diffs.py<br>- coverage_breakdown.py | Phase 10 (security) | 0.25 days |
| **Phase 10: Security Validation** | 17 adversarial corpora | Security tests green | All adversarial corpora pass:<br>- XSS prevention<br>- Unicode safety<br>- DoS limits enforced | Production ready | 0.5 days |

**Total Critical Path**: Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 8 → Production (13-20 days)

---

## Critical Path Visualization

```
START
  ↓
┌─────────────────┐
│  Phase 0: Prep  │ ← Creates test infrastructure
│  (0.75d) ✅     │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 1: Indices│ ← Builds core data structures
│  (1-2d)         │   Needs: test_indices.py
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 2: Binary │ ← section_of() O(log N)
│ Search (0.5-1d) │   Needs: test_section_of.py + indices
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 3: Helpers│ ← 8 helper methods
│  (1d) **GATE**  │   Needs: test_helper_methods.py + section_of
└────────┬────────┘   🔍 MID-PHASE BENCHMARK CHECKPOINT
         ↓
┌─────────────────┐
│ Phase 4: Dispatch│ ← O(N+M) single-pass
│  (1-2d)         │   Needs: test_dispatch.py + helpers
└────────┬────────┘
         ↓
┌─────────────────┐
│Phase 5: Collectors│ ← Migrate all 12 collectors
│  (2-3d)         │   Needs: Collector tests + dispatch
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 6: API    │ ← MarkdownParserCore shim
│  (1d)           │   Needs: test_api_compat.py + collectors
└────────┬────────┘
         ↓
  ┌──────┴──────┐
  ↓             ↓
┌─────────┐ ┌──────────┐
│ Phase 7 │ │ Phase 8  │ ← Baseline parity (CRITICAL)
│ Tests   │ │ Parity   │   Needs: 542 baseline tests
│ (1.5d)  │ │ (2-4d)   │   Gate: ≥80% pass (447/542)
└─────────┘ └────┬─────┘
               ↓
         ┌──────┴──────┐
         ↓             ↓
    ┌─────────┐  ┌──────────┐
    │ Phase 9 │  │ Phase 10 │
    │ CI Tools│  │ Security │
    │ (0.25d) │  │ (0.5d)   │
    └─────────┘  └────┬─────┘
                      ↓
                 PRODUCTION
```

---

## Test Scaffold → Phase Mapping

| Test File | Tests Phase | Created Status | Filled During | Purpose |
|-----------|-------------|----------------|---------------|---------|
| `test_indices.py` | Phase 1 | ✅ Created | Step 1 implementation | Verify by_type, pairs, parents, children, sections indices |
| `test_section_of.py` | Phase 2 | ✅ Created | Step 2 implementation | Verify binary search O(log N) performance |
| `test_helper_methods.py` | Phase 3 | ✅ Created | Step 3 implementation | Verify 8 helper methods (find_close, tokens_between, etc.) |
| `test_dispatch.py` | Phase 4 | ✅ Created | Step 4 implementation | Verify O(N+M) single-pass dispatch, routing table |
| `test_api_compat.py` | Phase 6 | ⏳ Pending | Step 6 implementation | Verify MarkdownParserCore API matches src/ |
| `test_collectors_*.py` (12 files) | Phase 5 | ⏳ Pending | Step 5 collector migration | Verify each collector uses indices (not iteration) |
| **23 existing tests** | Ongoing | ✅ Exists | Background validation | Security, performance, warehouse, collector tests |

---

## CI Gate Details

### Gate 1: Unit Tests Green (Phases 1-6)
- **Trigger**: After each phase implementation
- **Check**: pytest exit code 0
- **Required Coverage**: ≥80% on modified files
- **Blocker**: Phase cannot proceed if tests fail

### Gate 2: Mid-Phase Benchmark (Phase 3)
- **Trigger**: After helper methods implemented
- **Tool**: `tools/benchmark_dispatch.py` (NEW - Recommendation #3)
- **Check**: Dispatch overhead baseline established
- **Purpose**: Detect routing table regressions BEFORE collector migration
- **Metrics**:
  - Routing table lookup time (μs)
  - Memory overhead (KB)
  - Dispatch loop overhead vs src/

### Gate 3: Complexity Proof (Phase 4)
- **Trigger**: After dispatch_all() rewrite
- **Check**: `visited_tokens == len(tokens)` (hard invariant)
- **Test**: `test_dispatch_single_pass_hard_invariant()`
- **Purpose**: Prove O(N+M) not O(N×M)

### Gate 4: Baseline Parity (Phase 8)
- **Trigger**: After API shim complete
- **Tool**: `tools/baseline_test_runner.py`
- **Check**: ≥80% of 542 tests byte-for-byte identical (447/542 minimum)
- **Blocker**: Cannot proceed to production below 80%

### Gate 5: Security Validation (Phase 10)
- **Trigger**: Before production rollout
- **Tool**: `tools/run_adversarial.py`
- **Check**: All 17 adversarial corpora handled safely
- **Coverage**: XSS, SSTI, unicode, DoS, etc.

---

## Dependency Edge Cases

### "What if Phase 2 fails?"
- **Blocker**: Cannot proceed to Phase 3
- **Fix Path**: Debug binary search, review section index build
- **Fallback**: Implement linear scan temporarily (but mark as tech debt)

### "What if baseline parity <80%?"
- **Blocker**: Cannot deploy to production
- **Fix Path**:
  1. Analyze diff with `tools/visualize_baseline_diffs.py`
  2. Fix output structure mismatches
  3. Iterate until ≥80%
- **No Fallback**: This is a hard requirement

### "What if mid-phase benchmark shows regression?"
- **Not a Blocker**: Can proceed, but investigate cause
- **Purpose**: Early warning, not hard gate
- **Action**: Record regression, plan fix before Phase 5

### "Can Phase 7 (tests) run in parallel with Phase 8 (parity)?"
- **Yes**: Phase 7 is additive, doesn't block parity
- **Benefit**: Saves 1.5 days on critical path
- **Risk**: Low - tests validate finished work

---

## Fast-Track Dependencies (72-Hour Plan)

| Day | Phases | Dependencies | Gates |
|-----|--------|--------------|-------|
| **Day 1** | Phase 1-3 | test_indices.py → test_section_of.py → test_helper_methods.py | Unit tests green |
| **Day 2** | Phase 4-5 | test_dispatch.py → Collector migration (3 collectors only) | Complexity proof + collector tests |
| **Day 3** | Phase 6, 8 | test_api_compat.py → baseline_test_runner.py | API compat + ≥80% parity |

**Shortcuts in 72-hour plan**:
- Only migrate 3 collectors (vs 12)
- Skip Phase 7 (test completion)
- Skip Phase 9 (CI tools)
- Skip Phase 10 (security)
- Accept lower parity threshold temporarily (60% vs 80%)

---

## Summary: Unlock Chains

**To start Phase 1**: Need Phase 0 complete ✅
**To start Phase 2**: Need Phase 1 complete (indices built)
**To start Phase 3**: Need Phase 2 complete (section_of working)
**To start Phase 4**: Need Phase 3 complete (helpers working) + **benchmark gate passed**
**To start Phase 5**: Need Phase 4 complete (dispatch working)
**To start Phase 6**: Need Phase 5 complete (collectors migrated)
**To start Phase 8**: Need Phase 6 complete (API shim working)
**To go to production**: Need Phase 8 complete (≥80% parity) + Phase 10 complete (security validated)

**Critical Path**: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 8 → 10 → Production

**Parallel Work**: Phase 7 (tests) can run alongside Phase 8 (parity)

---

**Last Updated**: 2025-10-19
**Next Update**: Before Phase 1 begins
**Owner**: Refactoring Team
