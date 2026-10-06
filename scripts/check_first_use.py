#!/usr/bin/env python3
"""Check that the first use of the name AIM in each reader-facing file is expanded.

The first line of a checked file that contains the whole word AIM must also
contain the exact phrase "OpenA2A AIM (Agent Identity Management)", so a
reader meets the full name before the bare acronym. Later lines may use AIM
alone. A file without the word passes. FILES lists the specification and the
documents a reader reaches from it or from the repository page.

Run in CI by scripts/validate_examples.py. Also runs on its own:
    python3 scripts/check_first_use.py [FILE ...]
With no FILE it checks the files in FILES. python3 standard library only.
Exit code 0 = every checked file passes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / name
    for name in (
        "AIP-SPEC.md",
        "README.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "GAP-ANALYSIS.md",
    )
]
PHRASE = "OpenA2A AIM (Agent Identity Management)"
WORD = re.compile(r"\bAIM\b")


def first_use_error(path: Path) -> str | None:
    """Return why the first use fails, or None when it is expanded or absent."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        if WORD.search(line):
            if PHRASE in line:
                return None
            return f"line {number} does not contain {PHRASE!r}: {line.strip()[:120]}"
    return None


def check(paths: list[Path]) -> int:
    failures = 0
    for path in paths:
        name = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        error = first_use_error(path)
        if error:
            print(f"first use FAIL {name}: {error}")
            failures += 1
        else:
            print(f"first use OK   {name}")
    return failures


def main(argv: list[str]) -> int:
    paths = [Path(arg).resolve() for arg in argv] or FILES
    return 1 if check(paths) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
