# REGEX_REFACTOR_EXECUTION_GUIDE
_A lean, operator-focused playbook for the Markdown parser regex → MarkdownIt refactor._

> **Scope (code change):** `content_context.py`, `markdown_parser_core.py`  
> **Non-goals here:** policy debates, governance philosophy, long rationale. See `REGEX_REFACTOR_POLICY_GATES.md` for rules, CI gates, retained-regex inventory, and evidence schema.

---

## 0) Quick Principles (what to keep in mind while executing)
- **One parse, many traversals.** Build the token stream once; reuse it for headings, code blocks, links/images, plaintext.
- **No hybrids in PRs.** Feature flags okay locally; **must be absent** in PRs (CI enforces).
- **Delete regex when you add token logic.** Same commit removes the redundant regex path.
- **Fail closed.** `html=False`, strict URL and data-URI validation, timeouts around every parse step.
- **Parity first.** Never proceed to next phase until the full corpus (canonical pairs) passes byte-identical output.

---

## 1) Prerequisites
- Python env ready (`uv`, `pytest`, `ruff`, `mypy` installed).
- Dataset path for the **canonical corpus** (md + json pairs).
- Baseline JSON (generated in §2).  
- **Tools available locally:**  
  - `token_replacement_lib.py` (helpers: `iter_blocks`, `extract_links_and_images`)  
  - `Regex_clean.md`, `Regex_calls_with_categories__action_queue_.csv`

---

## 2) One-time Baseline (run before touching code)
```bash
uv run ruff check .
uv run mypy src/
# Baseline parity + perf (moderate profile, linkify same as current behavior)
uv run python -m docpipe.md_parser_testing.testing_md_parser --profile=moderate --seed=1729 --runs-cold=3 --runs-warm=5 --emit-baseline baseline/perf_baseline.json
```
**What to capture automatically:**
- canonical **pair count** (md+json) and the corpus path
- Python / OS / CPU summary
- markdown-it-py + plugins exact versions
- profile: `moderate`
- medians + p95 (per-run + aggregate), tracemalloc medians
- shuffle seed printed once and saved

---

## 3) Phase Plan (commit-by-commit)

### Phase 1 — Fences & indented code (regex → tokens)
- Replace custom fence/indent detection with tokens: `type in {'fence','code_block'}`, line span via `token.map`, language via `token.info`.
- **Delete** old regex/state-machine paths in the same commit.
- **Fixtures to check:** unterminated fence; list-nested fence; info string; minimal ```/~~~.
- **Run:** `uv run python -m docpipe.md_parser_testing.testing_md_parser --profile=moderate`  
- **Gate:** 100% parity; perf within Δmedian ≤5%, Δp95 ≤10% vs baseline.

### Phase 2 — Inline → Plaintext (strip markdown → token text)
- Replace “strip markdown” regex with inline token traversal; concatenate only `text` nodes.
- **Policy decision:** include or drop `code_inline`? (stick to plan; update tests accordingly)
- **Run & Gate:** same as Phase 1.

### Phase 3 — Links & Images (regex → tokens)
- Traverse inline tokens: `link_open`/`link_close` span collection; collect text from nested descendants.
- `image` attrs: `src`, alt from children. Validate scheme allowlist.
- **No hybrids:** remove `[...] ( ... )` regex.
- **Run & Gate:** same as Phase 1.

### Phase 4 — HTML handling
- Enforce `html=False` at parser init. If toggled externally, **raise** or run through a single sanitizer (documented), but default reject.
- Treat `html_inline` tokens under `html=False` as **warnings** (plugin quirks), not errors.
- **Run & Gate:** same as Phase 1.

### Phase 5 — Tables
- Use table tokens; for alignment, call centralized retained utility `parse_gfm_alignment(sep_line)` (format regex retained, tagged).
- **Run & Gate:** same as Phase 1.

### Phase 6 — Security regex (retained)
- Keep **content** regex only: data-URI budgets, scheme allow/deny, confusables/mixed-script.
- Centralize in `security/validator.py` or equivalent section in the monolith for now.
- **Run & Gate:** same as Phase 1.

> **Rule:** After each phase: commit with message `refactor(phase-X): …`, include Evidence blocks in PR body, and re-generate perf delta JSON.

---

## 4) Commands (repeat each phase)
```bash
uv run ruff check .
uv run mypy src/
uv run pytest -q
uv run python -m docpipe.md_parser_testing.testing_md_parser \
  --profile=moderate --seed=1729 --runs-cold=3 --runs-warm=5 \
  --compare-baseline baseline/perf_baseline.json \
  --emit-report reports/phase_X.json
