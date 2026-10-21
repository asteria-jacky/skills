# Findings

The report format every lens follows. `restructure` turns the reports into design moves with [`SYNTHESIS.md`](SYNTHESIS.md).

## Report format

Write the report to the file path your prompt gives: one fenced `findings` block, then one fenced `hints` block, and nothing else.

Report only what the code shows. An empty `findings` block is a valid, common report: a tidy change has nothing to restructure. A weaker finding added to fill the report misleads the verdict. The same holds for an empty `hints` block. Under 1,500 words in total. Then reply with one line only: the path, and how many findings and hints it holds.

Each finding is a run of `key: value` lines; separate findings with a line holding only `---`. Keep each value on one line, except `cast` and `after`, which take one `- ` item per line beneath the key. `effect` repeats: one `effect:` line per measure.

You have read the code; whoever reads your report has not. Write every finding so a reader can follow it **without opening a file**, in the ASD-STE100 style of **Report prose** in [`CONTRACT.md`](CONTRACT.md#report-prose).

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
effect: must-know 5 → 1 (parameters of Invoice.addLine, src/billing/invoice.ts:42: price, quantity, taxCode, currency, sku)
effect: test-setup 5 → 1 (values makeInvoice rebuilds for each line, test/billing/invoice.test.ts:8)
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
- skill: /improve-codebase-architecture · where: src/billing/, src/shipping/ · why: both parse tax codes
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
- **effect**: what acting on the finding would gain, as a count a reader and the next review can check. Shape: `effect: <measure> <today> → <after> (<evidence>)`, one line per measure, using the measures under **Measures** below. **Today** is counted in the code now, and the evidence lists what you counted (the places, the parameters, the names, the setup lines) so verify can count it again. **After** is your prediction from `after`. When nothing can be counted, write `effect: not counted`.
- **technique**: the named refactoring and its book. Use the names in Fowler's catalog (refactoring.com/catalog); a class rename has no catalog name, so write "rename class".
- **restructure**: what changes, in one sentence.
- **after**: the resulting shape, one line per object that is new or changes: its new home, signature, or responsibility.
- **cause**: your best guess at the underlying problem the smell is a symptom of, in one sentence: a missing concept, a decision with no single owner, a role nobody named. Synthesis looks for one cause behind several findings, so state the cause, not the smell again.
- **direction**: one of `extract`, `combine`, `move`, `rename`, `introduce`, `inline`, `hide`, `expose`, `remove`. Synthesis detects conflicts from opposite directions on the same symbol (the pairs under **Opposite directions** in [`CONTRACT.md`](CONTRACT.md#opposite-directions)).
- **tests**: which tests the change will likely break, and whether each tests behaviour or is pinned to internals. Write `untested` when no test exercises the code.
- **strength**: `Strong` (clear evidence, a counted effect), `Worth exploring` (real signal, uncertain remedy), or `Possible` (a hunch worth a look). **No count, no Strong**: a finding with `effect: not counted` is `Worth exploring` at most.

**Hints** are smells this lens can't act on at class or function scale. One line each, `- skill: <skill> · where: <area> · why: <the smell, in a few words>`, so a Factory can route it. Name the skill from **Hints: what no lens covers** in [`CONTRACT.md`](CONTRACT.md#hints-what-no-lens-covers).

## Measures

Every lens shares these five measures, and any lens may use any of them. The book terms say which smell each one counts.

| Measure | Counts | Book terms |
|---|---|---|
| `places-to-change` | places that must change together for one decision or rule | change amplification (Ousterhout); Shotgun Surgery, Duplicated Code (Fowler) |
| `must-know` | things a caller must know to use the code correctly: parameters, flags, ordering rules, error cases | cognitive load, unknown unknowns (Ousterhout) |
| `reasons-to-change` | separate reasons one unit changes | Divergent Change (Fowler); SRP (Martin) |
| `names-per-concept` | names the code uses for one domain concept | translation (Evans) |
| `test-setup` | setup lines or mocks per test | test friction (Freeman & Pryce) |

An effect is evidence for the finding and a target for the move that removes it. It is not a score: synthesis ranks moves by value, weighted by strength.
