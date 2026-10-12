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


def unshipped_level_2_rows(spec: str) -> list[str]:
    """Return the Appendix A.1 rows for a section Level 2 requires whose AIM status is not Shipped.

    The Level 2 requirements in Section 2 cite their sections as "(Section N...)"; an A.1 row
    belongs to one when its first cell starts with "§N " for the same top-level N.
    """
    level_2 = spec.split("### Level 2: Managed Identity", 1)[1].split("### Level 3", 1)[0]
    sections = set(re.findall(r"\(Section (\d+)", level_2))
    rows = []
    for line in spec.split("### A.1 ", 1)[1].splitlines():
        match = re.match(r"\| §(\d+) ([^|]*)\| ([^|]*)\|", line)
        if match and match.group(1) in sections and not match.group(3).strip().startswith("Shipped"):
            rows.append(f"§{match.group(1)} {match.group(2).strip()}")
    return rows


def level_2_claims(text: str) -> list[str]:
    """Return the sentences that name a conformance level for the reference implementation."""
    claims = []
    for paragraph in re.split(r"\n\s*\n", text):
        for sentence in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", paragraph).strip()):
            if "Level 2" in sentence and ("AIM" in sentence or "reference implementation" in sentence):
                claims.append(sentence)
    return claims


LEVEL_2_SPEC = (
    "### Level 2: Managed Identity\n\nRequirements:\n"
    "- Challenge-response verification (Section 5)\n- Trust scoring (Section 6)\n\n"
    "### Level 3: Federated Identity\n\n### A.1 Spec sections\n\n"
    "| Section | AIM status | Notes |\n|---|---|---|\n"
    "| §3 Agent Identity | Partial | Not a Level 2 section. |\n"
    "| §5 Verification (challenge-response) | Partial | Not served. |\n"
    "| §6 Trust Scoring | Shipped, with notes | Served. |\n"
    "| §6.5 ATP integration | Not yet integrated | A subsection. |\n"
)


class ReferenceImplementationLevel(unittest.TestCase):
    def test_unshipped_rows_are_the_level_2_sections_not_marked_shipped(self):
        self.assertEqual(unshipped_level_2_rows(LEVEL_2_SPEC), ["§5 Verification (challenge-response)"])

    def test_level_2_claims_say_targets_while_a_level_2_section_is_not_shipped(self):
        # Level 2 requires every Level 2 section, so while Appendix A.1 marks one of them
        # Partial the reference implementation targets Level 2 and does not implement it.
        spec = (check_draft_sync.ROOT / "AIP-SPEC.md").read_text(encoding="utf-8")
        unshipped = unshipped_level_2_rows(spec)
        if not unshipped:
            self.skipTest("Appendix A.1 marks every Level 2 section Shipped")
        for name in ("README.md", "AIP-SPEC.md"):
            text = (check_draft_sync.ROOT / name).read_text(encoding="utf-8")
            with self.subTest(file=name):
                overclaims = [claim for claim in level_2_claims(text) if "targets" not in claim]
                self.assertEqual(overclaims, [], f"Appendix A.1 marks {unshipped} not Shipped")


def status_notes(spec: str, heading: str) -> list[str]:
    """Return the "Reference implementation status" notes in one numbered subsection.

    A subsection runs from its "### <heading>" line to the next "## " or "### " heading; a note
    is a blockquote paragraph that opens with "> **Reference implementation status".
    """
    body = ("\n" + spec).split(f"\n### {heading}\n", 1)[1]
    body = re.split(r"\n#{2,3} ", body, maxsplit=1)[0]
    return [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", body)
        if paragraph.strip().startswith("> **Reference implementation status")
    ]


STATUS_SPEC = (
    "### 3.3 Identity File Format\n\nPrivate keys MUST be encrypted at rest.\n\n"
    "> **Reference implementation status (date).** The tool writes\n> `identity.json`.\n\n"
    "### 3.4 Agent Types\n\n> **Reference implementation status (date).** Another section.\n"
)

# What the published CLI writes, which Sections 3.3 and 9.1 specify differently. A section's
# note must name each of these until the tool follows that section.
LOCAL_IDENTITY_GAPS = {
    "3.3 Identity File Format": ["identity.json", "secretKey", "0600", "not encrypted at rest"],
    "9.1 Local Audit Log": ["identity_created", "`action`", "`target`", "`result`", "`plugin`"],
}


class LocalIdentityStatus(unittest.TestCase):
    def test_status_notes_are_read_from_their_own_subsection(self):
        self.assertEqual(
            status_notes(STATUS_SPEC, "3.3 Identity File Format"),
            ["> **Reference implementation status (date).** The tool writes > `identity.json`."],
        )
        self.assertEqual(status_notes(STATUS_SPEC, "3.4 Agent Types")[0][-16:], "Another section.")

    def test_local_identity_sections_say_what_the_cli_writes(self):
        # The CLI stores one identity in identity.json with its private key in plain base64 and
        # writes no identity_created event, so Sections 3.3 and 9.1 carry a status note that
        # says so, as Section 3.2 does for the resolver.
        spec = (check_draft_sync.ROOT / "AIP-SPEC.md").read_text(encoding="utf-8")
        for heading, terms in LOCAL_IDENTITY_GAPS.items():
            with self.subTest(section=heading):
                notes = status_notes(spec, heading)
                self.assertEqual(len(notes), 1, f"Section {heading} has no status note")
                missing = [term for term in terms if term not in notes[0]]
                self.assertEqual(missing, [], f"Section {heading} status note")


if __name__ == "__main__":
    unittest.main()
