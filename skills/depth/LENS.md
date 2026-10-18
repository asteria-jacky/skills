# Depth

_Ousterhout, A Philosophy of Software Design (2nd ed. 2021), his Stanford CS 190 course (Winter 2024), and his joint record with Robert Martin, aposd-vs-clean-code (2024–25)._

Complexity is the enemy, and its causes are **dependencies** and **obscurity** (CS 190 "Key Concepts"): how much a developer must hold in their head to change something safely, and how hard that information is to find. The main tool against it is the **deep module**: a lot of functionality behind a simple interface, so callers know little and changes stay inside. A shallow module, one whose interface is nearly as complex as its body, adds a thing to learn without hiding anything. Ousterhout's summary: "Pull complexity downward, push specialization upward."

Here, depth means **how much a caller doesn't need to know**: what the module hides, set against what its interface makes callers understand. Line counts don't measure it.

Every finding is a judgement call: name the smell ("possible shallow class"), never a verdict. A repo's documented standards and ADRs override this lens.

Items marked † come from the book's chapter text, which wasn't available to verify; the red flags, key concepts, review questions and debate quotes are verified from Ousterhout's own course materials and repo. Treat † wording as a paraphrase.

## How to read

1. **Read interfaces before bodies.** For each class and function in scope, read what a caller must know to use it: signature, parameters, errors, ordering rules, comments. Then read what it hides.
2. **Ask Ousterhout's review questions** (CS 190 code reviews):
   - Are classes and methods deep?
   - Does each entity have a simple interface?
   - Does it do one thing completely and well?
   - Is there information leakage?
   - Are the interfaces as general-purpose as possible?
   - Is the code obvious: "everything immediately makes sense, and your first guesses about behavior turn out to be correct"?
3. **Run the deletion test** on each small unit: would deleting it (inlining it into its callers) concentrate complexity in one place, or just move it around? If deleting it changes little, it isn't earning its interface.
4. **Collect red flags** from the catalogue below, with locations as evidence. Ousterhout: "focus on red flags: aspects of the design that suggest problems."

## Catalogue: red flags

Ousterhout's own list, from his CS 190 wrap-up slide, in his words. The book gives the same flags slightly different names.

### Shallow classes

