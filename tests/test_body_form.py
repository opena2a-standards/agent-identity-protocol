#!/usr/bin/env python3
"""Regression tests for the body form that AIP-SPEC.md §5.1.4 rejects before its checks.

Before the checks, §5.1.4 rejects as PARSE_ERROR a challenge or response body
that is not a JSON object, a body from which a member that §5.1.1 or §5.1.2
gives it is absent or holds a value that is not a JSON string, and a challenge
body whose `issuedAt` or `expiresAt` is not in the date-time form the section
states. These tests read that rule from the section, check each example
timestamp it gives against the date-time form as the section states it, and
check that the §5.1.1 and §5.1.2 example bodies have the form and that the
body schemas require each member those sections give, as a string.

Run from the repository root:
    python3 -m unittest discover -s tests
python3 standard library only.
"""
from __future__ import annotations

import calendar
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "AIP-SPEC.md"
CHALLENGE_SCHEMA = ROOT / "schemas" / "challenge-body-v1.schema.json"
RESPONSE_SCHEMA = ROOT / "schemas" / "response-body-v1.schema.json"

RULE_START = "Before the checks below, a relying party MUST also reject the transcript"
CHECKS_START = "A relying party MUST reject the transcript unless all of the following hold."
FORM_START = "The date-time form is "
FENCED_JSON = re.compile(r"^```json\n(.*?)^```", re.DOTALL | re.MULTILINE)
# "`a` and `b` are in this form, and `c`, `d` and `e` are not."
EXAMPLES = re.compile(
    r"((?:`[^`]+`(?:,? and |, ))*`[^`]+`) are in this form, and "
    r"((?:`[^`]+`(?:,? and |, ))*`[^`]+`) are not\."
)
BACKTICKED = re.compile(r"`([^`]+)`")

# The date-time form as §5.1.4 states it: the date-time production of RFC 3339
# Section 5.6 with an upper-case T and Z, ASCII digits only, an optional full
# stop and one or more digits of fractional seconds, and Z or +HH:MM or -HH:MM.
FORM = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
    r"T(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})(?:\.[0-9]+)?"
    r"(?:Z|[+-](?P<offset_hour>[0-9]{2}):(?P<offset_minute>[0-9]{2}))"
)
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def in_date_time_form(value: str) -> bool:
    """Whether value is in the §5.1.4 date-time form.

    The day must be a day of its month in the Gregorian calendar, the hour
    and the offset hour 00 to 23, and the minute, the second and the offset
    minute 00 to 59.
    """
    match = FORM.fullmatch(value)
    if match is None:
        return False
    field = {name: int(text) for name, text in match.groupdict(default="0").items()}
    if not 1 <= field["month"] <= 12:
        return False
    days = DAYS_IN_MONTH[field["month"] - 1]
    if field["month"] == 2 and calendar.isleap(field["year"]):
        days = 29
    return (
        1 <= field["day"] <= days
        and field["hour"] <= 23
        and field["minute"] <= 59
        and field["second"] <= 59
        and field["offset_hour"] <= 23
        and field["offset_minute"] <= 59
    )


def section(spec: str, heading: str, next_heading: str) -> str:
    start = spec.index(heading)
    return spec[start : spec.index(next_heading, start)]


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def list_items(block: str) -> list[str]:
    """Return the "- " items of a block, each with its continuation lines joined by single spaces."""
    items: list[str] = []
    for line in block.splitlines():
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif items and line.strip():
            items[-1] += " " + line.strip()
    return items


def unique_members(pairs: list[tuple[str, object]]) -> dict:
    names = [name for name, _ in pairs]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        raise AssertionError(f"member names used twice in one object: {repeated}")
    return dict(pairs)


def example_body(spec: str, heading: str, next_heading: str) -> object:
    """The first ```json block under heading, parsed, with each member name used once."""
    block = FENCED_JSON.search(section(spec, heading, next_heading))
    if block is None:
        raise AssertionError(f"no ```json block under {heading!r}")
    return json.loads(block.group(1), object_pairs_hook=unique_members)


def string_typed(schema: dict, member: dict) -> bool:
    """Whether a schema member admits JSON strings only: a string type, a string enum, or a $defs entry of either."""
    if "$ref" in member:
        member = schema["$defs"][member["$ref"].split("#/$defs/", 1)[1]]
    if "enum" in member:
        return bool(member["enum"]) and all(isinstance(value, str) for value in member["enum"])
    return member.get("type") == "string"


class FormRule(unittest.TestCase):
    """§5.1.4 rejects a body outside the §5.1.1 and §5.1.2 form as PARSE_ERROR, before the checks."""

    def setUp(self) -> None:
        self.section = section(SPEC.read_text(encoding="utf-8"), "#### 5.1.4 ", "#### 5.1.5 ")
        self.assertTrue(RULE_START in self.section, "§5.1.4 states no body form rule before its checks")
        self.assertTrue(CHECKS_START in self.section, "§5.1.4 has no lead-in to its checks")
        start = self.section.index(RULE_START)
        self.assertLess(start, self.section.index(CHECKS_START), "the body form rule follows the checks")
        self.rule = self.section[start : self.section.index(CHECKS_START)]
        self.blocks = [block for block in re.split(r"\n\s*\n", self.rule) if block.strip()]

    def test_rule_rejects_with_parse_error(self) -> None:
        self.assertIn("(reject category `PARSE_ERROR`)", flat(self.blocks[0]))

    def test_rule_lists_the_three_form_defects(self) -> None:
        items = [flat(item) for item in list_items(self.rule)]
        self.assertEqual(len(items), 3, items)
        not_object, member, timestamp = items
        self.assertEqual(not_object, "The challenge body or the response body is not a JSON object.")
        self.assertIn("A member that §5.1.1 or §5.1.2 gives a body is absent from that body", member)
        self.assertIn("its value is not a JSON string", member)
        self.assertIn("A value of `null` is not a string.", member)
        self.assertIn("The challenge body's `issuedAt` or `expiresAt`", timestamp)
        self.assertIn("is not in the date-time form below", timestamp)

    def test_response_timestamps_are_strings_only(self) -> None:
        # The form test reads the challenge body's two timestamps. Check 1 compares the response's
        # echoes with them, so a response timestamp in another form fails there, not here.
        form = flat(next(block for block in self.blocks if block.startswith(FORM_START)))
        self.assertIn(
            "The response's `issuedAt`, `expiresAt` and `signedAt` are not tested for the date-time form",
            form,
        )

    def test_producers_must_not_emit_a_rejected_body(self) -> None:
        form = flat(next(block for block in self.blocks if block.startswith(FORM_START)))
        self.assertIn(
            "An identity provider MUST NOT emit a challenge body, and an agent MUST NOT emit a"
            " response body, that this rule rejects.",
            form,
        )


