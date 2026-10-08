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
# prints, with opena2a-cli 0.10.13 (your agent ID will differ; a repeat run in the
# same home directory prints "Identity already exists" and the same agent ID):
#   Identity created
#   Agent ID:    aim_LT56Njf8cjpbZggq

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

Where it stops today: in the reference implementation six of the nine factors are measured and three are stubbed (AIP-SPEC Section 6.1, implementation status).

Why you can check this yourself: [`AIP-SPEC.md`](AIP-SPEC.md) and the Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/); [aip-conformance](https://github.com/opena2a-standards/aip-conformance), 7 byte-pinned fixtures (4 challenge-response transcripts, 3 trust-score compositions) with Go and Python verifiers; the live discovery document at `https://aim.opena2a.org/.well-known/aip`; and the reference implementation, [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management).

## Specification

[AIP-SPEC.md](AIP-SPEC.md) — the full protocol specification.

**Internet-Draft.** This specification is also published as the individual Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/). This repository's specification is 1.2.0-draft, and `draft-fane-opena2a-aip-04` carries it except for two statements of §6.1 that Section 7.1 of the draft lacks, both in the specification when that revision was made: "AIP-conformant implementations MAY substitute their own per-factor scoring functions provided the factor set, weights, and 0.0-1.0 composite range remain unchanged" and "Implementers substituting their own scoring functions SHOULD NOT treat the stubbed factors as validated by the reference implementation until it measures them". One editorial change has been made to the specification since that revision: §12.1 now reads "MUST NOT be transmitted" where Section 13.1 of the draft reads "MUST NEVER be transmitted". That revision, submitted 2026-10-06, is the current datatracker revision. Its txt there matches the txt in this repository; the xml in this repository has since dropped its `submissionType` attribute and tags its BCP 14 keywords. The 1.2.0-draft entry in [CHANGELOG.md](CHANGELOG.md) lists what changed.

## Conformance Levels

| Level | Name | What It Means |
|-------|------|---------------|
| 1 | Local Identity | SDK/CLI keypair. No server needed. |
| 2 | Managed Identity | + verification, trust scoring, audit. |
| 3 | Federated Identity | + DIDs, verifiable credentials, cross-platform. |

## Interoperability

AIP is designed to complement:
- [Google A2A Protocol](https://github.com/a2aproject/A2A) — AIP identity in agent cards
- [Anthropic MCP](https://modelcontextprotocol.io) — capability-based tool access control
- [OpenID Connect](https://openid.net/connect/) — JWT tokens for machine-to-machine auth
- [WebAuthn/FIDO2](https://www.w3.org/TR/webauthn-3/) — hardware key storage for browsers
- [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/) — trust scores as VCs
- [ATP (Agent Trust Protocol)](https://github.com/opena2a-standards/agent-trust-protocol) — ecosystem trust

## How AIP and ATP Work Together

```
AIP (identity + behavior)     ATP (code + provenance)
  "Who is this agent?"           "Is this agent's code safe?"
         ↓                              ↓
              Combined Trust Decision
              "Is this agent safe to use?"
```

## Reference Implementation

The [OpenA2A AIM Platform](https://github.com/opena2a-org/agent-identity-management) implements AIP at Level 2.

## Related Standards

- [OASB (Open Agent Security Benchmark)](https://github.com/opena2a-org/oasb) — security controls

## Naming and prior art

The abbreviation "AIP" for "Agent Identity Protocol" appears in at least four independent Internet-Drafts or specifications as of 2026-09-30, three of them in the table below. Implementers comparing options should be aware of this collision and pin to the fully qualified name when referencing any of them.

| Spec                                                                                                 | Authors                                | First publication | Scope                                                                                                                                              |
| ---------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **OpenA2A AIP** (this repository)                                                                    | OpenA2A                                | March 2026        | Identity, capabilities, verification, trust scoring, governance, lifecycle, audit. Reference implementation in [AIM](https://github.com/opena2a-org/agent-identity-management). |
| **[draft-aip-agent-identity-protocol-00](https://datatracker.ietf.org/doc/draft-aip-agent-identity-protocol/)** | James Cao, Carlos Eduardo Arango Gutierrez (NVIDIA) | March 16, 2026    | Two-layer model: unique agent identity with cryptographic signing + policy enforcement through an interposing proxy.                                |
| **[draft-singla-agent-identity-protocol-00](https://datatracker.ietf.org/doc/draft-singla-agent-identity-protocol/00/)** | Paras Singla (Independent)             | April 16, 2026    | Decentralized identity + delegation; introduces the `did:aip` DID method, capability-based authorization, cryptographic delegation chains.          |

A fourth, draft-prakash-aip (revision 01, 2026-08-19), also uses the abbreviation; its scope is not summarized here. draft-aip-agent-identity-protocol-00 expired on 2026-09-17 (datatracker state as of 2026-09-30).

The three specs in the table are independent of one another. OpenA2A AIP has the broadest surface (identity through audit), the Cao/Arango draft is closest to OpenA2A AIP's capability + enforcement scope, and the Singla draft introduces a `did:aip` DID method. AIP defines no DID method; provider-scoped identifiers use `did:web`; pre-1.1 `did:aip:aim_` identifiers are deprecated aliases. The reference implementation issued identifiers in that form (AIP-SPEC §3.2). OpenA2A's registered W3C method is [`did:opena2a`](https://github.com/opena2a-standards/did-method-opena2a), used at the ATP/ATX layer.

OpenA2A's position is that the specifications in the table solve adjacent but distinct problems. The qualified name "OpenA2A AIP" is this repository's disambiguation.

## License

Apache-2.0
