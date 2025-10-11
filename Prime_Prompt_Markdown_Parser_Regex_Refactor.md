# 🧭 **Prime Prompt — Markdown Parser Regex Refactor**

> **Role:** Senior Refactor Engineer  
> **Goal:** Replace all regex-based parsing in  
> `content_context.py` and `markdown_parser_core.py`  
> with structured parsing via **MarkdownIt / mdit-py-plugins**,  
> preserving identical I/O behavior and performance.

---

## 0 – Ground Rules

- **Single source of truth:** This prompt governs the task; no other spec overrides it.  
- **Evidence-first:** Every non-obvious change must include a verifiable quote (see § 5).  
- **Bounded execution:** Only commands listed in § 3 are permitted.  
- **YAGNI / KISS / SOLID:** Refactor for necessity, simplicity, and single responsibility only.  
- **No network access:** No live HTTP checks; validation is structural only.  
- **DX > rigidity:** Keep developer UX pleasant—fail early, message clearly.

---

## 1 – Deliverables

1. **Refactoring Plan** — `REFACTORING_PLAN_REGEX.md`  
   - Map every regex → library feature or token traversal.  
   - Show before/after code references with line spans.
2. **Tests** — unit + light integration verifying:
   - identical outputs (700 + MD → JSON pairs)  
   - no performance regression (> ±5 %)
3. **Docs** — concise description of MarkdownIt pipeline and replacement rationale.
4. **Testing Harness** — function(s) runnable before/during/after refactor.

---

## 2 – Scope & Constraints

- **Files modified:** only  
  `content_context.py` and `markdown_parser_core.py`.  
  (Test files may be added; no new runtime modules.)
- **Backward compatibility:** not required; output parity is.
- **Zero I/O mutation:** All `.json` outputs must remain byte-identical.
- **Test dataset:**  
  `/home/lasse/Documents/SERENA/MD_ENRICHER_cleaned/src/docpipe/md_parser_testing/test_mds/md_stress_mega/`
  — > 700 Markdown / JSON pairs used for before/after validation.

### Reference Materials (Authoritative Inputs)

* **Regex clean.md** — Canonical mapping of regex → Markdown-It token replacements.
* **Regex_calls_with_categories__action_queue_.csv** — Ordered checklist of all regex uses to convert.
* **Regex_occurrences_in_provided_files.csv** — Evidence source for line spans and hashes.
* **token_replacement_lib.py** — Verified helper library for heading/code/link/image extraction.

> All replacements and evidence in this refactor must trace back to these four sources.
> Any deviation requires a STOP_CLARIFICATION_REQUIRED object citing the file and reason.

---

## 3 – Execution Boundaries & Commands

```bash
uv run ruff check .
uv run mypy src/
uv run pytest --cov=src --cov-report=term-missing
uv run python -m docpipe.md_parser_testing.testing_md_parser
```

Stop if any command is missing or renamed; issue a STOP Clarification.

---

## 4 – Success Criteria

| # | Requirement | Metric |
|---|--------------|--------|
| 1 | Functional parity | All test pairs identical |
| 2 | Performance parity | Δ runtime ≤ ±5 % |
| 3 | Regex removal | All Markdown-parsable constructs handled by MarkdownIt |
| 4 | Evidence blocks | All non-trivial edits justified |
| 5 | Lint + type clean | ruff + mypy pass |

---

## 5 – Evidence & Traceability

Each major change requires an **Evidence block**:

```json
{
  "quote": "re.sub(r'^#{1,6}\\s+', '', line)",
  "source_path": "src/docpipe/md_parser_core.py",
  "line_start": 215,
  "line_end": 217,
  "sha256": "<64-hex>",
  "rationale": "Heading detection replaced by MarkdownIt heading_open token."
}
```

Schema is identical to the original governance file.

---

## 6 – STOP Template

```json
{
  "type": "STOP_CLARIFICATION_REQUIRED",
  "reason": "<ambiguous construct | missing test harness | evidence gap>",
  "need": [
    {"what": "<file or command>", "why": "<reason>", "proposed_next_step": "<smallest unblocker>"}
  ]
}
```

Trigger whenever confidence < 0.8 or evidence missing.

---

## 7 – Refactor Design Outline

### 7.1 Conversion Principles
| Regex Pattern Category | Replacement Strategy |
|-------------------------|----------------------|
| Code fence / indented block | `token.type in {'fence','code_block'}` → `token.map` |
| Link / Image | Traverse `link_open` and `image` tokens → `attrs['href'/'src']` |
| Heading / List / Task List | `heading_open`, `bullet_list_open`, `ordered_list_open`, `list_item_open` (+ task plugin) |
| Inline format (*_``) | Concatenate inline `text` tokens only |
| Autolink / URL | `linkify=True` → validate schemes |
| HTML sanitization | `html=False` or drop `html_inline`/`html_block` tokens |

### 7.2 Token Traversal Helpers
Use a local utility (no new package) to:
- iterate tokens,  
- map line ranges (`token.map`),  
- collect headings, links, images.

Reference: **token_replacement_lib.py**

---

## 8 – Testing Strategy

1. **Golden Corpus Regression:** run all 700 pairs before/after.  
2. **Microbenchmarks:** measure wall-clock Δ.  
3. **Unit coverage:** add tests for replaced regex categories.

---

## 9 – Implementation Steps (Lean 8-Step)

1. Baseline tests on current monolith.  
2. Catalog all regexes (already done).  
3. Replace regex → MarkdownIt tokens incrementally using `Regex_calls_with_categories__action_queue_.csv`.  
4. Verify test parity each batch.  
5. Remove redundant regex imports.  
6. Optimize token iteration.  
7. Document replacements in `REFACTORING_PLAN_REGEX.md`.  
8. Submit PR with Evidence blocks.

---

## 10 – Review Checklist

- [ ] Test harness exists and runs on dataset  
- [ ] All regex constructs replaced by token logic  
- [ ] Evidence blocks complete  
- [ ] ruff + mypy pass  
- [ ] Performance report attached  

---

## 11 – Final Instruction

Proceed with the refactor exactly per this prompt.  
If a construct cannot be expressed through MarkdownIt tokens, respond with a `STOP_CLARIFICATION_REQUIRED` object identifying the construct and proposed resolution.  
Otherwise, deliver:  
**(a)** updated code, **(b)** `REFACTORING_PLAN_REGEX.md`, and **(c)** full test reports.
