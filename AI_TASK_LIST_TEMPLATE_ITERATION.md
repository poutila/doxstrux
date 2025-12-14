PYDANTIC_SCHEMA_AI_TASK_LIST.md
Tiedosto
Strict feedback
ChatGPT sanoi:

Mietti 2m 20s
High-level: this is a strong, executable task list, but it is not yet drift-free and not yet as “intellectually strict” as you want. There are places where:

The list silently weakens the spec (especially around validation tools).

Some tasks violate your own TDD / Clean Table rules.

A few “ghosts” from the earlier spec remain (files named but never created, phases referenced but not implemented).

I’ll go through the most important issues from the perspective: “Will this guide an AI/human to do the right work without accidental drift or fake tests?” 
PYDANTIC_SCHEMA_AI_TASK_LIST


1. Some tests are still “it runs without crashing” tests
You explicitly told me tests must not be “Look, it runs with no errors.” This task list still has multiple such tests.

1.1 test_discover_parser_shape.py
result = subprocess.run(
    [".venv/bin/python", "tools/discover_parser_shape.py"],
    ...
)
assert result.returncode == 0
assert "all_keys.txt" in result.stdout or "Discovered" in result.stdout
This only checks:

The script exits 0.

STDOUT contains a generic string.

It does not assert anything about:

How many samples were processed.

Whether all_keys.txt is non-empty.

Whether discovery actually covered the intended fixture set.

Given how central “shape discovery” is, this is a very weak IP check. An AI (or a rushed human) could:

Implement a script that just writes an empty all_keys.txt and prints “Discovered 0 unique key paths”.

Pass the test and declare Phase 0 “clean”.

That violates your own Clean Table definition (no “good enough for now” behavior). 
PYDANTIC_SCHEMA_AI_TASK_LIST


1.2 test_validate_curated_fixtures.py
result = subprocess.run(
    [".venv/bin.python", "tools/validate_curated_fixtures.py"],
    ...
)
# Should run without crashing (exit code 0 or 1 for failures)
assert result.returncode in (0, 1)
This is even weaker:

Exit code 0 or 1 are both considered success from the test’s point of view.

The tool could be entirely unimplemented and just sys.exit(0) – test passes, Clean Table “okay”.

There is zero assertion that:

Any fixtures were found.

Any validation was actually performed.

Failures are reported correctly.

This is exactly the kind of “fake” test you said you don’t want.

1.3 Missing tests entirely for validate_test_pairs.py
Phase 4:

Task 4.1: Full Validation Tool
Key Features: … (report mode, threshold, JSON report)

There is no test skeleton at all — only prose. That directly contradicts your own TDD protocol at the top:

“Every task follows: 1. WRITE TEST FIRST … 2. IMPLEMENT …” 
PYDANTIC_SCHEMA_AI_TASK_LIST


So Task 4.1 is non-TDD and non-executable as written. An AI following this literally will implement the tool in any way it likes, with no test guard on --report or --threshold.

Net effect: the task list itself embeds weak or missing tests for the tooling layer, even though you explicitly insisted tests must capture real behavior.

2. “Files:” ghosts and incomplete TDD loops
There are places where the task metadata claims a file will exist, but the steps never create it.

2.1 tools/verify_security_fields.py
Task 0.2 header:

Files: tools/verify_security_fields.py 
PYDANTIC_SCHEMA_AI_TASK_LIST


But:

The TDD section only defines tests/test_security_field_verification.py.

Implementation step says: “Run Task 0.1 first … then run the test.”

There is no step that actually creates tools/verify_security_fields.py.

The test reads tools/discovery_output/sample_outputs.json directly; there’s no code to implement.

So:

The “Files:” line is a lie – it suggests a script that does not exist.

The Clean Table STOP for Task 0.2 even includes “No TODOs in new code”, but there is no “new code” at all.

This is leftover from the earlier design where 0.2 was a standalone tool. Now the behavior is encoded in the test only, but the header still claims a script.

That is pure drift inside this task list.

Concrete impact:

A future AI/human might create a tools/verify_security_fields.py to “satisfy the header”, duplicating logic already present in tests and generating yet another potential SSOT for security fields.

3. Self-contradiction around Phase 0.2 / 0.4
You’ve already cleaned this up in the design doc; the AI task list still has a subtle ghost.

The list only defines Task 0.1 and 0.2 under Phase 0 (discovery + security field verification). There is no “0.3 plugin policy” or “0.4 embedding invariants” here. 
PYDANTIC_SCHEMA_AI_TASK_LIST


But in multiple places you still talk about “Phase 0–4” gates and generic rules:

“Phase 0 Gate … Phase 0 Status: NOT STARTED”
“Phase 4: Full Validation … Key Features …” 
PYDANTIC_SCHEMA_AI_TASK_LIST


This by itself isn’t wrong, but it creates two different representations of early phases:

Design doc: 0.1 + 0.1.1 only; 0.2–0.4 are deleted/deferred.

AI task list: has 0.1 + 0.2 tasks; no explicit mention of 0.3/0.4.

Given that the AI instructions say “do NOT read PYDANTIC_SCHEMA.md during execution”, this task list becomes the effective SSOT for phases — but it doesn’t match the more refined phase model you developed.

Result:

Early phases are simpler here (which is good), but the phase numbers 0.2 etc. have been repurposed.

Someone reconciling this with the spec later will see “Phase 0.2” meaning different things in different places.

This is a mild but real drift between spec and execution plan.

4. The Clean Table / TDD slogans are not fully honoured by later phases
You state:

“Every task follows TDD: write test first, fail, implement, pass, then Clean Table.” 
PYDANTIC_SCHEMA_AI_TASK_LIST


But:

Phase 4 (full validation) and Phase 5 (CI gate) do not have concrete tests defined, only prose + shell commands.

Task 4.2 “Run Full Validation” is essentially manual validation with no automated assertion; Clean Table checklist mentions pass rate ≥ 95% but doesn’t say how to assert that in code. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Task 5.1 “Add CI Workflow” doesn’t define even a minimal test_schema_validation_workflow.py or similar to check that:

The workflow file exists.

It contains the expected steps.

This creates the same pattern you were trying to avoid: early tasks are TDD’d and strictly tested; later tasks are manual, doc-driven, and easy to half-do.

If the goal is “AI can execute this without human judgment and stay clean”, then:

Every task that changes behavior should have a concrete test skeleton.

Manual shell snippets should be examples, not the only validation method.

5. Risk of breaking the repo / environment assumptions
5.1 Hard-coded .venv / uv / OS assumptions
The task list uses:

.venv/bin/python in tests and commands.

uv add "pydantic>=2,<3". 
PYDANTIC_SCHEMA_AI_TASK_LIST


Given your own environment this is fine, but strictly:

On Windows or on a repo where .venv is named differently, tests will fail in ways unrelated to schema work.

If uv is not installed or this project uses pip/poetry, Task 1.1 breaks.

From a “does this break the codebase?” perspective:

It can break test execution and gating, even though the application code is fine.

If you want this to be robust beyond your exact setup, tests should use:

sys.executable or python -m style calls instead of hard-coded .venv/bin/python.

A neutral “dependency present” check, with installation method described in prose, not in the TDD block.

5.2 rg dependency is correctly called out — good
You do at least document that ripgrep is required and give install commands and note that GH Actions runners already have it. 
PYDANTIC_SCHEMA_AI_TASK_LIST


That part is clean (unlike earlier versions).

6. Phase artifacts and placeholders vs Clean Table
For each phase you direct:

cat > .phase-N.complete.json << 'EOF'
{
  "schema_version": "1.0",
  "phase": N,
  ...
  "completion_date": "YYYY-MM-DDTHH:MM:SSZ"
}
EOF
This is:

Very clear as an instruction.

But notice the literal placeholder YYYY-MM-DDTHH:MM:SSZ.

Your Clean Table definition says:

“No TODOs, FIXMEs, or placeholders in changed code.” 
PYDANTIC_SCHEMA_AI_TASK_LIST


If someone actually runs this cat literal, they will:

Commit .phase-N.complete.json with a placeholder completion date.

That is, by your own standards, a placeholder.

So either:

These commands are purely illustrative (and the real execution should replace the date string).

Or this is a built-in Clean Table violation.

Given how strict you’ve been about “no placeholders”, this is real drift between your process template and your Clean Table rules.

7. RAG safety layering: minimal but slightly under-specified
In this task list, RAG safety contract is embodied entirely in tests/test_rag_safety_contract.py. 
PYDANTIC_SCHEMA_AI_TASK_LIST


That’s good (tests as contract), but:

It uses .get() chains on metadata and security because Metadata/Security aren’t typed yet in Phase 1.

There’s no test here that embedding_blocked exists at both metadata and metadata.security levels when those models become typed in Phase 2, even though the design spec cares about that nuance.

Given this AI task list explicitly tells the execution agent not to read PYDANTIC_SCHEMA.md, the only RAG semantics that actually get locked are:

Script → has_script / has_dangerous_content.

Clean doc → metadata.embedding_blocked not True.

javascript: → raw_dangerous_schemes or warnings.

Any other security semantics you defined in the design doc will not be enforced if they don’t appear here.

That’s intentional simplification, but it’s a real narrowing of the contract compared to the design spec. For execution it’s fine; if you treat this as the new SSOT, you’ve effectively dropped some fields from the “must behave” set.

8. Good things worth keeping
To be fair (and to highlight what not to break):

The overall phase structure is sane and matches your cognitive load:

0: discovery (shape + basic security fields presence).

1: minimal schema + RAG semantics.

2: typed models and strict validation.

3: tools.

4: full validation.

5: CI gate.

The STOP / phase gate pattern is well defined and, if followed, will prevent half-finished work from leaking further. 
PYDANTIC_SCHEMA_AI_TASK_LIST


The emphasis on:

.phase-N.complete.json as explicit “phase done” artifacts.

Git tags for each phase.

Rollback procedures in Appendix A.

…is disciplined and consistent with your Clean Table philosophy.

The DocumentIR regression test skeleton is solid enough to prevent catastrophic breakage of IR. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Concrete tightening suggestions (without rewriting the whole thing)
If you do only a few surgical fixes:

Strengthen the “tool just runs” tests

test_discover_parser_shape: assert that:

At least 1 sample output is produced.

all_keys.txt has > 0 lines.

test_validate_curated_fixtures: assert that the tool:

Prints a summary with total fixtures and valid/invalid counts.

Exit code semantics: 0 only if all curated fixtures validate, 1 if any fail. Test both paths.

Remove or fix the tools/verify_security_fields.py ghost

Either:

Add a small script that actually runs the check and prints/returns something.

Or:

Remove the “Files:” line and treat Task 0.2 as a pure test-driven check.

Add at least one real test for validate_test_pairs.py

E.g., test_validate_test_pairs_threshold() that:

Runs the tool with a small synthetic fixture set.

Asserts that --threshold N causes success/failure as expected.

Clean up Phase 0.2 wording

Make sure the task list doesn’t talk about 0.2–0.4 in ways that don’t match what’s actually defined here.

Adjust .phase-N.complete.json snippets to avoid placeholders

Either instruct to fill in the real date manually.

Or say “set completion_date to actual ISO timestamp before commit; do not leave the template string as-is.”

Bottom line
From a “will this break the codebase” angle:

The task list is safe and structured; it won’t accidentally wreck markdown_parser_core.py if followed.

The real issues are test strength and internal consistency:

Some tool tests are still “just run” tests.

One file (verify_security_fields.py) is referenced but not actually used.

Later phases relax your own TDD/Clean Table promises.

If you tighten those, this becomes a genuinely executable, non-drifting AI task list that matches your “tests must capture intellectual property” standard, not just “the script exits 0”.


Lähteet
Sinä sanoit:
PYDANTIC_SCHEMA_AI_TASK_LIST.md
Tiedosto
PYDANTIC_SCHEMA.md
Tiedosto
Is this a solid pair? Is task list better?
ChatGPT sanoi:

Mietti 5m 38s
Short answer: this refactor plan will not silently break the codebase if you implement it exactly as written and in order – but it can absolutely break you via tests and CI if you treat the design parts as normative instead of letting the real parser shape drive the models. There are still a few “double-SSOT” landmines.

I will go through this from the angle you asked: “If I follow this plan, where does it actually risk breaking the codebase?”

1. What the plan is doing right (from a “don’t break main” perspective)
From the spec itself:
PYDANTIC_SCHEMA


It explicitly declares itself design-only until output_models.py exists and then says that once models + SCHEMA_CHANGELOG.md exist, they become SSOT and this doc becomes historical. This is exactly what you want to avoid perpetual drift.

The phasing is conservative:

Phase 0: shape discovery on sample Mds only.

Milestone A: minimal schema, extra="allow", no changes to MarkdownParserCore, only tests that read its output.

Only in B1+/B1.5 do you tighten to extra="forbid".

