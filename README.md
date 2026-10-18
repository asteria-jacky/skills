# Claude Code skills

## Install

```
/plugin marketplace add asteria-jacky/skills
/plugin install jacky-skills@asteria-jacky
```

## Skills

- **`/jacky-skills:restructure [base-ref | scope]`**: restructure freshly implemented code toward the domain's ubiquitous language and deep modules. Takes a base ref to review what changed since then, or a scope (e.g. "Log module", "Editor", "ShippingService") to review that area's current code regardless of recent changes. Runs every lens in parallel sub-agents, merges their findings into design moves, reports first, then applies the moves you pick, one at a time.

Each lens also runs on its own, with the same arguments and the same report-then-apply process:

- **`/jacky-skills:listen-to-tests`**: reads test pain as design feedback (Freeman & Pryce, *Growing Object-Oriented Software, Guided by Tests*) and traces it to the missing role, value or responsibility.
- **`/jacky-skills:responsibilities`**: gives each piece of behaviour one home (Fowler, *Refactoring*; Martin): behaviour away from its data, units with several reasons to change, concepts written out in several places.
- **`/jacky-skills:domain-model`**: brings the model in line with the domain's language (Evans, *Domain-Driven Design*; Vernon, *Implementing Domain-Driven Design*): drifting names, implicit concepts, building blocks, aggregates.
- **`/jacky-skills:depth`**: makes modules deep (Ousterhout, *A Philosophy of Software Design*): shallow classes, information leakage, pass-through methods, temporal decomposition.

Lens decisions are recorded in [`docs/adr/`](docs/adr/); the shared report format is [`shared/FINDINGS.md`](shared/FINDINGS.md).
