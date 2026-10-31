#!/usr/bin/env python3
"""Check the aip-conformance fixture counts the documents state against the suite, at the commit they name.

docs/use-cases.md states how many fixtures the aip-conformance suite ships,
how many of them are Section 5.1 challenge-response transcripts and how many
are Section 6.1 trust-score compositions, and names the aip-conformance commit
the counts were read at. Those are measurements taken in another repository,
so they are checked here rather than maintained by hand: the page stated 7
fixtures while the suite shipped 17, and nothing caught it. This check reads
the suite at the commit the sentence names and fails when a stated count
differs.

It reads README.md and the Markdown files under docs/, outside fenced code
blocks, which hold the output of runs over chosen fixtures. A count belongs to
the conformance suite named before it in the same paragraph, and is read at
the commit named in that suite's part of the paragraph, as in

    [aip-conformance](...), 17 byte-pinned fixtures at commit `52ba849`
    (14 challenge-response transcripts, 3 trust-score compositions)

  "17 byte-pinned fixtures"            every .json file directly under fixtures/
                                       ("pinned", "shipped", "conformance" or no
                                       word may stand before "fixtures")
  "14 challenge-response transcripts"  the fixtures whose fixtureType is challengeResponse
  "3 trust-score compositions"         the fixtures whose fixtureType is trustScoreComposition

A section number, as in "the Section 5.1 fixtures", is not a count.

It fails when a stated count differs from the suite at the named commit; when
a count names no commit, two commits, or no suite before it; when the named
commit is not in the history of the suite checkout's HEAD or ships no
fixtures; and when docs/use-cases.md states no aip-conformance count, so it
never passes vacuously. When the suite's HEAD ships a different number of
fixtures than the named commit, it says so and passes: the sentence is true
at the commit it names.

This repository does not contain the fixtures, so the caller supplies the
suite as a git clone with its history, because the check reads a commit
rather than the working tree:

    python3 scripts/check_conformance_counts.py --suite <path-to-aip-conformance> [--root <tree>]

--root names the tree whose documents are read (default: this repository);
scripts/test_conformance_counts.py uses it on scratch trees. Modelled on the
conformance-count check of opena2a-standards/atx-spec. python3 standard
library and git only. Exit code 0 = every stated count matches.
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SUITE = "aip-conformance"
# The document that must state the suite's counts, so the check never passes vacuously.
REQUIRED = "docs/use-cases.md"

# The fixtureType each class word stands for.
CLASSES = {
    "challenge-response": "challengeResponse",
    "trust-score": "trustScoreComposition",
}
KINDS = ("fixtures",) + tuple(f"{word} fixtures" for word in CLASSES)

# A word that may sit between the count and "fixtures" and still describe the
# whole suite.
WHOLE_SUITE_QUALIFIERS = ("byte-pinned", "pinned", "shipped", "conformance")

# A number that is not the end of a section number such as 5.1.
NUMBER = r"(?<![\w.])(\d+)"
CLASS_RE = re.compile(
    NUMBER + r"\s+(" + "|".join(map(re.escape, CLASSES)) + r")\s+(?:transcripts|compositions|fixtures)\b"
)
FIXTURES_RE = re.compile(
    NUMBER + r"\s+(?:(?:" + "|".join(map(re.escape, WHOLE_SUITE_QUALIFIERS)) + r")\s+)?fixtures\b"
)
# The conformance suites of the family. Naming one starts that suite's part of
# a paragraph; the name inside a link target or a path does not.
SUITE_NAME_RE = re.compile(r"(?<![\w/.-])((?:aap|aip|atp|atx)-conformance)(?![\w-])")
COMMIT_RE = re.compile(r"\bcommit\s+`?([0-9a-f]{7,40})\b`?")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)\s]*\)")
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*$")
# A line that starts a block of its own: a heading, a list item, a block quote or a table row.
BLOCK_START_RE = re.compile(r"^\s*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\|)")


@dataclass
class Part:
    """One suite's part of a paragraph: from where the suite is named to where the next one is."""

    suite: str | None
    commits: list[tuple[str, int]] = field(default_factory=list)  # (commit, line)
    counts: list[tuple[str, int, int]] = field(default_factory=list)  # (kind, value, line)


def paragraphs(text: str):
    """Yield (line numbers, lines) per paragraph outside fenced code blocks, each link reduced to its text."""
    fence = None
    numbers: list[int] = []
    lines: list[str] = []
    for number, raw in enumerate(text.split("\n"), 1):
        if fence is not None:
            close = FENCE_CLOSE_RE.match(raw)
            if close and close.group(1)[0] == fence[0] and len(close.group(1)) >= len(fence):
                fence = None
            continue
        opening = FENCE_OPEN_RE.match(raw)
        if opening and opening.group(1)[0] == "`" and "`" in raw[opening.end():]:
            opening = None  # a run of backticks with a backtick after it on its line opens no fence
        if opening or not raw.strip() or (lines and BLOCK_START_RE.match(raw)):
            if lines:
                yield numbers, lines
            numbers, lines = [], []
            if opening:
                fence = opening.group(1)
                continue
            if not raw.strip():
                continue
        numbers.append(number)
        lines.append(LINK_RE.sub(r"\1", raw))
    if lines:
        yield numbers, lines


