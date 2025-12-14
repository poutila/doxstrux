Dead Code Analysis Report
Executive Summary
Scanned: src/doxstrux/ (vulture at 60% confidence)
Candidates: 70+ items flagged
Confirmed Dead: 2 items (revised after validation)
Test-Only (Keep): ~40 items (classes/methods with test coverage)
False Positives: ~30 items (dataclass fields, attributes)

---

## ⚠️ VALIDATION FEEDBACK (2025-12-13)

**Original report claimed 3 dead items. After validation: only 2 confirmed.**

| Item | Original Claim | Validation Result |
|------|----------------|-------------------|
| `sanitize()` | Dead (0 callers) | **WRONG** - 25+ calls in tests |
| `_slugify_base()` | Dead | ✅ Confirmed |
| `MarkdownPluginError` | Dead | ✅ Confirmed |

**`sanitize()` validation details:**
- `tests/test_phase3_fail_closed.py`: 4 calls
- `test_scripts/test_sanitize.py`: 12 calls
- `test_scripts/test_enterprise_security.py`: 7 calls
- `test_scripts/test_critical_fixes.py`: 2 calls

The claim "grep returns 0 results" was factually incorrect.

**Revised totals:**
- Lines recoverable: ~10 (not ~80)
- Items to delete: 2 (not 3)

---

✅ Confirmed Dead Code - Safe to Remove

### ~~1. MarkdownParserCore.sanitize() (lines 705-776)~~ ❌ INVALIDATED

| Item | Details |
|------|---------|
| Status | **NOT DEAD** - Used in tests |
| Evidence | 25+ calls found in `tests/` and `test_scripts/` |
| Recommendation | **KEEP** - Active test coverage |

2. MarkdownParserCore._slugify_base() (lines 1884-1889)
Item	Details
File	markdown_parser_core.py
Lines	1884-1889 (6 lines)
Evidence	Only defined, never called. Delegated to sections.slugify_base()
Comment	"Phase 7.6.1: Delegated to extractors/sections.slugify_base()"
Recommendation: DELETE. This is a dead wrapper with zero callers.

3. MarkdownPluginError exception class (line 13)
Item	Details
File	markdown/exceptions.py
Line	13
Evidence	Defined but never raised anywhere in codebase
Recommendation: DELETE. Exception class with no raise statements.

⚠️ Test-Only Code (NOT Dead - Keep For Testing)
These items are flagged by vulture but are used in tests. They are intentionally public for test coverage:

Module	Items	Test File
budgets.py	NodeBudget, CellBudget, get_max_injection_scan_chars	test_budgets.py
token_utils.py	collect_text_between_tokens, TokenAdapter, iter_blocks, extract_links_and_images	test_token_utils.py, test_runtime_robustness.py
ir.py	ChunkPolicy, Chunk, ChunkResult dataclass fields	test_document_ir.py
rag_guard.py	safe_for_embedding, safe_for_tools attributes	test_rag_guard.py
Decision: KEEP. These are public API for testing security invariants.

False Positives (Dataclass Fields)
Vulture flags dataclass fields and NamedTuple fields as "unused" because they're set at construction time:

ir.py:131-143 - ChunkPolicy dataclass fields
ir.py:165-173 - Chunk dataclass fields
validators.py:56 - PromptInjectionCheck.error field
Decision: KEEP. These are structural definitions, not executable code.

Summary
| Category | Count | Action |
|----------|-------|--------|
| Confirmed Dead | 2 | DELETE |
| Test-Only | ~40 | KEEP |
| False Positives | ~31 (includes sanitize) | KEEP |

Lines Recoverable (Revised)
| Item | Lines |
|------|-------|
| ~~sanitize()~~ | ~~70~~ KEEP |
| _slugify_base() | ~6 |
| MarkdownPluginError | ~4 |
| **Total** | **~10 lines** |

