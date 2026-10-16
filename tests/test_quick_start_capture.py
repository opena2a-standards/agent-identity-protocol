#!/usr/bin/env python3
"""Regression tests for the README Quick Start capture and scripts/capture_quick_start.py.

README.md shows what its first command prints in a text block under the line
'What `<command>` prints ([full output](docs/captures/<name>.txt)):'. The capture run
writes that .txt and a .json beside it. These tests check that the README block is the
excerpt the .json names, line for line, that the .json records the README's command, and
what the capture script writes, or refuses to write, with the command run replaced.

Run from the repository root:
    python3 -m unittest discover -s tests
python3 standard library only (3.11 or later).
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import capture_quick_start  # noqa: E402

README = ROOT / "README.md"
LABEL = re.compile(r"^What `(?P<command>[^`]+)` prints(?P<trimmed>, trimmed)? \(\[full output\]\((?P<txt>[^)]+)\)\):$")
VERSION_OR_DATE = re.compile(r"v?[0-9]+\.[0-9]+\.[0-9]+|20[0-9]{2}-[0-9]{2}-[0-9]{2}")


def quick_start(readme: str) -> list[str]:
    """Return the lines of the README's Quick Start section, without its heading."""
    return readme.split("\n## Quick Start\n", 1)[1].split("\n## ", 1)[0].splitlines()


def first_command(lines: list[str]) -> str:
    """Return the first line of the first fenced block that is not blank or a comment."""
    fence = next(i for i, line in enumerate(lines) if line.startswith("```"))
    return next(line for line in lines[fence + 1:] if line.strip() and not line.startswith("#"))


def capture(lines: list[str]) -> tuple[re.Match, list[str]]:
    """Return the capture label and the lines of the fenced block right after it."""
    for i, line in enumerate(lines):
        match = LABEL.match(line)
        if match:
            break
    else:
        raise AssertionError("the Quick Start has no 'What `<command>` prints ([full output](...)):' line")
    rest = lines[i + 1:]
    opening = next(j for j, line in enumerate(rest) if line.strip())
    if not rest[opening].startswith("```"):
        raise AssertionError("the capture label is not followed by a fenced block")
    block = rest[opening + 1:]
    return match, block[: next(j for j, line in enumerate(block) if line.startswith("```"))]


class QuickStartCapture(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = quick_start(README.read_text(encoding="utf-8"))
        self.label, self.block = capture(self.lines)
        self.txt = ROOT / self.label.group("txt")
        self.record = json.loads(self.txt.with_suffix(".json").read_text(encoding="utf-8"))

    def test_label_names_the_first_command_and_its_sidecar(self) -> None:
        self.assertEqual(self.label.group("command"), first_command(self.lines))
        self.assertEqual(self.label.group("txt"), f"docs/captures/{capture_quick_start.NAME}.txt")

    def test_sidecar_records_the_run_of_that_command(self) -> None:
        self.assertEqual(self.record["command"], self.label.group("command"))
        self.assertEqual(self.record["command"], capture_quick_start.COMMAND)
        self.assertEqual(self.record["package"], "opena2a-cli")
        self.assertRegex(self.record["version"], r"^[0-9]+\.[0-9]+\.[0-9]+$")
        self.assertRegex(self.record["date"], r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}$")
        self.assertEqual(self.record["exitCode"], 0)
        self.assertTrue(self.record["fixture"])

    def test_readme_block_is_the_excerpt_the_sidecar_names(self) -> None:
        captured = self.txt.read_text(encoding="utf-8").splitlines()
        first, last = self.record["excerpt"]["firstLine"], self.record["excerpt"]["lastLine"]
        self.assertEqual((first, last), capture_quick_start.excerpt_range(captured))
        # An untrimmed excerpt is shown as captured; ", trimmed" in the label would allow elision.
        self.assertIsNone(self.label.group("trimmed"))
        self.assertEqual(self.block, captured[first - 1 : last])

    def test_readme_block_prints_no_version_or_date(self) -> None:
        self.assertEqual([line for line in self.block if VERSION_OR_DATE.search(line)], [])


class ExcerptRange(unittest.TestCase):
    def test_range_runs_from_the_first_to_the_last_line_with_text(self) -> None:
        self.assertEqual(capture_quick_start.excerpt_range(["", "a", "", "b", " "]), (2, 4))

    def test_output_with_no_text_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            capture_quick_start.excerpt_range(["", "  "])


class InstalledVersion(unittest.TestCase):
    def test_version_is_read_from_the_one_npx_install(self) -> None:
        with tempfile.TemporaryDirectory() as cache:
            manifest = Path(cache, "_npx", "abc", "node_modules", "opena2a-cli", "package.json")
            with self.assertRaises(RuntimeError):
                capture_quick_start.installed_version(Path(cache))
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"name": "opena2a-cli", "version": "9.8.7"}', encoding="utf-8")
            self.assertEqual(capture_quick_start.installed_version(Path(cache)), "9.8.7")


class Main(unittest.TestCase):
    """main() with the command run replaced, writing into a temporary directory."""

    def run_main(self, result: subprocess.CompletedProcess, home_exists: bool = False) -> tuple[int, Path]:
        work = Path(self.enterContext(tempfile.TemporaryDirectory()))
        home = work / "home"
        if home_exists:
            home.mkdir()
        self.enterContext(mock.patch.object(capture_quick_start, "HOME", home))
        self.enterContext(mock.patch.object(capture_quick_start, "CAPTURES", work / "captures"))
        self.enterContext(mock.patch.object(capture_quick_start, "run_command", return_value=(result, "9.8.7")))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))
        return capture_quick_start.main(), work / "captures"

    def test_writes_the_untrimmed_output_and_the_record(self) -> None:
        stdout = "\nIdentity created\n  Agent ID:    aim_x\n\n"
        code, captures = self.run_main(subprocess.CompletedProcess([], 0, stdout, "npm warn\n"))
        self.assertEqual(code, 0)
        self.assertEqual((captures / "identity-create.txt").read_text(encoding="utf-8"), stdout)
        record = json.loads((captures / "identity-create.json").read_text(encoding="utf-8"))
        self.assertEqual(record["command"], capture_quick_start.COMMAND)
        self.assertEqual(record["version"], "9.8.7")
        self.assertEqual(record["exitCode"], 0)
        self.assertEqual(record["excerpt"], {"firstLine": 2, "lastLine": 3})

    def test_writes_nothing_when_the_command_fails(self) -> None:
        code, captures = self.run_main(subprocess.CompletedProcess([], 1, "", "failed\n"))
        self.assertEqual(code, 1)
        self.assertFalse(captures.exists())

    def test_refuses_to_run_in_a_home_directory_that_exists(self) -> None:
        code, captures = self.run_main(subprocess.CompletedProcess([], 0, "out\n", ""), home_exists=True)
        self.assertEqual(code, 2)
        self.assertFalse(captures.exists())
        capture_quick_start.run_command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
