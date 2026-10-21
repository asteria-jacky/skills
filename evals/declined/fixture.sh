#!/usr/bin/env bash
# The smell-in-diff repo, plus a move log in base that declines the move that
# fixes it, with the same evidence. The move must not be necessary and must be
# listed under Declined before.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.com
export GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.com
git init -q -b main .
mkdir -p shop move-log

cat > GLOSSARY.md <<'EOF'
# Glossary
- **Tax**: 20% added to a subtotal. One rule for the whole shop.
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

cat > move-log/tax-combine-shop-tax-py-add-tax.md <<'EOF'
# Tax · combine · shop/tax.py#add_tax

## proposed · head 1a2b3c4 · base 0f0f0f0
group: necessary
check: keep
report: /tmp/restructure-old
findings:
- depth · Information leakage · shop/invoice.py#invoice_total, shop/refund.py#refund_amount · Strong
effects:
- places-to-change 3 → 1 (tax rate 1.2 in shop/tax.py:2, shop/invoice.py:3, shop/refund.py:2)

## declined · by Factory
reason: Invoice and refund move to the billing service next sprint, which owns tax there.
notes: Raise it again if invoice.py or refund.py stay in this repo.
EOF

git add -A && git commit -qm base && git tag base

cat > shop/invoice.py <<'EOF'
def invoice_total(lines):
    subtotal = sum(price * qty for price, qty in lines)
    return round(subtotal * 1.2, 2)
EOF

cat > shop/refund.py <<'EOF'
def refund_amount(paid_subtotal):
    return round(paid_subtotal * 1.2, 2)
EOF

git add -A && git commit -qm "add invoice and refund totals"
