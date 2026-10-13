#!/usr/bin/env python3
"""Regression tests for the check scripts in scripts/ and the .gitignore entries.

Run from the repository root:
    python3 -m unittest discover -s tests
python3 standard library only, except the isolated validate_examples.py run,
which needs the 'jsonschema' package and is skipped without it.
"""
from __future__ import annotations

import contextlib
import io
import math
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tokenize
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_draft_sync  # noqa: E402
import check_first_use  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)


def paired_draft() -> str:
    spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
    version = check_draft_sync.spec_version(spec)
    name, _ = check_draft_sync.pairing(check_draft_sync.CHANGELOG.read_text(encoding="utf-8"), version)
    if name is None or not (ROOT / f"{name}.txt").exists():
        raise unittest.SkipTest(f"the draft paired with {version} is not built")
    return name


class DraftSyncWholeWord(unittest.TestCase):
    def setUp(self) -> None:
        self.name = paired_draft()
        self.spec = check_draft_sync.SPEC.read_text(encoding="utf-8")

    def test_paired_draft_is_in_sync(self) -> None:
        self.assertEqual(check_draft_sync.check_draft(self.name, self.spec), [])

    def test_field_renamed_in_spec_is_reported(self) -> None:
        spec = self.spec.replace("behaviorTier", "behaviorTierX")
        problems = check_draft_sync.check_draft(self.name, spec)
        self.assertTrue(any("'behaviorTier'" in p and "no longer" in p for p in problems), problems)

    def problems_in_copy(self, suffix: str, old: str, new: str) -> list[str]:
        """check_draft on a copy of the paired draft whose .xml or .txt has old replaced by new."""

        def edit(text: str) -> str:
            self.assertIn(old, text)
            return text.replace(old, new)

        return self.problems_in_edited_copy(suffix, edit)

    def problems_in_edited_copy(self, suffix: str, edit: Callable[[str], str]) -> list[str]:
        """check_draft on a copy of the paired draft whose .xml or .txt is passed through edit."""
        with tempfile.TemporaryDirectory() as tmp:
            for ext in (".xml", ".txt"):
                shutil.copy(ROOT / f"{self.name}{ext}", Path(tmp) / f"{self.name}{ext}")
            edited = Path(tmp) / f"{self.name}{suffix}"
            edited.write_text(edit(edited.read_text(encoding="utf-8")), encoding="utf-8")
            original = check_draft_sync.ROOT
            check_draft_sync.ROOT = Path(tmp)
            try:
                return check_draft_sync.check_draft(self.name, self.spec)
            finally:
                check_draft_sync.ROOT = original

    def test_field_renamed_in_draft_is_reported(self) -> None:
        problems = self.problems_in_copy(".txt", "behaviorTier", "behaviorTierX")
        self.assertTrue(any("lacks 'behaviorTier'" in p for p in problems), problems)

    def test_paired_draft_names_no_stream(self) -> None:
        xml = (ROOT / f"{self.name}.xml").read_text(encoding="utf-8")
        self.assertIsNone(check_draft_sync.flagged_stream(xml), f"{self.name}.xml names a stream")

    def test_stream_in_draft_is_reported(self) -> None:
        problems = self.problems_in_copy(".xml", 'ipr="trust200902"', 'ipr="trust200902"\n     submissionType="IETF"')
        self.assertTrue(any("SUBMISSION_TYPE_UNEXPECTED" in p for p in problems), problems)

    def test_stream_idnits_accepts_is_not_reported(self) -> None:
        problems = self.problems_in_copy(
            ".xml", 'ipr="trust200902"', 'ipr="trust200902"\n     submissionType="independent"'
        )
        self.assertFalse(any("submissionType" in p for p in problems), problems)

    def test_invalid_stream_in_draft_is_reported(self) -> None:
        problems = self.problems_in_copy(
            ".xml", 'ipr="trust200902"', 'ipr="trust200902"\n     submissionType="Independant"'
        )
        self.assertTrue(any("'Independant'" in p and "SUBMISSION_TYPE_INVALID" in p for p in problems), problems)
        self.assertFalse(any("SUBMISSION_TYPE_UNEXPECTED" in p for p in problems), problems)

    def test_stream_written_as_a_reference_is_reported(self) -> None:
        problems = self.problems_in_copy(
            ".xml", 'ipr="trust200902"', 'ipr="trust200902"\n     submissionType="&#32;independent"'
        )
        self.assertTrue(any("'&#32;independent'" in p and "SUBMISSION_TYPE_INVALID" in p for p in problems), problems)

    def test_stream_is_trimmed_before_references_as_idnits_does(self) -> None:
        def streams(value: str) -> tuple[str | None, str | None]:
            xml = f'<rfc submissionType="{value}"/>'
            return check_draft_sync.flagged_stream(xml), check_draft_sync.invalid_stream(xml)

        # idnits 3.1.0 trims the attribute text as written with JavaScript's trim() and then leaves
        # these references undecoded, so it reports SUBMISSION_TYPE_INVALID for each value.
        for invalid in ("&#32;independent", "&#9;independent", "&#160;independent", "&#10;", "IETF&#32;"):
            self.assertEqual(streams(invalid), (None, invalid), invalid)
        # trim() keeps U+0085, which str.strip() removes, and removes U+FEFF, which str.strip() keeps.
        self.assertEqual(streams("\u0085independent"), (None, "\u0085independent"))
        self.assertEqual(streams("\ufeffindependent"), (None, None))
        self.assertEqual(streams("\ufeffIETF\u3000"), ("\ufeffIETF\u3000", None))
        # A space written as a literal character, or "&amp;#32;" text, reads as before.
        self.assertEqual(streams("\tindependent\n"), (None, None))
        self.assertEqual(streams("&amp;#32;IETF"), (None, "&#32;IETF"))

    def test_invalid_stream_compares_in_lower_case(self) -> None:
        def stream(xml: str) -> str | None:
            return check_draft_sync.invalid_stream(xml)

        self.assertEqual(stream('<rfc submissionType="Independant"/>'), "Independant")
        self.assertEqual(stream('<rfc submissionType="ISE"/>'), "ISE")
        self.assertEqual(stream('<rfc submissionType=" ISE "/>'), " ISE ")
        for valid in ("IETF", "iab", "Irtf", "INDEPENDENT", "independent", "Editorial"):
            self.assertIsNone(stream(f'<rfc submissionType="{valid}"/>'), valid)
        # idnits 3.1.0 removes whitespace around the value and reports nothing for an empty one.
        for skipped in ("", "  ", " independent", "independent "):
            self.assertIsNone(stream(f'<rfc submissionType="{skipped}"/>'), repr(skipped))
        self.assertIsNone(stream('<rfc docName="d"/>'))

    def test_flagged_stream_reads_the_parsed_rfc_element(self) -> None:
        def stream(xml: str) -> str | None:
            return check_draft_sync.flagged_stream(xml)

        self.assertEqual(stream('<rfc docName="d" submissionType="IETF"/>'), "IETF")
        self.assertEqual(stream('<rfc docName="d"\n     submissionType = "iab"/>'), "iab")
        self.assertEqual(stream('<rfc submissionType="IRTF"/>'), "IRTF")
        self.assertEqual(stream('<rfc title="a>b" submissionType="IETF"/>'), "IETF")
        self.assertEqual(stream('<rfc submissionType=" IETF "/>'), " IETF ")
        self.assertIsNone(stream('<rfc docName="d" submissionType="independent"/>'))
        self.assertIsNone(stream('<rfc docName="d" submissionType="editorial"/>'))
        self.assertIsNone(stream('<!-- <rfc submissionType="IETF"> --><rfc docName="d"/>'))
        self.assertIsNone(stream('<rfc docName="d"><t>submissionType="IETF"</t></rfc>'))
        self.assertIsNone(stream('<rfc docName="d" category="std"/>'))

    def test_not_well_formed_draft_is_reported(self) -> None:
        problems = self.problems_in_copy(".xml", "</rfc>", "")
        self.assertTrue(any("not well-formed xml" in p for p in problems), problems)

    def test_paired_draft_tags_every_keyword(self) -> None:
        root = ET.fromstring((ROOT / f"{self.name}.xml").read_text(encoding="utf-8"))
        self.assertEqual(check_draft_sync.untagged_keywords(root), [])

    def test_untagged_keyword_in_draft_is_reported(self) -> None:
        problems = self.problems_in_copy(".xml", "<bcp14>OPTIONAL</bcp14>", "OPTIONAL")
        self.assertTrue(any("'OPTIONAL'" in p and "MISSING_REQLEVEL_REF" in p for p in problems), problems)

    def test_untagged_draft_counts_keywords_idnits_checks(self) -> None:
        xml = (ROOT / f"{self.name}.xml").read_text(encoding="utf-8")
        problems = self.problems_in_edited_copy(".xml", lambda text: re.sub(r"</?bcp14>", "", text))
        counts = [re.search(r"(\d+) BCP 14 keyword\(s\).*; (\d+) of them, in <t> or <li> text", p) for p in problems]
        counts = [(int(m.group(1)), int(m.group(2))) for m in counts if m]
        self.assertEqual(len(counts), 1, problems)
        total, checked = counts[0]
        self.assertEqual(total, xml.count("<bcp14>"))
        self.assertLess(checked, total)
        self.assertFalse(any("reports each" in p for p in problems), problems)

    def test_untagged_count_names_only_keywords_idnits_reads(self) -> None:
        probe = (
            "<section><name>Probe SHALL heading</name><ul><li>List item MUST hold.</li>"
            "<li><t>Para in li SHOULD hold.</t></li></ul><dl><dt>Term</dt><dd>Definition MAY apply.</dd></dl>"
            "<table><tbody><tr><td>Cell REQUIRED here</td></tr></tbody></table>"
            "<t>Plain para OPTIONAL here <em>emph MUST NOT</em> tail RECOMMENDED.</t></section>"
        )
        problems = self.problems_in_copy(".xml", "<middle>", "<middle>" + probe)
        counts = [re.search(r"(\d+) BCP 14 keyword\(s\).*; (\d+) of them, in <t> or <li> text", p) for p in problems]
        counts = [(int(m.group(1)), int(m.group(2))) for m in counts if m]
        # idnits 3.1.0 reports 4 MISSING_BCP14_TAGS on this probe: none for <name>, <dd>, <td> or <em>.
        self.assertEqual(counts, [(8, 4)], problems)
        reported = [u.keyword for u in check_draft_sync.untagged_keywords(ET.fromstring(probe)) if u.counted]
        self.assertEqual(reported, ["MUST", "SHOULD", "OPTIONAL", "RECOMMENDED"])

    def test_untagged_keywords_skips_tagged_and_verbatim_text(self) -> None:
        def keywords(xml: str) -> list[str]:
            return [u.keyword for u in check_draft_sync.untagged_keywords(ET.fromstring(xml))]

        self.assertEqual(
            keywords(
                "<rfc><t>A <bcp14>MUST</bcp14> and a MAY.</t>"
                "<artwork>MUST</artwork><sourcecode>SHOULD</sourcecode></rfc>"
            ),
            ["MAY"],
        )
        self.assertEqual(keywords("<rfc><t>It MUST\n      NOT be</t></rfc>"), ["MUST NOT"])
        self.assertEqual(keywords('<rfc><t><xref target="x"/> SHOULD hold</t></rfc>'), ["SHOULD"])
        self.assertEqual(keywords("<rfc><t>AUTH_REQUIRED, MAYBE and must</t></rfc>"), [])
        self.assertEqual(keywords("<rfc><t>It is NOT\n RECOMMENDED</t></rfc>"), ["NOT RECOMMENDED"])
        self.assertEqual(
            keywords(
                "<rfc><t><bcp14><em>MUST</em></bcp14> <sourcecode><x>SHALL</x></sourcecode>"
                "<artwork><svg><text>SHOULD</text></svg></artwork> then MAY</t></rfc>"
            ),
            ["MAY"],
        )

    def test_untagged_keywords_marks_the_boilerplate_paragraph(self) -> None:
        xml = (
            '<rfc><t>The key words "MUST" and "MAY" in this document are to be interpreted as'
            ' described in BCP 14 <xref target="RFC2119"/>.</t><t>It SHOULD hold.</t></rfc>'
        )
        found = [(u.keyword, u.boilerplate) for u in check_draft_sync.untagged_keywords(ET.fromstring(xml))]
        self.assertEqual(found, [("MUST", True), ("MAY", True), ("SHOULD", False)])

    def test_text_split_by_a_child_element_is_joined_as_idnits_joins_it(self) -> None:
        def found(xml: str) -> list[tuple[str, bool, bool]]:
            return [
                (u.keyword, u.boilerplate, u.counted) for u in check_draft_sync.untagged_keywords(ET.fromstring(xml))
            ]

        # idnits 3.1.0 trims each text segment of a <t> and joins the segments with no separator, so
        # this reads '"MAY"in this document', no boilerplate: it reports 2 MISSING_BCP14_TAGS.
        scope_after_child = (
            '<rfc><t>The key words "MUST" and "MAY" <xref target="BCP14"/> in this document are to be'
            " interpreted as described.</t></rfc>"
        )
        self.assertEqual(found(scope_after_child), [("MUST", False, True), ("MAY", False, True)])
        keywords_after_child = (
            '<rfc><t>The key words <xref target="BCP14"/> "MUST" and "MAY" in this document are to be'
            " interpreted as described.</t></rfc>"
        )
        self.assertEqual(found(keywords_after_child), [("MUST", False, True), ("MAY", False, True)])
        # This reads "BeforeMUST after", which holds no keyword: idnits reports none.
        self.assertEqual(
            found('<rfc><t>Before <xref target="RFC2119"/> MUST after</t></rfc>'), [("MUST", False, False)]
        )
        self.assertEqual(
            found('<rfc><t>It MUST <xref target="RFC2119"/> hold; <em>x</em>: it MAY too</t></rfc>'),
            [("MUST", False, False), ("MAY", False, True)],
        )
        # Children after its " in this document ", as in the RFC 8174 boilerplate, leave the paragraph whole.
        boilerplate = (
            '<rfc><t>The key words "MUST" and "MAY" in this document are to be interpreted as described in'
            ' BCP 14 <xref target="RFC2119"/> <xref target="RFC8174"/> when they appear in all capitals.</t></rfc>'
        )
        self.assertEqual(found(boilerplate), [("MUST", True, False), ("MAY", True, False)])

    def test_text_split_by_a_child_element_is_counted_in_a_draft(self) -> None:
        def counts(paragraph: str) -> list[tuple[int, int]]:
            problems = self.problems_in_copy(".xml", "<middle>", f"<middle><section><name>P</name>{paragraph}</section>")
            found = [re.search(r"(\d+) BCP 14 keyword\(s\).*; (\d+) of them, in <t> or <li> text", p) for p in problems]
            return [(int(m.group(1)), int(m.group(2))) for m in found if m]

        self.assertEqual(
            counts(
                '<t>The key words "MUST" and "MAY" <xref target="BCP14"/> in this document are to be'
                " interpreted as described.</t>"
            ),
            [(2, 2)],
        )
        self.assertEqual(counts('<t>Before <xref target="RFC2119"/> MUST after</t>'), [(1, 0)])

    def test_count_differs_from_idnits_for_reference_whitespace_pis_and_cdata(self) -> None:
        def counts(paragraph: str) -> list[tuple[int, int]]:
            problems = self.problems_in_copy(".xml", "<middle>", f"<middle><section><name>P</name>{paragraph}</section>")
            found = [re.search(r"(\d+) BCP 14 keyword\(s\).*; (\d+) of them, in <t> or <li> text", p) for p in problems]
            return [(int(m.group(1)), int(m.group(2))) for m in found if m]

        # idnits 3.1.0 trims each text segment as written and keeps "&#160;", so it reads
        # "Implementations MUST&#160;&#160;support it." and reports 1 MISSING_BCP14_TAGS. The parser
        # decodes the reference to U+00A0 before the check trims it, so the check reads
        # "Implementations MUSTsupport it." and counts 0.
        self.assertEqual(
            counts('<t>Implementations MUST&#160;<xref target="RFC2119"/>&#160;support it.</t>'), [(1, 0)]
        )
        # idnits splits the text at a processing instruction or CDATA section and reports none here;
        # the parser drops the one and merges the other into the text, so the check counts 1.
        self.assertEqual(counts("<t>Before <?pi x?> MUST after</t>"), [(1, 1)])
        self.assertEqual(counts("<t>Before<![CDATA[x]]> MUST after</t>"), [(1, 1)])

    def test_boilerplate_search_matches_the_idnits_pattern(self) -> None:
        idnits = re.compile(r"The key\s?words .+? in this document .+?.", re.IGNORECASE | re.DOTALL)
        texts = [
            'The key words "MUST" in this document are to be interpreted.',
            "the KEYWORDS x In This Document ab",
            "The key words x in this document ab",
            "The key words x in this document a",
            "The key words  in this document ab",
            "The key words x in this documentab",
            "in this document ab. The key words x",
            "The key words The key words x in this document ab",
            "The key words in this document in this document ab",
            "The key\twords x in this document\nab",
            "The key  words x in this document ab",
            "",
        ]
        for text in texts:
            self.assertEqual(check_draft_sync.bcp14_boilerplate(text), idnits.search(text) is not None, text)

    def test_boilerplate_search_takes_linear_time(self) -> None:
        root = ET.fromstring("<rfc><t>" + "The key words " * 20000 + "MUST</t></rfc>")
        start = time.monotonic()
        found = check_draft_sync.untagged_keywords(root)
        self.assertLess(time.monotonic() - start, 2.0)
        self.assertEqual([(u.keyword, u.boilerplate) for u in found], [("MUST", False)])

    def test_untagged_keywords_walks_deep_nesting(self) -> None:
        depth = sys.getrecursionlimit() + 200
        root = ET.fromstring("<rfc>" + "<t>" * depth + "MUST" + "</t>" * depth + "</rfc>")
        self.assertEqual([u.keyword for u in check_draft_sync.untagged_keywords(root)], ["MUST"])

    def test_carries_matches_whole_words(self) -> None:
        self.assertTrue(check_draft_sync.carries('{"behaviorTier": 3}', "behaviorTier"))
        self.assertFalse(check_draft_sync.carries('{"behaviorTierX": 3}', "behaviorTier"))
        self.assertFalse(check_draft_sync.carries('{"xbehaviorTier": 3}', "behaviorTier"))
        self.assertTrue(check_draft_sync.carries('{"trustLevel": 3}', '"trustLevel":'))
        self.assertTrue(check_draft_sync.carries("the clock-skew bound of", "clock-skew bound"))
        self.assertFalse(check_draft_sync.carries("the clock-skew bounds of", "clock-skew bound"))


