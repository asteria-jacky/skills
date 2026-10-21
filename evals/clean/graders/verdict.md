---
type: regex
# a verdict, and never change (a failure has no verdict line, so it fails too)
pattern: '^verdict: (pass|advise|ask)$'
flags: m
target: { source: file, path: review/report.md }
---
