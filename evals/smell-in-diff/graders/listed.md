---
type: regex
# the Moves section lists a necessary move
pattern: '^- \[\d+\. [^\]]*\]\(moves\.md#[^)]*\) · necessary · '
flags: m
target: { source: file, path: review/report.md }
---