class DraftDisclosure(unittest.TestCase):
    DRAFT, VERSION = "draft-fane-opena2a-aip-09", "9.9.9-draft"
    SUBMITTED = "`draft-fane-opena2a-aip-09` (submitted 2026-10-06) is the current datatracker revision."

    def problems(self, pairing: str, readme: str) -> list[str]:
        changelog = f"## [{self.VERSION}] - 2026-10-06\n\nDraft pairing: `{self.DRAFT}` pairs with {self.VERSION}. {pairing}\n"
        readme = f"**Internet-Draft.** `{self.DRAFT}` carries {self.VERSION}. {readme}\n"
        return check_draft_sync.disclosure_problems(readme, changelog, self.VERSION, self.DRAFT)

    def test_readme_discloses_the_paired_draft(self) -> None:
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        version = check_draft_sync.spec_version(spec)
        changelog = check_draft_sync.CHANGELOG.read_text(encoding="utf-8")
        name, _ = check_draft_sync.pairing(changelog, version)
        readme = check_draft_sync.README.read_text(encoding="utf-8")
        self.assertEqual(check_draft_sync.disclosure_problems(readme, changelog, version, name), [])

    def test_submitted_draft_with_its_date_passes(self) -> None:
        self.assertEqual(self.problems(self.SUBMITTED, "It was submitted 2026-10-06."), [])

    def test_pairing_must_record_the_submission(self) -> None:
        problems = self.problems("It was rendered.", "It was submitted 2026-10-06.")
        self.assertTrue(any("records no submission" in p for p in problems), problems)

    def test_submission_of_another_draft_does_not_count(self) -> None:
        pairing = self.SUBMITTED.replace("-09", "-08")
        problems = self.problems(pairing, "It was submitted 2026-10-06.")
        self.assertTrue(any("records no submission" in p for p in problems), problems)

    def test_submission_must_say_it_is_the_current_revision(self) -> None:
        pairing = "`draft-fane-opena2a-aip-09` (submitted 2026-10-06) was withdrawn."
        problems = self.problems(pairing, "It was submitted 2026-10-06.")
        self.assertTrue(any("records no submission" in p for p in problems), problems)

    def test_readme_must_name_the_submission_date(self) -> None:
        problems = self.problems(self.SUBMITTED, "It was submitted.")
        self.assertTrue(any("'2026-10-06'" in p for p in problems), problems)


