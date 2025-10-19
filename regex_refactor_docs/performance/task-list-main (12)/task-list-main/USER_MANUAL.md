8. Turning prose into the structured template (plan container workflow)

Use this pipeline to transform a free-form refactor brief (e.g., docs/DOXSTRUX_REFACTOR.md) into the v2 YAML task list (document / metadata / ci_gates / phases / render_meta).

8.1 Prose authoring template (for humans)

Ask authors to write briefs in this shape so extraction is deterministic:

# <Project or Component> — Refactor Brief

## Context
- Why this refactor is needed.
- Constraints (perf, memory, deadlines).

## Goals / Non-Goals
- Goal 1 …
- Goal 2 …
- Non-Goal 1 …

## Risks & Mitigations
- Risk: …
- Mitigation: …

## Phase 0 — <Title>
Time estimate: 0.5d
Success criteria:
- <measurable result>
- <measurable result>

### Step 1: <Imperative verb + noun>
Rationale: <short reason>
Expected artifacts: <files/dirs>
```bash
# commands or python invocations (optional but ideal)
python -m package.module --flag


Verify: <clear acceptance statement with “verify/ensure/assert/accept”>

Step 2: <Imperative …>

… (repeat)

Phase 1 — <Title>

Time estimate: 1d
Success criteria:

…

Step 1: …

…


**Authoring tips**
- Use **imperative** step titles (“Build indices”, “Add schema gate”).
- Put commands in fenced blocks (```bash, ```python).
- Write measurable **Verify:** lines (“verify schema has no `{{…}}`”, “ensure p95 ≤ +10%”).
- One phase per major milestone; steps inside phases.

---

## 8.2 Semantic parsing (text → task candidates)

A light regex-first pass is usually enough; add spaCy or an LLM only if needed.

```python
import re
from pathlib import Path

HEAD = re.compile(r"^(#+)\s+(.*)$", re.M)              # headings
STEP = re.compile(r"(?im)^\s*(?:step\s+\d+[:.)-]|\d+\.\d+)\s+(.*)$")
CODE = re.compile(r"```(?:bash|sh|python)?\n([\s\S]*?)\n```", re.M)
CRIT = re.compile(r"(?im)\b(verify|ensure|accept|assert)\b.*")

def split_sections(md: str):
    pos, out = 0, []
    for m in HEAD.finditer(md):
        if out: out[-1]["body"] = md[pos:m.start()].strip()
        out.append({"title": m.group(2).strip(), "level": len(m.group(1)), "body": ""})
        pos = m.end()
    if out: out[-1]["body"] = md[pos:].strip()
    return out or [{"title":"Refactor", "level":1, "body":md}]

def classify_kind(text: str) -> str:
    t = text.lower()
    if "test" in t or "pytest" in t: return "test_change"
    if "doc" in t or "readme" in t:  return "doc_change"
    if "deploy" in t or "ci" in t:   return "ops"
    return "code_change"

def infer_impact(text: str) -> str:
    t = text.lower()
    if "critical" in t or "must" in t or "blocker" in t: return "P0"
    if "should" in t or "important" in t:                return "P1"
    return "P2"

def extract_commands(section_body: str):
    return [c.strip() for c in CODE.findall(section_body)]

def extract_criteria(section_body: str):
    return [ln.strip() for ln in section_body.splitlines() if CRIT.search(ln)]

def extract_tasks_from_doc(md: str, phase_id="0"):
    sections = split_sections(md)
    tasks = []
    local_idx = 0
    for sec in sections:
        steps = STEP.findall(sec["body"]) or []
        cmds  = extract_commands(sec["body"])
        crit  = extract_criteria(sec["body"])

        if not steps and not cmds and not crit:
            continue

        n = max(1, len(steps))  # at least one task if signals exist
        for i in range(n):
            local_idx += 1
            title = steps[i] if i < len(steps) else sec["title"]
            tasks.append({
                "id": f"{phase_id}.{local_idx}",
                "name": title[:80],
                "kind": classify_kind(sec["body"]),
                "impact": infer_impact(sec["body"]),
                "files": [],
                "inputs": [],
                "outputs": [],
                "command_sequence": cmds or ["TBD_COMMAND"],
                "acceptance_criteria": crit or ["TBD: measurable acceptance"],
            })
    return tasks
