---
runs: 3
max_turns: 120
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Agent]
---

/jacky-skills:depth base --out review --move-log move-log
