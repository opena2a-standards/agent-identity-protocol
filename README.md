> **OpenA2A specs** · [did:opena2a](https://github.com/opena2a-standards/did-method-opena2a) · **AIP** · [ATX](https://github.com/opena2a-standards/atx-spec) · [ATP](https://github.com/opena2a-standards/agent-trust-protocol) · [AAP](https://github.com/opena2a-standards/agent-authorization-protocol) · [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management) · [all specs ↗](https://specs.opena2a.org)

# OpenA2A Agent Identity Protocol (OpenA2A AIP)

OpenA2A's open standard for AI agent identity, capabilities, and trust.

OpenA2A AIP answers "Who is this agent, what can it do, and should I trust it?" with cryptographic identity, structured capabilities, and multi-factor trust scoring.

> **Naming note.** Multiple independent specifications use the abbreviation "AIP" for "Agent Identity Protocol" (see [Naming and prior art](#naming-and-prior-art) below). When referenced outside this repository, please use the fully qualified name **"OpenA2A AIP"** to disambiguate. The bare "AIP" is retained inside this repository where context is unambiguous.

## Quick Start

Read [AIP-SPEC.md](AIP-SPEC.md), the protocol specification, first. The commands below create an agent identity with `opena2a-cli` and fetch the reference identity provider's discovery document:

```bash
# Create an agent identity
npx opena2a-cli identity create --name my-agent
```

What `npx opena2a-cli identity create --name my-agent` prints ([full output](docs/captures/identity-create.txt)):

```text
Identity created
  Agent ID:    aim_FwnY3huUgvFoeqwt
  Name:        my-agent
  Public Key:  FwnY3huUgvFoeqwt9PxqdWaR00Q4993c...
  Stored in:   /tmp/aip-quick-start/.opena2a/aim-core
```

Your agent ID and public key will differ, and Stored in names `.opena2a/aim-core` in your own home directory, where the command writes the identity. A repeat run in the same home directory prints "Identity already exists" and the same agent ID.

```bash
# Discover an identity provider
curl https://aim.opena2a.org/.well-known/aip
```

To resolve a registered agent's DID document, and for what the provider's endpoints answered when last measured, see [docs/specification-notes.md](docs/specification-notes.md#reference-provider).

## Use cases

### A browser agent acts for someone you cannot see

A shopping agent drives a real browser to your checkout for a person who has left the room. The web identifies people with passwords and cookies and identifies servers with TLS certificates; the agent is neither, so your site guesses from a User-Agent string, and anyone can send any string.

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

Where it stops today: the reference implementation scores all nine factors, but compliance counts only for an agent whose organization has a compliance snapshot, and user feedback only for an agent that has feedback ratings. [docs/use-cases.md](docs/use-cases.md) says how the score treats any other agent, and what each use case leaves out here.

Why you can check this yourself: [`AIP-SPEC.md`](AIP-SPEC.md) and the Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/); [aip-conformance](https://github.com/opena2a-standards/aip-conformance), byte-pinned fixtures with Go and Python verifiers; the live discovery document at `https://aim.opena2a.org/.well-known/aip`; and the reference implementation, [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management).

## Specification

[AIP-SPEC.md](AIP-SPEC.md) — the full protocol specification.

It is also published as the individual Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/). [docs/specification-notes.md](docs/specification-notes.md) names the draft revision that pairs with the specification's version and lists where the two differ.

### Naming and prior art

Other independent specifications also use "AIP" for "Agent Identity Protocol". [docs/naming-and-prior-art.md](docs/naming-and-prior-art.md) lists them with their authors, first publication and scope.

## Conformance Levels

| Level | Name | What It Means |
|-------|------|---------------|
| 1 | Local Identity | SDK/CLI keypair. No server needed. |
| 2 | Managed Identity | + verification, trust scoring, audit. |
| 3 | Federated Identity | + DIDs, verifiable credentials, cross-platform. |

## Reference Implementation

The [OpenA2A AIM Platform](https://github.com/opena2a-org/agent-identity-management) is the reference implementation and targets AIP Level 2. It does not serve the Section 5.1 challenge-response exchange yet, which Level 2 requires; [AIP-SPEC.md Appendix A.1](AIP-SPEC.md#a1-spec-sections-currently-implemented-by-aim) lists the status of each section.

## Documentation

- [docs/specification-notes.md](docs/specification-notes.md) — the Internet-Draft revision paired with the specification, where the two differ, and the reference provider's endpoints
- [docs/interoperability.md](docs/interoperability.md) — the protocols AIP is designed to complement, a status for each, and how AIP and ATP work together
- [GAP-ANALYSIS.md](GAP-ANALYSIS.md) — what the reference implementation has against what the specification requires
- [docs/naming-and-prior-art.md](docs/naming-and-prior-art.md) — the other specifications named "AIP"
- [docs/use-cases.md](docs/use-cases.md) — the text the use cases above leave out
- [CHANGELOG.md](CHANGELOG.md) — changes to the specification, by version
- [CONTRIBUTING.md](CONTRIBUTING.md) — co-authors, an independent second implementation and security review are wanted; how to contribute
- [OASB (Open Agent Security Benchmark)](https://github.com/opena2a-org/oasb) — security controls

## License

Apache-2.0