class DateTimeForm(unittest.TestCase):
    """The example timestamps §5.1.4 gives follow the date-time form it states."""

    def setUp(self) -> None:
        spec_section = section(SPEC.read_text(encoding="utf-8"), "#### 5.1.4 ", "#### 5.1.5 ")
        blocks = [flat(block) for block in re.split(r"\n\s*\n", spec_section)]
        forms = [block for block in blocks if block.startswith(FORM_START)]
        self.assertEqual(len(forms), 1, "§5.1.4 has no paragraph, or more than one, stating the date-time form")
        self.form = forms[0]

    def test_form_is_rfc_3339_date_time_with_upper_case_t_and_z(self) -> None:
        self.assertIn("the `date-time` production of RFC 3339, Section 5.6", self.form)
        self.assertIn("written with an upper-case `T` and `Z` and a second from `00` to `59`", self.form)
        self.assertIn("a day of the Gregorian calendar (RFC 3339, Section 5.7)", self.form)

    def test_examples_follow_the_stated_form(self) -> None:
        match = EXAMPLES.search(self.form)
        self.assertIsNotNone(match, "the date-time form paragraph gives no examples in and out of the form")
        inside = BACKTICKED.findall(match.group(1))
        outside = BACKTICKED.findall(match.group(2))
        self.assertGreaterEqual(len(inside), 2, inside)
        self.assertGreaterEqual(len(outside), 3, outside)
        self.assertEqual([value for value in inside if not in_date_time_form(value)], [])
        self.assertEqual([value for value in outside if in_date_time_form(value)], [])


class FormReading(unittest.TestCase):
    """in_date_time_form, the reading of the form the tests above use, on values §5.1.4 does not list."""

    def test_form_check_reads_each_part(self) -> None:
        for value in (
            "2024-02-29T00:00:00Z",
            "0000-02-29T00:00:00Z",
            "2026-12-31T23:59:59.999999999-23:59",
            "2026-05-27T23:58:00+00:00",
        ):
            self.assertTrue(in_date_time_form(value), value)
        for value in (
            "2023-02-29T00:00:00Z",
            "2026-04-31T00:00:00Z",
            "2026-00-10T00:00:00Z",
            "2026-13-10T00:00:00Z",
            "2026-05-27T24:00:00Z",
            "2026-05-27T23:60:00Z",
            "2026-05-27T23:58:00+24:00",
            "2026-05-27T23:58:00+02:60",
            "2026-05-27T23:58:00.Z",
            "2026-05-27T23:58:00,5Z",
            "2026-05-27T23:58Z",
            "2026-05-27T23:58:00+0200",
            "2026-05-27",
            "２026-05-27T23:58:00Z",
            "2026-05-27T23:58:00Z\n",
            "",
        ):
            self.assertFalse(in_date_time_form(value), repr(value))


class PinnedBodies(unittest.TestCase):
    """The §5.1.1 and §5.1.2 example bodies, the suite's valid transcript, pass the body form rule."""

    def setUp(self) -> None:
        spec = SPEC.read_text(encoding="utf-8")
        self.challenge = example_body(spec, "#### 5.1.1 ", "#### 5.1.2 ")
        self.response = example_body(spec, "#### 5.1.2 ", "#### 5.1.3 ")
        self.schemas = {
            "challenge": json.loads(CHALLENGE_SCHEMA.read_text(encoding="utf-8")),
            "response": json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8")),
        }

    def test_each_body_is_an_object_whose_members_are_strings(self) -> None:
        for name, body in (("challenge", self.challenge), ("response", self.response)):
            self.assertIsInstance(body, dict, name)
            self.assertEqual(
                sorted(member for member, value in body.items() if not isinstance(value, str)), [], name
            )

    def test_challenge_timestamps_are_in_the_date_time_form(self) -> None:
        for member in ("issuedAt", "expiresAt"):
            self.assertTrue(in_date_time_form(self.challenge[member]), (member, self.challenge[member]))

    def test_schemas_require_each_member_of_the_example_as_a_string(self) -> None:
        # The schemas carry the form §5.1.1 and §5.1.2 give each body: an object whose members are
        # exactly the example's, each required and each a string.
        for name, body in (("challenge", self.challenge), ("response", self.response)):
            schema = self.schemas[name]
            self.assertEqual(schema.get("type"), "object", name)
            self.assertIs(schema.get("additionalProperties"), False, name)
            self.assertEqual(sorted(schema["required"]), sorted(body), name)
            self.assertEqual(sorted(schema["properties"]), sorted(body), name)
            self.assertEqual(
                [member for member, value in schema["properties"].items() if not string_typed(schema, value)],
                [],
                name,
            )


if __name__ == "__main__":
    unittest.main()
