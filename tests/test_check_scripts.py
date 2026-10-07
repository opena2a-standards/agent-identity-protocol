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
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
        with tempfile.TemporaryDirectory() as tmp:
            for ext in (".xml", ".txt"):
                shutil.copy(ROOT / f"{self.name}{ext}", Path(tmp) / f"{self.name}{ext}")
            edited = Path(tmp) / f"{self.name}{suffix}"
            text = edited.read_text(encoding="utf-8")
            self.assertIn(old, text)
            edited.write_text(text.replace(old, new), encoding="utf-8")
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
        self.assertFalse(check_draft_sync.names_stream(xml), f"{self.name}.xml sets submissionType")

    def test_stream_in_draft_is_reported(self) -> None:
        problems = self.problems_in_copy(".xml", 'ipr="trust200902"', 'ipr="trust200902"\n     submissionType="IETF"')
        self.assertTrue(any("SUBMISSION_TYPE_UNEXPECTED" in p for p in problems), problems)

    def test_names_stream_reads_only_the_rfc_tag(self) -> None:
        self.assertTrue(check_draft_sync.names_stream('<rfc docName="d" submissionType="independent">'))
        self.assertTrue(check_draft_sync.names_stream('<rfc docName="d"\n     submissionType = "IETF">'))
        self.assertFalse(check_draft_sync.names_stream('<rfc docName="d"><t>submissionType="IETF"</t></rfc>'))
        self.assertFalse(check_draft_sync.names_stream('<rfc docName="d" category="std">'))

    def test_carries_matches_whole_words(self) -> None:
        self.assertTrue(check_draft_sync.carries('{"behaviorTier": 3}', "behaviorTier"))
        self.assertFalse(check_draft_sync.carries('{"behaviorTierX": 3}', "behaviorTier"))
        self.assertFalse(check_draft_sync.carries('{"xbehaviorTier": 3}', "behaviorTier"))
        self.assertTrue(check_draft_sync.carries('{"trustLevel": 3}', '"trustLevel":'))
        self.assertTrue(check_draft_sync.carries("the clock-skew bound of", "clock-skew bound"))
        self.assertFalse(check_draft_sync.carries("the clock-skew bounds of", "clock-skew bound"))


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
        for path in ("secrets.json", "secrets.local.json", "app.secrets.json", "credentials.json"):
            result = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
            self.assertEqual(result.returncode, 0, f"{path} is not ignored")


if __name__ == "__main__":
    unittest.main()
