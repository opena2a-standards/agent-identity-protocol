> **OpenA2A specs** · [did:opena2a](https://github.com/opena2a-standards/did-method-opena2a) · **AIP** · [ATX](https://github.com/opena2a-standards/atx-spec) · [ATP](https://github.com/opena2a-standards/agent-trust-protocol) · [AAP](https://github.com/opena2a-standards/agent-authorization-protocol) · [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management) · [all specs ↗](https://specs.opena2a.org)

# OpenA2A Agent Identity Protocol (OpenA2A AIP)

OpenA2A's open standard for AI agent identity, capabilities, and trust.

OpenA2A AIP answers "Who is this agent, what can it do, and should I trust it?" with cryptographic identity, structured capabilities, and multi-factor trust scoring.

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

What `curl https://aim.opena2a.org/.well-known/aip` prints, with line breaks added ([full output](docs/captures/discovery.txt)):

```json
{
  "conformanceLevel": 2,
  "endpoints": {
    "agents": "/api/v1/agents",
    "atc": "/api/v1/agents/{agentId}/atc",
    "audit": "/api/v1/agents/{agentId}/audit",
    "capabilities": "/api/v1/capabilities",
    "challenge": "/api/v1/agents/{agentId}/challenge",
    "didResolve": "/api/v1/did/{did}",
    "trustScore": "/api/v1/agents/{agentId}/trust",
    "verify": "/api/v1/agents/{agentId}/verify"
  },
  "providerDid": "did:aip:provider_opena2a",
  "supportedAgentTypes": ["claude", "gpt", "gemini", "langchain", "crewai", "autogen", "semantic-kernel", "mcp-server", "a2a-agent", "custom"],
  "supportedCapabilityNamespaces": ["file", "db", "api", "network", "system", "mcp", "data", "payment"],
  "supportedProtocols": ["mcp", "a2a"],
  "version": "1.0"
}
```

That is the provider's document on the date in [its capture record](docs/captures/discovery.json), and the provider can change it. [AIP-SPEC.md Section 10.1](AIP-SPEC.md#101-well-known-endpoint) shows the target form, and [Reference Implementation](#reference-implementation) says what the reference implementation does not serve yet.

To resolve a registered agent's DID document, and for what the provider's endpoints answered when last measured, see [docs/specification-notes.md](docs/specification-notes.md#reference-provider).

## Specification

[AIP-SPEC.md](AIP-SPEC.md) — the full protocol specification.

It is also published as the individual Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/). [docs/specification-notes.md](docs/specification-notes.md) names the draft revision that pairs with the specification's version and lists where the two differ.

### Naming and prior art

Other independent specifications also use "AIP" for "Agent Identity Protocol". [docs/naming-and-prior-art.md](docs/naming-and-prior-art.md) lists them with their authors, first publication and scope. When referenced outside this repository, use the fully qualified name **"OpenA2A AIP"**.

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
- [docs/use-cases.md](docs/use-cases.md) — two use cases, with what you can run today and where the reference implementation stops
- [CHANGELOG.md](CHANGELOG.md) — changes to the specification, by version
- [CONTRIBUTING.md](CONTRIBUTING.md) — co-authors, an independent second implementation and security review are wanted; how to contribute
- [OASB (Open Agent Security Benchmark)](https://github.com/opena2a-org/oasb) — security controls

## License

Apache-2.0
