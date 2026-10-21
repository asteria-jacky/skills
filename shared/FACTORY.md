# Guidance for the Factory

Advice for the Factory, or the person, that runs reviews. No review skill reads this file; what a review itself takes, reads and writes is in [`CONTRACT.md`](CONTRACT.md).

## Running a review

- Start each review from runner code, as its own session, with the slash command as the prompt: `claude -p "/jacky-skills:restructure <args>" --plugin-dir <plugin>`, or the Agent SDK's `query()` with the same prompt and the plugin. A sub-agent started with the Agent tool can't run these skills.
- Pass `--out`, then read `verdict` or `failure` from `<out>/report.md`. Under `claude -p`, the session ends at the review's question, with the report on disk.

## Permissions

Each review skill's `allowed-tools` pre-approves only reading: `Read`, `Grep`, `Glob`, `Agent`, read-only git, and `mktemp`. The grant reaches the sub-agents the review starts in that turn. Writing the report folder and the move log, editing code and running tests still ask, so applying a move always asks. Grant the writes yourself, e.g. `--allowedTools "Edit(//<out>/**)" "Edit(//<move log>/**)"`: a path rule for writing files must name `Edit`, because Claude Code never consults a path rule on `Write`.

## Models and cost

The default model per stage is in [`CONTRACT.md`](CONTRACT.md#models); `--models` overrides it. Model choice changes the price per token, not the token count.

## The review loop

- Review every round against the same base, where the feature started.
- On `change`, turn each necessary move into one ticket. Use `after` for blocking and Done when for acceptance.
- Pass the same `--move-log` folder every round. Decide whether to commit it with the code.
- After each round, append `applied` or `declined` to the move log file of each necessary move, with notes for next time.
- After 2 rounds that still say `change`, stop and ask a person, who reads the move log.
