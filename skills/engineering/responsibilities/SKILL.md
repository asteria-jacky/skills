---
name: responsibilities
description: Give each piece of behaviour one home (Fowler, Martin): find behaviour living away from its data, units with several reasons to change, and concepts written out in several places. Writes a review report with a verdict (`pass`, `advise`, `change`, `ask`).
disable-model-invocation: true
argument-hint: "[base-ref | \"scope\"] [--out <folder>] [--max-moves N] [--move-log <folder>] [--models <stage>=<model>,…]"
allowed-tools: Read Grep Glob Agent Bash(git diff *) Bash(git log *) Bash(git rev-parse *) Bash(git merge-base *) Bash(git show *) Bash(mktemp *)
---

# Responsibilities

Goal: make the code "easier to understand and cheaper to modify" (Fowler): one change, one place.

Use instead:

- `/jacky-skills:depth` if units look too small or only pass calls through.
- `/jacky-skills:restructure` for every angle.

What this review takes, reads and writes: [`CONTRACT.md`](${CLAUDE_PLUGIN_ROOT}/shared/CONTRACT.md).

The plugin root is `${CLAUDE_PLUGIN_ROOT}`. Read `${CLAUDE_PLUGIN_ROOT}/skills/engineering/restructure/SKILL.md` and follow its process with the argument `$ARGUMENTS`, dispatching only this lens: `${CLAUDE_SKILL_DIR}/LENS.md`. Paths in that file written as `${CLAUDE_PLUGIN_ROOT}/…` resolve against the plugin root above.
