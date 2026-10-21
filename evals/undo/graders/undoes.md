---
type: regex
# ask names an undo, and the Undoes section names the applied key
pattern: '^ask: \[[^\]]*U\d[^\]]*\]$(?:.*\n)*^## Undoes\n(?:.*\n)*?- U\d+ · key: Tax Policy · extract · shop/tax\.py#TaxPolicy · '
flags: m
target: { source: file, path: review/report.md }
---
