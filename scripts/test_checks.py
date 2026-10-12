#!/usr/bin/env python3
"""Regression tests for scripts/check_draft_sync.py, the README link lists and Quick Start,
the prior-art attribution in README.md, AIP-SPEC.md and GAP-ANALYSIS.md, the JWT
access-token lifetime in AIP-SPEC.md §5.4, the status on each line of the two lists of
protocols AIP is designed to complement, the lists under the README's Internet-Draft paragraph,
the RFCs listed in AIP-SPEC.md §14, the GAP-ANALYSIS.md priority list, the version note
AIP-SPEC.md carries while a change to a requirement is unreleased, the trust factor status
README.md, AIP-SPEC.md and GAP-ANALYSIS.md give, and the reference provider identifier
AIP-SPEC.md gives.

The draft sync cases run on small CHANGELOG and README texts built here, so
they do not depend on the repository's current pairing. Two cases read the specification as of
the commit that made the paired draft and are skipped where git or that history is missing, or
fail there where CI is set to a value other than an empty string, 0 or false (in any letter case
or with surrounding spaces), so a CI run needs git and a full clone.
Runs on its own:
    python3 scripts/test_checks.py
python3 standard library only.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

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

    def test_readme_says_the_draft_lacks_both_status_notes(self):
        # Sections 4.3 and 11.1 of draft -04, the counterparts of Sections 3.3 and 9.1, carry no
        # status note, so the lists under the README's Internet-Draft paragraph name each note,
        # beside its section of the draft, among the informative changes made since that revision.
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        items = [item for _, listed in counted_lists(draft_disclosure(readme)) for item in listed]
        for section, counterpart in (("§3.3", "Section 4.3 of the draft"), ("§9.1", "Section 11.1 of the draft")):
            with self.subTest(section=section):
                opening = f"- {section} carries a reference implementation status note"
                named = [item for item in items if item.startswith(opening)]
                self.assertEqual(len(named), 1, f"no Internet-Draft list item starts {opening!r}")
                self.assertIn(counterpart, named[0])


PRIOR_ART_DOCS = ("README.md", "AIP-SPEC.md", "GAP-ANALYSIS.md")


class PriorArtAttribution(unittest.TestCase):
    # draft-aip-agent-identity-protocol-00 lists J. Cao of Montcao and C. Arango Gutierrez of
    # NVIDIA; the datatracker records draft-singla-agent-identity-protocol-00 as submitted on
    # 2026-04-16, though the document itself is dated 2026-04-17.
    def test_each_author_has_their_own_affiliation(self):
        for name in PRIOR_ART_DOCS:
            text = (check_draft_sync.ROOT / name).read_text(encoding="utf-8")
            with self.subTest(doc=name):
                for author in ("James Cao (Montcao)", "Carlos Eduardo Arango Gutierrez (NVIDIA)"):
                    self.assertTrue(author in text, f"{name} does not name {author!r}")
                stray = [line for line in text.splitlines() if line.count("NVIDIA") > line.count("Arango Gutierrez (NVIDIA)")]
                self.assertEqual(stray, [], f"{name} names NVIDIA other than as Arango Gutierrez's affiliation")

    def test_singla_00_has_one_date(self):
        gap = (check_draft_sync.ROOT / "GAP-ANALYSIS.md").read_text(encoding="utf-8")
        row = next(line for line in gap.splitlines() if line.startswith("| draft-singla-agent-identity-protocol |"))
        self.assertIn("| -00, 2026-04-16 |", row)
        spec = (check_draft_sync.ROOT / "AIP-SPEC.md").read_text(encoding="utf-8")
        claim = "draft-singla-agent-identity-protocol (Singla, first published 2026-04-16,"
        self.assertTrue(claim in spec, f"AIP-SPEC.md does not say {claim!r}")
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        row = next(line for line in readme.splitlines() if "[draft-singla-agent-identity-protocol-00]" in line)
        self.assertIn("| April 16, 2026", row)


class JwtAccessTokenLifetime(unittest.TestCase):
    # The reference implementation issues access tokens valid for 2 hours by default, and the
    # lifetime is configurable, so §5.4 states a maximum instead of a fixed 1-hour TTL.
    def test_spec_states_a_maximum_lifetime(self):
        spec = (check_draft_sync.ROOT / "AIP-SPEC.md").read_text(encoding="utf-8")
        bullet = next(line for line in spec.splitlines() if line.startswith("- **JWT Bearer Tokens**"))
        self.assertNotIn("1-hour", bullet)
        self.assertNotIn("TTL", bullet)
        self.assertIn("lifetime SHOULD NOT exceed 2 hours", bullet)

    def test_readme_names_the_change_since_the_draft(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        items = [item for _, listed in counted_lists(draft_disclosure(readme)) for item in listed]
        named = [item for item in items if item.startswith("- §5.4 ")]
        self.assertEqual(len(named), 1, "no Internet-Draft list item starts '- §5.4 '")
        for claim in ("Section 6.4 of the draft", '"a one-hour time-to-live"'):
            self.assertTrue(claim in named[0], f"the §5.4 item does not say {claim!r}")


# The opening words of the two CHANGELOG entries the cases below read.
COUNT_ENTRY = "`scripts/test_checks.py` does not report"
HISTORY_ENTRY = "The two cases of `scripts/test_checks.py`"


def changelog_entry(start: str, changelog: str | None = None) -> str:
    """Return the first CHANGELOG entry that starts with start, on one line.

    The whole CHANGELOG is read, so an entry is found under Unreleased and, once a release moves
    it, under a version heading. Fails, quoting start, where no entry starts with it.
    """
    if changelog is None:
        changelog = check_draft_sync.CHANGELOG.read_text(encoding="utf-8")
    entries = [" ".join(entry.split()) for entry in re.findall(r"^- .*(?:\n  .*)*", changelog, flags=re.MULTILINE)]
    found = [entry for entry in entries if entry.startswith("- " + start)]
    if not found:
        raise AssertionError(f"no CHANGELOG.md entry starts with {start!r}")
    return found[0]


ENTRY_LOG = (
    "# Changelog\n\n## [Unreleased]\n\n### Fixed\n\n- A fix that is\n  not released.\n\n"
    "## [1.2.0-draft] - 2026-10-06\n\n### Fixed\n\n- A fix that was\n  released.\n"
)


class ChangelogEntryLookup(unittest.TestCase):
    """An entry a case reads is found wherever the CHANGELOG lists it, and a missing one is named."""

    def test_an_entry_is_found_under_unreleased_and_under_a_version_heading(self):
        self.assertEqual(changelog_entry("A fix that is", ENTRY_LOG), "- A fix that is not released.")
        self.assertEqual(changelog_entry("A fix that was", ENTRY_LOG), "- A fix that was released.")

    def test_an_entry_is_found_once_a_release_moves_it_under_a_version_heading(self):
        # A release dates the entries under Unreleased: a version heading right under the
        # Unreleased one moves each of them, the two entries the cases below read among them.
        heading = "## [Unreleased]\n"
        dated = heading + "\n## [1.3.0-draft] - 2026-11-01\n"
        self.assertEqual(
            changelog_entry("A fix that is", ENTRY_LOG.replace(heading, dated)), "- A fix that is not released."
        )
        released = check_draft_sync.CHANGELOG.read_text(encoding="utf-8").replace(heading, dated)
        for start in (COUNT_ENTRY, HISTORY_ENTRY):
            with self.subTest(start=start):
                self.assertEqual(changelog_entry(start, released), changelog_entry(start))

    def test_a_missing_entry_fails_with_a_message_that_quotes_its_opening_words(self):
        with self.assertRaises(AssertionError) as raised:
            changelog_entry("A fix nobody made", ENTRY_LOG)
        self.assertEqual(str(raised.exception), "no CHANGELOG.md entry starts with 'A fix nobody made'")


# The number words the checks know: zero to twelve only. A higher number written as one word, as
# "twenty" is in "a twenty-item list" and "thirteen" in "a thirteen-field form", is not read as a
# count and is not reported.
NUMBER_WORDS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
)
# A number word, with the hyphenated compound it begins. A number word right after a hyphen is not
# matched, whether it ends a compound ("non-zero") or is part of a count, as the "five" of "a
# twenty-five-field form" is; "twenty" is not a number word here either, so that count is not
# reported.
COUNT = re.compile(r"(?<![\w-])(%s)((?:-\w+)*)(?!\w)" % "|".join(NUMBER_WORDS), re.IGNORECASE)
# Compounds that begin with a number word and are not reported. Every other compound that begins
# with one is reported, whether it states a count ("a two-item list", "the five-field form") or
# not ("one-off", "one-shot", "one-sided"); an entry here or a rewording clears one that does not.
NO_COUNT = ("one-way", "two-way", "one-time", "one-hour", "one-to-one", "two-factor")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def draft_disclosure(readme: str) -> str:
    """Return the README text from its "**Internet-Draft.**" paragraph to the next heading."""
    start = readme.index("**Internet-Draft.**")
    end = re.search(r"^#", readme[start:], re.MULTILINE)
    return readme[start: start + end.start() if end else len(readme)]


def blocks(text: str) -> list[str]:
    """Return the paragraphs and lists of text: the runs of lines that blank lines separate."""
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def list_items(block: str) -> list[str]:
    """Return the items of a list block, each with its continuation lines joined to it."""
    items: list[str] = []
    for line in block.splitlines():
        if line.startswith("- "):
            items.append(line)
        else:
            items[-1] += " " + line.strip()
    return items


def counted_lists(text: str) -> list[tuple[str, list[str]]]:
    """Return (lead-in sentence, items) for each bullet list in text.

    A list is a block that starts with "- ". Its lead-in is the last sentence of the block
    right above it, the sentence that says how many items follow.
    """
    found = []
    previous = ""
    for block in blocks(text):
        if block.startswith("- "):
            found.append((SENTENCE_END.split(re.sub(r"\s+", " ", previous))[-1], list_items(block)))
        previous = block
    return found


def count_word(lead: str) -> int | None:
    """Return the number a lead-in sentence opens with, or None when it opens with no number word."""
    first = lead.split(" ", 1)[0].lower()
    return NUMBER_WORDS.index(first) if first in NUMBER_WORDS else None


def unchecked_counts(text: str) -> list[str]:
    """Return the number words in the paragraphs of text that do not open the lead-in of a list.

    A count that opens a lead-in is compared with the items under it. A count anywhere else in a
    paragraph has no list to be compared with, so it can go stale unnoticed.
    """
    found = []
    parts = blocks(text)
    for index, block in enumerate(parts):
        if block.startswith("- "):
            continue
        sentences = SENTENCE_END.split(re.sub(r"\s+", " ", block))
        leads_a_list = index + 1 < len(parts) and parts[index + 1].startswith("- ")
        if leads_a_list and count_word(sentences[-1]) is not None:
            sentences[-1] = sentences[-1].split(" ", 1)[1] if " " in sentences[-1] else ""
        found += [f"{word!r} in {sentence!r}" for sentence in sentences for word in counts(sentence)]
    return found


def counts(sentence: str) -> list[str]:
    """Return the number words in sentence that state a count: all but those that begin a NO_COUNT compound."""
    return [word for word, rest in COUNT.findall(sentence) if (word + rest).lower() not in NO_COUNT]


FRONT_LABEL = re.compile(r"(?:> )?\*\*([^*]+?)[.:]\*\*")


def part_name(heading: str) -> str:
    """Return the name README.md uses for the section under a heading of the specification.

    "3.1 Cryptographic Identity" is "§3.1", "14. References" is "§14", "Appendix A: Reference
    Implementation" is "Appendix A" and "A.1 Spec sections ..." is "Appendix A.1". Any other
    heading is named by its text up to a colon ("Abstract", "Level 2").
    """
    numbered = re.match(r"(\d+(?:\.\d+)*)\.? ", heading)
    if numbered:
        return "§" + numbered.group(1)
    appendix = re.match(r"([A-Z](?:\.\d+)+) |Appendix ([A-Z])\b", heading)
    if appendix:
        return "Appendix " + (appendix.group(1) or appendix.group(2))
    return heading.split(":", 1)[0].strip()


def spec_parts(spec: str) -> dict[str, str]:
    """Split the specification into named parts and return the text of each, without blank lines.

    Above the abstract a part is a line that opens with a bold label, named by that label in
    lower case ("version", "naming note"); the other lines there are the part "title". From the
    abstract on a part is a "## " or "### " section named by part_name, and a deeper heading
    stays in its "### " section.
    """
    parts: dict[str, list[str]] = {}
    name, front, fenced = "title", True, False
    for line in spec.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        heading = None if fenced else re.match(r"#{2,3} (.+)", line)
        if heading and (not front or heading.group(1) == "Abstract"):
            name, front = part_name(heading.group(1)), False
        elif front:
            label = FRONT_LABEL.match(line)
            name = label.group(1).lower() if label else "title"
        if line.strip():
            parts.setdefault(name, []).append(line)
    return {name: "\n".join(lines) for name, lines in parts.items()}


def changed_parts(before: str, after: str) -> list[str]:
    """Return the names of the parts whose text differs between two texts of the specification."""
    old, new = spec_parts(before), spec_parts(after)
    return [name for name in {**new, **old} if old.get(name) != new.get(name)]


def names_part(text: str, part: str) -> bool:
    """Whether text names a part: "§3.10" and "§3.1.2" do not name "§3.1", nor "Appendix A.1" "Appendix A"."""
    return re.search(re.escape(part) + r"(?!\.?\d|\w)", text, re.IGNORECASE) is not None


def a1_rows(spec: str) -> dict[str, str]:
    """Return the rows of the Appendix A.1 table under its header row, each keyed by its first cell."""
    lines = [line for line in spec_parts(spec).get("Appendix A.1", "").splitlines() if line.startswith("|")]
    if len(lines) > 1 and set(lines[1]) <= set("|-: "):
        lines = lines[2:]
    return {line.split("|")[1].strip(): line for line in lines}


def changed_a1_rows(before: str, after: str) -> list[str]:
    """Return the first cells of the Appendix A.1 rows that differ, are added or are removed between two texts."""
    old, new = a1_rows(before), a1_rows(after)
    return [cell for cell in {**new, **old} if old.get(cell) != new.get(cell)]


def row_section(cell: str) -> str:
    """Return the section an Appendix A.1 row is for: "§6" for "§6 Trust Scoring (9-factor)", else the whole cell."""
    numbered = re.match(r"§\d+(?:\.\d+)*", cell)
    return numbered.group(0) if numbered else cell


NO_COUNTERPART = "have no counterpart"
SPEC_SECTION = re.compile(r"(#{2,4}) (?:\d+(?:\.\d+)*\.?|Appendix [A-Z]:|[A-Z]\.\d+) +(.+?)\s*$")
# A heading in the body of a draft's txt starts in column 0; its table of contents is indented.
DRAFT_SECTION = re.compile(r"^((?:\d+\.)+|Appendix [A-Z]\.) +(\S.*?)\s*$", re.MULTILINE)


def change_items(readme: str) -> list[str]:
    """Return the items of the Internet-Draft lists that say what the draft leaves out of a part or what has changed.

    A list whose lead-in says its parts have no counterpart names whole sections that only one
    document has. Its items say nothing about a change, so they do not count as naming a changed
    part of the specification.
    """
    lists = counted_lists(draft_disclosure(readme))
    return [item for lead, items in lists if NO_COUNTERPART not in lead for item in items]


def counterpart_list(readme: str, document: str) -> tuple[str, list[str]]:
    """Return (lead-in, items) of the list of the parts of document that the other document lacks.

    document is "specification" or "draft".
    """
    opening = f"parts of the {document} {NO_COUNTERPART}"
    found = [(lead, items) for lead, items in counted_lists(draft_disclosure(readme)) if opening in lead]
    if len(found) != 1:
        raise AssertionError(f"expected one Internet-Draft list whose lead-in says {opening!r}, found {len(found)}")
    return found[0]


def spec_sections(spec: str) -> list[tuple[bool, str]]:
    """Return (whether it is top-level, title) for each numbered section and appendix heading of the specification."""
    found, fenced = [], False
    for line in spec.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        heading = None if fenced else SPEC_SECTION.match(line)
        if heading:
            found.append((heading.group(1) == "##", heading.group(2)))
    return found


def draft_sections(txt: str) -> list[tuple[bool, str]]:
    """Return (whether it is top-level, title) for each section and appendix heading in the body of a draft's txt."""
    return [(number.count(".") == 1, title) for number, title in DRAFT_SECTION.findall(txt)]


