#!/usr/bin/env bash
# Base and HEAD are the same commit: nothing changed.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.com
export GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.com
git init -q -b main .
mkdir -p shop

cat > shop/tax.py <<'EOF'
def add_tax(subtotal):
    return round(subtotal * 1.2, 2)
EOF

git add -A && git commit -qm base && git tag base
