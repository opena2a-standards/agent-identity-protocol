# Specification notes

Notes on [AIP-SPEC.md](../AIP-SPEC.md): the Internet-Draft revision it pairs with and where the two differ, and the reference identity provider's endpoints.

## Internet-Draft

**Internet-Draft.** This specification is also published as the individual Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/). `draft-fane-opena2a-aip-04`, submitted 2026-10-06, is the current datatracker revision and pairs with 1.2.0-draft; the 1.2.0-draft entry in [CHANGELOG.md](../CHANGELOG.md) lists what that version changed. Its txt on the datatracker matches the txt in this repository; the xml in this repository has since dropped its `submissionType` attribute and tags its BCP 14 keywords. `AIP-SPEC.md` in this repository is 1.2.0-draft with later changes that no dated version and no draft revision carries yet; CHANGELOG.md lists them under Unreleased. The lists below say where it differs from that revision.

One statement of §6.1 was in the specification when that revision was made and is not in Section 7.1 of the draft:

- "AIP-conformant implementations MAY substitute their own per-factor scoring functions provided the factor set, weights, and 0.0-1.0 composite range remain unchanged"

Four parts of the specification have no counterpart in the draft, and none of them carries a BCP 14 keyword:

- §2.1 Relationship to A2A-IDF identity levels.
- §11 Integration Patterns.
- Appendix A, Reference Implementation.
- Appendix B, Relationship to ATP.

Six parts of the draft have no counterpart in the specification:

- Section 1, Introduction. The specification's abstract carries the list of protocols AIP is designed to complement and names the reference implementation, as that section does.
- Section 8, Portable Credential and Transparency Log. It states a requirement the specification does not: "A verifier that encounters a credential declaring an ML-DSA-65 signature MUST verify at least one ML-DSA-65 signature in addition to at least one Ed25519 signature."
- Section 13.5, Unverified Type and Declared-Purpose Fields. Its MUST NOT statements restate the §3.3 rule on the declared purpose and the §3.4 rule on the agent type.
- Appendix A, Related Work.
- Appendix B, Document History.
- Appendix C, Acknowledgments.

Four changes made to the specification since that revision are to a requirement or its wording:

- §3.1 defines the agent ID as `aim_` followed by the base64url encoding of the first 12 bytes of the public key, the form `opena2a-cli identity create` prints, and lets a provider assign its own identifier instead, where Section 4.1 of the draft gives the first eight hexadecimal characters of the SHA-256 digest of the public key. The examples in §3.3, §5.3, §7.1, §8.2 and §9.1 carry `aim_PUAXw-hDiVqStwqn`, an agent ID of that form, where the draft's examples carry `aim_7f3a9c2e`.
- §5.4 says a JWT access token's lifetime SHOULD NOT exceed 2 hours, where Section 6.4 of the draft gives JWT bearer tokens "a one-hour time-to-live".
- §6.1 no longer says "Implementers substituting their own scoring functions SHOULD NOT treat the stubbed factors as validated by the reference implementation until it measures them", a statement that was in the specification when that revision was made and that Section 7.1 of the draft does not carry either. The statement applied until the reference implementation measured compliance, drift detection and user feedback, and it now has a scoring function for each.
- §12.1 reads "MUST NOT be transmitted" where Section 13.1 of the draft reads "MUST NEVER be transmitted". This change is editorial.

Nine changes made since that revision are informative:

