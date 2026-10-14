---
name: restructure
description: Restructure freshly implemented code toward the domain's ubiquitous language and deep modules. Reports findings first, then applies the ones you pick, one at a time.
disable-model-invocation: true
argument-hint: "[base-ref | scope]"
---

# Restructure

Implementation gets code _working_; this skill makes it _fit_. Review what changed since a base point, or the current state of a named scope, through the **lenses** in [LENSES.md](LENSES.md) (Fowler, Freeman & Pryce, Ousterhout, Martin, Evans, Vernon) and restructure it so names speak the **ubiquitous language**, each responsibility has one home, one concept lives in one place, and modules are **deep**.

The lenses are a way of seeing, not a checklist. Any smell the books name is in scope.

## Process

### 1. Pin the base point or scope

Without an argument, use the merge-base with the default branch (`git merge-base HEAD origin/HEAD`, else `main`/`master`) as the base point. If neither resolves, ask the user.

With an argument, try it as a git ref first: if `git rev-parse <arg>` resolves, it's the base point (**ref mode** — reviews what changed since then).

If it doesn't resolve, treat the argument as a **scope** instead (**scope mode** — a module, service, or feature name like "Log module", "Editor", "ShippingService"): reviews that area's current code regardless of recent changes. Don't try to resolve the scope to paths yourself; the sub-agent in step 4 locates it.

Done when, in ref mode, `git diff <base>` (working tree included) is non-empty; in scope mode, once the mode is set — the sub-agent confirms the scope exists.

### 2. Read the language

Read `GLOSSARY.md` (or the one `GLOSSARY-MAP.md` points to for the touched area or scope) and any ADRs in `docs/adr/`. With no glossary, the domain terms already in the code and docs are the language.

### 3. Snapshot the test baseline

Run the test suite once and record which tests pass and fail. The **baseline** is for comparison, not a gate: a red baseline is noted, not blocking.

### 4. Scan in a sub-agent

Dispatch one sub-agent so the code-reading stays out of this conversation. Its prompt carries:

- **Ref mode**: the diff command and the base point.
- **Scope mode**: the scope name, with instructions to locate it first (by directory, module name, class/service name, or whatever else identifies it) before scanning. If nothing in the codebase matches, it reports that back instead of scanning.
- The glossary/ADR paths.
- The absolute path to [LENSES.md](LENSES.md), to read in full first.
- The brief:
  - **Ref mode**: _"Scan the changed code and the existing code it touches, duplicates, or collaborates with. Concept consolidation needs both sides, so look past the diff."_
  - **Scope mode**: _"Scan all code in this scope, plus the existing code it touches, duplicates, or collaborates with. This isn't limited to recent changes — review the scope's current state as a whole."_
  - Both close with: _"For each finding report: **Technique** (the named refactoring and its book), **Where** (files/symbols), **Smell** (what's wrong, in domain terms), **Restructure** (what changes), **Tests** (which tests it will likely break, and whether they test behaviour or are pinned to internals), **Strength** (`Strong` / `Worth exploring` / `Speculative`). Separately list **hints**: module- or service-scale smells, and non-domain mechanical duplication, with the area each concerns. Under 600 words."_

### 5. Report

Present findings ordered by strength, then the hints under their own heading. Ask which findings to apply. Apply nothing yet.

### 6. Apply, one finding at a time

For each chosen finding, in the order the user prefers:

1. Make the restructure.
2. Rerun the affected tests and diff against the baseline.
3. For each newly failing test, give your read: a **regression** (behaviour broke: fix the code) or a **pinned test** (it asserted the old shape: update or delete it, ideally folding it into fewer tests through the new interface). The user decides.
4. When a rename changes a domain term and `GLOSSARY.md` exists, update it in the same step.
5. Show the diff and wait for the go-ahead before the next finding.

Done when every chosen finding is applied or explicitly dropped.

### 7. Close with hints

Restate the hints against the restructured code, each naming the skill to run and where:

- Module- or service-scale coupling, cohesion, or boundary smells: `/modularity:review` or `/improve-codebase-architecture`.
- Mechanical duplication with no domain concept behind it: `/simplify`.

Hints are for the user to run. Leave invoking them to the user.
