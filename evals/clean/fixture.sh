#!/usr/bin/env bash
# Base: add_tax owns the tax rule; Cart uses it.
# Change: a new invoice total that also uses add_tax. Nothing to restructure.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.com
export GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.com
git init -q -b main .
mkdir -p shop

cat > GLOSSARY.md <<'EOF'
# Glossary
- **Tax**: 20% added to a subtotal. One rule for the whole shop.
- **Invoice**: the bill for an order: its lines, then Tax on their subtotal.
EOF

cat > shop/tax.py <<'EOF'
def add_tax(subtotal):
    return round(subtotal * 1.2, 2)
EOF

cat > shop/cart.py <<'EOF'
from shop.tax import add_tax


class Cart:
    def __init__(self):
        self.prices = []

    def total(self):
        return add_tax(sum(self.prices))
EOF

git add -A && git commit -qm base && git tag base

cat > shop/invoice.py <<'EOF'
from shop.tax import add_tax


def invoice_total(lines):
    return add_tax(sum(price * qty for price, qty in lines))
EOF

git add -A && git commit -qm "add invoice total"
