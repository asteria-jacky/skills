"""Build the graph from raw extraction, resolve names, compute indicators."""
from __future__ import annotations

import os
import posixpath
from collections import defaultdict, deque

import extract

ABSTRACT_DECLS = {"protocol", "interface", "trait"}
MAX_SITES = 5


def build(root, files, modules, module_edges, module_source, notes):
    """Return (nodes, edges, coverage, node_files)."""
    raw, coverage = {}, {}
    for path in files:
        lang = extract.language_of(path)
        cov = coverage.setdefault(lang, {"files": 0, "read": 0, "unreadable": 0,
                                         "source": "patterns (" + extract.PACK.get(lang, "generic") + ")"})
        cov["files"] += 1
        result = extract.extract_file(root, path, lang)
        if result is None:
            cov["unreadable"] += 1
            continue
        cov["read"] += 1
        result["module"] = extract.module_of(path, modules) or "(root)"
        result["language"] = lang
        raw[path] = result

    nodes = {}
    for name, m in modules.items():
        nodes[name] = {"id": name, "kind": "module", "decl": None, "name": name, "parent": m["group"],
                       "path": m["path"], "line": None}
    if any(r["module"] == "(root)" for r in raw.values()) and "(root)" not in nodes:
        nodes["(root)"] = {"id": "(root)", "kind": "module", "decl": None, "name": "(root)",
                           "parent": ".", "path": "", "line": None}

    owner, node_files, duplicates = {}, defaultdict(set), 0
    # Pass 1: declared types.
    for path in sorted(raw):
        r = raw[path]
        for i, d in enumerate(r["decls"]):
            if d["kind"] in ("extension", "impl"):
                continue
            tid = r["module"] + "::" + d["qualified"]
            if tid in nodes:
                duplicates += 1
            else:
                outer = r["decls"][d["outer"]] if d["outer"] is not None else None
                parent = owner.get((path, d["outer"])) if outer is not None else r["module"]
                nodes[tid] = {"id": tid, "kind": "type", "decl": d["kind"], "name": d["qualified"],
                              "parent": parent or r["module"], "path": path, "line": d["line"]}
            owner[(path, i)] = tid
            node_files[tid].add(path)

    by_name = defaultdict(list)
    for n in nodes.values():
        if n["kind"] == "type":
            by_name[n["name"].split(".")[-1]].append(n["id"])
            if "." in n["name"]:
                by_name[n["name"]].append(n["id"])
    deps = defaultdict(set)
    for a, b in module_edges:
        deps[a].add(b)
    resolver = Resolver(by_name, nodes, deps, modules, set(raw))

    edges = {}

    def add_edge(src, dst, kind, path, line, ambiguous=False):
        key = (src, dst, kind)
        e = edges.get(key)
        if e is None:
            e = edges[key] = {"from": src, "to": dst, "kind": kind, "weight": 0,
                              "confidence": "heuristic", "ambiguous": ambiguous, "sites": set()}
        e["weight"] += 1
        e["sites"].add((path, line))

    # Pass 2: extensions merge into their type in the same module, else become their own node.
    for path in sorted(raw):
        r = raw[path]
        imports = resolver.imported_modules(path, r)
        for i, d in enumerate(r["decls"]):
            if d["kind"] not in ("extension", "impl"):
                continue
            targets, ambiguous = resolver.resolve(d["qualified"], r["module"], imports)
            same = [t for t in targets if module_id(t) == r["module"]]
            if len(same) == 1 and not ambiguous:
                owner[(path, i)] = same[0]
                node_files[same[0]].add(path)
                continue
            tid = r["module"] + "::" + d["qualified"] + "(extension)"
            if tid not in nodes:
                nodes[tid] = {"id": tid, "kind": "type", "decl": "extension", "name": d["qualified"],
                              "parent": r["module"], "path": path, "line": d["line"]}
            owner[(path, i)] = tid
            node_files[tid].add(path)
            for t in targets:
                add_edge(tid, t, "refs", path, d["line"], ambiguous)

    # Pass 3: inheritance clauses and references.
    unresolved = 0
    for path in sorted(raw):
        r = raw[path]
        imports = resolver.imported_modules(path, r)
        for i, d in enumerate(r["decls"]):
            src = owner.get((path, i))
            for name, hint in d["clause"]:
                targets, ambiguous = resolver.resolve(name, r["module"], imports)
                for t in targets:
                    if t == src:
                        continue
                    kind = hint
                    if hint == "supertype":
                        kind = "conforms" if nodes[t]["decl"] in ABSTRACT_DECLS else "inherits"
                    add_edge(src, t, kind, path, d["line"], ambiguous)
                if not targets:
                    unresolved += 1
        for idx, name, line in r["refs"]:
            if name not in by_name:
                continue
            src = owner.get((path, idx))
            targets, ambiguous = resolver.resolve(name, r["module"], imports)
            for t in targets:
                if t != src:
                    add_edge(src, t, "refs", path, line, ambiguous)

    structural = {(e["from"], e["to"]) for e in edges.values() if e["kind"] != "refs"}
    type_edges = [e for e in edges.values() if not (e["kind"] == "refs" and (e["from"], e["to"]) in structural)]

    # Module edges: declared by the manifest, or aggregated from type edges.
    agg = {}
    for e in type_edges:
        if e["ambiguous"]:
            continue
        a, b = module_id(e["from"]), module_id(e["to"])
        if a != b:
            m = agg.setdefault((a, b), {"weight": 0, "sites": set()})
            m["weight"] += e["weight"]
            m["sites"] |= e["sites"]
    mod_edges = []
    if module_source == "directories":
        for (a, b), m in agg.items():
            mod_edges.append({"from": a, "to": b, "kind": "imports", "weight": m["weight"],
                              "confidence": "heuristic", "ambiguous": False, "sites": m["sites"]})
    else:
        for a, b in module_edges:
            m = agg.get((a, b), {"weight": 0, "sites": set()})
            mod_edges.append({"from": a, "to": b, "kind": "imports", "weight": m["weight"],
                              "confidence": "exact", "ambiguous": False, "sites": m["sites"]})
        undeclared = sum(1 for k in agg if k not in module_edges)
        if undeclared:
            notes.append("%d cross-module reference pair(s) have no manifest dependency; "
                         "they are likely name collisions and are left out of the module level." % undeclared)

    if duplicates:
        notes.append("%d duplicate type declaration(s) merged into the first one found." % duplicates)
    ambiguous = sum(1 for e in type_edges if e["ambiguous"])
    if ambiguous:
        notes.append("%d edge(s) are ambiguous (a name matching several types) and stay out of the indicators." % ambiguous)

    all_edges = []
    for e in type_edges + mod_edges:
        e = dict(e)
        e["sites"] = ["%s:%d" % s for s in sorted(e["sites"])[:MAX_SITES]]
        all_edges.append(e)
    all_edges.sort(key=lambda e: (e["from"], e["to"], e["kind"]))
    for n in nodes.values():
        n["files"] = sorted(node_files.get(n["id"], []))
    return nodes, all_edges, coverage