def draft_section(txt: str, number: str) -> str:
    """Return a section of a draft's txt, from its heading to the next heading that is not a subsection of it.

    number is the heading's own, as "8.", "13.5." or "Appendix A.".
    """
    headings = [(match.group(1), match.start()) for match in DRAFT_SECTION.finditer(txt)]
    starts = [at for found, at in headings if found == number]
    if len(starts) != 1:
        raise AssertionError(f"expected one heading {number!r} in the draft, found {len(starts)}")
    end = next((at for found, at in headings if at > starts[0] and not found.startswith(number)), len(txt))
    return txt[starts[0]: end]


def has_counterpart(title: str, others: list[str]) -> bool:
    """Whether a title is one of others, or holds or is held in one, as "Terminology" is in "Conventions and Terminology"."""
    return any(title.lower() in other.lower() or other.lower() in title.lower() for other in others)


def only_in(sections: list[tuple[bool, str]], others: list[tuple[bool, str]], top_level: bool) -> list[str]:
    """Return the titles in sections that have no counterpart in others.

    With top_level the top-level sections of each are compared and the rest left out. Without it
    every heading is compared, and a subsection the other document renames is returned too
    ("ATP Integration" beside "Agent Trust Protocol Integration"), so that result says which titles
    an item may name, not which the lists have to name.
    """
    against = [title for top, title in others if top or not top_level]
    return [title for top, title in sections if (top or not top_level) and not has_counterpart(title, against)]


