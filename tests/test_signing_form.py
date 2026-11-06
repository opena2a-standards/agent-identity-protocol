#!/usr/bin/env python3
"""Regression tests for the timestamp normalization in AIP-SPEC.md §5.1.3.

Before §5.1.3 joins the five fields into the signed bytes, it normalizes
`issuedAt` and `expiresAt` to UTC RFC 3339, `Z`-suffixed, at second precision.
A timestamp in the §5.1.4 date-time form can carry a fraction of a second, and
dropping that fraction and rounding it give different signed bytes, so the
section states that the fraction is dropped. These tests read that statement
from the section, check each example it gives against the rule and against the
§5.1.4 date-time form, and check that the normalization leaves the timestamps
of the §5.1.1 example body as they are written.

Run from the repository root:
    python3 -m unittest discover -s tests
python3 standard library only.
"""
from __future__ import annotations

import re
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# One reading of the §5.1.4 date-time form for every test that needs it.
from test_body_form import FORM, example_body, flat, in_date_time_form, section  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "AIP-SPEC.md"

RULE = "When `issuedAt` and `expiresAt` are normalized, a fraction of a second is dropped, not rounded"
# "`a` is normalized to `b`, not `c`, and `d` to `e`, not `f`."
EXAMPLE = re.compile(r"`([^`]+)`(?: is normalized)? to `([^`]+)`, not `([^`]+)`")
FRACTION = re.compile(r"\.([0-9]+)")


def whole_second(value: str) -> tuple[datetime, str]:
    """The UTC instant of the whole second a §5.1.4 date-time value writes, and its fraction digits.

    The offset is a whole number of minutes, so converting to UTC leaves the
    fraction as written.
    """
    match = FORM.fullmatch(value)
    if match is None or not in_date_time_form(value):
        raise ValueError(f"not in the §5.1.4 date-time form: {value!r}")
    field = {name: int(text) for name, text in match.groupdict(default="0").items()}
    offset = timedelta(hours=field["offset_hour"], minutes=field["offset_minute"])
    if value.endswith("Z"):
        offset = timedelta(0)
    elif value[-6] == "-":
        offset = -offset
    written = datetime(
        field["year"], field["month"], field["day"], field["hour"], field["minute"], field["second"],
        tzinfo=timezone(offset),
    )
    fraction = FRACTION.search(value)
    return written.astimezone(timezone.utc), fraction.group(1) if fraction else ""


def utc_text(instant: datetime) -> str:
    """instant as UTC RFC 3339, `Z`-suffixed, at second precision, with a four-digit year."""
    return (
        f"{instant.year:04d}-{instant.month:02d}-{instant.day:02d}"
        f"T{instant.hour:02d}:{instant.minute:02d}:{instant.second:02d}Z"
    )


def normalized(value: str) -> str:
    """value as §5.1.3 normalizes it: in UTC, with any fraction of a second dropped."""
    instant, _ = whole_second(value)
    return utc_text(instant)


def rounded(value: str) -> str:
    """value in UTC with its fraction rounded to the nearest second, a half up.

    This is the reading §5.1.3 rules out.
    """
    instant, fraction = whole_second(value)
    if fraction and fraction[0] >= "5":
        instant += timedelta(seconds=1)
    return utc_text(instant)


class NormalizationRule(unittest.TestCase):
    """§5.1.3 says that a fraction of a second is dropped, not rounded, and gives examples."""

    def setUp(self) -> None:
        self.text = flat(section(SPEC.read_text(encoding="utf-8"), "#### 5.1.3 ", "#### 5.1.4 "))

    def rule_sentence(self) -> str:
        self.assertTrue(RULE in self.text, "§5.1.3 does not say whether a fraction of a second is dropped or rounded")
        start = self.text.index(RULE)
        # The sentence ends at the first full stop after a closing backtick; the full stop
        # inside a timestamp sits between backticks.
        return self.text[start : self.text.index("`. ", start) + 2]

    def test_section_says_a_fraction_is_dropped_not_rounded(self) -> None:
        self.assertIn(
            "a timestamp becomes the last whole second at or before the instant it writes",
            self.rule_sentence(),
        )

    def test_examples_follow_the_rule(self) -> None:
        examples = EXAMPLE.findall(self.rule_sentence())
        self.assertGreaterEqual(len(examples), 2, examples)
        for written, result, excluded in examples:
            self.assertTrue(in_date_time_form(written), written)
            self.assertTrue(FRACTION.search(written), f"{written} has no fraction of a second")
            self.assertEqual(normalized(written), result, written)
            # The value the example rules out is the rounded one, so the example tells the
            # two readings apart.
            self.assertEqual(rounded(written), excluded, written)
            self.assertNotEqual(result, excluded, written)
        self.assertTrue(
            [written for written, _, _ in examples if not written.endswith("Z")],
            "no example writes a numeric offset",
        )


class NormalizationReading(unittest.TestCase):
    """normalized and rounded, the readings the tests above use, on values §5.1.3 does not list."""

    def test_normalized_drops_the_fraction_after_converting_to_utc(self) -> None:
        for value, expected in (
            ("2026-05-27T23:58:00Z", "2026-05-27T23:58:00Z"),
            ("2026-05-27T23:58:00+00:00", "2026-05-27T23:58:00Z"),
            ("2026-05-27T23:58:00.000Z", "2026-05-27T23:58:00Z"),
            ("2026-05-27T23:58:00.4999Z", "2026-05-27T23:58:00Z"),
            ("2026-12-31T23:59:59.5Z", "2026-12-31T23:59:59Z"),
            ("2024-02-29T00:00:00.5+00:01", "2024-02-28T23:59:00Z"),
            ("2026-05-27T23:58:00.999999999-23:59", "2026-05-28T23:57:00Z"),
        ):
            self.assertEqual(normalized(value), expected, value)

    def test_rounded_carries_a_half_or_more_into_the_next_second(self) -> None:
        for value, expected in (
            ("2026-05-27T23:58:00.4999Z", "2026-05-27T23:58:00Z"),
            ("2026-05-27T23:58:00.5Z", "2026-05-27T23:58:01Z"),
            ("2026-12-31T23:59:59.5Z", "2027-01-01T00:00:00Z"),
            ("2026-05-27T23:58:00.999999999-23:59", "2026-05-28T23:57:01Z"),
        ):
            self.assertEqual(rounded(value), expected, value)

    def test_value_outside_the_date_time_form_is_refused(self) -> None:
        for value in ("2026-05-27T23:58:00", "2026-05-27t23:58:00.5z", "2026-05-27T23:58:00,5Z"):
            with self.assertRaises(ValueError, msg=value):
                normalized(value)


class PinnedTimestamps(unittest.TestCase):
    """The §5.1.1 example body, the suite's valid transcript, is unchanged by the normalization."""

    def test_challenge_timestamps_are_already_normalized(self) -> None:
        challenge = example_body(SPEC.read_text(encoding="utf-8"), "#### 5.1.1 ", "#### 5.1.2 ")
        for member in ("issuedAt", "expiresAt"):
            self.assertEqual(normalized(challenge[member]), challenge[member], member)


if __name__ == "__main__":
    unittest.main()