class SpecRequirementLevels(unittest.TestCase):
    def test_spec_uses_only_bcp14_forms(self) -> None:
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"\b(?:MUST|SHALL|SHOULD)\s+NEVER\b", spec), [])


class ImplementationStatusChallenge(unittest.TestCase):
    ROUTE = "`/api/v1/agents/{agentId}/challenge`"

    def section5_row(self) -> list[str]:
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        for line in spec.splitlines():
            if line.startswith("| §5 Verification (challenge-response) |"):
                return [cell.strip() for cell in line.strip().strip("|").split("|")]
        self.fail("Appendix A.1 has no §5 Verification (challenge-response) row")

    def test_row_agrees_with_readme_on_the_unserved_route(self) -> None:
        readme = check_draft_sync.README.read_text(encoding="utf-8")
        self.assertIn("advertises the challenge endpoint in its discovery document but does not serve that route", readme)
        _, status, note = self.section5_row()
        self.assertEqual(status, "Partial")
        self.assertIn(self.ROUTE, note)
        self.assertIn("registers no such route", note)


class ImplementationStatusTrustScoring(unittest.TestCase):
    def line(self, path: Path, prefix: str) -> str:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(prefix):
                return line
        self.fail(f"{path.name} has no line starting with {prefix}")

    def test_section_6_1_scopes_the_reference_calculator_to_algorithm_version_1(self) -> None:
        paragraph = self.line(check_draft_sync.SPEC, "**Reference implementation.**")
        self.assertNotIn("The 9-factor algorithm above is implemented", paragraph)
        self.assertIn("algorithm version 1", paragraph)
        status = self.line(check_draft_sync.SPEC, "**Composition implementation status (reference implementation,")
        self.assertIn("does not implement the unscored state", status)
        self.assertIn("`algorithmVersion`", status)

    def test_row_is_partial_and_names_the_unscored_state(self) -> None:
        row = self.line(check_draft_sync.SPEC, "| §6 Trust Scoring (9-factor) |")
        _, status, note = [cell.strip() for cell in row.strip().strip("|").split("|")]
        self.assertEqual(status, "Partial")
        self.assertIn("algorithm version 1", note)
        self.assertIn("unscored state", note)

    def test_gap_analysis_tracks_the_unscored_state(self) -> None:
        row = self.line(ROOT / "GAP-ANALYSIS.md", "| Unscored state and algorithm version (spec §6.1")
        _, status, _ = [cell.strip() for cell in row.strip().strip("|").split("|")]
        self.assertTrue(status.startswith("NOT IMPLEMENTED"), status)


