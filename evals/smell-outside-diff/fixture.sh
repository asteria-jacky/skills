#!/usr/bin/env bash
# Base: the tax rule is already written out in tax.py, invoice.py and refund.py.
# Change: a tidy new Cart.count method. The smell sits only in untouched code.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.com
export GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.com
git init -q -b main .
mkdir -p shop

cat > GLOSSARY.md <<'EOF'
# Glossary
- **Tax**: 20% added to a subtotal. One rule for the whole shop.
EOF

cat > shop/tax.py <<'EOF'
def add_tax(subtotal):
    return round(subtotal * 1.2, 2)
EOF

cat > shop/invoice.py <<'EOF'
def invoice_total(lines):
    subtotal = sum(price * qty for price, qty in lines)
    return round(subtotal * 1.2, 2)
EOF

cat > shop/refund.py <<'EOF'
def refund_amount(paid_subtotal):
    return round(paid_subtotal * 1.2, 2)
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

cat >> shop/cart.py <<'EOF'

    def count(self):
        return len(self.prices)
EOF

git add -A && git commit -qm "cart: count items"
