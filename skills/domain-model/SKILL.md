---
name: domain-model
description: Bring the code's model in line with the domain's language (Evans, Vernon): find drifting names, implicit concepts, misused building blocks and aggregate boundaries. Reports findings first, then applies the ones you pick, one at a time.
disable-model-invocation: true
argument-hint: "[base-ref | scope]"
---

# Domain model

The code should speak the domain's language and model its concepts. This lens compares the code with `GLOSSARY.md` and the domain's own words, finds concepts the code is missing or confusing, checks entities, values, services and aggregates behave like what they are, and looks for the breakthrough a deeper model would bring. This skill runs one lens, [LENS.md](LENS.md).

The plugin root is `${CLAUDE_PLUGIN_ROOT}`. Read `${CLAUDE_PLUGIN_ROOT}/skills/restructure/SKILL.md` and follow its process with the argument `$ARGUMENTS`, dispatching only this lens: `${CLAUDE_SKILL_DIR}/LENS.md`. Paths in that file written as `${CLAUDE_PLUGIN_ROOT}/…` resolve against the plugin root above.
