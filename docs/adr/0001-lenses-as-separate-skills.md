# Lenses are separate skills; `restructure` merges them into design moves

`restructure` used to review code through one combined lens file. The books behind it disagree with each other (Martin vs Ousterhout on decomposition, mockist vs classicist TDD), and each lens needs depth a shared checklist can't hold. So each lens is now its own skill: `skills/engineering/<lens>/SKILL.md`, with the lens itself in a plain `skills/engineering/<lens>/LENS.md`. `restructure` dispatches one sub-agent per lens in parallel. Each sub-agent reads its `LENS.md` by absolute path (`${CLAUDE_PLUGIN_ROOT}/skills/engineering/<lens>/LENS.md`) and reports in the shared format in `shared/FINDINGS.md`. `restructure` then merges the findings into **design moves**, keyed by concept, and surfaces conflicts between lenses rather than resolving them silently. A lens skill run on its own follows `restructure`'s process with only that lens.

## Considered options

- **Lens skills invoked through the Skill tool.** Rejected. Every skill here is `disable-model-invocation: true`, so none costs always-loaded context, and that flag blocks Skill-tool calls and sub-agent preloading. Reading `LENS.md` as a plain file works whatever the flags say.
- **`context: fork` lens skills.** Rejected. A fork has no conversation history, runs in the background by default, and can't hold the report → pick → apply loop with the user.
- **Ranking by convergence alone.** Rejected. Lenses run by the same model are correlated, so agreement is weak evidence. Per-finding strength ranks first; convergence breaks ties.

Research behind this decision: `.scratch/restructure-lenses/research.md`.
