---
type: regex
# not necessary, so never change; a failure fails too
pattern: '^verdict: (pass|advise)$'
flags: m
target: { source: file, path: review/report.md }
---
