---
name: restructure
description: Restructure freshly implemented code toward the domain's ubiquitous language and deep modules. Runs every lens in parallel, synthesises their findings into design moves that fix several smells at once, verifies them, reports first, then applies the moves you pick, one at a time.
disable-model-invocation: true
argument-hint: "[base-ref | scope]"
---

# Restructure

Implementation gets code _working_; this skill makes it _fit_. Review what changed since a base point, or the current state of a named scope, through several **lenses**, each grounded in its own books, and restructure the code so names speak the **ubiquitous language**, each responsibility has one home, one concept lives in one place, and modules are **deep**.

Each lens runs in its own sub-agent and reports in one shared format, [`FINDINGS.md`](${CLAUDE_PLUGIN_ROOT}/shared/FINDINGS.md). A synthesis sub-agent then looks for the root causes behind the smells and turns them into **design moves**: the fewest coherent changes that remove the most smells, with conflicts between lenses surfaced rather than resolved silently. Verify sub-agents check each move that claims to fix several smells before you see it.

The sub-agents pass their work through files in a **run folder**, so this conversation holds only the final moves.

## Lenses

| Lens | File | Sources |
|---|---|---|
| listen-to-tests | `${CLAUDE_PLUGIN_ROOT}/skills/listen-to-tests/LENS.md` | Freeman & Pryce |
| responsibilities | `${CLAUDE_PLUGIN_ROOT}/skills/responsibilities/LENS.md` | Fowler, Martin |
| domain-model | `${CLAUDE_PLUGIN_ROOT}/skills/domain-model/LENS.md` | Evans, Vernon |
| depth | `${CLAUDE_PLUGIN_ROOT}/skills/depth/LENS.md` | Ousterhout |

A lens skill (e.g. `/jacky-skills:depth`) runs this process with only its own lens.

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

Create the run folder with `mktemp -d -t restructure-XXXXXX` and tell the user its path.

Dispatch one sub-agent per lens in the run, all in a single message so they run in parallel, and wait for every one to report. Each prompt carries:

- **Ref mode**: the diff command and the base point.
- **Scope mode**: the scope name, with instructions to locate it first (by directory, module name, class/service name, or whatever else identifies it) before scanning. If nothing in the codebase matches, it replies that instead of scanning.
- The glossary/ADR paths.
- The absolute path to its lens file, to read in full first, and to `FINDINGS.md`, whose **Report format** it must follow.
- Its report path: `<run>/<lens>.md`.
- The brief:
  - **Ref mode**: _"Scan the changed code and the existing code it touches, duplicates, or collaborates with. Concept consolidation needs both sides, so look past the diff."_
  - **Scope mode**: _"Scan all code in this scope, plus the existing code it touches, duplicates, or collaborates with. This isn't limited to recent changes: review the scope's current state as a whole."_
  - Both close with: _"Look only through your lens: another sub-agent covers each other lens. Write your report to your report path in the Report format of FINDINGS.md, and reply with one line."_

If a sub-agent reports that the scope doesn't exist, stop and tell the user.

Done when every lens's report file exists.

### 5. Synthesise

Dispatch one sub-agent and wait for it. Its prompt carries the run folder, the lens names in the run, the glossary/ADR paths, the ref-mode diff command or the scope, and the absolute path to `${CLAUDE_PLUGIN_ROOT}/shared/SYNTHESIS.md`, to read in full and follow. It writes `<run>/moves.md`.

Done when `moves.md` exists.

### 6. Verify the combined moves

Dispatch one sub-agent per **combined** move in `moves.md`, the top five by rank at most, all in a single message, and wait for every one. Each prompt carries the run folder, the move's number, and the absolute path to `${CLAUDE_PLUGIN_ROOT}/shared/VERIFY.md`, to read in full and follow. Each writes `<run>/verify-<n>.md`.

Skip this step when the run has a single lens. Combined moves left unchecked, below the top five or in a single-lens run, are labelled **unverified** in the report.

Done when every dispatched move has a verify file.

### 7. Report

Read `moves.md` and every verify file, and apply each verdict:

- **keep**: label the move **verified**.
- **downgrade**: turn each claim that wasn't confirmed into ✘ with the verifier's reason, recount the move's value, and label it **verified (downgraded)**.
- **split**: split the move where the verifier says, each part keeping its own claims.
- **drop**: remove the move; its findings go under **Dropped** with the verifier's reason.
- Fix every correction in the move's text, and add each unlisted worse and each conflict with another move.

Re-rank by value after the verdicts. Present the moves in rank order, in the move format of `SYNTHESIS.md`, then the conflicts, then **Dropped**, then the hints, each under its own heading. The user hasn't read the code the sub-agents read: each move must stand on its own, naming its objects and their neighbours with `path:line`, what they do today, and what they do after. End with the suggested apply order. Ask which moves to apply, and how to settle each conflict. Apply nothing yet.

Done when the user could choose between the moves without opening a file.

### 8. Apply, one move at a time

For each chosen move, in the order the user prefers (the suggested apply order by default):

1. Make the restructure, step by step as the move lists them.
2. Rerun the affected tests and diff against the baseline.
3. For each newly failing test, give your read: a **regression** (behaviour broke: fix the code) or a **pinned test** (it asserted the old shape: update or delete it, ideally folding it into fewer tests through the new interface). The user decides.
4. When a rename changes a domain term and `GLOSSARY.md` exists, update it in the same step.
5. Show the diff and wait for the go-ahead before the next move.

Done when every chosen move is applied or explicitly dropped.

### 9. Close with hints

Restate the hints against the restructured code, each naming the skill to run and where:

- Module- or service-scale coupling, cohesion, or boundary smells: `/modularity:review` or `/improve-codebase-architecture`.
- Mechanical duplication with no domain concept behind it: `/simplify`.

Hints are for the user to run. Leave invoking them to the user.
