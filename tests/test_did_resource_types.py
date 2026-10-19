#!/usr/bin/env python3
"""Regression tests for the did:opena2a type prefixes that AIP-SPEC.md §3.2 lists.

Section 3.2 of did-method-opena2a is the resource-type registry of the OpenA2A
specification family, and the specifications that consume it mirror its set of
registered types. These tests check that each list of registered type prefixes
in AIP-SPEC.md names the types of that registry in its order, that the §3.2
paragraph on did:opena2a cites that section, and that it names `a2a_agent`, a
deprecated alias there, as an alias of `agent` and not as a registered type.

Run from the repository root:
    python3 -m unittest discover -s tests
python3 standard library only.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "AIP-SPEC.md"

# The "Resource type" column of registries/resource-types.json, row by row, in
# opena2a-standards/did-method-opena2a at 5c55fca3b639 (2026-10-16). A type
# registered there after that commit is added here and to §3.2 in one change.
REGISTERED = ("registry", "authority", "publisher", "agent", "mcp_server", "ai_tool", "llm", "skill")
# Each deprecated alias that did-method-opena2a Section 3.2 names, with the type it stands for.
DEPRECATED_ALIASES = {"a2a_agent": "agent"}

PARAGRAPH_LABEL = "**Ecosystem-scoped: `did:opena2a`"
# A list of type prefixes: code spans joined by ", ", " and " or ", and". A name may hold a
# digit so that a legacy name such as `a2a_agent` is read as an item of the list.
PREFIX_LIST = re.compile(r"registered type prefixes (?:are )?((?:`[a-z][a-z0-9_]*`(?:,? and |, ))*`[a-z][a-z0-9_]*`)")
CODE_SPAN = re.compile(r"`([^`]+)`")
CITATION = "Section 3.2 of `did-method-opena2a`"


def section(spec: str, heading: str, next_heading: str) -> str:
    start = spec.index(heading)
    return spec[start : spec.index(next_heading, start)]


def did_opena2a_paragraph(spec: str) -> str:
    """Return the §3.2 paragraph on the did:opena2a method."""
    text = section(spec, "### 3.2 Decentralized Identifier (DID)", "### 3.3 ")
    found = [p for p in text.split("\n\n") if p.startswith(PARAGRAPH_LABEL)]
    if len(found) != 1:
        raise AssertionError(f"expected one §3.2 paragraph that starts {PARAGRAPH_LABEL!r}, found {len(found)}")
    return found[0]


def prefix_lists(text: str) -> list[list[str]]:
    """Return each list of registered type prefixes in text, as the names in its code spans."""
    return [CODE_SPAN.findall(match.group(1)) for match in PREFIX_LIST.finditer(text)]


class PrefixListParsing(unittest.TestCase):
    def test_a_list_is_read_whichever_way_its_last_item_is_joined(self):
        for text in (
            "with registered type prefixes `a`, `b`, `c` and more",
            "Its registered type prefixes are `a`, `b` and `c`.",
            "Its registered type prefixes are `a`, `b`, and `c`.",
        ):
            with self.subTest(text=text):
                self.assertEqual(prefix_lists(text), [["a", "b", "c"]])

    def test_a_name_with_a_digit_is_read_as_an_item(self):
        text = "with registered type prefixes `agent`, `a2a_agent`, `skill` and more"
        self.assertEqual(prefix_lists(text), [["agent", "a2a_agent", "skill"]])

    def test_a_code_span_after_the_list_is_not_read_as_a_prefix(self):
        text = "Its registered type prefixes are `a` and `b`, as Section 3.2 of `did-method-opena2a` registers them."
        self.assertEqual(prefix_lists(text), [["a", "b"]])


class DidOpena2aTypePrefixes(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = SPEC.read_text(encoding="utf-8")
        self.paragraph = did_opena2a_paragraph(self.spec)

    def test_paragraph_lists_the_registered_type_prefixes(self):
        self.assertEqual(
            len(prefix_lists(self.paragraph)), 1,
            "the §3.2 did:opena2a paragraph has no list of registered type prefixes, or more than one",
        )

    def test_each_list_names_the_registered_types_in_registry_order(self):
        lists = prefix_lists(self.spec)
        self.assertTrue(lists, "AIP-SPEC.md has no list of registered type prefixes")
        for listed in lists:
            with self.subTest(listed=listed):
                self.assertEqual(listed, list(REGISTERED))

    def test_no_deprecated_alias_is_listed_as_a_registered_type(self):
        for listed in prefix_lists(self.spec):
            for alias in DEPRECATED_ALIASES:
                with self.subTest(alias=alias, listed=listed):
                    self.assertNotIn(alias, listed)

    def test_each_deprecated_alias_is_named_with_the_type_it_stands_for(self):
        for alias, target in DEPRECATED_ALIASES.items():
            with self.subTest(alias=alias):
                self.assertRegex(self.paragraph, rf"`{alias}`[^.]*\bdeprecated alias of `{target}`")

    def test_list_cites_the_registry_section_of_did_method_opena2a(self):
        list_end = PREFIX_LIST.search(self.paragraph)
        self.assertIsNotNone(list_end, "the §3.2 did:opena2a paragraph has no list of registered type prefixes")
        self.assertIn(CITATION, self.paragraph[list_end.end() :], f"no {CITATION!r} after the list")


if __name__ == "__main__":
    unittest.main()
