#!/usr/bin/env python3
"""Regression tests for the agent ID form of AIP-SPEC.md §3.1.

§3.1 derives the agent ID as "aim_" followed by the base64url encoding of the
first 12 bytes of the Ed25519 public key. These tests derive the ID of the §3.1
example from its public key, check that every other example ID has that shape,
and check the README Quick Start, which shows what the CLI prints, against the
same rule.

Run from the repository root:
    python3 -m unittest discover -s tests
python3 standard library only.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "AIP-SPEC.md"
README = ROOT / "README.md"

# An agent ID in an example: "aim_" not preceded by a DID method prefix such as
# "did:aip:", which marks the deprecated alias form of §3.2.
EXAMPLE_ID = re.compile(r"(?<![\w:])aim_[A-Za-z0-9_-]+")
AGENT_ID_SHAPE = re.compile(r"aim_[A-Za-z0-9_-]{16}")
FENCED = re.compile(r"^```[^\n]*\n(.*?)^```", re.DOTALL | re.MULTILINE)


def agent_id(public_key: bytes) -> str:
    """The §3.1 agent ID: "aim_" + base64url(first 12 bytes of the public key)."""
    return "aim_" + base64.urlsafe_b64encode(public_key[:12]).decode("ascii")


def b64decode(text: str) -> bytes:
    return base64.b64decode(text + "=" * (-len(text) % 4), validate=True)


def section(spec: str, heading: str, next_heading: str) -> str:
    start = spec.index(heading)
    return spec[start : spec.index(next_heading, start)]


def labelled(block: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}\s+(\S+)$", block, re.MULTILINE)
    if match is None:
        raise AssertionError(f"no line starting {label!r} in the block")
    return match.group(1)


class SpecExampleVector(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = SPEC.read_text(encoding="utf-8")
        self.section = section(self.spec, "### 3.1 Cryptographic Identity", "### 3.2 ")
        blocks = [b for b in FENCED.findall(self.section) if "Public key (base64):" in b]
        self.assertEqual(len(blocks), 1, "§3.1 has no example block with a 'Public key (base64):' line")
        self.example = blocks[0]

    def test_rule_names_base64url_of_twelve_bytes(self) -> None:
        self.assertIn('Agent ID:    "aim_" + base64url(first 12 bytes of public_key), 16 characters', self.section)

    def test_example_agent_id_derives_from_its_public_key(self) -> None:
        public_key = b64decode(labelled(self.example, "Public key (base64):"))
        self.assertEqual(len(public_key), 32)
        prefix = labelled(self.example, "First 12 bytes, base64url:")
        self.assertEqual(prefix, base64.urlsafe_b64encode(public_key[:12]).decode("ascii"))
        self.assertEqual(labelled(self.example, "Agent ID:"), agent_id(public_key))

    def test_example_public_key_is_the_fixture_key(self) -> None:
        response = section(self.spec, "#### 5.1.2 Response body", "#### 5.1.3")
        body = json.loads(FENCED.search(response).group(1))
        self.assertEqual(labelled(self.example, "Public key (base64):"), body["publicKey"])

    def test_earlier_rule_value_is_computed_from_the_same_key(self) -> None:
        public_key = b64decode(labelled(self.example, "Public key (base64):"))
        match = re.search(r"the earlier rule gives `(aim_[0-9a-f]{8})`", self.section)
        self.assertIsNotNone(match, "§3.1 does not give the earlier rule's value for the example key")
        self.assertEqual(match.group(1), "aim_" + hashlib.sha256(public_key).hexdigest()[:8])


class SpecExampleIds(unittest.TestCase):
    def test_every_example_agent_id_has_the_section_3_1_shape(self) -> None:
        spec = SPEC.read_text(encoding="utf-8")
        found = [i for block in FENCED.findall(spec) for i in EXAMPLE_ID.findall(block)]
        self.assertTrue(found, "no example agent ID found in AIP-SPEC.md")
        wrong = sorted({i for i in found if not AGENT_ID_SHAPE.fullmatch(i)})
        self.assertEqual(wrong, [], "example agent IDs without the §3.1 shape")


class ReadmeQuickStart(unittest.TestCase):
    def test_printed_agent_id_follows_section_3_1(self) -> None:
        readme = README.read_text(encoding="utf-8")
        printed_id = re.search(r"Agent ID:\s+(aim_\S+)", readme)
        printed_key = re.search(r"Public Key:\s+([A-Za-z0-9+/]{16,})", readme)
        self.assertIsNotNone(printed_id, "README.md shows no Agent ID line")
        self.assertIsNotNone(printed_key, "README.md shows no Public Key line")
        # 16 base64 characters are exactly the first 12 bytes of the key.
        first_bytes = b64decode(printed_key.group(1)[:16])
        self.assertEqual(printed_id.group(1), agent_id(first_bytes))


if __name__ == "__main__":
    unittest.main()
