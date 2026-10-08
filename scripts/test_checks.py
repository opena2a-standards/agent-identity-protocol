#!/usr/bin/env python3
"""Regression tests for scripts/check_draft_sync.py, the README link lists and Quick Start.

The draft sync cases run on small CHANGELOG and README texts built here, so
they do not depend on the repository's current pairing. Runs on its own:
    python3 scripts/test_checks.py
python3 standard library only.
"""
from __future__ import annotations

import re
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_draft_sync  # noqa: E402

VERSION = "1.2.0-draft"
DRAFT = "draft-fane-opena2a-aip-04"
SHAPE = (
    "`draft-fane-opena2a-aip-NN` (submitted YYYY-MM-DD) remains the current"
    " datatracker revision and carries the <version> text"
)

PENDING_PAIRING = (
    "Draft pairing: `draft-fane-opena2a-aip-04` pairs with 1.2.0-draft. It is not submitted yet:\n"
    "`draft-fane-opena2a-aip-03` (submitted 2026-10-02) remains the current datatracker revision and\n"
    "carries the 1.1.0-draft text.\n"
)
SUBMITTED_PAIRING = (
    "Draft pairing: `draft-fane-opena2a-aip-04` pairs with 1.2.0-draft.\n"
    "`draft-fane-opena2a-aip-04` (submitted 2026-10-07) is the current datatracker revision.\n"
)

PENDING_README = (
    "# Title\n\n"
    "**Internet-Draft.** This specification is also published as an Internet-Draft, and the\n"
    "datatracker copy is behind this repository. The current datatracker revision,\n"
    "`draft-fane-opena2a-aip-03` (submitted 2026-10-02), carries the 1.1.0-draft text. This\n"
    "repository's specification is 1.2.0-draft: `draft-fane-opena2a-aip-04` carries it and is not\n"
    "submitted yet.\n\n"
    "## Next\n"
)
SUBMITTED_README = (
    "# Title\n\n"
    "**Internet-Draft.** This specification is also published as an Internet-Draft. The current\n"
    "datatracker revision, `draft-fane-opena2a-aip-04` (submitted 2026-10-07), carries the\n"
    "1.2.0-draft text.\n\n"
    "## Next\n"
)


def changelog(before_added: str = "", under_added: str = "") -> str:
    return (
        "# Changelog\n\n## [Unreleased]\n\n"
        f"## [{VERSION}] - 2026-10-06\n\n{before_added}\n"
        f"### Added\n\n{under_added}- An entry.\n\n"
        "## [1.1.0-draft] - 2026-09-08\n\nAn older pairing that is not submitted.\n"
    )


def problems(readme: str, log: str) -> list[str]:
    return check_draft_sync.disclosure_problems(readme, log, VERSION, DRAFT)


class PairingParagraph(unittest.TestCase):
    def test_pending_pairing_before_first_heading_passes(self):
        self.assertEqual(problems(PENDING_README, changelog(before_added=PENDING_PAIRING)), [])

    def test_pending_pairing_under_a_heading_passes(self):
        log = changelog(under_added=PENDING_PAIRING + "\n")
        self.assertEqual(check_draft_sync.pairing(log, VERSION), (DRAFT, True))
        self.assertEqual(problems(PENDING_README, log), [])

    def test_pairing_paragraph_ends_at_the_next_list_item(self):
        log = changelog(under_added="- " + SUBMITTED_PAIRING + "- A sibling entry that is not submitted.\n")
        self.assertEqual(problems(SUBMITTED_README, log), [])

    def test_pairing_paragraph_ends_at_a_blank_line(self):
        log = changelog(before_added=SUBMITTED_PAIRING + "\nA later paragraph that is not submitted.\n")
        self.assertEqual(problems(SUBMITTED_README, log), [])


