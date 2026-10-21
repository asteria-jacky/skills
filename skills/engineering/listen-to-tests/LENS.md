# Listen to the tests

_Freeman & Pryce, Growing Object-Oriented Software, Guided by Tests (GOOS), and Freeman, Pryce, Mackinnon & Walnes, "Mock Roles, not Objects" (OOPSLA 2004)._

## Goal

Mock objects support good design "by guiding the discovery of a coherent system of types within a code base" (Freeman, Pryce, Mackinnon & Walnes, "Mock Roles, not Objects", the authors' summary). "The qualities that make an object easy to test also make our code responsive to change" (GOOS ch. 20) †.

This lens usually counts `test-setup` (setup lines, mocks and expectations per test). The design effect behind a test signal is usually a `reasons-to-change` or `places-to-change` count in the production code. The measures are defined in `shared/FINDINGS.md`.

When a test is hard to write, hard to read, or breaks for reasons unrelated to what it checks, that **test pain** is feedback on the production design. Ask _why_ the test is hard, not _how_ to make it pass. The answer is usually a missing object, a role nobody named, or a responsibility in the wrong place. GOOS ch. 20 "Listening to the Tests" is the catalogue; the paper supplies the reasoning: mock objects are "really a technique for identifying types in a system based on the roles that objects play".

Every finding is a judgement call: name the smell ("possible Bloated Constructor"), never a verdict. A repo's documented test standards and ADRs override this lens.

Items marked † come from the book's chapter text, which wasn't available to verify; the section titles are verified. Treat † wording as a paraphrase.

## How to read

1. **Read the tests first.** Read the test files for the scope before the production code: the tests show how the code is _used_, and where using it hurts.
2. **Name the test style.** Most suites lean one way:
   - **Mockist** (the GOOS style): collaborators are mocks or test doubles, and tests assert on interactions.
   - **Classicist** (Fowler's "classic TDD"): real collaborators, and tests assert on resulting state.

   Read the pain in the suite's own style, and recommend changes within it. Converting a suite from one style to the other is never a finding.
3. **Collect signals.** Walk the catalogue below, test file by test file. Count: "9 of 12 tests repeat this setup" is evidence; "setup is long" is not.
4. **Diagnose each signal.** The same pain has two possible causes (paper §4.4): the test over-specifies, or the object structure is wrong. "Re-examine the code and see if either the specification should be weakened, or the object structure is wrong and should be changed." Say which, and why:
   - **Over-specified test**: it checks "features that are an artefact of the implementation, not an expression of some requirement". The fix is in the test, and the finding is a pinned test, not a design change.
   - **Wrong structure**: the pain persists however carefully the test is written. The fix is in the production code.
5. **Trace to production code** and name what is missing: the role, the value, the object the tests keep reaching for. That name is the finding's `concept`.

## Catalogue: design signals

GOOS ch. 20's smells, each with what it looks like, what it means, and the remedy. Paper guidelines are quoted where they back the book.

### Can't replace a dependency

_GOOS ch. 20 "I Need to Mock an Object I Can't Replace (without Magic)"; paper §4.9 "Instantiating new objects"._

- **Looks like:** tests reach for static methods, globals, singletons or the system clock; tests use bytecode-level mocking tools; production code calls `new` on a collaborator, or `Date.now()`, inside the logic under test.
- **Means:** a hidden dependency. The object isn't context-independent, so it can't be tested, or reused, apart from its environment.
- **Remedy:** make the dependency explicit and pass it in. The paper: "The only solution is to intervene in the creation of the object, either by passing an instance in or by wrapping the call to new… The factory object often represents a useful concept in the domain, such as the Clock." Look for that concept: the extracted collaborator often deserves a domain name.

### Logging is a feature

_GOOS ch. 20 "Logging Is a Feature"._

- **Looks like:** tests can't check what gets logged, or production logic is threaded with logger calls the tests ignore.
- **Means:** two kinds of logging are mixed. **Support logging** (what operators rely on) is a requirement; **diagnostic logging** (for developers) is not. †
- **Remedy:** put support logging behind a notification role named for what happened in the domain, and test it like any other collaborator. Keep diagnostic logging separate. †

### Mocking concrete classes

_GOOS ch. 20 "Mocking Concrete Classes"; paper §2.1._

- **Looks like:** mocks or stubs of classes rather than interfaces; partial mocks; overriding methods in test subclasses.
- **Means:** an unnamed relationship. The caller depends on a _role_ the collaborator plays, but the code names only the class.
- **Remedy:** extract an interface named for the role the caller needs, from the caller's point of view. TDD with mocks yields "a system of narrow interfaces each of which defines a role in an interaction between objects, rather than wide interfaces that describe all the features provided by a class" (paper). Name the role in domain terms.

### Mocking values

_GOOS ch. 20 "Don't Mock Values"; paper §4.5 "Dont use mocks to test boundary objects"._

- **Looks like:** mocks of immutable data, IDs, money, dates, records, or objects with no collaborators of their own.
- **Means:** a misclassified object, or a value that is painful to construct. Values "are immutable instances that model fixed quantities. They have no individual identity" (GOOS ch. 2). An object with "no relationships to other objects… only needs to make assertions about values returned from its methods" (paper; here "boundary objects" means objects with no collaborators, not system boundaries).
- **Remedy:** use real instances. If they are hard to build, that is its own signal; see **Construction boilerplate**.

### Bloated constructor

_GOOS ch. 20 "Bloated Constructor"; paper §4.8 "Too Many Mocks"._

- **Looks like:** constructors with many parameters (more than about four collaborators is worth a look); long setup in every test; several collaborators that always appear together.
- **Means:** several responsibilities in one object, or collaborators that form a concept nobody named.
- **Remedy:** group collaborators that travel together into a new object named for what they do together; split the object along its responsibilities. The paper: "the solution might be to change misaligned responsibilities, or to introduce an intermediate role… the object under test is too large and should be broken up."

### Confused object

_GOOS ch. 20 "Confused Object"; GOOS ch. 6 "No And's, Or's, or But's"._

- **Looks like:** one test class covering unrelated features; test names that fall into clusters sharing no setup; describing the object needs "and" or "or".
- **Means:** too many responsibilities.
- **Remedy:** split the object along the clusters the tests reveal. The clusters are the evidence: list them.

### Too many dependencies

_GOOS ch. 20 "Too Many Dependencies"; GOOS ch. 6 "Object Peer Stereotypes"._

- **Looks like:** a constructor demanding collaborators the object can work without.
- **Means:** not every peer is a true dependency. GOOS distinguishes **dependencies** (the object can't work without them), **notifications** (peers told about what happens) and **adjustments** (peers that tune behaviour). †
- **Remedy:** only true dependencies go in the constructor. Notifications and adjustments get sensible defaults and can be set afterwards. †

### Too many expectations

_GOOS ch. 20 "Too Many Expectations"; GOOS ch. 24 "Precise Expectations"; paper §4.4 "Specify as little as possible in a test"._

- **Looks like:** tests with many interaction expectations on unrelated collaborators (more than about three is worth a look); hard to tell which expectations matter.
- **Means:** the object does too much, _or_ the test over-specifies. Diagnose which (see **How to read**, step 4).
- **Remedy:** if the test over-specifies, distinguish allowances (calls that may happen: typically queries) from expectations (calls that must happen: typically commands). † If the object does too much, split it as for **Bloated constructor**. "A specification should be as precise as possible, but not more precise" (paper).

### Asking instead of telling

_GOOS ch. 2 "Tell, Don't Ask" and "But Sometimes Ask"; paper §4.2 "Dont use getters", §4.7 "Only mock your immediate neighbours"._

- **Looks like:** tests stubbing getters on a collaborator so the object under test can decide something; stubs returning stubs; getter chains ("train wrecks") in production code.
- **Means:** a decision sits outside the object that holds the data. "Getters expose implementation, which increases coupling between objects and allows responsibilities to be left in the wrong module" (paper). An object that "has to navigate a network of objects in its implementation is likely to be brittle" (paper).
- **Remedy:** move the decision to where the data is, and tell that object what to do: "the calling object should describe what it wants in terms of the role that its neighbor plays, and let the called object decide how" (GOOS ch. 2). For navigation, "introduce a role to bridge between the object and its surroundings" (paper).
- **Not a finding:** GOOS asks too: "when getting information from values and collections, or when using a factory… Occasionally… when searching or filtering." A query that describes the caller's intent is fine. Flag asking only when the decision belongs inside the object being asked.

### Mocks with behaviour

_Paper §4.6 "Dont add behaviour"._

- **Looks like:** fakes or stubs with real logic: computing results, keeping state across calls, branching on arguments.
- **Means:** "an urge to start adding real behaviour to a mock object is usually a symptom of misplaced responsibilities" (paper). The logic the fake needs is logic some real object is missing.
- **Remedy:** find the object that should own that behaviour, and give it there.

### Mocking types you don't own

_Paper §4.1 "Only Mock Types You Own"; GOOS ch. 8 "Only Mock Types That You Own"._

- **Looks like:** mocks of library, framework, SDK or runtime types; tests that replay a third-party API's call sequence.
- **Means:** the code speaks the library's language where it should speak its own. Programmers "should not write mocks for fixed types, such as those defined by the runtime or external libraries. Instead they should write thin wrappers" (paper).
- **Remedy:** introduce an adapter named in domain terms, owned by this code; mock that, and test the adapter against the real library in an integration test (GOOS ch. 8 "Mock Application Objects in Integration Tests").

### Classicist-suite signals

GOOS writes from the mockist side, but its thesis applies to any suite. In a classicist suite the same design problems hurt differently:

- **Fixture graphs**: building many real objects to test one. The object under test depends on too much (see **Bloated constructor**).
- **Reaching into state**: tests setting private fields, or asserting through chains of getters. Information is in the wrong place (see **Asking instead of telling**).
- **Collateral breakage**: tests that fail when an unrelated collaborator changes. `git log` showing a test file changing alongside unrelated production files is the evidence. The test depends on details it doesn't check.

## Catalogue: test-side signals

These are fixed mostly in the tests. They still carry a design hint, and they decide the `tests` field of every finding: which tests will break, and whether they are pinned.

- **Names restate methods** (GOOS ch. 21 "Test Names Describe Features"): `testAddLine` rather than "rejects a line in a different currency". The suite has no domain vocabulary for the behaviour, which is a hint for the domain model too.
- **Construction boilerplate** (GOOS ch. 22 "Test Data Builders", "Emphasizing the Domain Model with Factory Methods"): the same object construction copied across tests. Remedy: builders or factory methods named in domain terms. A builder that is hard to write means the domain object is hard to build: a design signal.
- **Pinned to representation** (GOOS ch. 24 "Test for Information, Not Representation"): assertions on `toString()`, serialised formats, call order that doesn't matter, private structure. These are **pinned tests**: a restructure will break them, and that's expected. Name them in each finding's `tests` field.
- **Test sprawl**: many shallow tests around a cluster a restructure would deepen. Note that they can fold into fewer tests through the new interface.
- **Untested code**: a finding touching code no test exercises. Write `untested` so the user can weigh the risk.

## Where this lens meets the others

Name the `concept` so these overlaps merge into one move:

- **Responsibilities:** Bloated Constructor and Confused Object are the test-side view of Large Class and Divergent Change; Asking instead of telling is Feature Envy seen from the test.
- **Domain model:** the role, value or adapter a test keeps reaching for is often a domain concept with no class. Evans's **Assertions** ("State post-conditions of operations and invariants of classes and aggregates. If assertions cannot be coded directly in your programming language, write automated unit tests for them") makes the tests the place the model's rules live.
- **Depth:** GOOS's remedies add small role objects; Ousterhout warns against shallow classes and pass-through methods. When your remedy introduces a role whose interface would be as complex as what it hides, or that would only forward calls, say so in the finding and mark `direction: introduce` so `restructure` can surface the conflict.

## Out of scope

- Converting the suite between mockist and classicist styles, or recommending a mocking library.
- Mocks used to isolate third-party code: the paper finds this "less interesting… than is widely thought". The finding is the missing adapter, if any.
- Test coverage percentages, test speed and flaky infrastructure, unless the flakiness traces to a hidden dependency (see **Can't replace a dependency**).

## It's working if

- Every Strong finding shows a counted effect, and its evidence names the tests and lines counted.
- Each finding says whether the fix belongs in the test (over-specified) or in the production code (wrong structure).
- Each finding names the role, value or object the tests keep reaching for, not only the test that hurts.
- Recommendations stay within the suite's own test style.
