# Lenses

Each lens is a way of seeing the code, with the smells that signal it and the restructures that answer it. Every finding is a judgement call: name the smell ("possible Feature Envy"), never a verdict. A repo's documented standards and ADRs override any lens.

## Ubiquitous language

_Evans, Vernon, Martin._ Code speaks the domain: one term per concept, one concept per term, and the same word the domain experts and `GLOSSARY.md` use.

- **Mysterious Name**: a name that hides what the thing does or holds. If no honest name comes, the design is murky; look at the other lenses first.
- **Implementation names**: `Manager`, `Helper`, `Data`, `Info`, `Processor`, or type names (`userMap`) where a domain term exists.
- **Synonyms**: two names for one concept across files (`client` / `customer`).
- **Homonyms**: one name for two concepts. Split them, and name each.

→ Rename Variable / Function / Class, Change Function Declaration (Fowler).

## Responsibility

_Martin, Freeman & Pryce, Fowler._ Each object has one reason to change, and objects collaborate through roles: _tell, don't ask_. Reuse appears once a responsibility has a name and a home.

- **Divergent Change**, **Large Class**, **Long Function**: one unit doing several jobs.
- **Feature Envy**: logic living away from the data it works on.
- **Data Clumps**, **Primitive Obsession**: a concept with no type yet. Often a _value object_ waiting to be born.
- **Ask-then-act**: callers querying state to decide what an object should have decided itself.

→ Extract Function / Class, Move Function / Field, Introduce Parameter Object, Replace Primitive with Object (Fowler); Value Object, Entity, Domain Service (Evans).

## Concept consolidation

_Evans, Fowler._ One domain concept lives in one place. Duplicated code is _evidence_ of a concept implemented twice; the restructure unifies the concept, and the duplication goes with it.

- **Duplicated Code**, **Alternative Classes with Different Interfaces**: the same idea under two shapes.
- **Repeated Switches**: the same type-switch at several sites: a missing polymorphic concept.
- **Shotgun Surgery**: one change touches many places, so the concept is scattered.
- **Coincidental duplication**: code that looks alike but serves different concepts that will diverge. Leave it, and say why.

→ Combine Functions into Class, Pull Up Method, Replace Conditional with Polymorphism, Move Function (Fowler).

## Depth

_Ousterhout._ A **deep** module hides much behind a narrow interface. Pull complexity down; let the caller know less.

- **Shallow module**: an interface nearly as complex as its body. Deletion test: would removing it concentrate complexity, or just move it?
- **Information leakage**: one design decision spread across several units.
- **Pass-through**, **Middle Man**: methods that only forward.
- **Temporal decomposition**: split by _when_ things happen instead of _what knowledge_ they hold.
- **Speculative Generality**: hooks, parameters, and layers for needs nobody has. Common in generated code.

→ Combine into one deep unit, Inline Function / Class, Remove Middle Man, Hide Delegate (Fowler). Class/function scale only: a boundary between modules or services is a **hint**.

## Tests

_Freeman & Pryce, Ousterhout._ Tests exercise behaviour through the interface. Fewer tests through a deep module cover more than many tests pinned to internals.

- **Pinned tests**: tests asserting private structure, call order, or signatures a restructure is meant to change. Expected collateral: update or delete them.
- **Test sprawl**: many shallow tests around a cluster a restructure would deepen. Fold them into fewer tests through the new interface.
- **Untested restructure**: a finding touching code no test exercises. Flag it so the user weighs the risk.

## Hints

Not restructured here; named for the user to run.

- Coupling, cohesion, or boundary smells at module or service scale: `/modularity:review`, `/improve-codebase-architecture`.
- Mechanical duplication with no domain concept behind it: `/simplify`.
