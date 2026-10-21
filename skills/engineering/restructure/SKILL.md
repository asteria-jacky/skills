---
name: restructure
description: Review code through every lens at once (tests, responsibilities, domain model, depth) and synthesise the findings into verified design moves that fix several smells at once. Writes a review report with a verdict (`pass`, `advise`, `change`, `ask`).
disable-model-invocation: true
argument-hint: "[base-ref | \"scope\"] [--out <folder>] [--max-moves N] [--move-log <folder>] [--models <stage>=<model>,…]"
allowed-tools: Read Grep Glob Agent Bash(git diff *) Bash(git log *) Bash(git rev-parse *) Bash(git merge-base *) Bash(git show *) Bash(mktemp *)
---

# Restructure

Goal: find the fewest design moves that make the code speak the domain's **ubiquitous language**, give each responsibility one home, and keep modules **deep**.

Use instead: a single lens (`/jacky-skills:depth`, `responsibilities`, `domain-model`, `listen-to-tests`) for one angle only.

[`CONTRACT.md`](${CLAUDE_PLUGIN_ROOT}/shared/CONTRACT.md) defines what this review takes, reads and writes: the arguments, the report folder, the verdict, the failure reasons and the models. Read it in full first.

## Lenses

| Lens | File | Sources |
|---|---|---|
| listen-to-tests | `${CLAUDE_PLUGIN_ROOT}/skills/engineering/listen-to-tests/LENS.md` | Freeman & Pryce |
| responsibilities | `${CLAUDE_PLUGIN_ROOT}/skills/engineering/responsibilities/LENS.md` | Fowler, Martin |
| domain-model | `${CLAUDE_PLUGIN_ROOT}/skills/engineering/domain-model/LENS.md` | Evans, Vernon |
| depth | `${CLAUDE_PLUGIN_ROOT}/skills/engineering/depth/LENS.md` | Ousterhout |

A lens skill (e.g. `/jacky-skills:depth`) runs this process with only its own lens.

## Process

The paths below use `<report>` for the report folder and `<work>` for its work folder, `<report>/.work`. Run each git command on its own, with no `;`, `|`, `&&` or `echo` around it: permission grants match plain commands, and a denied command is retried plainly, never a reason to stop. Start every sub-agent on its stage's model, as **Models** in `CONTRACT.md` sets it. The sub-agents pass their work through files in the report folder, so this conversation holds only the final moves.

### 1. Make the report folder, and pin the base point or scope

Read the arguments as **Arguments** in `CONTRACT.md` defines them: the report folder, and without a base or scope argument the default base point, come from there. Folders inside the report folder appear as files are written into them.

With a base or scope argument, try it as a git ref first: if `git rev-parse <arg>` resolves, it's the base point (**ref mode**). If it doesn't resolve, it is a **scope** (**scope mode**). Leave resolving the scope to paths to the lens sub-agents in step 3; they locate it.

**Writing a failure.** When the review can't go on, write `<report>/report.md` as a failure report (see `CONTRACT.md`), print the report folder's path as the last line, and end the review. The one exception: after a `no-base` failure, a live session may ask the user for a base point and start again.

- `--models` names an unknown stage or model: `bad-argument`.
- No base point resolves without an argument: `no-base`.
- In ref mode, `git diff <base>` (working tree included) is empty: `no-change`.

Done when the mode is set and, in ref mode, the diff is non-empty.

### 2. Read the language

Read `GLOSSARY.md` (or the one `GLOSSARY-MAP.md` points to for the touched area or scope) and any ADRs in `docs/adr/`. With no glossary, the domain terms already in the code and docs are the language.

With `--move-log`, list the move log's keys: the first line of each file in the folder. A missing or empty folder is an empty move log. In ref mode, also find each key whose last decision is `applied` and whose main symbol the change touches, by the **Undo** rule in `CONTRACT.md`. Do this for every applied key, whatever the lenses later flag.

### 3. Scan, one sub-agent per lens

Dispatch one sub-agent per lens in the review, all in a single message so they run in parallel, and wait for every one to report. Each prompt carries:

- **Ref mode**: the diff command and the base point.
- **Scope mode**: the scope name, with instructions to locate it first (by directory, module name, class/service name, or whatever else identifies it) before scanning. If nothing in the codebase matches, it replies that instead of scanning.
- The glossary/ADR paths.
- The absolute path to its lens file, to read in full first, and to `${CLAUDE_PLUGIN_ROOT}/shared/FINDINGS.md`, whose **Report format** it must follow.
- Its report path: `<report>/lenses/<lens>.md`.
- The brief:
  - **Ref mode**: _"Scan the changed code and the existing code it touches, duplicates, or collaborates with. Concept consolidation needs both sides, so look past the diff."_
  - **Scope mode**: _"Scan all code in this scope, plus the existing code it touches, duplicates, or collaborates with. This isn't limited to recent changes: review the scope's current state as a whole."_
  - Both close with: _"Look only through your lens: another sub-agent covers each other lens. Report only what the code shows: an empty findings block is a valid report. Write your report to your report path in the Report format of FINDINGS.md, and reply with one line."_

A sub-agent that reports the scope doesn't exist: write a `no-scope` failure. A lens with no report file: write a `lens-failed` failure.

Done when every lens's report file exists.

### 4. Synthesise

