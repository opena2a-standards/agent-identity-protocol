#!/usr/bin/env python3
"""Check that the Internet-Draft paired with the spec version carries its wire terms.

CHANGELOG.md pairs each spec version with one draft revision in a line of the
form "Draft pairing: `draft-fane-opena2a-aip-NN` pairs with <version>". For the
version in AIP-SPEC.md this script finds that line and checks the paired
draft-fane-opena2a-aip-NN.{xml,txt}:

- the xml docName is the paired name;
- every tracked term is present in the draft text exactly when it is present
  in the specification (reject categories, the behavioral tier and unscored
  state fields, the clock-skew citation, the "trustLevel" JSON key that the
  tier rename removed), matched as a whole word so a renamed field such as
  "behaviorTierX" does not count as "behaviorTier";
- the capability grammar of Section 4.1 appears verbatim, and every namespace
  in registries/capability-namespaces.json is a row of the draft's namespace
  table;
- the draft carries the phrase "OpenA2A AIM (Agent Identity Management)" when
  the spec does, and the first use of AIM in the draft text is that phrase.

The pairing paragraph is the text from that line to the next blank line,
heading or list item, wherever it sits under the version's heading.

README.md must disclose the same pairing in one paragraph that starts with
"**Internet-Draft.**": it names the paired draft and the spec version; when
the pairing paragraph says the paired draft is not submitted, it says so too,
says the datatracker copy "is behind this repository", and names the revision
the CHANGELOG records as current on the datatracker, with its submission date
and the version it carries; once the pairing no longer says "not submitted",
the README may say neither. The pairing paragraph names that revision in one
sentence shape only (line breaks allowed):
    `draft-fane-opena2a-aip-NN` (submitted YYYY-MM-DD) remains the current
    datatracker revision and carries the <version> text

A version whose CHANGELOG heading still reads "unreleased" may name a draft that
is not built yet: that is the disclosed pending state and passes. A dated
version must have its paired draft. A version with no pairing line fails.

Run in CI by scripts/validate_examples.py. Also runs on its own:
    python3 scripts/check_draft_sync.py [--draft draft-fane-opena2a-aip-NN]
--draft checks the named revision against the current spec instead of the
paired one, and skips the README check. python3 standard library only. Exit
code 0 = in sync or pending.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Imported by module name; an isolated run (python3 -I or -P) leaves this
# directory off the path, so add it as a plain run does.
SCRIPTS = str(Path(__file__).resolve().parent)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import check_first_use

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "AIP-SPEC.md"
CHANGELOG = ROOT / "CHANGELOG.md"
README = ROOT / "README.md"
README_MARKER = "**Internet-Draft.**"
README_BEHIND = "is behind this repository"
CURRENT_SHAPE = (
    "`draft-fane-opena2a-aip-NN` (submitted YYYY-MM-DD) remains the current"
    " datatracker revision and carries the <version> text"
)
CURRENT = re.compile(
    r"`(draft-fane-opena2a-aip-\d\d)` \(submitted (\d{4}-\d{2}-\d{2})\) remains the current"
    r" datatracker revision and carries the (\S+) text"
)
NAMESPACES = ROOT / "registries" / "capability-namespaces.json"
GRAMMAR_MARKER = "<!-- opena2a-definition: capability-grammar -->"

# Present in the draft exactly when present in the spec.
TRACKED = [
    "SIGNATURE_INVALID",
    "UNTRUSTED_KEY",
    "CHALLENGE_EXPIRED",
    "NONCE_REPLAY",
    "behaviorTier",
    '"trustLevel":',
    "algorithmVersion",
    "scoreStatus",
    "unscoredReason",
    "includedWeight",
    "excludedFactors",
    "clock-skew bound",
]

# A blank line, a heading or a list item ends the pairing paragraph.
PARAGRAPH_END = re.compile(r"\n[ \t]*(?:\n|#|[-*+] )")

PAGE_LINE = re.compile(r"^(Fane\s+Expires\b.*\[Page \d+\]|Internet-Draft\s+OpenA2A AIP\s+.*)$")


def spec_version(text: str) -> str:
    match = re.search(r"^\*\*Version:\*\*\s*(\S+)", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"error: no **Version:** line in {SPEC.name}")
    return match.group(1)


def version_section(changelog: str, version: str) -> tuple[str, bool]:
    """Return (the text under the version's heading, whether the heading is dated)."""
    heading = re.compile(r"^## \[" + re.escape(version) + r"\] - (.+)$", re.MULTILINE)
    match = heading.search(changelog)
    if not match:
        raise SystemExit(f"error: no '## [{version}]' heading in {CHANGELOG.name}")
    dated = re.fullmatch(r"\d{4}-\d{2}-\d{2}", match.group(1).strip()) is not None
    end = changelog.find("\n## ", match.end())
    return changelog[match.end(): end if end != -1 else len(changelog)], dated


def pairing_paragraph(section: str, version: str) -> tuple[str | None, str]:
    """Return (paired draft name or None, the pairing paragraph with whitespace collapsed)."""
    paired = re.search(
        r"Draft pairing: `(draft-fane-opena2a-aip-\d\d)` pairs with\s+" + re.escape(version),
        section,
    )
    if not paired:
        return None, ""
    end = PARAGRAPH_END.search(section, paired.end())
    text = section[paired.start(): end.start() if end else len(section)]
    return paired.group(1), re.sub(r"\s+", " ", text).strip()


def pairing(changelog: str, version: str) -> tuple[str | None, bool]:
    """Return (paired draft name or None, whether the version heading is dated)."""
    section, dated = version_section(changelog, version)
    return pairing_paragraph(section, version)[0], dated


def draft_text(txt: str) -> str:
    """The rendered draft as one line: page breaks, headers and footers removed,
    line-end hyphen breaks rejoined, whitespace collapsed."""
    kept = [line for line in txt.replace("\f", "\n").splitlines() if not PAGE_LINE.match(line.strip())]
    joined = re.sub(r"-\n\s+", "-", "\n".join(kept))
    return re.sub(r"\s+", " ", joined)


def grammar(spec: str) -> str:
    after = spec.split(GRAMMAR_MARKER, 1)
    if len(after) != 2:
        raise SystemExit(f"error: no {GRAMMAR_MARKER} in {SPEC.name}")
    block = re.search(r"```json\n(.*?)\n```", after[1], re.DOTALL)
    if not block:
        raise SystemExit("error: no ```json block after the capability-grammar marker")
    return json.loads(block.group(1))["grammar"]


def table_first_cells(txt: str) -> set[str]:
    return {m.group(1) for m in re.finditer(r"^\s*\|\s*([a-z][a-z0-9_.-]*)\s+\|", txt, re.MULTILINE)}


def carries(text: str, term: str) -> bool:
    """Whether text carries term as a whole word: a word character at either end
    of the term may not run on into a longer name."""
    pattern = re.escape(term)
    if re.match(r"\w", term):
        pattern = r"\b" + pattern
    if re.search(r"\w$", term):
        pattern += r"\b"
    return re.search(pattern, text) is not None


def first_use_error(text: str) -> str | None:
    match = check_first_use.WORD.search(text)
    if not match:
        return None
    for phrase in re.finditer(re.escape(check_first_use.PHRASE), text):
        if phrase.start() <= match.start() < phrase.end():
            return None
    start = max(0, match.start() - 60)
    return f"first AIM is not {check_first_use.PHRASE!r}: ...{text[start:match.end() + 40]}..."


def check_draft(name: str, spec: str) -> list[str]:
    xml_path, txt_path = ROOT / f"{name}.xml", ROOT / f"{name}.txt"
    problems = [f"{p.name} missing" for p in (xml_path, txt_path) if not p.exists()]
    if problems:
        return problems
    if f'docName="{name}"' not in xml_path.read_text(encoding="utf-8"):
        problems.append(f'{xml_path.name}: docName is not "{name}"')
    raw = txt_path.read_text(encoding="utf-8")
    text = draft_text(raw)
    flat_spec = re.sub(r"\s+", " ", spec)
    for term in TRACKED:
        in_spec, in_draft = carries(flat_spec, term), carries(text, term)
        if in_spec and not in_draft:
            problems.append(f"{txt_path.name}: lacks {term!r}, which the spec carries")
        elif in_draft and not in_spec:
            problems.append(f"{txt_path.name}: carries {term!r}, which the spec no longer does")
    if grammar(spec) not in text:
        problems.append(f"{txt_path.name}: lacks the Section 4.1 capability grammar")
    rows = table_first_cells(raw)
    registry = json.loads(NAMESPACES.read_text(encoding="utf-8"))
    for row in registry["rows"]:
        if row[registry["key"]] not in rows:
            problems.append(f"{txt_path.name}: namespace table lacks {row[registry['key']]!r}")
    if check_first_use.PHRASE in flat_spec and check_first_use.PHRASE not in text:
        problems.append(f"{txt_path.name}: lacks {check_first_use.PHRASE!r}, which the spec carries")
    error = first_use_error(text)
    if error:
        problems.append(f"{txt_path.name}: {error}")
    return problems


def disclosure_problems(readme: str, changelog: str, version: str, draft: str) -> list[str]:
    """What the README's Internet-Draft paragraph misstates against the CHANGELOG pairing."""
    paragraphs = [p for p in re.split(r"\n\s*\n", readme) if p.strip().startswith(README_MARKER)]
    if len(paragraphs) != 1:
        return [f"expected one paragraph starting {README_MARKER!r}, found {len(paragraphs)}"]
    text = re.sub(r"\s+", " ", paragraphs[0])
    section, _ = version_section(changelog, version)
    _, pairing_text = pairing_paragraph(section, version)
    pending = "not submitted" in pairing_text
    expected = [draft, version]
    problems = []
    if pending:
        current = CURRENT.search(pairing_text)
        if current:
            expected += list(current.groups())
        else:
            problems.append(
                f"{CHANGELOG.name} says {draft} is not submitted and names no current revision"
                f" in the form: {CURRENT_SHAPE}"
            )
    for term in expected:
        if term not in text:
            problems.append(f"Internet-Draft paragraph lacks {term!r}, which {CHANGELOG.name} records")
    if pending and "not submitted" not in text:
        problems.append(f"Internet-Draft paragraph does not say {draft} is not submitted")
    if not pending and "not submitted" in text:
        problems.append(f"Internet-Draft paragraph says 'not submitted'; {CHANGELOG.name} no longer does")
    if pending and README_BEHIND not in text:
        problems.append(f"Internet-Draft paragraph does not say the datatracker copy {README_BEHIND!r}")
    if not pending and README_BEHIND in text:
        problems.append(
            f"Internet-Draft paragraph says the datatracker copy {README_BEHIND!r};"
            f" {CHANGELOG.name} no longer says {draft} is not submitted"
        )
    return problems


def check_disclosure(changelog: str, version: str, draft: str) -> int:
    problems = disclosure_problems(README.read_text(encoding="utf-8"), changelog, version, draft)
    for problem in problems:
        print(f"draft sync FAIL {README.name}: {problem}")
    if not problems:
        print(f"draft sync OK   {README.name} discloses the {draft} pairing with {version}")
    return 1 if problems else 0


def check(draft: str | None = None) -> int:
    spec = SPEC.read_text(encoding="utf-8")
    version = spec_version(spec)
    disclosure = 0
    if draft is None:
        changelog = CHANGELOG.read_text(encoding="utf-8")
        draft, dated = pairing(changelog, version)
        if draft is None:
            print(f"draft sync FAIL {version}: no 'Draft pairing' line under its {CHANGELOG.name} heading")
            return 1
        disclosure = check_disclosure(changelog, version, draft)
        if not dated and not (ROOT / f"{draft}.txt").exists():
            print(f"draft sync PENDING {version}: {draft} not built; the version is unreleased")
            return disclosure
    problems = check_draft(draft, spec)
    for problem in problems:
        print(f"draft sync FAIL {draft} vs {version}: {problem}")
    if not problems:
        print(f"draft sync OK   {draft} carries the {version} wire terms")
    return 1 if problems or disclosure else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--draft", help="draft name to check instead of the paired one")
    args = parser.parse_args(argv)
    return check(args.draft)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
