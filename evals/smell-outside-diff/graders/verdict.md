---
type: regex
# advise at most
pattern: '^verdict: (pass|advise)$'
flags: m
target: { source: file, path: review/report.md }
---
