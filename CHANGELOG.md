# Changelog

All notable changes to the OpenA2A Agent Identity Protocol specification are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Added

- `schemas/challenge-body-v1.schema.json` and
  `schemas/response-body-v1.schema.json`: machine-readable JSON Schemas
  (draft 2020-12) for the §5.1.1/§5.1.2 wire bodies, fixture-ground-truth
  derived (all four `aip-conformance` transcripts validate).
- `scripts/validate_examples.py` + `schemas/examples-map.json` + CI workflow:
  schemas metaschema-checked and both §5.1 examples validated on every push/PR.

### Changed

- §5.1.1/§5.1.2 example blocks now carry the suite's `challenge-response-valid`
  fixture bytes (a transcript that actually verifies) instead of placeholder
  annotations; the annotations moved into the surrounding prose.

## [1.0.1-draft] - 2026-07-03

### Added

- §5.1 ratified as normative wire format (previously pinned only by the
  `aip-conformance` suite): challenge body (§5.1.1), response body (§5.1.2),
  the five-field pipe-delimited canonical signing form with UTC timestamp
  normalization (§5.1.3), ordered verification rules with reject categories
  `SIGNATURE_INVALID` / `UNTRUSTED_KEY` / `CHALLENGE_EXPIRED` / `NONCE_REPLAY`
  (§5.1.4), and the conformance-fixture link (§5.1.5). Explicitly documents
  that `publicKey`, `keyId`, `signedAt`, and `algorithm` are unauthenticated.
- §6.1 per-factor implementation status: compliance, drift detection, and user
  feedback marked Proposed/stubbed in the reference implementation; six of
  nine factors measured.
- §6.4 status line: Verifiable Credential expression is Proposed and not yet
  implemented; the shipped signed trust expression is the ATP trust proof.
- This changelog.

### Changed

- §3.2 DID method scoping ratified: `did:aip:<namespace>_<id>` is the
  provider-scoped AIP-layer method (what the reference implementation issues
  and resolves); `did:opena2a:<type>:<id>` is the ecosystem-scoped method
  anchored at the OpenA2A Registry and used at the ATP/ATX layer. Earlier
  drafts said AIP itself uses `did:opena2a`, which never matched the reference
  implementation and conflated provider identity namespaces with the
  ecosystem authority namespace. DID Document example, §10.1 `providerDid`,
  and the references section updated to match; §6.4 example issuer corrected
  to the real ecosystem authority.
- GAP-ANALYSIS rows re-verified against the current tree: did:aip resolution
  and DID Document generation are Complete; trust scoring updated to the
  9-factor set (6 measured, 3 stubs).

## [1.0.0-draft+errata] - 2026-03-22 → 2026-07-03

The v1.0.0-draft line accumulated errata and clarifications after first
publication (2026-03-22):

- §6.1 anti-gaming ceiling on no-data factor redistribution: a factor with no
  data can never contribute more than a neutral measurement would. (#9)
- GAP-ANALYSIS: IETF prior-art and naming section; README branded as
  "OpenA2A AIP" with the naming-collision note. (#6, #8)
- Optional `declaredPurpose` documented on agent identity, aligned with
  ATX 1.1 §1.5. (#7)
- Appendix A.1 corrections: hybrid PQC signing row (end-to-end shipped
  status), Python conformance verifier noted in the local-verify row.
  (#3, #4, #5)
- DID method unified to `did:opena2a` and 9-factor trust reference
  (2026-05-23) — the DID portion of this change is superseded by the 1.0.1
  scoping above.
- Initial specification: identity, capabilities, verification, trust scoring,
  governance, lifecycle, audit, discovery, integration patterns, security
  considerations.
