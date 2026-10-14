# Naming and prior art

This page compares the specifications that use the abbreviation "AIP". OpenA2A AIP is the specification in this repository, and its reference implementation is OpenA2A AIM (Agent Identity Management).

The abbreviation "AIP" for "Agent Identity Protocol" appears in at least four independent Internet-Drafts or specifications as of 2026-09-30, three of them in the table below. Implementers comparing options should be aware of this collision and pin to the fully qualified name when referencing any of them.

| Spec                                                                                                 | Authors                                | First publication | Scope                                                                                                                                              |
| ---------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **OpenA2A AIP** (this repository)                                                                    | OpenA2A                                | March 2026        | Identity, capabilities, verification, trust scoring, governance, lifecycle, audit. Reference implementation in [AIM](https://github.com/opena2a-org/agent-identity-management). |
| **[draft-aip-agent-identity-protocol-00](https://datatracker.ietf.org/doc/draft-aip-agent-identity-protocol/)** | James Cao (Montcao), Carlos Eduardo Arango Gutierrez (NVIDIA) | March 16, 2026    | Two-layer model: unique agent identity with cryptographic signing + policy enforcement through an interposing proxy.                                |
| **[draft-singla-agent-identity-protocol-00](https://datatracker.ietf.org/doc/draft-singla-agent-identity-protocol/00/)** | Paras Singla (Independent)             | April 16, 2026    | Decentralized identity + delegation; introduces the `did:aip` DID method, capability-based authorization, cryptographic delegation chains.          |

A fourth, draft-prakash-aip (revision 01, 2026-08-19), also uses the abbreviation; its scope is not summarized here. draft-aip-agent-identity-protocol-00 expired on 2026-09-17 (datatracker state as of 2026-09-30).

The three specs in the table are independent of one another. OpenA2A AIP has the broadest surface (identity through audit), the Cao/Arango draft is closest to OpenA2A AIP's capability + enforcement scope, and the Singla draft introduces a `did:aip` DID method. AIP defines no DID method; provider-scoped identifiers use `did:web`; pre-1.1 `did:aip:aim_` identifiers are deprecated aliases. The reference implementation issued identifiers in that form (AIP-SPEC §3.2). OpenA2A's registered W3C method is [`did:opena2a`](https://github.com/opena2a-standards/did-method-opena2a), used at the ATP/ATX layer.

OpenA2A's position is that the specifications in the table solve adjacent but distinct problems. The qualified name "OpenA2A AIP" is this repository's disambiguation.
