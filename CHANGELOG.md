# Changelog

All notable changes to the OpenA2A Agent Identity Protocol specification are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Fixed

- `scripts/check_draft_sync.py` matches each tracked term as a whole word, so a field renamed
  in the specification or in the draft (`behaviorTier` to `behaviorTierX`) is reported instead
  of passing as a substring.
- `scripts/check_first_use.py` reports a FILE argument that does not exist, or cannot be read,
  as one "first use FAIL" line and counts it, instead of ending in a traceback.
- `scripts/validate_examples.py`, `scripts/check_draft_sync.py` and
  `scripts/stage_draft_upload.py` put their own directory on the import path, so an isolated
  run (`python3 -I` or `-P`) finds the sibling check scripts as a plain run does.
- `.gitignore` ignores secret-shaped files (`secrets.json`, `secrets.*.json`, `*.secrets.json`,
  `credentials.json`, `secrets/`, `credentials/`).
- `draft-fane-opena2a-aip-04.xml` no longer sets `submissionType="IETF"` on its `rfc` element.
  The draft is an individual submission with no stream on the datatracker, so `npx
  @ietf-tools/idnits@3.1.0` on the xml reported the attribute as a `SUBMISSION_TYPE_UNEXPECTED`
  error. xml2rfc 3.34.0 renders the same txt without it, so `draft-fane-opena2a-aip-04.txt` is
  unchanged. `scripts/check_draft_sync.py` now fails when the paired draft's `rfc` element sets
  `submissionType` to `IETF`, `IAB` or `IRTF`.
- `draft-fane-opena2a-aip-04.xml` wraps each of its 71 BCP 14 keywords in `<bcp14>`. On the xml,
  `npx @ietf-tools/idnits@3.1.0` counts a reference to BCP 14 only through an external entity or
  a tagged keyword, so it reported a `MISSING_REQLEVEL_REF` error and 60 `MISSING_BCP14_TAGS`
  comments; it now reports neither. xml2rfc 3.34.0 renders the same txt with the tags, so
  `draft-fane-opena2a-aip-04.txt` is unchanged. `scripts/check_draft_sync.py` now fails when a
  BCP 14 keyword in the paired draft's xml sits outside `<bcp14>`, `<artwork>` or `<sourcecode>`.
  The one error idnits still reports on the xml, `INVALID_REFERENCES_NAME`, is kept: idnits reads
  only the name of each top-level `<references>`, and -04 nests Normative References and
  Informative References under one References section. The flat layout of -03 clears that error
  on the xml, but idnits then reports `MULTIPLE_REFERENCES_SECTION_TITLES` on the rendered txt, as
  it does on `draft-fane-opena2a-aip-03.txt`.
- `scripts/check_draft_sync.py` reads `submissionType` from the parsed `rfc` element and fails
  for `IETF`, `IAB` or `IRTF` in any case, the values for which idnits 3.1.0 reports
  `SUBMISSION_TYPE_UNEXPECTED` on a draft with no datatracker stream; `independent` and
  `editorial` pass. An `<rfc` tag inside a comment or a `>` inside an attribute value no longer
  misleads it, and input with many `<rfc` and no `>` no longer takes quadratic time.
- `scripts/check_draft_sync.py` also fails when `submissionType` is a non-empty value other than
  `IETF`, `IAB`, `IRTF`, `independent` or `editorial`, compared in lower case, such as
  `Independant`, for which idnits 3.1.0 reports `SUBMISSION_TYPE_INVALID`. Both `submissionType`
  checks read the value as idnits does: the attribute text as written, with the whitespace that
  JavaScript's `trim()` removes taken off each end before any character reference is decoded, and
  pass an empty value. `""`, `" independent"` and `"independent "` pass, and `" IETF"` fails as
  `IETF` does. A value that holds a character reference, such as `"&#32;independent"`,
  `"&#160;independent"` or `"&#10;"`, fails as `SUBMISSION_TYPE_INVALID`, as does `"IETF&#32;"`,
  which no longer fails as `SUBMISSION_TYPE_UNEXPECTED`. A leading U+0085, which `trim()` keeps,
  fails as invalid, and a leading U+FEFF, which `trim()` removes, passes.
- The BCP 14 failure line of `scripts/check_draft_sync.py` gives the number of untagged keywords
  and says how many of them, in `<t>` or `<li>` text outside the BCP 14 boilerplate paragraph, are
  an estimate of the `MISSING_BCP14_TAGS` count of idnits 3.1.0. On the -04 xml without its tags the
  line gives 71 and 60, and on -00 to -03 the second number is 39, 39, 47 and 49, the counts
  idnits reports. idnits selects the text it checks by a different rule, so on other xml the two
  can differ. It no longer says idnits reports each untagged keyword. The boilerplate test and
  that count read an element's text as idnits does: each text segment trimmed and the segments
  joined with no separator. So `<t>The key words "MUST" and "MAY" <xref target="BCP14"/> in this
  document ...</t>` is not the boilerplate paragraph and counts 2, and `<t>Before <xref
  target="RFC2119"/> MUST after</t>`, which reads "BeforeMUST after", counts 0, as idnits reports.
  The names in the script say counted rather than idnits (`COUNTED_TEXT`, `Untagged.counted`).
