"""Extraction: files, modules and raw declarations, standard library only.

Modules come from build manifests when one exists (confidence `exact`) and
from directories otherwise. Declarations, inheritance clauses, imports and
type references come from per-language regex pattern packs (confidence
`heuristic`).
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".build", "build", "dist", "out",
    "Pods", "Carthage", "DerivedData", "vendor", ".venv", "venv", "__pycache__",
    "target", ".next", ".gradle", "coverage", ".swiftpm",
}

LANGUAGES = {
    ".swift": "swift",
    ".ts": "typescript", ".tsx": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".scala": "scala",
    ".cs": "csharp", ".go": "go", ".rs": "rust", ".py": "python", ".rb": "ruby",
    ".php": "php", ".dart": "dart", ".m": "objc", ".mm": "objc", ".h": "c",
    ".hpp": "cpp", ".cpp": "cpp", ".cc": "cpp", ".c": "c",
}

# Build manifests written in a code language: configuration, not code to map.
MANIFEST_FILES = {"Package.swift", "build.gradle.kts", "settings.gradle.kts", "setup.py", "conftest.py"}

# Which pattern pack and which block style each language uses.
PACK = {"swift": "swift", "typescript": "typescript", "javascript": "typescript"}
INDENT_BLOCKS = {"python"}
NO_BRACE_BLOCKS = {"ruby"}
NO_SINGLE_QUOTE_STRINGS = {"swift", "rust"}
HASH_COMMENTS = {"python", "ruby"}

IDENT = re.compile(r"[A-Za-z_$][\w$]*")
TOKEN = re.compile(r"[A-Za-z_$][\w$]*|[{};]")

SWIFT_DECL = re.compile(
    r"(?<![\w.])(class|struct|enum|protocol|actor|extension)\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)")
SWIFT_ALIAS = re.compile(r"(?<![\w.])typealias\s+([A-Za-z_]\w*)")
SWIFT_NOT_NAMES = {
    "func", "var", "let", "subscript", "init", "case", "override", "static", "final",
    "private", "public", "open", "internal", "fileprivate", "convenience", "required",
}
SWIFT_IMPORT = re.compile(
    r"^\s*(?:@[\w]+(?:\([^)]*\))?\s+)*import\s+(?:(?:class|struct|enum|protocol|func|var|let|typealias)\s+)?([\w]+)",
    re.M)

TS_DECL = re.compile(
    r"(?<![\w$.])(class|interface|enum)\s+([A-Za-z_$][\w$]*)|(?<![\w$.])(type)\s+([A-Za-z_$][\w$]*)\s*(?:<[^=]*>)?\s*=")
TS_IMPORT = re.compile(
    r"""(?:import|export)\s[^'"]*?from\s*['"]([^'"]+)['"]|import\s*['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\)|import\(\s*['"]([^'"]+)['"]\s*\)""")

GENERIC_DECL = re.compile(
    r"(?<![\w.])(class|struct|interface|enum|trait|protocol|record|object|union)\s+([A-Za-z_]\w*)")
GO_DECL = re.compile(r"(?<![\w.])type\s+([A-Za-z_]\w*)\s+(struct|interface)\b")
RUST_IMPL = re.compile(r"(?<![\w.])impl(?:\s*<[^>]*>)?\s+([A-Za-z_]\w*)(?:<[^>]*>)?\s+for\s+([A-Za-z_]\w*)")


def run(cmd, cwd, timeout=60):
    """Run a command; return stdout, or None when it is missing or fails."""
    if shutil.which(cmd[0]) is None:
        return None
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return res.stdout if res.returncode == 0 else None


# ---------------------------------------------------------------- files

def list_files(root):
    """Code files under root, as sorted POSIX paths relative to root."""
    out = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], root)
    if out is not None:
        paths = [p for p in out.splitlines() if p]
    else:
        paths = []
        for d, dirs, files in os.walk(root):
            dirs[:] = sorted(x for x in dirs if x not in IGNORED_DIRS and not x.startswith("."))
            for f in files:
                paths.append(os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/"))
    result = []
    for p in paths:
        parts = p.split("/")
        if any(x in IGNORED_DIRS for x in parts[:-1]):
            continue
        if parts[-1] in MANIFEST_FILES:
            continue
        if os.path.splitext(p)[1] in LANGUAGES and os.path.isfile(os.path.join(root, p)):
            result.append(p)
    return sorted(set(result))


def language_of(path):
    return LANGUAGES.get(os.path.splitext(path)[1])


# ---------------------------------------------------------------- modules

def detect_modules(root, files):
    """Return (modules, module_edges, source, notes).

    modules: {name: {"path": dir, "group": str}}
    module_edges: set of (from, to), declared by a manifest.
    """
    notes = []
    for finder in (swiftpm_modules, workspace_modules, go_modules, cargo_modules):
        found = finder(root, notes)
        if found:
            modules, edges, source = found
            if modules:
                return modules, edges, source, notes
    if any(name.endswith(".xcodeproj") for name in os.listdir(root)):
        notes.append("Xcode project found: v1 doesn't read its targets, so modules are directories.")
    return directory_modules(files), set(), "directories", notes


def swiftpm_modules(root, notes):
    if not os.path.isfile(os.path.join(root, "Package.swift")):
        return None
    out = run(["swift", "package", "describe", "--type", "json"], root, timeout=180)
    if out:
        try:
            data = json.loads(out[out.index("{"):])
            modules, edges = {}, set()
            for t in data.get("targets", []):
                path = t.get("path") or "Sources/" + t["name"]
                modules[t["name"]] = {"path": norm_dir(path), "group": norm_dir(path).split("/")[0]}
                for dep in t.get("target_dependencies", []) or []:
                    edges.add((t["name"], dep))
            return modules, edges, "swift package describe"
        except (ValueError, KeyError):
            notes.append("`swift package describe` output unreadable; parsed Package.swift instead.")
    else:
        notes.append("`swift` not available; parsed Package.swift with patterns instead.")
    return parse_package_swift(root)


TARGET_START = re.compile(r"\.(target|executableTarget|testTarget|macro|plugin)\s*\(")


def parse_package_swift(root):
    with open(os.path.join(root, "Package.swift"), encoding="utf-8", errors="replace") as fh:
        text = strip_code(fh.read(), "swift", keep_strings=True)
    modules, deps = {}, {}
    for m in TARGET_START.finditer(text):
        body = balanced(text, m.end() - 1)
        name = re.search(r'name:\s*"([^"]+)"', body)
        if not name:
            continue
        name = name.group(1)
        default = "Tests/" if m.group(1) == "testTarget" else "Sources/"
        path = re.search(r'path:\s*"([^"]+)"', body)
        path = norm_dir(path.group(1) if path else default + name)
        modules[name] = {"path": path, "group": path.split("/")[0]}
        dep_block = re.search(r"dependencies:\s*\[", body)
        names = []
        if dep_block:
            block = balanced(body, dep_block.end() - 1, "[", "]")
            block = re.sub(r"\.product\s*\([^)]*\)", "", block)
            names = re.findall(r'"([^"]+)"', block)
        deps[name] = names
    edges = {(a, b) for a, bs in deps.items() for b in bs if b in modules and b != a}
    return modules, edges, "Package.swift (patterns)"


def balanced(text, start, open_ch="(", close_ch=")"):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]


def workspace_modules(root, notes):
    pkg = os.path.join(root, "package.json")
    if not os.path.isfile(pkg):
        return None
    try:
        with open(pkg, encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError:
        return None
    patterns = data.get("workspaces") or []
    if isinstance(patterns, dict):
        patterns = patterns.get("packages", [])
    if not patterns:
        return None
    modules, manifests = {}, {}
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in IGNORED_DIRS and not x.startswith("."))
        rel = norm_dir(os.path.relpath(d, root))
        if rel and "package.json" in files and any(fnmatch.fnmatch(rel, p.rstrip("/")) for p in patterns):
            try:
                with open(os.path.join(d, "package.json"), encoding="utf-8") as fh:
                    m = json.load(fh)
            except ValueError:
                continue
            name = m.get("name") or rel
            modules[name] = {"path": rel, "group": rel.split("/")[0]}
            manifests[name] = m
    edges = set()
    for name, m in manifests.items():
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            for dep in (m.get(key) or {}):
                if dep in modules and dep != name:
                    edges.add((name, dep))
    return modules, edges, "package.json workspaces"


def go_modules(root, notes):
    if not os.path.isfile(os.path.join(root, "go.mod")):
        return None
    out = run(["go", "list", "-json", "./..."], root, timeout=180)
    if not out:
        notes.append("`go list` unavailable or failed; modules are directories.")
        return None
    decoder, idx, pkgs = json.JSONDecoder(), 0, []
    while idx < len(out):
        while idx < len(out) and out[idx].isspace():
            idx += 1
        if idx >= len(out):
            break
        obj, idx = decoder.raw_decode(out, idx)
        pkgs.append(obj)
    modules, edges = {}, set()
    paths = {p["ImportPath"] for p in pkgs}
    for p in pkgs:
        rel = norm_dir(os.path.relpath(p["Dir"], root))
        modules[p["ImportPath"]] = {"path": rel, "group": rel.split("/")[0] if rel else "."}
        for imp in p.get("Imports", []) or []:
            if imp in paths:
                edges.add((p["ImportPath"], imp))
    return modules, edges, "go list"


def cargo_modules(root, notes):
    if not os.path.isfile(os.path.join(root, "Cargo.toml")):
        return None
    out = run(["cargo", "metadata", "--no-deps", "--format-version", "1"], root, timeout=180)
    if not out:
        notes.append("`cargo metadata` unavailable or failed; modules are directories.")
        return None
    data = json.loads(out)
    modules, names = {}, set()
    for p in data.get("packages", []):
        rel = norm_dir(os.path.relpath(os.path.dirname(p["manifest_path"]), root))
        modules[p["name"]] = {"path": rel, "group": rel.split("/")[0] if rel else "."}
        names.add(p["name"])
    edges = {(p["name"], d["name"]) for p in data.get("packages", [])
             for d in p.get("dependencies", []) if d["name"] in names}
    return modules, edges, "cargo metadata"


def directory_modules(files):
    """Pick the shallowest directory level where code splits into two or more parts."""
    prefix = ""
    for _ in range(3):
        children = sorted({f[len(prefix):].split("/")[0] for f in files
                           if f.startswith(prefix) and "/" in f[len(prefix):]})
        loose = [f for f in files if f.startswith(prefix) and "/" not in f[len(prefix):]]
        if len(children) == 1 and not loose:
            prefix = prefix + children[0] + "/"
            continue
        break
    modules = {}
    for f in files:
        if not f.startswith(prefix):
            continue
        rest = f[len(prefix):]
        path = prefix + rest.split("/")[0] if "/" in rest else prefix.rstrip("/")
        name = path.rsplit("/", 1)[-1] if path else "(root)"
        group = prefix.rstrip("/") or "."
        modules.setdefault(name, {"path": path, "group": group})
    return modules


def norm_dir(path):
    path = path.replace(os.sep, "/").strip("/")
    return "" if path == "." else path


def module_of(path, modules):
    """The module whose directory is the longest prefix of path, or None."""
    best, best_len = None, -1
    for name, m in modules.items():
        d = m["path"]
        if (d == "" or path == d or path.startswith(d + "/")) and len(d) > best_len:
            best, best_len = name, len(d)
    return best


# ---------------------------------------------------------------- source text

def strip_code(text, language, keep_strings=False):
    """Blank out comments (and string contents) keeping newlines and offsets."""
    out = list(text)
    i, n = 0, len(text)
    hash_comments = language in HASH_COMMENTS
    single_quotes = language not in NO_SINGLE_QUOTE_STRINGS
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        three = text[i:i + 3]
        if (two == "//" and not hash_comments) or (c == "#" and hash_comments):
            j = text.find("\n", i)
            j = n if j < 0 else j
            blank(out, i, j)
            i = j
        elif two == "/*" and not hash_comments:
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            blank(out, i, j)
            i = j
        elif three in ('"""', "'''"):
            j = text.find(three, i + 3)
            j = n if j < 0 else j + 3
            if not keep_strings:
                blank(out, i + 3, j - 3)
            i = j
        elif c == '"' or c == "`" or (c == "'" and single_quotes):
            j = i + 1
            while j < n and text[j] != c and not (text[j] == "\n" and c != "`"):
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            if not keep_strings:
                blank(out, i + 1, j - 1)
            i = j
        else:
            i += 1
    return "".join(out)


