"""Each eval case's fixture builds the repo its case expects.

Run: python3 -m unittest discover -s evals/tests
Free: no model calls. Run it after editing a fixture.sh.
"""
import os
import re
import subprocess
import tempfile
import unittest

EVALS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(case):
    ws = tempfile.mkdtemp(prefix=f"eval-{case}-")
    home = tempfile.mkdtemp(prefix="eval-home-")
    env = {"PATH": os.environ["PATH"], "HOME": home, "TERM": "dumb"}
    subprocess.run(["bash", os.path.join(EVALS, case, "fixture.sh")], cwd=ws, env=env,
                   check=True, capture_output=True, text=True)
    return ws


def git(ws, *args):
    return subprocess.run(["git", "-C", ws, *args], check=True, capture_output=True, text=True).stdout


def changed(ws):
    return sorted(git(ws, "diff", "--name-only", "base").split())


class Fixtures(unittest.TestCase):
    def test_every_case_has_a_fixture_prompt_and_grader(self):
        cases = [d for d in os.listdir(EVALS)
                 if os.path.isfile(os.path.join(EVALS, d, "case.yaml"))]
        self.assertEqual(sorted(cases), sorted(CASES))
        for case in cases:
            for f in ("fixture.sh", "prompt.md"):
                self.assertTrue(os.path.isfile(os.path.join(EVALS, case, f)), f"{case}/{f}")
            self.assertTrue(os.listdir(os.path.join(EVALS, case, "graders")), case)

    def test_each_fixture_changes_what_its_case_needs(self):
        for case, files in CASES.items():
            with self.subTest(case=case):
                self.assertEqual(changed(build(case)), files)

    def test_conflict_seeds_a_one_line_rule_both_lenses_pull_on(self):
        ws = build("conflict")
        with open(os.path.join(ws, "shop/checkout.py")) as fh:
            checkout = fh.read()
        with open(os.path.join(ws, "GLOSSARY.md")) as fh:
            glossary = fh.read()
        # depth: a one-line method with one caller, its interface as large as its body
        self.assertEqual(checkout.count("def member_price("), 1)
        self.assertEqual(checkout.count("self.member_price("), 1)
        # responsibilities: Marketing's rule sits inside Checkout, apart from Finance's Tax
        self.assertIn("Marketing", glossary)
        # the necessary move: Checkout writes the tax rate out again instead of calling add_tax
        self.assertIn("* 1.2", checkout)
        self.assertNotIn("add_tax", checkout)
        # no ordered steps or shared state that one move could merge away
        self.assertNotIn("def begin(", checkout)

    def test_move_log_cases_commit_their_move_log_in_base(self):
        for case in ("declined", "undo"):
            with self.subTest(case=case):
                ws = build(case)
                logs = git(ws, "ls-tree", "--name-only", "base", "move-log/").split()
                self.assertEqual(len(logs), 1)
                entry = git(ws, "show", f"base:{logs[0]}")
                self.assertRegex(entry, r"(?m)^group: necessary$")
                self.assertNotRegex(entry, r"(?m)^status:")


def graders(case):
    """Each regex grader as (name, pattern, flags, match, path), from its frontmatter."""
    out = []
    gdir = os.path.join(EVALS, case, "graders")
    for name in sorted(os.listdir(gdir)):
        fields = {}
        with open(os.path.join(gdir, name)) as fh:
            front = fh.read().split("---")[1]
        for line in front.splitlines():
            if line.startswith("#") or ":" not in line:
                continue
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
        assert fields["type"] == "regex", (case, name)
        pattern = fields["pattern"]
        assert pattern.startswith("'") and pattern.endswith("'"), (case, name)
        path = re.search(r"path: ([^ }]+)", fields["target"]).group(1)
        out.append((name, pattern[1:-1].replace("''", "'"), fields.get("flags", ""),
                    fields.get("match", "contains"), path))
    return out


def passes(grader, files):
    _, pattern, flags, match, path = grader
    if path not in files:
        return False
    re_flags = (re.M if "m" in flags else 0) | (re.I if "i" in flags else 0)
    found = re.search(pattern, files[path], re_flags) is not None
    return found if match == "contains" else not found


