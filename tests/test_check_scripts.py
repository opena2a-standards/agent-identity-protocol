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
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
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


if __name__ == "__main__":
    unittest.main()