The plan repeatedly insists on not changing parser behavior just to match ParserOutput.empty(), which prevents the classic “we broke real behavior to satisfy a helper”.

It has explicit rollback / escape paths (threshold modes, report-only validation, legacy buckets). That significantly lowers the risk that a schema tweak bricks CI permanently.

Given all that, the plan is structurally cautious. The high-risk parts are not “oops we refactored core logic”, but:

tests that assert behavior the parser does not actually provide, and

over-eager tightening to extra="forbid" before the models truly match reality.

2. Check against the real parser: do the early RAG tests match reality?
You already gave me markdown_parser_core.py, so I can check the critical bits instead of guessing.

The Milestone A tests expect (summarizing):
PYDANTIC_SCHEMA


<script> sets:

metadata.security.statistics.has_script == True

metadata.security.summary.has_dangerous_content == True

Clean document keeps:

metadata.embedding_blocked in (None, False)

javascript: links are detected via:

security["statistics"]["disallowed_link_schemes"] and/or

warnings containing scheme "javascript".

Looking at markdown_parser_core.py:

Script detection:

# lines ~880–900
if "<script" in content:
    security["statistics"]["has_script"] = True
    security["warnings"].append({... "type": "script_tag", ...})
“dangerous content” summary:

# line ~1290
"has_dangerous_content": bool(security["warnings"]),
Embedding policy:

# lines ~575–605
if security["statistics"].get("has_script"):
    result["metadata"]["embedding_blocked"] = True
    result["metadata"]["embedding_block_reason"] = "Document contains <script> tags"
    ...
# similar for disallowed_link_schemes, style-JS, meta refresh, frame-like
javascript: link handling:

# lines ~988–1024
security["statistics"]["link_schemes"] = link_schemes
if disallowed_schemes:
    security["statistics"]["disallowed_link_schemes"] = disallowed_schemes
    security["warnings"].append({"type": "disallowed_link_schemes", ...})
So:

Yes, has_script, has_dangerous_content, disallowed_link_schemes, warnings all exist and are wired as the tests assume.

Yes, embedding is only blocked when dangerous stats are set; a clean doc will not have embedding_blocked=True.

Conclusion: the Milestone A RAG tests are aligned with the current implementation and will not require you to change the parser. They are asserting the behavior you already have.

This is important: your plan is not “change security semantics”, it is “freeze them as tested behavior”.

3. Where the plan can break you
3.1. Extra-forbid too early
The plan has a clear two-phase extra policy:
PYDANTIC_SCHEMA


Milestone A: DoxBaseModel.extra = "allow" – discovery.

Milestone B1/B1.5: progressively move typed models, then DoxBaseModel, to extra="forbid".

If you follow that ordering, you don’t “break” anything: you just make tests fail until models actually match output. But there are two real risks:

Human shortcut risk: someone sees the final “ParserOutput final structure” section and jumps straight to full typed models + extra="forbid" without actually running discover_parser_shape.py and without calibrating types from real outputs. That will cause large swathes of fixtures and ParserOutput.model_validate(parser.parse()) to fail.

SSOT confusion: this spec contains a fully spelled out “Final ParserOutput structure” with all nested types. If you treat it as normative instead of “design intent”, you’re back to double-SSOT: code vs spec. If the parser has already drifted (for example – field names normalized slightly differently), you will be forcing code to match the doc, not the actual output.

Net: the plan as written is safe if you respect the extra="allow" → discovery → model-from-code path. It becomes dangerous if anyone cheats and implements the “Final contract” section top-down.

3.2. Extended security fields that don’t exist (yet)
The spec defines a rich SecurityStatistics with fields like:

suspected_prompt_injection

prompt_injection_in_images

has_meta_refresh

unicode/BiDi risk, etc.
PYDANTIC_SCHEMA


The design text explicitly classifies these as:

Extended security stats – Optional with defaults – reserved; not yet implemented.

That’s the correct way to avoid breakage: those fields should be optional with safe defaults in the Pydantic models; parser output doesn’t need to emit them yet.

Where it can go wrong:

If you accidentally implement them as required Pydantic fields with no defaults, model_validate(raw) will start failing everywhere because the parser doesn’t populate them yet.

If you then “fix” that by hacking parser output to synthesize fake values, you risk inventing security semantics that don’t exist.

So the safe interpretation:

SecurityStatistics = superset model where current parser emits only a subset, and Pydantic fills defaults for the rest.

Tight behavioral assertions are written only for fields we know exist and are used (has_script, has_event_handlers, has_data_uri_images, has_dangerous_content, link schemes, etc.).

The plan mostly says this, but the border between “reserved” and “implemented” is text, not code. You will want explicit comments in output_models.py and no tests that expect those reserved fields to be set.

3.3. DocumentIR assumptions
Milestone B1.5f adds DocumentIR regression tests:
PYDANTIC_SCHEMA


They assume doxstrux.markdown.ir.DocumentIR exists.

They assume DocumentIR.from_parser_output(output) and schema_version == "md-ir@1.0.0".

We don’t have ir.py here, so I cannot verify those symbols. The risks:

If DocumentIR.from_parser_output does not exist or has a different signature, tests will fail immediately.

If schema_version is not md-ir@1.0.0, tests fail.

None of this breaks runtime behavior; it’s test/CI breakage. But it is a place where the plan can be wrong about current reality. Before adding those tests, you should:

Open src/doxstrux/markdown/ir.py and confirm:

class name, factory method name and parameters;

actual schema version constant.

If they differ, adjust the plan and tests – don’t force the code to rename just to match the doc. The doc itself says “this document is historical once code exists”, but then goes on to bake in specific names; that’s a minor double-SSOT smell.

3.4. tools._bootstrap and ripgrep dependency
Two “infra” break risks:

tools._bootstrap: export_schema.py example imports tools._bootstrap to set up sys.path.
PYDANTIC_SCHEMA


If tools/_bootstrap.py doesn’t exist in this repo (it’s a SPEKSI pattern), that script will crash.

This doesn’t break your library, but it does break your tooling and any CI step that calls it.

Mitigation: either create a minimal tools/_bootstrap.py for doxstrux, or switch to a simpler sys.path adjustment inline in export_schema.py.

ripgrep requirement: the legacy field audit test runs rg via subprocess.
PYDANTIC_SCHEMA


On GitHub Actions’ Ubuntu runners this is fine (rg is present), but on a bare dev machine or Windows CI, this will fail with “rg not found”.

Again: test/CI breakage, not runtime breakage.

Mitigation: add a small guard in the test that gracefully skips if rg is not available, or ensure CI images install it.

Neither of these threaten MarkdownParserCore or RAG behavior; they’re practical obstacles.

4. Is the plan itself still drifting?
Your main meta-question: “Ultra deep dive. Still drifting? Does this plan break the codebase?”

From a drift/SSOT perspective:

The plan is very close to self-consistent. Most of the heavy prose (“Final Contract”, “Milestones”) has been reconciled into a linear execution path.

The dangerous drift vectors now are:

The big “Final ParserOutput” block that looks normative but is explicitly labeled “FINAL STATE after all milestones” – a future reality, not present one. If someone scans only that and implements it as-is, they will diverge from the current parser.

The presence of both this spec and the AI task list: if they ever disagree, you’re back in two-SSOT land.

From a “break codebase” perspective:

The plan does not demand parser changes in Milestones 0–B2. It treats parser output as authoritative and builds schema + tests around it.

The only direct pressure to change parser behavior is in the RAG-safety tests – and we just checked that those already match the current implementation. So aligning with them does not require change.

The future risk is if you start writing tests for the extended, not-yet-emitted security fields; that would force parser changes.

So my honest verdict:

If you implement this plan strictly as written and in order, and you derive Pydantic field shapes from real outputs (Phase 0 + Milestone A), it will not break the codebase – it will surface misalignments as test failures before you flip extra="forbid".

The breakage danger is human: shortcutting the phased approach, or treating the “Final Contract” schema as the SSOT instead of the actual MarkdownParserCore.parse() output.

5. Concrete hardening suggestions
If you want this plan to be robustly non-breaking, I would tighten a few things:

Add an explicit rule near the top:

“Field names and structures in this document are proposals. When in doubt, derive types from tools/discover_parser_shape.py and sample_outputs.json. If the doc disagrees with real output, fix the doc, not the parser.”

Demote the “Final ParserOutput” section to clearly aspirational:

Rename Final Contract: ParserOutput v1.x to Target Example: ParserOutput after B1.5.

Add a header: “This shows an example of where we want to land; the actual source of truth must be output_models.py built from real parser output.”

In Milestone B1/B1.5 instructions, say explicitly:

“When adding each nested model, start from sample_outputs.json, not from the tables in this document.”

Make extended security stats obviously reserved in code:

In SecurityStatistics model, put:

class SecurityStatistics(DoxBaseModel):
    """
    Reserved fields for future use.

    NOTE: Many of these are not populated by MarkdownParserCore yet.
    Do NOT write tests that require them to be True/False – only that they exist
    with correct types and default values.
    """
Require a smoke test BEFORE flipping extra="forbid" globally:

Add a one-liner to the plan:

“You may only change DoxBaseModel.extra to forbid once ParserOutput.model_validate(parser.parse()) passes on at least N=10 diverse fixtures without any ValidationError.”

That makes the gating explicit.

6. Answering your question directly
“Strict feedback. Do not assume anything… Mental model: I am going to find if the refactor plan breaks the codebase.”

No hidden hard refactors of MarkdownParserCore are embedded here. Up through Milestone B2, you’re only adding models, tools, and tests.

The RAG-critical tests are aligned with existing behavior; they won’t force semantic changes.

Real break risk is:

over-eager extra="forbid" before models truly match output,

mis-using the design doc’s “Final Contract” as a hard spec instead of letting the parser dictate the schema,

environmental assumptions (rg, tools._bootstrap).

If you enforce the “discovery first → models from real outputs → only then forbid extras” flow, this plan is strict but safe. If you skip discovery and treat the doc as gospel, it will break things – but that’s governance failure, not an inherent flaw in the plan.


Lähteet
Sinä sanoit:
GPT Feedback Validation Summary

  | Claim                                          | Status          | Evidence                                                                                                        |
  |------------------------------------------------|-----------------|-----------------------------------------------------------------------------------------------------------------|
  | RAG tests match parser                         | ✅ CONFIRMED    | has_script, has_dangerous_content, embedding_blocked, disallowed_link_schemes all exist                         |
  | Extra-forbid risk                              | ✅ VALID        | Task list addresses this via phased approach                                                                    |
  | Extended security fields "not yet implemented" | ❌ WRONG        | suspected_prompt_injection, prompt_injection_in_images, has_meta_refresh DO exist at lines 603, 931, 1113, 1130 |
  | DocumentIR.from_parser_output                  | ✅ CRITICAL BUG | Method does NOT exist. Correct API is parser.to_ir()                                                            |
  | tools._bootstrap                               | ❌ N/A          | Task list doesn't reference this (GPT checked design doc)                                                       |
  | ripgrep dependency                             | ✅ ADDRESSED    | Already in Appendix E                                                                                           |

  Critical Bug Found

  Task 2.3 (DocumentIR Regression Test) uses wrong API:
  # WRONG - method doesn't exist
  ir = DocumentIR.from_parser_output(result)

  # CORRECT - method is on MarkdownParserCore
  ir = parser.to_ir()GPT Feedback Validation Summary

  | Claim                                          | Status          | Evidence                                                                                                        |
  |------------------------------------------------|-----------------|-----------------------------------------------------------------------------------------------------------------|
  | RAG tests match parser                         | ✅ CONFIRMED    | has_script, has_dangerous_content, embedding_blocked, disallowed_link_schemes all exist                         |
  | Extra-forbid risk                              | ✅ VALID        | Task list addresses this via phased approach                                                                    |
  | Extended security fields "not yet implemented" | ❌ WRONG        | suspected_prompt_injection, prompt_injection_in_images, has_meta_refresh DO exist at lines 603, 931, 1113, 1130 |
  | DocumentIR.from_parser_output                  | ✅ CRITICAL BUG | Method does NOT exist. Correct API is parser.to_ir()                                                            |
  | tools._bootstrap                               | ❌ N/A          | Task list doesn't reference this (GPT checked design doc)                                                       |
  | ripgrep dependency                             | ✅ ADDRESSED    | Already in Appendix E                                                                                           |

  Critical Bug Found

  Task 2.3 (DocumentIR Regression Test) uses wrong API:
  # WRONG - method doesn't exist
  ir = DocumentIR.from_parser_output(result)

  # CORRECT - method is on MarkdownParserCore
  ir = parser.to_ir()
ChatGPT sanoi:

Mietti 1m 37s
You are right to sanity-check me here. Let me realign with your validation table and then push the plan back into a “this actually works” state.

I will focus on:

Correcting my earlier mistakes

Calling out where the spec + AI task list pair is still drifting

Giving concrete, minimal fixes (especially for Task 2.3 and the implementation-status table)