def module_id(node_id):
    return node_id.split("::", 1)[0]


class Resolver:
    """Name resolution: same module, declared or imported modules, then a unique name."""

    def __init__(self, by_name, nodes, deps, modules, files):
        self.by_name, self.nodes, self.deps, self.modules, self.files = by_name, nodes, deps, modules, files

    def resolve(self, name, from_module, imports):
        cands = sorted(set(self.by_name.get(name, []) or self.by_name.get(name.split(".")[-1], [])))
        if not cands:
            return [], False
        for pool in (
                [c for c in cands if module_id(c) == from_module],
                [c for c in cands if module_id(c) in self.deps.get(from_module, ())],
                [c for c in cands if module_id(c) in imports],
                cands):
            if len(pool) == 1:
                return pool, False
            if len(pool) > 1:
                return pool, True
        return [], False

    def imported_modules(self, path, r):
        mods = set()
        for spec in r["imports"]:
            if r["language"] == "swift":
                if spec in self.modules:
                    mods.add(spec)
                continue
            if spec.startswith("."):
                base = posixpath.normpath(posixpath.join(posixpath.dirname(path), spec))
                for cand in [base] + [base + ext for ext in (".ts", ".tsx", ".js", ".jsx", ".mts", ".d.ts")] + \
                        [base + "/index" + ext for ext in (".ts", ".tsx", ".js")]:
                    if cand in self.files:
                        mods.add(extract.module_of(cand, self.modules) or "(root)")
                        break
            else:
                parts = spec.split("/")
                for name in ("/".join(parts[:2]), parts[0]):
                    if name in self.modules:
                        mods.add(name)
                        break
        return mods


