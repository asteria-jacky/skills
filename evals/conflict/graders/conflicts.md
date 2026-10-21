---
type: regex
# ask names a conflict, and the Conflicts section exists
pattern: '^ask: \[[^\]]*C\d[^\]]*\]$(?:.*\n)*^## Conflicts$'
flags: m
target: { source: file, path: review/report.md }
---
