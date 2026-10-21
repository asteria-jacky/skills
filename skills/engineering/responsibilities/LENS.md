# Responsibilities

_Fowler (with Beck), Refactoring 2nd ed., ch. 3 "Bad Smells in Code"; Martin, Agile Software Development and Clean Code; Fowler, "TellDontAsk"._

## Goal

Fowler: refactoring makes software "easier to understand and cheaper to modify without changing its observable behavior" (DefinitionOfRefactoring). The outcome is change locality: one change, one place.

This lens usually counts `places-to-change` (Shotgun Surgery, Duplicated Code: the places one change touches) and `reasons-to-change` (Divergent Change, SRP: the separate reasons one unit changes, from `git log` when it shows them). The measures are defined in `shared/FINDINGS.md`.

Each piece of behaviour has **one home**: the object that holds the data it works on and changes for the same reason it does. When behaviour lives away from its data, when one unit changes for several unrelated reasons, or when one concept is written out in several places, the code fights every change. Martin's Single Responsibility Principle names the test: "Gather together the things that change for the same reasons. Separate those things that change for different reasons." Fowler's smells are the signals; his catalogue (refactoring.com/catalog) names the moves.

Every finding is a judgement call: name the smell ("possible Feature Envy"), never a verdict. A repo's documented standards and ADRs override this lens.

Items marked † come from the book's chapter text, which wasn't available to verify; the smell names and refactoring names are verified. Treat † wording as a paraphrase.

## How to read

1. **Follow the change.** Read the code the way it will be changed. In ref mode, the diff is a real change: note every file it had to touch to deliver one idea. In both modes, `git log` on the scope shows which files change together, and for how many different reasons.
2. **Follow the data.** For each function, ask whose data it reads and writes. A function that mostly reads another object's fields lives in the wrong place.
3. **Name the reason to change.** For each class or module, try to say in one phrase what would make it change. Two unrelated phrases mean two responsibilities. Martin's later wording ties a reason to change to an **actor**: the group of people who would ask for it.
4. **Collect signals** from the catalogue below, with counts and locations as evidence.
5. **Check the stop condition** (below) before proposing any extraction.

## Catalogue: one unit, several jobs

### Divergent Change

- **Looks like:** one module edited for unrelated reasons; `git log` on it shows commits about different features; a class you change "in these three methods when the database changes, these four when the pricing rules change". †
- **Means:** two responsibilities share a home and change on separate axes.
- **Remedy:** Split Phase when the jobs run in sequence (parse then compute); otherwise Extract Class, then Move Function to give each job its own home.

### Large Class and Long Function

- **Looks like:** a class with many fields used by disjoint groups of methods; a function with commented sections, or several levels of abstraction in one body.
- **Means:** several responsibilities, or several steps nobody named.
- **Remedy:** Extract Class along the field groups; Extract Function along the commented sections, naming each piece for _what_ it does, not how.
- **Stop condition applies:** see below. Long is not the smell; mixed jobs are.

### Long Parameter List

- **Looks like:** functions taking many parameters, several of them flags or values the function could get itself.
- **Means:** the function reaches across responsibilities, or several of its parameters form a concept (see **Data Clumps**).
- **Remedy:** Introduce Parameter Object, Preserve Whole Object, Replace Parameter with Query, Remove Flag Argument.

## Catalogue: behaviour away from its data

### Feature Envy

- **Looks like:** a function that calls another object's getters more than it uses its own fields.
- **Means:** the logic lives away from the data it works on.
- **Remedy:** Move Function to the object whose data it uses; Extract Function first when only part of it is envious.
- **Not a finding:** patterns that deliberately separate behaviour from data, such as Strategy and Visitor, break this rule on purpose. †

### Data Class

- **Looks like:** classes with fields, getters and setters and no behaviour, while the logic about them sits in services or managers.
- **Means:** a responsibility was never given to the object that owns the data. Fowler's bliki calls the domain-wide version an Anemic Domain Model. †
- **Remedy:** Encapsulate Record, then Move Function: the behaviour moves onto the data.
- **Not a finding:** records that really are just data: results crossing a boundary, DTOs, immutable values with no rules.

### Ask then act

_Fowler, "TellDontAsk"; GOOS ch. 2 "But Sometimes Ask"._

- **Looks like:** a caller queries an object's state, decides, then tells the object what to do: `if (order.status == PAID && order.items.all(shipped)) order.close()`.
- **Means:** the decision belongs to the object being asked. "Rather than asking an object for data and acting on that data, we should instead tell an object what to do" (Fowler).
- **Remedy:** Move Function: the decision becomes a method on the object (`order.closeIfFulfilled()`).
- **Not a finding:** query methods themselves. Fowler: "personally, I don't use tell-dont-ask. I do look to co-locate data and behavior", and he warns the rule creates GetterEradicators: people removing every query. Asking is fine for values and collections, for searching and filtering, and wherever another concern (layering, say) outranks co-location. Flag ask-then-act only when the decision clearly belongs inside the object asked.

### Insider Trading

- **Looks like:** two modules swapping private data, reaching into each other's internals, or always changing together.
- **Means:** the boundary between them is in the wrong place.
- **Remedy:** Move Function and Move Field to put the shared knowledge in one of them, or Hide Delegate behind a third.

### Message Chains and Middle Man

These pull against each other, and Fowler's catalogue lists each refactoring as the inverse of the other.

