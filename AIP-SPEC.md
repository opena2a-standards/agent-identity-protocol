# OpenA2A Agent Identity Protocol (OpenA2A AIP)

## An Open Standard for AI Agent Identity, Capabilities, and Trust

**Version:** 1.2.0-draft
**Authors:** OpenA2A
**Date:** October 2026 (first published March 2026)

> **Version note.** This text is 1.2.0-draft, dated 2026-10-06, with later changes that no dated version carries yet. [CHANGELOG.md](./CHANGELOG.md) lists them under Unreleased, and those to §3.1, §3.3, §5.1.3, §5.1.4 and §5.4 change a requirement. `draft-fane-opena2a-aip-04` pairs with 1.2.0-draft as dated; [docs/specification-notes.md](./docs/specification-notes.md#internet-draft) lists where this text differs from that draft.

> **Naming note.** As of 2026-09-30, at least three other Internet-Drafts use the abbreviation "AIP" for an agent identity protocol: draft-aip-agent-identity-protocol-00 (James Cao (Montcao) and Carlos Eduardo Arango Gutierrez (NVIDIA), first published 2026-03-16, expired 2026-09-17), draft-singla-agent-identity-protocol (Singla, first published 2026-04-16, active) and draft-prakash-aip (revision 01, 2026-08-19, active). When referenced outside this document, use the fully qualified name "OpenA2A AIP". The bare "AIP" is retained within this specification where context is unambiguous. See [docs/naming-and-prior-art.md](./docs/naming-and-prior-art.md) for the prior-art list and OpenA2A's position on the collision.

---

## Abstract

The OpenA2A Agent Identity Protocol (OpenA2A AIP) defines an open standard for creating, managing, and verifying cryptographic identities for AI agents. As AI agents proliferate across browsers, cloud platforms, and enterprise environments, the question "which agent is this, what can it do, and should I trust it?" needs a standardized answer.

AIP provides:

1. **Identity** — cryptographic keypairs bound to agent metadata, resolvable via DID (Section 3)
2. **Capabilities** — a structured vocabulary for what agents can do, with enforcement (Section 4)
3. **Verification** — challenge-response protocol for proving agent identity (Section 5)
4. **Trust Scoring** — multi-factor algorithm for computing and communicating trust (Section 6)
5. **Governance** — behavioral policies that constrain agent actions (Section 7)
6. **Lifecycle** — creation, rotation, suspension, and revocation of agent identities (Section 8)
7. **Audit** — append-only event log for accountability (Section 9)

AIP is designed to complement existing protocols and standards. Each line below ends with a status, as of 2026-10-11, for what that line describes, read against the reference implementation named after the list: *specified* (this document describes it and no code for it was found in the reference implementation), *implemented* (the reference implementation has code for it) or *tested in conformance* (a fixture in the [`aip-conformance`](https://github.com/opena2a-standards/aip-conformance) suite exercises it). None of the six is tested in conformance: that suite's fixtures cover the §5.1 challenge-response and the §6.1 trust-score composition. The statuses are informative.

- **Google A2A** — AIP identity in the agent card. Agents verify each other via AIP before task delegation. *Status: implemented in part, for the agent card. The card the reference implementation serves carries the agent's ID and registered public key in an `aim` extension, and that ID is the UUID the provider assigns (§3.1). Appendix A lists the reference implementation's A2A verification service, which this status does not assess.*
- **Anthropic MCP** — AIP capabilities map to MCP tool permissions. MCP servers verify connecting agents via AIP challenge-response. *Status: implemented in part. The reference implementation checks capabilities (§4, Appendix A.1) and does not serve the §5.1 exchange a server would use to verify a connecting agent (§5, Appendix A.1).*
- **OpenID Connect** — AIP agent tokens extend OAuth 2.0 for machine-to-machine authentication. *Status: implemented in part. The reference implementation serves an OAuth 2.0 token endpoint (RFC 6749) that accepts the JWT-bearer grant type of RFC 7523, where a registered agent exchanges an assertion signed with its Ed25519 key for a bearer access token (GAP-ANALYSIS). The request carries that assertion in `client_assertion`, with `client_id` and `client_assertion_type`; the endpoint reads no `assertion` parameter, in which RFC 7523 Section 2.1 carries the JWT. That endpoint returns no OpenID Connect ID token, and §5.4 defines AIP's own JWT bearer tokens and no OAuth 2.0 or OpenID Connect flow.*
- **WebAuthn/FIDO2** — AIP key storage can use hardware authenticators for high-assurance agent identity. *Status: specified (§11.1, §12.1); not implemented by the reference implementation (GAP-ANALYSIS).*
- **W3C Verifiable Credentials** — AIP trust scores expressed as VCs for cross-platform portability. *Status: specified (§6.4); not implemented by the reference implementation (GAP-ANALYSIS).*
- **ATP (Agent Trust Protocol)** — AIP provides identity; ATP provides ecosystem-wide trust verification. They're complementary layers. *Status: implemented in part. The reference implementation has a one-way push through its registry bridge (GAP-ANALYSIS), and its credential issuance route sends the agent's 9-factor behavioral score to the OpenA2A Registry, which signs it into a credential and records the issuance in its transparency log (Appendix A.1). The reference implementation does not compute the §6.5 combined score.*

This specification defines the protocol. The OpenA2A AIM (Agent Identity Management) platform (`github.com/opena2a-org/agent-identity-management`) is the reference implementation.

---

## 1. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

| Term | Definition |
|------|-----------|
| **Agent** | An AI system that performs actions on behalf of a user or another agent |
| **Identity Provider** | A server that creates and manages agent identities |
| **Relying Party** | A system that verifies an agent's identity before granting access |
| **Capability** | A permission declared in `namespace:action` format |
| **Trust Score** | A 0.0-1.0 value computed from multiple behavioral and provenance signals |
| **Governance Policy** | Constraints on agent behavior (what it MUST and MUST NOT do) |
| **Audit Log** | Append-only record of agent actions and verification events |

---

## 2. Conformance Levels

### Level 1: Local Identity

Agent identity created and managed locally (SDK, CLI). No server required. Suitable for individual developers.

Requirements:
- Ed25519 keypair generation (Section 3.1)
- Local identity file (Section 3.3)
- Local audit log (Section 9.1)
- Capability declaration (Section 4.1)

### Level 2: Managed Identity

Agent identity managed by an identity provider. Adds verification, trust scoring, and centralized audit. Suitable for organizations.

Requirements:
- All Level 1 requirements
- Challenge-response verification (Section 5)
- Trust scoring (Section 6)
- Server-side audit log (Section 9.2)
- API key or JWT authentication (Section 5.4)
- Drift detection (Section 8.4)

### Level 3: Federated Identity

Agent identity verifiable across organizations. Adds DID resolution, verifiable credentials, and cross-platform trust. Suitable for ecosystem-wide deployment.

Requirements:
- All Level 2 requirements
- DID-based agent identifiers (Section 3.2)
- Verifiable Credential trust assertions (Section 6.4)
- Cross-platform capability negotiation (Section 4.3)
- ATP integration for ecosystem trust (Section 6.5)

### 2.1 Relationship to A2A-IDF identity levels

AIP's `Local`, `Managed`, and `Federated` conformance levels describe *deployment topology* (what infrastructure operates the agent identity). The A2A Identity Trust Framework (A2A-IDF, `a2aproject/A2A#1496`) defines a separate three-level taxonomy of `SELF_ASSERTED`, `DOMAIN_VERIFIED`, and `ORGANIZATION_VERIFIED` that describes *provenance of identity binding* (how the identity claim was verified at discovery time). Both taxonomies apply independently to the same agent. A `Local` AIP agent may be `SELF_ASSERTED` or `DOMAIN_VERIFIED` under A2A-IDF; a `Managed` AIP agent may be `DOMAIN_VERIFIED` or `ORGANIZATION_VERIFIED`; a `Federated` AIP agent may be `DOMAIN_VERIFIED` or `ORGANIZATION_VERIFIED`. AIP conformance does not constrain A2A-IDF level assignment and vice versa.

---

## 3. Agent Identity

### 3.1 Cryptographic Identity

Every agent MUST have an Ed25519 keypair (RFC 8032).

```
Private key: 64 bytes (generated via crypto/rand)
Public key:  32 bytes (derived from private key)
Agent ID:    "aim_" + base64url(first 12 bytes of public_key), 16 characters
```

The encoding is the URL and filename safe base64 alphabet of RFC 4648 Section 5. Twelve bytes encode to exactly 16 characters, so the agent ID carries no padding. A tool that creates an identity locally derives its agent ID this way, so anyone holding the public key can recompute it. An identity provider MAY instead assign its own identifier to an agent it registers: the reference provider assigns each agent a UUID and carries it in the agent's DID (§3.2). A verifier treats an agent ID of either kind as an opaque string bound to a key by its registration state (§3.2), and does not recompute it to authenticate the agent.

Example, for the public key of the §5.1.2 `challenge-response-valid` fixture:
```
Public key (base64):        PUAXw+hDiVqStwqnTRt+vJyYLM8uxJaMwM1V8Sr0Zgw
First 12 bytes, base64url:  PUAXw-hDiVqStwqn
Agent ID:                   aim_PUAXw-hDiVqStwqn
```

The 1.2.0-draft text dated 2026-10-06, which `draft-fane-opena2a-aip-04` pairs with, and every earlier revision specified the agent ID as "aim_" followed by the first 8 hexadecimal characters of SHA-256(public_key). Neither the reference CLI nor the reference provider produces that form, and identity files already created carry the form above, so this section specifies the form in use. For the key above the earlier rule gives `aim_39f713d0`, which is not a locally derived agent ID.

Implementations SHOULD also support hybrid Ed25519 + ML-DSA-65 (FIPS 204) for post-quantum readiness:

```
Classical key:     Ed25519 (32-byte pub, 64-byte priv)
Post-quantum key:  ML-DSA-65 (1,952-byte pub, 4,032-byte priv)
Hybrid signature:  Ed25519 sig (64 bytes) + ML-DSA-65 sig (3,309 bytes)
```

Both keys are generated simultaneously. Classical-only verifiers check the Ed25519 signature. Quantum-aware verifiers check both.

### 3.2 Decentralized Identifier (DID)

At Level 3, agents are identified by DIDs conforming to W3C DID Core. Two DID methods with distinct scopes participate in the stack; AIP identities use the first. AIP defines no DID method of its own.

**Provider-scoped: a `did:web` profile (the AIP layer).** An AIP identity provider issues its agents identifiers under the `did:web` method, with the provider's own host inside the identifier:

```
did:web:<provider-host>[:<path>]:agents:<id>
```

where `<provider-host>` is the DNS name of the issuing provider, `<path>` is zero or more colon-separated path segments under which the provider publishes DID Documents, and `<id>` is the provider-assigned identifier. The provider identifies itself as `did:web:<provider-host>`. Resolution follows the `did:web` method: the DID Document is fetched over HTTPS from the host the identifier names, at `https://<provider-host>/<path>/agents/<id>/did.json` for an agent and `https://<provider-host>/.well-known/did.json` for the provider, so the identifier needs no method registration of its own and any resolver that speaks `did:web` resolves it. The provider's `didResolve` endpoint, advertised in `/.well-known/aip` (§10.1), serves the same document under the provider's API path. The reference implementation (AIM) will issue `did:web:aim.opena2a.org:agents:<uuid>` and identify itself as `did:web:aim.opena2a.org`; until then it issues the deprecated alias form (below), and on 2026-10-11 its discovery document reported `providerDid` as `did:aip:provider_opena2a` (reference implementation status, below). A provider MUST reject resolution requests for identifiers it did not issue.

Example:
```
did:web:aim.opena2a.org:agents:7f3a9c2e-1b2d-4c3e-9f10-a1b2c3d4e5f6
```

**Deprecated alias.** Revisions before 1.1 of this section specified the provider-scoped identifier as `did:aip:<namespace>_<id>`, and the reference implementation issued `did:aip:aim_<uuid>` (method name registration, below). A provider that issued identifiers in the pre-1.1 form keeps resolving them for a migration window and lists the alias under `alsoKnownAs` in the agent's DID Document, so a verifier holding either form reaches the same document. Identifiers are opaque to verification (below), so credentials issued against an alias keep verifying.

**Ecosystem-scoped: `did:opena2a` (the trust-fabric method, informative here).** The unified `did:opena2a:<type>:<id>` method is shared by ATP (Agent Trust Protocol) and ATX (Agent Trust eXtension) and is anchored at the OpenA2A Registry, which operates its public resolver. It names cross-provider trust-fabric participants (issuing authorities, publishers, Registry-listed agents). Its registered type prefixes are `registry`, `authority`, `publisher`, `agent`, `mcp_server`, `ai_tool`, `llm` and `skill`, mirrored from the resource type registry in Section 3.2 of `did-method-opena2a`, the source of this list. That section names `a2a_agent` a deprecated alias of `agent`, not a registered type. An AIP identity provider does not serve `did:opena2a`; an agent acquires an ecosystem identifier when it is registered in the Registry, and a provider MAY record that binding in the agent's DID Document via `alsoKnownAs`. The method is normatively specified in [`did-method-opena2a`](https://github.com/opena2a-standards/did-method-opena2a).

Identifiers in AIP protocol messages (for example `agentDid` in the §5.1 transcript) are treated as opaque strings bound to keys by the verifier's registration state: verification semantics do not depend on which method the identifier uses.

The DID Document includes the agent's public keys, capabilities, and service endpoints:

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "id": "did:web:aim.opena2a.org:agents:7f3a9c2e-1b2d-4c3e-9f10-a1b2c3d4e5f6",
  "controller": "did:web:aim.opena2a.org",
  "verificationMethod": [{
    "id": "did:web:aim.opena2a.org:agents:7f3a9c2e-1b2d-4c3e-9f10-a1b2c3d4e5f6#key-1",
    "type": "Ed25519VerificationKey2020",
    "controller": "did:web:aim.opena2a.org:agents:7f3a9c2e-1b2d-4c3e-9f10-a1b2c3d4e5f6",
    "publicKeyMultibase": "z6Mkf5rGMoatrSj1f..."
  }],
  "capabilityInvocation": ["#key-1"],
  "service": [{
    "id": "#identity-provider",
    "type": "AgentIdentityProvider",
    "serviceEndpoint": "https://aim.opena2a.org"
  }]
}
```

> **Method-scoping note (2026-07, restated 2026-09).** Earlier drafts of this section said AIP itself uses the unified `did:opena2a` method. That never matched the reference implementation, which issues provider-scoped identifiers and rejects other methods at its resolver, and it conflated two trust domains: a self-hosted identity provider must not mint identifiers inside the ecosystem-shared namespace that the Registry anchors. The two-domain scoping stands: provider-scoped identifiers at the AIP layer, `did:opena2a` ecosystem-scoped at the ATP/ATX layer. Revision 1.1.0-draft changes only the form of the provider-scoped identifier, from a method name of AIP's own to the `did:web` profile above.

> **Reference implementation status (2026-09-08, public repository `opena2a-org/agent-identity-management`, `main` at `28434a0f`).** The reference resolver serves the deprecated alias form only: `GET /api/v1/did/{did}` answers `did:aip:aim_<uuid>` (the `aim_` tag is stripped when present, `handlers/aip_handler.go:87`), rejects every other method prefix with `400 invalid_did_format` (`aip_handler.go:68`; constant at `domain/agent_did.go:13`), and emits no `alsoKnownAs`. The DID Document it serves carries the agent's Ed25519 public key and, when the agent has one, its ML-DSA-65 public key (`aip_handler.go:112`, `:122`). The `did.json` route of the `did:web` form is not implemented, and no code path resolves `did:opena2a`. This revision specifies the target; it does not change the resolver.

> **Method name registration.** DID method names are registered in the W3C DID Extensions registry. `opena2a` is registered there (w3c/did-extensions#717, merged 2026-07-04), and `web` is listed there as well. The name `aip` is also listed; that entry (`methods/aip.json`, added 2026-05-31) is not OpenA2A's. AIP defines no DID method; provider-scoped identifiers use `did:web`; pre-1.1 `did:aip:aim_` identifiers are deprecated aliases. Identifiers already issued are unaffected because AIP verification treats them as opaque (see below).

### 3.3 Identity File Format

Local identities are stored in a standard directory structure:

```
~/.opena2a/aim-core/
  identities/
    my-agent.json        # Agent identity
  audit.jsonl            # Append-only audit log
```

Identity file format:

```json
{
  "agentId": "aim_PUAXw-hDiVqStwqn",
  "agentName": "my-agent",
  "type": "claude",
  "publicKey": "ed25519:PUAXw+hDiVqStwqn...Zgw",
  "encryptedPrivateKey": "aes-256-gcm:...",
  "capabilities": ["file:read", "api:call"],
  "declaredPurpose": {
    "vocabVersion": "1",
    "category": "customer-support",
    "taskScopes": ["support:triage"],
    "capabilityJustification": {
      "file:read": ["support:triage"],
      "api:call": ["support:triage"]
    },
    "autonomy": "supervised"
  },
  "createdAt": "2026-03-22T10:00:00Z",
  "status": "verified"
}
```

`agentId` holds the agent ID (§3.1) and `agentName` the agent's name. The 1.2.0-draft text dated 2026-10-06, which `draft-fane-opena2a-aip-04` pairs with, and every earlier revision named these keys `id` and `name`. `opena2a-cli identity create` writes the agent ID and name under `agentId` and `agentName`, and the examples in §5.3, §8.2 and §9.1 carry the agent ID under `agentId`, so this section uses those keys.

Private keys MUST be encrypted at rest. The default encryption is AES-256-GCM with a key derived from the user's system keychain or a passphrase.

`declaredPurpose` is **optional**: a structured declaration of what the agent is *for* (`category`, `taskScopes`, `capabilityJustification`, `autonomy`, and the optional `dataScopes` / `egressScopes`). It is an identity and attestation property plus an offline detection signal — it MUST NOT be used as an authorization input, and a verifier MUST NOT reject an identity for lacking it. Its full vocabulary and semantics are defined in [`atx-spec` core.md §1.5](https://github.com/opena2a-standards/atx-spec); when carried in an ATX it is covered by the v1.1 signed payload. At the DID layer, declared purpose is surfaced only as a `PurposeAttestation` service-endpoint pointer, never inline in the DID Document body.

> **Reference implementation status (2026-10-11, published packages `opena2a-cli` 0.10.13 and `@opena2a/aim-core` 0.2.0, the latest of each).** The CLI's local identity does not follow this section. `opena2a-cli identity create` keeps one identity per data directory, in `~/.opena2a/aim-core/identity.json` (aim-core `dist/identity.js:44`), not in a per-agent file under `identities/`. The file holds `agentId`, `agentName`, `publicKey`, `secretKey` and `createdAt`: `publicKey` is plain base64 without the `ed25519:` prefix, the private key is under `secretKey` where the file above has `encryptedPrivateKey`, and there is no `type`, `capabilities` or `status`. `secretKey` is the Ed25519 secret key in plain base64 (`dist/identity.js:62`), protected only by file mode 0600 (`dist/identity.js:71`), so the private key is not encrypted at rest as this section and Section 12.1 require. This revision specifies the target; it does not change the tool.

### 3.4 Agent Types

AIP defines a standard vocabulary for agent types:

| Type | Description |
|------|-----------|
| `claude` | Anthropic Claude-based agents |
| `gpt` | OpenAI GPT-based agents |
| `gemini` | Google Gemini-based agents |
| `langchain` | LangChain framework agents |
| `crewai` | CrewAI framework agents |
| `autogen` | Microsoft AutoGen agents |
| `semantic-kernel` | Microsoft Semantic Kernel agents |
| `mcp-server` | Model Context Protocol servers |
| `a2a-agent` | Agent-to-Agent protocol agents |
| `custom` | Custom implementation |

The type is informational. It MUST NOT be used for security decisions — an agent claiming to be `claude` is not verified as such by the type field alone.

---

## 4. Capabilities

### 4.1 Capability Format

<!-- opena2a-definition: capability-grammar -->
Capabilities are expressed as `namespace:action` strings. This section is the one home of
the capability grammar for the OpenA2A specification family: a capability is a reserved
namespace from Section 4.2, or a namespace prefixed with the defining organization's
domain, a colon, and an action; there is no wildcard action. Other specifications and
every conformance fixture cite this grammar rather than restate it.

```json
{"grammar": "^(?:[a-z0-9-]+(?:\\.[a-z0-9-]+)+/)?[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$"}
```

```
file:read          Read files from the filesystem
file:write         Write files to the filesystem
db:read            Read from databases
db:write           Write to databases
api:call           Make outbound API calls
network:listen     Listen on network ports
system:exec        Execute system commands
mcp:tool_use       Invoke MCP tools
data:pii_access    Access personally identifiable information
payment:process    Process financial transactions
```

### 4.2 Reserved Namespaces

The following namespaces are reserved and have standardized meanings. This table is the
shared capability-namespace registry of the specification family;
[`registries/capability-namespaces.json`](./registries/capability-namespaces.json) is
generated from it, and additions are made by pull request against this repository.

<!-- opena2a-definition: capability-namespaces -->
| Namespace | Description | Risk Level |
|-----------|-----------|------------|
| `file` | Filesystem operations | Medium-High |
| `db` | Database operations | Medium-High |
| `api` | External API calls | Medium |
| `network` | Network operations | High |
| `system` | System-level operations | Critical |
| `mcp` | MCP protocol operations | Medium |
| `data` | Data access and handling | High |
| `payment` | Financial operations | Critical |
| `user` | User data operations | High |
| `agent` | Agent-to-agent operations | Medium |
| `secrets` | Secret material: reading, writing or rotating credentials and keys | Critical |

Organizations MAY define custom namespaces prefixed with their domain:

```
acme.com/billing:charge
acme.com/internal:deploy
```

### 4.3 Capability Negotiation

When an agent connects to a service (MCP server, A2A agent, API), the service SHOULD:

1. Request the agent's declared capabilities
2. Compare against required capabilities for the requested operation
3. Reject the request if the agent lacks the required capability
4. Log the capability check result in the audit trail

```
Agent → Service: "I want to call tool X"
Service → Agent: "Tool X requires [file:read, api:call]. Your capabilities?"
Agent → Service: "My capabilities: [file:read, api:call, db:read]"
Service: Verify agent identity, check capability list, grant or deny
```

### 4.4 Capability Violations

When an agent attempts an action outside its declared capabilities, the identity provider MUST:

1. Record a `CapabilityViolation` event in the audit log
2. Apply a trust score penalty proportional to the violation severity
3. Optionally block the action (configurable per policy)

Violation severity levels:
- `low` — action attempted but not critical (trust penalty: -2%)
- `medium` — sensitive action attempted (trust penalty: -5%)
- `high` — dangerous action attempted (trust penalty: -10%)
- `critical` — system-level or financial action attempted (trust penalty: -20%)

---

## 5. Verification

### 5.1 Challenge-Response Protocol

Agent identity verification uses Ed25519 challenge-response:

```
1. Relying Party → Identity Provider:
   POST /api/v1/agents/{agentId}/challenge

2. Identity Provider → Relying Party: the challenge body (§5.1.1)

3. Relying Party → Agent: the challenge body, for signing

4. Agent → Relying Party: the response body (§5.1.2)

5. Relying Party verifies (§5.1.4)
```

The wire bodies, the canonical signing form, and the replay rule below were
first pinned by the [`aip-conformance`](https://github.com/opena2a-standards/aip-conformance)
suite (v0.2) and are ratified here as normative. A transcript that verifies
against this section produces the same verdict as the suite's reference
verifiers.

#### 5.1.1 Challenge body (IdP → RP)

```json
{
  "challenge": "ClvWi9D7pyXv3ttNMoKSQIct2T6MCf6Eme9f06GC6wY",
  "agentDid":  "did:opena2a:agent:agent_conformance_test_001",
  "nonce":     "nJKmKdgYM3lMNkzxAGiNdA",
  "issuedAt":  "2026-05-27T23:58:00Z",
  "expiresAt": "2026-05-28T00:03:00Z",
  "issuerDid": "did:opena2a:authority:opena2a.org"
}
```

The example is the suite's `challenge-response-valid` fixture bytes. All six
fields are REQUIRED. `challenge` is 32 random bytes and `nonce` 16 random bytes,
each freshly generated from a cryptographically secure source per challenge and
encoded as unpadded base64; `agentDid` is the agent identifier the challenge was
minted for, `issuerDid` the identity provider's DID, and both timestamps are
RFC 3339 UTC with `expiresAt` = `issuedAt` + 5 minutes. The machine-readable
shape is [`schemas/challenge-body-v1.schema.json`](./schemas/challenge-body-v1.schema.json).

The identifiers in this transcript (`agentDid`, `issuerDid`, and `keyId` in
§5.1.2) are ecosystem-scoped `did:opena2a` strings because the suite's test
subject is a Registry-listed agent. A provider-scoped `did:web` identifier
(§3.2) is carried in the same fields in the same way. The bytes above are the
pinned fixture and are unchanged by the §3.2 scoping: verification treats the
identifier as opaque and binds it to a key through the verifier's registration
state or the resolved DID Document (§5.1.4, rule 2).

#### 5.1.2 Response body (Agent → RP)

```json
{
  "agentDid":  "did:opena2a:agent:agent_conformance_test_001",
  "challenge": "ClvWi9D7pyXv3ttNMoKSQIct2T6MCf6Eme9f06GC6wY",
  "nonce":     "nJKmKdgYM3lMNkzxAGiNdA",
  "issuedAt":  "2026-05-27T23:58:00Z",
  "expiresAt": "2026-05-28T00:03:00Z",
  "signature": "8bno3dn0bwJ4/CiC9D8fq6ScFBdjVZAw8gp1I+gL6bUMdxoaKcyMt1h8SYteAWD1YZZnVuf7mUsBlw2dvB1TBw",
  "publicKey": "PUAXw+hDiVqStwqnTRt+vJyYLM8uxJaMwM1V8Sr0Zgw",
  "keyId":     "did:opena2a:agent:agent_conformance_test_001#key-1",
  "signedAt":  "2026-05-27T23:58:30Z",
  "algorithm": "Ed25519"
}
```

The example is the suite's `challenge-response-valid` fixture bytes — a
transcript that actually verifies. The agent echoes the five challenge fields
it is signing over (unpadded base64: `signature` 64 bytes, `publicKey` 32
bytes) and attaches the signature plus key metadata; `keyId` is the
fragment-qualified `<agentDid>#key-N` reference and `signedAt` is RFC 3339 UTC.
The machine-readable shape is
[`schemas/response-body-v1.schema.json`](./schemas/response-body-v1.schema.json).

#### 5.1.3 Canonical signing form

The signature covers a pipe-delimited UTF-8 string of exactly five fields, in
this order (mirroring the ATX eleven-field and ATP seven-field precedent):

```
<challenge>|<agentDid>|<nonce>|<issuedAt>|<expiresAt>
```

The field values are joined with a single `|` character (U+007C, no
surrounding whitespace) — the byte construction is `challenge + "|" + agentDid
+ "|" + nonce + "|" + issuedAt + "|" + expiresAt`. Before joining, `issuedAt`
and `expiresAt` are normalized to UTC RFC 3339 (`Z`-suffixed, second
precision), so an equivalent offset form (`+00:00`) produces the same signed
bytes; `challenge`, `agentDid`, and `nonce` are used byte-exactly as they
appear in the challenge body. Binding `agentDid` and the IdP-issued
`nonce` into the signed bytes is what prevents cross-relying-party replay: a
signature produced for one RP's challenge cannot be presented to another,
because the other RP's IdP would have issued different bytes.

**Unsigned response fields are unauthenticated.** `publicKey`, `keyId`,
`signedAt`, and `algorithm` are NOT covered by the signature. A verifier MUST
resolve the agent's key from its own registration record (or DID document) for
the challenge body's `agentDid` and MUST NOT trust the response's `publicKey` field as
the verification key by itself — a response that verifies only under its own
embedded key proves possession of *some* key, not the agent's bound key.
JCS-canonical JSON signing (RFC 8785) over the full response is a candidate
hardening for a future major revision; the five-field form is normative for
AIP 1.x.

#### 5.1.4 Verification rules

Before the checks below, a relying party MUST reject the transcript when an
object anywhere in the challenge body or the response body has two members
with the same name, or when either body has a member whose name is not one
that §5.1.1 or §5.1.2 gives that body (reject category `PARSE_ERROR`). Names
are compared code point for code point after JSON escape sequences are
resolved, so `"n\u006fnce"` is the name `nonce`, and a name that differs from
a defined one in letter case or in any other character is another name:
`Nonce` is not `nonce`, and neither `issued_at` nor `issuedAt` written with
U+0131 LATIN SMALL LETTER DOTLESS I in place of its `i` is `issuedAt`. Two
members with the same name are rejected whatever their values. RFC 8259,
Section 4, says that "the names within an object SHOULD be unique" and that
when they are not, "the behavior of software that receives such an object is
unpredictable"; decoders also differ in which names they treat as one: some
ignore letter case, some fold Unicode case, and some map one naming convention
onto another. Without this rule, two relying parties could read different
values from one transcript, and a relying party could read a member that no
signature covers as one that the checks below read. An identity provider MUST
NOT emit such a challenge body, and an agent MUST NOT emit such a response
body.

A relying party MUST reject the transcript unless all of the following hold.
The checks run in this order and the first failure determines the reject
category (the property the conformance fixtures pin). The checks take each
value from the challenge body, except the response's `publicKey` and
`signature` and the five fields the response echoes, which check 1 compares
with the challenge body.

1. **Signature** — each of the five fields the response echoes (`challenge`,
   `agentDid`, `nonce`, `issuedAt`, `expiresAt`) is equal to the member of the
   same name in the challenge body, as strings compared code point for code
   point after JSON escape sequences are resolved, and the Ed25519 signature
   verifies over the §5.1.3 canonical bytes under the response's `publicKey`
   (reject category `SIGNATURE_INVALID`). An echo that differs in any
   character is a signature failure, including a timestamp that writes the
   same instant in another form, such as `+00:00` in place of `Z`: §5.1.3
   normalizes the challenge body's timestamps to build the signed bytes, and
   does not normalize an echo before the comparison. This proves possession of
   the presented key; check 2 proves it is the right key.
2. **Bound key** — the presented `publicKey` matches the key bound to the
   challenge body's `agentDid` in the verifier's registration state or
   resolved DID document (for a provider-scoped `did:web` identifier, the
   document the issuing provider serves, §3.2; reject category
   `UNTRUSTED_KEY`). A transcript MUST NOT be accepted on check 1 alone.
3. **Freshness** — the verifier's clock is before the challenge body's
   `expiresAt` (the window is 5 minutes from issuance, evaluated within the
   family clock-skew bound of ATP Section 10.2, which never extends the window;
   reject category `CHALLENGE_EXPIRED`).
4. **Nonce single-use** — the challenge body's `nonce` has not been consumed
   by a prior verification. Verifiers MUST record consumed nonces at least
   until the corresponding challenge's `expiresAt` (reject category
   `NONCE_REPLAY`).
5. **Trusted issuer** — the challenge body's `issuerDid` is in the verifier's
   trusted-issuer set, compared code point for code point with each entry; a
   set with no entry trusts no issuer (reject category `UNTRUSTED_ISSUER`).

#### 5.1.5 Conformance fixtures

Byte-stable transcript fixtures for this section — valid, wrong-key,
stale-challenge, nonce-replay, a response whose echo differs from the challenge
body, an untrusted issuer, and a body with a member name used twice or not
defined for it, each pinned by SHA-256 and verified by
parity-gated Go and Python reference verifiers — live at
[`opena2a-standards/aip-conformance`](https://github.com/opena2a-standards/aip-conformance).
An implementation claiming §5.1 conformance MUST produce the pinned verdict on
every fixture.

### 5.2 Protocol-Specific Verification

AIP defines verification flows for common protocols:

**MCP Verification:**
```
MCP Client connects to MCP Server
  → Server requests AIP challenge
  → Client signs with agent key
  → Server verifies against identity provider
  → Server checks client capabilities against required MCP tools
  → Connection accepted or rejected
```

**A2A Verification:**
```
Agent A wants to delegate task to Agent B
  → A includes signed AIP assertion in A2A message
  → B verifies A's identity and trust score
  → B checks A's capabilities include agent:delegate
  → B accepts or rejects delegation
```

### 5.3 Verification Events

Every verification attempt MUST be logged as a verification event:

```json
{
  "id": "evt_abc123",
  "agentId": "aim_PUAXw-hDiVqStwqn",
  "protocol": "mcp",
  "verificationType": "identity",
  "status": "success",
  "signature": "base64...",
  "messageHash": "SHA256:...",
  "nonce": "base64...",
  "durationMs": 42,
  "driftDetected": false,
  "initiator": {
    "type": "agent",
    "name": "orchestrator-agent"
  },
  "timestamp": "2026-03-22T14:00:00Z"
}
```

### 5.4 Machine-to-Machine Authentication

For programmatic access, AIP supports:

- **API Keys** — SHA-256 hashed, stored server-side, base64-encoded for transport
- **JWT Bearer Tokens** — HMAC-SHA256 signed, containing agent ID and organization ID; an access token's lifetime SHOULD NOT exceed 2 hours
- **SDK Tokens** — scoped tokens for SDK operations (agent registration, verification)

JWT claims:

```json
{
  "sub": "user_123",
  "org": "org_456",
  "iss": "aim.example.com",
  "aud": "aim-api",
  "exp": 1711137600,
  "iat": 1711134000,
  "scope": "agent:read agent:write"
}
```

---

## 6. Trust Scoring

### 6.1 Multi-Factor Algorithm

AIP defines a 9-factor trust scoring algorithm. Each factor contributes a weighted score. The composite score is 0.0 (no trust) to 1.0 (full trust). Weights sum to 100.

| Factor | Weight | Input | Score Range |
|--------|--------|-------|-------------|
| **Verification status** | 25% | Signature verification success rate | 0.0-1.0 |
| **Uptime and availability** | 15% | Health check responsiveness | 0.0-1.0 |
| **Action success rate** | 15% | Action completion rate | 0.0-1.0 |
| **Security alerts** | 15% | Active security alerts (weighted by severity) | 0.0-1.0 |
| **Compliance** | 10% | Framework adherence (SOC 2, HIPAA, GDPR, etc.) | 0.0-1.0 |
| **Execution isolation** | 10% | Sandbox / process isolation posture | 0.0-1.0 |
| **Age and history** | 5% | Operational history | <7d: 0.3, 7-30d: 0.5, 30-90d: 0.75, 90d+: 1.0 |
| **Drift detection** | 3% | Behavioral consistency vs baseline | 0.0-1.0 |
| **User feedback** | 2% | Explicit trust ratings from humans | 0.0-1.0 |

```
trust_score = Σ (factor_weight * factor_score * confidence)
```

Where `confidence` is the data availability for each factor (0.0 = no data, 1.0 = sufficient data). Factors with no data are excluded and their weights redistributed proportionally.

**Anti-gaming ceiling.** Redistribution alone rewards data withholding: an excluded factor effectively inherits the agent's included average, so an operator could raise a well-behaved agent's score by never supplying compliance or feedback data (no data would outscore a measured 0.9). Implementations MUST therefore cap the published composite at the value obtained by scoring every excluded factor at its neutral default (0.5, or the factor's documented no-data baseline): a factor with no data can never contribute more than a neutral measurement would. Agents whose renormalized composite is below the neutral-imputed value keep the renormalized (lower) score — exclusion never props a poorly-scoring agent up toward neutral. Implementations SHOULD report which factors were excluded alongside the score.

**Unscored state and algorithm version.** The exclusion rule above says what happens to a factor with no data; it does not say what happens when most of the weight has no data. Redistribution over a small remainder publishes a composite that reads like a measurement of the whole agent while measuring a fraction of it. This paragraph is the one home of the unscored rule, the wire fields that carry it, and the algorithm version; implementations and their API documentation cite it rather than restate the threshold.

- *Included weight.* `includedWeight` is the sum of the weights of the factors that have data (confidence above 0.0), divided by 100, so it lies in 0.0-1.0. It is computed before redistribution.
- *Unscored rule.* When `includedWeight` is below 0.50, the agent is **unscored**. An implementation MUST NOT publish a composite for an unscored agent: `score` MUST be `null` (not 0, not a default, not the neutral-imputed ceiling), `scoreStatus` MUST be `"unscored"`, and `unscoredReason` MUST be present. The reason vocabulary is `insufficient_data`; an implementation MAY add reasons and MUST document each one. Unscored is a state, not an error: the response is an ordinary success. A trust credential (§6.4), and any credential another OpenA2A specification derives from the trust score, MUST NOT be issued from an unscored state.
- *Measured state.* When `includedWeight` is 0.50 or more, `scoreStatus` is `"measured"` and `score` is the composite computed under the exclusion, redistribution and anti-gaming rules above, in 0.0-1.0.
- *Algorithm version.* Every trust score an implementation publishes carries `algorithmVersion`, an integer. Version 1 is the composition rule without the unscored state; version 2 is this section as amended. A consumer that reads a score with no `algorithmVersion` MUST treat it as version 1. A change to the factor set, the weights, the composition rule, the threshold or the ceiling increments the version.
- *Reporting.* `includedWeight` MUST be reported beside the score in both states, and `unscoredReason` only in the unscored state. Factor identifiers on the wire (in `excludedFactors` and in any per-factor breakdown) are, in the table's order: `verification`, `uptime`, `successRate`, `securityAlerts`, `compliance`, `executionIsolation`, `age`, `driftDetection`, `userFeedback`.

```json
{
  "agentId": "did:web:idp.example:agents:agent_unscored_example_001",
  "algorithmVersion": 2,
  "scoreStatus": "unscored",
  "score": null,
  "unscoredReason": "insufficient_data",
  "includedWeight": 0.30,
  "excludedFactors": ["verification", "uptime", "successRate", "compliance", "driftDetection", "userFeedback"],
  "calculatedAt": "2026-09-22T21:00:00Z"
}
```

An agent with no verification events has no data for verification status, uptime and action success (weights 25, 15 and 15); with compliance, drift detection and user feedback also unmeasured (weights 10, 3 and 2), its `includedWeight` is 0.30 and it is unscored. The same agent scored under version 1 published a composite drawn from security alerts, execution isolation and age alone, capped by neutral imputation of the other six.

**Reference implementation.** The AIM (Agent Identity Management) reference implementation implements algorithm version 1 of the 9-factor algorithm above as the `TrustCalculator` service: the factor set, the weights, exclusion with redistribution, and the anti-gaming ceiling. It does not implement the unscored state that version 2 adds (see the composition implementation status below). AIP §6.1 specifies the factor set, weights, and composition rule; AIP-conformant implementations MAY substitute their own per-factor scoring functions provided the factor set, weights, and 0.0-1.0 composite range remain unchanged. The AIM `TrustCalculator` is the named reference implementation for AIP §6.1 in OpenA2A's ecosystem.

**Per-factor implementation status (reference implementation, 2026-10-11, `main` at `ff53b8cc`).** All nine factors have scoring functions. **Compliance** is scored from the latest compliance snapshot of the agent's organization (the reference implementation's own AIM framework, normalized from 0-100), and **user feedback** from the agent's feedback ratings, counted by sentiment. Each of the two is excluded, and its weight redistributed under the exclusion-and-cap rules above, for an agent that has no such data. **Drift detection** is scored from the configuration-drift and MCP-drift alerts of the last 30 days on the agent and on the MCP servers it connects to, each alert lowering the score by its severity; an agent with no drift alerts is measured at 1.0, not excluded.

**Composition implementation status (reference implementation, 2026-10).** The reference implementation composes scores under algorithm version 1 and does not implement the unscored state. It publishes a composite for every agent: verification status, uptime, action success rate, security alerts and age each fall back to a status-based value instead of reporting no data, so the included weight never falls below 0.75 and no agent falls under the 0.50 threshold. The agent with no verification events in the example above, unscored under this section, receives a number from the reference implementation. The calculator and its score type carry no `algorithmVersion` or `scoreStatus`, so under the algorithm version rule above a consumer treats a reference implementation score as version 1. A composite from the reference implementation therefore does not show that the agent's included weight, computed as this section defines it, reached 0.50.

### 6.2 Behavioral Tiers

Trust scores map to five behavioral tiers (0-4) for policy decisions. The `behaviorTier` field of an AIP-layer credential (§6.4) carries this integer:

| Score range | Tier | Name | Meaning |
|-------------|------|------|---------|
| 0.00 - 0.25 | 0 | Blocked | Agent is compromised or malicious |
| 0.25 - 0.50 | 1 | Warning | Significant trust concerns |
| 0.50 - 0.75 | 2 | Limited | Restricted access, monitoring required |
| 0.75 - 0.90 | 3 | Standard | Normal operations |
| 0.90 - 1.00 | 4 | Elevated | High-trust operations (financial, PII) |

A behavioral tier is not a trust level. The identity provider computes the tier from the §6.1 score. The five names above are tier names. `trustLevel` means the ATP-SPEC §4.1 trust level wherever it appears, in AIP and in any credential defined by another OpenA2A specification. AIP does not restate the ATP-SPEC §4.1 table.

### 6.3 Trust Score History

Identity providers MUST maintain a trust score history with:
- Previous score, new score, delta
- Reason for change (verification, alert, drift, manual)
- Timestamp
- Actor who triggered the change

### 6.4 Verifiable Credential Expression

*Status: Proposed — not yet implemented by the reference implementation (see GAP-ANALYSIS). The equivalent shipped artifact for signed trust expression is the ATP trust proof (§6.5).*

At Level 3, trust scores SHOULD be expressible as W3C Verifiable Credentials.
The sample below is an AIP-layer credential: the identity provider that
computes the score (§12.4) is the issuer, and the subject is the agent's
provider-scoped DID (§3.2). An ecosystem-scoped trust assertion about a
Registry-listed agent is the ATP trust proof (§6.5), issued under
`did:opena2a` by the ecosystem authority, not this credential.

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://opena2a.org/credentials/v1"
  ],
  "type": ["VerifiableCredential", "AgentTrustCredential"],
  "issuer": "did:web:aim.opena2a.org",
  "issuanceDate": "2026-03-22T14:00:00Z",
  "expirationDate": "2026-03-23T14:00:00Z",
  "credentialSubject": {
    "id": "did:web:aim.opena2a.org:agents:7f3a9c2e-1b2d-4c3e-9f10-a1b2c3d4e5f6",
    "trustScore": 0.82,
    "behaviorTier": 3,
    "capabilities": ["file:read", "api:call"],
    "verificationCount": 1847,
    "lastVerified": "2026-03-22T13:55:00Z"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-03-22T14:00:00Z",
    "verificationMethod": "did:web:aim.opena2a.org#key-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z58DAdFfa9SkqZMVPxAQp..."
  }
}
```

### 6.5 ATP Integration

AIP trust scores feed into ATP (Agent Trust Protocol) for ecosystem-wide trust:

- AIP provides **behavioral trust** — how the agent acts in deployment
- ATP provides **provenance trust** — how the agent's code was built and scanned

Combined score:
```
ecosystem_trust = α * aip_behavioral_trust + β * atp_provenance_trust
```

Where α and β are configurable weights (default: α=0.5, β=0.5).

---

## 7. Governance

### 7.1 Policy Format

Agent governance policies are expressed in YAML:

```yaml
agent: aim_PUAXw-hDiVqStwqn
policies:
  - name: "Require approval for file writes"
    capability: "file:write"
    action: "require_approval"
    approvers: ["user:admin@acme.com"]

  - name: "Block system commands"
    capability: "system:exec"
    action: "deny"

  - name: "Rate limit API calls"
    capability: "api:call"
    action: "rate_limit"
    limit: 100
    period: "1m"
