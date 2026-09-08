#!/usr/bin/env python3
"""Generate registries/<id>.json from the marked definition tables in the spec.

A table-shaped shared definition sits under a marker comment
`<!-- opena2a-definition: <id> -->` in the specification; the table that
follows the marker is the definition, and the JSON file under registries/ is
generated from it so consumers can pin a file by commit the way the
conformance suites pin schemas. `--check` fails when a generated file is
stale. python3 standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "AIP-SPEC.md"
REGISTRIES = ROOT / "registries"
# Marker ids whose table is exported. Keep in step with the drift harness homes.
TABLES = {"capability-namespaces": {"key": "Namespace"}}


def strip_cell(cell: str) -> str:
    c = cell.strip()
    c = re.sub(r"^\*\*(.*)\*\*$", r"\1", c)
    c = re.sub(r"^`(.*)`$", r"\1", c)
    return c.strip()


def table_after_marker(lines: list, marker: str) -> tuple:
    for i, line in enumerate(lines):
        if marker in line:
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("|"):
                if lines[j].startswith("#"):
                    raise SystemExit(f"{marker}: no table before the next heading")
                j += 1
            headers = [strip_cell(c) for c in lines[j].strip().strip("|").split("|")]
            rows = []
            j += 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                cells = [strip_cell(c) for c in lines[j].strip().strip("|").split("|")]
                rows.append(dict(zip(headers, cells)))
                j += 1
            return headers, rows
    raise SystemExit(f"marker not found in {SPEC.name}: {marker}")


def generate() -> dict:
    lines = SPEC.read_text(encoding="utf-8").split("\n")
    out = {}
    for rid, cfg in TABLES.items():
        headers, rows = table_after_marker(lines, f"<!-- opena2a-definition: {rid} -->")
        out[rid] = {
            "id": rid,
            "source": {"file": SPEC.name, "marker": f"<!-- opena2a-definition: {rid} -->"},
            "columns": headers,
            "key": cfg["key"],
            "rows": rows,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if a generated file is stale")
    args = ap.parse_args()
    stale = []
    for rid, data in generate().items():
        path = REGISTRIES / f"{rid}.json"
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(str(path.relative_to(ROOT)))
        else:
            REGISTRIES.mkdir(exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)} ({len(data['rows'])} rows)")
    if stale:
        print("stale registries (run scripts/gen_registries.py): " + ", ".join(stale), file=sys.stderr)
        return 1
    if args.check:
        print("registries match the specification tables")
    return 0


if __name__ == "__main__":
    sys.exit(main())
