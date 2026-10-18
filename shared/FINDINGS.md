# Findings

The shared contract between the lenses and `restructure`. A lens sub-agent reads **Report format** and returns its report in exactly that shape. `restructure` reads **Merging into design moves** when it combines the reports.

## Report format

Return one fenced `findings` block, then one fenced `hints` block, and nothing else. Under 1,500 words in total.

Each finding is a run of `key: value` lines; separate findings with a line holding only `---`. Keep each value on one line, except `cast` and `after`, which take one `- ` item per line beneath the key.

You have read the code; whoever reads your report has not. Write every finding so the user can follow it **without opening a file**: each object named with its `path:line`, each smell and refactoring explained in a clause the first time it appears.

````
```findings
lens: listen-to-tests
concept: Line Item
where: src/billing/invoice.ts#Invoice.addLine, test/billing/invoice.test.ts
today: Invoice.addLine takes a line as five loose values, and works out the line's tax by handing two of them to TaxCalculator
cast:
- Invoice.addLine (src/billing/invoice.ts:42): adds a line to the invoice; takes price, quantity, taxCode, currency, sku
- TaxCalculator.lineTax (src/billing/tax.ts:17): called by addLine; reads only price and taxCode
- CheckoutService.finalize (src/checkout/service.ts:88): the one production caller; unpacks a cart row into the five values
- makeInvoice (test/billing/invoice.test.ts:8): test helper; rebuilds the five values for every test
smell: possible Bloated Constructor (GOOS ch. 20: a long parameter list the tests must fill every time, a sign the values form an object nobody named)
evidence: 9 of 12 tests in invoice.test.ts (lines 20-140) repeat the same price, quantity, taxCode, currency, sku
technique: Introduce Parameter Object (bundle values that travel together), then Replace Primitive with Object (give the bundle behaviour) (Fowler)
restructure: introduce a Line Item value object; Invoice.addLine takes it, and the line computes its own tax
after:
- LineItem (new value, src/billing/line-item.ts): holds the five values; tax() replaces TaxCalculator.lineTax
- Invoice.addLine(item: LineItem)
- CheckoutService.finalize builds a LineItem from the cart row
direction: introduce
tests: 12 tests in invoice.test.ts change their setup; they test behaviour, so their assertions stand
strength: Strong
---
lens: listen-to-tests
...
```

```hints
- module scale: billing and shipping both parse tax codes; boundary question for /modularity:review
```
````

- **lens**: the lens's skill name.
- **concept**: the domain concept the finding is about. Use the `GLOSSARY.md` term when one exists. Otherwise name the concept in the domain's words, or fall back to the code symbol as `path#Symbol`. This is the key `restructure` merges on, so name the concept, not the smell.
- **where**: files and symbols, comma-separated, as `path#Symbol`.
- **today**: what the code does now, in plain words, one sentence.
- **cast**: every object or function the finding involves, one per line, as `Symbol (path:line): what it does today`. Include the **neighbours**: the callers and collaborators a reader needs to see why it hurts and what the change will touch.
- **smell**: what's wrong, in domain terms, as a labelled heuristic: "possible Feature Envy", never a verdict. Name the source.
- **evidence**: the concrete signal you saw: a test name, a count, a line. A finding with no evidence is speculation; mark it so.
- **technique**: the named refactoring and its book. Use the names in Fowler's catalog (refactoring.com/catalog); a class rename has no catalog name, so write "rename class".
- **restructure**: what changes, in one sentence.
- **after**: the resulting shape, one line per object that is new or changes: its new home, signature, or responsibility.
- **direction**: one of `extract`, `combine`, `move`, `rename`, `introduce`, `inline`, `hide`, `expose`, `remove`. `restructure` detects conflicts from opposite directions on the same symbol.
- **tests**: which tests the change will likely break, and whether each tests behaviour or is pinned to internals. Write `untested` when no test exercises the code.
- **strength**: `Strong` (clear evidence, clear payoff), `Worth exploring` (real signal, uncertain remedy), or `Speculative` (a hunch worth a look).

**Hints** are smells this lens can't act on at class or function scale: module- or service-scale coupling, cohesion and boundaries, and mechanical duplication with no domain concept behind it. One line each, naming the area.

## Merging into design moves

A **design move** is one coherent restructure: the findings from every lens that point at the same concept, turned into one change. Build the moves in this order:

1. **Key.** Group findings with the same `concept`. Then make a semantic pass: two keys that name one concept (`client` and `customer`, or a glossary term and the symbol that implements it) join one group. Two names for one concept is itself a domain-model signal; add it to the move.
2. **Compose.** Turn each group into one move: a sentence saying what changes and why, the findings it absorbs (by lens), and the order of its steps as named refactorings, small and behaviour-preserving.
3. **Conflict.** Opposite directions on the same symbol make a **conflict**, not a move: `extract` vs `combine` or `inline`, `hide` vs `remove`, `introduce` vs `remove`. Present both sides with each lens's reasoning, then recommend one using the shared test both Martin and Ousterhout accept: does the extracted piece have an interface simpler than its body, and does extracting it avoid entanglement? The user decides.
4. **Rank.** Order moves by their strongest finding's `strength`, then by **convergence**: the number of distinct lenses in the move. Convergence breaks ties only. The lenses run on one model, so their agreement is weak evidence on its own. A move several lenses reached independently is still the best candidate for a **breakthrough**: one restructure that dissolves several smells at once (Evans, *DDD* ch. 8). Name it as one when it is.
5. **Hints.** Collect every lens's hints, merge duplicates, and keep them apart from the moves.

Done when every finding sits in exactly one move or one conflict.

Carry each finding's `today`, `cast` and `after` into its move whole: merging joins them, never shortens them. When a move absorbs several findings, combine their casts into one list.

Report each move as:

```
### 1. Introduce Line Item value object · Strong · 3 lenses

**Today.** Invoice.addLine (src/billing/invoice.ts:42) takes each line as five loose values, and every caller and test has to supply all five.

**Who's involved.**
- `Invoice.addLine` (src/billing/invoice.ts:42): adds a line; takes price, quantity, taxCode, currency, sku
- `TaxCalculator.lineTax` (src/billing/tax.ts:17): called by addLine; reads only price and taxCode
- `CheckoutService.finalize` (src/checkout/service.ts:88): the one production caller
- `makeInvoice` (test/billing/invoice.test.ts:8): test helper that rebuilds the five values

**Signals.**
- listen-to-tests: Bloated Constructor, a long parameter list the tests must fill every time. 9 of 12 tests repeat the same five values (invoice.test.ts:20-140).
- responsibilities: Data Clumps, the same values always travelling together.
- domain-model: "Line Item" is in GLOSSARY.md but has no class.

**After.**
- `LineItem` (new value, src/billing/line-item.ts): holds the five values; `tax()` replaces `TaxCalculator.lineTax`
- `Invoice.addLine(item: LineItem)`
- `CheckoutService.finalize` builds a `LineItem` from the cart row

**Steps.**
1. Introduce Parameter Object: `addLine` takes a `LineItem` holding the five values.
2. Replace Primitive with Object: `LineItem` gains `tax()`.
3. Move Function: `TaxCalculator.lineTax` moves into `LineItem.tax()`; `TaxCalculator` is deleted if nothing else uses it.

**Tests.** The 12 tests in invoice.test.ts change their setup to build a `LineItem`; they test behaviour, so their assertions stand.
```

Each step names what moves from where to where. The move is done when a reader who hasn't opened the code can say which objects change and how.
