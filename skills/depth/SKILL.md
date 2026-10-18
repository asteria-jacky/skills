---
name: depth
description: Make modules deep (Ousterhout): find shallow classes, information leakage, pass-through methods and temporal decomposition. Reports findings first, then applies the ones you pick, one at a time.
disable-model-invocation: true
argument-hint: "[base-ref | scope]"
---

# Depth

A deep module hides a lot behind a simple interface. This lens reads interfaces before bodies, asks Ousterhout's review questions, and works through his red flags to pull complexity down and give each design decision one owner. This skill runs one lens, [LENS.md](LENS.md).

The plugin root is `${CLAUDE_PLUGIN_ROOT}`. Read `${CLAUDE_PLUGIN_ROOT}/skills/restructure/SKILL.md` and follow its process with the argument `$ARGUMENTS`, dispatching only this lens: `${CLAUDE_SKILL_DIR}/LENS.md`. Paths in that file written as `${CLAUDE_PLUGIN_ROOT}/…` resolve against the plugin root above.
