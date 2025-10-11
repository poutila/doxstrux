# REGEX_REFACTOR_POLICY_GATES
_A short, immutable rule sheet & CI checklist for the Markdown parser regex → MarkdownIt refactor._

> **Companion to:** `REGEX_REFACTOR_EXECUTION_GUIDE.md` and `REGEX_REFACTOR_DETAILED_MERGED_vNext.md`  
> **Audience:** reviewers, CI authors, release managers (not day‑to‑day implementers)

---

## 1) Immutable Policy (do not change without RFC)

1. **Single parse per document.** Build the token stream once; reuse for all extractors. Only front‑matter may trigger a second parse **if** the plugin verification passes.
2. **Iterative DFS only.** No recursive token walks in production paths.
3. **HTML off by default.** `html=False` at init. If a caller flips it, raise or route through the single sanitizer (default reject). `html_inline` tokens under `html=False` are logged as **warnings** only.
4. **Linkify parity.** Default **OFF** (`linkify=False`) unless a parity suite proves equivalence with legacy. If enabled, stamp profile & versions in the baseline header.
5. **Process isolation contract.** Strict profile uses a **top‑level worker** in a `ProcessPoolExecutor` that rebuilds the parser and returns a **serializable token view**. Moderate uses a thread guard. Error payloads identical in both.
6. **Security posture (fail‑closed).** Reject protocol‑relative URLs (`//…`), backslashes in any URL component, dotless hosts with schemes (`http:host/path`), control/zero‑width chars, malformed percent‑encodings; IDNA is applied **only** to `netloc`.
7. **Data‑URI budgets w/o decode.** Base64 size = `(len(b64)-padding)*3//4`. Non‑base64 size by bounded `%xx` counting with early bail‑out; never full‑decode to count.
8. **Retained regexes (structure must come from tokens):**
   - Data‑URI budget checks
   - Scheme allow/deny lists
   - Confusables / mixed‑script heuristics
   - **GFM table alignment** separator parsing  
   Tag each usage in code with `# REGEX RETAINED (§1.8)`.
9. **Evidence determinism.** Hash over **normalized** text: CRLF→LF, collapse all whitespace, UTF‑8, lowercase hex. Evidence validator runs in CI.
10. **Baseline comparability.** Gated comparisons are valid only when `profile`, Python, markdown‑it‑py + plugin versions, and **canonical pair count** match the baseline header. Otherwise regenerate a baseline in the PR.

---

## 2) CI Gates (all must pass)

- **G1 — No Hybrids:** No `USE_TOKEN_*`, `MD_REGEX_COMPAT`, or legacy regex parsing paths in `src/**.py` (tests/vendor excluded). Includes a **negative self‑test**.
- **G2 — Canonical Pairs:** Count only `.md` files that have a sibling `.json`. Drift is **blocking** unless the PR regenerates baseline artifacts.
- **G3 — Parity:** Byte‑identical JSONs for all canonical pairs.
- **G4 — Performance:** Per‑run **median** and **p95** within thresholds (Δmedian ≤ 5%, Δp95 ≤ 10%) in **moderate** profile; pooled stats are diagnostics only.
- **G5 — Evidence:** Evidence blocks present for non‑trivial changes and **hash‑valid** after normalization.
- **G6 — Profile & Versions:** Baseline/profile mismatch → mark run **incomparable** and require baseline regeneration in PR.
- **G7 — Security Warnings:** No **errors**; warnings allowed for `html_inline` under `html=False` and are reported.

---

## 3) Reference Paths & Artifacts

- **Baseline:** `baseline/perf_baseline.json`
- **Phase reports:** `reports/phase_*.json`
- **Final report:** `reports/final_summary.json`
- **Policy files:** this file; `REGEX_REFACTOR_EXECUTION_GUIDE.md`; `REGEX_REFACTOR_DETAILED_MERGED_vNext.md`
- **Adapters:** `token_adapter.py`

---

## 4) CI Snippets (portable; pure Python)

