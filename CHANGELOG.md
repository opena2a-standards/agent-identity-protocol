# Changelog

All notable changes to the OpenA2A Agent Identity Protocol specification are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Changed

- `AIP-SPEC.md` §3.1 defines the agent ID as `aim_` followed by the base64url encoding (RFC 4648
  Section 5) of the first 12 bytes of the public key, 16 characters, the form
  `opena2a-cli identity create` prints and writes to identity files. It previously gave `aim_`
  followed by the first 8 hexadecimal characters of SHA-256 of the public key, a form neither the
  CLI nor the reference provider produces. §3.1 also says a provider MAY assign its own
  identifier instead (the reference provider assigns a UUID) and that a verifier treats either
  kind as opaque. Its example is now a vector: the public key of the §5.1.2
  `challenge-response-valid` fixture and the agent ID derived from it, `aim_PUAXw-hDiVqStwqn`,
  which replaces `aim_7f3a9c2e` in every example. Appendix A.1 and GAP-ANALYSIS.md say the CLI
  derives the agent ID and the provider assigns a UUID. `draft-fane-opena2a-aip-04`, as
  submitted, still gives the SHA-256 form in Section 4.1; README.md says so.
- `AIP-SPEC.md` §5.4 says a JWT access token's lifetime SHOULD NOT exceed 2 hours, instead of
  giving JWT bearer tokens a fixed 1-hour TTL. The reference implementation issues access tokens
  valid for 2 hours by default and makes the lifetime configurable. `draft-fane-opena2a-aip-04`,
  as submitted, still gives "a one-hour time-to-live" in Section 6.4, and README.md now lists this
  change beside the §12.1 one. This entry was filed under Fixed; it changes a requirement, as the
  §3.1 entry above does.
- `tests/test_agent_id.py` derives the agent ID of the §3.1 example from its public key and checks
  it, checks that every other `aim_` agent ID in `AIP-SPEC.md` has the §3.1 shape, and checks the
  README Quick Start agent ID against the public key printed beside it.

### Fixed

- `AIP-SPEC.md` Appendix A.1 describes the reference implementation as it is, with each of three
  notes dated. The hybrid signing row says the Ed25519-only `RealATCIssuer` was removed, where it
  called it an issuer with no active production callers, and that the reference implementation
  signs no credential: its `POST /api/v1/agents/{id}/atc` route asks the
  Registry to sign. The §6.5 ATP row is Partial, not "Not yet integrated", matching
  `GAP-ANALYSIS.md`, and cites ATP-SPEC 1.1.0-draft instead of calling v1.0.0-rc1 recent. The
  local verification row names the TypeScript and Java SDK verifiers and leaves Python as the one
  SDK without one. The lists under the README's Internet-Draft paragraph name the three rows in
  one item. That item would be the thirteenth informative change in one list, and the count that
  opens a lead-in is a number word no higher than twelve, so the four changes to Appendix A.1 rows
  now have a list of their own, after the nine other informative changes.
  `scripts/test_checks.py` checks each note, and fails if an item on an Appendix A.1 row sits in
  another list.
- `AIP-SPEC.md` Appendix A.1 marks "§6 Trust Scoring (9-factor)" Partial, not Shipped, and §6.1
  says the reference calculator implements algorithm version 1, not "the 9-factor algorithm
  above". Since 1.2.0-draft that algorithm includes the unscored state, which the reference
  calculator does not implement: it publishes a composite for every agent, including one with no
  verification events, and carries no `algorithmVersion` or `scoreStatus`. §6.1 gains a
  composition implementation status paragraph and `GAP-ANALYSIS.md` a row for the gap.
- `AIP-SPEC.md` Sections 3.3 and 9.1 carry a reference implementation status note, as Section
  3.2 does. The published CLI (`opena2a-cli` 0.10.13 with `@opena2a/aim-core` 0.2.0) stores one
  identity in `~/.opena2a/aim-core/identity.json`, not under `identities/`, with `agentId` and
  `agentName` where Section 3.3 has `id` and `name`, no `type`, `capabilities` or `status`, and the
  Ed25519 secret key in plain base64 protected only by file mode 0600, so it is not encrypted at
  rest. `identity create` writes no `identity_created` audit event, and an event written by
  `identity log` has `timestamp`, `action`, `target`, `result` and `plugin` instead of the `type`
  and `agentId` keys in Section 9.1. The notes describe the gap; the requirements are unchanged.
  `draft-fane-opena2a-aip-04`, as submitted, carries neither note in its Sections 4.3 and 11.1,
  and the README's Internet-Draft paragraph says so.
