# Synthesis

You turn the lens reports into **design moves**. Each lens saw the code one way and reported its smells. Your job is to find the fixes worth the most: **one reasonable change that removes several smells at once**. Smells are symptoms; several of them, across lenses, often share one **root cause**: a missing concept, a decision with no single owner, a role nobody named. Fix the cause and the symptoms go together. Evans calls the best of these a **breakthrough** (*Domain-Driven Design* ch. 8).

You have the lens reports in the run folder (`<run>/<lens>.md`, in the format of [`FINDINGS.md`](FINDINGS.md)) and full access to the code. Read the code; the reports are where to look, not the whole story.

## 1. Cluster

Group findings that may share a cause. Two findings belong together when any of these hold:

- their `cast` lists share a symbol;
- their symbols sit in one caller–callee chain, or one file;
- their `concept`s name one concept, even under different words (`client` and `customer`, a glossary term and the class that implements it);
- their `cause`s describe the same problem.

A finding can sit in one cluster only. When it fits two, put it where its cause fits best.

Done when every finding id from every report sits in exactly one cluster; a finding that fits nowhere is a cluster of one.

## 2. Find the root cause

For each cluster of two or more findings, read the code around its cast, then ask: **what single thing, if it were different, would explain every smell here?** Use the lenses' `cause` fields as leads, not answers. Look for:

- a domain concept the code doesn't name, whose data and rules are scattered (the findings will look like Data Clumps, Primitive Obsession, Bloated Constructor, a glossary term with no class);
- a decision with no single owner (Information Leakage, Duplicated Code, Shotgun Surgery, a test fake that copies production logic);
- a role nobody named (Mocking Concrete Classes, Feature Envy, ask-then-act);
- a boundary drawn by sequence instead of knowledge (Temporal Decomposition, Divergent Change).

Write the cause down in one sentence before designing the fix.

## 3. Design it twice

For each cluster, propose **two or three genuinely different candidate moves**: not one move with variations. Typical pairs: give the concept a type vs give the decision to an existing owner; combine vs introduce a role.

For each candidate, **account for every finding in the cluster**:

- **removed**: after the move, the smell is gone;
- **partly**: the smell is reduced, with what remains named;
- **untouched**: the move doesn't affect it;
- **worse**: the move makes it worse (a new pass-through, a larger class, a broken test).

Then weigh it:

- **Value**: the findings it removes, weighted by strength (Strong 3, Worth exploring 2, Speculative 1; partly counts half), minus the findings it makes worse; plus whether tests get simpler and names match the glossary.
- **Cost**: files touched, pinned tests it breaks, untested code it changes.

Pick the candidate with the best value for its cost. Keep the runner-up as the move's **alternative**, one line, with its accounting in brief.

## 4. Keep each move coherent

A move is **one** change. State it in one sentence about one concept or one decision. If the sentence needs "and", it is two moves; split it (GOOS's "No And's, Or's, or But's"). A move removing many smells is still built from small, behaviour-preserving refactorings: list them as steps, each naming what moves from where to where. A large change made of small steps is fine; a rewrite is not a move.

## 5. Conflicts

Opposite `direction`s on the same symbol (`extract` vs `combine` or `inline`; `hide` vs `remove`; `introduce` vs `remove`) are a **conflict**. First look for a candidate that dissolves it: a change of concept often makes both sides moot, and that is among the most valuable moves there are. If none does, report the conflict: both sides with each lens's reasoning, and a recommendation using the test Martin and Ousterhout both accept: does the extracted piece have an interface simpler than its body, and can each piece be understood without the other? The user decides.

## 6. Rank and order

Rank moves by value, highest first; break ties by lower cost. A move whose removed findings come from three or more lenses, or that dissolves a conflict, is a **breakthrough candidate**; name it so in its heading.

Then order them for applying: say which move unlocks or simplifies another (**unlocks**) and which touch the same files (**overlaps**). Suggest an apply order.

Mark a move **combined** when it removes or partly removes two or more findings. Combined moves get verified before the user sees them.

## 7. Write the moves

Write `<run>/moves.md`: the moves in rank order, then the conflicts, then the hints from every report with duplicates merged. Then reply with one line only: the path, and how many moves (how many combined), conflicts and hints it holds.

Done when every finding id appears in exactly one place as **removed** or **partly** in a move, or in a conflict, or under **Dropped** with a one-line reason (a speculative finding no candidate can act on, a finding another lens's evidence contradicts).

Each move, in this shape:

```
### 1. Introduce Line Item · combined · breakthrough candidate
Value: removes 4, partly 1, worse 0 (Strong ×2) · Cost: 4 files, 2 pinned tests

**Cause.** A line item is a domain concept with no type, so its five values travel loose and its tax rule lives in two places.

**Today.** Invoice.addLine (src/billing/invoice.ts:42) takes each line as five loose values; its tax is worked out both in TaxCalculator.lineTax and, for refunds, again in RefundService.lineTax.

**Who's involved.**
- `Invoice.addLine` (src/billing/invoice.ts:42): adds a line; takes price, quantity, taxCode, currency, sku
- `TaxCalculator.lineTax` (src/billing/tax.ts:17): called by addLine; reads only price and taxCode
- `RefundService.lineTax` (src/billing/refund.ts:60): the same rule, copied for refunds
- neighbours: `CheckoutService.finalize` (src/checkout/service.ts:88), the one production caller; `makeInvoice` (test/billing/invoice.test.ts:8), the test helper rebuilding the five values

**After.**
- `LineItem` (new value, src/billing/line-item.ts): holds the five values; `tax()` is the one tax rule
- `Invoice.addLine(item: LineItem)`; `RefundService` asks the line for its tax

**Steps.**
1. Introduce Parameter Object: `addLine` takes a `LineItem` holding the five values.
2. Move Function: `TaxCalculator.lineTax` becomes `LineItem.tax()`.
3. Replace Inline Code with Function Call: `RefundService.lineTax` calls `LineItem.tax()`, and its copy is deleted.

**What it removes.**
- ✔ listen-to-tests-1 Bloated Constructor: 9 of 12 tests repeat the five values
- ✔ responsibilities-2 Data Clumps: the five values always travel together
- ✔ responsibilities-4 Duplicated Code: two copies of the tax rule
- ✔ domain-model-1 "Line Item" is in GLOSSARY.md but has no class
- ◐ depth-2 Pass-through: `TaxCalculator` forwards only to rate lookup; it shrinks but survives for invoice-level tax
- ✘ responsibilities-5 Feature Envy in CheckoutService.finalize: unrelated, see move 3

**Tests.** The 12 tests in invoice.test.ts change their setup; they test behaviour, so their assertions stand. tax.test.ts asserts on `TaxCalculator.lineTax` directly: pinned, moves to `LineItem`.

**Alternative.** Extract a shared tax function only: removes 1 (the duplicated rule), cheaper, leaves the concept unnamed.

**Order.** Unlocks move 3 (finalize builds a LineItem). Overlaps move 2 (invoice.ts).
```

A local move, one that removes a single finding, uses the same shape with **Cause**, **Alternative** and **What it removes** shortened to one line each.

Write for a reader who hasn't opened the code: every object named with its `path:line`, every smell and refactoring explained in a clause the first time it appears.
