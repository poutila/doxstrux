# USER_MANUAL.md
**Project:** doxstrux Refactor Phases  
**Applies to:** `DETAILED_TASK_LIST_template.yaml / .json / .md`  
**Audience:** Human contributors • AI agents • CI pipelines  
**Purpose:** Describe how task definitions are authored, rendered, validated, and executed by humans and automated agents.

---

## 1. Overview

Every refactor phase is described in a **single structured task list**.  
That list exists in **three synchronized formats**:

| Format | Audience | Editable | Source of truth | Function |
|:--|:--|:--|:--|:--|
| `.yaml` | Humans + AI | ✅ | ✅ (primary) | Human-readable master document |
| `.json` | AI + CI | ❌ | auto-generated | Strict, schema-validated execution plan |
| `.md` | Humans (review) | ❌ | auto-generated | Rendered documentation for PRs & dashboards |

The YAML file is edited manually.  
JSON and Markdown are regenerated automatically via `render_task_templates.py` (see § 6).

---

## 2. Editing rules (humans)

1. **Edit only the YAML file** (`DETAILED_TASK_LIST_template.yaml`).
2. Use clear indentation and keep one blank line between tasks.
3. Comments are allowed (`# …`) and ignored by renderers.
4. All placeholders in double braces must resolve during render, e.g.

   ```yaml
   {{FAST_TEST_COMMAND}}
   {{FULL_TEST_COMMAND}}
   {{CI_GATE_1}}
Rendering with --strict will fail if any placeholder remains unresolved.

3. Structure of the YAML template
3.1 Top-level keys
Key	Type	Purpose
meta	object	Phase number, author, date, summary
ai	object	Operating context for automated agents
tasks	list	Ordered list of actionable steps
gates	list	CI or validation commands
schema_version	string	Ensures renderer compatibility

3.2 AI section (for automated agents)
Example:

yaml
Kopioi koodi
ai:
  role: "Refactor Engineer"
  objectives:
    - "Complete Phase 8 without breaking baseline parity"
    - "Maintain Δmedian ≤ 5%, Δp95 ≤ 10%"
  constraints:
    - "No hybrids in PRs"
    - "Touch only src/docpipe/*"
  stop_conditions:
    - "Any CI gate fails (G1–G5)"
    - "Performance over budget"
  interaction_policy:
    ask_on_ambiguity: true
    max_questions: 3
    escalation_note: "Open ISSUE with evidence if blocked >30 min"
  runbook:
    fast_loop_cmd: "{{FAST_TEST_COMMAND}}"
    full_validation_cmd: "{{FULL_TEST_COMMAND}}"
    perf_cmd: "{{PERF_TEST_COMMAND}}"
    gates_cmd: "{{CI_GATE_1}} && {{CI_GATE_2}} && {{CI_GATE_3}} && {{CI_GATE_4}} && {{CI_GATE_5}}"
Agents read this section to know how to act, what to run, and when to stop.

3.3 Task section (for both humans and AI)
Each task entry must include:

Field	Type	Example	Meaning
id	string	"1.2"	Stable task identifier
name	string	"Build section indices"	Short title
kind	enum	"code_change"	Task category (code_change, test_change, doc_change, ops)
impact	enum	"P0"	Priority (P0 > P1 > P2)
files	list	[src/docpipe/markdown/utils/token_warehouse.py]	Key files to touch
inputs	list	[tools/test_mds/**/*.md]	Data sources
outputs	list	[build/index_map.json]	Expected artifacts
command_sequence	list	CLI or Python commands to run	
acceptance_criteria	list	Measurable success statements	
blockers_if_missing	list	Why this task is critical	
rollback	list	Commands to undo the task safely	

4. Rendering workflow
4.1 Manual generation
bash
Kopioi koodi
# From project root
python tools/render_task_templates.py --strict
This performs:

Validate YAML syntax.

Expand placeholders from environment or .env.

Render:

DETAILED_TASK_LIST_template.json

DETAILED_TASK_LIST_template.md

Validate JSON against schemas/detailed_task_list.schema.json.

Report unresolved variables (exit 1 on error).

4.2 Pre-commit hook
A pre-commit rule runs the same render command and aborts commits if:

Any placeholders remain.

JSON schema validation fails.

MD diff does not match rendered output.

5. Execution workflow (AI agents)
Load JSON version → parse strictly.

Read ai block to configure context and commands.

Iterate tasks in numeric order:

Execute command_sequence.

Verify acceptance_criteria.

If failure → trigger rollback and halt.

Run gates (section 7) at the end of each phase.

Mark completion by creating .phase-N.complete.json.

Agents must honor stop_conditions in the AI block.

6. Continuous Integration usage
CI jobs depend on the JSON format only:

Stage	Input	Validation
lint	YAML	yamllint
render	YAML → JSON, MD	Renderer script
schema	JSON	JSON Schema
gates	JSON	Execute ai.runbook.gates_cmd
complete	.phase-N.complete.json	Must exist for next phase

7. CI gates (example mapping)
Gate	Purpose	Command placeholder
G1	Syntax / lint	{{CI_GATE_1}}
G2	Unit tests	{{CI_GATE_2}}
G3	Security	{{CI_GATE_3}}
G4	Performance regression check	{{CI_GATE_4}}
G5	Documentation / schema parity	{{CI_GATE_5}}

All must pass before a phase is marked complete.

8. Rendering outputs
After rendering you will have:

arduino
Kopioi koodi
regex_refactor_docs/
 └── performance/
     ├── DETAILED_TASK_LIST_template.yaml   # editable
     ├── DETAILED_TASK_LIST_template.json   # generated for CI & AI
     ├── DETAILED_TASK_LIST_template.md     # generated for humans
     └── USER_MANUAL.md                     # this file
9. Human vs AI responsibilities

### AI Agent Autonomy Boundaries

**AI agents MUST NOT**:
- ❌ Modify YAML source files (`DETAILED_TASK_LIST_template.yaml`)
- ❌ Edit schema files (`schemas/*.schema.json`)
- ❌ Change meta fields (phase, author, schema_version)
- ❌ Alter task IDs or reorder tasks
- ❌ Modify acceptance criteria without human approval
- ❌ Skip CI gates or override stop conditions
- ❌ Commit changes to baseline test corpus

**AI agents MAY**:
- ✅ Execute tasks as defined in `command_sequence`
- ✅ Create or update completion artifacts (`.phase-N.complete.json`)
- ✅ Log evidence to `evidence/` directory
- ✅ Mark tasks as complete in `evidence/results/`
- ✅ Generate reports and summaries
- ✅ Ask clarifying questions (per `interaction_policy`)
- ✅ Create rollback commits if tasks fail

**AI agents MUST**:
- ✅ Honor `stop_conditions` immediately
- ✅ Validate `acceptance_criteria` before marking complete
- ✅ Execute `rollback` commands on failure
- ✅ Verify `post_rollback_criteria` after rollback (Phase 3)
- ✅ Log all actions to `evidence/logs/`
- ✅ Emit task results to `evidence/results/` using standard schema

**Enforcement**: CI validates that YAML/schema files are unchanged by AI commits.

### Responsibility Matrix

Area	Human	AI
Edit tasks / priorities	✅	❌
Interpret ambiguous goals	✅	⚠ Ask before continuing
Execute commands	⚠ Manual if local dev	✅ Automated
Validate acceptance criteria	✅	✅
Maintain parity test corpus	✅	❌ Read-only
Approve final completion artifact	✅	❌ (generate only)
Modify schemas or templates	✅	❌ Never
Write to evidence/	⚠ Review only	✅ All execution data

10. Safety & reproducibility
Always run with --strict rendering.

All commands must be idempotent.

Use environment variables for secrets and tokens.

JSON Schema validation prevents malformed task definitions.

Every rendered artifact is deterministic from the YAML source.

11. Quick reference
Action	Command
Edit tasks	nano regex_refactor_docs/performance/DETAILED_TASK_LIST_template.yaml
Render all formats	python tools/render_task_templates.py --strict
Validate JSON	python -m jsonschema -i DETAILED_TASK_LIST_template.json schemas/detailed_task_list.schema.json
Regenerate Markdown	same render command
Run all gates	bash -c "$(jq -r '.ai.runbook.gates_cmd' DETAILED_TASK_LIST_template.json)"

12. Versioning policy
Bump schema_version on any structural change.

Older JSON may still be readable but should trigger a warning.

Always regenerate MD + JSON before merging to main.

13. Example phase lifecycle
Step	Actor	Artifact
1 Define tasks	Human	YAML
2 Render formats	Pre-commit	JSON + MD
3 Execute tasks	AI agent	Console logs
4 Verify gates	CI	reports
5 Mark completion	AI + CI	.phase-N.complete.json
6 Review & merge	Human	PR + MD diff

14. Schema validation and enforcement notes
To guarantee consistency between human-authored YAML and CI-consumed JSON,
the project provides a strict schema at:

pgsql
Kopioi koodi
schemas/detailed_task_list.schema.json
Key points
no_placeholders_string — this schema rule rejects unresolved {{...}} tokens,
making --strict rendering behavior enforceable at schema level.

Enum flexibility — the schema allows future extension of enumerations
(for example, adding kind: "data_migration" or new gate types)
without breaking backwards compatibility.

Fail-closed validation — any extra or missing field causes a validation error
because additionalProperties is set to false.

Schema version — bump schema_version in YAML whenever a structural change occurs.

Manual validation command
From the project root, run:

bash
Kopioi koodi
python -m jsonschema \
  -i regex_refactor_docs/performance/DETAILED_TASK_LIST_template.json \
  schemas/detailed_task_list.schema.json
This checks that:

All required keys exist.

No placeholder patterns remain unresolved.

Every task and AI block matches the expected structure.

CI gates and IDs follow the defined naming rules.

Validation must succeed before merging to main.

End of USER_MANUAL.md