class Graders(unittest.TestCase):
    """Graders pass a right report and fail a wrong one. Samples follow CONTRACT.md."""

    def check(self, case, right, wrongs):
        for g in graders(case):
            self.assertTrue(passes(g, right), f"{case}/{g[0]} rejects the right report")
        for wrong in wrongs:
            self.assertFalse(all(passes(g, wrong) for g in graders(case)),
                             f"{case} accepts a wrong report: {wrong}")

    def test_clean(self):
        self.check("clean", {"review/report.md": REPORT.format(v="verdict: pass", body="")},
                   [{"review/report.md": REPORT.format(v="verdict: change", body="")},
                    {"review/report.md": FAILURE}, {}])

    def test_smell_in_diff(self):
        right = {"review/report.md": REPORT.format(v="verdict: change", body=MOVES_NECESSARY),
                 "review/moves.md": MOVE.format(n="yes", key="Tax rule · combine · shop/tax.py#add_tax")}
        self.check("smell-in-diff", right, [
            {**right, "review/report.md": REPORT.format(v="verdict: advise", body=MOVES_OTHER)},
            {**right, "review/moves.md": MOVE.format(n="yes", key="Invoice · combine · shop/tax.py#add_tax")},
            {**right, "review/moves.md": MOVE.format(n="no", key="Tax · combine · shop/tax.py#add_tax")},
        ])

    def test_smell_outside_diff(self):
        self.check("smell-outside-diff",
                   {"review/report.md": REPORT.format(v="verdict: advise", body=MOVES_OTHER)},
                   [{"review/report.md": REPORT.format(v="verdict: change", body=MOVES_NECESSARY)}])

    def test_declined(self):
        declined = ("## Declined before\n"
                    "- Give tax one owner · key: Tax · combine · shop/tax.py#add_tax"
                    " · declined: Invoice and refund move to billing.\n")
        self.check("declined", {"review/report.md": REPORT.format(v="verdict: pass", body=declined)}, [
            {"review/report.md": REPORT.format(v="verdict: change", body=MOVES_NECESSARY + declined)},
            {"review/report.md": REPORT.format(v="verdict: pass", body="")},
        ])

    def test_conflict(self):
        body = MOVES_NECESSARY + "\n## Conflicts\n\nC1. Checkout: depth combines, responsibilities extracts.\n"
        right = {"review/report.md": REPORT.format(v="verdict: ask", body=body).replace("ask: []", "ask: [1, C1]")}
        self.check("conflict", right, [
            {"review/report.md": REPORT.format(v="verdict: change", body=body)},
            {"review/report.md": REPORT.format(v="verdict: ask", body=MOVES_NECESSARY).replace("ask: []", "ask: [1]")},
        ])

    def test_undo(self):
        # the change itself works against the applied move: no design move needs to say so
        undoes = ("\n## Undoes\n\n"
                  "- U1 · key: Tax Policy · extract · shop/tax.py#TaxPolicy · by: the change"
                  " · how: invoice_total calls add_tax around TaxPolicy\n")

        def report(v, body, ask="[U1]"):
            return {"review/report.md": REPORT.format(v=v, body=body).replace("ask: []", f"ask: {ask}")}

        self.check("undo", report("verdict: ask", MOVES_OTHER + undoes), [
            report("verdict: advise", MOVES_OTHER + undoes, ask="[]"),
            report("verdict: ask", MOVES_OTHER),
            report("verdict: ask", MOVES_OTHER + undoes.replace("TaxPolicy", "Cart")),
        ])

    def test_empty_diff(self):
        self.check("empty-diff", {"review/report.md": FAILURE},
                   [{"review/report.md": REPORT.format(v="verdict: pass", body="")}, {}])


REPORT = """---
{v}
mode: ref
base: abc1234
lenses: [depth]
necessary: []
ask: []
counts: {{moves: 1}}
work: review/.work
---

{body}"""
FAILURE = "---\nfailure: no-change\nmode: ref\nbase: abc1234\n---\n\nThe diff since base is empty.\n"
MOVES_NECESSARY = "## Moves\n\n- [1. Give tax one owner](moves.md#1-give-tax-one-owner) · necessary · verified\n"
MOVES_OTHER = "## Moves\n\n- [1. Give tax one owner](moves.md#1-give-tax-one-owner) · other · unverified\n"
MOVE = "## Necessary moves\n\n### 1. Give tax one owner\nnecessary: {n} · check: keep · after:  · key: {key}\n"

# case -> files `git diff base` must show
CASES = {
    "clean": ["shop/invoice.py"],
    "smell-in-diff": ["shop/invoice.py", "shop/refund.py"],
    "smell-outside-diff": ["shop/cart.py"],
    "declined": ["shop/invoice.py", "shop/refund.py"],
    "conflict": ["shop/checkout.py", "shop/pay.py"],
    "undo": ["shop/invoice.py"],
    "empty-diff": [],
}

if __name__ == "__main__":
    unittest.main()