- `README.md` and `AIP-SPEC.md` Appendix A say the reference implementation targets Conformance
  Level 2, instead of saying it implements Level 2. Level 2 requires challenge-response
  verification (Section 5), which Appendix A.1 marks Partial because the reference backend does
  not serve the Section 5.1 exchange.
- `AIP-SPEC.md`, `README.md` and `GAP-ANALYSIS.md` attribute draft-aip-agent-identity-protocol-00
  as that draft does: James Cao (Montcao), Carlos Eduardo Arango Gutierrez (NVIDIA). They had
  placed both authors at NVIDIA. The `GAP-ANALYSIS.md` comparison heading calls it the Cao/Arango
  draft, and its prior-art table dates draft-singla-agent-identity-protocol-00 2026-04-16, the
  datatracker submission date the other two files use, instead of 2026-04-17, the date printed on
  the document.
- The README Interoperability list and the list of protocols AIP is designed to complement in the
  `AIP-SPEC.md` abstract end each of their six lines with a status as of 2026-10-11: specified,
  implemented, or tested in conformance. Both lists stated all six without one. WebAuthn/FIDO2
  and W3C Verifiable Credentials are specified, with no code for them found in the reference
  implementation. Google A2A, Anthropic MCP, OpenID Connect and ATP are implemented in part: the
  reference implementation serves an agent card that carries the agent's ID and registered public
  key in an `aim` extension, checks capabilities, serves an OAuth 2.0 token endpoint that accepts
  the JWT-bearer grant type of RFC 7523 from a registered agent, has a one-way push through its
  registry bridge, and has a credential issuance route that sends the agent's 9-factor behavioral
  score to the OpenA2A Registry, which signs it into a credential and records the issuance in its
  transparency log, and it does not serve the §5.1 exchange, return an OpenID Connect ID token
  from that endpoint, or compute the §6.5 combined score. Its A2A
  verification service is not assessed. None of the six is tested in conformance. The statuses
  are informative, and `draft-fane-opena2a-aip-04` does not carry them; the README's
  Internet-Draft paragraph says so. The `GAP-ANALYSIS.md` row for OAuth 2.0 / OIDC, which said
  that code was removed, names the token endpoint and the device authorization grant the backend
  serves. `scripts/test_checks.py` checks that each line of both lists carries one status, that
  the two lists agree, that the status matches the protocol's `GAP-ANALYSIS.md` row, that the
  OpenID Connect lines and that row name the token endpoint, and that the Google A2A lines name
  the `aim` extension.
- `GAP-ANALYSIS.md` points to Appendix A.1 of `AIP-SPEC.md` as the current record of
  implementation status and says Appendix A.1 prevails where a row of its own tables differs. Two
  rows contradicted Appendix A.1 and the README, and now agree with them: `/.well-known/aip`,
  recorded as not implemented and first in the priority order, is Complete, with a command to
  check it, and leaves the priority order; the challenge-response row, recorded as Complete, is
  Partial, because the backend registers no route for the §5.1 challenge endpoint its discovery
  document advertises. The prior-art table names the two OpenA2A drafts,
  `draft-fane-opena2a-aip` and `draft-fane-opena2a-aap`, each first posted 2026-07-06, where it
  said "not yet filed".
- `AIP-SPEC.md` §11.4 CI/CD Pipeline no longer quotes commands that `opena2a-cli` 0.10.13 does
  not have: `identity check-trust`, its `--min-score` option, `identity create --type` and
  `identity verify --name`. The section now describes the trust-threshold step as a flow, shows
  `identity create --name deploy-agent` as the one step the CLI runs today, and states that no CLI
  command fails a job when the trust score is below a threshold. A test in
  `tests/test_check_scripts.py` fails when `AIP-SPEC.md` or `README.md` quotes an
  `opena2a-cli identity` subcommand or option outside the ones the CLI accepts. The README's
  Internet-Draft paragraph lists the change as an informative one, in a list of its own for a
  change to an example that quoted commands the CLI does not have; `draft-fane-opena2a-aip-04`
  has no section of integration patterns.
