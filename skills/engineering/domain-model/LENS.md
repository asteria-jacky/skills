# Domain model

_Evans, Domain-Driven Design (2003) and the DDD Reference (2015); Vernon, "Effective Aggregate Design" (2011) and Implementing Domain-Driven Design (2013), ch. 10 "Aggregates"._

The code is a model of the domain, and it should **speak the domain's language**: one term per concept, one concept per term, and the same words the domain experts and `GLOSSARY.md` use. Evans: "Use the model as the backbone of a language… Recognize that a change in the language is a change to the model." A concept the experts talk about but the code doesn't name, a rule buried in an `if`, an object that should be a value but has identity: each makes the code harder to change in the ways the business changes. This lens finds where the model and the language have drifted apart, and where the model could go deeper.

Every finding is a judgement call: name the smell ("possible missing value object"), never a verdict. A repo's documented standards and ADRs override this lens. If a finding contradicts an ADR, say so explicitly in the finding.

Items marked † come from the book's chapter text, which wasn't available to verify; the chapter and pattern names, the DDD Reference quotes and Vernon's essay quotes are verified. Treat † wording as a paraphrase.

## How to read

1. **Read the language first.** `GLOSSARY.md` (or the glossary `GLOSSARY-MAP.md` points to), the ADRs, and the domain words in specs, issues and UI text. With no glossary, the language is the terms already in the code and docs.
2. **Map terms to code.** For each domain term in scope, find the class, type or function that embodies it. Note terms with no code, code with no term, and terms that map to two places or two terms that map to one.
3. **Read for awkwardness.** Evans's "Digging Out Concepts" (DDD ch. 9) is the method: listen to the language, scrutinise awkwardness, contemplate contradictions. Code that keeps getting patched in the same place, and rules that need comments to explain, are where an implicit concept hides.
4. **Classify the objects** in scope as entity, value object, service or aggregate, and check each behaves like what it is.
5. **Collect signals** from the catalogue below. Evidence is a term, a location, and what the glossary or the code says.

## Catalogue: language

### Mysterious and implementation names

- **Looks like:** names that hide what a thing does or holds (`process`, `handle`, `data`); implementation words where a domain term exists: `Manager`, `Helper`, `Data`, `Info`, `Processor`, `Util`, or type names like `userMap`.
- **Means:** the code is talking about its mechanism, not the domain. Evans's **Intention-Revealing Interfaces**: "Name classes and operations to describe their effect and purpose, without reference to the means by which they do what they promise… These names should conform to the ubiquitous language."
- **Remedy:** rename to the domain term (Rename Variable, Rename Field, Change Function Declaration; a class rename has no catalogue name). If no honest name comes, the design is murky: the responsibility is split wrong. Say so, and look for a responsibilities finding instead.

### Synonyms

- **Looks like:** two names for one concept across files: `client` and `customer`, `order` and `purchase`, `remove` and `delete` for the same act.
- **Means:** the team or the code disagrees on the language; readers will assume two concepts.
- **Remedy:** pick the glossary term, rename the other everywhere. If the glossary lacks the concept, note it as a gap for `/domain-modeling` rather than inventing a term.

### Homonyms

- **Looks like:** one name used for two concepts: an `Account` that is sometimes a login and sometimes a ledger; a `status` field meaning different things in different flows.
- **Means:** two concepts sharing a word. In a larger system this can be two **bounded contexts**, each with its own meaning for the word; that is a boundary question, so report it as a hint.
- **Remedy:** split them, and name each.

## Catalogue: implicit concepts

_DDD ch. 9 "Making Implicit Concepts Explicit"._

### A term with no class

- **Looks like:** a word in the glossary, specs or experts' talk ("line item", "allowance", "billing period") with no type in the code; its data and rules spread across other objects.
- **Means:** the model is missing a concept the domain has.
- **Remedy:** introduce the type and move its data and behaviour onto it (Extract Class, Move Function, Replace Primitive with Object).

### Explicit constraints

