# FDP Orientation: How to Operate Fact-Driven Planning (FDP)

**Purpose**: Onboard implementers and AI assistants into *operational* FDP behavior—tool-first, evidence-backed decisions, and drift-resistant plans.  
**Audience**: Implementers, AI assistants, orchestrators  
**Status**: Active orientation (“front door”); **not** a canonical source of truth  
**Source**: Transformed from `TO_UNDERSTAND_WHAT_APPLYING_FDP_MEANS.md`

---

## 1) FDP in one sentence

**FDP is a protocol that replaces “I think” with “I queried” by requiring runnable evidence blocks for claims that matter.**

If your plan contains assumptions that could cause drift, FDP converts them into verified facts and decision guardrails.

---

## 2) Your operating constraints (non‑negotiables)

This orientation does **not** redefine canonical content. It only teaches how to *behave*.

**Single Source of Truth (SSOT) owners:**
- Evidence block schema, hard-stops, validation, versioning → `FDP_SCHEMA.md`
- 7-phase execution protocol, deliverables, tool enforcement, quality gates → `FDP_AI_WORKFLOW.md`
- Decision ledgers, contract tables, test matrices, templates → `FDP_OPERATIONS.md`
- Decision scoring rubric → `DECISION_FOR_FDP.md`

**Rule**: If you feel tempted to “summarize the schema,” stop and link to the SSOT instead.

---

## 3) The “addiction loop”: Pain → Relief

FDP is designed to make bypassing tools psychologically difficult.

**Pain signals (you are about to guess):**
- You’re about to write “probably / should / seems / verified / confirmed”
- You’re about to name a file path, import path, signature, schema shape, count, or performance claim from memory
- You’re about to assume uniqueness (entity names, filenames, keys)

**Relief action (what you do instead):**
- Run the query tool first (`fact-file-query-tool`), capture output, and attach it as an evidence block with a runnable `verification_command`.

**Habit**: *If you can query it, you must query it.*

---

## 4) FDP decision: when to apply it

Use `DECISION_FOR_FDP.md` as the authoritative rubric.

Orientation shortcut:
1. If any “hard trigger” category is present, **apply FDP**.
2. Otherwise, score the task; if score ≥ threshold, **apply FDP**.

**Output format (decision record):**
```yaml
fdp_decision:
  apply_fdp: YES|NO
  score: <0-18>
  hard_triggers: [<trigger IDs or names from DECISION_FOR_FDP.md>]
  reasoning: "<brief explanation>"
  claim_inventory_count: <number>
  next_step: "<what to do next>"
```

---

## 5) The 7 phases (the mental model)

Do not reinvent phases; execute them.

1. **Intake**: restate goal, constraints, success criteria  
2. **Hypotheses**: list what could be wrong (drift risks)  
3. **Evidence planning**: draft evidence blocks (commands runnable)  
4. **Evidence execution**: run commands; replace placeholders with real results  
5. **Decisions**: decisions *must* cite evidence IDs  
6. **Implementation plan**: grounded steps + contract table  
7. **Verification + drift**: test matrix + drift triggers + evidence-as-tests plan

---

## 6) Definition of “FDP-applied” output

A plan is “FDP-applied” when it contains:

### Required deliverables
- Goal + constraints + measurable success criteria
- Hypotheses (risk inventory)
- Decision ledger (each decision cites evidence)
- Contract table (CLI/API/Docs/Tests/CI alignment where applicable)
- Test matrix (tests mapped to evidence/decisions)
- Evidence appendix (validated, runnable, complete results)
- Drift triggers (measurable)
- Evidence-as-tests plan (recommended)

### Required quality gates
- **9am implementer test** (a fresh implementer executes without questions)
- **Probably detector** (no unverified hedge-words)
- Evidence validity (schema-valid; runnable commands)
- Tool enforcement (tool-first; bash requires justification)
- Contract alignment (no drift across surfaces)

---

## 7) Tool-first enforcement (how to behave in practice)

### The rule
For **code facts**, default to `fact-file-query-tool` before using grep, manual reading, or reasoning.

### Minimum preflight sequence (muscle memory)
```bash
# 1) Discover what the tool can answer
uv run fact-file-query-tool families

# 2) If you know the file, see what it covers
uv run fact-file-query-tool manifest --file <file>

# 3) Discover canonical entity names
uv run fact-file-query-tool entities --file <file>

# 4) Query using exact entity + available families
uv run fact-file-query-tool query --file <file> --entity "<EXACT_NAME>" --families <FAMILY>
```

### Bash fallback (only with justification)
If the tool is unavailable/broken, you may use bash **only** with explicit `tool_usage_check` justification in the evidence block and a guardrail that forces re-verification once the tool is restored.

---

## 8) Evidence blocks: what “good” looks like (behavioral standard)

Use the templates in `FDP_OPERATIONS.md` (do not duplicate templates here). The “good” standard is:

- `verification_command` is copy-paste executable
- Results are captured as structured data (not prose)
- Decisions cite evidence IDs and specific result fields
- Guardrails are measurable (“if X > 5%”, not “if it changes”)

**Completeness levels**
- Level 1: runnable commands, placeholders allowed (planning only)
- Level 2: actual output captured, placeholders removed (required before decisions)

---

## 9) A minimal FDP workflow you can execute mechanically

### Step A — Inventory claims (2–5 minutes)
List every plan statement that implies a fact:
- counts, filenames, import paths, signatures, schemas, compatibility, performance

### Step B — Convert top risk claims into hypotheses (5 minutes)
Turn “we will do X” into “X is safe if Y is true.”

### Step C — Draft evidence blocks (10 minutes)
One hypothesis → one evidence block (or a small cluster).

### Step D — Run verification commands (variable)
Replace placeholders with captured output.

### Step E — Write decisions + guardrails (10 minutes)
Each decision must cite evidence IDs.

### Step F — Write implementation plan + tests + drift triggers
Ground steps in evidence; ensure a test matrix exists for high-risk evidence.

---

## 10) Troubleshooting (fast diagnosis)

### Symptom: tool returns `{}`
Common causes:
- Wrong entity name (did not run `entities` first)
- Wrong file path (relative vs absolute mismatch)
- Queried family not covered (did not run `manifest`)
- Stale/missing facts file (needs regeneration)

Fix: execute the preflight sequence in §7 and retry.

### Symptom: “9am implementer test” fails
Fix: run the probably detector and replace each hedge word with either:
- an evidence block, or
- a deletion/rewrite that removes the claim.

---

## 11) Drift control: keep this orientation from becoming a second SSOT

This document should remain an **orientation** layer. To prevent drift:
- Link to SSOT docs for definitions and schemas
- Avoid duplicating templates or enumerating canonical lists
- Prefer “how to operate” over “what the schema is”

If your repo uses “expected zero matches” drift checks, ensure they remain green.

---

## 12) What to read next (in order)

1. `FDP_AI_WORKFLOW.md` (execute the protocol)
2. `FDP_SCHEMA.md` (evidence rules and hard-stops)
3. `FDP_OPERATIONS.md` (templates + ledgers + tables)
4. `DECISION_FOR_FDP.md` (scoring and triggers)

---

**End of orientation**