- `scripts/check_draft_sync.py` finds the BCP 14 boilerplate paragraph in linear time. It used
  idnits' pattern, which takes quadratic time on text with many "The key words" and no " in this
  document" (about 1.4 s for 81 KB); it now searches in two steps that give the same result.
- The BCP 14 walk of `scripts/check_draft_sync.py` keeps its own stack, so xml nested about 1000
  elements deep or more gives the same result as shallower xml instead of an uncaught
  `RecursionError`.
- README.md and the 1.2.0-draft pairing paragraph say `draft-fane-opena2a-aip-04` was submitted
  on 2026-10-06 and is the current datatracker revision, instead of not submitted yet, and the
  pairing paragraph states how the xml on the datatracker differs from the repository xml.
  README.md also says one editorial change has been made to the specification since
  `draft-fane-opena2a-aip-04`: §12.1 now reads "MUST NOT be transmitted" where Section 13.1 of
  the draft reads "MUST NEVER be transmitted". It also quotes the two statements of §6.1 on
  substituting per-factor scoring functions that Section 7.1 of the draft lacks, though the
  specification carried both when -04 was made, instead of saying -04 carries 1.2.0-draft whole.
  Once a pairing paragraph no longer says its draft is not submitted,
  `scripts/check_draft_sync.py` requires it to record the submission as "`draft-fane-opena2a-aip-NN` (submitted YYYY-MM-DD) is
  the current datatracker revision" and requires README.md to name that date.
- AIP-SPEC.md §12.1 says private keys MUST NOT be transmitted in plaintext, the form BCP 14
  defines, instead of "MUST NEVER". `draft-fane-opena2a-aip-04`, as submitted, still reads "MUST
  NEVER".
- `test_secret_shaped_files_are_ignored` skips outside a git checkout instead of failing with
  git's exit code 128.
- `tests/test_check_scripts.py` covers the cases above, and pins three properties of the BCP 14
  rule: elements nested in `<artwork>`, `<sourcecode>` or `<bcp14>` are exempt, xml that is not
  well formed is reported, and "NOT RECOMMENDED" is one keyword. It also pins that a recorded
  submission must say "is the current datatracker revision", that a `submissionType` written with
  a character reference or a leading U+0085 or U+FEFF is read as idnits reads it, and that an
  element's text segments are trimmed and joined, so a paragraph whose "in this document" or
  keywords follow a child element such as `<xref/>` is not the boilerplate paragraph. Run
  `python3 -m unittest discover -s tests`.

## [1.2.0-draft] - 2026-10-06

Draft pairing: `draft-fane-opena2a-aip-04` pairs with 1.2.0-draft. It was rendered on 2026-10-06
with xml2rfc 3.34.0 and carries every change listed under this heading; `npx
@ietf-tools/idnits@3.1.0` on the txt reports 0 errors and 6 warnings.
`draft-fane-opena2a-aip-04` (submitted 2026-10-06) is the current datatracker revision. The txt
there is byte-identical to `draft-fane-opena2a-aip-04.txt`. The xml there predates two changes
listed under Unreleased, so it differs from `draft-fane-opena2a-aip-04.xml`: it sets
`submissionType="IETF"` and tags none of the 71 BCP 14 keywords that the repository xml wraps in
`<bcp14>`. `scripts/stage_draft_upload.py` prints the file to upload and its SHA-256 and submits
nothing. `-03` (submitted 2026-10-02) is the prior revision there and carries the 1.1.0-draft
text.

### Added

- `draft-fane-opena2a-aip-04.{xml,txt}`: Internet-Draft revision carrying this version: the §6.2
  tier rename and the §6.4 sample, the §6.1 unscored state and algorithm version together with
  the §6.1 anti-gaming ceiling they build on (in this specification since 1.0.0-draft, absent
  from `-00` through `-03`), the §4.1 capability grammar and the §4.2 registry with `secrets`,
  the §5.1 step 3 clock-skew citation, and the first use of the reference implementation's name
  as "OpenA2A AIM (Agent Identity Management)". The two reference lists are grouped under one
  References section, which clears the `MULTIPLE_REFERENCES_SECTION_TITLES` error idnits
  reported on `-03`. A "Changes from -03" appendix lists the changes.
