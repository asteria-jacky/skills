"""Mermaid diagrams and the map.md report."""
from __future__ import annotations

import re
from collections import defaultdict

from graph import DEFINITIONS, module_id

NODE_CAP = 25


def safe(text):
    return re.sub(r"[^A-Za-z0-9_]", "_", text).strip("_") or "_"


def label(text):
    return text.replace('"', "'")


def pick(nodes_list, edges, cap=NODE_CAP):
    """Choose which nodes to draw. Returns (shown ids, folded ids)."""
    degree = defaultdict(int)
    for e in edges:
        degree[e["from"]] += 1
        degree[e["to"]] += 1
    ranked = sorted(nodes_list, key=lambda n: (not n.get("changed"), not n["in_scope"], -degree[n["id"]], n["id"]))
    shown = [n["id"] for n in ranked[:cap]]
    folded = [n["id"] for n in ranked[cap:]]
    return shown, folded


def high_diagram(nodes, edges, cycle_edges):
    mods = [n for n in nodes.values() if n["kind"] == "module"]
    partial = not all(n["in_scope"] for n in mods)
    medges = [e for e in edges if e["kind"] == "imports"]
    shown, folded = pick(mods, medges, NODE_CAP - 1 if len(mods) > NODE_CAP else NODE_CAP)
    shown_set = set(shown)
    ids = {m: "m%d" % i for i, m in enumerate(sorted(shown))}
    groups = defaultdict(list)
    for m in sorted(shown):
        groups[nodes[m]["parent"] or "."].append(m)
    lines = ["flowchart LR"]
    for g in sorted(groups):
        lines.append('  subgraph %s["%s"]' % ("g_" + safe(g), label(g)))
        for m in groups[g]:
            mark = " ◆" if partial and nodes[m]["in_scope"] else ""
            lines.append('    %s["%s%s"]' % (ids[m], label(m), mark))
        lines.append("  end")
    if folded:
        lines.append('  folded["+%d more modules"]' % len(folded))
    links, link_index, red = defaultdict(int), {}, []
    for e in medges:
        a = ids.get(e["from"], "folded" if e["from"] not in shown_set else None)
        b = ids.get(e["to"], "folded" if e["to"] not in shown_set else None)
        if a and b and a != b:
            links[(a, b)] += max(e["weight"], 0)
            if (e["from"], e["to"]) in cycle_edges:
                red.append((a, b))
    for i, ((a, b), w) in enumerate(sorted(links.items())):
        link_index[(a, b)] = i
        lines.append("  %s -->%s %s" % (a, "|%d|" % w if w else "", b))
    for a, b in sorted(set(red)):
        lines.append("  linkStyle %d stroke:#d33,stroke-width:2px" % link_index[(a, b)])
    return "\n".join(lines), folded


ARROWS = {"inherits": "<|--", "conforms": "<|.."}


def low_diagram(nodes, edges, groups):
    types = [n for n in nodes.values() if n["kind"] == "type" and n["in_scope"]]
    tedges = [e for e in edges if e["kind"] != "imports" and not e["ambiguous"]]
    shown, folded = pick(types, tedges, NODE_CAP)
    shown_set = set(shown)
    ids = {t: "t%d" % i for i, t in enumerate(sorted(shown))}
    spaces = defaultdict(list)
    for t in sorted(shown):
        spaces[groups.get(t) or module_id(t)].append(t)
    folded_by_space = defaultdict(list)
    for t in folded:
        folded_by_space[groups.get(t) or module_id(t)].append(t)
    lines = ["classDiagram"]
    for space in sorted(set(spaces) | set(folded_by_space)):
        lines.append("  namespace %s {" % safe(space))
        for t in spaces.get(space, []):
            mark = "◆ " if nodes[t].get("changed") else ""
            lines.append('    class %s["%s%s"]' % (ids[t], mark, label(nodes[t]["name"])))
        if folded_by_space.get(space):
            ids["fold:" + space] = "f_" + safe(space)
            lines.append('    class %s["+%d more"]' % (ids["fold:" + space], len(folded_by_space[space])))
        lines.append("  }")
    for t in sorted(shown):
        if nodes[t]["decl"] in ("protocol", "interface", "trait", "enum", "extension"):
            lines.append("  <<%s>> %s" % (nodes[t]["decl"], ids[t]))
    links = defaultdict(int)
    for e in tedges:
        a = ids.get(e["from"]) if e["from"] in shown_set else ids.get("fold:" + (groups.get(e["from"]) or module_id(e["from"])))
        b = ids.get(e["to"]) if e["to"] in shown_set else ids.get("fold:" + (groups.get(e["to"]) or module_id(e["to"])))
        if a and b and a != b:
            links[(a, b, e["kind"])] += e["weight"]
    for (a, b, kind), w in sorted(links.items()):
        if kind in ARROWS:
            lines.append("  %s %s %s" % (b, ARROWS[kind], a))
        else:
            lines.append("  %s ..> %s : %d" % (a, b, w))
    return "\n".join(lines), folded


