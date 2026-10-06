#!/usr/bin/env python3
"""Stage the paired Internet-Draft for upload to the IETF datatracker.

Finds the draft that CHANGELOG.md pairs with the version in AIP-SPEC.md (or the
one named with --draft), runs scripts/check_draft_sync.py on it, rebuilds the
txt from the xml when xml2rfc is on PATH and requires the rebuild to be
byte-equal, then prints the txt file to upload and its SHA-256.

It makes no network call and submits nothing. The upload is done by the
draft's author, signed in at https://datatracker.ietf.org/submit/.

    python3 scripts/stage_draft_upload.py [--draft draft-fane-opena2a-aip-NN]

python3 standard library only. Exit code 0 = staged; anything else = do not
upload.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import check_draft_sync

ROOT = check_draft_sync.ROOT
SUBMIT_URL = "https://datatracker.ietf.org/submit/"
MONTHS = {name: number for number, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}


def document_date(xml: str) -> datetime.date:
    match = re.search(r'<date year="(\d{4})" month="([A-Za-z]+)" day="(\d{1,2})"/>', xml)
    if not match:
        raise SystemExit("error: no <date year=... month=... day=...> in the front matter")
    return datetime.date(int(match.group(1)), MONTHS[match.group(2)], int(match.group(3)))


def rebuild_matches(xml_path: Path, txt_path: Path) -> str:
    xml2rfc = shutil.which("xml2rfc")
    if not xml2rfc:
        return "skipped (xml2rfc not on PATH)"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / txt_path.name
        result = subprocess.run(
            [xml2rfc, "--quiet", "--text", str(xml_path), "-o", str(out)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise SystemExit(f"error: xml2rfc failed on {xml_path.name}: {result.stderr.strip()[:400]}")
        if out.read_bytes() != txt_path.read_bytes():
            raise SystemExit(f"error: {txt_path.name} is not the xml2rfc render of {xml_path.name}; rebuild it")
    return "byte-equal"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--draft", help="draft name to stage instead of the paired one")
    args = parser.parse_args(argv)

    name = args.draft
    if name is None:
        spec = check_draft_sync.SPEC.read_text(encoding="utf-8")
        version = check_draft_sync.spec_version(spec)
        name, _ = check_draft_sync.pairing(check_draft_sync.CHANGELOG.read_text(encoding="utf-8"), version)
        if name is None:
            print(f"not staged: no 'Draft pairing' line for {version}")
            return 1
    if check_draft_sync.check(name) != 0:
        print("not staged: the draft does not carry the specification's wire terms")
        return 1

    xml_path, txt_path = ROOT / f"{name}.xml", ROOT / f"{name}.txt"
    if name not in "\n".join(txt_path.read_text(encoding="utf-8").splitlines()[:40]):
        print(f"not staged: {txt_path.name} does not carry {name} in its title block")
        return 1
    print(f"rebuild:  {rebuild_matches(xml_path, txt_path)}")

    dated = document_date(xml_path.read_text(encoding="utf-8"))
    today = datetime.date.today()
    print(f"date:     document {dated.isoformat()}, today {today.isoformat()}")
    if abs((today - dated).days) > 3:
        print("warning:  the document date is more than 3 days from today; set <date> to the upload"
              " day and rebuild before uploading")

    digest = hashlib.sha256(txt_path.read_bytes()).hexdigest()
    print(f"file:     {txt_path}")
    print(f"sha256:   {digest}")
    print(f"upload:   {SUBMIT_URL} (signed in as the draft's author); this script submits nothing")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