FULL_CLONE = "use a full clone (in CI, actions/checkout with fetch-depth: 0)"
INSTALL_GIT = "install git"


def history_missing(reason: str, remedy: str) -> Exception:
    """Return what a case raises when the history it reads is missing: a skip, or in CI a failure.

    A skip reports OK, so a CI run from a shallow or exported tree would pass without running the
    case. Where CI is set to a value other than "", "0" or "false" (read without regard to letter
    case or surrounding spaces), it fails instead. remedy says what to do to run the case.
    """
    if os.environ.get("CI", "").strip().lower() not in ("", "0", "false"):
        return AssertionError(f"{reason}; CI is set, so this case fails instead of skipping; to run it, {remedy}")
    return unittest.SkipTest(f"{reason}; to run this case, {remedy}")


def spec_when_draft_was_made(draft: str) -> str:
    """Return AIP-SPEC.md as of the last commit that changed the draft's txt.

    Skips the calling test (fails it in CI, see history_missing) without git, outside a checkout,
    in a shallow clone, where that commit can be missing, when no commit in the history changed
    that file, or when git fails inside a full checkout (as over the repository's ownership or
    with GIT_DIR set elsewhere).
    """
    if shutil.which("git") is None:
        raise history_missing("git is not installed", INSTALL_GIT)

    def git(*args: str) -> str:
        # LC_ALL=C keeps git from translating its messages, so an error starts with "fatal:" or
        # "error:" under any locale ("Schwerwiegend:" or "Fehler:" under de_DE.UTF-8 otherwise).
        result = subprocess.run(
            ["git", *args], cwd=check_draft_sync.ROOT, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "LC_ALL": "C"},
        )
        if result.returncode != 0:
            # git can fail with history present (over the repository's ownership, or with GIT_DIR
            # set elsewhere), so the reason quotes what git said and the remedy starts from it.
            # git can write other lines first (GIT_TRACE writes trace lines), so the quote is the
            # first line that starts with "fatal:" or "error:", or the first line where none does.
            said = result.stderr.strip().splitlines()
            error = next((line for line in said if line.startswith(("fatal:", "error:"))), said[0] if said else "")
            quoted = f", saying {error!r}" if error else ""
            raise history_missing(
                f"git {args[0]} failed here{quoted}, so the text the draft was made from is not available",
                f"resolve what git reports, or {FULL_CLONE}",
            )
        return result.stdout

    if git("rev-parse", "--is-shallow-repository").strip() == "true":
        raise history_missing("shallow clone: the commit that made the draft can be missing", FULL_CLONE)
    commit = git("log", "-1", "--format=%H", "--", f"{draft}.txt").strip()
    if not commit:
        raise history_missing(f"no commit in this history changed {draft}.txt", FULL_CLONE)
    return git("show", f"{commit}:{check_draft_sync.SPEC.name}")


LISTS_README = (
    "**Internet-Draft.** The draft is submitted.\n\n"
    "Two statements are not in the draft:\n\n- \"First.\"\n- \"Second.\"\n\n"
    "The text has changed. Three changes are informative:\n\n"
    "- §3.3 carries a note.\n- Appendix A.1 marks a row\n  Partial.\n- The abstract's list ends each line with a status.\n\n"
    "## Next\n\n- [A link](a)\n"
)
PARTS_SPEC = (
    "# Title\n\n## A Subtitle\n\n**Version:** 1.0.0-draft\n\n> **Naming note.** Others use the name.\n\n"
    "## Abstract\n\nA summary.\n\n## 3. Identity\n\n### 3.1 Keys\n\nA key.\n\n#### 3.1.1 Example\n\n"
    "```\n## not a heading\n```\n\n### 3.10 Types\n\nTypes.\n\n## 14. References\n\n- RFC 2119\n\n"
    "## Appendix A: Reference Implementation\n\nIt targets Level 2.\n\n### A.1 Spec sections\n\n| §3 | Shipped |\n"
)


