# OpenA2A AIM (Agent Identity Management) → AIP: Gap Analysis

## What Exists vs What the Spec Requires

Based on source code review of `agent-identity-management` (March 2026; a row marked *updated* with a month was revised in that month).

The status of each specification section in the reference implementation is kept in
[Appendix A.1 of the specification](AIP-SPEC.md#a1-spec-sections-currently-implemented-by-aim).
The tables below break those sections into finer requirements; where a row here and Appendix
A.1 differ, Appendix A.1 is the current record.

### Identity (Section 3)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| Ed25519 keypair generation | Complete | `apps/backend/internal/crypto/keygen.go` |
| ML-DSA-65 hybrid signing | Complete | `apps/backend/internal/crypto/pqc/hybrid.go` |
| Agent ID format (`aim_` + 16 base64url characters, AIP-SPEC §3.1) | Complete in the CLI (*updated 2026-10*): `opena2a-cli identity create` derives it from the public key. The provider assigns each agent a UUID instead and has no `aim_` derivation, which §3.1 permits | `apps/backend/internal/domain/agent.go` (UUID) |
| DID resolution | Partial (*updated 2026-09*): the resolver answers the deprecated pre-1.1 alias form only; the `did:web` form and its `did.json` route (AIP-SPEC §3.2, 1.1.0-draft) are not implemented | `handlers/aip_handler.go` (ResolveDID), `domain/agent_did.go` |
| DID Document generation | Complete (*updated 2026-07*) — W3C DID Document served by the resolver | `handlers/aip_handler.go` |
| Local identity file format | Partial — SDK creates files but format not standardized | `sdk/typescript/` |
| Key rotation with grace period | Complete | `agent.go` (KeyRotationGraceUntil, PreviousPublicKey) |

### Capabilities (Section 4)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| namespace:action format | Complete | `apps/backend/internal/domain/capability.go` |
| Reserved namespaces | Partial (*updated 2026-10*): 9 of the 11 namespaces of AIP-SPEC §4.2 are reserved, all but `payment` and `agent`; the discovery document advertises a different list of 8 (AIP-SPEC Appendix A.1, the §4 row) | `apps/backend/internal/domain/capability.go` (ReservedNamespaces), `handlers/aip_handler.go` |
| Capability violation tracking | Complete | `capability.go` (CapabilityViolation) |
| Capability negotiation protocol | NOT IMPLEMENTED — capabilities checked server-side only | - |
| Custom org namespaces | NOT IMPLEMENTED | - |

### Verification (Section 5)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| Challenge-response (Ed25519) | Partial (*updated 2026-10*): the discovery document advertises the §5.1 challenge endpoint `/api/v1/agents/{agentId}/challenge`, but the backend registers no such route, so the §5.1 exchange is not served (AIP-SPEC Appendix A.1, the §5 row) | `apps/backend/internal/application/verification_event_service.go`, `handlers/aip_handler.go` |
| MCP verification flow | Complete | `mcp_service.go` |
| A2A verification flow | Complete | `a2a_service.go` |
| OAuth 2.0 / OIDC | Partial (*updated 2026-10*): the backend serves an OAuth 2.0 token endpoint, `POST /api/v1/oauth/token` (RFC 6749), that accepts the JWT-bearer grant type of RFC 7523 from a registered agent and returns a bearer access token, and a device authorization grant (RFC 8628) for CLI login. The token request carries the agent's signed JWT in `client_assertion`, with `client_id` and `client_assertion_type`; the handler reads no `assertion` parameter, in which RFC 7523 Section 2.1 carries the JWT. No code that issues an OpenID Connect ID token was found | `handlers/oauth_token_handler.go`, `handlers/device_auth_handler.go` |
| WebAuthn/FIDO2 | NOT IMPLEMENTED | - |
| JWT tokens | Complete (custom, not standard OAuth) | `infrastructure/auth/jwt.go` |
| API keys | Complete | `api_key_service.go` |

### Trust Scoring (Section 6)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| 9-factor algorithm (spec §6.1) | 9 of 9 factors implemented (*updated 2026-10*; §6.1 exclusion + anti-gaming cap implemented; compliance and feedback are excluded for an agent with no such data) | `trust_calculator.go` |
| Unscored state and algorithm version (spec §6.1, since 1.2.0-draft) | NOT IMPLEMENTED (*updated 2026-10*): a composite is published for every agent, including one with no verification events; no `algorithmVersion` or `scoreStatus` | `trust_calculator.go`, `domain/trust_score.go` |
| Verification factor (25%) | Complete | `trust_calculator.go` |
| Uptime factor (15%) | Complete | `trust_calculator.go` |
| Success rate factor (15%) | Complete | `trust_calculator.go` |
| Security alerts factor (15%) | Complete | `trust_calculator.go` |
| Compliance factor (10%) | Complete (*updated 2026-10*) — scored from the organization's latest AIM compliance snapshot; excluded when it has none | `trust_calculator.go` |
| Execution isolation factor (10%) | Complete (*updated 2026-07*) — measured in the composite; persistence of the stored breakdown column is a filed follow-up | `trust_calculator.go` |
| Age factor (5%) | Complete | `trust_calculator.go` |
| Drift factor (3%) | Complete (*updated 2026-10*) — scored from configuration-drift and MCP-drift alerts of the last 30 days on the agent and its connected MCP servers; no alerts scores 1.0 | `trust_calculator.go` |
| Feedback factor (2%) | Complete (*updated 2026-10*) — scored from the agent's feedback ratings, counted by sentiment; excluded when it has none | `trust_calculator.go` |
| Verifiable Credential expression | NOT IMPLEMENTED | - |
| ATP integration | Partial (one-way push via registry bridge) | `registry_bridge_service.go` |

### Governance (Section 7)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| Policy format (YAML) | NOT IMPLEMENTED (policies in DB, not YAML) | `security_policy_service.go` |
| Policy actions (allow/deny/approve/rate_limit) | Partial | `security_policy_service.go` |
| SOUL integration | NOT IMPLEMENTED in AIM (SOUL is CLI-side) | - |

### Lifecycle (Section 8)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| State machine | Complete (pending→verified→suspended→revoked) | `agent.go` |
| Key rotation | Complete | `agent.go` |
| Drift detection | Complete | `drift_detection_service.go` |
| Suspension | Complete | `agent_service.go` |
| Revocation | Complete | `agent_service.go` |

### Audit (Section 9)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| Server audit log | Complete | `audit_service.go` |
| Local audit log (SDK) | Complete | SDK writes to `audit.jsonl` |
| Verification events | Complete (comprehensive) | `verification_event_service.go` |

### Discovery (Section 10)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| /.well-known/aip | Complete (*updated 2026-10*): the provider serves its discovery document; on 2026-09-02 both `https://aim.opena2a.org/.well-known/aip` and `https://api.aim.opena2a.org/.well-known/aip` answered HTTP 200 ([docs/specification-notes.md](docs/specification-notes.md#reference-provider)) | `handlers/aip_handler.go` |

To check the discovery endpoint yourself, fetch the provider's discovery document; an HTTP 200
means it is served:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://aim.opena2a.org/.well-known/aip
```

### Integration Patterns (Section 11)

The status text of the rows below restates what the Google A2A and Anthropic MCP lines of the Interoperability list in [docs/interoperability.md](docs/interoperability.md) and of the AIP-SPEC abstract say as of 2026-10-11; it adds no new reading of the source. The File column of the A2A agent card identity row was read from the `agent-identity-management` source in 2026-10: the handler the backend routes `GET /.well-known/agent.json` to, and the service function that adds the `aim` extension to the card. The verification flows of both protocols have their own rows under Verification.

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| A2A agent card identity | Partial (*updated 2026-10*): the agent card the backend serves carries the agent's ID and registered public key in an `aim` extension, and that ID is the UUID the provider assigns (AIP-SPEC §3.1), not an `aim_` agent ID | `apps/backend/internal/interfaces/http/handlers/a2a_handler.go` (GetPublicAgentCard), `apps/backend/internal/application/a2a_service.go` (GetEnhancedAgentCard) |
| MCP capability-based tool access | Partial (*updated 2026-10*): the backend checks an agent's capabilities server-side; it does not serve the §5.1 exchange an MCP server would use to verify a connecting agent (AIP-SPEC Appendix A.1, the §5 row) | `apps/backend/internal/application/capability_service.go` |

---

## Priority Implementation Order

1. **DID resolution** — required for Level 3 and cross-platform identity
2. **Verifiable Credentials** — trust scores as W3C VCs for portability
3. **OpenID Connect ID token** — the backend serves an OAuth 2.0 token endpoint that returns a bearer access token (Verification table above); what is missing is an OpenID Connect ID token
4. **WebAuthn/FIDO2** — browser-based key storage for Chrome integration
5. **Capability negotiation** — runtime negotiation protocol between agents
6. **YAML policy format** — declarative governance policies

A completed item leaves this list, and a sentence here says where its status is recorded. Two
items left it in 2026-10. The `/.well-known/aip` discovery endpoint, first in this list until
then, is served (Discovery table above). The compliance, drift and feedback trust scoring
factors, third in this list until then, are implemented (Trust Scoring table above).

---

## Prior Art and Naming in the IETF Landscape (June 2026)

The abbreviations "AIP" and the sibling "AAP" are each used by more than one
Internet-Draft. This section records that prior art and how OpenA2A AIP relates to
it, so implementers and reviewers can disambiguate. When referenced outside this
repository, use the fully qualified name **OpenA2A AIP**.

### Drafts using the "AIP" / "AAP" names

| Draft | Author(s) | datatracker (initial) | Scope |
|---|---|---|---|
| draft-aip-agent-identity-protocol | James Cao (Montcao), Carlos Eduardo Arango Gutierrez (NVIDIA) | -00, 2026-03-16 | Agent identity registry + enforcement proxy |
| draft-singla-agent-identity-protocol | Singla | -00, 2026-04-16 | Agent identity + delegation |
| draft-aap-oauth-profile, "Agent Authorization Profile" | Cruz (independent) | -01, 2026-02-07 | OAuth 2.0 profile for agent-to-API authorization |
| OpenA2A AIP (this spec), `draft-fane-opena2a-aip` | OpenA2A | -00, 2026-07-06 | Identity, capabilities, verification, trust scoring, governance, lifecycle, audit |
| OpenA2A AAP (companion), `draft-fane-opena2a-aap` | OpenA2A | -00, 2026-07-06 | Authorization token model + broker/resolution layer |

The two OpenA2A rows were updated on 2026-10-11; the other rows record the datatracker as of
June 2026. [docs/specification-notes.md](docs/specification-notes.md) names the current revision of `draft-fane-opena2a-aip`.

### OpenA2A AIP vs draft-aip-agent-identity-protocol (Cao/Arango)

The two specifications share a common spine — a Layer 1 agent-identity registry
and a Layer 2 policy/enforcement proxy — and differ on what is built above it.

| Dimension | draft-aip-agent-identity-protocol-00 | OpenA2A AIP |
|---|---|---|
| Agent identifier | host-prefixed UUIDv4 (`host/uuid`) | DID: provider-scoped `did:web` profile at the AIP layer (`did:web:<provider-host>:agents:<id>`, AIP-SPEC §3.2); the ecosystem-scoped `did:opena2a` method (W3C did-extensions #717, merged 2026-07-04) names Registry-listed resources at the ATP/ATX layer |
| Signing keys | Ed25519 | Ed25519, with ML-DSA-65 hybrid in the ATX credential |
| Identity registry | HTTP registry, agent record | Managed / federated identity (Conformance Levels 2–3) |
| Per-call attestation | per-call signed AIP token (argumentsHash + nonce) | challenge-response verification (Section 5) |
| Enforcement | Layer 2 forward proxy; ALLOW / DENY / HOLD; YAML policy, DLP, HITL | governance (Section 7) + proxy enforcement |
| Capability model | tool allowlists only | structured capability vocabulary + reserved namespaces (Section 4) |
| Trust score | not defined | multi-factor trust score + levels + history (Section 6) |
| Portable credential | per-call JSON token | ATX signed portable credential via ATP |
| Transparency log | not defined | RFC 6962 Merkle log (Registry) |
| Verifiable Credentials | not defined | W3C VC expression of trust (Section 6.4) |
| Revocation | status + SSE invalidation | suspension / revocation + drift detection (Section 8) |

The identity-and-enforcement spine is common to both. The elements specific to
OpenA2A AIP — DID-based identity, a structured capability vocabulary, a
multi-factor trust score, a portable signed credential (ATX) carried via ATP, a
transparency log, and W3C Verifiable Credential expression — are not present in
draft-aip-agent-identity-protocol-00. OpenA2A AIP leads with those elements rather
than with the shared identity spine.