def counts_in(segment: str) -> list[tuple[str, int, int]]:
    """Every count stated in one suite's part of a paragraph, as (kind, value, offset)."""
    found = [(f"{m.group(2)} fixtures", int(m.group(1)), m.start()) for m in CLASS_RE.finditer(segment)]
    found += [("fixtures", int(m.group(1)), m.start()) for m in FIXTURES_RE.finditer(segment)]
    return sorted(found, key=lambda item: item[2])


def parts(text: str) -> list[Part]:
    """Each part of each paragraph of text that states a count or names a commit."""
    result = []
    for numbers, lines in paragraphs(text):
        joined = "\n".join(lines)
        starts = [0]
        for line in lines[:-1]:
            starts.append(starts[-1] + len(line) + 1)

        def line_of(offset: int) -> int:
            return numbers[bisect.bisect_right(starts, offset) - 1]

        names = list(SUITE_NAME_RE.finditer(joined))
        bounds = [(None, 0)] + [(m.group(1), m.start()) for m in names]
        for index, (suite, begin) in enumerate(bounds):
            end = bounds[index + 1][1] if index + 1 < len(bounds) else len(joined)
            segment = joined[begin:end]
            part = Part(suite)
            part.commits = [(m.group(1), line_of(begin + m.start())) for m in COMMIT_RE.finditer(segment)]
            part.counts = [(kind, value, line_of(begin + offset)) for kind, value, offset in counts_in(segment)]
            if part.counts or part.commits:
                result.append(part)
    return result


class SuiteError(Exception):
    pass


class Suite:
    """A git clone of the suite, read at commits rather than at its working tree."""

    def __init__(self, path: Path):
        self.path = path
        if self._git("rev-parse", "--git-dir").returncode != 0:
            raise SuiteError(
                f"{path} is not a git checkout; the check reads the suite at the commit a "
                f"sentence names, so it needs a clone with history"
            )
        self.head = self.resolve("HEAD")
        if self.head is None:
            raise SuiteError(f"{path} has no HEAD commit")
        self._facts: dict[str, dict[str, int]] = {}

    def _git(self, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.path), *args], input=stdin, capture_output=True, check=False
        )

    def resolve(self, name: str) -> str | None:
        """The full id of the commit name resolves to, or None when it resolves to none or to more than one."""
        proc = self._git("rev-parse", "--verify", "--quiet", f"{name}^{{commit}}")
        return proc.stdout.decode().strip() if proc.returncode == 0 else None

    def in_head_history(self, commit: str) -> bool:
        proc = self._git("merge-base", "--is-ancestor", commit, self.head)
        if proc.returncode not in (0, 1):
            raise SuiteError(f"git merge-base failed in {self.path}: {proc.stderr.decode().strip()}")
        return proc.returncode == 0

    def facts(self, commit: str) -> dict[str, int]:
        """The counts at commit: every .json file directly under fixtures/, and those of each class."""
        if commit in self._facts:
            return self._facts[commit]
        listing = self._git("ls-tree", "-z", "--full-tree", commit, "--", "fixtures/")
        if listing.returncode != 0:
            raise SuiteError(f"git ls-tree failed in {self.path}: {listing.stderr.decode().strip()}")
        objects = []
        for record in listing.stdout.split(b"\0"):
            meta, _, raw_path = record.partition(b"\t")
            if not meta:
                continue
            _mode, object_type, object_id = meta.split()
            path = raw_path.decode("utf-8", "surrogateescape")
            name = path[len("fixtures/"):]
            if (object_type == b"blob" and path.startswith("fixtures/") and "/" not in name
                    and name.endswith(".json")):
                objects.append(object_id.decode())
        facts = dict.fromkeys(KINDS, 0)
        facts["fixtures"] = len(objects)
        for data in self._blobs(objects):
            try:
                fixture_type = json.loads(data).get("fixtureType")
            except (ValueError, AttributeError):
                fixture_type = None
            for word, value in CLASSES.items():
                if fixture_type == value:
                    facts[f"{word} fixtures"] += 1
        self._facts[commit] = facts
        return facts

    def _blobs(self, objects: list[str]) -> list[bytes]:
        if not objects:
            return []
        proc = self._git("cat-file", "--batch", stdin="".join(f"{o}\n" for o in objects).encode())
        if proc.returncode != 0:
            raise SuiteError(f"git cat-file failed in {self.path}: {proc.stderr.decode().strip()}")
        out, position, blobs = proc.stdout, 0, []
        for _ in objects:
            header_end = out.index(b"\n", position)
            header = out[position:header_end].split()
            if len(header) != 3 or header[1] != b"blob":
                raise SuiteError(f"git cat-file did not return a blob in {self.path}: {header!r}")
            start = header_end + 1
            blobs.append(out[start:start + int(header[2])])
            position = start + int(header[2]) + 1
        return blobs