class InternetDraftLists(unittest.TestCase):
    """The lists under the README's Internet-Draft paragraph: where the specification and the draft differ."""

    def test_disclosure_ends_at_the_next_heading(self):
        disclosure = draft_disclosure("# Title\n\n" + LISTS_README)
        self.assertTrue(disclosure.startswith("**Internet-Draft.**"))
        self.assertNotIn("A link", disclosure)

    def test_each_list_is_read_with_its_lead_in_sentence(self):
        lists = counted_lists(draft_disclosure(LISTS_README))
        leads = ["Two statements are not in the draft:", "Three changes are informative:"]
        self.assertEqual([lead for lead, _ in lists], leads)
        self.assertEqual([len(items) for _, items in lists], [2, 3])
        self.assertEqual(lists[1][1][1], "- Appendix A.1 marks a row Partial.")
        self.assertEqual([count_word(lead) for lead, _ in lists], [2, 3])
        self.assertIsNone(count_word("The changes are informative:"))

    def test_a_count_outside_a_lead_in_is_reported(self):
        self.assertEqual(unchecked_counts(draft_disclosure(LISTS_README)), [])
        prose = LISTS_README.replace("The text has changed.", "Three informative additions have been made too.")
        found = unchecked_counts(draft_disclosure(prose))
        self.assertEqual(len(found), 1, found)
        self.assertIn("'Three' in 'Three informative additions have been made too.'", found[0])

    def test_a_hyphenated_compound_that_states_no_count_is_not_reported(self):
        # No NO_COUNT compound is reported, in any letter case ("One-way" opens the prose), nor is
        # a number word right after a hyphen ("non-zero") or at the start of a longer word
        # ("tenant", "ones", "zeros"); the same words standing alone are. The prose spells out
        # every NO_COUNT entry, so dropping one from NO_COUNT fails here.
        prose = (
            "One-way pushes and two-way links follow a two-factor login, with a one-time code, a"
            " one-hour lifetime, a one-to-one map and a non-zero value. A tenant stores ones and zeros."
        )
        self.assertEqual([entry for entry in NO_COUNT if entry not in prose.lower()], [])
        self.assertEqual(unchecked_counts(prose), [])
        found = unchecked_counts("One push, one way.")
        self.assertEqual(len(found), 2, found)

    def test_a_compound_outside_no_count_is_reported_even_where_it_states_no_count(self):
        # COUNT cannot tell "a one-off fix" from "a two-item list"; only NO_COUNT clears a compound.
        self.assertEqual(unchecked_counts("A one-off fix."), ["'one' in 'A one-off fix.'"])

    def test_changelog_entry_says_what_is_not_reported(self):
        # The entry names each NO_COUNT compound, and says that a number word after any hyphen is
        # skipped, not only one that ends a compound, and that "one-off" is still reported.
        entry = changelog_entry(COUNT_ENTRY)
        self.assertEqual([compound for compound in NO_COUNT if f'"{compound}"' not in entry], [])
        self.assertIn("a number word that follows a hyphen", entry)
        self.assertIn('as "one-off" does', entry)

    def test_changelog_entry_names_the_number_words_the_check_knows(self):
        # NUMBER_WORDS ends at "twelve", so a higher number written as one word, as "twenty" and
        # "thirteen" are, is never reported; the entry says so, and names the range NUMBER_WORDS
        # covers, so extending it fails here. A higher number written as a compound that begins
        # with a word in NUMBER_WORDS is reported, as any such compound outside NO_COUNT is.
        for text in ("A twenty-item list.", "A thirteen-field form.", "A twenty-five-field form."):
            self.assertEqual(unchecked_counts(text), [], text)
        self.assertEqual(unchecked_counts("A one-hundred-item list."), ["'one' in 'A one-hundred-item list.'"])
        self.assertEqual(unchecked_counts("Twelve-hundred rows."), ["'Twelve' in 'Twelve-hundred rows.'"])
        entry = changelog_entry(COUNT_ENTRY)
        self.assertIn("a higher number written as one word", entry)
        self.assertIn(f"the number words from {NUMBER_WORDS[0]} to {NUMBER_WORDS[-1]} only", entry)
        for example in ('"a twenty-item list"', '"a thirteen-field form"'):
            self.assertIn(example, entry)

    def test_a_hyphenated_compound_that_states_a_count_is_reported(self):
        # "a two-item list" and "the five-field form" (AIP-SPEC.md uses "five-field", "seven-field"
        # and "eleven-field") each state a count that can go stale outside a lead-in.
        found = unchecked_counts("The draft adds a two-item list and keeps the Five-field form.")
        self.assertEqual(len(found), 2, found)
        self.assertIn("'two' in ", found[0])
        self.assertIn("'Five' in ", found[1])

    def test_each_count_equals_the_items_listed_under_it(self):
        # Each lead-in opens with the number of items under it, so a count cannot be changed, or
        # an item added or removed, without the other.
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        lists = counted_lists(draft_disclosure(readme))
        self.assertTrue(lists, "no list under the Internet-Draft paragraph")
        for lead, items in lists:
            with self.subTest(lead=lead):
                self.assertIsNotNone(count_word(lead), "the lead-in opens with no number word")
                self.assertEqual(count_word(lead), len(items))

    def test_no_count_stands_outside_a_lead_in(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(unchecked_counts(draft_disclosure(readme)), [])

    def test_specification_parts_are_named_as_the_readme_names_them(self):
        parts = spec_parts(PARTS_SPEC)
        self.assertEqual(
            list(parts),
            ["title", "version", "naming note", "Abstract", "§3", "§3.1", "§3.10", "§14", "Appendix A", "Appendix A.1"],
        )
        self.assertIn("## not a heading", parts["§3.1"])
        self.assertIn("#### 3.1.1 Example", parts["§3.1"])
        self.assertEqual(part_name("Level 2: Managed Identity"), "Level 2")

    def test_changed_parts_are_the_parts_whose_text_differs(self):
        after = (
            PARTS_SPEC.replace("A key.", "A key.\n\n\nA note.")
            .replace("| Shipped |", "| Partial |")
            .replace("> **Naming note.**", "> **Version note.** Changed since.\n\n> **Naming note.**")
            .replace("## 14. References\n\n- RFC 2119\n\n", "")
        )
        self.assertEqual(changed_parts(PARTS_SPEC, after), ["version note", "§3.1", "Appendix A.1", "§14"])
        self.assertEqual(changed_parts(PARTS_SPEC, PARTS_SPEC.replace("\n\n", "\n\n\n")), [])

    def test_a_part_is_named_only_by_its_own_number(self):
        for text, part, named in (
            ("§3.1 defines the agent ID.", "§3.1", True),
            ("The examples in §3.3 and §3.1.", "§3.1", True),
            ("§3.10 lists types.", "§3.1", False),
            ("§3.1.2 has an example.", "§3.1", False),
            ("Appendix A.1 marks a row.", "Appendix A", False),
            ("Appendix A says so.", "Appendix A", True),
            ("Each line of the abstract's list.", "Abstract", True),
        ):
            with self.subTest(text=text, part=part):
                self.assertEqual(names_part(text, part), named)

    def test_changed_rows_are_the_appendix_a1_rows_whose_text_differs(self):
        before = PARTS_SPEC.replace(
            "| §3 | Shipped |\n",
            "| Section | Status |\n|---|---|\n| §3 Identity | Shipped |\n| §6 Trust | Shipped |\n| Local verify | Go only |\n",
        )
        after = before.replace("| §6 Trust | Shipped |", "| §6 Trust | Partial |").replace("| Local verify | Go only |\n", "")
        self.assertEqual(list(a1_rows(before)), ["§3 Identity", "§6 Trust", "Local verify"])
        self.assertEqual(changed_a1_rows(before, after), ["§6 Trust", "Local verify"])
        self.assertEqual([row_section(cell) for cell in ("§6 Trust", "Local verify")], ["§6", "Local verify"])

    def draft_then_and_now(self) -> tuple[str, str, str, list[str]]:
        """Return the paired draft, AIP-SPEC.md when it was made, AIP-SPEC.md now and the README change items."""
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        changelog = check_draft_sync.CHANGELOG.read_text(encoding="utf-8")
        draft, _ = check_draft_sync.pairing(changelog, check_draft_sync.spec_version(spec))
        if draft is None:
            self.skipTest("the CHANGELOG pairs no draft with the specification's version")
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        return draft, spec_when_draft_was_made(draft), spec, change_items(readme)

    def test_lists_name_every_part_of_the_specification_changed_since_the_draft(self):
        # The lists say where the specification differs from the paired draft, so each part of
        # AIP-SPEC.md that has changed since the commit that made that draft is named in an item.
        draft, before, spec, items = self.draft_then_and_now()
        changed = changed_parts(before, spec)
        unnamed = [part for part in changed if not any(names_part(item, part) for item in items)]
        self.assertEqual(unnamed, [], f"AIP-SPEC.md parts changed since {draft} that no Internet-Draft list item names")

    def test_lists_name_every_appendix_a1_row_changed_since_the_draft(self):
        # Appendix A.1 is one part however many of its rows change, so the test above passes once
        # an item names it. Each row changed since the commit that made the draft is named by its
        # section in an item that also names Appendix A.1.
        draft, before, spec, items = self.draft_then_and_now()
        unnamed = [
            cell for cell in changed_a1_rows(before, spec)
            if not any(names_part(item, "Appendix A.1") and names_part(item, row_section(cell)) for item in items)
        ]
        self.assertEqual(unnamed, [], f"Appendix A.1 rows changed since {draft} that no Internet-Draft list item names")


COUNTERPART_README = (
    "**Internet-Draft.** The draft is submitted.\n\n"
    "Two parts of the specification have no counterpart in the draft, and none of them carries a BCP 14 keyword:\n\n"
    "- §11 Integration Patterns.\n- Appendix A, Reference Implementation.\n\n"
    "One change is informative:\n\n- §3.1 carries a note.\n\n"
    "## Next\n"
)
DRAFT_TXT = (
    "Table of Contents\n\n   1.  Introduction . . . 3\n   2.  Identity . . . 4\n\n"
    "1.  Introduction\n\n   Text.\n\n2.  Identity\n\n   A key MUST be kept.\n\n2.1.  Keys\n\n   A key.\n\n"
    "10.  Discovery\n\n   Text.\n\nAppendix A.  Related Work\n\n   Text.\n"
)


class SectionsWithoutCounterpart(unittest.TestCase):
    """The two README lists of the parts that only the specification or only the paired draft has."""

    def test_a_no_counterpart_list_is_read_by_its_document_and_is_not_a_list_of_changes(self):
        lead, items = counterpart_list(COUNTERPART_README, "specification")
        self.assertTrue(lead.startswith("Two parts of the specification have no counterpart"), lead)
        self.assertEqual(items, ["- §11 Integration Patterns.", "- Appendix A, Reference Implementation."])
        with self.assertRaises(AssertionError) as raised:
            counterpart_list(COUNTERPART_README, "draft")
        self.assertIn("'parts of the draft have no counterpart', found 0", str(raised.exception))
        # An item that says §11 has no counterpart does not say what changed in §11.
        self.assertEqual(change_items(COUNTERPART_README), ["- §3.1 carries a note."])
        self.assertEqual(len(change_items(LISTS_README)), 5)

    def test_sections_are_read_from_each_document_with_their_level(self):
        self.assertEqual(
            spec_sections(PARTS_SPEC),
            [
                (True, "Identity"), (False, "Keys"), (False, "Example"), (False, "Types"), (True, "References"),
                (True, "Reference Implementation"), (False, "Spec sections"),
            ],
        )
        self.assertEqual(
            draft_sections(DRAFT_TXT),
            [(True, "Introduction"), (True, "Identity"), (False, "Keys"), (True, "Discovery"), (True, "Related Work")],
        )

    def test_a_draft_section_ends_at_the_next_heading_that_is_not_its_subsection(self):
        self.assertEqual(draft_section(DRAFT_TXT, "1."), "1.  Introduction\n\n   Text.\n\n")
        self.assertTrue(draft_section(DRAFT_TXT, "2.").endswith("2.1.  Keys\n\n   A key.\n\n"))
        self.assertEqual(draft_section(DRAFT_TXT, "Appendix A."), "Appendix A.  Related Work\n\n   Text.\n")
        with self.assertRaises(AssertionError):
            draft_section(DRAFT_TXT, "8.")

    def test_a_section_only_one_document_has_is_found(self):
        spec = [(True, "Terminology"), (False, "ATP Integration"), (True, "Integration Patterns"), (True, "Audit")]
        draft = [
            (True, "Introduction"), (True, "Conventions and Terminology"),
            (False, "Agent Trust Protocol Integration"), (False, "Integration Patterns"), (True, "Audit"),
        ]
        self.assertEqual(only_in(spec, draft, top_level=True), ["Integration Patterns"])
        self.assertEqual(only_in(draft, spec, top_level=True), ["Introduction"])
        self.assertEqual(only_in(spec, draft, top_level=False), ["ATP Integration"])
        self.assertEqual(only_in(draft, spec, top_level=False), ["Introduction", "Agent Trust Protocol Integration"])

    def documents(self) -> tuple[str, str, str]:
        """Return README.md, AIP-SPEC.md and the txt of the draft paired with the specification's version."""
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        changelog = check_draft_sync.CHANGELOG.read_text(encoding="utf-8")
        draft, _ = check_draft_sync.pairing(changelog, check_draft_sync.spec_version(spec))
        if draft is None or not (check_draft_sync.ROOT / f"{draft}.txt").exists():
            self.skipTest("the draft paired with the specification's version is not built")
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        return readme, spec, (check_draft_sync.ROOT / f"{draft}.txt").read_text(encoding="utf-8")

    def test_lists_name_every_top_level_section_only_one_document_has(self):
        readme, spec, txt = self.documents()
        ours, theirs = spec_sections(spec), draft_sections(txt)
        self.assertGreater(len([title for top, title in ours if top]), 10, ours)
        self.assertGreater(len([title for top, title in theirs if top]), 10, theirs)
        for document, sections, others in (("specification", ours, theirs), ("draft", theirs, ours)):
            with self.subTest(document=document):
                _, items = counterpart_list(readme, document)
                only = only_in(sections, others, top_level=True)
                unnamed = [title for title in only if not any(title.lower() in item.lower() for item in items)]
                self.assertEqual(unnamed, [], f"top-level sections only the {document} has that its list does not name")

    def test_each_item_names_a_section_the_other_document_lacks(self):
        # An item goes stale when the other document gains its section, or its own drops or
        # renames it: it then names no title that only its document has.
        readme, spec, txt = self.documents()
        ours, theirs = spec_sections(spec), draft_sections(txt)
        for document, sections, others in (("specification", ours, theirs), ("draft", theirs, ours)):
            _, items = counterpart_list(readme, document)
            only = only_in(sections, others, top_level=False)
            for item in items:
                with self.subTest(document=document, item=item):
                    self.assertTrue(
                        any(title.lower() in item.lower() for title in only),
                        f"the item names no section title that only the {document} has",
                    )

    def test_specification_only_parts_carry_no_keyword_where_the_lead_in_says_so(self):
        readme, spec, _ = self.documents()
        lead, items = counterpart_list(readme, "specification")
        parts = spec_parts(spec)
        carrying = []
        for item in items:
            named = re.match(r"- (§\d+(?:\.\d+)*|Appendix [A-Z])\b", item)
            self.assertIsNotNone(named, f"the item opens with no part of the specification: {item!r}")
            texts = [text for name, text in parts.items() if name == named.group(1) or name.startswith(named.group(1) + ".")]
            self.assertTrue(texts, f"AIP-SPEC.md has no part {named.group(1)}")
            if any(check_draft_sync.BCP14_KEYWORD.search(text) for text in texts):
                carrying.append(named.group(1))
        self.assertEqual("none of them carries a BCP 14 keyword" in lead, not carrying, carrying)

    def test_each_draft_only_item_names_a_keyword_where_its_section_carries_one(self):
        # A section only the draft has can state a requirement the specification lacks. Its item
        # names a BCP 14 keyword when the section carries one and none when it does not, and what
        # it quotes is in the draft and not in the specification.
        readme, spec, txt = self.documents()
        _, items = counterpart_list(readme, "draft")
        for item in items:
            with self.subTest(item=item):
                named = re.match(r"- (?:Section (\d+(?:\.\d+)*)|(Appendix [A-Z])), ", item)
                self.assertIsNotNone(named, "the item opens with no section of the draft")
                section = draft_section(txt, (named.group(1) or named.group(2)) + ".")
                self.assertEqual(
                    check_draft_sync.BCP14_KEYWORD.search(item) is not None,
                    check_draft_sync.BCP14_KEYWORD.search(section) is not None,
                )
                for quoted in re.findall(r'"([^"]+)"', item):
                    self.assertIn(quoted, check_draft_sync.draft_text(section))
                    self.assertNotIn(quoted, re.sub(r"\s+", " ", spec))


class MissingDraftHistory(unittest.TestCase):
    """The two cases above read the history: without it they skip, and in CI they fail instead."""

    # How the history can be missing where git is installed: a shallow clone, git exiting non-zero
    # (as in a tree exported with git archive, outside any checkout), or no commit that changed the
    # draft's txt.
    HISTORIES = ("shallow", "git fails", "draft unchanged")
    # The line git writes before its error where GIT_TRACE is set.
    TRACE = "05:22:41.554242 git.c:502               trace: built-in: git rev-parse --is-shallow-repository\n"

    def outcome(
        self, ci: str | None, history: str = "shallow", git: str | None = "git",
        stderr: str = "fatal: not a git repository\n", translated: str | None = None,
    ) -> BaseException:
        """Return what spec_when_draft_was_made raises where the history is missing, with CI set to ci or unset.

        Where history is "git fails", every git command exits 128 and prints stderr. Where
        translated is given, LC_ALL is de_DE.UTF-8 and a failing git command prints translated
        instead, unless it is run with LC_ALL=C, as git translates its messages under a locale
        other than C. self.ran lists the environment each git command was run with.
        """
        env = {name: value for name, value in os.environ.items() if name != "CI"}
        if ci is not None:
            env["CI"] = ci
        if translated is not None:
            env["LC_ALL"] = "de_DE.UTF-8"
        self.ran: list[dict[str, str]] = []

        def run(args: list[str], **options: object) -> subprocess.CompletedProcess:
            given = options.get("env")
            self.ran.append(dict(os.environ if given is None else given))
            if history == "git fails":
                said = stderr if translated is None or self.ran[-1].get("LC_ALL") == "C" else translated
                return subprocess.CompletedProcess(args, 128, stdout="", stderr=said)
            if args[1] == "rev-parse":
                shallow = "true\n" if history == "shallow" else "false\n"
                return subprocess.CompletedProcess(args, 0, stdout=shallow, stderr="")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch.object(shutil, "which", return_value=git),
            mock.patch.object(subprocess, "run", side_effect=run),
        ):
            try:
                spec_when_draft_was_made("draft-example-00")
            except (unittest.SkipTest, AssertionError) as raised:
                return raised
        self.fail(f"the specification was returned where the history is missing ({history})")

    def test_missing_history_skips_outside_ci(self):
        # CI is read without regard to letter case or surrounding spaces, so "FALSE" and " False "
        # skip as "false" does, and " " as "" does.
        for ci in (None, "", " ", "false", "0", "FALSE", " False "):
            for history in self.HISTORIES:
                with self.subTest(ci=ci, history=history):
                    raised = self.outcome(ci, history)
                    self.assertIsInstance(raised, unittest.SkipTest)
                    self.assertIn("use a full clone", str(raised))

    def test_missing_history_fails_in_ci(self):
        # A skip reports OK, so a CI run from a shallow or exported tree would pass without running
        # either case. In CI the missing history fails and names the checkout depth the cases need.
        for ci in ("true", "1", "TRUE"):
            for history in self.HISTORIES:
                with self.subTest(ci=ci, history=history):
                    raised = self.outcome(ci, history)
                    self.assertIsInstance(raised, AssertionError)
                    self.assertIn("fetch-depth: 0", str(raised))

    def test_missing_git_names_git_as_the_remedy(self):
        # Without git a full clone does not help, so the reason says to install git.
        for ci, kind in ((None, unittest.SkipTest), ("true", AssertionError)):
            with self.subTest(ci=ci):
                raised = self.outcome(ci, git=None)
                self.assertIsInstance(raised, kind)
                self.assertIn("install git", str(raised))
                self.assertNotIn("full clone", str(raised))

    def test_a_git_failure_quotes_what_git_said(self):
        # git can fail where the history is present, as over the repository's ownership or with
        # GIT_DIR set elsewhere, and a full clone does not help there, so the reason quotes the
        # first line of git's message that starts with "fatal:" or "error:", or its first line
        # where none does, and the remedy starts from it.
        stderr = "fatal: detected dubious ownership in repository at '/repo'\nTo add an exception, call:\n"
        for ci, kind in ((None, unittest.SkipTest), ("true", AssertionError)):
            with self.subTest(ci=ci):
                raised = self.outcome(ci, "git fails", stderr=stderr)
                self.assertIsInstance(raised, kind)
                self.assertIn("""saying "fatal: detected dubious ownership in repository at '/repo'",""", str(raised))
                self.assertNotIn("To add an exception", str(raised))
                self.assertIn("resolve what git reports, or use a full clone", str(raised))
        for ci in (None, "true"):
            with self.subTest(ci=ci, stderr=""):
                self.assertIn("git rev-parse failed here, so", str(self.outcome(ci, "git fails", stderr="")))

    def test_a_git_failure_quotes_git_s_error_after_lines_written_before_it(self):
        # With GIT_TRACE set, git writes a trace line before its error, so the reason quotes the
        # first line that starts with "fatal:" or "error:", and the first line where none does. A
        # line that has either word after its start, as the warning of the third case has both,
        # is not that line. No other line git wrote is quoted.
        cases = (
            (
                self.TRACE + "fatal: not a git repository: '/nonexistent'\n",
                "fatal: not a git repository: '/nonexistent'",
            ),
            (self.TRACE + "error: object file is empty\nfatal: bad object HEAD\n", "error: object file is empty"),
            ("warning: a hook wrote error: and fatal: lines\nfatal: bad object HEAD\n", "fatal: bad object HEAD"),
            ("warning: unable to access 'attributes'\nhint: check it\n", "warning: unable to access 'attributes'"),
        )
        for stderr, quoted in cases:
            for ci, kind in ((None, unittest.SkipTest), ("true", AssertionError)):
                with self.subTest(ci=ci, quoted=quoted):
                    raised = self.outcome(ci, "git fails", stderr=stderr)
                    self.assertIsInstance(raised, kind)
                    self.assertIn(f"git rev-parse failed here, saying {quoted!r}, so", str(raised))
                    for line in stderr.splitlines():
                        if line != quoted:
                            self.assertNotIn(line, str(raised))

    def test_git_runs_with_lc_all_c_so_its_error_is_quoted_under_another_locale(self):
        # git translates the "fatal:" and "error:" that start its messages ("Schwerwiegend:" and
        # "Fehler:" under de_DE.UTF-8), so under such a locale no line would start with either and
        # the trace line would be quoted. Each git command runs with LC_ALL=C, under which git does
        # not translate, and with the rest of the environment as it is.
        fatal = ("fatal: not a git repository: '/nonexistent'", "Schwerwiegend: Kein Git-Repository: '/nonexistent'")
        error = (
            "error: object file .git/objects/ab/cdef is empty", "Fehler: Objektdatei .git/objects/ab/cdef ist leer."
        )
        for english, german in (fatal, error):
            for ci, kind in ((None, unittest.SkipTest), ("true", AssertionError)):
                with self.subTest(ci=ci, english=english):
                    raised = self.outcome(
                        ci, "git fails", stderr=f"{self.TRACE}{english}\n", translated=f"{self.TRACE}{german}\n"
                    )
                    self.assertIsInstance(raised, kind)
                    self.assertIn(f"saying {english!r}, so", str(raised))
                    self.assertNotIn("trace:", str(raised))
        self.outcome("true", "draft unchanged", translated=fatal[1])
        self.assertEqual(self.ran, [{**os.environ, "CI": "true", "LC_ALL": "C"}] * 2)

    def test_docs_say_how_ci_is_read_and_what_a_git_failure_reports(self):
        # history_missing strips CI before reading it, so " false " skips; the module docstring and
        # the CHANGELOG entry say so, as the history_missing docstring does. The entry also says a
        # git failure quotes git, that the two cases run git with LC_ALL=C, and what a German
        # locale would otherwise write in place of each of "fatal:" and "error:".
        entry = changelog_entry(HISTORY_ENTRY)
        for text in (" ".join(sys.modules[__name__].__doc__.split()), entry):
            self.assertIn("in any letter case or with surrounding spaces", text)
        self.assertIn("the first line of git's message that starts with `fatal:` or `error:`", entry)
        self.assertIn("run git with `LC_ALL=C`", entry)
        self.assertIn('a `fatal:` line would otherwise start with "Schwerwiegend:"', entry)
        self.assertIn('an `error:` line with "Fehler:"', entry)