class BehindSentence(unittest.TestCase):
    def test_submitted_pairing_rejects_behind_sentence(self):
        readme = SUBMITTED_README.replace(
            "Internet-Draft. The", "Internet-Draft, and the datatracker copy is behind this repository. The"
        )
        found = problems(readme, changelog(before_added=SUBMITTED_PAIRING))
        self.assertEqual(len(found), 1, found)
        self.assertIn("is behind this repository", found[0])

    def test_pending_pairing_requires_behind_sentence(self):
        readme = PENDING_README.replace(", and the\ndatatracker copy is behind this repository", "")
        self.assertNotIn("behind", readme)
        found = problems(readme, changelog(before_added=PENDING_PAIRING))
        self.assertEqual(len(found), 1, found)
        self.assertIn("is behind this repository", found[0])


class CurrentRevisionShape(unittest.TestCase):
    def test_reworded_sentence_failure_names_expected_shape(self):
        log = changelog(before_added=PENDING_PAIRING.replace("remains the current", "is still the current"))
        found = problems(PENDING_README, log)
        self.assertTrue(found, "a reworded current-revision sentence must fail")
        self.assertIn(SHAPE, found[0])

    def test_docstring_names_expected_shape(self):
        doc = re.sub(r"\s+", " ", check_draft_sync.__doc__)
        self.assertIn(SHAPE, doc)


class ReadmeLinks(unittest.TestCase):
    def test_readme_lists_no_link_twice(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        bullets = Counter(line.strip() for line in readme.splitlines() if line.lstrip().startswith("- ["))
        self.assertEqual([line for line, n in bullets.items() if n > 1], [])

    def test_readme_repeats_no_command(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        commands: Counter[str] = Counter()
        in_block = False
        for line in readme.splitlines():
            if line.lstrip().startswith("```"):
                in_block = not in_block
            elif in_block and line.strip() and not line.lstrip().startswith("#"):
                commands[line.strip()] += 1
        self.assertEqual([line for line, n in commands.items() if n > 1], [])


def first_command_output(lines: list[str]) -> tuple[str, list[str]]:
    """Return the first command in the first fenced block and the comment lines right under it.

    The output shown for a command is the run of comment lines that follows it before a blank
    line, a closing fence or the next command.
    """
    fence = next(i for i, line in enumerate(lines) if line.startswith("```"))
    block = lines[fence + 1:]
    start = next(i for i, line in enumerate(block) if line.strip() and not line.startswith("#"))
    output = []
    for line in block[start + 1:]:
        if not line.startswith("#"):
            break
        output.append(line)
    return block[start], output


class ReadmeQuickStart(unittest.TestCase):
    def test_first_command_shows_its_output_in_the_first_30_lines(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        command, output = first_command_output(readme.splitlines()[:30])
        self.assertEqual(command, "npx opena2a-cli identity create --name my-agent")
        self.assertIn("#   Identity created", output)

    def test_output_note_says_a_repeat_run_keeps_the_agent_id(self):
        # A second run with the same data directory prints "Identity already exists" and the
        # same Agent ID, so the note must not say the ID differs on each run.
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        _, output = first_command_output(readme.splitlines()[:30])
        note = " ".join(line.lstrip("#").strip() for line in output)
        self.assertNotIn("each run", note)
        self.assertIn('"Identity already exists"', note)

    def test_first_command_shows_every_line_the_cli_prints(self):
        # opena2a-cli 0.10.13 prints a heading and four labelled lines for identity create.
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        _, output = first_command_output(readme.splitlines()[:30])
        shown = [line.removeprefix("#").strip() for line in output]
        labels = ["Identity created", "Agent ID:", "Name:", "Public Key:", "Stored in:"]
        start = shown.index(labels[0])
        self.assertEqual([line.split("  ")[0] for line in shown[start:]], labels)
        self.assertEqual(shown[start + 2].split(), ["Name:", "my-agent"])

    def test_output_ends_at_a_blank_line(self):
        lines = ["```bash", "# Create", "run a", "", "# Next", "run b", "```"]
        self.assertEqual(first_command_output(lines), ("run a", []))


if __name__ == "__main__":
    unittest.main()