- `AIP-SPEC.md` Appendix A.1 marks "§5 Verification (challenge-response)" Partial, not Shipped,
  matching the README. The reference provider's discovery document advertises
  `/api/v1/agents/{agentId}/challenge`, but its backend registers no such route. The row now names
  what is served: `/api/v1/agents/{id}/authorize`, a fine-grained authorization decision endpoint
  that verifies no signed challenge, and the MCP server attestation challenge at
  `/api/v1/mcp-servers/{id}/challenge`.
- `AIP-SPEC.md` §6.1 implementation status, README.md and GAP-ANALYSIS.md say the reference
  implementation scores all nine trust factors, instead of six measured and compliance, drift
  detection and user feedback stubbed. At `agent-identity-management` `main` (`ff53b8cc`,
  2026-10-11) compliance is scored from the organization's compliance snapshot and user feedback
  from the agent's feedback ratings, each excluded for an agent with no such data, and drift
  detection from drift alerts, where none scores 1.0. The Appendix A.1 row for §6 says all nine
  factors have scoring functions, instead of three stubbed. §6.1 no longer says implementers SHOULD
  NOT treat the stubbed factors as validated by the reference implementation, and its unscored
  example names compliance, drift detection and user feedback instead of "the three proposed
  factors", as Section 7.1 of `draft-fane-opena2a-aip-04` does. The lists under the README's
  Internet-Draft paragraph follow: one statement of §6.1 the draft lacks instead of two, and four
  changes to a requirement or its wording instead of three, the fourth being the statement §6.1
  dropped, which the draft does not carry either. `scripts/test_checks.py` fails if the §6.1
  status paragraph, the Appendix A.1 row or the README's trust use case calls a factor stubbed, if
  a GAP-ANALYSIS.md factor row is not Complete, or if the README lists the dropped statement as one
  the draft lacks.
- `AIP-SPEC.md` §3.2 says the reference implementation will issue
  `did:web:aim.opena2a.org:agents:<uuid>` and identify itself as `did:web:aim.opena2a.org`,
  instead of saying it does. On 2026-10-11 its discovery document at
  `https://aim.opena2a.org/.well-known/aip` reported `providerDid` as `did:aip:provider_opena2a`
  with no `publicKey`, and its resolver answers only the deprecated `did:aip:aim_<uuid>` form, as
  the §3.2 status note already said. §10.1 says its discovery sample is the target form and gives
  the reference provider's dated reading. `draft-fane-opena2a-aip-04`, as submitted, still says in
  Section 4.2 that the reference implementation issues the `did:web` form and carries the sample
  in Section 12 without the note; the README's Internet-Draft lists name both in one item, the
  twelfth informative change. `scripts/test_checks.py` fails if §3.2 says the reference
  implementation issues the `did:web` form, if §10.1 drops the note, or if the README item does
  not name both sections of the draft.
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
- `.pre-push-review-not-required` lists the Python check scripts and regression tests the
  repository holds and the four commands to run before a push, which include the two CI runs. It
  said the repository had no test suite or runnable artifacts. `tests/test_check_scripts.py`
  checks that the file does not deny the test suite and names both test commands and every
  script `.github/workflows/validate.yml` runs.
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
  that count trim each text segment and join the segments with no separator, as idnits does with
  text that a child element splits when the whitespace at the split is written literally. So
  `<t>The key words "MUST" and "MAY" <xref target="BCP14"/> in this document ...</t>` is not the
  boilerplate paragraph and counts 2, and `<t>Before <xref target="RFC2119"/> MUST after</t>`,
  which reads "BeforeMUST after", counts 0, as idnits reports. Whitespace that JavaScript's
  `trim()` removes, written as a character reference at a split, is removed by the check and kept
  by idnits, which trims the text as written: `<t>Implementations MUST&#160;<xref
  target="RFC2119"/>&#160;support it.</t>` counts 0 where idnits reports 1. A processing
  instruction or CDATA section splits the text for idnits only: `<t>Before <?pi x?> MUST
  after</t>` counts 1 where idnits reports none.
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
- README.md gives the differences between the specification and `draft-fane-opena2a-aip-04` as
  lists under its Internet-Draft paragraph, each introduced by the number of items in it: the two
  statements of §6.1 the draft lacks, the three changes to a requirement or its wording (§3.1,
  §5.4, §12.1) and eleven informative changes. The paragraph counted three changes and three
  informative additions and left out six edits made to `AIP-SPEC.md` since the draft was made:
  the naming note's attribution, the Appendix A sentence on Conformance Level 2, the Appendix A.1
  rows for §3, §5 and §6, and the §6.1 statement of the algorithm version the reference calculator
  implements, with its composition implementation status paragraph. The §3.1 item also names the
  sections whose examples carry an agent ID of the §3.1 form. `scripts/test_checks.py` checks that
  each count equals the items listed under it, that no other count stands in those paragraphs,
  and, where git history is available, that an item names every part of `AIP-SPEC.md` changed
  since the commit that made the paired draft.