# `opena2a-cli identity` subcommands and the options each accepts, as of opena2a-cli 0.10.13.
# `identity trust` also exists; add it with its options before a document quotes it. The
# §9.1 status note quotes `identity log` without an option, so none of its options is listed;
# add each one before a document quotes it. `create` accepts `--server` and `--api-key`
# (handleServerCreate). The CLI registers no short option for `identity`, so each one quoted
# is reported.
CLI_IDENTITY_OPTIONS = {
    "create": {"--name", "--server", "--api-key"},
    "verify": {"--data", "--signature", "--public-key"},
    "log": set(),
}


def unknown_cli_usage(text: str) -> list[str]:
    """Return each subcommand or option of a quoted `opena2a-cli identity` command the CLI lacks.

    The CLI's usage text calls it `opena2a`, so `opena2a identity` is read the same way, and a
    command continued with a backslash is read as one line.
    """
    text = re.sub(r"\\\r?\n", " ", text)
    problems = []
    for sub, rest in re.findall(r"\bopena2a(?:-cli)? identity ([a-z-]+)([^\n`]*)", text):
        if sub not in CLI_IDENTITY_OPTIONS:
            problems.append(f"identity {sub}")
            continue
        options = re.findall(r"(?<!\S)--?[a-zA-Z][a-zA-Z-]*", rest)
        problems += [f"identity {sub} {option}" for option in options if option not in CLI_IDENTITY_OPTIONS[sub]]
    return problems


