# REGEX_REFACTOR_DETAILED — Drop-in Plan (Redlines Merged)

> **Objective**: Remove all regex-based Markdown parsing from `content_context.py` and `markdown_parser_core.py` and replace with **MarkdownIt / mdit-py-plugins** token traversal — with identical outputs and no material perf regression.

> **Status**: This document merges reviewer redlines. It is executable as-is and supersedes any earlier draft.

---

## 0) Canonical Rules

- **Single Source of Truth**: This file governs this refactor.  
- **Evidence-First**: Non-obvious edits require Evidence Blocks (see §6).  
- **Bounded Execution**: Only commands in §3 are allowed.  
- **No Network**: Pure structural validation; no HTTP reachability.  
- **YAGNI / KISS / SRP**: Implement only what is required; simplify; split responsibilities.  
- **No Hybrids**: Regex + token “mixed” paths are disallowed (see §4.3).  
- **HTML Hard-Off**: `html=False` at MarkdownIt init is mandatory (see §4.4).

---

## 1) Scope & Constraints

- **Edit Only**: `content_context.py`, `markdown_parser_core.py`.  
  (Test files may be added; no new runtime modules introduced.)  
- **Output Parity**: All MD→JSON outputs must be byte-identical.  
- **Perf Budget**: Δ **median** runtime ≤ **5%**, Δ **p95** ≤ **10%** (per-file and aggregate).  
- **Timeout Parity**: Cross‑platform timeout guard (thread/future+`result(timeout=...)`) must protect all parsing sections previously guarded by `signal`.  
- **Dataset (Golden Corpus)**: Path (authoritative):  
  `.../src/docpipe/md_parser_testing/test_mds/md_stress_mega/`  
  > The **canonical_count** is computed at test start by enumerating `*.md` files with matching JSON siblings and logged to the report. All pass/fail gates use **canonical_count** (resolves prior 494 vs 700+ inconsistency).

- **Reference Materials (Authoritative Inputs)**  
  - `Regex clean.md` — canonical regex→token mapping & rationale.  
  - `Regex_calls_with_categories__action_queue_.csv` — ordered regex conversion queue.  
  - `Regex_occurrences_in_provided_files.csv` — line spans for evidence.  
  - `token_replacement_lib.py` — vetted helpers (`iter_blocks`, `extract_links_and_images`).

---

## 2) Deliverables

1) **Refactoring Plan** — `REFACTORING_PLAN_REGEX.md`  
   - Table mapping each regex to its MarkdownIt replacement; include file+lines.  
2) **Code Changes** — in the two target files only.  
3) **Tests** — unit + light integration + performance harness.  
4) **Reports** — before/after parity and perf summaries (median, p95).  
5) **Evidence** — JSON objects per change set (see §6).

---

## 3) Commands (Execution Boundary)

```bash
uv run ruff check .
uv run mypy src/
uv run pytest --cov=src --cov-report=term-missing
uv run python -m docpipe.md_parser_testing.testing_md_parser
```
> If any command is missing/renamed, STOP with a clarification (template §7).

---

## 4) Design & Replacement Strategy

### 4.1 Categories → Strategies (authoritative)
| Category | Strategy |
|---|---|
| **Fences & Indented Code** | Use tokens where `token.type in {'fence','code_block'}`; line ranges from `token.map`; language from `token.info`. |
| **Links & Images** | Traverse `inline` children; for `link_open` read `attrs['href']`; for `image` read `attrs['src']` and derive alt from child text. Validate **scheme allow‑list** in Python. |
| **Headings / Lists / Tasks** | `heading_open` (`tag`→level), `bullet_list_open`, `ordered_list_open`, `list_item_open`; task list plugin for checkbox state. |
| **Inline → Plain Text** | Build text by concatenating inline `text` tokens; **ignore** `strong/em/code_inline` tokens instead of regex-stripping. |
| **Autolinks** | Enable `linkify=True`; validate `href` schemes on produced link tokens. |
| **HTML** | `html=False` mandatory; if a caller toggles `True`, raise or route through a single sanitizer that drops `html_inline/html_block` unless allow-listed. |

### 4.2 Intentionally Retained Regex (non-structural checks)
- **Data URI budgets** (e.g., `^data:image/` + max length)  
- **Scheme allow‑list/deny‑list** (final guard on `href/src`)  
- **Unicode confusables / mixed‑script heuristics** for security
> These are *content* checks, not Markdown structure; they remain regex-based and are documented in code.

### 4.3 No Hybrids Policy
- Remove regex paths **in the same commit** that introduces token traversal.  
- If a short bridge is unavoidable, gate it behind `MD_REGEX_COMPAT` (default **0** in tests).  
- The flag **must be removed** in the immediate next PR; PR will fail if the flag remains.

### 4.4 MarkdownIt Initialization (hard requirement)
```python
md = MarkdownIt("commonmark", options_update={"html": False, "linkify": True})
# enable table + tasklist plugins as used in repo
```
- Enforce `html=False` at init. Document caller behavior if altered (raise/sanitize).

