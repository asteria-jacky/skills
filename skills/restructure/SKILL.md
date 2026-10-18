---
name: restructure
description: Restructure freshly implemented code toward the domain's ubiquitous language and deep modules. Runs every lens in parallel, merges their findings into design moves, reports first, then applies the moves you pick, one at a time.
disable-model-invocation: true
argument-hint: "[base-ref | scope]"
---

# Restructure

Implementation gets code _working_; this skill makes it _fit_. Review what changed since a base point, or the current state of a named scope, through several **lenses**, each grounded in its own books, and restructure the code so names speak the **ubiquitous language**, each responsibility has one home, one concept lives in one place, and modules are **deep**.

Each lens runs in its own sub-agent. Their findings come back in one shared format, [`FINDINGS.md`](${CLAUDE_PLUGIN_ROOT}/shared/FINDINGS.md), and merge into **design moves**: one coherent restructure per concept, with conflicts between lenses surfaced rather than resolved silently.

## Lenses

| Lens | File | Sources |
|---|---|---|
| listen-to-tests | `${CLAUDE_PLUGIN_ROOT}/skills/listen-to-tests/LENS.md` | Freeman & Pryce |
| design | `${CLAUDE_PLUGIN_ROOT}/skills/restructure/LENSES.md` | Fowler, Martin, Evans, Vernon, Ousterhout |

`design` holds the lenses not yet split into their own skills. A lens skill (e.g. `/jacky-skills:listen-to-tests`) runs this process with only its own lens.

## Process

### 1. Pin the base point or scope

Without an argument, use the merge-base with the default branch (`git merge-base HEAD origin/HEAD`, else `main`/`master`) as the base point. If neither resolves, ask the user.

With an argument, try it as a git ref first: if `git rev-parse <arg>` resolves, it's the base point (**ref mode**: reviews what changed since then).

If it doesn't resolve, treat the argument as a **scope** instead (**scope mode**: a module, service, or feature name like "Log module", "Editor", "ShippingService"): reviews that area's current code regardless of recent changes. Don't try to resolve the scope to paths yourself; the sub-agents in step 4 locate it.

Done when, in ref mode, `git diff <base>` (working tree included) is non-empty; in scope mode, once the mode is set: the sub-agents confirm the scope exists.

### 2. Read the language

Read `GLOSSARY.md` (or the one `GLOSSARY-MAP.md` points to for the touched area or scope) and any ADRs in `docs/adr/`. With no glossary, the domain terms already in the code and docs are the language.

### 3. Snapshot the test baseline

Run the test suite once and record which tests pass and fail. The **baseline** is for comparison, not a gate: a red baseline is noted, not blocking.

### 4. Scan, one sub-agent per lens

Dispatch one sub-agent per lens in the run, all in a single message so they run in parallel, and wait for every one to report. Each prompt carries:

- **Ref mode**: the diff command and the base point.
- **Scope mode**: the scope name, with instructions to locate it first (by directory, module name, class/service name, or whatever else identifies it) before scanning. If nothing in the codebase matches, it reports that back instead of scanning.
- The glossary/ADR paths.
- The absolute path to its lens file, to read in full first, and to `FINDINGS.md`, whose **Report format** it must follow.
- The brief:
  - **Ref mode**: _"Scan the changed code and the existing code it touches, duplicates, or collaborates with. Concept consolidation needs both sides, so look past the diff."_
  - **Scope mode**: _"Scan all code in this scope, plus the existing code it touches, duplicates, or collaborates with. This isn't limited to recent changes: review the scope's current state as a whole."_
  - Both close with: _"Look only through your lens: another sub-agent covers each other lens. Report in the Report format of FINDINGS.md, and nothing else."_

If a sub-agent reports that the scope doesn't exist, stop and tell the user.

### 5. Merge into design moves

Follow **Merging into design moves** in `FINDINGS.md`. With one lens in the run there is nothing to converge or conflict: each finding becomes its own move, ranked by strength.

Done when every finding sits in exactly one move or one conflict.

### 6. Report

Present the moves in rank order, then the conflicts, then the hints, each under its own heading. Ask which moves to apply, and how to settle each conflict. Apply nothing yet.

### 7. Apply, one move at a time

For each chosen move, in the order the user prefers:

1. Make the restructure, step by step as the move lists them.
2. Rerun the affected tests and diff against the baseline.
3. For each newly failing test, give your read: a **regression** (behaviour broke: fix the code) or a **pinned test** (it asserted the old shape: update or delete it, ideally folding it into fewer tests through the new interface). The user decides.
4. When a rename changes a domain term and `GLOSSARY.md` exists, update it in the same step.
5. Show the diff and wait for the go-ahead before the next move.

Done when every chosen move is applied or explicitly dropped.

### 8. Close with hints

Restate the hints against the restructured code, each naming the skill to run and where:

- Module- or service-scale coupling, cohesion, or boundary smells: `/modularity:review` or `/improve-codebase-architecture`.
- Mechanical duplication with no domain concept behind it: `/simplify`.

Hints are for the user to run. Leave invoking them to the user.
