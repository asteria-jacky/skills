---
name: map
description: Map the object relationships in a change, a module or a named scope, at module or type level, with indicators (cycles, fan-in/fan-out, blast radius) that point at structural problems.
disable-model-invocation: true
argument-hint: "[base-ref | scope] [--level high|low]"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*)
---

# Map

Draw the **object relationships** in a scope as a graph, and point at the places worth a look. The script does all the counting, the same way every run; you **interpret** (name the components in the domain's language) and **verify** (check the edges behind each headline before it's reported).

The map is a **sketch**: types and edges come from regex pattern packs that match names rather than compile code, so an edge can be a name collision. That's why step 4 exists.

## Process

### 1. Pin the scope

Without an argument, the scope is the diff against the merge-base with the default branch (`git merge-base HEAD origin/HEAD`, else `main`/`master`).

With an argument, try it as a git ref first: if `git rev-parse <arg>` resolves, it's the base point (**diff mode**: the changed types plus their one-hop neighbours).

Otherwise it's a **named scope**: a module, directory or feature name like "Log module" or "FileBrowser". Find the directories or files that hold it (`ls`, `rg -l`), and confirm them with the user if the match is uncertain.

Pass `--level` through when the user gave it. Without it, the script picks **low** (types) for a scope inside one module, **high** (modules) otherwise.

Done when you hold either a base ref or a list of paths.

### 2. Build

```
RUN=$(mktemp -d -t map-XXXXXX)
python3 ${CLAUDE_SKILL_DIR}/scripts/map.py build --root <repo root> --out "$RUN" (--base <ref> | --paths <path> ...) [--level high|low] [--label "<scope in the user's words>"]
```

It prints a summary and writes `graph.json`, `indicators.json`, `high.mmd`, `low.mmd` and a draft `map.md` into the run folder. Tell the user the run folder's path. Read detail with `map.py show` (below) or `jq` on the JSON; never read `graph.json` whole.

If the summary says no files matched, fix the scope and build again.

### 3. Name the components (low level)

Skip at the high level.

`python3 ${CLAUDE_SKILL_DIR}/scripts/map.py show --out "$RUN" --scope` lists the in-scope types by module. Group them into **components**: related functionality behind one interface, named in the domain's language (`GLOSSARY.md` terms when it exists). A component isn't necessarily a folder; aim for three to seven. Write `$RUN/groups.json`, mapping each type id to its component name:

```json
{"Core::FileStoreTree": "File Tree", "Core::FileStoreFolder": "File Tree", "Core::GravioServer": "Hub Connection"}
```

Types you leave out stay under their module's name.

### 4. Verify the headlines

`python3 ${CLAUDE_SKILL_DIR}/scripts/map.py show --out "$RUN" --checks` lists every edge the report's headlines rest on, with its `path:line` sites: each edge on a cycle's path, and each edge on the longest chain behind the top blast radius.

For each edge, read the code at its sites and decide:

- **verified**: the source type really uses the target type there.
- **refuted**: it doesn't: a different type with the same name, a local variable, a generic parameter. Say what it really is.

Write `$RUN/verified.json`, keyed `"<from> -> <to>"`:

```json
{"Core::Server -> Core::Tree": {"status": "verified", "note": "weak back-reference to report progress"},
 "Core::Tree -> Core::Logger": {"status": "refuted", "note": "Logger here is os.Logger, not Core's"}}
```

Done when every edge `--checks` listed has a status. A cycle with a refuted edge is not a cycle; say so rather than drop it.

### 5. Ask the questions

Write `$RUN/questions.md`: three to five questions the map raises, in the domain's words, each pointing at a `path:line`. They are pointers, not verdicts: "Should the Hub Connection know about the File Tree, or only report progress to it?" rather than "Server must not reference Tree". Indicators are questions to ask, never targets to optimise.

### 6. Render and report

```
python3 ${CLAUDE_SKILL_DIR}/scripts/map.py render --out "$RUN" --groups "$RUN/groups.json" --verified "$RUN/verified.json" --questions "$RUN/questions.md"
```

Leave out the flags for files you didn't write. Then show the user `map.md`: its headline facts, the diagram, the cycles with their verification, and the questions; give the path to the full report.

Done when every cycle and chain in `map.md` is marked verified, refuted or unverified, and the user can read the report without opening the code.

## When the map looks wrong

- **Modules look wrong.** The script reads `Package.swift` (or `swift package describe` when Swift is installed), package.json workspaces, `go list` and `cargo metadata`. Without a manifest, including Xcode projects, it uses directories, and says so under **Scope and coverage**.
- **Too few types for a language.** Swift and TypeScript/JavaScript have their own pattern packs; other languages use a generic one that finds declarations and references but little inheritance. Say so in the report rather than fill gaps by hand.
- **A big scope.** Diagrams cap at 25 nodes and fold the rest, listing what was folded. Narrow the scope or switch level rather than read more of the graph.
