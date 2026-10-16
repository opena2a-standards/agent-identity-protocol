#!/usr/bin/env python3
"""Run the README Quick Start command and write its capture sidecar.

Runs `npx opena2a-cli identity create --name my-agent`, the first command in the
README Quick Start, as a reader runs it for the first time: HOME is an empty
directory created for the run, and npm's prefix and cache are empty directories
created for the run, so npx installs opena2a-cli from the npm registry rather than
running a global install. Standard input is empty and standard output is a pipe.
Writes, under docs/captures/:

    identity-create.txt   what the command printed on standard output, untrimmed
    identity-create.json  the command, the opena2a-cli version npx installed, the
                          fixture, the UTC date, the exit code and the line range
                          of the .txt that README.md shows

README.md shows that range under the line
'What `<command>` prints ([full output](docs/captures/identity-create.txt)):', and
tests/test_quick_start_capture.py checks that the two agree. Nothing is written
when the command exits non-zero. Both temporary directories are removed afterwards.

Run from the repository root (needs node, npx and access to the npm registry):
    python3 scripts/capture_quick_start.py
python3 standard library only.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAPTURES = ROOT / "docs" / "captures"
NAME = "identity-create"
PACKAGE = "opena2a-cli"
COMMAND = "npx opena2a-cli identity create --name my-agent"
# The command prints the path of its data directory, which sits under HOME, so HOME is a
# fixed path that names no user rather than a randomly named temporary directory.
HOME = Path("/tmp/aip-quick-start")
FIXTURE = (
    f"HOME is {HOME}, an empty directory created for the run; npm's prefix and cache are "
    "empty directories created for the run, so npx installs the package from the npm "
    "registry; standard input is empty and standard output is a pipe"
)


def excerpt_range(lines: list[str]) -> tuple[int, int]:
    """Return the first and last line numbers (from 1) of the lines that hold text."""
    numbers = [n for n, line in enumerate(lines, 1) if line.strip()]
    if not numbers:
        raise ValueError("the command printed nothing on standard output")
    return numbers[0], numbers[-1]


def installed_version(cache: Path) -> str:
    """Return the version of the one opena2a-cli install npx made in the npm cache."""
    manifests = sorted(cache.glob(f"_npx/*/node_modules/{PACKAGE}/package.json"))
    if len(manifests) != 1:
        raise RuntimeError(f"expected one {PACKAGE} install in the npx cache, found {len(manifests)}")
    return json.loads(manifests[0].read_text(encoding="utf-8"))["version"]


def run_command() -> tuple[subprocess.CompletedProcess, str]:
    """Run COMMAND in the fixture and return its result and the installed version."""
    # Raises FileExistsError when HOME is already there, before anything is removed.
    HOME.mkdir()
    try:
        with tempfile.TemporaryDirectory(prefix="aip-capture-npm-") as npm:
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(HOME),
                "LANG": "en_US.UTF-8",
                "TERM": "dumb",
                "npm_config_prefix": str(Path(npm, "prefix")),
                "npm_config_cache": str(Path(npm, "cache")),
                "npm_config_update_notifier": "false",
            }
            if "TMPDIR" in os.environ:
                env["TMPDIR"] = os.environ["TMPDIR"]
            result = subprocess.run(
                shlex.split(COMMAND),
                cwd=HOME,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=600,
            )
            version = installed_version(Path(npm, "cache")) if result.returncode == 0 else ""
    finally:
        shutil.rmtree(HOME, ignore_errors=True)
    return result, version


def main() -> int:
    if HOME.exists():
        print(f"{HOME} exists; remove it so the command runs in an empty home directory", file=sys.stderr)
        return 2
    date = datetime.now(timezone.utc).date().isoformat()
    result, version = run_command()
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        print(f"{COMMAND} exited {result.returncode}; nothing written", file=sys.stderr)
        return 1
    first, last = excerpt_range(result.stdout.splitlines())
    record = {
        "command": COMMAND,
        "package": PACKAGE,
        "version": version,
        "fixture": FIXTURE,
        "date": date,
        "exitCode": result.returncode,
        "stream": "stdout",
        "excerpt": {"firstLine": first, "lastLine": last},
    }
    CAPTURES.mkdir(parents=True, exist_ok=True)
    (CAPTURES / f"{NAME}.txt").write_text(result.stdout, encoding="utf-8")
    (CAPTURES / f"{NAME}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote docs/captures/{NAME}.txt and docs/captures/{NAME}.json ({PACKAGE} {version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
