---
name: domain-model
description: Bring the code's model in line with the domain's language (Evans, Vernon): find drifting names, implicit concepts, misused building blocks and aggregate boundaries. Writes a review report with a verdict (`pass`, `advise`, `change`, `ask`).
disable-model-invocation: true
argument-hint: "[base-ref | \"scope\"] [--out <folder>] [--max-moves N] [--move-log <folder>] [--models <stage>=<model>,…]"
allowed-tools: Read Grep Glob Agent Bash(git diff *) Bash(git log *) Bash(git rev-parse *) Bash(git merge-base *) Bash(git show *) Bash(mktemp *)
---

# Domain model

Goal: make the code speak the domain's ubiquitous language, because "Translation blunts communication and makes knowledge crunching anemic" (Evans).

Use instead:

- `/jacky-skills:listen-to-tests` if names are fine but tests hurt.
- `/jacky-skills:restructure` for every angle.

What this review takes, reads and writes: [`CONTRACT.md`](${CLAUDE_PLUGIN_ROOT}/shared/CONTRACT.md).

The plugin root is `${CLAUDE_PLUGIN_ROOT}`. Read `${CLAUDE_PLUGIN_ROOT}/skills/engineering/restructure/SKILL.md` and follow its process with the argument `$ARGUMENTS`, dispatching only this lens: `${CLAUDE_SKILL_DIR}/LENS.md`. Paths in that file written as `${CLAUDE_PLUGIN_ROOT}/…` resolve against the plugin root above.