- **Looks like:** classes or functions whose interface is about as complex as their body: thin wrappers, one-call classes, getters and setters with no rules, stacks of small classes each adding one step (the book contrasts Unix file I/O with Java's layered `FileInputStream`/`BufferedInputStream` †). Many tiny classes together is what the book calls "classitis". † Fowler's Lazy Element (a class or function that no longer pulls its weight) is the same signal.
- **Means:** each unit adds something to learn and hides almost nothing.
- **Remedy:** combine into one deeper unit (Inline Function, Inline Class), or give the unit more of the job so its interface hides more. "It's more important for a module to have a simple interface than a simple implementation." †

### Information leakage

- **Looks like:** one design decision visible in several units: the same file format, protocol, ordering rule or data layout known by two or more classes, so they must change together. Ousterhout's sub-points: **dependencies** (units that must change together) and **conjoined methods or classes**: you can't understand one without the other, "flipping back and forth between the implementations of two methods".
- **Means:** the decision has no single owner.
- **Remedy:** give the knowledge one home (Move Function, Move Field, Combine Functions into Class); for conjoined methods, combine them. Ousterhout: "Entangled methods can usually be improved by combining them so that all the code is in one place."

### Temporal decomposition

- **Looks like:** structure that follows the order things happen in rather than what each part knows: `ReadConfig`, `ParseConfig`, `WriteConfig` classes all knowing the config format; a pipeline whose stages share private knowledge.
- **Means:** the split was made by _when_, so the knowledge each stage needs is leaked across all of them.
- **Remedy:** reorganise around the knowledge: one module owns the format, and the stages call it. Split Phase is the right Fowler move only when the phases really share nothing but a clean intermediate result.

### Pass-through methods

- **Looks like:** methods that do little but forward to another method with a similar signature; also pass-through variables threaded through several layers that don't use them. Fowler's Middle Man is the class-level version.
- **Means:** two layers with the same abstraction. "Different layers should have different abstractions."
- **Remedy:** Remove Middle Man or Inline Function to let callers go straight to the real work; or give the layer a real job. For pass-through variables, a context object the layers share. †

### Unnecessary specialization

- **Looks like:** general mechanisms with special-purpose knowledge mixed in: a text-storage class with UI-specific methods, a data layer branching on one use case; interfaces that fit exactly one caller.
- **Means:** specialization pushed down instead of up, so the general part can't be reused and every new use edits it.
- **Remedy:** "push specialization upward": move the special cases to the caller, and give the general module a **somewhat general-purpose** interface: general enough for several uses, implementing only what is needed today. †

### Special cases

- **Looks like:** `if` statements handling edge cases scattered through the logic; error paths and empty-input paths duplicated across callers.
- **Means:** the normal case doesn't cover the edges, so every reader must track them.
- **Remedy:** design the special cases out: choose semantics where the normal path handles the edge. See **Define errors out of existence**.

### Code duplication

- **Looks like:** nontrivial code repeated.
- **Means:** a missing abstraction.
- **Remedy:** the responsibilities lens owns duplication of domain concepts. Report it here only when the duplication is a sign of leakage: two units repeating the same knowledge of a decision.

### Inconsistencies

- **Looks like:** similar things done differently: two names for one idea, the same kind of operation with different parameter orders or error conventions.
- **Means:** readers can't carry knowledge from one place to the next, so every place must be learned.
- **Remedy:** align on one convention (Change Function Declaration, renames). Naming inconsistencies of domain terms belong to the domain-model lens; share the `concept`.

### Comments and documentation as signals

These flags read the comments for what they say about the design:

- **Comment duplicates code**: the comment repeats the name or the statement. Signal only; not a restructure.
- **Implementation contaminates interface documentation**: the interface comment has to explain internals for a caller to use it. The interface leaks the implementation.
- **Documentation has to be long to be complete**: describing what a unit does takes paragraphs. The abstraction is wrong: it does several things, or its interface exposes too much.
- **Vague names**: names too broad to say what a thing is or does; a name that is hard to pick suggests a murky design. †

Report the last three as design findings: the remedy is restructuring the unit so its interface is simple to describe. Writing or rewriting comments is out of scope.

### Code is not obvious

- **Looks like:** behaviour a reader can't predict from names and interfaces; generic containers (`Pair`, tuples, maps) where a named type would say what each part means; events and callbacks that hide control flow.
- **Means:** obscurity: the information a reader needs isn't where they look.
- **Remedy:** a named type or method that makes the meaning visible (Replace Primitive with Object, Introduce Parameter Object, Extract Function with an honest name).

## Principles, with their limits

- **Pull complexity downward.** A module should absorb the complexity of its job rather than export it to callers as configuration parameters, ordering rules or error cases. Limit: only complexity closely related to the module's existing job. †
- **General-purpose modules are deeper** (the 2nd edition's reworked ch. 6). A somewhat general-purpose interface usually needs fewer, more powerful methods. This pulls against Fowler's Speculative Generality; the two agree once separated: **generality of interface** is good, **unused hooks, parameters and layers** for needs nobody has are not. Flag the second, especially in generated code, as Speculative Generality (Fowler) with remedy Collapse Hierarchy, Inline Function or Remove Dead Code.
- **Define errors out of existence.** Exceptions and error cases are interface complexity. Redefine the operation so the error can't happen (deleting something already absent succeeds; a substring with out-of-range indexes clips †), mask errors at a low level, or aggregate handling in one place. Ousterhout's own limit: "use this idea judiciously: it's easy to take it too far." Never hide an error a caller genuinely needs to act on.
- **Better together or better apart?** Combine when pieces share information, are always used together, overlap conceptually, or can't be understood alone. Separate general-purpose code from special-purpose code. Method length is not the test: each method should do one thing and do it completely. †
- **Design it twice.** For a finding that proposes a new interface, sketch a radically different alternative in one line and say why the proposal wins. †

## The extract-versus-combine conflict

Martin and Ousterhout's joint record (*aposd-vs-clean-code*) is the primary source. Both value decomposition and both avoid entanglement, "but we disagree on the relative weighting of those two values" (Martin). Ousterhout: the One Thing Rule "lacks guardrails and will lead to over-decomposition." Martin: "if I must err, I'd rather err on the side of decomposition." Ousterhout also argues TDD "discourages good design"; that is not a finding in this lens.

The test both accept: an extracted piece earns its place when its interface is simpler than its body and understanding it doesn't need the other piece. When this lens proposes combining or inlining code that the responsibilities or listen-to-tests lens would extract or introduce, mark `direction: combine`, `inline` or `remove`, and give the evidence for the test. `restructure` surfaces the conflict and the user decides.

## Where this lens meets the others

- **responsibilities:** Middle Man and Message Chains appear in both lenses; this lens owns pass-throughs and leakage, responsibilities owns where behaviour lives. Extract versus combine is the main conflict.
- **listen-to-tests:** GOOS's small role objects and mocks can produce shallow classes and pass-throughs; GOOS's "Composite Simpler Than the Sum of Its Parts" and deep modules agree on the composite's interface and differ on its insides. When a role exists only to be mocked and only forwards, say so.
- **domain-model:** Conceptual Contours is the domain's say on where to cut. Where a deep module would merge two domain concepts, name both and let the conflict surface.

## Out of scope

- Module, package and service boundaries: report them as **hints** for `/modularity:review` or `/improve-codebase-architecture`. This lens works at class and function scale.
- Writing or editing comments; formatting and style.
- Performance, except where a design choice made for performance leaks into interfaces.