```

### 7.2 Policy Actions

| Action | Behavior |
|--------|----------|
| `allow` | Permit without restriction |
| `deny` | Block unconditionally |
| `require_approval` | Queue for human approval before execution |
| `rate_limit` | Allow up to N invocations per period |
| `audit` | Allow but log for review |
| `notify` | Allow but send notification to specified parties |

### 7.3 SOUL Integration

AIP governance policies complement SOUL.md behavioral governance:

- **AIP policies** — technical enforcement (capabilities, rate limits, approvals)
- **SOUL policies** — behavioral governance (injection hardening, data handling, honesty)

An agent SHOULD have both: AIP policies enforced by the identity provider, SOUL policies enforced by the LLM runtime.

---

## 8. Lifecycle

### 8.1 States

```
Created → Pending → Verified → Active
                                  ↓
                              Suspended → Revoked
                                  ↓
                              Reactivated → Active
```

| State | Meaning |
|-------|---------|
| `created` | Identity generated, not yet verified |
| `pending` | Verification in progress |
| `verified` | Identity cryptographically verified |
| `active` | Operating normally |
| `suspended` | Temporarily disabled (policy violation, drift detected) |
| `revoked` | Permanently disabled (compromised, decommissioned) |

### 8.2 Key Rotation

Agents SHOULD rotate keys periodically. The rotation protocol:

1. Generate new keypair
2. Register new public key with identity provider
3. Grace period begins (configurable, default 7 days)
4. During grace period, both old and new keys are valid
5. After grace period, old key is retired

```json
{
  "agentId": "aim_PUAXw-hDiVqStwqn",
  "currentKey": "ed25519:newKey...",
  "previousKey": "ed25519:oldKey...",
  "keyRotationGraceUntil": "2026-03-29T14:00:00Z"
}
```

### 8.3 Suspension and Revocation

An identity provider MUST support:

- **Suspension** — temporary, reversible. Triggers: policy violation, drift detection, manual action.
- **Revocation** — permanent, irreversible. Triggers: compromise confirmed, decommissioning.

Both MUST be logged in the audit trail with reason, actor, and timestamp.

### 8.4 Drift Detection

The identity provider SHOULD monitor for configuration drift:

- **Capability drift** — agent uses capabilities not in its registration
- **MCP drift** — agent connects to MCP servers not in its `talksTo` list
- **Behavioral drift** — action patterns diverge from historical baseline

When drift is detected:
1. Log a `drift_detected` event
2. Create a security alert (severity: high)
3. Apply trust score penalty (-5% first occurrence, -10% repeated)
4. Optionally suspend the agent (configurable per policy)

---

## 9. Audit

### 9.1 Local Audit Log

Level 1 implementations MUST maintain a local append-only audit log:

```
~/.opena2a/aim-core/audit.jsonl
```

Each line is a JSON event:

```json
{"type":"identity_created","agentId":"aim_PUAXw-hDiVqStwqn","timestamp":"2026-03-22T10:00:00Z"}
{"type":"verification_success","agentId":"aim_PUAXw-hDiVqStwqn","protocol":"mcp","durationMs":42,"timestamp":"2026-03-22T10:01:00Z"}
{"type":"capability_violation","agentId":"aim_PUAXw-hDiVqStwqn","capability":"system:exec","severity":"critical","blocked":true,"timestamp":"2026-03-22T10:02:00Z"}
```

> **Reference implementation status (2026-10-11, the packages named in Section 3.3).** The CLI appends events to `~/.opena2a/aim-core/audit.jsonl` (aim-core `dist/audit.js:42`), but `opena2a-cli identity create` writes none, so the log holds no `identity_created` event. An event written by `opena2a-cli identity log` has the keys `timestamp`, `action`, `target`, `result` and `plugin`, not the `type` and `agentId` keys shown above. This revision specifies the target; it does not change the tool.

### 9.2 Server Audit Log

Level 2+ implementations MUST maintain a server-side audit log in an append-only data store.

Event types:

| Event | Description |
|-------|-----------|
| `identity_created` | New agent identity registered |
| `identity_verified` | Challenge-response verification completed |
| `identity_suspended` | Agent suspended |
| `identity_revoked` | Agent permanently revoked |
| `capability_granted` | Capability added to agent |
| `capability_revoked` | Capability removed from agent |
| `capability_violation` | Agent attempted unauthorized action |
| `trust_score_changed` | Trust score recalculated |
| `drift_detected` | Configuration drift found |
| `key_rotated` | Agent key rotation completed |
| `policy_evaluated` | Governance policy applied |
| `a2a_delegation` | Agent-to-agent task delegation |
| `mcp_connection` | Agent connected to MCP server |

---

## 10. Discovery

### 10.1 Well-Known Endpoint

An AIP identity provider MUST serve a discovery document at:

```
GET /.well-known/aip
```

```json
{
  "providerDid": "did:web:aim.opena2a.org",
  "version": "1.0",
  "conformanceLevel": 2,
  "endpoints": {
    "agents": "/api/v1/agents",
    "challenge": "/api/v1/agents/{agentId}/challenge",
    "verify": "/api/v1/agents/{agentId}/verify",
    "capabilities": "/api/v1/capabilities",
    "trustScore": "/api/v1/agents/{agentId}/trust",
    "audit": "/api/v1/agents/{agentId}/audit",
    "didResolve": "/api/v1/did/{did}"
  },
  "publicKey": {
    "algorithm": "Ed25519",
    "publicKeyMultibase": "z6Mkf5rGMoatrSj1f..."
  },
  "supportedAgentTypes": ["claude", "gpt", "gemini", "langchain", "crewai", "mcp-server", "a2a-agent"],
  "supportedCapabilityNamespaces": ["file", "db", "api", "network", "system", "mcp", "data", "payment"],
  "supportedProtocols": ["mcp", "a2a"]
}
```

`providerDid` is the provider's `did:web` self-identifier (§3.2). The `didResolve` endpoint answers for the identifiers the provider issued, including deprecated aliases during their migration window; the same DID Document is also published at the `did:web` path derived from the identifier.

The sample shows the target form, not the reference provider's current document. On 2026-10-11 `https://aim.opena2a.org/.well-known/aip` reported `providerDid` as `did:aip:provider_opena2a` and carried no `publicKey`; check the current state with `curl https://aim.opena2a.org/.well-known/aip`.

