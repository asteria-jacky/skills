# Claude Code skills

## Install

```
/plugin marketplace add asteria-jacky/skills
/plugin install skills@asteria-jacky
```

## Skills

- **`/skills:restructure [base-ref | scope]`**: restructure freshly implemented code toward the domain's ubiquitous language and deep modules. Takes a base ref to review what changed since then, or a scope (e.g. "Log module", "Editor", "ShippingService") to review that area's current code regardless of recent changes. Reports findings first, then applies the ones you pick, one at a time.