def claim_files(root: Path) -> list[Path]:
    files = [root / "README.md"] if (root / "README.md").is_file() else []
    docs = root / "docs"
    if docs.is_dir():
        files += sorted(path for path in docs.rglob("*.md") if path.is_file())
    return files


def hint(suite: Suite) -> str:
    """The sentence's counts as the suite's HEAD would state them."""
    facts = suite.facts(suite.head)
    return (
        f"At HEAD {suite.head[:7]} the suite ships {facts['fixtures']} fixtures "
        f"({facts['challenge-response fixtures']} challenge-response transcripts, "
        f"{facts['trust-score fixtures']} trust-score compositions)."
    )


def check(root: Path, suite_path: Path) -> tuple[list[str], list[str], int, str]:
    """Return (failures, notes, number of stated values checked, a hint for the fix)."""
    failures: list[str] = []
    notes: list[str] = []
    checked = 0
    try:
        suite = Suite(suite_path)
    except SuiteError as error:
        return [str(error)], notes, checked, ""
    head = suite.head[:7]

    if not (root / REQUIRED).is_file():
        failures.append(f"{REQUIRED} is missing")
    required_stated = False
    for path in claim_files(root):
        rel = path.relative_to(root).as_posix()
        for part in parts(path.read_text(encoding="utf-8")):
            if not part.counts:
                continue
            if part.suite is None:
                for kind, value, line in part.counts:
                    failures.append(
                        f"{rel}:{line} states {value} ({kind}) before naming a conformance suite; "
                        f"name the suite and the commit the count was read at first"
                    )
                continue
            if part.suite != SUITE:
                for kind, value, line in part.counts:
                    failures.append(
                        f"{rel}:{line} states {value} ({kind}) for {part.suite}, which this check "
                        f"does not read"
                    )
                continue
            if rel == REQUIRED:
                required_stated = True
            commits = sorted({commit for commit, _ in part.commits})
            if not commits:
                at_head = suite.facts(suite.head)
                for kind, value, line in part.counts:
                    failures.append(
                        f"{rel}:{line} states {value} ({kind}) for {SUITE} and names no commit; "
                        f"at HEAD {head} the suite has {at_head[kind]}"
                    )
                continue
            line = part.commits[0][1]
            if len(commits) > 1:
                failures.append(
                    f"{rel}:{line} names {len(commits)} {SUITE} commits ({', '.join(commits)}); "
                    f"a count is read at one"
                )
                continue
            named = commits[0]
            commit = suite.resolve(named)
            if commit is None:
                failures.append(
                    f"{rel}:{line} names {SUITE} commit {named}, which the suite checkout at "
                    f"{suite_path} does not resolve to one commit; a shallow clone holds only its "
                    f"head, so fetch the suite's history"
                )
                continue
            if not suite.in_head_history(commit):
                failures.append(
                    f"{rel}:{line} names {SUITE} commit {named}, which is not in the history of "
                    f"the suite checkout's HEAD ({head})"
                )
                continue
            facts = suite.facts(commit)
            if facts["fixtures"] == 0:
                failures.append(
                    f"{rel}:{line} names {SUITE} commit {named}, which ships no fixtures; "
                    f"refusing to pass vacuously"
                )
                continue
            for kind, value, count_line in part.counts:
                checked += 1
                if value != facts[kind]:
                    failures.append(
                        f"{rel}:{count_line} states {value} ({kind}) for {SUITE} at {named}, "
                        f"which has {facts[kind]}"
                    )
            moved = suite.facts(suite.head)["fixtures"]
            if commit != suite.head and moved != facts["fixtures"]:
                notes.append(
                    f"note: {rel}:{line} states the {SUITE} count at {named} ({facts['fixtures']} "
                    f"fixtures); at HEAD {head} the suite ships {moved}. The sentence holds at the "
                    f"commit it names."
                )
    if (root / REQUIRED).is_file() and not required_stated:
        failures.append(
            f"{REQUIRED} states no {SUITE} count; the check would pass vacuously, so this is a failure"
        )
    return failures, notes, checked, hint(suite)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--suite", required=True, help=f"path to a git clone of opena2a-standards/{SUITE}")
    ap.add_argument("--root", default=str(ROOT), help="tree to check (default: this repository)")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        failures, notes, checked, fix = check(root, Path(args.suite))
    except SuiteError as error:
        failures, notes, checked, fix = [str(error)], [], 0, ""
    for note in notes:
        print(note)
    if failures:
        print("conformance counts do not match the suite:\n", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        print(
            f"\nState each count with the {SUITE} commit it was read at "
            f"(\"at commit `<sha>`\") and the suite's counts at that commit. {fix}".rstrip(),
            file=sys.stderr,
        )
        return 1
    print(
        f"{SUITE} counts match: {checked} stated value(s) checked, each at the commit "
        f"its sentence names"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
