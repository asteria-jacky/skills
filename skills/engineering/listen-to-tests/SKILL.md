---
name: listen-to-tests
description: Read test pain as design feedback (Freeman & Pryce) and trace it to the missing role, value or responsibility in the code. Writes a review report with a verdict (`pass`, `advise`, `change`, `ask`).
disable-model-invocation: true
argument-hint: "[base-ref | \"scope\"] [--out <folder>] [--max-moves N] [--move-log <folder>] [--models <stage>=<model>,…]"
allowed-tools: Read Grep Glob Agent Bash(git diff *) Bash(git log *) Bash(git rev-parse *) Bash(git merge-base *) Bash(git show *) Bash(mktemp *)
---

# Listen to the tests

Goal: let mock objects guide "the discovery of a coherent system of types" (Freeman & Pryce).

Use instead:

- `/jacky-skills:depth` or `/jacky-skills:responsibilities` if there are no tests to read.
- `/jacky-skills:restructure` for every angle.

What this review takes, reads and writes: [`CONTRACT.md`](${CLAUDE_PLUGIN_ROOT}/shared/CONTRACT.md).

The plugin root is `${CLAUDE_PLUGIN_ROOT}`. Read `${CLAUDE_PLUGIN_ROOT}/skills/engineering/restructure/SKILL.md` and follow its process with the argument `$ARGUMENTS`, dispatching only this lens: `${CLAUDE_SKILL_DIR}/LENS.md`. Paths in that file written as `${CLAUDE_PLUGIN_ROOT}/…` resolve against the plugin root above.