- `scripts/check_draft_sync.py`, run in CI by `scripts/validate_examples.py`: the draft that the
  changelog pairs with the specification's version must carry the specification's wire terms
  (the §5.1 reject categories, the tier and unscored-state fields, the clock-skew citation, the
  §4.1 grammar, every §4.2 namespace) and the expanded first use of the AIM name. An unreleased
  version may name a draft that is not built yet; a dated one may not.
- README.md gains an Internet-Draft paragraph under Specification: the datatracker copy is
  behind this repository, `draft-fane-opena2a-aip-03` (submitted 2026-10-02) is the current
  revision there and carries 1.1.0-draft, and `draft-fane-opena2a-aip-04` carries 1.2.0-draft and
  is not submitted yet. `scripts/check_draft_sync.py` fails when that paragraph does not name the
  paired draft and version, the current revision the pairing paragraph above records, and the
  submission state it states.
- `scripts/stage_draft_upload.py`: runs that check on the paired draft, rebuilds it when xml2rfc
  is available, and prints the txt file to upload with its SHA-256. It makes no network call and
  submits nothing.

- §6.1 gains the unscored state and the algorithm version: `includedWeight` (the weight
  with data, before redistribution) below 0.50 makes the agent unscored, with `score` null,
  `scoreStatus` `"unscored"` and `unscoredReason` present, and no §6.4 credential issued from
  that state; every published score carries `algorithmVersion` (1 = the rule without the
  unscored state, 2 = this text); the nine factor identifiers on the wire are named. The threshold and the field names have one home, this section.

### Changed

- §6.2 becomes the behavioral tier table: the field is `behaviorTier` (was `trustLevel`), the
  column is `Tier` (was `Level`), and the five names (Blocked, Warning, Limited, Standard,
  Elevated) are tier names. `trustLevel` in AIP and in any credential defined by another OpenA2A
  specification means the ATP-SPEC §4.1 trust level. AIP no longer restates the ATP-SPEC §4.1
  table. The §6.4 sample carries `behaviorTier`.
- One home per shared definition, marked for the family drift gate: Section 4.1 is the
  home of the capability grammar (reserved or domain-prefixed namespace, colon, action; no
  wildcard) with a machine-readable block; Section 4.2 is the shared capability-namespace
  registry, now including `secrets` (Critical), and `registries/capability-namespaces.json`
  is generated from its table by `scripts/gen_registries.py`, checked in CI.
- Section 5.1 step 3 (freshness) cites the family clock-skew bound in ATP Section 10.2.
- Editorial: the first use of the reference implementation's name reads "OpenA2A AIM (Agent
  Identity Management)". `scripts/check_first_use.py`, run in CI by
  `scripts/validate_examples.py`, fails when the first line of the specification containing AIM
  does not carry that phrase. The same check now covers README.md, CONTRIBUTING.md,
  CHANGELOG.md and GAP-ANALYSIS.md, whose first uses are expanded the same way.
- The §6.1 unscored example identifies its agent as
  `did:web:idp.example:agents:agent_unscored_example_001` (was a `did:opena2a` identifier): a
  score an identity provider publishes is about a provider-scoped identifier (§3.2), and an AIP
  identity provider does not serve `did:opena2a`. Identifiers are opaque to verification, so no
  rule changes.
- §13: the capability namespace registry line cites the §4.2 table instead of listing ten of its
  eleven namespaces.

### Fixed

- `scripts/check_draft_sync.py` reads the "Draft pairing" paragraph wherever it sits under the
  version's heading, the same way it finds the paired draft, instead of the text before the
  first `###` heading. It also fails when the README Internet-Draft paragraph says the
  datatracker copy is behind this repository once the pairing no longer says "not submitted",
  or leaves that out while the pairing still says it. When the pairing paragraph names no
  current datatracker revision, the failure message and the script docstring give the one
  sentence shape the check accepts. `scripts/test_checks.py` covers these cases.
- README.md lists the ATP link once, under Interoperability; the copy under Related Standards
  is removed.

## [1.1.0-draft] - 2026-09-08

Draft pairing: `draft-fane-opena2a-aip-03` pairs with 1.1.0-draft and was submitted to the
datatracker on 2026-10-02 as the current revision, with its document date set to 2026-09-30 and
its text otherwise the 2026-09-08 render. Minor bump: what a provider MUST issue changes
(provider-scoped identifiers are a `did:web` profile; the pre-1.1 form is a deprecated alias);
the §5.1 wire format does not. `-02` (2026-08-06) carried the §5.1 wire format of 1.0.1-draft but
not the §3.2 DID method scoping ratified in that same version; `-03` carries the scoping in its
1.1 form. `-00` (2026-07-06) and `-01` (2026-07-22, date-only) carried the pre-scoping text.

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
  a "Changes from -02" section are added. Rebuilt with xml2rfc on 2026-09-30
  with the document date set to that day; `npx @ietf-tools/idnits@3.1.0` on the txt:
  1 error, 4 warnings, dispositioned in pull request #33.
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
