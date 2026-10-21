## Agent skills

### Issue tracker

Issues and specs are tracked as local markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Branches

Agents commit only on branches under `agents/`: `agents/<topic>` for a piece of work, `agents/<topic>-<ticket>` for a sub-agent's ticket (a `/` after `<topic>` would clash with the `agents/<topic>` ref). Every other branch, `main` included, belongs to a person: agent work stays on its `agents/` branch, and the person squash-merges it into their own branch when they choose. Once an `agents/` branch is squashed, start the next piece of work on a fresh `agents/<topic>` branch from the person's branch; the squashed branch's history no longer matches theirs.

### Domain docs

Single-context layout: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
