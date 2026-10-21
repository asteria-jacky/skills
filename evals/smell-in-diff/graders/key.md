---
type: regex
# a necessary move's machine line whose key's concept names tax
pattern: '^necessary: yes · .*key: [^·\n]*tax[^·\n]* · '
flags: mi
target: { source: file, path: review/moves.md }
---