- **Message Chains** look like `a.getB().getC().doThing()`: the caller knows the structure between objects. Remedy: Hide Delegate, or Extract Function then Move Function so the chain becomes one request.
- **Middle Man** looks like a class whose methods mostly forward to another. Remedy: Remove Middle Man, or Inline Function.
- **Means:** each fix overdone produces the other smell. Say which side of the balance the code is on, and mark `direction: hide` (Hide Delegate) or `direction: expose` (Remove Middle Man) so `restructure` can surface a conflict with the depth lens.

## Catalogue: a concept with no type

### Data Clumps

- **Looks like:** the same two to four fields or parameters appearing together in several places. Test: delete one; if the others stop making sense, they are one concept. †
- **Means:** a concept nobody named.
- **Remedy:** Extract Class or Introduce Parameter Object, then Move Function to give the new object the behaviour that works on the clump.

### Primitive Obsession

- **Looks like:** strings, numbers and booleans standing for money, ranges, identifiers, codes, phone numbers, statuses; validation and formatting of the same primitive repeated at each use.
- **Means:** a concept with no type, so its rules have no home.
- **Remedy:** Replace Primitive with Object; Replace Type Code with Subclasses when a code selects behaviour. The new type is often a value object: hand the concept's naming to the domain-model lens through `concept`.

### Temporary Field

- **Looks like:** fields set only in some states or only during one operation, null the rest of the time.
- **Means:** an object hiding inside another, or an operation that needs its own object.
- **Remedy:** Extract Class for the fields and the code that uses them; Introduce Special Case for the null states.

## Catalogue: one concept, many places

Duplicated code is **evidence** of a concept implemented twice. The remedy unifies the concept; the duplication goes with it.

### Duplicated Code

- **Looks like:** the same logic, or the same rule with small variations, in several functions or classes.
- **Means:** one concept with no single home.
- **Remedy:** Extract Function into the concept's home; Pull Up Method when the copies share a parent; Slide Statements first to line the copies up.
- **Not a finding: coincidental duplication.** Code that looks alike but serves different concepts that will change for different reasons. Leave it, and say why in the report.

### Alternative Classes with Different Interfaces

- **Looks like:** two classes doing the same job under different method names.
- **Means:** one concept, implemented twice.
- **Remedy:** Change Function Declaration to align the interfaces, then Move Function or Extract Superclass to merge.

### Repeated Switches

- **Looks like:** the same `switch` or `if` chain on a type code at several sites.
- **Means:** a missing polymorphic concept: each case is a kind of thing whose behaviour is scattered across the switches.
- **Remedy:** Replace Conditional with Polymorphism; the cases become types that each own their behaviour.

### Shotgun Surgery

- **Looks like:** one change forces small edits in many files. In ref mode the diff shows it directly.
- **Means:** a concept scattered across homes.
- **Remedy:** Move Function and Move Field to gather it; Combine Functions into Class or Combine Functions into Transform; Inline Function or Inline Class to gather first, then split cleanly.

## Comments

- **Flag:** comments that excuse code ("this is complicated because…") or that restate a name. Fowler calls the first kind deodorant: the comment covers a smell the code should fix. Remedy: Extract Function with a name that says what the comment said; Introduce Assertion for comments stating a rule.
- **Not a finding:** missing comments, or interface comments explaining what a module promises. Ousterhout values these, and the lenses disagree about comments in general; this lens flags only comments standing in for a restructure.

## The stop condition

Martin and Ousterhout agree on one limit to decomposition (*aposd-vs-clean-code*, their joint record): extract only "because the interface is abstract, and the implementation has deeper detail" (Martin). Martin concedes that Clean Code's first edition gives little guidance on recognising over-decomposition, and writes "if I must err, I'd rather err on the side of decomposition"; Ousterhout warns that the One Thing Rule "lacks guardrails and will lead to over-decomposition".

Before proposing an Extract Function or Extract Class, check:

- Is the extracted piece's interface simpler than its body?
- Can a reader understand each piece without reading the other? If understanding one means flipping back and forth to the other, the pieces are entangled; keep them together.

If either answer is no, drop the finding or downgrade it to `Possible` with the reason. When you extract anyway, mark `direction: extract` so `restructure` can surface a conflict with the depth lens.

## Where this lens meets the others

- **listen-to-tests:** Bloated Constructor and Confused Object are the test-side view of Large Class and Divergent Change. Share the `concept` so they merge.
- **domain-model:** Data Clumps and Primitive Obsession end in a new type; the domain-model lens names it and decides whether it is a value object or an entity. Name the `concept` in domain words, not `ParamsObject`.
- **depth:** Extract versus combine is the main conflict between this lens and depth. Fowler's Speculative Generality and Lazy Element live with depth.

## Out of scope

- Module- and service-scale coupling and boundaries: report them as **hints**.
- Mechanical duplication with no domain concept behind it (boilerplate, repeated plumbing): a **hint**.
- Formatting, style and naming conventions a linter or formatter owns.

## It's working if

- Every Strong finding shows a counted effect, and its evidence lists each place or commit counted.
- Each `reasons-to-change` count names the reasons, and the actors behind them when the code or history shows them.
- Each finding names the home the behaviour moves to, and the data that home holds.
- Each `extract` finding passes the stop condition: the extracted piece's interface is simpler than its body.