Dispatch one sub-agent and wait for it. Its prompt carries the report folder, the work folder, the mode, the lens names in the review, the glossary/ADR paths, the ref-mode diff command or the scope, and the absolute path to `${CLAUDE_PLUGIN_ROOT}/shared/SYNTHESIS.md`, to read in full and follow, with `${CLAUDE_PLUGIN_ROOT}/shared/CONTRACT.md` for the rules it points to. It writes `<work>/moves.md`.

With `--move-log`, the prompt also carries the move log folder and the paths of:

- its matching files: each file whose key's main symbol sits in a file named in a lens report's `where` or `cast`;
- the applied files whose main symbol the change touches, from step 2, for synthesis to judge as undoes.

Synthesis reads them before it proposes anything.

No `<work>/moves.md`: write a `synthesis-failed` failure. A `moves.md` with zero moves is a valid result; go to step 6.

Done when `<work>/moves.md` exists.

### 5. Verify

`moves.md` marks each candidate (`necessary: candidate` in its machine line; the rule is under **Necessary moves** in `CONTRACT.md`). Verify:

- **every candidate**, in rank order, until `--max-moves` necessary moves are confirmed (default 5). A combined candidate gets its own verify sub-agent; group single-finding candidates about five per verify sub-agent;
- the **top five other combined moves** by rank, one verify sub-agent each.

Dispatch the first wave in a single message: the candidates in rank order up to `--max-moves` of them, plus the top five other combined moves. Wait for every one. A candidate is confirmed when its check result makes it a necessary move by the rule in `CONTRACT.md`. While fewer than `--max-moves` are confirmed and unverified candidates remain, dispatch the next ones in rank order, as many as are still needed, and wait again. Candidates still unverified when the count is reached are **Left for later**.

Each prompt carries the report folder, the work folder, the move numbers it checks, and the absolute path to `${CLAUDE_PLUGIN_ROOT}/shared/VERIFY.md`, to read in full and follow. Each writes `<work>/verify-<n>.md` per move.

A dispatched move with no verify file stays unverified, and an unverified move is never necessary.

Done when every dispatched move has a verify file or is marked unverified, and either `--max-moves` necessary moves are confirmed or no unverified candidate remains.

### 6. Write the report folder

Read `<work>/moves.md` and every verify file, and apply each check result:

- **keep**: label the move **verified**.
- **downgrade**: turn each claim that wasn't confirmed into ✘ with the verifier's reason, recount the move's value, and label it **verified (downgraded)**.
- **split**: split the move where the verifier says, each part keeping its own claims, and label each part **verified (split)**.
- **drop**: remove the move; its findings go under **Dropped** with the verifier's reason.
- Fix every correction in the move's text, and add each unlisted worse and each conflict with another move.

Then sort each move into one group:

- **Necessary moves**: candidates whose check result makes them necessary by the rule in `CONTRACT.md`.
- **Left for later**: candidates never verified because `--max-moves` was reached.
- **Other moves**: every other move that remains, including split parts and candidates that lost their Strong finding.

Re-rank by value inside each group, number the moves 1 to n through `moves.md`, and rewrite each machine line with its final values: `necessary: yes | no`, the check result (`none` if unverified), and `after` in the new numbers.

Set the verdict by the rule in `CONTRACT.md`, in its order. For `ask`, a conflict involves a necessary move when a symbol in the conflict appears in that move's **Who's involved**; a move reopens an ADR when its **ADR** line says `reopen: yes`; each entry under **Undoes** in `<work>/moves.md` gives `ask`, with its U number in `ask`; it keeps that number in `report.md`, with `by: move <n>` in the new move numbers. Moves under **Declined before** in `<work>/moves.md` go under Declined before in `report.md` and count in `declined-before` only.

Write `<report>/moves.md` and `<report>/report.md` as `CONTRACT.md` lays them out, in its **Report prose** style. Each move must stand on its own: its objects and their neighbours, what they do today, and what they do after.

With `--move-log`, append a `proposed` entry for each move in `moves.md` and each move under Declined before, in the shape `CONTRACT.md` gives. Create the file, with its key heading, when the key has none.

Done when `<report>/report.md` has a verdict, the counts in its frontmatter match `moves.md`, and with `--move-log` every move has its `proposed` entry.

Then close the review:

- **Live session**: show the verdict, each move's heading with one line on what changes, the conflicts and the undoes. Ask which moves to apply, and how to settle each conflict and undo. Apply nothing yet.
- **Under `claude -p`**: the session ends here, with the report on disk.

Either way, the last line of your message is the report folder's path.

### 7. Apply, one move at a time

Only when the user picks moves. First run the test suite once and record which tests pass and fail. The **baseline** is for comparison, not a gate: a red baseline is noted, not blocking.

Then for each chosen move, in the order the user prefers (the suggested order by default):

1. Make the restructure, step by step as the move lists them.
2. Rerun the affected tests and diff against the baseline.
3. For each newly failing test, give your read: a **regression** (behaviour broke: fix the code) or a **pinned test** (it asserted the old shape: update or delete it, ideally folding it into fewer tests through the new interface). The user decides.
4. When a rename changes a domain term and `GLOSSARY.md` exists, update it in the same step.
5. With `--move-log`, append an `applied` entry `by restructure` to the move's file: Done when met or not, what was hard, notes for next time.
6. Show the diff and wait for the go-ahead before the next move.

Done when every chosen move is applied or explicitly dropped.

Hints stay in the report. Leave running them to the user or the Factory.
