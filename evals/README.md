# Review eval suite

Checks that a review's verdict is still right after a change to the review skills. Each case is a tiny fixture repo, a slash command, and exact regex checks on the report the review writes (`review/report.md`, `review/moves.md`). No model judges the output.

| Case | Seeded | Skill | Expected | Tag |
|---|---|---|---|---|
| `clean` | tidy change that reuses `add_tax` | `responsibilities` | a verdict, never `change` | `clean` |
| `smell-in-diff` | the tax rule written out in 2 changed files | `depth` | `change`; a necessary move's key names tax; listed as necessary | `verdict` |
| `smell-outside-diff` | the same smell, only in untouched files | `depth` | `pass` or `advise` | `verdict` |
| `declined` | `smell-in-diff` plus a move log declining that move | `depth` | `pass` or `advise`; the logged key under Declined before | `verdict` |
| `conflict` | `Checkout` keeps Marketing's member discount in a one-line method with one caller (depth: inline; responsibilities: extract), plus a tax leak | `restructure` | `ask`, naming a conflict | `verdict` |
| `undo` | a move log with `TaxPolicy` extracted and applied; the change calls around it | `restructure` | `ask`; the Undoes section names that key | `verdict` |
| `empty-diff` | no change since `base` | `depth` | `failure: no-change`, no verdict | `failure` |

Each case's tags also name its skill, so you can see which cases a lens touches.

## Run

Needs Claude Code ≥ 2.1.269 (`claude plugin eval`) and git ≥ 2.31. Run from the plugin root.

- **Quick**, 1 try per case, all cases in parallel: `evals/run.sh quick`. Run it before merging a change to a `LENS.md`, `shared/*.md` or `restructure`'s `SKILL.md`.
- **Touched cases only**: name the cases, e.g. `evals/run.sh quick smell-in-diff smell-outside-diff declined empty-diff conflict undo` for a change to `depth/LENS.md`. A lens's `LENS.md` touches its own cases (by tag) plus `conflict` and `undo`, which run every lens. A change to `shared/` or `restructure` touches all cases.
- **Full**, 3 tries per case (`empty-diff`: 1): `evals/run.sh full`. Run it before a release, or when Quick looks shaky.
- **Fixtures and graders only**, free: `python3 -m unittest discover -s evals/tests`. Run it after editing a `fixture.sh` or a grader.

`run.sh` runs each case as its own `claude plugin eval` call, so each case gets its own bar (`--threshold` applies to a whole call). The bar per tag is set in one place, `threshold_for` in `run.sh`. In Quick, a single wrong try fails its case. The script prints one line per case and the results folder, `evals/results/<time>-<mode>/` (git-ignored), with each case's JSON, log and HTML report.

Settings, as environment variables:

- `EVAL_MODEL`: the model under test. Default `sonnet`. Pin it so a model rollout doesn't look like a skill regression.
- `EVAL_MAX_COST_USD`: the cost ceiling per case call. Default `3`. It is checked before each try starts, so it stops later tries, not one in flight.

Each call passes `--ablation none` (the slash command doesn't exist without the plugin), `--scaffold` (the fixture scripts build the repos), `--trust-plugin`, `--no-publish`, and the exact tool grants in `grants` in `run.sh`: writes to `review/` and `move-log/`, and the read-only git commands the skills' `allowed-tools` list. Grants are matched as patterns: a compound Bash command such as `git diff base; echo $?` is denied.

## Its limit

3 tries is a smoke check. It catches clear breakage, not rare errors. Over time, the move log is the evidence of how often reviews are wrong.