### 4.1 Gate G1 — No Hybrids (recursive, with negative self‑test)
```python
# ci_gate_no_hybrids.py
import sys, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(r"(USE_TOKEN_[A-Z_]+|MD_REGEX_COMPAT|LEGACY_REGEX_PARSER)")

def iter_py_files(root: pathlib.Path):
    for p in root.rglob("*.py"):
        rp = p.relative_to(root)
        if str(rp).startswith(("tests/", "vendor/", ".venv/", "venv/")):
            continue
        yield p

def main():
    bad = []
    for p in iter_py_files(ROOT / "src"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if FORBIDDEN.search(text):
            bad.append(str(p))
    # negative self-test
    sentry = ROOT / "scripts" / "ci_negative_test__hybrid_probe.txt"
    if not sentry.exists():
        sentry.write_text("USE_TOKEN_SHOULD_FAIL", encoding="utf-8")
        print("Created negative self-test probe. Re-run job.", file=sys.stderr)
        sys.exit(2)
    if bad:
        print("Forbidden hybrid flags found in:", *bad, sep="\n- ")
        sys.exit(1)
    print("G1 OK")
if __name__ == "__main__":
    main()
```

### 4.2 Gate G2 — Canonical Pair Count
```python
# ci_gate_canonical_pairs.py
import sys, json
from pathlib import Path

DATASET = Path("path/to/corpus")  # keep in CI env/config
def canonical_pairs(root: Path):
    pairs = []
    for md in root.rglob("*.md"):
        js = md.with_suffix(".json")
        if js.exists():
            pairs.append((md, js))
    return pairs

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else DATASET
    pairs = canonical_pairs(root)
    print(json.dumps({"canonical_count": len(pairs), "root": str(root)}))
if __name__ == "__main__":
    main()
```

### 4.3 Gate G5 — Evidence Hash Validator
```python
# ci_gate_evidence_hash.py
import sys, re, json, hashlib
from pathlib import Path

WHITESPACE = re.compile(r"\s+")

def norm(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n").strip()
    s = WHITESPACE.sub(" ", s)
    return s

def sha256_norm(s: str) -> str:
    return hashlib.sha256(norm(s).encode("utf-8")).hexdigest()

def main():
    # naive example: scan PR text / local EVIDENCE.jsonl
    path = Path(sys.argv[1])
    ok = True
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        want = obj.get("sha256")
        have = sha256_norm(obj.get("quote", ""))
        if want and want != have:
            print(f"BAD EVIDENCE: sha mismatch for {obj.get('source_path')}")
            ok = False
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

---

## 5) Profiles & Thresholds

- **Profiles:** `moderate` (threads), `strict` (process) — both wrap the **single parse** step. Front‑matter parse uses the **same** profile.
- **Perf thresholds:** Δmedian ≤ **5%**, Δp95 ≤ **10%** (per‑run). Shuffle seed is printed and stored.
- **Memory notes:** `tracemalloc` tracks allocator peaks (not RSS). Gate: warn at **+20%**, fail at **+50%** median vs baseline.

---

## 6) Link & Plaintext Policy (parity‑critical)

- **Plaintext:** concatenate only `text` nodes; `softbreak`/`hardbreak` → space; **policy: include `code_inline` text** (unless tests show legacy excluded it).  
- **Links:** collect descendant text between `link_open`…`link_close` at same depth; **include image alt text** by default.  
- **Autolinks:** `linkify=False` by default; enable only with proof of parity.

---

## 7) Retained Regex Inventory (must not grow)

- Data‑URI budget checks (size only)
- Scheme allow/deny (`http|https|mailto` allow; others reject)
- Confusables / mixed‑script heuristics
- GFM alignment row parsing (`parse_gfm_alignment(sep_line)`)

Every retained regex is centralized and unit‑tested; each site carries `# REGEX RETAINED (§7)`.

---

## 8) What blocks a PR (summary)

- Any hybrid flag or legacy regex parser path found (G1).  
- Canonical pair drift without baseline regeneration (G2).  
- Parity or perf gates fail (G3–G4).  
- Evidence blocks missing or hash invalid (G5).  
- Profile/versions mismatch (G6) or missing in artifacts.  
- Security policy violations promoted to **errors**.

---