def blank(out, start, end):
    for k in range(start, min(end, len(out))):
        if out[k] != "\n":
            out[k] = " "


# ---------------------------------------------------------------- declarations

def find_decls(line, language):
    """Declarations starting on a line: list of (pos, kind, name, clause)."""
    found = []
    if PACK.get(language) == "swift":
        for m in SWIFT_DECL.finditer(line):
            if m.group(2).split(".")[0] in SWIFT_NOT_NAMES:
                continue
            found.append((m.start(), m.group(1), m.group(2), swift_clause(line[m.end():])))
        for m in SWIFT_ALIAS.finditer(line):
            found.append((m.start(), "typealias", m.group(1), []))
    elif PACK.get(language) == "typescript":
        for m in TS_DECL.finditer(line):
            if m.group(1):
                found.append((m.start(), m.group(1), m.group(2), ts_clause(line[m.end():])))
            else:
                found.append((m.start(), "type", m.group(4), []))
    else:
        for m in GENERIC_DECL.finditer(line):
            found.append((m.start(), m.group(1), m.group(2), generic_clause(line[m.end():], language)))
        if language == "go":
            for m in GO_DECL.finditer(line):
                found.append((m.start(), m.group(2), m.group(1), []))
        if language == "rust":
            for m in RUST_IMPL.finditer(line):
                found.append((m.start(), "impl", m.group(2), [(m.group(1), "conforms")]))
    found.sort()
    return found


