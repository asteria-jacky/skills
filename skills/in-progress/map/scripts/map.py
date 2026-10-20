#!/usr/bin/env python3
"""map: object relationships in a scope, as a graph with indicators.

  map.py build  --root DIR --out RUN (--base REF | --paths P [P ...]) [--level high|low] [--label TEXT]
  map.py render --out RUN [--level high|low] [--groups FILE] [--verified FILE] [--questions FILE]
  map.py show   --out RUN (--scope | --checks | --node ID | --edge FROM TO)

Standard library only. Writes graph.json, indicators.json, high.mmd, low.mmd and
map.md into RUN, and prints a short summary.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import extract  # noqa: E402
import graph  # noqa: E402
import render  # noqa: E402

SUMMARY_LIMIT = 2000


def git(root, *args):
    return extract.run(["git"] + list(args), root)


def cmd_build(a):
    root = os.path.abspath(a.root)
    files = extract.list_files(root)
    modules, module_edges, source, notes = extract.detect_modules(root, files)
    nodes, edges, coverage = graph.build(root, files, modules, module_edges, source, notes)

    file_set = set(files)
    if a.base:
        changed = set((git(root, "diff", "--name-only", a.base, "--") or "").split())
        changed |= set((git(root, "ls-files", "--others", "--exclude-standard") or "").split())
        deleted = sorted(f for f in changed if not os.path.exists(os.path.join(root, f))
                         and extract.language_of(f))
        if deleted:
            notes.append("%d deleted file(s) are not mapped: v1 maps the code as it is now." % len(deleted))
        in_files = changed & file_set
        graph.apply_scope(nodes, edges, in_files, changed_files=in_files)
        mode, label = "diff", a.label or "changes since %s" % a.base
    else:
        in_files = graph.scope_files(files, a.paths or ["."])
        graph.apply_scope(nodes, edges, in_files)
        mode, label = "named", a.label or ", ".join(a.paths or ["whole repository"])
    if not in_files:
        notes.append("No code files matched the scope.")

    ind = {"high": graph.indicators(nodes, edges, "high"), "low": graph.indicators(nodes, edges, "low")}
    scoped_modules = [n for n in nodes.values() if n["kind"] == "module" and n["in_scope"]]
    level = a.level or ("low" if len(scoped_modules) <= 1 else "high")

    head = git(root, "rev-parse", "HEAD")
    status = git(root, "status", "--porcelain")
    meta = {"root": root, "commit": head.strip() if head else None, "dirty": bool(status and status.strip()),
            "scope_label": label, "mode": mode, "base": a.base, "paths": a.paths, "level": level,
            "module_source": source, "languages": coverage, "notes": notes,
            "scope_files": len(in_files)}
    os.makedirs(a.out, exist_ok=True)
    write_json(os.path.join(a.out, "graph.json"),
               {"meta": meta, "nodes": [nodes[k] for k in sorted(nodes)], "edges": edges})
    write_json(os.path.join(a.out, "indicators.json"), {"definitions": graph.DEFINITIONS, **ind})
    write_outputs(a.out, meta, nodes, edges, ind, level, {}, {}, "")
    print(summary(a.out, meta, nodes, edges, ind, level))


def cmd_render(a):
    meta, nodes, edges, ind = load(a.out)
    level = a.level or meta["level"]
    groups = read_json(a.groups) if a.groups else {}
    verified = read_json(a.verified) if a.verified else {}
    questions = open(a.questions, encoding="utf-8").read().strip() if a.questions else ""
    write_outputs(a.out, meta, nodes, edges, ind, level, groups, verified, questions)
    print("Rendered %s (level %s)." % (os.path.join(a.out, "map.md"), level))


def cmd_show(a):
    meta, nodes, edges, ind = load(a.out)
    if a.scope:
        by_module = {}
        for n in nodes.values():
            if n["kind"] == "type" and n["in_scope"]:
                by_module.setdefault(graph.module_id(n["id"]), []).append(n)
        for mod in sorted(by_module):
            print("## %s" % mod)
            for n in sorted(by_module[mod], key=lambda x: x["id"]):
                print("- %s%s (%s) %s:%s" % ("* " if n.get("changed") else "", n["name"], n["decl"], n["path"], n["line"]))
    elif a.checks:
        pairs = []
        for level in ("high", "low"):
            for c in ind[level]["cycles"]:
                pairs += list(zip(c["path"], c["path"][1:]))
        for level in ("high", "low"):
            if ind[level]["blast_radius"]:
                chain = ind[level]["blast_radius"][0]["chain"]
                pairs += list(zip(chain, chain[1:]))
        seen = set()
        for p in pairs:
            if p not in seen:
                seen.add(p)
                print_edge(nodes, edges, p[0], p[1])
        if not seen:
            print("Nothing to verify: no cycles and no dependency chains in scope.")
    elif a.node:
        nid = find(nodes, a.node)
        print(json.dumps(nodes[nid], indent=1))
        for e in edges:
            if nid in (e["from"], e["to"]):
                print("%s -[%s x%d%s]-> %s  %s" % (e["from"], e["kind"], e["weight"],
                                                  " ambiguous" if e["ambiguous"] else "", e["to"], " ".join(e["sites"])))
    elif a.edge:
        print_edge(nodes, edges, find(nodes, a.edge[0]), find(nodes, a.edge[1]))


def print_edge(nodes, edges, src, dst):
    for e in edges:
        if e["from"] == src and e["to"] == dst:
            print("%s -> %s  [%s x%d, %s]  %s" % (src, dst, e["kind"], e["weight"], e["confidence"],
                                                 " ".join(e["sites"]) or "(declared by the manifest)"))


def find(nodes, key):
    if key in nodes:
        return key
    hits = sorted(k for k, n in nodes.items() if n["name"] == key or k.endswith("::" + key))
    if len(hits) != 1:
        sys.exit("No unique node for %r: %s" % (key, ", ".join(hits[:10]) or "no match"))
    return hits[0]


def load(out):
    g = read_json(os.path.join(out, "graph.json"))
    ind = read_json(os.path.join(out, "indicators.json"))
    return g["meta"], {n["id"]: n for n in g["nodes"]}, g["edges"], ind


def write_outputs(out, meta, nodes, edges, ind, level, groups, verified, questions):
    cycle_edges = set()
    for c in ind["high"]["cycles"]:
        cycle_edges |= set(zip(c["path"], c["path"][1:]))
    high, _ = render.high_diagram(nodes, edges, cycle_edges)
    low, _ = render.low_diagram(nodes, edges, groups)
    write_text(os.path.join(out, "high.mmd"), high + "\n")
    write_text(os.path.join(out, "low.mmd"), low + "\n")
    write_text(os.path.join(out, "map.md"), render.report(meta, nodes, edges, ind, level, groups, verified, questions))


def summary(out, meta, nodes, edges, ind, level):
    lines = ["map: %s (%s mode, %s level)" % (meta["scope_label"], meta["mode"], level),
             "modules from: %s" % meta["module_source"]]
    langs = ", ".join("%s %d/%d" % (k, v["read"], v["files"]) for k, v in sorted(meta["languages"].items()))
    lines.append("files read: %s" % (langs or "none"))
    lines.append("repo: %d modules, %d types, %d edges (%d ambiguous)" % (
        ind["high"]["nodes"], ind["low"]["nodes"], len(edges), sum(1 for e in edges if e["ambiguous"])))
    lines.append("in scope: %d modules, %d types" % (ind["high"]["in_scope"], ind["low"]["in_scope"]))
    lines.append("cycles touching scope: %d type-level, %d module-level" % (
        len(ind["low"]["cycles"]), len(ind["high"]["cycles"])))
    lv = ind[level]
    if lv["blast_radius"]:
        b = lv["blast_radius"][0]
        lines.append("largest blast radius: %s (%d, %.1f%%)" % (nodes[b["id"]]["name"], b["count"], b["pct"]))
    if "diff" in ind["low"]:
        d = ind["low"]["diff"]
        lines.append("change: %d changed types, %d dependents (%.1f%%)" % (d["changed"], d["blast_radius"], d["pct"]))
    for note in meta["notes"]:
        lines.append("note: " + note)
    lines.append("wrote: %s/{graph.json,indicators.json,high.mmd,low.mmd,map.md}" % out)
    text = "\n".join(lines)
    return text if len(text) <= SUMMARY_LIMIT else text[:SUMMARY_LIMIT - 20] + "\n… (truncated)"


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, data):
    write_text(path, json.dumps(data, indent=1, sort_keys=True) + "\n")


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", default=".")
    b.add_argument("--out", required=True)
    scope = b.add_mutually_exclusive_group()
    scope.add_argument("--base")
    scope.add_argument("--paths", nargs="+")
    b.add_argument("--level", choices=["high", "low"])
    b.add_argument("--label")
    r = sub.add_parser("render")
    r.add_argument("--out", required=True)
    r.add_argument("--level", choices=["high", "low"])
    r.add_argument("--groups")
    r.add_argument("--verified")
    r.add_argument("--questions")
    s = sub.add_parser("show")
    s.add_argument("--out", required=True)
    what = s.add_mutually_exclusive_group(required=True)
    what.add_argument("--scope", action="store_true")
    what.add_argument("--checks", action="store_true")
    what.add_argument("--node")
    what.add_argument("--edge", nargs=2)
    a = p.parse_args(argv)
    {"build": cmd_build, "render": cmd_render, "show": cmd_show}[a.cmd](a)


if __name__ == "__main__":
    main()