```
**Fast path for local iteration:** `TEST_FAST=1` → `--runs-cold=1 --runs-warm=1`

---

## 5) Timeouts (where to wrap)
- Wrap the **single parse** in `_parse_with_timeout()` (thread by default, process in strict profile).
- Use the **same wrapper** for any front-matter parse (if needed). Prefer **single parse** and reuse tokens.
- Configurable time limit comes from the security profile.

---

## 6) Process isolation (strict profile only)
- Don’t pass `self.md` or `Token` objects to processes. Use a **top-level worker** that constructs the parser in the child and returns **serializable** token summaries + env-frontmatter.
- Toggle with: `--profile=strict` (CI nightly or hostile-input tests).

---

## 7) URL & Data-URI validation (practical cut list)
- Reject: protocol-relative `//…`, control chars, zero-widths, backslashes in netloc/path, dotless-host (`http:host/…`), invalid/ambiguous percent-encoding.
- Allow: `http`, `https`, optional `mailto`, `#fragment` (local anchors).
- Data-URI: O(1) base64 size estimate (`floor((len(b64)-padding)*3/4)`), and bounded `%xx` counting for non-base64 **without** full decode. Stop once over limit.

---

## 8) Evidence Blocks (drop these into PR body)
```json
{
  "quote": "re.sub(r\"^#{1,6}\\s+\", \"\", line)",
  "source_path": "src/docpipe/markdown_parser_core.py",
  "line_start": 215,
  "line_end": 217,
  "sha256": "<64-hex-of-normalized>",
  "context_before": ["  # earlier line"],
  "context_after":  ["  # next line"],
  "rationale": "Use MarkdownIt heading_open tokens; level from tag, text from inline descendants."
}
```
**Normalization for `sha256`:** strip → `\r\n` → `\n` → collapse whitespace → UTF‑8 → lowercase hex.

---

## 9) Checkpoints & Rollback
- **Checkpoint (pass gates):** commit, push branch, open PR with Evidence blocks.
- **If parity fails:** revert the last hunk; re-run fast path; re-apply with smaller deltas.
- **If perf gate fails:** profile hotspots; verify parser reuse; disable `linkify` if legacy behavior didn’t autolink.
- **If hybrid found in PR:** remove flag/regex path; CI must pass grep checks.

---

## 10) CI expectations (what will fail a PR)
- Any `USE_TOKEN_*`, `MD_REGEX_COMPAT`, or legacy regex path present in src (tests/vendor excluded).
- Canonical pair count drift vs baseline **without** a regenerated baseline.
- Parity failure on full corpus; perf over Δmedian 5% / Δp95 10% (moderate profile).
- Evidence hash mismatch (validator runs), or missing Evidence blocks for major changes.
- Plugin/version drift not recorded in the report header.

---

## 11) Troubleshooting quick map
- **RecursionError on deep docs** → replace all recursive walks with the iterative walker.
- **Autolink parity diffs** → set `linkify=False` to match legacy; document the policy.
- **Front-matter missing** → STOP: retain regex and file an issue; don’t ship sliced guess.
- **Huge data-URIs** → confirm O(1) size check; ensure limit is enforced before any decode.

---

## 12) Done criteria (green-light to merge)
- CI gates pass (no hybrids, pairs OK, parity OK, perf within budget, evidence valid).
- Retained-regex inventory matches the policy file.
- Phase commits squash-merged or kept atomic per team preference.
- Baseline updated (if corpus changed) with versions and profile stamped.

---

## 13) Appendix — Tiny utility snippets

**Iterative token walker**
```python
def walk_tokens_iter(tokens):
    stack=[(tokens,0)]
    while stack:
        lst,i=stack.pop()
        if i>=len(lst): 
            continue
        tok=lst[i]
        stack.append((lst,i+1))
        yield tok
        if getattr(tok, "children", None):
            stack.append((tok.children,0))
```

**Collect link text (descendants until matching close)**
```python
def collect_link_text(tokens, start_idx):
    depth=0; out=[]
    for i in range(start_idx, len(tokens)):
        t=tokens[i]
        if t.type=="link_open": depth+=1
        elif t.type=="link_close":
            depth-=1
            if depth==0: break
        elif depth>0 and t.type=="text":
            out.append(t.content)
        if t.children:
            # manually walk children
            for c in walk_tokens_iter(t.children):
                if depth>0 and c.type=="text":
                    out.append(c.content)
    return "".join(out)
```