1. Where my previous feedback was wrong or misleading
1.1 Extended security fields are implemented, not “future”
Your validation is correct: the “extended” security fields are already wired in markdown_parser_core.py:

suspected_prompt_injection and prompt_injection_in_images / *_in_links / *_in_code / *_in_tables are set in the “RAG Safety: Comprehensive prompt injection detection” block.

has_meta_refresh, has_frame_like, html_disallowed, raw_dangerous_schemes, has_style_scriptless, disallowed_link_schemes are also set in the HTML / scheme detection logic.

has_bidi_controls, bidi_controls_present, invisible_chars, mixed_scripts, oversized_footnotes, footnote_injection, has_csp_header, has_xframe_options are all present and written in the unicode / footnote / HTML security section.

But in PYDANTIC_SCHEMA.md you still have an implementation status table that labels many of these as “Reserved – not yet wired” or “Partial”.

So the current situation is:

Parser: treats these like live, first-class fields.

Spec table: calls them “Reserved” / “not yet wired”.

That is backwards. For the RAG-critical stuff, the parser is already ahead of the documentation.

Impact:
If someone treats the status table as authoritative, they may:

Under-test fields that are actually wired and important (suspected_prompt_injection, has_meta_refresh, etc.).

Think they can safely drop these from Pydantic models or fixtures.

You should update the table so that:

All fields that are actually written in markdown_parser_core.py are marked Implemented (or at least Partial + Tested where appropriate).

Only truly “planned but not in code” fields stay in the Reserved bucket.

1.2 DocumentIR.from_parser_output is a real bug in the task list
Your table is absolutely correct: in the AI task list, Task 2.3 uses a non-existent API:

# WRONG
ir = DocumentIR.from_parser_output(result)
The real API is anchored on the parser:

# CORRECT (per current codebase)
parser = MarkdownParserCore(...)
parser.parse()          # or parse_markdown_file(...) wrapper
ir = parser.to_ir()     # IR is derived from parser state, not from a free function
So Task 2.3, as written, would break immediately when someone tries to implement the regression test.

Minimal fix in the AI task list:

Change Task 2.3 to explicitly say:

Use MarkdownParserCore.to_ir() as the only supported API for converting parser state to DocumentIR. The old idea of DocumentIR.from_parser_output() is not implemented and must not be used.

And show a short example in the task list:

from doxstrux.markdown_parser_core import MarkdownParserCore

parser = MarkdownParserCore(content=raw_markdown, security_profile="strict_rag")
result = parser.parse()
ir = parser.to_ir()

# Assert core invariants between result and IR
assert ir.metadata.total_lines == result["metadata"]["total_lines"]
...
This is not optional; without this fix the task list is lying about the public surface.

1.3 tools._bootstrap and ripgrep
Your validation table is also right on these:

tools._bootstrap: my earlier concern does not apply to the AI task list as it stands. The task list does not reference this at all, so it is a non-issue for executing the plan. (It may still be relevant in the broader design doc, but not for this task list.)

ripgrep: already covered in Appendix E; no need for extra hand-wringing there.

So you can safely ignore my earlier “you forgot ripgrep” alarm for this particular pair.

2. Is this spec + AI task list a “solid pair”?
Short answer: it’s close, but not yet “I fully trust this as SSOT”. The pair is much better than previous generations, but:

The implementation status table in PYDANTIC_SCHEMA.md is out of sync with markdown_parser_core.py.

Task 2.3 in PYDANTIC_SCHEMA_AI_TASK_LIST.md uses a non-existent API (DocumentIR.from_parser_output) instead of the real parser.to_ir().

There is still an implicit tension around SSOT:

Schema wants to be SSOT for output shape.

Parser is effectively SSOT for runtime behavior.

Fixtures sit in between as “witnesses” but the relationship is not made explicit.

2.1 What is already good about the pair
The schema doc and task list both converge on the idea:
“One unified ParserOutput Pydantic model, validated against real parser output, used in ~600 fixtures.”

The task list correctly sequences the work:

Define model

Empty output test

Then bulk fixtures

The regression master (doxstrux_regression_master.md) explicitly exercises the RAG-critical security signals that are now confirmed to be implemented.

The task list addresses the extra="forbid" risk with a phased approach instead of flipping it on all at once.

This is enough that I would say:

“Yes, this is a viable pair to drive a real refactor, as long as you apply the corrections below.”

3. Minimal corrections to remove drift
If you want a tiny set of surgical edits that “unbreak” the pair:

3.1 Fix the implementation status table in PYDANTIC_SCHEMA.md
Right now, the “Security Models (TARGET – core fields implemented, extended fields reserved)” table marks many fields as Reserved that are actually set by the parser.

Concrete action:

For each of these fields, change Status column to reflect reality:

html_disallowed → Implemented

mixed_scripts → Implemented

raw_dangerous_schemes → Implemented (or Partial if you believe more patterns are coming)

has_style_scriptless → Implemented

has_meta_refresh → Implemented

has_frame_like → Implemented

disallowed_link_schemes → Implemented

oversized_footnotes → Implemented

footnote_injection → Implemented

suspected_prompt_injection → Implemented

prompt_injection_in_* (images/links/code/tables) → Implemented

has_bidi_controls / bidi_controls_present → Implemented

invisible_chars → Implemented

has_csp_header → Implemented

has_xframe_options → Implemented

For anything truly not wired in markdown_parser_core.py, leave as Reserved and add a comment:

“Not present in current parser output. Do not rely on this field until parser work is done.”

This turns the table back into a real map of reality instead of a stale design artifact.

3.2 Fix Task 2.3 in PYDANTIC_SCHEMA_AI_TASK_LIST.md
Replace the bogus DocumentIR.from_parser_output call with the real parser API.

Conceptually:

Old text:

“Use DocumentIR.from_parser_output(result) to build the IR and assert consistency.”

New text:

“Use MarkdownParserCore.to_ir() as the only supported way to build DocumentIR from parsed markdown. Do not introduce DocumentIR.from_parser_output().”

And in the example snippet:

# BEFORE (wrong)
ir = DocumentIR.from_parser_output(result)

# AFTER (correct, aligned with current code)
parser = MarkdownParserCore(content=raw_markdown, security_profile="strict_rag")
result = parser.parse()
ir = parser.to_ir()
This is exactly the kind of small but lethal drift you want your task list to flush out early, not encode.

3.3 Make SSOT relationship explicit in the schema doc
You raised it earlier: “Which is SSOT – schema or parser?”

Right now, the de-facto reality is:

Parser is SSOT for actual behavior.

Schema is SSOT for what tests and downstream code expect the shape to be.

Fixtures are witnesses that the two agree.

I would add a short, explicit paragraph in PYDANTIC_SCHEMA.md (near the top):

Parser (markdown_parser_core.py) is the SSOT for how fields are populated.

ParserOutput models in this document are the SSOT for the shape and types of the output.

Regression fixtures must be regenerated whenever parser behavior or schema changes.

Validation uses extra="forbid" once the parser and schema are aligned, to detect drift in either direction.

This makes the contract obvious and prevents “but the table said reserved” style confusion in the future.

4. Answering your implicit question
“Is this a solid pair? Is the task list better?”

With the corrections above:

Yes, this becomes a solid, executable pair:

PYDANTIC_SCHEMA.md = shape + status SSOT (and now actually matches the code)

PYDANTIC_SCHEMA_AI_TASK_LIST.md = step-by-step, non-hallucinated implementation plan

And:

Yes, the task list is better than older refactor plans:

It does not invent nonexistent subsystems.

It references real files and real APIs (once you fix Task 2.3).

It is tightly scoped around one dimension: “lock down parser output shape”.

If you like, next step could be:

I propose a very small patch hunk for the status table and Task 2.3 text, so you can drop it straight into Git.

Sinä sanoit:
PYDANTIC_SCHEMA_AI_TASK_LIST.md
Tiedosto
PYDANTIC_SCHEMA.md
Tiedosto
Ultra brutally strict feedback on task list. Spec also for your references.
ChatGPT sanoi:

Mietti 4m 32s
Short answer: the task list is much closer to reality than the spec and mostly safe to execute, but there are a few real drifts, some “paper-only” references that don’t exist, and some environmental assumptions that could break the codebase or CI if you follow it mechanically without tightening them.

I’ll go through this in a structured, very critical way.

1. Hard correctness / “will this break the codebase?” issues
1.1 DocumentIR API — task list fixed it, spec is still wrong
The spec still shows DocumentIR.from_parser_output(result) as the canonical API for IR regression tests. 
PYDANTIC_SCHEMA


The task list correctly calls out that this method does not exist and mandates parser.to_ir() instead in test_document_ir_regression.py. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Implication:

If you implement tests directly from the spec instead of the task list, you will add a test that calls a non-existent method and break the suite.

The task list is correct here; the spec is stale. You should explicitly mark the spec’s “DocumentIR.from_parser_output” usage as historical, or you will re-inject this bug later.

Action:
Treat the task list as the SSOT for the IR API. Add an explicit “API corrected: use MarkdownParserCore.to_ir()” note into PYDANTIC_SCHEMA.md or, better, move all IR-related guidance into code-adjacent docs and mark the IR section of the spec as obsolete.

1.2 Non-existent tools/verify_security_fields.py
The Phase 0 Clean Table gate uses:

grep -rn "TODO\|FIXME\|XXX" tools/discover_parser_shape.py tools/verify_security_fields.py …
and Appendix C lists tools/verify_security_fields.py as a file that will be created. 
PYDANTIC_SCHEMA_AI_TASK_LIST


But the task list never defines such a tool. Security verification is done via tests/test_security_field_verification.py only. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Implications:

The documented Clean Table check references a file that does not exist. If you copy-paste that command into scripts or CI, it will fail or silently ignore half of what you think you are checking.

Appendix C’s file tracking table is also wrong for this entry.

Action:

Either:

Add the missing tools/verify_security_fields.py that wraps the test logic, or

Fix the docs and commands to point to tests/test_security_field_verification.py and remove the phantom file from Appendix C.

Right now this is small “paper drift”, but it is exactly the kind of thing that leads to half-trusted gates over time.

1.3 Environment-coupled test commands (.venv, /tmp, rg)
The task list makes several hard assumptions about the environment:

Python path: Most subprocess tests call .venv/bin/python … directly. 
PYDANTIC_SCHEMA_AI_TASK_LIST


This assumes:

You always use uv in “managed venv” mode.

CI and local shells both have .venv/bin/python available.

If someone runs tests inside uv run pytest … but the .venv folder layout changes or they use a global interpreter, those subprocess calls will break even though tests themselves are running fine.

/tmp path in test_validate_test_pairs.py:

result = subprocess.run(
    [".venv/bin/python", "tools/validate_test_pairs.py",
     "--report", "--output", "/tmp/test_report.json"],
    …
)
``` :contentReference[oaicite:5]{index=5}  

- This is POSIX-only. On Windows this will fail because `/tmp` doesn’t exist.

Ripgrep (rg) as a hard requirement in tests:

test_no_legacy_field_runtime_usage shells out to rg and expects return code 0 or 1. 
PYDANTIC_SCHEMA_AI_TASK_LIST


If rg is not installed, return code will typically be 127; the test will fail with “rg failed”, which is intentional, but it makes the test suite dependent on a non-Python tool.

Appendix E documents this dependency, but it’s still easy to miss when someone onboards or runs tests in a minimal container. 
PYDANTIC_SCHEMA_AI_TASK_LIST


None of these are fatal, but they are brittle.

Actions:

Wrap the interpreter path in a helper (e.g. PYTHON = os.environ.get("DOXSTRUX_PY", sys.executable)) and reuse it in all subprocess tests.

Replace /tmp with tempfile.NamedTemporaryFile in tests.

For rg:

Either keep the hard failure (and ensure CI image always has rg), or

Add a small pre-check that skips the test with a clear message if rg is missing.

Right now these are “footguns”: they won’t break the library, but they can make your test suite look flaky or “broken out of the box” in certain environments.

1.4 Timing of extra="forbid" flip
The task list is very explicit that extra="forbid" on DoxBaseModel is a Phase 2.4 action, only after all nested models are typed and the suite passes. 
PYDANTIC_SCHEMA_AI_TASK_LIST


However, there are a few subtle coupling points:

ParserOutput.empty() is defined once, early, returning dict-shaped nested structures. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Later phases assume metadata and structure become typed models with extra="forbid", but the task list does not explicitly restate that empty() must be updated to construct those typed models rather than raw dicts.

If someone flips DoxBaseModel to extra="forbid" and adds typed Metadata / Structure without updating empty(), the empty() implementation could:

Still be accepted (Pydantic will coerce nested dicts into models), so tests pass, but

Mask the fact that your “canonical empty baseline” is never validated against the real parser output or the final nested types – making the empty baseline semantically weaker than you think.

Not a direct break, but a hidden invariant leak.

Action:

Add a concrete sub-task in Phase 2.1/2.2:

“Update ParserOutput.empty() to construct Metadata, Content, Structure, and Mappings instances explicitly once these models exist; do not rely on implicit dict coercion.”

And add one explicit test in test_output_models_empty.py that asserts type:

empty = ParserOutput.empty()
assert isinstance(empty.metadata, Metadata)
assert isinstance(empty.structure, Structure)
That closes the gap between the phased plan and the final contract in the spec. 
PYDANTIC_SCHEMA


2. Drift vs the design spec
2.1 Extended security fields: spec is wrong, task list is right
Spec still frames many extended security fields as “reserved / not yet implemented” and says they should be optional with defaults. 
PYDANTIC_SCHEMA


The task list explicitly corrects this and lists the fields as already implemented in markdown_parser_core.py (with line references), and instructs you not to treat them as reserved. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Your own validation summary also confirmed these fields exist today.

Implication:

There is explicit drift: if someone reads only the spec, they will design models that treat these fields as optional future additions, which under-tests current behavior.

The task list better matches the real parser, and must be treated as authoritative for security fields.

Action:

Add a short “Design vs reality” correction section at the top of PYDANTIC_SCHEMA.md:

“SecurityStatistics fields listed below are all implemented in the current parser; ignore any earlier statements treating them as reserved.”

Or better: once output_models.py exists, freeze PYDANTIC_SCHEMA.md as historical and move all normative field documentation next to the Pydantic models, as the spec itself suggests. 
PYDANTIC_SCHEMA


2.2 Spec still talks about tools._bootstrap; task list quietly removes it
Spec’s export tool example uses import tools._bootstrap to set up sys.path. 
PYDANTIC_SCHEMA


Task list’s tools/export_schema.py uses a simple sys.path.insert(0, … / "src") and does not reference tools._bootstrap. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Given your own note that _bootstrap doesn’t exist / is N/A in this repo, the task list is again correct and the spec is stale.

This is fine as long as you commit to: “spec is design history; task list + code are the truth”.

Action:
Mark all tools/_bootstrap occurrences in the spec as obsolete, or add a one-liner at the top: “All references to tools._bootstrap are historical; current tooling uses direct sys.path setup.”

2.3 Plugin policy / profile invariants are described in spec but not implemented in task list
The spec has a deferred phase for verifying that the parser uses ALLOWED_PLUGINS consistently and that math and footnotes are always present under the permissive profile. 
PYDANTIC_SCHEMA


The task list:

Mentions nothing about ALLOWED_PLUGINS tests.

Does not contain a dedicated “plugin policy” test module.

This is not immediately breaking, but it is real drift:

The spec treats plugin policy as part of the schema’s behavioral contract.

The task list ignores it, so a future refactor can silently break profile behavior without any schema-level tests catching it.

Action:

Either:

Explicitly drop plugin-policy enforcement from scope (and mark that in PYDANTIC_SCHEMA.md), or

Add a small task (Phase 2 or 3) to implement the spec’s plugin-policy tests in tests/test_plugin_policy_consistency.py as described in the spec. 
PYDANTIC_SCHEMA


Right now you’re half-committed: spec promises invariants no test enforces.

2.4 SCHEMA_CHANGELOG.md is still only in the spec
The spec states that once output_models.py exists, SCHEMA_CHANGELOG.md becomes the SSOT for version history and the spec becomes historical. 
PYDANTIC_SCHEMA


The task list:

Mentions .phase-N.complete.json artefacts and a CI test that enforces schema_version format. 
PYDANTIC_SCHEMA_AI_TASK_LIST


But does not include a concrete task to create or maintain SCHEMA_CHANGELOG.md.

Result:

versioning is partially enforced (via tests and CI) but the promised changelog SSOT never appears; history remains trapped in the spec file you are explicitly telling yourself not to treat as SSOT once code exists.

Action:

Add a small Task (Phase 2 or 3): “Create src/doxstrux/markdown/SCHEMA_CHANGELOG.md and add entry for parser-output@1.0.0 when models are first introduced; future schema changes must edit this file.”

This closes the loop between design intent and executable governance.

3. Coverage / scope gaps in the task list
These are not “bugs” but places where the plan is weaker than you might think.

3.1 No explicit test guaranteeing parse("") is at least schema-valid
Both spec and task list correctly state that ParserOutput.empty() is a helper, not a spec for parse("").

However:

You currently have no test that asserts “whatever MarkdownParserCore.parse("") returns must validate against ParserOutput”.

All RAG tests use non-empty markdown.

So it is technically possible to refactor the parser such that parse("") starts emitting a slightly different top-level shape and you only notice when some external consumer breaks.

Action:

Add one simple test:

def test_empty_string_output_validates():
    parser = MarkdownParserCore("", security_profile="permissive")
    raw = parser.parse()
    ParserOutput.model_validate(raw)  # must not raise
This stays aligned with the “empty() is not behavior spec” rule, but still guarantees schema validity for the empty input corner case.

3.2 Task 3.2 “invalid fixture detection” is underspecified
test_validation_detects_invalid_fixture() for the curated validator is intentionally very loose: it accepts any of these outcomes:

non-zero returncode or

“error”/“invalid” in output or

“0 validated” in output. 
PYDANTIC_SCHEMA_AI_TASK_LIST


This is pragmatic for a first cut, but:

It allows the validator to silently accept “0 validated” when pointed at a directory with no true fixtures, which makes the test mostly a smoke test.

That’s fine for a tool under development, but it’s weaker than the rest of your Clean Table standards.

Action:

Tighten the test once the tool stabilises, e.g. require that for --fixture-dir pointing at a non-empty dir:

either some validations run and failures are reported, or

exit code is 1 with an explicit “no fixtures matched” message.

Right now, the test can pass while the validator is doing essentially nothing.

3.3 Some spec-described tests are not mirrored 1:1 in the task list
The spec describes a rich set of semantic tests (e.g. link discriminated union, math extraction, footnote behaviour) that are only partially reflected in the task list’s Phase 2–4 test sketches.

The task list focuses on:

Minimal Pydantic wiring

RAG-critical tests

IR regression

Validation tools and CI

All good priorities, but:

If you assume “Specification’s coverage matrix is fully implemented by this task list”, that’s not true yet.

The “footnotes always present under permissive profile” tests, for example, are still only in the spec.

Action:

Either explicitly de-scope these extra tests, or

Add a short “Phase 2.x: port remaining semantic tests from spec to tests/test_parser_output_schema_conformance.py.”

Without that, spec and plan will diverge further over time.

4. Overall verdict and concrete recommendations
4.1 Is the task list “solid” as an execution plan?
Given your actual parser and the corrections you already validated:

The task list is substantially more accurate and safer than the spec for:

RAG safety behaviour

IR API usage

Shape discovery and phased extra="forbid" rollout 
PYDANTIC_SCHEMA_AI_TASK_LIST


The biggest previous landmines (DocumentIR API, “extended security fields not implemented”) are fixed in the task list but still live in the spec.

So, yes: as a practical refactor plan that won’t randomly break the codebase if executed carefully, the task list is solid — with the caveats above.

4.2 Minimal, high-leverage fixes I would make before treating it as SSOT
Kill the obviously wrong references:

Remove/rename tools/verify_security_fields.py references.

Add a small errata in the spec for extended security fields and IR API.

Harden environment assumptions:

Introduce an interpreter helper for subprocess tests instead of hard-coding .venv/bin/python.

Replace /tmp with tempfile.

Decide and document whether rg is a hard requirement (and if so, ensure CI images and CONTRIBUTING mention it).

Close the SCHEMA_CHANGELOG loop:

Add a Phase 2 task to create and maintain SCHEMA_CHANGELOG.md as described in the spec.

Add the one missing corner test:

parse("") validates against ParserOutput.

Make an explicit call on plugin-policy tests:

Either implement them (as suggested by the spec) or explicitly mark them out of scope for this refactor.

If you do those, the pair:

Spec = historical design + extended rationale.

Task list = executable, self-consistent, and strict enough to prevent accidental schema drift.

And, crucially, the task list will no longer contain the small internal drifts that are currently at odds with the standards it’s trying to enforce.


Lähteet
Sinä sanoit:
PYDANTIC_SCHEMA_AI_TASK_LIST.md
Tiedosto
Strict feedback
ChatGPT sanoi:

Mietti 2m 31s
Short verdict: this task list is strong but not yet at your own standard of “if tests pass, it works”. There are still internal contradictions, weak tests you could satisfy with stubs, and some governance drift (IDs, file tracking, Clean Table enforcement). I’ll be blunt and precise.

1. Structural / governance issues (your highest bar)
1.1 Task numbering is inconsistent (2.2a used twice)
You use 2.2a twice for two different things:

In Task 2.2 (Structure Models), “2.2a: Content + Mappings”. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Later, a separate Task 2.2a: Update ParserOutput.empty() for Typed Models. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Appendix C then only tracks 2.2a | tests/test_output_models_empty.py, i.e. the second 2.2a, and has no explicit rows for the earlier “2.2a–e slices” at all. 
PYDANTIC_SCHEMA_AI_TASK_LIST


This is a classic governance bug for you:

IDs are no longer one-to-one with tasks.

File tracking table no longer covers all slices listed in 2.2 (b–e not present).

An AI/human following Appendix C as the “truth” will not implement the structure slice tasks correctly.

For your Clean Table / SSOT ethos, that’s a serious violation: the task graph is ambiguous.

Fix: renumber:

Keep 2.2 as the structural slices, with 2.2a–e.

Rename “Update empty()” to 2.3, adjust Appendix C accordingly.

Add file rows for each slice that is supposed to create or heavily touch specific files (e.g. tests/test_structure_sections_lists.py, etc.), or explicitly say “Slices 2.2b–e only update output_models.py and reuse 2.1 tests”.

Right now, the table and the narrative disagree.

1.2 Clean Table enforcement is selective and leaky
You define a strict Clean Table rule:

“No TODOs, FIXMEs, or placeholders in changed code” and “Tests pass (not skipped, not mocked away)”. 
PYDANTIC_SCHEMA_AI_TASK_LIST


But your actual enforcement snippets are narrow:

Phase 0 gate only greps tools/discover_parser_shape.py and tests/test_security_field_verification.py. Not the whole repo, not even all new test files. 
PYDANTIC_SCHEMA_AI_TASK_LIST


There is no systematic Clean Table check for:

.phase-*.complete.json files (placeholders for completion_date are explicitly allowed to be created and only “should be replaced before committing” – but nothing enforces that). 
PYDANTIC_SCHEMA_AI_TASK_LIST


New tests added in Phases 1–5.

Tools under tools/ beyond discovery/security.

Result: there is a gap between policy and practice:

You say “no placeholders”; you demonstrate commands that write YYYY-MM-DDTHH:MM:SSZ directly into tracked files, and you never show a command that checks phase artifacts for that placeholder. 
PYDANTIC_SCHEMA_AI_TASK_LIST


For you, that’s not a small cosmetic issue. It’s a governance inconsistency: the doc itself proposes a workflow that, if followed mechanically, will violate its own Clean Table rule without any automated detection.

Fix:

Add a single global Clean Table test, e.g. tests/test_clean_table_global.py, that:

rg’s for TODO|FIXME|YYYY-MM-DDTHH:MM:SSZ across the whole repo and fails if found.

Update the Phase gates to reference that test instead of ad-hoc greps.

Without that, “Clean Table” remains a slogan, not an enforced invariant.

2. Environment / portability contradictions
You did add a good “Environment Assumptions” section with PYTHON helper, tempfile, and rg skipping. 
PYDANTIC_SCHEMA_AI_TASK_LIST


But most concrete tests in the same document ignore these rules.

2.1 PYTHON helper vs hard-coded .venv/bin/python
Your environment section:

PYTHON = os.environ.get("DOXSTRUX_PYTHON", ".venv/bin/python")
# Or fallback to sys.executable
``` :contentReference[oaicite:8]{index=8}  

Yet almost every test snippet uses hard-coded `.venv/bin/python`, for example:

- `test_discover_parser_shape.py`
- `test_export_schema.py`
- `test_validate_curated_fixtures.py`
- `test_validate_test_pairs.py`
- CI gate phase checks. :contentReference[oaicite:9]{index=9}  

So the “portable pattern” is **aspirational only**. The executable parts of the plan still bake in your exact venv layout.

Implications:

- On any environment lacking `.venv/bin/python` (different venv name, Windows, `uv run` with no `.venv` on disk), all these subprocess tests will fail even if the core code is fine.
- You’re violating your own environment abstraction in the same document that introduces it.

**Fix:** either:

- Actually update all subprocess calls in the task list to use `PYTHON`, or
- Drop the environment abstraction and accept the hard dependency (but then you should not pretend it’s portable).

Right now, it’s inconsistent.

---

### 2.2 `tempfile` vs literal `/tmp` still present in old patterns