class CliCommandsInDocs(unittest.TestCase):
    def test_spec_and_readme_quote_only_commands_the_cli_has(self) -> None:
        for path in (check_draft_sync.SPEC, check_draft_sync.README):
            text = path.read_text(encoding="utf-8")
            self.assertIn("opena2a-cli identity create --name", text, path.name)
            self.assertEqual(unknown_cli_usage(text), [], path.name)

    def test_unknown_subcommand_and_option_are_reported(self) -> None:
        text = (
            "npx opena2a-cli identity create --name a --type custom\n"
            "npx opena2a-cli identity verify --name a\n"
            "npx opena2a-cli identity check-trust --name a --min-score 0.7\n"
            "npx opena2a-cli identity verify --data d --signature s --public-key k\n"
        )
        self.assertEqual(
            unknown_cli_usage(text),
            ["identity create --type", "identity verify --name", "identity check-trust"],
        )

    def test_continued_line_bin_name_and_short_option_are_read(self) -> None:
        cases = {
            "npx opena2a-cli identity verify \\\n  --name a --min-score 0.7": [
                "identity verify --name",
                "identity verify --min-score",
            ],
            "npx opena2a identity check-trust --min-score 0.7": ["identity check-trust"],
            "npx opena2a-cli identity create --name a -t custom": ["identity create -t"],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(unknown_cli_usage(text), expected)

    def test_server_options_of_create_are_accepted(self) -> None:
        text = "npx opena2a-cli identity create --name a --server cloud --api-key k"
        self.assertEqual(unknown_cli_usage(text), [])


class PairingIdnitsCount(unittest.TestCase):
    def paragraph(self) -> str:
        changelog = check_draft_sync.CHANGELOG.read_text(encoding="utf-8")
        section, _ = check_draft_sync.version_section(changelog, "1.2.0-draft")
        return check_draft_sync.pairing_paragraph(section, "1.2.0-draft")[1]

    def test_warning_count_names_the_day_it_was_measured(self) -> None:
        # idnits adds DOC_DATE_IN_PAST once it runs more than three and a half days after the
        # start of the document date, so the -04 txt reports 6 warnings on its render date and
        # 7 from the afternoon of 2026-10-09 on.
        paragraph = self.paragraph()
        self.assertIn("0 errors and 6 warnings on 2026-10-06", paragraph)
        self.assertIn("a seventh, `DOC_DATE_IN_PAST`,", paragraph)

    @staticmethod
    def warns(at: datetime) -> bool:
        # idnits 3.1.0 warns when Math.round(days from now back to local midnight of the document
        # date) is below -3. Math.round rounds a half up, so exactly -3.5 days is still -3.
        days = (datetime(2026, 10, 6) - at) / timedelta(days=1)
        return math.floor(days + 0.5) < -3

    def test_first_instant_that_warns_is_one_millisecond_after_noon(self) -> None:
        # The first instant that warns is 12:00:00.001 local on the third day after the
        # document date, not the first whole minute after noon.
        noon = datetime(2026, 10, 9, 12)
        self.assertFalse(self.warns(noon))
        self.assertTrue(self.warns(noon + timedelta(milliseconds=1)))

    def test_seventh_warning_is_dated_by_the_idnits_rule(self) -> None:
        # Stepping in whole minutes, the first whole minute that warns is 12:01 local on the
        # third day after the document date.
        day = 24 * 60
        start = datetime(2026, 10, 6)
        minutes = next(m for m in range(7 * day) if self.warns(start + timedelta(minutes=m)))
        first = start + timedelta(minutes=minutes)
        self.assertEqual(first, datetime(2026, 10, 9, 12, 1))
        paragraph = self.paragraph()
        self.assertIn("more than three and a half days after the start of the document date", paragraph)
        self.assertIn(f"from the afternoon of {first.date().isoformat()} on", paragraph)
        self.assertNotIn("2026-10-10", paragraph)

    def test_a_later_section_records_the_two_corrections_made_in_place(self) -> None:
        # The idnits sentence was edited in place after 1.2.0-draft was dated: the warning names
        # and the measurement date were added, then the DOC_DATE_IN_PAST boundary moved from
        # 2026-10-10 to the afternoon of 2026-10-09. An entry above that heading records both.
        changelog = check_draft_sync.CHANGELOG.read_text(encoding="utf-8")
        later = changelog[: changelog.index("\n## [1.2.0-draft]")]
        entries = [" ".join(e.split()) for e in re.findall(r"^- .*(?:\n  .*)*", later, flags=re.MULTILINE)]
        terms = (
            "1.2.0-draft pairing paragraph",
            "0 errors and 6 warnings on 2026-10-06",
            "`DOC_DATE_IN_PAST`",
            "from 2026-10-10 on",
            "from the afternoon of 2026-10-09 on",
        )
        recorded = [entry for entry in entries if all(term in entry for term in terms)]
        self.assertTrue(recorded, f"no entry above the 1.2.0-draft heading names all of {terms}")


class GapAnalysisDefersToAppendix(unittest.TestCase):
    """GAP-ANALYSIS.md points to Appendix A.1 as the current status record and agrees with it."""

    GAP = ROOT / "GAP-ANALYSIS.md"
    MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
    # The common abbreviations of the month names.
    ABBREVIATIONS = "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec"
    # The quarters and halves of a year.
    PERIODS = "Q[1-4]|H[12]"

    @staticmethod
    def slug(heading: str) -> str:
        return re.sub(r"[^a-z0-9 _-]", "", heading.strip().lower()).replace(" ", "-")

    def gap(self) -> str:
        return self.GAP.read_text(encoding="utf-8")

    def row(self, name: str) -> str:
        for line in self.gap().splitlines():
            if line.startswith(f"| {name}"):
                return line
        self.fail(f"GAP-ANALYSIS.md has no {name} row")

    def status(self, name: str) -> str:
        return self.row(name).strip().strip("|").split("|")[1].strip()

    @classmethod
    def finished(cls, items: list[str]) -> list[str]:
        """Return each priority list item that is marked finished or asks for trust scoring.

        "done", "complete" and "completed" mark an item as finished, in any letter case. Of these,
        "complete" is no mark where an object follows it: a space and a word with a letter, as in
        "complete the depth limit enforcement", "a complete runtime protocol" and "complete
        in-browser key storage", or a space, a number, a space and such a word, as in "complete 3
        remaining checks". That word is not and, but, or, as, at, by, for, in, on, since or with,
        in any letter case, and it does not start a date that, with the closed asides after it,
        ends the item, stands before a punctuation mark, after a space or not, that no letter,
        digit or underscore follows, or stands before a space and an opening parenthesis or square
        bracket, that of an aside that is not closed, whatever follows it. An aside is no object.
        It is closed where a closing parenthesis follows its opening parenthesis with no other
        parenthesis in between, or a closing square bracket its opening square bracket with no
        other square bracket in between, and a date takes every closed aside that follows it, each
        after a space. So "complete 3 (of 5) remaining checks" and "complete Q4-2026 [1]
        conformance checks" hold a date and a closed aside that a word follows, and "complete" is
        no mark there. A date before an aside that is not closed leaves "complete" a mark: an
        aside with no closing parenthesis or bracket, as in "complete Q4-2026 (Discovery table
        above", or one that holds a parenthesis or bracket of its own kind, as in "complete
        Q4-2026 (see (a) and (b)) conformance checks". A date is one or more parts with a space, a
        punctuation mark, or a full stop or comma and a space between each two: a part is a month
        name, the abbreviation of one (Jan to Dec, and Sept), a quarter (Q1 to Q4), a half-year
        (H1 or H2) or a number, in any letter case, so "Oct", "Q4 2026", "Q4-2026", "2026-Q4",
        "Q4/2026", "Oct-2026", "2026-Oct", "3-Oct-2026", "Oct. 2026" and "October 3, 2026" are
        dates. An abbreviation takes the full stop right after it into the date, where no letter,
        digit or underscore follows that full stop, so "complete Sept. conformance checks" holds
        the date "Sept.", which a word follows, and no date "Sept" before a full stop. A full stop
        after a month name, a quarter, a half-year or a number is a punctuation mark. A date takes
        every part that follows it, so "complete Oct. 2026 conformance checks" holds the date
        "Oct. 2026", which a word follows, and no date "Oct" before a full stop. A word runs up to
        a space or to a punctuation mark that no letter, digit or underscore follows, so
        "in-browser", "802.1X", "Octet" and "Q4-based" are each one word, and neither "in-browser"
        nor "inside" is "in", nor is "Octet" "Oct" or "Q4-based" a date. Where "complete" opens
        the item's title, it is also no mark where "and", a word and an object follow it, as in
        "Complete and publish the DID resolver". So "complete" is still a mark at the end of an
        item and before punctuation, one of those words or such a date, as in "complete 2026-10",
        "complete and served", "(complete October 2026)", "(complete Oct 2026)", "(complete
        Sept.)", "(complete Q4 2026)", "(complete Q4-2026)", "(complete H2 2026)", "(complete 3
        October 2026)" and "complete Q4-2026 (Discovery table above)", and where it opens a title
        such as "Complete 2026-10" or "Complete and served". It is no mark before a date that a
        word follows, as in "complete Q4-2026 conformance checks" and "complete Oct the backend".
        A finished item worded "complete per Appendix A.1", "complete from 2026-10", "complete Q4
        2026 and served" or "complete Sept. Served by the backend" is not reported, and neither is
        one dated "complete 2026Q4": with nothing between the year and the quarter, that is one
        word with a letter. Nor is "complete Q4-2026(Discovery table above)": with no space before
        it, the parenthesis that a letter follows joins the date and "Discovery" into one word.
        Nor is "complete Q4-2026 (Discovery table above) and served by the backend": a word
        follows the closed aside.
        """
        # A word ends where neither a letter, digit or underscore nor a punctuation mark and one of
        # those follows.
        end = r"(?![^\w\s]?\w)"
        word = r"\w+(?:[^\w\s]\w+)*"
        # The full stop right after an abbreviation belongs to it, unless a letter, digit or
        # underscore follows: there it is the punctuation mark before the next part or word.
        part = rf"(?:{cls.MONTHS}|(?:{cls.ABBREVIATIONS})(?:\.(?!\w))?|{cls.PERIODS}|\d+)"
        # A date takes every part it can and gives none back, so "Oct. 2026 conformance" holds no
        # date "Oct" that a full stop follows.
        date = rf"(?>{part}(?:(?:[.,]\s|[^\w\s]|\s){part})*)"
        # A closed aside: a space, an opening parenthesis or square bracket and the closing one of
        # its kind, with no other of that kind in between.
        aside = r"\s+(?:\([^()]*\)|\[[^\[\]]*\])"
        # A date takes every closed aside after it and gives none back, so "Q4-2026 [1]
        # conformance" holds no date that stands before a space and an opening bracket. With those
        # asides, a date leaves "complete" a mark only where it ends the item, stands before a
        # punctuation mark, after a space or not, that no letter, digit or underscore follows, or
        # stands before a space and an opening parenthesis or square bracket, that of an aside
        # that is not closed.
        dated = rf"{date}(?>(?:{aside})*)(?=\s*(?:[^\w\s](?!\w)|$)|\s+[(\[])"
        no_object = rf"(?:(?:and|but|or|as|at|by|for|in|on|since|with){end}|{dated})"
        obj = rf"\s+(?:\d+\s+)?(?!{no_object})\w"
        marks = re.compile(rf"\b(?:done|completed)\b|\bcomplete\b(?!{obj})|trust scoring", re.IGNORECASE)
        verb = re.compile(rf"^(\d+\. \**)complete(?=\s+and\s+{word}{obj})", re.IGNORECASE)
        return [item for item in items if marks.search(verb.sub(r"\1", item))]

    def test_challenge_response_row_is_partial_as_in_appendix_a1(self) -> None:
        # Appendix A.1 marks the §5 row Partial because the backend registers no route for the
        # challenge endpoint the discovery document advertises; the gap analysis row agrees.
        status = self.status("Challenge-response (Ed25519) |")
        self.assertTrue(status.startswith("Partial"), status)
        self.assertIn("`/api/v1/agents/{agentId}/challenge`", status)
        self.assertIn("registers no such route", status)

    def test_discovery_row_says_the_endpoint_is_served_as_the_readme_does(self) -> None:
        readme = check_draft_sync.README.read_text(encoding="utf-8")
        self.assertIn("`https://aim.opena2a.org/.well-known/aip`", readme)
        self.assertIn("answered HTTP 200", readme)
        status = self.status("/.well-known/aip |")
        self.assertTrue(status.startswith("Complete"), status)
        self.assertIn("answered HTTP 200", status)
        self.assertIn("curl -s -o /dev/null -w '%{http_code}\\n' https://aim.opena2a.org/.well-known/aip", self.gap())

    def test_priority_list_does_not_ask_for_the_served_discovery_endpoint(self) -> None:
        priorities = self.gap().split("## Priority Implementation Order", 1)[1].split("\n---", 1)[0]
        items = [line for line in priorities.splitlines() if re.match(r"\d+\. ", line)]
        self.assertTrue(items, "the priority list has no items")
        self.assertEqual([item for item in items if "well-known" in item], [])
        self.assertEqual([item.split(".")[0] for item in items], [str(n) for n in range(1, len(items) + 1)])

    def test_priority_list_holds_no_completed_item_and_says_where_each_one_went(self) -> None:
        # A completed item leaves the list, as the discovery endpoint did, instead of staying in
        # it marked done, and the sentences under the list point to the table that records it.
        priorities = self.gap().split("## Priority Implementation Order", 1)[1].split("\n---", 1)[0]
        items = [line for line in priorities.splitlines() if re.match(r"\d+\. ", line)]
        self.assertEqual(self.finished(items), [])
        note = " ".join(line for line in priorities.splitlines() if line and not re.match(r"\d+\. ", line))
        self.assertIn("A completed item leaves this list", note)
        self.assertIn("is served (Discovery table above)", note)
        self.assertIn("trust scoring factors, third in this list until then, are implemented (Trust Scoring table above)", note)
        for factor in ("Compliance", "Drift", "Feedback"):
            self.assertTrue(self.status(f"{factor} factor").startswith("Complete"), factor)

    def test_priority_list_item_marked_complete_is_reported(self) -> None:
        # "Complete" is the word the tables above the list use for a finished row, so an item that
        # carries it as a mark is reported, as one marked done is.
        marked = [
            "4. **WebAuthn/FIDO2** — browser-based key storage for Chrome integration (done, *updated 2026-10*)",
            "6. **YAML policy format** — declarative governance policies (complete)",
            "6. **YAML policy format** — declarative governance policies (completed 2026-10)",
            "6. **YAML policy format** — Complete (*updated 2026-10*)",
            "6. **Complete** — YAML policy format",
            "1. **Complete the DID resolver** — required for Level 3 and cross-platform identity (complete)",
            "6. **YAML policy format** — declarative governance policies (complete 2026-10)",
            "6. **YAML policy format** — complete and served by the backend",
            "6. **YAML policy format** — declarative governance policies, complete since 2026-10",
            "6. **YAML policy format** — declarative governance policies (complete October 2026)",
            "6. **YAML policy format** — declarative governance policies (complete 3 October 2026)",
            "6. **YAML policy format** — declarative governance policies, complete (October 2026)",
            "6. **YAML policy format** — declarative governance policies (complete Oct 2026)",
            "6. **YAML policy format** — declarative governance policies (complete Oct. 2026)",
            "6. **YAML policy format** — declarative governance policies (complete Sept 2026)",
            "6. **YAML policy format** — declarative governance policies (complete 3 Oct 2026)",
            "6. **YAML policy format** — declarative governance policies (complete Q4 2026)",
            # One punctuation mark between a quarter, a half-year, a month or a number and the
            # next of them joins them into one date.
            "6. **YAML policy format** — declarative governance policies (complete Q4-2026)",
            "6. **YAML policy format** — declarative governance policies (complete 2026-Q4)",
            "6. **YAML policy format** — declarative governance policies (complete Q4/2026)",
            "6. **YAML policy format** — declarative governance policies (complete Oct-2026)",
            "6. **YAML policy format** — declarative governance policies (complete 2026-Oct)",
            "6. **YAML policy format** — declarative governance policies (complete 3-Oct-2026)",
            "6. **YAML policy format** — declarative governance policies (complete October/2026)",
            "6. **YAML policy format** — declarative governance policies (complete H2 2026)",
            "6. **YAML policy format** — declarative governance policies (complete H2-2026)",
            "6. **YAML policy format** — declarative governance policies (complete 2026-H2)",
            "6. **YAML policy format** — declarative governance policies, complete since Q4-2026",
            "6. **Complete Q4-2026** — YAML policy format",
            # A full stop or a comma and a space between two parts joins them into one date, and a
            # date before a punctuation mark, after a space or not, leaves "complete" a mark.
            "6. **YAML policy format** — declarative governance policies (complete October 3, 2026)",
            "6. **YAML policy format** — declarative governance policies, complete Q4-2026.",
            "6. **YAML policy format** — declarative governance policies, complete Q4 2026, served by the backend",
            "6. **YAML policy format** — complete Q4 2026 — served by the backend",
            "6. **YAML policy format** — complete and served to every caller",
            # A space and an opening parenthesis or square bracket after a date open an aside, not
            # an object, so "complete" is a mark where the aside ends the item, whatever the aside
            # starts with.
            "6. **YAML policy format** — complete Q4-2026 (Discovery table above)",
            "6. **YAML policy format** — complete Q4 2026 (Discovery table above)",
            "6. **YAML policy format** — complete October 3, 2026 (Discovery table above)",
            "6. **YAML policy format** — complete 2026-10 [see Appendix A.1]",
            "6. **YAML policy format** — complete Oct. 2026 (2 checks remain in Appendix A.1)",
            # A date takes each closed aside after it, so "complete" is still a mark where a
            # punctuation mark or a second aside follows the first.
            "6. **YAML policy format** — complete Q4-2026 (Discovery table above), served by the backend",
            "6. **YAML policy format** — complete Q4-2026 (Discovery table above). Served by the backend",
            "6. **YAML policy format** — complete Q4-2026 (Discovery table above) — served by the backend",
            "6. **YAML policy format** — complete Q4-2026 (Discovery table above) [see Appendix A.1]",
            # An aside that is not closed leaves "complete" a mark whatever follows its opening
            # parenthesis or bracket: one with no closing parenthesis or bracket, also after a
            # closed aside, and one that holds a parenthesis or bracket of its own kind, which
            # is reported here in an item still to do.
            "6. **YAML policy format** — complete Q4-2026 (Discovery table above",
            "6. **YAML policy format** — complete 2026-10 [see Appendix A.1",
            "6. **YAML policy format** — complete Q4-2026 (Discovery table above) [see Appendix A.1",
            "3. **Delegation chains** — complete Q4-2026 (see (a) and (b)) conformance checks",
            "3. **Delegation chains** — complete Q4-2026 [see [1]] conformance checks",
            # A title that opens with "Complete" and no object of it is a mark as well.
            "6. **Complete 2026-10** — YAML policy format",
            "6. **Complete and served** — YAML policy format",
            "6. **COMPLETE and served** — YAML policy format",
            # The word after "and" ends before punctuation, so no object follows it here.
            "6. **Complete and served**: YAML policy format",
            "6. **Complete and served** YAML policy format",
            "6. **Complete and served.** YAML policy format",
            "1. **Complete and publish, then x** — required for Level 3",
        ]
        # Each word finished() names, in each letter case, leaves "complete" a mark before it, and
        # so does each month name, each abbreviation of one, each quarter and each half-year where
        # it ends the item, stands before punctuation or stands before a space and an aside.
        words = ("and", "but", "or", "as", "at", "by", "for", "in", "on", "since", "with")
        dates = (
            "January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
            "November", "December", "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov",
            "Dec", "Q1", "Q2", "Q3", "Q4", "H1", "H2",
        )
        for word in words:
            for case in (word.lower(), word.title(), word.upper()):
                marked.append(f"6. **YAML policy format** — complete {case} the backend")
        for date in dates:
            for case in (date.lower(), date.title(), date.upper()):
                marked.append(f"6. **YAML policy format** — declarative governance policies (complete {case})")
                marked.append(f"6. **YAML policy format** — declarative governance policies, complete {case}")
                marked.append(f"6. **YAML policy format** — complete {case} (Discovery table)")
        self.assertEqual(self.finished(marked), marked)
        # It is no mark where an object follows it in an item still to do: a word with a letter
        # that finished() does not name, or a number and such a word, or a date and such a word,
        # or, where it opens the title, "and", a word and an object.
        unfinished = [
            "1. **Complete the DID resolver** — required for Level 3 and cross-platform identity",
            "1. **Complete 2FA support** — required for Level 3",
            "4. **Complete in-browser key storage** — WebAuthn/FIDO2 for Chrome integration",
            "1. **Complete and publish the DID resolver** — required for Level 3",
            "1. **complete and publish the DID resolver** — required for Level 3",
            "1. **COMPLETE and publish the DID resolver** — required for Level 3",
            "1. **Complete 802.1X support** — required for Level 3",
            "3. **Delegation chains** — complete the depth limit enforcement",
            "2. **Capability negotiation** — needs a complete runtime protocol",
            "5. **Capability negotiation** — the runtime negotiation protocol between agents is incomplete",
            "5. **Capability negotiation** — check the completeness of the runtime protocol",
            "4. **WebAuthn/FIDO2** — complete in-browser key storage",
            "3. **Delegation chains** — complete 3 remaining checks",
            "6. **YAML policy format** — complete inside the backend",
            # A word that starts with an abbreviation or a quarter is not that abbreviation.
            "4. **Content types** — complete Octet stream parsing",
            "1. **Complete Decimal encoding** — required for Level 3",
            "3. **Delegation chains** — complete Q42 conformance checks",
            "4. **Content types** — complete H264 stream parsing",
            # Nor is a date and a punctuation mark before a word that is no part of a date.
            "3. **Delegation chains** — complete Q4-based conformance checks",
            "3. **Delegation chains** — complete May-day conformance checks",
            "3. **Delegation chains** — complete 2026-ready conformance checks",
            # A date that a word follows is no mark, nor is the part of it before a full stop or a
            # comma and a space.
            "3. **Delegation chains** — complete Q4-2026 conformance checks",
            "3. **Delegation chains** — complete Q4 2026 conformance checks",
            "3. **Delegation chains** — complete 3 October 2026 conformance checks",
            "3. **Delegation chains** — complete Oct. 2026 conformance checks",
            "3. **Delegation chains** — complete October 3, 2026 conformance checks",
            "1. **Complete and publish Q4-2026 conformance checks** — required for Level 3",
            # An aside after the word that follows the date leaves that word the object.
            "3. **Delegation chains** — complete Q4-2026 conformance checks (Discovery table)",
            # A closed aside after a count or a date is no object, and the word after it is one,
            # after one aside or two and in a title as well.
            "3. **Delegation chains** — complete 3 (of 5) remaining checks",
            "3. **Delegation chains** — complete Q4-2026 [1] conformance checks",
            "3. **Delegation chains** — complete Q4 2026 (Discovery table) conformance checks",
            "3. **Delegation chains** — complete Q4-2026 (of 5) [1] conformance checks",
            "1. **Complete Q4-2026 (of 5) conformance checks** — required for Level 3",
            "1. **Complete and publish Q4-2026 [1] conformance checks** — required for Level 3",
        ]
        for date in dates:
            for case in (date.lower(), date.title(), date.upper()):
                unfinished.append(f"3. **Delegation chains** — complete {case} the backend")
                unfinished.append(f"3. **Delegation chains** — complete {case} (Discovery table) the backend")
        self.assertEqual(self.finished(unfinished), [])
        # So a finished item worded that way is not reported either, and neither is one dated
        # with nothing between a year and its quarter, which is one word with a letter, nor one
        # with no space between a date and a parenthesis that a letter follows, which joins them
        # into one word, nor one with a word after the closed aside that follows its date.
        unreported = [
            "6. **YAML policy format** — complete per Appendix A.1",
            "6. **YAML policy format** — complete from 2026-10",
            "6. **YAML policy format** — complete Q4 2026 and served by the backend",
            "6. **YAML policy format** — declarative governance policies (complete 2026Q4)",
            "6. **YAML policy format** — complete Q4-2026(Discovery table above)",
            "6. **YAML policy format** — complete Q4-2026 (Discovery table above) and served by the backend",
        ]
        self.assertEqual(self.finished(unreported), [])

    def test_full_stop_right_after_a_month_abbreviation_is_part_of_the_date(self) -> None:
        # The full stop that ends an abbreviation is no punctuation mark after the date, so a word
        # after it is an object of "complete" and the item is still to do.
        unfinished = [
            "3. **Delegation chains** — complete Sept. conformance checks",
            "3. **Delegation chains** — complete 3 Sept. conformance checks",
            "3. **Delegation chains** — complete 2026-Sept. conformance checks",
            "1. **Complete Sept. conformance checks** — required for Level 3",
            "1. **Complete and publish Sept. conformance checks** — required for Level 3",
            # A closed aside after that full stop changes nothing: the word after the aside is the
            # object.
            "3. **Delegation chains** — complete Sept. (of 5) conformance checks",
        ]
        marked = [
            # With its full stop, the date still stands before a punctuation mark here.
            "6. **YAML policy format** — declarative governance policies, complete Sept., served by the backend",
            "6. **YAML policy format** — complete Sept. — served by the backend",
            "6. **Complete Sept.** — YAML policy format",
            # A part follows the full stop here, after a space, a punctuation mark or nothing, and
            # the date takes it.
            "6. **YAML policy format** — declarative governance policies (complete Sept. 2026)",
            "6. **YAML policy format** — declarative governance policies (complete Sept.-2026)",
            "6. **YAML policy format** — declarative governance policies (complete Sept.2026)",
            # A letter right after the full stop leaves it out of the abbreviation, as a digit
            # does: it is the punctuation mark before the next part, and the date takes that part.
            "6. **YAML policy format** — declarative governance policies (complete Sept.Oct)",
            # A full stop after a number or a month name is a punctuation mark after the date.
            "6. **YAML policy format** — complete Sept. 2026. Served by the backend",
            "6. **YAML policy format** — complete Q4 2026. Served by the backend",
            "6. **YAML policy format** — complete October. Served by the backend",
        ]
        abbreviations = ("Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov", "Dec")
        for abbreviation in abbreviations:
            for case in (abbreviation.lower(), abbreviation.title(), abbreviation.upper()):
                unfinished.append(f"3. **Delegation chains** — complete {case}. conformance checks")
                marked.append(f"6. **YAML policy format** — declarative governance policies (complete {case}.)")
                marked.append(f"6. **YAML policy format** — declarative governance policies, complete {case}.")
                marked.append(f"6. **YAML policy format** — complete {case}. (Discovery table)")
        self.assertEqual(self.finished(unfinished), [])
        self.assertEqual(self.finished(marked), marked)
        # So a finished item is not reported where a sentence starts right after the abbreviation.
        self.assertEqual(self.finished(["6. **YAML policy format** — complete Sept. Served by the backend"]), [])

    def test_links_to_appendix_a1(self) -> None:
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        headings = re.findall(r"(?m)^### (A\.1 .+)$", spec)
        self.assertEqual(len(headings), 1, headings)
        link = f"](AIP-SPEC.md#{self.slug(headings[0])})"
        self.assertTrue(link in self.gap(), f"GAP-ANALYSIS.md has no link ending {link!r}")

    def test_openA2A_aip_row_names_the_filed_draft_and_its_first_date(self) -> None:
        header = (ROOT / "draft-fane-opena2a-aip-00.txt").read_text(encoding="utf-8")
        found = re.search(rf"\b(\d{{1,2}}) ({self.MONTHS}) (\d{{4}})\b", header)
        self.assertIsNotNone(found, "draft-fane-opena2a-aip-00.txt carries no date")
        day, month, year = found.groups()
        first = f"{year}-{self.MONTHS.split('|').index(month) + 1:02d}-{int(day):02d}"
        row = self.row("OpenA2A AIP")
        self.assertIn("`draft-fane-opena2a-aip`", row)
        self.assertIn(f"-00, {first}", row)

    def test_openA2A_rows_do_not_say_not_yet_filed(self) -> None:
        self.assertIn("`draft-fane-opena2a-aap`", self.row("OpenA2A AAP"))
        self.assertNotIn("not yet filed", self.gap())


class FirstUseMissingFile(unittest.TestCase):
    def test_missing_file_is_a_counted_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.md"
            result = run(str(SCRIPTS / "check_first_use.py"), str(missing))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "")
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1, result.stdout)
        self.assertTrue(lines[0].startswith("first use FAIL "), lines[0])

    def test_missing_file_counts_once_among_others(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as out:
            failures = check_first_use.check([ROOT / "missing.md", ROOT / "README.md"])
        self.assertEqual(failures, 1)
        self.assertIn("first use FAIL missing.md", out.getvalue())


class IsolatedMode(unittest.TestCase):
    def test_check_draft_sync_runs_isolated(self) -> None:
        result = run("-I", str(SCRIPTS / "check_draft_sync.py"))
        self.assertNotIn("No module named", result.stderr)
        self.assertEqual(result.returncode, run(str(SCRIPTS / "check_draft_sync.py")).returncode)

    def test_validate_examples_runs_isolated(self) -> None:
        if run("-I", "-c", "import jsonschema").returncode != 0:
            self.skipTest("jsonschema is not importable in isolated mode")
        isolated = run("-I", str(SCRIPTS / "validate_examples.py"))
        self.assertNotIn("No module named", isolated.stderr)
        self.assertEqual(isolated.returncode, run(str(SCRIPTS / "validate_examples.py")).returncode)

    def test_stage_draft_upload_imports_isolated(self) -> None:
        result = run("-I", str(SCRIPTS / "stage_draft_upload.py"), "--help")
        self.assertNotIn("No module named", result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)


class PrePushReviewMarker(unittest.TestCase):
    def setUp(self) -> None:
        self.marker = (ROOT / ".pre-push-review-not-required").read_text(encoding="utf-8")

    def test_marker_does_not_deny_the_test_suite(self) -> None:
        self.assertIsNone(re.search(r"\bno\b[^.]*\btest suite\b", self.marker, re.IGNORECASE), self.marker)

    def test_marker_names_no_slash_command(self) -> None:
        # A slash command names a review workflow the repository does not contain, so a reader of
        # the repository cannot run or find it. The commands the marker lists run from the root.
        self.assertIsNone(re.search(r"(?<![\w./])/[A-Za-z][\w-]*", self.marker), self.marker)

    def test_marker_names_the_test_commands(self) -> None:
        self.assertTrue(sorted((ROOT / "tests").glob("test_*.py")))
        self.assertIn("python3 -m unittest discover -s tests", self.marker)
        self.assertTrue((SCRIPTS / "test_checks.py").exists())
        self.assertIn("python3 scripts/test_checks.py", self.marker)

    def test_marker_names_every_script_ci_runs(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        commands = re.findall(r"^\s*run:\s*(python3 scripts/\S.*?)\s*$", workflow, re.MULTILINE)
        self.assertTrue(commands, "validate.yml runs no script")
        for command in commands:
            self.assertIn(command, self.marker)


class GitignoreSecrets(unittest.TestCase):
    def test_secret_shaped_files_are_ignored(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT, capture_output=True)
        if inside.returncode != 0:
            self.skipTest("not a git checkout")
        for path in ("secrets.json", "secrets.local.json", "app.secrets.json", "credentials.json"):
            result = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
            self.assertEqual(result.returncode, 0, f"{path} is not ignored")


class OperatorSpacing(unittest.TestCase):
    """The Python files in scripts/ and tests/ put whitespace on both sides of an operator.

    This is the rule of pycodestyle E225 for assignment, augmented assignment and comparison
    operators, checked with the standard library tokenizer so it runs without pycodestyle. As
    there, an "=" takes no whitespace and is left out where it stands directly inside parentheses,
    passing a keyword argument or giving a parameter default, among the parameters of a lambda, or
    in an f-string or t-string replacement field, asking for the "{name=}" form. An "=" directly inside square
    brackets gives the default of a type parameter and is checked. A line break or a comment is
    not a neighbour, so an operator that ends a line touches nothing on that side.
    """

    OPERATORS = {
        "=", "+=", "-=", "*=", "/=", "//=", "%=", "**=", "|=", "&=", "^=", ">>=", "<<=", ":=",
        "==", "!=", "<", ">", "<=", ">=", "->",
    }
    # Tokens that hold no code.
    SKIPPED = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT}
    # Python 3.12 and later tokenize an f-string in parts, and 3.14 and later a t-string.
    STRING_STARTS = {getattr(tokenize, name, None) for name in ("FSTRING_START", "TSTRING_START")} - {None}
    STRING_ENDS = {getattr(tokenize, name, None) for name in ("FSTRING_END", "TSTRING_END")} - {None}

    def unspaced_in(self, source: str) -> list[str]:
        """Return "line:column: operator" for each operator of source that touches a neighbour."""
        found = []
        tokens = [t for t in tokenize.generate_tokens(io.StringIO(source).readline) if t.type not in self.SKIPPED]
        # What encloses the token, innermost last: an opening bracket, "f" for a string tokenized
        # in parts, or "lambda" from that keyword to the colon that ends its parameters.
        inside: list[str] = []
        for before, token, after in zip([None, *tokens], tokens, tokens[1:]):
            op = token.string if token.type == tokenize.OP else ""
            if op in ("(", "[", "{"):
                inside.append(op)
            elif token.type in self.STRING_STARTS:
                inside.append("f")
            elif token.type == tokenize.NAME and token.string == "lambda":
                inside.append("lambda")
            elif inside and (
                op in (")", "]", "}") or token.type in self.STRING_ENDS or (op == ":" and inside[-1] == "lambda")
            ):
                inside.pop()
            if op not in self.OPERATORS:
                continue
            if op == "=" and (inside[-1:] in (["("], ["lambda"]) or inside[-2:] == ["f", "{"]):
                continue
            if (before is not None and before.end == token.start) or token.end == after.start:
                found.append(f"{token.start[0]}:{token.start[1] + 1}: {op}")
        return found

    def unspaced(self, path: Path) -> list[str]:
        with tokenize.open(path) as source:
            return [f"{path.relative_to(ROOT)}:{place}" for place in self.unspaced_in(source.read())]

    def test_operators_have_whitespace_around_them(self) -> None:
        paths = sorted([*SCRIPTS.glob("*.py"), *(ROOT / "tests").glob("*.py")])
        self.assertIn(SCRIPTS / "test_checks.py", paths)
        self.assertEqual([line for path in paths for line in self.unspaced(path)], [])

    def test_operator_that_ends_a_line_inside_brackets_is_not_reported(self) -> None:
        # The line break starts where the operator ends, and is not a neighbour of it.
        self.assertEqual(self.unspaced_in("_Z = (1 ==\n      2)\n"), [])
        self.assertEqual(self.unspaced_in("_Z = (1 ==  # a comment\n      2)\n"), [])
        # Nor is a comment that starts where the operator ends.
        self.assertEqual(self.unspaced_in("_Z = (1 ==# a comment\n      2)\n"), [])
        self.assertEqual(self.unspaced_in("_Z = (1==\n      2)\n"), ["1:8: =="])
        self.assertEqual(self.unspaced_in("_Z = (1\n      ==2)\n"), ["2:7: =="])

    def test_default_of_a_lambda_parameter_is_not_reported(self) -> None:
        self.assertEqual(self.unspaced_in("_L = lambda a=1: a\n"), [])
        self.assertEqual(self.unspaced_in("_L = lambda a={1: 2}, b=_Z[1:2]: a\n"), [])
        # The colon ends the parameters, so an operator after it is checked again.
        self.assertEqual(self.unspaced_in("_L = lambda a=1: a==1\n"), ["1:19: =="])
        self.assertEqual(self.unspaced_in("_L = lambda: 0\n_M=1\n"), ["2:3: ="])

    def test_default_of_a_type_parameter_is_reported(self) -> None:
        self.assertEqual(self.unspaced_in("def _n[T=int]():\n    pass\n"), ["1:9: ="])
        self.assertEqual(self.unspaced_in("def _n[T = int](a=1):\n    pass\n"), [])

    def test_keyword_argument_parameter_default_and_replacement_field_are_not_reported(self) -> None:
        self.assertEqual(self.unspaced_in('def _f(a=1):\n    return _f(a=2), f"{a=}", _Z[_f(a=3)]\n'), [])
        self.assertEqual(self.unspaced_in("_G = (_Z:=1)\n"), ["1:9: :="])

    @unittest.skipUnless(hasattr(tokenize, "TSTRING_START"), "Python 3.14 and later tokenize a t-string in parts")
    def test_replacement_field_of_a_t_string_is_not_reported(self) -> None:
        self.assertEqual(self.unspaced_in('_A = 1\n_T = t"{a=}"\n'), [])
        self.assertEqual(self.unspaced_in('_A = 1\n_T = t"{(a==1)=}"\n'), ["2:11: =="])
        # The t-string ends at its closing quote, so a keyword argument after it is skipped again.
        self.assertEqual(self.unspaced_in('_f(t"{_A}", b=1)\n'), [])


if __name__ == "__main__":
    unittest.main()
