# Review contract

What every review skill takes, reads and writes: `restructure` and each lens, and every new lens. `restructure`'s [`SKILL.md`](../skills/engineering/restructure/SKILL.md) holds the process that fulfils it. Advice for the Factory that runs reviews is in [`FACTORY.md`](FACTORY.md); no review reads it.

## Arguments

```
[base-ref | "scope"] [--out <folder>] [--max-moves N] [--move-log <folder>] [--models <stage>=<model>,…]
```

- `base-ref | "scope"`: an argument that `git rev-parse` resolves is a base point and gives **ref mode**: the review covers what changed since then. Anything else is a scope (a module, service or feature name such as "Editor") and gives **scope mode**: the review covers that area's current code. With no argument, the base point is the merge-base with the default branch: `git merge-base HEAD origin/HEAD`, else the same with `main`, then `master`. Quote a scope that has spaces.
- `--out <folder>`: the report folder. Without it, a new temp folder from `mktemp -d -t restructure-XXXXXX`.
- `--max-moves N`: stop verifying candidates once N necessary moves are confirmed. Default **5**.
- `--move-log <folder>`: the [move log](#move-log) to read and append to. Without it, the review reads and writes no move log.
- `--models <stage>=<model>,…`: override the default model per stage (see **Models**), e.g. `--models lens=opus,verify=haiku`. A stage other than `lens`, `synthesis` or `verify`, or a model that is neither an alias (`sonnet`, `opus`, `haiku`) nor a full model ID (`claude-…`), gives the failure `bad-argument`.

## What a review reads

- The code in and around the diff or scope: the changed code (or the scope's code) and the code it touches, duplicates or collaborates with.
- `GLOSSARY.md`, or the one `GLOSSARY-MAP.md` points to for the area.
- The ADRs in `docs/adr/`.
- With `--move-log`, the move log files that match its moves, and every file whose last decision is `applied` and whose main symbol the reviewed change touches (see [Undo](#undo)), before synthesis proposes anything.

## What a review writes

- The report folder, before it asks anything. It never commits it.
- With `--move-log`, entries appended to the move log: `proposed` after the report is written, `applied` when it applies a move.
- Code, and `GLOSSARY.md` for a renamed term, only when someone applies a move after the report is written.

The review writes nowhere else.

## Report folder

```
<report folder>/
  report.md          # frontmatter, then the index and short sections
  moves.md           # every design move in full
  lenses/<lens>.md   # each lens's findings
  .work/             # the work folder: synthesis output, check results, other working files
```

The last line of the review's output is the report folder's path, on its own line. This holds for failures too.

### `report.md`

Frontmatter:

```yaml
verdict: change            # pass | advise | change | ask; absent when failure is set
failure: no-change         # only when the review could not finish; absent when verdict is set
mode: ref                  # ref | scope
base: 270efe5              # ref mode; or  scope: "Editor"
lenses: [depth, domain-model, listen-to-tests, responsibilities]
necessary: [1, 3]          # move numbers
ask: []                    # move numbers, conflict numbers (C1, C2…) and undo numbers (U1, U2…) behind an `ask`
counts: {moves: 5, necessary: 2, unverified: 2, left-for-later: 1, declined-before: 0, conflicts: 1, undoes: 0, hints: 3}
work: <report folder>/.work
```

`verdict` and `failure` never appear together. `counts.moves` counts every move in `moves.md`, Left for later included.

Body, in this order, each section under its own `##` heading. Leave out a section with nothing in it.

1. **Moves**: one line per design move, `- [<n>. <title>](moves.md#<anchor>) · necessary | other | left-for-later · verified | unverified`.
2. **Conflicts**: numbered C1, C2…, each with both sides, each lens's reasoning and a recommendation.
3. **Undoes**: numbered U1, U2…, one line each: `- U<n> · key: <applied key> · by: move <n> | the change · how: <what works against the applied move>`.
4. **Declined before**: moves that match a move declined in the move log, with the same evidence. One line each: `- <title> · key: <key> · declined: <old reason> · removes: <finding ids>`.
5. **Dropped**: findings no move acts on, each with its reason.
6. **Hints**: one line each, so a Factory can route it: `- skill: /simplify · where: src/billing/ · why: same date parsing in 3 files`.
7. **Suggested order**: the order to apply the moves in.

A failure report holds the frontmatter (with `failure`, without `verdict`) and one sentence that says what failed.

### `moves.md`

Every design move in the move shape of [`SYNTHESIS.md`](SYNTHESIS.md), numbered 1 to n through the whole file, in three groups:

- `## Necessary moves`, in rank order;
- `## Other moves`, in rank order, each heading labelled `verified`, `verified (downgraded)`, `verified (split)` or `unverified`;
- `## Left for later`: candidates not verified because `--max-moves` was reached. They don't become work and don't change the verdict. The next review finds them again.

Each move has its machine line directly under its heading and a **Done when** part.

### Report prose

Prose in `report.md`, `moves.md`, `lenses/` and the work folder follows ASD-STE100 style: short sentences, one idea in each, common verbs. Write for a reader who hasn't opened the code: every object named with its `path:line`, every smell and refactoring explained in a clause the first time it appears.

## Necessary moves

A **candidate** is a design move that removes (✔, not ◐) at least one **Strong** finding in the code the review was asked to look at:

- in ref mode, a finding whose `where` or `cast` lies in the reviewed diff. A move that acts only on untouched code is never a candidate, so it can reach `advise` at most;
- in scope mode, a finding anywhere in the scope.

A candidate is a **necessary move** when its check result is `keep`, or `downgrade` and it still removes (✔) a Strong finding that made it a candidate. A move listed under Declined before is never a candidate.

## Opposite directions

These `direction` pairs are opposite, in either order: `extract` against `combine` or `inline`; `introduce` against `remove`; `hide` against `expose`. Opposite directions on the same symbol make a **conflict** between lenses, or an **undo** against the move log.

## Verdict

| Value | Means | The Factory |
|---|---|---|
| `pass` | nothing to do | goes on |
| `advise` | design moves exist, but no necessary move | goes on; the moves are optional |
| `change` | at least one necessary move | goes back and applies the necessary moves |
| `ask` | a person must decide | stops and asks a person |

Apply the rule in this order; the first that holds decides:

1. The review could not finish → **no verdict**. `report.md` holds `failure: <reason>` instead. A broken review never reads as `pass`.
2. `ask` if any of these holds. List those move, conflict and undo numbers in `ask`.
   - a conflict between lenses involves a symbol that a necessary move touches;
   - a design move contradicts an ADR strongly enough to reopen it;
   - a design move, or the reviewed change itself, **undoes** an `applied` move in the move log (see [Undo](#undo)).
3. `change` if there is at least one necessary move.
4. `advise` if there is at least one other design move. Moves under Left for later or Declined before don't count.
5. `pass` otherwise. A review whose only moves are under Declined before gives `pass`.

Zero findings and zero design moves are a normal, expected result, and give `pass`. Conflicts that don't involve a necessary move are reported but don't change the verdict.

## Move log

The **move log** records each design move's history across reviews, so each review starts from what earlier ones learned. It is the `--move-log` folder, chosen by the Factory or person (e.g. `.scratch/<feature>/move-log/`). The Factory or person decides whether to commit it. Reviews write no ADRs: the move log keeps the reason for a "no", and a "no" today can become a "yes" later.

### File shape

One Markdown file per move key. The file name is the key in lower case, with each run of characters other than letters and digits turned into one `-`: `line-item-introduce-src-billing-invoice-ts-invoice-addline.md`. The first line is the exact key as a heading; match keys on that line, not on the file name. Entries follow, oldest first, each under its own `##` heading. Append only: earlier entries stay as written.

```
# Line Item · introduce · src/billing/invoice.ts#Invoice.addLine

## proposed · head 3f2a1bc · base 270efe5
group: necessary
check: keep
report: /tmp/restructure-a1b2c3
findings:
- responsibilities · Data Clumps · src/billing/invoice.ts:42 · Strong
- domain-model · Glossary term with no class · src/billing/invoice.ts:42 · Strong
effects:
- places-to-change 3 → 1 (tax rule in tax.ts:17, refund.ts:60, checkout.ts:91)

## declined · by Factory
reason: The billing rewrite next sprint replaces Invoice.
notes: Raise it again if the rewrite keeps addLine.

## applied · by restructure
done-when: met
hard: Two pinned tests in tax.test.ts asserted on TaxCalculator.lineTax.
notes: -
```

| Entry | Written by | Fields |
|---|---|---|
| `proposed` | the review, for each design move, after it writes the report | `group`: `necessary`, `other`, `left-for-later` or `declined-before`; `check`: the check result, `none` if unverified; `report`: the report folder; `findings`: one line per finding the move removes or partly removes, `<lens> · <smell> · <where> · <strength>`; `effects`: those findings' `effect` lines |
| `applied` | the interactive apply step, for each move it applies; otherwise the implementer, the Factory or a person | `done-when`: `met`, or `not met` and what is left; `hard`: what was hard; `notes`: for next time |
| `declined` | the implementer, the Factory or a person | `reason`: why; `notes`: for next time |

A `proposed` heading names the commit reviewed (`head <sha>`, from `git rev-parse --short HEAD`) and the base or scope. An `applied` or `declined` heading names who wrote it (`by <who>`). A field with nothing to say holds `-`.

### Matching

A move log file **matches** a design move when its key has the move's main symbol: the same key, or a key with another concept or direction on that symbol. A key's **last decision** is the latest `applied` or `declined` entry in its file.

- **Declined, same evidence.** The move's own key has last decision `declined`, and the evidence has not grown since the `proposed` entry just before that decision. The move is never necessary. It goes under **Declined before** in `report.md` with the old reason, and stays out of `moves.md`.
- **Declined, grown evidence.** The evidence has **grown** when the move removes a Strong finding that the earlier `proposed` entry doesn't list (match on smell and `where`), or a "today" count in its effects is higher than in that entry. The move is judged as if never declined, and its text shows the old reason.
- **Undo.** See [Undo](#undo).

### Undo

An **undo** works against a move whose last decision is `applied`, on that move's main symbol. Two things can undo:

- **a design move**: it matches the applied key, and its direction is opposite to the key's (see [Opposite directions](#opposite-directions));
- **the reviewed change**: it reverses what the applied move did on its main symbol. It calls around the symbol, copies the symbol's body back to a caller, splits again what was combined, or exposes again what was hidden.

To find the second kind, compare the diff with the applied entries, not only the files a lens flags. In ref mode, an applied key's main symbol is **touched by the change** when `git diff <base> --name-only` lists the symbol's file, or `git diff <base> --name-only -G'<name>'` lists any file, where `<name>` is the symbol's last segment (`TaxPolicy` for `src/tax.py#TaxPolicy`, `addLine` for `src/billing/invoice.ts#Invoice.addLine`). Synthesis reads each touched file's history and judges whether the change undoes the move. Scope mode has no reviewed change, so only design moves can undo.

Each undo is listed under **Undoes** in `report.md`, and the verdict is `ask`.

## Failures

A review that can't finish writes `failure: <reason>` in `report.md`, with no verdict, before it asks anything:

| Reason | When |
|---|---|
| `bad-argument` | `--models` names an unknown stage or model |
| `no-base` | no base point resolves |
| `no-change` | the diff is empty |
| `no-scope` | nothing matches the scope |
| `lens-failed` | a lens wrote no report |
| `synthesis-failed` | synthesis wrote no `moves.md` |

A question nobody can answer becomes a failure or an `ask` verdict. The review never guesses.

## Models

| Stage | Default |
|---|---|
| `lens` | `sonnet` |
| `synthesis` | session model |
| `verify` | `sonnet` |
| main session | session model |

Start each sub-agent with the Agent tool's `model` set to its stage's model; for the session model, leave `model` out. `--models` overrides `lens`, `synthesis` and `verify` with a model alias (`sonnet`, `opus`, `haiku`) or a full model ID such as `claude-sonnet-4-5`. The main session runs on the model the session started with.

## Hints: what no lens covers

Lenses report these as hints, never as findings:

- module- or service-scale coupling, cohesion or boundaries → `/improve-codebase-architecture`;
- mechanical duplication with no domain concept behind it → `/simplify`.