---

## 11. Integration Patterns

### 11.1 Google Chrome — Browser Agent Identity

For agents running in the browser (Chrome extensions, web-based agents):

```
1. Agent creates identity using WebCrypto API (Ed25519)
2. Private key stored in IndexedDB (encrypted) or hardware key (WebAuthn)
3. Agent card published at /.well-known/agent.json with AIP identity
4. When user installs agent, Chrome verifies AIP trust score
5. Agent capabilities enforced by extension permissions model
```

AIP maps to Chrome's existing permission model:
- `file:read` → Chrome `fileSystem` permission
- `network:listen` → Chrome `webRequest` permission
- `api:call` → Chrome `fetch` permission

### 11.2 MCP Server Integration

```
MCP Server starts up
  → Registers AIP identity with provider
  → Declares capabilities: mcp:tool_use, file:read
  → MCP Client connects
  → Server challenges client for AIP identity
  → Client signs challenge
  → Server verifies identity + capabilities
  → Client can only invoke tools matching its capabilities
```

### 11.3 A2A Agent-to-Agent

```
Agent A wants to delegate to Agent B
  → A looks up B's AIP identity (DID resolution)
  → A verifies B's trust score (via ATP or direct)
  → A includes signed delegation token in A2A message
  → B verifies A's identity and delegation authority
  → B executes task within its own capability boundaries
  → Both agents log the interaction in their audit trails
```