# ---------------------------------------------------------------- scope

def scope_files(files, paths):
    paths = [p.strip("/") for p in paths]
    if not paths or "" in paths or "." in paths:
        return set(files)
    return {f for f in files if any(f == p or f.startswith(p + "/") for p in paths)}


def apply_scope(nodes, edges, in_files, changed_files=None):
    """Mark in_scope (and changed, in diff mode) on every node."""
    for n in nodes.values():
        n["changed"] = False
        n["in_scope"] = False
    for n in nodes.values():
        if n["kind"] == "type" and set(n["files"]) & in_files:
            n["in_scope"] = True
            n["changed"] = changed_files is not None
    if changed_files is not None:
        changed = {n["id"] for n in nodes.values() if n["changed"]}
        for e in edges:
            if e["ambiguous"] or e["kind"] == "imports":
                continue
            if e["from"] in changed:
                nodes[e["to"]]["in_scope"] = True
            if e["to"] in changed:
                nodes[e["from"]]["in_scope"] = True
    scoped_modules = {module_id(n["id"]) for n in nodes.values() if n["kind"] == "type" and n["in_scope"]}
    for n in nodes.values():
        if n["kind"] == "module" and n["id"] in scoped_modules:
            n["in_scope"] = True


# ---------------------------------------------------------------- indicators

def level_graph(nodes, edges, level, include_ambiguous=False):
    kind = "module" if level == "high" else "type"
    ids = sorted(n["id"] for n in nodes.values() if n["kind"] == kind)
    idset = set(ids)
    adj = {i: set() for i in ids}
    for e in edges:
        if e["from"] in idset and e["to"] in idset and e["from"] != e["to"] \
                and (include_ambiguous or not e["ambiguous"]):
            adj[e["from"]].add(e["to"])
    return ids, {k: sorted(v) for k, v in adj.items()}


def strongly_connected(ids, adj):
    """Tarjan's algorithm, iterative. Components of two or more nodes, sorted."""
    index, low, on_stack, stack, comps, counter = {}, {}, set(), [], [], [0]
    for start in ids:
        if start in index:
            continue
        work = [(start, 0)]
        while work:
            v, i = work.pop()
            if i == 0:
                index[v] = low[v] = counter[0]
                counter[0] += 1
                stack.append(v)
                on_stack.add(v)
            succ = adj[v]
            if i < len(succ):
                work.append((v, i + 1))
                w = succ[i]
                if w not in index:
                    work.append((w, 0))
                elif w in on_stack:
                    low[v] = min(low[v], index[w])
                continue
            for w in succ:
                if w in on_stack and index[w] > index[v]:
                    low[v] = min(low[v], low[w])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    comps.append(sorted(comp))
    return sorted(comps, key=lambda c: (-len(c), c[0]))