- A version note above the abstract says the text is 1.2.0-draft with changes made after that version was dated, and names §3.1 and §5.4 as the changed requirements.
- The naming note gives each author of draft-aip-agent-identity-protocol-00 their own affiliation, James Cao (Montcao) and Carlos Eduardo Arango Gutierrez (NVIDIA), where it had given both the second one. The draft cites that document in its Appendix A, Related Work, and its reference gives the authors as "Cao and Arango".
- Each line of the abstract's list of protocols AIP is designed to complement ends with an implementation status, which Section 1 of the draft does not give.
- §3.2 says the reference implementation will issue `did:web:aim.opena2a.org:agents:<uuid>` and identify itself as `did:web:aim.opena2a.org`, where it had said it does, as Section 4.2 of the draft still says. §10.1 says its discovery sample shows the target form and gives the `providerDid` the reference provider reported on 2026-10-11, `did:aip:provider_opena2a`; Section 12 of the draft carries the sample without that note.
- §3.3 carries a reference implementation status note, which Section 4.3 of the draft does not.
- §6.1 says the reference implementation implements algorithm version 1 of the 9-factor algorithm, without the unscored state that version 2 adds, where it had said the 9-factor algorithm is implemented in the reference implementation. Its per-factor implementation status paragraph says all nine factors have scoring functions, where it had said six were measured and compliance, drift detection and user feedback were stubbed. A composition implementation status paragraph says the reference implementation publishes a composite for every agent, including one with no verification events, and that its calculator and score type carry no `algorithmVersion` or `scoreStatus`. Section 7.1 of the draft names no reference implementation.
- §9.1 carries a reference implementation status note, which Section 11.1 of the draft does not.
- §14 lists RFC 3339, RFC 4648, RFC 6749, RFC 7523 and RFC 8785, which the text cites and the list had omitted. Section 15 of the draft lists RFC 3339, RFC 4648 and RFC 8785, and does not cite the other two, which only the OpenID Connect status line in the abstract cites.
- Appendix A says the reference implementation targets Conformance Level 2 and does not meet it yet, where it had said the reference implementation was "at Conformance Level 2". The draft's appendices are Related Work, Document History and Acknowledgments, so it has no counterpart of Appendix A or of the A.1 table.

Four more changes made since that revision are informative too, each to a row of the Appendix A.1 table:

- Appendix A.1 marks its row for §5 Verification Partial, where it had Shipped, and says the §5.1 exchange is not served.
- Appendix A.1 marks its row for §6 Trust Scoring Partial, where it had Shipped, and says the reference implementation is at algorithm version 1 and does not implement the unscored state or `algorithmVersion` of version 2.
- Appendix A.1 says in its row for §3 Agent Identity that the provider assigns each agent a UUID and that `opena2a-cli identity create` derives the §3.1 agent ID.
- Appendix A.1 dates its notes on §3 Hybrid PQC signing, §6.5 ATP integration and Local offline verification 2026-10-11. The §3 Hybrid PQC signing row says the reference implementation signs no ATC and its issuance route asks the Registry to sign, where it had named an Ed25519-only issuer with no production callers. The §6.5 row marks ATP integration Partial, where it had Not yet integrated. The Local offline verification row names the TypeScript and Java SDK verifiers, where it had said none of the TypeScript, Python and Java SDKs ships one.

One more change made since that revision is informative too, to an example that quoted commands the CLI does not have:

- §11.4 describes the trust-threshold step of a CI/CD pipeline as a flow and shows `identity create --name deploy-agent` as the step the CLI runs, where it had quoted `identity check-trust`, its `--min-score` option, `identity create --type` and `identity verify --name`, which `opena2a-cli` 0.10.13 does not have. The draft has no section of integration patterns, so it has no counterpart of §11.4.

## Reference provider

These commands continue the README [Quick Start](../README.md#quick-start): "the identity created above" is the one its first command creates.

```bash
# Discover an identity provider
curl https://aim.opena2a.org/.well-known/aip

# Resolve an agent's DID document. The identifier printed is the deprecated pre-1.1
# alias form, the one the reference resolver answers as of 2026-09-08; the specified
# form is did:web:aim.opena2a.org:agents:<agent-uuid> (AIP-SPEC 3.2) and its did.json
# route is not served. This answers only for an agent registered with this
# provider; without opena2a login, the identity created above is stored locally and
# is not registered. <agent-uuid> is a placeholder: as printed the request returns
# 400 invalid_agent_id, and a UUID the provider has not issued returns 404 did_not_found.
curl "https://aim.opena2a.org/api/v1/did/did:aip:aim_<agent-uuid>"
```

On 2026-09-02 both `https://aim.opena2a.org/.well-known/aip` and `https://api.aim.opena2a.org/.well-known/aip` answered HTTP 200 with the provider's discovery document; that is a dated measurement, and the discovery command above is how to check the current state.
