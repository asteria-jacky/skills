# Claude Code skills

## Install

```
/plugin marketplace add asteria-jacky/skills
/plugin install jacky-skills@asteria-jacky
```

## Skills

- **`/jacky-skills:restructure [base-ref | "scope"] [--out <folder>] [--max-moves N] [--move-log <folder>] [--models <stage>=<model>,…]`**: reviews code toward the domain's ubiquitous language and deep modules. Takes a base ref to review what changed since then, or a scope (e.g. "Log module", "Editor", "ShippingService") to review that area's current code. Runs every lens in parallel sub-agents (Sonnet by default), synthesises their findings into design moves that fix several smells at once, and verifies every move that could be necessary. Writes a review report with a verdict (`pass`, `advise`, `change`, `ask`) to `--out` or a temp folder, and prints its path last. In a live session it then asks which moves to apply, and applies them one at a time; under `claude -p` it ends with the report. It only pre-approves reading, so writing the report and applying a move ask for permission.

Each lens also runs on its own, with the same arguments, the same report and the same verdict:

- **`/jacky-skills:listen-to-tests`**: reads test pain as design feedback (Freeman & Pryce, *Growing Object-Oriented Software, Guided by Tests*) and traces it to the missing role, value or responsibility.
- **`/jacky-skills:responsibilities`**: gives each piece of behaviour one home (Fowler, *Refactoring*; Martin): behaviour away from its data, units with several reasons to change, concepts written out in several places.
- **`/jacky-skills:domain-model`**: brings the model in line with the domain's language (Evans, *Domain-Driven Design*; Vernon, *Implementing Domain-Driven Design*): drifting names, implicit concepts, building blocks, aggregates.
- **`/jacky-skills:depth`**: makes modules deep (Ousterhout, *A Philosophy of Software Design*): shallow classes, information leakage, pass-through methods, temporal decomposition.

- **`/jacky-skills:map [base-ref | scope] [--level high|low]`**: maps the object relationships in a change, a module or a named scope, as a Mermaid diagram at module level (high) or type level (low), with three indicators: cycles, fan-in/fan-out and blast radius. Works for any language: modules come from build manifests, types from regex pattern packs (Swift and TypeScript/JavaScript have their own, others a generic one). A script does the counting; the model names components in the domain's language and verifies the edges behind each cycle before reporting it. Needs only Python 3.

Lens decisions are recorded in [`docs/adr/`](docs/adr/); the arguments, review report, verdict, move log and models every review skill shares are [`shared/CONTRACT.md`](shared/CONTRACT.md); how a Factory runs reviews, grants their writes and ends its loop is [`shared/FACTORY.md`](shared/FACTORY.md); the shared report format is [`shared/FINDINGS.md`](shared/FINDINGS.md), synthesis and verification are [`shared/SYNTHESIS.md`](shared/SYNTHESIS.md) and [`shared/VERIFY.md`](shared/VERIFY.md).