def split_list(text):
    """Split a comma list at top level (ignoring commas inside <>, (), [])."""
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "<([":
            depth += 1
        elif ch in ">)]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    names = []
    for p in parts:
        m = IDENT.search(re.sub(r"<.*", "", p).replace("any ", "").replace("some ", ""))
        if m:
            names.append(m.group(0).split(".")[-1])
    return names


def swift_clause(rest):
    m = re.match(r"\s*(?:<[^>]*>)?\s*:\s*([^{]*)", rest)
    if not m:
        return []
    text = re.split(r"\bwhere\b", m.group(1))[0]
    return [(n, "supertype") for n in split_list(text)]


def ts_clause(rest):
    rest = re.sub(r"^\s*<[^>]*>", "", rest).split("{")[0]
    clause = []
    m = re.search(r"\bextends\s+(.*?)(?=\bimplements\b|$)", rest)
    if m:
        clause += [(n, "inherits") for n in split_list(m.group(1))]
    m = re.search(r"\bimplements\s+(.*)$", rest)
    if m:
        clause += [(n, "conforms") for n in split_list(m.group(1))]
    return clause


def generic_clause(rest, language):
    rest = rest.split("{")[0]
    if language == "python":
        m = re.match(r"\s*\(([^)]*)\)", rest)
        return [(n, "inherits") for n in split_list(m.group(1))] if m else []
    clause = []
    m = re.search(r"\bextends\s+(.*?)(?=\bimplements\b|$)", rest)
    if m:
        clause += [(n, "inherits") for n in split_list(m.group(1))]
    m = re.search(r"\bimplements\s+(.*)$", rest)
    if m:
        clause += [(n, "conforms") for n in split_list(m.group(1))]
    m = re.match(r"\s*(?:<[^>]*>)?\s*(?:\([^)]*\))?\s*:\s*(.*)$", rest)
    if m and not clause:
        clause += [(n, "supertype") for n in split_list(re.split(r"\bwhere\b", m.group(1))[0])]
    return clause