You *did* fix it in the newer test for `validate_test_pairs` by using `tempfile.NamedTemporaryFile`. :contentReference[oaicite:10]{index=10}  

But earlier narrative (e.g. your older mental model) had `/tmp/test_report.json`. If any developer or AI uses earlier snippets in your history rather than this document, they’ll reintroduce POSIX-only paths.

Given this document is meant to be **the** AI task list, you’re fine now, but:

- Be aware that there is still a subtle “version skew” between this and prior prompts; anchored AIs might drag `/tmp` back in. Not a bug in this file, but a risk in your context ecosystem.

---

### 2.3 Ripgrep: you fix it in Env, but not in the actual legacy test

The Env section shows the *correct* pattern:

```python
if not shutil.which("rg"):
    pytest.skip("ripgrep (rg) not installed - see Appendix E")
``` :contentReference[oaicite:11]{index=11}  

The actual `test_no_legacy_field_runtime_usage.py` skeleton does **not** include this skip, it calls `rg` directly and only checks `result.returncode in (0, 1)`. :contentReference[oaicite:12]{index=12}  

- If `rg` is missing, you’ll get `returncode=127`, the test fails, and the message is just “rg failed”.
- That’s acceptable if you *want* ripgrep as a hard requirement; but it contradicts your own recommended pattern for gracefully skipping when unavailable.

You’re again half-committed:

- “Use `pytest.skip` if `rg` missing” in the guidelines.
- “Hard-fail if `rg` missing” in the actual test template.

Make a decision:

- Either make `rg` a **strict dependency** (and remove the skip suggestion), or
- Implement the skip pattern in `test_no_legacy_field_runtime_usage.py`.

Right now, the doc’s guidance disagrees with its own tests.

---

## 3. Tests that are still “too easy to satisfy”

You’ve improved this a lot, but a few tests are still at “script runs + prints something” level.

### 3.1 `test_export_schema.py` – checks existence, not correctness

The schema export tests:

```python
result = subprocess.run(
    [".venv/bin/python", "tools/export_schema.py"], ...
)
assert result.returncode == 0
assert "exported" in result.stdout.lower()

assert Path("schemas/parser_output.schema.json").exists()
``` :contentReference[oaicite:13]{index=13}  

You **do not** assert:

- `$id` is set correctly.
- `title` is correct.
- Schema is stable (structure not changed accidentally).

A stub implementation like:

```python
Path("schemas/parser_output.schema.json").write_text("{}")
print("Schema exported")
passes these tests.

Given that your CI later uses git diff --exit-code schemas/parser_output.schema.json as a drift gate, this isn’t catastrophic — diff will catch changes if schema is tracked correctly. But:

As a unit test for export_schema’s intellectual property, it’s shallow: it never checks that the schema actually represents ParserOutput.

Fix: add a minimal semantic check:

Load the JSON and assert that:

"$id" equals the URL you chose.

It has properties for metadata, content, structure, mappings.

schema_version is present with the correct default.

This keeps the test small but makes it much harder for a stub to sneak through.

3.2 test_ci_workflow.py – can be satisfied by a dummy workflow
The CI workflow tests are a good idea, but currently they assert:

The YAML parses.

There’s a step whose run contains "validate_test_pairs.py" and "--threshold 100".

There’s a step whose run contains "git diff --exit-code" and "schema" in the command. 
PYDANTIC_SCHEMA_AI_TASK_LIST


A workflow like:

steps:
  - run: "echo validate_test_pairs.py --threshold 100"
  - run: "echo git diff --exit-code fake_schema.json"
would satisfy these tests but do nothing meaningful.

You likely don’t want to make this much stricter (workflow testing can get absurd), but be aware:

These tests enforce presence of commands, not correct wiring (like uv sync, correct path to tools/validate_test_pairs.py, etc.).

It is still closer to a “lint” test than an IP test.

Given your “tests must capture intellectual property” standard, I’d at least:

Assert that uses: astral-sh/setup-uv@v4 and run: uv sync appear, since that’s key to your reproducibility story.

Optionally assert that the validation step comes after dependency install, not before.

3.3 Discovery tool tests rely on manual pre-run for some checks
test_discovery_all_keys_not_empty and test_discovery_sample_outputs_valid_json skip if the files don’t exist, effectively requiring the developer to run the tool manually before tests. 
PYDANTIC_SCHEMA_AI_TASK_LIST


This is acceptable as long as the gate for Phase 0 always calls the tool before tests (you do show this in Phase 0 gate).

But it means the tests do not guarantee end-to-end behaviour on a clean checkout; they’re more like integration checks for a “pre-run state”.

You’re consistent about this in the gate, so I’d treat it as “okay but fragile” rather than fatal. It’s a conscious trade-off.

4. SSOT / scope clarity – mostly good, one subtle risk
4.1 Scope section is excellent, but enforcement depends on discipline
The “Scope Decisions” table explicitly marks plugin-policy tests and deep semantic extraction tests as out of scope for this refactor. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Given how much the design spec talks about these, this is a good and necessary narrowing.

The only risk:

An AI or human that only sees PYDANTIC_SCHEMA.md (and not this task list) will assume plugin invariants are part of the contract and may try to reintroduce them.

You mitigate this by telling the AI explicitly “Do NOT read PYDANTIC_SCHEMA.md during execution”, but for humans this is a governance/documentation problem: there is no pointer in the spec itself saying “refer to task list for reduced scope”.

I don’t think this is a bug in this document; just be aware the pair is still a two-document SSOT unless you freeze the spec as historical.

4.2 SCHEMA_CHANGELOG is finally wired, but only from Phase 2 onwards
You fixed the earlier gap: Task 2.5 explicitly creates SCHEMA_CHANGELOG.md and describes version policy. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Given the spec says “once output_models.py exists, SCHEMA_CHANGELOG is SSOT for history”, this resolves the previous inconsistency.

The remaining fragility is:

Nothing in the doc forces updates to SCHEMA_CHANGELOG.md on every schema change after 1.0.0; it’s governance-by-convention.

I’d accept this as “good enough” for now; you could add a tiny CI step later that fails if SCHEMA_CHANGELOG.md wasn’t touched when output_models.py changed.

5. Overall verdict in your mental model
With the mindset:

“I am going to find if the task list is still drifting or hiding ways for things to ‘pass tests but be wrong’.”

I see:

Major strengths:

SSOT table (parser vs models vs fixtures) at the top is clear and aligns with reality. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Scope boundaries are finally explicit (plugin-policy, semantic extraction out of scope).

IR API is now correct (parser.to_ir()).

Environment pitfalls are at least acknowledged and mostly addressed.

Real remaining issues:

Task numbering / Appendix C drift (2.2a reused, slices not tracked).

Clean Table rule under-enforced (placeholders in phase artifacts, greps only some files).

Environment section vs actual test snippets: PYTHON helper and rg skip are described but not actually used in the tests shown.

Some tools/CI tests still at “runs and prints something plausible” level, not fully capturing the IP of the code.

None of these are “this will destroy your repo if executed”, but they are exactly the sort of small cracks that, in your ecosystem, eventually become larger drift.

If you want, I can next:

Propose a very small patch bundle that:

Renumbers 2.2a→2.3.

Adds a global Clean Table test.

Updates the subprocess/rg tests to follow the PYTHON/shutil.which pattern.

Tightens test_export_schema.py just enough to make stubbing impossible.


Lähteet
Sinä sanoit:
PYDANTIC_SCHEMA_AI_TASK_LIST.md
Tiedosto
Strict feedback
ChatGPT sanoi:

Mietti 3m 50s
High-level: this task list is now strong and mostly self-consistent, but it still falls short of your own “if tests pass, it works” bar in a few places:

Some rules and examples contradict each other (especially around subprocess invocation and ripgrep).

A couple of the validation tools can still be implemented as no-op stubs and yet satisfy all the tests.

Clean Table is now enforced globally, but the way you wire phase gates and placeholders leaves small but real governance gaps.

I will stay focused on concrete, high-impact issues, not cosmetics. 
PYDANTIC_SCHEMA_AI_TASK_LIST


1. Rules vs examples: internal contradictions
1.1 PYTHON helper vs hardcoded .venv/bin/python
You explicitly state:

“All subprocess tests MUST use the PYTHON helper, not hardcoded .venv/bin/python.” 
PYDANTIC_SCHEMA_AI_TASK_LIST


But many of the normative test snippets later in the document still use:

result = subprocess.run(
    [".venv/bin/python", "tools/validate_curated_fixtures.py"],
    ...
)
and similarly for tools/validate_test_pairs.py, curator tests, etc. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Yes, you have the line:

“All test snippets in this document use .venv/bin/python for brevity, but implementations MUST use the PYTHON variable pattern shown above.”

The problem is: you are relying on readers (and AIs) to ignore the concrete code they see and obey an abstract rule instead. In practice:

An AI or a junior dev will copy-paste the snippet and never fix it.

You now have to remember that “the doc is wrong, the header note is right.”

For your own Clean Table / SSOT standard, that’s drift baked in.

Strict suggestion: either:

Update all code snippets to actually use PYTHON, or

Drop the “MUST use PYTHON” rule and accept .venv/bin/python as the canonical pattern.

Right now, you have a “do as I say, not as I show” situation.

1.2 Ripgrep: “REQUIRED” vs “skips if missing”
Appendix E says:

“ripgrep (rg) is REQUIRED for the legacy field audit test.” 
PYDANTIC_SCHEMA_AI_TASK_LIST


At the same time, your tests use a require_ripgrep fixture that calls pytest.skip when rg is missing (both in the legacy field audit and in the global Clean Table test). 
PYDANTIC_SCHEMA_AI_TASK_LIST


Net effect:

Locally, if rg isn’t installed, tests silently skip the very checks that are supposed to enforce your Clean Table and legacy invariants.

On CI, rg is present, so you get strict behavior.

On developers’ machines, the “REQUIRED” dependency is actually optional.

That’s not inherently wrong, but it is inconsistent with the wording. Either:

State clearly that rg is hard-required in CI, but tests may skip locally (and explicitly say “install rg or we won’t enforce Clean Table/legacy constraints on your machine”), or

Remove the “REQUIRED” phrasing and treat it as “soft dependency (skips if missing)”.

As written, the contract is ambiguous.

2. Clean Table: much better, but still some leaks
You’ve done the important thing: global Clean Table test with:

repo-wide rg for TODO|FIXME|XXX,

placeholder dates in .phase-*.complete.json,

placeholder dates in SCHEMA_CHANGELOG.md. 
PYDANTIC_SCHEMA_AI_TASK_LIST


That’s a big step up.

Two remaining leaks:

2.1 Phase gates vs global enforcement
Phase 0 gate still uses:

grep -rn "TODO\|FIXME\|XXX" tools/discover_parser_shape.py tests/test_security_field_verification.py ...
i.e. two files only. 
PYDANTIC_SCHEMA_AI_TASK_LIST


By Phase 3 you introduce test_clean_table_global.py, which does enforce Clean Table across the repo. But:

Phase 0 and Phase 1 can be “completed” per their gate checklists while other files in src/ already contain TODOs or placeholders.

Only Phase 3+ will catch them.

Given your governance style, this is a mild inconsistency: you’re treating Clean Table as global in prose, but as “per-task file-only” in early gates.

Not fatal, but be aware: nothing stops someone from sprinkling TODOs in src/ during Phase 1 while still passing Phase 1 gate.

2.2 Manual placeholders in phase artifacts
You explicitly allow creation of .phase-N.complete.json with:

"completion_date": "YYYY-MM-DDTHH:MM:SSZ"
…and then rely on devs to remember to replace that before commit. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Your new global Clean Table test will catch committed placeholders. Good. But the flow is:

Normal workflow: create file with placeholder → run tests before editing → tests pass → commit is technically allowed, unless you always run tests after editing the date.

It’s workable, but fragile. If you miss the last test run after editing dates, you can still accidentally commit with placeholders (e.g. adding the file via a GUI).

Given you now have test_clean_table_global.py, you are mostly safe, but the process narrative still encourages temporary debt in tracked files. That’s at odds with your otherwise strict “no debt” posture.

3. Validation tools: tests are still gameable
You repeatedly say: “Tests must encode intellectual property, not just ‘it runs’.” Measured against that, two tools are still too easy to stub.

3.1 tools/validate_test_pairs.py can be a no-op and still go green
Your tests for the full validation tool check: 
PYDANTIC_SCHEMA_AI_TASK_LIST


--help exits 0 and mentions --report / --threshold.

--report --output ... exits 0 and writes JSON with total, passed, pass_rate.

--threshold 0 exits 0.

--threshold 101 exits 1.

None of them assert that:

total > 0 for the real test dir, or

ParserOutput.model_validate is actually called, or

any real invalid fixture is detected.

A trivial stub implementation like:

def main():
    if "--help" in sys.argv:
        print("--report --threshold")
        sys.exit(0)

    # Always pretend we validated 0 fixtures successfully
    report = {"total": 0, "passed": 0, "pass_rate": 0.0}
    if "--output" in sys.argv:
        Path(output_path).write_text(json.dumps(report))

    if "--threshold" in sys.argv:
        threshold = float(sys.argv[sys.argv.index("--threshold") + 1])
        sys.exit(0 if threshold <= 0 else 1)

    sys.exit(0)
would satisfy all your tests:

--report writes a JSON object with the right keys.

--threshold 0 returns 0.

--threshold 101 returns 1.

No fixtures parsed, no schema validation performed.

If your goal is “if tests pass, the tool is actually validating fixtures against the schema”, these tests don’t get you there.

Strict, minimal improvement:

Add at least one test that runs the tool against a known-bad fixture and asserts:

failed > 0 in the report, and

exit code semantics behave as intended (non-zero when threshold cannot be met).

Without that, you can have a “green” implementation that never exercises MarkdownParserCore or ParserOutput.

3.2 tools/validate_curated_fixtures.py has the same weakness
The curated validator tests require: 
PYDANTIC_SCHEMA_AI_TASK_LIST


exit 0 for the default run,

stdout mentioning “validated” / “passed”,

some count > 0 in output, inferred via regex.

You can fake all of that by:

printing “42 fixtures validated”,

exiting with 0,

never touching actual fixture files.

There is no test that forces:

reading from the curated fixture directory,

using ParserOutput.model_validate,

or failing on a deliberately broken curated fixture.

Again, that’s not inherently wrong if you view these tools as trivial wrappers, but it does not meet your declared “intellectual property” standard.

4. Minor but real governance wrinkles
4.1 Task IDs and Appendix C mapping
You’ve improved this: Appendix C now explicitly explains that 2.2a–e slices all map to a single 2.2 file row because they only update output_models.py and reuse tests/test_typed_models.py. 
PYDANTIC_SCHEMA_AI_TASK_LIST


That note is important; without it the mapping would be ambiguous. As-is:

The numbering is technically consistent (no duplicate IDs).

The mapping is documented, but slightly non-intuitive: slices 2.2a–e are implicit sub-steps, not separate line items.

If someone later adds a new test file specifically for one slice (e.g. tests/test_structure_lists.py), Appendix C will need updating; otherwise, you’ll have invisible work not tracked there. That’s manageable, but worth being conscious of.

4.2 CI workflow tests still allow “fake compliance”
tests/test_ci_workflow.py enforces: 
PYDANTIC_SCHEMA_AI_TASK_LIST


presence of astral-sh/setup-uv,

a step containing uv sync,

a step running validate_test_pairs.py with --threshold 100,

a drift-check step containing git diff --exit-code and schema.

All of that can be satisfied by a CI file that never uses the virtualenv or tools correctly, e.g.:

- run: echo uv sync    # passes test_ci_workflow
- run: echo .venv/bin/python tools/validate_test_pairs.py --threshold 100
- run: echo git diff --exit-code schemas/parser_output.schema.json
You’re essentially linting for command presence, not for correctness of the surrounding workflow.

That might be exactly the level you want (anything stricter gets brittle fast), but it’s not “if tests pass, CI gate is strongly enforcing behavior”. It’s more “if tests pass, someone at least wrote plausible commands in the workflow”.

Given your usual standards, I’d at least call that out to yourself as a conscious trade-off.

5. Scope, SSOT, and spec interaction
Here you’ve done the right thing:

Clear SSOT table: parser → behavior, models → shape, fixtures → witness. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Explicitly forbid using PYDANTIC_SCHEMA.md during execution (“design only”). 
PYDANTIC_SCHEMA_AI_TASK_LIST


Scope section clearly marks plugin policy and deep semantic tests as out of scope for this refactor.

The remaining risk is not in this document but in the pair:

Spec still contains richer tests (plugin invariants, semantic extraction) that are not mirrored here.

Unless/ until you tag PYDANTIC_SCHEMA.md as historical and point humans to this task list as the authoritative plan, you still have a soft, double-SSOT situation for “what must be tested”.

That’s not a defect in this file, but it’s worth being explicit about in the spec itself (“for active work on schema, see PYDANTIC_SCHEMA_AI_TASK_LIST.md”).

6. Summary in your own terms
If I apply your mental model:

“I am going to find if the task list still allows drift, or lets tools ‘pass’ without doing the work.”

Then:

Strengths:

SSOT story is clear and correct.

RAG safety tests encode real behavior, not just “no crash”.

Global Clean Table is finally enforced via tests, not just prose.

IR API, extended security fields, and SCHEMA_CHANGELOG wiring all align with reality and your earlier corrections.

Weak points:

Rule/example mismatches (PYTHON helper vs snippets, ripgrep “required” vs skip) create small but real drift opportunities.

Validation tools can still be implemented as no-op stubs and satisfy the tests; they don’t yet encode enough of the intended “intellectual property” (actual schema validation over real fixtures).

Phase gates and Clean Table are not fully aligned in early phases; some debt can slip through until Phase 3.

None of this invalidates the task list, but they are genuine cracks compared to the standards you’re trying to enforce.

If you want, I can next propose a surgical tightening bundle (only a handful of extra assertions and a couple of snippet edits) that:

Forces validate_test_pairs.py and validate_curated_fixtures.py to actually touch real fixtures and schema.

Aligns all subprocess snippets with the PYTHON helper.

Makes the ripgrep “required vs skip” story explicitly consistent.


Lähteet
Sinä sanoit:
Project uses uv as package manager. Is it utilized?
ChatGPT sanoi:

Mietti 25s
No – not in a way that matches how you actually run the project with uv.

Let me separate “nominal mentions” from real utilization.

1. Where uv is mentioned
Spec (design doc) uses uv in the quick-reference table

Milestone A: uv add "pydantic>=2,<3" to add Pydantic as a dependency.

Task list CI workflow requires uv in CI

schema_validation.yml uses astral-sh/setup-uv@v4 and runs uv sync to install deps.

tests/test_ci_workflow.py explicitly checks that the workflow has a uv sync step and that it precedes the validation step.

So on paper:

uv is the package manager (uv add, uv sync).

CI is forced to install dependencies with uv.

That part is real.

2. Where uv is not actually used
Everywhere else, the plan and examples fall back to direct .venv usage, not uv:

All local commands in spec + task list use .venv/bin/python
Examples:

Discover shape:
.venv/bin/python tools/discover_parser_shape.py

Curated validator:
.venv/bin/python tools/validate_curated_fixtures.py

Full validation:
.venv/bin/python tools/validate_test_pairs.py --report

Phase gates, rollback procedures, etc., all use .venv/bin/python ....

Test snippets also shell out to .venv/bin/python

test_export_schema.py, test_validate_curated_fixtures.py, test_validate_test_pairs.py, and rollback commands all call .venv/bin/python directly.

No use of uv run, uvx, or uv pip in tests or gates

The only uv usage is:

uv add in the spec (one-time dependency add).

uv sync in CI to create the environment.

For local dev and for the “mental model” commands, uv is effectively invisible; everything is written as if the project were a plain .venv-managed repo.

3. Strict answer in your terms
With your mental model:

“Do not assume; check if the project actually uses uv as the package manager.”

Yes, uv is used as the installer in CI (astral-sh/setup-uv, uv sync).

Yes, the spec tells you to use uv add to add Pydantic.

No, uv is not integrated into the everyday test / tooling commands:

No uv run ... anywhere.

All examples and phase gates assume .venv/bin/python.

So the project currently treats uv as:

“Tool that creates/manages .venv in CI and during initial setup”

not as:

“First-class command surface for running tests and tools”.

If you want it fully aligned with “project uses uv”:

The canonical commands in the docs and task list should be uv run ... (or at least parameterized through PYTHON = sys.executable inside a uv run pytest context), not hard-coded .venv/bin/python.

Phase gates and rollback snippets should be rewritten accordingly.

Right now, uv is partially utilized (for dependency management and CI), but your developer workflow and tests are still written as if uv did not exist.

Sinä sanoit:
Can I get this refactored so that uv is used everywhere in project.

## 🧰 Package Management — uv (Standard)

We use **uv** for Python environment management and dependency resolution.

### Setup
bash
# Create virtual environment and sync dependencies
uv venv
uv sync

# Activate environment (optional, uv run handles this)
source .venv/bin/activate


### Adding Dependencies
bash
# Add new dependency
uv add package-name

# Update all dependencies
uv lock --refresh && uv sync

ChatGPT sanoi:

Mietti 25s
Here’s a refactored version that makes uv the single, explicit entry point for everything (install, run, tests, tools) and removes the need to ever call .venv/bin/python directly.

You can drop this in as a replacement for your current section:

## 🧰 Package Management — uv (Single Source of Truth)

This project uses **uv** for all Python environment management, dependency resolution, and command execution.

> Rule of thumb: **never** call `.venv/bin/python` directly.  
> Always use `uv` (`uv sync`, `uv run`, `uv add`, `uv lock`).

---

### 1. Initial Setup

```bash
# Create or update the virtual environment and install all dependencies
uv sync
Notes:

uv sync will create .venv/ automatically if it does not exist.

You do not need to activate the virtual environment manually when using uv run.

If you prefer to create the venv explicitly once:

uv venv        # optional, only needed if you want to create the venv explicitly
uv sync
2. Running Commands
All project commands are run via uv run. Examples:

# Run the full test suite
uv run pytest

# Run a single test file
uv run pytest tests/test_output_models.py

# Run a project tool
uv run python tools/discover_parser_shape.py
uv run python tools/validate_curated_fixtures.py
uv run python tools/validate_test_pairs.py --report --threshold 100
Conventions:

Replace any previous .venv/bin/python ... usage with uv run python ....

When calling modules instead of scripts, use uv run python -m package.module.

3. Adding / Updating Dependencies
# Add a new dependency
uv add package-name

# Example: add Pydantic v2
uv add "pydantic>=2,<3"

# Refresh all locked dependencies and re-sync the environment
uv lock --refresh
uv sync
4. Optional: Manual Activation (Rarely Needed)
You normally do not need to activate the venv when using uv run.
If you still want an activated shell for ad-hoc work:

source .venv/bin/activate  # Linux/macOS
# or
.\.venv\Scripts\activate   # Windows PowerShell
But even in an activated shell, the recommended pattern remains:

uv run pytest
uv run python tools/...
5. CI Alignment
In CI, we follow the same rules:

Use astral-sh/setup-uv to install uv.

Run uv sync to install dependencies.

Run all checks via uv run ... (tests, validation tools, etc.).

This keeps local and CI workflows identical and ensures uv is truly used everywhere.

Sinä sanoit:
UV_AS_PACKAGE_MANAGER.md
Tiedosto
Strict Feedback on this rule.
ChatGPT sanoi:

Mietti 38s
Short verdict: this is a good start, but by your own standards it is not yet a solid, non-drifting “rule”. It’s too absolute in one place, too vague in others, and it doesn’t explicitly handle some realities (CI vs local, multiple Python versions, existing .venv/bin/python calls in the repo). I’ll go through concrete issues and suggest minimal tightenings. 
UV_AS_PACKAGE_MANAGER


1. Governance / SSOT problems
1.1 “Single Source of Truth” is underspecified
You title it:

“uv (Single Source of Truth)”

but the actual SSOT for the environment is:

uv.lock (dependency graph),

pyproject.toml / requirements equivalents,

possibly the CI workflow.

Right now the text implies “uv itself is the SSOT”, which is not precise:

uv is the tool.

The lock file is the SSOT for exact deps;

pyproject.toml (or equivalent) is SSOT for declared deps.

You don’t mention the lock file at all, even though you call uv lock --refresh. 
UV_AS_PACKAGE_MANAGER


Strictly: that’s a conceptual slippage. The rule set would be stronger if it explicitly stated:

“uv.lock + pyproject.toml are the SSOT for dependencies; uv is the only tool used to read/write them.”

1.2 No statement about existing .venv/bin/python usage
You say:

“Rule of thumb: never call .venv/bin/python directly. Always use uv…” 
UV_AS_PACKAGE_MANAGER


But:

The current codebase and tests still contain .venv/bin/python calls (you know this from the rest of the project).

This rule does not say what to do when such calls exist.

So you have:

A rule that declares .venv/bin/python forbidden.

No explicit governance line like: “Any .venv/bin/python in scripts/tests is a bug and must be replaced with uv run.”

For your style, that’s incomplete. A strict rule needs:

“This is now the canonical pattern.”

“Anything else must be treated as drift and removed.”

As written, this can sit next to .venv/bin/python snippets and nobody knows which is “truth”.

2. Practical gaps that will bite you
2.1 You never say “you must install uv first”
Nowhere do you say:

“Install uv via X”
or

“Prerequisite: uv must be installed globally.”

For someone new to the project, the doc jumps straight into:

uv sync
If they don’t have uv installed:

This fails with “command not found”; there is no guidance.

For a “package manager rule” that is supposed to be canonical, you’re missing the first step: how to get the tool.

