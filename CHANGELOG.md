# Changelog

All notable changes to the OpenA2A Agent Identity Protocol specification are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

## [1.2.0-draft] - unreleased

Draft pairing: `draft-fane-opena2a-aip-04` pairs with 1.2.0-draft and is built once this change
set closes. Until then `draft-fane-opena2a-aip-03` is the latest render and carries the 1.1.0-draft
text.

### Changed

- §6.2 becomes the behavioral tier table: the field is `behaviorTier` (was `trustLevel`), the
  column is `Tier` (was `Level`), and the five names (Blocked, Warning, Limited, Standard,
  Elevated) are tier names. `trustLevel` in AIP and in any credential defined by another OpenA2A
  specification means the ATP-SPEC §4.1 trust level. AIP no longer restates the ATP-SPEC §4.1
  table. The §6.4 sample carries `behaviorTier`.

## [1.1.0-draft] - 2026-09-08

Draft pairing: `draft-fane-opena2a-aip-03` pairs with 1.1.0-draft. Minor
bump: what a provider MUST issue changes (provider-scoped identifiers are a
`did:web` profile; the pre-1.1 form is a deprecated alias); the §5.1 wire
format does not. `-02` (2026-08-06) carried the §5.1 wire format of
1.0.1-draft but not the §3.2 DID method scoping ratified in that same version;
`-03` carries the scoping in its 1.1 form. `-00` (2026-07-06) and `-01`
(2026-07-22, date-only) carried the pre-scoping text.

### Added

- `draft-fane-opena2a-aip-03.{xml,txt}`: Internet-Draft revision carrying the
  §3.2 DID method scoping. `-02` said OpenA2A AIP uses the unified
  `did:opena2a` method and showed `did:opena2a` strings in the DID Document,
  discovery, and Verifiable Credential examples; `-03` states that AIP
  defines no DID method, that an identity provider issues and resolves
  provider-scoped identifiers as a `did:web` profile
  (`did:web:<provider-host>[:<path>]:agents:<id>`, provider self-identifier
  `did:web:<provider-host>`), that `did:opena2a` is the ecosystem-scoped
  method an identity provider does not serve, and that verification treats
  identifiers as opaque. The challenge-response transcript is unchanged (it
  is the pinned fixture) and is annotated as ecosystem-scoped. The IANA
  section requests no DID method action: method names are a W3C registry,
  `did:opena2a` is registered there, and the name `aip` is held by a
  registration that is not OpenA2A's. Informative references to `did-method-opena2a`,
  the W3C DID Extensions registry and the did:web method specification and
  a "Changes from -02" section are added. Built with xml2rfc; idnits was not
  available at build time and no idnits pass is claimed.
- §3.2 `did:web` profile for provider-scoped identifiers, with the reference
  form `did:web:aim.opena2a.org:agents:<uuid>`, a deprecated-alias paragraph
  (the pre-1.1 form is served for a migration window and linked by
  `alsoKnownAs`), a reference implementation status paragraph (the resolver
  answers the pre-1.1 alias form only, the `did.json` route is not
  implemented, source read 2026-09-08) and a method name registration
  paragraph disclosing the third-party `aip` entry in the W3C DID Extensions
  registry (registered 2026-05-31) and stating that AIP registers nothing.
- §5.1.1 note stating that the fixture identifiers are ecosystem-scoped
  `did:opena2a` strings, that provider-scoped `did:web` identifiers are
  carried the same way, and that the fixture bytes do not change with §3.2.
- §6.2: one informative sentence that AIP's trust level is a behavioral tier
  distinct from the ATP provenance scale (ATP-SPEC §4.1). The field and the
  level names are unchanged in this revision.
- §14: references to the `did:opena2a` W3C DID Extensions registry entry and
  to the W3C CCG did:web method specification.
