---
name: responsibilities
description: Give each piece of behaviour one home (Fowler, Martin): find behaviour living away from its data, units with several reasons to change, and concepts written out in several places. Reports findings first, then applies the ones you pick, one at a time.
disable-model-invocation: true
argument-hint: "[base-ref | scope]"
---

# Responsibilities

Each piece of behaviour belongs with the data it works on and changes for one reason. This lens reads the code for Fowler's smells (Feature Envy, Divergent Change, Data Clumps, Shotgun Surgery) and moves behaviour to its home, with a stop condition against over-decomposition. This skill runs one lens, [LENS.md](LENS.md).

The plugin root is `${CLAUDE_PLUGIN_ROOT}`. Read `${CLAUDE_PLUGIN_ROOT}/skills/engineering/restructure/SKILL.md` and follow its process with the argument `$ARGUMENTS`, dispatching only this lens: `${CLAUDE_SKILL_DIR}/LENS.md`. Paths in that file written as `${CLAUDE_PLUGIN_ROOT}/…` resolve against the plugin root above.