- **Looks like:** a business rule buried inside a conditional in a method that does other things: a limit, an eligibility check, a policy.
- **Means:** a constraint the domain cares about has no name, so it can't be found, tested or changed on its own. †
- **Remedy:** extract the constraint into a named method or object, so the rule reads in domain words.

### Processes as domain objects

- **Looks like:** a long service method that walks through a business process the experts name (a "settlement", a "reconciliation").
- **Means:** the process is a domain concept in its own right. †
- **Remedy:** give it a name: a service or an object named for the process. Evans is careful here: make a process explicit when the experts talk about it, not every procedure.

### Specification

- **Looks like:** the same selection or validation rule ("overdue invoices", "eligible customers") written in several queries or filters.
- **Means:** a rule about _which_ objects qualify, with no home. †
- **Remedy:** a **Specification**: a predicate object named in domain terms that can be tested and combined. Cite DDD ch. 9 ("SPECIFICATION").

## Catalogue: building blocks

The DDD Reference definitions are the test for each.

### Value object

- **Definition:** "When you care only about the attributes and logic of an element of the model, classify it as a value object. Make it express the meaning of the attributes it conveys and give it related functionality. Treat the value object as immutable… Don't give a value object any identity."
- **Looks like a problem when:** a value has an id or is compared by reference; a value is mutable; a value is a bare primitive or a bag of fields with its logic elsewhere (see responsibilities: Primitive Obsession, Data Clumps).
- **Remedy:** make it immutable, compare by attributes, and move its logic onto it.

### Entity

- **Definition:** an object defined by identity and continuity, not attributes: "The model must define what it means to be the same thing."
- **Looks like a problem when:** identity is unclear or computed from changing attributes; two objects for the same thing can exist at once; an entity carries attributes and behaviour that belong to a value it should hold.
- **Remedy:** make identity explicit; move attribute clusters into value objects the entity holds (Vernon: "Favor Value Object Parts").

### Domain service

- **Definition:** "When a significant process or transformation in the domain is not a natural responsibility of an entity or value object, add an operation to the model as a standalone interface declared as a service… Give the service a name, which also becomes part of the ubiquitous language."
- **Looks like a problem when:** a service holds logic that _is_ a natural responsibility of an entity or value (the anemic model, seen from the domain side); or a service is named for mechanism (`OrderManager`) rather than the domain operation.
- **Remedy:** move the logic onto the entity or value, or rename the service for the operation it performs.

## Catalogue: supple design

_DDD ch. 10 "Supple Design"._ Signs the model resists change, and the shapes that make it easy to work with.

- **Side-Effect-Free Functions.** "Place as much of the logic of the program as possible into functions, operations that return results with no observable side effects. Strictly segregate commands… into very simple operations that do not return domain information." Signal: methods that both change state and compute domain results. Remedy: Separate Query from Modifier; move the computation into a value object.
- **Assertions.** "State post-conditions of operations and invariants of classes and aggregates. If assertions cannot be coded directly in your programming language, write automated unit tests for them." Signal: an invariant only callers enforce, or enforced in some paths and not others. Remedy: enforce it in the object that owns it; name it in a test.
- **Conceptual Contours.** "Decompose design elements… into cohesive units, taking into consideration your intuition of the important divisions in the domain. Observe the axes of change and stability through successive refactorings." Evans rejects both splitting everything and lumping everything: "Half of a uranium atom is not uranium." Signal: changes that keep cutting across a class in the same direction, or classes that always change together. Remedy: redraw the boundary along the domain's own division. This is Evans's answer to the extract-versus-combine argument: follow the domain.
- **Standalone Classes.** "Low coupling is fundamental to object design. When you can, go all the way." Signal: a domain object that drags in many other concepts to do its job. Remedy: cut dependencies the concept doesn't need.
- **Closure of Operations.** "Where it fits, define an operation whose return type is the same as the type of its argument(s)… A closed operation provides a high-level interface without introducing any dependency on other concepts." Signal: operations on values that return primitives or other types and make callers reassemble (`addMoney(a, b) → number`). Remedy: return the same type (`Money.plus(Money) → Money`).

## Catalogue: aggregates

_Evans, Aggregates (DDD Reference); Vernon, "Effective Aggregate Design" Parts I–II._