def cycle_path(members, adj):
    """A shortest cycle through the first member, as a node list ending where it starts."""
    start, inside = members[0], set(members)
    prev, queue = {}, deque()
    for w in adj[start]:
        if w in inside and w not in prev:
            prev[w] = start
            queue.append(w)
    while queue:
        v = queue.popleft()
        if v == start:
            break
        for w in adj[v]:
            if w in inside and w not in prev:
                prev[w] = v
                queue.append(w)
    path, v = [start], prev.get(start)
    while v is not None and v != start:
        path.append(v)
        v = prev.get(v)
    path.append(start)
    return list(reversed(path))


def reverse_closure(node, radj):
    """Every node that depends on `node`, directly or transitively, with BFS parents."""
    seen, queue = {node: None}, deque([node])
    while queue:
        v = queue.popleft()
        for w in radj[v]:
            if w not in seen:
                seen[w] = v
                queue.append(w)
    return seen


def indicators(nodes, edges, level, top=5):
    ids, adj = level_graph(nodes, edges, level)
    in_scope = {i for i in ids if nodes[i]["in_scope"]}
    radj = {i: [] for i in ids}
    for v, ws in adj.items():
        for w in ws:
            radj[w].append(v)
    for v in radj:
        radj[v].sort()

    comps = strongly_connected(ids, adj)
    cycles = [{"members": c, "path": cycle_path(c, adj)} for c in comps if set(c) & in_scope]
    confirmed = {tuple(c) for c in comps}
    _, adj_all = level_graph(nodes, edges, level, include_ambiguous=True)
    possible = [{"members": c, "path": cycle_path(c, adj_all)}
                for c in strongly_connected(ids, adj_all)
                if tuple(c) not in confirmed and set(c) & in_scope]

    def ranked(values):
        rows = sorted(((v, k) for k, v in values.items() if k in in_scope and v > 0), key=lambda x: (-x[0], x[1]))
        return [{"id": k, "value": v} for v, k in rows[:top]]

    fan_in = ranked({i: len(radj[i]) for i in ids})
    fan_out = ranked({i: len(adj[i]) for i in ids})

    total = len(ids)
    blast = {}
    for i in in_scope:
        blast[i] = len(reverse_closure(i, radj)) - 1
    blast_rows = []
    for row in ranked(blast):
        closure = reverse_closure(row["id"], radj)
        far = max(closure, key=lambda k: (depth_of(k, closure), k))
        chain, v = [], far
        while v is not None:
            chain.append(v)
            v = closure[v]
        blast_rows.append({"id": row["id"], "count": row["value"],
                           "pct": round(100.0 * row["value"] / max(total - 1, 1), 1), "chain": chain})

    result = {"nodes": total, "in_scope": len(in_scope), "cycles": cycles, "possible_cycles": possible,
              "cycles_total": len(comps), "fan_in": fan_in, "fan_out": fan_out, "blast_radius": blast_rows}

    changed = sorted(i for i in ids if nodes[i].get("changed"))
    if changed:
        union = set()
        for c in changed:
            union |= set(reverse_closure(c, radj))
        union -= set(changed)
        result["diff"] = {"changed": len(changed), "blast_radius": len(union),
                          "pct": round(100.0 * len(union) / max(total, 1), 1)}
    return result


def depth_of(node, parents):
    d = 0
    while parents[node] is not None:
        node = parents[node]
        d += 1
    return d


DEFINITIONS = {
    "cycles": "Strongly connected components: types (or modules) that depend on each other in a loop. "
              "Martin's Acyclic Dependencies Principle says the dependency graph should have none.",
    "fan_in": "How many distinct types (or modules) depend directly on this one: a hub, risky to change.",
    "fan_out": "How many distinct types (or modules) this one depends on directly: it knows a lot.",
    "blast_radius": "How many types (or modules) depend on this one directly or transitively "
                    "(the reverse transitive closure): how far a change here can ripple.",
}


def exists(root, path):
    return os.path.exists(os.path.join(root, path))