- README.md also lists, under its Internet-Draft paragraph, the parts that only one of the two
  documents has. Four parts of the specification have no counterpart in
  `draft-fane-opena2a-aip-04`, and none of them carries a BCP 14 keyword: §2.1, §11 Integration
  Patterns, Appendix A and Appendix B. Six parts of the draft have no counterpart in the
  specification: its Introduction, Section 8 (Portable Credential and Transparency Log), Section
  13.5 and its Related Work, Document History and Acknowledgments appendices. Section 8 states a
  requirement the specification does not, which the README quotes, and the MUST NOT statements of
  Section 13.5 restate rules of §3.3 and §3.4. The lists said only that the draft has no
  counterpart of Appendix A, inside the item on another change. `scripts/test_checks.py` checks
  that the two lists name every top-level section or appendix only one document has, that each
  item names a section the other document lacks, that the parts of the specification carry no
  BCP 14 keyword while the lead-in says so, that an item on a part of the draft names a keyword
  when that part carries one and none when it does not, and that what such an item quotes is in
  the draft and not in the specification. An item of these two lists does not count as naming a
  part of `AIP-SPEC.md` changed since the draft.
- `AIP-SPEC.md` carries a version note above the abstract: the text is 1.2.0-draft, dated
  2026-10-06, with later changes that no dated version carries yet, and those to §3.1 and §5.4
  change a requirement. §3.1 attributes the earlier agent ID rule to "The 1.2.0-draft text dated
  2026-10-06 ... and every earlier revision" instead of "Revisions up to 1.2.0-draft", which read
  as naming the present text, and README.md says `AIP-SPEC.md` is 1.2.0-draft with later changes
  instead of saying the specification is 1.2.0-draft. The version number is unchanged.
- The OpenID Connect status lines in `README.md` and the `AIP-SPEC.md` abstract, and the OAuth 2.0
  / OIDC row of `GAP-ANALYSIS.md`, name the parameters of the token request: it carries the
  agent's signed JWT in `client_assertion`, with `client_id` and `client_assertion_type`, and the
  endpoint reads no `assertion` parameter, in which RFC 7523 Section 2.1 carries the JWT. They
  named the JWT-bearer grant type without its parameters.
- The ATP status lines in `README.md` and the `AIP-SPEC.md` abstract cite Appendix A.1 for what
  they say of the transparency log. They cited
  §6.5, which specifies the combined score and names no transparency log; the Appendix A.1 row
  for §6.5 does.
- `AIP-SPEC.md` §14 lists RFC 3339, RFC 4648, RFC 6749, RFC 7523 and RFC 8785, which the text
  cites and the list omitted.
- `GAP-ANALYSIS.md` gains an Integration Patterns table with a row for the A2A agent card and a
  row for MCP capability-based tool access. Both restate the Google A2A and Anthropic MCP status
  lines, so each of the six statuses has a row, `scripts/test_checks.py` checks all six against
  one instead of four, and README.md names the six rows. The priority list of `GAP-ANALYSIS.md`
  asks for an OpenID Connect ID token instead of saying to re-add OAuth 2.0 / OIDC, which its
  OAuth 2.0 / OIDC row says the backend serves.
- `.pre-push-review-not-required` no longer names a review workflow the repository does not
  contain; it keeps the commands to run before a push and the sentence on what CI runs.
  `tests/test_check_scripts.py` checks that it names no slash command.
- The two cases of `scripts/test_checks.py` that read `AIP-SPEC.md` as of the commit that made the
  paired draft fail, instead of skipping, where `CI` is set to a value other than an empty
  string, `0` or `false` (in any letter case or with surrounding spaces) and git or that history
  is missing, so a CI run from a shallow clone or an exported tree no longer reports OK without
  running them. A CI job that runs the file needs git and a full clone (`actions/checkout` with
  `fetch-depth: 0`). Elsewhere they still skip. The skip or failure reason names the remedy:
  install git where git is missing, and otherwise use a full clone. Where git runs and fails, the
  reason also quotes the first line of git's message that starts with `fatal:` or `error:`, or its
  first line where none does, so a trace line that `GIT_TRACE` writes first is not quoted in place
  of the error, and the remedy starts with resolving it, since git can fail where the history is
  present, as over the repository's ownership. The two cases run git with `LC_ALL=C`, so its
  message is not translated and its error starts with `fatal:` or `error:` under any locale; under
  a German locale a `fatal:` line would otherwise start with "Schwerwiegend:" and an `error:` line
  with "Fehler:", and a trace line written before either would be quoted in its place.
