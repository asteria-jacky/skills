#!/usr/bin/env bash
# Change: Checkout keeps Marketing's member discount in a one-line method,
# member_price, with one caller, and writes Finance's tax rate out again.
# Depth wants member_price inlined into Checkout.total: its interface is as
# large as its body. Responsibilities wants the member discount extracted out
# of Checkout: it changes for Marketing, apart from Tax. A one-line rule can't
# be both its own unit and part of total, so no single move settles it. The
# necessary tax move also touches Checkout.total.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.com
export GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.com
git init -q -b main .
mkdir -p shop

cat > GLOSSARY.md <<'EOF'
# Glossary
- **Tax**: 20% added to a subtotal. Finance owns it. One rule for the whole shop.
- **Member discount**: members pay 10% less, before Tax. Marketing owns it and changes it each season, apart from Tax.
- **Checkout**: turns a basket's lines into the amount to pay.
EOF

cat > shop/tax.py <<'EOF'
def add_tax(subtotal):
    return round(subtotal * 1.2, 2)
EOF

git add -A && git commit -qm base && git tag base

cat > shop/checkout.py <<'EOF'
class Checkout:
    def __init__(self, lines, member):
        self.lines = lines
        self.member = member

    def total(self):
        subtotal = sum(price * qty for price, qty in self.lines)
        return round(self.member_price(subtotal, self.member) * 1.2, 2)

    def member_price(self, amount, member):
        return amount * 0.9 if member else amount
EOF

cat > shop/pay.py <<'EOF'
from shop.checkout import Checkout


def amount_to_pay(lines, member):
    return Checkout(lines, member).total()
EOF

git add -A && git commit -qm "add checkout"