### 4.5 Timeout Guard (cross‑platform)
- Replace any Unix‑only `signal.alarm` with a cross‑platform guard:  
  - Execute parsing in a worker (`concurrent.futures` or thread), call `result(timeout=...)`.  
  - On timeout, cancel and raise domain exception used by the monolith.

---

## 5) Test & Perf Methodology

1) **Golden Parity**  
   - Enumerate **canonical_count** from the dataset (see §1).  
   - For each MD file, compare produced JSON to the expected reference (byte‑identical).

2) **Performance Harness**  
   - **3× cold runs** (cleared cache) + **5× warm runs**.  
   - Report **per‑file** and **aggregate** **median** and **p95** (ms/file).  
   - Shuffle file order once to reduce cache bias.  
   - Pin Python + MarkdownIt versions in the report header.

3) **Edge Fixtures (must pass)**  
   - Unterminated fences; lazy‑indented blocks; code inside lists.  
   - Links with titles, escaped brackets `\[`, nested brackets.  
   - Tables with complex headers; task lists.  
   - Bare URLs; `data:image/*` with size near limit.  
   - Malicious HTML input (should be dropped with `html=False`).

---

## 6) Evidence Protocol (authoritative)

- For each non‑trivial change, add an Evidence JSON object to the PR body or `REFACTORING_PLAN_REGEX.md` (appendix).  
- **sha256** is computed on the **normalized‑whitespace** version of the quoted snippet.

**Schema**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Evidence",
  "type": "object",
  "required": ["quote", "source_path", "line_start", "line_end", "sha256", "rationale"],
  "properties": {
    "quote": {"type": "string", "minLength": 1},
    "source_path": {"type": "string", "minLength": 1},
    "line_start": {"type": "integer", "minimum": 1},
    "line_end": {"type": "integer", "minimum": 1},
    "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    "rationale": {"type": "string", "minLength": 1}
  }
}
```

**Example (Heading Regex → Token)**
```json
{
  "quote": "re.sub(r'^#{1,6}\\s+', '', line)",
  "source_path": "src/docpipe/markdown_parser_core.py",
  "line_start": 215,
  "line_end": 217,
  "sha256": "<64-hex>",
  "rationale": "Replace header detection with MarkdownIt `heading_open` tokens (level via tag, text via inline children)."
}
```

**Example (Fence Detection → Token)**
```json
{
  "quote": "m = re.match(r'^\\s*([`~])\\1{2,}(\\s*\\S.*)?\\s*$', line)",
  "source_path": "src/docpipe/content_context.py",
  "line_start": 44,
  "line_end": 50,
  "sha256": "<64-hex>",
  "rationale": "Use `fence`/`code_block` tokens and `token.map` for line ranges; language from `token.info`."
}
```

---

## 7) STOP Clarification Template

```json
{
  "type": "STOP_CLARIFICATION_REQUIRED",
  "reason": "<ambiguous construct | missing test harness | evidence gap | command unavailable>",
  "need": [
    {"what": "<file or command>", "why": "<1 sentence>", "proposed_next_step": "<smallest unblocker>"}
  ]
}
```

Trigger when confidence < 0.8, evidence missing, or boundaries exceeded.

---

## 8) Sequencing (Commit Order)

1) **Fences (regex → tokens)** — delete fence/indent regex and state machine.  
2) **Inline→Plain‑Text** — remove all markdown‑stripping regex; use inline token text.  
3) **Links & Images** — token traversal only; remove `[...] ( ... )` regex. **No hybrids**.  
4) **HTML** — enforce `html=False`; drop `html_inline/html_block` unless whitelisted.  
5) **Tables** — move entirely to token ranges; delete pipe/dash heuristics.  
6) **Security** — retain content regexes (data URI, schemes, confusables) and document as retained.

> Each step must maintain green tests on the entire corpus before proceeding.

---

## 9) Review Checklist (Gate to Merge)

- [ ] **Parity**: All outputs identical for **canonical_count** files.  
- [ ] **Performance**: Δ median ≤ 5%, Δ p95 ≤ 10% (per‑file & aggregate).  
- [ ] **No Hybrids**: No code paths mixing regex and tokens remain.  
- [ ] **Timeouts**: Cross‑platform guard in place.  
- [ ] **HTML**: `html=False` enforced; sanitizer path documented if toggled.  
- [ ] **Evidence**: Complete JSON objects with sha256 for each change set.  
- [ ] **Tooling**: `ruff` + `mypy` clean; tests green.  
- [ ] **Flag Removal**: Any temporary `MD_REGEX_COMPAT` removed (or PR fails).

---

## 10) Appendix — Implementation Hints

- Prefer one **parse pass** and walk the token stream to collect all structures; avoid re‑parsing per category.  
- Use `token.map` for line spans (start inclusive, end exclusive).  
- For headings: `level = int(token.tag[1])`; text from `inline.children[text]`.  
- For links: `href = dict(open.attrs or {}).get('href', '')`; link text from inline text children.  
- For images: `src` + `alt` (inline text children).  
- Keep the small slug utility but **derive source text from tokens**, not by stripping markdown with regex.

---

**Ready to execute.** This plan integrates redlines and locks the gates so the refactor lands safely and measurably.