- `scripts/test_checks.py` does not report "one-way", "two-way", "one-time", "one-hour",
  "one-to-one" or "two-factor", in any letter case, or a number word that follows a hyphen, as in
  "non-zero", as a count outside a lead-in, so a sentence such as "after a one-way comparison" in
  the README Internet-Draft section no longer fails `test_no_count_stands_outside_a_lead_in`. Any
  other hyphenated compound that begins with a number word from zero to twelve is still reported,
  whether it states a count, as "a two-item list" and "the five-field form" do, or not, as
  "one-off" does. The check knows the number words from zero to twelve only, so a higher number
  written as one word, as "twenty" is in "a twenty-item list" and "thirteen" in "a thirteen-field
  form", is not reported. A number word that follows a hyphen is not reported even where it is
  part of a count, as the "five" of "a twenty-five-field form" is, so no part of that count is
  reported.
- `test_changelog_entry_says_what_is_not_reported` and
  `test_docs_say_how_ci_is_read_and_what_a_git_failure_reports` in `scripts/test_checks.py` look
  their entry up in the whole of this file, not only under Unreleased, so they no longer end in a
  bare `StopIteration` once a release moves the two entries above under a version heading. Where
  no entry starts with the words a case looks for, the case fails and its message quotes those
  words.
- The idnits sentence of the 1.2.0-draft pairing paragraph was corrected in place twice. It read
  "reports 0 errors and 6 warnings", with no date and no warning names. The first correction made
  it "0 errors and 6 warnings on 2026-10-06", named the six (`PREFER_BCP14_REF`, two
  `DOWNREF_TO_LOWER_STATUS_IN_REGISTRY` and three `SECTION_TITLE_HAS_UNEXPECTED_INDENTATION`) and
  added a seventh, `DOC_DATE_IN_PAST`, which it dated from 2026-10-10 on, "once the document date
  is more than three days before the day idnits runs". The second correction replaced that rule
  and date: the seventh warning appears once idnits runs more than three and a half days after
  the start of the document date in local time, which is from the afternoon of 2026-10-09 on.
  `tests/test_check_scripts.py` checks the count and its date, derives that boundary from the
  rule idnits 3.1.0 applies, and checks that an entry above the 1.2.0-draft heading names both
  corrections.
- The priority list of `GAP-ANALYSIS.md` no longer keeps "Complete trust scoring" as item 2
  marked done; the item leaves the list, as the `/.well-known/aip` discovery endpoint did. The
  sentences under the list say that a completed item leaves it and where each item that left it
  in 2026-10 is recorded: the discovery endpoint in the Discovery table, and the compliance,
  drift and feedback factors in the Trust Scoring table. `tests/test_check_scripts.py` checks
  that no item is marked done or asks for trust scoring.
- `scripts/test_checks.py` has a space after the `=` that assigns `FULL_CLONE`, so
  `flake8 --select=E225` no longer reports it. `tests/test_check_scripts.py` checks that the
  Python files in `scripts/` and `tests/` put whitespace around assignment and comparison
  operators, the pycodestyle E225 rule, using the standard library tokenizer, so the check needs
  no package.

## [1.2.0-draft] - 2026-10-06

Draft pairing: `draft-fane-opena2a-aip-04` pairs with 1.2.0-draft. It was rendered on 2026-10-06
with xml2rfc 3.34.0 and carries every change listed under this heading; `npx
@ietf-tools/idnits@3.1.0` on the txt reports 0 errors and 6 warnings on 2026-10-06
(`PREFER_BCP14_REF`, two `DOWNREF_TO_LOWER_STATUS_IN_REGISTRY` and three
`SECTION_TITLE_HAS_UNEXPECTED_INDENTATION`); a seventh, `DOC_DATE_IN_PAST`, appears once idnits
runs more than three and a half days after the start of the document date in local time, which
is from the afternoon of 2026-10-09 on.
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