```

8.3 Schema builder (task candidates → validated YAML v2)
from jsonschema import validate
import yaml, json
from pathlib import Path

SCHEMA = json.loads(Path("tasklist/schemas/detailed_task_list.schema.json").read_text(encoding="utf-8"))
md = Path("docs/DOXSTRUX_REFACTOR.md").read_text(encoding="utf-8")
tasks = extract_tasks_from_doc(md, phase_id="0")

yaml_obj = {
    "schema_version": "2.0.0",
    "document": {
        "title": "DOXSTRUX_REFACTOR",
        "version": "1.0.0",
        "created": "TBD_UTC",
        "owner": "TBD_OWNER",
        "audience": ["engineers","reviewers"],
        "summary": "Plan auto-extracted from prose; human will refine."
    },
    "metadata": {"author":"TBD_AUTHOR", "phase": 0, "updated_utc":"TBD_UTC", "tags":["refactor"]},
    "success_criteria": ["No schema violations", "CI gates G1–G5 green"],
    "phase_unlock_mechanism": ["phase_0_complete.json"],
    "ci_gates": [
        {"id":"G1","name":"Lint & Schema","command":"{{CI_GATE_1}}"},
        {"id":"G2","name":"Unit Tests","command":"{{CI_GATE_2}}"}
    ],
    "phases": {
        "phase_0": {
            "name":"Bootstrap from prose",
            "goal":"Convert prose to executable plan",
            "time_estimate":"TBD",
            "status":"draft",
            "tasks": tasks
        }
    },
    "render_meta": {
        "source_file": "docs/DOXSTRUX_REFACTOR.md",
        "schema_version": "2.0.0",
        "sha256_of_yaml": "TBD",
        "rendered_utc": "TBD"
    }
}

validate(instance=yaml_obj, schema=SCHEMA)
Path("DETAILED_TASK_LIST_generated.yaml").write_text(
    yaml.safe_dump(yaml_obj, sort_keys=False, width=100),
    encoding="utf-8"
)
print("Wrote DETAILED_TASK_LIST_generated.yaml")


Notes

Fill required metadata before validation.

Use TBD_… placeholders for values awaiting human review **only** when rendering with the draft profile:

```bash
tasklist-render --strict --allow-tbd --root $REPO
```

In a release profile, fail CI if any TBD_ remains in required fields. Run a strict render without
`--allow-tbd` and block on any failures (including {{…}} templates):

```bash
tasklist-render --strict --root $REPO
grep -RE "TBD_" DETAILED_TASK_LIST_template.yaml && exit 1
```

8.4 Rendering & round-trip validation
# Strict render → JSON + MD; enforces placeholder rules and repeats schema validation
tasklist-render --source DETAILED_TASK_LIST_generated.yaml --strict

# Confirm renders are committed & synced with YAML (drift gate)
git diff --exit-code DETAILED_TASK_LIST_template.json DETAILED_TASK_LIST_template.md


This produces synchronized JSON/MD, injects render_meta (YAML SHA, UTC timestamp, schema version), and sets you up for agent/CI consumption.

8.5 Optional AI-assisted flow (prompt template)

If you use an LLM to draft tasks directly:

System: You are a task extractor.
Goal: Convert a refactor brief into YAML conforming to the v2 schema (keys: schema_version, document, metadata, ci_gates, phases, render_meta).
Rules:

Use imperative task names.

Default kind to code_change unless testing/docs/ops are explicit.

Default impact to P1; upgrade to P0 if critical/blocked.

Put commands from code fences into command_sequence (list).

acceptance_criteria must be a list of measurable statements starting with verbs (“verify…”, “ensure…”).

Output strictly valid YAML (no comments), with schema_version: "2.0.0".

Always pass the LLM output through 8.3 and 8.4 so the renderer and CI lint the result automatically.

8.6 Quality checks (common failure points)

No headings / steps: still emit at least one task if you see any code fence or verification phrase.

Inconsistent IDs: ensure id matches ^\d+(\.\d+)*$ and is monotone within the phase.

Absolute/unsafe paths: sanitize to repo-relative POSIX paths; deny .. and drive letters.

Placeholders leaking: --strict blocks {{…}}. For release, also grep-fail on TBD_ in required fields.

Schema drift: run jsonschema validation after render; block merges on failure.