STATUSES = ("Specified", "Implemented", "Tested in conformance")
README_STATUS = re.compile(r"\*\*(%s)\*\*" % "|".join(STATUSES))
SPEC_STATUS = re.compile(r"\*Status: (%s)\b" % "|".join(STATUSES).lower())
# Each protocol's GAP-ANALYSIS.md row for what the lists say of it: the start of the name both
# lists use, then the row.
GAP_ROWS = {
    "Google A2A": "A2A agent card identity",
    "Anthropic MCP": "MCP capability-based tool access",
    "OpenID Connect": "OAuth 2.0 / OIDC",
    "WebAuthn/FIDO2": "WebAuthn/FIDO2",
    "W3C Verifiable Credentials": "Verifiable Credential expression",
    "ATP (Agent Trust Protocol)": "ATP integration",
}


def complemented(text: str, end: str, bullet: str) -> list[str]:
    """Return the list items between "AIP is designed to complement" and the line starting with end."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("AIP is designed to complement"))
    stop = next(i for i, line in enumerate(lines) if i > start and line.startswith(end))
    return [line for line in lines[start:stop] if line.startswith(bullet)]


def statuses(items: list[str], pattern: re.Pattern[str]) -> dict[str, list[str]]:
    """Map each item's protocol name to the statuses it carries, capitalised as in STATUSES."""
    named = {}
    for item in items:
        name = re.match(r"- (?:\[|\*\*)([^\]*]+)", item).group(1)
        named[name] = [found.capitalize() for found in pattern.findall(item)]
    return named