### 11.4 CI/CD Pipeline

```
Pipeline starts a deployment job
  → Job uses the deploying agent's AIP identity
  → Job reads the agent's trust score from the provider's trustScore endpoint (Section 10)
  → Job fails if the score is below the pipeline's threshold (for example 0.7)
  → Deployment runs only after that check passes
```

With `opena2a-cli` 0.10.13, the identity step is the one the CLI runs:

```yaml
- name: Create agent identity
  run: npx opena2a-cli identity create --name deploy-agent
```

As shown, without `opena2a login`, the identity is stored on the runner and is not registered with an identity provider. The CLI has no command for the trust check: it has no `check-trust` subcommand and no `--min-score` option, so no CLI step fails a job when the score is below a threshold. `identity verify` checks a signature over supplied data (`--data`, `--signature`, `--public-key`) and does not look up an agent by name, and `identity create` has no `--type` option.

---

## 12. Security Considerations

### 12.1 Key Storage

Private keys MUST be encrypted at rest. Implementations SHOULD support:
- System keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- Hardware security keys (WebAuthn/FIDO2)
- HSM integration for server deployments

Private keys MUST NOT be transmitted in plaintext. The identity provider stores only public keys.

### 12.2 Replay Attacks

Challenge-response verification MUST use single-use nonces with a maximum validity of 5 minutes. Nonces MUST NOT be reusable.

