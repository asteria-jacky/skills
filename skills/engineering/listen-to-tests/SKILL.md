---
name: listen-to-tests
description: Read test pain as design feedback (Freeman & Pryce) and restructure the code it points at. Reports findings first, then applies the ones you pick, one at a time.
disable-model-invocation: true
argument-hint: "[base-ref | scope]"
---

# Listen to the tests

Hard-to-write tests are telling you about the design. This skill runs one lens, [LENS.md](LENS.md): it reads the tests for pain (bloated constructors, confused objects, mocks of concrete classes, too many expectations) and traces each pain to the missing role, value or responsibility in the production code.

The plugin root is `${CLAUDE_PLUGIN_ROOT}`. Read `${CLAUDE_PLUGIN_ROOT}/skills/engineering/restructure/SKILL.md` and follow its process with the argument `$ARGUMENTS`, dispatching only this lens: `${CLAUDE_SKILL_DIR}/LENS.md`. Paths in that file written as `${CLAUDE_PLUGIN_ROOT}/…` resolve against the plugin root above.