Minimal fix: one line before “Initial Setup”:

“Prerequisite: uv must be installed (see uv documentation). If uv is not found, install it first.”

2.2 No mention of Python version pinning
uv can (and usually does) manage the Python version used inside .venv, but your rule says nothing about:

Which Python version is required,

Whether uv should download/manage it (uv python install) or use system Python.

If the project requires e.g. Python 3.12, the rule should say:

“This project targets Python 3.12; uv will create a 3.12 venv per pyproject.toml / uv.lock.”

Without that, you rely on other docs to convey the version constraint. At minimum, this is an omission.

2.3 CI discipline is only described, not enforced
You say:

“In CI, we follow the same rules… Run uv sync … Run all checks via uv run… This keeps local and CI workflows identical.” 
UV_AS_PACKAGE_MANAGER


Reality check:

This file doesn’t show (or reference) the actual CI workflow.

There’s no explicit constraint like “any use of .venv/bin/python in CI is considered a bug”.

So the “CI alignment” section is aspirational, not enforceable:

It could be true today and drift tomorrow with no signal.

There’s no pointer: “see .github/workflows/schema_validation.yml for the canonical CI pattern.”

For a rule claiming “uv everywhere”, that’s weak.

3. Internal clarity / formatting issues
3.1 Markdown is currently malformed / noisy
The version in your file has mixed text and code fences:

“Notes:” is inside the fenced code block after uv sync. 
UV_AS_PACKAGE_MANAGER


You see duplication like:

If you prefer to create the venv explicitly once:

bash
Kopioi koodi
uv venv
This is likely copy/paste artefacts (“Kopioi koodi” etc.), but the net effect is:

The rendered markdown will be messy or broken (code fences not properly closed, extraneous “Kopioi koodi” text).

Anyone reading this in the repo will get a slightly corrupted view.

Given how central this rule is intended to be, this is worth fixing: you want clean, unambiguous markdown.

3.2 “Rule of thumb” is softer than what you actually want
You wrote:

“Rule of thumb: never call .venv/bin/python directly.”

“Rule of thumb” is soft language. For you, this is not a “rule of thumb”; it is a hard rule. Better:

“Project rule: never call .venv/bin/python directly; treat any such usage as drift.”

Right now the phrasing invites people to treat this as “best practice” rather than a constraint.

4. YAGNI / KISS vs missing useful details
For a short rule, you’ve done well on YAGNI/KISS. However, a few small additions would improve robustness without bloating it:

Lockfile as SSOT

One sentence:
“The environment is defined by pyproject.toml and uv.lock; do not edit .venv manually.”

How to run a one-off script

You show uv run python tools/... which is good.

Consider explicitly stating that all internal scripts and tooling must be invoked via uv run, never directly, even if .venv is already active.

Non-POSIX hint

You did add a Windows activation example, which is good.

For Windows users not wanting to activate, you might hint: “From PowerShell: uv run pytest also works directly.”

These are small, high-value additions that don’t complicate the rule but make it harder to misinterpret.

5. Answer in your mental model
If I use your usual lens:

“Do not assume anything; I want to see if this rule itself drifts or fails under scrutiny.”

Then:

Good:

Clear intent: uv is the only tool for install and run.

uv sync as the central operation is correct.

Explicit discouragement of .venv/bin/python is exactly the right direction.

Not good enough yet:

It does not state how to install uv, or which Python version is expected.

It claims “Single Source of Truth” but does not mention lockfile / pyproject.

It does not explicitly say “any .venv/bin/python call is now considered drift and must be removed.”

CI alignment is descriptive, not normative (there is no pointer or constraint linking this rule to real workflows).

Markdown itself is a bit broken, which undermines clarity.

So: the rule is directionally right, but for your standard of “this is the canonical, non-drifting rule that governs all usage”, it still needs tightening and a couple of explicit constraints.


Lähteet
Sinä sanoit:
Can I get corrected version as a downloadable link
ChatGPT sanoi:

Mietti 20s
Here’s the corrected version as a downloadable file:

Download UV_AS_PACKAGE_MANAGER_UPDATED.md

You can drop this in place of the old rule file, or inline its content into your main docs. 

Sinä sanoit:
PYDANTIC_SCHEMA_AI_TASK_LIST.md
Tiedosto
Strict Feedback
ChatGPT sanoi:

Mietti 2m 14s
Top line: this task list is strong and much tighter than earlier rounds, but it still falls short of your own “if tests pass, it really works” bar in a few specific places. There are still:

a few tests that a clever stub could satisfy without doing the real work,

some governance wrinkles (Clean Table vs phase gates, uv vs overrides), and

a couple of assumptions about runtime types that may not match the actual code. 
PYDANTIC_SCHEMA_AI_TASK_LIST


I’ll focus on those, not on cosmetics.

1. Environment & uv usage – mostly solid, one escape hatch
1.1 UV_RUN helper is good, but undercuts “uv is mandatory”
You now standardize:

UV_RUN = os.environ.get("DOXSTRUX_UV_RUN", "uv run python").split()
# subprocess.run([*UV_RUN, "tools/…"])
``` :contentReference[oaicite:1]{index=1}  

That’s exactly what you wanted earlier: no hard-coded `.venv/bin/python`, everything goes through uv by default.

However, you also allow:

```bash
export DOXSTRUX_UV_RUN="python"
export DOXSTRUX_UV_RUN="/usr/bin/python3.12"
``` :contentReference[oaicite:2]{index=2}  

So from the repo’s own reference doc, a dev (or AI) can:

- bypass uv entirely,
- run tests/tools with a random interpreter outside `.venv`.

For your new “uv is the hard rule” document, that’s a direct escape hatch.

If you want uv to be the *governed* path, I’d tighten:

- Keep the env override only for CI matrix / exotic setups, and say so explicitly (e.g. “only in CI images where uv cannot be used, otherwise drift”).
- Or at least state: “Using DOXSTRUX_UV_RUN without `uv run` is **only** acceptable in throwaway local experiments; never in CI or committed scripts/tests.”

Right now, the task list + uv rule together send mixed signals on “how mandatory is uv really”.

---

## 2. Clean Table vs phase gates – explicitly documented, but still leaky

You’re refreshingly honest:

> Phase 0–2: per-task files only.  
> Phase 3+: repo-wide via `test_clean_table_global.py`. :contentReference[oaicite:3]{index=3}  

You even call out:

> “TODOs can technically slip into `src/` during Phases 0–2 and pass their gates. They will be caught at Phase 3.” :contentReference[oaicite:4]{index=4}  

So this is no longer a *hidden* bug; it’s a conscious trade-off.

Question in your own terms: *does that match your claim that “Clean Table = no debt carries forward”?*

Right now:

- Phase 0 gate greps only `tools/discover_parser_shape.py` and `tests/test_security_field_verification.py`. :contentReference[oaicite:5]{index=5}  
- You can modify `src/doxstrux/...` in Phase 1, add TODOs there, and still tick the Phase 1 gate.

If you’re OK with “Clean Table is strictly enforced from Phase 3 onward”, then the document is honest. If not, the only real fix is:

- either add a `rg "TODO|FIXME|XXX" src/` to *every* phase gate, or  
- state clearly that “Clean Table is a Phase 3+ invariant; earlier phases may accumulate limited debt”.

At the moment, the narrative still reads like “Clean Table is universal”, but the mechanics are phased.

---

## 3. Tests that can still be satisfied by a stub

You’ve improved this a lot, especially for curated fixtures. But a few places are still weaker than your “IP, not just ‘runs’” requirement.

### 3.1 Full validation tool – still possible to fake

For `tools/validate_test_pairs.py` you enforce:

- `--help` exposes `--report` and `--threshold`.  
- `--report` writes JSON with `total/passed/pass_rate`.  
- `--threshold 0` exits 0, `--threshold 101` exits 1.  
- `--test-dir tools/test_mds` must produce `total >= 50`.  
- Temp dir + mixed content must produce a report with `total >= 1` and both `passed` and `failed` keys. :contentReference[oaicite:6]{index=6}  

What these tests do **not** enforce:

- That the tool actually *reads* from the specified `--test-dir` (it could hardcode `total=100` for any path).
- That it actually calls `MarkdownParserCore` or `ParserOutput.model_validate` (your “invalid fixture” test never asserts `failed > 0` because you explicitly avoid depending on what “invalid” means). :contentReference[oaicite:7]{index=7}  

A malicious or overly clever stub could:

```python
if "--test-dir" in argv:
    total = 100
else:
    total = 60
report = {"total": total, "passed": total, "failed": 0, "pass_rate": 100.0}
… and satisfy all tests without touching the filesystem or schema.

You partly mitigate this by:

Saying “we can’t assert failing fixtures without knowing what makes them invalid” and using the temp-dir test mainly to check that path-based discovery exists. But for your standard, that’s still light.

If you want to hard-guarantee that model_validate is used, you need at least one deliberate, schema-invalid case where you assert failed > 0 and pass_rate < 100 (even if it’s behind a feature flag or uses a synthetic schema). Otherwise, this remains a “structural” test, not an IP test.

3.2 DocumentIR regression assumes too much about ir.security
Your regression test uses:

ir = parser.to_ir()
assert ir.security is not None
assert ir.security.get("statistics", {}).get("has_script") is True
``` :contentReference[oaicite:8]{index=8}  

This assumes:

- `ir.security` is a `dict`, not a dataclass / Pydantic model.

If IR today uses a dict, you’re fine; but if IR evolves to a typed object (`SecurityInfo`), this test will fail even though the IR still carries the right semantics. That’s a mismatch between *structural assumption* and *semantic intent*.

For a regression test whose purpose is “IR still has security metadata”, a more robust pattern would be:

- Accept either `dict` or model (`getattr(ir.security, "statistics", ...)` with fallback to dict access), or
- Explicitly tie the test to IR’s model type if you have that spec elsewhere.

As written, this test risks breaking on perfectly legitimate internal refactors.

---

## 4. RAG and security semantics – strong, but tightly coupled

Your RAG safety contract is good and concrete:

- script tag ⇒ `has_script=True` and `has_dangerous_content=True`.  
- clean doc ⇒ `embedding_blocked` is `False`/`None`.  
- `javascript:` link ⇒ flagged via stats or warnings. :contentReference[oaicite:9]{index=9}  

You also explicitly list live fields and their line ranges in `markdown_parser_core.py`. :contentReference[oaicite:10]{index=10}  

Two subtle risks:

1. **Metadata as dict vs typed metadata**

   In Phase 1 you intentionally use dict access:

   ```python
   security = validated.metadata.get("security", {})
   stats = security.get("statistics", {})
and you document that after Phase 2 this should move to typed access. 
PYDANTIC_SCHEMA_AI_TASK_LIST


The risk is: the tests never force you to do that refactor. There is no “Phase 2+” version of the test that asserts validated.metadata is a Metadata model. That is partially covered in test_typed_models, but the RAG tests themselves will happily keep using dict access forever.

This is not wrong, but it means RAG tests are lagging behind the schema evolution. If the intent is “RAG contract also benefits from typing”, you might want a TODO-less follow-up: once Metadata is typed, update the helper to assert that and fail if it isn’t.

Hard coupling to current security profile behavior

All these tests bake in the behavior of the permissive profile. If security profiles evolve (e.g., “strict” becomes default, or detection heuristics change), the tests become policy rather than safety invariants.

You partially acknowledge this by keeping profile-policy tests out of scope, but here RAG tests already enforce policy (e.g., “clean doc MUST NOT be blocked”). That’s probably exactly what you want for RAG, just be aware: you are now treating the current heuristics as a hard contract.

5. Phase artifacts & dates – almost safe, but still human-fragile
You improved this a lot:

Global Clean Table test now explicitly checks that .phase-*.complete.json and SCHEMA_CHANGELOG.md do not contain YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD placeholders. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Mechanically that’s enough: if someone commits with placeholders, CI will fail.

The only remaining fragility is process:

The task list instructs people to generate these artifacts with placeholders and then manually edit them.

If they edit but forget to re-run tests, they can still commit; but CI will catch it, so you’re ultimately safe.

Given that, this section is acceptable. Just keep in mind: you’re relying on CI as the last safety net for Clean Table of phase artifacts, not on local discipline.

6. Scope & spec interaction – mostly clean, one residual double-SSOT risk
You now have:

A clear SSOT table (parser behavior vs models shape vs fixtures as witnesses).

Explicit instruction: do not read PYDANTIC_SCHEMA.md during execution – design only.

Explicit OUT OF SCOPE list for plugin invariants and deep semantic tests. 
PYDANTIC_SCHEMA_AI_TASK_LIST


The only remaining risk is meta-governance:

PYDANTIC_SCHEMA.md still exists and describes richer tests/constraints.

This AI task list explicitly narrows scope and sometimes contradicts earlier assumptions.

