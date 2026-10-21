---
type: regex
# the Declined before section lists the logged key
pattern: '^## Declined before\n(?:.*\n)*?- .* · key: Tax · combine · shop/tax\.py#add_tax · declined: '
flags: m
target: { source: file, path: review/report.md }
---