### 12.3 Capability Escalation

An agent MUST NOT be able to grant itself capabilities it doesn't have. Capability changes MUST be authorized by the identity provider or an administrator.

### 12.4 Trust Score Manipulation

Trust scores MUST be computed server-side. Agents MUST NOT be able to self-report trust scores. All inputs to the trust calculation MUST be independently verifiable (verification events, uptime checks, audit logs).

---

## 13. IANA Considerations

- **DID methods (no IANA action):** DID method names are registered in the W3C DID Extensions registry, not with IANA. AIP defines no DID method; provider-scoped identifiers use `did:web`; pre-1.1 `did:aip:aim_` identifiers are deprecated aliases (§3.2). `did:opena2a`, the ecosystem-scoped method anchored at the OpenA2A Registry and shared with ATP and ATX, is registered (w3c/did-extensions#717, merged 2026-07-04) and specified in [`did-method-opena2a`](https://github.com/opena2a-standards/did-method-opena2a), whose §3.2 is the registry of resource-type prefixes. `did:web` is specified by the W3C Credentials Community Group and listed in the same registry.
- **Well-Known URI:** `/.well-known/aip`. Identity provider discovery.
- **Capability Namespace Registry:** Standard capability namespaces, initially populated from the §4.2 table.

---

## 14. References

- RFC 2119 — Key words for use in RFCs
- RFC 8032 — Edwards-Curve Digital Signature Algorithm (Ed25519)
- RFC 7519 — JSON Web Token (JWT)
- RFC 3339 — Date and Time on the Internet: Timestamps
- RFC 4648 — The Base16, Base32, and Base64 Data Encodings
- RFC 6749 — The OAuth 2.0 Authorization Framework
- RFC 7523 — JSON Web Token (JWT) Profile for OAuth 2.0 Client Authentication and Authorization Grants
- RFC 8785 — JSON Canonicalization Scheme (JCS)
- RFC 8259 — The JavaScript Object Notation (JSON) Data Interchange Format
- W3C DID Core — Decentralized Identifiers v1.0
- W3C DID Extensions registry: `did:opena2a` method entry (w3c/did-extensions#717, merged 2026-07-04)
- W3C CCG did:web Method Specification: the `did:web` method under which provider-scoped AIP identifiers are issued (§3.2)
- W3C Verifiable Credentials — Verifiable Credentials Data Model v2.0
- WebAuthn Level 3 — Web Authentication API
- FIPS 204 — Module-Lattice-Based Digital Signature Standard (ML-DSA)
- Google A2A Protocol — Agent-to-Agent communication
- Anthropic MCP — Model Context Protocol
- OpenID Connect Core 1.0

---

## Appendix A: Reference Implementation

The OpenA2A AIM platform (`github.com/opena2a-org/agent-identity-management`) is the reference implementation and targets Conformance Level 2. It does not meet Level 2 yet: challenge-response verification (Section 5) is a Level 2 requirement, and A.1 below marks it Partial because the Section 5.1 exchange is not served.

| Component | Implementation |
|-----------|---------------|
| Ed25519 identity | `apps/backend/internal/crypto/keygen.go` |
| Hybrid PQC signing | `apps/backend/internal/crypto/pqc/hybrid.go` |
| Agent lifecycle | `apps/backend/internal/application/agent_service.go` |
| Trust scoring (9-factor reference) | `apps/backend/internal/application/trust_calculator.go` |
| Capability enforcement | `apps/backend/internal/application/capability_service.go` |
| Drift detection | `apps/backend/internal/application/drift_detection_service.go` |
| MCP verification | `apps/backend/internal/application/mcp_service.go` |
| A2A verification | `apps/backend/internal/application/a2a_service.go` |
| Registry bridge | `apps/backend/internal/application/registry_bridge_service.go` |
| TypeScript SDK | `sdk/typescript/src/` |

### A.1 Spec sections currently implemented by AIM

The reference implementation's coverage is uneven and the gaps are tracked publicly here. Any cross-implementation pitch should scope claims to the rows marked Shipped.

| AIP / AIP-adjacent section | AIM status | Notes |
|---|---|---|
| §3 Agent Identity (Ed25519 keypair, agent ID, DID) | Shipped | `crypto/keygen.go`, `domain/agent.go`. Server-side key generation; agent receives Ed25519 public key registered on its record. The provider identifies each agent by a UUID it assigns, as §3.1 permits, and derives no `aim_` agent ID; `opena2a-cli identity create` derives the §3.1 agent ID from the public key. DID resolution serves the deprecated alias form only and rejects other prefixes (`handlers/aip_handler.go:68`); the `did:web` route of §3.2 is not implemented as of 2026-09-08. |
| §3 Hybrid PQC signing (Ed25519 + ML-DSA-65) | Shipped end to end on the registry path | Registry-side code paths below are in a private repository; the publicly checkable evidence for this row is the hybrid fixture in [`atx-conformance`](https://github.com/opena2a-standards/atx-conformance) (`fixtures/baseline-valid-hybrid.json`), which the Go reference verifier accepts on both algorithms. Registry-side `ATCService.IssueATC()` at `opena2a-registry/internal/application/atc_service.go` emits hybrid signatures in production: threshold Ed25519 plus one ML-DSA-65 signature from the hybrid keypair wired in at `cmd/server/main.go:682-685` (startup log: "ATC post-quantum hybrid signing enabled (Ed25519 + ML-DSA-65)"). The ML-DSA-65 signature `Value` is the raw 3309-byte `mldsa65.SignatureSize` blob as of opena2a-registry PR #215 (prior credentials carried a legacy combined Ed25519+ML-DSA blob; ATC TTL is 7 days, so the rollover is naturally complete one week after PR #215 ships). The standalone offline-verify package `opena2a-registry/pkg/atcverify` enforces the hybrid signing mandate as of opena2a-registry PR #214: when a credential declares an ML-DSA-65 signature, at least one ML-DSA-65 signature must verify in addition to at least one Ed25519 signature. AIM itself signs no ATC (status 2026-10-11, public repository `opena2a-org/agent-identity-management`, `main` at `8500bc98`). Its Ed25519-only CBOR issuer `RealATCIssuer` was removed in agent-identity-management PR #217, and `infrastructure/atc/` now holds the verifiers (`atc_verifier.go`, `server_verifier.go`) and the CRL client. The issuance route `POST /api/v1/agents/{id}/atc` (`handlers/atc_issuance_handler.go`, registered in `cmd/server/main.go`) computes the agent's 9-factor behavioral score and asks the Registry's issuance endpoint to sign the credential and record it in the transparency log (`application/atc_issuance_service.go`, `infrastructure/registry/atc_client.go`). |
| §4 Capabilities | Partial | `application/capability_service.go`, FGA engine at `application/fga_engine.go` with 5-step blocking enforcement (capability, attribute, context, chain, intent). Not implemented as of 2026-10-21 (AIM `main` at `9290cc1c`): the §4.4 penalty schedule and the reservation of `payment` and `agent`. When a verified agent that holds at least one granted capability, and is not marked compromised, requests a capability outside its grants, `AgentService.VerifyCapability` (`application/agent_service.go`), which serves `POST /api/v1/agents/{id}/verify-capability` and `POST /api/v1/verifications`, records a capability violation and subtracts 0.10 (10%) from the agent's trust score when it blocks the request and 0.05 (5%) when it lets it through, never below 0, whatever the violation's severity; the severity it records follows the agent's trust score and whether the request is blocked, not the action attempted. `CapabilityService.VerifyAction` in `application/capability_service.go`, which subtracts a flat 0.10 for every violation, is mounted on no route. `ReservedNamespaces` in `domain/capability.go` lists nine of the eleven §4.2 namespaces, all but `payment` and `agent`, and the discovery document (`handlers/aip_handler.go`) advertises a different list of eight in `supportedCapabilityNamespaces`, with `payment` and without `user`, `agent` and `secrets`. |
| §4 JIT capability grants with TTL | Partial | TTL exists for PAM (Privileged Access Management) emergency-escalation grants. Routine capability grants are static. |
| §5 Verification (challenge-response) | Partial | The discovery document (`handlers/aip_handler.go`) advertises the §5.1 challenge endpoint `/api/v1/agents/{agentId}/challenge`, but the backend router (`cmd/server/main.go`) registers no such route as of 2026-10-08, so the §5.1 exchange is not served; the challenge-response transcripts in [`aip-conformance`](https://github.com/opena2a-standards/aip-conformance) are the way to exercise it. Served today: `POST /api/v1/agents/{id}/authorize`, the fine-grained authorization decision endpoint, which checks a capability request and does not verify a signed challenge; and `GET /api/v1/mcp-servers/{id}/challenge` with `POST /api/v1/mcp-servers/{id}/attest`, an Ed25519 proof-of-possession challenge scoped to MCP server attestation, not the §5.1 challenge and response bodies. |
| §6 Trust Scoring (9-factor) | Partial | `application/trust_calculator.go`, reference algorithm with audited weights, at algorithm version 1: the factor set, the weights, exclusion with redistribution and the anti-gaming ceiling. The §6.1 unscored state and `algorithmVersion` (version 2, in this specification since 1.2.0-draft) are not implemented as of 2026-10-11: the calculator publishes a composite for every agent, including one with no verification events, and carries no `algorithmVersion` or `scoreStatus`. All nine factors have scoring functions (§6.1, per-factor implementation status). |
| §6.5 ATP integration | Partial | One way, AIM to Registry (status 2026-10-11, AIM `main` at `8500bc98`; ATP-SPEC is at 1.1.0-draft, last released as v1.0.0-rc1 on 2026-04-28). `POST /api/v1/agents/{id}/atc` sends the agent's 9-factor behavioral score to the Registry, which signs it into the credential and records the issuance in its transparency log (`application/atc_issuance_service.go`). When enabled (`REGISTRY_BRIDGE_ENABLED=true`, `cmd/server/main.go`), the registry bridge pushes each active organization's events as one batch under a fixed per-organization pseudonymous token, the SHA-256 of the organization ID and a server secret, so the Registry can link every batch from one organization: one event per agent and MCP server the agent attested, whose fields include that agent's own trust score as `successRate`, its audit log entry count (up to 1000) and its capability violation count (`application/registry_bridge_service.go`). That is the one-way push GAP-ANALYSIS records. The credential carries AIM's behavioral score alone; AIM does not compute the §6.5 combined `ecosystem_trust` score. |
| §9 Audit (append-only) | Shipped, not cryptographically signed | `repository/audit_log_repository.go` enforces append-only at the repository layer. Hash-chain or signed-log fields (`signature`, `hash`, `previous_hash`) are not present; integrity relies on database-level access control today. |
| Local offline verification | TypeScript and Java in the AIM SDKs; Go in the registry; Go plus Python in the conformance suite | Standalone offline-verify package exists at the registry's `pkg/atcverify` (Go, full hybrid). As of 2026-10-11 (AIM `main` at `8500bc98`) the TypeScript SDK ships `LocalVerifier` (`sdk/typescript/src/local/LocalVerifier.ts`, built on `@opena2a/atx-verify`) and the Java SDK ships `LocalAtxVerifier` (`sdk/java/src/main/java/org/opena2a/aim/atx/LocalAtxVerifier.java`); both verify Ed25519 and every declared ML-DSA-65 signature. The Python AIM SDK does not yet ship a local-verify library. The [`opena2a-org/atx-conformance`](https://github.com/opena2a-standards/atx-conformance) suite ships an additional SDK-independent Python reference verifier (Ed25519 only; ML-DSA-65 verification out of scope for the Python stdlib stack) and a Go reference verifier with full Ed25519 plus ML-DSA-65 coverage. Both validate the same byte-stable fixture set and demonstrate that the wire format is implementable in a second language without an SDK dependency. |

Note on runtime self-attestation and protocol-enforcement: AIP does not specify a runtime self-attestation layer (that surface belongs to ATX core §5 and the ARC runtime layer, not AIP). For ecosystem context: OpenA2A's reference implementation of the runtime layer ships today as a first-party module inside HMA (`hackmyagent/src/arp/`), not yet inside AIM. AIM-side integration is on the AIM roadmap as a separate track.

## Appendix B: Relationship to ATP

AIP and ATP are complementary protocols:

```
AIP (Agent Identity Protocol)          ATP (Agent Trust Protocol)
  "Who is this agent?"                   "Should I trust this agent's code?"
  Identity, capabilities, governance     Provenance, supply chain, scanning
  Behavioral trust (how it acts)         Code trust (how it was built)
  Per-organization                       Ecosystem-wide

          ↓ feeds into ↓                        ↓ feeds into ↓
                    Combined Trust Decision
                    "Is this agent safe to use?"
```

An agent with a strong AIP identity (verified, high trust score, clean audit log) but weak ATP score (unscanned code, no provenance) is a well-behaved agent running unverified code.

An agent with a strong ATP score (scanned code, SLSA provenance, federation-verified) but weak AIP identity (no verification history, capability violations) is verified code running in an uncontrolled environment.

Both are needed for a complete trust decision.
