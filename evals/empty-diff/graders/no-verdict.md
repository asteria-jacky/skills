---
type: regex
pattern: '^verdict:'
flags: m
match: not_contains
target: { source: file, path: review/report.md }
---
