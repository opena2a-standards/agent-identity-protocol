> **OpenA2A specs** · [did:opena2a](https://github.com/opena2a-standards/did-method-opena2a) · **AIP** · [ATX](https://github.com/opena2a-standards/atx-spec) · [ATP](https://github.com/opena2a-standards/agent-trust-protocol) · [AAP](https://github.com/opena2a-standards/agent-authorization-protocol) · [AIM](https://github.com/opena2a-org/agent-identity-management) · [all specs ↗](https://specs.opena2a.org)

# OpenA2A Agent Identity Protocol (OpenA2A AIP)

OpenA2A's open standard for AI agent identity, capabilities, and trust.

OpenA2A AIP answers "Who is this agent, what can it do, and should I trust it?" with cryptographic identity, structured capabilities, and multi-factor trust scoring.

> **Naming note.** Multiple independent specifications use the abbreviation "AIP" for "Agent Identity Protocol" (see [Naming and prior art](#naming-and-prior-art) below). When referenced outside this repository, please use the fully qualified name **"OpenA2A AIP"** to disambiguate. The bare "AIP" is retained inside this repository where context is unambiguous.

## Quick Start

```bash
# Create an agent identity
npx opena2a-cli identity create --name my-agent

# Verify an agent
curl "https://aim.opena2a.org/api/v1/did/did:aip:aim_7f3a9c2e"

# Discover an identity provider
curl https://aim.opena2a.org/.well-known/aip
```

## Specification

[AIP-SPEC.md](AIP-SPEC.md) — the full protocol specification.

## Conformance Levels

| Level | Name | What It Means |
|-------|------|---------------|
| 1 | Local Identity | SDK/CLI keypair. No server needed. |
| 2 | Managed Identity | + verification, trust scoring, audit. |
| 3 | Federated Identity | + DIDs, verifiable credentials, cross-platform. |

## Interoperability

AIP is designed to complement:
- [Google A2A Protocol](https://github.com/google/A2A) — AIP identity in agent cards
- [Anthropic MCP](https://modelcontextprotocol.io) — capability-based tool access control
- [OpenID Connect](https://openid.net/connect/) — JWT tokens for machine-to-machine auth
- [WebAuthn/FIDO2](https://www.w3.org/TR/webauthn-3/) — hardware key storage for browsers
- [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/) — trust scores as VCs
- [ATP (Agent Trust Protocol)](https://github.com/opena2a-org/agent-trust-protocol) — ecosystem trust

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

- [ATP (Agent Trust Protocol)](https://github.com/opena2a-org/agent-trust-protocol) — ecosystem trust
- [OASB (Open Agent Security Benchmark)](https://github.com/opena2a-org/oasb) — security controls

## Naming and prior art

The abbreviation "AIP" for "Agent Identity Protocol" appears in at least three independent specifications as of mid-2026. Implementers comparing options should be aware of this collision and pin to the fully qualified name when referencing any of them.

| Spec                                                                                                 | Authors                                | First publication | Scope                                                                                                                                              |
| ---------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **OpenA2A AIP** (this repository)                                                                    | OpenA2A                                | March 2026        | Identity, capabilities, verification, trust scoring, governance, lifecycle, audit. Reference implementation in [AIM](https://github.com/opena2a-org/agent-identity-management). |
| **[draft-aip-agent-identity-protocol-00](https://datatracker.ietf.org/doc/draft-aip-agent-identity-protocol/)** | James Cao, Carlos Eduardo Arango Gutierrez (NVIDIA) | March 16, 2026    | Two-layer model: unique agent identity with cryptographic signing + policy enforcement through an interposing proxy.                                |
| **[draft-singla-agent-identity-protocol-00](https://datatracker.ietf.org/doc/draft-singla-agent-identity-protocol/00/)** | Paras Singla (Independent)             | April 17, 2026    | Decentralized identity + delegation; introduces the `did:aip` DID method, capability-based authorization, cryptographic delegation chains.          |

The three specs are independent of one another. OpenA2A AIP has the broadest surface (identity through audit), the Cao/Arango draft is closest to OpenA2A AIP's capability + enforcement scope, and the Singla draft overlaps with OpenA2A's [`did:opena2a` method](https://github.com/opena2a-standards/did-method-opena2a) on the DID-method axis (`did:aip` vs `did:opena2a`).

OpenA2A's position is that the three specs solve adjacent but distinct problems and that coordination on shared vocabulary is preferable to a name fight. Outreach to the IETF draft authors is tracked separately. In the meantime, the "OpenA2A AIP" branding in this repository is the unilateral disambiguation step.

## License

Apache-2.0
