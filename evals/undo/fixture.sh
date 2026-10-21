#!/usr/bin/env bash
# Base: TaxPolicy was extracted (move log says applied); both callers use it.
# Change: invoice.py drops TaxPolicy and calls add_tax directly, leaving
# TaxPolicy a pass-through with one caller. The change works against the
# applied move on TaxPolicy, so the review must ask, whatever moves it proposes.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.com
export GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.com
git init -q -b main .
mkdir -p shop move-log

cat > GLOSSARY.md <<'EOF'
# Glossary
- **Tax**: 20% added to a subtotal. One rule for the whole shop.
- **Tax Policy**: the object that applies Tax to an amount.
EOF

cat > shop/tax.py <<'EOF'
def add_tax(subtotal):
    return round(subtotal * 1.2, 2)


class TaxPolicy:
    def apply(self, amount):
        return add_tax(amount)
EOF

cat > shop/cart.py <<'EOF'
from shop.tax import TaxPolicy


class Cart:
    def __init__(self):
        self.prices = []

    def total(self):
        return TaxPolicy().apply(sum(self.prices))
EOF

cat > shop/invoice.py <<'EOF'
from shop.tax import TaxPolicy


def invoice_total(lines):
    return TaxPolicy().apply(sum(price * qty for price, qty in lines))
EOF

cat > move-log/tax-policy-extract-shop-tax-py-taxpolicy.md <<'EOF'
# Tax Policy · extract · shop/tax.py#TaxPolicy

## proposed · head 1a2b3c4 · base 0f0f0f0
group: necessary
check: keep
report: /tmp/restructure-old
findings:
- responsibilities · Duplicated Code · shop/cart.py#Cart.total · Strong
effects:
- places-to-change 2 → 1 (tax rule in cart.py, invoice.py)

## applied · by restructure
done-when: met
hard: -
notes: Callers go through TaxPolicy so the tax rule has one home.
EOF

git add -A && git commit -qm base && git tag base

cat > shop/invoice.py <<'EOF'
from shop.tax import add_tax


def invoice_total(lines):
    return add_tax(sum(price * qty for price, qty in lines))
EOF

git add -A && git commit -qm "invoice: call add_tax directly"
