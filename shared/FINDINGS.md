# Findings

The report format every lens follows. `restructure` turns the reports into design moves with [`SYNTHESIS.md`](SYNTHESIS.md).

## Report format

Write the report to the file path your prompt gives: one fenced `findings` block, then one fenced `hints` block, and nothing else. Under 1,500 words in total. Then reply with one line only: the path, and how many findings and hints it holds.

Each finding is a run of `key: value` lines; separate findings with a line holding only `---`. Keep each value on one line, except `cast` and `after`, which take one `- ` item per line beneath the key.

You have read the code; whoever reads your report has not. Write every finding so the user can follow it **without opening a file**: each object named with its `path:line`, each smell and refactoring explained in a clause the first time it appears.

````
```findings
id: listen-to-tests-1
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
cause: a line item is a domain concept with no type, so its values and its tax rule have no home
direction: introduce
tests: 12 tests in invoice.test.ts change their setup; they test behaviour, so their assertions stand
strength: Strong
---
id: listen-to-tests-2
...
```

```hints
- module scale: billing and shipping both parse tax codes; boundary question for /modularity:review
```
````

- **id**: the lens name and a number, unique in your report. Synthesis accounts for every finding by its id.
- **lens**: the lens's skill name.
- **concept**: the domain concept the finding is about. Use the `GLOSSARY.md` term when one exists. Otherwise name the concept in the domain's words, or fall back to the code symbol as `path#Symbol`. Name the concept, not the smell.
- **where**: files and symbols, comma-separated, as `path#Symbol`.
- **today**: what the code does now, in plain words, one sentence.
- **cast**: every object or function the finding involves, one per line, as `Symbol (path:line): what it does today`. Include the **neighbours**: the callers and collaborators a reader needs to see why it hurts and what the change will touch.
- **smell**: what's wrong, in domain terms, as a labelled heuristic: "possible Feature Envy", never a verdict. Name the source.
- **evidence**: the concrete signal you saw: a test name, a count, a line. A finding with no evidence is speculation; mark it so.
- **technique**: the named refactoring and its book. Use the names in Fowler's catalog (refactoring.com/catalog); a class rename has no catalog name, so write "rename class".
- **restructure**: what changes, in one sentence.
- **after**: the resulting shape, one line per object that is new or changes: its new home, signature, or responsibility.
- **cause**: your best guess at the underlying problem the smell is a symptom of, in one sentence: a missing concept, a decision with no single owner, a role nobody named. Synthesis looks for one cause behind several findings, so state the cause, not the smell again.
- **direction**: one of `extract`, `combine`, `move`, `rename`, `introduce`, `inline`, `hide`, `expose`, `remove`. Synthesis detects conflicts from opposite directions on the same symbol.
- **tests**: which tests the change will likely break, and whether each tests behaviour or is pinned to internals. Write `untested` when no test exercises the code.
- **strength**: `Strong` (clear evidence, clear payoff), `Worth exploring` (real signal, uncertain remedy), or `Speculative` (a hunch worth a look).

**Hints** are smells this lens can't act on at class or function scale: module- or service-scale coupling, cohesion and boundaries, and mechanical duplication with no domain concept behind it. One line each, naming the area.
