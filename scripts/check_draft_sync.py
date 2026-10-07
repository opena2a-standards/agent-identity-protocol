#!/usr/bin/env python3
"""Check that the Internet-Draft paired with the spec version carries its wire terms.

CHANGELOG.md pairs each spec version with one draft revision in a line of the
form "Draft pairing: `draft-fane-opena2a-aip-NN` pairs with <version>". For the
version in AIP-SPEC.md this script finds that line and checks the paired
draft-fane-opena2a-aip-NN.{xml,txt}:

- the xml docName is the paired name;
- the parsed rfc element's submissionType is independent, editorial or
  empty, or absent: an individual draft has no stream on the datatracker,
  idnits 3.1.0 reports SUBMISSION_TYPE_UNEXPECTED for IETF, IAB and IRTF,
  SUBMISSION_TYPE_INVALID for a non-empty value other than those five, and
  nothing for an empty one. The value is read as idnits reads it: the
  attribute text as written, with the whitespace JavaScript's trim() removes
  taken off each end before any character reference is decoded, compared in
  lower case. So "&#32;independent" is invalid and a leading U+FEFF is
  removed. Without the attribute xml2rfc 3.34.0 warns "Expected a valid
  submissionType (stream) setting" and uses 'IETF' to render; that warning
  is expected;
- every BCP 14 keyword in the xml text sits in a <bcp14> element (text in
  <artwork> and <sourcecode>, and in any element nested in those or in
  <bcp14>, is verbatim or tagged and exempt): idnits skips the BCP 14
  boilerplate paragraph ("The key words ... in this document ...") and
  reports untagged keywords elsewhere in the text it checks as
  MISSING_BCP14_TAGS, and, since it counts a reference to BCP 14 on the xml
  only through an external entity or a tagged keyword, reports
  MISSING_REQLEVEL_REF when none is tagged. The failure line also counts the
  untagged keywords in <t> or <li> text outside that paragraph. Both the
  paragraph test and that count read an element's text as idnits does: each
  text segment (the element's text and the tail of each child) trimmed, and
  the segments joined with no separator, so "Before <xref/> MUST" reads as
  "BeforeMUST" and holds no keyword. The count is an estimate of idnits'
  MISSING_BCP14_TAGS: it equals the count idnits 3.1.0 reports on -00 to -03
  and on the -04 xml without its tags, and can differ on other xml, because
  idnits selects the text it checks by a different rule;
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
and the version it carries. Once the pairing no longer says "not submitted",
it must record the paired draft's submission in the second shape below, and
the README names that submission date and may say neither. The pairing
paragraph names each revision in one sentence shape only (line breaks
allowed):
    `draft-fane-opena2a-aip-NN` (submitted YYYY-MM-DD) remains the current
    datatracker revision and carries the <version> text
    `draft-fane-opena2a-aip-NN` (submitted YYYY-MM-DD) is the current
    datatracker revision

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
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple

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
SUBMITTED_SHAPE = "`draft-fane-opena2a-aip-NN` (submitted YYYY-MM-DD) is the current datatracker revision"
SUBMITTED = re.compile(
    r"`(draft-fane-opena2a-aip-\d\d)` \(submitted (\d{4}-\d{2}-\d{2})\) is the current datatracker revision"
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

# idnits 3.1.0 reports SUBMISSION_TYPE_UNEXPECTED for these submissionType
# values, read as stream_value reads them, when the datatracker has no stream
# for the draft.
FLAGGED_STREAMS = {"ietf", "iab", "irtf"}
# idnits 3.1.0 reports SUBMISSION_TYPE_INVALID for any non-empty submissionType
# value outside these, read the same way.
VALID_STREAMS = FLAGGED_STREAMS | {"independent", "editorial"}
# The characters JavaScript's String.prototype.trim() removes, with which idnits
# 3.1.0 trims attribute values and text segments: tab, line feed, vertical tab,
# form feed, carriage return, U+2028, U+2029, U+FEFF and every Zs space.
# Python's str.strip() differs: it also removes U+0085 and U+001C to U+001F,
# and keeps U+FEFF.
JS_WHITESPACE = (
    "\t\n\v\f\r\u2028\u2029\ufeff"
    " \xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u202f\u205f\u3000"
)

BCP14_KEYWORD = re.compile(
    r"\b(?:MUST\s+NOT|SHALL\s+NOT|SHOULD\s+NOT|NOT\s+RECOMMENDED"
    r"|MUST|SHALL|SHOULD|RECOMMENDED|REQUIRED|MAY|OPTIONAL)\b"
)
# Text in these elements needs no <bcp14> tag: the tag itself and verbatim blocks.
TAGGED_OR_VERBATIM = {"bcp14", "artwork", "sourcecode"}
# idnits 3.1.0 checks no keyword in a text that matches its BCP 14 boilerplate
# pattern, /The key\s?words .+? in this document .+?./is. Searched as one
# pattern, it rescans the rest of the text from every "The key words", which
# takes quadratic time; bcp14_boilerplate applies it in two linear steps.
BCP14_KEY_WORDS = re.compile(r"The key\s?words ", re.IGNORECASE)
BCP14_IN_DOCUMENT = re.compile(r" in this document ..", re.IGNORECASE | re.DOTALL)
# The failure line's second count takes keywords only from the text of these
# elements, tails of their children included. It is an estimate of idnits'
# MISSING_BCP14_TAGS: it equals the count idnits 3.1.0 reports on -00 to -03
# and on the -04 xml without its tags; idnits selects the text it checks by a
# different rule, so on other xml the two can differ.
COUNTED_TEXT = {"t", "li"}


class Untagged(NamedTuple):
    keyword: str
    context: str
    boilerplate: bool  # in the BCP 14 boilerplate paragraph, which idnits skips
    # In the failure line's second count: outside the boilerplate paragraph, in
    # the text of a COUNTED_TEXT element, and still a keyword once that element's
    # text segments are trimmed and joined.
    counted: bool

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


def submission_type(xml: str) -> str | None:
    """The rfc element's submissionType as written, character references not
    decoded, or None when it has none. Each "&#" is escaped before parsing, so
    the parser decodes "&amp;#32;" to "&#32;" and leaves the reference as idnits
    reads it."""
    return ET.fromstring(xml.replace("&#", "&amp;#")).get("submissionType")


def stream_value(stream: str) -> str:
    """A submissionType as idnits 3.1.0 compares it: the text as written,
    trimmed as JavaScript's trim() trims, in lower case. idnits trims before it
    handles character references and leaves most numeric ones undecoded, so a
    value that still holds a reference is no stream name here."""
    return stream.strip(JS_WHITESPACE).lower()


def flagged_stream(xml: str) -> str | None:
    """The rfc element's submissionType when idnits flags it on a draft that has
    no datatracker stream, else None."""
    stream = submission_type(xml)
    return stream if stream is not None and stream_value(stream) in FLAGGED_STREAMS else None


def invalid_stream(xml: str) -> str | None:
    """The rfc element's submissionType when idnits reports it as SUBMISSION_TYPE_INVALID, else None.
    idnits skips a value that is empty once trimmed."""
    stream = submission_type(xml)
    value = stream_value(stream or "")
    return stream if value and value not in VALID_STREAMS else None


def bcp14_boilerplate(text: str) -> bool:
    """Whether idnits' BCP 14 boilerplate pattern matches text. The first
    "The key words" ends earliest, so the pattern matches exactly when " in
    this document " starts at least one character after it and two characters
    follow."""
    key = BCP14_KEY_WORDS.search(text)
    return key is not None and BCP14_IN_DOCUMENT.search(text, key.end() + 1) is not None


def untagged_keywords(root: ET.Element) -> list[Untagged]:
    """Each BCP 14 keyword in the xml text that no <bcp14>, <artwork> or
    <sourcecode> element encloses, in document order. An element's text is
    read as idnits 3.1.0 reads it: each segment (the element's text and each
    child's tail) trimmed as JavaScript's trim() trims, whitespace collapsed,
    and the segments joined with no separator. The boilerplate test and the
    second count read the joined text; each keyword is found in its own
    segment. The walk keeps its own stack, so no nesting depth raises
    RecursionError."""
    found: list[Untagged] = []

    def scan(segment: str, start: int, boilerplate: bool, counted: set[tuple[int, int]]) -> None:
        for match in BCP14_KEYWORD.finditer(segment):
            context = segment[max(0, match.start() - 30): match.end() + 30].strip()
            span = (start + match.start(), start + match.end())
            found.append(Untagged(match.group(0), context, boilerplate, span in counted))

    # An element still to visit, or a child's tail to scan with its offset in
    # the parent's joined text, the parent's boilerplate flag and counted spans.
    stack: list[ET.Element | tuple[str, int, bool, set[tuple[int, int]]]] = [root]
    while stack:
        item = stack.pop()
        if isinstance(item, tuple):
            scan(*item)
            continue
        if item.tag in TAGGED_OR_VERBATIM:
            continue
        texts = [item.text, *(child.tail for child in item)]
        segments = [re.sub(r"\s+", " ", (text or "").strip(JS_WHITESPACE)) for text in texts]
        starts = [0]
        for segment in segments:
            starts.append(starts[-1] + len(segment))
        joined = "".join(segments)
        boilerplate = bcp14_boilerplate(joined)
        counted: set[tuple[int, int]] = set()
        if item.tag in COUNTED_TEXT and not boilerplate:
            counted = {match.span() for match in BCP14_KEYWORD.finditer(joined)}
        scan(segments[0], 0, boilerplate, counted)
        for child, segment, start in reversed(list(zip(item, segments[1:], starts[1:]))):
            stack.append((segment, start, boilerplate, counted))
            stack.append(child)
    return found


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
    xml = xml_path.read_text(encoding="utf-8")
    if f'docName="{name}"' not in xml:
        problems.append(f'{xml_path.name}: docName is not "{name}"')
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as error:
        problems.append(f"{xml_path.name}: not well-formed xml: {error}")
    else:
        stream = flagged_stream(xml)
        if stream is not None:
            problems.append(
                f"{xml_path.name}: the rfc element sets submissionType={stream!r}; an individual draft has"
                " no datatracker stream, so idnits reports SUBMISSION_TYPE_UNEXPECTED. Remove the attribute."
            )
        stream = invalid_stream(xml)
        if stream is not None:
            problems.append(
                f"{xml_path.name}: the rfc element sets submissionType={stream!r}, which is not IETF, IAB,"
                " IRTF, independent or editorial, so idnits reports SUBMISSION_TYPE_INVALID. Remove the attribute."
            )
        untagged = untagged_keywords(root)
        if untagged:
            first = untagged[0]
            counted = sum(u.counted for u in untagged)
            problems.append(
                f"{xml_path.name}: {len(untagged)} BCP 14 keyword(s) outside <bcp14>, first {first.keyword!r}"
                f" in '...{first.context}...'; {counted} of them, in <t> or <li> text outside the BCP 14"
                " boilerplate paragraph, are an estimate of idnits' MISSING_BCP14_TAGS count, and"
                " idnits reports MISSING_REQLEVEL_REF when none is tagged. Wrap each in <bcp14>."
            )
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
    else:
        submitted = SUBMITTED.search(pairing_text)
        if submitted and submitted.group(1) == draft:
            expected.append(submitted.group(2))
        else:
            problems.append(
                f"{CHANGELOG.name} does not say {draft} is not submitted and records no submission"
                f" of it in the form: {SUBMITTED_SHAPE}"
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