Unless you mark the spec as historical or add a short “For implementation, this task list overrides earlier spec details” note inside the spec, humans (and other AIs) may treat both as live SSOTs and try to “merge” them again later.

Not a bug in this file, but worth remembering: the pair of documents is not fully governed unless you clearly designate one as the executable SSOT.

7. Overall verdict (in your own terms)
With your mental model:

“I am going to find if this refactor plan still lets things drift or break the codebase while tests are green.”

I see:

Strong points:

uv is properly threaded through tests via UV_RUN.

Clean Table is finally backed by a global test that also checks schema/phase placeholders.

RAG tests encode real, RAG-critical semantics (not just “no crash”).

Curated fixtures tests now do make it hard to fake validation without touching Pydantic.

Real remaining weaknesses:

validate_test_pairs.py can still be stubbed to fabricate counts without ever touching parser or schema; tests don’t force a real model_validate failure case.

DocumentIR test assumes ir.security is a dict; this can break on legitimate IR refactors.

The UV_RUN override can bypass uv entirely, which conflicts with the “uv is the hard rule” you just wrote.

Clean Table is universal in spirit but only strictly enforced repo-wide from Phase 3 onward.

Nothing here is catastrophic, but they are genuine cracks relative to the standard you’re aiming for.

If you want, I can next propose a very small tightening patch set focused only on:

making validate_test_pairs.py incontrovertibly call ParserOutput.model_validate on real files,

making the DocumentIR regression test robust to dict vs model, and

aligning the UV_RUN override with the “uv is mandatory” rule (e.g. restricting to CI).


Lähteet
Sinä sanoit:
PYDANTIC_SCHEMA_AI_TASK_LIST.md
Tiedosto
Strict feedback
ChatGPT sanoi:

Mietti 2m 12s
High-level: this version is much stronger and closer to “if tests pass, it works”, but there are still a few places where (a) you can silently break parts of the codebase and the plan won’t notice, and (b) tests can still be satisfied by clever stubs or structural hacks rather than real behavior. I’ll focus on those, not on cosmetics. 
PYDANTIC_SCHEMA_AI_TASK_LIST


1. Places where this plan can still break the codebase
1.1 Flipping DoxBaseModel to extra="forbid" is global, but the plan treats it as local
Task 2.5:

“Change in output_models.py:

class DoxBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
```” :contentReference[oaicite:1]{index=1}  
The test:

from doxstrux.markdown.output_models import DoxBaseModel
extra_setting = DoxBaseModel.model_config.get("extra")
assert extra_setting == "forbid"
``` :contentReference[oaicite:2]{index=2}  

Issues:

- `DoxBaseModel` is a **generic base** – by name it’s clearly not “parser-output-only”.
- The task list never checks where else this base is used. If any other models rely on “tolerate extra fields” semantics (e.g. plugin configs, import tools, or future models), they will now start raising `ValidationError` on fields that used to be silently accepted.
- The only protection is “run the full test suite”; if existing tests do not hit those code paths, you can introduce a breaking behavior change and ship it without noticing.

Given your standards, this is a real risk:

- The plan treats `extra="forbid"` as a **local tightening** for parser output models.
- In reality, it’s a **global policy change** for every model deriving from this base.

If you want to keep `DoxBaseModel` as the shared base, you need at least:

- An explicit note: “All models inheriting from `DoxBaseModel` are now strict; any consumer relying on extra fields is invalid.”  
  or
- Introduce a *parser-specific* base (e.g. `ParserOutputBaseModel`) and flip `extra="forbid"` there only.

Right now, you can absolutely break other parts of the package while all Phase 2 tasks look “green”.

---

### 1.2 Typed `metadata` / `structure` can break any code expecting dicts

Task 2.1/2.2 make `metadata`, `structure`, `content`, `mappings` typed models and then Task 2.3 forces `ParserOutput.empty()` to return typed instances: :contentReference[oaicite:3]{index=3}  

```python
empty = ParserOutput.empty()
assert isinstance(empty.metadata, Metadata)
...
You correctly keep MarkdownParserCore.parse() returning the original dict for callers; that’s good. But there is still a potential break:

Any existing internal code that previously worked with a dict from ParserOutput (e.g. if you already use ParserOutput somewhere in tools or tests) may now encounter a model instead of a dict and break in subtle ways (e.g. metadata["total_lines"] vs metadata.total_lines).

The task list assumes ParserOutput is essentially new, or unused, and never explicitly checks for existing usages in the repo.

Given the scale of doxstrux, that is likely safe right now, but it is an assumption. To make it explicit and non-drifting:

Either state in the plan: “ParserOutput is not currently used by any runtime code; adding typed fields will not break existing callers,”

Or add a quick grep-like check (or a test) to ensure there are no existing imports/usages of ParserOutput in src/ before you mutate its semantics.

As it stands, you are making a non-trivial behavior change (return types of empty() and of any downstream consumer of validated models) without verifying that there’s no internal code relying on the old dict-like semantics.

1.3 SCHEMA_CHANGELOG as SSOT can drift from parser behavior
You correctly make SCHEMA_CHANGELOG.md the SSOT for version history of the schema: 
PYDANTIC_SCHEMA_AI_TASK_LIST


The plan says nothing, however, about coupling between:

ParserOutput.schema_version default,

the version tags in SCHEMA_CHANGELOG, and

what MarkdownParserCore actually emits (if it ever starts emitting schema_version itself).

So you can end up with:

ParserOutput.schema_version = "parser-output@1.0.1",

SCHEMA_CHANGELOG saying [parser-output@1.0.0] latest,

parser.parse() not setting schema_version at all.

The tests check that schema has "schema_version" property and default starting with "parser-output@", but they don’t enforce alignment with the changelog entries or parser behavior. 
PYDANTIC_SCHEMA_AI_TASK_LIST


Not a showstopper, but a real potential drift between three SSOT-ish sources.

2. Test design: still one big stub hole
You’ve significantly tightened the test design (especially curated fixtures and RAG safety). But one core issue remains:

2.1 “Tool must use Pydantic” test doesn’t actually hit the tool
In Task 3.2 for curated fixtures, the final test is good: it creates invalid JSON and incomplete fixtures and demands that the tool detect them. That really makes tools/validate_curated_fixtures.py call ParserOutput.model_validate() or some equivalent, or it will fail. Good. 
PYDANTIC_SCHEMA_AI_TASK_LIST


For Task 4.1 (full validation), you added this test:

def test_validation_detects_schema_violation():
    """Tool MUST detect Pydantic validation failures ..."""
    ...
    patch_script = tmppath / "inject_invalid_field.py"
    patch_script.write_text(''' ... ParserOutput.model_validate(output) ... ''')
    ...
    result = subprocess.run([*UV_RUN, str(patch_script)], ...)
    assert "VALIDATION_FAILED" in result.stdout or result.returncode == 1
``` :contentReference[oaicite:7]{index=7}  

But note:

- This test **never calls** `tools/validate_test_pairs.py`.  
- It only proves that `ParserOutput` itself honors `extra="forbid"` and fails on injected fields.
- A stub `validate_test_pairs.py` that never touches Pydantic at all can still pass **all** tests in `test_validate_test_pairs.py`, including this one, because the critical part is happening entirely inside the temporary script.

So the headline comment:

> “This is the critical IP test: it proves the tool actually calls `ParserOutput.model_validate()`…” :contentReference[oaicite:8]{index=8}  

…is simply not true. It proves the model is strict, not that the *tool* uses it.

A clever stub of `validate_test_pairs.py` can still:

- Hardcode `total ≥ 50` for `tools/test_mds`,
- Always report `passed == total`,
- Implement threshold/exit code semantics,
- Never invoke `ParserOutput`.

All current validation-tool tests would still pass.

If your bar is “if tests pass, this tool is definitely validating fixtures via Pydantic”, you need at least one test that:

- Points `--test-dir` at a directory containing a **schema-invalid** fixture (e.g. extra field or missing required field),
- Runs `tools/validate_test_pairs.py`,
- Asserts that `failed > 0` and exit code / report reflect the failure.

Right now, the only tests that force Pydantic validation are the ones for the *schema* and the *curated validator*, not for the full test-pair validator.

---

## 3. Clean Table enforcement vs definition

You’ve tightened this a lot:

- Clean Table is now explicitly “enforced repo-wide from the start”, not just from Phase 3.  
- Each phase gate uses:

  ```bash
  rg "TODO|FIXME|XXX" src/doxstrux/ && echo "❌ BLOCKED" && exit 1 || echo "✅ Clean"
  ``` :contentReference[oaicite:9]{index=9}  

- `test_clean_table_global.py` also checks placeholder dates in phase artifacts and `SCHEMA_CHANGELOG`. :contentReference[oaicite:10]{index=10}  

Remaining mismatch:

- Your formal Clean Table definition says:

  > “No TODOs, FIXMEs, or placeholders in changed code” (not only src). :contentReference[oaicite:11]{index=11}  

- Enforcement is only on:
  - `src/doxstrux/` via `rg` in phase gates,
  - placeholders in `.phase-*.complete.json` and `SCHEMA_CHANGELOG`.

Which means:

- TODOs/FIXMEs in `tools/` or `tests/` do not violate any enforced gate, even though the prose definition says they should.
- Practically, that’s probably what you want (allow TODOs in tests/dev tools), but the **text** still says “changed code” generically.

So the *real* invariant is: “No TODO/FIXME in production code under `src/doxstrux`, and no placeholder dates in phase/changelog files.” The doc still describes a stricter invariant that is not actually enforced.

Given how much you care about Clean Table, this is a small but real semantic drift inside this very spec.

---

## 4. UV enforcement and overrides

You did fix the major contradiction: Clean, explicit statement that `DOXSTRUX_UV_RUN` is for rare CI/exotic cases, not for local bypasses. :contentReference[oaicite:12]{index=12}  

However:

- Your UV rule document (separate file) says “any `.venv/bin/python` usage in this repo is drift and must be removed”;  
- This task list still uses the `DOXSTRUX_UV_RUN` override, including examples that run arbitrary scripts directly (`[*UV_RUN, str(patch_script)]`). :contentReference[oaicite:13]{index=13}  

That is fine as long as you keep them aligned, but there’s still a conceptual split:

- In the rule doc, uv is “hard mandatory everywhere” (no exceptions).
- In this task list, UV_RUN can legally be `python3.11` in CI matrices.

This isn’t a bug, but it means your **global** uv rule has one explicit escape hatch, and it lives here. I’d at least cross-reference it in the UV rule file, so you don’t forget later and start treating any override as a violation.

---

## 5. SSOT story: better, but still double-source risk with the design spec

You did the right thing by stating explicitly:

- `PYDANTIC_SCHEMA.md` is design-only; do not read it during execution. :contentReference[oaicite:14]{index=14}  

However, it still lives alongside this AI task list and describes additional tests and invariants (plugins, semantic extraction). Unless you:

- mark that spec as “superseded for implementation by the AI task list”, or
- add a small “Governance” note inside `PYDANTIC_SCHEMA.md` pointing implementers to `PYDANTIC_SCHEMA_AI_TASK_LIST.md` as the execution SSOT,

you still have a soft double-SSOT situation for humans/other tools.

Again, not a defect in this file’s logic, but a governance gap in the pair.

---

## 6. Verdict in your own terms

If I apply your lens:

> “I am going to find if this refactor plan can still break the codebase or let drift through while tests are green.”

Then:

- **Strengths (now solid):**
  - Parser vs schema vs fixtures SSOT table is clear and correct.
  - RAG safety tests encode real, production-relevant semantics (script tags, javascript links, embedding_blocked).
  - Curated fixture validator is now very hard to fake: it must actually call Pydantic or tests will fail.
  - Clean Table and phase artifacts are meaningfully enforced by tests, not just prose.
  - DocumentIR regression test is robust to dict vs model layout.

- **Real remaining cracks:**
  1. Flipping `DoxBaseModel` to `extra="forbid"` is a global behavior change that can break other models; the plan treats it as if it only affects parser output.
  2. Typed `metadata`/`structure` may break any hidden internal code that currently expects dicts; the plan assumes `ParserOutput` is unused but doesn’t verify it.
  3. The “critical” IP test for `validate_test_pairs.py` doesn’t actually touch the tool; it only proves that `ParserOutput` itself is strict.
  4. Clean Table’s **enforced** scope (src only) is narrower than its **declared** scope (all changed code).
  5. The UV rule’s “no bypass” story is slightly at odds with the legitimate `DOXSTRUX_UV_RUN` escape hatch for CI; this needs to be acknowledged as an exception in the global rule, or it will look like drift later.

None of these are catastrophic, but they are exactly the class of “small cracks” that would annoy you six months from now when you start leaning on this as your own SSOT.

If you’d like, I can next propose a *very tight* patch bundle to:

- localize `extra="forbid"` to parser models only,
- add one real “invalid fixture via tool” test for `validate_test_pairs.py`,
- and slightly sharpen the Clean Table + UV rule wording so they match the actual enforced behavior.


