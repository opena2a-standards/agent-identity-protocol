#!/usr/bin/env python3
"""Run a README Quick Start command and write its capture sidecar.

With no argument, or with identity-create, runs
`npx opena2a-cli identity create --name my-agent`, the first command in the
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

With discovery, runs `curl https://aim.opena2a.org/.well-known/aip`, the second
command in the README Quick Start, with HOME set to an empty temporary directory
(so curl reads no .curlrc) and no proxy variables. Writes, under docs/captures/:

    discovery.txt   what curl printed on standard output, untrimmed
    discovery.json  the command, the fixture, the UTC date and the exit code

README.md shows that document under the line
'What `<command>` prints, with line breaks added ([full output](docs/captures/discovery.txt)):',
written by format_json: one object member per line, arrays on one line.
Nothing is written when curl exits non-zero or prints something other than a
JSON object with a providerDid and an endpoints object (curl exits 0 on an HTTP
error, so an error body is refused here).

Run from the repository root (needs node, npx and access to the npm registry
for identity-create; curl and access to aim.opena2a.org for discovery):
    python3 scripts/capture_quick_start.py [identity-create | discovery]
python3 standard library only.
"""
from __future__ import annotations

import argparse
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
DISCOVERY_NAME = "discovery"
DISCOVERY_COMMAND = "curl https://aim.opena2a.org/.well-known/aip"
DISCOVERY_FIXTURE = (
    "HOME is an empty directory created for the run, so curl reads no .curlrc; no proxy "
    "variables are set; standard input is empty and standard output is a pipe"
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


def capture_identity() -> int:
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


def format_json(value: object, indent: str = "") -> str:
    """Return value as JSON text with one object member per line.

    Object members are indented two spaces per level, in the order they were read; any other
    value, arrays included, is written on one line. json.loads of the result equals value.
    """
    if not isinstance(value, dict) or not value:
        return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
    inner = indent + "  "
    members = [f"{inner}{json.dumps(key, ensure_ascii=False)}: {format_json(item, inner)}" for key, item in value.items()]
    return "{\n" + ",\n".join(members) + "\n" + indent + "}"


def discovery_document(text: str) -> dict:
    """Return the discovery document curl printed, refusing anything that is not one."""
    document = json.loads(text)
    if not isinstance(document, dict) or "providerDid" not in document or not isinstance(document.get("endpoints"), dict):
        raise ValueError("the output is not a JSON object with a providerDid and an endpoints object")
    return document


def run_discovery() -> subprocess.CompletedProcess:
    """Run DISCOVERY_COMMAND in its fixture and return the result."""
    with tempfile.TemporaryDirectory(prefix="aip-capture-home-") as home:
        env = {"PATH": os.environ.get("PATH", ""), "HOME": home, "LANG": "en_US.UTF-8", "TERM": "dumb"}
        return subprocess.run(
            shlex.split(DISCOVERY_COMMAND),
            cwd=home,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=120,
        )


def capture_discovery() -> int:
    date = datetime.now(timezone.utc).date().isoformat()
    result = run_discovery()
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        print(f"{DISCOVERY_COMMAND} exited {result.returncode}; nothing written", file=sys.stderr)
        return 1
    try:
        discovery_document(result.stdout)
    except ValueError as error:
        print(f"{DISCOVERY_COMMAND}: {error}; nothing written", file=sys.stderr)
        return 1
    record = {
        "command": DISCOVERY_COMMAND,
        "fixture": DISCOVERY_FIXTURE,
        "date": date,
        "exitCode": result.returncode,
        "stream": "stdout",
        "shown": "the whole document, with line breaks added by format_json in scripts/capture_quick_start.py",
    }
    CAPTURES.mkdir(parents=True, exist_ok=True)
    (CAPTURES / f"{DISCOVERY_NAME}.txt").write_text(result.stdout, encoding="utf-8")
    (CAPTURES / f"{DISCOVERY_NAME}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"wrote docs/captures/{DISCOVERY_NAME}.txt and docs/captures/{DISCOVERY_NAME}.json")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a README Quick Start command and write its capture.")
    parser.add_argument("capture", nargs="?", choices=(NAME, DISCOVERY_NAME), default=NAME)
    args = parser.parse_args([] if argv is None else argv)
    return capture_identity() if args.capture == NAME else capture_discovery()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
