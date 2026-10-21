# Engineering review skills

Skills that review code through book-grounded lenses and propose design moves, for a person at the keyboard or for a factory of agents.

## Language

**Lens**:
One book-grounded way of reviewing code, run as its own skill and as part of `restructure`.
_Avoid_: reviewer, checker, reviewing skill

**Review**:
One run of `restructure` or of a single lens over a base point or a scope.
_Avoid_: scan, audit, run

**Report folder**:
The folder a review writes: `report.md`, `moves.md`, the lens findings in `lenses/`, and the work folder.
_Avoid_: output folder, results folder

**Work folder**:
The `.work/` folder inside the report folder, where a review keeps its working files (synthesis output, check results) before it writes the review report. Lens findings sit in `lenses/`, not here.
_Avoid_: run folder, temp folder

**Ref mode** / **Scope mode**:
What a review covers. Ref mode: the code changed since a base point. Scope mode: the current code of a named area, such as a module or a service.
_Avoid_: diff mode, area mode

**Round**:
One pass of a Factory's loop: review, then apply the necessary moves.
_Avoid_: iteration, cycle, run

**Try**:
One execution of a review against a test case, to see whether its verdict comes out right.
_Avoid_: run, attempt, trial

**Finding**:
One smell a lens reports, with its evidence, cause and suggested refactoring.
_Avoid_: issue, problem

**Strong** / **Worth exploring** / **Possible**:
A finding's strength. Strong: clear evidence and a counted effect. Worth exploring: real signal, uncertain remedy. Possible: a hunch worth a look.
_Avoid_: high, medium, low; severity

**Hint**:
A smell a lens sees but can't act on at class or function scale, routed to another skill in one line.
_Avoid_: note, suggestion

**Effect**:
The counted result of acting on a finding: one measure, its count today and its count after.
_Avoid_: payoff, benefit, win, impact

**Measure**:
One of the shared counts an effect uses: places-to-change, must-know, reasons-to-change, names-per-concept, test-setup.
_Avoid_: metric, score

**Design move**:
One coherent change, synthesised from findings, that removes one or more of them.
_Avoid_: fix, recommendation

**Option**:
One of the two or three different design moves synthesis designs for a cluster of findings, before it picks one.
_Avoid_: candidate, variant

**Candidate**:
A design move that could become a necessary move once verified. The rule is in `shared/CONTRACT.md`.
_Avoid_: proposal

**Conflict**:
Two lenses pull one symbol in opposite directions, and no option dissolves it. Numbered C1, C2…; a person decides.
_Avoid_: clash, disagreement

**Machine line**:
The line under each move's heading that a machine reads: `necessary`, `check`, `after` and `key`.
_Avoid_: metadata, header

**Necessary move**:
A candidate whose check result confirms it. The rule is in `shared/CONTRACT.md`.
_Avoid_: gating move, blocking move, strong move, major move

**Left for later**:
A candidate not verified because the review reached `--max-moves`. It is neither work nor advice; the next review finds it again.
_Avoid_: not pursued, deferred

**Move log**:
The files that record each design move's history across reviews: what was proposed, and what was done with it.
_Avoid_: history, decisions file

**Declined before**:
A design move that matches a move declined in the move log, with the same evidence. Listed in the report, never necessary.
_Avoid_: rejected, skipped

**Undo**:
A design move, or the reviewed change, that works against a move the move log records as applied, on the same main symbol. It gives `ask`.
_Avoid_: revert, rollback

**Review report**:
The file a review writes, holding its verdict, design moves and hints.
_Avoid_: output, results

**Verdict**:
The part of a review report a machine reads to decide whether more work is needed: `pass`, `advise`, `change` or `ask`.
_Avoid_: status, score, indicator

**Check result**:
What a verify sub-agent decides about one design move: keep, downgrade, split or drop.
_Avoid_: verdict

**Factory**:
A chain of agents that builds software and consumes reviews to decide what to do next.
_Avoid_: pipeline, software factory, orchestrator