An aggregate is a cluster of entities and values with one root, treated as one unit for consistency. Evans: "allow external objects to hold references to the root only… Within an aggregate boundary, apply consistency rules synchronously. Across boundaries, handle updates asynchronously." Vernon: "Aggregate is synonymous with transactional consistency boundary."

**Only apply this section when the code persists aggregates and transactional consistency matters.** In code with no persistence or concurrency concerns, these rules collapse into plain encapsulation of invariants: report an invariant enforced in the wrong place (see Assertions) and leave aggregates out of it.

Vernon's four rules, each a signal:

1. **Model true invariants in consistency boundaries.** "An invariant is a business rule that must always be consistent." "A properly designed bounded context modifies only one aggregate instance per transaction in all cases." Signal: a use case or transaction that saves several aggregates.
2. **Design small aggregates.** Large clusters cause concurrency failures and load far more than they need. Limit the aggregate "to just the root entity and a minimal number of attributes and/or value-typed properties. The correct minimum is the ones necessary, and no more." Signal: an aggregate loading large collections to change one element. Caveat: "Don't Trust Every Use Case": a use case that changes several aggregates at once "may not accurately reflect the true aggregates of our model".
3. **Reference other aggregates by identity.** "Prefer references to external aggregates only by their globally unique identity, not by holding a direct object reference." Signal: object references to another aggregate's root; lazily loaded graphs; repositories called from inside an aggregate.
4. **Use eventual consistency outside the boundary.** When one command's rules reach other aggregates, update them eventually, typically through domain events. To decide, **ask whose job it is**: "ask whether it's the job of the user executing the use case to make the data consistent. If it is, try to make it transactionally consistent… If it is another user's job, or the job of the system, allow it to be eventually consistent."

Vernon names four reasons to break these rules (user-interface convenience, lack of technical mechanisms, global transactions, query performance) and adds "we don't go in search of excuses to break the aggregate rules of thumb." If the code breaks a rule for one of these reasons, it is not a finding.

When boundaries don't fit, Evans says to "reconsider the model. Is the domain scenario hinting at an important new insight?" That question belongs in the finding.

## Breakthrough

_DDD Part III "Refactoring Toward Deeper Insight", ch. 8 "Breakthrough"._ "Refactoring can also be motivated by an insight into the domain… A model that sloughs off the superficial and captures the essential is a deep model."

A breakthrough is a restructure where a new or reframed concept makes several problems disappear at once. Evans's example turns a tangle of loan-share bookkeeping into a single "share pie". † Breakthroughs come from many small refactorings toward insight, not from forcing one; Evans's advice is to focus on basics. †

**Looks like:** several findings, here or in other lenses, all pointing at one concept: awkward code, duplicated rules and test pain clustered around a term the code doesn't have. When you see that, say so in the finding's `restructure` and `strength`, name the concept, and give `restructure` the evidence to merge it.

## Glossary

- Use the glossary's terms in every finding. If the concept you need isn't there, say so: either the code is inventing language the project doesn't use, or there is a real gap. A gap is a note for `/domain-modeling`, not a term this lens adds.
- When a finding renames a domain term, `restructure` updates `GLOSSARY.md` in the same step. Say in `restructure` which entry changes.

## Where this lens meets the others

- **responsibilities:** Data Clumps and Primitive Obsession find a missing type; this lens names it and says whether it is a value or an entity. Data Class is the anemic model this lens sees from the service side. Share the `concept`.
- **listen-to-tests:** the role or value the tests keep reaching for is often the concept this lens finds missing; test names that describe features are the language in use.
- **depth:** Conceptual Contours is the domain's say in extract versus combine. When the domain division and the depth lens disagree, name both in the finding and let `restructure` surface the conflict.

## Out of scope

- Bounded-context boundaries and context maps: report them as **hints** for `/modularity:review`.
- Writing or editing `GLOSSARY.md` and ADRs as findings: that belongs to `/domain-modeling`. A finding may say which entry a rename would change.
- Persistence, framework and infrastructure design, except where it leaks into the domain model.
