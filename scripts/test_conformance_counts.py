#!/usr/bin/env python3
"""Tests for scripts/check_conformance_counts.py. python3 standard library and git only.

Each phrasing the check reads is built here in a scratch tree and checked
against a scratch aip-conformance suite: a git repository whose commits ship
fixtures of a known number and fixtureType. A stated count that differs from
the suite at the commit it names is asserted to exit 1 naming the file, the
line and the kind of count. The delivered docs/use-cases.md is asserted to
state three counts at one named commit that agree with each other, and the
delivered README.md and docs/ pass against a suite of the shape they state.

Set AIP_CONFORMANCE_SUITE to a git clone of opena2a-standards/aip-conformance
to also check the delivered documents against the real suite; that test is
skipped otherwise.

Runs on its own:
    python3 scripts/test_conformance_counts.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent
CHECK = SCRIPTS / "check_conformance_counts.py"
sys.path.insert(0, str(SCRIPTS))

import check_conformance_counts as counts

LINK = "[aip-conformance](https://github.com/opena2a-standards/aip-conformance)"


def sentence(total: int, challenge_response: int, trust_score: int, commit: str | None = None) -> str:
    """docs/use-cases.md with the count sentence on line 3; with no commit, the sentence as it read before."""
    at = f" at commit `{commit}`" if commit else ""
    return (
        "# Use cases\n\n"
        f"Why you can check this yourself: {LINK}, {total} byte-pinned fixtures{at} "
        f"({challenge_response} challenge-response transcripts, {trust_score} trust-score compositions) "
        "with Go and Python verifiers.\n"
    )


class CountsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="aip-conformance-counts-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # Only what git needs, no user or system git configuration, and no
        # repository found above the scratch directory.
        self.env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.tmp),
            "GIT_CEILING_DIRECTORIES": os.path.realpath(self.tmp),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "fixture author",
            "GIT_AUTHOR_EMAIL": "author@example.invalid",
            "GIT_COMMITTER_NAME": "fixture author",
            "GIT_COMMITTER_EMAIL": "author@example.invalid",
        }
        self.suite = self.tmp / "aip-conformance"
        self.suite.mkdir()
        self.git("init", "-q")
        self.trees = 0

    def git(self, *args: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(self.suite), *args],
            env=self.env, capture_output=True, text=True, check=True,
        )
        return proc.stdout.strip()

    def commit(self, challenge_response: int = 14, trust_score: int = 3, untyped: int = 0,
               extra: dict[str, str] | None = None) -> str:
        """Commit a fixtures/ tree of this shape to the scratch suite; return its short id."""
        fixtures = self.suite / "fixtures"
        shutil.rmtree(fixtures, ignore_errors=True)
        fixtures.mkdir()
        shapes = [("challenge-response", "challengeResponse", challenge_response),
                  ("trust-score", "trustScoreComposition", trust_score),
                  ("other", None, untyped)]
        for prefix, fixture_type, number in shapes:
            for index in range(number):
                body = {"fixtureType": fixture_type} if fixture_type else {"name": prefix}
                (fixtures / f"{prefix}-{index}.json").write_text(json.dumps(body) + "\n")
        for name, text in (extra or {}).items():
            path = self.suite / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.git("add", "--all")
        self.trees += 1
        self.git("commit", "-q", "--allow-empty", "-m", f"tree {self.trees}")
        return self.git("rev-parse", "--short=7", "HEAD")

    def tree(self, use_cases: str | None, files: dict[str, str] | None = None) -> Path:
        """A scratch tree holding docs/use-cases.md (unless None) and any other files given."""
        root = self.tmp / f"tree-{len(list(self.tmp.glob('tree-*')))}"
        (root / "docs").mkdir(parents=True)
        if use_cases is not None:
            (root / "docs" / "use-cases.md").write_text(use_cases)
        for name, text in (files or {}).items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        return root

    def run_check(self, root: Path, suite: Path | str | None = None) -> tuple[int, str]:
        proc = subprocess.run(
            [sys.executable, "-B", str(CHECK), "--root", str(root), "--suite", str(suite or self.suite)],
            env=self.env, capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout + proc.stderr

    def assertFails(self, root: Path, *reported: str, suite: Path | str | None = None) -> None:
        code, out = self.run_check(root, suite)
        self.assertEqual(code, 1, out)
        for text in reported:
            self.assertIn(text, out)

    def assertPasses(self, root: Path, *reported: str, suite: Path | str | None = None) -> str:
        code, out = self.run_check(root, suite)
        self.assertEqual(code, 0, out)
        for text in reported:
            self.assertIn(text, out)
        return out


class DeliveredTest(CountsTest):
    def stated(self) -> counts.Part:
        text = (REPO / "docs" / "use-cases.md").read_text(encoding="utf-8")
        stated = [part for part in counts.parts(text) if part.suite == counts.SUITE and part.counts]
        self.assertEqual(len(stated), 1, "docs/use-cases.md states the aip-conformance counts once")
        self.assertTrue(stated[0].commits, "the aip-conformance counts name no commit")
        return stated[0]

    def delivered_tree(self, named: str, commit: str) -> Path:
        """README.md and docs/ as delivered, with the named suite commit replaced by a scratch one."""
        files = {}
        for path in [REPO / "README.md", *sorted((REPO / "docs").rglob("*.md"))]:
            files[path.relative_to(REPO).as_posix()] = path.read_text(encoding="utf-8").replace(named, commit)
        return self.tree(None, files)

    def test_the_delivered_page_states_three_counts_at_one_named_commit_that_agree(self):
        part = self.stated()
        self.assertEqual(len({commit for commit, _ in part.commits}), 1, part.commits)
        values = {kind: value for kind, value, _ in part.counts}
        self.assertEqual(sorted(values), sorted(counts.KINDS))
        self.assertEqual(values["fixtures"],
                         values["challenge-response fixtures"] + values["trust-score fixtures"])

    def test_the_delivered_documents_pass_against_a_suite_of_the_shape_they_state(self):
        part = self.stated()
        values = {kind: value for kind, value, _ in part.counts}
        commit = self.commit(values["challenge-response fixtures"], values["trust-score fixtures"])
        self.assertPasses(self.delivered_tree(part.commits[0][0], commit), "3 stated value(s) checked")

    def test_the_delivered_documents_fail_against_a_suite_that_differs_at_the_named_commit(self):
        part = self.stated()
        values = {kind: value for kind, value, _ in part.counts}
        line = next(line for kind, _, line in part.counts if kind == "fixtures")
        commit = self.commit(values["challenge-response fixtures"] + 2, values["trust-score fixtures"])
        self.assertFails(
            self.delivered_tree(part.commits[0][0], commit),
            f"docs/use-cases.md:{line} states {values['fixtures']} (fixtures) for aip-conformance "
            f"at {commit}, which has {values['fixtures'] + 2}",
        )

    @unittest.skipUnless(os.environ.get("AIP_CONFORMANCE_SUITE"), "AIP_CONFORMANCE_SUITE not set")
    def test_the_delivered_documents_state_the_real_suite_counts(self):
        self.assertPasses(REPO, "3 stated value(s) checked", suite=os.environ["AIP_CONFORMANCE_SUITE"])


class PhrasingTest(CountsTest):
    def test_counts_equal_to_the_suite_at_the_named_commit_pass(self):
        commit = self.commit(14, 3)
        self.assertPasses(self.tree(sentence(17, 14, 3, commit)), "3 stated value(s) checked")

    def test_a_commit_written_without_backticks_is_read(self):
        commit = self.commit(14, 3)
        text = sentence(17, 14, 3, commit).replace(f"`{commit}`", commit)
        self.assertPasses(self.tree(text), "3 stated value(s) checked")

    def test_a_stale_total_fails_naming_the_file_line_and_kind(self):
        commit = self.commit(14, 3)
        self.assertFails(self.tree(sentence(16, 14, 3, commit)),
                         f"docs/use-cases.md:3 states 16 (fixtures) for aip-conformance at {commit}, which has 17")

    def test_a_stale_count_of_each_class_fails(self):
        commit = self.commit(14, 3)
        self.assertFails(
            self.tree(sentence(17, 13, 4, commit)),
            f"docs/use-cases.md:3 states 13 (challenge-response fixtures) for aip-conformance at {commit}, which has 14",
            f"docs/use-cases.md:3 states 4 (trust-score fixtures) for aip-conformance at {commit}, which has 3",
        )

    def test_the_sentence_as_it_read_before_fails(self):
        # 7 fixtures (4 challenge-response transcripts, 3 trust-score compositions), no commit named.
        head = self.commit(14, 3)
        self.assertFails(
            self.tree(sentence(7, 4, 3)),
            f"docs/use-cases.md:3 states 7 (fixtures) for aip-conformance and names no commit; "
            f"at HEAD {head} the suite has 17",
            f"docs/use-cases.md:3 states 4 (challenge-response fixtures) for aip-conformance and names no commit",
        )

    def test_a_count_that_names_no_commit_fails_even_when_it_matches_the_head(self):
        self.commit(14, 3)
        self.assertFails(self.tree(sentence(17, 14, 3)), "states 17 (fixtures) for aip-conformance and names no commit")

    def test_a_count_read_at_an_older_commit_passes_and_says_the_suite_has_moved(self):
        older = self.commit(4, 3)
        head = self.commit(14, 3)
        out = self.assertPasses(self.tree(sentence(7, 4, 3, older)), "3 stated value(s) checked")
        self.assertIn(f"at HEAD {head} the suite ships 17", out)

    def test_the_head_counts_stated_at_an_older_commit_fail(self):
        older = self.commit(4, 3)
        self.commit(14, 3)
        self.assertFails(self.tree(sentence(17, 14, 3, older)),
                         f"docs/use-cases.md:3 states 17 (fixtures) for aip-conformance at {older}, which has 7")

    def test_a_commit_the_suite_does_not_have_fails(self):
        self.commit(14, 3)
        self.assertFails(self.tree(sentence(17, 14, 3, "0000000")),
                         "names aip-conformance commit 0000000, which the suite checkout at",
                         "does not resolve to one commit")

    def test_a_commit_outside_the_history_of_the_suite_head_fails(self):
        self.commit(14, 3)
        branch = self.git("rev-parse", "--abbrev-ref", "HEAD")
        self.git("checkout", "-q", "-b", "side")
        side = self.commit(15, 3)
        self.git("checkout", "-q", branch)
        self.assertFails(self.tree(sentence(18, 15, 3, side)),
                         f"names aip-conformance commit {side}, which is not in the history of the suite checkout's HEAD")

    def test_two_commits_in_one_suite_part_fail(self):
        first = self.commit(14, 3)
        second = self.commit(14, 3)
        text = sentence(17, 14, 3, first).replace("transcripts,", f"transcripts at commit `{second}`,")
        self.assertFails(self.tree(text), "docs/use-cases.md:3 names 2 aip-conformance commits")

    def test_a_section_number_is_not_a_count(self):
        commit = self.commit(14, 3)
        text = sentence(17, 14, 3, commit) + (
            "\nThe pinned verdicts of the Section 5.1 fixtures come from "
            f"{LINK}, which covers the Section 5.1 challenge-response transcripts and the "
            "Section 6.1 trust-score compositions.\n"
        )
        self.assertPasses(self.tree(text), "3 stated value(s) checked")

    def test_fenced_code_is_not_read(self):
        commit = self.commit(14, 3)
        text = sentence(17, 14, 3, commit) + (
            "\nOutput at aip-conformance commit `0000000`:\n\n"
            "```\naip-conformance\nsummary: 2 pass, 0 fail (2 fixtures)\n```\n"
        )
        self.assertPasses(self.tree(text), "3 stated value(s) checked")

    def test_a_line_opening_with_an_inline_code_span_is_not_a_fence(self):
        commit = self.commit(14, 3)
        text = sentence(16, 14, 3, commit).replace("# Use cases\n", "# Use cases\n\n```code``` comes first here.\n")
        self.assertFails(self.tree(text), "states 16 (fixtures) for aip-conformance")

    def test_a_count_before_any_suite_is_named_fails(self):
        commit = self.commit(14, 3)
        text = sentence(17, 14, 3, commit) + "\nThe suite ships 17 fixtures.\n"
        self.assertFails(self.tree(text),
                         "docs/use-cases.md:5 states 17 (fixtures) before naming a conformance suite")

    def test_a_count_for_another_suite_is_not_read_as_aip_conformance(self):
        commit = self.commit(14, 3)
        text = sentence(17, 14, 3, commit) + (
            "\n[atx-conformance](https://github.com/opena2a-standards/atx-conformance) ships 41 fixtures.\n"
        )
        self.assertFails(self.tree(text),
                         "docs/use-cases.md:5 states 41 (fixtures) for atx-conformance, which this check does not read")

    def test_a_count_wrapped_onto_the_next_line_is_read_and_reported_there(self):
        commit = self.commit(14, 3)
        text = (
            "# Use cases\n\n"
            f"Why you can check this yourself: {LINK}, 17 byte-pinned fixtures at commit `{commit}`\n"
            "(13 challenge-response transcripts, 3 trust-score compositions).\n"
        )
        self.assertFails(self.tree(text),
                         f"docs/use-cases.md:4 states 13 (challenge-response fixtures) for aip-conformance at {commit}")

    def test_a_count_in_the_readme_or_another_page_is_read(self):
        commit = self.commit(14, 3)
        stale = f"# Title\n\n{LINK} at commit `{commit}` ships 16 fixtures.\n"
        self.assertFails(self.tree(sentence(17, 14, 3, commit), {"README.md": stale}),
                         f"README.md:3 states 16 (fixtures) for aip-conformance at {commit}, which has 17")
        self.assertFails(self.tree(sentence(17, 14, 3, commit), {"docs/notes/suite.md": stale}),
                         f"docs/notes/suite.md:3 states 16 (fixtures) for aip-conformance at {commit}")

    def test_a_page_that_states_no_count_fails_instead_of_passing_vacuously(self):
        self.commit(14, 3)
        self.assertFails(self.tree("# Use cases\n\nNo count here.\n"),
                         "docs/use-cases.md states no aip-conformance count")

    def test_a_missing_use_cases_page_fails(self):
        self.commit(14, 3)
        self.assertFails(self.tree(None), "docs/use-cases.md is missing")

    def test_a_commit_that_ships_no_fixtures_fails_instead_of_passing_vacuously(self):
        empty = self.commit(0, 0)
        self.assertFails(self.tree(sentence(0, 0, 0, empty)),
                         f"names aip-conformance commit {empty}, which ships no fixtures; refusing to pass vacuously")

    def test_only_json_files_directly_under_fixtures_are_counted(self):
        commit = self.commit(14, 3, extra={"fixtures/load-errors/truncated.json": "{\n",
                                           "fixtures/NOTES.md": "notes\n"})
        self.assertPasses(self.tree(sentence(17, 14, 3, commit)), "3 stated value(s) checked")

    def test_a_fixture_of_another_type_counts_toward_the_total_only(self):
        commit = self.commit(14, 3, untyped=1)
        self.assertPasses(self.tree(sentence(18, 14, 3, commit)), "3 stated value(s) checked")
        self.assertFails(self.tree(sentence(17, 14, 3, commit)), "states 17 (fixtures) for aip-conformance")

    def test_a_suite_path_that_is_not_a_git_checkout_fails(self):
        plain = self.tmp / "plain"
        (plain / "fixtures").mkdir(parents=True)
        (plain / "fixtures" / "challenge-response-0.json").write_text("{}\n")
        self.assertFails(self.tree(sentence(1, 1, 0, "0000000")), "is not a git checkout", suite=plain)


if __name__ == "__main__":
    unittest.main()