def extract_file(root, path, language):
    """Raw declarations, references and imports from one file.

    Returns {"decls": [...], "refs": [(decl_index, name, line)], "imports": [...]}
    or None when the file can't be read.
    """
    try:
        with open(os.path.join(root, path), encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError:
        return None
    if PACK.get(language) == "swift":
        imports = SWIFT_IMPORT.findall(strip_code(raw, language))
    elif PACK.get(language) == "typescript":
        imports = [next(g for g in m if g) for m in TS_IMPORT.findall(strip_code(raw, language, keep_strings=True))]
    else:
        imports = []
    text = strip_code(raw, language)
    decls, refs = [], []
    stack = []            # (decl_index, depth or indent)
    pending = None        # declaration waiting for its opening brace
    pending_line = 0
    depth = 0
    for lineno, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        if pending is not None and lineno - pending_line > 2:
            pending = None    # no body brace nearby: a body-less declaration
        if language in INDENT_BLOCKS:
            indent = len(line) - len(line.lstrip())
            while stack and indent <= stack[-1][1]:
                stack.pop()
        line_decls = find_decls(line, language)
        di = 0
        for tok in TOKEN.finditer(line):
            while di < len(line_decls) and line_decls[di][0] <= tok.start():
                pos, kind, name, clause = line_decls[di]
                outer = stack[-1][0] if stack else None
                qualified = name if outer is None or kind == "extension" and "." in name \
                    else decls[outer]["qualified"] + "." + name
                decls.append({"name": name.split(".")[-1], "qualified": qualified, "kind": kind,
                              "line": lineno, "clause": clause, "outer": outer})
                idx = len(decls) - 1
                if language in INDENT_BLOCKS:
                    stack.append((idx, len(line) - len(line.lstrip())))
                elif language in NO_BRACE_BLOCKS or kind == "typealias":
                    stack[:] = [(idx, -1)] if language in NO_BRACE_BLOCKS else stack
                    pending = None if kind == "typealias" else pending
                else:
                    pending, pending_line = idx, lineno
                di += 1
            t = tok.group(0)
            if t == "{":
                if pending is not None:
                    stack.append((pending, depth))
                    pending = None
                depth += 1
            elif t == "}":
                depth = max(depth - 1, 0)
                if stack and language not in INDENT_BLOCKS and language not in NO_BRACE_BLOCKS \
                        and stack[-1][1] == depth:
                    stack.pop()
            elif t == ";":
                pending = None
            else:
                owner = pending if pending is not None else (stack[-1][0] if stack else None)
                if owner is not None:
                    refs.append((owner, t, lineno))
        # a typealias owns the rest of its own line
        for pos, kind, name, clause in line_decls:
            if kind == "typealias":
                idx = next(i for i in range(len(decls) - 1, -1, -1)
                           if decls[i]["line"] == lineno and decls[i]["name"] == name)
                for tok in IDENT.finditer(line[pos:]):
                    refs.append((idx, tok.group(0), lineno))
    return {"decls": decls, "refs": refs, "imports": sorted(set(imports))}
