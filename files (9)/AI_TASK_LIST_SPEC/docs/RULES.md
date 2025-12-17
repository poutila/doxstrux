# AI_TASK_LIST Rules Reference

**Spec:** AI_TASK_LIST_SPEC
**Version:** 2.0.0
**Generated:** 2025-12-17 02:47:50

---

## Overview

This document contains 33 rules defined in the ai_task_list specification.

---

## Rules

### R-ATL-000

**Description:** If spec and linter diverge, linter MUST be updated to match spec

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_000`

---

### R-ATL-001

**Description:** Task list MUST start with YAML front matter containing ai_task_list block with schema_version, mode, runner, runner_prefix, search_tool

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_001`

---

### R-ATL-002

**Description:** Mode semantics: template allows placeholders; plan requires real commands; instantiated forbids all placeholders

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_002`

---

### R-ATL-003

**Description:** Only `[[PH:NAME]]` placeholders recognized, NAME matching `[A-Z0-9_]+`

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_003`

---

### R-ATL-010

**Description:** Task list MUST contain all required headings with exact text and case

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_010`

---

### R-ATL-011

**Description:** If mode is plan or instantiated, MUST include `## Prose Coverage Mapping` section with table

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_011`

---

### R-ATL-020

**Description:** Baseline Snapshot MUST include table with Date, Repo, Branch, Commit, Runner, Runtime rows

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_020`

---

### R-ATL-021

**Description:** Baseline Snapshot MUST include Evidence block with commands and output

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_021`

---

### R-ATL-022

**Description:** In instantiated mode, linter MUST fail if any `[[PH:...]]` tokens remain

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_022`

---

### R-ATL-023

**Description:** In instantiated mode, required evidence slots MUST contain real output lines

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_023`

---

### R-ATL-024

**Description:** With `--require-captured-evidence`, evidence blocks MUST include cmd and exit headers

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_024`

---

### R-ATL-030

**Description:** Phase headings MUST match `^## Phase (\d+) — (.+)$`; Phase 0 MUST exist

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_030`

---

### R-ATL-031

**Description:** Task headings MUST match `^### Task (\d+)\.(\d+) — (.+)$`; Task IDs MUST be unique

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_031`

---

### R-ATL-032

**Description:** Every task MUST contain `**Paths**:` block with `TASK_<N>_<M>_PATHS=(<quoted paths>)`

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_032`

---

### R-ATL-033

**Description:** Document MUST include naming rule linking Task ID N.M to array exactly once

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_033`

---

### R-ATL-040

**Description:** Each non-Phase-0 task MUST include TDD Step 1, 2, 3 headings

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_040`

---

### R-ATL-041

**Description:** Each non-Phase-0 task MUST include `### STOP — Clean Table` with evidence slots and checklists

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_041`

---

### R-ATL-042

**Description:** Linter MUST verify presence of five Clean Table checklist items

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_042`

---

### R-ATL-050

**Description:** Task list MUST include `## Phase Unlock Artifact` section with .phase-N.complete.json generation

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_050`

---

### R-ATL-051

**Description:** `## STOP — Phase Gate` MUST include checklist referencing unlock artifacts

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_051`

---

### R-ATL-060

**Description:** `## Global Clean Table Scan` MUST include command and evidence paste slot

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_060`

---

### R-ATL-061

**Description:** In instantiated mode, `[[PH:PASTE_CLEAN_TABLE_OUTPUT]]` MUST NOT remain

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_061`

---

### R-ATL-063

**Description:** When runner=uv and instantiated, Global Clean Table MUST include import hygiene checks

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_063`

---

### R-ATL-070

**Description:** runner and runner_prefix MUST be non-empty strings (or runner_prefix explicitly empty)

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_070`

---

### R-ATL-071

**Description:** In instantiated mode with non-empty runner_prefix, tool invocations MUST include prefix

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_071`

---

### R-ATL-072

**Description:** When runner=uv and instantiated, forbidden: .venv/bin/python, python -m, pip install

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_072`

---

### R-ATL-075

**Description:** In plan/instantiated mode, command lines in gated sections MUST start with `$`

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_075`

---

### R-ATL-080

**Description:** Drift Ledger MUST contain table with Date, Higher, Lower, Mismatch, Resolution, Evidence columns

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_080`

---

### R-ATL-090

**Description:** Each task MUST contain `**Status**:` with exactly one of: PLANNED, IN PROGRESS, COMPLETE, BLOCKED

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_090`

---

### R-ATL-091

**Description:** If task is COMPLETE and instantiated, all checklist items in STOP block MUST be checked

**Section:** §2 RULES

**Enforcement:** `enforce_r_atl_091`

---

### R-LNT-001

**Description:** Linter exit codes: 0=pass, 1=violations, 2=usage error

**Section:** §2 RULES

**Enforcement:** `enforce_r_lnt_001`

---

### R-LNT-002

**Description:** Default diagnostics format: path:line:rule_id:message

**Section:** §2 RULES

**Enforcement:** `enforce_r_lnt_002`

---

### R-LNT-003

**Description:** With --json flag, emit JSON object with passed, error_count, errors, mode, runner, schema_version

**Section:** §2 RULES

**Enforcement:** `enforce_r_lnt_003`

---