def where(nodes, node_id):
    n = nodes[node_id]
    return "`%s:%d`" % (n["path"], n["line"]) if n["line"] else "`%s/`" % n["path"]


def edge_lookup(edges):
    table = {}
    for e in edges:
        if not e["ambiguous"]:
            table.setdefault((e["from"], e["to"]), e)
    return table


def status_of(pairs, verified):
    marks = [verified.get("%s -> %s" % p, {}).get("status", "unverified") for p in pairs]
    if any(m == "refuted" for m in marks):
        return "**refuted**"
    if marks and all(m == "verified" for m in marks):
        return "**verified**"
    return "unverified"


def notes_for(pairs, verified):
    out = []
    for p in pairs:
        note = verified.get("%s -> %s" % p, {}).get("note")
        if note:
            out.append("  - `%s → %s`: %s" % (p[0], p[1], note))
    return out


def report(meta, nodes, edges, ind, level, groups, verified, questions):
    lv = ind[level]
    other = ind["low" if level == "high" else "high"]
    unit = "modules" if level == "high" else "types"
    elookup = edge_lookup(edges)
    out = ["# Map: %s" % meta["scope_label"], ""]

    out += ["## Scope and coverage", ""]
    out.append("- **Mode:** %s · **level:** %s · **commit:** `%s`%s" % (
        meta["mode"], level, meta["commit"][:12] if meta["commit"] else "none",
        " (uncommitted changes)" if meta["dirty"] else ""))
    out.append("- **Modules from:** %s" % meta["module_source"])
    out.append("- **Types and edges from:** regex pattern packs, so every type-level edge is `heuristic`: "
               "names are matched, not compiled. Treat the low level as a sketch.")
    out += ["", "| Language | Files | Read | Unreadable | Source |", "|---|---|---|---|---|"]
    for lang, c in sorted(meta["languages"].items()):
        out.append("| %s | %d | %d | %d | %s |" % (lang, c["files"], c["read"], c["unreadable"], c["source"]))
    out.append("")
    for note in meta["notes"]:
        out.append("- %s" % note)
    out.append("")

    out += ["## Headline facts", ""]
    out.append("- **%d** modules and **%d** types in the repo; **%d** %s in scope." % (
        ind["high"]["nodes"], ind["low"]["nodes"], lv["in_scope"], unit))
    out.append("- **Cycles:** %d at type level (%d touching the scope), %d at module level." % (
        ind["low"]["cycles_total"], len(ind["low"]["cycles"]), ind["high"]["cycles_total"]))
    if lv["blast_radius"]:
        b = lv["blast_radius"][0]
        out.append("- **Largest blast radius in scope:** `%s`, %d %s (%.1f%%) depend on it." % (
            nodes[b["id"]]["name"], b["count"], unit, b["pct"]))
    if "diff" in ind["low"]:
        d = ind["low"]["diff"]
        out.append("- **This change:** %d changed types; %d other types (%.1f%%) depend on them." % (
            d["changed"], d["blast_radius"], d["pct"]))
    out.append("")

    cycle_edges = set()
    for c in ind["high"]["cycles"]:
        cycle_edges |= set(zip(c["path"], c["path"][1:]))
    if level == "high":
        diagram, folded = high_diagram(nodes, edges, cycle_edges)
        legend = "◆ in scope · edge labels count type references · red edges close a cycle"
    else:
        diagram, folded = low_diagram(nodes, edges, groups)
        legend = "◆ changed · `<|--` inherits · `<|..` conforms · `..>` references (count)"
    out += ["## Diagram", "", "```mermaid", diagram, "```", "", legend]
    if folded:
        out += ["", "Folded to stay readable (%d): %s" % (
            len(folded), ", ".join("`%s`" % nodes[f]["name"] for f in folded[:30]) + (" …" if len(folded) > 30 else ""))]
    out.append("")

    out += ["## Cycles", "", "_%s_" % DEFINITIONS["cycles"], ""]
    cycles = lv["cycles"]
    if not cycles:
        out.append("No cycles touch the scope at this level.")
    for i, c in enumerate(cycles, 1):
        pairs = list(zip(c["path"], c["path"][1:]))
        out.append("%d. %s · %d %s · %s" % (i, " → ".join("`%s`" % nodes[p]["name"] for p in c["path"]),
                                            len(c["members"]), unit, status_of(pairs, verified)))
        for a, b in pairs:
            e = elookup.get((a, b))
            sites = ", ".join("`%s`" % s for s in e["sites"][:3]) if e and e["sites"] else "declared by the manifest"
            out.append("   - `%s` → `%s` (%s): %s" % (nodes[a]["name"], nodes[b]["name"], e["kind"] if e else "?", sites))
        out += notes_for(pairs, verified)
    if lv["possible_cycles"]:
        out += ["", "**Possible cycles** (closed only by ambiguous edges, where a name matches several types):"]
        for c in lv["possible_cycles"]:
            out.append("- " + " → ".join("`%s`" % nodes[p]["name"] for p in c["path"]))
    if level == "high" and ind["low"]["cycles"]:
        out += ["", "%d type-level cycle(s) touch the scope; run with `--level low` to see them." % len(ind["low"]["cycles"])]
    if level == "low" and ind["high"]["cycles"]:
        out += ["", "Module-level cycles: " + "; ".join(
            " → ".join("`%s`" % p for p in c["path"]) for c in ind["high"]["cycles"])]
    out.append("")

    out += ["## Fan-in and fan-out", "",
            "_Fan-in: %s_" % DEFINITIONS["fan_in"], "", "_Fan-out: %s_" % DEFINITIONS["fan_out"], "",
            "| Fan-in | | Where | Fan-out | | Where |", "|---|---|---|---|---|---|"]
    for k in range(max(len(lv["fan_in"]), len(lv["fan_out"]))):
        cells = []
        for col in (lv["fan_in"], lv["fan_out"]):
            if k < len(col):
                cells += ["`%s`" % nodes[col[k]["id"]]["name"], str(col[k]["value"]), where(nodes, col[k]["id"])]
            else:
                cells += ["", "", ""]
        out.append("| " + " | ".join(cells) + " |")
    if not lv["fan_in"] and not lv["fan_out"]:
        out.append("| none | | | | | |")
    out.append("")

    out += ["## Blast radius", "", "_%s_" % DEFINITIONS["blast_radius"], ""]
    if lv["blast_radius"]:
        out += ["| In scope | Depend on it | % of repo | Where |", "|---|---|---|---|"]
        for b in lv["blast_radius"]:
            out.append("| `%s` | %d | %.1f%% | %s |" % (nodes[b["id"]]["name"], b["count"], b["pct"], where(nodes, b["id"])))
        top = lv["blast_radius"][0]
        pairs = list(zip(top["chain"], top["chain"][1:]))
        if pairs:
            out += ["", "Longest dependency chain to `%s` · %s:" % (nodes[top["id"]]["name"], status_of(pairs, verified)), ""]
            out.append(" → ".join("`%s`" % nodes[p]["name"] for p in top["chain"]))
            out += notes_for(pairs, verified)
    else:
        out.append("Nothing in scope has dependents.")
    out.append("")

    out += ["## Questions", ""]
    out += questions.splitlines() if questions else [
        "<!-- The model writes 3 to 5 questions here, in the domain's words: pointers, not verdicts. -->"]
    out.append("")
    return "\n".join(out)
