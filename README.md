> **OpenA2A specs** · [did:opena2a](https://github.com/opena2a-standards/did-method-opena2a) · **AIP** · [ATX](https://github.com/opena2a-standards/atx-spec) · [ATP](https://github.com/opena2a-standards/agent-trust-protocol) · [AAP](https://github.com/opena2a-standards/agent-authorization-protocol) · [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management) · [all specs ↗](https://specs.opena2a.org)

# OpenA2A Agent Identity Protocol (OpenA2A AIP)

OpenA2A's open standard for AI agent identity, capabilities, and trust.

OpenA2A AIP answers "Who is this agent, what can it do, and should I trust it?" with cryptographic identity, structured capabilities, and multi-factor trust scoring.

> **Naming note.** Multiple independent specifications use the abbreviation "AIP" for "Agent Identity Protocol" (see [Naming and prior art](#naming-and-prior-art) below). When referenced outside this repository, please use the fully qualified name **"OpenA2A AIP"** to disambiguate. The bare "AIP" is retained inside this repository where context is unambiguous.

## Contributing

This specification is early and authored in the open. We are looking for co-authors, an independent second implementation, and security review before it goes to an external standards body. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Quick Start

```bash
# Create an agent identity
npx opena2a-cli identity create --name my-agent
# prints, with opena2a-cli 0.10.13 (your agent ID and public key will differ and
# Stored in names your own home directory; a repeat run in the same home directory
# prints "Identity already exists" and the same agent ID):
#   Identity created
#     Agent ID:    aim_z9eLMMCNM2A3VpcV
#     Name:        my-agent
#     Public Key:  z9eLMMCNM2A3VpcVeef9RvgDQVX+E6zk...
#     Stored in:   /home/you/.opena2a/aim-core

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

## Use cases

### A browser agent acts for someone you cannot see

A shopping agent drives a real browser to your checkout for a person who has left the room. The web identifies people with passwords and cookies and identifies servers with TLS certificates; the agent is neither, so your site guesses from a User-Agent string, and anyone can send any string. When the guess is wrong, the person whose account the agent used pays for it.

AIP gives the agent a cryptographic identity and a way to prove it. The verifier issues a random challenge, the agent signs it with the key bound to its identity, and the verifier checks the signature, the key binding, the challenge's freshness and that the nonce was used once (AIP-SPEC Section 5.1).

What you can do today: run the Section 5.1 transcripts in the conformance suite. One is accepted; three are rejected for a wrong key, a stale challenge and a replayed nonce.

```bash
git clone https://github.com/opena2a-standards/aip-conformance
cd aip-conformance/verifiers/go
go run . ../../fixtures
```

Where it stops today: the reference identity provider advertises the challenge endpoint in its discovery document but does not serve that route yet, so the transcripts above are the way to exercise Section 5.1.

### You run many agents and need to know which one to trust less today

A platform team runs agents built by several teams. One begins failing actions and tripping security alerts, and nobody has a number that moves, so its access stays where it was until a person notices.

AIP defines a trust score from 0.0 to 1.0 composed of nine weighted factors (Section 6). Penalties are applied and recorded against the agent, and the identity provider publishes a discovery document that any relying party can fetch.

What you can do today: run the first two commands in [Quick Start](#quick-start), which create an agent identity and fetch the identity provider's discovery document.

Where it stops today: the reference implementation scores all nine factors, but compliance counts only for an agent whose organization has a compliance snapshot, and user feedback only for an agent that has feedback ratings. For any other agent those factors are excluded: their weight is redistributed, and the composite is capped at the value it would have with them scored neutral (AIP-SPEC Section 6.1, implementation status).

Why you can check this yourself: [`AIP-SPEC.md`](AIP-SPEC.md) and the Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/); [aip-conformance](https://github.com/opena2a-standards/aip-conformance), 7 byte-pinned fixtures (4 challenge-response transcripts, 3 trust-score compositions) with Go and Python verifiers; the live discovery document at `https://aim.opena2a.org/.well-known/aip`; and the reference implementation, [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management).

## Specification

[AIP-SPEC.md](AIP-SPEC.md) — the full protocol specification.

**Internet-Draft.** This specification is also published as the individual Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/). `draft-fane-opena2a-aip-04`, submitted 2026-10-06, is the current datatracker revision and pairs with 1.2.0-draft; the 1.2.0-draft entry in [CHANGELOG.md](CHANGELOG.md) lists what that version changed. Its txt on the datatracker matches the txt in this repository; the xml in this repository has since dropped its `submissionType` attribute and tags its BCP 14 keywords. `AIP-SPEC.md` in this repository is 1.2.0-draft with later changes that no dated version and no draft revision carries yet; CHANGELOG.md lists them under Unreleased. The lists below say where it differs from that revision.

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

Twelve changes made since that revision are informative:

- A version note above the abstract says the text is 1.2.0-draft with changes made after that version was dated, and names §3.1 and §5.4 as the changed requirements.
- The naming note gives each author of draft-aip-agent-identity-protocol-00 their own affiliation, James Cao (Montcao) and Carlos Eduardo Arango Gutierrez (NVIDIA), where it had given both the second one. The draft cites that document in its Appendix A, Related Work, and its reference gives the authors as "Cao and Arango".
- Each line of the abstract's list of protocols AIP is designed to complement ends with an implementation status, which Section 1 of the draft does not give.
- §3.2 says the reference implementation will issue `did:web:aim.opena2a.org:agents:<uuid>` and identify itself as `did:web:aim.opena2a.org`, where it had said it does, as Section 4.2 of the draft still says. §10.1 says its discovery sample shows the target form and gives the `providerDid` the reference provider reported on 2026-10-11, `did:aip:provider_opena2a`; Section 12 of the draft carries the sample without that note.
- §3.3 carries a reference implementation status note, which Section 4.3 of the draft does not.
- §6.1 says the reference implementation implements algorithm version 1 of the 9-factor algorithm, without the unscored state that version 2 adds, where it had said the 9-factor algorithm is implemented in the reference implementation. Its per-factor implementation status paragraph says all nine factors have scoring functions, where it had said six were measured and compliance, drift detection and user feedback were stubbed. A composition implementation status paragraph says the reference implementation publishes a composite for every agent, including one with no verification events, and that its calculator and score type carry no `algorithmVersion` or `scoreStatus`. Section 7.1 of the draft names no reference implementation.
- §9.1 carries a reference implementation status note, which Section 11.1 of the draft does not.
- §14 lists RFC 3339, RFC 4648, RFC 6749, RFC 7523 and RFC 8785, which the text cites and the list had omitted. Section 15 of the draft lists RFC 3339, RFC 4648 and RFC 8785, and does not cite the other two, which only the OpenID Connect status line in the abstract cites.
- Appendix A says the reference implementation targets Conformance Level 2 and does not meet it yet, where it had said the reference implementation was "at Conformance Level 2". The draft's appendices are Related Work, Document History and Acknowledgments, so it has no counterpart of Appendix A or of the A.1 table.
- Appendix A.1 marks its row for §5 Verification Partial, where it had Shipped, and says the §5.1 exchange is not served.
- Appendix A.1 marks its row for §6 Trust Scoring Partial, where it had Shipped, and says the reference implementation is at algorithm version 1 and does not implement the unscored state or `algorithmVersion` of version 2.
- Appendix A.1 says in its row for §3 Agent Identity that the provider assigns each agent a UUID and that `opena2a-cli identity create` derives the §3.1 agent ID.

One more change made since that revision is informative too, to an example that quoted commands the CLI does not have:

- §11.4 describes the trust-threshold step of a CI/CD pipeline as a flow and shows `identity create --name deploy-agent` as the step the CLI runs, where it had quoted `identity check-trust`, its `--min-score` option, `identity create --type` and `identity verify --name`, which `opena2a-cli` 0.10.13 does not have. The draft has no section of integration patterns, so it has no counterpart of §11.4.

## Conformance Levels

| Level | Name | What It Means |
|-------|------|---------------|
| 1 | Local Identity | SDK/CLI keypair. No server needed. |
| 2 | Managed Identity | + verification, trust scoring, audit. |
| 3 | Federated Identity | + DIDs, verifiable credentials, cross-platform. |

## Interoperability

AIP is designed to complement the six protocols below. Each line ends with a status, as of 2026-10-11, for what that line describes. **Specified** means AIP-SPEC describes it and no code for it was found in the reference implementation. **Implemented** means the reference implementation has code for it. **Tested in conformance** means a fixture in [aip-conformance](https://github.com/opena2a-standards/aip-conformance) exercises it; none of the six is, because that suite's fixtures cover the Section 5.1 challenge-response and the Section 6.1 trust-score composition.

- [Google A2A Protocol](https://github.com/a2aproject/A2A) — AIP identity in agent cards. **Implemented** in part, for the agent card: the card the reference implementation serves carries the agent's ID and registered public key in an `aim` extension, and that ID is the UUID the provider assigns (AIP-SPEC Section 3.1). Its A2A verification service (AIP-SPEC Appendix A) is not assessed here.
- [Anthropic MCP](https://modelcontextprotocol.io) — capability-based tool access control. **Implemented** in part: the reference implementation checks an agent's capabilities server-side. Verifying a connecting agent by the Section 5.1 challenge-response is specified, and the reference implementation does not serve that exchange.
- [OpenID Connect](https://openid.net/connect/) — JWT tokens for machine-to-machine auth. **Implemented** in part: the reference implementation serves an OAuth 2.0 token endpoint (RFC 6749) that accepts the JWT-bearer grant type of RFC 7523, where a registered agent exchanges an assertion signed with its Ed25519 key for a bearer access token. The request carries that assertion in `client_assertion`, with `client_id` and `client_assertion_type`; the endpoint reads no `assertion` parameter, in which RFC 7523 Section 2.1 carries the JWT. That endpoint returns no OpenID Connect ID token, and Section 5.4 defines AIP's own JWT bearer tokens and no OAuth 2.0 or OpenID Connect flow.
- [WebAuthn/FIDO2](https://www.w3.org/TR/webauthn-3/) — hardware key storage for browsers. **Specified** (Sections 11.1 and 12.1).
- [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/) — trust scores as VCs. **Specified** (Section 6.4).
- [ATP (Agent Trust Protocol)](https://github.com/opena2a-standards/agent-trust-protocol) — ecosystem trust. **Implemented** in part: the reference implementation has a one-way push through its registry bridge, and AIP trust scores are not yet wired into the ATP transparency log (AIP-SPEC Appendix A.1).

The rows behind these statuses are in [GAP-ANALYSIS.md](GAP-ANALYSIS.md) (A2A agent card identity, MCP capability-based tool access, OAuth 2.0 / OIDC, WebAuthn/FIDO2, Verifiable Credential expression, ATP integration) and in AIP-SPEC Appendix A.1 (§4 Capabilities, §5 Verification, §6.5 ATP integration).

## How AIP and ATP Work Together

```
AIP (identity + behavior)     ATP (code + provenance)
  "Who is this agent?"           "Is this agent's code safe?"
         ↓                              ↓
              Combined Trust Decision
              "Is this agent safe to use?"
```

## Reference Implementation

The [OpenA2A AIM Platform](https://github.com/opena2a-org/agent-identity-management) is the reference implementation and targets AIP Level 2. It does not serve the Section 5.1 challenge-response exchange yet, which Level 2 requires; [AIP-SPEC.md Appendix A.1](AIP-SPEC.md#a1-spec-sections-currently-implemented-by-aim) lists the status of each section.

## Related Standards

- [OASB (Open Agent Security Benchmark)](https://github.com/opena2a-org/oasb) — security controls

## Naming and prior art

The abbreviation "AIP" for "Agent Identity Protocol" appears in at least four independent Internet-Drafts or specifications as of 2026-09-30, three of them in the table below. Implementers comparing options should be aware of this collision and pin to the fully qualified name when referencing any of them.

| Spec                                                                                                 | Authors                                | First publication | Scope                                                                                                                                              |
| ---------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **OpenA2A AIP** (this repository)                                                                    | OpenA2A                                | March 2026        | Identity, capabilities, verification, trust scoring, governance, lifecycle, audit. Reference implementation in [AIM](https://github.com/opena2a-org/agent-identity-management). |
| **[draft-aip-agent-identity-protocol-00](https://datatracker.ietf.org/doc/draft-aip-agent-identity-protocol/)** | James Cao (Montcao), Carlos Eduardo Arango Gutierrez (NVIDIA) | March 16, 2026    | Two-layer model: unique agent identity with cryptographic signing + policy enforcement through an interposing proxy.                                |
| **[draft-singla-agent-identity-protocol-00](https://datatracker.ietf.org/doc/draft-singla-agent-identity-protocol/00/)** | Paras Singla (Independent)             | April 16, 2026    | Decentralized identity + delegation; introduces the `did:aip` DID method, capability-based authorization, cryptographic delegation chains.          |

A fourth, draft-prakash-aip (revision 01, 2026-08-19), also uses the abbreviation; its scope is not summarized here. draft-aip-agent-identity-protocol-00 expired on 2026-09-17 (datatracker state as of 2026-09-30).

The three specs in the table are independent of one another. OpenA2A AIP has the broadest surface (identity through audit), the Cao/Arango draft is closest to OpenA2A AIP's capability + enforcement scope, and the Singla draft introduces a `did:aip` DID method. AIP defines no DID method; provider-scoped identifiers use `did:web`; pre-1.1 `did:aip:aim_` identifiers are deprecated aliases. The reference implementation issued identifiers in that form (AIP-SPEC §3.2). OpenA2A's registered W3C method is [`did:opena2a`](https://github.com/opena2a-standards/did-method-opena2a), used at the ATP/ATX layer.

OpenA2A's position is that the specifications in the table solve adjacent but distinct problems. The qualified name "OpenA2A AIP" is this repository's disambiguation.

## License

Apache-2.0