- `draft-fane-opena2a-aip-02.{xml,txt}`: Internet-Draft revision carrying the
  §5.1 wire format ratified in 1.0.1-draft. `-01` was a date-only resubmission
  of `-00`, so the datatracker copy described challenge-response in one prose
  paragraph while this repository had five normative subsections; the reject
  categories (`SIGNATURE_INVALID`, `UNTRUSTED_KEY`, `CHALLENGE_EXPIRED`,
  `NONCE_REPLAY`) appeared zero times in the draft and the two documents
  disagreed. `-02` adds the challenge body, the response body with the
  unsigned-fields warning, the five-field canonical signing form with UTC
  normalization, the ordered verification rules with their reject categories,
  and the conformance-fixture pointer, plus normative references to RFC 3339,
  RFC 4648, RFC 8785 and RFC 8792. No other technical change. The example
  transcript is the suite's `challenge-response-valid` fixture and its Ed25519
  signature was verified against the documented canonical form before commit.

- `schemas/challenge-body-v1.schema.json` and
  `schemas/response-body-v1.schema.json`: machine-readable JSON Schemas
  (draft 2020-12) for the §5.1.1/§5.1.2 wire bodies, fixture-ground-truth
  derived (all four `aip-conformance` transcripts validate).
- `scripts/validate_examples.py` + `schemas/examples-map.json` + CI workflow:
  schemas metaschema-checked and both §5.1 examples validated on every push/PR.

### Changed

- §3.2 DID Document example and §10.1 discovery document carry the `did:web`
  form (`providerDid` is the provider's `did:web` self-identifier); a
  paragraph after the discovery document says the `didResolve` endpoint
  answers for issued identifiers including deprecated aliases and that the
  same document is published at the `did:web` path.
- §6.4 Verifiable Credential example is now an AIP-layer sample: issuer
  `did:web:aim.opena2a.org`, subject
  `did:web:aim.opena2a.org:agents:<uuid>` (the §3.2 example), proof key
  `did:web:aim.opena2a.org#key-1`. 1.0.1-draft had set the issuer to the
  ecosystem authority `did:opena2a:authority:opena2a.org` with the subject
  `did:opena2a:agent:aim_7f3a9c2e`, a provider identifier inside the ecosystem
  namespace, which is the conflation §3.2 rules out. The prose now says that an
  ecosystem-scoped trust assertion is the ATP trust proof (§6.5).
- §5.1.4 rule 2 names the document that resolves a provider-scoped `did:web`
  identifier (the document the issuing provider serves).
- §13 rewritten: DID method registration is a W3C matter, not an IANA action;
  AIP defines no DID method; the resource-type prefix list now defers to
  `did-method-opena2a` §3.2.
- Appendix A.1 §3 row records that resolution serves the deprecated alias
  form only and that the `did:web` route is not implemented.
- GAP-ANALYSIS: the DID resolution row is Partial (alias form only, `did:web`
  route not implemented); the agent identifier row says provider-scoped
  `did:web` profile at the AIP layer with `did:opena2a` at the ATP/ATX layer.
- README prior-art paragraph: the Singla draft introduces a `did:aip` method;
  OpenA2A AIP defines no DID method and the reference implementation's
  pre-1.1 identifiers are deprecated aliases. README resolve example says the
  printed identifier is the alias form the resolver answers today.
- Not changed in this revision: the trust level field and names (§6.2; the
  rename to a behavioral tier field is the next wire revision), the
  `transparencyLogIndex` field (lives in atx-spec), identifier length (§3.1),
  relying-party-minted challenges and the audience field (§5.1.3), and the
  post-quantum verification method in the DID Document example.
- §5.1.1/§5.1.2 example blocks now carry the suite's `challenge-response-valid`
  fixture bytes (a transcript that actually verifies) instead of placeholder
  annotations; the annotations moved into the surrounding prose.

### Fixed

- README Quick Start: discovery is listed before DID resolution; the resolve example carries the placeholder `did:aip:aim_<agent-uuid>` and states that resolution answers only for an agent registered with the provider. The previous sample `did:aip:aim_7f3a9c2e` is not a UUID and the reference deployment answered it with 400 `invalid_agent_id`.

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
