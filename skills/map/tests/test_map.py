"""Tests for the map scripts. Run: python3 -m unittest discover -s skills/map/tests"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "map.py")
FIXTURES = os.path.join(HERE, "fixtures")


def build(root, *args):
    out = tempfile.mkdtemp(prefix="map-test-")
    res = subprocess.run([sys.executable, SCRIPT, "build", "--root", root, "--out", out] + list(args),
                         capture_output=True, text=True, check=True)
    with open(os.path.join(out, "graph.json")) as fh:
        g = json.load(fh)
    with open(os.path.join(out, "indicators.json")) as fh:
        ind = json.load(fh)
    return out, g, ind, res.stdout


def edge_set(g, kind=None):
    return {(e["from"], e["to"]) for e in g["edges"] if kind is None or e["kind"] == kind}


def isolated_copy(name):
    """Copy a fixture outside the repo so git sees it as its own tree."""
    dst = os.path.join(tempfile.mkdtemp(prefix="map-fx-"), name)
    shutil.copytree(os.path.join(FIXTURES, name), dst)
    return dst


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false"] + list(args),
                   cwd=cwd, check=True, capture_output=True)


class SwiftFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out, cls.g, cls.ind, cls.stdout = build(os.path.join(FIXTURES, "swiftpkg"), "--paths", "Sources/Core")
        cls.nodes = {n["id"]: n for n in cls.g["nodes"]}

    def test_modules_come_from_the_manifest(self):
        modules = sorted(n["id"] for n in self.g["nodes"] if n["kind"] == "module")
        self.assertEqual(modules, ["App", "Core", "CoreTests"])
        self.assertEqual(edge_set(self.g, "imports"), {("App", "Core"), ("CoreTests", "Core")})
        self.assertTrue(all(e["confidence"] == "exact" for e in self.g["edges"] if e["kind"] == "imports"))

    def test_types_and_nesting(self):
        types = sorted(n["id"] for n in self.g["nodes"] if n["kind"] == "type")
        self.assertEqual(types, ["App::App", "App::FileName(extension)", "Core::FileName", "Core::Node",
                                 "Core::Server", "Core::Tree", "Core::Tree.Entry", "CoreTests::TreeTests"])
        self.assertEqual(self.nodes["Core::Tree.Entry"]["parent"], "Core::Tree")

    def test_same_module_extension_merges_into_its_type(self):
        self.assertIn("Sources/Core/Tree.swift", self.nodes["Core::Tree"]["files"])
        self.assertNotIn("Core::Tree(extension)", self.nodes)

    def test_comments_and_strings_are_not_references(self):
        self.assertNotIn(("Core::Node", "Core::Server"), edge_set(self.g))
        tree_server = [e for e in self.g["edges"] if (e["from"], e["to"]) == ("Core::Tree", "Core::Server")]
        self.assertEqual(tree_server[0]["weight"], 1)

    def test_conformance_and_sites(self):
        self.assertIn(("Core::Tree", "Core::Node"), edge_set(self.g, "conforms"))
        for e in self.g["edges"]:
            if e["kind"] != "imports":
                self.assertTrue(e["sites"], e)
                self.assertEqual(e["confidence"], "heuristic")

    def test_cycle_with_its_path(self):
        cycles = self.ind["low"]["cycles"]
        self.assertEqual([c["members"] for c in cycles], [["Core::Server", "Core::Tree"]])
        self.assertEqual(cycles[0]["path"][0], cycles[0]["path"][-1])
        self.assertEqual(self.ind["high"]["cycles"], [])

    def test_fan_in_and_blast_radius(self):
        self.assertEqual(self.ind["low"]["fan_in"][0], {"id": "Core::FileName", "value": 4})
        top = self.ind["low"]["blast_radius"][0]
        self.assertEqual((top["id"], top["count"]), ("Core::FileName", 6))
        self.assertEqual(top["chain"][-1], "Core::FileName")

    def test_ids_have_no_line_numbers(self):
        for n in self.g["nodes"]:
            self.assertNotRegex(n["id"], r":\d")

    def test_summary_is_short(self):
        self.assertLess(len(self.stdout), 2000)


class OtherLanguages(unittest.TestCase):
    def test_typescript_workspaces(self):
        _, g, ind, _ = build(os.path.join(FIXTURES, "tsrepo"))
        self.assertEqual(edge_set(g, "imports"), {("@app/ui", "@app/model")})
        self.assertIn(("@app/model::Order", "@app/model::Document"), edge_set(g, "inherits"))
        self.assertIn(("@app/model::Order", "@app/model::Priced"), edge_set(g, "conforms"))
        self.assertIn(("@app/ui::OrderView", "@app/model::Order"), edge_set(g, "refs"))

    def test_python_without_a_manifest_uses_directories(self):
        _, g, _, _ = build(os.path.join(FIXTURES, "plain"))
        self.assertEqual(g["meta"]["module_source"], "directories")
        self.assertIn(("shipping::Label", "shipping::Parcel"), edge_set(g, "inherits"))
        self.assertIn(("billing::Invoice", "shipping::Parcel"), edge_set(g, "refs"))
        self.assertNotIn(("shipping::Parcel", "billing::Invoice"), edge_set(g))


class Stability(unittest.TestCase):
    def test_runs_are_byte_identical(self):
        root = os.path.join(FIXTURES, "swiftpkg")
        a, b = build(root)[0], build(root)[0]
        for name in ("graph.json", "indicators.json", "map.md"):
            with open(os.path.join(a, name)) as fa, open(os.path.join(b, name)) as fb:
                self.assertEqual(fa.read(), fb.read(), name)

    def test_ids_survive_moving_code_within_a_file(self):
        root = isolated_copy("swiftpkg")
        before = {n["id"] for n in build(root)[1]["nodes"]}
        path = os.path.join(root, "Sources/Core/Server.swift")
        with open(path) as fh:
            text = fh.read()
        with open(path, "w") as fh:
            fh.write("\n\n\n" + text)
        after = {n["id"] for n in build(root)[1]["nodes"]}
        self.assertEqual(before, after)


class DiffMode(unittest.TestCase):
    def test_changed_types_and_one_hop_neighbours(self):
        root = isolated_copy("swiftpkg")
        git(root, "init", "-q")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "init")
        with open(os.path.join(root, "Sources/Core/Server.swift"), "a") as fh:
            fh.write("\n// touched\n")
        _, g, ind, _ = build(root, "--base", "HEAD")
        nodes = {n["id"]: n for n in g["nodes"]}
        self.assertEqual(g["meta"]["mode"], "diff")
        self.assertEqual(sorted(k for k, n in nodes.items() if n.get("changed")), ["Core::Server"])
        scoped = sorted(k for k, n in nodes.items() if n["kind"] == "type" and n["in_scope"])
        self.assertEqual(scoped, ["Core::FileName", "Core::Server", "Core::Tree"])
        self.assertEqual(ind["low"]["diff"]["changed"], 1)
        self.assertGreater(ind["low"]["diff"]["blast_radius"], 0)


class Rendering(unittest.TestCase):
    def test_large_scope_folds_to_the_cap(self):
        root = tempfile.mkdtemp(prefix="map-big-")
        for m in range(4):
            os.makedirs(os.path.join(root, "mod%d" % m))
            for t in range(300):
                with open(os.path.join(root, "mod%d" % m, "T%d_%d.swift" % (m, t)), "w") as fh:
                    fh.write("class T%d_%d { var next: T%d_%d? }\n" % (m, t, m, (t + 1) % 300))
        out, g, ind, stdout = build(root, "--level", "low")
        self.assertEqual(ind["low"]["nodes"], 1200)
        self.assertLess(len(stdout), 2000)
        with open(os.path.join(out, "low.mmd")) as fh:
            classes = [l for l in fh if l.strip().startswith("class ")]
        self.assertLessEqual(len(classes), 25 + 4)
        with open(os.path.join(out, "map.md")) as fh:
            self.assertIn("Folded to stay readable", fh.read())

    def test_render_applies_groups_verification_and_questions(self):
        out = build(os.path.join(FIXTURES, "swiftpkg"), "--paths", "Sources/Core")[0]
        groups, verified, questions = (os.path.join(out, n) for n in ("g.json", "v.json", "q.md"))
        with open(groups, "w") as fh:
            json.dump({"Core::Tree": "File Tree", "Core::Server": "Hub Connection"}, fh)
        with open(verified, "w") as fh:
            json.dump({"Core::Server -> Core::Tree": {"status": "verified", "note": "weak back-reference"},
                       "Core::Tree -> Core::Server": {"status": "verified"}}, fh)
        with open(questions, "w") as fh:
            fh.write("- Should the server know the tree?")
        subprocess.run([sys.executable, SCRIPT, "render", "--out", out, "--groups", groups,
                        "--verified", verified, "--questions", questions], check=True, capture_output=True)
        with open(os.path.join(out, "map.md")) as fh:
            text = fh.read()
        self.assertIn("namespace File_Tree", text)
        self.assertIn("**verified**", text)
        self.assertIn("weak back-reference", text)
        self.assertIn("Should the server know the tree?", text)


if __name__ == "__main__":
    unittest.main()