def gap_status(row: str) -> str:
    """Return the status GAP-ANALYSIS.md gives a row: no code is Specified, some code is Implemented."""
    gap = (check_draft_sync.ROOT / "GAP-ANALYSIS.md").read_text(encoding="utf-8")
    cell = next(line.split("|")[2].strip() for line in gap.splitlines() if line.startswith(f"| {row} |"))
    return "Specified" if cell.startswith(("NOT IMPLEMENTED", "REMOVED")) else "Implemented"


class ComplementedProtocols(unittest.TestCase):
    """Each protocol AIP is designed to complement carries one status, in the README and in the spec."""

    def setUp(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        self.readme_items = complemented(readme, "## ", "- [")
        self.spec_items = complemented(spec, "This specification defines", "- **")
        self.readme = statuses(self.readme_items, README_STATUS)
        self.spec = statuses(self.spec_items, SPEC_STATUS)

    def lines(self, protocol: str) -> dict[str, str]:
        """Return the README line and the spec line whose protocol name starts with protocol."""
        return {
            "README.md": next(item for item in self.readme_items if item.startswith(f"- [{protocol}")),
            "AIP-SPEC.md": next(item for item in self.spec_items if item.startswith(f"- **{protocol}")),
        }

    def test_each_readme_line_carries_one_status(self):
        self.assertEqual(len(self.readme), 6, self.readme)
        self.assertEqual({name: found for name, found in self.readme.items() if len(found) != 1}, {})

    def test_each_spec_line_carries_one_status(self):
        self.assertEqual(len(self.spec), 6, self.spec)
        self.assertEqual({name: found for name, found in self.spec.items() if len(found) != 1}, {})

    def test_readme_and_spec_give_each_protocol_the_same_status(self):
        self.assertEqual(list(self.readme.values()), list(self.spec.values()))

    def status_of(self, named: dict[str, list[str]], protocol: str) -> list[str]:
        """Return the statuses of the one protocol in named whose name starts with protocol."""
        found = [status for name, status in named.items() if name.startswith(protocol)]
        self.assertEqual(len(found), 1, f"{protocol!r} names {len(found)} lines")
        return found[0]

    def test_status_matches_the_gap_analysis_row(self):
        # A protocol whose row says NOT IMPLEMENTED or REMOVED is Specified, and one whose row
        # reports code is Implemented, so neither list can claim code the gap analysis denies.
        # Every line has a row: a line without one would be checked against nothing.
        self.assertEqual(len(GAP_ROWS), len(self.readme))
        for name, row in GAP_ROWS.items():
            with self.subTest(protocol=name):
                self.assertEqual(self.status_of(self.readme, name), [gap_status(row)])
                self.assertEqual(self.status_of(self.spec, name), [gap_status(row)])

    def test_readme_names_the_gap_analysis_row_behind_each_status(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        sentence = next(line for line in readme.splitlines() if line.startswith("The rows behind these statuses"))
        named = re.search(r"\[GAP-ANALYSIS\.md\]\(GAP-ANALYSIS\.md\) \(([^)]*)\)", sentence)
        self.assertIsNotNone(named, "the sentence lists no GAP-ANALYSIS.md rows")
        self.assertEqual(named.group(1).split(", "), list(GAP_ROWS.values()))

    def test_openid_connect_lines_name_the_token_request_parameters(self):
        # The token handler reads client_id, client_assertion and client_assertion_type and no
        # assertion parameter, the one in which RFC 7523 Section 2.1 carries the JWT, so a line
        # that names the JWT-bearer grant type also names the parameters the request carries.
        gap = (check_draft_sync.ROOT / "GAP-ANALYSIS.md").read_text(encoding="utf-8")
        row = next(line for line in gap.splitlines() if line.startswith("| OAuth 2.0 / OIDC |"))
        parameters = ("`client_assertion`", "`client_id`", "`client_assertion_type`")
        terms = (*parameters, "no `assertion` parameter", "RFC 7523 Section 2.1")
        for name, line in {**self.lines("OpenID Connect"), "GAP-ANALYSIS.md": row}.items():
            with self.subTest(doc=name):
                self.assertEqual([term for term in terms if term not in line], [])

    def test_atp_lines_cite_a_place_that_names_the_transparency_log(self):
        # Section 6.5 specifies the combined score and names no transparency log; the Appendix
        # A.1 row for it does, so that table is what the lines cite for the statement.
        parts = spec_parts(check_draft_sync.SPEC.read_text(encoding="utf-8"))
        for name, line in self.lines("ATP (Agent Trust Protocol)").items():
            with self.subTest(doc=name):
                citation = re.search(r"transparency log \(([^)]*)\)", line)
                self.assertIsNotNone(citation, "the transparency-log statement cites nothing")
                cited = [part for part in parts if names_part(citation.group(1).replace("Section ", "§"), part)]
                self.assertTrue(cited, f"{citation.group(1)!r} names no part of AIP-SPEC.md")
                self.assertEqual([part for part in cited if "transparency log" not in parts[part]], [])

    def test_openid_connect_lines_name_the_oauth_token_endpoint(self):
        # The reference implementation serves an OAuth 2.0 token endpoint that accepts the
        # JWT-bearer grant type of RFC 7523 from a registered agent, so neither list nor the
        # gap analysis row says its OAuth 2.0 code was removed.
        gap = (check_draft_sync.ROOT / "GAP-ANALYSIS.md").read_text(encoding="utf-8")
        row = next(line for line in gap.splitlines() if line.startswith("| OAuth 2.0 / OIDC |"))
        for name, line in {**self.lines("OpenID Connect"), "GAP-ANALYSIS.md": row}.items():
            with self.subTest(doc=name):
                self.assertIn("OAuth 2.0 token endpoint", line)
                self.assertIn("RFC 7523", line)
                self.assertNotIn("removed", line.lower())

    def test_google_a2a_lines_name_the_identity_in_the_agent_card(self):
        # The agent card the reference implementation serves carries the agent's ID and its
        # registered public key in an `aim` extension, so neither list says that no AIP
        # identifier field was found in that card.
        for name, line in self.lines("Google A2A").items():
            with self.subTest(doc=name):
                self.assertIn("`aim` extension", line)
                self.assertNotIn("no aip identifier field", line.lower())
        self.assertEqual(self.readme["Google A2A Protocol"], ["Implemented"])
        self.assertEqual(self.spec["Google A2A"], ["Implemented"])

    def test_readme_defines_each_status_before_the_list(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        intro = next(line for line in readme.splitlines() if line.startswith("AIP is designed to complement"))
        self.assertEqual([status for status in STATUSES if f"**{status}**" not in intro], [])


class References(unittest.TestCase):
    def test_section_14_lists_every_rfc_the_text_cites(self):
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        listed = set(re.findall(r"^- RFC (\d{4}) — ", spec_parts(spec)["§14"], re.MULTILINE))
        cited = set(re.findall(r"\bRFC (\d{4})\b", spec))
        self.assertEqual(sorted(cited - listed), [], "RFCs AIP-SPEC.md cites and Section 14 does not list")


class GapAnalysisPriorities(unittest.TestCase):
    def test_priority_list_asks_for_the_id_token_and_not_for_oauth_again(self):
        # The OAuth 2.0 / OIDC row says the backend serves a token endpoint and that no code
        # issuing an OpenID Connect ID token was found, so the priority list asks for the ID
        # token and does not say to re-add OAuth 2.0.
        gap = (check_draft_sync.ROOT / "GAP-ANALYSIS.md").read_text(encoding="utf-8")
        priorities = gap.split("## Priority Implementation Order", 1)[1].split("\n---", 1)[0]
        items = [
            line for line in priorities.splitlines()
            if re.match(r"\d+\. ", line) and ("OAuth" in line or "OpenID" in line)
        ]
        self.assertEqual(len(items), 1, items)
        self.assertNotIn("re-add", items[0])
        self.assertIn("what is missing is an OpenID Connect ID token", items[0])
        row = next(line for line in gap.splitlines() if line.startswith("| OAuth 2.0 / OIDC |"))
        self.assertIn("serves an OAuth 2.0 token endpoint", row)
        self.assertIn("No code that issues an OpenID Connect ID token was found", row)


def unreleased_entries(changelog: str) -> dict[str, list[str]]:
    """Return the entries under each "### " heading of the CHANGELOG's Unreleased section.

    An entry starts at a line that opens with "- " and takes the lines under it, joined with
    single spaces; the "- " is dropped.
    """
    section = changelog.split("\n## [Unreleased]", 1)[1] if "\n## [Unreleased]" in changelog else ""
    section = re.split(r"^## ", section, maxsplit=1, flags=re.MULTILINE)[0]
    entries: dict[str, list[str]] = {}
    kind = ""
    for line in section.splitlines():
        if line.startswith("### "):
            kind = line[4:].strip()
        elif line.startswith("- "):
            entries.setdefault(kind, []).append(line[2:].strip())
        elif line.strip() and entries.get(kind):
            entries[kind][-1] += " " + line.strip()
    return entries


UNRELEASED_LOG = (
    "# Changelog\n\n## [Unreleased]\n\n### Changed\n\n- `AIP-SPEC.md` §3.1 defines the agent ID\n  another way.\n"
    "- `tests/test_agent_id.py` checks it.\n\n### Fixed\n\n- A fix.\n\n## [1.2.0-draft] - 2026-10-06\n\n"
    "### Changed\n\n- `AIP-SPEC.md` §6.2 becomes a table.\n"
)


class UnreleasedRequirementChanges(unittest.TestCase):
    """A change to a requirement of AIP-SPEC.md that no dated version carries yet."""

    def setUp(self):
        self.spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        self.version = check_draft_sync.spec_version(self.spec)
        self.changelog = check_draft_sync.CHANGELOG.read_text(encoding="utf-8")
        self.entries = unreleased_entries(self.changelog)

    def changed_sections(self) -> list[str]:
        """Return the sections of AIP-SPEC.md an unreleased Changed entry opens with, or skip without one."""
        sections = [
            match.group(1) for entry in self.entries.get("Changed", [])
            if (match := re.match(r"`AIP-SPEC\.md` (§\d+(?:\.\d+)*) ", entry))
        ]
        if not sections:
            self.skipTest("no unreleased Changed entry opens with a section of AIP-SPEC.md")
        return sections

    def test_entries_are_read_under_their_heading_from_the_unreleased_section_only(self):
        entries = unreleased_entries(UNRELEASED_LOG)
        self.assertEqual(
            entries,
            {
                "Changed": ["`AIP-SPEC.md` §3.1 defines the agent ID another way.", "`tests/test_agent_id.py` checks it."],
                "Fixed": ["A fix."],
            },
        )
        self.assertEqual(unreleased_entries("# Changelog\n\n## [1.2.0-draft] - 2026-10-06\n\n- An entry.\n"), {})

    def test_token_lifetime_change_is_filed_under_changed(self):
        # §5.4 replaces a fixed token lifetime with a maximum. That changes a requirement, as the
        # §3.1 entry does, so the entry is filed under Changed with it and not under Fixed.
        opening = "`AIP-SPEC.md` §5.4 says a JWT access token's lifetime SHOULD NOT exceed 2 hours"
        filed = [kind for kind, listed in self.entries.items() for entry in listed if entry.startswith(opening)]
        if not filed:
            self.skipTest("the §5.4 token lifetime entry is no longer unreleased")
        self.assertEqual(filed, ["Changed"])
        self.assertIn("§5.4", self.changed_sections())

    def test_version_note_names_each_section_whose_requirement_changed(self):
        # The text under the Version line is that version plus the unreleased changes, so a
        # version note above the abstract says so and names the sections whose requirement changed.
        sections = self.changed_sections()
        note = spec_parts(self.spec).get("version note", "")
        self.assertTrue(note, "AIP-SPEC.md has no version note above the abstract")
        self.assertIn(f"This text is {self.version}, dated ", note)
        self.assertIn("Unreleased", note)
        self.assertEqual([section for section in sections if not names_part(note, section)], [])

    def test_earlier_agent_id_rule_names_the_dated_text_that_carried_it(self):
        # §3.1 changed after the version on the Version line was dated, so the sentence on the
        # earlier rule names that version's text by its date instead of "Revisions up to" it.
        section = re.sub(r"\s+", " ", spec_parts(self.spec)["§3.1"])
        sentences = [sentence for sentence in SENTENCE_END.split(section) if "specified the agent ID as" in sentence]
        self.assertEqual(len(sentences), 1, sentences)
        self.assertNotIn("Revisions up to", sentences[0])
        named = re.search(r"The (\S+) text dated (\d{4}-\d{2}-\d{2}),", sentences[0])
        self.assertIsNotNone(named, "the sentence names no version text by its date")
        self.assertIn(f"\n## [{named.group(1)}] - {named.group(2)}\n", self.changelog)

    def test_readme_says_the_specification_has_changed_since_the_dated_version(self):
        self.changed_sections()
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        paragraph = re.sub(r"\s+", " ", blocks(draft_disclosure(readme))[0])
        self.assertNotIn(f"specification is {self.version},", paragraph)
        self.assertIn(f"is {self.version} with later changes", paragraph)
        self.assertIn("lists them under Unreleased", paragraph)


def paragraph(text: str, start: str) -> str:
    """Return the paragraph of text that begins with start, up to the next blank line."""
    lines = text.splitlines()
    first = next(i for i, line in enumerate(lines) if line.startswith(start))
    end = next((i for i in range(first, len(lines)) if not lines[i].strip()), len(lines))
    return "\n".join(lines[first:end])


class TrustFactorStatus(unittest.TestCase):
    # The reference implementation has a scoring function for each of the nine trust factors:
    # compliance, drift detection and user feedback are no longer stubs.

    def test_spec_status_says_all_nine_factors_are_scored(self):
        spec = (check_draft_sync.ROOT / "AIP-SPEC.md").read_text(encoding="utf-8")
        status = paragraph(spec, "**Per-factor implementation status")
        self.assertNotIn("stub", status.lower())
        self.assertIn("All nine factors have scoring functions", status)
        self.assertNotIn("three proposed factors", spec)

    def test_appendix_a1_row_names_no_stubbed_factor(self):
        spec = (check_draft_sync.ROOT / "AIP-SPEC.md").read_text(encoding="utf-8")
        row = a1_rows(spec)["§6 Trust Scoring (9-factor)"]
        self.assertNotIn("stub", row.lower())
        self.assertIn("All nine factors have scoring functions", row)

    def test_readme_lists_the_dropped_statement_as_a_change_since_the_draft(self):
        # §6.1 dropped its SHOULD NOT on stubbed factors with the stubs. The README's list of
        # statements the draft lacks quotes only what AIP-SPEC.md still says, and the dropped
        # statement is named once, among the changes made since the draft.
        spec = (check_draft_sync.ROOT / "AIP-SPEC.md").read_text(encoding="utf-8")
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        dropped = "SHOULD NOT treat the stubbed factors as validated by the reference implementation"
        self.assertNotIn(dropped, spec)
        lists = counted_lists(draft_disclosure(readme))
        lacking = [items for lead, items in lists if "not in Section 7.1 of the draft" in lead]
        self.assertEqual(len(lacking), 1, [lead for lead, _ in lists])
        self.assertEqual([item for item in lacking[0] if item[2:].strip('"') not in spec], [])
        named = [item for _, items in lists for item in items if dropped in item]
        self.assertEqual(len(named), 1, named)
        self.assertTrue(named[0].startswith("- §6.1 no longer says"), named[0])

    def test_readme_trust_use_case_names_no_stubbed_factor(self):
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        section = readme.split("### You run many agents", 1)[1].split("\n#", 1)[0]
        stops = paragraph(section, "Where it stops today:")
        self.assertNotIn("stub", stops.lower())
        self.assertIn("all nine factors", stops)

    def test_gap_analysis_lists_no_trust_factor_as_stub(self):
        gap = (check_draft_sync.ROOT / "GAP-ANALYSIS.md").read_text(encoding="utf-8")
        table = gap.split("### Trust Scoring (Section 6)", 1)[1].split("\n#", 1)[0]
        rows = [line.split("|")[1:3] for line in table.splitlines() if line.startswith("| ")]
        status = {cells[0].strip(): cells[1].strip() for cells in rows}
        factors = [name for name in status if re.fullmatch(r".+ factor \(\d+%\)", name)]
        self.assertEqual(len(factors), 9, factors)
        self.assertEqual([name for name in factors if not status[name].startswith("Complete")], [])
        self.assertTrue(status["9-factor algorithm (spec §6.1)"].startswith("9 of 9"))


class ReferenceProviderDid(unittest.TestCase):
    # The reference provider still issues did:aip:aim_<uuid> and its discovery document reports
    # providerDid did:aip:provider_opena2a, so the spec states the did:web form as its target.

    def setUp(self):
        self.spec = (check_draft_sync.ROOT / "AIP-SPEC.md").read_text(encoding="utf-8")

    def test_spec_section_3_2_says_the_reference_implementation_will_issue_did_web(self):
        profile = paragraph(self.spec, "where `<provider-host>` is the DNS name")
        self.assertNotIn("The reference implementation (AIM) issues `did:web:", profile)
        self.assertNotIn("identifies itself as `did:web:aim.opena2a.org`", profile)
        self.assertIn("will issue `did:web:aim.opena2a.org:agents:<uuid>`", profile)
        self.assertIn("`did:aip:provider_opena2a`", profile)

    def test_spec_section_10_1_says_its_sample_is_the_target_form(self):
        discovery = self.spec.split("### 10.1 Well-Known Endpoint", 1)[1].split("\n#", 1)[0]
        self.assertIn("\nThe sample shows the target form", discovery)
        note = paragraph(discovery, "The sample shows the target form")
        self.assertIn("`did:aip:provider_opena2a`", note)
        self.assertIn("no `publicKey`", note)

    def test_readme_names_the_change_since_the_draft(self):
        # Section 4.2 of draft -04 still says the reference implementation issues the did:web
        # form, and its Section 12 carries the discovery sample without the note.
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        items = [item for _, listed in counted_lists(draft_disclosure(readme)) for item in listed]
        named = [item for item in items if item.startswith("- §3.2 ")]
        self.assertEqual(len(named), 1, "no Internet-Draft list item starts '- §3.2 '")
        for claim in ("Section 4.2 of the draft", "§10.1", "Section 12 of the draft"):
            self.assertTrue(claim in named[0], f"the §3.2 item does not say {claim!r}")


if __name__ == "__main__":
    unittest.main()
