# Claude Code skills

## Install

```
/plugin marketplace add asteria-jacky/skills
/plugin install jacky-skills@asteria-jacky
```

## Skills

- **`/jacky-skills:restructure [base-ref | scope]`**: restructure freshly implemented code toward the domain's ubiquitous language and deep modules. Takes a base ref to review what changed since then, or a scope (e.g. "Log module", "Editor", "ShippingService") to review that area's current code regardless of recent changes. Runs every lens in parallel sub-agents, merges their findings into design moves, reports first, then applies the moves you pick, one at a time.
- **`/jacky-skills:listen-to-tests [base-ref | scope]`**: the same process with one lens: reads test pain as design feedback (Freeman & Pryce, *Growing Object-Oriented Software, Guided by Tests*) and traces it to the missing role, value or responsibility.

Lens decisions are recorded in [`docs/adr/`](docs/adr/); the shared report format is [`shared/FINDINGS.md`](shared/FINDINGS.md).
