#!/usr/bin/env python3
"""Regression tests for scripts/check_draft_sync.py, the README link lists and Quick Start,
the prior-art attribution in README.md, AIP-SPEC.md and GAP-ANALYSIS.md, the JWT
access-token lifetime in AIP-SPEC.md §5.4, the status on each line of the two lists of
protocols AIP is designed to complement, the lists under the README's Internet-Draft paragraph,
the RFCs listed in AIP-SPEC.md §14, the GAP-ANALYSIS.md priority list, and the version note
AIP-SPEC.md carries while a change to a requirement is unreleased.

The draft sync cases run on small CHANGELOG and README texts built here, so
they do not depend on the repository's current pairing. One case reads the specification as of
the commit that made the paired draft and is skipped where git or that history is missing.
Runs on its own:
    python3 scripts/test_checks.py
python3 standard library only.
"""
from __future__ import annotations

import re
import shutil
import subprocess
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


NUMBER_WORDS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
)
COUNT = re.compile(r"\b(%s)\b" % "|".join(NUMBER_WORDS), re.IGNORECASE)
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
        found += [f"{word!r} in {sentence!r}" for sentence in sentences for word in COUNT.findall(sentence)]
    return found


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


def spec_when_draft_was_made(draft: str) -> str:
    """Return AIP-SPEC.md as of the last commit that changed the draft's txt.

    Skips the calling test without git, outside a checkout, in a shallow clone, where that commit
    can be missing, or when no commit in the history changed that file.
    """
    if shutil.which("git") is None:
        raise unittest.SkipTest("git is not installed")

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=check_draft_sync.ROOT, capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0:
            raise unittest.SkipTest(f"git {args[0]} failed here, so the text the draft was made from is not available")
        return result.stdout

    if git("rev-parse", "--is-shallow-repository").strip() == "true":
        raise unittest.SkipTest("shallow clone: the commit that made the draft can be missing")
    commit = git("log", "-1", "--format=%H", "--", f"{draft}.txt").strip()
    if not commit:
        raise unittest.SkipTest(f"no commit in this history changed {draft}.txt")
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
        """Return the paired draft, AIP-SPEC.md when it was made, AIP-SPEC.md now and the README list items."""
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        changelog = check_draft_sync.CHANGELOG.read_text(encoding="utf-8")
        draft, _ = check_draft_sync.pairing(changelog, check_draft_sync.spec_version(spec))
        if draft is None:
            self.skipTest("the CHANGELOG pairs no draft with the specification's version")
        readme = (check_draft_sync.ROOT / "README.md").read_text(encoding="utf-8")
        items = [item for _, listed in counted_lists(draft_disclosure(readme)) for item in listed]
        return draft, spec_when_draft_was_made(draft), spec, items

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


if __name__ == "__main__":
    unittest.main()
